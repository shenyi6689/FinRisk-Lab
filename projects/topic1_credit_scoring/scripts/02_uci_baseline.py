"""
02_uci_baseline.py

Week 2 Topic 1: Trustworthy Credit Scoring

Purpose:
Run transparent UCI credit-scoring baselines and save model metrics,
threshold-policy tables, and test-set predictions.

Outputs:
- results/tables/uci_baseline_metrics.csv
- results/tables/uci_threshold_policy.csv
- data/processed/uci_test_predictions.csv
- results/tables/uci_model_config.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np

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
PROCESSED_DIR = TOPIC_DIR / "data" / "processed"
RESULTS_DIR = TOPIC_DIR / "results" / "tables"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

LABEL = "target_default"
RANDOM_STATE = 42
TEST_SIZE = 0.30


def top_k_capture(y_true, scores, q):
    """
    Capture@q:
    If the top q share of customers by model score is reviewed,
    what share of all true defaults is captured?
    """
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)

    threshold = np.quantile(scores, 1 - q)
    reviewed = scores >= threshold

    total_positives = y_true.sum()
    if total_positives == 0:
        return np.nan

    captured = y_true[reviewed].sum()
    return captured / total_positives


def threshold_policy_table(y_true, scores, model_name):
    rows = []
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)

    for q in [0.05, 0.10, 0.20]:
        threshold = np.quantile(scores, 1 - q)
        reviewed = scores >= threshold

        review_count = reviewed.sum()
        default_count = y_true.sum()
        captured_defaults = y_true[reviewed].sum()

        precision = captured_defaults / review_count if review_count > 0 else np.nan
        capture = captured_defaults / default_count if default_count > 0 else np.nan

        rows.append({
            "model": model_name,
            "review_share": q,
            "score_threshold": threshold,
            "review_count": int(review_count),
            "captured_defaults": int(captured_defaults),
            "total_defaults": int(default_count),
            "precision_in_reviewed_group": precision,
            "capture_rate": capture,
        })

    return rows


def main():
    if not RAW_PATH.exists():
        raise FileNotFoundError(
            f"Missing raw file: {RAW_PATH}. Run 00_download_uci.py first."
        )

    df = pd.read_csv(RAW_PATH)

    if LABEL not in df.columns:
        raise ValueError(f"Label column {LABEL} not found in {RAW_PATH}")

    X = df.drop(columns=[LABEL])
    y = df[LABEL].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    label_prevalence_train = y_train.mean()
    label_prevalence_test = y_test.mean()

    models = {
        "logistic_regression": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
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
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
    }

    metric_rows = []
    policy_rows = []
    prediction_frames = []

    for model_name, model in models.items():
        model.fit(X_train, y_train)
        scores = model.predict_proba(X_test)[:, 1]

        roc_auc = roc_auc_score(y_test, scores)
        avg_precision = average_precision_score(y_test, scores)
        brier = brier_score_loss(y_test, scores)

        metric_rows.append({
            "dataset": "UCI Default of Credit Card Clients",
            "model": model_name,
            "n_train": len(X_train),
            "n_test": len(X_test),
            "label": LABEL,
            "label_prevalence_train": label_prevalence_train,
            "label_prevalence_test": label_prevalence_test,
            "roc_auc": roc_auc,
            "average_precision": avg_precision,
            "brier_score": brier,
            "top_5pct_capture": top_k_capture(y_test, scores, 0.05),
            "top_10pct_capture": top_k_capture(y_test, scores, 0.10),
            "top_20pct_capture": top_k_capture(y_test, scores, 0.20),
        })

        policy_rows.extend(threshold_policy_table(y_test, scores, model_name))

        pred = pd.DataFrame({
            "row_id": X_test.index,
            "y_true": y_test.values,
            f"score_{model_name}": scores,
        })
        prediction_frames.append(pred)

    metrics = pd.DataFrame(metric_rows)
    policy = pd.DataFrame(policy_rows)

    predictions = prediction_frames[0]
    for frame in prediction_frames[1:]:
        predictions = predictions.merge(frame, on=["row_id", "y_true"], how="inner")

    config = pd.DataFrame([
        {
            "item": "train_test_split",
            "value": f"test_size={TEST_SIZE}, random_state={RANDOM_STATE}, stratify=target_default",
        },
        {
            "item": "preprocessing_logistic_regression",
            "value": "median imputation + standard scaling",
        },
        {
            "item": "preprocessing_hist_gradient_boosting",
            "value": "median imputation",
        },
        {
            "item": "logistic_regression_params",
            "value": "max_iter=1000, class_weight=balanced",
        },
        {
            "item": "hist_gradient_boosting_params",
            "value": "max_iter=200, learning_rate=0.05, max_leaf_nodes=31",
        },
    ])

    metrics.to_csv(RESULTS_DIR / "uci_baseline_metrics.csv", index=False)
    policy.to_csv(RESULTS_DIR / "uci_threshold_policy.csv", index=False)
    predictions.to_csv(PROCESSED_DIR / "uci_test_predictions.csv", index=False)
    config.to_csv(RESULTS_DIR / "uci_model_config.csv", index=False)

    print("Saved baseline metrics to:")
    print(RESULTS_DIR / "uci_baseline_metrics.csv")
    print()
    print(metrics)

    print()
    print("Saved threshold policy table to:")
    print(RESULTS_DIR / "uci_threshold_policy.csv")
    print()
    print(policy)

    print()
    print("Saved test predictions to:")
    print(PROCESSED_DIR / "uci_test_predictions.csv")


if __name__ == "__main__":
    main()
