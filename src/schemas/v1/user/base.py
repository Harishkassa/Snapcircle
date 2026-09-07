from src.schemas.v1 import *

class UserBase(BaseModel):
    username : str = Field(..., min_length=8, max_length=15, pattern=r"^[a-zA-Z0-9_]+$") # Alphanumeric and underscore allowed
    email_id : EmailStr = Field(..., description="User's email address") # Valid email format enforced with desc
    mobile_number: str = Field(..., pattern=r"^\d{10}$")  # Must be a 10-digit number

