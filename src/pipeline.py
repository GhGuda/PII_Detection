"""
Pipeline orchestration module.
Handles execution of structured stages.
"""

from config.settings import RAW_DATA_PATH
from src.loader import load_csv
from src.logger import setup_logger
from src.profiler import generate_data_quality_report

logger = setup_logger(__name__)


def run_load_stage():
    """
    Execute Stage 1: Load raw dataset.

    Returns:
        DataFrame: Loaded raw dataset.
    """

    logger.info("Stage 1: LOAD started")

    df = load_csv(RAW_DATA_PATH)

    logger.info("Stage 1: LOAD completed successfully")

    print("Stage 1: LOAD")
    print("[OK] Loaded customers_raw.csv")
    print(f"- {df.shape[0]} rows, {df.shape[1]} columns")

    return df


def run_profiling_stage(df):
    """
    Execute Stage 2: Data Profiling.
    """
    generate_data_quality_report(df)
    print("Stage 2: PROFILING")
    print("[OK] Data quality report generated")
