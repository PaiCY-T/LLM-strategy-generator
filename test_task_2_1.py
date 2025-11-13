#!/usr/bin/env python3
"""Test script for Task 2.1: AntiChurnManager additive threshold support."""

from src.config.anti_churn_manager import AntiChurnManager


def test_additive_threshold():
    """Test that AntiChurnManager loads and exposes additive_threshold."""
    print("=" * 70)
    print("Task 2.1 Test: AntiChurnManager Additive Threshold Support")
    print("=" * 70)

    # Initialize manager
    manager = AntiChurnManager()

    # Test 1: Verify attribute exists and is loaded from config
    print("\n[Test 1] Verify additive_threshold attribute exists")
    assert hasattr(manager, 'additive_threshold'), "Missing additive_threshold attribute"
    print(f"✅ additive_threshold attribute exists: {manager.additive_threshold}")

    # Test 2: Verify getter method exists and returns correct value
    print("\n[Test 2] Verify get_additive_threshold() method")
    assert hasattr(manager, 'get_additive_threshold'), "Missing get_additive_threshold method"
    threshold = manager.get_additive_threshold()
    print(f"✅ get_additive_threshold() returns: {threshold}")

    # Test 3: Verify value matches config file (should be 0.02)
    print("\n[Test 3] Verify value matches config file")
    expected_value = 0.02
    assert manager.additive_threshold == expected_value, \
        f"Expected {expected_value}, got {manager.additive_threshold}"
    assert threshold == expected_value, \
        f"Getter returned {threshold}, expected {expected_value}"
    print(f"✅ Value matches config: {threshold} == {expected_value}")

    # Test 4: Verify backward compatibility (existing attributes still work)
    print("\n[Test 4] Verify backward compatibility")
    assert hasattr(manager, 'probation_period'), "Missing probation_period"
    assert hasattr(manager, 'probation_threshold'), "Missing probation_threshold"
    assert hasattr(manager, 'post_probation_threshold'), "Missing post_probation_threshold"
    print("✅ All existing attributes present")

    # Test 5: Display all thresholds
    print("\n[Test 5] Display all threshold values")
    print(f"  Probation threshold: {manager.probation_threshold * 100:.0f}%")
    print(f"  Post-probation threshold: {manager.post_probation_threshold * 100:.0f}%")
    print(f"  Additive threshold: {manager.additive_threshold} (absolute)")
    print("✅ All thresholds loaded successfully")

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Task 2.1 Implementation Complete")
    print("=" * 70)


if __name__ == '__main__':
    test_additive_threshold()
