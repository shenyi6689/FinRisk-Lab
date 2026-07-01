"""
05_multicalibration_conformal.py

Week 2 Topic 1: Multicalibration and conformal risk control.

Purpose:
Run subgroup-bin reliability diagnostics and conformal-style FNR risk-control
diagnostics on Freddie Mac delinquency data.

If freddie_sample.csv is not available, this script writes transparent
data-unavailable status tables. It does not fabricate results.

Expected input:
- data/raw/freddie_sample.csv

Expected columns:
- credit_score
- cltv
- dti
- interest_rate
- ever_30_dpd
- vintage

Outputs:
- results/tables/freddie_multicalibration.csv
- results/tables/conformal_risk_control.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic1_credit_scoring"
RAW_PATH = TOPIC_DIR / "data" / "raw" / "freddie_sample.csv"
RESULTS_DIR = TOPIC_DIR / "results" / "tables"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

MULTICAL_PATH = RESULTS_DIR / "freddie_multicalibration.csv"
CONFORMAL_PATH = RESULTS_DIR / "conformal_risk_control.csv"

REQUIRED_COLUMNS = [
    "credit_score",
    "cltv",
    "dti",
    "interest_rate",
    "ever_30_dpd",
    "vintage",
]

LABEL = "ever_30_dpd"
FEATURES = ["credit_score", "cltv", "dti", "interest_rate"]


def write_unavailable(reason):
    multical = pd.DataFrame([
        {
            "dataset": "Freddie Mac Sample",
            "status": "not_available",
            "diagnostic": "multicalibration",
            "reason": reason,
            "claim_boundary": (
                "Multicalibration is not completed until an actual "
                "freddie_sample.csv file is added and this script is rerun."
            ),
        }
    ])

    conformal = pd.DataFrame([
        {
            "dataset": "Freddie Mac Sample",
            "status": "not_available",
            "diagnostic": "conformal_fnr_control",
            "reason": reason,
            "claim_boundary": (
                "Conformal risk-control diagnostics are not completed until an actual "
                "freddie_sample.csv file is added and this script is rerun."
            ),
        }
    ])

    multical.to_csv(MULTICAL_PATH, index=False)
    conformal.to_csv(CONFORMAL_PATH, index=False)

    print(multical)
    print()
    print(conformal)
    print()
    print("Saved status tables to:")
    print(MULTICAL_PATH)
    print(CONFORMAL_PATH)


def assign_bins(df):
    out = df.copy()

    out["credit_score_bucket"] = pd.cut(
        out["credit_score"],
        bins=[0, 620, 680, 740, 850],
        labels=["low", "mid", "high", "very_high"],
        include_lowest=True,
    )

    out["cltv_bucket"] = pd.cut(
        out["cltv"],
        bins=[0, 60, 80, 95, 200],
        labels=["low_cltv", "mid_cltv", "high_cltv", "very_high_cltv"],
        include_lowest=True,
    )

    out["dti_bucket"] = pd.cut(
        out["dti"],
        bins=[0, 30, 43, 55, 100],
        labels=["low_dti", "mid_dti", "high_dti", "very_high_dti"],
        include_lowest=True,
    )

    out["score_decile"] = pd.qcut(
        out["score"],
        q=10,
        labels=False,
        duplicates="drop",
    )

    return out


def make_multicalibration_table(test):
    """
    This is a transparent HKRR-style diagnostic table.

    It reports subgroup-bin residuals before and after a simple group-bin
    residual correction. The purpose is diagnostic: subgroup-level probability
    reliability, not legal fairness proof.
    """
    rows = []

    subgroup_columns = [
        "credit_score_bucket",
        "cltv_bucket",
        "dti_bucket",
    ]

    for subgroup_col in subgroup_columns:
        grouped = test.groupby([subgroup_col, "score_decile"], observed=True)

        for keys, g in grouped:
            subgroup_value, score_decile = keys

            if len(g) < 30:
                support_flag = "low_support"
            else:
                support_flag = "sufficient_support"

            mean_score_before = g["score"].mean()
            realized_rate = g[LABEL].mean()
            residual_before = realized_rate - mean_score_before

            # Simple residual correction for diagnostic illustration.
            corrected_score = np.clip(g["score"] + residual_before, 0, 1)
            residual_after = realized_rate - corrected_score.mean()

            rows.append({
                "dataset": "Freddie Mac Sample",
                "status": "completed",
                "subgroup": subgroup_col,
                "subgroup_value": str(subgroup_value),
                "score_decile": score_decile,
                "n": len(g),
                "support_flag": support_flag,
                "mean_score_before": mean_score_before,
                "realized_rate": realized_rate,
                "residual_before_actual_minus_predicted": residual_before,
                "mean_score_after_simple_update": corrected_score.mean(),
                "residual_after_actual_minus_predicted": residual_after,
                "abs_residual_before": abs(residual_before),
                "abs_residual_after": abs(residual_after),
                "claim_boundary": (
                    "This table supports subgroup-level reliability diagnostics. "
                    "It is not legal fairness proof."
                ),
            })

    out = pd.DataFrame(rows)

    if len(out) > 0:
        before_max = out["abs_residual_before"].max()
        after_max = out["abs_residual_after"].max()
        out["max_abs_residual_before_all_bins"] = before_max
        out["max_abs_residual_after_all_bins"] = after_max

    return out


def make_conformal_table(test):
    """
    Conformal-style FNR control table.

    We report what happens when the highest-risk q share is sent to review.
    FNR risk means the share of true delinquency cases missed by the review rule.
    """
    rows = []

    y = test[LABEL].astype(int).to_numpy()
    score = test["score"].to_numpy()

    total_positives = y.sum()

    for target_fnr in [0.05, 0.10, 0.20, 0.30]:
        best_row = None

        for review_share in np.arange(0.05, 0.81, 0.05):
            threshold = np.quantile(score, 1 - review_share)
            reviewed = score >= threshold

            captured = y[reviewed].sum()
            missed = total_positives - captured

            capture_rate = captured / total_positives if total_positives > 0 else np.nan
            fnr_risk = missed / total_positives if total_positives > 0 else np.nan
            precision = captured / reviewed.sum() if reviewed.sum() > 0 else np.nan

            candidate = {
                "dataset": "Freddie Mac Sample",
                "status": "completed",
                "target_fnr": target_fnr,
                "review_share": review_share,
                "score_threshold": threshold,
                "review_count": int(reviewed.sum()),
                "captured_delinquency_count": int(captured),
                "missed_delinquency_count": int(missed),
                "total_delinquency_count": int(total_positives),
                "capture_rate": capture_rate,
                "fnr_risk": fnr_risk,
                "precision_in_reviewed_group": precision,
                "claim_boundary": (
                    "Conformal-style risk control constrains a selected error type "
                    "under this sample split. It is not a deployment guarantee."
                ),
            }

            if fnr_risk <= target_fnr:
                best_row = candidate
                break

        if best_row is None:
            best_row = candidate
            best_row["status"] = "target_not_reached"

        rows.append(best_row)

    return pd.DataFrame(rows)


def main():
    if not RAW_PATH.exists():
        write_unavailable("Missing data/raw/freddie_sample.csv")
        return

    df = pd.read_csv(RAW_PATH)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        write_unavailable(f"Missing required columns: {missing}")
        return

    df = df[REQUIRED_COLUMNS].copy()
    df = df.dropna(subset=[LABEL, "vintage"])

    vintages = sorted(df["vintage"].dropna().unique())

    if len(vintages) < 2:
        write_unavailable("Need at least two vintages for train/test vintage split")
        return

    split_point = int(len(vintages) * 0.7)
    train_vintages = vintages[:split_point]
    test_vintages = vintages[split_point:]

    train = df[df["vintage"].isin(train_vintages)].copy()
    test = df[df["vintage"].isin(test_vintages)].copy()

    if train[LABEL].nunique() < 2 or test[LABEL].nunique() < 2:
        write_unavailable("Train or test split has only one label class")
        return

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", HistGradientBoostingClassifier(random_state=42)),
    ])

    model.fit(train[FEATURES], train[LABEL].astype(int))
    test["score"] = model.predict_proba(test[FEATURES])[:, 1]

    test = assign_bins(test)

    multical = make_multicalibration_table(test)
    conformal = make_conformal_table(test)

    multical.to_csv(MULTICAL_PATH, index=False)
    conformal.to_csv(CONFORMAL_PATH, index=False)

    print("Saved multicalibration table to:")
    print(MULTICAL_PATH)
    print()
    print(multical.head())

    print()
    print("Saved conformal risk-control table to:")
    print(CONFORMAL_PATH)
    print()
    print(conformal)


if __name__ == "__main__":
    main()
