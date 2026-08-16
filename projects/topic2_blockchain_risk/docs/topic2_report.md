# Topic 2 Report: Blockchain Market-Integrity Risk Signals

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

Sample period: 2021-01-01 to 2025-06-29

Assets covered: BNB, BTC, ETH, SOL, USDC, USDT

Main panel size: 11487 asset-day observations.

Number of assets: 6

Validated public incident events: 5

Weak-label event-window rows: 396

## 3. Four-layer data coverage

The project uses four data layers:

1. Yahoo OHLCV market data.
2. Coin Metrics network and market context data where available.
3. DeFiLlama DEX, TVL, and stablecoin context data.
4. Public incident ledger and weak-label event windows.

### Data-layer summary

| data_layer | n_datasets | available_count | failed_or_missing_count | total_rows | coverage_status | claim_boundary |
| --- | --- | --- | --- | --- | --- | --- |
| Layer 1: Yahoo OHLCV | 6 | 6 | 0 | 9846 | complete | Coverage status describes data availability only; it does not validate incident truth or causal identification. |
| Layer 2/3: Coin Metrics | 24 | 16 | 8 | 26272 | partial | Coverage status describes data availability only; it does not validate incident truth or causal identification. |
| Layer 2/3: DeFiLlama | 6 | 6 | 0 | 14089 | complete | Coverage status describes data availability only; it does not validate incident truth or causal identification. |
| Layer 4: Incident ledger | 1 | 1 | 0 | 5 | complete | Coverage status describes data availability only; it does not validate incident truth or causal identification. |
| Layer 4: Weak-label windows | 1 | 1 | 0 | 396 | complete | Coverage status describes data availability only; it does not validate incident truth or causal identification. |

### Coverage matrix excerpt

| data_layer | dataset | scope | file_path | file_exists | file_size_kb | file_status | n_rows | n_columns | start_date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Layer 1: Yahoo OHLCV | daily_ohlcv | BTC | projects/topic2_blockchain_risk/data/raw/yahoo_ohlcv.csv | True | 1182.34 | available | 1641 | 9 | 2021-01-01 |
| Layer 1: Yahoo OHLCV | daily_ohlcv | ETH | projects/topic2_blockchain_risk/data/raw/yahoo_ohlcv.csv | True | 1182.34 | available | 1641 | 9 | 2021-01-01 |
| Layer 1: Yahoo OHLCV | daily_ohlcv | BNB | projects/topic2_blockchain_risk/data/raw/yahoo_ohlcv.csv | True | 1182.34 | available | 1641 | 9 | 2021-01-01 |
| Layer 1: Yahoo OHLCV | daily_ohlcv | SOL | projects/topic2_blockchain_risk/data/raw/yahoo_ohlcv.csv | True | 1182.34 | available | 1641 | 9 | 2021-01-01 |
| Layer 1: Yahoo OHLCV | daily_ohlcv | USDC | projects/topic2_blockchain_risk/data/raw/yahoo_ohlcv.csv | True | 1182.34 | available | 1641 | 9 | 2021-01-01 |
| Layer 1: Yahoo OHLCV | daily_ohlcv | USDT | projects/topic2_blockchain_risk/data/raw/yahoo_ohlcv.csv | True | 1182.34 | available | 1641 | 9 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | BTC:AdrActCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | BTC:TxCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | BTC:CapMrktCurUSD | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | BTC:SplyCur | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | ETH:AdrActCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | ETH:TxCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | ETH:CapMrktCurUSD | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | ETH:SplyCur | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | BNB:AdrActCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | missing_or_empty | 0 | 0 |  |
| Layer 2/3: Coin Metrics | asset_metrics | BNB:TxCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | missing_or_empty | 0 | 0 |  |
| Layer 2/3: Coin Metrics | asset_metrics | BNB:CapMrktCurUSD | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | missing_or_empty | 0 | 0 |  |
| Layer 2/3: Coin Metrics | asset_metrics | BNB:SplyCur | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | missing_or_empty | 0 | 0 |  |
| Layer 2/3: Coin Metrics | asset_metrics | SOL:AdrActCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | download_failed | 0 | 0 |  |
| Layer 2/3: Coin Metrics | asset_metrics | SOL:TxCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | download_failed | 0 | 0 |  |
| Layer 2/3: Coin Metrics | asset_metrics | SOL:CapMrktCurUSD | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | download_failed | 0 | 0 |  |
| Layer 2/3: Coin Metrics | asset_metrics | SOL:SplyCur | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | download_failed | 0 | 0 |  |
| Layer 2/3: Coin Metrics | asset_metrics | USDC:AdrActCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | USDC:TxCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | USDC:CapMrktCurUSD | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | USDC:SplyCur | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | USDT:AdrActCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | USDT:TxCnt | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | USDT:CapMrktCurUSD | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |
| Layer 2/3: Coin Metrics | asset_metrics | USDT:SplyCur | projects/topic2_blockchain_risk/data/raw/coinmetrics_asset_metrics.csv | True | 482.98 | available | 1642 | 5 | 2021-01-01 |

## 4. Incident ledger and weak labels

The incident ledger records public blockchain-related events. These records are used to build event windows, but they are not treated as verified fraud labels.

### Incident audit

| check_name | status | n_failed | details | claim_boundary |
| --- | --- | --- | --- | --- |
| required_columns | passed | 0 | All required incident ledger columns are present. | Column completeness does not mean incident truth is verified. |
| row_level_validation | passed | 0 | Row-level validation checks date range, asset coverage, source URL, event type, and severity. | Warnings should be disclosed in the report and not treated as evidence of fraud. |
| severity_distribution | passed | 0 | {'high': 3, 'medium': 2} | Severity is a manual research label, not a legal classification. |
| event_type_distribution | passed | 0 | {'stablecoin_depeg': 2, 'exchange_failure': 1, 'regulatory_action': 1, 'network_stress': 1} | Event type is a research category used for stratified diagnostics. |

