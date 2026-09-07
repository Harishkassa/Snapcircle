from src.models import *

# internal imports
from src.db import Base

class GroupPhoto(Base):
    __tablename__ = "group_photos"

    group_photo_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6.uuid7)
    photo_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # FK — child hai Event ka
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, unique=True)

    # Relationship
    event: Mapped["Event"] = relationship("Event", back_populates="group_photo")