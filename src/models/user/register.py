from src.models import *

# internal imports
from src.db import Base

class UserRegister(Base):
    __tablename__ = "user_register"
    
    user_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6.uuid7)
    username: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    gender: Mapped[str] = mapped_column(nullable=False)
    mobile_number: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    email_id: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(nullable=False)
    role_name: Mapped[str] = mapped_column(server_default="User", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


    __table_args__ = (
        CheckConstraint(r"username ~ '^[a-zA-Z0-9_]+$'", name="valid_username"),
        CheckConstraint(r"mobile_number ~ '^\d{10}$'", name="valid_mobile"),
        CheckConstraint(r"email_id ~ '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'", name="valid_email"),
    )

    profile_photo : Mapped["ProfilePhoto"] = relationship("ProfilePhoto", back_populates="user", cascade="all, delete-orphan", passive_deletes=True, uselist=False)  # One-to-one relationship with ProfilePhoto
    event : Mapped[list["Event"]] = relationship("Event", back_populates="organizer")  # One-to-many
    event_photos : Mapped[list["EventPhoto"]] = relationship("EventPhoto", back_populates="uploader")  # One-to-many
    event_participants : Mapped[list["EventParticipant"]] = relationship("EventParticipant", back_populates="user")  # One-to-many
    event_organizers: Mapped[list["EventOrganizer"]] = relationship("EventOrganizer", back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def profile_photo_id(self) -> Optional[UUID]:
        return self.profile_photo.photo_id if self.profile_photo else None