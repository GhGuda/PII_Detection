"""
Main entry point for the PII Detection & Data Quality Pipeline.
"""

import sys
from src.pipeline import run_load_stage
from src.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """
    Execute pipeline stages sequentially.
    """

    try:
        run_load_stage()

    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        print("Pipeline execution failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()