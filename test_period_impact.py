"""
Quick test to verify if IS period restriction causes lower Sharpe.

This test runs the Phase 1 champion strategy on:
1. IS period only (2015-2020)
2. Full period (all available data)
3. OOS period only (2021-2024)

To verify if data period restriction explains the Sharpe gap.
"""

import finlab
from finlab import data
from src.templates.momentum_template import MomentumTemplate

# Load API token
finlab.login("MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyTXXRbvScfaO#vip_m")

# Phase 1 champion parameters
champion_params = {
    "momentum_period": 20,
    "ma_periods": 120,
    "catalyst_type": "revenue",
    "catalyst_lookback": 2,
    "n_stocks": 10,
    "stop_loss": 0.1,
    "resample": "W",
    "resample_offset": 2
}

template = MomentumTemplate()

print("=" * 70)
print("TESTING PERIOD IMPACT ON SHARPE RATIO")
print("=" * 70)
print(f"\nChampion Strategy: MW{champion_params['momentum_period']}_MA{champion_params['ma_periods']}_"
      f"{champion_params['catalyst_type'][:3]}{champion_params['catalyst_lookback']}_"
      f"N{champion_params['n_stocks']}_SL{int(champion_params['stop_loss']*100)}_"
      f"{champion_params['resample']}{champion_params['resample_offset']}")
print()

# Test 1: Full period (Phase 0 behavior)
print("\n1️⃣  FULL PERIOD (Phase 0 baseline)")
print("-" * 70)
try:
    report_full, metrics_full = template.generate_strategy(champion_params)
    print(f"✅ Sharpe Ratio: {metrics_full.get('sharpe_ratio', 0):.4f}")
    print(f"   Annual Return: {metrics_full.get('annual_return', 0):.2%}")
    print(f"   Max Drawdown: {metrics_full.get('max_drawdown', 0):.2%}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: IS period only (2015-2020) - Phase 1 training data
print("\n2️⃣  IS PERIOD ONLY (2015-2020) - Phase 1 training")
print("-" * 70)
try:
    # Manually filter DataCache like FitnessEvaluator does
    from src.templates.data_cache import DataCache
    cache = DataCache.get_instance()

    KEYS_TO_FILTER = [
        'price:收盤價',
        'price:成交股數',
        'monthly_revenue:當月營收',
        'fundamental_features:ROE綜合損益',
    ]

    # Save original
    original_cache = {}
    for key in KEYS_TO_FILTER:
        if key in cache._cache:
            original_cache[key] = cache._cache[key]

    # Filter to IS period
    for key in KEYS_TO_FILTER:
        if key in cache._cache:
            cache._cache[key] = original_cache[key]['2015':'2020']

    report_is, metrics_is = template.generate_strategy(champion_params)
    print(f"✅ Sharpe Ratio: {metrics_is.get('sharpe_ratio', 0):.4f}")
    print(f"   Annual Return: {metrics_is.get('annual_return', 0):.2%}")
    print(f"   Max Drawdown: {metrics_is.get('max_drawdown', 0):.2%}")

    # Restore original
    for key, original_data in original_cache.items():
        cache._cache[key] = original_data

except Exception as e:
    print(f"❌ Error: {e}")
    # Ensure cache is restored
    for key, original_data in original_cache.items():
        cache._cache[key] = original_data

# Test 3: OOS period only (2021-2024) - Phase 1 validation data
print("\n3️⃣  OOS PERIOD ONLY (2021-2024) - Phase 1 validation")
print("-" * 70)
try:
    # Filter to OOS period
    original_cache = {}
    for key in KEYS_TO_FILTER:
        if key in cache._cache:
            original_cache[key] = cache._cache[key]

    for key in KEYS_TO_FILTER:
        if key in cache._cache:
            cache._cache[key] = original_cache[key]['2021':'2024']

    report_oos, metrics_oos = template.generate_strategy(champion_params)
    print(f"✅ Sharpe Ratio: {metrics_oos.get('sharpe_ratio', 0):.4f}")
    print(f"   Annual Return: {metrics_oos.get('annual_return', 0):.2%}")
    print(f"   Max Drawdown: {metrics_oos.get('max_drawdown', 0):.2%}")

    # Restore original
    for key, original_data in original_cache.items():
        cache._cache[key] = original_data

except Exception as e:
    print(f"❌ Error: {e}")
    for key, original_data in original_cache.items():
        cache._cache[key] = original_data

print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)
print(f"\nIf IS Sharpe ≈ Phase 1 result (0.81):")
print("  → IS/OOS split is working correctly")
print("  → Lower Sharpe is due to restricted time period, not a bug")
print(f"\nIf Full Sharpe ≈ Phase 0 result (2.48):")
print("  → Confirms Phase 0 used all available data")
print("  → Target Sharpe >2.5 was unrealistic for 5-year IS period")
print("\n" + "=" * 70)
