from fastapi import APIRouter

router = APIRouter()

from src.api.v1.endpoints.user import register_api, user_login, face_capture
from src.api.v1.endpoints.event import events, event_participant, event_photos

router.include_router(register_api.router, prefix="/users", tags=["User"])
router.include_router(user_login.router, prefix="/users", tags=["Auth"])
router.include_router(face_capture.router, prefix="/face_capture", tags=["Face_capture"])
router.include_router(event_participant.router, prefix="/events", tags=["Event"])
router.include_router(events.router, prefix="/events", tags=["Event"])
router.include_router(event_photos.router, prefix="/events", tags=["Event"])
