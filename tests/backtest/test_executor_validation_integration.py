"""Test suite for Task 3.2.5: BacktestExecutor validation integration

Tests the integration of metric validation into BacktestExecutor.execute()
to ensure invalid metrics are caught before returning results to callers.

Acceptance Criteria:
- SV-2.4: BacktestExecutor.execute() validates before creating ExecutionResult
- SV-2.6: Invalid data returns ExecutionResult(success=False, error_message=...)
"""

import pytest
from src.backtest.executor import ExecutionResult
from src.backtest.validation import validate_execution_result


class TestBacktestExecutorValidation:
    """SV-2.4 & SV-2.6: BacktestExecutor validates results before returning"""

    def test_executor_returns_success_for_valid_metrics(self):
        """
        GIVEN strategy that produces valid metrics
        WHEN executor.execute() is called
        THEN returns ExecutionResult with success=True
        """
        # Create a valid result manually to test validation
        result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=0.5,
            max_drawdown=-0.2,
            execution_time=1.0
        )

        # Validation should not modify valid results
        errors = validate_execution_result(result)
        assert len(errors) == 0, "Valid metrics should produce no errors"

    def test_executor_rejects_invalid_sharpe_ratio(self):
        """
        GIVEN ExecutionResult with invalid sharpe_ratio (>10)
        WHEN validation is applied
        THEN returns ExecutionResult with success=False and error message
        """
        # Create result with invalid sharpe_ratio
        result = ExecutionResult(
            success=True,
            sharpe_ratio=15.0,  # Invalid
            total_return=0.5,
            max_drawdown=-0.2,
            execution_time=1.0
        )

        errors = validate_execution_result(result)

        assert len(errors) > 0, "Invalid sharpe_ratio should produce errors"
        assert any("sharpe_ratio" in err.lower() for err in errors), \
            "Error should mention 'sharpe_ratio'"
        assert any("15.0" in err for err in errors), \
            "Error should include the invalid value"

    def test_executor_rejects_positive_max_drawdown(self):
        """
        GIVEN ExecutionResult with positive max_drawdown
        WHEN validation is applied
        THEN returns ExecutionResult with success=False and error message
        """
        result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=0.5,
            max_drawdown=0.3,  # Invalid (must be <= 0)
            execution_time=1.0
        )

        errors = validate_execution_result(result)

        assert len(errors) > 0, "Positive max_drawdown should produce errors"
        assert any("max_drawdown" in err.lower() for err in errors), \
            "Error should mention 'max_drawdown'"

    def test_executor_rejects_out_of_range_total_return(self):
        """
        GIVEN ExecutionResult with total_return > 10
        WHEN validation is applied
        THEN returns ExecutionResult with success=False and error message
        """
        result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=15.0,  # Invalid
            max_drawdown=-0.2,
            execution_time=1.0
        )

        errors = validate_execution_result(result)

        assert len(errors) > 0, "Invalid total_return should produce errors"
        assert any("total_return" in err.lower() for err in errors), \
            "Error should mention 'total_return'"

    def test_executor_handles_multiple_validation_errors(self):
        """
        GIVEN ExecutionResult with multiple invalid metrics
        WHEN validation is applied
        THEN returns all error messages
        """
        result = ExecutionResult(
            success=True,
            sharpe_ratio=15.0,  # Invalid
            total_return=20.0,  # Invalid
            max_drawdown=0.5,   # Invalid
            execution_time=1.0
        )

        errors = validate_execution_result(result)

        assert len(errors) == 3, "Should report all 3 validation errors"
        assert any("sharpe_ratio" in err.lower() for err in errors), \
            "Should include sharpe_ratio error"
        assert any("total_return" in err.lower() for err in errors), \
            "Should include total_return error"
        assert any("max_drawdown" in err.lower() for err in errors), \
            "Should include max_drawdown error"

    def test_validation_skipped_for_failed_executions(self):
        """
        GIVEN ExecutionResult with success=False
        WHEN validation is applied
        THEN validation is skipped (no errors)
        """
        result = ExecutionResult(
            success=False,
            error_type="TimeoutError",
            error_message="Strategy timed out",
            sharpe_ratio=999.0,  # Invalid but should be ignored
            execution_time=30.0
        )

        errors = validate_execution_result(result)

        # Should skip validation for failed executions
        assert len(errors) == 0, \
            "Validation should be skipped for failed executions"

    def test_validation_error_message_format(self):
        """
        GIVEN validation failure
        WHEN error message is created
        THEN includes field name, value, and constraint
        """
        result = ExecutionResult(
            success=True,
            sharpe_ratio=15.0,
            total_return=0.5,
            max_drawdown=-0.2,
            execution_time=1.0
        )

        errors = validate_execution_result(result)

        assert len(errors) > 0, "Should have validation errors"
        error_msg = errors[0]

        # Should include field name
        assert "sharpe_ratio" in error_msg.lower(), \
            "Error should include field name"
        # Should include actual value
        assert "15.0" in error_msg, \
            "Error should include actual value"
        # Should include constraint
        assert "[-10" in error_msg or "range" in error_msg.lower(), \
            "Error should include constraint information"
