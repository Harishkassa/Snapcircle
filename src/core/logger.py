from src.core import *
from logging.handlers import RotatingFileHandler

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Define a strict production log format
LOG_FORMAT = "%(asctime)s - %(levelname)s [%(filename)s:%(lineno)d] - %(message)s"


def setup_logging():
    """Initializes centralized enterprise logging."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)   # logger khud sabse niche level pe rakho, taaki handlers filter karein

    # Clean existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    # 1. Console Handler (For Docker logs/Stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.LOG_LEVEL)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. Debug Log File (sirf DEBUG level ke logs)
    debug_handler = RotatingFileHandler(
        LOG_DIR / "debug.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
    debug_handler.setFormatter(formatter)
    logger.addHandler(debug_handler)

    # 3. Info Log File (sirf INFO level ke logs)
    info_handler = RotatingFileHandler(
        LOG_DIR / "info.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3
    )
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(lambda record: record.levelno == logging.INFO)
    info_handler.setFormatter(formatter)
    logger.addHandler(info_handler)

    # 4. Warning Log File (sirf WARNING level)
    warning_handler = RotatingFileHandler(
        LOG_DIR / "warning.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.addFilter(lambda record: record.levelno == logging.WARNING)
    warning_handler.setFormatter(formatter)
    logger.addHandler(warning_handler)

    # 5. Error Log File (ERROR aur usse upar — CRITICAL bhi)
    error_handler = RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)   # koi filter nahi, setLevel(ERROR) khud ERROR+CRITICAL allow karta hai
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    logger.info("Centralized logging system initialized successfully.")
    return logger

