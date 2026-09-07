from src.schemas.v1 import *  

# Schema for event update request
class EventUpdate(BaseModel):
    # event_name: str = Field(..., max_length=30, pattern="^[A-Za-z ]+$")  # Event name with validation
    new_event_name: Optional[str] = Field(None, max_length=50, pattern="^[A-Za-z ]+$")  # Optional new event name
    new_description: Optional[str] = Field(None, min_length=5, max_length=500)  # Description length constraints