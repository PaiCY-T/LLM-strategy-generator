"""
Test BaselineMetrics Implementation

This script tests the baseline metrics framework to ensure:
1. Baseline metrics can be computed from iteration history
2. Baseline can be locked as immutable reference
3. Adaptive thresholds are correctly calculated
4. Innovation validation works correctly
5. Statistical tests function properly

Run this BEFORE Week 1 to ensure baseline framework is working.
"""

import sys
import json
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.innovation.baseline_metrics import BaselineMetrics, StatisticalValidator


def create_mock_iteration_history():
    """Create mock iteration history for testing."""
    history = []
    for i in range(20):
        history.append({
            'iteration': i,
            'metrics': {
                'sharpe_ratio': np.random.uniform(0.4, 0.9),
                'calmar_ratio': np.random.uniform(1.5, 3.5),
                'max_drawdown': np.random.uniform(0.15, 0.30),
                'total_return': np.random.uniform(0.20, 0.60),
                'win_rate': np.random.uniform(0.50, 0.70)
            }
        })
    return history


def test_compute_baseline():
    """Test 1: Compute baseline metrics."""
    print("\n" + "="*60)
    print("TEST 1: Compute Baseline Metrics")
    print("="*60)

    # Create mock data
    history = create_mock_iteration_history()
    history_path = Path('test_iteration_history.json')
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)

    # Compute baseline
    baseline = BaselineMetrics()
    metrics = baseline.compute_baseline(str(history_path))

    # Validate metrics structure
    assert 'mean_sharpe' in metrics, "Missing mean_sharpe"
    assert 'adaptive_sharpe_threshold' in metrics, "Missing adaptive_sharpe_threshold"
    assert 'adaptive_calmar_threshold' in metrics, "Missing adaptive_calmar_threshold"
    assert 'max_drawdown_limit' in metrics, "Missing max_drawdown_limit"
    assert 'total_iterations' in metrics, "Missing total_iterations"

    # Validate adaptive threshold calculation
    expected_sharpe_threshold = metrics['mean_sharpe'] * 1.2
    assert abs(metrics['adaptive_sharpe_threshold'] - expected_sharpe_threshold) < 0.001, \
        f"Adaptive threshold incorrect: {metrics['adaptive_sharpe_threshold']} != {expected_sharpe_threshold}"

    # Validate MDD limit
    assert metrics['max_drawdown_limit'] == 0.25, "MDD limit should be 0.25"

    print(f"✅ TEST 1 PASSED: Baseline computed with {metrics['total_iterations']} iterations")

    # Cleanup
    history_path.unlink()

    return baseline


def test_lock_baseline(baseline):
    """Test 2: Lock baseline as immutable."""
    print("\n" + "="*60)
    print("TEST 2: Lock Baseline as Immutable")
    print("="*60)

    # Lock baseline
    lock_record = baseline.lock_baseline()

    assert lock_record['baseline_hash'] is not None, "Hash not generated"
    assert lock_record['lock_timestamp'] is not None, "Timestamp not set"
    assert lock_record['is_locked'] is True, "Should be locked"
    assert baseline.is_locked is True, "Instance should be locked"

    # Attempt to recompute (should fail)
    try:
        baseline.compute_baseline('dummy.json')
        raise AssertionError("Should not allow recompute after lock")
    except RuntimeError as e:
        print(f"✅ Recompute correctly blocked: {e}")

    # Attempt to re-lock (should fail)
    try:
        baseline.lock_baseline()
        raise AssertionError("Should not allow re-lock")
    except RuntimeError as e:
        print(f"✅ Re-lock correctly blocked: {e}")

    print("✅ TEST 2 PASSED: Baseline locked as immutable")


def test_validate_innovation(baseline):
    """Test 3: Validate innovation against adaptive thresholds."""
    print("\n" + "="*60)
    print("TEST 3: Validate Innovation Against Adaptive Thresholds")
    print("="*60)

    # Get baseline thresholds
    sharpe_threshold = baseline.metrics['adaptive_sharpe_threshold']
    calmar_threshold = baseline.metrics['adaptive_calmar_threshold']

    # Test Case 1: Innovation PASSES all thresholds
    print("\nTest Case 1: Innovation PASSES")
    result = baseline.validate_innovation(
        sharpe_ratio=sharpe_threshold + 0.1,
        max_drawdown=0.20,
        calmar_ratio=calmar_threshold + 0.5,
        verbose=True
    )
    assert result is True, "Should pass all thresholds"

    # Test Case 2: Innovation FAILS Sharpe threshold
    print("\nTest Case 2: Innovation FAILS (Sharpe too low)")
    result = baseline.validate_innovation(
        sharpe_ratio=sharpe_threshold - 0.1,
        max_drawdown=0.20,
        calmar_ratio=calmar_threshold + 0.5,
        verbose=True
    )
    assert result is False, "Should fail Sharpe threshold"

    # Test Case 3: Innovation FAILS MDD limit
    print("\nTest Case 3: Innovation FAILS (MDD too high)")
    result = baseline.validate_innovation(
        sharpe_ratio=sharpe_threshold + 0.1,
        max_drawdown=0.30,
        calmar_ratio=calmar_threshold + 0.5,
        verbose=True
    )
    assert result is False, "Should fail MDD limit"

    # Test Case 4: Innovation FAILS Calmar threshold
    print("\nTest Case 4: Innovation FAILS (Calmar too low)")
    result = baseline.validate_innovation(
        sharpe_ratio=sharpe_threshold + 0.1,
        max_drawdown=0.20,
        calmar_ratio=calmar_threshold - 0.5,
        verbose=True
    )
    assert result is False, "Should fail Calmar threshold"

    print("\n✅ TEST 3 PASSED: Innovation validation working correctly")


