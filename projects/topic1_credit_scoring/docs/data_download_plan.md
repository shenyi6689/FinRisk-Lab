# Topic 1 Data Download Plan

This document records the raw-data preparation status for the trustworthy credit scoring module.

## Current status

| Dataset | Status | File | Notes |
|---|---|---|---|
| UCI Default of Credit Card Clients | Available | `data/raw/uci_default.csv` | Downloaded using `00_download_uci.py` |
| FRED Macro Rates | Available | `data/raw/fred_macro.csv` | Downloaded using `00_download_fred.py` |
| HMDA Sample | Available | `data/raw/hmda_sample.csv` | Downloaded from HMDA Data Browser with geography and loan-purpose filters |
| Freddie Mac Sample | Available locally | `data/raw/freddie_sample.csv` | Prepared from Freddie Mac sample origination and servicing files using `00_prepare_freddie_sample.py` |

## Freddie Mac raw-data boundary

The Freddie Mac sample origination and servicing text files are stored locally under:

`projects/topic1_credit_scoring/data/raw/freddie/`

These raw files and the derived `freddie_sample.csv` are excluded from GitHub because they come from Freddie Mac's loan-level data access process. The conversion script is included so that the derived file can be reproduced locally after downloading the sample files.

## Required modelling columns

| File | Role | Required columns |
|---|---|---|
| `uci_default.csv` | baseline credit default modelling | `LIMIT_BAL`, `PAY_0`-`PAY_6`, `BILL_AMT1`-`BILL_AMT6`, `PAY_AMT1`-`PAY_AMT6`, `target_default` |
| `freddie_sample.csv` | delinquency, vintage drift, multicalibration, conformal risk control | `credit_score`, `cltv`, `dti`, `interest_rate`, `ever_30_dpd`, `ever_90_dpd`, `vintage` |
| `hmda_sample.csv` | denial-risk and fairness-slice diagnostics | `derived_race`, `derived_ethnicity`, `derived_sex`, `income`, `action_taken`, `loan_purpose`, `target_denied` or derivable `action_taken` |
| `fred_macro.csv` | macro regime and interest-rate context | `date`, `FEDFUNDS`, `MORTGAGE30US`, `DGS10`, `UNRATE` |

## Label boundary

- `target_default` means credit-card default.
- `ever_30_dpd` and `ever_90_dpd` mean mortgage delinquency.
- `target_denied` means mortgage application denial.
- These labels are not interchangeable and should not be described as the same risk event.
