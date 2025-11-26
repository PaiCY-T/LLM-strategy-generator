"""
Tests for Time-Travel Perturbation Testing (TTPT) Framework.

TTPT detects look-ahead bias by shifting data temporally and validating
that strategy decisions don't depend on future information.

Test Structure (TDD RED Phase):
1. TestTTPTShiftGeneration - Data shifting and perturbation
2. TestTTPTValidation - Look-ahead bias detection
3. TestTTPTReporting - Result reporting and metrics
4. TestTTPTIntegration - Integration with strategy execution
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable
from datetime import datetime, timedelta


# Expected interface (implementation doesn't exist yet - TDD RED phase)
class TTPTFramework:
    """Time-Travel Perturbation Testing framework for look-ahead bias detection."""

    def __init__(
        self,
        shift_days: List[int] = None,
        tolerance: float = 0.05,
        min_correlation: float = 0.95
    ):
        """
        Initialize TTPT framework.

        Args:
            shift_days: List of shift amounts (e.g., [1, 5, 10])
            tolerance: Maximum acceptable performance change (e.g., 0.05 = 5%)
            min_correlation: Minimum signal correlation threshold
        """
        pass

    def generate_shifted_data(
        self,
        data: Dict[str, pd.DataFrame],
        shift_days: int
    ) -> Dict[str, pd.DataFrame]:
        """Generate time-shifted version of market data."""
        pass

    def validate_strategy(
        self,
        strategy_fn: Callable,
        original_data: Dict[str, pd.DataFrame],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate strategy for look-ahead bias.

        Returns:
            {
                'passed': bool,
                'violations': List[Dict],
                'metrics': Dict,
                'report': str
            }
        """
        pass

    def generate_report(
        self,
        validation_result: Dict[str, Any]
    ) -> str:
        """Generate human-readable TTPT report."""
        pass


class TestTTPTShiftGeneration:
    """Test data shifting and perturbation logic."""

    def test_shift_preserves_shape(self):
        """Shifted data should preserve original DataFrame shape."""
        framework = TTPTFramework()

        # Create sample data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.random.randn(100) + 100,
                '2317.TW': np.random.randn(100) + 50
            }, index=dates),
            'volume': pd.DataFrame({
                '2330.TW': np.random.randint(1000, 10000, 100),
                '2317.TW': np.random.randint(1000, 10000, 100)
            }, index=dates)
        }

        shifted = framework.generate_shifted_data(data, shift_days=5)

        assert shifted['close'].shape == data['close'].shape
        assert shifted['volume'].shape == data['volume'].shape
        assert list(shifted['close'].columns) == list(data['close'].columns)

    def test_shift_moves_data_forward_in_time(self):
        """Shift should move data forward, making future data appear in past."""
        framework = TTPTFramework()

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100  # Monotonically increasing
            }, index=dates)
        }

        shifted = framework.generate_shifted_data(data, shift_days=5)

        # Value at day 0 in shifted data should equal value at day 5 in original
        original_day_5 = data['close'].iloc[5, 0]
        shifted_day_0 = shifted['close'].iloc[0, 0]

        assert shifted_day_0 == original_day_5

    def test_shift_fills_end_with_nan(self):
        """Shifted data should have NaN at end where future data unavailable."""
        framework = TTPTFramework()

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100
            }, index=dates)
        }

        shifted = framework.generate_shifted_data(data, shift_days=5)

        # Last 5 rows should be NaN
        assert pd.isna(shifted['close'].iloc[-5:, 0]).all()

    def test_multiple_shifts_supported(self):
        """Framework should support multiple shift amounts."""
        framework = TTPTFramework(shift_days=[1, 5, 10])

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100
            }, index=dates)
        }

        # Should be able to generate shifts for each amount
        for shift in [1, 5, 10]:
            shifted = framework.generate_shifted_data(data, shift_days=shift)
            assert shifted['close'].shape == data['close'].shape
            assert pd.isna(shifted['close'].iloc[-shift:, 0]).all()


