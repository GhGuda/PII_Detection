"""
Schema validation module.
Enforces business rules and generates validation results report.
"""

from pathlib import Path
from typing import Dict, List
import pandas as pd
import re

from config.settings import BASE_DIR
from src.logger import setup_logger

logger = setup_logger(__name__)

REPORT_PATH = BASE_DIR / "reports" / "validation_results.txt"

VALID_ACCOUNT_STATUS = {"active", "inactive", "suspended"}


class ValidationResult:
    """
    Represents a validation failure for a specific column and row.
    """

    def __init__(self, column: str, row: int, message: str):
        self.column = column
        self.row = row
        self.message = message


def _is_valid_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, str(email).strip()))


def _is_valid_phone(phone: str) -> bool:
    """Validate phone number format (basic length and digit check)."""
    digits = re.sub(r"\D", "", str(phone))
    return len(digits) == 10


def _is_valid_date(date_value: str) -> bool:
    """Validate ISO date format YYYY-MM-DD."""
    try:
        parsed = pd.to_datetime(date_value, format="%Y-%m-%d", errors="raise")
        return True
    except Exception:
        return False


def validate_dataframe(df: pd.DataFrame) -> Dict[str, List[ValidationResult]]:
    """
    Validate dataframe against schema rules.

    Returns:
        Dict[str, List[ValidationResult]]: Failures grouped by column.
    """

    logger.info("Stage 3: Validation started")

    failures: Dict[str, List[ValidationResult]] = {}

    def add_failure(column: str, row: int, message: str):
        if column not in failures:
            failures[column] = []
        failures[column].append(ValidationResult(column, row, message))

    # ---------------------------
    # customer_id
    # ---------------------------
    if not df["customer_id"].is_unique:
        duplicates = df[df["customer_id"].duplicated()].index.tolist()
        for row in duplicates:
            add_failure("customer_id", row, "Duplicate ID")

    for idx, value in df["customer_id"].items():
        if pd.isna(value) or int(value) <= 0:
            add_failure("customer_id", idx, "Must be positive integer")

    # ---------------------------
    # first_name / last_name
    # ---------------------------
    for col in ["first_name", "last_name"]:
        for idx, value in df[col].items():
            if pd.isna(value) or not str(value).isalpha():
                add_failure(col, idx, "Must be alphabetic and non-null")
            elif not (2 <= len(str(value)) <= 50):
                add_failure(col, idx, "Must be 2-50 characters")

    # ---------------------------
    # email
    # ---------------------------
    for idx, value in df["email"].items():
        if not _is_valid_email(value):
            add_failure("email", idx, "Invalid email format")

    # ---------------------------
    # phone
    # ---------------------------
    for idx, value in df["phone"].items():
        if not _is_valid_phone(value):
            add_failure("phone", idx, "Invalid phone format")

    # ---------------------------
    # date_of_birth / created_date
    # ---------------------------
    for col in ["date_of_birth", "created_date"]:
        for idx, value in df[col].items():
            if not _is_valid_date(value):
                add_failure(col, idx, "Invalid date format (YYYY-MM-DD required)")

    # ---------------------------
    # account_status
    # ---------------------------
    for idx, value in df["account_status"].items():
        if value not in VALID_ACCOUNT_STATUS:
            add_failure("account_status", idx, "Invalid status value")

    # ---------------------------
    # income
    # ---------------------------
    for idx, value in df["income"].items():
        try:
            numeric_value = float(value)
            if numeric_value < 0:
                add_failure("income", idx, "Income cannot be negative")
            if numeric_value > 10_000_000:
                add_failure("income", idx, "Income exceeds allowed limit")
        except Exception:
            add_failure("income", idx, "Income must be numeric")

    logger.info("Stage 3: Validation completed")

    return failures


def write_validation_report(failures: Dict[str, List[ValidationResult]], total_rows: int) -> None:
    """
    Write validation results to file.
    """

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    total_failures = sum(len(v) for v in failures.values())
    passed_rows = total_rows - total_failures

    with open(REPORT_PATH, "w") as f:
        f.write("VALIDATION RESULTS\n")
        f.write("==================\n\n")

        f.write(f"PASS: {passed_rows} rows passed all checks\n")
        f.write(f"FAIL: {total_failures} validation failures\n\n")

        f.write("FAILURES BY COLUMN:\n")
        f.write("-------------------\n")

        for column, failure_list in failures.items():
            f.write(f"\n{column}:\n")
            for failure in failure_list:
                f.write(f"- Row {failure.row}: {failure.message}\n")

    logger.info("Validation report generated")