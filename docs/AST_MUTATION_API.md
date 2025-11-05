# AST Mutation Framework API Reference

**Version**: 1.0
**Module**: `src.mutation.tier3`
**Status**: Production Ready

---

## Overview

The AST Mutation Framework provides Tier 3 (Advanced) mutations for the Factor Graph architecture. It enables structural evolution of trading strategies through:

1. **AST Factor Mutation**: Modify factor logic at code level
2. **Signal Combination**: Create composite factors from multiple signals
3. **Adaptive Parameters**: Dynamic parameter adjustment based on market conditions
4. **Safety Validation**: Prevent unsafe operations

---

## Quick Start

```python
from src.mutation.tier3 import (
    ASTFactorMutator,
    SignalCombiner,
    AdaptiveParameterMutator,
    ASTValidator
)

# Create factor
rsi_factor = create_rsi_factor()

# Mutate logic
mutator = ASTFactorMutator()
mutated = mutator.mutate(rsi_factor, {
    'mutation_type': 'operator_mutation'
})

# Validate safety
validator = ASTValidator()
result = validator.validate(mutator.get_source(mutated))
```

---

## API Reference

### ASTValidator

Validates AST mutations for safety and correctness.

#### `validate(source: str) -> ValidationResult`

Run all validation checks on Python source code.

**Parameters**:
- `source` (str): Python source code to validate

**Returns**:
- `ValidationResult`: Object with `success`, `errors`, `warnings`

**Example**:
```python
validator = ASTValidator()
result = validator.validate(code)

if result.success:
    print("Valid code")
else:
    print(f"Errors: {result.errors}")
```

#### `validate_fast(source: str) -> bool`

Fast syntax-only validation.

**Parameters**:
- `source` (str): Python source code

**Returns**:
- `bool`: True if syntax is valid

**Example**:
```python
if validator.validate_fast(code):
    print("Syntax OK")
```

---

### ASTFactorMutator

Mutate factor logic at AST level.

#### `mutate(factor: Factor, config: Dict[str, Any]) -> Factor`

Apply AST mutation to factor logic.

**Parameters**:
- `factor` (Factor): Factor with logic callable
- `config` (dict): Mutation configuration
  - `mutation_type` (str): Type of mutation
    - `'operator_mutation'`: Change comparison operators
    - `'threshold_adjustment'`: Modify numeric constants
    - `'expression_modification'`: Change calculations
  - `adjustment_factor` (float): For threshold adjustment (default: 1.1)
  - `seed` (int): Random seed for reproducibility
  - `validate` (bool): Validate after mutation (default: True)

**Returns**:
- `Factor`: New factor with mutated logic

**Raises**:
- `ValueError`: If mutation produces invalid code

**Example**:
```python
mutator = ASTFactorMutator()

# Operator mutation
mutated = mutator.mutate(factor, {
    'mutation_type': 'operator_mutation',
    'seed': 42
})

# Threshold adjustment
mutated = mutator.mutate(factor, {
    'mutation_type': 'threshold_adjustment',
    'adjustment_factor': 1.2
})
```

#### `apply_multiple_mutations(factor: Factor, mutations: List[Dict]) -> Factor`

Apply multiple mutations sequentially.

**Parameters**:
- `factor` (Factor): Factor to mutate
- `mutations` (list): List of mutation configs

**Returns**:
- `Factor`: Factor with all mutations applied

**Example**:
```python
mutations = [
    {'mutation_type': 'operator_mutation'},
    {'mutation_type': 'threshold_adjustment', 'adjustment_factor': 1.1}
]
mutated = mutator.apply_multiple_mutations(factor, mutations)
```

#### `mutate_with_rollback(factor: Factor, config: Dict) -> Optional[Factor]`

Apply mutation with automatic rollback on failure.

**Parameters**:
- `factor` (Factor): Factor to mutate
- `config` (dict): Mutation configuration

**Returns**:
- `Factor` or `None`: Mutated factor if successful, None if failed

**Example**:
```python
mutated = mutator.mutate_with_rollback(factor, config)
if mutated:
    print("Mutation successful")
else:
    print("Mutation failed, rolled back")
```

#### `get_source(factor: Factor) -> str`

Extract source code from factor logic.

**Parameters**:
- `factor` (Factor): Factor to extract source from

**Returns**:
- `str`: Source code