### Validated incident ledger

| event_id | event_date | asset | event_type | severity | brief | source_note | source_url | affected_assets | n_affected_assets_in_ohlcv |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E001 | 2022-05-09 | USDT | stablecoin_depeg | high | Terra/Luna collapse stress spilled into stablecoin markets | public incident source | https://www.reuters.com/technology/stablecoin-tether-breaks-dollar-peg-falls-095-2022-05-12/ | USDT,USDC,BTC,ETH | 4 |
| E002 | 2022-11-08 | BNB | exchange_failure | high | FTX crisis public disclosure and exchange-sector stress | public incident source | https://www.reuters.com/technology/crypto-exchange-binance-says-it-will-buy-rival-ftxcom-2022-11-08/ | BNB,BTC,ETH,SOL | 4 |
| E003 | 2023-03-11 | USDC | stablecoin_depeg | high | USDC depeg during Silicon Valley Bank reserve concerns | public incident source | https://www.circle.com/pressroom/3-3-billion-of-usdc-reserve-risk-removed-dollar-de-peg-closes | USDC,USDT,BTC,ETH | 4 |
| E004 | 2023-06-05 | BNB | regulatory_action | medium | SEC action against Binance-related entities and market stress | public incident source | https://www.sec.gov/newsroom/press-releases/2023-101-sec-files-13-charges-against-binance-entities-founder-changpeng-... | BNB,BTC,ETH | 3 |
| E005 | 2024-03-15 | SOL | network_stress | medium | Solana congestion and block-optimization period | public incident source | https://solana.com/uk/news/block-optimization-on-the-solana-network | SOL,BTC,ETH | 3 |

## 5. Feature engineering

The feature-engineered panel combines market features, stablecoin peg-deviation features, DeFi context features, Coin Metrics context where available, and weak-label event-window indicators.

### Feature dictionary

| feature | definition | role |
| --- | --- | --- |
| log_return | Daily log return from Yahoo close price. | market stress |
| abs_log_return | Absolute daily log return. | volatility proxy |
| rolling_vol_7d | 7-day rolling standard deviation of log returns. | short-horizon volatility |
| rolling_vol_30d | 30-day rolling standard deviation of log returns. | medium-horizon volatility |
| volume_z_30d | 30-day rolling z-score of log trading volume. | volume abnormality |
| return_z_30d | 30-day rolling z-score of daily log return. | return abnormality |
| abs_return_z_30d | 30-day rolling z-score of absolute return. | volatility shock |
| drawdown_30d | Close price relative to 30-day rolling peak minus one. | drawdown stress |
| intraday_range | High-low range divided by close. | intraday instability |
| intraday_range_z_30d | 30-day rolling z-score of intraday range. | range abnormality |
| stablecoin_peg_deviation | Absolute deviation from one dollar for USDC/USDT. | stablecoin peg stress |
| stablecoin_depeg_1pct | Indicator for stablecoin price deviation of at least 1%. | stablecoin depeg flag |
| AdrActCnt_log | Log active address count from Coin Metrics where available. | network context |
| TxCnt_log | Log transaction count from Coin Metrics where available. | network context |
| CapMrktCurUSD_log | Log market capitalization from Coin Metrics where available. | market-size context |
| SplyCur_log | Log current supply from Coin Metrics where available. | supply context |
| total_dex_volume_log | Log aggregate DeFiLlama DEX volume. | DeFi market context |
| dex_volume_z_30d | 30-day z-score of aggregate DEX volume. | DeFi market stress |
| chain_tvl_log | Log DeFiLlama chain TVL mapped to asset chain. | chain liquidity context |
| chain_tvl_z_30d | 30-day z-score of mapped chain TVL. | chain liquidity stress |
| weak_label_3d | Indicator for public incident window within +/-3 calendar days. | weak label |
| weak_label_7d | Indicator for public incident window within +/-7 calendar days. | weak label |
| event_count_3d | Number of public events linked to asset-day within +/-3 days. | weak-label intensity |
| event_count_7d | Number of public events linked to asset-day within +/-7 days. | weak-label intensity |

### Feature audit excerpt

