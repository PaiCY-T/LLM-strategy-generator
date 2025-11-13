"""
Test suite for ExecutionResult validation - Phase 3.2 Schema Validation.

This module tests field validators for ExecutionResult metrics to ensure
data integrity and catch anomalous values early.

Task 3.2.1: Sharpe ratio field validation [-10, 10]
"""

import math
import pytest
from src.backtest.executor import ExecutionResult


class TestSharpeRatioValidation:
    """SV-2.1: Sharpe ratio range validation [-10, 10]

    Task 3.2.1: Implement sharpe_ratio field validator
    Acceptance Criteria: Validate sharpe_ratio is within [-10, 10] range
    """

    def test_sharpe_ratio_none_is_valid(self):
        """
        GIVEN ExecutionResult with sharpe_ratio=None
        WHEN validating sharpe_ratio
        THEN validation passes (None is valid for optional field)
        """
        from src.backtest.validation import validate_sharpe_ratio

        result = ExecutionResult(success=True, sharpe_ratio=None)
        error = validate_sharpe_ratio(result.sharpe_ratio)
        assert error is None

    def test_sharpe_ratio_at_lower_boundary(self):
        """
        GIVEN ExecutionResult with sharpe_ratio=-10.0
        WHEN validating sharpe_ratio
        THEN validation passes (boundary value is valid)
        """
        from src.backtest.validation import validate_sharpe_ratio

        result = ExecutionResult(success=True, sharpe_ratio=-10.0)
        error = validate_sharpe_ratio(result.sharpe_ratio)
        assert error is None

    def test_sharpe_ratio_at_upper_boundary(self):
        """
        GIVEN ExecutionResult with sharpe_ratio=10.0
        WHEN validating sharpe_ratio
        THEN validation passes (boundary value is valid)
        """
        from src.backtest.validation import validate_sharpe_ratio

        result = ExecutionResult(success=True, sharpe_ratio=10.0)
        error = validate_sharpe_ratio(result.sharpe_ratio)
        assert error is None

    def test_sharpe_ratio_within_valid_range(self):
        """
        GIVEN ExecutionResult with sharpe_ratio in [-10, 10]
        WHEN validating sharpe_ratio
        THEN validation passes
        """
        from src.backtest.validation import validate_sharpe_ratio

        for value in [-5.0, 0.0, 1.5, 5.0]:
            result = ExecutionResult(success=True, sharpe_ratio=value)
            error = validate_sharpe_ratio(result.sharpe_ratio)
            assert error is None, f"Valid value {value} should pass"

    def test_sharpe_ratio_below_range_fails(self):
        """
        GIVEN ExecutionResult with sharpe_ratio < -10
        WHEN validating sharpe_ratio
        THEN validation fails with descriptive error
        """
        from src.backtest.validation import validate_sharpe_ratio

        result = ExecutionResult(success=True, sharpe_ratio=-10.001)
        error = validate_sharpe_ratio(result.sharpe_ratio)

        assert error is not None
        assert "sharpe_ratio" in error.lower()
        assert "-10.001" in error
        assert "[-10" in error or "range" in error.lower()

    def test_sharpe_ratio_above_range_fails(self):
        """
        GIVEN ExecutionResult with sharpe_ratio > 10
        WHEN validating sharpe_ratio
        THEN validation fails with descriptive error
        """
        from src.backtest.validation import validate_sharpe_ratio

        result = ExecutionResult(success=True, sharpe_ratio=10.001)
        error = validate_sharpe_ratio(result.sharpe_ratio)

        assert error is not None
        assert "10.001" in error
        assert "10]" in error or "range" in error.lower()

    def test_sharpe_ratio_nan_is_invalid(self):
        """
        GIVEN ExecutionResult with sharpe_ratio=NaN
        WHEN validating sharpe_ratio
        THEN validation fails
        """
        from src.backtest.validation import validate_sharpe_ratio

        result = ExecutionResult(success=True, sharpe_ratio=float('nan'))
        error = validate_sharpe_ratio(result.sharpe_ratio)

        assert error is not None
        assert "nan" in error.lower() or "invalid" in error.lower()

    def test_sharpe_ratio_infinity_is_invalid(self):
        """
        GIVEN ExecutionResult with sharpe_ratio=Inf or -Inf
        WHEN validating sharpe_ratio
        THEN validation fails
        """
        from src.backtest.validation import validate_sharpe_ratio

        for value in [float('inf'), float('-inf')]:
            result = ExecutionResult(success=True, sharpe_ratio=value)
            error = validate_sharpe_ratio(result.sharpe_ratio)

            assert error is not None
            assert "inf" in error.lower() or "infinite" in error.lower()


