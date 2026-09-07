from src.models import *

# internal imports
from src.db import Base

class Event(Base):
    __tablename__ = "events"

    event_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6.uuid7)
    event_name: Mapped[str] = mapped_column(nullable=False, index=True)
    description: Mapped[str] = mapped_column(nullable=False)
    location: Mapped[str] = mapped_column(nullable=False, index=True)
    date: Mapped[datetime] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    total_media: Mapped[int] = mapped_column(default=0, nullable=False)
    total_members: Mapped[int] = mapped_column(default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    # Foreign Keys
    organizer_id: Mapped[UUID] = mapped_column(ForeignKey("user_register.user_id", ondelete="CASCADE"), nullable=True)
    
    __table_args__ = (
        CheckConstraint(r"event_name ~ '^[A-Za-z ]+$'", name="valid_event_name"),
        CheckConstraint(r"location ~ '^[A-Za-z ]+$'", name="valid_location"),
        CheckConstraint("total_media >= 0", name="valid_total_media"),
        CheckConstraint("total_members >= 1", name="valid_total_members"),
    )

    # Relationships
    organizer: Mapped["UserRegister"] = relationship("UserRegister", back_populates="event")
    group_photo: Mapped[Optional["GroupPhoto"]] = relationship("GroupPhoto", back_populates="event", cascade="all, delete-orphan", passive_deletes=True, uselist=False)
    participants: Mapped[list["EventParticipant"]] = relationship("EventParticipant", back_populates="event", cascade="all, delete-orphan", passive_deletes=True)
    event_photos: Mapped[list["EventPhoto"]] = relationship("EventPhoto", back_populates="event")
    co_organizers: Mapped[list["EventOrganizer"]] = relationship("EventOrganizer", back_populates="event")
    
    @property
    def group_photo_id(self) -> Optional[UUID]:
        return self.group_photo.group_photo_id if self.group_photo else None