def test_statistical_tests():
    """Test 4: Statistical significance tests."""
    print("\n" + "="*60)
    print("TEST 4: Statistical Significance Tests")
    print("="*60)

    # Create baseline and innovation samples
    np.random.seed(42)
    baseline_sharpe = [np.random.normal(0.6, 0.1) for _ in range(20)]
    innovation_sharpe = [np.random.normal(0.75, 0.1) for _ in range(20)]  # Significantly better

    # Test paired t-test
    print("\nTest Case 1: Paired T-Test")
    t_result = StatisticalValidator.paired_t_test(baseline_sharpe, innovation_sharpe)
    print(f"   t-statistic: {t_result['t_statistic']:.3f}")
    print(f"   p-value: {t_result['p_value']:.4f}")
    print(f"   Conclusion: {t_result['conclusion']}")
    assert t_result['is_significant'] == True, "Should be significant with p < 0.05"
    print("✅ Paired t-test detected significant improvement")

    # Test Wilcoxon test
    print("\nTest Case 2: Wilcoxon Signed-Rank Test")
    w_result = StatisticalValidator.wilcoxon_test(baseline_sharpe, innovation_sharpe)
    print(f"   statistic: {w_result['statistic']:.3f}")
    print(f"   p-value: {w_result['p_value']:.4f}")
    print(f"   Conclusion: {w_result['conclusion']}")
    assert w_result['is_significant'] == True, "Should be significant"
    print("✅ Wilcoxon test detected significant improvement")

    # Test hold-out validation
    print("\nTest Case 3: Hold-Out Validation")
    baseline_mean = np.mean(baseline_sharpe)
    baseline_std = np.std(baseline_sharpe)
    exceptional_sharpe = baseline_mean + 2.5 * baseline_std  # Clearly exceptional

    h_result = StatisticalValidator.holdout_validation(
        innovation_sharpe=exceptional_sharpe,
        baseline_mean_sharpe=baseline_mean,
        baseline_std_sharpe=baseline_std
    )
    print(f"   Innovation Sharpe: {h_result['innovation_sharpe']:.3f}")
    print(f"   Baseline 95% CI: [{h_result['baseline_ci_lower']:.3f}, {h_result['baseline_ci_upper']:.3f}]")
    print(f"   Conclusion: {h_result['conclusion']}")
    assert h_result['is_exceptional'] == True, "Should be exceptional"
    print("✅ Hold-out validation correctly identified exceptional performance")

    print("\n✅ TEST 4 PASSED: All statistical tests working correctly")


def test_baseline_summary(baseline):
    """Test 5: Baseline summary reporting."""
    print("\n" + "="*60)
    print("TEST 5: Baseline Summary Reporting")
    print("="*60)

    summary = baseline.get_baseline_summary()

    assert summary['is_locked'] is True, "Should be locked"
    assert 'baseline_hash' in summary, "Missing baseline_hash"
    assert 'key_metrics' in summary, "Missing key_metrics"
    assert 'adaptive_sharpe_threshold' in summary['key_metrics'], "Missing adaptive threshold"

    print(f"\nBaseline Summary:")
    print(f"   Lock Timestamp: {summary['lock_timestamp']}")
    print(f"   Total Iterations: {summary['total_iterations']}")
    print(f"   Mean Sharpe: {summary['key_metrics']['mean_sharpe']:.3f}")
    print(f"   Adaptive Sharpe Threshold: {summary['key_metrics']['adaptive_sharpe_threshold']:.3f}")
    print(f"   Mean Calmar: {summary['key_metrics']['mean_calmar']:.3f}")
    print(f"   Adaptive Calmar Threshold: {summary['key_metrics']['adaptive_calmar_threshold']:.3f}")

    print("\n✅ TEST 5 PASSED: Baseline summary reporting working correctly")


def run_all_tests():
    """Run all baseline metrics tests."""
    print("\n" + "="*60)
    print("BASELINE METRICS FRAMEWORK TEST SUITE")
    print("="*60)
    print("\nThis test suite validates the baseline metrics framework")
    print("required by Condition 1 of the Executive Approval.")
    print("\nTests:")
    print("1. Compute baseline metrics from iteration history")
    print("2. Lock baseline as immutable reference")
    print("3. Validate innovation against adaptive thresholds")
    print("4. Statistical significance tests")
    print("5. Baseline summary reporting")

    try:
        # Run tests
        baseline = test_compute_baseline()
        test_lock_baseline(baseline)
        test_validate_innovation(baseline)
        test_statistical_tests()
        test_baseline_summary(baseline)

        # Final summary
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nBaseline metrics framework is working correctly.")
        print("You may proceed with Week 1 baseline test.")

        # Clean up test baseline file
        baseline_file = Path('.spec-workflow/specs/llm-innovation-capability/baseline_metrics.json')
        if baseline_file.exists():
            baseline_file.unlink()
            print(f"\n🗑️  Cleaned up test baseline file: {baseline_file}")

        return True

    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED")
        print("="*60)
        print(f"\nError: {e}")
        print("\nPlease fix the baseline metrics implementation before proceeding.")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
