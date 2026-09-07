from src.schemas.v1 import *

class UserUpdate(BaseModel):
    new_username: str = Field(..., min_length=8, max_length=15, pattern=r"^[a-zA-Z0-9_]+$")

class UpdateProfilePhoto(BaseModel):
    temp_face_id: UUID

class UserUpdatePassword(BaseModel):
    email_id : EmailStr = Field(..., description="User's email address") # Valid email format enforced with desc
    otp : Optional[str] = None
    new_password : Optional[str] = None
