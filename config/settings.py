"""
Application configuration settings for the PII Detection Pipeline.
Centralized configuration to support scalability and maintainability.
"""

from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data paths
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "customers_raw.csv"

# Logs
LOG_DIR = BASE_DIR / "logs"
LOG_FILE_PATH = LOG_DIR / "pipeline.log"

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2

# Timeout configuration (seconds)
LOAD_TIMEOUT_SECONDS = 10