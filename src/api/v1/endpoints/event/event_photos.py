from typing import Annotated
from fastapi import File
from src.api.v1.endpoints.event import *
from src.api.v1.router import router

from src.models import UserRegister
from src.utils.file_validator import photos_file_validator
from src.services.v1 import get_current_user, EventService
from src.init import get_event_service

router = APIRouter()


# Uploads one or more photos for a given event (e.g. group/event photos to run face matching against)
@router.post("/{event_id}/photos",
            response_description="Upload Event Photos by event_id",
            response_class=JSONResponse)

async def upload_multi_event_photos(
    event_id: UUID = Path(..., description="Event's ID"),
    uploaded_event_photos: List[UploadFile] = Depends(photos_file_validator),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    # Restricted to "User" role only
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return await service.upload_multi_event_photos(current_user.user_id, uploaded_event_photos, event_id)