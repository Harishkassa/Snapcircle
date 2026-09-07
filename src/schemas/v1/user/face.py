"""
FaceSession -- per-WebSocket-connection state.

Not a DB model, not a Pydantic request/response schema -- it's a runtime
state-holder that lives only for the duration of one websocket connection.
Each connection gets its own instance, so there is no shared mutable state
across users (no race conditions between different users' sessions).
"""

import numpy as np
import time

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


from src.utils import LOCK_FRAMES_REQUIRED


@dataclass
class FaceSession:
    session_id: UUID
    good_frame_count: int = 0
    best_frame: Optional[np.ndarray] = None
    best_sharpness: float = -1.0
    created_at: float = field(default_factory=time.time)

    def reset_streak(self):
        self.good_frame_count = 0

    def register_good_frame(self, face_crop: np.ndarray, sharpness: float):
        self.good_frame_count += 1
        if sharpness > self.best_sharpness:
            self.best_sharpness = sharpness
            self.best_frame = face_crop.copy()

    def is_locked(self) -> bool:
        return self.good_frame_count >= LOCK_FRAMES_REQUIRED