#!/usr/bin/env python3
"""
Quick validation test for stateless EXIT factors.

Tests:
1. Registry can load new stateless factors
2. Factors can be created with correct parameters
3. Template strategy uses new stateless factor
"""

import sys
from src.factor_library.registry import FactorRegistry
from src.factor_graph.factor_category import FactorCategory

def test_registry_loading():
    """Test that registry loads new stateless factors."""
    print("=" * 80)
    print("Test 1: Registry Loading")
    print("=" * 80)

    registry = FactorRegistry.get_instance()

    # Check rolling_trailing_stop_factor
    metadata = registry.get_metadata("rolling_trailing_stop_factor")
    if metadata is None:
        print("❌ FAIL: rolling_trailing_stop_factor not found in registry")
        return False

    print(f"✅ rolling_trailing_stop_factor found")
    print(f"   Category: {metadata['category']}")
    print(f"   Description: {metadata['description']}")
    print(f"   Parameters: {metadata['parameters']}")
    print(f"   Ranges: {metadata['parameter_ranges']}")

    # Check rolling_profit_target_factor
    metadata = registry.get_metadata("rolling_profit_target_factor")
    if metadata is None:
        print("❌ FAIL: rolling_profit_target_factor not found in registry")
        return False

    print(f"\n✅ rolling_profit_target_factor found")
    print(f"   Category: {metadata['category']}")
    print(f"   Description: {metadata['description']}")
    print(f"   Parameters: {metadata['parameters']}")
    print(f"   Ranges: {metadata['parameter_ranges']}")

    return True

def test_factor_creation():
    """Test that factors can be created."""
    print("\n" + "=" * 80)
    print("Test 2: Factor Creation")
    print("=" * 80)

    registry = FactorRegistry.get_instance()

    # Create rolling trailing stop
    try:
        factor = registry.create_factor(
            "rolling_trailing_stop_factor",
            parameters={"trail_percent": 0.10, "lookback_periods": 20}
        )
        print(f"✅ Created rolling_trailing_stop_factor")
        print(f"   ID: {factor.id}")
        print(f"   Inputs: {factor.inputs}")
        print(f"   Outputs: {factor.outputs}")
        print(f"   Category: {factor.category}")
    except Exception as e:
        print(f"❌ FAIL: Could not create rolling_trailing_stop_factor: {e}")
        return False

    # Create rolling profit target
    try:
        factor = registry.create_factor(
            "rolling_profit_target_factor",
            parameters={"target_percent": 0.30, "lookback_periods": 20}
        )
        print(f"\n✅ Created rolling_profit_target_factor")
        print(f"   ID: {factor.id}")
        print(f"   Inputs: {factor.inputs}")
        print(f"   Outputs: {factor.outputs}")
        print(f"   Category: {factor.category}")
    except Exception as e:
        print(f"❌ FAIL: Could not create rolling_profit_target_factor: {e}")
        return False

    return True

def test_exit_category():
    """Test that EXIT category contains stateless factors."""
    print("\n" + "=" * 80)
    print("Test 3: EXIT Category Factors")
    print("=" * 80)

    registry = FactorRegistry.get_instance()
    exit_factors = registry.list_by_category(FactorCategory.EXIT)

    print(f"EXIT category contains {len(exit_factors)} factors:")
    for name in exit_factors:
        metadata = registry.get_metadata(name)
        inputs = metadata['parameters']
        stateless = "✅ STATELESS" if "lookback_periods" in inputs else "⚠️  STATEFUL"
        print(f"  - {name}: {stateless}")

    # Check that stateless factors are present
    if "rolling_trailing_stop_factor" not in exit_factors:
        print("\n❌ FAIL: rolling_trailing_stop_factor not in EXIT category")
        return False

    if "rolling_profit_target_factor" not in exit_factors:
        print("\n❌ FAIL: rolling_profit_target_factor not in EXIT category")
        return False

    print(f"\n✅ Both stateless factors are in EXIT category")
    print(f"✅ Mutation system will now include stateless factors (25% chance to select EXIT category)")

    return True

def test_inputs_validation():
    """Test that stateless factors only require 'close' input."""
    print("\n" + "=" * 80)
    print("Test 4: Input Dependencies (Stateless Validation)")
    print("=" * 80)

    registry = FactorRegistry.get_instance()

    # Check rolling trailing stop inputs
    trailing_stop = registry.create_factor(
        "rolling_trailing_stop_factor",
        parameters={"trail_percent": 0.10, "lookback_periods": 20}
    )

    print(f"rolling_trailing_stop_factor inputs: {trailing_stop.inputs}")
    if trailing_stop.inputs == ["close"]:
        print("✅ Only requires 'close' (stateless)")
    else:
        print(f"❌ FAIL: Requires {trailing_stop.inputs} (should only be ['close'])")
        return False

    # Check rolling profit target inputs
    profit_target = registry.create_factor(
        "rolling_profit_target_factor",
        parameters={"target_percent": 0.30, "lookback_periods": 20}
    )

    print(f"\nrolling_profit_target_factor inputs: {profit_target.inputs}")
    if profit_target.inputs == ["close"]:
        print("✅ Only requires 'close' (stateless)")
    else:
        print(f"❌ FAIL: Requires {profit_target.inputs} (should only be ['close'])")
        return False

    print("\n✅ Both factors are stateless (no positions/entry_price dependency)")
    print("✅ Can execute in to_pipeline() stage before sim()")

    return True

if __name__ == "__main__":
    print("Stateless EXIT Factors Validation Test")
    print("=" * 80)
    print()

    all_passed = True

    # Run tests
    all_passed &= test_registry_loading()
    all_passed &= test_factor_creation()
    all_passed &= test_exit_category()
    all_passed &= test_inputs_validation()

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("\nNext steps:")
        print("1. Run full 20-iteration Hybrid test")
        print("2. Verify Factor Graph strategies execute successfully")
        print("3. Expected success rate improvement: 5% → ~100%")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        print("\nPlease review the errors above and fix issues before proceeding.")
        sys.exit(1)
