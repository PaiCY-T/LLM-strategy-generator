# Troubleshooting Guide - Factor Graph System

**Version**: 2.0+
**Last Updated**: 2025-10-23

---

## Common Errors and Solutions

### 1. Circular Dependency

**Error**: `ValueError: Adding factor X would create cycle`

**Diagnosis**:
```python
import networkx as nx

# Find cycles
cycles = list(nx.simple_cycles(strategy.dag))
if cycles:
    print(f"Cycles found: {cycles}")
```

**Solution**: Remove circular dependencies by restructuring factor DAG.

---

### 2. Missing Inputs

**Error**: `ValueError: Factor 'X' missing inputs: ['col']`

**Diagnosis**:
```python
available = ["open", "high", "low", "close", "volume"]
for factor_id in nx.topological_sort(strategy.dag):
    factor = strategy.factors[factor_id]
    missing = set(factor.inputs) - set(available)
    if missing:
        print(f"{factor_id} missing: {missing}")
    available.extend(factor.outputs)
```

**Solution**: Ensure all required inputs are produced by previous factors.

---

### 3. No Position Signals

**Error**: `ValueError: Strategy does not produce position signals`

**Diagnosis**:
```python
has_positions = any(
    "positions" in f.outputs or "signal" in f.outputs
    for f in strategy.factors.values()
)
print(f"Has position signals: {has_positions}")
```

**Solution**: Add factor that produces "positions" or "signal" output.

---

### 4. Factor Not Found in Registry

**Error**: `ValueError: Factor 'X' not found in registry`

**Diagnosis**:
```python
from src.factor_library.registry import FactorRegistry

registry = FactorRegistry.get_instance()
available = registry.list_factors()
print(f"Available: {available}")
```

**Solution**: Use registered factor name or register custom factor.

---

### 5. Invalid Parameters

**Error**: `ValueError: Invalid parameters for factor 'X': param 'Y' out of range`

**Diagnosis**:
```python
metadata = registry.get_metadata("factor_name")
print(f"Valid parameters: {metadata['parameters']}")
```

**Solution**: Use parameters within valid ranges.

---

### 6. Performance Issues

**Symptom**: Slow strategy execution (>5 minutes)

**Diagnosis**:
```python
import time

for factor_id in nx.topological_sort(strategy.dag):
    start = time.time()
    factor.execute(data)
    print(f"{factor_id}: {time.time() - start:.3f}s")
```

**Solutions**:
- Reduce DAG complexity
- Cache expensive computations
- Use vectorized operations
- See [Performance Tuning Guide](./PERFORMANCE_TUNING_GUIDE.md)

---

### 7. Mutation Failures

**Symptom**: High mutation failure rate (>50%)

**Diagnosis**:
```python
from src.mutation.tier_selection.tier_selection_manager import TierSelectionManager

manager = TierSelectionManager()
risk = manager.assess_risk(strategy)
print(f"Risk score: {risk:.2f}")
```

**Solutions**:
- Use lower risk tier (Tier 1 > Tier 2 > Tier 3)
- Simplify strategy before mutation
- Check mutation logs for specific errors

---

## Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("factor_graph")
logger.setLevel(logging.DEBUG)
```

---

## Getting Help

1. Check error message carefully
2. Review [User Guide](./FACTOR_GRAPH_USER_GUIDE.md)
3. Check [API Reference](./FACTOR_GRAPH_API_REFERENCE.md)
4. Review test examples in `tests/integration/`

---

**Version**: 2.0+ (Production Ready)
**Last Updated**: 2025-10-23
