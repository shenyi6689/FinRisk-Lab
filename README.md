# FinRisk Lab

## Project motivation

This project builds a reproducible research structure for financial technology and financial risk analysis. The lab focuses on three areas: credit scoring, blockchain risk, and geopolitical ETF volatility. The purpose is not only to produce model outputs, but also to create a clear research archive where data sources, scripts, results, and claim boundaries can be traced.

## Topics

### Topic 1: Credit scoring

This topic studies credit risk prediction and model reliability. The focus is on whether baseline credit scoring models produce stable and interpretable results across borrower groups.

### Topic 2: Blockchain risk

This topic studies blockchain-related risk signals using incident ledgers or weak-label risk indicators. The focus is on building a transparent evidence base rather than claiming confirmed fraud detection.

### Topic 3: Geopolitical ETF volatility

This topic studies whether geopolitical events are associated with changes in ETF volatility. The focus is on event-window evidence and volatility comparison, not strict causal identification.

## Data

Each topic will maintain separate raw and processed data folders.

- `data/raw/`: original downloaded data, not manually edited.
- `data/processed/`: cleaned model-ready datasets.
- `results/`: model outputs, figures, diagnostic tables, and robustness results.
- `docs/`: research notes, evidence explanations, and claim-boundary documentation.

Large raw datasets will not be committed directly to GitHub. Instead, their sources, download methods, sample periods, and reproducibility notes will be recorded in the dataset manifest.

## Methods

The project will begin with simple baseline models and descriptive evidence. Later stages may include extended diagnostics, robustness checks, calibration analysis, event-window analysis, and subgroup-level comparison.

The general workflow is:

raw data → schema check → type conversion → missing audit → feature table → model-ready panel → results

## Evidence artifacts

Each important result should be linked to the script that generated it, the conclusion it supports, and the boundary of that conclusion.

| Artifact | Script | Supports | Boundary |
|---|---|---|---|
| Baseline metrics | baseline script | baseline ranking or calibration evidence | not deployment-ready |
| Credit subgroup diagnostics | credit analysis script | subgroup residual check | not legal fairness proof |
| Blockchain weak-label summary | blockchain analysis script | noisy alert benchmark | not fraud ground truth |
| Geopolitical event-window table | geo analysis script | volatility model comparison | not causal identification |

## Results

Results will be added after each topic produces initial tables, figures, or model outputs. Each result will be stored in the corresponding topic-level `results/` folder.

## Limitations

This project does not claim that fairness diagnostics are equivalent to legal compliance proof. It also does not treat weak labels as verified true labels. For geopolitical event-window analysis, the results should be interpreted as association-based evidence rather than strict causal identification.

## How to run

First, install the required packages:

pip install -r requirements.txt

Then run the scripts inside each topic folder. Outputs will be saved in the corresponding `results/` folder.
