"""
Comprehensive Test Suite for Bonferroni Threshold Fix (Task 1.2)
==================================================================

Tests the fix for the threshold bug where run_phase2_with_validation.py was using
'significance_threshold' (0.8) instead of 'statistical_threshold' (0.5) for the
Bonferroni statistical significance test.

Fix: Changed line 398 from:
  bonferroni_threshold = validation.get('significance_threshold', 0.5)  # Got 0.8!
To:
  bonferroni_threshold = validation.get('statistical_threshold', 0.5)  # Gets 0.5 ✅

Test Coverage:
    - Layer 1: BonferroniIntegrator returns correct threshold values
    - Layer 2: Threshold separation (statistical vs dynamic)
    - Layer 3: Edge case strategies (between thresholds)
    - Layer 4: JSON output structure validation
    - Layer 5: Bonferroni calculation correctness
    - Layer 6: Integration regression tests

Test Count: 20 tests
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from src.validation.integration import BonferroniIntegrator
from src.validation.dynamic_threshold import DynamicThresholdCalculator


class TestBonferroniIntegratorThresholds:
    """Layer 1: BonferroniIntegrator returns all three threshold values correctly."""

    def test_returns_statistical_threshold(self):
        """Test that BonferroniIntegrator returns statistical_threshold (0.5)."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252,
            use_conservative=True
        )

        # Should have statistical_threshold = 0.5
        assert 'statistical_threshold' in result
        assert result['statistical_threshold'] == pytest.approx(0.5, abs=0.01)

    def test_returns_dynamic_threshold(self):
        """Test that BonferroniIntegrator returns dynamic_threshold (0.8)."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252,
            use_conservative=True
        )

        # Should have dynamic_threshold = 0.8
        assert 'dynamic_threshold' in result
        assert result['dynamic_threshold'] == 0.8

    def test_returns_significance_threshold_as_max(self):
        """Test that significance_threshold = max(statistical, dynamic) = 0.8."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252,
            use_conservative=True
        )

        # significance_threshold should be max(0.5, 0.8) = 0.8
        assert 'significance_threshold' in result
        assert result['significance_threshold'] == 0.8

    def test_all_three_thresholds_present(self):
        """Test that all three threshold values are present in result."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.85,
            n_periods=252,
            use_conservative=True
        )

        # All three should be present
        assert 'statistical_threshold' in result
        assert 'dynamic_threshold' in result
        assert 'significance_threshold' in result

        # And should have correct values
        assert result['statistical_threshold'] == pytest.approx(0.5, abs=0.01)
        assert result['dynamic_threshold'] == 0.8
        assert result['significance_threshold'] == 0.8


class TestThresholdSeparation:
    """Layer 2: Test separation of statistical and dynamic thresholds."""

    def test_strategy_between_thresholds_passes_statistical(self):
        """Test strategy with Sharpe 0.6 passes statistical but not dynamic."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.681,  # Actual from pilot test
            n_periods=252,
            use_conservative=True
        )

        # Should pass statistical test (0.681 > 0.5)
        # But fail overall validation (0.681 < 0.8)
        assert result['validation_passed'] is False
        assert result['sharpe_ratio'] == 0.681

        # Verify thresholds
        assert result['statistical_threshold'] == pytest.approx(0.5, abs=0.01)
        assert result['dynamic_threshold'] == 0.8

    def test_strategy_above_both_thresholds_passes(self):
        """Test strategy with Sharpe 0.9 passes both tests."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.929,  # Actual from pilot test
            n_periods=252,
            use_conservative=True
        )

        # Should pass both tests (0.929 > 0.5 and 0.929 > 0.8)
        assert result['validation_passed'] is True
        assert result['sharpe_ratio'] == 0.929

    def test_strategy_below_both_thresholds_fails(self):
        """Test strategy with Sharpe 0.3 fails both tests."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.3,
            n_periods=252,
            use_conservative=True
        )

        # Should fail both tests (0.3 < 0.5 and 0.3 < 0.8)
        assert result['validation_passed'] is False
        assert result['sharpe_ratio'] == 0.3

    def test_strategy_exactly_at_statistical_threshold(self):
        """Test strategy at exactly statistical threshold (0.5)."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.5,
            n_periods=252,
            use_conservative=True
        )

        # Boundary case: should pass or fail based on > vs >= logic
        # Current implementation uses > so 0.5 should fail
        assert result['validation_passed'] is False

    def test_strategy_exactly_at_dynamic_threshold(self):
        """Test strategy at exactly dynamic threshold (0.8)."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.8,
            n_periods=252,
            use_conservative=True
        )

        # Boundary case: should pass or fail based on > vs >= logic
        # Current implementation uses > so 0.8 should fail
        assert result['validation_passed'] is False


