# Standard imports
import os
import random
import shutil
import logging

# third party imports
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload


# internal imports
from src.repository.event.event_participant_read_repository import EventParticipantReadRepository
from src.repository.event.event_participant_write_repository import EventParticipantWriteRepository
from src.repository.event.event_repository import EventRepository