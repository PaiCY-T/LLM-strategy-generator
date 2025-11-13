# Novelty Detection System - Quick Reference

## Overview

3-layer novelty detection system for LLM-evolved trading strategies.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│            NOVELTY DETECTION SYSTEM                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Layer 1: FACTOR DIVERSITY (20% weight)            │
│  ├─ Measures: Factor selection novelty             │
│  ├─ Tests: 23/23 PASSED                            │
│  └─ Performance: 14,628 strategies/sec             │
│                                                     │
│  Layer 2: COMBINATION PATTERNS (50% weight)        │
│  ├─ Measures: Factor combination creativity        │
│  ├─ Tests: 19/19 PASSED                            │
│  └─ Performance: 25,475 strategies/sec             │
│                                                     │
│  Layer 3: LOGIC COMPLEXITY (30% weight)            │
│  ├─ Measures: Control flow complexity              │
│  ├─ Tests: 24/24 PASSED                            │
│  └─ Performance: 2,036 strategies/sec              │
│                                                     │
├─────────────────────────────────────────────────────┤
│  TOTAL: 61/61 tests PASSED                         │
│  STATUS: ✅ ALL LAYERS COMPLETE                    │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### Layer 1: Factor Diversity

```python
from src.analysis.novelty.factor_diversity import calculate_factor_diversity

templates = ["close = data.get('price:收盤價')\nma20 = close.average(20)"]
strategy = "volume = data.get('price:成交股數')\nvol_ma = volume.average(10)"

score, details = calculate_factor_diversity(strategy, templates)
print(f"Factor Diversity: {score:.3f}")
```

### Layer 2: Combination Patterns

```python
from src.analysis.novelty.combination_patterns import calculate_combination_complexity

strategy = "cond = (ma20 > ma60) & (volume > vol_ma) & (close > open)"
score, details = calculate_combination_complexity(strategy)
print(f"Combination Complexity: {score:.3f}")
```

### Layer 3: Logic Complexity

```python
from src.analysis.novelty.logic_complexity import calculate_logic_complexity

strategy = """
def momentum(prices):
    return prices.diff()

if ma20 > ma60:
    if momentum > 0:
        position = 1.0
    else:
        position = 0.5
else:
    position = 0.0
"""

score, details = calculate_logic_complexity(strategy)
print(f"Logic Complexity: {score:.3f}")
```

## Project Structure

```
finlab/
├── src/analysis/novelty/
│   ├── __init__.py
│   ├── factor_diversity.py          # Layer 1
│   ├── combination_patterns.py      # Layer 2
│   └── logic_complexity.py          # Layer 3
│
├── tests/analysis/novelty/
│   ├── test_factor_diversity.py
│   ├── test_factor_diversity_performance.py
│   ├── test_combination_patterns.py
│   ├── test_logic_complexity.py
│   └── test_logic_complexity_performance.py
│
└── docs/novelty_system/
    ├── README.md (this file)
    ├── factor_diversity_design.md
    ├── combination_patterns_design.md
    ├── logic_complexity_design.md
    ├── LAYER1_COMPLETION_REPORT.md
    ├── LAYER2_COMPLETION_REPORT.md
    ├── LAYER3_COMPLETION_REPORT.md
    └── TASK_NOV_003_COMPLETION_SUMMARY.md
```

## Performance Summary

| Layer | Tests | Throughput | Status |
|-------|-------|------------|--------|
| Factor Diversity | 17 | 14,628/sec | ✅ |
| Combination Patterns | 19 | 25,475/sec | ✅ |
| Logic Complexity | 24 | 2,036/sec | ✅ |
| **TOTAL** | **61** | **>2,000/sec** | ✅ |

All layers exceed minimum requirement of 10 strategies/second.

## Test Coverage

### Run All Tests
```bash
python3 -m pytest tests/analysis/novelty/ -v
```

### Run Performance Tests
```bash
python3 -m pytest tests/analysis/novelty/ -k performance -v -s
```

### Run Specific Layer
```bash
python3 -m pytest tests/analysis/novelty/test_logic_complexity.py -v
```

## Documentation

### Design Documents
- **Layer 1**: `docs/novelty_system/factor_diversity_design.md`
- **Layer 2**: `docs/novelty_system/combination_patterns_design.md`
- **Layer 3**: `docs/novelty_system/logic_complexity_design.md`

### Completion Reports
- **Layer 1**: `docs/novelty_system/LAYER1_COMPLETION_REPORT.md`
- **Layer 2**: `docs/novelty_system/LAYER2_COMPLETION_REPORT.md`
- **Layer 3**: `docs/novelty_system/LAYER3_COMPLETION_REPORT.md`

### Task Summaries
- **TASK-NOV-003**: `docs/novelty_system/TASK_NOV_003_COMPLETION_SUMMARY.md`

## Scoring Formula

### Individual Layer Scores
Each layer returns a score in [0.0, 1.0] where:
- **0.0**: Identical to templates
- **0.5**: Moderate novelty
- **1.0**: Maximum novelty

### Combined Novelty Score (Not Yet Implemented)
```
novelty_score = (
    0.20 * factor_diversity +      # Layer 1
    0.50 * combination_patterns +  # Layer 2
    0.30 * logic_complexity        # Layer 3
)
```

## Integration Status

### Completed Layers ✅
- [x] Layer 1: Factor Diversity (20% weight)
- [x] Layer 2: Combination Patterns (50% weight)
- [x] Layer 3: Logic Complexity (30% weight)

### Next Steps
- [ ] 3-layer integration (TASK-NOV-004)
- [ ] End-to-end testing
- [ ] LLM feedback loop integration
- [ ] Production deployment

## Historical Strategy Analysis

Test on real strategies:
```bash
python3 test_historical_strategies_logic.py
```

Results from 6 historical strategies:
- Average complexity: 0.427
- Range: 0.312 - 0.450
- All strategies are template-like (expected behavior)

## Validation Results

### Layer 1 (Factor Diversity)
- Template detection: ✅ Working
- TF-IDF scoring: ✅ Accurate
- Cosine distance: ✅ Reliable
- Performance: ✅ 14,628/sec

### Layer 2 (Combination Patterns)
- Domain counting: ✅ Working
- Timeframe detection: ✅ Accurate
- Weighting patterns: ✅ Detected
- Nonlinear operations: ✅ Counted
- Performance: ✅ 25,475/sec

### Layer 3 (Logic Complexity)
- Branch counting: ✅ Working
- Nesting depth: ✅ Accurate
- Function detection: ✅ Reliable
- Variable tracking: ✅ Counted
- Binary operators (&, |): ✅ Supported
- Performance: ✅ 2,036/sec

## Common Issues

### Import Errors
Ensure you're running from project root:
```bash
cd /mnt/c/Users/jnpi/documents/finlab
python3 -m pytest tests/analysis/novelty/
```

### Performance Issues
All layers are highly optimized (>1000/sec). If seeing slowdowns:
1. Check for large code samples
2. Verify no I/O operations in hot path
3. Profile with `pytest --profile`

### Test Failures
All tests should pass. If failures occur:
1. Check Python version (requires 3.8+)
2. Verify all dependencies installed
3. Check file paths are absolute

## Contact

For questions or issues related to the novelty detection system, refer to:
- Design documents in `docs/novelty_system/`
- Completion reports for detailed implementation notes
- Test files for usage examples

---

**Version**: 1.0
**Last Updated**: 2025-11-07
**Status**: ✅ ALL LAYERS COMPLETE
