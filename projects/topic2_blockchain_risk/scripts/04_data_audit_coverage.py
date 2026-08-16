"""
04_data_audit_coverage.py

Build the four-layer coverage matrix for Topic 2.

Data layers:
1. Yahoo OHLCV
2. Coin Metrics
3. DeFiLlama
4. Incident ledger / weak-label windows

Outputs:
- results/tables/coverage_matrix.csv
- results/tables/data_layer_summary.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

RAW_DIR = TOPIC_DIR / "data" / "raw"
PROCESSED_DIR = TOPIC_DIR / "data" / "processed"
TABLE_DIR = TOPIC_DIR / "results" / "tables"

TABLE_DIR.mkdir(parents=True, exist_ok=True)

OHLCV_AUDIT_PATH = TABLE_DIR / "ohlcv_audit.csv"
CONTEXT_AUDIT_PATH = TABLE_DIR / "context_data_audit.csv"
INCIDENT_AUDIT_PATH = TABLE_DIR / "incident_ledger_audit.csv"

OHLCV_PATH = RAW_DIR / "yahoo_ohlcv.csv"
COINMETRICS_PATH = RAW_DIR / "coinmetrics_asset_metrics.csv"
DEFILLAMA_DEX_PATH = RAW_DIR / "defillama_dex_volume_daily.csv"
DEFILLAMA_TVL_PATH = RAW_DIR / "defillama_chain_tvl.csv"
DEFILLAMA_STABLE_PATH = RAW_DIR / "defillama_stablecoin_chains.csv"
INCIDENT_PATH = PROCESSED_DIR / "incident_ledger_validated.csv"
WINDOW_PATH = PROCESSED_DIR / "event_windows.csv"

COVERAGE_PATH = TABLE_DIR / "coverage_matrix.csv"
SUMMARY_PATH = TABLE_DIR / "data_layer_summary.csv"


def read_csv_if_exists(path):
    if path.exists():
        return pd.read_csv(path)
    return pd.DataFrame()


def file_info(path):
    return {
        "file_exists": path.exists(),
        "file_size_kb": round(path.stat().st_size / 1024, 2) if path.exists() else 0,
    }


def date_range(df, date_col="date"):
    if df.empty or date_col not in df.columns:
        return "", ""
    dates = pd.to_datetime(df[date_col], errors="coerce")
    if dates.notna().any():
        return dates.min().date(), dates.max().date()
    return "", ""


def add_row(rows, layer, dataset, scope, path, status, n_rows, n_columns, start_date, end_date, coverage_quality, notes, claim_boundary):
    info = file_info(path)
    rows.append({
        "data_layer": layer,
        "dataset": dataset,
        "scope": scope,
        "file_path": str(path.relative_to(PROJECT_ROOT)),
        "file_exists": info["file_exists"],
        "file_size_kb": info["file_size_kb"],
        "file_status": status,
        "n_rows": n_rows,
        "n_columns": n_columns,
        "start_date": start_date,
        "end_date": end_date,
        "coverage_quality": coverage_quality,
        "notes": notes,
        "claim_boundary": claim_boundary,
    })


def main():
    rows = []

    # Layer 1: Yahoo OHLCV, by asset.
    ohlcv_audit = read_csv_if_exists(OHLCV_AUDIT_PATH)

    if not ohlcv_audit.empty:
        for _, r in ohlcv_audit.iterrows():
            quality = "high" if r.get("file_status") == "available" and float(r.get("coverage_ratio", 0)) >= 0.95 else "limited"
            add_row(
                rows,
                "Layer 1: Yahoo OHLCV",
                "daily_ohlcv",
                str(r.get("asset", "")),
                OHLCV_PATH,
                r.get("file_status", "unknown"),
                r.get("n_rows", 0),
                9,
                r.get("start_date", ""),
                r.get("end_date", ""),
                quality,
                f"coverage_ratio={r.get('coverage_ratio', '')}; zero_or_negative_price_days={r.get('zero_or_negative_price_days', '')}; zero_volume_days={r.get('zero_volume_days', '')}",
                "OHLCV supports market-risk signals, not fraud attribution.",
            )
    else:
        add_row(
            rows,
            "Layer 1: Yahoo OHLCV",
            "daily_ohlcv",
            "all_assets",
            OHLCV_PATH,
            "missing_audit",
            0,
            0,
            "",
            "",
            "missing",
            "ohlcv_audit.csv not found.",
            "OHLCV layer must be audited before feature engineering.",
        )

    # Layer 2 and 3: context audit rows.
    context_audit = read_csv_if_exists(CONTEXT_AUDIT_PATH)

    if not context_audit.empty:
        for _, r in context_audit.iterrows():
            source_layer = r.get("source_layer", "")
            dataset = r.get("dataset", "")
            scope = r.get("scope", "")
            file_path = PROJECT_ROOT / r.get("file_path", "") if isinstance(r.get("file_path", ""), str) else RAW_DIR

            status = r.get("file_status", "unknown")
            n_rows = r.get("n_rows", 0)
            n_columns = r.get("n_columns", 0)

            if status == "available" and float(n_rows) > 0:
                quality = "medium" if source_layer == "Coin Metrics" else "high"
            elif status in ["missing_or_empty", "empty"]:
                quality = "low"
            else:
                quality = "failed"

            add_row(
                rows,
                f"Layer 2/3: {source_layer}",
                dataset,
                scope,
                file_path,
                status,
                n_rows,
                n_columns,
                r.get("start_date", ""),
                r.get("end_date", ""),
                quality,
                r.get("notes", ""),
                "Context data are supplementary risk signals and should not be treated as incident labels.",
            )
    else:
        add_row(
            rows,
            "Layer 2/3: Context",
            "context_data",
            "all",
            CONTEXT_AUDIT_PATH,
            "missing_audit",
            0,
            0,
            "",
            "",
            "missing",
            "context_data_audit.csv not found.",
            "Context layer must be audited before use.",
        )

    # Layer 4: incident ledger.
    incidents = read_csv_if_exists(INCIDENT_PATH)
    windows = read_csv_if_exists(WINDOW_PATH)
    incident_audit = read_csv_if_exists(INCIDENT_AUDIT_PATH)

    incident_start, incident_end = date_range(incidents, "event_date")
    window_start, window_end = date_range(windows, "date")

    if not incidents.empty:
        passed_count = 0
        if "status" in incidents.columns:
            passed_count = int((incidents["status"] == "passed").sum())

        quality = "high" if passed_count == len(incidents) else "medium"

        add_row(
            rows,
            "Layer 4: Incident ledger",
            "validated_incident_ledger",
            "public_seed_events",
            INCIDENT_PATH,
            "available",
            len(incidents),
            incidents.shape[1],
            incident_start,
            incident_end,
            quality,
            f"validated_events={passed_count}; total_events={len(incidents)}",
            "Incident ledger records public events, not verified fraud ground truth.",
        )
    else:
        add_row(
            rows,
            "Layer 4: Incident ledger",
            "validated_incident_ledger",
            "public_seed_events",
            INCIDENT_PATH,
            "missing_or_empty",
            0,
            0,
            "",
            "",
            "missing",
            "incident_ledger_validated.csv not found.",
            "Cannot construct weak labels without incident ledger.",
        )

    if not windows.empty:
        add_row(
            rows,
            "Layer 4: Weak-label windows",
            "event_windows",
            "event_window_3d_and_7d",
            WINDOW_PATH,
            "available",
            len(windows),
            windows.shape[1],
            window_start,
            window_end,
            "high",
            f"window_names={','.join(sorted(windows['window_name'].unique()))}",
            "Event windows are weak labels, not verified fraud labels.",
        )
    else:
        add_row(
            rows,
            "Layer 4: Weak-label windows",
            "event_windows",
            "event_window_3d_and_7d",
            WINDOW_PATH,
            "missing_or_empty",
            0,
            0,
            "",
            "",
            "missing",
            "event_windows.csv not found.",
            "Weak-label evaluation requires event windows.",
        )

    coverage = pd.DataFrame(rows)
    coverage.to_csv(COVERAGE_PATH, index=False)

    # Layer summary.
    summary = (
        coverage
        .groupby("data_layer", as_index=False)
        .agg(
            n_datasets=("dataset", "count"),
            available_count=("file_status", lambda x: int((x == "available").sum())),
            failed_or_missing_count=("file_status", lambda x: int((x != "available").sum())),
            total_rows=("n_rows", "sum"),
        )
    )

    summary["coverage_status"] = np.where(
        summary["failed_or_missing_count"] == 0,
        "complete",
        np.where(summary["available_count"] > 0, "partial", "missing"),
    )

    summary["claim_boundary"] = (
        "Coverage status describes data availability only; it does not validate incident truth or causal identification."
    )

    summary.to_csv(SUMMARY_PATH, index=False)

    print("Saved coverage matrix to:")
    print(COVERAGE_PATH)
    print()
    print(coverage)

    print()
    print("Saved data layer summary to:")
    print(SUMMARY_PATH)
    print()
    print(summary)


if __name__ == "__main__":
    main()
