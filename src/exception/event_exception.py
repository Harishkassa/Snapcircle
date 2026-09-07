from src.exception import *

# Event related
class JoinedNotFoundException(CustomBaseException):
    """Triggered when no any joined events"""
    def __init__(self, message = "No any joined events found please join the event."):
        super().__init__(message, status_code = 404)

class EventNotFoundException(CustomBaseException):
    def __init__(self, message = "Event is not found"):
        super().__init__(message, status_code=404)

class FailedEventCodeGeneration(CustomBaseException):
    """Triggered when event code generation is failed"""
    def __init__(self, message = "Event code generation failed"):
        super().__init__(message, status_code=500)

class UnabletoRemovememberException(CustomBaseException):
    """Triggered when unable to remove participant from event"""
    def __init__(self, message = "Unable to remove event participant"):
        super().__init__(message, status_code=500)

