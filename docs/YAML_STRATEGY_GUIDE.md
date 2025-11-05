# YAML Strategy Guide - Complete Reference

**Version**: 1.0.0
**Schema Version**: strategy_schema_v1.json
**Last Updated**: 2025-10-26

---

## Table of Contents

1. [Schema Reference](#schema-reference)
2. [Metadata Section](#metadata-section)
3. [Indicators Section](#indicators-section)
4. [Entry Conditions Section](#entry-conditions-section)
5. [Exit Conditions Section](#exit-conditions-section)
6. [Position Sizing Section](#position-sizing-section)
7. [Risk Management Section](#risk-management-section)
8. [Complete Strategy Examples](#complete-strategy-examples)
9. [Advanced Topics](#advanced-topics)

---

## Schema Reference

### Top-Level Structure

```yaml
metadata:           # REQUIRED - Strategy identification
  name: string
  strategy_type: enum
  rebalancing_frequency: enum
  # ... other metadata fields

indicators:         # REQUIRED - At least one indicator type
  technical_indicators: [...]
  fundamental_factors: [...]
  custom_calculations: [...]
  volume_filters: [...]

entry_conditions:   # REQUIRED - At least one rule type
  threshold_rules: [...]
  ranking_rules: [...]
  logical_operator: enum
  min_liquidity: {...}

exit_conditions:    # OPTIONAL - Risk management
  stop_loss_pct: number
  take_profit_pct: number
  trailing_stop: {...}
  conditional_exits: [...]
  holding_period_days: integer
  exit_operator: enum

position_sizing:    # OPTIONAL - Defaults to equal_weight
  method: enum
  max_positions: integer
  max_position_pct: number
  weighting_field: string
  custom_formula: string

risk_management:    # OPTIONAL - Portfolio constraints
  max_sector_exposure: number
  rebalance_threshold: number
  max_drawdown_limit: number
  cash_reserve_pct: number

backtest_config:    # OPTIONAL - Backtest parameters
  start_date: string
  end_date: string
  initial_capital: number
  transaction_cost: number
  slippage: number
```

---

## Metadata Section

### Required Fields

#### `name`
- **Type**: String
- **Length**: 5-100 characters
- **Pattern**: Alphanumeric, spaces, underscores, hyphens
- **Description**: Unique strategy identifier

**Examples**:
```yaml
name: "High ROE Momentum Strategy"           # ✅ Descriptive
name: "Momentum_v2"                          # ✅ Simple
name: "Quality-Value Combined"               # ✅ With hyphens
name: "Test"                                 # ❌ Too short (<5 chars)
name: "Strategy with special chars @#$%"    # ❌ Invalid characters
```

#### `strategy_type`
- **Type**: Enum
- **Values**: `"momentum"`, `"mean_reversion"`, `"factor_combination"`
- **Description**: Primary strategy category

**Guidelines by Type**:

**momentum**:
- Use: Trend-following, breakout strategies
- Indicators: RSI, MACD, moving averages, momentum calculations
- Entry: Strong trends, volume confirmation
- Exit: Trailing stops, trend reversal signals
```yaml
strategy_type: "momentum"
```

**mean_reversion**:
- Use: Oversold bounce-back, range-bound strategies
- Indicators: RSI, Bollinger Bands, z-scores
- Entry: Extreme readings, oversold conditions
- Exit: Return to mean, overbought conditions
```yaml
strategy_type: "mean_reversion"
```

**factor_combination**:
- Use: Multi-factor fundamental + technical strategies
- Indicators: Fundamental factors (ROE, growth) + technical filters
- Entry: Ranking rules, quality/value screens
- Exit: Less critical, often monthly rebalancing
```yaml
strategy_type: "factor_combination"
```

#### `rebalancing_frequency`
- **Type**: Enum
- **Values**: `"M"` (Monthly), `"W-FRI"`, `"W-MON"`, `"W-TUE"`, `"W-WED"`, `"W-THU"`, `"Q"` (Quarterly)
- **Description**: Portfolio rebalancing schedule

**Recommendations**:
```yaml
rebalancing_frequency: "M"        # Monthly - factor strategies, fundamental
rebalancing_frequency: "W-FRI"    # Weekly Friday - momentum, technical
rebalancing_frequency: "W-MON"    # Weekly Monday - alternative to Friday
rebalancing_frequency: "Q"        # Quarterly - long-term value investing
```

### Optional Fields

#### `description`
- **Type**: String
- **Length**: 10-500 characters
- **Description**: Human-readable strategy explanation

```yaml
description: "Selects top 20% stocks by ROE, filters by positive momentum, uses trailing stops for profit protection"
```

#### `version`
- **Type**: String
- **Pattern**: Semantic versioning (e.g., "1.0.0")
- **Default**: "1.0.0"

```yaml
version: "1.0.0"   # Initial version
version: "1.2.3"   # Major.Minor.Patch
```

#### `author`
- **Type**: String
- **Default**: "FinLab LLM System"

```yaml
author: "FinLab LLM System"
author: "Custom Strategy Team"
```

#### `tags`
- **Type**: Array of strings
- **Max Items**: 10
- **Pattern**: Lowercase, numbers, underscores, hyphens
- **Description**: Categorization tags

```yaml
tags:
  - momentum
  - volume
  - rsi
  - trailing_stop
  - high_quality
```

#### `risk_level`
- **Type**: Enum
- **Values**: `"low"`, `"medium"`, `"high"`, `"very_high"`
- **Default**: "medium"

```yaml
risk_level: "low"        # Conservative, defensive
risk_level: "medium"     # Balanced
risk_level: "high"       # Aggressive, high turnover
risk_level: "very_high"  # Speculative, leverage
```

---

## Indicators Section

At least ONE of the following must be present: `technical_indicators`, `fundamental_factors`, `custom_calculations`, or `volume_filters`.

### Technical Indicators

#### Schema
```yaml
technical_indicators:
  - name: string              # REQUIRED - lowercase_with_underscores
    type: enum                # REQUIRED - indicator type
    period: integer           # OPTIONAL - 1 to 250
    source: string            # OPTIONAL - data.get('FIELD_NAME')
    parameters:               # OPTIONAL - type-specific params
      fast_period: integer
      slow_period: integer
      signal_period: integer
      std_dev: number
```

#### Supported Indicator Types

**1. RSI (Relative Strength Index)**
- **Type**: `"RSI"`
- **Parameters**: `period` (default: 14)
- **Range**: 0-100
- **Usage**: Overbought (>70), oversold (<30)

```yaml
technical_indicators:
  - name: "rsi_14"
    type: "RSI"
    period: 14
    source: "data.get('RSI_14')"

# Usage in conditions
entry_conditions:
  threshold_rules:
    - condition: "rsi_14 < 30"     # Oversold entry
    - condition: "rsi_14 > 70"     # Overbought exit
```

**2. MACD (Moving Average Convergence Divergence)**
- **Type**: `"MACD"`
- **Parameters**: `fast_period` (12), `slow_period` (26), `signal_period` (9)
- **Outputs**: MACD line, signal line, histogram

```yaml
technical_indicators:
  - name: "macd"
    type: "MACD"
    source: "data.get('MACD')"
    parameters:
      fast_period: 12
      slow_period: 26
      signal_period: 9

# Usage
entry_conditions:
  threshold_rules:
    - condition: "macd > 0"        # Bullish MACD
```

**3. BB (Bollinger Bands)**
- **Type**: `"BB"`
- **Parameters**: `period` (20), `std_dev` (2.0)
- **Outputs**: Upper band, middle band, lower band

```yaml
technical_indicators:
  - name: "bb_upper"
    type: "BB"
    period: 20
    source: "data.get('BB_upper')"
    parameters:
      std_dev: 2.0

  - name: "bb_lower"
    type: "BB"
    period: 20
    source: "data.get('BB_lower')"
    parameters:
      std_dev: 2.0

# Mean reversion usage
entry_conditions:
  threshold_rules:
    - condition: "close < bb_lower"   # Oversold
exit_conditions:
  conditional_exits:
    - condition: "close > bb_upper"   # Overbought
```

**4. SMA (Simple Moving Average)**
- **Type**: `"SMA"`
- **Parameters**: `period` (common: 20, 50, 200)

```yaml
technical_indicators:
  - name: "ma_50"
    type: "SMA"
    period: 50
    source: "data.get('MA_50')"

  - name: "ma_200"
    type: "SMA"
    period: 200
    source: "data.get('MA_200')"

# Trend filter
entry_conditions:
  threshold_rules:
    - condition: "close > ma_50"      # Uptrend
    - condition: "ma_50 > ma_200"     # Golden cross
```

**5. EMA (Exponential Moving Average)**
- **Type**: `"EMA"`
- **Parameters**: `period` (common: 12, 26)
- **Note**: More responsive than SMA

```yaml
technical_indicators:
  - name: "ema_12"
    type: "EMA"
    period: 12
    source: "data.get('EMA_12')"
```

**6. ATR (Average True Range)**
- **Type**: `"ATR"`
- **Parameters**: `period` (14)
- **Usage**: Volatility measurement, position sizing

```yaml
technical_indicators:
  - name: "atr_14"
    type: "ATR"
    period: 14
    source: "data.get('ATR_14')"

# Volatility-based stop loss
exit_conditions:
  conditional_exits:
    - condition: "close < (entry_price - 2 * atr_14)"
```

**7. ADX (Average Directional Index)**
- **Type**: `"ADX"`
- **Parameters**: `period` (14)
- **Range**: 0-100 (>25 = trending)

```yaml
technical_indicators:
  - name: "adx_14"
    type: "ADX"
    period: 14
    source: "data.get('ADX_14')"

# Trend strength filter
entry_conditions:
  threshold_rules:
    - condition: "adx_14 > 25"   # Strong trend
```

**8. Other Supported Types**:
- **Stochastic**: Momentum oscillator
- **CCI** (Commodity Channel Index): Cycle identification
- **Williams_R**: Momentum indicator
- **MFI** (Money Flow Index): Volume-weighted RSI
- **OBV** (On-Balance Volume): Volume accumulation
- **VWAP** (Volume-Weighted Average Price): Intraday benchmark
- **Momentum**: Rate of change
- **ROC** (Rate of Change): Momentum variant
- **TSI** (True Strength Index): Momentum oscillator

### Fundamental Factors

#### Schema
```yaml
fundamental_factors:
  - name: string              # REQUIRED - lowercase_with_underscores
    field: enum               # REQUIRED - fundamental field type
    source: string            # OPTIONAL - data.get('FIELD_NAME')
    transformation: enum      # OPTIONAL - data transformation
```

#### Supported Fields

**Quality Factors**:
```yaml
fundamental_factors:
  # Return on Equity
  - name: "roe"
    field: "ROE"
    source: "data.get('ROE')"
    transformation: "winsorize"  # Handle outliers

  # Return on Assets
  - name: "roa"
    field: "ROA"
    source: "data.get('ROA')"
    transformation: "winsorize"

  # Operating Margin
  - name: "operating_margin"
    field: "operating_margin"
    source: "data.get('operating_margin')"

  # Net Margin
  - name: "net_margin"
    field: "net_margin"
    source: "data.get('net_margin')"
```

**Value Factors**:
```yaml
fundamental_factors:
  # Price-to-Book
  - name: "pb_ratio"
    field: "PB_ratio"
    source: "data.get('PB_ratio')"
    transformation: "rank"  # Percentile ranking

  # Price-to-Earnings
  - name: "pe_ratio"
    field: "PE_ratio"
    source: "data.get('PE_ratio')"
    transformation: "winsorize"

  # Price-to-Sales
  - name: "ps_ratio"
    field: "PS_ratio"
    source: "data.get('PS_ratio')"
```

**Growth Factors**:
```yaml
fundamental_factors:
  # Revenue Growth
  - name: "revenue_growth"
    field: "revenue_growth"
    source: "data.get('revenue_growth')"
    transformation: "winsorize"

  # Earnings Growth
  - name: "earnings_growth"
    field: "earnings_growth"
    source: "data.get('earnings_growth')"
    transformation: "winsorize"
```

**Financial Health**:
```yaml
fundamental_factors:
  # Debt Ratio
  - name: "debt_ratio"
    field: "debt_ratio"
    source: "data.get('debt_ratio')"

  # Debt-to-Equity
  - name: "debt_to_equity"
    field: "debt_to_equity"
    source: "data.get('debt_to_equity')"

  # Current Ratio
  - name: "current_ratio"
    field: "current_ratio"
    source: "data.get('current_ratio')"

  # Quick Ratio
  - name: "quick_ratio"
    field: "quick_ratio"
    source: "data.get('quick_ratio')"
```

**Dividend Factors**:
```yaml
fundamental_factors:
  # Dividend Yield
  - name: "dividend_yield"
    field: "dividend_yield"
    source: "data.get('dividend_yield')"

  # Payout Ratio
  - name: "payout_ratio"
    field: "payout_ratio"
    source: "data.get('payout_ratio')"
```

**Efficiency Factors**:
```yaml
fundamental_factors:
  # Asset Turnover
  - name: "asset_turnover"
    field: "asset_turnover"
    source: "data.get('asset_turnover')"

  # Inventory Turnover
  - name: "inventory_turnover"
    field: "inventory_turnover"
    source: "data.get('inventory_turnover')"

  # Receivables Turnover
  - name: "receivables_turnover"
    field: "receivables_turnover"
    source: "data.get('receivables_turnover')"
```

#### Transformation Options

**`"none"`** (Default):
- No transformation, use raw values
```yaml
transformation: "none"
```

**`"log"`**:
- Natural logarithm (useful for skewed distributions)
```yaml
transformation: "log"
# roe_log = ln(roe)
```

**`"sqrt"`**:
- Square root transformation
```yaml
transformation: "sqrt"
# roe_sqrt = sqrt(roe)
```

**`"rank"`**:
- Percentile ranking (0-100)
```yaml
transformation: "rank"
# roe_rank = percentile rank of roe
```

**`"zscore"`**:
- Z-score normalization (mean=0, std=1)
```yaml
transformation: "zscore"
# roe_zscore = (roe - mean) / std
```

**`"winsorize"`**:
- Clip extreme values (1st-99th percentile)
```yaml
transformation: "winsorize"
# roe_winsorized = clip(roe, p01, p99)
```

### Custom Calculations

#### Schema
```yaml
custom_calculations:
  - name: string              # REQUIRED - lowercase_with_underscores
    expression: string        # REQUIRED - Python expression
    description: string       # OPTIONAL - explanation
```

#### Expression Syntax

Custom calculations use Python pandas expressions:

**Arithmetic Operations**:
```yaml
custom_calculations:
  # Addition
  - name: "total_margin"
    expression: "operating_margin + net_margin"

  # Subtraction
  - name: "margin_delta"
    expression: "net_margin - operating_margin"

  # Multiplication
  - name: "quality_score"
    expression: "roe * (1 + revenue_growth)"

  # Division
  - name: "roe_pb_ratio"
    expression: "roe / pb_ratio"

  # Exponentiation
  - name: "growth_squared"
    expression: "revenue_growth ** 2"
```

**Time Series Operations**:
```yaml
custom_calculations:
  # Lagged values
  - name: "prev_close"
    expression: "close.shift(1)"

  # Momentum (percentage change)
  - name: "momentum_20"
    expression: "(close - close.shift(20)) / close.shift(20)"

  # Rolling statistics
  - name: "volatility_20"
    expression: "close.pct_change().rolling(20).std()"

  - name: "ma_20"
    expression: "close.rolling(20).mean()"

  # Cumulative operations
  - name: "cumulative_return"
    expression: "(close / close.iloc[0]) - 1"
```

**Logical Operations**:
```yaml
custom_calculations:
  # Boolean indicators
  - name: "is_uptrend"
    expression: "(close > ma_50).astype(int)"

  # Conditional expressions
  - name: "risk_adjusted_roe"
    expression: "roe if debt_ratio < 0.5 else roe * 0.5"
```

**Complex Composites**:
```yaml
custom_calculations:
  # Quality × Momentum
  - name: "quality_momentum"
    expression: "roe * momentum_20"
    description: "Combined quality and momentum score"

  # Z-score normalization
  - name: "roe_zscore"
    expression: "(roe - roe.mean()) / roe.std()"
    description: "Standardized ROE"

  # Relative strength
  - name: "relative_volume"
    expression: "volume / volume.rolling(20).mean()"
    description: "Volume relative to 20-day average"

  # Composite factor
  - name: "value_quality"
    expression: "(1 / pb_ratio) * roe"
    description: "Value (inverse P/B) × Quality (ROE)"
```

### Volume Filters

#### Schema
```yaml
volume_filters:
  - name: string              # REQUIRED
    metric: enum              # REQUIRED
    period: integer           # OPTIONAL - 1 to 250
    threshold: number         # OPTIONAL
```

#### Metrics

**`"average_volume"`**:
```yaml
volume_filters:
  - name: "avg_volume_20"
    metric: "average_volume"
    period: 20
    threshold: 100000000  # 100M shares

# Usage
entry_conditions:
  threshold_rules:
    - condition: "avg_volume_20 > 100000000"
```

**`"dollar_volume"`**:
```yaml
volume_filters:
  - name: "dollar_vol"
    metric: "dollar_volume"
    period: 20
    threshold: 5000000000  # $5B

# Liquidity filter
min_liquidity:
  dollar_volume: 5000000000
```

**`"turnover_ratio"`**:
```yaml
volume_filters:
  - name: "turnover"
    metric: "turnover_ratio"
    period: 20
```

**`"bid_ask_spread"`**:
```yaml
volume_filters:
  - name: "spread"
    metric: "bid_ask_spread"
    threshold: 0.01  # 1% max spread
```

---

## Entry Conditions Section

At least ONE of `threshold_rules` or `ranking_rules` must be present.

### Threshold Rules

#### Schema
```yaml
entry_conditions:
  threshold_rules:
    - condition: string     # REQUIRED - boolean expression
      description: string   # OPTIONAL - explanation
```

#### Condition Syntax

**Simple Comparisons**:
```yaml
threshold_rules:
  # Greater than
  - condition: "rsi_14 > 30"
    description: "RSI not oversold"

  # Less than
  - condition: "pb_ratio < 2.0"
    description: "Value filter (P/B < 2)"

  # Greater than or equal
  - condition: "roe >= 15"
    description: "Minimum ROE 15%"

  # Less than or equal
  - condition: "debt_ratio <= 0.5"
    description: "Conservative leverage"

  # Equality
  - condition: "sector == 'Technology'"
    description: "Tech sector only"

  # Inequality
  - condition: "market_cap != 0"
    description: "Valid market cap"
```

**Range Conditions**:
```yaml
threshold_rules:
  # Between range
  - condition: "rsi_14 > 30 and rsi_14 < 70"
    description: "RSI in neutral zone"

  # Outside range
  - condition: "rsi_14 < 30 or rsi_14 > 70"
    description: "RSI extreme readings"
```

**Multi-Indicator Conditions**:
```yaml
threshold_rules:
  # AND combination (all must be true)
  - condition: "close > ma_50 and volume > avg_volume * 1.5"
    description: "Uptrend with high volume"

  # OR combination (any can be true)
  - condition: "rsi_14 < 30 or close < bb_lower"
    description: "Oversold by RSI or Bollinger"

  # Complex logic
  - condition: "(roe > 15 and pb_ratio < 2) or (revenue_growth > 0.20)"
    description: "Quality+Value OR High Growth"
```

### Ranking Rules

#### Schema
```yaml
entry_conditions:
  ranking_rules:
    - field: string           # REQUIRED - indicator name
      method: enum            # REQUIRED - ranking method
      value: number           # OPTIONAL - threshold
      ascending: boolean      # OPTIONAL - sort direction (default: false)
      percentile_min: number  # OPTIONAL - for percentile_range
      percentile_max: number  # OPTIONAL - for percentile_range
```

#### Methods

**`"top_percent"`**:
- Select top X% of stocks
```yaml
ranking_rules:
  - field: "momentum_20"
    method: "top_percent"
    value: 20              # Top 20%
    ascending: false       # Highest values first

# Selects stocks in 80th-100th percentile by momentum
```

**`"bottom_percent"`**:
- Select bottom X% of stocks
```yaml
ranking_rules:
  - field: "pb_ratio"
    method: "bottom_percent"
    value: 30              # Bottom 30% (cheapest)
    ascending: true        # Lowest values first

# Value strategy: cheapest 30% by P/B
```

**`"top_n"`**:
- Select top N stocks
```yaml
ranking_rules:
  - field: "quality_score"
    method: "top_n"
    value: 50              # Top 50 stocks
    ascending: false       # Highest quality first

# Portfolio of exactly 50 highest quality stocks
```

**`"bottom_n"`**:
- Select bottom N stocks
```yaml
ranking_rules:
  - field: "volatility"
    method: "bottom_n"
    value: 30              # 30 lowest volatility
    ascending: true

# Low-volatility anomaly: 30 least volatile stocks
```

**`"percentile_range"`**:
- Select stocks in percentile range
```yaml
ranking_rules:
  - field: "momentum_20"
    method: "percentile_range"
    percentile_min: 60     # 60th percentile
    percentile_max: 80     # 80th percentile
    ascending: false

# Select stocks in 60th-80th percentile (moderate momentum)
```

### Logical Operator

**`"AND"`** (Default):
- All rules must be satisfied
```yaml
logical_operator: "AND"

threshold_rules:
  - condition: "rsi_14 < 70"      # Must be true
  - condition: "close > ma_50"    # AND must be true
  - condition: "volume > 1000000" # AND must be true
```

**`"OR"`**:
- Any rule can be satisfied
```yaml
logical_operator: "OR"

threshold_rules:
  - condition: "rsi_14 < 30"      # Can be true
  - condition: "close < bb_lower" # OR can be true
```

### Minimum Liquidity

```yaml
min_liquidity:
  average_volume_20d: number    # OPTIONAL - min 20-day avg volume
  dollar_volume: number         # OPTIONAL - min dollar volume
```

**Examples**:
```yaml
# Conservative liquidity
min_liquidity:
  average_volume_20d: 150000000  # 150M shares/day

# Aggressive liquidity
min_liquidity:
  average_volume_20d: 50000000   # 50M shares/day
  dollar_volume: 2000000000      # $2B/day
```

---

## Exit Conditions Section

All fields are optional. If omitted, positions held until rebalancing.

### Stop Loss

**`stop_loss_pct`**:
- Maximum loss before exit
- **Range**: 0.01 to 0.50 (1% to 50%)

```yaml
exit_conditions:
  stop_loss_pct: 0.08    # Exit at -8% loss

  stop_loss_pct: 0.05    # Tight stop: -5%
  stop_loss_pct: 0.15    # Wide stop: -15%
```

### Take Profit

**`take_profit_pct`**:
- Target profit for exit
- **Range**: 0.05 to 2.0 (5% to 200%)

```yaml
exit_conditions:
  take_profit_pct: 0.25   # Exit at +25% profit

  take_profit_pct: 0.10   # Conservative: +10%
  take_profit_pct: 0.50   # Aggressive: +50%
```

### Trailing Stop

**Schema**:
```yaml
trailing_stop:
  trail_percent: number         # REQUIRED - 0.01 to 0.30
  activation_profit: number     # OPTIONAL - 0 to 0.50
```

**Examples**:
```yaml
# Aggressive trailing stop
trailing_stop:
  trail_percent: 0.05      # Trail 5% below peak
  activation_profit: 0.03  # Activate after 3% gain

# Conservative trailing stop
trailing_stop:
  trail_percent: 0.10      # Trail 10% below peak
  activation_profit: 0.10  # Activate after 10% gain

# Immediate trailing stop
trailing_stop:
  trail_percent: 0.08
  activation_profit: 0     # Activate immediately
```

### Holding Period

**`holding_period_days`**:
- Maximum days to hold position
- **Range**: 1 to 365

```yaml
exit_conditions:
  holding_period_days: 30    # Exit after 30 days max

  holding_period_days: 7     # Week-long momentum
  holding_period_days: 90    # Quarter-long position
  holding_period_days: 365   # Annual holding
```

### Conditional Exits

**Schema**:
```yaml
conditional_exits:
  - condition: string     # REQUIRED - boolean expression
    description: string   # OPTIONAL
```

**Examples**:
```yaml
conditional_exits:
  # Indicator-based exits
  - condition: "rsi_14 > 80"
    description: "Exit on extreme overbought"

  - condition: "close < ma_20"
    description: "Exit on short-term trend reversal"

  - condition: "macd < 0"
    description: "Exit on bearish MACD"

  # Multi-condition exits
  - condition: "rsi_14 > 70 and volume < avg_volume * 0.8"
    description: "Overbought with low volume (weak rally)"

  # Fundamental deterioration
  - condition: "roe < 10"
    description: "Exit if quality deteriorates"
```

### Exit Operator

**`"OR"`** (Default):
- Exit if ANY condition is met
```yaml
exit_operator: "OR"

exit_conditions:
  stop_loss_pct: 0.08           # Exit at -8%
  take_profit_pct: 0.25         # OR +25%
  holding_period_days: 30       # OR 30 days
  conditional_exits:
    - condition: "rsi_14 > 80"  # OR overbought
```

**`"AND"`**:
- Exit only if ALL conditions are met
```yaml
exit_operator: "AND"

exit_conditions:
  conditional_exits:
    - condition: "rsi_14 > 70"    # Must be overbought
    - condition: "volume < avg_volume * 0.5"  # AND low volume
```

---

## Position Sizing Section

### Method Selection

**`"equal_weight"`** (Default):
```yaml
position_sizing:
  method: "equal_weight"
  max_positions: 20
  max_position_pct: 0.10  # Cap at 10%
```

**`"factor_weighted"`**:
```yaml
position_sizing:
  method: "factor_weighted"
  weighting_field: "quality_score"  # Must be defined in indicators
  max_positions: 30
  max_position_pct: 0.15
  min_position_pct: 0.01
```

**`"risk_parity"`**:
```yaml
position_sizing:
  method: "risk_parity"
  max_positions: 25
  max_position_pct: 0.12
```

**`"volatility_weighted"`**:
```yaml
position_sizing:
  method: "volatility_weighted"
  max_positions: 20
  max_position_pct: 0.10
```

**`"custom_formula"`**:
```yaml
position_sizing:
  method: "custom_formula"
  custom_formula: "quality_score / volatility"
  max_positions: 30
  max_position_pct: 0.10
```

### Position Constraints

**`max_positions`**:
- Maximum number of positions
- **Range**: 1 to 100

```yaml
max_positions: 20   # Concentrated portfolio
max_positions: 50   # Diversified portfolio
max_positions: 100  # Highly diversified
```

**`max_position_pct`**:
- Maximum percentage per position
- **Range**: 0.01 to 1.0

```yaml
max_position_pct: 0.05   # 5% max (20+ positions)
max_position_pct: 0.10   # 10% max (10+ positions)
max_position_pct: 0.20   # 20% max (5+ positions)
```

**`min_position_pct`**:
- Minimum percentage per position
- **Range**: 0.001 to 0.50

```yaml
min_position_pct: 0.01   # 1% minimum
min_position_pct: 0.02   # 2% minimum
```

---

## Risk Management Section

All fields are optional.

### Portfolio Constraints

**`max_sector_exposure`**:
- Maximum allocation to any sector
- **Range**: 0.05 to 1.0

```yaml
risk_management:
  max_sector_exposure: 0.30   # 30% max per sector
  max_sector_exposure: 0.25   # Conservative: 25%
  max_sector_exposure: 0.50   # Aggressive: 50%
```

**`max_correlation`**:
- Maximum average correlation between positions
- **Range**: -1.0 to 1.0

```yaml
risk_management:
  max_correlation: 0.70   # Limit to 70% correlation
```

**`rebalance_threshold`**:
- Minimum deviation to trigger rebalancing
- **Range**: 0.01 to 0.50

```yaml
risk_management:
  rebalance_threshold: 0.15   # Rebalance if >15% drift
  rebalance_threshold: 0.05   # Frequent rebalancing
  rebalance_threshold: 0.25   # Infrequent rebalancing
```

**`max_drawdown_limit`**:
- Maximum drawdown before reducing positions
- **Range**: 0.05 to 0.50

```yaml
risk_management:
  max_drawdown_limit: 0.20   # Reduce at -20% DD
  max_drawdown_limit: 0.15   # Conservative: -15%
  max_drawdown_limit: 0.30   # Aggressive: -30%
```

**`cash_reserve_pct`**:
- Minimum cash reserve
- **Range**: 0 to 0.50

```yaml
risk_management:
  cash_reserve_pct: 0.05   # Keep 5% cash
  cash_reserve_pct: 0.10   # Conservative: 10% cash
  cash_reserve_pct: 0        # Fully invested
```

---

## Complete Strategy Examples

### Example 1: Momentum Strategy

```yaml
metadata:
  name: "Classic Momentum with Volume"
  description: "20-day momentum with volume confirmation, RSI filter, trailing stops"
  strategy_type: "momentum"
  rebalancing_frequency: "W-FRI"
  version: "1.0.0"
  risk_level: "medium"
  tags: [momentum, volume, rsi, trailing_stop]

indicators:
  technical_indicators:
    - name: "rsi_14"
      type: "RSI"
      period: 14
      source: "data.get('RSI_14')"

    - name: "ma_50"
      type: "SMA"
      period: 50
      source: "data.get('MA_50')"

  custom_calculations:
    - name: "momentum_20"
      expression: "(close - close.shift(20)) / close.shift(20)"
      description: "20-day price momentum"

    - name: "volume_ratio"
      expression: "volume / volume.rolling(20).mean()"
      description: "Volume relative to average"

entry_conditions:
  threshold_rules:
    - condition: "momentum_20 > 0.10"
      description: "Strong momentum (>10%)"

    - condition: "rsi_14 < 70"
      description: "Not overbought"

    - condition: "close > ma_50"
      description: "Uptrend confirmation"

    - condition: "volume_ratio > 1.2"
      description: "Above-average volume"

  logical_operator: "AND"

  min_liquidity:
    average_volume_20d: 100000000

exit_conditions:
  stop_loss_pct: 0.08
  take_profit_pct: 0.25

  trailing_stop:
    trail_percent: 0.08
    activation_profit: 0.05

  conditional_exits:
    - condition: "rsi_14 > 80"
      description: "Extreme overbought"

  holding_period_days: 30
  exit_operator: "OR"

position_sizing:
  method: "equal_weight"
  max_positions: 20
  max_position_pct: 0.10

risk_management:
  max_sector_exposure: 0.30
  rebalance_threshold: 0.15
```

### Example 2: Mean Reversion Strategy

```yaml
metadata:
  name: "RSI Bollinger Mean Reversion"
  description: "Buy oversold stocks (RSI<30, below BB lower), exit at mean"
  strategy_type: "mean_reversion"
  rebalancing_frequency: "M"
  version: "1.0.0"
  risk_level: "medium"

indicators:
  technical_indicators:
    - name: "rsi_14"
      type: "RSI"
      period: 14
      source: "data.get('RSI_14')"

    - name: "bb_upper"
      type: "BB"
      period: 20
      source: "data.get('BB_upper')"
      parameters:
        std_dev: 2.0

    - name: "bb_middle"
      type: "BB"
      period: 20
      source: "data.get('BB_middle')"

    - name: "bb_lower"
      type: "BB"
      period: 20
      source: "data.get('BB_lower')"
      parameters:
        std_dev: 2.0

entry_conditions:
  threshold_rules:
    - condition: "rsi_14 < 30"
      description: "Oversold RSI"

    - condition: "close < bb_lower"
      description: "Price below lower Bollinger Band"

  logical_operator: "AND"

  min_liquidity:
    average_volume_20d: 80000000

exit_conditions:
  take_profit_pct: 0.15

  conditional_exits:
    - condition: "rsi_14 > 50"
      description: "Return to neutral RSI"

    - condition: "close > bb_middle"
      description: "Return to mean (middle BB)"

  holding_period_days: 20
  exit_operator: "OR"

position_sizing:
  method: "equal_weight"
  max_positions: 30
  max_position_pct: 0.08

risk_management:
  max_sector_exposure: 0.25
  rebalance_threshold: 0.10
```

### Example 3: Factor Combination Strategy

```yaml
metadata:
  name: "Quality Value Growth Combo"
  description: "Top 20% by quality×growth score, value filter, momentum confirmation"
  strategy_type: "factor_combination"
  rebalancing_frequency: "M"
  version: "1.0.0"
  risk_level: "medium"

indicators:
  fundamental_factors:
    - name: "roe"
      field: "ROE"
      source: "data.get('ROE')"
      transformation: "winsorize"

    - name: "revenue_growth"
      field: "revenue_growth"
      source: "data.get('revenue_growth')"
      transformation: "winsorize"

    - name: "pb_ratio"
      field: "PB_ratio"
      source: "data.get('PB_ratio')"
      transformation: "winsorize"

  technical_indicators:
    - name: "rsi_14"
      type: "RSI"
      period: 14
      source: "data.get('RSI_14')"

  custom_calculations:
    - name: "quality_growth"
      expression: "roe * (1 + revenue_growth)"
      description: "Quality × Growth composite"

entry_conditions:
  ranking_rules:
    - field: "quality_growth"
      method: "top_percent"
      value: 20
      ascending: false

  threshold_rules:
    - condition: "roe > 10"
      description: "Minimum quality threshold"

    - condition: "pb_ratio < 3"
      description: "Value filter"

    - condition: "rsi_14 > 30"
      description: "Not oversold"

  logical_operator: "AND"

  min_liquidity:
    average_volume_20d: 120000000

exit_conditions:
  stop_loss_pct: 0.10
  take_profit_pct: 0.30
  holding_period_days: 60
  exit_operator: "OR"

position_sizing:
  method: "factor_weighted"
  weighting_field: "quality_growth"
  max_positions: 30
  max_position_pct: 0.12
  min_position_pct: 0.02

risk_management:
  max_sector_exposure: 0.30
  rebalance_threshold: 0.15
  max_drawdown_limit: 0.20
```

---

## Advanced Topics

### Complex Entry Conditions

**Multi-Stage Filtering**:
```yaml
entry_conditions:
  # Stage 1: Ranking (universe reduction)
  ranking_rules:
    - field: "quality_score"
      method: "top_percent"
      value: 50  # Top 50% by quality

  # Stage 2: Threshold filters (additional screens)
  threshold_rules:
    - condition: "momentum_20 > 0"      # Positive momentum
    - condition: "pb_ratio < 2"         # Value screen
    - condition: "debt_ratio < 0.6"     # Financial health

  logical_operator: "AND"
```

**Dynamic Thresholds**:
```yaml
custom_calculations:
  # Market-relative threshold
  - name: "rsi_market_adj"
    expression: "rsi_14 - market_rsi_14"
    description: "RSI relative to market"

entry_conditions:
  threshold_rules:
    - condition: "rsi_market_adj < -10"  # Stock RSI below market
```

### Multi-Factor Combinations

**Quality + Value + Momentum**:
```yaml
indicators:
  fundamental_factors:
    - name: "roe"
      field: "ROE"
      transformation: "rank"

    - name: "pb_ratio"
      field: "PB_ratio"
      transformation: "rank"

  technical_indicators:
    - name: "rsi_14"
      type: "RSI"
      period: 14

  custom_calculations:
    # Composite score
    - name: "composite_score"
      expression: "roe_rank * (100 - pb_ratio_rank) * (rsi_14 / 50)"
      description: "Quality × Value × Momentum composite"

entry_conditions:
  ranking_rules:
    - field: "composite_score"
      method: "top_n"
      value: 30
```

### Custom Position Sizing Formulas

**Risk-Adjusted Weighting**:
```yaml
indicators:
  custom_calculations:
    - name: "volatility"
      expression: "close.pct_change().rolling(20).std()"

    - name: "sharpe_estimate"
      expression: "momentum_20 / volatility"

position_sizing:
  method: "custom_formula"
  custom_formula: "sharpe_estimate / sharpe_estimate.sum()"
  max_positions: 25
```

**Quality-Weighted with Volatility Adjustment**:
```yaml
position_sizing:
  method: "custom_formula"
  custom_formula: "(quality_score / volatility) / (quality_score / volatility).sum()"
  max_position_pct: 0.15
  min_position_pct: 0.02
```

### Risk Management Strategies

**Adaptive Risk Management**:
```yaml
risk_management:
  # Sector limits
  max_sector_exposure: 0.30

  # Correlation limits
  max_correlation: 0.70

  # Dynamic rebalancing
  rebalance_threshold: 0.15

  # Drawdown protection
  max_drawdown_limit: 0.20

  # Cash buffer
  cash_reserve_pct: 0.05
```

**Market Regime Adaptation** (via conditional logic):
```yaml
indicators:
  custom_calculations:
    - name: "market_volatility"
      expression: "market_index.pct_change().rolling(20).std()"

exit_conditions:
  conditional_exits:
    # Exit when market volatility spikes
    - condition: "market_volatility > 0.02"
      description: "High market volatility regime"
```

---

**For API documentation, see**: [STRUCTURED_INNOVATION_API.md](STRUCTURED_INNOVATION_API.md)

**For user guide, see**: [STRUCTURED_INNOVATION.md](STRUCTURED_INNOVATION.md)

**Happy YAML Strategy Building! 📊**
