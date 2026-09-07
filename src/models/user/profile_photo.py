from src.models import *

# internal imports
from src.db import Base

# Model for profile photo
class ProfilePhoto(Base):
    __tablename__ = "profile_photo"

    photo_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6.uuid7)
    photo_url: Mapped[str] = mapped_column(nullable=False)
    photo_type: Mapped[str] = mapped_column(nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    embedding: Mapped[list[float]] = mapped_column(JSONB, nullable=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user_register.user_id", ondelete="CASCADE"), nullable=False, unique=True)

    user: Mapped["UserRegister"] = relationship("UserRegister", back_populates="profile_photo")  # One-to-one relationship with UserRegister
