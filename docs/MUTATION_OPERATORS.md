# Factor Mutation Operators

## Overview

The Factor Graph system provides Tier 2 structural mutations for evolving trading strategies through factor-level operations. Mutation operators enable the evolutionary algorithm to modify strategies by adding, removing, or replacing factors.

**Architecture**: Phase 2.0+ Factor Graph System
**Task**: C.1 - add_factor() Mutation Operator
**Module**: `src.factor_graph.mutations`

## Mutation Operators

### 1. add_factor()

Intelligently add factors to strategies with automatic dependency resolution.

```python
from src.factor_graph.mutations import add_factor
from src.factor_library.registry import FactorRegistry

# Get existing strategy
strategy = load_momentum_strategy()

# Add trailing stop exit factor
mutated = add_factor(
    strategy=strategy,
    factor_name="trailing_stop_factor",
    parameters={"trail_percent": 0.10, "activation_profit": 0.05},
    insert_point="leaf"  # Add at end of DAG
)

# Validate and use
mutated.validate()
result = mutated.to_pipeline(data)
```

**Parameters**:
- `strategy`: Strategy to mutate (original not modified)
- `factor_name`: Factor name from registry (e.g., "momentum_factor")
- `parameters`: Factor parameters (uses registry defaults if not provided)
- `insert_point`: Where to insert factor:
  - `"root"`: Add with no dependencies (root factor)
  - `"leaf"`: Add at end (depends on all leaf factors)
  - `"smart"`: Auto-determine optimal location (default)
  - `<factor_id>`: Add after specified factor

**Returns**: New Strategy with factor added (pure function)

### 2. remove_factor()

Safely remove factors with dependency checking and optional cascade.

```python
from src.factor_graph.mutations import remove_factor

# Safe removal (fails if dependents exist)
mutated = remove_factor(
    strategy=strategy,
    factor_id="old_exit_factor",
    cascade=False  # Default: safe mode
)

# Cascade removal (removes dependents recursively)
mutated = remove_factor(
    strategy=strategy,
    factor_id="old_momentum_factor",
    cascade=True  # Remove entire subtree
)
```

**Parameters**:
- `strategy`: Strategy to mutate (original not modified)
- `factor_id`: ID of factor to remove
- `cascade`: If True, also remove dependent factors; if False, raise error if dependents exist (default: False)

**Returns**: New Strategy with factor removed (pure function)

**Behavior**:
- **Safe Mode** (cascade=False): Only removes factors with no dependents
- **Cascade Mode** (cascade=True): Removes factor and all transitive dependents
- **Position Signal Protection**: Cannot remove only position signal producer

### 3. replace_factor()

Replace factor with compatible alternative while preserving DAG structure.

```python
from src.factor_graph.mutations import replace_factor

# Replace momentum factor with MA filter (same category)
mutated = replace_factor(
    strategy=strategy,
    old_factor_id="momentum_20",
    new_factor_name="ma_filter_factor",
    parameters={"ma_periods": 60},
    match_category=True  # Ensure both are MOMENTUM (default)
)

# Replace exit strategy
mutated = replace_factor(
    strategy=strategy,
    old_factor_id="profit_target",
    new_factor_name="trailing_stop_factor",
    parameters={"trail_percent": 0.10, "activation_profit": 0.05},
    match_category=True  # Ensure both are EXIT (default)
)
```

**Parameters**:
- `strategy`: Strategy to mutate (original not modified)
- `old_factor_id`: ID of factor to replace
- `new_factor_name`: Name of replacement factor from registry
- `parameters`: Parameters for new factor (uses defaults if None)
- `match_category`: If True, validate new factor is same category as old (default: True)

**Returns**: New Strategy with factor replaced (pure function)

**Replacement Modes**:

1. **Same-Category Replacement** (match_category=True, default):
   - Ensures semantic consistency
   - Only allows factors from same category
   - Reduces invalid mutations
   - Example: Replace MomentumFactor with MAFilterFactor (both MOMENTUM)

2. **Compatible Replacement** (match_category=False):
   - More flexible mutations
   - Allows any factor with compatible inputs/outputs
   - Useful for exploratory evolution
   - Example: Replace any factor if inputs/outputs match

