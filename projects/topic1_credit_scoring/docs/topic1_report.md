# Topic 1 Report: Trustworthy Credit Scoring


## Research motivation

This module studies trustworthy credit scoring as a financial-risk diagnostic problem. The goal is not only to rank borrowers by risk, but also to examine whether model scores are reliable, stable across samples, interpretable as probabilities, and cautious across subgroup and threshold-policy settings.

The module covers four data roles: UCI credit-card default modelling, Freddie Mac mortgage delinquency diagnostics, HMDA denial-risk and fairness-slice diagnostics, and FRED macro-rate context.


## Data and label definitions

The labels in this module have different meanings and should not be treated as interchangeable.

- `target_default`: credit-card default in the UCI dataset.
- `ever_30_dpd`: whether a Freddie Mac mortgage loan ever became at least 30 days past due.
- `ever_90_dpd`: whether a Freddie Mac mortgage loan ever became at least 90 days past due.
- `target_denied`: whether a mortgage application was denied in the HMDA sample.
- FRED macro rates are contextual variables, not risk labels.

## Schema audit

| dataset | file_status | n_rows | n_features | label | positive_rate | date_or_vintage_field | risk_meaning |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UCI Default of Credit Card Clients | available | 30000 | 24 | target_default | 0.2212 | none; random split only | default |
| Freddie Mac Sample | available | 100000 | 8 | ever_30_dpd | 0.1018 | vintage | delinquency |
| HMDA Fair-Lending Sample | available | 18743 | 99 | target_denied |  | activity_year | denial |
| FRED Macro Rates | available | 17217 | 5 | none |  | date | macro context |


## UCI baseline results

Two transparent baseline models were estimated on the UCI credit-card default dataset. The evaluation focuses on ranking quality, probability quality, and top-risk capture rather than raw accuracy.

| model | n_train | n_test | label_prevalence_test | roc_auc | average_precision | brier_score | top_5pct_capture | top_10pct_capture | top_20pct_capture |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| logistic_regression | 21000 | 9000 | 0.2212 | 0.7159 | 0.4957 | 0.2080 | 0.1683 | 0.2983 | 0.4797 |
| hist_gradient_boosting | 21000 | 9000 | 0.2212 | 0.7773 | 0.5493 | 0.1359 | 0.1668 | 0.3114 | 0.5063 |


The threshold-policy table asks what happens if only the highest-risk 5%, 10%, or 20% of cases are reviewed.

| model | review_share | score_threshold | review_count | captured_defaults | total_defaults | precision_in_reviewed_group | capture_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| logistic_regression | 0.0500 | 0.7951 | 450 | 335 | 1991 | 0.7444 | 0.1683 |
| logistic_regression | 0.1000 | 0.7236 | 900 | 594 | 1991 | 0.6600 | 0.2983 |
| logistic_regression | 0.2000 | 0.5746 | 1800 | 955 | 1991 | 0.5306 | 0.4797 |
| hist_gradient_boosting | 0.0500 | 0.6999 | 450 | 332 | 1991 | 0.7378 | 0.1668 |
| hist_gradient_boosting | 0.1000 | 0.6003 | 900 | 620 | 1991 | 0.6889 | 0.3114 |
| hist_gradient_boosting | 0.2000 | 0.3146 | 1800 | 1008 | 1991 | 0.5600 | 0.5063 |


## Calibration and probability reliability

A high AUC does not imply that predicted probabilities can be directly interpreted as realized default probabilities. Calibration was therefore evaluated through equal-frequency bins, a calibration curve, Brier decomposition, and a reliability summary.

| model | expected_calibration_error | maximum_absolute_calibration_gap | high_risk_mean_predicted_risk | high_risk_realized_default_rate | interpretation |
| --- | --- | --- | --- | --- | --- |
| logistic_regression | 0.2348 | 0.3535 | 0.8052 | 0.6600 | high-risk bin overestimates realized default rate |
| hist_gradient_boosting | 0.0119 | 0.0256 | 0.7035 | 0.6889 | high-risk bin overestimates realized default rate |



