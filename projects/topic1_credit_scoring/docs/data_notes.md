# Topic 1 Data Notes

This document records the data sources, label definitions, sample periods, and claim boundaries for the trustworthy credit scoring module.

## Dataset roles

- UCI Default of Credit Card Clients: baseline credit default modelling.
- Freddie Mac Sample: delinquency, vintage drift, multicalibration, and conformal risk-control diagnostics.
- HMDA Sample: denial-risk modelling and fairness-slice diagnostics.
- FRED Macro Rates: macro regime and interest-rate context.

## Label meanings

- Default: borrower fails to repay according to the credit contract.
- Delinquency: borrower becomes late on payment, such as 30 days past due or 90 days past due.
- Denial: a loan application is rejected.

These labels are not interchangeable and should not be described as the same risk event.
