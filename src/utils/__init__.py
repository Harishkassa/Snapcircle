import random
import string
import secrets
import io
import numpy as np

# Third party imports
from uuid import UUID
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from fastapi import HTTPException, status, UploadFile, File, Request
from typing import List
from PIL import Image

# internal imports
from src.utils.file_validator import filevalidator
from src.utils.generate_event_code import GenerateEventCode
from src.utils.similarity import find_best_match
from src.utils.generate_otp import GenerateOtp 
from src.utils.rate_limiter import limiter
from src.utils.hydra_initialization import  (
    MIN_FACE_RATIO, 
    MIN_CONFIDENCE, 
    MIN_SHARPNESS, 
    LOCK_FRAMES_REQUIRED, 
    MAX_DETECTION_DIM, 
    SAVE_DIR,
    FACE_TTL_SECONDS,
    MATCH_THRESHOLD)