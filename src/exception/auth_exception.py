from src.exception import *

# Otp related
class FailedOtpGeneration(CustomBaseException):
    """Triggered when Otp generation is failed"""
    def __init__(self, message = "Otp generation failed"):
        super().__init__(message, status_code=500)

class OTPVerificationException(CustomBaseException):
    """Triggerd when otp verification failed"""
    def __init__(self, message = "Failed to verify the otp"):
        super().__init__(message, status_code = 500)

class OTPHashingException(CustomBaseException):
    """Triggered when otp hashing failed"""
    def __init__(self, message = "Unable to hash the otp"):
        super().__init__(message, status_code = 500)

class OTPRateLimitException(CustomBaseException):
    def __init__(self, message = "You already got an email please check!"):
        super().__init__(message, status_code = 400)

class OTPExpiredException(CustomBaseException):
    def __init__(self, message = "Otp already expired or not available"):
        super().__init__(message, status_code = 410)

# Password related
class PasswordHashingException(CustomBaseException):
    """Triggered when pwd hashing failed"""
    def __init__(self, message = "Failed to hashing the password"):
        super().__init__(message, status_code = 500)

class PasswordVerificationException(CustomBaseException):
    """Triggered when pwd verification failed"""
    def __init__(self, message = "Failed to verify the password"):
        super().__init__(message, status_code = 500)

# Jwt related
class JWTVerificationfailedException(CustomBaseException):
    """Triggered when jwt token verification failed"""
    def __init__(self, message= "Failed to verify the jwt token"):
        super().__init__(message, status_code = 401)

class JWTCreationfailedException(CustomBaseException):
    """Triggered when jwt token creation failed"""
    def __init__(self, message = "Unable to create the Jwt token, token creation failed:"):
        super().__init__(message, status_code = 401)

# Email related
class EmailDeliveryException(CustomBaseException):
    """Triggered when email sending operations fail."""
    def __init__(self, message = "Email delivery connection failed"):
        super().__init__(message, status_code = 502)

class EmailException(CustomBaseException):
    """Triggered when wrong request we get."""
    def __init__(self, message = "Failed to send email."):
        super().__init__(message, status_code = 400)

# SMS related
class SMSDeliveryException(CustomBaseException):
    """Triggered when sms sending operations fail (transient, retry-worthy)."""
    def __init__(self, message = "SMS delivery connection failed"):
        super().__init__(message, status_code = 502)

class SMSException(CustomBaseException):
    """Triggered when sms request itself is bad (invalid number, missing creds - don't retry)."""
    def __init__(self, message = "Failed to send sms."):
        super().__init__(message, status_code = 400)

class MissingRefreshToken(CustomBaseException):
    """Triggered when Refresh token is missing"""
    def __init__(self, message = "Missing refresh token."):
        super().__init__(message, status_code = 401)

class InvalidRefreshToken(CustomBaseException):
    """Triggered when Refresh token is invalid"""
    def __init__(self, message = "Invalid refresh token."):
        super().__init__(message, status_code = 401)

class ExpiredRefreshToken(CustomBaseException):
    """Triggered when Refresh token is expired"""
    def __init__(self, message = "Expired refresh token."):
        super().__init__(message, status_code = 401)


