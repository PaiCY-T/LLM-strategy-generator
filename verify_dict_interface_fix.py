"""Quick verification that Phase 3.3 dict interface fix works end-to-end.

This script tests the critical code paths that were failing in Phase 7:
1. Champion tracker comparison using .get()
2. Prompt builder success factor extraction using .get()
3. Metrics serialization/deserialization with from_dict()/to_dict()
"""

from src.backtest.metrics import StrategyMetrics
from src.learning.champion_tracker import ChampionStrategy
from src.constants import METRIC_SHARPE, METRIC_DRAWDOWN

print("=" * 70)
print("Phase 3.3 Dict Interface Compatibility Verification")
print("=" * 70)

# Test 1: Dict-like .get() access (champion_tracker.py pattern)
print("\n[Test 1] Champion tracker .get() pattern")
metrics = StrategyMetrics(sharpe_ratio=1.5, max_drawdown=-0.12)
champion_sharpe = metrics.get(METRIC_SHARPE, 0)
champion_dd = metrics.get(METRIC_DRAWDOWN, 1.0)
print(f"  ✓ metrics.get(METRIC_SHARPE, 0) = {champion_sharpe}")
print(f"  ✓ metrics.get(METRIC_DRAWDOWN, 1.0) = {champion_dd}")
assert champion_sharpe == 1.5
assert champion_dd == -0.12
print("  ✓ PASS: Dict-like .get() works with constants")

# Test 2: Empty metrics with defaults (prompt_builder.py pattern)
print("\n[Test 2] Prompt builder empty metrics pattern")
empty_metrics = StrategyMetrics()
sharpe = empty_metrics.get('sharpe_ratio', 0)
mdd = empty_metrics.get('max_drawdown', 1.0)
win_rate = empty_metrics.get('win_rate', 0)
print(f"  ✓ empty_metrics.get('sharpe_ratio', 0) = {sharpe}")
print(f"  ✓ empty_metrics.get('max_drawdown', 1.0) = {mdd}")
print(f"  ✓ empty_metrics.get('win_rate', 0) = {win_rate}")
assert sharpe == 0
assert mdd == 1.0
assert win_rate == 0
print("  ✓ PASS: Empty metrics return defaults")

# Test 3: Bracket access
print("\n[Test 3] Bracket access pattern")
metrics = StrategyMetrics(sharpe_ratio=2.0, win_rate=0.65)
print(f"  ✓ metrics['sharpe_ratio'] = {metrics['sharpe_ratio']}")
print(f"  ✓ metrics['win_rate'] = {metrics['win_rate']}")
assert metrics['sharpe_ratio'] == 2.0
assert metrics['win_rate'] == 0.65
print("  ✓ PASS: Bracket access works")

# Test 4: Membership testing
print("\n[Test 4] Membership testing pattern")
metrics = StrategyMetrics()
assert 'sharpe_ratio' in metrics
assert 'nonexistent' not in metrics
print("  ✓ 'sharpe_ratio' in metrics = True")
print("  ✓ 'nonexistent' in metrics = False")
print("  ✓ PASS: Membership testing works")

# Test 5: ChampionStrategy serialization roundtrip
print("\n[Test 5] ChampionStrategy serialization roundtrip")
original = ChampionStrategy(
    iteration_num=10,
    code="# strategy",
    metrics=StrategyMetrics(sharpe_ratio=1.8, max_drawdown=-0.1),
    timestamp='2025-11-13T10:00:00'
)
data = original.to_dict()
restored = ChampionStrategy.from_dict(data)
print(f"  ✓ Original metrics type: {type(original.metrics).__name__}")
print(f"  ✓ Restored metrics type: {type(restored.metrics).__name__}")
print(f"  ✓ Sharpe ratio matches: {restored.metrics.sharpe_ratio == 1.8}")
assert isinstance(restored.metrics, StrategyMetrics)
assert restored.metrics.sharpe_ratio == 1.8
assert restored.metrics.max_drawdown == -0.1
print("  ✓ PASS: Serialization preserves StrategyMetrics type")

# Test 6: Legacy dict metrics auto-conversion
print("\n[Test 6] Legacy dict metrics auto-conversion")
champion_with_dict = ChampionStrategy(
    iteration_num=5,
    code="# old",
    metrics={'sharpe_ratio': 2.5, 'max_drawdown': -0.15},
    timestamp='2025-11-13T09:00:00'
)
print(f"  ✓ Metrics type after __post_init__: {type(champion_with_dict.metrics).__name__}")
print(f"  ✓ Can use .get(): {champion_with_dict.metrics.get('sharpe_ratio', 0)}")
assert isinstance(champion_with_dict.metrics, StrategyMetrics)
assert champion_with_dict.metrics.get('sharpe_ratio', 0) == 2.5
print("  ✓ PASS: Legacy dict auto-converts to StrategyMetrics")

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - Phase 3.3 dict interface fix is working!")
print("=" * 70)
print("\nKey compatibility features verified:")
print("  • Dict-like .get() method with defaults")
print("  • Bracket notation access")
print("  • Membership testing ('in' operator)")
print("  • Serialization/deserialization preserves types")
print("  • Legacy dict metrics auto-convert to StrategyMetrics")
print("  • Empty metrics return defaults (not None)")
