# Backtest Execution Results Report

## Executive Summary

- **Total Executions**: 3
- **Successful**: 3 (100.0%)
- **Failed**: 0 (0.0%)
- **Profitable Strategies (Level 3)**: 3

## Success/Failure Breakdown

| Status | Count | Percentage |
|--------|-------|------------|
| Successful | 3 | 100.0% |
| Failed | 0 | 0.0% |

## Classification Level Distribution

| Level | Name | Count | Percentage |
|-------|------|-------|------------|
| 0 | Failed | 0 | 0.0% |
| 1 | Executed | 0 | 0.0% |
| 2 | Valid Metrics | 0 | 0.0% |
| 3 | Profitable | 3 | 100.0% |

## Performance Metrics Summary

| Metric | Value |
|--------|-------|
| Avg Sharpe Ratio | 0.8095 |
| Avg Return | 483.66% |
| Avg Max Drawdown | -31.46% |
| Win Rate | 100.0% |
| Execution Success Rate | 100.0% |


## Statistical Validation (v1.1)

### Validation Framework Settings

- **Dynamic Threshold**: 0.80
- **Benchmark**: 0050.TW (Taiwan 50 ETF)
- **Margin**: 0.2 (active must beat passive by 0.2 Sharpe)
- **Significance Level (α)**: 0.05
- **Bonferroni Corrected α**: 0.0167

### Validation Statistics

- **Total Validated**: 2/3 (66.7%)
- **Statistically Significant**: 3
- **Beat Dynamic Threshold**: 2

### Validated Strategies

| Strategy | Sharpe | Threshold | Statistical Sig. | Validated |
|----------|--------|-----------|------------------|------------|
| iter0 | 0.68 | 0.80 | ✅ | ❌ |
| iter1 | 0.82 | 0.80 | ✅ | ✅ |
| iter2 | 0.93 | 0.80 | ✅ | ✅ |

## Execution Statistics

| Metric | Value |
|--------|-------|
| Average Execution Time | 22.30s |
| Total Execution Time | 66.91s |
| Timeout Count | 0 |
