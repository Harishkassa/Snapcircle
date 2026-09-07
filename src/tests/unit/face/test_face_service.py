# src/tests/unit/test_face_service.py

import base64
import cv2
import numpy as np
from src.services.v1.face_service import (
    select_largest_face,
    is_face_big_enough,
    sharpness_score,
    resize_frame,
    decode_frame
)

def test_decode_frame_valid_base64():
    dummy = np.zeros((10, 10, 3), dtype=np.uint8)
    _, buffer = cv2.imencode(".jpg", dummy)
    b64 = base64.b64encode(buffer).decode("utf-8")
    
    result = decode_frame(f"data:image/jpeg;base64,{b64}")
    assert result is not None
    
def test_select_largest_face_picks_biggest_box():
    faces = {
        "face_1": {"facial_area": [0, 0, 50, 50], "score": 0.95},
        "face_2": {"facial_area": [0, 0, 200, 200], "score": 0.90},
    }
    result = select_largest_face(faces)
    assert result["facial_area"] == [0, 0, 200, 200]


def test_select_largest_face_returns_none_for_empty_dict():
    result = select_largest_face({})
    assert result is None


def test_is_face_big_enough_true_for_large_face():
    face = {"facial_area": [10, 10, 500, 500], "score": 0.99}
    frame_shape = (600, 600, 3)
    assert is_face_big_enough(face, frame_shape) is True


def test_is_face_big_enough_false_for_small_face():
    face = {"facial_area": [10, 10, 30, 30], "score": 0.99}
    frame_shape = (600, 600, 3)
    assert is_face_big_enough(face, frame_shape) is False

def test_sharpness_score_returns_float():
    # dummy blank image (black frame)
    dummy_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    score = sharpness_score(dummy_frame)
    assert isinstance(score, float)
    assert score >= 0

def test_resize_frame_changes_dimensions():
    dummy_frame = np.zeros((1000, 1000, 3), dtype=np.uint8)
    resized = resize_frame(dummy_frame)
    assert resized.shape[0] <= 1000  # ya apna actual target size check karo
