"""
07_anomaly_ensemble.py

Build unsupervised anomaly benchmarks for Topic 2.

Methods:
- Isolation Forest
- Local Outlier Factor
- Robust z-score max rule
- Ensemble average

Inputs:
- data/processed/blockchain_risk_panel_scored.csv

Outputs:
- data/processed/blockchain_risk_panel_anomaly.csv
- results/tables/unsupervised_anomaly_benchmark.csv
- results/tables/anomaly_method_agreement.csv
- results/tables/anomaly_top_alerts.csv
- results/figures/anomaly_event_window_lift.png
- results/figures/anomaly_method_ap_comparison.png
"""

from pathlib import Path
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler
from sklearn.metrics import average_precision_score, roc_auc_score


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

PROCESSED_DIR = TOPIC_DIR / "data" / "processed"
TABLE_DIR = TOPIC_DIR / "results" / "tables"
FIGURE_DIR = TOPIC_DIR / "results" / "figures"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

INPUT_PATH = PROCESSED_DIR / "blockchain_risk_panel_scored.csv"
OUTPUT_PATH = PROCESSED_DIR / "blockchain_risk_panel_anomaly.csv"

BENCHMARK_PATH = TABLE_DIR / "unsupervised_anomaly_benchmark.csv"
AGREEMENT_PATH = TABLE_DIR / "anomaly_method_agreement.csv"
TOP_ALERTS_PATH = TABLE_DIR / "anomaly_top_alerts.csv"

LIFT_FIGURE_PATH = FIGURE_DIR / "anomaly_event_window_lift.png"
AP_FIGURE_PATH = FIGURE_DIR / "anomaly_method_ap_comparison.png"


FEATURE_CANDIDATES = [
    "abs_return_z_30d",
    "volume_z_30d",
    "intraday_range_z_30d",
    "drawdown_30d",
    "stablecoin_peg_deviation",
    "dex_volume_z_30d",
    "chain_tvl_z_30d",
    "AdrActCnt_z_30d",
    "TxCnt_z_30d",
    "CapMrktCurUSD_z_30d",
    "SplyCur_z_30d",
]

SCORE_COLUMNS = [
    "transparent_risk_score",
    "isolation_forest_score",
    "lof_score",
    "robust_z_score",
    "anomaly_ensemble_score",
]

K_SHARES = [0.01, 0.05, 0.10, 0.20]


def percentile_rank(series):
    x = pd.to_numeric(series, errors="coerce").fillna(0)
    if x.nunique(dropna=True) <= 1:
        return pd.Series(0.0, index=x.index)
    return x.rank(pct=True)


def prepare_features(sub, feature_cols):
    X = sub[feature_cols].copy()

    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    X = X.replace([np.inf, -np.inf], np.nan)

    # Median imputation within the asset; fall back to zero.
    X = X.fillna(X.median(numeric_only=True)).fillna(0)

    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X)

    X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=0.0, neginf=0.0)

    return X_scaled


def robust_z_max_score(sub, feature_cols):
    X = sub[feature_cols].copy()

    scores = []

    for col in feature_cols:
        x = pd.to_numeric(X[col], errors="coerce")
        median = x.median()
        mad = (x - median).abs().median()

        if pd.isna(mad) or mad == 0:
            z = pd.Series(0.0, index=x.index)
        else:
            z = 0.6745 * (x - median) / mad

        if col == "drawdown_30d":
            # More negative drawdown means more stress.
            scores.append(np.maximum(-z, 0))
        elif col == "stablecoin_peg_deviation":
            scores.append(z.abs())
        else:
            scores.append(z.abs())

    if not scores:
        return pd.Series(0.0, index=sub.index)

    stacked = pd.concat(scores, axis=1)
    return stacked.max(axis=1).fillna(0)


