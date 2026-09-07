# standard library imports
import logging
# import aioredis
from redis.asyncio import Redis, ConnectionPool

# third party imports
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, registry
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from tenacity import retry, stop_after_attempt, wait_exponential
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase

# internal imports
from src.db.redis_connection import redisconnection
from src.db.database_connection import DatabaseConnection
from src.db.database_connection import db, Base
