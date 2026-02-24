"""
Centralized logging configuration for the pipeline.
Implements rotating file logging for production readiness.
"""

import logging
from logging.handlers import RotatingFileHandler
from config.settings import LOG_FILE_PATH, LOG_DIR


def setup_logger(name: str) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name (str): Logger name.

    Returns:
        logging.Logger: Configured logger instance.
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5
        )

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger