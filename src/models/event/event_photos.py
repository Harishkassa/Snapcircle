from src.models import *

# internal imports
from src.db import Base

class EventPhoto(Base):
    __tablename__ = "event_photos"

    event_photo_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6.uuid7)
    photo_url: Mapped[str] = mapped_column(nullable=False)
    photo_type: Mapped[str] = mapped_column(nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Foreign Keys
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_user_id: Mapped[UUID] = mapped_column(ForeignKey("user_register.user_id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="event_photos")
    uploader: Mapped["UserRegister"] = relationship("UserRegister", back_populates="event_photos")
    detect_faces: Mapped["DetectedFace"] = relationship("DetectedFace", back_populates="event_photos", cascade="all, delete-orphan", passive_deletes=True)
