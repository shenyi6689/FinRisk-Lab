"""
12_write_topic2_report.py

Generate the final Topic 2 report, reproducibility checklist, and Topic 2 README.

Inputs:
- processed data files
- result tables
- result figures

Outputs:
- projects/topic2_blockchain_risk/docs/topic2_report.md
- projects/topic2_blockchain_risk/docs/topic2_reproducibility_checklist.md
- projects/topic2_blockchain_risk/README.md
"""

from pathlib import Path
import pandas as pd
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOPIC_DIR = PROJECT_ROOT / "projects" / "topic2_blockchain_risk"

PROCESSED_DIR = TOPIC_DIR / "data" / "processed"
TABLE_DIR = TOPIC_DIR / "results" / "tables"
FIGURE_DIR = TOPIC_DIR / "results" / "figures"
DOCS_DIR = TOPIC_DIR / "docs"

DOCS_DIR.mkdir(parents=True, exist_ok=True)

REPORT_PATH = DOCS_DIR / "topic2_report.md"
CHECKLIST_PATH = DOCS_DIR / "topic2_reproducibility_checklist.md"
README_PATH = TOPIC_DIR / "README.md"


def read_csv_safe(path):
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def fmt_num(x, digits=4):
    try:
        if pd.isna(x):
            return "NA"
        return f"{float(x):.{digits}f}"
    except Exception:
        return "NA"


def clean_cell(x, max_len=120):
    if pd.isna(x):
        return ""
    s = str(x)
    s = s.replace("\n", " ").replace("\r", " ")
    s = s.replace("|", "\\|")
    s = " ".join(s.split())
    if len(s) > max_len:
        s = s[:max_len - 3] + "..."
    return s


def markdown_table(df, max_rows=20, max_cols=10):
    if df is None or df.empty:
        return "_No table available._"

    d = df.head(max_rows).copy()

    if len(d.columns) > max_cols:
        d = d.iloc[:, :max_cols].copy()

    cols = list(d.columns)

    header = "| " + " | ".join(clean_cell(c, 60) for c in cols) + " |"
    divider = "| " + " | ".join("---" for _ in cols) + " |"

    rows = []
    for _, row in d.iterrows():
        rows.append("| " + " | ".join(clean_cell(row[c]) for c in cols) + " |")

    return "\n".join([header, divider] + rows)


def get_date_range(df):
    if df.empty or "date" not in df.columns:
        return "NA", "NA"

    dates = pd.to_datetime(df["date"], errors="coerce")
    if dates.notna().sum() == 0:
        return "NA", "NA"

    return str(dates.min().date()), str(dates.max().date())


def get_assets(df):
    if df.empty or "asset" not in df.columns:
        return []
    return sorted(df["asset"].dropna().astype(str).unique())


def get_eval_row(df, method=None, label="weak_label_7d", top_share=0.05):
    if df.empty:
        return {}

    d = df.copy()

    if "evaluation_scope" in d.columns:
        d = d[d["evaluation_scope"] == "all_assets"]

    if "label" in d.columns:
        d = d[d["label"] == label]

    if method is not None and "method" in d.columns:
        d = d[d["method"] == method]

    if "top_share" in d.columns:
        top_share_num = pd.to_numeric(d["top_share"], errors="coerce")
        d = d[np.isclose(top_share_num, top_share)]

    if d.empty:
        return {}

    return d.iloc[0].to_dict()


def write_report():
    panel = read_csv_safe(PROCESSED_DIR / "blockchain_risk_panel_weak_supervision.csv")
    scored_panel = read_csv_safe(PROCESSED_DIR / "blockchain_risk_panel_scored.csv")
    anomaly_panel = read_csv_safe(PROCESSED_DIR / "blockchain_risk_panel_anomaly.csv")
    incidents = read_csv_safe(PROCESSED_DIR / "incident_ledger_validated.csv")
    event_windows = read_csv_safe(PROCESSED_DIR / "event_windows.csv")

    layer_summary = read_csv_safe(TABLE_DIR / "data_layer_summary.csv")
    coverage = read_csv_safe(TABLE_DIR / "coverage_matrix.csv")
    incident_audit = read_csv_safe(TABLE_DIR / "incident_ledger_audit.csv")
    feature_audit = read_csv_safe(TABLE_DIR / "feature_audit.csv")
    feature_dictionary = read_csv_safe(TABLE_DIR / "feature_dictionary.csv")

    transparent_eval = read_csv_safe(TABLE_DIR / "transparent_risk_score_eval.csv")
    transparent_components = read_csv_safe(TABLE_DIR / "transparent_risk_score_components.csv")
    anomaly_eval = read_csv_safe(TABLE_DIR / "unsupervised_anomaly_benchmark.csv")
    anomaly_agreement = read_csv_safe(TABLE_DIR / "anomaly_method_agreement.csv")
    weak_eval = read_csv_safe(TABLE_DIR / "weak_supervision_label_model.csv")
    weak_lfs = read_csv_safe(TABLE_DIR / "weak_supervision_label_functions.csv")

    spillover = read_csv_safe(TABLE_DIR / "spillover_connectedness.csv")
    changepoints = read_csv_safe(TABLE_DIR / "change_point_timeline.csv")
    evt = read_csv_safe(TABLE_DIR / "evt_tail_risk.csv")

    ablation = read_csv_safe(TABLE_DIR / "ablation_placebo_sensitivity.csv")
    placebo = read_csv_safe(TABLE_DIR / "placebo_label_audit.csv")

    false_summary = read_csv_safe(TABLE_DIR / "false_alert_summary.csv")
    error_sample = read_csv_safe(TABLE_DIR / "error_review_sample.csv")

    sample_start, sample_end = get_date_range(panel)
    assets = get_assets(panel)

    n_panel = len(panel)
    n_assets = len(assets)
    n_incidents = len(incidents)
    n_event_windows = len(event_windows)

    transparent_row = get_eval_row(
        transparent_eval,
        method=None,
        label="weak_label_7d",
        top_share=0.05,
    )

    anomaly_row = get_eval_row(
        anomaly_eval,
        method="anomaly_ensemble_score",
        label="weak_label_7d",
        top_share=0.05,
    )

    weak_row = get_eval_row(
        weak_eval,
        method="weak_supervision_score",
        label="weak_label_7d",
        top_share=0.05,
    )

    report = f"""# Topic 2 Report: Blockchain Market-Integrity Risk Signals

## 1. Purpose and claim boundary

This topic builds a transparent research pipeline for blockchain-related market-integrity risk diagnostics.

The project does not claim confirmed fraud detection. Public event windows are weak labels. Anomaly scores are review signals. Spillover, change-point, and EVT outputs are descriptive diagnostics rather than causal identification.

The main claim boundary is:

- Event windows are weak labels, not verified fraud ground truth.
- Transparent scores are interpretable alert signals, not proof of manipulation.
- Unsupervised anomaly outputs are review candidates, not confirmed fraud cases.
- Weak-supervision label functions are noisy research rules.
- False-alert taxonomy is an error-review framework, not a verified false-positive rate.

## 2. Data scope

Sample period: {sample_start} to {sample_end}

Assets covered: {", ".join(assets) if assets else "NA"}

Main panel size: {n_panel} asset-day observations.

Number of assets: {n_assets}

Validated public incident events: {n_incidents}

Weak-label event-window rows: {n_event_windows}

## 3. Four-layer data coverage

The project uses four data layers:

1. Yahoo OHLCV market data.
2. Coin Metrics network and market context data where available.
3. DeFiLlama DEX, TVL, and stablecoin context data.
4. Public incident ledger and weak-label event windows.

### Data-layer summary

{markdown_table(layer_summary, max_rows=20)}

### Coverage matrix excerpt

{markdown_table(coverage, max_rows=30)}

## 4. Incident ledger and weak labels

The incident ledger records public blockchain-related events. These records are used to build event windows, but they are not treated as verified fraud labels.

### Incident audit

{markdown_table(incident_audit, max_rows=20)}

### Validated incident ledger

{markdown_table(incidents, max_rows=20)}

## 5. Feature engineering

The feature-engineered panel combines market features, stablecoin peg-deviation features, DeFi context features, Coin Metrics context where available, and weak-label event-window indicators.

### Feature dictionary

{markdown_table(feature_dictionary, max_rows=40)}

### Feature audit excerpt

{markdown_table(feature_audit, max_rows=30)}

## 6. Transparent risk score

The transparent score combines interpretable components, including return shocks, volume shocks, intraday instability, drawdown stress, stablecoin peg stress, DeFi volume context, and chain TVL context.

All-asset benchmark against weak_label_7d at top 5 percent alerts:

- Average precision: {fmt_num(transparent_row.get("average_precision"))}
- ROC-AUC: {fmt_num(transparent_row.get("roc_auc"))}
- Precision at 5 percent: {fmt_num(transparent_row.get("precision_at_k"))}
- Recall at 5 percent: {fmt_num(transparent_row.get("recall_at_k"))}
- Lift at 5 percent: {fmt_num(transparent_row.get("lift_at_k"))}

### Transparent score components

{markdown_table(transparent_components, max_rows=20)}

Main figures:

- results/figures/transparent_score_event_window_lift.png
- results/figures/transparent_score_timeseries.png

## 7. Unsupervised anomaly benchmark

The project benchmarks the transparent score against unsupervised anomaly methods:

- Isolation Forest
- Local Outlier Factor
- Robust z-score rule
- Ensemble average

All-asset anomaly ensemble benchmark against weak_label_7d at top 5 percent alerts:

- Average precision: {fmt_num(anomaly_row.get("average_precision"))}
- ROC-AUC: {fmt_num(anomaly_row.get("roc_auc"))}
- Precision at 5 percent: {fmt_num(anomaly_row.get("precision_at_k"))}
- Recall at 5 percent: {fmt_num(anomaly_row.get("recall_at_k"))}
- Lift at 5 percent: {fmt_num(anomaly_row.get("lift_at_k"))}

### Anomaly method agreement excerpt

{markdown_table(anomaly_agreement, max_rows=20)}

Main figures:

- results/figures/anomaly_event_window_lift.png
- results/figures/anomaly_method_ap_comparison.png

## 8. Weak-supervision label model

The weak-supervision model combines multiple noisy label functions into a composite score. Label functions include transparent-score tail alerts, anomaly-score tail alerts, return-volume joint stress, range-drawdown joint stress, stablecoin peg stress, DeFi context shock, and multi-method consensus.

All-asset weak-supervision benchmark against weak_label_7d at top 5 percent alerts:

- Average precision: {fmt_num(weak_row.get("average_precision"))}
- ROC-AUC: {fmt_num(weak_row.get("roc_auc"))}
- Precision at 5 percent: {fmt_num(weak_row.get("precision_at_k"))}
- Recall at 5 percent: {fmt_num(weak_row.get("recall_at_k"))}
- Lift at 5 percent: {fmt_num(weak_row.get("lift_at_k"))}

### Label-function summary

{markdown_table(weak_lfs, max_rows=20)}

Main figures:

- results/figures/weak_supervision_event_window_lift.png
- results/figures/weak_supervision_lf_coverage.png

## 9. Spillover, change-point, and EVT diagnostics

The project adds three diagnostic layers:

1. Spillover connectedness: whether asset correlations and score correlations differ around event windows.
2. Change-point timeline: whether aggregate risk-score breaks occur near public incident windows.
3. EVT tail risk: whether extreme return or stress tails can be summarized using POT-style tail diagnostics.

### Spillover connectedness excerpt

{markdown_table(spillover, max_rows=20)}

### Change-point timeline excerpt

{markdown_table(changepoints, max_rows=20)}

### EVT tail-risk excerpt

{markdown_table(evt, max_rows=30)}

Main figures:

- results/figures/spillover_connectedness_heatmap.png
- results/figures/changepoint_timeline.png
- results/figures/evt_tail_thresholds.png

## 10. Ablation, placebo, and sensitivity checks

The robustness layer checks whether the result depends on one label function, one scoring rule, or random/shifted placebo event labels.

### Placebo label audit

{markdown_table(placebo, max_rows=20)}

### Ablation and placebo excerpt

{markdown_table(ablation, max_rows=30)}

Main figures:

- results/figures/ablation_ap_comparison.png
- results/figures/placebo_lift_comparison.png

## 11. False-alert taxonomy and error review

The false-alert taxonomy classifies top alerts into event-window hits, stablecoin peg-stress non-events, multi-method market-stress non-events, DeFi context shocks, and isolated anomaly review cases.

### False-alert summary

{markdown_table(false_summary, max_rows=20)}

### Error-review sample excerpt

{markdown_table(error_sample, max_rows=30)}

Main figures:

- results/figures/false_alert_taxonomy_counts.png
- results/figures/false_alert_score_by_category.png

## 12. Reproducibility order

Run the scripts in this order:

    python projects/topic2_blockchain_risk/scripts/00_project_setup_topic2.py
    python projects/topic2_blockchain_risk/scripts/01_download_ohlcv.py
    python projects/topic2_blockchain_risk/scripts/02_download_context_data.py
    python projects/topic2_blockchain_risk/scripts/03_incident_ledger.py
    python projects/topic2_blockchain_risk/scripts/04_data_audit_coverage.py
    python projects/topic2_blockchain_risk/scripts/05_feature_engineering.py
    python projects/topic2_blockchain_risk/scripts/06_transparent_risk_score.py
    python projects/topic2_blockchain_risk/scripts/07_anomaly_ensemble.py
    python projects/topic2_blockchain_risk/scripts/08_weak_supervision_label_model.py
    python projects/topic2_blockchain_risk/scripts/09_spillover_changepoint_evt.py
    python projects/topic2_blockchain_risk/scripts/10_ablation_placebo_sensitivity.py
    python projects/topic2_blockchain_risk/scripts/11_false_alert_taxonomy.py
    python projects/topic2_blockchain_risk/scripts/12_write_topic2_report.py

## 13. Final interpretation

This topic provides a reproducible evidence base for blockchain market-integrity risk diagnostics. It has a complete data audit, event-window construction, transparent scoring, anomaly benchmarking, weak-supervision aggregation, advanced diagnostics, robustness checks, and error-review taxonomy.

The final interpretation should remain cautious: the pipeline supports review-prioritization and research diagnostics, not confirmed fraud detection, legal classification, or strict causal identification.
"""

    REPORT_PATH.write_text(report, encoding="utf-8")


