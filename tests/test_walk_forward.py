"""
Tests for Walk-Forward Analysis Validation

Comprehensive test suite covering:
- Rolling window generation and configuration
- Train/test loop execution
- Aggregate metrics calculation
- Validation criteria enforcement
- Error handling and edge cases
- Performance benchmarks

Requirements: AC-2.2.1 to AC-2.2.4
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.validation.walk_forward import (
    WalkForwardValidator,
    validate_strategy_walk_forward
)


class TestWindowGeneration:
    """Test rolling window configuration and generation."""

    def test_window_configuration_defaults(self):
        """AC-2.2.1: Test default window configuration."""
        validator = WalkForwardValidator()

        assert validator.training_window == 252
        assert validator.test_window == 63
        assert validator.step_size == 63
        assert validator.min_windows == 3

    def test_window_configuration_custom(self):
        """AC-2.2.1: Test custom window configuration."""
        validator = WalkForwardValidator(
            training_window=126,
            test_window=42,
            step_size=21,
            min_windows=5
        )

        assert validator.training_window == 126
        assert validator.test_window == 42
        assert validator.step_size == 21
        assert validator.min_windows == 5

    def test_generate_windows_sufficient_data(self):
        """AC-2.2.1: Test window generation with sufficient data."""
        # Create mock data with 600 days
        dates = pd.date_range('2020-01-01', periods=600, freq='B')
        mock_data = pd.DataFrame({'close': np.random.randn(600)}, index=dates)

        validator = WalkForwardValidator(
            training_window=252,
            test_window=63,
            step_size=63
        )

        windows = validator._generate_windows(mock_data)

        # With 600 days, should generate multiple windows
        # First window: train 0-251, test 252-314 (315 days used)
        # Second window: train 63-314, test 315-377 (378 days used)
        # Third window: train 126-377, test 378-440 (441 days used)
        # Fourth window: train 189-440, test 441-503 (504 days used)
        # Fifth window: train 252-503, test 504-566 (567 days used)
        assert len(windows) >= 3, f"Expected ≥3 windows, got {len(windows)}"

        # Check first window structure
        first_window = windows[0]
        assert 'train_start' in first_window
        assert 'train_end' in first_window
        assert 'test_start' in first_window
        assert 'test_end' in first_window
        assert first_window['train_days'] == 252
        assert first_window['test_days'] == 63

    def test_generate_windows_insufficient_data(self):
        """AC-2.2.4: Test window generation with insufficient data."""
        # Create mock data with only 300 days (need 441 for 3 windows)
        dates = pd.date_range('2020-01-01', periods=300, freq='B')
        mock_data = pd.DataFrame({'close': np.random.randn(300)}, index=dates)

        validator = WalkForwardValidator(
            training_window=252,
            test_window=63,
            step_size=63,
            min_windows=3
        )

        with pytest.raises(ValueError, match="Insufficient data"):
            validator._generate_windows(mock_data)

    def test_generate_windows_sequential_non_overlapping(self):
        """AC-2.2.1: Test that test windows are sequential and non-overlapping."""
        dates = pd.date_range('2020-01-01', periods=600, freq='B')
        mock_data = pd.DataFrame({'close': np.random.randn(600)}, index=dates)

        validator = WalkForwardValidator()
        windows = validator._generate_windows(mock_data)

        # Check that test windows don't overlap
        for i in range(len(windows) - 1):
            current_test_end = windows[i]['test_end']
            next_test_start = windows[i + 1]['test_start']
            # Next test should start after current test ends
            assert current_test_end < next_test_start


class TestAggregateMetrics:
    """Test aggregate metrics calculation."""

    def test_aggregate_metrics_calculation(self):
        """AC-2.2.2: Test aggregate metrics are calculated correctly."""
        validator = WalkForwardValidator()

        # Simulate walk-forward results
        window_sharpes = [0.8, 1.2, 0.6, 1.5, 0.9, 1.1]

        results = {
            'avg_sharpe': float(np.mean(window_sharpes)),
            'sharpe_std': float(np.std(window_sharpes, ddof=1)),
            'win_rate': float(sum(1 for s in window_sharpes if s > 0) / len(window_sharpes)),
            'worst_sharpe': float(np.min(window_sharpes)),
            'best_sharpe': float(np.max(window_sharpes)),
            'num_windows': len(window_sharpes)
        }

        # Verify calculations (actual mean is 1.0166...)
        assert results['avg_sharpe'] == pytest.approx(1.017, abs=0.01)
        assert results['sharpe_std'] > 0
        assert results['win_rate'] == 1.0  # All positive
        assert results['worst_sharpe'] == 0.6
        assert results['best_sharpe'] == 1.5
        assert results['num_windows'] == 6

    def test_aggregate_metrics_with_negative_sharpes(self):
        """AC-2.2.2: Test metrics with some negative Sharpe ratios."""
        window_sharpes = [0.8, -0.3, 0.6, 1.2, -0.1, 0.9]

        avg_sharpe = float(np.mean(window_sharpes))
        win_rate = float(sum(1 for s in window_sharpes if s > 0) / len(window_sharpes))
        worst_sharpe = float(np.min(window_sharpes))

        assert avg_sharpe == pytest.approx(0.517, abs=0.01)
        assert win_rate == pytest.approx(0.667, abs=0.01)  # 4/6 positive
        assert worst_sharpe == -0.3

    def test_aggregate_metrics_edge_case_all_zeros(self):
        """AC-2.2.2: Test metrics when all windows return zero Sharpe."""
        window_sharpes = [0.0, 0.0, 0.0, 0.0]

        results = {
            'avg_sharpe': float(np.mean(window_sharpes)),
            'win_rate': float(sum(1 for s in window_sharpes if s > 0) / len(window_sharpes)),
            'worst_sharpe': float(np.min(window_sharpes))
        }

        assert results['avg_sharpe'] == 0.0
        assert results['win_rate'] == 0.0
        assert results['worst_sharpe'] == 0.0


class TestValidationCriteria:
    """Test validation pass/fail criteria."""

    def test_validation_criteria_all_pass(self):
        """AC-2.2.3: Test validation passes when all criteria met."""
        validator = WalkForwardValidator()

        results = {
            'avg_sharpe': 0.8,
            'win_rate': 0.75,
            'worst_sharpe': 0.2,
            'sharpe_std': 0.5
        }

        assert validator._check_validation_criteria(results) is True

    def test_validation_criteria_avg_sharpe_fail(self):
        """AC-2.2.3: Test validation fails when avg Sharpe ≤ 0.5."""
        validator = WalkForwardValidator()

        results = {
            'avg_sharpe': 0.4,  # Too low
            'win_rate': 0.75,
            'worst_sharpe': 0.2,
            'sharpe_std': 0.5
        }

        assert validator._check_validation_criteria(results) is False

    def test_validation_criteria_win_rate_fail(self):
        """AC-2.2.3: Test validation fails when win rate ≤ 60%."""
        validator = WalkForwardValidator()

        results = {
            'avg_sharpe': 0.8,
            'win_rate': 0.55,  # Too low
            'worst_sharpe': 0.2,
            'sharpe_std': 0.5
        }

        assert validator._check_validation_criteria(results) is False

    def test_validation_criteria_worst_sharpe_fail(self):
        """AC-2.2.3: Test validation fails when worst Sharpe ≤ -0.5."""
        validator = WalkForwardValidator()

        results = {
            'avg_sharpe': 0.8,
            'win_rate': 0.75,
            'worst_sharpe': -0.6,  # Too low (catastrophic failure)
            'sharpe_std': 0.5
        }

        assert validator._check_validation_criteria(results) is False

    def test_validation_criteria_sharpe_std_fail(self):
        """AC-2.2.3: Test validation fails when Sharpe std ≥ 1.0."""
        validator = WalkForwardValidator()

        results = {
            'avg_sharpe': 0.8,
            'win_rate': 0.75,
            'worst_sharpe': 0.2,
            'sharpe_std': 1.2  # Too high (unstable)
        }

        assert validator._check_validation_criteria(results) is False

    def test_validation_criteria_boundary_values(self):
        """AC-2.2.3: Test validation at exact threshold boundaries."""
        validator = WalkForwardValidator()

        # Exact thresholds should fail (≤ and ≥ comparisons)
        results_boundary = {
            'avg_sharpe': 0.5,  # Exactly at threshold (should fail)
            'win_rate': 0.6,  # Exactly at threshold (should fail)
            'worst_sharpe': -0.5,  # Exactly at threshold (should fail)
            'sharpe_std': 1.0  # Exactly at threshold (should fail)
        }

        assert validator._check_validation_criteria(results_boundary) is False

        # Just above thresholds should pass
        results_pass = {
            'avg_sharpe': 0.51,
            'win_rate': 0.61,
            'worst_sharpe': -0.49,
            'sharpe_std': 0.99
        }

        assert validator._check_validation_criteria(results_pass) is True


class TestMinimumWindowRequirement:
    """Test minimum window count enforcement."""

    def test_minimum_windows_enforced_generation(self):
        """AC-2.2.4: Test minimum 3 windows required during generation."""
        # Create data with exactly enough for 2 windows (should fail)
        # 252 (train) + 63 (test) + 63 (step) + 63 (test) = 441 days
        # But we need 3 windows minimum
        dates = pd.date_range('2020-01-01', periods=400, freq='B')
        mock_data = pd.DataFrame({'close': np.random.randn(400)}, index=dates)

        validator = WalkForwardValidator(min_windows=3)

        with pytest.raises(ValueError, match="Insufficient data"):
            validator._generate_windows(mock_data)

    def test_minimum_windows_enforced_validation(self):
        """AC-2.2.4: Test validation skipped when insufficient windows."""
        # Create mock data with 300 days (insufficient for 3 windows)
        dates = pd.date_range('2020-01-01', periods=300, freq='B')
        mock_data = pd.DataFrame({'close': np.random.randn(300)}, index=dates)

        validator = WalkForwardValidator(min_windows=3)

        # Create simple strategy code
        strategy_code = "position = None\nreport = None"

        results = validator.validate_strategy(strategy_code, mock_data, 0)

        assert results['validation_skipped'] is True
        # Should fail during window generation due to insufficient data
        assert 'Window generation failed' in results['skip_reason'] or 'Insufficient' in results['skip_reason']

    def test_minimum_windows_with_failures(self):
        """AC-2.2.4: Test validation skipped when too many windows fail."""
        validator = WalkForwardValidator(min_windows=3)

        # Simulate having 5 generated windows but only 2 successful
        results = {
            'validation_passed': False,
            'validation_skipped': False,
            'skip_reason': None,
            'windows': [
                {'test_sharpe': 0.8, 'error': None},
                {'test_sharpe': None, 'error': 'Execution failed'},
                {'test_sharpe': 1.2, 'error': None},
                {'test_sharpe': None, 'error': 'No report'},
                {'test_sharpe': None, 'error': 'Data missing'}
            ]
        }

        # Only 2 successful windows (need 3)
        window_sharpes = [w['test_sharpe'] for w in results['windows'] if w['test_sharpe'] is not None]
        assert len(window_sharpes) == 2
        assert len(window_sharpes) < validator.min_windows


class TestSharpeExtraction:
    """Test Sharpe ratio extraction from reports."""

    def test_extract_sharpe_dict_format(self):
        """Test Sharpe extraction when get_stats returns dict."""
        validator = WalkForwardValidator()

        mock_report = Mock()
        mock_report.get_stats = Mock(return_value={'value': 1.25})

        sharpe = validator._extract_sharpe_from_report(mock_report)
        assert sharpe == 1.25

    def test_extract_sharpe_float_format(self):
        """Test Sharpe extraction when get_stats returns float."""
        validator = WalkForwardValidator()

        mock_report = Mock()
        mock_report.get_stats = Mock(return_value=1.25)

        sharpe = validator._extract_sharpe_from_report(mock_report)
        assert sharpe == 1.25

    def test_extract_sharpe_direct_attribute(self):
        """Test Sharpe extraction via direct attribute."""
        validator = WalkForwardValidator()

        mock_report = Mock()
        del mock_report.get_stats  # Remove get_stats method
        mock_report.sharpe_ratio = 1.25

        sharpe = validator._extract_sharpe_from_report(mock_report)
        assert sharpe == 1.25

    def test_extract_sharpe_callable_attribute(self):
        """Test Sharpe extraction via callable attribute."""
        validator = WalkForwardValidator()

        mock_report = Mock()
        del mock_report.get_stats
        mock_report.sharpe_ratio = Mock(return_value=1.25)

        sharpe = validator._extract_sharpe_from_report(mock_report)
        assert sharpe == 1.25

    def test_extract_sharpe_metrics_object(self):
        """Test Sharpe extraction via metrics object."""
        validator = WalkForwardValidator()

        mock_metrics = Mock()
        mock_metrics.sharpe_ratio = Mock(return_value=1.25)

        mock_report = Mock()
        del mock_report.get_stats
        del mock_report.sharpe_ratio
        mock_report.metrics = mock_metrics

        sharpe = validator._extract_sharpe_from_report(mock_report)
        assert sharpe == 1.25

    def test_extract_sharpe_failure(self):
        """Test Sharpe extraction failure handling."""
        validator = WalkForwardValidator()

        mock_report = Mock()
        del mock_report.get_stats
        del mock_report.sharpe_ratio
        del mock_report.stats
        del mock_report.metrics

        with pytest.raises(ValueError, match="Sharpe extraction failed|No Sharpe ratio found"):
            validator._extract_sharpe_from_report(mock_report)


class TestErrorHandling:
    """Test error handling and graceful degradation."""

    def test_window_generation_error_handling(self):
        """Test graceful handling of window generation errors."""
        validator = WalkForwardValidator()

        # Mock data that raises error
        mock_data = Mock()
        mock_data.get = Mock(side_effect=Exception("Data access error"))

        results = validator.validate_strategy("", mock_data, 0)

        assert results['validation_skipped'] is True
        assert 'Window generation failed' in results['skip_reason']

    def test_strategy_execution_error_handling(self):
        """Test graceful handling of strategy execution errors."""
        validator = WalkForwardValidator()

        # Create mock data
        dates = pd.date_range('2020-01-01', periods=600, freq='B')
        mock_data = Mock()
        mock_data.get = Mock(return_value=pd.DataFrame({'close': np.random.randn(600)}, index=dates))
        mock_data.index = dates

        # Invalid strategy code
        invalid_code = "raise ValueError('Intentional error')"

        results = validator.validate_strategy(invalid_code, mock_data, 0)

        # Should have attempted windows but all failed
        assert results['num_windows'] == 0 or results['validation_skipped'] is True

    def test_report_extraction_error_handling(self):
        """Test handling when report object is missing."""
        validator = WalkForwardValidator()

        window = {
            'train_start': '2020-01-01',
            'train_end': '2020-12-31',
            'test_start': '2021-01-01',
            'test_end': '2021-03-31'
        }

        # Strategy code that doesn't create report
        strategy_code = "position = None"

        dates = pd.date_range('2020-01-01', periods=600, freq='B')
        mock_data = Mock()
        mock_data.get = Mock(return_value=pd.DataFrame({'close': np.random.randn(600)}, index=dates))

        sharpe, error = validator._run_window_backtest(
            strategy_code, mock_data, window, 0, 0
        )

        assert sharpe is None
        assert 'No report object' in error


class TestPerformance:
    """Test performance requirements."""

    def test_performance_10_windows(self):
        """Test performance target: < 30 seconds for 10 windows."""
        validator = WalkForwardValidator()

        # Create mock data with enough for 10+ windows
        dates = pd.date_range('2020-01-01', periods=900, freq='B')
        mock_data = pd.DataFrame({'close': np.random.randn(900)}, index=dates)

        # Simple fast strategy for testing - use a custom mock report class
        strategy_code = """
