"""
03_incident_ledger.py

Validate the public incident ledger and create weak-label event windows.

Outputs:
- data/processed/incident_ledger_validated.csv
- data/processed/event_windows.csv
- results/tables/incident_ledger_audit.csv
"""

from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

RAW_DIR = TOPIC_DIR / "data" / "raw"
PROCESSED_DIR = TOPIC_DIR / "data" / "processed"
TABLE_DIR = TOPIC_DIR / "results" / "tables"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

INCIDENT_PATH = RAW_DIR / "crypto_incidents_seed.csv"
OHLCV_PATH = RAW_DIR / "yahoo_ohlcv.csv"

VALIDATED_PATH = PROCESSED_DIR / "incident_ledger_validated.csv"
WINDOW_PATH = PROCESSED_DIR / "event_windows.csv"
AUDIT_PATH = TABLE_DIR / "incident_ledger_audit.csv"

REQUIRED_COLUMNS = [
    "event_id",
    "event_date",
    "asset",
    "event_type",
    "severity",
    "brief",
    "source_note",
    "source_url",
    "affected_assets",
]

VALID_SEVERITY = {"low", "medium", "high"}
VALID_EVENT_TYPES = {
    "stablecoin_depeg",
    "exchange_failure",
    "regulatory_action",
    "network_stress",
    "protocol_exploit",
    "broad_market_stress",
}

WINDOW_SPECS = [
    ("event_window_3d", 3),
    ("event_window_7d", 7),
]


def split_assets(value):
    if pd.isna(value):
        return []
    return [x.strip().upper() for x in str(value).split(",") if x.strip()]


