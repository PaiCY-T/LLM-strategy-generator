#!/usr/bin/env python3
"""Test direct execution without multiprocessing to isolate the issue"""

import sys
import time

sys.path.insert(0, '.')

from finlab import data, backtest
from src.factor_graph.strategy import Strategy
from src.factor_library.registry import FactorRegistry

def create_template_strategy():
    """Create template Factor Graph strategy"""
    registry = FactorRegistry.get_instance()
    strategy = Strategy(id="template_test", generation=0)

    # Add factors
    momentum_factor = registry.create_factor(
        "momentum_factor",
        parameters={"momentum_period": 20}
    )
    strategy.add_factor(momentum_factor, depends_on=[])

    breakout_factor = registry.create_factor(
        "breakout_factor",
        parameters={"entry_window": 20}
    )
    strategy.add_factor(breakout_factor, depends_on=[])

    trailing_stop_factor = registry.create_factor(
        "rolling_trailing_stop_factor",
        parameters={"trail_percent": 0.10, "lookback_periods": 20}
    )
    strategy.add_factor(
        trailing_stop_factor,
        depends_on=[momentum_factor.id, breakout_factor.id]
    )

    return strategy

print("=" * 80)
print("Direct Execution Test (No Multiprocessing)")
print("=" * 80)

strategy = create_template_strategy()
print(f"✓ Created strategy with {len(strategy.factors)} factors")

# Execute to_pipeline
print("\n1. Executing to_pipeline()...")
pipeline_start = time.time()
positions_df = strategy.to_pipeline(data)
print(f"   ✓ Completed in {time.time() - pipeline_start:.2f}s")
print(f"   Position matrix shape: {positions_df.shape}")

# Filter dates
print("\n2. Filtering dates...")
filter_start = time.time()
positions_df = positions_df.loc["2018-01-01":"2024-12-31"]
print(f"   ✓ Completed in {time.time() - filter_start:.2f}s")
print(f"   Filtered shape: {positions_df.shape}")

# Run sim()
print("\n3. Running backtest.sim()...")
sim_start = time.time()
report = backtest.sim(
    positions_df,
    fee_ratio=0.001425,
    tax_ratio=0.003,
    resample="M"
)
print(f"   ✓ Completed in {time.time() - sim_start:.2f}s")

# Extract metrics
sharpe = report.stats.sharpe if hasattr(report.stats, 'sharpe') else None
print(f"\n✅ Direct execution succeeded!")
print(f"   Sharpe Ratio: {sharpe}")
print("=" * 80)
