# Exit Mutation API Reference

**Version**: 1.0
**Date**: 2025-10-20
**Target Audience**: Developers, ML Engineers

---

## Overview

The Exit Mutation framework provides AST-based mutation operators for modifying exit strategies in trading algorithms. The framework consists of four main components:

1. **ExitMutationOperator** - Unified interface for exit strategy mutations
2. **ExitMechanismDetector** - AST-based exit pattern detection
3. **ExitStrategyMutator** - 3-tier mutation engine
4. **ExitCodeValidator** - 3-layer validation pipeline

---

## ExitMutationOperator

**File**: `src/mutation/exit_mutation_operator.py`

### Constructor

```python
def __init__(self, max_retries: int = 3):
    """
    Initialize operator with component instances.

    Args:
        max_retries: Maximum mutation attempts if validation fails (default: 3)
    """
```

**Example**:
```python
from src.mutation.exit_mutation_operator import ExitMutationOperator

operator = ExitMutationOperator(max_retries=3)
```

### Primary Method: mutate_exit_strategy()

```python
def mutate_exit_strategy(
    self,
    code: str,
    config: Optional[MutationConfig] = None
) -> MutationResult:
    """
    Apply mutation to exit strategy code with validation and retry.

    Pipeline:
    1. Detect current exit strategy profile
    2. Apply mutation to AST
    3. Generate new Python code
    4. Validate mutated code
    5. Retry with different mutation if validation fails (max N attempts)

    Args:
        code: Original Python source code with exit strategies
        config: Mutation configuration (uses default if None)

    Returns:
        MutationResult with success status, code, and validation details
    """
```

**Example**:
```python
strategy_code = '''
def strategy(data):
    position = entry_signal(data)
    
    # Exit mechanisms
    stop_loss_pct = -0.05
    take_profit_pct = 0.10
    
    position = apply_stop_loss(position, stop_loss_pct)
    position = apply_take_profit(position, take_profit_pct)
    
    return position
'''

result = operator.mutate_exit_strategy(code=strategy_code)

if result.success:
    print(f"Mutation successful: {result.mutation_type}")
    print(f"Mutated code:\n{result.mutated_code}")
else:
    print(f"Mutation failed: {result.validation_details.errors}")
```

---

## MutationResult

**Dataclass**: Return type for mutation operations

```python
@dataclass
class MutationResult:
    success: bool                       # Mutation succeeded
    mutated_code: str                   # Mutated Python code
    mutation_type: str                  # "parametric", "structural", "relational"
    original_profile: ExitProfile       # Original exit mechanism profile
    mutated_profile: ExitProfile        # Mutated exit mechanism profile
    validation_details: ValidationResult # Validation pipeline results
    attempts: int                       # Number of mutation attempts
```

**Example**:
```python
result = operator.mutate_exit_strategy(code)

print(f"Success: {result.success}")
print(f"Type: {result.mutation_type}")
print(f"Attempts: {result.attempts}")
print(f"Original stops: {result.original_profile.stops}")
print(f"Mutated stops: {result.mutated_profile.stops}")
print(f"Validation: {result.validation_details.passed}")
```

---

## MutationConfig

**Dataclass**: Configuration for mutation behavior

```python
@dataclass
class MutationConfig:
    tier1_weight: float = 0.5           # Parametric mutations (50%)
    tier2_weight: float = 0.3           # Structural mutations (30%)
    tier3_weight: float = 0.2           # Relational mutations (20%)
    
    # Parameter mutation ranges
    stop_loss_range: Tuple[float, float] = (0.8, 1.2)    # ±20%
    take_profit_range: Tuple[float, float] = (0.9, 1.3)  # +30%
    trailing_range: Tuple[float, float] = (0.85, 1.25)   # ±25%
```

**Example**:
```python
from src.mutation.exit_mutation_operator import MutationConfig

# Custom configuration
config = MutationConfig(
    tier1_weight=0.7,  # Prefer parametric mutations
    tier2_weight=0.2,
    tier3_weight=0.1,
    stop_loss_range=(0.9, 1.1)  # Tighter range
)

result = operator.mutate_exit_strategy(code, config=config)
```

---

## ExitProfile

**Dataclass**: Exit mechanism profile

```python
@dataclass
class ExitProfile:
    stops: List[str]                    # Stop-loss mechanisms
    profits: List[str]                  # Take-profit mechanisms
    trailing: List[str]                 # Trailing stop mechanisms
    dynamic: List[str]                  # Dynamic exit mechanisms
    parameters: Dict[str, Any]          # Exit parameters (thresholds, etc.)
```

