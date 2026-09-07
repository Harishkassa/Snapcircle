from src.schemas.v1 import *

# Response schema for group photos
class GroupPhotosResponse(BaseModel):
    group_photo_id: UUID  # Group ID
    photo_url: str  # URL of the uploaded photo
    uploaded_at: datetime  # Timestamp of when the photo was uploaded

    # Enable Orm support , Configdict : dict like configuration object
    model_config = ConfigDict(from_attributes=True)

# Schema for event response
class EventResponse(EventBase):
    event_id: UUID  # Unique event identifier
    organizer_id: Optional[UUID] = None  # id of the event organizer
    code: str  # Event code
    group_photo_id: Optional[UUID] = None  # Optional group photo id

    model_config = ConfigDict(from_attributes=True)  # Config to map attributes from ORM

# Response schema for event photos
class EventPhotosResponse(EventPhotosBase):
    event_photo_id: UUID
    user_id: UUID
    event_name: str
    photo_url: str
    uploaded_at: datetime

    # Configuration for model serialization
    model_config = ConfigDict(from_attributes=True)

# Joined Events Response Schema
class JoinedEventsResponse(BaseModel):
    organizer_id: UUID
    event_name: str
    code : str

    model_config = ConfigDict(from_attributes=True)

class EventOrganizerResponse(BaseModel):
    event_id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class EventParticipantResponse(BaseModel):
    participant_id: UUID
    event_id: UUID
    user_id: UUID

    model_config = ConfigDict(from_attributes=True) 