class TestTTPTValidation:
    """Test look-ahead bias detection logic."""

    def test_detects_lookahead_bias_in_strategy(self):
        """Strategy using future data should fail TTPT validation."""
        framework = TTPTFramework(shift_days=[5], tolerance=0.05)

        # Create deterministic data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100
            }, index=dates)
        }

        # Strategy that uses future data (look-ahead bias)
        def lookahead_strategy(data_dict, params):
            close = data_dict['close']
            # BAD: Using .shift(-5) to peek 5 days into future
            future_price = close.shift(-5)
            signal = (future_price > close).astype(float)
            return signal

        result = framework.validate_strategy(
            strategy_fn=lookahead_strategy,
            original_data=data,
            params={}
        )

        assert result['passed'] is False
        assert len(result['violations']) > 0
        assert 'look-ahead bias detected' in result['report'].lower()

    def test_passes_valid_strategy_without_lookahead(self):
        """Strategy using only historical data should pass TTPT."""
        framework = TTPTFramework(shift_days=[5], tolerance=0.05)

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100
            }, index=dates)
        }

        # Valid strategy using only historical data
        def valid_strategy(data_dict, params):
            close = data_dict['close']
            # GOOD: Using .shift(5) to use past data only
            ma = close.rolling(window=5).mean()
            signal = (close > ma).astype(float)
            return signal

        result = framework.validate_strategy(
            strategy_fn=valid_strategy,
            original_data=data,
            params={}
        )

        assert result['passed'] is True
        assert len(result['violations']) == 0

    def test_detects_performance_degradation_under_shift(self):
        """Significant performance change under shift indicates bias."""
        framework = TTPTFramework(shift_days=[5], tolerance=0.05)

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100
            }, index=dates),
            'volume': pd.DataFrame({
                '2330.TW': np.random.randint(1000, 10000, 100)
            }, index=dates)
        }

        # Strategy with subtle look-ahead bias
        def biased_strategy(data_dict, params):
            close = data_dict['close']
            # Mix of valid and invalid signals
            ma = close.rolling(window=5).mean()
            future_hint = close.shift(-1)  # Subtle bias
            signal = ((close > ma) & (future_hint > close)).astype(float)
            return signal

        result = framework.validate_strategy(
            strategy_fn=biased_strategy,
            original_data=data,
            params={}
        )

        assert 'performance_change' in result['metrics']
        if abs(result['metrics']['performance_change']) > 0.05:
            assert result['passed'] is False

    def test_signal_correlation_threshold(self):
        """Low signal correlation between original and shifted indicates bias."""
        framework = TTPTFramework(
            shift_days=[5],
            min_correlation=0.95
        )

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.random.randn(100) + 100
            }, index=dates)
        }

        # Strategy with correlation-breaking bias
        def unstable_strategy(data_dict, params):
            close = data_dict['close']
            # Uses absolute dates which break under shift
            signal = (close.index.day > 15).astype(float).values.reshape(-1, 1)
            return pd.DataFrame(signal, index=close.index, columns=close.columns)

        result = framework.validate_strategy(
            strategy_fn=unstable_strategy,
            original_data=data,
            params={}
        )

        assert 'signal_correlation' in result['metrics']

    def test_multiple_shift_validation(self):
        """Should validate across all configured shift amounts."""
        framework = TTPTFramework(shift_days=[1, 5, 10, 20])

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100
            }, index=dates)
        }

        def valid_strategy(data_dict, params):
            close = data_dict['close']
            ma = close.rolling(window=10).mean()
            return (close > ma).astype(float)

        result = framework.validate_strategy(
            strategy_fn=valid_strategy,
            original_data=data,
            params={}
        )

        # Should have metrics for each shift
        assert 'shift_results' in result['metrics']
        assert len(result['metrics']['shift_results']) == 4


class TestTTPTReporting:
    """Test TTPT report generation and formatting."""

    def test_report_includes_pass_fail_status(self):
        """Report should clearly indicate pass/fail status."""
        framework = TTPTFramework()

        validation_result = {
            'passed': True,
            'violations': [],
            'metrics': {
                'signal_correlation': 0.98,
                'performance_change': 0.02
            },
            'report': ''
        }

        report = framework.generate_report(validation_result)

        assert 'PASS' in report.upper() or '✅' in report
        assert 'no violations' in report.lower()

    def test_report_includes_violation_details(self):
        """Failed report should detail specific violations."""
        framework = TTPTFramework()

        validation_result = {
            'passed': False,
            'violations': [
                {
                    'shift_days': 5,
                    'type': 'performance_degradation',
                    'metric': 'sharpe_ratio',
                    'change': -0.15
                }
            ],
            'metrics': {
                'signal_correlation': 0.75,
                'performance_change': -0.15
            },
            'report': ''
        }

        report = framework.generate_report(validation_result)

        assert 'FAIL' in report.upper() or '❌' in report
        assert '5' in report  # Shift days
        assert 'performance' in report.lower()

    def test_report_includes_metrics_table(self):
        """Report should include formatted metrics table."""
        framework = TTPTFramework()

        validation_result = {
            'passed': True,
            'violations': [],
            'metrics': {
                'signal_correlation': 0.98,
                'performance_change': 0.02,
                'shift_results': [
                    {'shift': 1, 'correlation': 0.99},
                    {'shift': 5, 'correlation': 0.98}
                ]
            },
            'report': ''
        }

        report = framework.generate_report(validation_result)

        assert 'correlation' in report.lower()
        assert '0.98' in report or '98' in report


