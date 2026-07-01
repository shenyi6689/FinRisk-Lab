from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic1_credit_scoring"
TABLE_DIR = TOPIC_DIR / "results" / "tables"
DOC_DIR = TOPIC_DIR / "docs"
REPORT_PATH = DOC_DIR / "topic1_report.md"

DOC_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_file(filename):
    path = TABLE_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def fmt_value(x):
    if pd.isna(x):
        return ""
    if isinstance(x, float):
        return f"{x:.4f}"
    return str(x).replace("\n", " ").replace("|", "/")


def make_markdown_table(df, columns=None, max_rows=12):
    if df.empty:
        return "_No table available._"

    out = df.copy()

    if columns is not None:
        existing = [c for c in columns if c in out.columns]
        out = out[existing]

    out = out.head(max_rows)

    if out.empty:
        return "_No matching columns available._"

    headers = list(out.columns)
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for _, row in out.iterrows():
        lines.append("| " + " | ".join(fmt_value(row[c]) for c in headers) + " |")

    return "\n".join(lines)


schema = read_csv_file("schema_audit.csv")
uci_metrics = read_csv_file("uci_baseline_metrics.csv")
uci_policy = read_csv_file("uci_threshold_policy.csv")
decomposition = read_csv_file("proper_score_decomposition.csv")
reliability = read_csv_file("venn_abers_or_reliability_summary.csv")
freddie_vintage = read_csv_file("freddie_vintage_drift.csv")
freddie_multi = read_csv_file("freddie_multicalibration.csv")
conformal = read_csv_file("conformal_risk_control.csv")
hmda_fairness = read_csv_file("hmda_fairness_slice.csv")
hmda_bootstrap = read_csv_file("hmda_bootstrap_ci.csv")
robustness = read_csv_file("robustness_summary.csv")
error_review = read_csv_file("error_review_sample.csv")

sections = []

sections.append("# Topic 1 Report: Trustworthy Credit Scoring\n")

sections.append("""
## Research motivation

This module studies trustworthy credit scoring as a financial-risk diagnostic problem. The goal is not only to rank borrowers by risk, but also to examine whether model scores are reliable, stable across samples, interpretable as probabilities, and cautious across subgroup and threshold-policy settings.

The module covers four data roles: UCI credit-card default modelling, Freddie Mac mortgage delinquency diagnostics, HMDA denial-risk and fairness-slice diagnostics, and FRED macro-rate context.
""")

sections.append("""
## Data and label definitions

The labels in this module have different meanings and should not be treated as interchangeable.

- `target_default`: credit-card default in the UCI dataset.
- `ever_30_dpd`: whether a Freddie Mac mortgage loan ever became at least 30 days past due.
- `ever_90_dpd`: whether a Freddie Mac mortgage loan ever became at least 90 days past due.
- `target_denied`: whether a mortgage application was denied in the HMDA sample.
- FRED macro rates are contextual variables, not risk labels.
""")

sections.append("## Schema audit\n")
sections.append(make_markdown_table(
    schema,
    ["dataset", "file_status", "n_rows", "n_features", "label", "positive_rate", "date_or_vintage_field", "risk_meaning"],
    10
))

sections.append("\n\n## UCI baseline results\n")
sections.append("Two transparent baseline models were estimated on the UCI credit-card default dataset. The evaluation focuses on ranking quality, probability quality, and top-risk capture rather than raw accuracy.\n")
sections.append(make_markdown_table(
    uci_metrics,
    ["model", "n_train", "n_test", "label_prevalence_test", "roc_auc", "average_precision", "brier_score", "top_5pct_capture", "top_10pct_capture", "top_20pct_capture"],
    10
))

sections.append("\n\nThe threshold-policy table asks what happens if only the highest-risk 5%, 10%, or 20% of cases are reviewed.\n")
sections.append(make_markdown_table(
    uci_policy,
    ["model", "review_share", "score_threshold", "review_count", "captured_defaults", "total_defaults", "precision_in_reviewed_group", "capture_rate"],
    12
))

sections.append("\n\n## Calibration and probability reliability\n")
sections.append("A high AUC does not imply that predicted probabilities can be directly interpreted as realized default probabilities. Calibration was therefore evaluated through equal-frequency bins, a calibration curve, Brier decomposition, and a reliability summary.\n")
sections.append(make_markdown_table(
    reliability,
    ["model", "expected_calibration_error", "maximum_absolute_calibration_gap", "high_risk_mean_predicted_risk", "high_risk_realized_default_rate", "interpretation"],
    10
))

sections.append("\n\n")
sections.append(make_markdown_table(
    decomposition,
    ["model", "brier_score", "uncertainty", "resolution", "reliability", "overall_default_rate"],
    10
))

sections.append("\n\nThe calibration figure is saved as `projects/topic1_credit_scoring/results/figures/uci_calibration_curve.png`.\n")

