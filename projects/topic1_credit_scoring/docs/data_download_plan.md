# Topic 1 Data Download Plan

This document records the remaining raw-data preparation steps for the trustworthy credit scoring module.

## Current status

The UCI Default of Credit Card Clients dataset has been downloaded and saved as:

`projects/topic1_credit_scoring/data/raw/uci_default.csv`

The Freddie Mac Sample, HMDA Sample, and FRED Macro Rates files still need to be added to `data/raw/`.

## Required raw files

| File | Role | Required columns | Notes |
|---|---|---|---|
| `uci_default.csv` | baseline credit default modelling | `LIMIT_BAL`, `PAY_0`-`PAY_6`, `BILL_AMT1`-`BILL_AMT6`, `PAY_AMT1`-`PAY_AMT6`, `target_default` | already available |
| `freddie_sample.csv` | delinquency, vintage drift, multicalibration, conformal risk control | `credit_score`, `cltv`, `dti`, `interest_rate`, `ever_30_dpd`, `ever_90_dpd`, `vintage` | use Freddie Mac sample files, not full dataset |
| `hmda_sample.csv` | denial-risk and fairness-slice diagnostics | `derived_race`, `derived_ethnicity`, `derived_sex`, `income`, `action_taken`, `loan_purpose`, `target_denied` | use a filtered HMDA sample |
| `fred_macro.csv` | macro regime and interest-rate context | `date`, `FEDFUNDS`, `MORTGAGE30US` | CSV from FRED |

## Label boundary

- `target_default` means credit-card default.
- `ever_30_dpd` and `ever_90_dpd` mean mortgage delinquency.
- `target_denied` means mortgage application denial.
- These labels should not be described as the same risk event.
