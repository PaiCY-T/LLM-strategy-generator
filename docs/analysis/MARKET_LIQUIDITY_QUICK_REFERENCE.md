# Market Liquidity Statistics Analyzer - Quick Reference

## Usage

### Run Full Market Analysis
```bash
python3 analyze_market_liquidity.py
```

This will:
1. Query Finlab data for trading value and market cap
2. Calculate 60-day rolling averages for all stocks
3. Categorize stocks by liquidity thresholds
4. Generate MARKET_LIQUIDITY_STATS.md report
5. Display summary statistics

**Execution time**: 5-10 minutes first run, <1 minute subsequent runs

---

## Individual Function Usage

### 1. Query Market Liquidity
```python
from analyze_market_liquidity import query_market_liquidity
from finlab import data
import finlab
import os

finlab.login(os.getenv('FINLAB_API_TOKEN'))

# Get liquidity data for all stocks
df = query_market_liquidity(data, lookback_days=60, verbose=True)

print(f"Total stocks: {len(df)}")
print(f"Columns: {list(df.columns)}")
print(df.head())
```

**Output columns**:
- `stock_id`: Stock ticker symbol
- `avg_trading_value_60d`: 60-day rolling average trading value (TWD)
- `min_trading_value`: Minimum trading value over lookback period
- `max_trading_value`: Maximum trading value over lookback period
- `data_points`: Number of valid data points (quality indicator)

### 2. Categorize by Threshold
```python
from analyze_market_liquidity import categorize_by_threshold

# Default thresholds: 50M, 100M, 150M, 200M TWD
counts = categorize_by_threshold(df, verbose=True)

print(f"Stocks above 150M: {counts[150_000_000]:,}")

# Custom thresholds
custom_thresholds = [75_000_000, 125_000_000, 175_000_000]
custom_counts = categorize_by_threshold(df, thresholds=custom_thresholds, verbose=True)
```

### 3. Categorize by Market Cap
```python
from analyze_market_liquidity import categorize_by_market_cap

breakdown = categorize_by_market_cap(df, data, verbose=True)

# Access results
large_cap_at_150m = breakdown['large_cap'][150_000_000]
mid_cap_at_150m = breakdown['mid_cap'][150_000_000]
small_cap_at_150m = breakdown['small_cap'][150_000_000]

print(f"150M threshold breakdown:")
print(f"  Large cap: {large_cap_at_150m} stocks")
print(f"  Mid cap: {mid_cap_at_150m} stocks")
print(f"  Small cap: {small_cap_at_150m} stocks")
```

### 4. Generate Custom Report
```python
from analyze_market_liquidity import generate_market_report

# Generate report with custom parameters
report_path = generate_market_report(
    threshold_counts=counts,
    marketcap_breakdown=breakdown,
    total_stocks=len(df),
    lookback_days=90,  # Custom lookback period
    output_file='CUSTOM_LIQUIDITY_REPORT.md',
    verbose=True
)

print(f"Report saved to: {report_path}")
```

---

## Current Market Statistics (As of 2025-10-10)

### Overall Market
- **Total Stocks Analyzed**: 2,632
- **Data Source**: 60-day rolling average of trading value

### Stock Counts by Threshold
| Threshold | Stock Count | % of Market |
|-----------|-------------|-------------|
| 50M TWD   | 803         | 30.5%       |
| 100M TWD  | 599         | 22.8%       |
| 150M TWD  | 480         | 18.2%       |
| 200M TWD  | 413         | 15.7%       |

### Market Cap Distribution at 150M TWD
- **Large Cap** (>100B TWD): 105 stocks (25.6%)
- **Mid Cap** (10B-100B TWD): 231 stocks (56.3%)
- **Small Cap** (<10B TWD): 74 stocks (18.0%)

---

## Integration with Strategy Generation

### Check if Stock Meets Threshold
```python
def meets_liquidity_threshold(stock_id, df, threshold=150_000_000):
    """Check if stock meets minimum liquidity threshold."""
    stock_data = df[df['stock_id'] == stock_id]
    if len(stock_data) == 0:
        return False
    return stock_data['avg_trading_value_60d'].values[0] >= threshold

# Example
if meets_liquidity_threshold('2330', df, 150_000_000):
    print("Stock 2330 meets 150M threshold")
```

### Filter Universe by Liquidity
```python
def filter_by_liquidity(df, threshold=150_000_000):
    """Get list of stocks meeting liquidity threshold."""
    return df[df['avg_trading_value_60d'] >= threshold]['stock_id'].tolist()

# Get tradeable universe
liquid_stocks = filter_by_liquidity(df, 150_000_000)
print(f"Tradeable universe: {len(liquid_stocks)} stocks")
```

