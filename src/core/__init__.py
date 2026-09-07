# standard library imports
import logging
import logging.handlers
import sys
import bcrypt
import boto3
import jwt
import hashlib

# third party imports
from fastapi import FastAPI, Request, Depends, HTTPException, status
from pydantic import PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from botocore.config import Config
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt


# internal imports
from src.core.config import settings
from src.core.logger import setup_logging
from src.core.security import OtpManager, PasswordManager, JWTManager