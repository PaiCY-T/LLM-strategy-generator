# Mutation Operator Reference - Factor Graph System

**Version**: 2.0+
**Last Updated**: 2025-10-23

---

## Three-Tier Mutation System

### Tier 1: YAML Configuration (Safe)
- **Risk**: LOW | **Success Rate**: ~80%
- **Use**: LLM-generated strategies, configuration evolution

### Tier 2: Factor Operations (Domain-Specific)  
- **Risk**: MEDIUM | **Success Rate**: ~60%
- **Use**: Structural strategy evolution

### Tier 3: AST Mutations (Advanced)
- **Risk**: HIGH | **Success Rate**: ~50%
- **Use**: Logic-level innovation

---

## Tier 2 Operators

### add_factor()
Add new factor to strategy with dependency validation.

```python
from src.factor_graph.mutations import add_factor

mutated = add_factor(
    strategy=original_strategy,
    new_factor=volatility_filter,
    depends_on=["momentum_20"],
    insert_before="entry_signal"
)
```

### remove_factor()
Remove factor with orphan detection.

```python
from src.factor_graph.mutations import remove_factor

mutated = remove_factor(
    strategy=original_strategy,
    factor_id="old_indicator",
    remove_dependents=False
)
```

### replace_factor()
Swap factor with same-category alternative.

```python
from src.factor_graph.mutations import replace_factor

mutated = replace_factor(
    strategy=original_strategy,
    old_factor_id="momentum_20",
    new_factor_name="ma_filter_factor",
    parameters={"ma_periods": 60},
    match_category=True
)
```

### mutate_parameters()
Gaussian parameter mutation.

```python
from src.factor_graph.mutations import mutate_parameters

mutated = mutate_parameters(
    strategy=original_strategy,
    factor_id="rsi_14",
    mutation_rate=0.1,
    mutation_scale=0.2
)
```

---

## Tier 3 Operators

### AST Logic Modification
```python
from src.mutation.ast_mutations.logic_modifier import ASTFactorMutator

mutator = ASTFactorMutator()
mutated_factor = mutator.mutate_logic(
    factor=original_factor,
    mutation_type="modify_operator",
    target_line=15
)
```

### Signal Combination
```python
combined_factor = mutator.combine_signals(
    factors=[rsi_factor, macd_factor],
    combination_type="and"
)
```

---

## Adaptive Tier Selection

```python
from src.mutation.tier_selection.tier_selection_manager import TierSelectionManager

manager = TierSelectionManager()
risk_score = manager.assess_risk(strategy)
tier = manager.select_tier(strategy, risk_score)

# Tier ranges:
# 0.0-0.3: Tier 1 (YAML)
# 0.3-0.7: Tier 2 (Factor ops)
# 0.7-1.0: Tier 3 (AST)
```

---

**Version**: 2.0+ (Production Ready)
**Last Updated**: 2025-10-23
