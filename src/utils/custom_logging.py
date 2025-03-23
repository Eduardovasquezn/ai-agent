import logging
import logging.config
import logging.handlers
import os

from src.config import settings

log_dir = os.path.join(os.path.dirname(__file__), "../../logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.log_level,
            "formatter": "detailed",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": settings.log_file,
            "maxBytes": 1000000,
            "backupCount": 3,
            "level": "DEBUG",
            "formatter": "detailed",
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["console", "file"],
    },
}


def setup_logging():
    logging.config.dictConfig(LOG_CONFIG)
