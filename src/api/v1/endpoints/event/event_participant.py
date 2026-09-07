from src.api.v1.endpoints.event import *
from src.api.v1.router import router

# internal imports
from src.init import get_event_service
from src.services.v1 import EventService, get_current_user
from src.models import UserRegister, Event
from src.schemas.v1 import EventJoin, JoinedEventsResponse, EventParticipantResponse

router = APIRouter()


# Lets a user join an event using an event join code
@router.post("/join",
            response_description="Join an Event using Code",
            response_class=JSONResponse)

async def join_event(
    join_data: EventJoin = Body(...),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    await service.join_event(user_id=current_user.user_id, code=join_data.event_code)
    return {"message": "Successfully joined the event"}


# Returns a paginated list of events the current user has joined
@router.get("/joined", response_model=List[JoinedEventsResponse],
            response_description="Returns Names of Joined Events",
            response_class=JSONResponse)

async def get_joined_events(
    skip: int = Query(0, ge=0, description="Records skip"),
    limit: int = Query(100, le=500, description="Max records"),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return await service.get_joined_events(user_id=current_user.user_id, skip=skip, limit=limit)


# Adds a co-organizer to an event; only the main event organizer is allowed to do this
@router.post("/{event_id}/participants/{participant_id}",
            response_description="Remove a Co Organizer by main event organizer and Co organizer from Event",
            response_class=JSONResponse)

async def add_co_organizer(
    event_id: UUID = Path(..., description="Event's ID"),
    participant_id: UUID = Path(..., description="Participant's ID"),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    event = await service.get_event_by_id(event_id=event_id)

    # Only the main organizer (not co-organizers) can promote a participant to co-organizer
    if current_user.user_id != event.organizer_id:
        raise HTTPException(status_code=403, detail="Only the event organizer can add co-organizers")

    await service.add_co_organizer(
        event_id=event_id,
        user_id=participant_id
    )
    return {"message": f"Event co-organizer added by event organizer"}

# Returns a paginated list of all participants in an event
@router.get("/{event_id}/participants",
            response_model=List[EventParticipantResponse],
            response_description="Get all Participant from an Event",
            response_class=JSONResponse)
            
async def get_all_participants(
    event_id: UUID = Path(..., description="Event's ID"),
    skip: int = Query(0, ge=0, description="Records skip"),
    limit: int = Query(100, le=500, description="Max records"),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
    ):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    return await service.get_all_participants(event_id=event_id, skip=skip, limit=limit)

# Removes a participant from an event; allowed for the organizer or a co-organizer
@router.delete("/{event_id}/participants/{participant_id}",
            response_description="Remove a Participant from Event",
            response_class=JSONResponse)

async def remove_event_participant(
    event_id: UUID = Path(..., description="Event's ID"),
    participant_id: UUID = Path(..., description="Participant's ID"),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Authorization (organizer/co-org check) is handled inside the service layer
    await service.remove_participant_by_organizer_and_co_org(
        user_id=current_user.user_id,
        event_id=event_id,
        participant_id=participant_id
    )
    return {"message": f"Participant {participant_id} removed from event {event_id}"}


# Removes a co-organizer from an event; can be done by the main organizer or the co-organizer themselves
@router.delete("/{event_id}/co-organizers/{co_organizer_id}",
            response_description="Remove a Co Organizer by main event organizer and Co organizer from Event",
            response_class=JSONResponse)

async def remove_co_organizer(
    event_id: UUID = Path(..., description="Event's ID"),
    co_organizer_id: UUID = Path(..., description="Co_org's ID"),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Authorization (must be main organizer or the co-organizer themself) handled in service layer
    await service.remove_co_organizer(
        user_id=current_user.user_id,
        event_id=event_id,
        co_organizer_id=co_organizer_id
    )
    return {"message": f"Event co-organizer {co_organizer_id} removed from event {event_id}"}

# Removes the main organizer from an event; only the organizer themself can do this
@router.delete("/{event_id}/organizer/{organizer_id}",
            response_description="Remove a Co Organizer by main event organizer and Co organizer from Event",
            response_class=JSONResponse)

async def remove_organizer(
    event_id: UUID = Path(..., description="Event's ID"),
    organizer_id: UUID = Path(..., description="Organizer's ID"),
    current_user: UserRegister = Depends(get_current_user),
    service: EventService = Depends(get_event_service)
):
    if current_user.role_name != "User":
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Service enforces that only the organizer themself can trigger this removal
    await service.remove_organizer_by_self(
        user_id=current_user.user_id,
        event_id=event_id,
    )
    return {"message": f"Event organizer {organizer_id} removed from event {event_id}"}