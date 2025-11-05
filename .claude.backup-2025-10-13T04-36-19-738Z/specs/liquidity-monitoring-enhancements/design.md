# Design: Liquidity Monitoring Enhancements

**Spec ID**: liquidity-monitoring-enhancements
**Status**: Draft
**Last Updated**: 2025-10-10

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              Iteration Engine (Existing)                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ iteration_engine.py                                   │  │
│  │   └─> Generates strategies                           │  │
│  │   └─> Saves to generated_strategy_iterN.py          │  │
│  │   └─> Logs to iteration_history.json                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│          Enhanced Monitoring System (NEW)                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Component 1: Liquidity Compliance Checker             │  │
│  │  - analyze_metrics.py (enhanced)                     │  │
│  │  - Parses strategy code with AST                     │  │
│  │  - Validates ≥150M threshold                         │  │
│  │  - Logs to liquidity_compliance.json                 │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Component 2: Performance Analyzer                     │  │
│  │  - analyze_performance_by_threshold.py (new)         │  │
│  │  - Groups strategies by liquidity threshold          │  │
│  │  - Compares Sharpe, success rate, market impact      │  │
│  │  - Generates LIQUIDITY_PERFORMANCE_REPORT.md         │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Component 3: Market Statistics Analyzer               │  │
│  │  - analyze_market_liquidity.py (new)                 │  │
│  │  - Queries Finlab for trading value data            │  │
│  │  - Counts stocks by threshold buckets               │  │
│  │  - Generates MARKET_LIQUIDITY_STATS.md              │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Component 4: Dynamic Liquidity Calculator             │  │
│  │  - src/liquidity_calculator.py (new module)          │  │
│  │  - calculate_min_liquidity() function                │  │
│  │  - Foundation for future prompt integration          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Output Artifacts                            │
│  - liquidity_compliance.json                                 │
│  - LIQUIDITY_PERFORMANCE_REPORT.md                          │
│  - MARKET_LIQUIDITY_STATS.md                                │
│  - market_liquidity_stats.json                              │
└─────────────────────────────────────────────────────────────┘
```

## Component Designs

### Component 1: Liquidity Compliance Checker

**File**: `analyze_metrics.py` (enhancement)

**New Functions**:

```python
def extract_liquidity_threshold(strategy_code: str) -> Optional[int]:
    """Extract liquidity threshold from strategy code using AST parsing.

    Looks for patterns like:
    - trading_value.rolling(N).mean() > THRESHOLD
    - trading_value.rolling(N).mean().shift(M) > THRESHOLD

    Returns:
        Threshold value in TWD (e.g., 150_000_000) or None if not found
    """
    pass

def check_liquidity_compliance(
    iteration_num: int,
    strategy_file: str,
    min_threshold: int = 150_000_000
) -> Dict[str, Any]:
    """Check if strategy meets liquidity compliance requirements.

    Returns:
        {
            'iteration': int,
            'threshold_found': int or None,
            'compliant': bool,
            'timestamp': str,
            'strategy_file': str
        }
    """
    pass

def log_compliance_result(result: Dict[str, Any], log_file: str = 'liquidity_compliance.json'):
    """Append compliance result to JSON log."""
    pass

def get_compliance_statistics(log_file: str = 'liquidity_compliance.json') -> Dict[str, Any]:
    """Calculate compliance statistics from log.

    Returns:
        {
            'total_checks': int,
            'compliant_count': int,
            'compliance_rate': float,
            'non_compliant_iterations': List[int],
            'average_threshold': float
        }
    """
    pass
```

**Integration Point**: Add to `analyze_iteration_history()` function in `analyze_metrics.py`

**Data Structure** (`liquidity_compliance.json`):
```json
{
  "checks": [
    {
      "iteration": 0,
      "threshold_found": 150000000,
      "compliant": true,
      "timestamp": "2025-10-10T07:22:55",
      "strategy_file": "generated_strategy_iter0.py"
    }
  ],
  "summary": {
    "total_checks": 125,
    "compliant_count": 125,
    "compliance_rate": 1.0,
    "last_updated": "2025-10-10T08:00:00"
  }
}
```

### Component 2: Performance Analyzer

**File**: `analyze_performance_by_threshold.py` (new)

**Main Functions**:

```python
def group_strategies_by_threshold(
    history_file: str = 'iteration_history.json'
) -> Dict[int, List[Dict]]:
    """Group iteration history by liquidity threshold.

    Returns:
        {
            50_000_000: [strategy1, strategy2, ...],
            100_000_000: [...],
            150_000_000: [...]
        }
    """
    pass

