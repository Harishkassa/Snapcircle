from src.models import *

# internal imports
from src.db import Base

class EventOrganizer(Base):
    __tablename__ = "event_organizers"

    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("events.event_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_register.user_id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Relationships
    event: Mapped["Event"] = relationship("Event", back_populates="co_organizers")
    user: Mapped["UserRegister"] = relationship("UserRegister", back_populates="event_organizers")