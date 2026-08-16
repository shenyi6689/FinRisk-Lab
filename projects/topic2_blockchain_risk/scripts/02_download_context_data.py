"""
02_download_context_data.py

Download and audit context data for Topic 2 Blockchain Market Integrity Risk.

Data layers:
- Coin Metrics community asset metrics
- DeFiLlama stablecoin / DEX / TVL context

Outputs:
- data/raw/coinmetrics_asset_metrics.csv
- data/raw/defillama_dex_volume_daily.csv
- data/raw/defillama_chain_tvl.csv
- data/raw/defillama_stablecoin_chains.csv
- results/tables/context_data_audit.csv
"""

from pathlib import Path
import json
import time
import requests
import pandas as pd
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

RAW_DIR = TOPIC_DIR / "data" / "raw"
TABLE_DIR = TOPIC_DIR / "results" / "tables"

RAW_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

START_DATE = "2021-01-01"
END_DATE = "2025-06-30"

CONTEXT_AUDIT_PATH = TABLE_DIR / "context_data_audit.csv"

COINMETRICS_OUTPUT = RAW_DIR / "coinmetrics_asset_metrics.csv"
DEFILLAMA_DEX_OUTPUT = RAW_DIR / "defillama_dex_volume_daily.csv"
DEFILLAMA_TVL_OUTPUT = RAW_DIR / "defillama_chain_tvl.csv"
DEFILLAMA_STABLECHAIN_OUTPUT = RAW_DIR / "defillama_stablecoin_chains.csv"

COINMETRICS_BASE = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"

ASSET_MAP = {
    "BTC": "btc",
    "ETH": "eth",
    "BNB": "bnb",
    "SOL": "sol",
    "USDC": "usdc",
    "USDT": "usdt",
}

COINMETRICS_METRICS = [
    "AdrActCnt",
    "TxCnt",
    "CapMrktCurUSD",
    "SplyCur",
]

DEFILLAMA_ENDPOINTS = {
    "stablecoin_chains": "https://stablecoins.llama.fi/stablecoinchains",
    "dex_overview": "https://api.llama.fi/overview/dexs",
    "protocols": "https://api.llama.fi/protocols",
}

DEFILLAMA_CHAINS = [
    "Ethereum",
    "Solana",
    "BSC",
    "Bitcoin",
]


def safe_get_json(url, params=None, timeout=45):
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def audit_row(source_layer, dataset, scope, path, status, df=None, notes=""):
    if df is None or df.empty:
        return {
            "source_layer": source_layer,
            "dataset": dataset,
            "scope": scope,
            "file_path": str(path.relative_to(PROJECT_ROOT)) if path else "",
            "file_status": status,
            "n_rows": 0,
            "n_columns": 0,
            "start_date": "",
            "end_date": "",
            "missing_ratio": "",
            "notes": notes,
        }

    out = {
        "source_layer": source_layer,
        "dataset": dataset,
        "scope": scope,
        "file_path": str(path.relative_to(PROJECT_ROOT)) if path else "",
        "file_status": status,
        "n_rows": len(df),
        "n_columns": df.shape[1],
        "start_date": "",
        "end_date": "",
        "missing_ratio": df.isna().mean().mean(),
        "notes": notes,
    }

    if "date" in df.columns:
        dates = pd.to_datetime(df["date"], errors="coerce")
        if dates.notna().any():
            out["start_date"] = dates.min().date()
            out["end_date"] = dates.max().date()

    return out


def download_coinmetrics_one(asset_label, cm_asset, metric):
    params = {
        "assets": cm_asset,
        "metrics": metric,
        "frequency": "1d",
        "start_time": START_DATE,
        "end_time": END_DATE,
        "page_size": 10000,
    }

    rows = []
    next_url = COINMETRICS_BASE
    next_params = params

    while next_url:
        payload = safe_get_json(next_url, params=next_params)

        data = payload.get("data", [])
        rows.extend(data)

        next_url = payload.get("next_page_url")
        next_params = None

        if next_url:
            time.sleep(0.2)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["asset"] = asset_label
    df["coinmetrics_asset"] = cm_asset
    df["metric"] = metric

    # normalize time/date
    if "time" in df.columns:
        df["date"] = pd.to_datetime(df["time"], errors="coerce").dt.date

    if metric in df.columns:
        df[metric] = pd.to_numeric(df[metric], errors="coerce")

    keep = ["date", "asset", "coinmetrics_asset", "metric", metric]
    existing = [c for c in keep if c in df.columns]
    return df[existing].copy()