| feature | n_rows | missing_ratio | n_unique | min | max | claim_boundary |
| --- | --- | --- | --- | --- | --- | --- |
| volume | 11487 | 0.0 | 9841 | 25722549.0 | 83252070566791.0 | Features support market-integrity risk diagnostics, not fraud attribution. |
| log_close | 11487 | 0.0 | 7882 | -0.0289140312701471 | 11.623332755459392 | Features support market-integrity risk diagnostics, not fraud attribution. |
| log_return | 11487 | 0.0006093845216331 | 9819 | -0.5495821084962169 | 0.5292178669714955 | Features support market-integrity risk diagnostics, not fraud attribution. |
| abs_log_return | 11487 | 0.0006093845216331 | 9809 | 0.0 | 0.5495821084962169 | Features support market-integrity risk diagnostics, not fraud attribution. |
| negative_return | 11487 | 0.0 | 2 | 0.0 | 1.0 | Features support market-integrity risk diagnostics, not fraud attribution. |
| rolling_vol_7d | 11487 | 0.0030469226081657 | 9816 | 2.0111261026125737e-05 | 0.2775089316086132 | Features support market-integrity risk diagnostics, not fraud attribution. |
| rolling_vol_30d | 11487 | 0.0091407678244972 | 9756 | 5.495954981520587e-05 | 0.1549031478434348 | Features support market-integrity risk diagnostics, not fraud attribution. |
| volume_log | 11487 | 0.0 | 9841 | 17.062878597053714 | 32.052894116152984 | Features support market-integrity risk diagnostics, not fraud attribution. |
| volume_z_30d | 11487 | 0.0054844606946983 | 9792 | -3.1328108963030328 | 5.224528782346566 | Features support market-integrity risk diagnostics, not fraud attribution. |
| return_z_30d | 11487 | 0.0060938452163315 | 9786 | -5.291883585999826 | 5.053130645166781 | Features support market-integrity risk diagnostics, not fraud attribution. |
| abs_return_z_30d | 11487 | 0.0060938452163315 | 9786 | -1.7656158760325107 | 5.293419389105287 | Features support market-integrity risk diagnostics, not fraud attribution. |
| drawdown_30d | 11487 | 0.0054844606946983 | 8872 | -0.6777923855801311 | 0.0 | Features support market-integrity risk diagnostics, not fraud attribution. |
| intraday_range | 11487 | 0.0 | 9844 | 6.293960873020055e-05 | 1.3509588636935872 | Features support market-integrity risk diagnostics, not fraud attribution. |
| intraday_range_z_30d | 11487 | 0.0054844606946983 | 9792 | -5.117743891567658 | 5.29464080582564 | Features support market-integrity risk diagnostics, not fraud attribution. |
| stablecoin_peg_deviation | 11487 | 0.0 | 1218 | 0.0 | 0.0285000205039978 | Features support market-integrity risk diagnostics, not fraud attribution. |
| stablecoin_depeg_1pct | 11487 | 0.0 | 2 | 0.0 | 1.0 | Features support market-integrity risk diagnostics, not fraud attribution. |
| event_count_3d | 11487 | 0.0 | 2 | 0.0 | 1.0 | Features support market-integrity risk diagnostics, not fraud attribution. |
| weak_label_3d | 11487 | 0.0 | 2 | 0.0 | 1.0 | Features support market-integrity risk diagnostics, not fraud attribution. |
| event_count_7d | 11487 | 0.0 | 2 | 0.0 | 1.0 | Features support market-integrity risk diagnostics, not fraud attribution. |
| weak_label_7d | 11487 | 0.0 | 2 | 0.0 | 1.0 | Features support market-integrity risk diagnostics, not fraud attribution. |
| AdrActCnt | 11487 | 0.2857142857142857 | 6533 | 18610.0 | 5478691.0 | Features support market-integrity risk diagnostics, not fraud attribution. |
| TxCnt | 11487 | 0.2857142857142857 | 6546 | 35343.0 | 9187396.0 | Features support market-integrity risk diagnostics, not fraud attribution. |
| CapMrktCurUSD | 11487 | 0.2857142857142857 | 6563 | 4119730823.507957 | 2214868273238.022 | Features support market-integrity risk diagnostics, not fraud attribution. |
| SplyCur | 11487 | 0.2857142857142857 | 5925 | 18587827.69247703 | 159644543727.436 | Features support market-integrity risk diagnostics, not fraud attribution. |
| AdrActCnt_log | 11487 | 0.2857142857142857 | 6533 | 9.831508082743964 | 15.516376944302744 | Features support market-integrity risk diagnostics, not fraud attribution. |
| AdrActCnt_z_30d | 11487 | 0.2896317576390702 | 6528 | -4.983684748492508 | 4.9469322843463885 | Features support market-integrity risk diagnostics, not fraud attribution. |
| TxCnt_log | 11487 | 0.2857142857142857 | 6546 | 10.472883925659898 | 16.033343211556033 | Features support market-integrity risk diagnostics, not fraud attribution. |
| TxCnt_z_30d | 11487 | 0.2896317576390702 | 6528 | -4.609511969742306 | 5.011752669001078 | Features support market-integrity risk diagnostics, not fraud attribution. |
| CapMrktCurUSD_log | 11487 | 0.2857142857142857 | 6563 | 22.139053664316204 | 28.42621404733623 | Features support market-integrity risk diagnostics, not fraud attribution. |
| CapMrktCurUSD_z_30d | 11487 | 0.2896317576390702 | 6528 | -5.294472083691089 | 5.290410029066385 | Features support market-integrity risk diagnostics, not fraud attribution. |

## 6. Transparent risk score

The transparent score combines interpretable components, including return shocks, volume shocks, intraday instability, drawdown stress, stablecoin peg stress, DeFi volume context, and chain TVL context.

All-asset benchmark against weak_label_7d at top 5 percent alerts:

- Average precision: 0.0953
- ROC-AUC: 0.6356
- Precision at 5 percent: 0.1063
- Recall at 5 percent: 0.2033
- Lift at 5 percent: 4.0691

### Transparent score components

| component | source_column | weight | direction | source_column_missing | mean_scaled_component | max_scaled_component | definition | claim_boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| return_shock | abs_return_z_30d | 0.22 | positive_tail | 0 | 0.5000435274658309 | 1.0 | Large absolute return shocks relative to recent asset history. | Transparent score components are alert signals, not proof of fraud. |
| volume_shock | volume_z_30d | 0.18 | positive_tail | 0 | 0.5000435274658309 | 1.0 | Abnormal trading volume relative to recent asset history. | Transparent score components are alert signals, not proof of fraud. |
| intraday_instability | intraday_range_z_30d | 0.18 | positive_tail | 0 | 0.5000435274658309 | 1.0 | Abnormal intraday high-low range. | Transparent score components are alert signals, not proof of fraud. |
| drawdown_stress | drawdown_30d | 0.18 | negative_tail | 0 | 0.5000435274658309 | 1.0 | Price drawdown from recent 30-day rolling peak. | Transparent score components are alert signals, not proof of fraud. |
| stablecoin_peg_stress | stablecoin_peg_deviation | 0.14 | absolute_level | 0 | 0.5000435274658309 | 1.0 | Absolute stablecoin price deviation from one dollar. | Transparent score components are alert signals, not proof of fraud. |
| defi_volume_context | dex_volume_z_30d | 0.05 | positive_tail | 0 | 0.5000435274658309 | 0.9997388352050144 | Aggregate DEX volume abnormality. | Transparent score components are alert signals, not proof of fraud. |
| chain_tvl_context | chain_tvl_z_30d | 0.05 | absolute_tail | 0 | 0.500043527465831 | 1.0 | Mapped chain TVL abnormality. | Transparent score components are alert signals, not proof of fraud. |

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

