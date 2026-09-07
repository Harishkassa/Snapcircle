from src.models import *

# internal imports
from src.db import Base

class DetectedFace(Base):
    __tablename__ = "detected_faces"

    detected_face_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6.uuid7)
    embedding: Mapped[list[float]] = mapped_column(JSONB, nullable=False)
    matched_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("user_register.user_id", ondelete="SET NULL"), nullable=True, index=True
    )
    # facial_area: Mapped[dict] = mapped_column(JSONB, nullable=True)  # {"x1":.., "y1":.., "x2":.., "y2":..}
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Foreign Key
    event_photo_id: Mapped[UUID] = mapped_column(
        ForeignKey("event_photos.event_photo_id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    event_photos: Mapped["EventPhoto"] = relationship("EventPhoto", back_populates="detect_faces")