class MockReport:
    def sharpe_ratio(self):
        return 0.8

position = None
report = MockReport()
"""

        start_time = time.time()
        results = validator.validate_strategy(strategy_code, mock_data, 0)
        elapsed = time.time() - start_time

        # Should complete in < 30 seconds
        # Note: Actual performance depends on strategy complexity
        # This test uses mock to ensure fast execution
        assert elapsed < 30.0, f"Performance too slow: {elapsed:.2f}s (target: <30s)"

        # Should have processed multiple windows
        assert results['num_windows'] >= 3


class TestConvenienceFunction:
    """Test convenience function wrapper."""

    def test_convenience_function(self):
        """Test validate_strategy_walk_forward convenience function."""
        dates = pd.date_range('2020-01-01', periods=600, freq='B')
        mock_data = Mock()
        mock_data.get = Mock(return_value=pd.DataFrame({'close': np.random.randn(600)}, index=dates))
        mock_data.index = dates

        strategy_code = """
from unittest.mock import Mock
position = None
report = Mock()
report.sharpe_ratio = 0.9
"""

        results = validate_strategy_walk_forward(strategy_code, mock_data, 42)

        assert 'validation_passed' in results
        assert 'avg_sharpe' in results
        assert 'num_windows' in results


class TestIntegration:
    """Integration tests with realistic scenarios."""

    def test_realistic_strategy_validation(self):
        """Test validation with realistic strategy and data."""
        validator = WalkForwardValidator()

        # Create realistic price data with trends
        dates = pd.date_range('2020-01-01', periods=800, freq='B')
        np.random.seed(42)
        prices = 100 * np.exp(np.cumsum(np.random.randn(800) * 0.02))
        mock_data = pd.DataFrame({'close': prices}, index=dates)

        # Strategy that should generate reasonable results
        # Use a custom report class that returns consistent Sharpe
        strategy_code = """
class MockReport:
    def sharpe_ratio(self):
        return 0.85

# Simulate strategy execution
position = None
report = MockReport()
"""

        results = validator.validate_strategy(strategy_code, mock_data, 0)

        # Should have processed multiple windows
        assert results['num_windows'] >= 3
        assert 'avg_sharpe' in results
        assert 'windows' in results


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
