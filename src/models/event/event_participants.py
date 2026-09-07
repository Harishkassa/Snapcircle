from src.models import *

# internal imports
from src.db import Base

class EventParticipant(Base):
    __tablename__ = "event_participants"

    # Primary Key
    participant_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6.uuid7)

    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user_register.user_id", ondelete="CASCADE"), nullable=False, index=True)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.event_id", ondelete="CASCADE"), nullable=False, index=True)

    # Timestamp
    joined_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["UserRegister"] = relationship("UserRegister", back_populates="event_participants")
    event: Mapped["Event"] = relationship("Event", back_populates="participants")