def calculate_threshold_statistics(
    strategies: List[Dict]
) -> Dict[str, float]:
    """Calculate aggregate statistics for a threshold group.

    Returns:
        {
            'count': int,
            'avg_sharpe': float,
            'std_sharpe': float,
            'median_sharpe': float,
            'avg_cagr': float,
            'avg_max_dd': float,
            'success_rate': float  # Sharpe > 0.5
        }
    """
    pass

def compare_thresholds_significance(
    group1: List[Dict],
    group2: List[Dict],
    metric: str = 'sharpe_ratio'
) -> Dict[str, Any]:
    """Perform t-test to determine if performance difference is significant.

    Returns:
        {
            't_statistic': float,
            'p_value': float,
            'significant': bool,  # p < 0.05
            'effect_size': float   # Cohen's d
        }
    """
    pass

def generate_performance_report(
    threshold_groups: Dict[int, List[Dict]],
    output_file: str = 'LIQUIDITY_PERFORMANCE_REPORT.md'
):
    """Generate markdown report with threshold comparison."""
    pass
```

**Report Structure** (`LIQUIDITY_PERFORMANCE_REPORT.md`):
```markdown
# Liquidity Threshold Performance Analysis

Generated: 2025-10-10

## Summary

| Threshold | Count | Avg Sharpe | Std Sharpe | Success Rate | Avg CAGR | Avg MaxDD |
|-----------|-------|------------|------------|--------------|----------|-----------|
| 50M       | 20    | 1.2450     | 0.5234     | 65%          | 15.2%    | -22.1%    |
| 100M      | 35    | 1.3821     | 0.4891     | 71%          | 16.8%    | -20.5%    |
| 150M      | 50    | 1.4156     | 0.4523     | 76%          | 17.3%    | -19.2%    |
| 200M      | 20    | 1.3902     | 0.4778     | 75%          | 17.1%    | -19.8%    |

## Statistical Significance

