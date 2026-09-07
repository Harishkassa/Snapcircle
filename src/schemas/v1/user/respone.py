from src.schemas.v1 import *

# schemas for login response containing user details and authentication token
class LoginResponse(BaseModel):
    username: str  # username of the logged-in user
    role_name: str  # Role assigned to the user
    access_token: str  # JWT access token
    token_type: str = "Bearer"  # Type of token (e.g., "Bearer")

    model_config = ConfigDict(from_attributes=True)

# schema for profile photo response
class ProfilePhotoResponse(BaseModel):
    profile_photo_id: UUID  # Unique identifier for the profile photo
    profile_photo_url: str  # URL to access the profile photo
    profile_photo_type : Literal["jpeg", "png"]  # MIME type of the photo (e.g., "image/jpeg")
    uploaded_at: datetime  # Timestamp of when the photo was uploaded

    model_config = ConfigDict(from_attributes=True)

class UserResponse(UserBase):
    user_id : UUID
    role_name : str = "User"
    profile_photo_id : Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)