- Average precision: 0.0954
- ROC-AUC: 0.6652
- Precision at 5 percent: 0.1237
- Recall at 5 percent: 0.2367
- Lift at 5 percent: 4.7362

### Anomaly method agreement excerpt

| method_a | method_b | spearman_corr | top_share | top_n | top_overlap_count | jaccard_top_overlap | claim_boundary |
| --- | --- | --- | --- | --- | --- | --- | --- |
| transparent_risk_score | isolation_forest_score | 0.3333799804659614 | 0.01 | 115 | 68 | 0.419753086419753 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | isolation_forest_score | 0.3333799804659614 | 0.05 | 574 | 253 | 0.28268156424581 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | isolation_forest_score | 0.3333799804659614 | 0.1 | 1149 | 477 | 0.2619439868204283 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | lof_score | 0.3495513734439203 | 0.01 | 115 | 18 | 0.0849056603773584 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | lof_score | 0.3495513734439203 | 0.05 | 574 | 116 | 0.1124031007751938 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | lof_score | 0.3495513734439203 | 0.1 | 1149 | 282 | 0.1398809523809523 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | robust_z_score | 0.3699655781827873 | 0.01 | 115 | 20 | 0.0952380952380952 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | robust_z_score | 0.3699655781827873 | 0.05 | 574 | 133 | 0.1310344827586207 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | robust_z_score | 0.3699655781827873 | 0.1 | 1149 | 378 | 0.196875 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | anomaly_ensemble_score | 0.3879838766342774 | 0.01 | 115 | 46 | 0.25 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | anomaly_ensemble_score | 0.3879838766342774 | 0.05 | 574 | 192 | 0.200836820083682 | Method agreement measures alert-score similarity, not incident truth. |
| transparent_risk_score | anomaly_ensemble_score | 0.3879838766342774 | 0.1 | 1149 | 442 | 0.2381465517241379 | Method agreement measures alert-score similarity, not incident truth. |
| isolation_forest_score | lof_score | 0.7390471667254344 | 0.01 | 115 | 34 | 0.173469387755102 | Method agreement measures alert-score similarity, not incident truth. |
| isolation_forest_score | lof_score | 0.7390471667254344 | 0.05 | 574 | 255 | 0.2855543113101904 | Method agreement measures alert-score similarity, not incident truth. |
| isolation_forest_score | lof_score | 0.7390471667254344 | 0.1 | 1149 | 600 | 0.3533568904593639 | Method agreement measures alert-score similarity, not incident truth. |
| isolation_forest_score | robust_z_score | 0.7983777901289703 | 0.01 | 115 | 28 | 0.1386138613861386 | Method agreement measures alert-score similarity, not incident truth. |
| isolation_forest_score | robust_z_score | 0.7983777901289703 | 0.05 | 574 | 255 | 0.2855543113101904 | Method agreement measures alert-score similarity, not incident truth. |
| isolation_forest_score | robust_z_score | 0.7983777901289703 | 0.1 | 1149 | 625 | 0.3735803945008966 | Method agreement measures alert-score similarity, not incident truth. |
| isolation_forest_score | anomaly_ensemble_score | 0.9414295188481656 | 0.01 | 115 | 67 | 0.4110429447852761 | Method agreement measures alert-score similarity, not incident truth. |
| isolation_forest_score | anomaly_ensemble_score | 0.9414295188481656 | 0.05 | 574 | 402 | 0.5388739946380697 | Method agreement measures alert-score similarity, not incident truth. |

Main figures:

- results/figures/anomaly_event_window_lift.png
- results/figures/anomaly_method_ap_comparison.png

## 8. Weak-supervision label model

The weak-supervision model combines multiple noisy label functions into a composite score. Label functions include transparent-score tail alerts, anomaly-score tail alerts, return-volume joint stress, range-drawdown joint stress, stablecoin peg stress, DeFi context shock, and multi-method consensus.

All-asset weak-supervision benchmark against weak_label_7d at top 5 percent alerts:

- Average precision: 0.0972
- ROC-AUC: 0.6288
- Precision at 5 percent: 0.1307
- Recall at 5 percent: 0.2500
- Lift at 5 percent: 5.0030

### Label-function summary

| label_function | weight | fires_count | coverage_rate | weak_label_7d_rate_when_fires | definition | claim_boundary |
| --- | --- | --- | --- | --- | --- | --- |
| lf_transparent_top5 | 0.2 | 580 | 0.0504918603638896 | 0.1034482758620689 | Transparent risk score is in the asset-specific top 5%. | Label functions are noisy heuristic alerts, not verified fraud labels. |
| lf_anomaly_top5 | 0.2 | 579 | 0.0504048054322277 | 0.1260794473229706 | Anomaly ensemble score is in the asset-specific top 5%. | Label functions are noisy heuristic alerts, not verified fraud labels. |
| lf_return_volume_joint | 0.15 | 366 | 0.0318621049882475 | 0.1311475409836065 | Absolute return shock and volume shock are both in the asset-specific top 10%. | Label functions are noisy heuristic alerts, not verified fraud labels. |
| lf_range_drawdown_joint | 0.15 | 167 | 0.0145381735875337 | 0.1257485029940119 | Intraday range shock and drawdown stress are both in the asset-specific top 10%. | Label functions are noisy heuristic alerts, not verified fraud labels. |
| lf_stablecoin_depeg | 0.15 | 9 | 0.0007834943849569 | 0.6666666666666666 | Stablecoin deviates from one dollar by at least 0.5%. | Label functions are noisy heuristic alerts, not verified fraud labels. |
| lf_defi_context_shock | 0.05 | 970 | 0.0844432837120222 | 0.0762886597938144 | DEX volume or mapped chain TVL context is in an extreme asset-specific tail. | Label functions are noisy heuristic alerts, not verified fraud labels. |
| lf_multimethod_consensus | 0.1 | 439 | 0.0382171149995647 | 0.1571753986332574 | Transparent and anomaly scores are both in the asset-specific top 10%. | Label functions are noisy heuristic alerts, not verified fraud labels. |
| all_label_functions_summary | 1.0000000000000002 | 1735 | 0.1510403064333594 | 0.0651296829971181 | Any label function fires. | Aggregated weak supervision remains noisy and weak-label based. |

