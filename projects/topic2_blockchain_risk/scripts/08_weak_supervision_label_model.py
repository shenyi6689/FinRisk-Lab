"""
08_weak_supervision_label_model.py

Build a weak-supervision label model for blockchain market-integrity alerts.

Important boundary:
- Label functions are noisy research rules.
- Event windows are weak benchmark labels.
- This script does not produce verified fraud ground truth.

Inputs:
- data/processed/blockchain_risk_panel_anomaly.csv

Outputs:
- data/processed/blockchain_risk_panel_weak_supervision.csv
- results/tables/weak_supervision_label_model.csv
- results/tables/weak_supervision_label_functions.csv
- results/tables/weak_supervision_top_alerts.csv
- results/figures/weak_supervision_event_window_lift.png
- results/figures/weak_supervision_lf_coverage.png
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

INPUT_PATH = PROCESSED_DIR / "blockchain_risk_panel_anomaly.csv"
OUTPUT_PATH = PROCESSED_DIR / "blockchain_risk_panel_weak_supervision.csv"

MODEL_EVAL_PATH = TABLE_DIR / "weak_supervision_label_model.csv"
LF_TABLE_PATH = TABLE_DIR / "weak_supervision_label_functions.csv"
TOP_ALERTS_PATH = TABLE_DIR / "weak_supervision_top_alerts.csv"

LIFT_FIGURE_PATH = FIGURE_DIR / "weak_supervision_event_window_lift.png"
LF_COVERAGE_FIGURE_PATH = FIGURE_DIR / "weak_supervision_lf_coverage.png"

K_SHARES = [0.01, 0.05, 0.10, 0.20]


def asset_percentile(df, col):
    if col not in df.columns:
        return pd.Series(0.0, index=df.index)

    x = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return (
        x.groupby(df["asset"])
        .rank(pct=True)
        .fillna(0)
    )


def safe_metric(y, s, metric):
    y = pd.Series(y).fillna(0).astype(int)
    s = pd.Series(s).fillna(0).astype(float)

    if y.nunique(dropna=True) < 2:
        return np.nan

    if metric == "average_precision":
        return average_precision_score(y, s)

    if metric == "roc_auc":
        return roc_auc_score(y, s)

    return np.nan


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


def build_label_functions(df):
    out = df.copy()

    # Asset-relative percentiles.
    out["p_transparent"] = asset_percentile(out, "transparent_risk_score")
    out["p_anomaly"] = asset_percentile(out, "anomaly_ensemble_score")
    out["p_abs_return"] = asset_percentile(out, "abs_return_z_30d")
    out["p_volume"] = asset_percentile(out, "volume_z_30d")
    out["p_range"] = asset_percentile(out, "intraday_range_z_30d")
    out["p_drawdown_stress"] = asset_percentile(out.assign(drawdown_stress=-pd.to_numeric(out["drawdown_30d"], errors="coerce")), "drawdown_stress")
    out["p_dex_volume"] = asset_percentile(out, "dex_volume_z_30d")
    out["p_chain_tvl_abs"] = asset_percentile(out.assign(chain_tvl_abs=pd.to_numeric(out.get("chain_tvl_z_30d", 0), errors="coerce").abs()), "chain_tvl_abs")

    # Label functions: each gives 1 for alert, 0 for abstain/non-alert.
    out["lf_transparent_top5"] = (out["p_transparent"] >= 0.95).astype(int)
    out["lf_anomaly_top5"] = (out["p_anomaly"] >= 0.95).astype(int)

    out["lf_return_volume_joint"] = (
        (out["p_abs_return"] >= 0.90)
        & (out["p_volume"] >= 0.90)
    ).astype(int)

    out["lf_range_drawdown_joint"] = (
        (out["p_range"] >= 0.90)
        & (out["p_drawdown_stress"] >= 0.90)
    ).astype(int)

    out["lf_stablecoin_depeg"] = (
        (out["asset"].isin(["USDC", "USDT"]))
        & (pd.to_numeric(out.get("stablecoin_peg_deviation", 0), errors="coerce").fillna(0) >= 0.005)
    ).astype(int)

    out["lf_defi_context_shock"] = (
        (out["p_dex_volume"] >= 0.95)
        | (out["p_chain_tvl_abs"] >= 0.95)
    ).astype(int)

    out["lf_multimethod_consensus"] = (
        (out["p_transparent"] >= 0.90)
        & (out["p_anomaly"] >= 0.90)
    ).astype(int)

    label_functions = [
        {
            "label_function": "lf_transparent_top5",
            "weight": 0.20,
            "definition": "Transparent risk score is in the asset-specific top 5%.",
        },
        {
            "label_function": "lf_anomaly_top5",
            "weight": 0.20,
            "definition": "Anomaly ensemble score is in the asset-specific top 5%.",
        },
        {
            "label_function": "lf_return_volume_joint",
            "weight": 0.15,
            "definition": "Absolute return shock and volume shock are both in the asset-specific top 10%.",
        },
        {
            "label_function": "lf_range_drawdown_joint",
            "weight": 0.15,
            "definition": "Intraday range shock and drawdown stress are both in the asset-specific top 10%.",
        },
        {
            "label_function": "lf_stablecoin_depeg",
            "weight": 0.15,
            "definition": "Stablecoin deviates from one dollar by at least 0.5%.",
        },
        {
            "label_function": "lf_defi_context_shock",
            "weight": 0.05,
            "definition": "DEX volume or mapped chain TVL context is in an extreme asset-specific tail.",
        },
        {
            "label_function": "lf_multimethod_consensus",
            "weight": 0.10,
            "definition": "Transparent and anomaly scores are both in the asset-specific top 10%.",
        },
    ]

    lf_cols = [x["label_function"] for x in label_functions]
    weights = pd.Series({x["label_function"]: x["weight"] for x in label_functions})

    out["lf_vote_count"] = out[lf_cols].sum(axis=1)
    out["weak_supervision_score_raw"] = out[lf_cols].mul(weights, axis=1).sum(axis=1)
    out["weak_supervision_score"] = 100 * out["weak_supervision_score_raw"].rank(pct=True)

    out["weak_supervision_alert_top5"] = (
        out.groupby("asset")["weak_supervision_score"]
        .rank(pct=True)
        .ge(0.95)
        .astype(int)
    )

    lf_rows = []
    n = len(out)

    for spec in label_functions:
        col = spec["label_function"]
        coverage = out[col].mean()
        event7_rate_when_fires = out.loc[out[col] == 1, "weak_label_7d"].mean() if out[col].sum() > 0 else np.nan

        lf_rows.append({
            "label_function": col,
            "weight": spec["weight"],
            "fires_count": int(out[col].sum()),
            "coverage_rate": coverage,
            "weak_label_7d_rate_when_fires": event7_rate_when_fires,
            "definition": spec["definition"],
            "claim_boundary": "Label functions are noisy heuristic alerts, not verified fraud labels.",
        })

    lf_table = pd.DataFrame(lf_rows)

    # Pairwise conflict/overlap summary.
    positive_any = out[lf_cols].sum(axis=1)
    lf_table.loc[len(lf_table)] = {
        "label_function": "all_label_functions_summary",
        "weight": weights.sum(),
        "fires_count": int((positive_any > 0).sum()),
        "coverage_rate": (positive_any > 0).mean(),
        "weak_label_7d_rate_when_fires": out.loc[positive_any > 0, "weak_label_7d"].mean() if (positive_any > 0).sum() > 0 else np.nan,
        "definition": "Any label function fires.",
        "claim_boundary": "Aggregated weak supervision remains noisy and weak-label based.",
    }

    return out, lf_table, lf_cols


def evaluate_model(df):
    rows = []

    for label_col in ["weak_label_3d", "weak_label_7d"]:
        if label_col not in df.columns:
            continue

        for score_col in ["weak_supervision_score", "weak_supervision_score_raw", "lf_vote_count", "transparent_risk_score", "anomaly_ensemble_score"]:
            if score_col not in df.columns:
                continue

            y = df[label_col].fillna(0).astype(int)
            s = df[score_col].fillna(0).astype(float)

            base = {
                "evaluation_scope": "all_assets",
                "asset": "ALL",
                "label": label_col,
                "method": score_col,
                "n_rows": len(df),
                "label_positive_count": int(y.sum()),
                "label_positive_rate": y.mean(),
                "average_precision": safe_metric(y, s, "average_precision"),
                "roc_auc": safe_metric(y, s, "roc_auc"),
                "claim_boundary": "Weak-supervision model is evaluated against event-window weak labels, not verified fraud ground truth.",
            }

            for k_share in K_SHARES:
                row = base.copy()
                row.update(eval_at_k(df.assign(**{label_col: y}), label_col, score_col, k_share))
                rows.append(row)

            for asset, sub in df.groupby("asset"):
                y_asset = sub[label_col].fillna(0).astype(int)
                s_asset = sub[score_col].fillna(0).astype(float)

                base_asset = {
                    "evaluation_scope": "by_asset",
                    "asset": asset,
                    "label": label_col,
                    "method": score_col,
                    "n_rows": len(sub),
                    "label_positive_count": int(y_asset.sum()),
                    "label_positive_rate": y_asset.mean(),
                    "average_precision": safe_metric(y_asset, s_asset, "average_precision"),
                    "roc_auc": safe_metric(y_asset, s_asset, "roc_auc"),
                    "claim_boundary": "Asset-level weak-supervision evaluation is descriptive only.",
                }

                for k_share in K_SHARES:
                    row = base_asset.copy()
                    row.update(eval_at_k(sub.assign(**{label_col: y_asset}), label_col, score_col, k_share))
                    rows.append(row)

    return pd.DataFrame(rows)


def save_top_alerts(df, lf_cols):
    cols = [
        "date",
        "asset",
        "weak_supervision_score",
        "weak_supervision_score_raw",
        "lf_vote_count",
        "weak_supervision_alert_top5",
        "transparent_risk_score",
        "anomaly_ensemble_score",
        "weak_label_3d",
        "weak_label_7d",
        "event_ids_7d",
        "event_type_list_7d",
        "severity_list_7d",
        "log_return",
        "volume_z_30d",
        "intraday_range_z_30d",
        "drawdown_30d",
        "stablecoin_peg_deviation",
    ] + lf_cols

    existing = [c for c in cols if c in df.columns]

    top = (
        df[existing]
        .sort_values("weak_supervision_score", ascending=False)
        .head(100)
        .copy()
    )

    top["claim_boundary"] = "Weak-supervision top alerts are review candidates, not confirmed fraud cases."
    top.to_csv(TOP_ALERTS_PATH, index=False)


def make_figures(df, lf_table):
    # Event-window lift.
    fig_data = (
        df
        .assign(group=np.where(df["weak_label_7d"] == 1, "event_window_7d", "non_event_window"))
        .groupby("group", as_index=False)
        .agg(mean_score=("weak_supervision_score", "mean"))
    )

    plt.figure(figsize=(8, 5))
    plt.bar(fig_data["group"], fig_data["mean_score"])
    plt.title("Weak-supervision score: event-window lift")
    plt.ylabel("Mean weak-supervision score")
    plt.xlabel("Group")
    plt.tight_layout()
    plt.savefig(LIFT_FIGURE_PATH, dpi=200)
    plt.close()

    # Label function coverage.
    plot_data = lf_table[lf_table["label_function"] != "all_label_functions_summary"].copy()

    plt.figure(figsize=(11, 5))
    plt.bar(plot_data["label_function"], plot_data["coverage_rate"])
    plt.title("Weak-supervision label-function coverage")
    plt.ylabel("Coverage rate")
    plt.xlabel("Label function")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(LF_COVERAGE_FIGURE_PATH, dpi=200)
    plt.close()


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError("Missing blockchain_risk_panel_anomaly.csv. Run 07_anomaly_ensemble.py first.")

    df = pd.read_csv(INPUT_PATH)
    df["date"] = pd.to_datetime(df["date"])

    out, lf_table, lf_cols = build_label_functions(df)
    eval_table = evaluate_model(out)

    out.to_csv(OUTPUT_PATH, index=False)
    lf_table.to_csv(LF_TABLE_PATH, index=False)
    eval_table.to_csv(MODEL_EVAL_PATH, index=False)
    save_top_alerts(out, lf_cols)
    make_figures(out, lf_table)

    print("Saved weak-supervision panel to:")
    print(OUTPUT_PATH)
    print()

    print("Saved label-function table to:")
    print(LF_TABLE_PATH)
    print()
    print(lf_table)

    print()
    print("Saved weak-supervision model evaluation to:")
    print(MODEL_EVAL_PATH)
    print()
    print(eval_table.head(30))

    print()
    print("Saved weak-supervision top alerts to:")
    print(TOP_ALERTS_PATH)

    print()
    print("Saved figures:")
    print(LIFT_FIGURE_PATH)
    print(LF_COVERAGE_FIGURE_PATH)


if __name__ == "__main__":
    main()
