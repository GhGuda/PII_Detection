"""
Data profiling module for raw dataset assessment.
Generates data quality report without modifying data.
"""

from pathlib import Path
import pandas as pd
import re
from typing import Dict

from config.settings import BASE_DIR
from src.logger import setup_logger

logger = setup_logger(__name__)

REPORT_PATH = BASE_DIR / "reports" / "data_quality_report.txt"


EXPECTED_SCHEMA = {
    "customer_id": "int",
    "first_name": "string",
    "last_name": "string",
    "email": "string",
    "phone": "string",
    "date_of_birth": "date",
    "address": "string",
    "income": "float",
    "account_status": "string",
    "created_date": "date"
}


VALID_ACCOUNT_STATUS = {"active", "inactive", "suspended"}


def calculate_completeness(df: pd.DataFrame) -> Dict[str, str]:
    """
    Calculate completeness percentage per column.
    """
    results = {}

    total_rows = len(df)

    for col in df.columns:
        non_null = df[col].notna().sum()
        percent = round((non_null / total_rows) * 100, 2)
        missing = total_rows - non_null
        results[col] = f"{percent}% ({missing} missing)"

    return results


def detect_phone_formats(series: pd.Series) -> set:
    """
    Detect distinct phone number formats.
    """
    formats = set()

    for value in series.dropna():
        value = str(value).strip()

        if re.match(r"\d{3}-\d{3}-\d{4}", value):
            formats.add("XXX-XXX-XXXX")
        elif re.match(r"\(\d{3}\)\s?\d{3}-\d{4}", value):
            formats.add("(XXX) XXX-XXXX")
        elif re.match(r"\d{3}\.\d{3}\.\d{4}", value):
            formats.add("XXX.XXX.XXXX")
        elif re.match(r"\d{10}", value):
            formats.add("XXXXXXXXXX")
        else:
            formats.add("UNKNOWN")

    return formats


def detect_invalid_dates(series: pd.Series) -> list:
    """
    Detect invalid date strings.
    """
    invalid = []

    for idx, value in series.items():
        try:
            pd.to_datetime(value, errors="raise")
        except Exception:
            invalid.append((idx, value))

    return invalid


def generate_data_quality_report(df: pd.DataFrame) -> None:
    """
    Generate a structured data quality profile report.
    """

    logger.info("Stage 2: Profiling started")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    completeness = calculate_completeness(df)
    phone_formats = detect_phone_formats(df["phone"])
    invalid_dob = detect_invalid_dates(df["date_of_birth"])
    invalid_created = detect_invalid_dates(df["created_date"])

    duplicate_ids = df["customer_id"].duplicated().sum()

    invalid_status = df[~df["account_status"].isin(VALID_ACCOUNT_STATUS)]

    negative_income = df[df["income"].fillna(0) < 0]
    excessive_income = df[df["income"].fillna(0) > 10_000_000]

    with open(REPORT_PATH, "w") as f:
        f.write("DATA QUALITY PROFILE REPORT\n")
        f.write("===========================\n\n")

        f.write("COMPLETENESS:\n")
        for col, value in completeness.items():
            f.write(f"- {col}: {value}\n")

        f.write("\nDATA TYPES (Detected by Pandas):\n")
        for col in df.columns:
            f.write(f"- {col}: {df[col].dtype}\n")

        f.write("\nFORMAT ANALYSIS:\n")
        f.write(f"- Phone formats detected: {phone_formats}\n")
        f.write(f"- Invalid DOB values: {invalid_dob}\n")
        f.write(f"- Invalid created_date values: {invalid_created}\n")

        f.write("\nUNIQUENESS CHECK:\n")
        f.write(f"- Duplicate customer_id count: {duplicate_ids}\n")

        f.write("\nVALUE RULE VIOLATIONS:\n")
        f.write(f"- Invalid account_status rows: {len(invalid_status)}\n")
        f.write(f"- Negative income rows: {len(negative_income)}\n")
        f.write(f"- Income > 10M rows: {len(excessive_income)}\n")

    logger.info("Stage 2: Profiling completed")
    logger.info(f"Report generated at {REPORT_PATH}")