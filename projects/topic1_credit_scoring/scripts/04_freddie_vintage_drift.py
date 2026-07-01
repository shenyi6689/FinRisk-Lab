"""
04_freddie_vintage_drift.py

Week 2 Topic 1: Freddie Mac vintage and delinquency extension.

Purpose:
Evaluate whether delinquency risk and model performance change across vintages.

If freddie_sample.csv is not available, this script writes a transparent
data-unavailable status table. It does not fabricate Freddie Mac results.

Expected input:
- data/raw/freddie_sample.csv

Expected columns:
- credit_score
- cltv
- dti
- interest_rate
- ever_30_dpd
- ever_90_dpd
- vintage

Output:
- results/tables/freddie_vintage_drift.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic1_credit_scoring"
RAW_PATH = TOPIC_DIR / "data" / "raw" / "freddie_sample.csv"
RESULTS_DIR = TOPIC_DIR / "results" / "tables"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = RESULTS_DIR / "freddie_vintage_drift.csv"

REQUIRED_COLUMNS = [
    "credit_score",
    "cltv",
    "dti",
    "interest_rate",
    "ever_30_dpd",
    "ever_90_dpd",
    "vintage",
]


def write_unavailable(reason):
    out = pd.DataFrame([
        {
            "dataset": "Freddie Mac Sample",
            "status": "not_available",
            "diagnostic": "vintage_drift",
            "reason": reason,
            "claim_boundary": (
                "Freddie vintage drift is not completed until an actual "
                "freddie_sample.csv file is added and this script is rerun."
            ),
        }
    ])
    out.to_csv(OUTPUT_PATH, index=False)
    print(out)
    print()
    print("Saved status table to:")
    print(OUTPUT_PATH)


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
    df = df.dropna(subset=["ever_30_dpd", "vintage"])

    label = "ever_30_dpd"
    features = ["credit_score", "cltv", "dti", "interest_rate"]

    vintages = sorted(df["vintage"].dropna().unique())

    if len(vintages) < 2:
        write_unavailable("Need at least two vintages for vintage split")
        return

    split_point = int(len(vintages) * 0.7)
    train_vintages = vintages[:split_point]
    test_vintages = vintages[split_point:]

    train = df[df["vintage"].isin(train_vintages)].copy()
    test = df[df["vintage"].isin(test_vintages)].copy()

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("model", HistGradientBoostingClassifier(random_state=42)),
    ])

    model.fit(train[features], train[label].astype(int))
    test["score"] = model.predict_proba(test[features])[:, 1]

    rows = []

    for vintage, g in test.groupby("vintage"):
        y = g[label].astype(int)
        s = g["score"]

        if y.nunique() < 2:
            roc_auc = np.nan
            ap = np.nan
        else:
            roc_auc = roc_auc_score(y, s)
            ap = average_precision_score(y, s)

        rows.append({
            "dataset": "Freddie Mac Sample",
            "status": "completed",
            "label": label,
            "vintage": vintage,
            "n": len(g),
            "positive_rate": y.mean(),
            "roc_auc": roc_auc,
            "average_precision": ap,
            "brier_score": brier_score_loss(y, s),
            "claim_boundary": (
                "Vintage drift is association-based diagnostic evidence, "
                "not causal identification."
            ),
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_PATH, index=False)

    print(out)
    print()
    print("Saved Freddie vintage drift table to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
