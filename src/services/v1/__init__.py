# Standard Library
import logging
import random
import string
import smtplib
import asyncio
import os
import shutil
import numpy as np
import cv2
import base64

# third party imports
from fastapi import HTTPException, Depends, UploadFile, Response, Cookie
from io import BytesIO
from datetime import datetime, timedelta, timezone
from PIL import Image
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from celery import Celery, group, shared_task
from uuid6 import uuid
import uuid6
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Literal, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from sqlalchemy.orm import Session
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi.concurrency import run_in_threadpool
from insightface.app import FaceAnalysis
from retinaface import RetinaFace
from asgiref.sync import async_to_sync


# internal imports
from src.services.v1 import embedding_service 
from src.services.v1.email_service import EmailService, celery_app
from src.services.v1.event_service import EventService
from src.services.v1.user_service import UserService
from src.services.v1.auth_service import get_current_user, http_bearer
from src.services.v1.sms_service import SMSService, send_sms_task
from src.services.v1.face_service import (
    decode_frame,
    resize_frame,
    select_largest_face,
    is_face_big_enough,
    crop_face,
    sharpness_score,
    save_best_frame,
    build_feedback,
)