sections.append("\n## Freddie Mac vintage drift\n")
sections.append("The Freddie Mac sample was prepared from origination and servicing files for two vintages. The target used here is `ever_30_dpd`, which is a delinquency outcome rather than a legal default label.\n")
sections.append(make_markdown_table(
    freddie_vintage,
    ["status", "label", "vintage", "n", "positive_rate", "roc_auc", "average_precision", "brier_score"],
    10
))
sections.append("\n\nThis table should be interpreted as vintage-drift diagnostic evidence, not causal identification.\n")

sections.append("\n## Multicalibration and conformal risk control\n")
sections.append("The multicalibration diagnostic checks subgroup-bin residuals across score buckets, CLTV buckets, DTI buckets, and model score deciles.\n")
sections.append(make_markdown_table(
    freddie_multi,
    ["status", "subgroup", "subgroup_value", "score_decile", "n", "support_flag", "realized_rate", "residual_before_actual_minus_predicted", "residual_after_actual_minus_predicted"],
    12
))

sections.append("\n\nThe conformal-style risk-control table reports review-share requirements under different target false-negative-risk levels.\n")
sections.append(make_markdown_table(
    conformal,
    ["status", "target_fnr", "review_share", "score_threshold", "review_count", "captured_delinquency_count", "missed_delinquency_count", "capture_rate", "fnr_risk", "precision_in_reviewed_group"],
    10
))
sections.append("\n\nThese outputs are threshold-policy diagnostics. They are not deployment guarantees.\n")

sections.append("\n## HMDA fairness slice\n")
sections.append("The HMDA sample is used to model mortgage application denial rather than future borrower default. The fairness-slice table reports group-level denial rates, approval rates, mean model score, and top-risk capture.\n")
sections.append(make_markdown_table(
    hmda_fairness,
    ["status", "group_variable", "group_value", "n", "support_flag", "denial_rate", "approval_rate", "mean_model_score", "top_20pct_group_capture"],
    12
))

sections.append("\n\nBootstrap confidence intervals are used to check whether selected group-level approval-rate gaps are statistically visible in the sample.\n")
sections.append(make_markdown_table(
    hmda_bootstrap,
    ["status", "group_variable", "reference_group", "comparison_group", "bootstrap_mean_gap", "ci_lower_2_5pct", "ci_upper_97_5pct", "n_reference", "n_comparison"],
    12
))
sections.append("\n\nThese are fairness diagnostics, not legal discrimination findings.\n")

sections.append("\n## Robustness and error review\n")
sections.append("Robustness checks were performed across multiple random seeds. The purpose is to evaluate whether core metrics are stable across train/test splits.\n")
sections.append(make_markdown_table(
    robustness,
    ["table_section", "model", "random_seed", "roc_auc", "average_precision", "brier_score", "top_10pct_capture", "roc_auc_mean", "roc_auc_std", "average_precision_mean", "average_precision_std"],
    16
))

sections.append("\n\nThe error-review sample includes high-score non-default cases and low-score default cases. These cases help diagnose model failure modes, but they are not causal explanations.\n")
sections.append(make_markdown_table(
    error_review,
    ["row_id", "y_true", "score_logistic_regression", "score_hist_gradient_boosting", "error_taxonomy", "LIMIT_BAL", "AGE", "PAY_0", "PAY_2"],
    12
))

sections.append("""
## Claim boundary

This module is a research-oriented credit scoring diagnostic.

Fairness diagnostics are not legal compliance proof. Group-level gaps, approval-rate differences, or bootstrap confidence intervals can show statistically visible differences in the sample, but they do not establish a legal discrimination claim.

Weak labels, derived labels, delinquency labels, denial labels, and default labels are not the same risk event.

Baseline credit scores are not deployment-ready lending decisions. They are used to evaluate ranking, probability reliability, threshold policy, vintage drift, and subgroup-level diagnostics.

Calibration, multicalibration, conformal risk control, and threshold-policy tables support cautious model interpretation. They do not remove label bias, sample selection, omitted-variable problems, macroeconomic confounding, or institutional constraints.

## How to reproduce

Run the scripts in this order:

1. `python projects/topic1_credit_scoring/scripts/00_download_uci.py`
2. `python projects/topic1_credit_scoring/scripts/00_download_fred.py`
3. `python projects/topic1_credit_scoring/scripts/00_prepare_freddie_sample.py`
4. `python projects/topic1_credit_scoring/scripts/01_schema_audit.py`
5. `python projects/topic1_credit_scoring/scripts/02_uci_baseline.py`
6. `python projects/topic1_credit_scoring/scripts/03_calibration_reliability.py`
7. `python projects/topic1_credit_scoring/scripts/04_freddie_vintage_drift.py`
8. `python projects/topic1_credit_scoring/scripts/05_multicalibration_conformal.py`
9. `python projects/topic1_credit_scoring/scripts/06_hmda_fairness_slice.py`
10. `python projects/topic1_credit_scoring/scripts/07_robustness_error_review.py`
11. `python projects/topic1_credit_scoring/scripts/08_write_topic1_report.py`

Freddie Mac raw files are not committed to GitHub. They must be downloaded locally before running `00_prepare_freddie_sample.py`.
""")

REPORT_PATH.write_text("\n".join(sections), encoding="utf-8")

print("Saved Topic 1 report to:")
print(REPORT_PATH)
