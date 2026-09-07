from uuid import UUID
from src.db import *

# internal imports
from src.exception import (
    RedisConnectionException, 
    OTPExpiredException, 
    OTPRateLimitException,
    OTPVerificationException,
    CustomBaseException
) 
from src.core import settings, OtpManager


logger = logging.getLogger(__name__)

class RedisConnection:

    def __init__(self):
        self.redis_client = None

    # for async redis connection
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def connect(self):
        try:
            pool = ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0,
                decode_responses=True,
                username="default",
                password=settings.REDIS_PASSWORD,
                max_connections=10
            )

            self.redis_client = Redis(connection_pool=pool)
            await self.redis_client.ping()

            logger.info("Redis connection established")
        except Exception as e:
            logger.critical("Redis connection failed.", exc_info=True)
            raise RedisConnectionException()

    async def store_otp(self, email_id : str, otp : str, channel : str = "email"):
        try:
            hashed_otp = OtpManager.hash_otp(otp)
            await self.redis_client.setex(f"otp:{channel}:{email_id}", settings.OTP_EXPIRE_SECONDS, hashed_otp)
            logger.debug(f"OTP stored for {email_id} via {channel}, expires in 300s")
        except CustomBaseException:
            raise
        except Exception as e:
            logger.error(f"Redis connection error: {str(e)}", exc_info=True)
            raise RedisConnectionException()
                                               
    async def otp_verification_by_email(self, email: str, otp: str):
        try:
            if len(otp) != 6:
                raise ValueError("Otp should be not more than 6")

            channel = None
            hashed_otp = await self.redis_client.get(f"otp:mobile:{email}")
            if hashed_otp:
                channel = "mobile"
            else:
                hashed_otp = await self.redis_client.get(f"otp:email:{email}")
                if hashed_otp:
                    channel = "email"

            if not hashed_otp:
                logger.info("Otp is expired or not available")
                raise OTPExpiredException("OTP expired or not found!")
            
            is_valid = OtpManager.verify_otp(otp, hashed_otp)
            if not is_valid:
                raise OTPVerificationException("Invalid OTP provided")
            
            # Delete only the channel key that actually matched
            await self.redis_client.delete(f"otp:{channel}:{email}")

            return is_valid
        
        except CustomBaseException:
            raise
        except Exception as e:
            logger.error(f"Redis connection failed error: {str(e)}", exc_info=True)
            raise RedisConnectionException()
        
    async def save_otp_with_rate_limit(self, email_id : str, new_otp : str, channel: str = "email"):
        try:
            lock_acquired = await self.redis_client.set(f"otp_lock:{channel}:{email_id}", "1", nx=True, ex=settings.OTP_LOCK_SECONDS)
            if not lock_acquired:
                logger.warning(f"OTP rate limit hit for {email_id} on {channel}")
                raise OTPRateLimitException()
            await self.store_otp(email_id, new_otp, channel)
        except CustomBaseException:
            raise
        except Exception as e:
            logger.error(f"Redis connection failed  error: {str(e)}", exc_info=True)
            raise RedisConnectionException()
            
    async def blacklisted_expire_token(self, token):
        try:
            await self.redis_client.setex(f"blacklisted:{token}", settings.ACCESS_TOKEN_EXPIRES_MINUTES * 60, "1")
        except Exception as e:
            logger.error(f"Redis connection failed error: {str(e)}", exc_info=True)
            raise RedisConnectionException()

    async def is_token_blacklisted(self, token: str) -> bool:
        try:
            return await self.redis_client.exists(f"blacklisted:{token}") == 1
        except Exception as e:
            logger.error(f"Redis connection failed error: {str(e)}", exc_info=True)
            raise RedisConnectionException()
        
    async def set_expiration(self, id : UUID, data : str, ttl_seconds : int):
        try:
            return await self.redis_client.set(f"temp_face:{id}",
                                               data,
                                               ex=ttl_seconds  # TTL - Redis khud expire kar dega)
            )
        except Exception as e:
            logger.error(f"Redis connection failed error: {str(e)}", exc_info=True)
            raise RedisConnectionException()
    
    async def get_value(self, key: str):
        try:
            return await self.redis_client.getdel(key)
        except Exception as e:
            logger.error(f"Redis connection failed error: {str(e)}", exc_info=True)
            raise RedisConnectionException()
            
redisconnection = RedisConnection()
