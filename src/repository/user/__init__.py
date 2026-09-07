import logging
import os
import shutil
import secrets

from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import select
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

# internal imports
from src.repository.user.user_repository import UserRepository