"""
Test Suite for Data Split Validation

Tests the train/validation/test temporal split validation component.

Requirements: AC-2.1.1 to AC-2.1.6
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation.data_split import DataSplitValidator, validate_strategy_with_data_split


class TestDataSplitValidator:
    """Test DataSplitValidator class initialization and configuration."""

    def test_validator_initialization(self):
        """Test validator initializes with correct period configurations."""
        validator = DataSplitValidator()

        assert validator.TRAIN_START == "2018-01-01"
        assert validator.TRAIN_END == "2020-12-31"
        assert validator.VALIDATION_START == "2021-01-01"
        assert validator.VALIDATION_END == "2022-12-31"
        assert validator.TEST_START == "2023-01-01"
        assert validator.TEST_END == "2024-12-31"

        assert len(validator.periods) == 3
        assert 'training' in validator.periods
        assert 'validation' in validator.periods
        assert 'test' in validator.periods

    def test_validation_criteria_constants(self):
        """Test validation criteria constants are correctly set."""
        validator = DataSplitValidator()

        assert validator.MIN_VALIDATION_SHARPE == 1.0
        assert validator.MIN_CONSISTENCY == 0.6
        assert validator.MIN_DEGRADATION_RATIO == 0.7
        assert validator.MIN_TRADING_DAYS == 252


class TestConsistencyCalculation:
    """Test consistency score calculation (AC-2.1.2)."""

    def test_consistency_with_identical_values(self):
        """Identical Sharpe ratios should have consistency = 1.0."""
        validator = DataSplitValidator()
        sharpes = [1.5, 1.5, 1.5]

        consistency = validator._calculate_consistency(sharpes)

        assert consistency == 1.0

    def test_consistency_with_varying_values(self):
        """Varying Sharpe ratios should have 0 < consistency < 1."""
        validator = DataSplitValidator()
        sharpes = [1.0, 1.5, 2.0]

        consistency = validator._calculate_consistency(sharpes)

        assert 0.0 < consistency < 1.0

    def test_consistency_with_high_variance(self):
        """High variance should result in low consistency."""
        validator = DataSplitValidator()
        sharpes = [0.5, 2.0, -0.5]

        consistency = validator._calculate_consistency(sharpes)

        assert consistency < 0.5

    def test_consistency_with_insufficient_data(self):
        """Less than 2 values should return 0.0."""
        validator = DataSplitValidator()

        assert validator._calculate_consistency([1.5]) == 0.0
        assert validator._calculate_consistency([]) == 0.0

    def test_consistency_with_zero_mean(self):
        """Zero mean should return 0.0 to avoid division by zero."""
        validator = DataSplitValidator()
        sharpes = [1.0, -1.0]

        consistency = validator._calculate_consistency(sharpes)

        assert consistency == 0.0


class TestValidationCriteria:
    """Test validation pass/fail criteria (AC-2.1.3, AC-2.1.4)."""

    def test_all_criteria_pass(self):
        """Test strategy passes when all criteria are met."""
        validator = DataSplitValidator()
        results = {
            'sharpes': {
                'training': 1.5,
                'validation': 1.2,
                'test': 1.1
            },
            'consistency': 0.85,
            'degradation_ratio': 0.8
        }

        passed = validator._check_validation_criteria(results)

        assert passed is True

    def test_validation_sharpe_too_low(self):
        """Test fails when validation Sharpe <= 1.0."""
        validator = DataSplitValidator()
        results = {
            'sharpes': {
                'training': 1.5,
                'validation': 0.9,  # Too low
                'test': 1.1
            },
            'consistency': 0.85,
            'degradation_ratio': 0.8
        }

        passed = validator._check_validation_criteria(results)

        assert passed is False

    def test_consistency_too_low(self):
        """Test fails when consistency <= 0.6."""
        validator = DataSplitValidator()
        results = {
            'sharpes': {
                'training': 1.5,
                'validation': 1.2,
                'test': 1.1
            },
            'consistency': 0.5,  # Too low
            'degradation_ratio': 0.8
        }

        passed = validator._check_validation_criteria(results)

        assert passed is False

    def test_degradation_ratio_too_low(self):
        """Test fails when degradation ratio <= 0.7."""
        validator = DataSplitValidator()
        results = {
            'sharpes': {
                'training': 2.0,
                'validation': 1.2,  # 1.2/2.0 = 0.6 < 0.7
                'test': 1.1
            },
            'consistency': 0.85,
            'degradation_ratio': 0.6  # Too low
        }

        passed = validator._check_validation_criteria(results)

        assert passed is False

    def test_missing_validation_sharpe(self):
        """Test fails when validation Sharpe is None."""
        validator = DataSplitValidator()
        results = {
            'sharpes': {
                'training': 1.5,
                'validation': None,  # Missing
                'test': 1.1
            },
            'consistency': 0.85,
            'degradation_ratio': 0.8
        }

        passed = validator._check_validation_criteria(results)

        assert passed is False


class TestSharpeExtraction:
    """Test Sharpe ratio extraction from report objects."""

    def test_extract_from_dict_get_stats(self):
        """Test extraction when get_stats() returns dict."""
        validator = DataSplitValidator()

        mock_report = Mock()
        mock_report.get_stats.return_value = {'sharpe_ratio': 1.5}

        sharpe = validator._extract_sharpe_from_report(mock_report)

        assert sharpe == 1.5

    def test_extract_from_float_get_stats(self):
        """Test extraction when get_stats() returns float."""
        validator = DataSplitValidator()

        mock_report = Mock()
        mock_report.get_stats.return_value = 1.5

        sharpe = validator._extract_sharpe_from_report(mock_report)

        assert sharpe == 1.5

    def test_extract_from_attribute(self):
        """Test extraction from direct attribute."""
        validator = DataSplitValidator()

        mock_report = Mock()
        del mock_report.get_stats  # Remove method
        mock_report.sharpe_ratio = 1.5

        sharpe = validator._extract_sharpe_from_report(mock_report)

        assert sharpe == 1.5

    def test_extract_from_stats_attribute(self):
        """Test extraction from stats attribute."""
        validator = DataSplitValidator()

        mock_report = Mock()
        del mock_report.get_stats
        del mock_report.sharpe_ratio
        mock_report.stats = {'sharpe_ratio': 1.5}

        sharpe = validator._extract_sharpe_from_report(mock_report)

        assert sharpe == 1.5

    def test_extract_fails_when_not_found(self):
        """Test raises ValueError when Sharpe not found."""
        validator = DataSplitValidator()

        mock_report = Mock(spec=[])  # Empty mock

        with pytest.raises(ValueError, match="No Sharpe ratio found"):
            validator._extract_sharpe_from_report(mock_report)


class TestValidateStrategy:
    """Test complete strategy validation workflow (AC-2.1.1, AC-2.1.5, AC-2.1.6)."""

    def test_validation_with_all_periods_success(self):
        """Test validation passes when all periods execute successfully."""
        validator = DataSplitValidator()

        # Mock strategy code and data
        strategy_code = "# Mock strategy"
        mock_data = Mock()

        # Mock _run_period_backtest to return success
        with patch.object(validator, '_run_period_backtest') as mock_run:
            mock_run.side_effect = [
                (1.5, None),  # Training: success
                (1.2, None),  # Validation: success
                (1.1, None),  # Test: success
            ]

            results = validator.validate_strategy(strategy_code, mock_data, iteration_num=42)

            assert results['validation_passed'] is True
            assert results['validation_skipped'] is False
            assert results['skip_reason'] is None
            assert len(results['periods_tested']) == 3
            assert len(results['periods_skipped']) == 0
            assert results['sharpes']['training'] == 1.5
            assert results['sharpes']['validation'] == 1.2
            assert results['sharpes']['test'] == 1.1
            assert results['consistency'] > 0.6
            assert results['degradation_ratio'] == 1.2 / 1.5

    def test_validation_with_one_period_failure(self):
        """Test validation continues with partial results when one period fails (AC-2.1.6)."""
        validator = DataSplitValidator()

        strategy_code = "# Mock strategy"
        mock_data = Mock()

        with patch.object(validator, '_run_period_backtest') as mock_run:
            mock_run.side_effect = [
                (1.5, None),  # Training: success
                (None, "Insufficient data"),  # Validation: failed
                (1.1, None),  # Test: success
            ]

            results = validator.validate_strategy(strategy_code, mock_data)

            assert len(results['periods_tested']) == 2
            assert len(results['periods_skipped']) == 1
            assert results['sharpes']['validation'] is None
            assert results['periods_skipped'][0]['period'] == 'validation'
            assert results['periods_skipped'][0]['reason'] == "Insufficient data"

    def test_validation_skipped_with_insufficient_periods(self):
        """Test validation skipped when < 2 periods succeed (AC-2.1.5)."""
        validator = DataSplitValidator()

        strategy_code = "# Mock strategy"
        mock_data = Mock()

        with patch.object(validator, '_run_period_backtest') as mock_run:
            mock_run.side_effect = [
                (1.5, None),  # Training: success
                (None, "Error 1"),  # Validation: failed
                (None, "Error 2"),  # Test: failed
            ]

            results = validator.validate_strategy(strategy_code, mock_data)

            assert results['validation_skipped'] is True
            assert 'Insufficient periods tested' in results['skip_reason']
            assert results['validation_passed'] is False

    def test_validation_fails_low_validation_sharpe(self):
        """Test validation fails when criteria not met."""
        validator = DataSplitValidator()

        strategy_code = "# Mock strategy"
        mock_data = Mock()

        with patch.object(validator, '_run_period_backtest') as mock_run:
            mock_run.side_effect = [
                (1.5, None),
                (0.8, None),  # Validation Sharpe too low (<1.0)
                (0.9, None),
            ]

            results = validator.validate_strategy(strategy_code, mock_data)

            assert results['validation_passed'] is False
            assert results['validation_skipped'] is False


class TestConvenienceFunction:
    """Test convenience function for validation."""

    def test_validate_strategy_with_data_split(self):
        """Test convenience function calls validator correctly."""
        strategy_code = "# Mock strategy"
        mock_data = Mock()

        with patch('src.validation.data_split.DataSplitValidator') as MockValidator:
            mock_instance = MockValidator.return_value
            mock_instance.validate_strategy.return_value = {'validation_passed': True}

            result = validate_strategy_with_data_split(strategy_code, mock_data, iteration_num=42)

            assert result['validation_passed'] is True
            mock_instance.validate_strategy.assert_called_once_with(strategy_code, mock_data, 42)


class TestErrorHandling:
    """Test error handling scenarios (AC-2.1.5, AC-2.1.6)."""

    def test_handles_insufficient_data_error(self):
        """Test graceful handling when data is insufficient."""
        validator = DataSplitValidator()

        with patch.object(validator, '_has_sufficient_data', return_value=False):
            sharpe, error = validator._run_period_backtest(
                strategy_code="# code",
                data=Mock(),
                start_date="2018-01-01",
                end_date="2020-12-31",
                period_name="training",
                iteration_num=0
            )

            assert sharpe is None
            assert "Insufficient data" in error

    def test_handles_execution_error(self):
        """Test graceful handling when strategy execution fails."""
        validator = DataSplitValidator()

        with patch.object(validator, '_has_sufficient_data', return_value=True):
            # Strategy code that raises exception
            strategy_code = "raise ValueError('Execution error')"

            sharpe, error = validator._run_period_backtest(
                strategy_code=strategy_code,
                data=Mock(),
                start_date="2018-01-01",
                end_date="2020-12-31",
                period_name="training",
                iteration_num=0
            )

            assert sharpe is None
            assert error is not None
            assert "Execution error" in error

    def test_handles_metric_extraction_error(self):
        """Test graceful handling when metric extraction fails."""
        validator = DataSplitValidator()

        with patch.object(validator, '_has_sufficient_data', return_value=True):
            with patch.object(validator, '_extract_sharpe_from_report', side_effect=ValueError("Extraction failed")):
                # Mock successful execution
                strategy_code = "report = Mock()"
                namespace = {'Mock': Mock}
                exec(strategy_code, namespace)

                sharpe, error = validator._run_period_backtest(
                    strategy_code=strategy_code,
                    data=Mock(),
                    start_date="2018-01-01",
                    end_date="2020-12-31",
                    period_name="training",
                    iteration_num=0
                )

                assert sharpe is None
                assert "error" in error.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
