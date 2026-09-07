from src.api.v1.endpoints.event import *
from src.api.v1.router import router

# internal imports
from src.init import get_event_service
from src.utils import filevalidator
from src.models import Event
from src.services.v1 import EventService, get_current_user
from src.models import UserRegister
from src.utils import limiter
from src.schemas.v1 import (
    EventCreate,
    EventResponse,
    EventUpdate
)

router = APIRouter()


# Creates a new event along with an uploaded group photo
@router.post("/", response_model=EventResponse, status_code=201)
@limiter.limit("5/minute")
async def create_event(
    request: Request,
    event_create_data: EventCreate = Depends(EventCreate.as_form),
    uploaded_group_photo: UploadFile = Depends(filevalidator),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")

    event = await service.create_event(
        event_create_data,
        uploaded_group_photo,
        organizer_id=current_user.user_id
    )

    return event


# Returns a paginated list of all events
@router.get("/", response_model=List[EventResponse],
            response_description="Returns All Events",
            response_class=JSONResponse)

async def get_all_events(
    skip: int = Query(0, ge=0, description="Records skip"),
    limit: int = Query(100, le=500, description="Max records"),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "Admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return await service.get_all_events(skip=skip, limit=limit)


# Searches events by name, scoped to the current user
@router.get("/search", response_model=List[EventResponse],
            response_description="Search Events By Name",
            response_class=JSONResponse)

async def search_event_by_name(
    event_name: str = Query(...),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return await service.get_event_by_name(event_name=event_name, user_id=current_user.user_id)


# Returns details of a single event by ID
@router.get("/{event_id}", response_model=EventResponse,
            response_description="Returns Event Details",
            response_class=JSONResponse)

async def get_event(
    event_id: UUID = Path(..., description="Event's ID"),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return await service.get_event_by_id(event_id)


# Updates details of an existing event
@router.put("/{event_id}",
            response_description="Update Event Details",
            response_class=JSONResponse)

async def update_event(
    event_id: UUID = Path(..., description="Event's ID"),
    event_update: EventUpdate = Body(...),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    await service.update_event_details(event_id, event_update)
    return {"message": f"Event {event_id} is updated"}


# Deletes an event by ID
@router.delete("/{event_id}",
            response_description="Delete Event",
            response_class=JSONResponse)

async def delete_event(
    event_id: UUID = Path(..., description="Event's ID"),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    await service.delete_event(event_id)
    return {"message": f"Event {event_id} is deleted"}