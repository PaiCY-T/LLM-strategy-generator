# Backtest Execution Results Report

## Executive Summary

- **Total Executions**: 20
- **Successful**: 20 (100.0%)
- **Failed**: 0 (0.0%)
- **Profitable Strategies (Level 3)**: 20

## Success/Failure Breakdown

| Status | Count | Percentage |
|--------|-------|------------|
| Successful | 20 | 100.0% |
| Failed | 0 | 0.0% |

## Classification Level Distribution

| Level | Name | Count | Percentage |
|-------|------|-------|------------|
| 0 | Failed | 0 | 0.0% |
| 1 | Executed | 0 | 0.0% |
| 2 | Valid Metrics | 0 | 0.0% |
| 3 | Profitable | 20 | 100.0% |

## Performance Metrics Summary

| Metric | Value |
|--------|-------|
| Avg Sharpe Ratio | 0.7196 |
| Avg Return | 404.35% |
| Avg Max Drawdown | -34.37% |
| Win Rate | 100.0% |
| Execution Success Rate | 100.0% |


## Statistical Validation (v1.1)

### Validation Framework Settings

- **Dynamic Threshold**: 0.80
- **Benchmark**: 0050.TW (Taiwan 50 ETF)
- **Margin**: 0.2 (active must beat passive by 0.2 Sharpe)
- **Significance Level (α)**: 0.05
- **Bonferroni Corrected α**: 0.0025

### Validation Statistics

- **Total Validated**: 4/20 (20.0%)
- **Statistically Significant**: 4
- **Beat Dynamic Threshold**: 4

### Validated Strategies

| Strategy | Sharpe | Threshold | Statistical Sig. | Validated |
|----------|--------|-----------|------------------|------------|
| iter0 | 0.68 | 0.80 | ❌ | ❌ |
| iter1 | 0.82 | 0.80 | ✅ | ✅ |
| iter2 | 0.93 | 0.80 | ✅ | ✅ |
| iter3 | 0.75 | 0.80 | ❌ | ❌ |
| iter4 | 0.64 | 0.80 | ❌ | ❌ |
| iter5 | 0.54 | 0.80 | ❌ | ❌ |
| iter6 | 0.76 | 0.80 | ❌ | ❌ |
| iter7 | 0.68 | 0.80 | ❌ | ❌ |
| iter8 | 0.67 | 0.80 | ❌ | ❌ |
| iter9 | 0.94 | 0.80 | ✅ | ✅ |
| iter10 | 0.78 | 0.80 | ❌ | ❌ |
| iter11 | 0.52 | 0.80 | ❌ | ❌ |
| iter12 | 0.75 | 0.80 | ❌ | ❌ |
| iter13 | 0.94 | 0.80 | ✅ | ✅ |
| iter14 | 0.80 | 0.80 | ❌ | ❌ |
| iter15 | 0.63 | 0.80 | ❌ | ❌ |
| iter16 | 0.43 | 0.80 | ❌ | ❌ |
| iter17 | 0.77 | 0.80 | ❌ | ❌ |
| iter18 | 0.63 | 0.80 | ❌ | ❌ |
| iter19 | 0.73 | 0.80 | ❌ | ❌ |

## Execution Statistics

| Metric | Value |
|--------|-------|
| Average Execution Time | 14.65s |
| Total Execution Time | 292.94s |
| Timeout Count | 0 |