**Example**:
```python
profile = result.original_profile

print(f"Stops: {profile.stops}")        # ['stop_loss_pct']
print(f"Profits: {profile.profits}")    # ['take_profit_pct']
print(f"Trailing: {profile.trailing}")  # ['trailing_stop_pct']
print(f"Parameters: {profile.parameters}")  # {'stop_loss_pct': -0.05, ...}
```

---

## ValidationResult

**Dataclass**: Validation pipeline results

```python
@dataclass
class ValidationResult:
    passed: bool                        # Overall validation passed
    syntax_valid: bool                  # Syntax check passed
    semantics_valid: bool               # Semantics check passed
    types_valid: bool                   # Type check passed
    errors: List[str]                   # Validation error messages
    warnings: List[str]                 # Validation warnings
```

**Example**:
```python
validation = result.validation_details

if not validation.passed:
    print("Validation failed:")
    for error in validation.errors:
        print(f"  - {error}")
        
if validation.warnings:
    print("Warnings:")
    for warning in validation.warnings:
        print(f"  - {warning}")
```

---

## PopulationManager Integration

**File**: `src/evolution/population_manager.py`

### Method: apply_exit_mutation()

```python
def apply_exit_mutation(
    self,
    strategy_code: str,
    strategy_id: str
) -> Tuple[str, bool]:
    """
    Apply exit mutation to strategy code.

    Args:
        strategy_code: Original strategy code
        strategy_id: Strategy identifier for logging

    Returns:
        (mutated_code, success): Tuple of mutated code and success flag
    """
```

**Example**:
```python
from src.evolution.population_manager import PopulationManager

manager = PopulationManager(config_path="config/learning_system.yaml")

mutated_code, success = manager.apply_exit_mutation(
    strategy_code=original_code,
    strategy_id="strategy_001"
)

if success:
    print(f"Mutation applied successfully")
    print(f"Attempts: {manager.exit_mutation_attempts}")
    print(f"Successes: {manager.exit_mutation_successes}")
```

### Statistics Attributes

```python
# Mutation statistics (tracked automatically)
manager.exit_mutation_attempts: int      # Total attempts
manager.exit_mutation_successes: int     # Successful mutations
manager.exit_mutation_failures: int      # Failed mutations
manager.mutation_type_counts: Dict[str, int]  # Distribution by type
```

**Example**:
```python
# Check statistics
print(f"Attempts: {manager.exit_mutation_attempts}")
print(f"Success Rate: {manager.exit_mutation_successes / manager.exit_mutation_attempts:.1%}")
print(f"Type Distribution: {manager.mutation_type_counts}")
```

---

## Mutation Types

### Tier 1: Parametric Mutations (50% default)

**Description**: Adjust numeric thresholds while preserving structure

**Examples**:
- `stop_loss_pct = -0.05` → `stop_loss_pct = -0.06`
- `take_profit_pct = 0.10` → `take_profit_pct = 0.12`
- `trailing_stop_pct = 0.03` → `trailing_stop_pct = 0.035`

**Characteristics**:
- Safest mutations (preserves code structure)
- Highest frequency (50% default weight)
- Fastest to validate
- Smallest impact on strategy behavior

### Tier 2: Structural Mutations (30% default)

**Description**: Change exit mechanism type or structure

**Examples**:
- Fixed stop-loss → Trailing stop
- Simple take-profit → ATR-based dynamic exit
- Single condition → Multi-condition exit

**Characteristics**:
- Moderate risk (changes code structure)
- Medium frequency (30% default weight)
- Requires more validation
- Significant impact on strategy behavior

### Tier 3: Relational Mutations (20% default)

**Description**: Modify logical operators and conditions

**Examples**:
- `if close < stop_loss` → `if close <= stop_loss`
- `if (condition1 and condition2)` → `if (condition1 or condition2)`
- Add/remove exit criteria

**Characteristics**:
- Highest risk (changes logic)
- Lowest frequency (20% default weight)
- Most validation required
- Largest impact on strategy behavior

---

## Error Handling

### Common Errors

**1. Validation Failure**
```python
result = operator.mutate_exit_strategy(code)

if not result.success:
    if not result.validation_details.syntax_valid:
        print("Syntax error in mutated code")
    elif not result.validation_details.semantics_valid:
        print("Semantic error (invalid AST)")
    elif not result.validation_details.types_valid:
        print("Type error in mutated code")
```

**2. No Exit Mechanisms Detected**
```python
try:
    result = operator.mutate_exit_strategy(code)
except ValueError as e:
    if "No exit mechanisms detected" in str(e):
        print("Strategy has no exit mechanisms to mutate")
```

**3. Max Retries Exceeded**
```python
result = operator.mutate_exit_strategy(code)

if not result.success and result.attempts >= operator.max_retries:
    print(f"Failed after {result.attempts} attempts")
    print(f"Last error: {result.validation_details.errors[-1]}")
```

