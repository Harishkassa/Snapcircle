from src.exception import *

# S3 related
class S3ClientInitException(CustomBaseException):
    def __init__(self, message= "S3 client intialization failed."):
        super().__init__(message, status_code= 503)

class S3StorageException(CustomBaseException):
    """Triggered when file uploads or AWS operations fail."""
    def __init__(self, message = "S3 Storage failed upload object file."):
        super().__init__(message, status_code = 502)