def download_coinmetrics():
    frames = []
    audit_rows = []

    for asset_label, cm_asset in ASSET_MAP.items():
        for metric in COINMETRICS_METRICS:
            print(f"Coin Metrics: downloading {asset_label} {metric}")

            try:
                df = download_coinmetrics_one(asset_label, cm_asset, metric)

                if df.empty:
                    audit_rows.append(audit_row(
                        "Coin Metrics",
                        "asset_metrics",
                        f"{asset_label}:{metric}",
                        COINMETRICS_OUTPUT,
                        "missing_or_empty",
                        df,
                        "No rows returned by Coin Metrics community API.",
                    ))
                else:
                    frames.append(df)
                    audit_rows.append(audit_row(
                        "Coin Metrics",
                        "asset_metrics",
                        f"{asset_label}:{metric}",
                        COINMETRICS_OUTPUT,
                        "available",
                        df,
                        "Downloaded from Coin Metrics community API.",
                    ))

            except Exception as exc:
                audit_rows.append(audit_row(
                    "Coin Metrics",
                    "asset_metrics",
                    f"{asset_label}:{metric}",
                    COINMETRICS_OUTPUT,
                    "download_failed",
                    None,
                    f"{type(exc).__name__}: {exc}",
                ))

            time.sleep(0.2)

    if frames:
        long_df = pd.concat(frames, ignore_index=True)

        wide = (
            long_df
            .pivot_table(
                index=["date", "asset", "coinmetrics_asset"],
                columns="metric",
                values=COINMETRICS_METRICS,
                aggfunc="first",
            )
        )

        # Flatten possible multi-index columns safely.
        if isinstance(wide.columns, pd.MultiIndex):
            wide.columns = [
                c[0] if c[0] == c[1] else "_".join([str(x) for x in c if x])
                for c in wide.columns
            ]

        wide = wide.reset_index()
        wide.to_csv(COINMETRICS_OUTPUT, index=False)
    else:
        wide = pd.DataFrame()
        wide.to_csv(COINMETRICS_OUTPUT, index=False)

    return wide, audit_rows


def download_defillama_stablecoin_chains():
    url = DEFILLAMA_ENDPOINTS["stablecoin_chains"]

    payload = safe_get_json(url)

    if isinstance(payload, dict):
        rows = payload.get("chains", payload.get("data", []))
    elif isinstance(payload, list):
        rows = payload
    else:
        rows = []

    df = pd.DataFrame(rows)

    if not df.empty:
        df.to_csv(DEFILLAMA_STABLECHAIN_OUTPUT, index=False)
    else:
        df.to_csv(DEFILLAMA_STABLECHAIN_OUTPUT, index=False)

    return df