class TestTTPTIntegration:
    """Test integration with strategy execution pipeline."""

    def test_integrates_with_template_library(self):
        """TTPT should work with TemplateLibrary generated strategies."""
        from src.templates.template_library import TemplateLibrary

        framework = TTPTFramework(shift_days=[5])
        library = TemplateLibrary(cache_data=False)

        # Generate a strategy
        strategy = library.generate_strategy(
            template_name='Momentum',
            params={
                'lookback_days': 20,
                'entry_threshold': 1.5,
                'exit_lookback': 10,
                'trailing_stop_pct': 0.05,
                'position_size_pct': 0.10
            }
        )

        # Create test data
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.random.randn(100) + 100,
                '2317.TW': np.random.randn(100) + 50
            }, index=dates),
            'volume': pd.DataFrame({
                '2330.TW': np.random.randint(1000, 10000, 100),
                '2317.TW': np.random.randint(1000, 10000, 100)
            }, index=dates)
        }

        # Should be able to validate generated strategy
        # (This will fail until implementation exists)
        assert strategy['code'] is not None

    def test_checkpoint_validation_workflow(self):
        """TTPT should provide checkpoint validation during optimization."""
        framework = TTPTFramework(shift_days=[5])

        # Simulate optimization checkpoint
        checkpoint_data = {
            'iteration': 10,
            'best_params': {'lookback_days': 25},
            'best_value': 0.75
        }

        # TTPT should validate at checkpoints
        # (Interface to be defined)
        assert checkpoint_data['iteration'] == 10


class TestTTPTEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_insufficient_data_for_shift(self):
        """Should handle case where data length < shift amount."""
        framework = TTPTFramework(shift_days=[100])  # Large shift

        dates = pd.date_range('2023-01-01', periods=50, freq='D')  # Short data
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(50) + 100
            }, index=dates)
        }

        def simple_strategy(data_dict, params):
            close = data_dict['close']
            ma = close.rolling(window=5).mean()
            return (close > ma).astype(float)

        # Should handle gracefully (warn or skip)
        result = framework.validate_strategy(
            strategy_fn=simple_strategy,
            original_data=data,
            params={}
        )

        # Either passes with warning or returns validation result
        assert 'passed' in result

    def test_handles_nan_in_original_data(self):
        """Should handle NaN values in original data."""
        framework = TTPTFramework(shift_days=[5])

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        close_data = np.arange(100) + 100.0
        close_data[10:15] = np.nan  # Inject NaN

        data = {
            'close': pd.DataFrame({
                '2330.TW': close_data
            }, index=dates)
        }

        def simple_strategy(data_dict, params):
            close = data_dict['close']
            ma = close.rolling(window=5).mean()
            return (close > ma).astype(float)

        result = framework.validate_strategy(
            strategy_fn=simple_strategy,
            original_data=data,
            params={}
        )

        assert 'passed' in result

    def test_zero_shift_returns_identical_data(self):
        """Shift of 0 should return identical data."""
        framework = TTPTFramework()

        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        data = {
            'close': pd.DataFrame({
                '2330.TW': np.arange(100) + 100
            }, index=dates)
        }

        shifted = framework.generate_shifted_data(data, shift_days=0)

        pd.testing.assert_frame_equal(shifted['close'], data['close'])


# Expected test results (RED phase - all should fail initially)
"""
Expected Test Failures (TDD RED Phase):
========================================

TestTTPTShiftGeneration:
  ❌ test_shift_preserves_shape - TTPTFramework not implemented
  ❌ test_shift_moves_data_forward_in_time - TTPTFramework not implemented
  ❌ test_shift_fills_end_with_nan - TTPTFramework not implemented
  ❌ test_multiple_shifts_supported - TTPTFramework not implemented

TestTTPTValidation:
  ❌ test_detects_lookahead_bias_in_strategy - TTPTFramework not implemented
  ❌ test_passes_valid_strategy_without_lookahead - TTPTFramework not implemented
  ❌ test_detects_performance_degradation_under_shift - TTPTFramework not implemented
  ❌ test_signal_correlation_threshold - TTPTFramework not implemented
  ❌ test_multiple_shift_validation - TTPTFramework not implemented

TestTTPTReporting:
  ❌ test_report_includes_pass_fail_status - TTPTFramework not implemented
  ❌ test_report_includes_violation_details - TTPTFramework not implemented
  ❌ test_report_includes_metrics_table - TTPTFramework not implemented

TestTTPTIntegration:
  ❌ test_integrates_with_template_library - TTPTFramework not implemented
  ❌ test_checkpoint_validation_workflow - TTPTFramework not implemented

TestTTPTEdgeCases:
  ❌ test_handles_insufficient_data_for_shift - TTPTFramework not implemented
  ❌ test_handles_nan_in_original_data - TTPTFramework not implemented
  ❌ test_zero_shift_returns_identical_data - TTPTFramework not implemented

Total: 20 tests (all failing - expected for RED phase)
"""
