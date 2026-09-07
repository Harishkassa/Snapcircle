from src.repository.event import *

# internal imports
from src.models import (
    Event, 
    EventParticipant, 
    EventPhoto,
    GroupPhoto,
    DetectedFace,
    ProfilePhoto
)
from src.exception import (
    EventNotFoundException,
    handle_db_errors
)

from src.schemas.v1 import EventCreate

logger = logging.getLogger(__name__)

class EventRepository:

    def __init__(self, db : Session):
        self.db = db

    async def create_event(self, create_event_data: EventCreate, event_code, organizer_id):

        new_event = Event(
            event_name=create_event_data.event_name,
            description=create_event_data.description,
            location=create_event_data.location,
            date=create_event_data.date,
            code=event_code,
            organizer_id=organizer_id
        )

        self.db.add(new_event)
        await self.db.flush()
        await self.db.refresh(new_event)

        logger.info(f"New Event added into Event table")  

        return new_event

    @handle_db_errors("add_group_photo")
    async def add_group_photo(self, photo_url, new_event):

        new_groupphoto = GroupPhoto(
                photo_url=photo_url,
                event_id=new_event.event_id
            )
        self.db.add(new_groupphoto)
        await self.db.flush()

        logger.info(f"New Group Photo added into table")  

        await self.db.refresh(new_event, attribute_names=["group_photo"])

        return new_groupphoto

    @handle_db_errors("get_event_by_id")  
    async def get_event_by_id(self, event_id : UUID):
        
        stmt = (select(Event)
                .options(selectinload(Event.group_photo))
                .where(Event.event_id == event_id))
        event = (await self.db.scalars(stmt)).first() 

        if not event:
            logger.warning(f"Event {event_id} not found")
            raise EventNotFoundException(f"Event {event_id} not found")

        logger.info(f"Event {event_id} fetched")
        return event
        
    @handle_db_errors("get_event_by_code")  
    async def get_event_by_code(self, code: str):
        
        stmt = select(Event).where(Event.code == code)
        event = (await self.db.scalars(stmt)).first() 

        if not event:
            logger.warning(f"Event with code {code} not found")
            raise EventNotFoundException(f"Event {code} not found")

        logger.info(f"Event {code} fetched")
        return event
        
    @handle_db_errors("get_all")  
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Event]:

        stmt = (select(Event)
        .options(selectinload(Event.group_photo))
        .offset(skip)
        .limit(limit)
        .order_by(Event.updated_at.desc()))

        events = list((await self.db.scalars(stmt)).all())

        return events

    @handle_db_errors("get_event_by_name")  
    async def get_event_by_name(self, event_name : str, user_id : UUID) -> list[Event]:
    
        # Modern SQLAlchemy 2.0 Pattern matching your template
        stmt = (select(Event)
                .join(EventParticipant, EventParticipant.event_id == Event.event_id)
                .options(selectinload(Event.group_photo))
                .where(Event.event_name.ilike(f"%{event_name}%"), EventParticipant.user_id == user_id).limit(10))
                
        result = (await self.db.scalars(stmt))
        events = list(result.all())
            
        if not events:
            logger.warning(f"Event {event_name} is not found for user {user_id}")
            raise EventNotFoundException(f"Event {event_name} is not found")
        logger.info(f"Events with name '{event_name}' fetched")
        return events
        
    @handle_db_errors("update_event")  
    async def update_event(self, event: Event, new_event_name: str, new_description: str) -> Event:
        
        if new_event_name:
            event.event_name = new_event_name
        if new_description:
            event.description = new_description
        await self.db.flush()
        logger.info(f"Event {event.event_id} successfully updated")
        
    @handle_db_errors("delete_event")  
    async def delete_event(self, event: Event) -> None:
        
        await self.db.delete(event)
        await self.db.flush()
        logger.info(f"Successfully deleted Event {event.event_id}")
            
    @handle_db_errors("insert_event_photo")
    async def insert_event_photo(self, event_id, user_id, photo_url, photo_type):

        new_event_photo = EventPhoto(
            event_id=event_id,
            uploaded_user_id=user_id,
            photo_url=photo_url,
            photo_type=photo_type
        )
        self.db.add(new_event_photo)
        await self.db.flush()
        await self.db.refresh(new_event_photo)

        logger.info("Event photos added into table succesfully")
        return new_event_photo
    
    @handle_db_errors("get_event_photos_by_event_id")
    async def get_event_photos_by_event_id(self, event_id):

        stmt = (select(EventPhoto).where(EventPhoto.event_id == event_id))
        event_photos = list((await self.db.scalars(stmt)).all())

        logger.info("Event photos fetched by event id succesfully")
        return event_photos

    @handle_db_errors("insert_detected_face")
    async def insert_detected_face(self, event_photo_id, embedding, matched_user_id):

        new_photo_detetcted_face = DetectedFace(
            embedding=embedding,
            matched_user_id=matched_user_id,
            event_photo_id=event_photo_id
        )
        self.db.add(new_photo_detetcted_face)
        
        logger.info("Save detected face added into Detected face table")
        await self.db.flush()

    @handle_db_errors("get_all_embeddings_for_event")
    async def get_all_embeddings_for_event(self, event_id: UUID) -> list[tuple[UUID, list[float]]]:
        """
        Fetches (user_id, embedding) pairs for every user registered/participating
        in this event, joining through ProfilePhoto for the embedding.

        ADJUST: replace EventParticipant with your actual participant/registration
        model name and the correct join condition.
        """
        stmt = (
            select(ProfilePhoto.user_id, ProfilePhoto.embedding)
            .join(EventParticipant, EventParticipant.user_id == ProfilePhoto.user_id)
            .where(
                EventParticipant.event_id == event_id,
                ProfilePhoto.embedding.isnot(None),
            )
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [(row.user_id, row.embedding) for row in rows]