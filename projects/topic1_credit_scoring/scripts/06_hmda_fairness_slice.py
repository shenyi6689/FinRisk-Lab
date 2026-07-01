"""
06_hmda_fairness_slice.py

Week 2 Topic 1: HMDA fairness-slice diagnostics.

Purpose:
Run group-level denial-risk and fairness-slice diagnostics on HMDA data.

If hmda_sample.csv is not available, this script writes transparent
data-unavailable status tables. It does not fabricate HMDA fairness results.

Expected input:
- data/raw/hmda_sample.csv

Expected columns:
- derived_race
- derived_ethnicity
- derived_sex
- income
- action_taken
- loan_purpose
- target_denied

If target_denied is missing, the script attempts to derive it from action_taken.

Outputs:
- results/tables/hmda_fairness_slice.csv
- results/tables/hmda_bootstrap_ci.csv
"""

from pathlib import Path
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import HistGradientBoostingClassifier


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic1_credit_scoring"
RAW_PATH = TOPIC_DIR / "data" / "raw" / "hmda_sample.csv"
RESULTS_DIR = TOPIC_DIR / "results" / "tables"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

FAIRNESS_PATH = RESULTS_DIR / "hmda_fairness_slice.csv"
BOOTSTRAP_PATH = RESULTS_DIR / "hmda_bootstrap_ci.csv"

REQUIRED_BASE_COLUMNS = [
    "derived_race",
    "derived_ethnicity",
    "derived_sex",
    "income",
    "action_taken",
    "loan_purpose",
]

GROUP_COLUMNS = [
    "derived_race",
    "derived_ethnicity",
    "derived_sex",
    "income_bucket",
]

LABEL = "target_denied"


def write_unavailable(reason):
    fairness = pd.DataFrame([
        {
            "dataset": "HMDA Fair-Lending Sample",
            "status": "not_available",
            "diagnostic": "fairness_slice",
            "reason": reason,
            "claim_boundary": (
                "HMDA fairness-slice diagnostics are not completed until an actual "
                "hmda_sample.csv file is added and this script is rerun."
            ),
        }
    ])

    bootstrap = pd.DataFrame([
        {
            "dataset": "HMDA Fair-Lending Sample",
            "status": "not_available",
            "diagnostic": "bootstrap_fairness_gap_ci",
            "reason": reason,
            "claim_boundary": (
                "Bootstrap confidence intervals are not completed until an actual "
                "hmda_sample.csv file is added and this script is rerun."
            ),
        }
    ])

    fairness.to_csv(FAIRNESS_PATH, index=False)
    bootstrap.to_csv(BOOTSTRAP_PATH, index=False)

    print(fairness)
    print()
    print(bootstrap)
    print()
    print("Saved status tables to:")
    print(FAIRNESS_PATH)
    print(BOOTSTRAP_PATH)


def make_onehot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def derive_target_denied(df):
    out = df.copy()

    if LABEL in out.columns:
        out[LABEL] = out[LABEL].astype(int)
        return out

    if "action_taken" not in out.columns:
        raise ValueError("Cannot derive target_denied because action_taken is missing.")

    # HMDA action_taken is often numeric-coded.
    # Common code: 3 = application denied.
    action = out["action_taken"]

    if pd.api.types.is_numeric_dtype(action):
        out[LABEL] = (action == 3).astype(int)
    else:
        lowered = action.astype(str).str.lower()
        out[LABEL] = lowered.str.contains("denied").astype(int)

    return out


def add_income_bucket(df):
    out = df.copy()
    out["income"] = pd.to_numeric(out["income"], errors="coerce")

    out["income_bucket"] = pd.cut(
        out["income"],
        bins=[-np.inf, 50, 100, 150, np.inf],
        labels=["low_income", "mid_income", "upper_mid_income", "high_income"],
    )

    return out


def make_fairness_slice_table(test):
    rows = []

    for group_col in GROUP_COLUMNS:
        for group_value, g in test.groupby(group_col, observed=True):
            n = len(g)

            if n < 50:
                support_flag = "low_support"
            else:
                support_flag = "sufficient_support"

            denied = g[LABEL].astype(int)
            score = g["score"]

            denial_rate = denied.mean()
            approval_rate = 1 - denial_rate

            # top 20% highest predicted denial-risk review slice
            threshold = np.quantile(score, 0.80)
            reviewed = score >= threshold

            if denied.sum() > 0:
                group_capture = denied[reviewed].sum() / denied.sum()
            else:
                group_capture = np.nan

            rows.append({
                "dataset": "HMDA Fair-Lending Sample",
                "status": "completed",
                "group_variable": group_col,
                "group_value": str(group_value),
                "n": n,
                "support_flag": support_flag,
                "denial_rate": denial_rate,
                "approval_rate": approval_rate,
                "mean_model_score": score.mean(),
                "top_20pct_group_capture": group_capture,
                "claim_boundary": (
                    "This is a fairness diagnostic slice. It is not legal "
                    "compliance proof and does not establish discrimination."
                ),
            })

    return pd.DataFrame(rows)


