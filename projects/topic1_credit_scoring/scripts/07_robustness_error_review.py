"""
07_robustness_error_review.py

Week 2 Topic 1: Robustness and error review.

Purpose:
Run UCI robustness checks across several random seeds and create an error
review sample for high-score non-defaults and low-score defaults.

Outputs:
- results/tables/robustness_summary.csv
- results/tables/error_review_sample.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic1_credit_scoring"

RAW_PATH = TOPIC_DIR / "data" / "raw" / "uci_default.csv"
PRED_PATH = TOPIC_DIR / "data" / "processed" / "uci_test_predictions.csv"
RESULTS_DIR = TOPIC_DIR / "results" / "tables"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ROBUSTNESS_PATH = RESULTS_DIR / "robustness_summary.csv"
ERROR_REVIEW_PATH = RESULTS_DIR / "error_review_sample.csv"

LABEL = "target_default"
SEEDS = [7, 21, 42, 84, 202]
TEST_SIZE = 0.30


def top_k_capture(y_true, scores, q):
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)

    threshold = np.quantile(scores, 1 - q)
    reviewed = scores >= threshold

    total_positives = y_true.sum()
    if total_positives == 0:
        return np.nan

    return y_true[reviewed].sum() / total_positives


def get_models(seed):
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=seed,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        max_iter=200,
                        learning_rate=0.05,
                        max_leaf_nodes=31,
                        random_state=seed,
                    ),
                ),
            ]
        ),
    }


def run_robustness(df):
    X = df.drop(columns=[LABEL])
    y = df[LABEL].astype(int)

    rows = []

    for seed in SEEDS:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=TEST_SIZE,
            random_state=seed,
            stratify=y,
        )

        for model_name, model in get_models(seed).items():
            model.fit(X_train, y_train)
            scores = model.predict_proba(X_test)[:, 1]

            rows.append({
                "dataset": "UCI Default of Credit Card Clients",
                "model": model_name,
                "random_seed": seed,
                "n_train": len(X_train),
                "n_test": len(X_test),
                "label_prevalence_test": y_test.mean(),
                "roc_auc": roc_auc_score(y_test, scores),
                "average_precision": average_precision_score(y_test, scores),
                "brier_score": brier_score_loss(y_test, scores),
                "top_10pct_capture": top_k_capture(y_test, scores, 0.10),
                "claim_boundary": (
                    "Robustness across seeds supports stability diagnostics, "
                    "not deployment readiness."
                ),
            })

    detail = pd.DataFrame(rows)

    summary = (
        detail
        .groupby(["dataset", "model"], as_index=False)
        .agg(
            n_runs=("random_seed", "count"),
            roc_auc_mean=("roc_auc", "mean"),
            roc_auc_std=("roc_auc", "std"),
            average_precision_mean=("average_precision", "mean"),
            average_precision_std=("average_precision", "std"),
            brier_score_mean=("brier_score", "mean"),
            brier_score_std=("brier_score", "std"),
            top_10pct_capture_mean=("top_10pct_capture", "mean"),
            top_10pct_capture_std=("top_10pct_capture", "std"),
            label_prevalence_test_mean=("label_prevalence_test", "mean"),
        )
    )

    summary["claim_boundary"] = (
        "This table checks whether core metrics are stable across random seeds. "
        "It does not prove that the score is suitable for lending deployment."
    )

    # Keep both run-level and summary-level information in one CSV.
    detail["table_section"] = "run_level"
    summary["table_section"] = "summary"

    # Align columns.
    combined = pd.concat(
        [detail, summary],
        ignore_index=True,
        sort=False,
    )

    return combined


def classify_error(row):
    y = row["y_true"]
    score = row["score_hist_gradient_boosting"]

    if y == 0 and score >= 0.70:
        return "high_score_non_default_false_alarm"
    if y == 1 and score <= 0.20:
        return "low_score_default_missed_risk"
    if y == 1 and score >= 0.70:
        return "high_score_default_correct_high_risk"
    if y == 0 and score <= 0.20:
        return "low_score_non_default_correct_low_risk"
    return "middle_score_case"


def make_error_review(df):
    if not PRED_PATH.exists():
        raise FileNotFoundError(
            f"Missing predictions file: {PRED_PATH}. Run 02_uci_baseline.py first."
        )

    pred = pd.read_csv(PRED_PATH)

    merged = pred.merge(
        df.reset_index().rename(columns={"index": "row_id"}),
        on="row_id",
        how="left",
    )

    merged["error_taxonomy"] = merged.apply(classify_error, axis=1)

    # Select interpretable error-review examples.
    high_score_non_default = (
        merged[merged["error_taxonomy"] == "high_score_non_default_false_alarm"]
        .sort_values("score_hist_gradient_boosting", ascending=False)
        .head(25)
    )

    low_score_default = (
        merged[merged["error_taxonomy"] == "low_score_default_missed_risk"]
        .sort_values("score_hist_gradient_boosting", ascending=True)
        .head(25)
    )

    sample = pd.concat(
        [high_score_non_default, low_score_default],
        ignore_index=True,
    )

    if len(sample) == 0:
        sample = (
            merged
            .sort_values("score_hist_gradient_boosting", ascending=False)
            .head(50)
            .copy()
        )
        sample["error_taxonomy"] = "fallback_high_score_review_sample"

    review_columns = [
        "row_id",
        "y_true",
        "score_logistic_regression",
        "score_hist_gradient_boosting",
        "error_taxonomy",
        "LIMIT_BAL",
        "SEX",
        "EDUCATION",
        "MARRIAGE",
        "AGE",
        "PAY_0",
        "PAY_2",
        "PAY_3",
        "PAY_4",
        "PAY_5",
        "PAY_6",
        "BILL_AMT1",
        "BILL_AMT2",
        "BILL_AMT3",
        "PAY_AMT1",
        "PAY_AMT2",
        "PAY_AMT3",
    ]

    existing_columns = [col for col in review_columns if col in sample.columns]
    sample = sample[existing_columns].copy()

    sample["review_note"] = (
        "Manual error review sample. High-score non-defaults may indicate "
        "conservative risk scoring; low-score defaults may indicate missed risk. "
        "These are diagnostic cases, not causal explanations."
    )

    return sample


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Missing raw UCI data: {RAW_PATH}. Run 00_download_uci.py first."
        )

    df = pd.read_csv(RAW_PATH)

    if LABEL not in df.columns:
        raise ValueError(f"Missing label column: {LABEL}")

    robustness = run_robustness(df)
    error_review = make_error_review(df)

    robustness.to_csv(ROBUSTNESS_PATH, index=False)
    error_review.to_csv(ERROR_REVIEW_PATH, index=False)

    print("Saved robustness summary to:")
    print(ROBUSTNESS_PATH)
    print()
    print(robustness.head(10))

    print()
    print("Saved error review sample to:")
    print(ERROR_REVIEW_PATH)
    print()
    print(error_review.head(10))


if __name__ == "__main__":
    main()
