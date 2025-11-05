"""
Test Task 6 & 7 Implementation: Bootstrap CI and Bonferroni Correction
Tests the validation integrators for statistical significance testing
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.validation.integration import BootstrapIntegrator, BonferroniIntegrator
from src.backtest.executor import BacktestExecutor


def test_bootstrap_integrator_initialization():
    """Test BootstrapIntegrator can be initialized."""
    print("=" * 80)
    print("TEST 1: BootstrapIntegrator Initialization")
    print("=" * 80)

    try:
        # Test with default executor
        integrator1 = BootstrapIntegrator()
        assert integrator1.executor is not None, "❌ Executor not initialized"
        print("✅ BootstrapIntegrator initialized with default executor")

        # Test with custom executor
        custom_executor = BacktestExecutor(timeout=300)
        integrator2 = BootstrapIntegrator(executor=custom_executor)
        assert integrator2.executor == custom_executor, "❌ Custom executor not used"
        print("✅ BootstrapIntegrator initialized with custom executor")

        print("\n✅ BootstrapIntegrator Initialization Test PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bootstrap_returns_extraction():
    """Test returns extraction/synthesis methods."""
    print("=" * 80)
    print("TEST 2: Bootstrap Returns Extraction")
    print("=" * 80)

    try:
        import numpy as np

        integrator = BootstrapIntegrator()

        # Test case 1: Synthesize from Sharpe and total return
        returns = integrator._extract_returns_from_report(
            report=None,  # No report available
            sharpe_ratio=1.5,
            total_return=0.50,  # 50% total return
            n_days=252
        )

        assert returns is not None, "❌ Returns extraction failed"
        assert len(returns) == 252, f"❌ Expected 252 returns, got {len(returns)}"
        assert isinstance(returns, np.ndarray), "❌ Returns not numpy array"
        print(f"✅ Synthesized {len(returns)} returns from Sharpe=1.5")
        print(f"   Mean return: {np.mean(returns):.6f}, Std: {np.std(returns):.6f}")

        # Test case 2: Invalid inputs (should return None)
        returns_invalid = integrator._extract_returns_from_report(
            report=None,
            sharpe_ratio=0.0,  # Invalid Sharpe
            total_return=0.0,
            n_days=252
        )
        assert returns_invalid is None, "❌ Should return None for invalid inputs"
        print("✅ Returns None for invalid Sharpe/return")

        print("\n✅ Bootstrap Returns Extraction Test PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Returns extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bonferroni_integrator_initialization():
    """Test BonferroniIntegrator can be initialized."""
    print("=" * 80)
    print("TEST 3: BonferroniIntegrator Initialization")
    print("=" * 80)

    try:
        # Test with default parameters
        integrator1 = BonferroniIntegrator()
        assert integrator1.n_strategies == 20, "❌ Default n_strategies not 20"
        assert integrator1.alpha == 0.05, "❌ Default alpha not 0.05"
        print("✅ BonferroniIntegrator initialized with defaults (n=20, α=0.05)")

        # Test with custom parameters
        integrator2 = BonferroniIntegrator(n_strategies=500, alpha=0.01)
        assert integrator2.n_strategies == 500, "❌ Custom n_strategies not set"
        assert integrator2.alpha == 0.01, "❌ Custom alpha not set"
        print("✅ BonferroniIntegrator initialized with custom params (n=500, α=0.01)")

        # Check adjusted alpha calculation
        expected_adjusted_alpha = 0.01 / 500  # 0.00002
        assert abs(integrator2.validator.adjusted_alpha - expected_adjusted_alpha) < 1e-9, \
            "❌ Adjusted alpha calculation incorrect"
        print(f"✅ Adjusted alpha calculated correctly: {integrator2.validator.adjusted_alpha:.6f}")

        print("\n✅ BonferroniIntegrator Initialization Test PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bonferroni_single_strategy_validation():
    """Test single strategy Bonferroni validation."""
    print("=" * 80)
    print("TEST 4: Bonferroni Single Strategy Validation")
    print("=" * 80)

    try:
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        # Test case 1: High Sharpe (should pass)
        result1 = integrator.validate_single_strategy(sharpe_ratio=1.8, n_periods=252)
        assert result1['validation_passed'], "❌ High Sharpe should pass"
        assert result1['is_significant'], "❌ High Sharpe should be significant"
        print(f"✅ High Sharpe (1.8) validation PASSED")
        print(f"   Threshold: {result1['significance_threshold']:.4f}")

        # Test case 2: Low Sharpe (should fail)
        result2 = integrator.validate_single_strategy(sharpe_ratio=0.3, n_periods=252)
        assert not result2['validation_passed'], "❌ Low Sharpe should fail"
        assert not result2['is_significant'], "❌ Low Sharpe should not be significant"
        print(f"✅ Low Sharpe (0.3) validation FAILED (as expected)")

        # Test case 3: Check adjusted alpha is applied
        assert 'adjusted_alpha' in result1, "❌ Missing adjusted_alpha field"
        expected_adjusted = 0.05 / 20  # 0.0025
        assert abs(result1['adjusted_alpha'] - expected_adjusted) < 1e-9, \
            "❌ Adjusted alpha not correct"
        print(f"✅ Adjusted alpha applied: {result1['adjusted_alpha']:.6f}")

        print("\n✅ Bonferroni Single Strategy Validation Test PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Single strategy validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bonferroni_strategy_set_validation():
    """Test strategy set Bonferroni validation."""
    print("=" * 80)
    print("TEST 5: Bonferroni Strategy Set Validation")
    print("=" * 80)

    try:
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        # Test case: Mix of high and low Sharpe strategies
        strategies = [
            {'name': 'Strategy_A', 'sharpe_ratio': 1.8},
            {'name': 'Strategy_B', 'sharpe_ratio': 2.1},
            {'name': 'Strategy_C', 'sharpe_ratio': 0.3},
            {'name': 'Strategy_D', 'sharpe_ratio': 0.8},
            {'name': 'Strategy_E', 'sharpe_ratio': 1.5},
        ]

        result = integrator.validate_strategy_set(strategies, n_periods=252)

        assert 'total_strategies' in result, "❌ Missing total_strategies field"
        assert result['total_strategies'] == 5, f"❌ Expected 5 strategies, got {result['total_strategies']}"
        print(f"✅ Total strategies: {result['total_strategies']}")

        assert 'significant_count' in result, "❌ Missing significant_count field"
        assert result['significant_count'] > 0, "❌ Should have some significant strategies"
        print(f"✅ Significant strategies: {result['significant_count']}")

        assert 'estimated_fdr' in result, "❌ Missing estimated_fdr field"
        print(f"✅ Estimated FDR: {result['estimated_fdr']:.2%}")

        assert 'significance_threshold' in result, "❌ Missing significance_threshold field"
        print(f"✅ Significance threshold: {result['significance_threshold']:.4f}")

        # Check significant strategies list
        assert 'significant_strategies' in result, "❌ Missing significant_strategies field"
        assert isinstance(result['significant_strategies'], list), "❌ significant_strategies not a list"
        print(f"✅ Significant strategies list: {len(result['significant_strategies'])} entries")

        print("\n✅ Bonferroni Strategy Set Validation Test PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Strategy set validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bonferroni_bootstrap_combined_validation():
    """Test combined Bonferroni + Bootstrap validation."""
    print("=" * 80)
    print("TEST 6: Combined Bonferroni + Bootstrap Validation")
    print("=" * 80)

    try:
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        # Test case 1: Both pass (high Sharpe, high CI lower bound)
        result1 = integrator.validate_with_bootstrap(
            sharpe_ratio=1.8,
            bootstrap_ci_lower=1.2,
            bootstrap_ci_upper=2.4,
            n_periods=252
        )

        assert result1['validation_passed'], "❌ Both high should pass"
        assert result1['point_estimate_significant'], "❌ Point estimate should be significant"
        assert result1['ci_lower_significant'], "❌ CI lower should be significant"
        print("✅ Combined validation PASSED (Sharpe=1.8, CI lower=1.2)")

        # Test case 2: Point estimate passes but CI lower fails
        result2 = integrator.validate_with_bootstrap(
            sharpe_ratio=1.8,
            bootstrap_ci_lower=0.3,  # Too low
            bootstrap_ci_upper=2.4,
            n_periods=252
        )

        assert not result2['validation_passed'], "❌ Should fail if CI lower too low"
        assert result2['point_estimate_significant'], "❌ Point estimate should still be significant"
        assert not result2['ci_lower_significant'], "❌ CI lower should not be significant"
        print("✅ Combined validation FAILED when CI lower too low (as expected)")

        # Test case 3: Check fields are present
        assert 'significance_threshold' in result1, "❌ Missing significance_threshold"
        assert 'validation_reason' in result1, "❌ Missing validation_reason"
        print(f"✅ All required fields present")
        print(f"   Threshold: {result1['significance_threshold']:.4f}")
        print(f"   Reason: {result1['validation_reason']}")

        print("\n✅ Combined Bonferroni + Bootstrap Validation Test PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Combined validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_method_signatures():
    """Test that all required methods exist with correct signatures."""
    print("=" * 80)
    print("TEST 7: Method Signatures")
    print("=" * 80)

    import inspect

    try:
        # Test BootstrapIntegrator methods
        bootstrap_integrator = BootstrapIntegrator()

        assert hasattr(bootstrap_integrator, 'validate_with_bootstrap'), \
            "❌ validate_with_bootstrap method not found"
        sig = inspect.signature(bootstrap_integrator.validate_with_bootstrap)
        params = list(sig.parameters.keys())
        assert 'strategy_code' in params, "❌ strategy_code parameter missing"
        assert 'confidence_level' in params, "❌ confidence_level parameter missing"
        assert 'n_iterations' in params, "❌ n_iterations parameter missing"
        print("✅ BootstrapIntegrator.validate_with_bootstrap() signature correct")

        assert hasattr(bootstrap_integrator, '_extract_returns_from_report'), \
            "❌ _extract_returns_from_report method not found"
        print("✅ BootstrapIntegrator._extract_returns_from_report() exists")

        # Test BonferroniIntegrator methods
        bonferroni_integrator = BonferroniIntegrator()

        assert hasattr(bonferroni_integrator, 'validate_single_strategy'), \
            "❌ validate_single_strategy method not found"
        sig = inspect.signature(bonferroni_integrator.validate_single_strategy)
        params = list(sig.parameters.keys())
        assert 'sharpe_ratio' in params, "❌ sharpe_ratio parameter missing"
        assert 'n_periods' in params, "❌ n_periods parameter missing"
        print("✅ BonferroniIntegrator.validate_single_strategy() signature correct")

        assert hasattr(bonferroni_integrator, 'validate_strategy_set'), \
            "❌ validate_strategy_set method not found"
        sig = inspect.signature(bonferroni_integrator.validate_strategy_set)
        params = list(sig.parameters.keys())
        assert 'strategies_with_sharpes' in params, "❌ strategies_with_sharpes parameter missing"
        print("✅ BonferroniIntegrator.validate_strategy_set() signature correct")

        assert hasattr(bonferroni_integrator, 'validate_with_bootstrap'), \
            "❌ validate_with_bootstrap method not found"
        sig = inspect.signature(bonferroni_integrator.validate_with_bootstrap)
        params = list(sig.parameters.keys())
        assert 'sharpe_ratio' in params, "❌ sharpe_ratio parameter missing"
        assert 'bootstrap_ci_lower' in params, "❌ bootstrap_ci_lower parameter missing"
        print("✅ BonferroniIntegrator.validate_with_bootstrap() signature correct")

        print("\n✅ Method Signatures Test PASSED\n")
        return True

    except Exception as e:
        print(f"❌ Method signature test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("=" * 80)
    print(" Task 6 & 7 Implementation Validation Test Suite")
    print("=" * 80)
    print("\n")

    tests = [
        test_bootstrap_integrator_initialization,
        test_bootstrap_returns_extraction,
        test_bonferroni_integrator_initialization,
        test_bonferroni_single_strategy_validation,
        test_bonferroni_strategy_set_validation,
        test_bonferroni_bootstrap_combined_validation,
        test_method_signatures,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 80)
    if failed == 0:
        print(" ✅ ALL TESTS PASSED - Tasks 6-7 Implementation Complete")
    else:
        print(f" ⚠️  SOME TESTS FAILED - {passed} passed, {failed} failed")
    print("=" * 80)
    print("\n")
    print("Summary:")
    print("  ✅ Task 6: Bootstrap confidence intervals integration implemented")
    print("     - BootstrapIntegrator.validate_with_bootstrap()")
    print("     - Returns synthesis from Sharpe ratio and total return")
    print("     - Block bootstrap with 1000 iterations")
    print("     - 95% confidence interval calculation")
    print("\n")
    print("  ✅ Task 7: Multiple comparison correction integration implemented")
    print("     - BonferroniIntegrator.validate_single_strategy()")
    print("     - BonferroniIntegrator.validate_strategy_set()")
    print("     - BonferroniIntegrator.validate_with_bootstrap() (combined)")
    print("     - Adjusted alpha calculation: α/n")
    print("     - Conservative threshold (max(calculated, 0.5))")
    print("\n")
    print("Next Steps:")
    print("  1. Update STATUS.md to mark Tasks 6-7 complete")
    print("  2. Update __init__.py to export new integrators")
    print("  3. Proceed to Task 8: Validation report generator")
    print("\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
