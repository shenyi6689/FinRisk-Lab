"""
05_feature_engineering.py

Build the Topic 2 blockchain market-integrity risk panel.

Inputs:
- data/raw/yahoo_ohlcv.csv
- data/raw/coinmetrics_asset_metrics.csv
- data/raw/defillama_dex_volume_daily.csv
- data/raw/defillama_chain_tvl.csv
- data/processed/event_windows.csv

Outputs:
- data/processed/blockchain_risk_panel.csv
- results/tables/feature_audit.csv
- results/tables/feature_dictionary.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

RAW_DIR = TOPIC_DIR / "data" / "raw"
PROCESSED_DIR = TOPIC_DIR / "data" / "processed"
TABLE_DIR = TOPIC_DIR / "results" / "tables"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

OHLCV_PATH = RAW_DIR / "yahoo_ohlcv.csv"
COINMETRICS_PATH = RAW_DIR / "coinmetrics_asset_metrics.csv"
DEX_PATH = RAW_DIR / "defillama_dex_volume_daily.csv"
TVL_PATH = RAW_DIR / "defillama_chain_tvl.csv"
WINDOW_PATH = PROCESSED_DIR / "event_windows.csv"

PANEL_PATH = PROCESSED_DIR / "blockchain_risk_panel.csv"
FEATURE_AUDIT_PATH = TABLE_DIR / "feature_audit.csv"
FEATURE_DICT_PATH = TABLE_DIR / "feature_dictionary.csv"

ASSET_CHAIN_MAP = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "BNB": "BSC",
    "SOL": "Solana",
    "USDC": "Ethereum",
    "USDT": "Ethereum",
}

STABLECOINS = {"USDC", "USDT"}


def zscore_by_asset(df, col, window=30):
    mean = df.groupby("asset")[col].transform(lambda x: x.rolling(window, min_periods=10).mean())
    std = df.groupby("asset")[col].transform(lambda x: x.rolling(window, min_periods=10).std())
    return (df[col] - mean) / std.replace(0, np.nan)


def rolling_max_drawdown(close, window=30):
    rolling_peak = close.rolling(window, min_periods=10).max()
    return close / rolling_peak - 1


def build_market_features(ohlcv):
    df = ohlcv.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["asset"] = df["asset"].astype(str).str.upper()

    df = df.sort_values(["asset", "date"]).reset_index(drop=True)

    for col in ["open", "high", "low", "close", "adj_close", "volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["log_close"] = np.log(df["close"].replace(0, np.nan))
    df["log_return"] = df.groupby("asset")["log_close"].diff()
    df["abs_log_return"] = df["log_return"].abs()
    df["negative_return"] = np.where(df["log_return"] < 0, 1, 0)

    df["rolling_vol_7d"] = df.groupby("asset")["log_return"].transform(
        lambda x: x.rolling(7, min_periods=5).std()
    )
    df["rolling_vol_30d"] = df.groupby("asset")["log_return"].transform(
        lambda x: x.rolling(30, min_periods=15).std()
    )

    df["volume_log"] = np.log1p(df["volume"])
    df["volume_z_30d"] = zscore_by_asset(df, "volume_log", 30)

    df["return_z_30d"] = zscore_by_asset(df, "log_return", 30)
    df["abs_return_z_30d"] = zscore_by_asset(df, "abs_log_return", 30)

    df["drawdown_30d"] = df.groupby("asset")["close"].transform(
        lambda x: rolling_max_drawdown(x, 30)
    )

    df["intraday_range"] = (df["high"] - df["low"]) / df["close"].replace(0, np.nan)
    df["intraday_range_z_30d"] = zscore_by_asset(df, "intraday_range", 30)

    df["stablecoin_peg_deviation"] = 0.0
    stable_mask = df["asset"].isin(STABLECOINS)
    df.loc[stable_mask, "stablecoin_peg_deviation"] = (
        df.loc[stable_mask, "close"] - 1.0
    ).abs()

    df["stablecoin_depeg_1pct"] = np.where(
        (df["asset"].isin(STABLECOINS)) & (df["stablecoin_peg_deviation"] >= 0.01),
        1,
        0,
    )

    return df


def merge_event_windows(panel):
    if not WINDOW_PATH.exists():
        panel["weak_label_3d"] = 0
        panel["weak_label_7d"] = 0
        panel["event_count_3d"] = 0
        panel["event_count_7d"] = 0
        panel["event_type_list_7d"] = ""
        panel["severity_list_7d"] = ""
        return panel

    windows = pd.read_csv(WINDOW_PATH)
    if windows.empty:
        panel["weak_label_3d"] = 0
        panel["weak_label_7d"] = 0
        panel["event_count_3d"] = 0
        panel["event_count_7d"] = 0
        panel["event_type_list_7d"] = ""
        panel["severity_list_7d"] = ""
        return panel

    windows["date"] = pd.to_datetime(windows["date"])
    windows["asset"] = windows["asset"].astype(str).str.upper()

    w3 = (
        windows[windows["window_name"] == "event_window_3d"]
        .groupby(["date", "asset"], as_index=False)
        .agg(
            event_count_3d=("event_id", "nunique"),
            event_ids_3d=("event_id", lambda x: ",".join(sorted(set(map(str, x))))),
        )
    )
    w3["weak_label_3d"] = 1

    w7 = (
        windows[windows["window_name"] == "event_window_7d"]
        .groupby(["date", "asset"], as_index=False)
        .agg(
            event_count_7d=("event_id", "nunique"),
            event_ids_7d=("event_id", lambda x: ",".join(sorted(set(map(str, x))))),
            event_type_list_7d=("event_type", lambda x: ",".join(sorted(set(map(str, x))))),
            severity_list_7d=("severity", lambda x: ",".join(sorted(set(map(str, x))))),
        )
    )
    w7["weak_label_7d"] = 1

    out = panel.merge(w3, on=["date", "asset"], how="left")
    out = out.merge(w7, on=["date", "asset"], how="left")

    for col in ["weak_label_3d", "weak_label_7d", "event_count_3d", "event_count_7d"]:
        out[col] = out[col].fillna(0).astype(int)

    for col in ["event_ids_3d", "event_ids_7d", "event_type_list_7d", "severity_list_7d"]:
        if col in out.columns:
            out[col] = out[col].fillna("")

    return out


def merge_coinmetrics(panel):
    if not COINMETRICS_PATH.exists():
        return panel

    cm = pd.read_csv(COINMETRICS_PATH)
    if cm.empty:
        return panel

    cm["date"] = pd.to_datetime(cm["date"])
    cm["asset"] = cm["asset"].astype(str).str.upper()

    # Keep only columns likely to exist after the previous download script.
    possible_cols = [
        "date",
        "asset",
        "AdrActCnt",
        "TxCnt",
        "CapMrktCurUSD",
        "SplyCur",
    ]
    existing = [c for c in possible_cols if c in cm.columns]
    cm = cm[existing].copy()

    for col in ["AdrActCnt", "TxCnt", "CapMrktCurUSD", "SplyCur"]:
        if col in cm.columns:
            cm[col] = pd.to_numeric(cm[col], errors="coerce")
            cm[f"{col}_log"] = np.log1p(cm[col])
            cm[f"{col}_z_30d"] = cm.groupby("asset")[f"{col}_log"].transform(
                lambda x: (x - x.rolling(30, min_periods=10).mean()) / x.rolling(30, min_periods=10).std().replace(0, np.nan)
            )

    out = panel.merge(cm, on=["date", "asset"], how="left")
    return out


def merge_defillama(panel):
    out = panel.copy()

    if DEX_PATH.exists():
        dex = pd.read_csv(DEX_PATH)
        if not dex.empty and "date" in dex.columns:
            dex["date"] = pd.to_datetime(dex["date"])
            if "total_dex_volume" in dex.columns:
                dex["total_dex_volume"] = pd.to_numeric(dex["total_dex_volume"], errors="coerce")
                dex = dex.sort_values("date")
                dex["total_dex_volume_log"] = np.log1p(dex["total_dex_volume"])
                dex["dex_volume_z_30d"] = (
                    dex["total_dex_volume_log"]
                    - dex["total_dex_volume_log"].rolling(30, min_periods=10).mean()
                ) / dex["total_dex_volume_log"].rolling(30, min_periods=10).std().replace(0, np.nan)

                out = out.merge(
                    dex[["date", "total_dex_volume", "total_dex_volume_log", "dex_volume_z_30d"]],
                    on="date",
                    how="left",
                )

    if TVL_PATH.exists():
        tvl = pd.read_csv(TVL_PATH)
        if not tvl.empty and {"date", "chain", "tvl"}.issubset(tvl.columns):
            tvl["date"] = pd.to_datetime(tvl["date"])
            tvl["tvl"] = pd.to_numeric(tvl["tvl"], errors="coerce")
            tvl["asset"] = tvl["chain"].map({v: k for k, v in ASSET_CHAIN_MAP.items()})

            # Stablecoins are mapped to Ethereum in ASSET_CHAIN_MAP, but this reverse map only keeps ETH.
            # Add stablecoins separately as Ethereum-context TVL.
            eth_tvl = tvl[tvl["chain"] == "Ethereum"].copy()
            stable_extra = []
            for stable in ["USDC", "USDT"]:
                tmp = eth_tvl.copy()
                tmp["asset"] = stable
                stable_extra.append(tmp)

            tvl_asset = pd.concat([tvl, *stable_extra], ignore_index=True)
            tvl_asset = tvl_asset.dropna(subset=["asset"])

            tvl_asset = tvl_asset[["date", "asset", "chain", "tvl"]].copy()
            tvl_asset = tvl_asset.rename(columns={"chain": "defillama_chain", "tvl": "chain_tvl"})

            tvl_asset["chain_tvl_log"] = np.log1p(tvl_asset["chain_tvl"])
            tvl_asset["chain_tvl_z_30d"] = tvl_asset.groupby("asset")["chain_tvl_log"].transform(
                lambda x: (x - x.rolling(30, min_periods=10).mean()) / x.rolling(30, min_periods=10).std().replace(0, np.nan)
            )

            out = out.merge(
                tvl_asset,
                on=["date", "asset"],
                how="left",
            )

    return out


def build_feature_audit(panel):
    feature_cols = [
        c for c in panel.columns
        if c not in [
            "date", "asset", "ticker", "open", "high", "low", "close", "adj_close",
            "event_ids_3d", "event_ids_7d", "event_type_list_7d", "severity_list_7d"
        ]
    ]

    rows = []
    for col in feature_cols:
        rows.append({
            "feature": col,
            "n_rows": len(panel),
            "missing_ratio": panel[col].isna().mean(),
            "n_unique": panel[col].nunique(dropna=True),
            "min": pd.to_numeric(panel[col], errors="coerce").min() if col in panel.columns else "",
            "max": pd.to_numeric(panel[col], errors="coerce").max() if col in panel.columns else "",
            "claim_boundary": "Features support market-integrity risk diagnostics, not fraud attribution.",
        })

    return pd.DataFrame(rows)


def build_feature_dictionary():
    rows = [
        ("log_return", "Daily log return from Yahoo close price.", "market stress"),
        ("abs_log_return", "Absolute daily log return.", "volatility proxy"),
        ("rolling_vol_7d", "7-day rolling standard deviation of log returns.", "short-horizon volatility"),
        ("rolling_vol_30d", "30-day rolling standard deviation of log returns.", "medium-horizon volatility"),
        ("volume_z_30d", "30-day rolling z-score of log trading volume.", "volume abnormality"),
        ("return_z_30d", "30-day rolling z-score of daily log return.", "return abnormality"),
        ("abs_return_z_30d", "30-day rolling z-score of absolute return.", "volatility shock"),
        ("drawdown_30d", "Close price relative to 30-day rolling peak minus one.", "drawdown stress"),
        ("intraday_range", "High-low range divided by close.", "intraday instability"),
        ("intraday_range_z_30d", "30-day rolling z-score of intraday range.", "range abnormality"),
        ("stablecoin_peg_deviation", "Absolute deviation from one dollar for USDC/USDT.", "stablecoin peg stress"),
        ("stablecoin_depeg_1pct", "Indicator for stablecoin price deviation of at least 1%.", "stablecoin depeg flag"),
        ("AdrActCnt_log", "Log active address count from Coin Metrics where available.", "network context"),
        ("TxCnt_log", "Log transaction count from Coin Metrics where available.", "network context"),
        ("CapMrktCurUSD_log", "Log market capitalization from Coin Metrics where available.", "market-size context"),
        ("SplyCur_log", "Log current supply from Coin Metrics where available.", "supply context"),
        ("total_dex_volume_log", "Log aggregate DeFiLlama DEX volume.", "DeFi market context"),
        ("dex_volume_z_30d", "30-day z-score of aggregate DEX volume.", "DeFi market stress"),
        ("chain_tvl_log", "Log DeFiLlama chain TVL mapped to asset chain.", "chain liquidity context"),
        ("chain_tvl_z_30d", "30-day z-score of mapped chain TVL.", "chain liquidity stress"),
        ("weak_label_3d", "Indicator for public incident window within +/-3 calendar days.", "weak label"),
        ("weak_label_7d", "Indicator for public incident window within +/-7 calendar days.", "weak label"),
        ("event_count_3d", "Number of public events linked to asset-day within +/-3 days.", "weak-label intensity"),
        ("event_count_7d", "Number of public events linked to asset-day within +/-7 days.", "weak-label intensity"),
    ]

    return pd.DataFrame(rows, columns=["feature", "definition", "role"])


def main():
    if not OHLCV_PATH.exists():
        raise FileNotFoundError("Missing Yahoo OHLCV data. Run 01_download_ohlcv.py first.")

    ohlcv = pd.read_csv(OHLCV_PATH)

    panel = build_market_features(ohlcv)
    panel = merge_event_windows(panel)
    panel = merge_coinmetrics(panel)
    panel = merge_defillama(panel)

    panel = panel.sort_values(["asset", "date"]).reset_index(drop=True)
    panel.to_csv(PANEL_PATH, index=False)

    feature_audit = build_feature_audit(panel)
    feature_audit.to_csv(FEATURE_AUDIT_PATH, index=False)

    feature_dict = build_feature_dictionary()
    feature_dict.to_csv(FEATURE_DICT_PATH, index=False)

    print("Saved blockchain risk panel to:")
    print(PANEL_PATH)
    print()
    print("Panel shape:", panel.shape)
    print()
    print(panel.head())

    print()
    print("Weak-label counts:")
    print(panel[["weak_label_3d", "weak_label_7d"]].sum())

    print()
    print("Saved feature audit to:")
    print(FEATURE_AUDIT_PATH)
    print()
    print(feature_audit.head(30))

    print()
    print("Saved feature dictionary to:")
    print(FEATURE_DICT_PATH)


if __name__ == "__main__":
    main()
