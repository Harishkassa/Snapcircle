# Standard imports
import uuid6
from uuid import UUID
from time import timezone

# third party imports
from datetime import datetime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint, func, DateTime, Index, Boolean
from typing import Optional, List
from sqlalchemy.dialects.postgresql import JSONB

# internal imports
from src.models.user.register import UserRegister
from src.models.user.refresh_token import RefreshToken
from src.models.event.event_creation import Event
from src.models.event.event_photos import EventPhoto
from src.models.event.group_photos import GroupPhoto
from src.models.event.event_participants import EventParticipant
from src.models.event.event_organizer import EventOrganizer
from src.models.user.profile_photo import ProfilePhoto
from src.models.event.detected_faces import DetectedFace
