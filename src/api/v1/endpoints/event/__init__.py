import json

# Standard Library
from uuid import UUID
from typing import List

# Third Party
from fastapi import Depends, HTTPException, UploadFile, APIRouter, Body, Query, Path, Request, Form
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dependency_injector.wiring import inject, Provide, Closing
from fastapi.security import HTTPAuthorizationCredentials