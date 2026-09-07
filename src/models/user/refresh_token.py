from src.models import *

# internal imports
from src.db import Base


class RefreshToken(Base):
    """
    Stores a HASH of the refresh token, never the raw value.
    `family_id` links all tokens issued from the same original login,
    so we can revoke the whole chain on reuse detection.
    """
    __tablename__ = "refresh_tokens"
 
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid6.uuid7)
    token_hash: Mapped[str] = mapped_column(unique=True, index=True)
 
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("user_register.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
 
    family_id: Mapped[str] = mapped_column(nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
 
    # relationship back to the user
    user: Mapped["UserRegister"] = relationship(back_populates="refresh_tokens")