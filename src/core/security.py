from src.core import *

# internal imports
from src.exception import (PasswordHashingException,
                           UserUnauthorizedException,
                           PasswordVerificationException,
                           OTPHashingException,
                           OTPVerificationException,
                           JWTCreationfailedException,
                           JWTVerificationfailedException)

logger = logging.getLogger(__name__)

class PasswordManager:
    """Handles password hashing and verification."""
    
    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    def hash(password: str) -> str:
        try:
            hashed = PasswordManager._pwd_context.hash(password)
            logger.info("Password hashed successfully")
            return hashed
        except Exception as e:
            logger.error(f"Password hashing error: {str(e)}", exc_info=True)
            raise PasswordHashingException()

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        try:
            result = PasswordManager._pwd_context.verify(plain_password, hashed_password)
            logger.info("Password verification completed")
            return result
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}", exc_info=True)
            raise PasswordVerificationException()
        
class OtpManager:
    @staticmethod
    def hash_otp(otp: str) -> str:
        try:
            return bcrypt.hashpw(otp.encode(), bcrypt.gensalt()).decode()
        except Exception as e:
            logger.error(f"OTP hashing error: {str(e)}", exc_info=True)
            raise OTPHashingException()

    @staticmethod
    def verify_otp(otp: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(otp.encode(), hashed.encode())
        except Exception as e:
            logger.error(f"OTP verification error: {str(e)}", exc_info=True)
            raise OTPVerificationException("Otp verification process failed or temporary crashed")

class JWTManager:
    """Handles JWT token creation and verification."""

    @staticmethod
    def create_access_token(data: dict) -> str:
        try:
            to_encode = data.copy()
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=int(settings.ACCESS_TOKEN_EXPIRES_MINUTES)
            )
            to_encode.update({"exp": expire})
            logger.info("Access token created")
            return jwt.encode(to_encode, settings.SECURITY_KEY, algorithm=settings.ALGORITHM)
        except Exception as e:
            logger.error(f"JWT creation failed: {str(e)}", exc_info=True)
            raise JWTCreationfailedException()

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.SECURITY_KEY, algorithms=[settings.ALGORITHM])
            logger.info("Token verification completed")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise UserUnauthorizedException("Token has expired, please login again")

        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token attempt: {e}", exc_info=True)
            raise JWTVerificationfailedException()

    @staticmethod  
    def hash_token(raw_token: str) -> str:
    # SHA-256 is fine here (we're hashing a high-entropy random token,
    # not a low-entropy password, so no need for bcrypt's slowness)
        return hashlib.sha256(raw_token.encode()).hexdigest()