def download_defillama_dex_volume():
    url = DEFILLAMA_ENDPOINTS["dex_overview"]

    payload = safe_get_json(url)

    raw_path = RAW_DIR / "defillama_dex_overview_raw.json"
    raw_path.write_text(json.dumps(payload)[:2000000], encoding="utf-8")

    rows = []

    # DeFiLlama commonly returns totalDataChart as [[timestamp, volume], ...]
    chart = payload.get("totalDataChart", []) if isinstance(payload, dict) else []

    for item in chart:
        if isinstance(item, list) and len(item) >= 2:
            rows.append({
                "date": pd.to_datetime(item[0], unit="s", errors="coerce").date(),
                "total_dex_volume": item[1],
            })
        elif isinstance(item, dict):
            ts = item.get("date") or item.get("timestamp")
            val = item.get("volume") or item.get("totalVolume") or item.get("total_dex_volume")
            rows.append({
                "date": pd.to_datetime(ts, unit="s", errors="coerce").date(),
                "total_dex_volume": val,
            })

    df = pd.DataFrame(rows)

    if not df.empty:
        df["total_dex_volume"] = pd.to_numeric(df["total_dex_volume"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")

    df.to_csv(DEFILLAMA_DEX_OUTPUT, index=False)
    return df


def download_defillama_chain_tvl():
    frames = []
    audit_notes = []

    for chain in DEFILLAMA_CHAINS:
        url = f"https://api.llama.fi/v2/historicalChainTvl/{chain}"
        print(f"DeFiLlama: downloading chain TVL {chain}")

        try:
            payload = safe_get_json(url)

            rows = []
            if isinstance(payload, list):
                for item in payload:
                    rows.append({
                        "date": pd.to_datetime(item.get("date"), unit="s", errors="coerce").date(),
                        "chain": chain,
                        "tvl": item.get("tvl"),
                    })

            df = pd.DataFrame(rows)

            if not df.empty:
                df["tvl"] = pd.to_numeric(df["tvl"], errors="coerce")
                frames.append(df)

            audit_notes.append((chain, "available" if not df.empty else "empty", ""))

        except Exception as exc:
            audit_notes.append((chain, "download_failed", f"{type(exc).__name__}: {exc}"))

        time.sleep(0.2)

    if frames:
        tvl = pd.concat(frames, ignore_index=True)
        tvl = tvl.dropna(subset=["date"]).sort_values(["chain", "date"])
    else:
        tvl = pd.DataFrame(columns=["date", "chain", "tvl"])

    tvl.to_csv(DEFILLAMA_TVL_OUTPUT, index=False)
    return tvl, audit_notes


def download_defillama():
    audit_rows = []

    print("DeFiLlama: downloading stablecoin chain context")
    try:
        stablechains = download_defillama_stablecoin_chains()
        audit_rows.append(audit_row(
            "DeFiLlama",
            "stablecoin_chains",
            "all_chains_current",
            DEFILLAMA_STABLECHAIN_OUTPUT,
            "available" if not stablechains.empty else "empty",
            stablechains,
            "Current stablecoin market-cap context by chain.",
        ))
    except Exception as exc:
        stablechains = pd.DataFrame()
        audit_rows.append(audit_row(
            "DeFiLlama",
            "stablecoin_chains",
            "all_chains_current",
            DEFILLAMA_STABLECHAIN_OUTPUT,
            "download_failed",
            None,
            f"{type(exc).__name__}: {exc}",
        ))

    print("DeFiLlama: downloading DEX volume context")
    try:
        dex = download_defillama_dex_volume()
        audit_rows.append(audit_row(
            "DeFiLlama",
            "dex_volume_daily",
            "all_chains",
            DEFILLAMA_DEX_OUTPUT,
            "available" if not dex.empty else "empty",
            dex,
            "Daily aggregate DEX volume context.",
        ))
    except Exception as exc:
        dex = pd.DataFrame()
        audit_rows.append(audit_row(
            "DeFiLlama",
            "dex_volume_daily",
            "all_chains",
            DEFILLAMA_DEX_OUTPUT,
            "download_failed",
            None,
            f"{type(exc).__name__}: {exc}",
        ))

    tvl, tvl_notes = download_defillama_chain_tvl()
    for chain, status, note in tvl_notes:
        sub = tvl[tvl["chain"] == chain] if not tvl.empty else pd.DataFrame()
        audit_rows.append(audit_row(
            "DeFiLlama",
            "chain_tvl",
            chain,
            DEFILLAMA_TVL_OUTPUT,
            status,
            sub,
            note or "Historical chain TVL context.",
        ))

    return stablechains, dex, tvl, audit_rows


def main():
    audit_rows = []

    coinmetrics_df, cm_audit = download_coinmetrics()
    audit_rows.extend(cm_audit)

    stablechains, dex, tvl, dl_audit = download_defillama()
    audit_rows.extend(dl_audit)

    audit = pd.DataFrame(audit_rows)
    audit.to_csv(CONTEXT_AUDIT_PATH, index=False)

    print()
    print("Saved Coin Metrics data to:")
    print(COINMETRICS_OUTPUT)
    print("Coin Metrics shape:", coinmetrics_df.shape)

    print()
    print("Saved DeFiLlama stablecoin chain data to:")
    print(DEFILLAMA_STABLECHAIN_OUTPUT)
    print("Stablecoin chain shape:", stablechains.shape)

    print()
    print("Saved DeFiLlama DEX volume data to:")
    print(DEFILLAMA_DEX_OUTPUT)
    print("DEX volume shape:", dex.shape)

    print()
    print("Saved DeFiLlama chain TVL data to:")
    print(DEFILLAMA_TVL_OUTPUT)
    print("TVL shape:", tvl.shape)

    print()
    print("Saved context data audit to:")
    print(CONTEXT_AUDIT_PATH)
    print()
    print(audit)


if __name__ == "__main__":
    main()
