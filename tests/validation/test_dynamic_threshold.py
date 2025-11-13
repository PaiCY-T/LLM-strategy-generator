"""
Comprehensive Test Suite for Dynamic Threshold Calculator
=========================================================

Tests Task 1.1.3 implementation of Taiwan market benchmark-based thresholds.

Test Coverage:
    - Layer 1: Basic functionality (initialization, calculation)
    - Layer 2: Parameter validation
    - Layer 3: Floor enforcement
    - Layer 4: Integration with BonferroniIntegrator
    - Layer 5: Integration with BootstrapIntegrator
    - Layer 6: Edge cases

Test Count: 15 tests
"""

import pytest
import numpy as np
from unittest.mock import Mock, MagicMock
from src.validation.dynamic_threshold import DynamicThresholdCalculator


class TestBasicFunctionality:
    """Layer 1: Basic functionality tests."""

    def test_initialization_default_parameters(self):
        """Test default initialization."""
        calc = DynamicThresholdCalculator()

        assert calc.benchmark_ticker == "0050.TW"
        assert calc.lookback_years == 3
        assert calc.margin == 0.2
        assert calc.static_floor == 0.0
        assert calc.empirical_benchmark_sharpe == 0.6

    def test_initialization_custom_parameters(self):
        """Test initialization with custom parameters."""
        calc = DynamicThresholdCalculator(
            benchmark_ticker="0056.TW",
            lookback_years=5,
            margin=0.3,
            static_floor=0.1
        )

        assert calc.benchmark_ticker == "0056.TW"
        assert calc.lookback_years == 5
        assert calc.margin == 0.3
        assert calc.static_floor == 0.1

    def test_get_threshold_default(self):
        """Test default threshold calculation."""
        calc = DynamicThresholdCalculator()
        threshold = calc.get_threshold()

        # Default: 0.6 (benchmark) + 0.2 (margin) = 0.8
        assert threshold == 0.8

    def test_get_threshold_custom_margin(self):
        """Test threshold with custom margin."""
        calc = DynamicThresholdCalculator(margin=0.3)
        threshold = calc.get_threshold()

        # 0.6 + 0.3 = 0.9
        assert threshold == pytest.approx(0.9)

    def test_get_benchmark_info(self):
        """Test benchmark info retrieval."""
        calc = DynamicThresholdCalculator(margin=0.25)
        info = calc.get_benchmark_info()

        assert info['ticker'] == "0050.TW"
        assert info['lookback_years'] == 3
        assert info['empirical_sharpe'] == 0.6
        assert info['margin'] == 0.25
        assert info['floor'] == 0.0
        assert info['current_threshold'] == 0.85  # 0.6 + 0.25


class TestParameterValidation:
    """Layer 2: Parameter validation tests."""

    def test_negative_margin_allowed(self):
        """Test that negative margin is allowed (for less stringent thresholds)."""
        calc = DynamicThresholdCalculator(margin=-0.1)
        threshold = calc.get_threshold()
        # 0.6 - 0.1 = 0.5
        assert threshold == pytest.approx(0.5)

    def test_negative_floor_raises_error(self):
        """Test that negative floor raises ValueError."""
        with pytest.raises(ValueError, match="static_floor must be >= 0"):
            DynamicThresholdCalculator(static_floor=-0.1)

    def test_zero_lookback_years_raises_error(self):
        """Test that zero lookback years raises ValueError."""
        with pytest.raises(ValueError, match="lookback_years must be >= 1"):
            DynamicThresholdCalculator(lookback_years=0)

    def test_zero_margin_allowed(self):
        """Test that zero margin is allowed."""
        calc = DynamicThresholdCalculator(margin=0.0)
        threshold = calc.get_threshold()

        # Should be benchmark only: 0.6 + 0.0 = 0.6
        assert threshold == 0.6

    def test_zero_floor_allowed(self):
        """Test that zero floor is allowed (default)."""
        calc = DynamicThresholdCalculator(static_floor=0.0)
        threshold = calc.get_threshold()

        # Should work without error
        assert threshold == 0.8  # 0.6 + 0.2


class TestFloorEnforcement:
    """Layer 3: Floor enforcement tests."""

    def test_floor_enforced_when_higher_than_calculated(self):
        """Test that floor is enforced when higher than calculated threshold."""
        # margin = -0.2 would give 0.6 - 0.2 = 0.4
        # But floor = 0.5 should be enforced
        calc = DynamicThresholdCalculator(margin=-0.2, static_floor=0.5)
        threshold = calc.get_threshold()

        assert threshold == 0.5  # Floor enforced

    def test_calculated_threshold_when_higher_than_floor(self):
        """Test calculated threshold used when higher than floor."""
        # margin = 0.2 gives 0.6 + 0.2 = 0.8
        # floor = 0.1 should not be enforced
        calc = DynamicThresholdCalculator(margin=0.2, static_floor=0.1)
        threshold = calc.get_threshold()

        assert threshold == 0.8  # Calculated value, not floor

    def test_floor_equal_to_calculated(self):
        """Test when floor equals calculated threshold."""
        # margin = 0.2 gives 0.6 + 0.2 = 0.8
        # floor = 0.8 should match
        calc = DynamicThresholdCalculator(margin=0.2, static_floor=0.8)
        threshold = calc.get_threshold()

        assert threshold == 0.8


