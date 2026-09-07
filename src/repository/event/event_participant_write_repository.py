from src.repository.event import *

# internal imports
from src.models import (
    Event, 
    EventParticipant,
    EventOrganizer,
)
from src.exception import (
    UserAlreadyExistsException, 
    UserNotFoundException,
    handle_db_errors
)
from src.repository.event.event_participant_read_repository import EventParticipantReadRepository
from src.repository.event.event_repository import EventRepository

logger = logging.getLogger(__name__)

class EventParticipantWriteRepository:

    def __init__(self, db : Session, ep_read_repo : EventParticipantReadRepository, event_repo : EventRepository):
        self.db = db
        self.ep_read_repo = ep_read_repo
        self.event_repo = event_repo

    @handle_db_errors("add_co_organizer")  
    async def add_co_organizer(self, user_id: UUID, event_id: UUID):
        
        existing_participant = await self.ep_read_repo.get_event_participant_by_id(participant_id=user_id, event_id=event_id)

        if not existing_participant:
            logger.warning(f"User {user_id} must be a participant before becoming co-organizer of event {event_id}")
            raise UserNotFoundException("User must be a participant before becoming co-organizer")
        
        event_organizer = await self.ep_read_repo.get_organizer_of_event_by_id(event_id=event_id, user_id=user_id)

        if event_organizer:
            logger.warning(f"User {user_id} is already the organizer of event {event_id}, cannot become co-organizer")
            raise UserAlreadyExistsException("You can not change event organizer to co-organizer")

        self.db.add(EventOrganizer(event_id=event_id, user_id=user_id))
        await self.db.flush()

        logger.info("New co organizer added into table")
    

    @handle_db_errors("add_event_participant")  
    async def add_event_participant(self, user_id: UUID, event: Event):
            
        new_participant = EventParticipant(
                user_id = user_id,
                event_id = event.event_id
            )
        self.db.add(new_participant)
        await self.db.flush()

        logger.info(f"Event participant added into table")  
    
    @handle_db_errors("remove_event_participant") 
    async def remove_event_participant(self, event_participant: EventParticipant):
        
        await self.db.delete(event_participant)
        await self.db.flush()
        logger.info(f"Successfully removed participant {event_participant.user_id} from event {event_participant.event_id}")
    
    @handle_db_errors("remove_event_organizer")
    async def remove_event_organizer(self, event_id: UUID):

        event = await self.event_repo.get_event_by_id(event_id=event_id)
        
        if event.organizer_id:
            event.organizer_id = None
        
        await self.db.flush()
        logger.info(f"Organizer ID successfully removed")

    @handle_db_errors("remove_co_organizer") 
    async def remove_co_organizer(self, event_id: UUID, user_id: UUID):
                
        co_organizer = await self.ep_read_repo.get_event_co_organizer(event_id=event_id, user_id=user_id)

        if co_organizer is None:
            logger.warning(f"No co-organizer {user_id} found for event {event_id}")
            raise UserNotFoundException("No any co-organizer found")

        await self.db.delete(co_organizer)
        await self.db.flush()
        logger.info("Co-organizer removed successfully")