**Compatibility Validation**:

- **Input Compatibility**: New factor's inputs must be available from base data or predecessor outputs
- **Output Compatibility**: New factor must provide all outputs needed by dependent factors
- **Dependency Preservation**: All incoming and outgoing edges maintained
- **Strategy Validation**: Resulting strategy must pass all validation checks

**Common Replacements by Category**:

| Category | Replacements |
|----------|--------------|
| MOMENTUM | MomentumFactor ↔ MAFilterFactor ↔ DualMAFilterFactor |
| EXIT | TrailingStopFactor ↔ ProfitTargetFactor ↔ VolatilityStopFactor ↔ TimeBasedExitFactor |
| RISK | ATRFactor ↔ VolatilityFactor |
| ENTRY | BreakoutFactor ↔ other entry signals |

**Example - Evolutionary Strategy Replacement**:

```python
from src.factor_graph.mutations import replace_factor
from src.factor_library.registry import FactorRegistry

registry = FactorRegistry.get_instance()

# Get same-category alternatives for a factor
old_factor = strategy.factors["momentum_20"]
same_category_factors = registry.list_by_category(old_factor.category)

# Replace with alternative from same category
for alternative in same_category_factors:
    if alternative != "momentum_factor":  # Don't replace with same
        try:
            mutated = replace_factor(
                strategy=strategy,
                old_factor_id="momentum_20",
                new_factor_name=alternative,
                match_category=True
            )
            # Evaluate fitness of mutated strategy
            fitness = evaluate_strategy(mutated, data)
            if fitness > best_fitness:
                best_strategy = mutated
        except ValueError as e:
            # Handle incompatible replacements
            continue
```

## Insertion Strategies

### Root Insertion

Add factor with no dependencies (uses only base OHLCV data).

```python
mutated = add_factor(
    strategy=strategy,
    factor_name="momentum_factor",
    parameters={"momentum_period": 20},
    insert_point="root"
)
```

**Use cases**:
- Adding independent indicators
- New data sources
- Parallel feature calculation

### After-Factor Insertion

Add factor after specific existing factor.

```python
mutated = add_factor(
    strategy=strategy,
    factor_name="ma_filter_factor",
    parameters={"ma_periods": 60},
    insert_point="momentum_20"  # Existing factor ID
)
```

**Use cases**:
- Building factor chains
- Sequential transformations
- Explicit dependencies

### Leaf Insertion

Add factor at end of DAG (depends on all leaf factors).

```python
mutated = add_factor(
    strategy=strategy,
    factor_name="trailing_stop_factor",
    parameters={"trail_percent": 0.10},
    insert_point="leaf"
)
```

**Use cases**:
- Exit factors
- Final aggregations
- Signal combinations

### Smart Insertion

Auto-determine optimal location based on factor category and inputs.

```python
mutated = add_factor(
    strategy=strategy,
    factor_name="atr_factor",
    parameters={"atr_period": 20},
    insert_point="smart"  # or omit (default)
)
```

**Category-aware positioning**:
- **ENTRY** factors → early in pipeline (near roots)
- **MOMENTUM/VALUE/QUALITY** → middle layers
- **EXIT** factors → late in pipeline (near leaves)
- **RISK** factors → mid-to-late (after positions available)
- **SIGNAL** factors → final aggregation layers

## Factor Registry Integration

All mutations use the Factor Registry for factor creation and validation.

### Available Factors

**Momentum Factors** (4):
- `momentum_factor`: Price momentum using rolling mean of returns
- `ma_filter_factor`: Moving average filter for trend confirmation
- `revenue_catalyst_factor`: Revenue acceleration catalyst detection
- `earnings_catalyst_factor`: Earnings momentum catalyst (ROE improvement)

**Turtle Factors** (4):
- `atr_factor`: Average True Range calculation
- `breakout_factor`: N-day high/low breakout detection
- `dual_ma_filter_factor`: Dual moving average filter
- `atr_stop_loss_factor`: ATR-based stop loss calculation

