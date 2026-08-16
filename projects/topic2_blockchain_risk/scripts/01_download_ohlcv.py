"""
01_download_ohlcv.py

Download Yahoo OHLCV data for Topic 2 Blockchain Market Integrity Risk.

Assets:
- BTC
- ETH
- BNB
- SOL
- USDC
- USDT

Outputs:
- data/raw/yahoo_ohlcv.csv
- results/tables/ohlcv_audit.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

RAW_DIR = TOPIC_DIR / "data" / "raw"
TABLE_DIR = TOPIC_DIR / "results" / "tables"

RAW_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = RAW_DIR / "yahoo_ohlcv.csv"
AUDIT_PATH = TABLE_DIR / "ohlcv_audit.csv"

START_DATE = "2021-01-01"
END_DATE = "2025-06-30"

TICKERS = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BNB": "BNB-USD",
    "SOL": "SOL-USD",
    "USDC": "USDC-USD",
    "USDT": "USDT-USD",
}


def download_one_asset(asset, ticker):
    print(f"Downloading {asset}: {ticker}")

    data = yf.download(
        ticker,
        start=START_DATE,
        end=END_DATE,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=False,
    )

    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()

    rename_map = {
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Adj Close": "adj_close",
        "Volume": "volume",
    }

    data = data.rename(columns=rename_map)

    keep_cols = ["date", "open", "high", "low", "close", "adj_close", "volume"]
    existing = [c for c in keep_cols if c in data.columns]
    data = data[existing].copy()

    data["asset"] = asset
    data["ticker"] = ticker

    for col in ["open", "high", "low", "close", "adj_close", "volume"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    data["date"] = pd.to_datetime(data["date"]).dt.date

    return data


def audit_asset(df, asset):
    sub = df[df["asset"] == asset].copy()

    if sub.empty:
        return {
            "asset": asset,
            "ticker": TICKERS[asset],
            "file_status": "missing",
            "start_date": "",
            "end_date": "",
            "n_rows": 0,
            "n_calendar_days": 0,
            "coverage_ratio": 0,
            "missing_close_ratio": "",
            "missing_volume_ratio": "",
            "zero_or_negative_price_days": "",
            "zero_volume_days": "",
            "duplicate_date_count": "",
            "notes": "No data downloaded from Yahoo.",
        }

    sub["date"] = pd.to_datetime(sub["date"])

    start_date = sub["date"].min()
    end_date = sub["date"].max()
    n_calendar_days = (end_date - start_date).days + 1

    zero_or_negative_price_days = (
        (sub[["open", "high", "low", "close"]] <= 0)
        .any(axis=1)
        .sum()
    )

    zero_volume_days = (sub["volume"].fillna(0) <= 0).sum()
    duplicate_date_count = sub.duplicated(subset=["date"]).sum()

    return {
        "asset": asset,
        "ticker": TICKERS[asset],
        "file_status": "available",
        "start_date": start_date.date(),
        "end_date": end_date.date(),
        "n_rows": len(sub),
        "n_calendar_days": n_calendar_days,
        "coverage_ratio": len(sub) / n_calendar_days if n_calendar_days > 0 else np.nan,
        "missing_close_ratio": sub["close"].isna().mean(),
        "missing_volume_ratio": sub["volume"].isna().mean(),
        "zero_or_negative_price_days": int(zero_or_negative_price_days),
        "zero_volume_days": int(zero_volume_days),
        "duplicate_date_count": int(duplicate_date_count),
        "notes": "Daily Yahoo OHLCV downloaded. Crypto trades continuously, so calendar-day coverage is expected to be high.",
    }


def main():
    frames = []

    for asset, ticker in TICKERS.items():
        asset_df = download_one_asset(asset, ticker)
        if not asset_df.empty:
            frames.append(asset_df)

    if not frames:
        raise RuntimeError("No OHLCV data downloaded. Check internet connection or yfinance availability.")

    panel = pd.concat(frames, ignore_index=True)
    panel = panel.sort_values(["asset", "date"])

    panel.to_csv(OUTPUT_PATH, index=False)

    audit_rows = [audit_asset(panel, asset) for asset in TICKERS.keys()]
    audit = pd.DataFrame(audit_rows)
    audit.to_csv(AUDIT_PATH, index=False)

    print()
    print("Saved Yahoo OHLCV panel to:")
    print(OUTPUT_PATH)
    print()
    print(panel.head())

    print()
    print("Saved OHLCV audit to:")
    print(AUDIT_PATH)
    print()
    print(audit)


if __name__ == "__main__":
    main()
