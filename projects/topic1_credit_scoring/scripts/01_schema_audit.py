"""
01_schema_audit.py

Week 2 Topic 1: Trustworthy Credit Scoring

Purpose:
Create a schema and label audit table for the credit scoring module.

This script checks whether the expected raw datasets exist, records basic
schema information, identifies label fields, calculates positive rates when
possible, and saves the audit table to results/tables/schema_audit.csv.

Expected raw files:
- projects/topic1_credit_scoring/data/raw/uci_default.csv
- projects/topic1_credit_scoring/data/raw/freddie_sample.csv
- projects/topic1_credit_scoring/data/raw/hmda_sample.csv
- projects/topic1_credit_scoring/data/raw/fred_macro.csv
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic1_credit_scoring"
RAW_DIR = TOPIC_DIR / "data" / "raw"
RESULTS_DIR = TOPIC_DIR / "results" / "tables"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


DATASETS = [
    {
        "dataset": "UCI Default of Credit Card Clients",
        "filename": "uci_default.csv",
        "label": "target_default",
        "risk_meaning": "default",
        "date_or_vintage_field": "none; random split only",
    },
    {
        "dataset": "Freddie Mac Sample",
        "filename": "freddie_sample.csv",
        "label": "ever_30_dpd",
        "risk_meaning": "delinquency",
        "date_or_vintage_field": "origination_date or vintage if available",
    },
    {
        "dataset": "HMDA Fair-Lending Sample",
        "filename": "hmda_sample.csv",
        "label": "target_denied",
        "risk_meaning": "denial",
        "date_or_vintage_field": "activity_year or action_date if available",
    },
    {
        "dataset": "FRED Macro Rates",
        "filename": "fred_macro.csv",
        "label": "none",
        "risk_meaning": "macro context",
        "date_or_vintage_field": "date",
    },
]


def read_csv_safely(path: Path) -> pd.DataFrame:
    """Read a CSV file with basic fallback encodings."""
    try:
        return pd.read_csv(path)
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="latin1")


def summarize_dataset(meta: dict) -> dict:
    path = RAW_DIR / meta["filename"]

    if not path.exists():
        return {
            "dataset": meta["dataset"],
            "raw_file": str(path.relative_to(PROJECT_ROOT)),
            "file_status": "missing",
            "n_rows": None,
            "n_features": None,
            "label": meta["label"],
            "positive_rate": None,
            "date_or_vintage_field": meta["date_or_vintage_field"],
            "main_missing_fields": "file not available yet",
            "risk_meaning": meta["risk_meaning"],
            "notes": "Add raw CSV to data/raw and rerun this script.",
        }

    df = read_csv_safely(path)

    n_rows = len(df)
    n_features = df.shape[1]

    label = meta["label"]
    if label != "none" and label in df.columns:
        positive_rate = df[label].mean()
    else:
        positive_rate = None

    missing_rates = df.isna().mean().sort_values(ascending=False)
    missing_rates = missing_rates[missing_rates > 0].head(5)

    if len(missing_rates) == 0:
        main_missing_fields = "none detected"
    else:
        main_missing_fields = "; ".join(
            [f"{col}: {rate:.3f}" for col, rate in missing_rates.items()]
        )

    date_field = meta["date_or_vintage_field"]
    possible_date_fields = [
        "date",
        "activity_year",
        "origination_date",
        "vintage",
        "quarter",
        "year",
    ]
    detected_dates = [col for col in possible_date_fields if col in df.columns]
    if detected_dates:
        date_field = ", ".join(detected_dates)

    return {
        "dataset": meta["dataset"],
        "raw_file": str(path.relative_to(PROJECT_ROOT)),
        "file_status": "available",
        "n_rows": n_rows,
        "n_features": n_features,
        "label": label,
        "positive_rate": positive_rate,
        "date_or_vintage_field": date_field,
        "main_missing_fields": main_missing_fields,
        "risk_meaning": meta["risk_meaning"],
        "notes": "Schema audit completed.",
    }


def main():
    rows = [summarize_dataset(meta) for meta in DATASETS]
    audit = pd.DataFrame(rows)

    output_path = RESULTS_DIR / "schema_audit.csv"
    audit.to_csv(output_path, index=False)

    print("Schema audit saved to:")
    print(output_path)
    print()
    print(audit)


if __name__ == "__main__":
    main()
