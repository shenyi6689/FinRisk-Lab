# Topic 2 Data Notes

This module uses four data layers.

## Layer 1: Yahoo OHLCV

Daily open, high, low, close, and volume data for BTC, ETH, BNB, SOL, USDC, and USDT.

Main use:
- returns
- rolling volatility
- volume z-score
- drawdown
- stablecoin peg deviation

## Layer 2: Coin Metrics

Public network metrics where available.

Main use:
- active address coverage
- transaction count coverage
- market cap or supply context

Coverage may be uneven across assets. Low-coverage metrics should be reported in the coverage matrix and treated as supplementary context.

## Layer 3: DeFiLlama

DeFi and stablecoin context.

Main use:
- stablecoin supply context
- DEX volume context
- chain TVL context

These variables are contextual signals. They are not incident labels.

## Layer 4: Incident ledger

Manual ledger of public crypto market-integrity incidents.

Main use:
- event date
- affected asset
- event type
- severity
- source note
- weak-label event window

Incident labels are weak labels and should not be treated as verified fraud ground truth.
