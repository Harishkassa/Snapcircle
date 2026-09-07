from src.schemas.v1 import * 
 
# Schema for EventBase
class EventBase(BaseModel):
    event_name: str = Field(..., max_length=30, pattern="^[A-Za-z ]+$") # Unique event name required to join an event
    location : str = Field(..., max_length=100, pattern="^[A-Za-z ]+$") # Location of the event
    date : datetime = Field(..., description="Date of the event") # Date and time of the event

# Schema for EventPhotosBase
class EventPhotosBase(BaseModel):
    event_id : UUID   