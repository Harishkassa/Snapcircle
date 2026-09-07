from src.services.v1 import *

# Loads the InsightFace face-embedding model (buffalo_l) once at module import time
_face_app = FaceAnalysis(name="buffalo_l")
_face_app.prepare(ctx_id=-1)  # ctx_id=-1 forces CPU inference (no GPU)

logger = logging.getLogger(__name__)


async def generate_embedding(cropped_face_image) -> list[float]:
    """
    cropped_face_image: numpy array (BGR), already RetinaFace se crop kiya hua face.
    """
    try:
        # Runs the CPU-bound model inference in a threadpool to avoid blocking the event loop
        faces = await run_in_threadpool(_face_app.get, cropped_face_image)

        if not faces:
            return None

        logger.info("Embedding generation has been done!")
        # Return only the first detected face's embedding as a plain list (JSON/DB friendly)
        return faces[0].embedding.tolist()

    except Exception as e:
        # Non-fatal: caller treats a None embedding as "skip this frame/face"
        logger.warning(f"Embedding generation skipped: {e}")
        return None