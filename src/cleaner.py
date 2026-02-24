"""
Data cleaning and normalization module.
Strictly aligned with project deliverable specification.
"""

from pathlib import Path
from typing import Dict, Tuple
import pandas as pd
import re

from config.settings import BASE_DIR
from src.logger import setup_logger

logger = setup_logger(__name__)

CLEANED_DATA_PATH = BASE_DIR / "customers_cleaned.csv"
CLEANING_LOG_PATH = BASE_DIR / "reports" / "cleaning_log.txt"


def _extract_phone_format(phone: str) -> str:
    """
    Identify phone format pattern.
    """
    value = str(phone).strip()

    if re.match(r"\d{3}-\d{3}-\d{4}", value):
        return "XXX-XXX-XXXX"
    if re.match(r"\(\d{3}\)\s?\d{3}-\d{4}", value):
        return "(XXX) XXX-XXXX"
    if re.match(r"\d{3}\.\d{3}\.\d{4}", value):
        return "XXX.XXX.XXXX"
    if re.match(r"\d{10}", value):
        return "XXXXXXXXXX"

    return "UNKNOWN"


def _normalize_phone(phone: str) -> str:
    """
    Convert phone to XXX-XXX-XXXX format.
    """
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return phone


def _normalize_date(value: str) -> str:
    """
    Convert date to YYYY-MM-DD format if possible.
    """
    try:
        return pd.to_datetime(value).strftime("%Y-%m-%d")
    except Exception:
        return value


def clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict]:
    """
    Apply deterministic cleaning rules.

    Returns:
        Tuple[pd.DataFrame, Dict]: cleaned dataframe and structured cleaning metadata
    """

    logger.info("Stage 4: Cleaning started")

    metadata = {
        "phone_formats_before": set(),
        "phone_rows_affected": 0,
        "date_formats_before": set(),
        "date_rows_affected": 0,
        "name_rows_affected": 0,
        "name_example": None,
        "missing_counts": {}
    }

    # ---------------------------
    # Phone normalization
    # ---------------------------
    for idx, value in df["phone"].items():
        metadata["phone_formats_before"].add(_extract_phone_format(value))

        normalized = _normalize_phone(value)
        if normalized != value:
            df.at[idx, "phone"] = normalized
            metadata["phone_rows_affected"] += 1

    # ---------------------------
    # Date normalization
    # ---------------------------
    for col in ["date_of_birth", "created_date"]:
        for idx, value in df[col].items():
            metadata["date_formats_before"].add(type(value).__name__)
            normalized = _normalize_date(value)
            if normalized != value:
                df.at[idx, col] = normalized
                metadata["date_rows_affected"] += 1

    # ---------------------------
    # Name title case
    # ---------------------------
    for col in ["first_name", "last_name"]:
        for idx, value in df[col].items():
            if pd.notna(value):
                title_value = str(value).title()
                if title_value != value:
                    df.at[idx, col] = title_value
                    metadata["name_rows_affected"] += 1
                    if metadata["name_example"] is None:
                        metadata["name_example"] = value

    # ---------------------------
    # Missing value handling
    # ---------------------------
    fill_strategies = {
        "first_name": "[UNKNOWN]",
        "last_name": "[UNKNOWN]",
        "address": "[UNKNOWN]",
        "income": 0,
        "account_status": "unknown"
    }

    for col, fill_value in fill_strategies.items():
        missing_count = df[col].isna().sum()
        metadata["missing_counts"][col] = {
            "count": int(missing_count),
            "fill_value": fill_value
        }

        if missing_count > 0:
            df[col] = df[col].fillna(fill_value)

    logger.info("Stage 4: Cleaning completed")

    return df, metadata


def write_cleaning_log(
    metadata: Dict,
    before_failures: int,
    after_failures: int,
    df: pd.DataFrame
) -> None:
    """
    Generate cleaning_log.txt strictly matching deliverable format.
    """

    CLEANING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    status = "PASS" if after_failures == 0 else "FAIL"

    with open(CLEANING_LOG_PATH, "w") as f:
        f.write("DATA CLEANING LOG\n")
        f.write("=================\n\n")

        f.write("ACTIONS TAKEN:\n")
        f.write("--------------\n")

        # Normalization section
        f.write("Normalization:\n")
        f.write(
            f"- Phone format: Converted {len(metadata['phone_formats_before'])} formats "
            f"-> XXX-XXX-XXXX ({metadata['phone_rows_affected']} rows affected)\n"
        )
        f.write(
            f"- Date format: Converted {len(metadata['date_formats_before'])} formats "
            f"-> YYYY-MM-DD ({metadata['date_rows_affected']} rows affected)\n"
        )

        if metadata["name_rows_affected"] > 0:
            f.write(
                f"- Name case: Applied title case to {metadata['name_example']} "
                f"({metadata['name_rows_affected']} row{'s' if metadata['name_rows_affected'] > 1 else ''} affected)\n"
            )
        else:
            f.write("- Name case: No changes required\n")

        f.write("\nMissing Values:\n")
        for col, details in metadata["missing_counts"].items():
            if details["count"] > 0:
                f.write(
                    f"- {col}: {details['count']} row{'s' if details['count'] > 1 else ''} "
                    f"missing -> filled with '{details['fill_value']}'\n"
                )

        f.write("\nValidation After Cleaning:\n")
        f.write(f"- Before: {before_failures} rows failed\n")
        f.write(f"- After: {after_failures} rows failed\n")
        f.write(f"- Status: {status}\n\n")

        f.write(
            f"Output: customers_cleaned.csv "
            f"({df.shape[0]} rows, {df.shape[1]} columns)\n"
        )

    logger.info("Cleaning log generated successfully")