from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dependency_injector import containers, providers
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler