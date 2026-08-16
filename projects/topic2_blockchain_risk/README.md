# Topic 2: Blockchain Market-Integrity Risk Signals

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
