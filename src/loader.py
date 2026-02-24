"""
Data loading module for the PII Detection Pipeline.
Includes retry logic and timeout handling.
"""

import pandas as pd
import time
import signal
from pathlib import Path
from typing import Optional

from config.settings import MAX_RETRIES, RETRY_BACKOFF_SECONDS, LOAD_TIMEOUT_SECONDS
from src.logger import setup_logger

logger = setup_logger(__name__)


class TimeoutException(Exception):
    """Custom exception raised when an operation times out."""
    pass


def timeout_handler(signum, frame):
    """Internal timeout signal handler."""
    raise TimeoutException("File loading operation timed out.")


def load_csv(file_path: Path) -> pd.DataFrame:
    """
    Load a CSV file with retry and timeout handling.

    Args:
        file_path (Path): Path to the CSV file.

    Returns:
        pd.DataFrame: Loaded DataFrame.

    Raises:
        FileNotFoundError: If file does not exist.
        TimeoutException: If loading exceeds timeout limit.
        Exception: If loading fails after retries.
    """

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    attempt = 0

    while attempt < MAX_RETRIES:
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(LOAD_TIMEOUT_SECONDS)

            logger.info(f"Attempting to load file (Attempt {attempt + 1})")

            df = pd.read_csv(file_path)

            signal.alarm(0)  # Cancel alarm

            logger.info(
                f"Successfully loaded file: {file_path} "
                f"({df.shape[0]} rows, {df.shape[1]} columns)"
            )

            return df

        except TimeoutException as te:
            logger.error(f"Timeout occurred: {te}")
            raise

        except Exception as e:
            attempt += 1
            logger.error(
                f"Error loading file (Attempt {attempt}): {e}"
            )

            if attempt >= MAX_RETRIES:
                logger.critical("Max retries reached. Aborting load.")
                raise

            time.sleep(RETRY_BACKOFF_SECONDS * attempt)

    raise Exception("Unexpected loader failure.")