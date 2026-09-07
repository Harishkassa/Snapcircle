from src.schemas.v1 import *

# Schema for event creation
class EventCreate(EventBase):
    description: str = Field(..., min_length=5, max_length=500)  # Description length constraints

    @classmethod
    def as_form(
        cls,
        event_name: str = Form(..., max_length=30, pattern="^[A-Za-z ]+$"),
        location: str = Form(..., max_length=100, pattern="^[A-Za-z ]+$"),
        date: datetime = Form(..., description="Date of the event"),
        description: str = Form(..., min_length=5, max_length=500),
    ) -> "EventCreate":
        return cls(
            event_name=event_name,
            location=location,
            date=date,
            description=description,
        )
    
# Schema for event photos creation
class EventPhotosCreate(EventPhotosBase):
    pass

# Model for event members, extending JoinedEventsResponse
class EventParticipants(JoinedEventsResponse):
    event_id : Optional[UUID]  # Optional event identifier
    username: Optional[str]  # Optional username field

# Schema for event join request
class EventJoin(BaseModel):
    event_code: str = Field(..., max_length=30, pattern=r"^[a-z]{4}-[a-z]{4}-[a-z]{4}$")  # Event code with validation

class EventOrganizerAdd(BaseModel):
    user_id: UUID