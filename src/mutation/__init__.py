"""
Exit Strategy Mutation Framework - Phase 1 Implementation.

AST-based mutation system for evolving exit strategies in trading algorithms.

Components:
-----------
- ExitMechanismDetector: Detect exit logic in strategy code
- ExitStrategyMutator: Mutate exit strategies via AST manipulation
- ExitCodeValidator: Validate mutated code for correctness
- ExitMutationOperator: Unified interface for mutation pipeline

Example Usage:
--------------
```python
from src.mutation import ExitMutationOperator, MutationConfig

# Create operator
operator = ExitMutationOperator()

# Configure mutation
config = MutationConfig(seed=42)

# Apply mutation
result = operator.mutate_exit_strategy(original_code, config)

if result.success:
    print(f"Mutation successful: {result.summary()}")
else:
    print(f"Mutation failed: {result.errors}")
```
"""

from src.mutation.exit_detector import ExitMechanismDetector, ExitStrategyProfile
from src.mutation.exit_mutator import ExitStrategyMutator, MutationConfig
from src.mutation.exit_validator import ExitCodeValidator, ValidationResult
from src.mutation.exit_mutation_operator import ExitMutationOperator, MutationResult

__all__ = [
    'ExitMechanismDetector',
    'ExitStrategyProfile',
    'ExitStrategyMutator',
    'MutationConfig',
    'ExitCodeValidator',
    'ValidationResult',
    'ExitMutationOperator',
    'MutationResult',
]
