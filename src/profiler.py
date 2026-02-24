"""
Data profiling module for raw dataset assessment.
Generates a structured data quality report matching project deliverables.
"""

from pathlib import Path
from typing import Dict, List
import pandas as pd

from config.settings import BASE_DIR
from src.logger import setup_logger

logger = setup_logger(__name__)

REPORT_PATH = BASE_DIR / "reports" / "data_quality_report.txt"

EXPECTED_SCHEMA = {
    "customer_id": "INT",
    "first_name": "STRING",
    "last_name": "STRING",
    "email": "STRING",
    "phone": "STRING",
    "date_of_birth": "DATE",
    "address": "STRING",
    "income": "FLOAT",
    "account_status": "STRING",
    "created_date": "DATE"
}

VALID_ACCOUNT_STATUS = {"active", "inactive", "suspended"}


class DataQualityIssue:
    """
    Represents a structured data quality issue.
    """

    def __init__(self, description: str, examples: List[str], severity: str):
        self.description = description
        self.examples = examples
        self.severity = severity


def calculate_completeness(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Calculate completeness metrics per column.
    """
    results = {}
    total_rows = len(df)

    for col in df.columns:
        missing = df[col].isna().sum()
        percent = round(((total_rows - missing) / total_rows) * 100, 2)
        results[col] = {
            "percent": percent,
            "missing": missing
        }

    return results


def map_dtype(dtype) -> str:
    """
    Map pandas dtype to logical type.
    """
    if "int" in str(dtype):
        return "INT"
    if "float" in str(dtype):
        return "FLOAT"
    if "datetime" in str(dtype):
        return "DATE"
    return "STRING"


def generate_data_quality_report(df: pd.DataFrame) -> None:
    """
    Generate structured data quality profile report.
    """

    logger.info("Stage 2: Profiling started")

    # Normalize headers defensively to handle leading/trailing whitespace.
    df = df.copy()
    df.columns = [
        col.strip() if isinstance(col, str) else col
        for col in df.columns
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    issues: List[DataQualityIssue] = []
    total_rows = len(df)

    # --------------------------
    # Completeness
    # --------------------------
    completeness = calculate_completeness(df)

    for col, metrics in completeness.items():
        if metrics["missing"] > 0:
            examples = df[df[col].isna()].index.tolist()[:3]
            issues.append(
                DataQualityIssue(
                    description=f"{metrics['missing']} rows have missing {col} "
                                f"= {round((metrics['missing']/total_rows)*100,2)}% incomplete",
                    examples=[f"Rows: {examples}"],
                    severity="High"
                )
            )

    # --------------------------
    # Type validation
    # --------------------------
    type_results = {}

    for col in df.columns:
        detected = map_dtype(df[col].dtype)
        expected = EXPECTED_SCHEMA.get(col, "UNKNOWN")

        type_results[col] = {
            "detected": detected,
            "expected": expected,
            "match": detected == expected
        }

        if detected != expected:
            issues.append(
                DataQualityIssue(
                    description=f"{col} detected as {detected} but expected {expected}",
                    examples=[f"Detected dtype: {df[col].dtype}"],
                    severity="Critical"
                )
            )

    # --------------------------
    # Duplicate ID check
    # --------------------------
    duplicate_count = df["customer_id"].duplicated().sum()

    if duplicate_count > 0:
        examples = df[df["customer_id"].duplicated()]["customer_id"].tolist()
        issues.append(
            DataQualityIssue(
                description=f"{duplicate_count} duplicate customer_id values found",
                examples=[f"Duplicate IDs: {examples}"],
                severity="Critical"
            )
        )

    # --------------------------
    # Invalid account status
    # --------------------------
    status_series = df["account_status"].astype(str).str.strip().str.lower()
    invalid_status_df = df[
        df["account_status"].notna() & ~status_series.isin(VALID_ACCOUNT_STATUS)
    ]

    if not invalid_status_df.empty:
        examples = invalid_status_df.index.tolist()[:3]
        issues.append(
            DataQualityIssue(
                description=f"{len(invalid_status_df)} rows contain invalid account_status values",
                examples=[f"Rows: {examples}"],
                severity="High"
            )
        )

    # --------------------------
    # Invalid dates
    # --------------------------
    for date_col in ["date_of_birth", "created_date"]:
        invalid_rows = []
        for idx, value in df[date_col].items():
            if pd.isna(value):
                continue
            try:
                pd.to_datetime(value, errors="raise")
            except Exception:
                invalid_rows.append(idx)

        if invalid_rows:
            issues.append(
                DataQualityIssue(
                    description=f"{len(invalid_rows)} invalid values found in {date_col}",
                    examples=[f"Rows: {invalid_rows[:3]}"],
                    severity="High"
                )
            )

    # --------------------------
    # Income validation
    # --------------------------
    income_numeric = pd.to_numeric(df["income"], errors="coerce")
    invalid_income_df = df[df["income"].notna() & income_numeric.isna()]
    negative_income = df[income_numeric < 0]
    excessive_income = df[income_numeric > 10_000_000]

    if not invalid_income_df.empty:
        issues.append(
            DataQualityIssue(
                description=f"{len(invalid_income_df)} rows contain non-numeric income values",
                examples=[f"Rows: {invalid_income_df.index.tolist()[:3]}"],
                severity="High"
            )
        )

    if not negative_income.empty:
        issues.append(
            DataQualityIssue(
                description=f"{len(negative_income)} rows contain negative income values",
                examples=[f"Rows: {negative_income.index.tolist()[:3]}"],
                severity="High"
            )
        )

    if not excessive_income.empty:
        issues.append(
            DataQualityIssue(
                description=f"{len(excessive_income)} rows exceed income limit (>10M)",
                examples=[f"Rows: {excessive_income.index.tolist()[:3]}"],
                severity="High"
            )
        )

    # --------------------------
    # Severity summary
    # --------------------------
    severity_counts = {
        "Critical": 0,
        "High": 0,
        "Medium": 0
    }

    for issue in issues:
        severity_counts[issue.severity] += 1

    # --------------------------
    # Write report
    # --------------------------
    with open(REPORT_PATH, "w") as f:
        f.write("DATA QUALITY PROFILE REPORT\n")
        f.write("===========================\n\n")

        f.write("COMPLETENESS:\n")
        for col, metrics in completeness.items():
            f.write(f"- {col}: {metrics['percent']}% "
                    f"({metrics['missing']} missing)\n")

        f.write("\nDATA TYPES:\n")
        for col, result in type_results.items():
            status = "OK" if result["match"] else "X"
            f.write(f"- {col}: {result['detected']} {status}")
            if not result["match"]:
                f.write(f" (should be {result['expected']})")
            f.write("\n")

        f.write("\nQUALITY ISSUES:\n")
        for idx, issue in enumerate(issues, start=1):
            f.write(f"{idx}. {issue.description}\n")
            for example in issue.examples:
                f.write(f"   Examples: {example}\n")

        f.write("\nSEVERITY:\n")
        f.write(f"- Critical (blocks processing): {severity_counts['Critical']}\n")
        f.write(f"- High (data incorrect): {severity_counts['High']}\n")
        f.write(f"- Medium (needs cleaning): {severity_counts['Medium']}\n")

    logger.info("Stage 2: Profiling completed successfully")
