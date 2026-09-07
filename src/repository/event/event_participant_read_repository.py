from src.repository.event import *

# internal imports
from src.models import (
    Event, 
    EventParticipant, 
    EventOrganizer
)
from src.exception import (
    UserAlreadyExistsException,
    JoinedNotFoundException,
    handle_db_errors
)


logger = logging.getLogger(__name__)

class EventParticipantReadRepository:

    def __init__(self, db : Session):
        self.db = db

    @handle_db_errors("get_organizer_of_event_by_id")  
    async def get_organizer_of_event_by_id(self, event_id: UUID, user_id : UUID):
        
        stmt = (select(Event.organizer_id)
                .where(
            Event.event_id == event_id,
            Event.organizer_id == user_id
            ))
        event_organizer = (await self.db.scalars(stmt)).first() 

        if not event_organizer:
            return None

        logger.info(f"Event Organizer {event_organizer} fetched")
        return event_organizer
    
    @handle_db_errors("check_participant_exist")  
    async def check_participant_exist(self, event_id: UUID, user_id: UUID):

        existing_participant = await self.get_event_participant_by_id(participant_id=user_id, event_id=event_id)

        if existing_participant is not None:
            logger.warning(f"User {existing_participant.user_id} is already a participant of event {event_id}")
            raise UserAlreadyExistsException(f"User {existing_participant.user_id} Already Exist")                

    @handle_db_errors("get_co_organizer_of_event_by_id")  
    async def get_co_organizer_of_event_by_id(self, event_id : UUID): 
            
        stmt = select(EventOrganizer.user_id).where(EventOrganizer.event_id == event_id)
        event_organizers = list((await self.db.scalars(stmt)).all())

        if not event_organizers:
            return None
            
        logger.info(f"Event organizer {event_id} fetched")
        return event_organizers
    
    @handle_db_errors("get_event_participant_by_id") 
    async def get_event_participant_by_id(self, participant_id: UUID, event_id: UUID):
        
        stmt = select(EventParticipant).where(
            EventParticipant.user_id == participant_id,
            EventParticipant.event_id == event_id
        )
        event_participant = (await self.db.scalars(stmt)).first()

        if not event_participant:
            return None
            
        logger.info(f"event participant {event_participant.user_id} fetched")
        return event_participant
    
    @handle_db_errors("get_event_co_organizer") 
    async def get_event_co_organizer(self, event_id: UUID, user_id: UUID):
        

        stmt = select(EventOrganizer).where(
            EventOrganizer.event_id == event_id,
            EventOrganizer.user_id == user_id
        )
        co_organizer = (await self.db.scalars(stmt)).first()
        if not co_organizer:
            return None
            
        logger.info(f"Event co organizer {co_organizer.user_id} fetched")
        return co_organizer

    @handle_db_errors("get_joined_events") 
    async def get_joined_events(self, user_id: UUID, skip: int = 0, limit: int = 100) -> list["EventParticipant"]:
        

        stmt = (
        select(Event)
        .join(EventParticipant, Event.event_id == EventParticipant.event_id)
        .where(EventParticipant.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(EventParticipant.joined_at.desc())
        )
            
        joined_events = list((await self.db.scalars(stmt)).all())
        if not joined_events:
            logger.warning(f"No joined events found for user {user_id}")
            raise JoinedNotFoundException()
            
        logger.info("Joined Events featched sucessfully")
        return joined_events
    
    @handle_db_errors("get_all_participants")
    async def get_all_participants(self, event_id: UUID, skip: int = 0, limit: int = 100):

        stmt = (select(EventParticipant)
            .where(EventParticipant.event_id == event_id)
            .offset(skip)
            .limit(limit=limit)
            .order_by(EventParticipant.joined_at.desc()))
        
        particiapnts = list((await self.db.scalars(stmt)).all())
        if not particiapnts:
            None
        
        logger.info("Event participant featched sucessfully")
        return particiapnts
    