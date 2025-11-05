# Liquidity Threshold Performance Analysis Report

**Generated:** 2025-10-16 12:25:35

**Analysis:** Comparison of trading strategy performance across different liquidity thresholds

## Summary Statistics by Threshold

| Threshold | Count | Avg Sharpe | Std Sharpe | Median Sharpe | Avg CAGR | Avg Max DD | Success Rate |
|-----------|-------|------------|------------|---------------|----------|------------|-------------|
| 40M TWD | 5 | 0.6527 | 0.7545 | 0.3421 | 21.19% | -19.90% | 40.00% |
| 50M TWD | 365 | 1.0508 | 0.9095 | 1.0338 | 10.20% | -26.82% | 67.23% |
| 60M TWD | 1 | -0.0568 | N/A | -0.0568 | 20.29% | -24.65% | 0.00% |

## Statistical Significance Tests

Pairwise comparisons of Sharpe ratios between threshold groups using independent t-tests.

*No pairwise comparisons performed. Requires at least 10 strategies per threshold group.*

## Recommendations

### Optimal Threshold

Based on average Sharpe ratio, the **50M TWD** threshold shows the best performance:

- **Average Sharpe Ratio:** 1.0508
- **Median Sharpe Ratio:** 1.0338
- **Success Rate:** 67.23%
- **Sample Size:** 365 strategies

### Current Threshold Analysis

**Note:** The current minimum threshold of 150M TWD has **no historical data**. All 371 historical strategies used lower thresholds.

**Recommendation:** Consider reducing the minimum threshold to align with historical practice, or collect more data using the 150M threshold before making comparisons.

## Detailed Statistics

### 40M TWD Threshold

**Sample Size:** 5 strategies

**Performance Metrics:**
- Average Sharpe Ratio: 0.6527
- Std Dev Sharpe Ratio: 0.7545
- Median Sharpe Ratio: 0.3421
- Average CAGR: 21.19%
- Average Max Drawdown: -19.90%
- Success Rate (Sharpe > 0.5): 40.00%

### 50M TWD Threshold

**Sample Size:** 365 strategies

**Performance Metrics:**
- Average Sharpe Ratio: 1.0508
- Std Dev Sharpe Ratio: 0.9095
- Median Sharpe Ratio: 1.0338
- Average CAGR: 10.20%
- Average Max Drawdown: -26.82%
- Success Rate (Sharpe > 0.5): 67.23%

### 60M TWD Threshold

**Sample Size:** 1 strategies

**Performance Metrics:**
- Average Sharpe Ratio: -0.0568
- Std Dev Sharpe Ratio: N/A
- Median Sharpe Ratio: -0.0568
- Average CAGR: 20.29%
- Average Max Drawdown: -24.65%
- Success Rate (Sharpe > 0.5): 0.00%

## Methodology

### Data Sources
- **Strategy Performance:** `iteration_history.json` (125 total iterations)
- **Liquidity Thresholds:** `liquidity_compliance.json` (extracted from strategy code)

### Statistical Tests
- **Test:** Independent two-sample t-test
- **Null Hypothesis:** No difference in mean Sharpe ratios between threshold groups
- **Significance Level:** α = 0.05
- **Effect Size:** Cohen's d (|d| < 0.2: negligible, 0.2-0.5: small, 0.5-0.8: medium, > 0.8: large)
- **Minimum Sample Size:** 10 strategies per group for pairwise comparisons

### Metrics
- **Sharpe Ratio:** Risk-adjusted return measure
- **CAGR:** Compound Annual Growth Rate
- **Max Drawdown:** Maximum peak-to-trough decline
- **Success Rate:** Percentage of strategies with Sharpe > 0.5

