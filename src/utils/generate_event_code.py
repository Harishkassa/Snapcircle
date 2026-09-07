from src.utils import *
from src.exception import FailedEventCodeGeneration

class GenerateEventCode:
    try:
        """Generate the random event code"""
        @staticmethod    
        def generate_event_code():
            parts =  ["".join(random.choices(string.ascii_lowercase, k=4)) for _ in range(3)]
            return "-".join(parts)
    except Exception as e:
        raise FailedEventCodeGeneration