Main figures:

- results/figures/weak_supervision_event_window_lift.png
- results/figures/weak_supervision_lf_coverage.png

## 9. Spillover, change-point, and EVT diagnostics

The project adds three diagnostic layers:

1. Spillover connectedness: whether asset correlations and score correlations differ around event windows.
2. Change-point timeline: whether aggregate risk-score breaks occur near public incident windows.
3. EVT tail risk: whether extreme return or stress tails can be summarized using POT-style tail diagnostics.

### Spillover connectedness excerpt

| asset_a | asset_b | return_corr_all | return_corr_event_window_7d | return_corr_non_event | delta_abs_return_corr_event_minus_non_event | weak_score_corr_all | weak_score_corr_event_window_7d | weak_score_corr_non_event | delta_abs_score_corr_event_minus_non_event |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BNB | BTC | 0.6579580308060141 | 0.7916535188713257 | 0.6449728019559232 | 0.1466807169154025 | 0.5011077811549693 | 0.6012872740326746 | 0.486540709034477 | 0.1147465649981975 |
| BNB | ETH | 0.6709725883068093 | 0.7807156098589471 | 0.6612613025744646 | 0.1194543072844824 | 0.4792875544694312 | 0.3778007021857897 | 0.4762343014665541 | -0.0984335992807644 |
| BNB | SOL | 0.5775709634977519 | 0.7851297208203459 | 0.5551458437335617 | 0.2299838770867842 | 0.491779162585169 | 0.5702075112394026 | 0.4672853288344076 | 0.102922182404995 |
| BNB | USDC | 0.0187772593056622 | 0.0599323813417813 | 0.0086202141398137 | 0.0513121672019676 | 0.4270477292685823 | 0.6133606605614461 | 0.4066596389599812 | 0.2067010216014648 |
| BNB | USDT | 0.0713363836525067 | 0.1709484274896676 | 0.0600354386448895 | 0.110912988844778 | 0.4253261522680625 | 0.5027356399943818 | 0.4028965639522494 | 0.0998390760421323 |
| BTC | ETH | 0.8170304276689188 | 0.9422272941083926 | 0.8059965225393688 | 0.1362307715690237 | 0.5343017147946292 | 0.5652387528400625 | 0.5269438471301364 | 0.0382949057099261 |
| BTC | SOL | 0.6077096338356073 | 0.8141314141543045 | 0.5829145531063169 | 0.2312168610479875 | 0.4729016758432898 | 0.5331760380375594 | 0.4612798442782967 | 0.0718961937592626 |
| BTC | USDC | 0.0128632902852532 | 0.1042952354221438 | -0.0322354146277347 | 0.072059820794409 | 0.4355931792458148 | 0.5341639830460156 | 0.4245548517914706 | 0.109609131254545 |
| BTC | USDT | 0.091487653622413 | 0.0850284280972139 | 0.0923203687677332 | -0.0072919406705193 | 0.4499872003879561 | 0.4672129635206879 | 0.4422644129480453 | 0.0249485505726426 |
| ETH | SOL | 0.6532836583589289 | 0.8554676478413299 | 0.633278645585801 | 0.2221890022555288 | 0.519050809706797 | 0.5288016407238421 | 0.5014755213464501 | 0.0273261193773919 |
| ETH | USDC | -0.0096133227903771 | 0.0454983732558273 | -0.0440974292054268 | 0.0014009440504005 | 0.3884765981084245 | 0.4076303753774252 | 0.3825672119110441 | 0.0250631634663811 |
| ETH | USDT | 0.0765141108744856 | 0.1479279344428124 | 0.0689392563115885 | 0.0789886781312238 | 0.4538035512397319 | 0.3173186799463279 | 0.4550577060261817 | -0.1377390260798537 |
| SOL | USDC | -0.0033806077626122 | 0.0633317752281432 | -0.0515687594381037 | 0.0117630157900395 | 0.3774697378464265 | 0.5520518484939737 | 0.3566827850382127 | 0.195369063455761 |
| SOL | USDT | 0.0402542589468923 | 0.2242218164690145 | 0.0127081719924254 | 0.2115136444765891 | 0.4077383731868077 | 0.4235938492330626 | 0.3877867595124915 | 0.0358070897205711 |
| USDC | USDT | 0.1512782419206157 | -0.5479515990445228 | 0.7278363096946855 | -0.1798847106501626 | 0.6109732452622338 | 0.6821381769784777 | 0.6034524202324933 | 0.0786857567459843 |

### Change-point timeline excerpt