| model | brier_score | uncertainty | resolution | reliability | overall_default_rate |
| --- | --- | --- | --- | --- | --- |
| logistic_regression | 0.2080 | 0.1723 | 0.0280 | 0.0647 | 0.2212 |
| hist_gradient_boosting | 0.1359 | 0.1723 | 0.0356 | 0.0002 | 0.2212 |


The calibration figure is saved as `projects/topic1_credit_scoring/results/figures/uci_calibration_curve.png`.


## Freddie Mac vintage drift

The Freddie Mac sample was prepared from origination and servicing files for two vintages. The target used here is `ever_30_dpd`, which is a delinquency outcome rather than a legal default label.

| status | label | vintage | n | positive_rate | roc_auc | average_precision | brier_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| completed | ever_30_dpd | 2023 | 50000 | 0.0809 | 0.7043 | 0.1686 | 0.0726 |


This table should be interpreted as vintage-drift diagnostic evidence, not causal identification.


## Multicalibration and conformal risk control

The multicalibration diagnostic checks subgroup-bin residuals across score buckets, CLTV buckets, DTI buckets, and model score deciles.

| status | subgroup | subgroup_value | score_decile | n | support_flag | realized_rate | residual_before_actual_minus_predicted | residual_after_actual_minus_predicted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| completed | credit_score_bucket | low | 9 | 98 | sufficient_support | 0.2551 | -0.1067 | 0.0000 |
| completed | credit_score_bucket | mid | 8 | 279 | sufficient_support | 0.2115 | -0.0000 | 0.0000 |
| completed | credit_score_bucket | mid | 9 | 3850 | sufficient_support | 0.2132 | -0.0760 | 0.0000 |
| completed | credit_score_bucket | high | 1 | 2 | low_support | 0.0000 | -0.0526 | 0.0000 |
| completed | credit_score_bucket | high | 2 | 35 | sufficient_support | 0.0571 | -0.0047 | 0.0000 |
| completed | credit_score_bucket | high | 3 | 82 | sufficient_support | 0.0732 | 0.0027 | 0.0000 |
| completed | credit_score_bucket | high | 4 | 178 | sufficient_support | 0.0843 | 0.0015 | 0.0000 |
| completed | credit_score_bucket | high | 5 | 1270 | sufficient_support | 0.0843 | -0.0159 | 0.0000 |
| completed | credit_score_bucket | high | 6 | 3328 | sufficient_support | 0.0962 | -0.0265 | -0.0000 |
| completed | credit_score_bucket | high | 7 | 4203 | sufficient_support | 0.1118 | -0.0394 | 0.0000 |
| completed | credit_score_bucket | high | 8 | 4508 | sufficient_support | 0.1511 | -0.0409 | 0.0000 |
| completed | credit_score_bucket | high | 9 | 1016 | sufficient_support | 0.1624 | -0.0907 | 0.0000 |


The conformal-style risk-control table reports review-share requirements under different target false-negative-risk levels.

| status | target_fnr | review_share | score_threshold | review_count | captured_delinquency_count | missed_delinquency_count | capture_rate | fnr_risk | precision_in_reviewed_group |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| target_not_reached | 0.0500 | 0.8000 | 0.0533 | 40023 | 3781 | 262 | 0.9352 | 0.0648 | 0.0945 |
| completed | 0.1000 | 0.7500 | 0.0585 | 37500 | 3685 | 358 | 0.9115 | 0.0885 | 0.0983 |
| completed | 0.2000 | 0.5500 | 0.0823 | 27500 | 3262 | 781 | 0.8068 | 0.1932 | 0.1186 |
| completed | 0.3000 | 0.4500 | 0.0973 | 22530 | 2963 | 1080 | 0.7329 | 0.2671 | 0.1315 |


