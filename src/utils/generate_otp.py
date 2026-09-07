from src.utils import *
from src.exception import FailedOtpGeneration

class GenerateOtp:
    try:
        """Generate random Otp"""
        @staticmethod
        def generate_otp():
            return str(secrets.randbelow(900000) + 100000)
    except Exception as e:
        raise FailedOtpGeneration() from e