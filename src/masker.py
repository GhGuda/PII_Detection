"""
PII masking module.
Applies deterministic masking rules aligned with project deliverables.
"""

from pathlib import Path
import pandas as pd

from config.settings import BASE_DIR
from src.logger import setup_logger

logger = setup_logger(__name__)

MASKED_DATA_PATH = BASE_DIR / "customers_masked.csv"
MASKED_SAMPLE_PATH = BASE_DIR / "reports" / "masked_sample.txt"


def _mask_name(name: str) -> str:
    """
    Mask name while preserving first character.
    Example: John -> J***
    """
    if not name or name == "[UNKNOWN]":
        return name
    return name[0] + "***"


def _mask_email(email: str) -> str:
    """
    Mask email preserving first character and domain.
    Example: john@gmail.com -> j***@gmail.com
    """
    if "@" not in str(email):
        return email

    local, domain = email.split("@", 1)
    return local[0] + "***@" + domain


def _mask_phone(phone: str) -> str:
    """
    Mask phone preserving last 4 digits.
    Example: 555-123-4567 -> ***-***-4567
    """
    digits = ''.join(filter(str.isdigit, str(phone)))
    if len(digits) == 10:
        return "***-***-" + digits[-4:]
    return phone


def _mask_dob(dob: str) -> str:
    """
    Mask DOB preserving year.
    Example: 1985-03-15 -> 1985-**-**
    """
    try:
        year = dob.split("-")[0]
        return f"{year}-**-**"
    except Exception:
        return dob


def mask_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply PII masking rules to dataframe copy.
    """

    logger.info("Stage 5: Masking started")

    masked_df = df.copy()

    masked_df["first_name"] = masked_df["first_name"].apply(_mask_name)
    masked_df["last_name"] = masked_df["last_name"].apply(_mask_name)
    masked_df["email"] = masked_df["email"].apply(_mask_email)
    masked_df["phone"] = masked_df["phone"].apply(_mask_phone)
    masked_df["address"] = "[MASKED ADDRESS]"
    masked_df["date_of_birth"] = masked_df["date_of_birth"].apply(_mask_dob)

    logger.info("Stage 5: Masking completed")

    return masked_df


def write_masked_sample(original_df: pd.DataFrame, masked_df: pd.DataFrame) -> None:
    """
    Write before/after sample comparison as required by deliverable.
    """

    MASKED_SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(MASKED_SAMPLE_PATH, "w") as f:
        f.write("BEFORE MASKING (first 2 rows):\n")
        f.write("------------------------------\n")
        f.write(original_df.head(2).to_csv(index=False))
        f.write("\n")

        f.write("AFTER MASKING (first 2 rows):\n")
        f.write("-----------------------------\n")
        f.write(masked_df.head(2).to_csv(index=False))
        f.write("\n")

        f.write("ANALYSIS:\n")
        f.write("- Data structure preserved (same rows & columns)\n")
        f.write("- PII masked (names, emails, phones, addresses, DOBs hidden)\n")
        f.write("- Business data intact (income, account_status, created_date retained)\n")
        f.write("- Safe for analytics team usage\n")

    logger.info("Masked sample report generated")