def fit_asset_anomaly_scores(df, feature_cols):
    out_frames = []

    for asset, sub in df.groupby("asset"):
        sub = sub.sort_values("date").copy()

        if len(sub) < 50:
            sub["isolation_forest_score"] = 0.0
            sub["lof_score"] = 0.0
            sub["robust_z_score"] = 0.0
            sub["anomaly_ensemble_score"] = 0.0
            out_frames.append(sub)
            continue

        X = prepare_features(sub, feature_cols)

        iso = IsolationForest(
            n_estimators=300,
            contamination=0.03,
            random_state=42,
        )
        iso.fit(X)
        iso_raw = -iso.decision_function(X)

        n_neighbors = min(35, max(5, len(sub) // 20))
        n_neighbors = min(n_neighbors, len(sub) - 1)

        lof = LocalOutlierFactor(
            n_neighbors=n_neighbors,
            contamination=0.03,
        )
        lof.fit_predict(X)
        lof_raw = -lof.negative_outlier_factor_

        rz_raw = robust_z_max_score(sub, feature_cols)

        sub["isolation_forest_score"] = percentile_rank(pd.Series(iso_raw, index=sub.index))
        sub["lof_score"] = percentile_rank(pd.Series(lof_raw, index=sub.index))
        sub["robust_z_score"] = percentile_rank(rz_raw)

        sub["anomaly_ensemble_score"] = (
            sub[["isolation_forest_score", "lof_score", "robust_z_score"]]
            .mean(axis=1)
        )

        # Make ensemble also a within-asset percentile.
        sub["anomaly_ensemble_score"] = percentile_rank(sub["anomaly_ensemble_score"])

        out_frames.append(sub)

    return pd.concat(out_frames, ignore_index=True)


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


def benchmark_scores(df):
    rows = []

    label_cols = ["weak_label_3d", "weak_label_7d"]
    score_cols = [c for c in SCORE_COLUMNS if c in df.columns]

    for label_col in label_cols:
        if label_col not in df.columns:
            continue

        for score_col in score_cols:
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
                "claim_boundary": "Anomaly benchmark is evaluated against event-window weak labels, not verified fraud ground truth.",
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
                    "claim_boundary": "Asset-level anomaly performance is descriptive and weak-label based.",
                }

                for k_share in K_SHARES:
                    row = base_asset.copy()
                    row.update(eval_at_k(sub.assign(**{label_col: y_asset}), label_col, score_col, k_share))
                    rows.append(row)

    return pd.DataFrame(rows)


def method_agreement(df):
    score_cols = [c for c in SCORE_COLUMNS if c in df.columns]
    rows = []

    for a, b in itertools.combinations(score_cols, 2):
        corr = df[[a, b]].corr(method="spearman").iloc[0, 1]

        for k_share in [0.01, 0.05, 0.10]:
            n = len(df)
            k = max(1, int(round(n * k_share)))

            top_a = set(df.sort_values(a, ascending=False).head(k).index)
            top_b = set(df.sort_values(b, ascending=False).head(k).index)

            inter = len(top_a.intersection(top_b))
            union = len(top_a.union(top_b))
            jaccard = inter / union if union > 0 else np.nan

            rows.append({
                "method_a": a,
                "method_b": b,
                "spearman_corr": corr,
                "top_share": k_share,
                "top_n": k,
                "top_overlap_count": inter,
                "jaccard_top_overlap": jaccard,
                "claim_boundary": "Method agreement measures alert-score similarity, not incident truth.",
            })

    return pd.DataFrame(rows)


def save_top_alerts(df):
    cols = [
        "date",
        "asset",
        "anomaly_ensemble_score",
        "isolation_forest_score",
        "lof_score",
        "robust_z_score",
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
    ]

    existing = [c for c in cols if c in df.columns]

    top = (
        df[existing]
        .sort_values("anomaly_ensemble_score", ascending=False)
        .head(100)
        .copy()
    )

    top["claim_boundary"] = "Anomaly top alerts are review candidates, not confirmed fraud cases."
    top.to_csv(TOP_ALERTS_PATH, index=False)


def make_figures(df, benchmark):
    # Figure 1: event-window lift for ensemble anomaly score.
    fig_data = (
        df
        .assign(group=np.where(df["weak_label_7d"] == 1, "event_window_7d", "non_event_window"))
        .groupby("group", as_index=False)
        .agg(mean_score=("anomaly_ensemble_score", "mean"))
    )

    plt.figure(figsize=(8, 5))
    plt.bar(fig_data["group"], fig_data["mean_score"])
    plt.title("Anomaly ensemble score: event-window lift")
    plt.ylabel("Mean anomaly ensemble score")
    plt.xlabel("Group")
    plt.tight_layout()
    plt.savefig(LIFT_FIGURE_PATH, dpi=200)
    plt.close()

    # Figure 2: AP comparison for all-assets, weak_label_7d.
    ap_data = benchmark[
        (benchmark["evaluation_scope"] == "all_assets")
        & (benchmark["label"] == "weak_label_7d")
        & (benchmark["top_share"] == 0.05)
    ].copy()

    ap_data = ap_data.drop_duplicates(subset=["method"])

    plt.figure(figsize=(10, 5))
    plt.bar(ap_data["method"], ap_data["average_precision"])
    plt.title("Average precision by anomaly method")
    plt.ylabel("Average precision against weak_label_7d")
    plt.xlabel("Method")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(AP_FIGURE_PATH, dpi=200)
    plt.close()


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError("Missing blockchain_risk_panel_scored.csv. Run 06_transparent_risk_score.py first.")

    df = pd.read_csv(INPUT_PATH)
    df["date"] = pd.to_datetime(df["date"])

    feature_cols = [c for c in FEATURE_CANDIDATES if c in df.columns]

    if not feature_cols:
        raise ValueError("No anomaly feature columns found. Run 05_feature_engineering.py first.")

    anomaly_df = fit_asset_anomaly_scores(df, feature_cols)

    benchmark = benchmark_scores(anomaly_df)
    agreement = method_agreement(anomaly_df)

    anomaly_df.to_csv(OUTPUT_PATH, index=False)
    benchmark.to_csv(BENCHMARK_PATH, index=False)
    agreement.to_csv(AGREEMENT_PATH, index=False)

    save_top_alerts(anomaly_df)
    make_figures(anomaly_df, benchmark)

    print("Saved anomaly-scored panel to:")
    print(OUTPUT_PATH)
    print()
    print("Used anomaly features:")
    print(feature_cols)

    print()
    print("Anomaly score summary:")
    print(anomaly_df[["isolation_forest_score", "lof_score", "robust_z_score", "anomaly_ensemble_score"]].describe())

    print()
    print("Saved anomaly benchmark to:")
    print(BENCHMARK_PATH)
    print()
    print(benchmark.head(30))

    print()
    print("Saved anomaly method agreement to:")
    print(AGREEMENT_PATH)
    print()
    print(agreement.head(20))

    print()
    print("Saved top anomaly alerts to:")
    print(TOP_ALERTS_PATH)

    print()
    print("Saved figures:")
    print(LIFT_FIGURE_PATH)
    print(AP_FIGURE_PATH)


if __name__ == "__main__":
    main()
