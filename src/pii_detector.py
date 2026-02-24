"""
PII detection module.
Identifies and quantifies personally identifiable information exposure.
"""

from pathlib import Path
import pandas as pd
import re

from config.settings import BASE_DIR
from src.logger import setup_logger

logger = setup_logger(__name__)

REPORT_PATH = BASE_DIR / "reports" / "pii_detection_report.txt"


EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
PHONE_REGEX = r"(\d{3}-\d{3}-\d{4}|\(\d{3}\)\s?\d{3}-\d{4}|\d{3}\.\d{3}\.\d{4}|\d{10})"


def detect_pii(df: pd.DataFrame) -> dict:
    """
    Detect PII patterns using regex and presence checks.

    Returns:
        dict: counts and percentages of detected PII.
    """

    logger.info("PII detection started")

    total_rows = len(df)

    email_matches = df["email"].astype(str).str.match(EMAIL_REGEX, na=False)
    phone_matches = df["phone"].astype(str).str.contains(PHONE_REGEX, regex=True, na=False)
    address_present = df["address"].notna() & (df["address"].astype(str).str.strip() != "")
    dob_present = df["date_of_birth"].notna()

    results = {
        "emails": email_matches.sum(),
        "phones": phone_matches.sum(),
        "addresses": address_present.sum(),
        "dob": dob_present.sum(),
        "total_rows": total_rows
    }

    logger.info("PII detection completed")

    return results


def write_pii_report(results: dict) -> None:
    """
    Write structured PII detection report aligned with project specification.
    """

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    total = results["total_rows"]

    with open(REPORT_PATH, "w") as f:
        f.write("PII DETECTION REPORT\n")
        f.write("======================\n\n")

        f.write("RISK ASSESSMENT:\n")
        f.write("- HIGH: Names, emails, phone numbers, addresses, dates of birth\n")
        f.write("- MEDIUM: Income (financial sensitivity)\n\n")

        f.write("DETECTED PII:\n")
        f.write(f"- Emails found: {results['emails']} ({round(results['emails']/total*100)}%)\n")
        f.write(f"- Phone numbers found: {results['phones']} ({round(results['phones']/total*100)}%)\n")
        f.write(f"- Addresses found: {results['addresses']} ({round(results['addresses']/total*100)}%)\n")
        f.write(f"- Dates of birth found: {results['dob']} ({round(results['dob']/total*100)}%)\n\n")

        f.write("EXPOSURE RISK:\n")
        f.write("If this dataset were breached, attackers could:\n")
        f.write("- Phish customers (have emails)\n")
        f.write("- Spoof identities (have names + DOB + address)\n")
        f.write("- Social engineer (have phone numbers)\n\n")

        f.write("MITIGATION: Mask all PII before sharing with analytics teams\n")

    logger.info("PII detection report generated")