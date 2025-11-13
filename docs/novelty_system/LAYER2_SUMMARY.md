# Layer 2: Combination Pattern Analyzer - Summary

## Quick Facts

- **Status**: ✅ COMPLETE
- **Weight**: 40% (Highest in 3-layer system)
- **Tests**: 19/19 passing (100%)
- **Performance**: 25,475 strategies/second (2,547x above target)
- **Implementation**: 289 lines of Python
- **Dependencies**: `re`, `logging`, `typing` (standard library only)

## What It Does

Detects novel **factor combination patterns** that go beyond simple Factor Graph templates.

### 4 Detection Dimensions

1. **Cross-Domain** (40%): Combines price, revenue, fundamentals, technical, insider data
2. **Multi-Timeframe** (30%): Uses multiple MA/rolling periods (MA20, MA60, MA200)
3. **Complex Weighting** (15%): Custom factor weights (e.g., `score = a*0.6 + b*0.4`)
4. **Non-Linear** (15%): Ratios, products, differences (e.g., `close/revenue`)

## Example

```python
from src.analysis.novelty.combination_patterns import calculate_combination_complexity

code = """
close = data.get('price:收盤價')
revenue = data.get('monthly_revenue:當月營收')
pe = data.get('fundamental_features:本益比')
ma20 = close.average(20)
ma60 = close.average(60)
ratio = close / revenue
score = ratio * 0.6 + pe * 0.4
"""

score, details = calculate_combination_complexity(code)
print(f"Combination Score: {score:.3f}")
print(f"Domains: {details['domains']}")
print(f"Timeframes: {details['timeframes']}")
```

## Scoring Examples

| Strategy Type | Score | Reason |
|---------------|-------|--------|
| Simple template | 0.37 | Single domain, one timeframe |
| Complex multi-domain | 1.00 | 4 domains, 3 timeframes, weighting, non-linear |
| Champion pattern | 0.90 | 3 domains, 2 timeframes, weighted, ratios |

## Integration

Works seamlessly with Layer 1 (Factor Diversity):

```python
from src.analysis.novelty.factor_diversity import calculate_factor_diversity
from src.analysis.novelty.combination_patterns import calculate_combination_complexity

diversity, _ = calculate_factor_diversity(code)
combination, _ = calculate_combination_complexity(code)

partial_novelty = 0.20 * diversity + 0.40 * combination
# Layer 3 not yet implemented (adds another 0.40)
```

## Files

- **Design**: `docs/novelty_system/combination_patterns_design.md`
- **Implementation**: `src/analysis/novelty/combination_patterns.py`
- **Tests**: `tests/analysis/novelty/test_combination_patterns.py`
- **Status**: `docs/novelty_system/LAYER2_COMPLETION_STATUS.md`

## Next: Layer 3

Layer 3 (Logic Complexity) will detect:
- Conditional branching (if/else)
- Loop complexity
- Nested conditions
- State management

Weight: 40% (same as Layer 2)
