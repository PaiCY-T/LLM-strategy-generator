# Structured Innovation - User Guide

**Version**: 1.0.0
**Last Updated**: 2025-10-26
**Status**: Production Ready

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [YAML Strategy Format](#yaml-strategy-format)
4. [Position Sizing Methods](#position-sizing-methods)
5. [Integration with Autonomous Loop](#integration-with-autonomous-loop)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

---

## Introduction

The Structured Innovation system represents a breakthrough in LLM-driven strategy generation. Instead of generating full Python code (which often contains hallucinations and syntax errors), the LLM generates **validated YAML specifications** that are mechanically transformed into executable Python code.

### Why YAML Instead of Full Python Code?

**Traditional LLM Code Generation** (Full Python):
```python
# LLM-generated Python code
def strategy(data):
    # Common issues:
    # - Hallucinated API calls: data.get_rsi(14) ❌
    # - Syntax errors: missing colons, indentation ❌
    # - Invalid logic: undefined variables ❌
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15  # May work, but often contains errors
```
❌ ~60% success rate due to hallucinations
❌ Unpredictable errors and edge cases
❌ Difficult to validate before execution

**Structured Innovation** (YAML → Code):
```yaml
# LLM-generated YAML specification
metadata:
  name: "High ROE Strategy"
  strategy_type: "factor_combination"
  rebalancing_frequency: "M"

indicators:
  fundamental_factors:
    - name: "roe"
      field: "ROE"
      source: "data.get('ROE')"

entry_conditions:
  threshold_rules:
    - condition: "roe > 15"
      description: "Select stocks with ROE > 15%"

position_sizing:
  method: "equal_weight"
  max_positions: 20
```
✅ >90% success rate (schema-validated)
✅ Predictable code generation
✅ Validation before code generation
✅ Eliminates API hallucinations

### Benefits and Tradeoffs

**Benefits**:
1. **High Success Rate**: >90% valid strategies vs ~60% with full code generation
2. **Hallucination Elimination**: Schema validation prevents invalid indicator types, incorrect API calls
3. **Faster Iteration**: Validation catches errors before expensive backtest execution
4. **LLM-Friendly**: Declarative YAML is easier for LLMs to generate correctly than imperative Python
5. **Maintainability**: YAML specs are version-controlled, readable, and reusable

**Tradeoffs**:
1. **Coverage Limitation**: ~85% of strategy patterns expressible via YAML (very complex custom logic may require full Python)
2. **Less Flexibility**: Cannot write arbitrary Python code within YAML specs
3. **Template Dependency**: Code generation relies on Jinja2 templates (but they're comprehensive and tested)

**When to Use Each Mode**:
- **YAML Mode (Recommended)**: Default for 90% of strategies, especially momentum, mean reversion, factor combination
- **Full Code Mode**: For highly custom strategies requiring complex logic not covered by schema
- **Hybrid Mode**: 80% YAML, 20% full code for diversity and experimentation

---

## Quick Start

### 1. Create a YAML Strategy

Create a file `my_momentum_strategy.yaml`:

```yaml
metadata:
  name: "My First Momentum Strategy"
  description: "Simple price momentum with RSI filter and volume confirmation"
  strategy_type: "momentum"
  rebalancing_frequency: "W-FRI"
  version: "1.0.0"
  risk_level: "medium"

indicators:
  technical_indicators:
    # RSI for overbought/oversold detection
    - name: "rsi_14"
      type: "RSI"
      period: 14
      source: "data.get('RSI_14')"

    # 50-day moving average for trend
    - name: "ma_50"
      type: "SMA"
      period: 50
      source: "data.get('MA_50')"

  custom_calculations:
    # 20-day momentum
    - name: "momentum_20"
      expression: "(close - close.shift(20)) / close.shift(20)"
      description: "20-day price momentum"

entry_conditions:
  threshold_rules:
    - condition: "momentum_20 > 0.10"
      description: "Strong positive momentum (>10%)"

    - condition: "rsi_14 < 70"
      description: "Not overbought"

    - condition: "close > ma_50"
      description: "Price above 50-day MA"

  logical_operator: "AND"

  min_liquidity:
    average_volume_20d: 100000000

exit_conditions:
  stop_loss_pct: 0.08
  take_profit_pct: 0.25

  trailing_stop:
    trail_percent: 0.08
    activation_profit: 0.05

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

### 2. Validate and Generate Code

```python
from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator

# Initialize validator and generator
validator = YAMLSchemaValidator()
generator = YAMLToCodeGenerator(validator)

# Generate code from YAML file
code, errors = generator.generate_from_file('my_momentum_strategy.yaml')

if code:
    print("✅ Generated code successfully!")
    print(code[:500])  # Print first 500 characters

    # Save to file
    with open('generated_strategy.py', 'w') as f:
        f.write(code)
else:
    print("❌ Validation errors:")
    for error in errors:
        print(f"  - {error}")
```

**Expected Output**:
```
✅ Generated code successfully!
def strategy(data):
    """
    My First Momentum Strategy
    Simple price momentum with RSI filter and volume confirmation

    Strategy Type: momentum
    Rebalancing: W-FRI
    """
    # Indicators
    rsi_14 = data.get('RSI_14')
    ma_50 = data.get('MA_50')

    # Custom calculations
    momentum_20 = (data['close'] - data['close'].shift(20)) / data['close'].shift(20)

    # Entry conditions
    ...
```

### 3. Use in InnovationEngine

```python
from src.innovation.innovation_engine import InnovationEngine

# Initialize with YAML mode
engine = InnovationEngine(
    provider_name='gemini',
    generation_mode='yaml',  # Enable YAML mode
    max_retries=3,
    temperature=0.7
)

# Generate new strategy
champion_metrics = {
    'sharpe_ratio': 1.5,
    'annual_return': 0.15,
    'max_drawdown': -0.20
}

failure_history = [
    "Overtrading with >200 trades/year caused slippage",
    "Large drawdowns when ignoring liquidity filters"
]

# LLM generates YAML, validates, and returns Python code
code = engine.generate_innovation(
    champion_code="",  # Not used in YAML mode
    champion_metrics=champion_metrics,
    failure_history=failure_history,
    target_metric="sharpe_ratio"
)

if code:
    print("✅ LLM generated valid strategy!")
    # Execute backtest...
else:
    print("⚠️ LLM generation failed, falling back to mutation")
    # Fallback to factor graph mutation
```

---

## YAML Strategy Format

### Schema Overview

Every YAML strategy consists of 6 main sections:

1. **metadata** (required): Strategy identification and configuration
2. **indicators** (required): Technical indicators, fundamental factors, custom calculations
3. **entry_conditions** (required): Rules for entering positions
4. **exit_conditions** (optional): Risk management and exit rules
5. **position_sizing** (optional): Portfolio construction rules
6. **risk_management** (optional): Portfolio-level risk constraints

### Required vs Optional Fields

**Required**:
- `metadata.name`: Strategy name (5-100 characters)
- `metadata.strategy_type`: "momentum", "mean_reversion", or "factor_combination"
- `metadata.rebalancing_frequency`: "M" (monthly), "W-FRI", "W-MON", or "Q"
- `indicators`: At least one indicator (technical, fundamental, or custom)
- `entry_conditions`: At least one threshold_rule or ranking_rule

**Optional but Recommended**:
- `metadata.description`: Human-readable strategy explanation
- `exit_conditions`: Risk management (stop loss, take profit, trailing stops)
- `position_sizing.method`: Defaults to "equal_weight" if not specified
- `risk_management`: Portfolio-level constraints

### Strategy Types

#### 1. Momentum Strategy

Trend-following strategies that buy stocks with strong recent price performance.

**Key Characteristics**:
- Use technical indicators (RSI, MACD, moving averages)
- Entry: Strong positive momentum + trend confirmation
- Exit: Trailing stops to protect profits

**Example Pattern**:
```yaml
metadata:
  strategy_type: "momentum"
  rebalancing_frequency: "W-FRI"

indicators:
  technical_indicators:
    - name: "rsi_14"
      type: "RSI"
      period: 14
  custom_calculations:
    - name: "momentum_20"
      expression: "(close - close.shift(20)) / close.shift(20)"

entry_conditions:
  threshold_rules:
    - condition: "momentum_20 > 0.10"
    - condition: "rsi_14 < 70"
  logical_operator: "AND"
```

#### 2. Mean Reversion Strategy

Buy oversold stocks expecting bounce-back to average levels.

**Key Characteristics**:
- Use mean reversion indicators (RSI, Bollinger Bands, z-scores)
- Entry: Oversold conditions with reversal signals
- Exit: Return to mean or take profit

**Example Pattern**:
```yaml
metadata:
  strategy_type: "mean_reversion"
  rebalancing_frequency: "M"

indicators:
  technical_indicators:
    - name: "rsi_14"
      type: "RSI"
      period: 14
    - name: "bb_lower"
      type: "BB"
      period: 20

entry_conditions:
  threshold_rules:
    - condition: "rsi_14 < 30"
    - condition: "close < bb_lower"
  logical_operator: "AND"

exit_conditions:
  take_profit_pct: 0.15
  conditional_exits:
    - condition: "rsi_14 > 50"
```

#### 3. Factor Combination Strategy

Multi-factor strategies combining fundamental and technical signals.

**Key Characteristics**:
- Combine fundamental factors (ROE, revenue growth) with technical filters
- Use ranking_rules to select top stocks
- Often use factor_weighted position sizing

**Example Pattern**:
```yaml
metadata:
  strategy_type: "factor_combination"
  rebalancing_frequency: "M"

indicators:
  fundamental_factors:
    - name: "roe"
      field: "ROE"
      source: "data.get('ROE')"
    - name: "revenue_growth"
      field: "revenue_growth"
      source: "data.get('revenue_growth')"

  custom_calculations:
    - name: "quality_score"
      expression: "roe * (1 + revenue_growth)"

entry_conditions:
  ranking_rules:
    - field: "quality_score"
      method: "top_percent"
      value: 20
      ascending: false

  threshold_rules:
    - condition: "roe > 10"

position_sizing:
  method: "factor_weighted"
  weighting_field: "quality_score"
  max_positions: 30
```

---

## Position Sizing Methods

### 1. Equal Weight

Distribute capital equally across all positions.

**Usage**:
```yaml
position_sizing:
  method: "equal_weight"
  max_positions: 20
  max_position_pct: 0.10  # Cap at 10% per position
```

**Best For**: Momentum and mean reversion strategies, simplicity

**Generated Code**:
```python
# Equal weight across all positions
weights = selected_stocks / selected_stocks.sum()
```

### 2. Factor Weighted

Weight positions by factor score (stronger signals get larger positions).

**Usage**:
```yaml
position_sizing:
  method: "factor_weighted"
  weighting_field: "quality_score"  # Must be defined in indicators
  max_positions: 30
  max_position_pct: 0.15
  min_position_pct: 0.01
```

**Best For**: Factor combination strategies, quality-based selection

**Generated Code**:
```python
# Weight by quality_score
weights = quality_score / quality_score.sum()
weights = weights.clip(lower=0.01, upper=0.15)  # Apply limits
```

### 3. Risk Parity

Weight positions by inverse volatility (lower vol = higher weight).

**Usage**:
```yaml
position_sizing:
  method: "risk_parity"
  max_positions: 25
  max_position_pct: 0.12
```

**Best For**: Diversified portfolios, risk-adjusted allocation

**Generated Code**:
```python
# Calculate inverse volatility weights
volatility = data['close'].rolling(20).std()
inv_vol = 1 / volatility
weights = inv_vol / inv_vol.sum()
```

### 4. Volatility Weighted

Similar to risk parity, weights by inverse volatility.

**Usage**:
```yaml
position_sizing:
  method: "volatility_weighted"
  max_positions: 20
```

**Best For**: Risk-conscious strategies, low-volatility anomaly

### 5. Custom Formula

Use custom expression for position sizing.

**Usage**:
```yaml
position_sizing:
  method: "custom_formula"
  custom_formula: "quality_score / volatility"
  max_positions: 30
  max_position_pct: 0.10
```

**Best For**: Advanced users, unique weighting schemes

**Generated Code**:
```python
# Custom weighting formula
weights = (quality_score / volatility)
weights = weights / weights.sum()
```

---

## Integration with Autonomous Loop

### Enabling YAML Mode

Configure the InnovationEngine to use YAML mode:

```python
# In autonomous loop configuration
engine = InnovationEngine(
    provider_name='gemini',
    generation_mode='yaml',  # Use YAML mode
    max_retries=3,
    temperature=0.7
)
```

### Configuration Options

Three generation modes are supported:

1. **YAML Mode** (Recommended):
```python
generation_mode='yaml'
```
- LLM generates YAML specs
- Validates against schema
- Generates Python code
- >90% success rate

2. **Full Code Mode** (Legacy):
```python
generation_mode='full_code'
```
- LLM generates complete Python code
- Direct validation with AST
- ~60% success rate
- Use for highly custom logic

3. **Hybrid Mode** (Experimental):
```python
generation_mode='hybrid'
# 80% YAML, 20% full code by default
```
- Alternates between YAML and full code
- Configured via `config/learning_system.yaml`

### Innovation Rate Control

Control how often YAML mode is used in hybrid mode:

```yaml
# config/learning_system.yaml
llm:
  mode: "hybrid"
  hybrid_structured_ratio: 0.80  # 80% YAML, 20% full code
  provider: "gemini"
  model: "gemini-2.0-flash-exp"
```

### Integration Example

```python
from src.innovation.innovation_engine import InnovationEngine
from src.backtest.metrics import calculate_metrics

# Initialize YAML mode engine
engine = InnovationEngine(
    provider_name='gemini',
    generation_mode='yaml',
    temperature=0.7
)

# Autonomous loop iteration
for iteration in range(100):
    # Generate new strategy
    new_code = engine.generate_innovation(
        champion_code=champion.code,
        champion_metrics=champion.metrics,
        failure_history=recent_failures[-3:],
        target_metric="sharpe_ratio"
    )

    if new_code is None:
        # Fallback to factor graph mutation
        new_code = factor_graph_mutate(champion.strategy)

    # Backtest and evaluate
    metrics = calculate_metrics(new_code, data)

    # Update champion if better
    if metrics['sharpe_ratio'] > champion.metrics['sharpe_ratio']:
        champion.code = new_code
        champion.metrics = metrics
        print(f"✅ New champion! Sharpe: {metrics['sharpe_ratio']:.2f}")
```

---

## Best Practices

### Designing Effective YAML Strategies

1. **Start Simple**:
   - Begin with 2-3 indicators
   - Use clear threshold rules
   - Test before adding complexity

2. **Use Clear Naming**:
```yaml
# Good: descriptive, lowercase with underscores
indicators:
  technical_indicators:
    - name: "rsi_14"
    - name: "ma_50"
  custom_calculations:
    - name: "momentum_20d"

# Bad: unclear, inconsistent
indicators:
  technical_indicators:
    - name: "x1"
    - name: "MovingAvg"
```

3. **Validate Indicator References**:
```yaml
entry_conditions:
  threshold_rules:
    - condition: "rsi_14 > 30"  # ✅ rsi_14 defined in indicators
    - condition: "momentum > 0.10"  # ❌ momentum not defined

# Fix: define momentum first
indicators:
  custom_calculations:
    - name: "momentum"
      expression: "(close - close.shift(20)) / close.shift(20)"
```

4. **Use Realistic Parameters**:
```yaml
# Good: realistic ranges
entry_conditions:
  threshold_rules:
    - condition: "rsi_14 < 70"  # Reasonable RSI threshold
  min_liquidity:
    average_volume_20d: 100000000  # 100M volume

# Bad: unrealistic parameters
entry_conditions:
  threshold_rules:
    - condition: "rsi_14 < 5"  # Extreme oversold (rarely triggers)
  min_liquidity:
    average_volume_20d: 10000000000  # 10B volume (too restrictive)
```

### Using Indicators Correctly

1. **Technical Indicators**:
```yaml
technical_indicators:
  # RSI: Use for overbought/oversold
  - name: "rsi_14"
    type: "RSI"
    period: 14  # Standard: 14 days

  # MACD: Use for trend and momentum
  - name: "macd"
    type: "MACD"
    parameters:
      fast_period: 12
      slow_period: 26
      signal_period: 9

  # Bollinger Bands: Use for volatility and mean reversion
  - name: "bb_upper"
    type: "BB"
    period: 20
    parameters:
      std_dev: 2.0
```

2. **Fundamental Factors**:
```yaml
fundamental_factors:
  # Quality factors
  - name: "roe"
    field: "ROE"
    transformation: "winsorize"  # Handle outliers

  # Growth factors
  - name: "revenue_growth"
    field: "revenue_growth"
    transformation: "winsorize"

  # Value factors
  - name: "pb_ratio"
    field: "PB_ratio"
    transformation: "rank"  # Percentile ranking
```

3. **Custom Calculations**:
```yaml
custom_calculations:
  # Combine multiple indicators
  - name: "quality_momentum"
    expression: "roe * momentum_20"
    description: "Quality × Momentum composite score"

  # Normalize factors
  - name: "roe_zscore"
    expression: "(roe - roe.mean()) / roe.std()"
    description: "Z-score normalized ROE"
```

### Entry/Exit Condition Patterns

**Momentum Entry Pattern**:
```yaml
entry_conditions:
  threshold_rules:
    - condition: "momentum_20 > 0.10"  # Strong momentum
    - condition: "rsi_14 < 70"  # Not overbought
    - condition: "close > ma_50"  # Uptrend
  logical_operator: "AND"
```

**Mean Reversion Entry Pattern**:
```yaml
entry_conditions:
  threshold_rules:
    - condition: "rsi_14 < 30"  # Oversold
    - condition: "close < bb_lower"  # Below lower band
  logical_operator: "AND"
```

**Factor Combination Pattern**:
```yaml
entry_conditions:
  ranking_rules:
    - field: "quality_score"
      method: "top_percent"
      value: 20  # Top 20% by quality

  threshold_rules:
    - condition: "roe > 10"  # Minimum quality threshold
    - condition: "pb_ratio < 3"  # Valuation filter
```

**Exit Condition Pattern**:
```yaml
exit_conditions:
  # Hard stops
  stop_loss_pct: 0.08  # -8% stop loss
  take_profit_pct: 0.25  # +25% take profit

  # Trailing stop (activates after profit)
  trailing_stop:
    trail_percent: 0.08  # Trail 8% below peak
    activation_profit: 0.05  # Activate after 5% gain

  # Conditional exits
  conditional_exits:
    - condition: "rsi_14 > 80"  # Extreme overbought
    - condition: "close < ma_20"  # Trend reversal

  # Time-based exit
  holding_period_days: 30  # Max 30 days

  # Exit if ANY condition met
  exit_operator: "OR"
```

### Risk Management Guidelines

```yaml
risk_management:
  # Sector concentration
  max_sector_exposure: 0.30  # Max 30% in any sector

  # Rebalancing
  rebalance_threshold: 0.15  # Rebalance if position drifts >15%

  # Drawdown protection
  max_drawdown_limit: 0.20  # Reduce positions if DD >20%

  # Cash reserve
  cash_reserve_pct: 0.05  # Keep 5% in cash
```

---

## Troubleshooting

### Common YAML Validation Errors

#### Error: Missing required field 'rebalancing_frequency'

```yaml
# ❌ Missing required field
metadata:
  name: "My Strategy"
  strategy_type: "momentum"
  # Missing: rebalancing_frequency

# ✅ Fixed
metadata:
  name: "My Strategy"
  strategy_type: "momentum"
  rebalancing_frequency: "M"  # Added required field
```

#### Error: Field 'momentum' not found in indicators

```yaml
# ❌ Using undefined indicator
entry_conditions:
  threshold_rules:
    - condition: "momentum > 0.10"  # momentum not defined

# ✅ Fixed
indicators:
  custom_calculations:
    - name: "momentum"  # Define first
      expression: "(close - close.shift(20)) / close.shift(20)"

entry_conditions:
  threshold_rules:
    - condition: "momentum > 0.10"  # Now valid
```

#### Error: Invalid strategy_type value

```yaml
# ❌ Invalid enum value
metadata:
  strategy_type: "trend_following"  # Not a valid type

# ✅ Fixed - use one of: momentum, mean_reversion, factor_combination
metadata:
  strategy_type: "momentum"
```

#### Error: Period must be between 1 and 250

```yaml
# ❌ Invalid period
technical_indicators:
  - name: "ma_500"
    type: "SMA"
    period: 500  # Exceeds maximum

# ✅ Fixed
technical_indicators:
  - name: "ma_200"
    type: "SMA"
    period: 200  # Within valid range (1-250)
```

### Code Generation Failures

#### Issue: Generated code has syntax error

**Cause**: Template bug or invalid custom expression

**Solution**:
1. Check custom_calculations expressions are valid Python:
```yaml
# ❌ Invalid Python syntax
custom_calculations:
  - name: "score"
    expression: "roe * (1 + revenue_growth"  # Missing closing paren

# ✅ Fixed
custom_calculations:
  - name: "score"
    expression: "roe * (1 + revenue_growth)"
```

2. Report template bugs if valid YAML produces invalid code

#### Issue: Generated code references undefined variables

**Cause**: Indicator reference not defined in indicators section

**Solution**: Ensure all referenced indicators are defined:
```yaml
# ❌ References undefined 'volume_ratio'
entry_conditions:
  threshold_rules:
    - condition: "volume_ratio > 1.5"

# ✅ Fixed - define volume_ratio
indicators:
  custom_calculations:
    - name: "volume_ratio"
      expression: "volume / volume.rolling(20).mean()"
```

### Performance Issues

#### Issue: YAML validation is slow

**Cause**: Large YAML file or complex schema validation

**Solution**:
- Keep YAML files under 500 lines
- Limit indicators to <20
- Use `validate_semantics=False` if only checking schema:
```python
generator = YAMLToCodeGenerator(
    schema_validator,
    validate_semantics=False  # Skip semantic validation
)
```

#### Issue: Code generation takes >1 second

**Cause**: Complex Jinja2 template rendering

**Solution**:
- Simplify custom calculations
- Reduce number of conditions
- Batch generation if processing multiple specs:
```python
results = generator.generate_batch_from_files(yaml_files)
```

### LLM Generation Issues

#### Issue: LLM returns invalid YAML

**Cause**: LLM hallucination or prompt confusion

**Solution**:
- Check prompt includes schema and examples
- Increase temperature for more creative output
- Use retry logic (automatic in InnovationEngine):
```python
engine = InnovationEngine(
    generation_mode='yaml',
    max_retries=3  # Retry on validation errors
)
```

#### Issue: LLM generates YAML but validation fails

**Cause**: LLM not following schema exactly

**Solution**:
- Review validation errors for patterns
- Update prompt examples if specific field consistently wrong
- Add field-specific guidance to structured prompt:
```python
builder = StructuredPromptBuilder()
prompt = builder.build_yaml_generation_prompt(
    champion_metrics=metrics,
    failure_patterns=failures,
    target_strategy_type="momentum"  # Specify target type
)
```

#### Issue: All LLM attempts fail, always falling back

**Cause**: Provider configuration or API issues

**Solution**:
1. Check API keys are valid:
```bash
export GOOGLE_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"
```

2. Check provider availability:
```python
engine = InnovationEngine(provider_name='gemini')
if not engine.provider_available:
    print("Provider not configured correctly")
```

3. Review failure logs:
```python
print(f"Total attempts: {engine.total_attempts}")
print(f"Success rate: {engine.successful_generations / engine.total_attempts}")
print(f"YAML validation failures: {engine.yaml_validation_failures}")
```

### Getting Help

1. **Check validation errors**: Read error messages carefully, they include field paths
2. **Review examples**: Look at `examples/yaml_strategies/` for working examples
3. **Schema reference**: See `docs/YAML_STRATEGY_GUIDE.md` for complete field documentation
4. **API reference**: See `docs/STRUCTURED_INNOVATION_API.md` for programmatic usage

---

## Next Steps

- Read [YAML Strategy Guide](YAML_STRATEGY_GUIDE.md) for complete schema documentation
- Read [API Reference](STRUCTURED_INNOVATION_API.md) for programmatic usage
- Review [example strategies](../examples/yaml_strategies/) for patterns
- Experiment with YAML mode in InnovationEngine

**Happy Structured Innovating! 🚀**
