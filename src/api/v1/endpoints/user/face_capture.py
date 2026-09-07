"""
WebSocket route for real-time face capture.

Orchestrates the pipeline per frame:
  decode -> detect (threadpool) -> select largest face -> size check
  -> sharpness check -> streak tracking -> lock & save

All actual detection/scoring logic lives in services/face_service.py.
All per-connection state lives in schemas/face_session.py (FaceSession).
"""

from src.api.v1.endpoints.user import *

from src.utils import MIN_SHARPNESS, LOCK_FRAMES_REQUIRED, FACE_TTL_SECONDS
from src.api.v1.router import router
from src.schemas.v1 import FaceSession
from src.db.redis_connection import redisconnection
from src.services.v1.face_service import (
    decode_frame,
    resize_frame,
    select_largest_face,
    is_face_big_enough,
    crop_face,
    sharpness_score,
    build_feedback,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/face-capture")
async def face_capture_ws(websocket: WebSocket):
    await websocket.accept()

    # Each connection gets its own isolated session state (tracks streaks, best frame, etc.)
    session = FaceSession(session_id=str(uuid6.uuid7()))
    logger.info(f"[{session.session_id}] Client connected")

    try:
        while True:
            # ---- 1. Receive frame ----
            try:
                data = await websocket.receive_json()
            except ValueError:
                await websocket.send_json(build_feedback("error", message="Invalid JSON"))
                continue

            # Client is expected to send base64-encoded frame under "frame" key
            b64_frame = data.get("frame")
            if not b64_frame:
                await websocket.send_json(build_feedback("error", message="Missing 'frame' field"))
                continue

            frame = decode_frame(b64_frame)
            if frame is None:
                await websocket.send_json(build_feedback("error", message="Could not decode frame"))
                continue

            # Resize to a standard size for consistent detection performance/accuracy
            frame = resize_frame(frame)

            # ---- 2. Detect faces (non-blocking) ----
            try:
                # Run CPU-bound detection in a threadpool so it doesn't block the event loop
                faces = await run_in_threadpool(RetinaFace.detect_faces, frame)
            except Exception as e:
                logger.error(f"[{session.session_id}] Detection failed: {e}")
                await websocket.send_json(build_feedback("error", message="Detection failed"))
                continue

            # RetinaFace returns a tuple () when nothing is detected, dict when faces found
            if not isinstance(faces, dict) or not faces:
                session.reset_streak()
                await websocket.send_json(build_feedback("no_face"))
                continue

            # ---- 3. Pick largest confident face (multiple faces are fine, we just pick one) ----
            face = select_largest_face(faces)
            if face is None:
                session.reset_streak()
                await websocket.send_json(build_feedback("no_confident_face"))
                continue

            # ---- 4. Size check ----
            # Ensures the face occupies enough of the frame (user isn't too far away)
            if not is_face_big_enough(face, frame.shape):
                session.reset_streak()
                await websocket.send_json(build_feedback("move_closer"))
                continue

            # ---- 5. Sharpness check ----
            # Crop just the face region and score it for blur/focus quality
            face_crop = crop_face(frame, face['facial_area'])
            sharpness_value = sharpness_score(face_crop)

            if sharpness_value < MIN_SHARPNESS:
                session.reset_streak()
                await websocket.send_json(build_feedback(
                    "too_blurry", sharpness=round(sharpness_value, 2), required=MIN_SHARPNESS
                ))
                continue

            # ---- 6. Register good frame, update streak ----
            # This frame passed all checks; track it as a "good" frame and update the lock streak
            session.register_good_frame(face_crop, sharpness_value)

            await websocket.send_json(build_feedback(
                "verifying",
                progress=round(session.good_frame_count / LOCK_FRAMES_REQUIRED, 2),
                sharpness=round(sharpness_value, 2),
                confidence=round(float(face["score"]), 2),
            ))

            # ---- 7. Lock + save ----
            # Once enough consecutive good frames are collected, lock in the best one and persist it
            if session.is_locked():
        
                # face image ko base64 mein convert karo (numpy array -> jpeg bytes -> base64)
                success, jpeg_buffer = cv2.imencode(".jpg", session.best_frame)
                if not success:
                    await websocket.send_json(build_feedback("error", message="Encoding failed"))
                    break

                face_b64 = base64.b64encode(jpeg_buffer).decode("utf-8")

                temp_face_id = session.session_id  # unique key

                # Cache the locked face temporarily in Redis (auto-expires after FACE_TTL_SECONDS)
                await redisconnection.set_expiration(temp_face_id, face_b64, FACE_TTL_SECONDS)

                logger.info(f"[{session.session_id}] Face locked & cached in Redis")
                await websocket.send_json(build_feedback(
                    "success",
                    temp_face_id=temp_face_id,
                    expires_in=FACE_TTL_SECONDS,
                    sharpness=round(session.best_sharpness, 2)
                ))
                
                # Face successfully captured and cached — end the loop/connection handling
                break

    except WebSocketDisconnect:
        logger.info(f"[{session.session_id}] Client disconnected")

    except Exception as e:
        logger.exception(f"[{session.session_id}] Unexpected error: {e}")
        try:
            # Notify client of internal error before closing the socket
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            logger.debug(f"[{session.session_id}] websocket already closed while closing")