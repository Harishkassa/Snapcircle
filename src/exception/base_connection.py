
# Base exception class
class CustomBaseException(Exception):
    """Base exception class for our enterprise application."""
    def __init__(self, message : str, status_code : int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)