# Standard Library
import base64
import logging
import cv2
import uuid6

from uuid import UUID
from typing import List, Optional

# Third Party
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, UploadFile, APIRouter, Body, Request, Depends, Query, Path, Cookie, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dependency_injector.wiring import inject, Provide, Closing
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.concurrency import run_in_threadpool
from retinaface import RetinaFace