**Example**:
```python
source = mutator.get_source(factor)
print(source)
```

---

### SignalCombiner

Create composite factors by combining signals.

#### `combine_and(factor1: Factor, factor2: Factor) -> Factor`

Create AND combination factor.

**Parameters**:
- `factor1` (Factor): First factor
- `factor2` (Factor): Second factor

**Returns**:
- `Factor`: Composite factor with AND logic

**Example**:
```python
combiner = SignalCombiner()
composite = combiner.combine_and(rsi_factor, macd_factor)
```

#### `combine_or(factor1: Factor, factor2: Factor) -> Factor`

Create OR combination factor.

**Parameters**:
- `factor1` (Factor): First factor
- `factor2` (Factor): Second factor

**Returns**:
- `Factor`: Composite factor with OR logic

**Example**:
```python
composite = combiner.combine_or(rsi_factor, macd_factor)
```

#### `combine_weighted(factors: List[Factor], weights: List[float]) -> Factor`

Create weighted combination factor.

**Parameters**:
- `factors` (list): List of factors to combine
- `weights` (list): Corresponding weights (must sum to 1.0)

**Returns**:
- `Factor`: Composite factor with weighted logic

**Raises**:
- `ValueError`: If weights don't sum to ~1.0
- `ValueError`: If factor/weight counts don't match

**Example**:
```python
composite = combiner.combine_weighted(
    [rsi_factor, macd_factor, momentum_factor],
    [0.5, 0.3, 0.2]
)
```

---

### AdaptiveParameterMutator

Create factors with dynamic parameters.

#### `create_volatility_adaptive(base_factor: Factor, param_name: str, volatility_period: int, scale_factor: float) -> Factor`

Make factor parameters adapt to volatility.

**Parameters**:
- `base_factor` (Factor): Original factor
- `param_name` (str): Parameter to adapt (default: first numeric)
- `volatility_period` (int): Period for volatility calculation (default: 20)
- `scale_factor` (float): Scaling factor (default: 1.0)

**Returns**:
- `Factor`: Factor with volatility-adaptive parameter

**Example**:
```python
mutator = AdaptiveParameterMutator()
adaptive = mutator.create_volatility_adaptive(
    base_factor=rsi_factor,
    param_name='overbought',
    volatility_period=20
)
```

#### `create_regime_adaptive(base_factor: Factor, param_name: str, bull_value: float, bear_value: float, regime_period: int) -> Factor`

Make factor parameters adapt to market regime.

**Parameters**:
- `base_factor` (Factor): Original factor
- `param_name` (str): Parameter to adapt
- `bull_value` (float): Value in bull market (default: base * 0.8)
- `bear_value` (float): Value in bear market (default: base * 1.2)
- `regime_period` (int): Period for regime detection (default: 50)

**Returns**:
- `Factor`: Factor with regime-adaptive parameter

**Example**:
```python
adaptive = mutator.create_regime_adaptive(
    base_factor=momentum_factor,
    param_name='period',
    bull_value=14,
    bear_value=30
)
```

#### `create_bounded_adaptive(base_factor: Factor, param_name: str, min_value: float, max_value: float, adaptation_rate: float) -> Factor`

Create factor with bounded adaptive parameter.

**Parameters**:
- `base_factor` (Factor): Original factor
- `param_name` (str): Parameter to adapt
- `min_value` (float): Minimum allowed value
- `max_value` (float): Maximum allowed value
- `adaptation_rate` (float): Rate of adaptation (0-1, default: 0.1)

**Returns**:
- `Factor`: Factor with bounded adaptive parameter

**Raises**:
- `ValueError`: If min >= max
- `ValueError`: If base value outside bounds

**Example**:
```python
adaptive = mutator.create_bounded_adaptive(
    base_factor=rsi_factor,
    param_name='period',
    min_value=10,
    max_value=30,
    adaptation_rate=0.1
)
```

---

## Data Classes

### ValidationResult

Result of AST validation.

**Attributes**:
- `success` (bool): Whether validation passed
- `errors` (List[str]): Error messages
- `warnings` (List[str]): Warning messages

**Methods**:
- `aggregate(results: List[ValidationResult]) -> ValidationResult`: Combine multiple results

**Example**:
```python
result = validator.validate(code)
print(f"Success: {result.success}")
print(f"Errors: {result.errors}")
print(f"Warnings: {result.warnings}")
```

