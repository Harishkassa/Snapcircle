from src.init import *

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
 
from src.repository.user import UserRepository
from src.repository.event import (
    EventRepository,
    EventParticipantReadRepository,
    EventParticipantWriteRepository,
)
from src.db import db

from src.services.v1 import UserService, EventService, EmailService
 
async def get_user_repo(session: AsyncSession = Depends(db.get_db)) -> UserRepository:
    return UserRepository(db=session)

async def get_event_repo(session: AsyncSession = Depends(db.get_db)) -> EventRepository:
    return EventRepository(db=session)

async def get_event_participant_read_repo(session: AsyncSession = Depends(db.get_db)) -> EventParticipantReadRepository:
    return EventParticipantReadRepository(db=session)

async def get_event_participant_write_repo(session: AsyncSession = Depends(db.get_db)) -> EventParticipantWriteRepository:
    ep_read_repo = EventParticipantReadRepository(db=session)
    event_repo = EventRepository(db=session)
    return EventParticipantWriteRepository(db=session, ep_read_repo=ep_read_repo, event_repo=event_repo)

def get_email_service() -> EmailService:
    return EmailService()

async def get_user_service(
    repo: UserRepository = Depends(get_user_repo),
    email_service: EmailService = Depends(get_email_service),
) -> UserService:
    return UserService(user_repo=repo, email_service=email_service)

async def get_event_service(
    event_repo: EventRepository = Depends(get_event_repo),
    ep_read_repo: EventParticipantReadRepository = Depends(get_event_participant_read_repo),
    ep_write_repo: EventParticipantWriteRepository = Depends(get_event_participant_write_repo),
) -> EventService:
    return EventService(
        event_repo=event_repo,
        ep_read_repo=ep_read_repo,
        ep_write_repo=ep_write_repo,
    )