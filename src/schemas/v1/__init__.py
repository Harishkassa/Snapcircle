# standard library import
import re
import uuid6

#  third party imports
from typing import Literal, Optional
from fastapi import Form
from pydantic import ConfigDict, BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from uuid import UUID

# internal imports
from src.schemas.v1.user.base import UserBase
from src.schemas.v1.user.respone import UserResponse, LoginResponse, ProfilePhotoResponse
from src.schemas.v1.user.create import UserCreate
from src.schemas.v1.user.login import LoginRequest, OtpVerification, ResendOtpTemp
from src.schemas.v1.event.base import EventBase, EventPhotosBase
from src.schemas.v1.event.response import EventResponse, EventPhotosResponse, JoinedEventsResponse, EventParticipantResponse
from src.schemas.v1.user.update import UserUpdate, UpdateProfilePhoto, UserUpdatePassword
from src.schemas.v1.event.create import EventCreate, EventJoin
from src.schemas.v1.event.update import EventUpdate
from src.schemas.v1.user.face import FaceSession

