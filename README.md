# PII Detection Pipeline

Production-oriented Python pipeline for ingesting customer data, profiling quality, validating schema rules, cleaning records, detecting PII exposure, and producing a masked dataset for safer analytics sharing.

## Overview

This project processes a raw customer CSV and generates:
- Data quality profiling reports
- Validation failure reports
- Cleaning audit logs
- PII exposure assessment report
- Masked dataset and before/after masking sample
- End-to-end pipeline execution report

The pipeline is stage-based and logs operational details to rotating log files for traceability.

## Architecture

Execution entrypoint:
- `main.py` -> `src.orchestrator.run_pipeline()`

Core stages:
1. `LOAD`: Read CSV with retry/backoff and timeout handling (`src/loader.py`)
2. `PROFILING`: Generate quality profile (`src/profiler.py`)
3. `DETECT PII`: Detect sensitive fields and write risk report (`src/pii_detector.py`)
4. `VALIDATE (before clean)`: Enforce schema/business rules (`src/validator.py`)
5. `CLEAN`: Normalize/repair known issues (`src/cleaner.py`)
6. `VALIDATE (after clean)`: Measure post-clean quality (`src/validator.py`)
7. `MASK`: Mask direct identifiers and write masked sample (`src/masker.py`)
8. `REPORT`: Write execution summary (`src/orchestrator.py`)

## Project Structure

```text
.
|- config/
|  `- settings.py
|- data/
|  `- customers_raw.csv
|- src/
|  |- cleaner.py
|  |- loader.py
|  |- logger.py
|  |- masker.py
|  |- orchestrator.py
|  |- pii_detector.py
|  |- pipeline.py
|  |- profiler.py
|  `- validator.py
|- reports/
|  |- cleaning_log.txt
|  |- data_quality_report.txt
|  |- masked_sample.txt
|  |- pii_detection_report.txt
|  |- pipeline_execution_report.txt
|  `- validation_results.txt
|- logs/
|  `- pipeline.log
|- main.py
`- requirements.txt
```

## Requirements

- Python 3.10+ (tested on Python 3.13)
- `pip`
- Windows, macOS, or Linux

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Runtime settings are in [`config/settings.py`](/c:/Users/MelchizedekTettehNar/OneDrive%20-%20AmaliTech%20gGmbH/Desktop/PII_Detection_Pipeline/config/settings.py):

- `RAW_DATA_PATH`
- `LOG_FILE_PATH`
- `MAX_RETRIES`
- `RETRY_BACKOFF_SECONDS`
- `LOAD_TIMEOUT_SECONDS`

Update these values to match your deployment paths and reliability targets.

## Running the Pipeline

From project root:

```bash
python main.py
```

Expected console progress:
- Stage 1: Load
- Stage 2: Profiling
- Stage 4: Cleaning
- Stage 5: Masking

Detailed execution status is written to:
- `logs/pipeline.log`
- `reports/pipeline_execution_report.txt`

## Input Data Contract

Expected columns in raw data:
- `customer_id`
- `first_name`
- `last_name`
- `email`
- `phone`
- `date_of_birth`
- `address`
- `income`
- `account_status`
- `created_date`

Notes:
- Loader trims header whitespace automatically.
- Validator expects strict formats (e.g., `YYYY-MM-DD`, valid status enum).

## Outputs

Primary data outputs:
- `customers_cleaned.csv`
- `customers_masked.csv`

Governance and quality outputs:
- `reports/data_quality_report.txt`
- `reports/validation_results.txt`
- `reports/cleaning_log.txt`
- `reports/pii_detection_report.txt`
- `reports/masked_sample.txt`
- `reports/pipeline_execution_report.txt`

Operational output:
- `logs/pipeline.log` (rotating, 5 MB each, backup count: 5)

## Privacy and Security

PII fields handled:
- Names
- Email
- Phone
- Address
- Date of birth

Masking behavior:
- Names masked to first character + `***`
- Emails masked to local-prefix + domain
- Phones masked to `***-***-NNNN`
- Address replaced with `[MASKED ADDRESS]`
- DOB masked to `YYYY-**-**`

Recommendation:
- Share only `customers_masked.csv` with non-privileged analytics users.
- Restrict access to raw/cleaned data and logs via IAM and least privilege.

## Reliability and Observability

Current reliability controls:
- Retry with exponential backoff on load failures
- Timeout support on Unix via `SIGALRM` (graceful fallback on Windows)
- Structured stage logging
- Execution report summarizing run status and failure counts

Operational recommendations for production:
- Run on a scheduler (Airflow/cron/GitHub Actions)
- Add alerting on non-zero failure thresholds
- Add metrics export (row counts, failure rates, stage duration)
- Persist run metadata (run ID, source version, timestamp, status)

## Failure Handling

Failure behavior:
- Exceptions bubble to orchestration and stop the run
- Error details are logged in `logs/pipeline.log`
- Partial reports may still exist from completed stages

Suggested production policy:
- Hard fail on schema breakage or parser corruption
- Soft fail with warnings on non-critical quality issues
- Quarantine malformed rows for triage

## Known Limitations

- Validation pass metric in `validation_results.txt` is currently based on total rule failures (not unique passing rows), which can produce misleading pass counts when multiple failures occur per row.
- Some stage labels/messages are not perfectly aligned numerically (e.g., PII stage labeling in execution report).
- Data repair is rule-based; malformed row shifts may be detected but not fully auto-repaired.

## Development

Run style checks and tests (recommended to add in CI):

```bash
# Example (if added later)
pytest -q
```

Suggested next hardening steps:
1. Add unit/integration tests per stage.
2. Add schema contracts (Pandera/Great Expectations).
3. Move configuration to environment variables.
4. Add Dockerfile and CI workflow for reproducible runs.