| change_point_date | method | weak_score_mean_before_7d | weak_score_mean_after_7d | weak_score_delta_after_minus_before | anomaly_score_mean_before_7d | anomaly_score_mean_after_7d | anomaly_score_delta_after_minus_before | abs_return_mean_before_7d | abs_return_mean_after_7d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2021-03-17 | ruptures_pelt_rbf | 42.45233742491512 | 54.94960585435532 | 12.497268429440195 | 0.290266014998321 | 0.5663109850887339 | 0.2760449700904128 | 0.0250044024627034 | 0.0112357237736886 |
| 2021-07-20 | ruptures_pelt_rbf | 45.544208803918536 | 54.38428178793064 | 8.840072984012103 | 0.5776716536706089 | 0.5818254175527615 | 0.0041537638821526 | 0.0179372580569583 | 0.0196331182945528 |
| 2024-07-09 | ruptures_pelt_rbf | 64.53275486219559 | 42.45233742491512 | -22.080417437280467 | 0.6620776281262047 | 0.3241366016241963 | -0.3379410265020084 | 0.025710390332749 | 0.0137699990036547 |

### EVT tail-risk excerpt

| asset | tail_variable | definition | n_obs | threshold_quantile | threshold_value | n_exceedances | exceedance_rate | gpd_shape | gpd_scale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BNB | abs_log_return | absolute daily log return | 1640 | 0.95 | 0.0839174725114382 | 82 | 0.05 | 0.3957937248679645 | 0.0320081895152089 |
| BNB | intraday_range | intraday range divided by close | 1641 | 0.95 | 0.133493869157599 | 82 | 0.0499695307739183 | 0.2739725741932676 | 0.052421433626425 |
| BTC | abs_log_return | absolute daily log return | 1640 | 0.95 | 0.0678972985369534 | 82 | 0.05 | -0.0795892794578398 | 0.0266633318980637 |
| BTC | intraday_range | intraday range divided by close | 1641 | 0.95 | 0.0986251476888721 | 82 | 0.0499695307739183 | 0.032094176803381 | 0.037032309173405 |
| ETH | abs_log_return | absolute daily log return | 1640 | 0.95 | 0.0866785476964799 | 82 | 0.05 | 0.1160556972713677 | 0.0319480361899285 |
| ETH | intraday_range | intraday range divided by close | 1641 | 0.95 | 0.1295994451380219 | 82 | 0.0499695307739183 | 0.286808616942717 | 0.0368932548416756 |
| SOL | abs_log_return | absolute daily log return | 1640 | 0.95 | 0.1216271402368299 | 82 | 0.05 | 0.2038919229051999 | 0.0446181388513721 |
| SOL | intraday_range | intraday range divided by close | 1641 | 0.95 | 0.1833777793786643 | 82 | 0.0499695307739183 | 0.243119076003774 | 0.0635315465364958 |
| USDC | abs_log_return | absolute daily log return | 1640 | 0.95 | 0.0007176357463624 | 82 | 0.05 | 0.8813705521829812 | 0.0002989068677101 |
| USDC | intraday_range | intraday range divided by close | 1641 | 0.95 | 0.0031807349838452 | 82 | 0.0499695307739183 | 0.9855251206100748 | 0.000831767518057 |
| USDC | stablecoin_peg_deviation | absolute stablecoin peg deviation | 1641 | 0.95 | 0.0005860328674316 | 82 | 0.0499695307739183 | 0.6515292005552928 | 0.0003364856186008 |
| USDT | abs_log_return | absolute daily log return | 3280 | 0.95 | 0.0009248345029024 | 164 | 0.05 | 0.5542472778635801 | 0.0003586485530908 |
| USDT | intraday_range | intraday range divided by close | 3282 | 0.95 | 0.003502131574221 | 164 | 0.0499695307739183 | 0.9945015213182852 | 0.0004940305739436 |
| USDT | stablecoin_peg_deviation | absolute stablecoin peg deviation | 3282 | 0.95 | 0.0013370513916015 | 164 | 0.0499695307739183 | 0.3750239886444223 | 0.0005291075091575 |

Main figures:

- results/figures/spillover_connectedness_heatmap.png
- results/figures/changepoint_timeline.png
- results/figures/evt_tail_thresholds.png

## 10. Ablation, placebo, and sensitivity checks

The robustness layer checks whether the result depends on one label function, one scoring rule, or random/shifted placebo event labels.

### Placebo label audit

| label | positive_count | positive_rate | claim_boundary |
| --- | --- | --- | --- |
| weak_label_7d | 300 | 0.0261164794985635 | Placebo labels are validity checks; they are not alternative incident truths. |
| placebo_7d_shift_plus_90 | 270 | 0.0235048315487072 | Placebo labels are validity checks; they are not alternative incident truths. |
| placebo_7d_shift_minus_90 | 270 | 0.0235048315487072 | Placebo labels are validity checks; they are not alternative incident truths. |
| placebo_7d_random_by_asset | 300 | 0.0261164794985635 | Placebo labels are validity checks; they are not alternative incident truths. |

### Ablation and placebo excerpt

