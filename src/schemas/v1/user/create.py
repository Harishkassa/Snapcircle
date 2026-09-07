from src.schemas.v1 import *

class UserCreate(UserBase):
    gender: Literal["Male", "Female", "Other"]  # Restricting to specific choices
    password: str = Field(..., min_length=8, max_length=50)  # Password length constraints
    temp_face_id: UUID

    # gender field upper to lower case conversion
    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, v):
        return v.capitalize() # "Male" → "male" automatically
    
    # Password complexity validation using regex
    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v):
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one capital letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[@$!%*?&]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