class TestMaxDrawdownValidation:
    """SV-2.2: Max drawdown validation (must be <= 0)

    Task 3.2.2: Implement max_drawdown field validator
    Acceptance Criteria: Validate max_drawdown is <= 0 (drawdown is negative)
    """

    def test_max_drawdown_none_is_valid(self):
        """WHEN max_drawdown=None THEN validation passes"""
        from src.backtest.validation import validate_max_drawdown
        error = validate_max_drawdown(None)
        assert error is None

    def test_max_drawdown_zero_is_valid(self):
        """WHEN max_drawdown=0 THEN validation passes (no drawdown)"""
        from src.backtest.validation import validate_max_drawdown
        error = validate_max_drawdown(0.0)
        assert error is None

    def test_max_drawdown_negative_is_valid(self):
        """WHEN max_drawdown < 0 THEN validation passes"""
        from src.backtest.validation import validate_max_drawdown
        for value in [-0.1, -0.5, -0.99]:
            error = validate_max_drawdown(value)
            assert error is None, f"Negative drawdown {value} should be valid"

    def test_max_drawdown_positive_fails(self):
        """WHEN max_drawdown > 0 THEN validation fails"""
        from src.backtest.validation import validate_max_drawdown
        error = validate_max_drawdown(0.1)

        assert error is not None
        assert "max_drawdown" in error.lower()
        assert "0.1" in error
        assert "negative" in error.lower() or "<= 0" in error

    def test_max_drawdown_large_positive_fails(self):
        """WHEN max_drawdown >> 0 THEN validation fails with clear error"""
        from src.backtest.validation import validate_max_drawdown
        error = validate_max_drawdown(50.0)

        assert error is not None
        assert "50.0" in error

    def test_max_drawdown_nan_is_invalid(self):
        """WHEN max_drawdown=NaN THEN validation fails"""
        from src.backtest.validation import validate_max_drawdown
        error = validate_max_drawdown(float('nan'))

        assert error is not None
        assert "nan" in error.lower() or "invalid" in error.lower()

    def test_max_drawdown_infinity_is_invalid(self):
        """WHEN max_drawdown=Inf/-Inf THEN validation fails"""
        from src.backtest.validation import validate_max_drawdown
        for value in [float('inf'), float('-inf')]:
            error = validate_max_drawdown(value)
            assert error is not None


class TestTotalReturnValidation:
    """SV-2.3: Total return range validation [-1, 10]

    Task 3.2.3: Implement total_return field validator
    Acceptance Criteria: Validate total_return is within [-1, 10] range
    (allowing -100% loss to 1000% gain)
    """

    def test_total_return_none_is_valid(self):
        """
        GIVEN ExecutionResult with total_return=None
        WHEN validating total_return
        THEN validation passes (None is valid for optional field)
        """
        from src.backtest.validation import validate_total_return

        error = validate_total_return(None)
        assert error is None

    def test_total_return_at_lower_boundary(self):
        """
        GIVEN ExecutionResult with total_return=-1.0
        WHEN validating total_return
        THEN validation passes (-100% loss boundary)
        """
        from src.backtest.validation import validate_total_return

        error = validate_total_return(-1.0)
        assert error is None

    def test_total_return_at_upper_boundary(self):
        """
        GIVEN ExecutionResult with total_return=10.0
        WHEN validating total_return
        THEN validation passes (1000% gain boundary)
        """
        from src.backtest.validation import validate_total_return

        error = validate_total_return(10.0)
        assert error is None

    def test_total_return_within_valid_range(self):
        """
        GIVEN ExecutionResult with total_return in [-1, 10]
        WHEN validating total_return
        THEN validation passes
        """
        from src.backtest.validation import validate_total_return

        for value in [-0.5, 0.0, 0.15, 1.0, 5.0]:
            error = validate_total_return(value)
            assert error is None, f"Valid value {value} should pass"

    def test_total_return_below_range_fails(self):
        """
        GIVEN ExecutionResult with total_return < -1
        WHEN validating total_return
        THEN validation fails (> 100% loss is anomalous)
        """
        from src.backtest.validation import validate_total_return

        error = validate_total_return(-1.1)

        assert error is not None
        assert "total_return" in error.lower()
        assert "-1.1" in error
        assert "[-1" in error or "range" in error.lower()

    def test_total_return_above_range_fails(self):
        """
        GIVEN ExecutionResult with total_return > 10
        WHEN validating total_return
        THEN validation fails (> 1000% gain is anomalous)
        """
        from src.backtest.validation import validate_total_return

        error = validate_total_return(15.0)

        assert error is not None
        assert "15.0" in error
        assert "10]" in error or "range" in error.lower()

    def test_total_return_nan_is_invalid(self):
        """
        GIVEN ExecutionResult with total_return=NaN
        WHEN validating total_return
        THEN validation fails
        """
        from src.backtest.validation import validate_total_return

        error = validate_total_return(float('nan'))

        assert error is not None
        assert "nan" in error.lower() or "invalid" in error.lower()

    def test_total_return_infinity_is_invalid(self):
        """
        GIVEN ExecutionResult with total_return=Inf/-Inf
        WHEN validating total_return
        THEN validation fails
        """
        from src.backtest.validation import validate_total_return

        for value in [float('inf'), float('-inf')]:
            error = validate_total_return(value)
            assert error is not None
