# Performance Tuning Guide - Factor Graph System

**Version**: 2.0+
**Last Updated**: 2025-10-23

---

## Performance Targets

- **DAG Compilation**: <1 second
- **Factor Execution**: <5 minutes per strategy
- **Generation Evolution**: <2 hours for N=20, 20 generations
- **Mutation Operation**: <1 second

---

## Optimization Strategies

### 1. DAG Complexity Management

**Problem**: Large DAGs (>20 factors) slow execution

**Solutions**:
- Combine related factors
- Use factor caching
- Parallelize independent factors

```python
# Before: 15 separate factors
for i in range(15):
    strategy.add_factor(indicator_factors[i])

# After: 5 combined factors
strategy.add_factor(combined_indicator)  # Combines 15 into 5
```

### 2. Factor Execution Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def cached_logic(data_hash, params_tuple):
    # Expensive computation
    return result

def factor_logic(data, params):
    data_hash = hash(data.to_string())
    params_tuple = tuple(sorted(params.items()))
    return cached_logic(data_hash, params_tuple)
```

### 3. Vectorization

```python
# ❌ Slow: row-by-row
for i in range(len(data)):
    data.loc[i, 'result'] = data.loc[i, 'close'] > data.loc[i, 'ma']

# ✅ Fast: vectorized
data['result'] = (data['close'] > data['ma']).astype(int)
```

### 4. Parallel Evaluation

```python
from src.population.population_manager_v2 import PopulationManagerV2

manager = PopulationManagerV2(
    population_size=20,
    enable_three_tier=True,
    n_jobs=4  # Parallel evaluation
)
```

### 5. Memory Optimization

```python
# Use appropriate data types
data['positions'] = data['signal'].astype('int8')  # Not int64

# Drop intermediate columns
data = data.drop(columns=['temp_col1', 'temp_col2'])

# Use inplace operations carefully
data['ma'] = data['close'].rolling(window=20).mean()  # Creates copy
```

---

## Profiling Tools

### Execution Time Profiling

```python
import time
import networkx as nx

for factor_id in nx.topological_sort(strategy.dag):
    start = time.time()
    factor = strategy.factors[factor_id]
    result = factor.execute(data)
    elapsed = time.time() - start
    print(f"{factor_id}: {elapsed:.3f}s")
```

### Memory Profiling

```python
import sys

def get_size(obj):
    return sys.getsizeof(obj) / 1024 / 1024  # MB

print(f"Strategy size: {get_size(strategy):.2f} MB")
print(f"Data size: {get_size(data):.2f} MB")
```

---

## Best Practices

1. **Minimize DAG Depth**: Target 3-5 layers
2. **Minimize DAG Width**: Target 5-10 factors per layer
3. **Cache Expensive Computations**: Use @lru_cache
4. **Use Vectorized Operations**: Avoid loops
5. **Profile Before Optimizing**: Measure first

---

**Version**: 2.0+ (Production Ready)
**Last Updated**: 2025-10-23
