"""
06_transparent_risk_score.py

Build a transparent market-integrity risk score.

Inputs:
- data/processed/blockchain_risk_panel.csv

Outputs:
- data/processed/blockchain_risk_panel_scored.csv
- results/tables/transparent_risk_score_eval.csv
- results/tables/transparent_risk_score_components.csv
- results/tables/transparent_risk_top_alerts.csv
- results/figures/transparent_score_event_window_lift.png
- results/figures/transparent_score_timeseries.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import average_precision_score, roc_auc_score


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

PROCESSED_DIR = TOPIC_DIR / "data" / "processed"
TABLE_DIR = TOPIC_DIR / "results" / "tables"
FIGURE_DIR = TOPIC_DIR / "results" / "figures"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

PANEL_PATH = PROCESSED_DIR / "blockchain_risk_panel.csv"
SCORED_PANEL_PATH = PROCESSED_DIR / "blockchain_risk_panel_scored.csv"

EVAL_PATH = TABLE_DIR / "transparent_risk_score_eval.csv"
COMPONENT_PATH = TABLE_DIR / "transparent_risk_score_components.csv"
TOP_ALERTS_PATH = TABLE_DIR / "transparent_risk_top_alerts.csv"

LIFT_FIGURE_PATH = FIGURE_DIR / "transparent_score_event_window_lift.png"
TIMESERIES_FIGURE_PATH = FIGURE_DIR / "transparent_score_timeseries.png"


COMPONENTS = [
    {
        "component": "return_shock",
        "source_column": "abs_return_z_30d",
        "weight": 0.22,
        "direction": "positive_tail",
        "definition": "Large absolute return shocks relative to recent asset history.",
    },
    {
        "component": "volume_shock",
        "source_column": "volume_z_30d",
        "weight": 0.18,
        "direction": "positive_tail",
        "definition": "Abnormal trading volume relative to recent asset history.",
    },
    {
        "component": "intraday_instability",
        "source_column": "intraday_range_z_30d",
        "weight": 0.18,
        "direction": "positive_tail",
        "definition": "Abnormal intraday high-low range.",
    },
    {
        "component": "drawdown_stress",
        "source_column": "drawdown_30d",
        "weight": 0.18,
        "direction": "negative_tail",
        "definition": "Price drawdown from recent 30-day rolling peak.",
    },
    {
        "component": "stablecoin_peg_stress",
        "source_column": "stablecoin_peg_deviation",
        "weight": 0.14,
        "direction": "absolute_level",
        "definition": "Absolute stablecoin price deviation from one dollar.",
    },
    {
        "component": "defi_volume_context",
        "source_column": "dex_volume_z_30d",
        "weight": 0.05,
        "direction": "positive_tail",
        "definition": "Aggregate DEX volume abnormality.",
    },
    {
        "component": "chain_tvl_context",
        "source_column": "chain_tvl_z_30d",
        "weight": 0.05,
        "direction": "absolute_tail",
        "definition": "Mapped chain TVL abnormality.",
    },
]


def positive_tail(series):
    x = pd.to_numeric(series, errors="coerce").fillna(0)
    return np.maximum(x, 0)


def absolute_tail(series):
    x = pd.to_numeric(series, errors="coerce").fillna(0)
    return np.abs(x)


def negative_tail(series):
    x = pd.to_numeric(series, errors="coerce").fillna(0)
    return np.maximum(-x, 0)


def absolute_level(series):
    x = pd.to_numeric(series, errors="coerce").fillna(0)
    return x.abs()


def percentile_scale(series):
    x = pd.to_numeric(series, errors="coerce").fillna(0)
    if x.nunique(dropna=True) <= 1:
        return pd.Series(0.0, index=x.index)
    return x.rank(pct=True)


def build_score(df):
    out = df.copy()

    component_rows = []

    weighted_sum = pd.Series(0.0, index=out.index)

    for spec in COMPONENTS:
        col = spec["source_column"]
        component = spec["component"]
        weight = spec["weight"]
        direction = spec["direction"]

        if col not in out.columns:
            raw_signal = pd.Series(0.0, index=out.index)
            missing_flag = 1
        else:
            if direction == "positive_tail":
                raw_signal = positive_tail(out[col])
            elif direction == "negative_tail":
                raw_signal = negative_tail(out[col])
            elif direction == "absolute_tail":
                raw_signal = absolute_tail(out[col])
            elif direction == "absolute_level":
                raw_signal = absolute_level(out[col])
            else:
                raw_signal = pd.Series(0.0, index=out.index)

            missing_flag = 0

        scaled = percentile_scale(raw_signal)
        out[f"score_component_{component}"] = scaled

        weighted_sum = weighted_sum + weight * scaled

        component_rows.append({
            "component": component,
            "source_column": col,
            "weight": weight,
            "direction": direction,
            "source_column_missing": missing_flag,
            "mean_scaled_component": scaled.mean(),
            "max_scaled_component": scaled.max(),
            "definition": spec["definition"],
            "claim_boundary": "Transparent score components are alert signals, not proof of fraud.",
        })

    # Convert to 0-100 score.
    out["transparent_risk_score_raw"] = weighted_sum
    out["transparent_risk_score"] = 100 * percentile_scale(weighted_sum)

    components = pd.DataFrame(component_rows)

    return out, components


def eval_at_k(df, label_col, score_col, k_share):
    n = len(df)
    k = max(1, int(round(n * k_share)))

    ranked = df.sort_values(score_col, ascending=False).head(k)

    positives = df[label_col].sum()
    captured = ranked[label_col].sum()

    precision = captured / k if k > 0 else np.nan
    recall = captured / positives if positives > 0 else np.nan
    base_rate = positives / n if n > 0 else np.nan
    lift = precision / base_rate if base_rate and base_rate > 0 else np.nan

    return {
        "top_share": k_share,
        "top_n": k,
        "precision_at_k": precision,
        "recall_at_k": recall,
        "lift_at_k": lift,
        "captured_weak_labels": int(captured),
        "total_weak_labels": int(positives),
    }


def safe_metric(y, s, metric_name):
    y = pd.Series(y).astype(int)
    s = pd.Series(s).astype(float)

    if y.nunique(dropna=True) < 2:
        return np.nan

    if metric_name == "average_precision":
        return average_precision_score(y, s)

    if metric_name == "roc_auc":
        return roc_auc_score(y, s)

    return np.nan


def evaluate_score(df):
    rows = []

    label_cols = ["weak_label_3d", "weak_label_7d"]
    k_shares = [0.01, 0.05, 0.10, 0.20]

    for label_col in label_cols:
        if label_col not in df.columns:
            continue

        y = df[label_col].fillna(0).astype(int)
        s = df["transparent_risk_score"]

        base = {
            "evaluation_scope": "all_assets",
            "asset": "ALL",
            "label": label_col,
            "n_rows": len(df),
            "label_positive_count": int(y.sum()),
            "label_positive_rate": y.mean(),
            "average_precision": safe_metric(y, s, "average_precision"),
            "roc_auc": safe_metric(y, s, "roc_auc"),
            "claim_boundary": "Evaluation uses event-window weak labels, not verified fraud ground truth.",
        }

        for k_share in k_shares:
            r = eval_at_k(df.assign(**{label_col: y}), label_col, "transparent_risk_score", k_share)
            row = base.copy()
            row.update(r)
            rows.append(row)

        for asset, sub in df.groupby("asset"):
            y_asset = sub[label_col].fillna(0).astype(int)
            s_asset = sub["transparent_risk_score"]

            base_asset = {
                "evaluation_scope": "by_asset",
                "asset": asset,
                "label": label_col,
                "n_rows": len(sub),
                "label_positive_count": int(y_asset.sum()),
                "label_positive_rate": y_asset.mean(),
                "average_precision": safe_metric(y_asset, s_asset, "average_precision"),
                "roc_auc": safe_metric(y_asset, s_asset, "roc_auc"),
                "claim_boundary": "Asset-level evaluation is descriptive and weak-label based.",
            }

            for k_share in k_shares:
                r = eval_at_k(sub.assign(**{label_col: y_asset}), label_col, "transparent_risk_score", k_share)
                row = base_asset.copy()
                row.update(r)
                rows.append(row)

    return pd.DataFrame(rows)


def save_top_alerts(df):
    cols = [
        "date",
        "asset",
        "transparent_risk_score",
        "weak_label_3d",
        "weak_label_7d",
        "event_ids_7d",
        "event_type_list_7d",
        "severity_list_7d",
        "log_return",
        "rolling_vol_7d",
        "volume_z_30d",
        "intraday_range_z_30d",
        "drawdown_30d",
        "stablecoin_peg_deviation",
        "dex_volume_z_30d",
        "chain_tvl_z_30d",
    ]

    existing = [c for c in cols if c in df.columns]

    top = (
        df[existing]
        .sort_values("transparent_risk_score", ascending=False)
        .head(100)
        .copy()
    )

    top["claim_boundary"] = "Top alerts are review candidates, not confirmed fraud cases."
    top.to_csv(TOP_ALERTS_PATH, index=False)


def make_figures(df, eval_df):
    # Figure 1: average score on weak-label days vs non-window days.
    label_col = "weak_label_7d"
    fig_data = (
        df
        .assign(group=np.where(df[label_col] == 1, "event_window_7d", "non_event_window"))
        .groupby("group", as_index=False)
        .agg(mean_score=("transparent_risk_score", "mean"))
    )

    plt.figure(figsize=(8, 5))
    plt.bar(fig_data["group"], fig_data["mean_score"])
    plt.title("Transparent risk score: event-window lift")
    plt.ylabel("Mean transparent risk score")
    plt.xlabel("Group")
    plt.tight_layout()
    plt.savefig(LIFT_FIGURE_PATH, dpi=200)
    plt.close()

    # Figure 2: time series average score across assets.
    ts = (
        df
        .groupby("date", as_index=False)
        .agg(
            mean_score=("transparent_risk_score", "mean"),
            max_weak_label_7d=("weak_label_7d", "max"),
        )
    )
    ts["date"] = pd.to_datetime(ts["date"])

    plt.figure(figsize=(12, 5))
    plt.plot(ts["date"], ts["mean_score"])
    event_days = ts[ts["max_weak_label_7d"] == 1]
    plt.scatter(event_days["date"], event_days["mean_score"], s=12)
    plt.title("Average transparent risk score over time")
    plt.ylabel("Mean transparent risk score")
    plt.xlabel("Date")
    plt.tight_layout()
    plt.savefig(TIMESERIES_FIGURE_PATH, dpi=200)
    plt.close()


def main():
    if not PANEL_PATH.exists():
        raise FileNotFoundError("Missing blockchain_risk_panel.csv. Run 05_feature_engineering.py first.")

    panel = pd.read_csv(PANEL_PATH)
    panel["date"] = pd.to_datetime(panel["date"])

    scored, components = build_score(panel)
    eval_df = evaluate_score(scored)

    scored.to_csv(SCORED_PANEL_PATH, index=False)
    components.to_csv(COMPONENT_PATH, index=False)
    eval_df.to_csv(EVAL_PATH, index=False)
    save_top_alerts(scored)
    make_figures(scored, eval_df)

    print("Saved scored panel to:")
    print(SCORED_PANEL_PATH)
    print()
    print("Score summary:")
    print(scored["transparent_risk_score"].describe())

    print()
    print("Saved transparent score components to:")
    print(COMPONENT_PATH)
    print()
    print(components)

    print()
    print("Saved transparent score evaluation to:")
    print(EVAL_PATH)
    print()
    print(eval_df.head(20))

    print()
    print("Saved top alerts to:")
    print(TOP_ALERTS_PATH)

    print()
    print("Saved figures:")
    print(LIFT_FIGURE_PATH)
    print(TIMESERIES_FIGURE_PATH)


if __name__ == "__main__":
    main()