---

## Best Practices

### 1. Use Default Configuration First

```python
# Start with defaults
operator = ExitMutationOperator()
result = operator.mutate_exit_strategy(code)

# Adjust if needed
if result.success:
    # Defaults work well
    pass
else:
    # Try custom config
    config = MutationConfig(tier1_weight=0.7)
    result = operator.mutate_exit_strategy(code, config)
```

### 2. Check Validation Details

```python
result = operator.mutate_exit_strategy(code)

if not result.success:
    # Review validation details
    print("Validation Errors:")
    for error in result.validation_details.errors:
        print(f"  - {error}")
        
    # Adjust code or configuration
```

### 3. Monitor Success Rate

```python
# Track mutations over time
total = manager.exit_mutation_attempts
successes = manager.exit_mutation_successes
success_rate = successes / total if total > 0 else 0

if success_rate < 0.8:
    print(f"Low success rate: {success_rate:.1%}")
    print("Consider:")
    print("  - Reviewing strategy code structure")
    print("  - Adjusting mutation configuration")
    print("  - Increasing max_retries")
```

### 4. Log Mutations

```python
import logging

logging.basicConfig(level=logging.INFO)

result = operator.mutate_exit_strategy(code)

if result.success:
    logging.info(f"Mutation successful: {result.mutation_type}")
    logging.info(f"Attempts: {result.attempts}")
else:
    logging.warning(f"Mutation failed after {result.attempts} attempts")
    logging.warning(f"Errors: {result.validation_details.errors}")
```

---

## Integration Examples

### Example 1: Basic Integration

```python
from src.mutation.exit_mutation_operator import ExitMutationOperator

# Initialize operator
operator = ExitMutationOperator(max_retries=3)

# Define strategy code
strategy_code = '''
def strategy(data):
    close = data.get('close')
    
    # Entry signal
    position = entry_logic(close)
    
    # Exit mechanisms
    stop_loss_pct = -0.05
    take_profit_pct = 0.10
    
    position = apply_stop_loss(position, close, stop_loss_pct)
    position = apply_take_profit(position, close, take_profit_pct)
    
    return position
'''

# Apply mutation
result = operator.mutate_exit_strategy(code=strategy_code)

# Handle result
if result.success:
    print("Mutation successful!")
    print(f"Type: {result.mutation_type}")
    print(f"Attempts: {result.attempts}")
    # Use mutated code
    new_strategy_code = result.mutated_code
else:
    print("Mutation failed")
    print(f"Errors: {result.validation_details.errors}")
```

### Example 2: Custom Configuration

```python
from src.mutation.exit_mutation_operator import (
    ExitMutationOperator,
    MutationConfig
)

# Create custom configuration
config = MutationConfig(
    tier1_weight=0.6,  # Prefer parametric
    tier2_weight=0.3,
    tier3_weight=0.1,
    stop_loss_range=(0.9, 1.1),  # Tighter range
    take_profit_range=(0.95, 1.2)
)

# Initialize operator
operator = ExitMutationOperator(max_retries=5)

# Apply mutation with custom config
result = operator.mutate_exit_strategy(
    code=strategy_code,
    config=config
)
```

### Example 3: PopulationManager Integration

```python
from src.evolution.population_manager import PopulationManager

# Initialize manager with config
manager = PopulationManager(
    config_path="config/learning_system.yaml"
)

# Apply exit mutation during evolution
for generation in range(num_generations):
    for strategy in population:
        # Apply exit mutation with 30% probability
        if should_apply_exit_mutation():
            mutated_code, success = manager.apply_exit_mutation(
                strategy_code=strategy.code,
                strategy_id=strategy.id
            )
            
            if success:
                strategy.code = mutated_code
                
# Review statistics
print(f"Total mutations: {manager.exit_mutation_attempts}")
print(f"Success rate: {manager.exit_mutation_successes / manager.exit_mutation_attempts:.1%}")
print(f"Type distribution: {manager.mutation_type_counts}")
```

---

## Performance Considerations

### Benchmarks

**Single Mutation**: 1.11ms average (900x faster than 1s target)
**Batch Throughput**: 56,718 mutations/minute
**Memory Usage**: 1.15MB peak (87x under 100MB budget)

### Optimization Tips

1. **Use Default Configuration**: Already optimized for performance
2. **Cache Operator Instance**: Reuse operator across mutations
3. **Monitor Success Rate**: Adjust `max_retries` if needed
4. **Batch Validation**: Validation is already efficient

---

**Last Updated**: 2025-10-20
**Version**: 1.0
**Maintainer**: Development Team
