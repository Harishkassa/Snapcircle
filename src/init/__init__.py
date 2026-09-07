# di_container.py imports


# third party imports
from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession
from dependency_injector.wiring import Closing, inject, Provide
from fastapi import Depends

# internal imports
# from src.init.di_containers import Container, container
from src.init.dependencies import get_user_service, get_event_service