| check_family | score_family | label | method | n_rows | label_positive_count | label_positive_rate | average_precision | roc_auc | claim_boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main_weak_label | benchmark_existing_score | weak_label_3d | anomaly_ensemble_score | 11487 | 140 | 0.012187690432663 | 0.1085953797922804 | 0.7312659733850357 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | benchmark_existing_score | weak_label_3d | anomaly_ensemble_score | 11487 | 140 | 0.012187690432663 | 0.1085953797922804 | 0.7312659733850357 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | benchmark_existing_score | weak_label_3d | anomaly_ensemble_score | 11487 | 140 | 0.012187690432663 | 0.1085953797922804 | 0.7312659733850357 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | benchmark_existing_score | weak_label_3d | anomaly_ensemble_score | 11487 | 140 | 0.012187690432663 | 0.1085953797922804 | 0.7312659733850357 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_baseline_all_lfs | 11487 | 140 | 0.012187690432663 | 0.1313363132356764 | 0.7154908786463381 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_baseline_all_lfs | 11487 | 140 | 0.012187690432663 | 0.1313363132356764 | 0.7154908786463381 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_baseline_all_lfs | 11487 | 140 | 0.012187690432663 | 0.1313363132356764 | 0.7154908786463381 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_baseline_all_lfs | 11487 | 140 | 0.012187690432663 | 0.1313363132356764 | 0.7154908786463381 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_chain_tvl_context | 11487 | 140 | 0.012187690432663 | 0.0420216055486744 | 0.5824607511110551 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_chain_tvl_context | 11487 | 140 | 0.012187690432663 | 0.0420216055486744 | 0.5824607511110551 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_chain_tvl_context | 11487 | 140 | 0.012187690432663 | 0.0420216055486744 | 0.5824607511110551 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_chain_tvl_context | 11487 | 140 | 0.012187690432663 | 0.0420216055486744 | 0.5824607511110551 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_defi_volume_context | 11487 | 140 | 0.012187690432663 | 0.0725358407306146 | 0.762686172556623 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_defi_volume_context | 11487 | 140 | 0.012187690432663 | 0.0725358407306146 | 0.762686172556623 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_defi_volume_context | 11487 | 140 | 0.012187690432663 | 0.0725358407306146 | 0.762686172556623 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_defi_volume_context | 11487 | 140 | 0.012187690432663 | 0.0725358407306146 | 0.762686172556623 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_drawdown_stress | 11487 | 140 | 0.012187690432663 | 0.0167489976252318 | 0.5766445504790442 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_drawdown_stress | 11487 | 140 | 0.012187690432663 | 0.0167489976252318 | 0.5766445504790442 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_drawdown_stress | 11487 | 140 | 0.012187690432663 | 0.0167489976252318 | 0.5766445504790442 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_drawdown_stress | 11487 | 140 | 0.012187690432663 | 0.0167489976252318 | 0.5766445504790442 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_intraday_instability | 11487 | 140 | 0.012187690432663 | 0.0785164237644892 | 0.7207247982474916 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_intraday_instability | 11487 | 140 | 0.012187690432663 | 0.0785164237644892 | 0.7207247982474916 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_intraday_instability | 11487 | 140 | 0.012187690432663 | 0.0785164237644892 | 0.7207247982474916 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_intraday_instability | 11487 | 140 | 0.012187690432663 | 0.0785164237644892 | 0.7207247982474916 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_return_shock | 11487 | 140 | 0.012187690432663 | 0.0945827605288938 | 0.6680560626471439 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_return_shock | 11487 | 140 | 0.012187690432663 | 0.0945827605288938 | 0.6680560626471439 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_return_shock | 11487 | 140 | 0.012187690432663 | 0.0945827605288938 | 0.6680560626471439 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_return_shock | 11487 | 140 | 0.012187690432663 | 0.0945827605288938 | 0.6680560626471439 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_stablecoin_peg_stress | 11487 | 140 | 0.012187690432663 | 0.0829354035165064 | 0.4498435709879264 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |
| main_weak_label | ablation | weak_label_3d | score_component_stablecoin_peg_stress | 11487 | 140 | 0.012187690432663 | 0.0829354035165064 | 0.4498435709879264 | Ablation, placebo, and sensitivity checks evaluate robustness against weak labels, not verified fraud ground truth. |

Main figures:

- results/figures/ablation_ap_comparison.png
- results/figures/placebo_lift_comparison.png

## 11. False-alert taxonomy and error review

The false-alert taxonomy classifies top alerts into event-window hits, stablecoin peg-stress non-events, multi-method market-stress non-events, DeFi context shocks, and isolated anomaly review cases.

### False-alert summary

| taxonomy_category | n_alerts | mean_weak_supervision_score | mean_transparent_score | mean_anomaly_score | weak_label_3d_rate | weak_label_7d_rate | mean_lf_vote_count | share_of_top_alerts | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| multi_method_market_stress_non_event | 295 | 98.05694868038005 | 96.62417205595712 | 0.954887470434522 | 0.0 | 0.0 | 3.701694915254237 | 0.5184534270650264 | Non-event alerts where several methods agree and market stress is visible. |
| market_stress_non_event | 89 | 96.01757922732388 | 90.55551805998574 | 0.8998178693452198 | 0.0 | 0.0 | 2.0 | 0.156414762741652 | Non-event alerts mainly explained by market volatility, return, drawdown, or volume stress. |
| multi_method_consensus_non_event | 68 | 97.1712908198014 | 95.65231028425995 | 0.9220144639208516 | 0.0 | 0.0 | 2.838235294117647 | 0.1195079086115993 | Non-event alerts where methods agree but market-stress evidence is less direct. |
| event_window_hit_3d | 62 | 98.28677298601224 | 96.69177218566853 | 0.9662037310058776 | 1.0 | 1.0 | 4.258064516129032 | 0.1089630931458699 | Top alerts that align with tight public incident windows. |
| defi_context_shock_non_event | 21 | 95.49988185402133 | 86.9728512977403 | 0.8575346043353356 | 0.0 | 0.0 | 2.0 | 0.0369068541300527 | Non-event alerts mainly explained by DeFi or chain-context variables. |
| isolated_anomaly_review | 16 | 96.64131191782012 | 95.56999216505616 | 0.7444012797074955 | 0.0 | 0.0 | 2.0 | 0.0281195079086115 | Isolated high-score cases that need manual review and are likely false-alert candidates. |
| event_window_hit_7d | 15 | 97.08249905690492 | 91.45875047154756 | 0.9734308348567946 | 0.0 | 1.0 | 3.066666666666667 | 0.0263620386643233 | Top alerts that align with wider public incident windows. |
| stablecoin_peg_stress_non_event | 3 | 99.59954731435536 | 97.75398276312352 | 0.9994921795653056 | 0.0 | 0.0 | 5.0 | 0.0052724077328646 | Stablecoin peg-stress alerts outside public incident windows. |

