"""Comprehensive test suite for Task 3.2.7: All validators with edge cases"""

import math
import pytest
from src.backtest.validation import (
    validate_sharpe_ratio,
    validate_max_drawdown,
    validate_total_return,
    validate_execution_result
)
from src.backtest.executor import ExecutionResult


class TestValidatorEdgeCases:
    """Edge case testing for all validators"""

    # Sharpe Ratio Edge Cases
    def test_sharpe_ratio_very_small_negative(self):
        """WHEN sharpe_ratio is very small negative THEN passes"""
        error = validate_sharpe_ratio(-0.0001)
        assert error is None

    def test_sharpe_ratio_very_small_positive(self):
        """WHEN sharpe_ratio is very small positive THEN passes"""
        error = validate_sharpe_ratio(0.0001)
        assert error is None

    def test_sharpe_ratio_exactly_at_boundaries(self):
        """WHEN sharpe_ratio exactly at -10 or 10 THEN passes"""
        assert validate_sharpe_ratio(-10.0) is None
        assert validate_sharpe_ratio(10.0) is None

    def test_sharpe_ratio_just_outside_boundaries(self):
        """WHEN sharpe_ratio just outside bounds THEN fails"""
        assert validate_sharpe_ratio(-10.0001) is not None
        assert validate_sharpe_ratio(10.0001) is not None

    # Max Drawdown Edge Cases
    def test_max_drawdown_exactly_zero(self):
        """WHEN max_drawdown is exactly 0 THEN passes"""
        error = validate_max_drawdown(0.0)
        assert error is None

    def test_max_drawdown_very_small_negative(self):
        """WHEN max_drawdown is very small negative THEN passes"""
        error = validate_max_drawdown(-0.0001)
        assert error is None

    def test_max_drawdown_very_small_positive(self):
        """WHEN max_drawdown is very small positive THEN fails"""
        error = validate_max_drawdown(0.0001)
        assert error is not None

    def test_max_drawdown_large_negative_valid(self):
        """WHEN max_drawdown is -0.99 THEN passes"""
        error = validate_max_drawdown(-0.99)
        assert error is None

    # Total Return Edge Cases
    def test_total_return_exactly_at_boundaries(self):
        """WHEN total_return exactly at -1 or 10 THEN passes"""
        assert validate_total_return(-1.0) is None
        assert validate_total_return(10.0) is None

    def test_total_return_just_outside_boundaries(self):
        """WHEN total_return just outside bounds THEN fails"""
        assert validate_total_return(-1.0001) is not None
        assert validate_total_return(10.0001) is not None

    def test_total_return_zero(self):
        """WHEN total_return is 0 THEN passes (no gain/loss)"""
        error = validate_total_return(0.0)
        assert error is None


class TestValidateExecutionResult:
    """Test the main validate_execution_result function"""

    def test_validate_successful_result_with_valid_metrics(self):
        """WHEN ExecutionResult has valid metrics THEN validation passes"""
        result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=0.5,
            max_drawdown=-0.2
        )
        errors = validate_execution_result(result)
        assert len(errors) == 0

    def test_validate_failed_result_skips_validation(self):
        """WHEN ExecutionResult.success=False THEN skip metric validation"""
        result = ExecutionResult(
            success=False,
            error_message="Strategy failed",
            sharpe_ratio=999.0  # Invalid, but should be ignored
        )
        errors = validate_execution_result(result)
        assert len(errors) == 0

    def test_validate_result_with_multiple_invalid_metrics(self):
        """WHEN multiple metrics invalid THEN returns all errors"""
        result = ExecutionResult(
            success=True,
            sharpe_ratio=15.0,  # Invalid
            total_return=20.0,  # Invalid
            max_drawdown=0.5    # Invalid
        )
        errors = validate_execution_result(result)

        assert len(errors) == 3
        assert any("sharpe_ratio" in err for err in errors)
        assert any("total_return" in err for err in errors)
        assert any("max_drawdown" in err for err in errors)

    def test_validate_result_with_all_none_metrics(self):
        """WHEN all metrics are None THEN validation passes"""
        result = ExecutionResult(
            success=True,
            sharpe_ratio=None,
            total_return=None,
            max_drawdown=None
        )
        errors = validate_execution_result(result)
        assert len(errors) == 0

    def test_validate_result_with_partial_metrics(self):
        """WHEN some metrics None, some valid THEN validation passes"""
        result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=None,
            max_drawdown=-0.2
        )
        errors = validate_execution_result(result)
        assert len(errors) == 0
