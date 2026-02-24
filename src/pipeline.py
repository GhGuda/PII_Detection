"""
Pipeline orchestration module.
Handles execution of structured stages.
"""

from config.settings import RAW_DATA_PATH
from src.cleaner import clean_dataframe, write_cleaning_log
from src.loader import load_csv
from src.logger import setup_logger
from src.masker import mask_dataframe, write_masked_sample
from src.pii_detector import detect_pii, write_pii_report
from src.profiler import generate_data_quality_report
from src.validator import validate_dataframe, write_validation_report

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
    
    
def run_pii_detection_stage(df):
    """
    Execute PII detection stage.
    """

    results = detect_pii(df)
    write_pii_report(results)

    print("Stage: PII DETECTION")
    print("✓ PII detection report generated")

    return results


def run_validation_stage(df):
    """
    Execute Stage 3: Schema Validation.
    """
    failures = validate_dataframe(df)
    write_validation_report(failures, len(df))

    print("Stage 3: VALIDATION")
    print("[OK] Validation report generated")

    return failures


def run_cleaning_stage(df):
    """
    Execute Stage 4: Data Cleaning and Normalization.
    """

    # Validation before cleaning
    failures_before = validate_dataframe(df)
    before_count = sum(len(v) for v in failures_before.values())

    # Cleaning
    df, metadata = clean_dataframe(df)

    # Validation after cleaning
    failures_after = validate_dataframe(df)
    after_count = sum(len(v) for v in failures_after.values())

    # Write cleaned CSV
    df.to_csv("customers_cleaned.csv", index=False)

    # Write cleaning log
    write_cleaning_log(metadata, before_count, after_count, df)

    print("Stage 4: CLEANING")
    print("[OK] Cleaned dataset saved")
    print("[OK] Cleaning log generated")

    return df


def run_masking_stage(df):
    """
    Execute Stage 5: PII Masking.
    """

    masked_df = mask_dataframe(df)

    masked_df.to_csv("customers_masked.csv", index=False)

    write_masked_sample(df, masked_df)

    print("Stage 5: MASKING")
    print("[OK] Masked dataset saved")
    print("[OK] Masked sample report generated")

    return masked_df