### Market Cap Aware Filtering
```python
def filter_by_liquidity_and_cap(df, data_obj, threshold=150_000_000, cap_category='mid_cap'):
    """Filter stocks by liquidity and market cap category."""
    import pandas as pd

    # Get market cap data
    market_cap = data_obj.get('etl:market_value')
    latest_market_cap = market_cap.iloc[-1]

    # Merge with liquidity data
    df_merged = df.copy()
    df_merged['market_cap'] = df_merged['stock_id'].map(latest_market_cap)
    df_merged = df_merged.dropna(subset=['market_cap'])

    # Categorize
    LARGE_CAP_THRESHOLD = 100_000_000_000
    MID_CAP_THRESHOLD = 10_000_000_000

    df_merged['cap_category'] = pd.cut(
        df_merged['market_cap'],
        bins=[0, MID_CAP_THRESHOLD, LARGE_CAP_THRESHOLD, float('inf')],
        labels=['small_cap', 'mid_cap', 'large_cap']
    )

    # Filter
    filtered = df_merged[
        (df_merged['avg_trading_value_60d'] >= threshold) &
        (df_merged['cap_category'] == cap_category)
    ]

    return filtered['stock_id'].tolist()

# Example: Get mid-cap stocks with 150M+ liquidity
mid_cap_liquid = filter_by_liquidity_and_cap(df, data, 150_000_000, 'mid_cap')
print(f"Mid-cap liquid stocks: {len(mid_cap_liquid)}")
```

---

## Threshold Selection Guidelines

### For Different Portfolio Strategies

**Weekly Rebalancing** (high turnover):
- **Recommended**: 200M TWD
- **Universe size**: 413 stocks (15.7%)
- **Rationale**: Minimize market impact from frequent trading

**Monthly Rebalancing** (balanced):
- **Recommended**: 150M TWD
- **Universe size**: 480 stocks (18.2%)
- **Rationale**: Good balance of liquidity and selection

**Quarterly Rebalancing** (low turnover):
- **Recommended**: 100M TWD
- **Universe size**: 599 stocks (22.8%)
- **Rationale**: Lower liquidity acceptable with less frequent trades

**Large Portfolios** (>20 positions):
- **Recommended**: 100M TWD
- **Universe size**: 599 stocks (22.8%)
- **Rationale**: Need wider selection for diversification

**Small Portfolios** (5-10 positions):
- **Recommended**: 200M TWD
- **Universe size**: 413 stocks (15.7%)
- **Rationale**: Can afford to be selective, minimize slippage

---

## Market Cap Category Definitions

```python
LARGE_CAP_THRESHOLD = 100_000_000_000  # 100 billion TWD (100億)
MID_CAP_THRESHOLD = 10_000_000_000      # 10 billion TWD (10億)

# Categories:
# - Large Cap: > 100億 TWD
# - Mid Cap: 10億 - 100億 TWD
# - Small Cap: < 10億 TWD
```

---

## Data Quality Indicators

### Valid Data Points
The `data_points` column indicates data quality:
- **>1000**: Excellent (>4 years of data)
- **500-1000**: Good (2-4 years)
- **100-500**: Moderate (few months to 2 years)
- **<100**: Poor (limited history)

### Filtering by Quality
```python
# Keep only stocks with >1 year of data (~250 trading days)
high_quality = df[df['data_points'] >= 250]
print(f"High quality stocks: {len(high_quality)}")
```

---

## Testing

### Run Unit Tests
```bash
python3 test_market_liquidity.py
```

**Tests include**:
1. Query market liquidity data
2. Categorize by threshold
3. Categorize by market cap
4. Generate market report

All tests should pass in ~20 seconds.

---

## Files

- **analyze_market_liquidity.py**: Main implementation (620 lines)
- **test_market_liquidity.py**: Unit tests (169 lines)
- **MARKET_LIQUIDITY_STATS.md**: Generated report (93 lines, auto-generated)
- **TASK3_MARKET_LIQUIDITY_ANALYSIS.md**: Full implementation summary (376 lines)

---

## Common Issues

### Issue: FINLAB_API_TOKEN not found
**Solution**: Ensure `.env` file exists with valid token
```bash
echo 'FINLAB_API_TOKEN=your_token_here' > .env
```

### Issue: Slow first run
**Explanation**: Finlab downloads historical data (~5-10 minutes)
**Solution**: Subsequent runs use cached data (<1 minute)

### Issue: Market cap data mismatch
**Explanation**: Some stocks have trading data but no market cap data
**Solution**: Script handles gracefully, reports 71.6% match rate

### Issue: Different stock counts than expected
**Explanation**: Analysis excludes stocks with insufficient data (<30 days)
**Solution**: Check `data_points` column for data quality indicators

---

## Next Steps

See **TASK3_MARKET_LIQUIDITY_ANALYSIS.md** for:
- Detailed implementation summary
- Integration recommendations
- Portfolio construction insights
- Task 4 and Task 5 planning