These outputs are threshold-policy diagnostics. They are not deployment guarantees.


## HMDA fairness slice

The HMDA sample is used to model mortgage application denial rather than future borrower default. The fairness-slice table reports group-level denial rates, approval rates, mean model score, and top-risk capture.

| status | group_variable | group_value | n | support_flag | denial_rate | approval_rate | mean_model_score | top_20pct_group_capture |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| completed | derived_race | 2 or more minority races | 12 | low_support | 0.1667 | 0.8333 | 0.1423 | 0.5000 |
| completed | derived_race | American Indian or Alaska Native | 14 | low_support | 0.1429 | 0.8571 | 0.1232 | 0.0000 |
| completed | derived_race | Asian | 1786 | sufficient_support | 0.0963 | 0.9037 | 0.0987 | 0.2907 |
| completed | derived_race | Black or African American | 39 | low_support | 0.2308 | 0.7692 | 0.1681 | 0.4444 |
| completed | derived_race | Joint | 215 | sufficient_support | 0.0837 | 0.9163 | 0.0740 | 0.2778 |
| completed | derived_race | Native Hawaiian or Other Pacific Islander | 11 | low_support | 0.0909 | 0.9091 | 0.1574 | 0.0000 |
| completed | derived_race | Race Not Available | 1369 | sufficient_support | 0.1417 | 0.8583 | 0.1290 | 0.3918 |
| completed | derived_race | White | 2177 | sufficient_support | 0.1231 | 0.8769 | 0.1310 | 0.3433 |
| completed | derived_ethnicity | Ethnicity Not Available | 1258 | sufficient_support | 0.1256 | 0.8744 | 0.1241 | 0.3291 |
| completed | derived_ethnicity | Hispanic or Latino | 553 | sufficient_support | 0.1772 | 0.8228 | 0.1917 | 0.4796 |
| completed | derived_ethnicity | Joint | 210 | sufficient_support | 0.0619 | 0.9381 | 0.0810 | 0.3077 |
| completed | derived_ethnicity | Not Hispanic or Latino | 3602 | sufficient_support | 0.1102 | 0.8898 | 0.1073 | 0.2821 |


Bootstrap confidence intervals are used to check whether selected group-level approval-rate gaps are statistically visible in the sample.

| status | group_variable | reference_group | comparison_group | bootstrap_mean_gap | ci_lower_2_5pct | ci_upper_97_5pct | n_reference | n_comparison |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| completed | derived_race | White | Asian | 0.0264 | 0.0076 | 0.0454 | 2177 | 1786 |
| completed | derived_race | White | Race Not Available | -0.0186 | -0.0388 | 0.0032 | 2177 | 1369 |
| completed | derived_race | White | Joint | 0.0399 | 0.0021 | 0.0766 | 2177 | 215 |
| completed | derived_ethnicity | Not Hispanic or Latino | Ethnicity Not Available | -0.0152 | -0.0350 | 0.0050 | 3602 | 1258 |
| completed | derived_ethnicity | Not Hispanic or Latino | Hispanic or Latino | -0.0671 | -0.1012 | -0.0353 | 3602 | 553 |
| completed | derived_ethnicity | Not Hispanic or Latino | Joint | 0.0483 | 0.0144 | 0.0801 | 3602 | 210 |
| completed | derived_sex | Joint | Male | -0.0494 | -0.0724 | -0.0278 | 2403 | 1592 |
| completed | derived_sex | Joint | Female | -0.0206 | -0.0432 | 0.0024 | 2403 | 1043 |
| completed | derived_sex | Joint | Sex Not Available | -0.0361 | -0.0647 | -0.0070 | 2403 | 585 |


These are fairness diagnostics, not legal discrimination findings.


## Robustness and error review

Robustness checks were performed across multiple random seeds. The purpose is to evaluate whether core metrics are stable across train/test splits.

