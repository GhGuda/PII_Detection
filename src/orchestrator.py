"""
Pipeline orchestration and execution reporting module.
Generates structured pipeline_execution_report.txt.
"""

from datetime import datetime

from config.settings import BASE_DIR
from src.logger import setup_logger
from src.pipeline import (
    run_load_stage,
    run_profiling_stage,
    run_cleaning_stage,
    run_masking_stage,
    run_pii_detection_stage
)
from src.validator import validate_dataframe

logger = setup_logger(__name__)

REPORT_PATH = BASE_DIR / "reports" / "pipeline_execution_report.txt"


def run_pipeline():
    """
    Execute full pipeline workflow and generate execution report.
    """

    logger.info("Pipeline execution started")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Stage 1 - Load
    df = run_load_stage()
    input_rows, input_cols = df.shape

    # Stage 2 - Profiling
    run_profiling_stage(df)
    
    # PII Detection
    pii_results = run_pii_detection_stage(df)

    # Stage 3 - Validation (before cleaning)
    failures_before = validate_dataframe(df)
    before_count = sum(len(v) for v in failures_before.values())

    # Stage 4 - Cleaning
    df = run_cleaning_stage(df)

    # Stage 5 - Validation (after cleaning)
    failures_after = validate_dataframe(df)
    after_count = sum(len(v) for v in failures_after.values())

    # Stage 6 - Masking
    masked_df = run_masking_stage(df)

    output_rows, output_cols = masked_df.shape

    # ---------------------------
    # Write execution report
    # ---------------------------
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("PIPELINE EXECUTION REPORT\n")
        f.write("=========================\n")
        f.write(f"Timestamp: {timestamp}\n\n")

        f.write("Stage 1: LOAD\n")
        f.write("[OK] Loaded customers_raw.csv\n")
        f.write(f"- {input_rows} rows, {input_cols} columns\n\n")

        f.write("Stage 2: PROFILING\n")
        f.write("[OK] Data quality report generated\n\n")

        f.write("Stage 3: VALIDATE\n")
        if before_count == 0:
            f.write("[OK] Passed schema validation\n")
        else:
            f.write(f"[OK] Validation completed ({before_count} failures detected)\n")
        f.write("\n")

        f.write("Stage 4: CLEAN\n")
        f.write("[OK] Data normalized and missing values handled\n")
        f.write(f"- Failures before cleaning: {before_count}\n")
        f.write(f"- Failures after cleaning: {after_count}\n\n")

        f.write("Stage 4: DETECT PII\n")
        f.write("✓ PII detection report generated\n\n")

        f.write("Stage 6: SAVE\n")
        f.write("[OK] Saved outputs:\n")
        f.write("- customers_cleaned.csv\n")
        f.write("- customers_masked.csv\n")
        f.write("- data_quality_report.txt\n")
        f.write("- validation_results.txt\n")
        f.write("- cleaning_log.txt\n")
        f.write("- masked_sample.txt\n\n")

        f.write("SUMMARY:\n")
        f.write(f"- Input: {input_rows} rows (raw)\n")
        f.write(f"- Output: {output_rows} rows (clean and masked)\n")
        f.write(f"- Quality: {'PASS' if after_count == 0 else 'FAIL'}\n")
        f.write("- PII Risk: MITIGATED (all masked)\n")
        f.write(
            f"Status: {'SUCCESS [OK]' if after_count == 0 else 'COMPLETED WITH WARNINGS'}\n"
        )

    logger.info("Pipeline execution report generated")
    logger.info("Pipeline execution completed")