---

## Configuration Examples

### Operator Mutation Config

```python
config = {
    'mutation_type': 'operator_mutation',
    'seed': 42,           # For reproducibility
    'validate': True      # Validate after mutation
}
```

### Threshold Adjustment Config

```python
config = {
    'mutation_type': 'threshold_adjustment',
    'adjustment_factor': 1.15,  # 15% increase
    'validate': True
}
```

### Expression Modification Config

```python
config = {
    'mutation_type': 'expression_modification',
    'seed': 42,
    'validate': True
}
```

---

## Error Handling

### Common Errors

**ValueError: Cannot extract source**
```python
# Cause: Lambda functions not supported
factor.logic = lambda d, p: d  # ✗ Won't work

# Solution: Use regular function
def logic(data, params):
    return data
factor.logic = logic  # ✓ Works
```

**ValueError: Mutation produced invalid code**
```python
# Cause: Mutation created syntax error
# Solution: Use validate=True (default) and handle rollback
mutated = mutator.mutate_with_rollback(factor, config)
if not mutated:
    print("Mutation failed, using original")
    mutated = factor
```

**ValidationResult: Security violation**
```python
# Cause: Forbidden operation detected
# Solution: Fix code to remove unsafe operations
# Check result.errors for specific violations
```

---

## Best Practices

### 1. Always Validate

```python
# ✓ Good: Validate before and after
validator = ASTValidator()
result = validator.validate(mutator.get_source(factor))
if result.success:
    mutated = mutator.mutate(factor, config)
```

### 2. Use Rollback for Robustness

```python
# ✓ Good: Handle failures gracefully
mutated = mutator.mutate_with_rollback(factor, config)
if not mutated:
    # Fall back to original or try different mutation
    pass
```

### 3. Set Random Seeds for Reproducibility

```python
# ✓ Good: Reproducible mutations
config = {'mutation_type': 'operator_mutation', 'seed': 42}
mutated = mutator.mutate(factor, config)
```

### 4. Normalize Weights for Combinations

```python
# ✓ Good: Weights sum to 1.0
weights = [0.6, 0.4]
composite = combiner.combine_weighted(factors, weights)

# ✗ Bad: Weights don't sum to 1.0
weights = [0.6, 0.3]  # Sum = 0.9
# Raises ValueError
```

### 5. Test Adaptive Factors with Representative Data

```python
# ✓ Good: Test with realistic data
adaptive = mutator.create_volatility_adaptive(factor)
test_data = load_historical_data(periods=252)  # 1 year
result = adaptive.execute(test_data)
```

---

## Performance Tips

### 1. Cache Compiled Functions

AST compilation is expensive. Cache compiled functions when possible:

```python
# Cache mutated factors
cache = {}
key = f"{factor.id}_{mutation_type}"
if key not in cache:
    cache[key] = mutator.mutate(factor, config)
mutated = cache[key]
```

### 2. Use Fast Validation for Iteration

```python
# Use fast validation during exploration
if validator.validate_fast(code):
    # Full validation only when needed
    result = validator.validate(code)
```

### 3. Batch Mutations

```python
# Apply multiple mutations in one pass
mutations = [config1, config2, config3]
mutated = mutator.apply_multiple_mutations(factor, mutations)
```

---

## Limitations

### 1. Type Annotations

Mutated code may fail with complex type annotations. Workaround:

```python
# Simplify type hints in original logic
def logic(data, params):  # Simple hints
    period = params.get('period', 14)
    ...
```

### 2. Lambda Functions

Cannot extract source from lambdas:

```python
# ✗ Not supported
factor.logic = lambda d, p: d['close'] > 100

# ✓ Use regular function
def logic(data, params):
    return data['close'] > 100
factor.logic = logic
```

### 3. Adaptive Parameter Constraints

Very small datasets may cause issues:

```python
# Ensure sufficient data
assert len(data) >= volatility_period + 10
```

---

## See Also

- [Factor Graph Architecture](FACTOR_GRAPH.md)
- [Tier 2 Parameter Mutations](PARAMETER_MUTATION.md)
- [Examples](../examples/ast_mutation_examples.py)
- [Tests](../tests/mutation/tier3/test_ast_mutations.py)

---

*Last Updated: 2025-10-23*
*Version: 1.0*
