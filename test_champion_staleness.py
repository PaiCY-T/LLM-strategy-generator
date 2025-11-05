"""Test script for champion staleness checking mechanism."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'artifacts/working/modules'))

from autonomous_loop import AutonomousLoop, ChampionStrategy
from history import IterationHistory
from datetime import datetime


def test_staleness_basic():
    """Test basic staleness checking with competitive champion."""
    print("\n" + "="*60)
    print("TEST 1: Competitive Champion (Should NOT demote)")
    print("="*60)

    # Setup: Create loop with test history
    loop = AutonomousLoop(history_file="test_staleness_history.json")
    loop.history.clear()

    # Create champion with Sharpe 2.5 (should remain competitive)
    loop.champion = ChampionStrategy(
        iteration_num=5,
        code="# Champion code",
        parameters={'lookback': 20},
        metrics={'sharpe_ratio': 2.5, 'total_return': 0.50},
        success_patterns=['momentum'],
        timestamp=datetime.now().isoformat()
    )

    # Add 50 successful iterations with varying Sharpe ratios
    # Champion remains competitive (Sharpe 2.5 is above median of top 10%)
    # With 50 strategies, top 10% = 5 strategies (meets minimum cohort size)
    # Top 10% will be around 2.2-2.3 range, champion at 2.5 is above median
    sharpe_values = (
        [1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.75, 1.8, 1.85, 1.9] +  # Lower tier (10)
        [1.5, 1.6, 1.7, 1.75, 1.8, 1.85, 1.9, 1.95, 2.0, 2.05] +  # Mid tier (10)
        [1.6, 1.7, 1.8, 1.85, 1.9, 1.95, 2.0, 2.05, 2.1, 2.15] +  # Upper tier (10)
        [1.7, 1.8, 1.85, 1.9, 1.95, 2.0, 2.05, 2.1, 2.15, 2.2] +  # High tier (10)
        [1.8, 1.85, 1.9, 1.95, 2.0, 2.05, 2.1, 2.15, 2.2, 2.3]  # Top tier (10)
    )

    for i, sharpe in enumerate(sharpe_values):
        loop.history.add_record(
            iteration_num=i,
            model="test-model",
            code=f"# Strategy {i}",
            validation_passed=True,
            validation_errors=[],
            execution_success=True,
            execution_error=None,
            metrics={'sharpe_ratio': sharpe, 'total_return': 0.30},
            feedback="Test feedback"
        )

    # Check staleness
    result = loop._check_champion_staleness()

    print(f"\nShould demote: {result['should_demote']}")
    print(f"Reason: {result['reason']}")
    print(f"Metrics:")
    for key, value in result['metrics'].items():
        print(f"  {key}: {value}")

    # Verify
    assert result['should_demote'] == False, "Champion should NOT be demoted (still competitive)"
    assert result['metrics']['champion_sharpe'] == 2.5
    assert result['metrics']['cohort_size'] >= 5
    assert result['metrics']['champion_sharpe'] >= result['metrics']['cohort_median'], \
        f"Champion Sharpe {result['metrics']['champion_sharpe']} should be >= cohort median {result['metrics']['cohort_median']}"
    print("\n✅ Test 1 PASSED: Competitive champion retained")

    # Cleanup
    loop.history.clear()


def test_staleness_stale_champion():
    """Test staleness checking with stale champion."""
    print("\n" + "="*60)
    print("TEST 2: Stale Champion (Should demote)")
    print("="*60)

    # Setup
    loop = AutonomousLoop(history_file="test_staleness_history.json")
    loop.history.clear()

    # Create champion with Sharpe 1.5 (was good initially)
    loop.champion = ChampionStrategy(
        iteration_num=2,
        code="# Old champion code",
        parameters={'lookback': 10},
        metrics={'sharpe_ratio': 1.5, 'total_return': 0.30},
        success_patterns=['trend'],
        timestamp=datetime.now().isoformat()
    )

    # Add 50 successful iterations with improved Sharpe ratios
    # System has improved significantly, champion is now stale
    # Top 10% (5 strategies) will have median > 2.7, champion at 1.5 is clearly stale
    sharpe_values = (
        [2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9] +  # Baseline (10)
        [2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9] +  # Duplicate (10)
        [2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.0] +  # Improved (10)
        [2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.0, 3.1] +  # Better (10)
        [2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.0, 3.1, 3.2]   # Best (10)
    )

    for i, sharpe in enumerate(sharpe_values):
        loop.history.add_record(
            iteration_num=i + 3,  # Start after champion iteration
            model="test-model",
            code=f"# Strategy {i}",
            validation_passed=True,
            validation_errors=[],
            execution_success=True,
            execution_error=None,
            metrics={'sharpe_ratio': sharpe, 'total_return': 0.40},
            feedback="Test feedback"
        )

    # Check staleness
    result = loop._check_champion_staleness()

    print(f"\nShould demote: {result['should_demote']}")
    print(f"Reason: {result['reason']}")
    print(f"Metrics:")
    for key, value in result['metrics'].items():
        print(f"  {key}: {value}")

    # Verify
    assert result['should_demote'] == True, "Champion SHOULD be demoted (stale)"
    assert result['metrics']['champion_sharpe'] == 1.5
    assert result['metrics']['cohort_median'] > 1.5, "Cohort median should be higher than champion"
    print("\n✅ Test 2 PASSED: Stale champion detected")

    # Cleanup
    loop.history.clear()


def test_staleness_edge_cases():
    """Test edge cases for staleness checking."""
    print("\n" + "="*60)
    print("TEST 3: Edge Cases")
    print("="*60)

    # Setup
    loop = AutonomousLoop(history_file="test_staleness_history.json")
    loop.history.clear()

    # Test 3.1: No champion
    print("\n--- Test 3.1: No champion ---")
    loop.champion = None
    result = loop._check_champion_staleness()
    assert result['should_demote'] == False
    assert "No champion exists" in result['reason']
    print(f"✅ Result: {result['reason']}")

    # Test 3.2: No successful iterations
    print("\n--- Test 3.2: No successful iterations ---")
    loop.champion = ChampionStrategy(
        iteration_num=0,
        code="# Champion",
        parameters={},
        metrics={'sharpe_ratio': 2.0},
        success_patterns=[],
        timestamp=datetime.now().isoformat()
    )
    result = loop._check_champion_staleness()
    assert result['should_demote'] == False
    assert "No successful iterations" in result['reason']
    print(f"✅ Result: {result['reason']}")

    # Test 3.3: Insufficient data (less than min_cohort_size)
    print("\n--- Test 3.3: Insufficient data ---")
    for i in range(3):  # Only 3 strategies (less than min 5)
        loop.history.add_record(
            iteration_num=i,
            model="test-model",
            code=f"# Strategy {i}",
            validation_passed=True,
            validation_errors=[],
            execution_success=True,
            execution_error=None,
            metrics={'sharpe_ratio': 1.5 + i * 0.1, 'total_return': 0.30},
            feedback="Test feedback"
        )

    result = loop._check_champion_staleness()
    assert result['should_demote'] == False
    assert "Insufficient data" in result['reason']
    print(f"✅ Result: {result['reason']}")

    print("\n✅ Test 3 PASSED: All edge cases handled correctly")

    # Cleanup
    loop.history.clear()


def main():
    """Run all staleness tests."""
    print("\n" + "="*70)
    print("CHAMPION STALENESS MECHANISM - TEST SUITE")
    print("="*70)

    try:
        test_staleness_basic()
        test_staleness_stale_champion()
        test_staleness_edge_cases()

        print("\n" + "="*70)
        print("ALL TESTS PASSED ✅")
        print("="*70)
        print("\nImplementation verified:")
        print("  ✅ Correctly identifies competitive champions")
        print("  ✅ Correctly identifies stale champions")
        print("  ✅ Handles edge cases gracefully")
        print("  ✅ Returns structured decision with metrics")
        print("  ✅ Provides clear logging of comparison results")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
