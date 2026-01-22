"""
Logging configuration for the application.
Provides structured logging with JSON format support.
"""
import logging
import sys
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    if settings.LOG_FORMAT == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]

    logging.getLogger("uvicorn.access").handlers = []


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
