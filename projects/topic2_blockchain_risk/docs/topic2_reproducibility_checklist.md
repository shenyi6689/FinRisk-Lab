# Topic 2 Reproducibility Checklist

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
