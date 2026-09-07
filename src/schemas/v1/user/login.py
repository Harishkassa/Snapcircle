from src.schemas.v1 import *

# schema for user login request
class LoginRequest(BaseModel):
    identifier: str = Field(..., description="User identifier (username or email)")
    password: str = Field(..., description="User password")

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, value):
        if re.match(r"^[a-zA-Z0-9_]{8,15}$", value):
            return value  # Valid username
        elif re.match(r"^[\w\.-]+@[\w\.-]+\.(com|in|org)$", value):
            return value  # Valid email
        else:
            raise ValueError("Identifier must be a valid username or email address")
        
# schemas for OTP verification request
class OtpVerification(BaseModel):
    email_id: EmailStr = Field(..., description="User's email address")
    otp: str = Field(..., description="OTP code for verification")

class ResendOtpTemp(BaseModel):
    email_id: EmailStr = Field(..., description="User's email address") # Valid email format enforced with desc