def bootstrap_gap_ci(test, group_col, reference_value, comparison_value, n_boot=500):
    ref = test[test[group_col].astype(str) == str(reference_value)].copy()
    comp = test[test[group_col].astype(str) == str(comparison_value)].copy()

    if len(ref) < 50 or len(comp) < 50:
        return None

    gaps = []

    for _ in range(n_boot):
        ref_sample = ref.sample(len(ref), replace=True)
        comp_sample = comp.sample(len(comp), replace=True)

        ref_approval = 1 - ref_sample[LABEL].mean()
        comp_approval = 1 - comp_sample[LABEL].mean()

        gaps.append(comp_approval - ref_approval)

    gaps = np.asarray(gaps)

    return {
        "dataset": "HMDA Fair-Lending Sample",
        "status": "completed",
        "group_variable": group_col,
        "reference_group": str(reference_value),
        "comparison_group": str(comparison_value),
        "gap_definition": "comparison approval rate minus reference approval rate",
        "bootstrap_mean_gap": gaps.mean(),
        "ci_lower_2_5pct": np.quantile(gaps, 0.025),
        "ci_upper_97_5pct": np.quantile(gaps, 0.975),
        "n_reference": len(ref),
        "n_comparison": len(comp),
        "claim_boundary": (
            "A confidence interval that does not cross zero indicates a "
            "statistically visible sample gap, not a legal discrimination claim."
        ),
    }


def make_bootstrap_table(test):
    rows = []

    for group_col in ["derived_race", "derived_ethnicity", "derived_sex"]:
        counts = test[group_col].astype(str).value_counts()

        if len(counts) < 2:
            continue

        reference_value = counts.index[0]

        for comparison_value in counts.index[1:4]:
            result = bootstrap_gap_ci(
                test,
                group_col,
                reference_value,
                comparison_value,
                n_boot=500,
            )
            if result is not None:
                rows.append(result)

    if not rows:
        return pd.DataFrame([
            {
                "dataset": "HMDA Fair-Lending Sample",
                "status": "not_enough_group_support",
                "diagnostic": "bootstrap_fairness_gap_ci",
                "reason": "No group pairs had enough support for bootstrap CI.",
                "claim_boundary": (
                    "Low-support groups should not be used for strong fairness claims."
                ),
            }
        ])

    return pd.DataFrame(rows)


def main():
    if not RAW_PATH.exists():
        write_unavailable("Missing data/raw/hmda_sample.csv")
        return

    df = pd.read_csv(RAW_PATH)

    missing = [col for col in REQUIRED_BASE_COLUMNS if col not in df.columns]
    if missing:
        write_unavailable(f"Missing required columns: {missing}")
        return

    df = derive_target_denied(df)
    df = add_income_bucket(df)

    modelling_columns = [
        "income",
        "loan_purpose",
        "derived_race",
        "derived_ethnicity",
        "derived_sex",
        "income_bucket",
        LABEL,
    ]

    df = df[modelling_columns].dropna(subset=[LABEL]).copy()

    if df[LABEL].nunique() < 2:
        write_unavailable("target_denied has only one class")
        return

    train, test = train_test_split(
        df,
        test_size=0.30,
        random_state=42,
        stratify=df[LABEL],
    )

    numeric_features = ["income"]
    categorical_features = [
        "loan_purpose",
        "derived_race",
        "derived_ethnicity",
        "derived_sex",
        "income_bucket",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", SimpleImputer(strategy="median"), numeric_features),
            (
                "cat",
                Pipeline([
                    ("imputer", SimpleImputer(strategy="most_frequent")),
                    ("onehot", make_onehot_encoder()),
                ]),
                categorical_features,
            ),
        ]
    )

    model = Pipeline([
        ("preprocessor", preprocessor),
        ("model", HistGradientBoostingClassifier(random_state=42)),
    ])

    X_train = train[numeric_features + categorical_features]
    y_train = train[LABEL].astype(int)

    X_test = test[numeric_features + categorical_features]
    y_test = test[LABEL].astype(int)

    model.fit(X_train, y_train)
    test = test.copy()
    test["score"] = model.predict_proba(X_test)[:, 1]

    fairness = make_fairness_slice_table(test)
    bootstrap = make_bootstrap_table(test)

    fairness.to_csv(FAIRNESS_PATH, index=False)
    bootstrap.to_csv(BOOTSTRAP_PATH, index=False)

    print("Saved HMDA fairness-slice table to:")
    print(FAIRNESS_PATH)
    print()
    print(fairness.head())

    print()
    print("Saved HMDA bootstrap CI table to:")
    print(BOOTSTRAP_PATH)
    print()
    print(bootstrap.head())


if __name__ == "__main__":
    main()
