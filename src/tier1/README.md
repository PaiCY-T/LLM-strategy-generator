# Tier 1: YAML Configuration Layer

**Status**: ✅ Complete (Task D.1)
**Purpose**: Safe, declarative strategy configuration for LLMs

---

## Quick Start

```python
from src.tier1 import YAMLValidator

# Validate configuration
validator = YAMLValidator()
result = validator.validate_file("my_strategy.yaml")

if result.is_valid:
    print(f"✓ Valid: {result.config['strategy_id']}")
else:
    for error in result.errors:
        print(f"✗ {error}")
```

---

## Minimal Example

```yaml
strategy_id: "simple-momentum-v1"
description: "Simple momentum strategy"

factors:
  - id: "momentum_20"
    type: "momentum_factor"
    parameters:
      momentum_period: 20
    depends_on: []
```

---

## Files

- `yaml_schema.json` - JSON Schema definition (285 lines)
- `yaml_validator.py` - YAMLValidator class (518 lines)
- `__init__.py` - Package exports

---

## Key Features

- ✅ 13 factor types supported
- ✅ Multi-stage validation (schema → rules → parameters)
- ✅ Dependency cycle detection
- ✅ Clear error messages
- ✅ <5ms validation time
- ✅ Support for YAML and JSON

---

## Documentation

See `/docs/YAML_CONFIGURATION_GUIDE.md` for complete documentation (560 lines).

---

## Examples

See `/examples/yaml_strategies/` for 3 working examples:
1. `momentum_basic.yaml` - Simple momentum (3 factors)
2. `turtle_exit_combo.yaml` - Turtle with composite exit (6 factors)
3. `multi_factor_complex.yaml` - Advanced multi-factor (9 factors)

---

## Tests

Run tests: `pytest tests/tier1/ -v`
- 40 test cases
- 100% pass rate
- <2s execution time

---

## Supported Factor Types

| Category | Factors |
|----------|---------|
| Momentum | momentum_factor, ma_filter_factor, dual_ma_filter_factor |
| Value | revenue_catalyst_factor |
| Quality | earnings_catalyst_factor |
| Risk | atr_factor |
| Entry | breakout_factor |
| Exit | trailing_stop_factor, time_based_exit_factor, volatility_stop_factor, profit_target_factor, atr_stop_loss_factor, composite_exit_factor |

---

## Next Steps

**Task D.2**: YAML → Factor Interpreter (safe instantiation from validated configs)