### Error-review sample excerpt

| date | asset | taxonomy_category | manual_review_priority | weak_supervision_score | transparent_risk_score | anomaly_ensemble_score | lf_vote_count | weak_label_3d | weak_label_7d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-03-11 | USDC | event_window_hit_3d | high | 99.9956472534169 | 100.0 | 1.0 | 7 | 1 | 1 |
| 2023-03-12 | USDC | event_window_hit_3d | high | 99.9956472534169 | 99.88682858883956 | 0.9987812309567335 | 7 | 1 | 1 |
| 2022-11-09 | SOL | event_window_hit_3d | high | 99.80847915034389 | 99.96517802733524 | 1.0 | 6 | 1 | 1 |
| 2022-05-11 | USDT | event_window_hit_3d | high | 99.80847915034389 | 99.98258901366762 | 0.9972577696526508 | 6 | 1 | 1 |
| 2022-05-11 | BTC | event_window_hit_3d | high | 99.80847915034389 | 99.75624619134676 | 0.9539914686166971 | 6 | 1 | 1 |
| 2022-05-11 | USDT | event_window_hit_3d | high | 99.80847915034389 | 99.9912945068338 | 0.9975624619134674 | 6 | 1 | 1 |
| 2022-05-12 | USDT | event_window_hit_3d | high | 99.80847915034389 | 99.89553408200574 | 0.9966483851310176 | 6 | 1 | 1 |
| 2022-05-12 | USDT | event_window_hit_3d | high | 99.80847915034389 | 99.90423957517194 | 0.9969530773918344 | 6 | 1 | 1 |
| 2023-06-10 | BNB | event_window_hit_7d | high | 99.80847915034389 | 99.79106816401148 | 0.9823278488726388 | 6 | 0 | 1 |
| 2022-05-09 | BTC | event_window_hit_3d | high | 99.80847915034389 | 99.87812309567336 | 0.9817184643510056 | 6 | 1 | 1 |
| 2023-03-11 | USDT | event_window_hit_3d | high | 99.80847915034389 | 98.9292243405589 | 0.9998476538695916 | 6 | 1 | 1 |
| 2023-06-10 | ETH | event_window_hit_7d | high | 99.29050230695567 | 97.57987289979977 | 0.9859841560024376 | 5 | 0 | 1 |
| 2024-03-19 | ETH | event_window_hit_7d | high | 98.87699138156177 | 98.45042221641856 | 0.9890310786106032 | 4 | 0 | 1 |
| 2024-03-20 | ETH | event_window_hit_7d | high | 98.87699138156177 | 96.87472795333856 | 0.959780621572212 | 4 | 0 | 1 |
| 2022-05-05 | BTC | event_window_hit_7d | high | 98.87699138156177 | 98.25890136676244 | 0.9616087751371116 | 4 | 0 | 1 |
| 2023-06-12 | BNB | event_window_hit_7d | high | 96.79637851484286 | 97.16200922782276 | 0.9360146252285192 | 3 | 0 | 1 |
| 2022-05-13 | USDT | event_window_hit_7d | high | 96.79637851484286 | 93.20971533037348 | 0.9890310786106032 | 3 | 0 | 1 |
| 2022-05-13 | USDT | event_window_hit_7d | high | 96.79637851484286 | 93.20100983720728 | 0.9887263863497868 | 3 | 0 | 1 |
| 2023-03-15 | USDT | event_window_hit_7d | high | 95.96500391747192 | 92.78314616523026 | 0.9917733089579523 | 2 | 0 | 1 |
| 2023-03-16 | USDT | event_window_hit_7d | high | 95.96500391747192 | 91.07686950465744 | 0.9722730042656916 | 2 | 0 | 1 |
| 2021-12-04 | BTC | multi_method_market_stress_non_event | medium_high | 99.80847915034389 | 99.79977365717768 | 0.9865935405240708 | 6 | 0 | 0 |
| 2021-05-19 | BTC | multi_method_market_stress_non_event | medium_high | 99.80847915034389 | 99.93906154783669 | 1.0 | 6 | 0 | 0 |
| 2021-04-05 | USDT | multi_method_market_stress_non_event | medium_high | 99.80847915034389 | 99.59954731435536 | 0.978823887873248 | 6 | 0 | 0 |
| 2021-04-05 | USDT | multi_method_market_stress_non_event | medium_high | 99.80847915034389 | 99.59084182118916 | 0.9776051188299816 | 6 | 0 | 0 |
| 2024-08-05 | BNB | multi_method_market_stress_non_event | medium_high | 99.80847915034389 | 99.74754069818054 | 0.9963436928702012 | 6 | 0 | 0 |
| 2022-11-10 | USDT | multi_method_market_stress_non_event | medium_high | 99.80847915034389 | 99.8520066161748 | 0.994210847044485 | 6 | 0 | 0 |
| 2022-11-10 | USDT | multi_method_market_stress_non_event | medium_high | 99.80847915034389 | 99.860712109341 | 0.9945155393053016 | 6 | 0 | 0 |
| 2022-06-13 | BTC | multi_method_market_stress_non_event | medium_high | 99.80847915034389 | 99.66048576651868 | 0.9987812309567335 | 6 | 0 | 0 |
| 2024-08-05 | BTC | multi_method_market_stress_non_event | medium_high | 99.80847915034389 | 99.73883520501435 | 0.9945155393053016 | 6 | 0 | 0 |
| 2021-05-19 | ETH | multi_method_market_stress_non_event | medium_high | 99.80847915034389 | 99.5647253416906 | 0.9829372333942716 | 6 | 0 | 0 |

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
