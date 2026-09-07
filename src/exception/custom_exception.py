from src.exception.base_connection import CustomBaseException
from src.exception.conn_exception import DatabaseConnectionException

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps

logger = logging.getLogger(__name__)


def handle_db_errors(operation_name: str):
    """
    Wraps a repo method with standard DB error handling:
    - Known/custom exceptions (UserNotFoundException, PasswordHashingException, etc.)
      are passed through as-is.
    - Unexpected SQLAlchemy errors are rolled back, logged, and wrapped
      into a generic DatabaseConnectionException.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            
            try:
                return await func(self, *args, **kwargs)
            except CustomBaseException:
                await self.db.rollback()
                # Known business/domain error — don't touch it, let it bubble up
                raise
            except SQLAlchemyError as e:
                # Real DB failure — clean up the session and wrap it
                await self.db.rollback()
                logger.error(f"DB error in {operation_name}: {str(e)}", exc_info=True)
                raise DatabaseConnectionException() from e
        return wrapper
    return decorator


def register_exception_handlers(app : FastAPI):

    """Binds exception catchers to the FastAPI application instance."""
    @app.exception_handler(CustomBaseException)
    async def customer_exception_handler(request : Request, exc : CustomBaseException):
        logger.error(f"Application error on {request.url.path} : {exc.message}", exc_info=True)
        return JSONResponse(
            status_code=exc.status_code,
            content={"Success": False, "error": exc.message}    
        )
        
    """Captures unexpected system-level crashes safely without leaking code traces to public"""
    @app.exception_handler(Exception)
    async def global_unhandled_exception_handler(request : Request, exc : Exception):
        logger.error(f"Unhandled System Crash on {request.url.path} : {str(exc)}", exc_info=True)               
        return JSONResponse(
            status_code=500,
            content={"Success" : False, "error": "Internal server error. Please try after some time."}
        )
    