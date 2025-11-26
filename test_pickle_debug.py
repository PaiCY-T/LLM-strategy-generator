#!/usr/bin/env python3
"""Debug which objects can/cannot be pickled"""

import sys
import pickle
import time

sys.path.insert(0, '.')

from finlab import data, backtest
from src.factor_graph.strategy import Strategy
from src.factor_library.registry import FactorRegistry

def test_pickle(obj, name):
    """Test if an object can be pickled"""
    try:
        start = time.time()
        serialized = pickle.dumps(obj)
        elapsed = time.time() - start
        print(f"✅ {name}: {len(serialized)} bytes in {elapsed:.3f}s")
        return True
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__}: {str(e)[:100]}")
        return False

print("=" * 80)
print("Pickle Compatibility Test")
print("=" * 80)

# Test finlab.data module
print("\n1. finlab.data module:")
test_pickle(data, "data")

# Test finlab.backtest.sim function
print("\n2. finlab.backtest.sim function:")
test_pickle(backtest.sim, "sim")

# Test Strategy object
print("\n3. Empty Strategy object:")
empty_strategy = Strategy(id="test", generation=0)
test_pickle(empty_strategy, "empty_strategy")

# Test Strategy with factors
print("\n4. Strategy with factors:")
registry = FactorRegistry.get_instance()
strategy = Strategy(id="template_test", generation=0)

momentum_factor = registry.create_factor(
    "momentum_factor",
    parameters={"momentum_period": 20}
)
strategy.add_factor(momentum_factor, depends_on=[])

test_pickle(strategy, "strategy_with_factors")

# Test individual factor
print("\n5. Individual momentum_factor:")
test_pickle(momentum_factor, "momentum_factor")

print("\n" + "=" * 80)
