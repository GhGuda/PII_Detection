"""
Main entry point for the PII Detection & Data Quality Pipeline.
"""

import sys
from src.pipeline import run_load_stage
from src.logger import setup_logger
from src.pipeline import run_profiling_stage
from src.pipeline import run_validation_stage
logger = setup_logger(__name__)


def main():
    """
    Execute pipeline stages sequentially.
    """

    try:
        df = run_load_stage()
        run_profiling_stage(df)
        run_validation_stage(df)

    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        print("Pipeline execution failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()