**Exit Factors** (5):
- `trailing_stop_factor`: Trailing stop loss that follows price
- `time_based_exit_factor`: Exit positions after N periods
- `volatility_stop_factor`: Volatility-based stop using standard deviation
- `profit_target_factor`: Fixed profit target exit
- `composite_exit_factor`: Combines multiple exit signals

### Using Registry

```python
from src.factor_library.registry import FactorRegistry

registry = FactorRegistry.get_instance()

# Discover factors by category
momentum_factors = registry.list_by_category(FactorCategory.MOMENTUM)
exit_factors = registry.list_by_category(FactorCategory.EXIT)

# Get factor metadata
metadata = registry.get_metadata("momentum_factor")
print(f"Default parameters: {metadata['parameters']}")
print(f"Valid ranges: {metadata['parameter_ranges']}")

# Create factor directly (without mutation)
factor = registry.create_factor(
    "momentum_factor",
    parameters={"momentum_period": 30}
)
```

## Validation

Mutations automatically validate:
1. Factor exists in registry
2. Parameters within valid ranges
3. Dependencies satisfied
4. No cycles created
5. Strategy remains valid

**Example validation**:
```python
try:
    mutated = add_factor(
        strategy=strategy,
        factor_name="momentum_factor",
        parameters={"momentum_period": 1000},  # Out of range!
        insert_point="root"
    )
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Evolution Integration

Mutation operators are designed for evolutionary algorithms:

```python
def evolve_strategy(parent_strategy, registry):
    """Evolutionary mutation example."""
    # Randomly select mutation
    mutation_type = random.choice(["add", "remove", "replace"])

    if mutation_type == "add":
        # Add random factor from registry
        factor_name = random.choice(registry.list_factors())
        mutated = add_factor(
            strategy=parent_strategy,
            factor_name=factor_name,
            insert_point="smart"
        )

    elif mutation_type == "remove":
        # Remove random leaf factor
        leaf_factors = _get_leaf_factors(parent_strategy)
        if leaf_factors:
            mutated = remove_factor(
                strategy=parent_strategy,
                factor_id=random.choice(leaf_factors)
            )

    else:  # replace
        # Replace random factor with same-category alternative
        old_factor = random.choice(list(parent_strategy.factors.values()))
        same_category = registry.list_by_category(old_factor.category)
        new_name = random.choice(same_category)

        mutated = replace_factor(
            strategy=parent_strategy,
            old_factor_id=old_factor.id,
            new_factor_name=new_name
        )

    return mutated
```

## Best Practices

1. **Use smart insertion** when unsure about dependencies
2. **Validate strategies** after mutations before fitness evaluation
3. **Check factor IDs** - they include parameters (e.g., `momentum_20` not `momentum_factor`)
4. **Preserve originals** - mutations return new strategies (pure functions)
5. **Leverage categories** - use same-category replacements for meaningful mutations
6. **Test incremental** - add one factor at a time, validate, then continue

## Performance

- Typical add_factor operation: <10ms
- Dependency resolution: O(n) where n = number of factors
- Validation overhead: ~1ms per factor
- No performance degradation with strategy size (up to 100 factors tested)

## Error Handling

Common errors and solutions:

**Factor not found**:
```python
ValueError: Factor 'nonexistent' not found in registry
# Solution: Check available factors with registry.list_factors()
```

**Invalid parameters**:
```python
ValueError: Invalid parameters for 'momentum_factor':
    Parameter 'momentum_period' value 1 out of range [5, 100]
# Solution: Check valid ranges with registry.get_metadata()
```

**Missing inputs**:
```python
ValueError: Cannot add factor 'exit_factor':
    required inputs ['entry_price'] are not available
# Solution: Add factors that provide required inputs first
```

**Orphaned dependents**:
```python
ValueError: Cannot remove factor 'momentum_20':
    factors ['entry_signal'] depend on its outputs
# Solution: Remove dependent factors first
```

## See Also

- [Factor Registry Documentation](../src/factor_library/registry.py)
- [Strategy DAG Documentation](../src/factor_graph/strategy.py)
- [Factor Categories](../src/factor_graph/factor_category.py)
- [Test Examples](../tests/factor_graph/test_mutations_core.py)
