# Strategy Configuration YAML Format

**Version:** 1.0
**Last Updated:** 2025-11-18
**Task Reference:** 18.3 - Strategy Configuration Documentation

## Table of Contents

1. [Overview](#overview)
2. [Schema Specification](#schema-specification)
3. [Field Usage](#field-usage)
4. [Parameter Types](#parameter-types)
5. [Logic Configuration](#logic-configuration)
6. [Constraint Types](#constraint-types)
7. [Pattern Examples](#pattern-examples)
8. [Validation and Error Handling](#validation-and-error-handling)
9. [Best Practices](#best-practices)

---

## Overview

### Purpose

This document defines the YAML configuration format for trading strategy specifications in the LLM Strategy Generator system. The YAML format provides:

- **Structured Strategy Definition**: Clear separation of fields, parameters, logic, and constraints
- **Three-Layered Defense Integration**:
  - **Layer 1**: Field validation via DataFieldManifest (canonical names and aliases)
  - **Layer 2**: AST-based code validation via FieldValidator
  - **Layer 3**: Schema validation via SchemaValidator
- **Pattern-Based Templates**: Support for 5 proven strategy patterns covering 84% of successful strategies
- **Automatic Error Correction**: Auto-suggestion for common field naming mistakes (29.4% error rate)

### Architecture Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    YAML Strategy Config                      │
│  (Pure data specification - no executable code)              │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              Three-Layered Defense System                    │
│                                                               │
│  Layer 1: DataFieldManifest (Field Validation)               │
│  - O(1) alias resolution (e.g., 'close' → 'price:收盤價')   │
│  - Auto-correction for common mistakes                       │
│  - Canonical name enforcement                                │
│                                                               │
│  Layer 2: FieldValidator (Code Validation)                   │
│  - AST-based code parsing and field extraction               │
│  - Invalid field detection in logic expressions              │
│                                                               │
│  Layer 3: SchemaValidator (Structure Validation)             │
│  - Required keys validation                                  │
│  - Data type validation                                      │
│  - Parameter range checking                                  │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                    StrategyConfig Dataclass                  │
│  - Type-safe parameter representation                        │
│  - Field mapping with usage documentation                    │
│  - Constraint enforcement                                    │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

- **Type Safety**: All parameters validated against declared types (integer, float, boolean, string)
- **Range Enforcement**: Numeric parameters validated against min/max ranges
- **Dependency Tracking**: Automatic validation that all required fields are available
- **Error Messages**: Structured error reporting with line numbers and suggestions
- **Pattern Coverage**: 5 pre-defined patterns representing 84% of successful strategies

---

## Schema Specification

### Top-Level Structure

Every strategy configuration YAML file must contain the following top-level keys:

```yaml
name: "Strategy Name"                    # Required: Human-readable strategy name
type: "pattern_type"                     # Required: Pattern type (see Pattern Types)
description: "Strategy description"      # Optional: Human-readable description
coverage: 0.18                          # Optional: Pattern coverage percentage (0.0-1.0)

required_fields: [...]                   # Required: List of required data fields
optional_fields: [...]                   # Optional: List of optional enhancement fields
parameters: [...]                        # Required: List of strategy parameters
logic: {...}                            # Required: Entry/exit logic specification
constraints: [...]                       # Optional: Validation constraints
```

### Pattern Types

The system supports 5 validated strategy patterns:

| Pattern Type | Coverage | Description |
|-------------|----------|-------------|
| `pure_momentum` | 18% | Fast breakout using price momentum with rolling mean returns |
| `momentum_exit` | 18% | Momentum strategy with trailing stop loss for risk management |
| `turtle_breakout` | 16% | N-day high/low breakout with ATR-based position sizing |
| `multi_factor_scoring` | 16% | Factor-based scoring combining momentum, value, quality |
| `complex_combination` | 16% | Multi-strategy combination with regime detection |

**Total Coverage**: 84% of successful strategies

---

## Field Usage

### Required Fields Section

Required fields define the minimum data needed for strategy execution. Each field must specify:

```yaml
required_fields:
  - field: "price:收盤價"                 # Canonical field name (Layer 1)
    aliases: ["close", "closing_price", "收盤價", "closing"]
    usage: "Signal generation - momentum calculation"
    category: "price"

  - field: "price:成交金額"               # CRITICAL: Trading VALUE not shares
    aliases: ["volume", "trading_value", "turnover", "成交金額"]
    usage: "Volume filtering - minimum liquidity requirement"
    category: "price"
    note: "CRITICAL: This is trading VALUE (金額), not shares (股數)"
```

#### Field Structure

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `field` | string | Yes | Canonical field name from Layer 1 DataFieldManifest |
| `aliases` | list[string] | No | Alternative names for the field (for LLM compatibility) |
| `usage` | string | No | Human-readable description of how field is used |
| `category` | string | No | Field category: "price", "fundamental", "technical" |
| `note` | string | No | Additional notes or warnings |

### Layer 1 Integration: Canonical Names

All field names must match canonical names from the DataFieldManifest:

**Price Fields:**
- `price:收盤價` (Close price) - Aliases: `close`, `closing_price`, `收盤價`
- `price:成交金額` (Trading value) - Aliases: `volume`, `trading_value`, `turnover`
- `price:最高價` (High price) - Aliases: `high`, `highest`, `最高價`
- `price:最低價` (Low price) - Aliases: `low`, `lowest`, `最低價`
- `price:開盤價` (Open price) - Aliases: `open`, `opening_price`, `開盤價`
- `price:成交股數` (Share volume) - Aliases: `volume_shares`, `share_volume`

**Fundamental Fields:**
- `fundamental_features:本益比` (PE ratio) - Aliases: `pe_ratio`, `PE`, `本益比`
- `fundamental_features:股價淨值比` (PB ratio) - Aliases: `pb_ratio`, `PB`, `股價淨值比`
- `fundamental_features:ROE` - Aliases: `roe`, `return_on_equity`, `ROE`, `股東權益報酬率`
- `fundamental_features:ROA` - Aliases: `roa`, `return_on_assets`, `ROA`, `資產報酬率`
- `fundamental_features:殖利率` (Dividend yield) - Aliases: `dividend_yield`, `殖利率`, `現金殖利率`

### Common Field Corrections

The system automatically corrects common LLM field naming mistakes (29.4% error rate):

| Incorrect Field | Correct Field | Reason |
|----------------|---------------|---------|
| `price:成交量` | `price:成交金額` | Ambiguous term - should use trading VALUE |
| `成交量` | `price:成交金額` | CRITICAL: Missing 金額 suffix |
| `trading_volume` | `price:成交金額` | English term confusion |
| `close_value` | `price:收盤價` | Redundant "value" suffix |
| `pe_ratio` | `fundamental_features:本益比` | Missing category prefix |

See `src/config/data_fields.py` for complete list of auto-corrections.

### Optional Fields Section

Optional fields provide enhancements but are not required:

```yaml
optional_fields:
  - field: "price:最高價"
    aliases: ["high", "highest", "最高價"]
    usage: "Alternative signal generation"

  - field: "fundamental_features:股價淨值比"
    aliases: ["pb_ratio", "PB", "股價淨值比"]
    usage: "Additional value factor"
```

---

## Parameter Types

### Parameter Structure

Each parameter must specify type, value, range, and metadata:

```yaml
parameters:
  - name: "momentum_period"              # Parameter name (used in logic)
    type: "integer"                      # Data type (see Valid Types)
    description: "Lookback period for momentum calculation"
    value: 20                            # Current parameter value
    default: 20                          # Default parameter value
    range: [10, 60]                      # Valid range: [min, max]
    unit: "trading_days"                 # Optional unit descriptor
```

### Valid Parameter Types

| Type | Python Type | Validation Rules | Example Values |
|------|-------------|-----------------|----------------|
| `integer` | `int` | Must be integer, must be in range | `20`, `100`, `252` |
| `float` | `float` | Must be numeric, must be in range | `0.02`, `0.5`, `1.5` |
| `boolean` | `bool` | Must be true/false | `true`, `false` |
| `string` | `str` | No range validation | `"aggressive"`, `"conservative"` |
| `list` | `list` | Must be list type | `[0.4, 0.3, 0.3]` |

### Parameter Validation Rules

1. **Type Matching**: `value` and `default` must match declared `type`
2. **Range Validation**: Numeric types (`integer`, `float`) require `range` field
3. **Range Format**: Range must be `[min, max]` where `min < max`
4. **Value in Range**: `value` must satisfy `min <= value <= max`
5. **Unit Documentation**: `unit` field is recommended for clarity

### Parameter Examples

```yaml
# Integer parameter with range
- name: "momentum_period"
  type: "integer"
  value: 20
  default: 20
  range: [10, 60]
  unit: "trading_days"

# Float parameter with range
- name: "entry_threshold"
  type: "float"
  value: 0.02
  default: 0.02
  range: [0.01, 0.10]
  unit: "percentage"

# Boolean parameter (no range)
- name: "regime_detection"
  type: "boolean"
  value: true
  default: true
  description: "Enable adaptive strategy weighting by market regime"

# String parameter (no range)
- name: "mode"
  type: "string"
  value: "aggressive"
  default: "conservative"
```

### Parameter Constraints

Weight parameters in multi-factor strategies must sum to 1.0:

```yaml
# Multi-factor weight parameters (must sum to 1.0)
- name: "momentum_weight"
  type: "float"
  value: 0.4
  default: 0.4
  range: [0.0, 1.0]
  unit: "weight"

- name: "value_weight"
  type: "float"
  value: 0.3
  default: 0.3
  range: [0.0, 1.0]
  unit: "weight"

- name: "quality_weight"
  type: "float"
  value: 0.3
  default: 0.3
  range: [0.0, 1.0]
  unit: "weight"
  note: "Weights should sum to 1.0"
```

Validation constraint ensures sum equals 1.0 within tolerance:

```yaml
constraints:
  - type: "parameter"
    condition: "momentum_weight + value_weight + quality_weight == 1.0"
    severity: "critical"
    tolerance: 0.01
```

---

## Logic Configuration

### Logic Structure

The `logic` section defines entry and exit conditions with field dependencies:

```yaml
logic:
  entry:
    description: "Enter when momentum exceeds threshold with sufficient volume"
    formula: "(price.pct_change(momentum_period).rolling(5).mean() > entry_threshold) & (volume > min_volume)"
    dependencies: ["price:收盤價", "price:成交金額"]

  exit:
    description: "Exit when price drops below trailing stop"
    formula: "price < peak_price * (1 - trailing_stop_pct)"
    dependencies: ["price:收盤價", "price:最高價"]
```

### Entry Logic

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `description` | string | Yes | Human-readable description of entry logic |
| `formula` | string | Yes | Python expression for entry condition |
| `dependencies` | list[string] | Yes | List of canonical field names used in formula |

### Exit Logic

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `description` | string | Yes | Human-readable description of exit logic |
| `formula` | string | Yes | Python expression for exit condition (use `"None"` for no exit) |
| `dependencies` | list[string] | Yes | List of canonical field names used in formula (empty list for no exit) |

### Logic Formula Syntax

Formulas use pandas/numpy-style expressions:

**Valid Operations:**
- **Comparison**: `>`, `<`, `>=`, `<=`, `==`, `!=`
- **Logical**: `&` (AND), `|` (OR), `~` (NOT)
- **Arithmetic**: `+`, `-`, `*`, `/`, `**` (power)
- **Pandas Methods**: `.pct_change()`, `.rolling()`, `.shift()`, `.rank()`, `.mean()`, `.std()`

**Example Formulas:**

```python
# Simple threshold
"close > 100"

# Momentum with rolling average
"price.pct_change(20).rolling(5).mean() > 0.02"

# Multi-condition with volume filter
"(close > high.rolling(20).max().shift(1)) & (volume > 1000000)"

# Factor scoring with ranking
"(1 / pe_ratio).rank(pct=True) > 0.8"

# Volatility calculation
"close.pct_change().rolling(20).std() * sqrt(252) < 0.30"
```

### Dependencies Validation

All fields referenced in `formula` must be listed in `dependencies`:

```yaml
# VALID - all fields in formula are in dependencies
formula: "(close > 100) & (volume > 1000000)"
dependencies: ["price:收盤價", "price:成交金額"]

# INVALID - 'volume' used in formula but missing from dependencies
formula: "(close > 100) & (volume > 1000000)"
dependencies: ["price:收盤價"]  # ERROR: Missing "price:成交金額"
```

The StrategyConfig dataclass provides validation:

```python
config = StrategyConfig(...)
assert config.validate_dependencies() == True  # All dependencies satisfied
```

### Multi-Line Formulas

For complex logic, use YAML multi-line strings:

```yaml
entry:
  description: "Weighted combination of momentum, breakout, and factor signals"
  formula: |
    # Individual sub-strategy signals
    momentum_signal = (price.pct_change(momentum_period) > 0.02)
    breakout_signal = (close > high.rolling(breakout_period).max().shift(1))
    factor_signal = (composite_score >= 0.8)

    # Volatility filter
    volatility = close.pct_change().rolling(volatility_period).std() * sqrt(252)
    vol_filter = (volatility < max_volatility)

    # Weighted combination
    combined_score = (momentum_weight * momentum_signal +
                     breakout_weight * breakout_signal +
                     factor_score_weight * factor_signal)

    entry = (combined_score > 0.5) & vol_filter
  dependencies:
    - "price:收盤價"
    - "price:最高價"
    - "fundamental_features:本益比"
```

---

## Constraint Types

### Constraint Structure

Constraints define validation rules with severity levels:

```yaml
constraints:
  - type: "data_quality"                 # Constraint category
    condition: "No NaN values in price field"
    severity: "critical"                 # Severity level
    message: "Price field contains missing values"

  - type: "parameter"
    condition: "momentum_period < total_backtest_days"
    severity: "critical"

  - type: "logic"
    condition: "trailing_stop_pct must be less than expected max drawdown"
    severity: "warning"
```

### Constraint Categories

| Type | Purpose | Example |
|------|---------|---------|
| `data_quality` | Data integrity checks | NaN detection, value ranges, consistency |
| `parameter` | Parameter validity | Range checks, relationship validation |
| `logic` | Strategy logic correctness | Dependency validation, calculation checks |
| `performance` | Performance requirements | Minimum Sharpe ratio, max drawdown limits |

### Severity Levels

| Severity | Meaning | Action |
|----------|---------|--------|
| `critical` | Must pass - strategy execution blocked | Strategy rejected immediately |
| `high` | Should pass - high risk if violated | Warning logged, execution may continue |
| `medium` | Should pass - medium risk | Warning logged |
| `low` | Nice to have - low risk | Info logged |
| `warning` | Informational - no blocking | Info logged |

### Constraint Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | Yes | One of: `data_quality`, `parameter`, `logic`, `performance` |
| `condition` | string | Yes | Constraint condition or check description |
| `severity` | string | Yes | One of: `critical`, `high`, `medium`, `low`, `warning` |
| `message` | string | No | Custom error message for constraint violations |
| `tolerance` | float | No | Tolerance for numeric comparisons (default: 0.0) |
| `max_nan_pct` | float | No | Maximum NaN percentage for data quality (0.0-1.0) |

### Constraint Examples

```yaml
constraints:
  # Data quality constraint with max NaN percentage
  - type: "data_quality"
    condition: "No excessive NaN values in required fields"
    severity: "critical"
    max_nan_pct: 0.05
    message: "More than 5% NaN values detected in required fields"

  # Parameter relationship constraint
  - type: "parameter"
    condition: "entry_threshold > 0 and trailing_stop_pct > 0"
    severity: "critical"
    message: "Threshold parameters must be positive"

  # Weight sum constraint with tolerance
  - type: "parameter"
    condition: "momentum_weight + value_weight + quality_weight == 1.0"
    severity: "critical"
    tolerance: 0.01
    message: "Factor weights must sum to 1.0 (±0.01)"

  # Logic dependency constraint
  - type: "logic"
    condition: "ATR calculation requires minimum history of atr_period + 1"
    severity: "critical"

  # Performance constraint
  - type: "performance"
    condition: "min_volume filter must exclude <5% of universe"
    severity: "warning"
```

---

## Pattern Examples

### Pattern 1: Pure Momentum

**Coverage**: 18% of successful strategies
**Performance**: Sharpe 0.301, Return 41.6%, MaxDD -32.2%

```yaml
name: "Pure Momentum Strategy"
type: "pure_momentum"
description: "Fast breakout strategy using price momentum with rolling mean returns"
coverage: 0.18

required_fields:
  - field: "price:收盤價"
    aliases: ["close", "closing_price", "收盤價"]
    usage: "Signal generation - momentum calculation"
    category: "price"

  - field: "price:成交金額"
    aliases: ["volume", "trading_value", "成交金額"]
    usage: "Volume filtering - minimum liquidity requirement"
    category: "price"

parameters:
  - name: "momentum_period"
    type: "integer"
    description: "Lookback period for momentum calculation"
    value: 20
    default: 20
    range: [10, 60]
    unit: "trading_days"

  - name: "entry_threshold"
    type: "float"
    description: "Momentum threshold for entry signal"
    value: 0.02
    default: 0.02
    range: [0.01, 0.10]
    unit: "percentage"

  - name: "min_volume"
    type: "float"
    description: "Minimum trading value for liquidity filter"
    value: 1000000.0
    default: 1000000.0
    range: [100000.0, 10000000.0]
    unit: "currency"

logic:
  entry:
    description: "Enter when momentum exceeds threshold with sufficient volume"
    formula: "(price.pct_change(momentum_period).rolling(5).mean() > entry_threshold) & (volume > min_volume)"
    dependencies: ["price:收盤價", "price:成交金額"]

  exit:
    description: "No explicit exit - position held until rebalance"
    formula: "None"
    dependencies: []

constraints:
  - type: "data_quality"
    condition: "No NaN values in price field"
    severity: "critical"

  - type: "parameter"
    condition: "momentum_period < total_backtest_days"
    severity: "critical"

  - type: "performance"
    condition: "min_volume filter must exclude <5% of universe"
    severity: "warning"
```

### Pattern 2: Momentum + Exit Strategy

**Coverage**: 18% of successful strategies
**Performance**: Sharpe 0.301, Return 41.6%, MaxDD -32.2%

```yaml
name: "Momentum with Trailing Stop"
type: "momentum_exit"
description: "Momentum strategy with trailing stop loss for downside protection"
coverage: 0.18

required_fields:
  - field: "price:收盤價"
    aliases: ["close", "closing_price"]
    usage: "Entry signal and stop loss calculation"
    category: "price"

  - field: "price:成交金額"
    aliases: ["volume", "trading_value"]
    usage: "Liquidity filtering"
    category: "price"

optional_fields:
  - field: "price:最高價"
    aliases: ["high", "highest"]
    usage: "Trailing stop calculation - track peak price"

parameters:
  - name: "momentum_period"
    type: "integer"
    description: "Momentum calculation period"
    value: 20
    default: 20
    range: [10, 60]
    unit: "trading_days"

  - name: "entry_threshold"
    type: "float"
    description: "Momentum threshold for entry"
    value: 0.02
    default: 0.02
    range: [0.01, 0.10]
    unit: "percentage"

  - name: "trailing_stop_pct"
    type: "float"
    description: "Trailing stop distance from peak price"
    value: 0.10
    default: 0.10
    range: [0.05, 0.30]
    unit: "percentage"

  - name: "min_volume"
    type: "float"
    description: "Minimum trading value"
    value: 1000000.0
    default: 1000000.0
    range: [100000.0, 10000000.0]
    unit: "currency"

logic:
  entry:
    description: "Momentum breakout with volume filter"
    formula: "(price.pct_change(momentum_period).rolling(5).mean() > entry_threshold) & (volume > min_volume)"
    dependencies: ["price:收盤價", "price:成交金額"]

  exit:
    description: "Exit when price drops below trailing stop"
    formula: "price < peak_price * (1 - trailing_stop_pct)"
    dependencies: ["price:收盤價", "price:最高價"]

constraints:
  - type: "data_quality"
    condition: "No NaN in price and volume"
    severity: "critical"

  - type: "logic"
    condition: "trailing_stop_pct must be less than expected max drawdown"
    severity: "warning"

  - type: "parameter"
    condition: "entry_threshold > 0 and trailing_stop_pct > 0"
    severity: "critical"
```

### Pattern 3: Turtle Breakout

**Coverage**: 16% of successful strategies
**Performance**: Sharpe 0.301, Return 41.6%, MaxDD -32.2%

```yaml
name: "Turtle Breakout Strategy"
type: "turtle_breakout"
description: "N-day high/low breakout with ATR-based position sizing and stop loss"
coverage: 0.16

required_fields:
  - field: "price:收盤價"
    aliases: ["close", "closing_price"]
    usage: "Breakout detection and stop loss"
    category: "price"

  - field: "price:最高價"
    aliases: ["high", "highest"]
    usage: "N-day high for entry breakout"
    category: "price"

  - field: "price:最低價"
    aliases: ["low", "lowest"]
    usage: "N-day low for exit breakout and ATR calculation"
    category: "price"

  - field: "price:成交金額"
    aliases: ["volume", "trading_value"]
    usage: "Volume confirmation"
    category: "price"

parameters:
  - name: "breakout_period"
    type: "integer"
    description: "N-day period for breakout detection"
    value: 20
    default: 20
    range: [10, 55]
    unit: "trading_days"
    note: "Classic Turtle uses 20-day for entry, 55-day for exit"

  - name: "atr_period"
    type: "integer"
    description: "Period for ATR calculation"
    value: 14
    default: 14
    range: [7, 30]
    unit: "trading_days"

  - name: "atr_stop_multiplier"
    type: "float"
    description: "ATR multiplier for stop loss distance"
    value: 2.0
    default: 2.0
    range: [1.0, 4.0]
    unit: "multiplier"

  - name: "min_volume"
    type: "float"
    description: "Minimum trading value for breakout validity"
    value: 1000000.0
    default: 1000000.0
    range: [100000.0, 10000000.0]
    unit: "currency"

logic:
  entry:
    description: "Enter when price breaks above N-day high with volume"
    formula: "(close > high.rolling(breakout_period).max().shift(1)) & (volume > min_volume)"
    dependencies: ["price:收盤價", "price:最高價", "price:成交金額"]

  exit:
    description: "Exit when price hits ATR-based stop loss"
    formula: "close < (entry_price - atr * atr_stop_multiplier)"
    dependencies: ["price:收盤價", "price:最高價", "price:最低價"]
    note: "ATR = average true range over atr_period"

constraints:
  - type: "data_quality"
    condition: "High >= Low >= Close for all periods"
    severity: "critical"

  - type: "parameter"
    condition: "breakout_period > atr_period for stability"
    severity: "warning"

  - type: "logic"
    condition: "ATR calculation requires minimum history of atr_period + 1"
    severity: "critical"
```

### Pattern 4: Multi-Factor Scoring

**Coverage**: 16% of successful strategies
**Performance**: Sharpe 0.301, Return 41.6%, MaxDD -32.2%

```yaml
name: "Multi-Factor Scoring Strategy"
type: "multi_factor_scoring"
description: "Combines multiple factors (momentum, value, quality) with weighted scoring"
coverage: 0.16

required_fields:
  - field: "price:收盤價"
    aliases: ["close", "closing_price"]
    usage: "Momentum factor calculation"
    category: "price"

  - field: "fundamental_features:本益比"
    aliases: ["pe_ratio", "PE", "本益比"]
    usage: "Value factor - inverse PE scoring"
    category: "fundamental"

  - field: "fundamental_features:ROE"
    aliases: ["roe", "return_on_equity", "ROE"]
    usage: "Quality factor - profitability screening"
    category: "fundamental"

  - field: "price:成交金額"
    aliases: ["volume", "trading_value"]
    usage: "Liquidity screening"
    category: "price"

optional_fields:
  - field: "fundamental_features:股價淨值比"
    aliases: ["pb_ratio", "PB"]
    usage: "Additional value factor"

  - field: "fundamental_features:殖利率"
    aliases: ["dividend_yield", "殖利率"]
    usage: "Income factor"

parameters:
  - name: "momentum_weight"
    type: "float"
    description: "Weight for momentum factor in composite score"
    value: 0.4
    default: 0.4
    range: [0.0, 1.0]
    unit: "weight"

  - name: "value_weight"
    type: "float"
    description: "Weight for value factor (inverse PE)"
    value: 0.3
    default: 0.3
    range: [0.0, 1.0]
    unit: "weight"

  - name: "quality_weight"
    type: "float"
    description: "Weight for quality factor (ROE)"
    value: 0.3
    default: 0.3
    range: [0.0, 1.0]
    unit: "weight"
    note: "Weights should sum to 1.0"

  - name: "momentum_period"
    type: "integer"
    description: "Lookback for momentum calculation"
    value: 20
    default: 20
    range: [10, 60]
    unit: "trading_days"

  - name: "top_n_pct"
    type: "float"
    description: "Select top N% by composite score"
    value: 0.10
    default: 0.10
    range: [0.05, 0.30]
    unit: "percentage"

  - name: "min_roe"
    type: "float"
    description: "Minimum ROE threshold for quality screen"
    value: 0.10
    default: 0.10
    range: [0.05, 0.30]
    unit: "percentage"

logic:
  entry:
    description: "Rank stocks by weighted composite score, select top N%"
    formula: |
      momentum_score = price.pct_change(momentum_period).rank(pct=True)
      value_score = (1 / pe_ratio).rank(pct=True)
      quality_score = roe.rank(pct=True)
      composite = (momentum_weight * momentum_score +
                  value_weight * value_score +
                  quality_weight * quality_score)
      entry = (composite >= (1 - top_n_pct)) & (roe > min_roe)
    dependencies: ["price:收盤價", "fundamental_features:本益比", "fundamental_features:ROE"]

  exit:
    description: "Exit positions falling out of top N% on rebalance"
    formula: "composite < (1 - top_n_pct)"
    dependencies: ["price:收盤價", "fundamental_features:本益比", "fundamental_features:ROE"]

constraints:
  - type: "parameter"
    condition: "momentum_weight + value_weight + quality_weight == 1.0"
    severity: "critical"
    tolerance: 0.01

  - type: "data_quality"
    condition: "PE ratio > 0 for value scoring"
    severity: "critical"

  - type: "data_quality"
    condition: "ROE values available and valid"
    severity: "critical"

  - type: "logic"
    condition: "Composite score calculation produces valid rankings"
    severity: "critical"
```

### Pattern 5: Complex Combination

**Coverage**: 16% of successful strategies
**Performance**: Sharpe 0.301, Return 41.6%, MaxDD -32.2%

```yaml
name: "Complex Combination Strategy"
type: "complex_combination"
description: "Combines momentum, breakout, and factor scoring with regime detection"
coverage: 0.16

required_fields:
  - field: "price:收盤價"
    aliases: ["close", "closing_price"]
    usage: "All sub-strategies - momentum, breakout, scoring"
    category: "price"

  - field: "price:最高價"
    aliases: ["high", "highest"]
    usage: "Breakout detection"
    category: "price"

  - field: "price:最低價"
    aliases: ["low", "lowest"]
    usage: "Volatility calculation and risk management"
    category: "price"

  - field: "price:成交金額"
    aliases: ["volume", "trading_value"]
    usage: "Volume filtering and regime detection"
    category: "price"

  - field: "fundamental_features:本益比"
    aliases: ["pe_ratio", "PE"]
    usage: "Value component in factor scoring"
    category: "fundamental"

  - field: "fundamental_features:ROE"
    aliases: ["roe", "return_on_equity"]
    usage: "Quality component in factor scoring"
    category: "fundamental"

optional_fields:
  - field: "fundamental_features:殖利率"
    aliases: ["dividend_yield"]
    usage: "Income factor for defensive regime"

parameters:
  # Momentum sub-strategy
  - name: "momentum_period"
    type: "integer"
    description: "Momentum lookback period"
    value: 20
    default: 20
    range: [10, 60]
    unit: "trading_days"

  - name: "momentum_weight"
    type: "float"
    description: "Weight for momentum sub-strategy"
    value: 0.4
    default: 0.4
    range: [0.0, 1.0]
    unit: "weight"

  # Breakout sub-strategy
  - name: "breakout_period"
    type: "integer"
    description: "Breakout detection period"
    value: 20
    default: 20
    range: [10, 55]
    unit: "trading_days"

  - name: "breakout_weight"
    type: "float"
    description: "Weight for breakout sub-strategy"
    value: 0.3
    default: 0.3
    range: [0.0, 1.0]
    unit: "weight"

  # Factor scoring sub-strategy
  - name: "factor_score_weight"
    type: "float"
    description: "Weight for factor scoring sub-strategy"
    value: 0.3
    default: 0.3
    range: [0.0, 1.0]
    unit: "weight"
    note: "Strategy weights should sum to 1.0"

  # Risk management
  - name: "volatility_period"
    type: "integer"
    description: "Period for volatility calculation"
    value: 20
    default: 20
    range: [10, 60]
    unit: "trading_days"

  - name: "max_volatility"
    type: "float"
    description: "Maximum allowed volatility for position entry"
    value: 0.30
    default: 0.30
    range: [0.10, 0.50]
    unit: "annualized_std"

  # Regime detection
  - name: "regime_detection"
    type: "boolean"
    description: "Enable adaptive strategy weighting by market regime"
    value: true
    default: true

  - name: "regime_period"
    type: "integer"
    description: "Period for regime classification"
    value: 60
    default: 60
    range: [30, 120]
    unit: "trading_days"

logic:
  entry:
    description: "Weighted combination of momentum, breakout, and factor signals"
    formula: |
      # Individual sub-strategy signals
      momentum_signal = (price.pct_change(momentum_period) > 0.02)
      breakout_signal = (close > high.rolling(breakout_period).max().shift(1))
      factor_signal = (composite_score >= 0.8)  # Top 20%

      # Volatility filter
      volatility = close.pct_change().rolling(volatility_period).std() * sqrt(252)
      vol_filter = (volatility < max_volatility)

      # Regime detection (optional)
      if regime_detection:
          market_regime = detect_regime(close, volume, regime_period)
          weights = adjust_weights(market_regime, [momentum_weight, breakout_weight, factor_score_weight])
      else:
          weights = [momentum_weight, breakout_weight, factor_score_weight]

      # Weighted combination
      combined_score = (weights[0] * momentum_signal +
                       weights[1] * breakout_signal +
                       weights[2] * factor_signal)

      entry = (combined_score > 0.5) & vol_filter
    dependencies:
      - "price:收盤價"
      - "price:最高價"
      - "price:最低價"
      - "price:成交金額"
      - "fundamental_features:本益比"
      - "fundamental_features:ROE"

  exit:
    description: "Exit when combined score falls below threshold or volatility spikes"
    formula: |
      volatility_spike = (volatility > max_volatility * 1.5)
      score_decline = (combined_score < 0.3)
      exit = volatility_spike | score_decline
    dependencies:
      - "price:收盤價"
      - "price:最低價"

constraints:
  - type: "parameter"
    condition: "momentum_weight + breakout_weight + factor_score_weight == 1.0"
    severity: "critical"
    tolerance: 0.01

  - type: "data_quality"
    condition: "All required fields available without excessive NaN"
    severity: "critical"
    max_nan_pct: 0.10

  - type: "logic"
    condition: "Regime detection function produces valid classifications"
    severity: "warning"

  - type: "performance"
    condition: "Individual sub-strategies show positive correlation with combined strategy"
    severity: "warning"

  - type: "parameter"
    condition: "volatility_period <= min(momentum_period, breakout_period)"
    severity: "warning"
```

---

## Validation and Error Handling

### Three-Layered Defense Validation

The system uses a three-layered validation architecture:

#### Layer 1: Field Validation (DataFieldManifest)

**Purpose**: Validate field names and provide auto-corrections

**Validation**:
- O(1) canonical name lookup
- O(1) alias resolution
- Auto-correction suggestions for common mistakes

**Example**:

```python
from src.config.data_fields import DataFieldManifest

manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')

# Valid field
is_valid, suggestion = manifest.validate_field_with_suggestion('close')
assert is_valid is True

# Common mistake with suggestion
is_valid, suggestion = manifest.validate_field_with_suggestion('price:成交量')
assert is_valid is False
assert suggestion == "Did you mean 'price:成交金額'?"
```

#### Layer 2: Code Validation (FieldValidator)

**Purpose**: AST-based validation of logic formulas

**Validation**:
- Parse Python expressions using AST
- Extract field references from code
- Validate all fields against Layer 1 manifest

**Example**:

```python
from src.validation.field_validator import FieldValidator

validator = FieldValidator(manifest)

# Valid formula
result = validator.validate("(close > 100) & (volume > 1000000)")
assert len(result.errors) == 0

# Invalid field in formula
result = validator.validate("(invalid_field > 100)")
assert len(result.errors) > 0
assert "invalid_field" in result.errors[0].message
```

#### Layer 3: Schema Validation (SchemaValidator)

**Purpose**: Validate YAML structure and constraints

**Validation**:
- Required keys validation
- Data type validation
- Parameter range validation
- Constraint enforcement

**Example**:

```python
from src.execution.schema_validator import SchemaValidator, ValidationSeverity

validator = SchemaValidator(manifest=manifest)

yaml_dict = {
    "name": "Test Strategy",
    "type": "factor_graph",
    "required_fields": ["close", "volume"],
    "parameters": [{"name": "period", "type": "int", "value": 20}],
    "logic": {"entry": "close > 100", "exit": "close < 90"}
}

errors = validator.validate(yaml_dict)
if errors:
    for error in errors:
        print(f"{error.severity.value}: {error.message}")
```

### Error Types and Messages

#### Structured Error Format

```python
@dataclass
class ValidationError:
    severity: ValidationSeverity     # ERROR, WARNING, INFO
    message: str                     # Human-readable error message
    field_path: str                  # Path to error field (e.g., "parameters[0].value")
    line_number: Optional[int]       # Line number in YAML (if available)
    suggestion: Optional[str]        # Auto-correction suggestion
```

#### Common Error Examples

**Missing Required Key:**

```
ERROR: Missing required key: 'parameters'
  Field: <root>
  Suggestion: Add 'parameters' to the top level of your YAML
```

**Invalid Field Name:**

```
ERROR: Invalid field name: 'price:成交量'
  Field: required_fields[1]
  Suggestion: Did you mean 'price:成交金額'?
```

**Parameter Type Mismatch:**

```
ERROR: Parameter value type mismatch: expected int, got str
  Field: parameters[0].value
```

**Parameter Out of Range:**

```
ERROR: Parameter value 100 outside range [10, 60]
  Field: parameters[0].value
```

**Weight Sum Constraint Violation:**

```
ERROR: Weight sum constraint violated: sum = 0.95, expected 1.0 (±0.01)
  Field: constraints[0]
  Condition: momentum_weight + value_weight + quality_weight == 1.0
```

### Validation Workflow

```
1. Load YAML file
   ↓
2. Parse YAML to dictionary
   ↓
3. Layer 3: Schema validation
   - Check required keys
   - Validate data types
   - Check parameter ranges
   ↓
4. Layer 1: Field validation
   - Validate all field names
   - Apply auto-corrections
   ↓
5. Layer 2: Code validation
   - Parse logic formulas
   - Validate field references
   ↓
6. Constraint validation
   - Check all constraints
   - Enforce severity levels
   ↓
7. Create StrategyConfig dataclass
   ↓
8. Final validation
   - validate_dependencies()
   - get_critical_constraints()
```

---

## Best Practices

### 1. Field Naming

**DO:**
- ✅ Use canonical field names from DataFieldManifest
- ✅ Include all common aliases for LLM compatibility
- ✅ Document field usage with clear descriptions
- ✅ Use the CRITICAL note for trading VALUE vs shares distinction

**DON'T:**
- ❌ Mix canonical names and aliases inconsistently
- ❌ Assume "volume" means shares (it means trading VALUE)
- ❌ Skip the `usage` field (important for documentation)

**Example:**

```yaml
# GOOD - Clear canonical name with aliases and usage
- field: "price:成交金額"
  aliases: ["volume", "trading_value", "turnover"]
  usage: "Volume filtering - minimum liquidity requirement"
  note: "CRITICAL: This is trading VALUE (金額), not shares (股數)"

# BAD - Ambiguous field name
- field: "volume"  # Is this VALUE or shares?
```

### 2. Parameter Configuration

**DO:**
- ✅ Always specify `range` for numeric parameters
- ✅ Use descriptive parameter names
- ✅ Include `unit` field for clarity
- ✅ Set reasonable default values
- ✅ Document parameter relationships in notes

**DON'T:**
- ❌ Use vague parameter names like `param1`, `threshold`
- ❌ Omit range validation for numeric types
- ❌ Set defaults outside valid range

**Example:**

```yaml
# GOOD - Well-documented parameter with range
- name: "momentum_period"
  type: "integer"
  description: "Lookback period for momentum calculation"
  value: 20
  default: 20
  range: [10, 60]
  unit: "trading_days"

# BAD - Poorly documented parameter
- name: "period"
  type: "integer"
  value: 20
  # Missing: description, range, unit
```

### 3. Logic Formulas

**DO:**
- ✅ Use clear, readable pandas/numpy expressions
- ✅ List all dependencies explicitly
- ✅ Use multi-line formulas for complex logic
- ✅ Add comments in multi-line formulas
- ✅ Validate dependencies match formula

**DON'T:**
- ❌ Use Python features not supported by pandas (e.g., list comprehensions)
- ❌ Reference fields not in dependencies
- ❌ Use ambiguous variable names

**Example:**

```yaml
# GOOD - Clear formula with all dependencies
entry:
  description: "Momentum breakout with volume confirmation"
  formula: "(price.pct_change(20).rolling(5).mean() > 0.02) & (volume > 1000000)"
  dependencies: ["price:收盤價", "price:成交金額"]

# BAD - Missing dependencies
entry:
  formula: "(close > high.rolling(20).max()) & (volume > 1000000)"
  dependencies: ["price:收盤價"]  # Missing "price:最高價" and "price:成交金額"
```

### 4. Constraints

**DO:**
- ✅ Use appropriate severity levels
- ✅ Set `critical` severity for must-pass constraints
- ✅ Include tolerance for numeric comparisons
- ✅ Provide helpful error messages

**DON'T:**
- ❌ Overuse `critical` severity (blocks execution)
- ❌ Forget tolerance for floating-point comparisons
- ❌ Write vague constraint messages

**Example:**

```yaml
# GOOD - Well-defined constraint with tolerance
- type: "parameter"
  condition: "momentum_weight + value_weight + quality_weight == 1.0"
  severity: "critical"
  tolerance: 0.01
  message: "Factor weights must sum to 1.0 (±0.01 tolerance)"

# BAD - No tolerance for float comparison
- type: "parameter"
  condition: "sum_of_weights == 1.0"
  severity: "critical"
  # Will fail due to floating-point precision issues
```

### 5. Documentation

**DO:**
- ✅ Write clear `description` fields
- ✅ Document parameter units
- ✅ Explain complex logic in multi-line formulas
- ✅ Add notes for important warnings

**DON'T:**
- ❌ Leave descriptions empty
- ❌ Assume readers understand your notation
- ❌ Skip documentation for "obvious" parameters

### 6. Testing Strategies

**DO:**
- ✅ Validate YAML before deployment
- ✅ Test with Layer 1 field validation
- ✅ Run Layer 2 code validation on formulas
- ✅ Check constraint satisfaction
- ✅ Verify all dependencies are available

**DON'T:**
- ❌ Deploy untested configurations
- ❌ Skip validation steps
- ❌ Assume field names are correct

**Example Validation:**

```python
from src.config.data_fields import DataFieldManifest
from src.execution.schema_validator import SchemaValidator
import yaml

# Load manifest
manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')

# Load YAML
with open('strategy.yaml', 'r') as f:
    yaml_dict = yaml.safe_load(f)

# Validate schema
validator = SchemaValidator(manifest=manifest)
errors = validator.validate(yaml_dict)

# Check errors
if errors:
    for error in errors:
        print(error)
else:
    print("✅ Strategy configuration is valid")
```

### 7. Version Control

**DO:**
- ✅ Track schema version in YAML
- ✅ Document pattern coverage
- ✅ Include creation/modification dates
- ✅ Reference source pattern IDs

**DON'T:**
- ❌ Mix different schema versions
- ❌ Skip metadata documentation

**Example:**

```yaml
name: "My Strategy"
type: "pure_momentum"
description: "Custom momentum strategy"
coverage: 0.18

metadata:
  schema_version: "1.0"
  created_date: "2025-11-18"
  pattern_reference: "template_0"
  author: "Strategy Developer"
```

---

## Additional Resources

### Related Files

- **Schema Definition**: `src/config/strategy_schema.yaml` - Central schema with all 5 patterns
- **Dataclass Definitions**: `src/execution/strategy_config.py` - StrategyConfig and related classes
- **Schema Validator**: `src/execution/schema_validator.py` - SchemaValidator implementation
- **Field Manifest**: `src/config/data_fields.py` - DataFieldManifest with field validation
- **Pattern Analysis**: `docs/PATTERN_COVERAGE_ANALYSIS.md` - Pattern coverage analysis

### Testing

Comprehensive test suite:

- `tests/execution/test_strategy_config.py` - StrategyConfig dataclass tests
- `tests/execution/test_schema_validator.py` - SchemaValidator tests
- `tests/config/test_data_field_manifest.py` - DataFieldManifest tests

### References

- **finlab API Documentation**: [finlab.tw](https://finlab.tw)
- **Three-Layered Defense**: See project architecture documentation
- **Pattern Analysis**: Task 15.3 - Pattern extraction and coverage analysis
- **Schema Design**: Task 16.3 - Central schema definition

---

## Appendix: Quick Reference

### Valid Pattern Types

- `pure_momentum`
- `momentum_exit`
- `turtle_breakout`
- `multi_factor_scoring`
- `complex_combination`

### Valid Parameter Types

- `integer`
- `float`
- `boolean`
- `string`
- `list`

### Valid Constraint Types

- `data_quality`
- `parameter`
- `logic`
- `performance`

### Valid Severity Levels

- `critical` - Strategy execution blocked
- `high` - High risk, execution may continue
- `medium` - Medium risk
- `low` - Low risk
- `warning` - Informational only

### Common Field Names

**Price Fields:**
- `price:收盤價` (close)
- `price:成交金額` (volume/trading value)
- `price:最高價` (high)
- `price:最低價` (low)
- `price:開盤價` (open)

**Fundamental Fields:**
- `fundamental_features:本益比` (PE ratio)
- `fundamental_features:股價淨值比` (PB ratio)
- `fundamental_features:ROE`
- `fundamental_features:ROA`
- `fundamental_features:殖利率` (dividend yield)

---

**Document Version**: 1.0
**Created**: 2025-11-18
**Maintained By**: LLM Strategy Generator Team
**Schema Version**: 1.0