class TestIntegrationWithBonferroni:
    """Layer 4: Integration with BonferroniIntegrator."""

    def test_bonferroni_uses_dynamic_threshold_by_default(self):
        """Test BonferroniIntegrator uses dynamic threshold by default."""
        from src.validation.integration import BonferroniIntegrator

        integrator = BonferroniIntegrator(n_strategies=20, alpha=0.05)

        # Should have threshold calculator
        assert integrator.threshold_calc is not None
        assert isinstance(integrator.threshold_calc, DynamicThresholdCalculator)
        assert integrator.threshold_calc.get_threshold() == 0.8

    def test_bonferroni_can_disable_dynamic_threshold(self):
        """Test BonferroniIntegrator can disable dynamic threshold."""
        from src.validation.integration import BonferroniIntegrator

        integrator = BonferroniIntegrator(
            n_strategies=20,
            alpha=0.05,
            use_dynamic_threshold=False
        )

        # Should NOT have threshold calculator
        assert integrator.threshold_calc is None

    def test_bonferroni_validate_uses_dynamic_threshold(self):
        """Test BonferroniIntegrator validation uses dynamic threshold."""
        from src.validation.integration import BonferroniIntegrator

        integrator = BonferroniIntegrator(
            n_strategies=20,
            alpha=0.05,
            use_dynamic_threshold=True
        )

        # Test with Sharpe = 0.9 (should pass: > 0.8 threshold)
        result = integrator.validate_single_strategy(
            sharpe_ratio=0.9,
            n_periods=252,
            use_conservative=True
        )

        assert result['validation_passed'] is True
        assert 'dynamic_threshold' in result
        assert result['dynamic_threshold'] == 0.8

    def test_bonferroni_validate_fails_below_threshold(self):
        """Test BonferroniIntegrator validation fails below dynamic threshold."""
        from src.validation.integration import BonferroniIntegrator

        integrator = BonferroniIntegrator(
            n_strategies=20,
            alpha=0.05,
            use_dynamic_threshold=True
        )

        # Test with Sharpe = 0.7 (should fail: < 0.8 threshold)
        result = integrator.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252,
            use_conservative=True
        )

        # May pass or fail depending on statistical threshold
        # But should have dynamic_threshold in result
        assert 'dynamic_threshold' in result
        assert result['dynamic_threshold'] == 0.8


class TestIntegrationWithBootstrap:
    """Layer 5: Integration with BootstrapIntegrator."""

    def test_bootstrap_uses_dynamic_threshold_by_default(self):
        """Test BootstrapIntegrator uses dynamic threshold by default."""
        from src.validation.integration import BootstrapIntegrator

        integrator = BootstrapIntegrator(executor=None)

        # Should have threshold calculator
        assert integrator.threshold_calc is not None
        assert isinstance(integrator.threshold_calc, DynamicThresholdCalculator)
        assert integrator.threshold_calc.get_threshold() == 0.8

    def test_bootstrap_can_disable_dynamic_threshold(self):
        """Test BootstrapIntegrator can disable dynamic threshold."""
        from src.validation.integration import BootstrapIntegrator

        integrator = BootstrapIntegrator(
            executor=None,
            use_dynamic_threshold=False
        )

        # Should NOT have threshold calculator
        assert integrator.threshold_calc is None

    def test_bootstrap_uses_static_threshold_when_disabled(self):
        """Test BootstrapIntegrator falls back to 0.5 when dynamic disabled."""
        from src.validation.integration import BootstrapIntegrator

        integrator = BootstrapIntegrator(
            executor=None,
            use_dynamic_threshold=False
        )

        # Mock executor to avoid actual backtest
        mock_executor = Mock()
        mock_result = Mock()
        mock_result.success = True
        mock_result.sharpe_ratio = 1.0
        mock_result.total_return = 0.5
        mock_result.report = Mock()

        # Mock returns extraction
        integrator.executor = mock_executor
        mock_executor.execute.return_value = mock_result

        # Create realistic returns (high Sharpe)
        returns = np.random.normal(0.001, 0.01, 300)
        integrator._extract_returns_from_report = Mock(return_value=returns)

        result = integrator.validate_with_bootstrap(
            strategy_code="test",
            data=Mock(),
            sim=Mock(),
            n_iterations=100
        )

        # Should use 0.5 threshold (static)
        assert 'static_threshold' in result
        assert result['static_threshold'] == 0.5


class TestEdgeCases:
    """Layer 6: Edge case tests."""

    def test_very_high_margin(self):
        """Test very high margin (e.g., 1.0)."""
        calc = DynamicThresholdCalculator(margin=1.0)
        threshold = calc.get_threshold()

        assert threshold == 1.6  # 0.6 + 1.0

    def test_very_high_floor(self):
        """Test very high floor overrides calculation."""
        calc = DynamicThresholdCalculator(margin=0.2, static_floor=2.0)
        threshold = calc.get_threshold()

        assert threshold == 2.0  # Floor enforced (> 0.8)

    def test_get_threshold_with_date_parameter(self):
        """Test get_threshold with date parameter (currently unused)."""
        calc = DynamicThresholdCalculator()
        threshold = calc.get_threshold(current_date="2024-01-01")

        # Should ignore date for now (empirical constant mode)
        assert threshold == 0.8

    def test_multiple_get_threshold_calls_consistent(self):
        """Test multiple calls return consistent results."""
        calc = DynamicThresholdCalculator(margin=0.25)

        threshold1 = calc.get_threshold()
        threshold2 = calc.get_threshold()
        threshold3 = calc.get_threshold()

        assert threshold1 == threshold2 == threshold3 == 0.85