def write_checklist():
    checklist = """# Topic 2 Reproducibility Checklist

## Repository structure

- [x] Topic folder exists.
- [x] Raw data folder exists.
- [x] Processed data folder exists.
- [x] Result tables folder exists.
- [x] Result figures folder exists.
- [x] Docs folder exists.
- [x] Scripts folder exists.

## Data layers

- [x] Yahoo OHLCV downloaded and audited.
- [x] Coin Metrics context downloaded where available and audit warnings recorded.
- [x] DeFiLlama context downloaded and audited.
- [x] Public incident ledger validated.
- [x] Weak-label event windows constructed.
- [x] Coverage matrix generated.

## Model and diagnostic layers

- [x] Feature-engineered blockchain risk panel generated.
- [x] Transparent risk score generated.
- [x] Unsupervised anomaly benchmark generated.
- [x] Weak-supervision label model generated.
- [x] Spillover connectedness diagnostics generated.
- [x] Change-point diagnostics generated.
- [x] EVT tail-risk diagnostics generated.
- [x] Ablation, placebo, and sensitivity checks generated.
- [x] False-alert taxonomy generated.
- [x] Error-review sample generated.

## Claim boundaries

- [x] The project does not claim confirmed fraud detection.
- [x] Public incident windows are described as weak labels.
- [x] Anomaly scores are described as review candidates.
- [x] Connectedness and change-point outputs are descriptive diagnostics, not causality.
- [x] EVT is described as tail-risk diagnostics, not manipulation proof.
- [x] False-alert taxonomy is described as an error-review framework, not a verified false-positive rate.

## Main outputs

- [x] data/processed/blockchain_risk_panel.csv
- [x] data/processed/blockchain_risk_panel_scored.csv
- [x] data/processed/blockchain_risk_panel_anomaly.csv
- [x] data/processed/blockchain_risk_panel_weak_supervision.csv
- [x] results/tables/coverage_matrix.csv
- [x] results/tables/transparent_risk_score_eval.csv
- [x] results/tables/unsupervised_anomaly_benchmark.csv
- [x] results/tables/weak_supervision_label_model.csv
- [x] results/tables/spillover_connectedness.csv
- [x] results/tables/change_point_timeline.csv
- [x] results/tables/evt_tail_risk.csv
- [x] results/tables/ablation_placebo_sensitivity.csv
- [x] results/tables/false_alert_summary.csv
- [x] docs/topic2_report.md

## Final note

This checklist confirms that Topic 2 has a reproducible pipeline and documented claim boundaries.
"""
    CHECKLIST_PATH.write_text(checklist, encoding="utf-8")