| table_section | model | random_seed | roc_auc | average_precision | brier_score | top_10pct_capture | roc_auc_mean | roc_auc_std | average_precision_mean | average_precision_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| run_level | logistic_regression | 7.0000 | 0.7294 | 0.5085 | 0.2055 | 0.3084 |  |  |  |  |
| run_level | hist_gradient_boosting | 7.0000 | 0.7892 | 0.5712 | 0.1315 | 0.3275 |  |  |  |  |
| run_level | logistic_regression | 21.0000 | 0.7363 | 0.5249 | 0.2038 | 0.3149 |  |  |  |  |
| run_level | hist_gradient_boosting | 21.0000 | 0.7934 | 0.5824 | 0.1303 | 0.3295 |  |  |  |  |
| run_level | logistic_regression | 42.0000 | 0.7159 | 0.4957 | 0.2080 | 0.2983 |  |  |  |  |
| run_level | hist_gradient_boosting | 42.0000 | 0.7773 | 0.5493 | 0.1359 | 0.3114 |  |  |  |  |
| run_level | logistic_regression | 84.0000 | 0.7281 | 0.5148 | 0.2074 | 0.3129 |  |  |  |  |
| run_level | hist_gradient_boosting | 84.0000 | 0.7858 | 0.5750 | 0.1321 | 0.3290 |  |  |  |  |
| run_level | logistic_regression | 202.0000 | 0.7176 | 0.5044 | 0.2068 | 0.3164 |  |  |  |  |
| run_level | hist_gradient_boosting | 202.0000 | 0.7772 | 0.5611 | 0.1338 | 0.3235 |  |  |  |  |
| summary | hist_gradient_boosting |  |  |  |  |  | 0.7846 | 0.0072 | 0.5678 | 0.0129 |
| summary | logistic_regression |  |  |  |  |  | 0.7254 | 0.0086 | 0.5097 | 0.0110 |


The error-review sample includes high-score non-default cases and low-score default cases. These cases help diagnose model failure modes, but they are not causal explanations.

| row_id | y_true | score_logistic_regression | score_hist_gradient_boosting | error_taxonomy | LIMIT_BAL | AGE | PAY_0 | PAY_2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9671 | 0 | 0.9121 | 0.8143 | high_score_non_default_false_alarm | 170000 | 48 | 2 | 2 |
| 28747 | 0 | 0.9175 | 0.8095 | high_score_non_default_false_alarm | 50000 | 28 | 3 | 2 |
| 10142 | 0 | 0.7906 | 0.7987 | high_score_non_default_false_alarm | 400000 | 39 | 2 | 2 |
| 25248 | 0 | 0.8865 | 0.7897 | high_score_non_default_false_alarm | 120000 | 23 | 3 | 2 |
| 13421 | 0 | 0.7983 | 0.7885 | high_score_non_default_false_alarm | 100000 | 29 | 2 | 2 |
| 7067 | 0 | 0.8442 | 0.7853 | high_score_non_default_false_alarm | 90000 | 30 | 2 | 2 |
| 11844 | 0 | 0.8869 | 0.7824 | high_score_non_default_false_alarm | 30000 | 24 | 2 | 2 |
| 1521 | 0 | 0.9276 | 0.7791 | high_score_non_default_false_alarm | 60000 | 40 | 3 | 3 |
| 798 | 0 | 0.8357 | 0.7771 | high_score_non_default_false_alarm | 100000 | 48 | 2 | 2 |
| 11993 | 0 | 0.7404 | 0.7725 | high_score_non_default_false_alarm | 100000 | 28 | 2 | 0 |
| 26880 | 0 | 0.8861 | 0.7713 | high_score_non_default_false_alarm | 50000 | 39 | 3 | 3 |
| 18658 | 0 | 0.8346 | 0.7696 | high_score_non_default_false_alarm | 40000 | 28 | 2 | 2 |

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
