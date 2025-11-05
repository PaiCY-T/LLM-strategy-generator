"""
Tier 3 AST Mutation Module

Advanced structural mutations using AST (Abstract Syntax Tree) transformations
for factor logic modification. Enables breakthrough innovations beyond parameter
tuning by modifying code structure.

Architecture: Phase 2.0+ Factor Graph System
Task: D.3 - AST-Based Factor Logic Mutation

Capabilities:
------------
1. Factor Logic Mutation: Modify factor logic at AST level
2. Signal Combination: Create composite factors from multiple signals
3. Adaptive Parameters: Dynamic parameter adjustment factors
4. Safety Validation: AST correctness and security checks

Mutation Tiers:
--------------
- Tier 1 (YAML): Safe parameter configuration
- Tier 2 (Domain): Factor-level operations (add/remove/replace/mutate)
- Tier 3 (AST): Advanced structural code mutations (THIS TIER)

Example Usage:
-------------
```python
from src.mutation.tier3 import ASTFactorMutator, SignalCombiner

# Mutate factor logic
mutator = ASTFactorMutator()
mutated_factor = mutator.mutate(
    factor=rsi_factor,
    config={"operation": "adjust_threshold", "value": 75}
)

# Combine signals
combiner = SignalCombiner()
composite_factor = combiner.combine_and(
    factor1=rsi_factor,
    factor2=macd_factor
)
```

Components:
----------
- ASTFactorMutator: Main AST mutation orchestrator
- SignalCombiner: Composite signal creation
- AdaptiveParameterMutator: Dynamic parameter factors
- ASTValidator: Safety and correctness validation
"""

from .ast_factor_mutator import ASTFactorMutator
from .signal_combiner import SignalCombiner
from .adaptive_parameter_mutator import AdaptiveParameterMutator
from .ast_validator import ASTValidator, ValidationResult

__all__ = [
    "ASTFactorMutator",
    "SignalCombiner",
    "AdaptiveParameterMutator",
    "ASTValidator",
    "ValidationResult",
]
