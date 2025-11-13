# Factor Graph System - User Guide

**Version**: 2.0+
**Last Updated**: 2025-10-23
**Status**: Production Ready

---

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Getting Started](#getting-started)
4. [Creating Factors](#creating-factors)
5. [Building Strategies](#building-strategies)
6. [Three-Tier Mutation System](#three-tier-mutation-system)
7. [Running Backtests](#running-backtests)
8. [Best Practices](#best-practices)
9. [Common Patterns](#common-patterns)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

The Factor Graph System represents a paradigm shift in quantitative strategy development. Instead of treating strategies as parameter dictionaries, strategies are now **Directed Acyclic Graphs (DAGs) of atomic Factors**.

### Why Factor Graphs?

**Traditional Approach** (Parameter Dictionary):
```python
strategy = {
    "entry_period": 20,
    "exit_period": 10,
    "stop_loss": 0.02
}
```
❌ Limited to pre-defined templates
❌ Cannot change strategy structure
❌ Innovation constrained to parameter tuning

**Factor Graph Approach** (Compositional):
```python
strategy = Strategy(id="my_strategy")
strategy.add_factor(momentum_factor)
strategy.add_factor(entry_signal, depends_on=["momentum_20"])
strategy.add_factor(stop_loss, depends_on=["entry_signal"])
```
✅ Structural innovation through composition
✅ Reusable factor library
✅ Validation-first approach (DAG integrity)
✅ Natural mutation at factor level

### Key Benefits

1. **Breakthrough Performance**: Enable strategies that exceed single-template ceiling (Sharpe >2.5)
2. **Compositional Innovation**: Novel trading logic through factor combinations
3. **Safety**: DAG validation prevents invalid strategies before backtest
4. **Maintainability**: Modular, testable, reusable components
5. **Flexibility**: Three-tier mutation system (Safe → Domain → Advanced)

---

## Core Concepts

### Factor

An atomic strategy component with:
- **Inputs**: Required data columns (e.g., `["close", "volume"]`)
- **Outputs**: Produced data columns (e.g., `["rsi", "signal"]`)
- **Category**: Factor type (MOMENTUM, VALUE, QUALITY, RISK, EXIT, ENTRY, SIGNAL)
- **Logic**: Computation function `(DataFrame, params) → DataFrame`
- **Parameters**: Tunable values for optimization

**Example**:
```python
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory

def calculate_rsi(data, params):
    period = params["period"]
    delta = data["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    data["rsi"] = 100 - (100 / (1 + rs))
    data["rsi_signal"] = (data["rsi"] < params["oversold"]).astype(int)
    return data

rsi_factor = Factor(
    id="rsi_14",
    name="RSI Momentum Signal",
    category=FactorCategory.MOMENTUM,
    inputs=["close"],
    outputs=["rsi", "rsi_signal"],
    logic=calculate_rsi,
    parameters={"period": 14, "oversold": 30, "overbought": 70}
)
```

### Strategy

A DAG of Factors with:
- **factors**: Dictionary of Factor instances
- **dag**: NetworkX DiGraph tracking dependencies
- **validate()**: Check DAG integrity (no cycles, all inputs available)
- **to_pipeline()**: Compile to executable backtest

**Example**:
```python
from src.factor_graph.strategy import Strategy

strategy = Strategy(id="rsi_strategy", generation=0)

# Add factors in dependency order
strategy.add_factor(rsi_factor)  # Root factor (no dependencies)
strategy.add_factor(entry_factor, depends_on=["rsi_14"])
strategy.add_factor(exit_factor, depends_on=["entry_factor"])

# Validate DAG
strategy.validate()  # Raises ValueError if invalid

# Execute backtest
result = strategy.to_pipeline(data)
positions = result["positions"]
```

### Factor Categories

```python
class FactorCategory(Enum):
    MOMENTUM = "momentum"      # Trend-following, momentum indicators
    VALUE = "value"            # Valuation metrics, fundamental factors
    QUALITY = "quality"        # Financial health, quality metrics
    RISK = "risk"              # Volatility, risk management
    EXIT = "exit"              # Stop-loss, take-profit, exit signals
    ENTRY = "entry"            # Entry timing, position sizing
    SIGNAL = "signal"          # Combined signals, meta-strategies
```

---

## Getting Started

### Installation

The Factor Graph system is integrated into the finlab project:

```bash
# Ensure you're in the project directory
cd /path/to/finlab

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "from src.factor_graph.factor import Factor; print('✅ Factor Graph installed')"
```

### Quick Start Example

```python
import pandas as pd
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.strategy import Strategy

# 1. Create a simple momentum factor
def ma_crossover_logic(data, params):
    short_ma = data["close"].rolling(window=params["short_period"]).mean()
    long_ma = data["close"].rolling(window=params["long_period"]).mean()
    data["short_ma"] = short_ma
    data["long_ma"] = long_ma
    data["signal"] = (short_ma > long_ma).astype(int)
    return data

ma_factor = Factor(
    id="ma_crossover",
    name="MA Crossover Signal",
    category=FactorCategory.MOMENTUM,
    inputs=["close"],
    outputs=["short_ma", "long_ma", "signal"],
    logic=ma_crossover_logic,
    parameters={"short_period": 20, "long_period": 60}
)

# 2. Create entry factor
def entry_logic(data, params):
    data["positions"] = data["signal"]  # Use MA crossover signal
    return data

entry_factor = Factor(
    id="entry",
    name="Entry Signal",
    category=FactorCategory.ENTRY,
    inputs=["signal"],
    outputs=["positions"],
    logic=entry_logic,
    parameters={}
)

# 3. Build strategy
strategy = Strategy(id="ma_crossover_strategy", generation=0)
strategy.add_factor(ma_factor)
strategy.add_factor(entry_factor, depends_on=["ma_crossover"])

# 4. Validate
strategy.validate()  # ✅ Check DAG integrity

# 5. Backtest
import finlab
data = finlab.data.get("price:收盤價", start="2020-01-01")
result = strategy.to_pipeline(data)
print(result[["close", "short_ma", "long_ma", "positions"]].tail())
```

---

## Creating Factors

### Factor Design Principles

1. **Single Responsibility**: Each factor does ONE thing well
2. **Pure Functions**: Logic functions should be deterministic (same inputs → same outputs)
3. **Explicit Dependencies**: Declare all required inputs
4. **Meaningful Names**: Use descriptive IDs and names
5. **Parameter Validation**: Validate parameters in logic function

### Factor Templates

#### Momentum Factor Template

```python
def momentum_logic(data, params):
    """Calculate momentum indicator."""
    period = params["period"]
    data["momentum"] = data["close"].pct_change(period)
    data["momentum_signal"] = (data["momentum"] > params["threshold"]).astype(int)
    return data

momentum_factor = Factor(
    id=f"momentum_{params['period']}",
    name=f"Momentum ({params['period']}d)",
    category=FactorCategory.MOMENTUM,
    inputs=["close"],
    outputs=["momentum", "momentum_signal"],
    logic=momentum_logic,
    parameters={"period": 20, "threshold": 0.0}
)
```

#### Exit Factor Template

```python
def stop_loss_logic(data, params):
    """Apply fixed percentage stop-loss."""
    stop_loss_pct = params["stop_loss_pct"]

    # Assuming positions column exists
    entry_price = data["close"].where(data["positions"] == 1)
    entry_price = entry_price.fillna(method="ffill")

    # Calculate stop-loss trigger
    loss = (data["close"] - entry_price) / entry_price
    data["stop_loss_signal"] = (loss < -stop_loss_pct).astype(int)

    return data

stop_loss_factor = Factor(
    id="stop_loss_2pct",
    name="Stop Loss (2%)",
    category=FactorCategory.EXIT,
    inputs=["close", "positions"],
    outputs=["stop_loss_signal"],
    logic=stop_loss_logic,
    parameters={"stop_loss_pct": 0.02}
)
```

### Factor Registry Usage

```python
from src.factor_library.registry import FactorRegistry

# Get registry instance
registry = FactorRegistry.get_instance()

# List all available factors
factors = registry.list_factors()
print(f"Available factors: {len(factors)}")

# Get factor by category
momentum_factors = registry.get_factors_by_category(FactorCategory.MOMENTUM)
print(f"Momentum factors: {momentum_factors}")

# Create factor from registry
ma_filter = registry.create_factor("ma_filter_factor", parameters={"ma_periods": 60})

# Get factor metadata
metadata = registry.get_metadata("ma_filter_factor")
print(f"Parameters: {metadata['parameters']}")
print(f"Category: {metadata['category']}")
```

---

## Building Strategies

### Strategy Construction Patterns

#### Pattern 1: Linear Pipeline

```python
strategy = Strategy(id="linear_strategy", generation=0)

# Root factor (no dependencies)
strategy.add_factor(data_preprocessor)

# Sequential factors
strategy.add_factor(indicator1, depends_on=["data_preprocessor"])
strategy.add_factor(indicator2, depends_on=["indicator1"])
strategy.add_factor(signal, depends_on=["indicator2"])
strategy.add_factor(entry, depends_on=["signal"])
```

#### Pattern 2: Multi-Indicator Combination

```python
strategy = Strategy(id="multi_indicator", generation=0)

# Multiple root factors
strategy.add_factor(rsi_factor)
strategy.add_factor(macd_factor)
strategy.add_factor(bollinger_factor)

# Combine signals
strategy.add_factor(
    combined_signal,
    depends_on=["rsi_factor", "macd_factor", "bollinger_factor"]
)

# Entry based on combined signal
strategy.add_factor(entry, depends_on=["combined_signal"])
```

#### Pattern 3: Entry + Exit Strategy

```python
strategy = Strategy(id="entry_exit_strategy", generation=0)

# Entry logic
strategy.add_factor(momentum_indicator)
strategy.add_factor(entry_signal, depends_on=["momentum_indicator"])

# Multiple exit conditions
strategy.add_factor(stop_loss, depends_on=["entry_signal"])
strategy.add_factor(take_profit, depends_on=["entry_signal"])
strategy.add_factor(trailing_stop, depends_on=["entry_signal"])

# Combine exits
strategy.add_factor(
    exit_combiner,
    depends_on=["stop_loss", "take_profit", "trailing_stop"]
)
```

### Strategy Validation

```python
try:
    strategy.validate()
    print("✅ Strategy is valid")
except ValueError as e:
    print(f"❌ Validation failed: {e}")

    # Common validation errors:
    # - "Strategy contains cycles" → circular dependency
    # - "Factor X missing inputs: ['col']" → input not available
    # - "Strategy does not produce position signals" → no positions output
    # - "Strategy contains orphaned factors" → disconnected factors
```

---

## Three-Tier Mutation System

The Factor Graph system supports three tiers of mutations with progressively increasing risk and innovation potential:

### Tier 1: YAML Configuration (Safe)

**Risk Level**: LOW
**Use Case**: LLM-generated strategies, configuration-driven evolution
**Success Rate**: ~80%

```yaml
# config/my_strategy.yaml
strategy:
  id: "yaml_generated_strategy"
  factors:
    - type: "ma_filter_factor"
      parameters:
        ma_periods: 60

    - type: "entry_signal_factor"
      depends_on: ["ma_filter_60"]

    - type: "stop_loss_factor"
      parameters:
        stop_loss_pct: 0.02
      depends_on: ["entry_signal"]
```

**Usage**:
```python
from src.mutation.yaml.interpreter import YAMLInterpreter

interpreter = YAMLInterpreter()
strategy = interpreter.parse_yaml_file("config/my_strategy.yaml")
strategy.validate()
```

### Tier 2: Factor Operations (Domain-Specific)

**Risk Level**: MEDIUM
**Use Case**: Structural strategy evolution
**Success Rate**: ~60%

```python
from src.factor_graph.mutations import (
    add_factor,
    remove_factor,
    replace_factor,
    mutate_parameters
)

# Add new factor
mutated = add_factor(
    strategy=original_strategy,
    new_factor=volatility_filter,
    depends_on=["momentum_20"],
    insert_before="entry_signal"
)

# Remove factor
mutated = remove_factor(
    strategy=original_strategy,
    factor_id="old_indicator"
)

# Replace factor (same category)
mutated = replace_factor(
    strategy=original_strategy,
    old_factor_id="momentum_20",
    new_factor_name="ma_filter_factor",
    parameters={"ma_periods": 60},
    match_category=True
)

# Mutate parameters (Gaussian)
mutated = mutate_parameters(
    strategy=original_strategy,
    factor_id="rsi_14",
    mutation_rate=0.1,
    mutation_scale=0.2
)
```

### Tier 3: AST Mutations (Advanced)

**Risk Level**: HIGH
**Use Case**: Logic-level innovation
**Success Rate**: ~50%

```python
from src.mutation.ast_mutations.logic_modifier import ASTFactorMutator

mutator = ASTFactorMutator()

# Modify factor logic (AST-level)
mutated_factor = mutator.mutate_logic(
    factor=original_factor,
    mutation_type="modify_operator",  # change > to >=
    target_line=15
)

# Combine signals
combined_factor = mutator.combine_signals(
    factors=[rsi_factor, macd_factor],
    combination_type="and"  # logical AND
)
```

### Adaptive Tier Selection

```python
from src.mutation.tier_selection.tier_selection_manager import TierSelectionManager

manager = TierSelectionManager()

# Assess risk
risk_score = manager.assess_risk(strategy)
print(f"Risk score: {risk_score:.2f}")

# Select appropriate tier
tier = manager.select_tier(strategy, risk_score)
print(f"Selected tier: {tier}")

# Tier ranges:
# 0.0-0.3: Tier 1 (YAML - Safe)
# 0.3-0.7: Tier 2 (Factor ops - Medium risk)
# 0.7-1.0: Tier 3 (AST - High risk)
```

---

## Running Backtests

### Basic Backtest

```python
import finlab
from src.backtest.metrics import calculate_all_metrics

# Get data
data = finlab.data.get("price:收盤價", start="2020-01-01", end="2023-12-31")

# Run strategy pipeline
result = strategy.to_pipeline(data)
positions = result["positions"]

# Calculate metrics
metrics = calculate_all_metrics(positions, data["close"])
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Calmar Ratio: {metrics['calmar_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
```

### Multi-Objective Evaluation

```python
from src.evaluation.multi_objective_evaluator import MultiObjectiveEvaluator

evaluator = MultiObjectiveEvaluator()

# Evaluate strategy
metrics = evaluator.evaluate(strategy, data)

print(f"Primary metrics:")
print(f"  Sharpe: {metrics.sharpe_ratio:.2f}")
print(f"  Calmar: {metrics.calmar_ratio:.2f}")

print(f"Risk metrics:")
print(f"  Max Drawdown: {metrics.max_drawdown:.2%}")
print(f"  Volatility: {metrics.volatility:.2%}")

print(f"Robustness metrics:")
print(f"  Win Rate: {metrics.win_rate:.2%}")
print(f"  Profit Factor: {metrics.profit_factor:.2f}")
```

### Population Evolution

```python
from src.population.population_manager_v2 import PopulationManagerV2

# Initialize population
manager = PopulationManagerV2(
    population_size=20,
    enable_three_tier=True
)

# Run evolution
results = manager.evolve(
    generations=50,
    data=data,
    checkpoint_interval=10
)

# Get best strategy
best_strategy = results["best_strategy"]
best_metrics = results["best_metrics"]

print(f"Best Sharpe: {best_metrics.sharpe_ratio:.2f}")
print(f"Generation: {best_strategy.generation}")
```

---

## Best Practices

### 1. Factor Design

✅ **DO**:
- Keep factors focused (single responsibility)
- Use clear, descriptive names
- Validate parameters explicitly
- Handle edge cases (missing data, division by zero)
- Document expected inputs/outputs

❌ **DON'T**:
- Create overly complex factors (>100 lines)
- Modify input data in-place (use `.copy()`)
- Use global variables or external state
- Create circular dependencies

### 2. Strategy Composition

✅ **DO**:
- Validate after each factor addition
- Use meaningful factor IDs
- Document strategy intent
- Test with real data before evolution
- Track strategy lineage

❌ **DON'T**:
- Add factors without dependency checks
- Create strategies with >20 factors (complexity)
- Skip validation step
- Use hardcoded values (use parameters instead)

### 3. Mutation Operations

✅ **DO**:
- Start with Tier 1 (YAML) for new strategies
- Use Tier 2 for structural evolution
- Reserve Tier 3 for proven strategies
- Monitor tier success rates
- Preserve best strategies (elitism)

❌ **DON'T**:
- Jump to Tier 3 immediately
- Mutate all factors simultaneously
- Ignore validation failures
- Skip performance comparison

---

## Common Patterns

### Pattern 1: Indicator → Signal → Entry

```python
# Step 1: Calculate indicator
indicator_factor = Factor(
    id="indicator",
    inputs=["close"],
    outputs=["indicator_value"],
    logic=calculate_indicator,
    ...
)

# Step 2: Generate signal
signal_factor = Factor(
    id="signal",
    inputs=["indicator_value"],
    outputs=["signal"],
    logic=generate_signal,
    ...
)

# Step 3: Entry logic
entry_factor = Factor(
    id="entry",
    inputs=["signal"],
    outputs=["positions"],
    logic=entry_logic,
    ...
)

strategy.add_factor(indicator_factor)
strategy.add_factor(signal_factor, depends_on=["indicator"])
strategy.add_factor(entry_factor, depends_on=["signal"])
```

### Pattern 2: Multi-Factor Confirmation

```python
# Multiple independent indicators
strategy.add_factor(rsi_factor)
strategy.add_factor(macd_factor)
strategy.add_factor(volume_factor)

# Combine for confirmation
def combine_logic(data, params):
    data["combined_signal"] = (
        (data["rsi_signal"] == 1) &
        (data["macd_signal"] == 1) &
        (data["volume_signal"] == 1)
    ).astype(int)
    return data

combiner = Factor(
    id="combiner",
    inputs=["rsi_signal", "macd_signal", "volume_signal"],
    outputs=["combined_signal"],
    logic=combine_logic,
    ...
)

strategy.add_factor(combiner, depends_on=["rsi", "macd", "volume"])
```

### Pattern 3: Dynamic Risk Management

```python
# Calculate volatility
strategy.add_factor(atr_factor)

# Position sizing based on volatility
def position_size_logic(data, params):
    risk_per_trade = params["risk_pct"]
    atr = data["atr"]
    position_size = risk_per_trade / atr
    position_size = position_size.clip(lower=0, upper=1)  # Cap at 100%
    data["position_size"] = position_size
    return data

position_sizer = Factor(
    id="position_sizer",
    inputs=["atr", "signal"],
    outputs=["position_size"],
    logic=position_size_logic,
    parameters={"risk_pct": 0.01}
)

strategy.add_factor(position_sizer, depends_on=["atr", "signal"])
```

---

## Troubleshooting

### Common Errors

#### 1. Circular Dependency

**Error**: `ValueError: Adding factor X would create cycle`

**Cause**: Factor A depends on B, B depends on C, C depends on A

**Solution**:
```python
# Check DAG before adding
import networkx as nx
if not nx.is_directed_acyclic_graph(strategy.dag):
    print("Cycle detected!")
    # Use nx.simple_cycles(strategy.dag) to find cycles
```

#### 2. Missing Inputs

**Error**: `ValueError: Factor 'X' missing inputs: ['col']`

**Cause**: Required input column not produced by any previous factor

**Solution**:
```python
# Check available columns at each step
available = ["open", "high", "low", "close", "volume"]
for factor_id in nx.topological_sort(strategy.dag):
    factor = strategy.factors[factor_id]
    print(f"{factor_id}: needs {factor.inputs}, available: {available}")
    available.extend(factor.outputs)
```

#### 3. Invalid Strategy Structure

**Error**: `ValueError: Strategy does not produce position signals`

**Cause**: No factor produces "positions" or "signal" output

**Solution**:
```python
# Ensure at least one factor produces positions
has_positions = any(
    "positions" in f.outputs or "signal" in f.outputs
    for f in strategy.factors.values()
)
if not has_positions:
    print("❌ No position signal factor")
```

#### 4. Performance Issues

**Issue**: Strategy execution is slow

**Solutions**:
- Reduce DAG complexity (combine factors)
- Cache intermediate results
- Use vectorized operations (avoid loops)
- Parallelize independent factors

```python
# Profile execution time
import time
for factor_id in nx.topological_sort(strategy.dag):
    start = time.time()
    factor = strategy.factors[factor_id]
    result = factor.execute(data)
    elapsed = time.time() - start
    print(f"{factor_id}: {elapsed:.3f}s")
```

---

## Next Steps

1. **Read API Reference**: [FACTOR_GRAPH_API_REFERENCE.md](./FACTOR_GRAPH_API_REFERENCE.md)
2. **YAML Configuration**: [YAML_CONFIGURATION_GUIDE.md](./YAML_CONFIGURATION_GUIDE.md)
3. **Mutation Reference**: [MUTATION_OPERATOR_REFERENCE.md](./MUTATION_OPERATOR_REFERENCE.md)
4. **Performance Tuning**: [PERFORMANCE_TUNING_GUIDE.md](./PERFORMANCE_TUNING_GUIDE.md)
5. **Troubleshooting**: [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)

---

## Support

For questions or issues:
- Check [Troubleshooting Guide](./TROUBLESHOOTING_GUIDE.md)
- Review [API Reference](./FACTOR_GRAPH_API_REFERENCE.md)
- See examples in `tests/integration/`

---

**Version**: 2.0+ (Production Ready)
**Last Updated**: 2025-10-23
**Spec**: structural-mutation-phase2