def main():
    if not INCIDENT_PATH.exists():
        raise FileNotFoundError(f"Missing incident ledger: {INCIDENT_PATH}")

    if not OHLCV_PATH.exists():
        raise FileNotFoundError(f"Missing OHLCV data. Run 01_download_ohlcv.py first: {OHLCV_PATH}")

    incidents = pd.read_csv(INCIDENT_PATH)
    ohlcv = pd.read_csv(OHLCV_PATH)

    incidents["event_date"] = pd.to_datetime(incidents["event_date"], errors="coerce")
    ohlcv["date"] = pd.to_datetime(ohlcv["date"], errors="coerce")
    ohlcv["asset"] = ohlcv["asset"].astype(str).str.upper()

    available_assets = set(ohlcv["asset"].dropna().unique())
    sample_start = ohlcv["date"].min()
    sample_end = ohlcv["date"].max()

    audit_rows = []

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in incidents.columns]

    if missing_columns:
        audit_rows.append({
            "check_name": "required_columns",
            "status": "failed",
            "n_failed": len(missing_columns),
            "details": f"Missing columns: {missing_columns}",
            "claim_boundary": "Incident ledger cannot be used until required metadata fields exist.",
        })
    else:
        audit_rows.append({
            "check_name": "required_columns",
            "status": "passed",
            "n_failed": 0,
            "details": "All required incident ledger columns are present.",
            "claim_boundary": "Column completeness does not mean incident truth is verified.",
        })

    row_checks = []

    for _, row in incidents.iterrows():
        event_id = row.get("event_id", "")
        asset = str(row.get("asset", "")).upper()
        event_date = row.get("event_date")
        event_type = row.get("event_type", "")
        severity = row.get("severity", "")
        source_url = row.get("source_url", "")
        affected_assets = split_assets(row.get("affected_assets", ""))

        failures = []

        if pd.isna(event_date):
            failures.append("invalid_event_date")
        else:
            if event_date < sample_start or event_date > sample_end:
                failures.append("event_date_outside_ohlcv_sample")

        if asset not in available_assets:
            failures.append("main_asset_not_in_ohlcv")

        if severity not in VALID_SEVERITY:
            failures.append("invalid_severity")

        if event_type not in VALID_EVENT_TYPES:
            failures.append("nonstandard_event_type")

        if not isinstance(source_url, str) or not source_url.startswith("http"):
            failures.append("missing_source_url")

        affected_assets_in_ohlcv = [a for a in affected_assets if a in available_assets]

        if not affected_assets_in_ohlcv:
            failures.append("no_affected_asset_in_ohlcv")

        row_checks.append({
            "event_id": event_id,
            "event_date": event_date.date() if pd.notna(event_date) else "",
            "asset": asset,
            "event_type": event_type,
            "severity": severity,
            "n_affected_assets": len(affected_assets),
            "n_affected_assets_in_ohlcv": len(affected_assets_in_ohlcv),
            "affected_assets_in_ohlcv": ",".join(affected_assets_in_ohlcv),
            "source_url_present": isinstance(source_url, str) and source_url.startswith("http"),
            "status": "passed" if not failures else "warning",
            "failure_reasons": ";".join(failures),
            "claim_boundary": "Passing ledger validation does not convert the event window into verified fraud ground truth.",
        })

    row_check_df = pd.DataFrame(row_checks)

    audit_rows.append({
        "check_name": "row_level_validation",
        "status": "passed" if (row_check_df["status"] == "passed").all() else "warning",
        "n_failed": int((row_check_df["status"] != "passed").sum()),
        "details": "Row-level validation checks date range, asset coverage, source URL, event type, and severity.",
        "claim_boundary": "Warnings should be disclosed in the report and not treated as evidence of fraud.",
    })

    severity_counts = incidents["severity"].value_counts(dropna=False).to_dict()
    type_counts = incidents["event_type"].value_counts(dropna=False).to_dict()

    audit_rows.append({
        "check_name": "severity_distribution",
        "status": "passed",
        "n_failed": 0,
        "details": str(severity_counts),
        "claim_boundary": "Severity is a manual research label, not a legal classification.",
    })

    audit_rows.append({
        "check_name": "event_type_distribution",
        "status": "passed",
        "n_failed": 0,
        "details": str(type_counts),
        "claim_boundary": "Event type is a research category used for stratified diagnostics.",
    })

    # Add validation status back to incident ledger.
    validated = incidents.merge(
        row_check_df[
            [
                "event_id",
                "n_affected_assets_in_ohlcv",
                "affected_assets_in_ohlcv",
                "source_url_present",
                "status",
                "failure_reasons",
                "claim_boundary",
            ]
        ],
        on="event_id",
        how="left",
    )

    validated.to_csv(VALIDATED_PATH, index=False)

    # Create weak-label event windows.
    window_rows = []

    all_dates = (
        ohlcv[["date", "asset"]]
        .drop_duplicates()
        .sort_values(["asset", "date"])
        .copy()
    )

    for _, event in validated.iterrows():
        event_date = pd.to_datetime(event["event_date"], errors="coerce")

        if pd.isna(event_date):
            continue

        affected_assets = split_assets(event.get("affected_assets_in_ohlcv", ""))

        for affected_asset in affected_assets:
            asset_dates = all_dates[all_dates["asset"] == affected_asset].copy()

            for window_name, width in WINDOW_SPECS:
                start = event_date - pd.Timedelta(days=width)
                end = event_date + pd.Timedelta(days=width)

                matched = asset_dates[
                    (asset_dates["date"] >= start)
                    & (asset_dates["date"] <= end)
                ].copy()

                for _, day in matched.iterrows():
                    window_rows.append({
                        "date": day["date"].date(),
                        "asset": affected_asset,
                        "event_id": event["event_id"],
                        "event_date": event_date.date(),
                        "window_name": window_name,
                        "window_width_days": width,
                        "event_type": event["event_type"],
                        "severity": event["severity"],
                        "weak_label": 1,
                        "claim_boundary": "This is an event-window weak label, not verified fraud ground truth.",
                    })

    windows = pd.DataFrame(window_rows)

    if not windows.empty:
        windows = windows.drop_duplicates(
            subset=["date", "asset", "event_id", "window_name"]
        ).sort_values(["event_id", "asset", "window_name", "date"])

    windows.to_csv(WINDOW_PATH, index=False)

    audit = pd.DataFrame(audit_rows)
    audit.to_csv(AUDIT_PATH, index=False)

    print("Saved validated incident ledger to:")
    print(VALIDATED_PATH)
    print()
    print(validated)

    print()
    print("Saved event windows to:")
    print(WINDOW_PATH)
    print()
    print(windows.head(20))
    print()
    print("Event-window counts:")
    if not windows.empty:
        print(windows.groupby(["window_name", "event_id"]).size())

    print()
    print("Saved incident ledger audit to:")
    print(AUDIT_PATH)
    print()
    print(audit)


if __name__ == "__main__":
    main()