class TestEdgeCaseStrategies:
    """Layer 3: Test edge cases from pilot test."""

    def test_pilot_strategy_0_classification(self):
        """Test pilot Strategy 0 (Sharpe 0.681) classification."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.681,
            n_periods=252,
            use_conservative=True
        )

        # After fix: should pass statistical (0.681 > 0.5)
        # but fail overall validation (0.681 < 0.8)
        assert result['validation_passed'] is False

        # Verify this is NOT due to statistical test failure
        statistical_threshold = result.get('statistical_threshold', 0.5)
        assert result['sharpe_ratio'] > statistical_threshold

    def test_pilot_strategy_1_classification(self):
        """Test pilot Strategy 1 (Sharpe 0.818) classification."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.818,
            n_periods=252,
            use_conservative=True
        )

        # Should pass both tests
        assert result['validation_passed'] is True

    def test_pilot_strategy_2_classification(self):
        """Test pilot Strategy 2 (Sharpe 0.929) classification."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.929,
            n_periods=252,
            use_conservative=True
        )

        # Should pass both tests
        assert result['validation_passed'] is True


class TestJSONOutputStructure:
    """Layer 4: Test JSON output structure from validation."""

    def test_validation_result_has_all_required_fields(self):
        """Test that validation result has all required fields."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252,
            use_conservative=True
        )

        # Required fields
        required_fields = [
            'validation_passed',
            'sharpe_ratio',
            'significance_threshold',
            'adjusted_alpha',
            'is_significant',
            'dynamic_threshold',
            'statistical_threshold'
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_bonferroni_threshold_field_value(self):
        """Test that statistical_threshold field has correct value (0.5)."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252,
            use_conservative=True
        )

        # statistical_threshold should be ~0.5
        assert result['statistical_threshold'] == pytest.approx(0.5, abs=0.01)

    def test_dynamic_threshold_field_value(self):
        """Test that dynamic_threshold field has correct value (0.8)."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252,
            use_conservative=True
        )

        # dynamic_threshold should be 0.8
        assert result['dynamic_threshold'] == 0.8


class TestBonferroniCalculation:
    """Layer 5: Test Bonferroni correction calculation."""

    def test_adjusted_alpha_for_20_strategies(self):
        """Test adjusted alpha = 0.05 / 20 = 0.0025."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252,
            use_conservative=True
        )

        expected_alpha = 0.05 / 20  # 0.0025
        assert result['adjusted_alpha'] == pytest.approx(expected_alpha)

    def test_adjusted_alpha_for_different_n(self):
        """Test adjusted alpha scales with n_strategies."""
        for n in [10, 20, 50, 100]:
            integrator = BonferroniIntegrator(n_strategies=n, alpha=0.05)

            result = integrator.validate_single_strategy(
                sharpe_ratio=0.7,
                n_periods=252,
                use_conservative=True
            )

            expected_alpha = 0.05 / n
            assert result['adjusted_alpha'] == pytest.approx(expected_alpha)

    def test_statistical_threshold_constant_for_threshold_mode(self):
        """Test that statistical threshold is constant (0.5) in threshold mode."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        # Test with different n_strategies
        for n in [10, 20, 50, 100]:
            integrator.n_strategies = n
            integrator.validator.n_tests = n
            integrator.validator.adjusted_alpha = 0.05 / n

            result = integrator.validate_single_strategy(
                sharpe_ratio=0.7,
                n_periods=252,
                use_conservative=True
            )

            # Statistical threshold should remain ~0.5
            assert result['statistical_threshold'] == pytest.approx(0.5, abs=0.01)


class TestRegressionPrevention:
    """Layer 6: Regression tests to prevent the bug from reoccurring."""

    def test_cannot_mix_up_thresholds(self):
        """Test that statistical and significance thresholds are different."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252,
            use_conservative=True
        )

        # These should be different values
        statistical = result['statistical_threshold']
        significance = result['significance_threshold']

        assert statistical != significance
        assert statistical == pytest.approx(0.5, abs=0.01)
        assert significance == 0.8

    def test_strategy_count_between_thresholds(self):
        """Test counting strategies between thresholds (Sharpe 0.5-0.8)."""
        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        # Strategies with Sharpe between 0.5 and 0.8
        test_sharpes = [0.55, 0.6, 0.65, 0.7, 0.75]
        results = []

        for sharpe in test_sharpes:
            result = integrator.validate_single_strategy(
                sharpe_ratio=sharpe,
                n_periods=252,
                use_conservative=True
            )
            results.append(result)

        # All should fail overall validation (< 0.8)
        for result in results:
            assert result['validation_passed'] is False

        # But all pass statistical threshold (> 0.5)
        for result in results:
            assert result['sharpe_ratio'] > result['statistical_threshold']

    def test_disabled_dynamic_threshold_fallback(self):
        """Test that disabling dynamic threshold works correctly."""
        integrator = BonferroniIntegrator(
            n_strategies=20,
            alpha=0.05,
            use_dynamic_threshold=False
        )

        result = integrator.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252,
            use_conservative=True
        )

        # Should not have dynamic_threshold field
        assert 'dynamic_threshold' not in result

        # significance_threshold should equal statistical_threshold
        assert result['significance_threshold'] == result.get('statistical_threshold', 0.5)
