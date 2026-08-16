"""
10_ablation_placebo_sensitivity.py

Run ablation, placebo, and sensitivity checks for Topic 2.

Inputs:
- data/processed/blockchain_risk_panel_weak_supervision.csv

Outputs:
- results/tables/ablation_placebo_sensitivity.csv
- results/tables/placebo_label_audit.csv
- results/figures/ablation_ap_comparison.png
- results/figures/placebo_lift_comparison.png
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

INPUT_PATH = PROCESSED_DIR / "blockchain_risk_panel_weak_supervision.csv"

OUTPUT_PATH = TABLE_DIR / "ablation_placebo_sensitivity.csv"
PLACEBO_AUDIT_PATH = TABLE_DIR / "placebo_label_audit.csv"

ABLATION_FIGURE_PATH = FIGURE_DIR / "ablation_ap_comparison.png"
PLACEBO_FIGURE_PATH = FIGURE_DIR / "placebo_lift_comparison.png"

LF_WEIGHTS = {
    "lf_transparent_top5": 0.20,
    "lf_anomaly_top5": 0.20,
    "lf_return_volume_joint": 0.15,
    "lf_range_drawdown_joint": 0.15,
    "lf_stablecoin_depeg": 0.15,
    "lf_defi_context_shock": 0.05,
    "lf_multimethod_consensus": 0.10,
}

ABLATION_SPECS = {
    "baseline_all_lfs": [],
    "drop_transparent_lf": ["lf_transparent_top5"],
    "drop_anomaly_lf": ["lf_anomaly_top5"],
    "drop_return_volume_lf": ["lf_return_volume_joint"],
    "drop_range_drawdown_lf": ["lf_range_drawdown_joint"],
    "drop_stablecoin_lf": ["lf_stablecoin_depeg"],
    "drop_defi_context_lf": ["lf_defi_context_shock"],
    "drop_multimethod_consensus_lf": ["lf_multimethod_consensus"],
    "market_only_lfs": [
        "lf_stablecoin_depeg",
        "lf_defi_context_shock",
    ],
    "context_only_lfs": [
        "lf_return_volume_joint",
        "lf_range_drawdown_joint",
        "lf_transparent_top5",
        "lf_anomaly_top5",
        "lf_multimethod_consensus",
    ],
}

K_SHARES = [0.01, 0.05, 0.10, 0.20]


def percentile_score(series):
    x = pd.to_numeric(series, errors="coerce").fillna(0)
    if x.nunique(dropna=True) <= 1:
        return pd.Series(0.0, index=x.index)
    return 100 * x.rank(pct=True)


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


def make_ablation_scores(df):
    out = df.copy()

    existing_lfs = [lf for lf in LF_WEIGHTS if lf in out.columns]

    for lf in existing_lfs:
        out[lf] = pd.to_numeric(out[lf], errors="coerce").fillna(0).astype(int)

    for spec_name, dropped in ABLATION_SPECS.items():
        keep_lfs = [lf for lf in existing_lfs if lf not in dropped]

        if not keep_lfs:
            raw = pd.Series(0.0, index=out.index)
        else:
            total_weight = sum(LF_WEIGHTS[lf] for lf in keep_lfs)
            raw = sum(out[lf] * LF_WEIGHTS[lf] for lf in keep_lfs)

            if total_weight > 0:
                raw = raw / total_weight

        out[f"score_{spec_name}"] = percentile_score(raw)

    return out


def make_placebo_labels(df):
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out["asset"] = out["asset"].astype(str).str.upper()

    out["placebo_7d_shift_plus_90"] = 0
    out["placebo_7d_shift_minus_90"] = 0
    out["placebo_7d_random_by_asset"] = 0

    key_index = {
        (asset, date): idx
        for idx, asset, date in out[["asset", "date"]].itertuples(index=True, name=None)
    }

    true_window = out[out["weak_label_7d"] == 1][["asset", "date"]].copy()

    for _, row in true_window.iterrows():
        asset = row["asset"]
        date = row["date"]

        plus_key = (asset, date + pd.Timedelta(days=90))
        minus_key = (asset, date - pd.Timedelta(days=90))

        if plus_key in key_index:
            out.loc[key_index[plus_key], "placebo_7d_shift_plus_90"] = 1

        if minus_key in key_index:
            out.loc[key_index[minus_key], "placebo_7d_shift_minus_90"] = 1

    rng = np.random.default_rng(42)

    for asset, sub in out.groupby("asset"):
        n_true = int(sub["weak_label_7d"].sum())
        if n_true <= 0:
            continue

        idx = sub.index.to_numpy()
        n_pick = min(n_true, len(idx))

        picked = rng.choice(idx, size=n_pick, replace=False)
        out.loc[picked, "placebo_7d_random_by_asset"] = 1

    audit_rows = []

    for label in [
        "weak_label_7d",
        "placebo_7d_shift_plus_90",
        "placebo_7d_shift_minus_90",
        "placebo_7d_random_by_asset",
    ]:
        audit_rows.append({
            "label": label,
            "positive_count": int(out[label].sum()),
            "positive_rate": out[label].mean(),
            "claim_boundary": "Placebo labels are validity checks; they are not alternative incident truths.",
        })

    placebo_audit = pd.DataFrame(audit_rows)

    return out, placebo_audit


def evaluate_all(df):
    rows = []

    score_cols = [c for c in df.columns if c.startswith("score_")]
    extra_scores = [
        "weak_supervision_score",
        "transparent_risk_score",
        "anomaly_ensemble_score",
    ]

    for col in extra_scores:
        if col in df.columns:
            score_cols.append(col)

    score_cols = sorted(set(score_cols))

    label_cols = [
        "weak_label_3d",
        "weak_label_7d",
        "placebo_7d_shift_plus_90",
        "placebo_7d_shift_minus_90",
        "placebo_7d_random_by_asset",
    ]

    for label_col in label_cols:
        if label_col not in df.columns:
            continue

        for score_col in score_cols:
            y = df[label_col].fillna(0).astype(int)
            s = df[score_col].fillna(0).astype(float)

            check_family = (
                "placebo"
                if label_col.startswith("placebo")
                else "main_weak_label"
            )

            score_family = (
                "ablation"
                if score_col.startswith("score_")
                else "benchmark_existing_score"
            )

            base = {
                "check_family": check_family,
                "score_family": score_family,
                "label": label_col,
                "method": score_col,
                "n_rows": len(df),
                "label_positive_count": int(y.sum()),
                "label_positive_rate": y.mean(),
                "average_precision": safe_metric(y, s, "average_precision"),
                "roc_auc": safe_metric(y, s, "roc_auc"),
                "claim_boundary": "Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth.",
            }

            for k_share in K_SHARES:
                row = base.copy()
                row.update(eval_at_k(df.assign(**{label_col: y}), label_col, score_col, k_share))
                rows.append(row)

    return pd.DataFrame(rows)


def make_figures(results):
    # Ablation AP comparison for weak_label_7d.
    ablation = results[
        (results["check_family"] == "main_weak_label")
        & (results["label"] == "weak_label_7d")
        & (results["score_family"] == "ablation")
        & (results["top_share"] == 0.05)
    ].copy()

    ablation = ablation.drop_duplicates(subset=["method"])
    ablation = ablation.sort_values("average_precision", ascending=False)

    plt.figure(figsize=(12, 5))
    plt.bar(ablation["method"], ablation["average_precision"])
    plt.title("Ablation check: AP against weak_label_7d")
    plt.ylabel("Average precision")
    plt.xlabel("Score variant")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(ABLATION_FIGURE_PATH, dpi=200)
    plt.close()

    # Placebo lift comparison for baseline weak-supervision score.
    placebo = results[
        (results["method"] == "weak_supervision_score")
        & (results["top_share"] == 0.05)
    ].copy()

    placebo = placebo[
        placebo["label"].isin([
            "weak_label_7d",
            "placebo_7d_shift_plus_90",
            "placebo_7d_shift_minus_90",
            "placebo_7d_random_by_asset",
        ])
    ]

    plt.figure(figsize=(10, 5))
    plt.bar(placebo["label"], placebo["lift_at_k"])
    plt.title("Placebo check: Lift@5% for weak-supervision score")
    plt.ylabel("Lift@5%")
    plt.xlabel("Label")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    plt.savefig(PLACEBO_FIGURE_PATH, dpi=200)
    plt.close()


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError("Missing blockchain_risk_panel_weak_supervision.csv. Run 08_weak_supervision_label_model.py first.")

    df = pd.read_csv(INPUT_PATH)
    df["date"] = pd.to_datetime(df["date"])

    ablated = make_ablation_scores(df)
    with_placebos, placebo_audit = make_placebo_labels(ablated)

    results = evaluate_all(with_placebos)

    results.to_csv(OUTPUT_PATH, index=False)
    placebo_audit.to_csv(PLACEBO_AUDIT_PATH, index=False)

    make_figures(results)

    print("Saved ablation/placebo/sensitivity table to:")
    print(OUTPUT_PATH)
    print()
    print(results.head(40))

    print()
    print("Saved placebo label audit to:")
    print(PLACEBO_AUDIT_PATH)
    print()
    print(placebo_audit)

    print()
    print("Saved figures:")
    print(ABLATION_FIGURE_PATH)
    print(PLACEBO_FIGURE_PATH)


if __name__ == "__main__":
    main()