### 150M vs 100M
- t-statistic: 2.45
- p-value: 0.016
- **Significant**: Yes (p < 0.05)
- Effect size (Cohen's d): 0.31 (small-medium)

### 150M vs 50M
- t-statistic: 3.89
- p-value: 0.0003
- **Significant**: Yes (p < 0.001)
- Effect size (Cohen's d): 0.52 (medium)

## Recommendation

**Optimal Threshold**: 150M TWD
- Best balance of performance (Sharpe 1.42) and availability
- Statistically significant improvement over lower thresholds
- Acceptable market impact (≤2.2% worst case)
```

### Component 3: Market Statistics Analyzer

**File**: `analyze_market_liquidity.py` (new)

**Main Functions**:

```python
def query_market_liquidity(
    data_obj,
    lookback_days: int = 60
) -> pd.DataFrame:
    """Query Taiwan stock market for trading value statistics.

    Returns DataFrame with columns:
    - stock_id
    - avg_trading_value_60d
    - min_trading_value_60d
    - max_trading_value_60d
    """
    pass

def categorize_by_threshold(
    df: pd.DataFrame,
    thresholds: List[int] = [50_000_000, 100_000_000, 150_000_000, 200_000_000]
) -> Dict[int, int]:
    """Count stocks meeting each threshold.

    Returns:
        {
            50_000_000: 1500,
            100_000_000: 800,
            150_000_000: 450,
            200_000_000: 250
        }
    """
    pass

def categorize_by_market_cap(
    df: pd.DataFrame
) -> Dict[str, Dict[int, int]]:
    """Group by market cap and count stocks per threshold.

    Returns:
        {
            'large_cap': {150_000_000: 300, ...},
            'mid_cap': {150_000_000: 120, ...},
            'small_cap': {150_000_000: 30, ...}
        }
    """
    pass

def generate_market_report(
    threshold_counts: Dict[int, int],
    marketcap_breakdown: Dict[str, Dict[int, int]],
    output_file: str = 'MARKET_LIQUIDITY_STATS.md'
):
    """Generate markdown report with market liquidity statistics."""
    pass
```

**Report Structure** (`MARKET_LIQUIDITY_STATS.md`):
```markdown
# Taiwan Stock Market Liquidity Analysis

Generated: 2025-10-10
Lookback Period: 60 days

## Overall Market

Total Stocks Analyzed: 1,800

| Threshold | Count | % of Market |
|-----------|-------|-------------|
| ≥ 50M     | 1,200 | 66.7%       |
| ≥ 100M    | 650   | 36.1%       |
| ≥ 150M    | 380   | 21.1%       |
| ≥ 200M    | 220   | 12.2%       |

## By Market Capitalization

### Large Cap (>100B TWD)
- ≥ 150M: 280 stocks (73.7% of large cap)

### Mid Cap (10B-100B TWD)
- ≥ 150M: 85 stocks (22.4% of mid cap)

### Small Cap (<10B TWD)
- ≥ 150M: 15 stocks (3.9% of small cap)

## Implications

With 150M threshold:
- Universe: ~380 stocks (21% of market)
- Adequate for diversification (6-12 stock portfolios)
- Skewed toward large-cap (reduces small-cap risk)
```

### Component 4: Dynamic Liquidity Calculator

**File**: `src/liquidity_calculator.py` (new module)

**Core Function**:

```python
def calculate_min_liquidity(
    portfolio_value: float = 20_000_000,  # TWD
    stock_count: int = 8,
    safety_multiplier: float = 50.0,      # 50x = 2% market impact
    safety_margin: float = 0.9            # 10% buffer below theoretical
) -> Dict[str, Any]:
    """Calculate minimum liquidity requirement for given portfolio parameters.

    Formula:
        position_size = portfolio_value / stock_count
        theoretical_min = position_size * safety_multiplier
        recommended = theoretical_min * (1 - safety_margin)

    Args:
        portfolio_value: Total capital in TWD
        stock_count: Number of stocks in portfolio
        safety_multiplier: Multiplier for market impact (50x = 2%)
        safety_margin: Buffer percentage below theoretical minimum

    Returns:
        {
            'portfolio_value': float,
            'stock_count': int,
            'position_size': float,
            'theoretical_min': float,
            'recommended_threshold': float,
            'market_impact_pct': float,
            'safety_multiplier': float
        }

    Example:
        >>> calc = calculate_min_liquidity(20_000_000, stock_count=6)
        >>> calc['recommended_threshold']
        150000000  # 150M TWD
        >>> calc['market_impact_pct']
        2.2  # 2.2% at worst case
    """
    position_size = portfolio_value / stock_count
    theoretical_min = position_size * safety_multiplier
    recommended = theoretical_min * (1 - safety_margin)
    market_impact = (position_size / recommended) * 100

    return {
        'portfolio_value': portfolio_value,
        'stock_count': stock_count,
        'position_size': position_size,
        'theoretical_min': theoretical_min,
        'recommended_threshold': recommended,
        'market_impact_pct': market_impact,
        'safety_multiplier': safety_multiplier
    }

def validate_liquidity_threshold(
    threshold: float,
    portfolio_value: float = 20_000_000,
    stock_count_range: tuple = (6, 12)
) -> Dict[str, Any]:
    """Validate if threshold is safe across stock count range.

    Returns:
        {
            'threshold': float,
            'valid': bool,
            'worst_case_impact': float,
            'worst_case_stock_count': int,
            'details': Dict[int, Dict]
        }
    """
    pass
```

**Unit Tests** (in `tests/test_liquidity_calculator.py`):

```python
def test_calculate_min_liquidity_basic():
    result = calculate_min_liquidity(20_000_000, stock_count=6)
    assert result['position_size'] == pytest.approx(3_333_333, rel=1)
    assert result['theoretical_min'] == pytest.approx(166_666_650, rel=1)
    assert result['market_impact_pct'] < 2.5

def test_calculate_min_liquidity_edge_cases():
    # Test with 12 stocks (best case)
    result = calculate_min_liquidity(20_000_000, stock_count=12)
    assert result['market_impact_pct'] < 1.5

    # Test with 6 stocks (worst case)
    result = calculate_min_liquidity(20_000_000, stock_count=6)
    assert result['market_impact_pct'] < 2.5

def test_validate_150m_threshold():
    result = validate_liquidity_threshold(150_000_000)
    assert result['valid'] is True
    assert result['worst_case_impact'] < 2.5
    assert result['worst_case_stock_count'] == 6
```

## Data Flow Diagram

```
┌────────────────────┐
│ iteration_engine   │
│ generates strategy │
└────────┬───────────┘
         │
         ▼
┌────────────────────────────────┐
│ generated_strategy_iterN.py    │
│ Contains: liquidity_filter =   │
│   trading_value.rolling(20)    │
│   .mean().shift(1) > 150M      │
└────────┬───────────────────────┘
         │
         ├──────────────────────┬──────────────────┬──────────────────┐
         ▼                      ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐  ┌─────────────────┐
│ Compliance      │  │ Performance     │  │ Market      │  │ Calculator      │
│ Checker         │  │ Analyzer        │  │ Analyzer    │  │ (future use)    │
│                 │  │                 │  │             │  │                 │
│ • AST parse     │  │ • Group by      │  │ • Query     │  │ • Validate      │
│ • Extract       │  │   threshold     │  │   Finlab    │  │   thresholds    │
│   threshold     │  │ • Calc stats    │  │ • Count     │  │ • Recommend     │
│ • Validate      │  │ • T-test        │  │   stocks    │  │   values        │
│   ≥150M         │  │ • Report        │  │ • Report    │  │                 │
└────────┬────────┘  └────────┬────────┘  └──────┬──────┘  └─────────────────┘
         │                    │                   │
         ▼                    ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ liquidity_      │  │ LIQUIDITY_      │  │ MARKET_         │
│ compliance.json │  │ PERFORMANCE_    │  │ LIQUIDITY_      │
│                 │  │ REPORT.md       │  │ STATS.md        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Error Handling

### Compliance Checker Errors
- **AST Parse Failure**: Fall back to regex pattern matching, log warning
- **No Threshold Found**: Mark as non-compliant, flag for manual review
- **Invalid Threshold Type**: Try numeric conversion, else mark as error

### Performance Analyzer Errors
- **Insufficient Data**: Require minimum 10 strategies per threshold group
- **Statistical Test Failure**: Report raw statistics without significance testing
- **Missing Metrics**: Skip strategies with incomplete data

### Market Analyzer Errors
- **Finlab API Failure**: Use cached data if available, else abort with error
- **Empty Dataset**: Log warning, generate report with disclaimer
- **Data Quality Issues**: Filter outliers (>1000x median), log removals

## Performance Considerations

- **AST Parsing**: Cache parsed results per file (avoid re-parsing)
- **Market Query**: Limit to 60-day lookback, cache for 24 hours
- **Statistical Tests**: Use scipy.stats for efficiency
- **Report Generation**: Stream write to file (don't load all in memory)

## Security Considerations

- All file operations use safe paths (no user input in file names)
- AST parsing is read-only (no code execution)
- JSON logs use atomic writes (prevent corruption)
- Market queries use read-only Finlab API

## Backwards Compatibility

- Existing `iteration_history.json` format unchanged
- New compliance log is separate file
- Analyze_metrics.py maintains existing output format
- All new features are opt-in

## Future Extensions

1. **Real-time Monitoring Dashboard**: Web UI showing compliance metrics
2. **Automated Threshold Adjustment**: Dynamically adjust based on market conditions
3. **Multi-Currency Support**: Extend to other markets (USD, EUR)
4. **Machine Learning**: Predict optimal threshold based on market regime
