from src.exception.base_connection import CustomBaseException

# conn related
class DatabaseConnectionException(CustomBaseException):
    """Triggered when DB connections fail or pool starves."""
    def __init__(self, message = "Database connection failure occurred."):
        super().__init__(message, status_code = 503)

class RedisConnectionException(CustomBaseException):
    def __init__(self, message = "Redis failed connection error occured."):
        super().__init__(message, status_code = 503)
