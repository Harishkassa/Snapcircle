"""
Stateless helper functions for the face capture pipeline.

Pure functions -- no shared state, no side effects except save_best_frame()
which writes to disk. Easy to unit test in isolation.
"""

import base64
import logging
import os
import time
from typing import Optional

import cv2
import numpy as np

from src.utils import (
    MIN_FACE_RATIO,
    MIN_CONFIDENCE,
    MAX_DETECTION_DIM,
    SAVE_DIR,
)
from src.schemas.v1 import FaceSession

logger = logging.getLogger(__name__)


def decode_frame(b64_jpeg: str) -> Optional[np.ndarray]:
    """Decode a base64 data-URL JPEG string into a BGR OpenCV frame."""
    try:
        # Strip data-URL prefix (e.g. "data:image/jpeg;base64,") if present, keep only the payload
        img_bytes = base64.b64decode(b64_jpeg.split(",")[-1])
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        logger.warning(f"Frame decode failed: {e}")
        return None


def resize_frame(frame: np.ndarray, max_dim: int = MAX_DETECTION_DIM) -> np.ndarray:
    # Downscale only if the longer side exceeds max_dim; never upscale (scale < 1 check)
    h, w = frame.shape[:2]
    scale = max_dim / max(h, w)
    if scale < 1:
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
    return frame


def select_largest_face(faces: dict) -> Optional[dict]:
    """From RetinaFace's output dict, pick the largest-area face above MIN_CONFIDENCE."""
    if not isinstance(faces, dict):
        return None
    best, best_area = None, 0
    for face_data in faces.values():
        x1, y1, x2, y2 = face_data["facial_area"]
        area = (x2 - x1) * (y2 - y1)
        # Only consider confident detections; keep the one with the largest bounding-box area
        if area > best_area and face_data["score"] >= MIN_CONFIDENCE:
            best_area = area
            best = face_data
    return best


def is_face_big_enough(face: dict, frame_shape) -> bool:
    # Uses face height relative to frame height as a proxy for "close enough to camera"
    x1, y1, x2, y2 = face["facial_area"]
    face_h = y2 - y1
    frame_h = frame_shape[0]
    return (face_h / frame_h) >= MIN_FACE_RATIO

def crop_face(frame: np.ndarray, facial_area: list, margin: float = 0.3) -> np.ndarray:
    # Expand the tight bounding box by a margin (default 30%) so the crop includes
    # some context around the face (hair, chin, etc.), not just the exact detection box
    x1, y1, x2, y2 = [int(v) for v in facial_area]  
    h, w = frame.shape[:2]

    face_w, face_h = x2 - x1, y2 - y1
    margin_x, margin_y = int(face_w * margin), int(face_h * margin)

    # Clamp to frame boundaries so the expanded box never goes out of image bounds
    x1, y1 = max(0, x1 - margin_x), max(0, y1 - margin_y)
    x2, y2 = min(w, x2 + margin_x), min(h, y2 + margin_y)

    return frame[y1:y2, x1:x2]

def sharpness_score(img: np.ndarray) -> float:
    # Variance of the Laplacian is a standard blur-detection metric —
    # higher variance = sharper edges = less blurry image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def save_best_frame(session: FaceSession) -> Optional[str]:
    # Persists the best-quality frame captured during the session to disk
    if session.best_frame is None:
        return None
    os.makedirs(SAVE_DIR, exist_ok=True)
    filename = f"{SAVE_DIR}/face_{session.session_id}_{int(time.time())}.jpg"
    success = cv2.imwrite(filename, session.best_frame)
    if not success:
        logger.error(f"Failed to write file: {filename}")
        return None
    return filename


def build_feedback(status: str, **extra) -> dict:
    # Small helper to keep websocket response payloads consistent in shape
    return {"status": status, **extra}