def write_readme():
    readme = """# Topic 2: Blockchain Market-Integrity Risk Signals

This topic builds a transparent and reproducible research pipeline for blockchain-related market-integrity risk diagnostics.

## Data layers

- Yahoo daily OHLCV data
- Coin Metrics context data where available
- DeFiLlama DEX, TVL, and stablecoin context data
- Public incident ledger
- Weak-label event windows

## Analysis layers

- Coverage matrix
- Feature engineering
- Transparent risk score
- Unsupervised anomaly benchmark
- Weak-supervision label model
- Spillover connectedness
- Change-point diagnostics
- EVT tail-risk diagnostics
- Ablation, placebo, and sensitivity checks
- False-alert taxonomy and error review

## Claim boundary

This topic does not claim confirmed fraud detection. Public event windows are weak labels, anomaly scores are review signals, and the taxonomy is an error-review framework.

## How to reproduce

Run the scripts in this order:

    python projects/topic2_blockchain_risk/scripts/00_project_setup_topic2.py
    python projects/topic2_blockchain_risk/scripts/01_download_ohlcv.py
    python projects/topic2_blockchain_risk/scripts/02_download_context_data.py
    python projects/topic2_blockchain_risk/scripts/03_incident_ledger.py
    python projects/topic2_blockchain_risk/scripts/04_data_audit_coverage.py
    python projects/topic2_blockchain_risk/scripts/05_feature_engineering.py
    python projects/topic2_blockchain_risk/scripts/06_transparent_risk_score.py
    python projects/topic2_blockchain_risk/scripts/07_anomaly_ensemble.py
    python projects/topic2_blockchain_risk/scripts/08_weak_supervision_label_model.py
    python projects/topic2_blockchain_risk/scripts/09_spillover_changepoint_evt.py
    python projects/topic2_blockchain_risk/scripts/10_ablation_placebo_sensitivity.py
    python projects/topic2_blockchain_risk/scripts/11_false_alert_taxonomy.py
    python projects/topic2_blockchain_risk/scripts/12_write_topic2_report.py

## Main report

See:

    projects/topic2_blockchain_risk/docs/topic2_report.md

## Main processed outputs

- data/processed/blockchain_risk_panel.csv
- data/processed/blockchain_risk_panel_scored.csv
- data/processed/blockchain_risk_panel_anomaly.csv
- data/processed/blockchain_risk_panel_weak_supervision.csv

## Main result tables

- results/tables/coverage_matrix.csv
- results/tables/transparent_risk_score_eval.csv
- results/tables/unsupervised_anomaly_benchmark.csv
- results/tables/weak_supervision_label_model.csv
- results/tables/spillover_connectedness.csv
- results/tables/change_point_timeline.csv
- results/tables/evt_tail_risk.csv
- results/tables/ablation_placebo_sensitivity.csv
- results/tables/false_alert_summary.csv

## Main figures

- results/figures/transparent_score_event_window_lift.png
- results/figures/anomaly_method_ap_comparison.png
- results/figures/weak_supervision_event_window_lift.png
- results/figures/spillover_connectedness_heatmap.png
- results/figures/changepoint_timeline.png
- results/figures/evt_tail_thresholds.png
- results/figures/ablation_ap_comparison.png
- results/figures/placebo_lift_comparison.png
- results/figures/false_alert_taxonomy_counts.png
"""
    README_PATH.write_text(readme, encoding="utf-8")


def main():
    write_report()
    write_checklist()
    write_readme()

    print("Saved Topic 2 report to:")
    print(REPORT_PATH)
    print()
    print("Saved reproducibility checklist to:")
    print(CHECKLIST_PATH)
    print()
    print("Updated Topic 2 README to:")
    print(README_PATH)


if __name__ == "__main__":
    main()
