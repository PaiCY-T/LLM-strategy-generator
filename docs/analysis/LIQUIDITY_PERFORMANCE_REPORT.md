# Liquidity Threshold Performance Analysis Report

**Generated:** 2025-10-10 08:21:02

**Analysis:** Comparison of trading strategy performance across different liquidity thresholds

## Summary Statistics by Threshold

| Threshold | Count | Avg Sharpe | Std Sharpe | Median Sharpe | Avg CAGR | Avg Max DD | Success Rate |
|-----------|-------|------------|------------|---------------|----------|------------|-------------|
| 10M TWD | 2 | 1.3377 | N/A | 1.3377 | 5.14% | -36.47% | 100.00% |
| 20M TWD | 4 | 2.0006 | 0.1307 | 2.0006 | 28.56% | -37.71% | 100.00% |
| 30M TWD | 3 | 2.2060 | N/A | 2.2060 | -0.72% | -33.76% | 100.00% |
| 50M TWD | 69 | 1.2582 | 0.8447 | 1.2819 | 8.64% | -27.98% | 81.82% |
| 100M TWD | 7 | 1.6137 | 0.4371 | 1.5597 | 14.66% | -29.89% | 100.00% |

## Statistical Significance Tests

Pairwise comparisons of Sharpe ratios between threshold groups using independent t-tests.

*No pairwise comparisons performed. Requires at least 10 strategies per threshold group.*

## Recommendations

### Optimal Threshold

Based on average Sharpe ratio, the **100M TWD** threshold shows the best performance:

- **Average Sharpe Ratio:** 1.6137
- **Median Sharpe Ratio:** 1.5597
- **Success Rate:** 100.00%
- **Sample Size:** 7 strategies

### Current Threshold Analysis

**Note:** The current minimum threshold of 150M TWD has **no historical data**. All 85 historical strategies used lower thresholds.

**Recommendation:** Consider reducing the minimum threshold to align with historical practice, or collect more data using the 150M threshold before making comparisons.

## Detailed Statistics

### 10M TWD Threshold

**Sample Size:** 2 strategies

**Performance Metrics:**
- Average Sharpe Ratio: 1.3377
- Std Dev Sharpe Ratio: N/A
- Median Sharpe Ratio: 1.3377
- Average CAGR: 5.14%
- Average Max Drawdown: -36.47%
- Success Rate (Sharpe > 0.5): 100.00%

### 20M TWD Threshold

**Sample Size:** 4 strategies

**Performance Metrics:**
- Average Sharpe Ratio: 2.0006
- Std Dev Sharpe Ratio: 0.1307
- Median Sharpe Ratio: 2.0006
- Average CAGR: 28.56%
- Average Max Drawdown: -37.71%
- Success Rate (Sharpe > 0.5): 100.00%

### 30M TWD Threshold

**Sample Size:** 3 strategies

**Performance Metrics:**
- Average Sharpe Ratio: 2.2060
- Std Dev Sharpe Ratio: N/A
- Median Sharpe Ratio: 2.2060
- Average CAGR: -0.72%
- Average Max Drawdown: -33.76%
- Success Rate (Sharpe > 0.5): 100.00%

### 50M TWD Threshold

**Sample Size:** 69 strategies

**Performance Metrics:**
- Average Sharpe Ratio: 1.2582
- Std Dev Sharpe Ratio: 0.8447
- Median Sharpe Ratio: 1.2819
- Average CAGR: 8.64%
- Average Max Drawdown: -27.98%
- Success Rate (Sharpe > 0.5): 81.82%

### 100M TWD Threshold

**Sample Size:** 7 strategies

**Performance Metrics:**
- Average Sharpe Ratio: 1.6137
- Std Dev Sharpe Ratio: 0.4371
- Median Sharpe Ratio: 1.5597
- Average CAGR: 14.66%
- Average Max Drawdown: -29.89%
- Success Rate (Sharpe > 0.5): 100.00%

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

