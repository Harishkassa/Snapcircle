import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from functools import wraps


from src.exception.base_connection import CustomBaseException

from src.exception.conn_exception import (
    DatabaseConnectionException,
    RedisConnectionException
)

from src.exception.custom_exception import register_exception_handlers, handle_db_errors


from src.exception.auth_exception import (
    JWTCreationfailedException, 
    JWTVerificationfailedException,
    OTPRateLimitException, 
    OTPExpiredException,
    OTPHashingException,
    OTPVerificationException,
    PasswordHashingException,
    PasswordVerificationException,
    FailedOtpGeneration,
    EmailDeliveryException,
    EmailException,
    SMSDeliveryException,
    SMSException,
    MissingRefreshToken,
    InvalidRefreshToken,
    ExpiredRefreshToken
)


from src.exception.event_exception import(EventNotFoundException,
                                          JoinedNotFoundException,
                                          FailedEventCodeGeneration,
                                          UnabletoRemovememberException)

from src.exception.s3_exception import (S3ClientInitException,
                                        S3StorageException)

from src.exception.user_exception import (UserAlreadyExistsException,
                                          UserNotAuthenticated,
                                          UserNotFoundException,
                                          ProfilePhotoNotFound,
                                          FaceExpiredException,
                                          UserUnauthorizedException,
                                          InvalidCredentialsException)
