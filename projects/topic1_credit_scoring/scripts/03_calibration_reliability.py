"""
03_calibration_reliability.py

Week 2 Topic 1: Trustworthy Credit Scoring

Purpose:
Evaluate whether UCI baseline model scores can be cautiously interpreted
as risk probabilities.

Outputs:
- results/tables/uci_calibration_table.csv
- results/tables/proper_score_decomposition.csv
- results/tables/venn_abers_or_reliability_summary.csv
- results/figures/uci_calibration_curve.png
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import brier_score_loss


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic1_credit_scoring"

PRED_PATH = TOPIC_DIR / "data" / "processed" / "uci_test_predictions.csv"
RESULTS_DIR = TOPIC_DIR / "results" / "tables"
FIGURES_DIR = TOPIC_DIR / "results" / "figures"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

N_BINS = 10


def make_calibration_table(y_true, scores, model_name, n_bins=10):
    df = pd.DataFrame({
        "y_true": y_true,
        "score": scores,
    }).copy()

    # Equal-frequency bins are more stable when scores are concentrated.
    df["bin"] = pd.qcut(
        df["score"],
        q=n_bins,
        labels=False,
        duplicates="drop",
    )

    rows = []
    n = len(df)

    for b, g in df.groupby("bin", observed=True):
        mean_score = g["score"].mean()
        default_rate = g["y_true"].mean()
        gap = mean_score - default_rate
        abs_gap = abs(gap)
        weight = len(g) / n

        rows.append({
            "model": model_name,
            "bin": int(b),
            "n": len(g),
            "score_min": g["score"].min(),
            "score_max": g["score"].max(),
            "mean_predicted_risk": mean_score,
            "realized_default_rate": default_rate,
            "calibration_gap_pred_minus_actual": gap,
            "abs_calibration_gap": abs_gap,
            "ece_component": weight * abs_gap,
        })

    return pd.DataFrame(rows)


def brier_decomposition(y_true, scores, model_name, n_bins=10):
    """
    Approximate Brier decomposition using calibration bins.

    Brier = Reliability - Resolution + Uncertainty

    Reliability: whether predicted probabilities match observed rates.
    Resolution: whether bins separate high-risk and low-risk groups.
    Uncertainty: baseline uncertainty from overall positive rate.
    """
    df = pd.DataFrame({
        "y_true": y_true,
        "score": scores,
    }).copy()

    df["bin"] = pd.qcut(
        df["score"],
        q=n_bins,
        labels=False,
        duplicates="drop",
    )

    n = len(df)
    overall_rate = df["y_true"].mean()

    reliability = 0.0
    resolution = 0.0

    for _, g in df.groupby("bin", observed=True):
        weight = len(g) / n
        mean_score = g["score"].mean()
        observed_rate = g["y_true"].mean()

        reliability += weight * (mean_score - observed_rate) ** 2
        resolution += weight * (observed_rate - overall_rate) ** 2

    uncertainty = overall_rate * (1 - overall_rate)
    brier = brier_score_loss(y_true, scores)

    return {
        "model": model_name,
        "brier_score": brier,
        "uncertainty": uncertainty,
        "resolution": resolution,
        "reliability": reliability,
        "brier_decomposition_check": reliability - resolution + uncertainty,
        "overall_default_rate": overall_rate,
        "n_bins": n_bins,
    }


def reliability_summary(calibration_table, model_name):
    subset = calibration_table[calibration_table["model"] == model_name].copy()

    ece = subset["ece_component"].sum()
    max_abs_gap = subset["abs_calibration_gap"].max()

    high_risk_bin = subset.sort_values("mean_predicted_risk").tail(1).iloc[0]
    high_risk_gap = high_risk_bin["calibration_gap_pred_minus_actual"]

    if high_risk_gap > 0:
        high_risk_interpretation = "high-risk bin overestimates realized default rate"
    elif high_risk_gap < 0:
        high_risk_interpretation = "high-risk bin underestimates realized default rate"
    else:
        high_risk_interpretation = "high-risk bin is exactly calibrated in this sample"

    return {
        "model": model_name,
        "expected_calibration_error": ece,
        "maximum_absolute_calibration_gap": max_abs_gap,
        "high_risk_bin": int(high_risk_bin["bin"]),
        "high_risk_mean_predicted_risk": high_risk_bin["mean_predicted_risk"],
        "high_risk_realized_default_rate": high_risk_bin["realized_default_rate"],
        "high_risk_calibration_gap": high_risk_gap,
        "interpretation": high_risk_interpretation,
        "diagnostic_boundary": (
            "This is a probability reliability diagnostic, not proof that the "
            "model is deployment-ready or legally compliant."
        ),
    }


def main():
    if not PRED_PATH.exists():
        raise FileNotFoundError(
            f"Missing predictions file: {PRED_PATH}. Run 02_uci_baseline.py first."
        )

    pred = pd.read_csv(PRED_PATH)

    y_true = pred["y_true"].astype(int)

    score_columns = [
        col for col in pred.columns
        if col.startswith("score_")
    ]

    if not score_columns:
        raise ValueError("No score columns found in uci_test_predictions.csv")

    calibration_tables = []
    decomposition_rows = []
    summary_rows = []

    plt.figure(figsize=(7, 6))
    plt.plot([0, 1], [0, 1], linestyle="--", label="perfect calibration")

    for score_col in score_columns:
        model_name = score_col.replace("score_", "")
        scores = pred[score_col].astype(float)

        cal = make_calibration_table(y_true, scores, model_name, N_BINS)
        calibration_tables.append(cal)

        decomposition_rows.append(
            brier_decomposition(y_true, scores, model_name, N_BINS)
        )

        summary_rows.append(
            reliability_summary(cal, model_name)
        )

        plot_df = cal.sort_values("mean_predicted_risk")
        plt.plot(
            plot_df["mean_predicted_risk"],
            plot_df["realized_default_rate"],
            marker="o",
            label=model_name,
        )

    calibration_table = pd.concat(calibration_tables, ignore_index=True)
    decomposition = pd.DataFrame(decomposition_rows)
    reliability = pd.DataFrame(summary_rows)

    calibration_table.to_csv(
        RESULTS_DIR / "uci_calibration_table.csv",
        index=False,
    )
    decomposition.to_csv(
        RESULTS_DIR / "proper_score_decomposition.csv",
        index=False,
    )
    reliability.to_csv(
        RESULTS_DIR / "venn_abers_or_reliability_summary.csv",
        index=False,
    )

    plt.xlabel("Mean predicted risk")
    plt.ylabel("Realized default rate")
    plt.title("UCI calibration curve")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "uci_calibration_curve.png", dpi=300)
    plt.close()

    print("Saved calibration table to:")
    print(RESULTS_DIR / "uci_calibration_table.csv")
    print()
    print(calibration_table)

    print()
    print("Saved proper score decomposition to:")
    print(RESULTS_DIR / "proper_score_decomposition.csv")
    print()
    print(decomposition)

    print()
    print("Saved reliability summary to:")
    print(RESULTS_DIR / "venn_abers_or_reliability_summary.csv")
    print()
    print(reliability)

    print()
    print("Saved calibration curve to:")
    print(FIGURES_DIR / "uci_calibration_curve.png")


if __name__ == "__main__":
    main()
