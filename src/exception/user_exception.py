from src.exception import *

# User related
class UserNotFoundException(CustomBaseException):
    def __init__(self, message = "User not found"):
        super().__init__(message, status_code = 404)

class UserAlreadyExistsException(CustomBaseException):
    def __init__(self, message = "User already exists!"): 
        super().__init__(message, status_code = 409)

class UserNotAuthenticated(CustomBaseException):
    """Triggered when user is not authenticated"""
    def __init__(self, message = "Not authenticate please login"):
        super().__init__(message, status_code=401)

class UserUnauthorizedException(CustomBaseException):
    """Triggered when user unauthorized"""
    def __init__(self, message = "Server understands the request but refuses to authorize it."):
        super().__init__(message, status_code = 403)

class InvalidCredentialsException(CustomBaseException):
    """Triggered when credentials is not valid"""
    def __init__(self, message = "invalid Credentials"):
        super().__init__(message, status_code=400)

class ProfilePhotoNotFound(CustomBaseException):
    """Triggered when profile photo is not found"""
    def __init__(self, message = "Profile photo not found"):
        super().__init__(message, status_code=404)

class FaceExpiredException(CustomBaseException):
    """Triggered when img byes not found"""
    def __init__(self, message = "face may expired or not found"):
        super().__init__(message, status_code=400)