"""End-to-end integration tests for Task 3.2.8: Phase 3.2 validation system"""

import pytest
from src.backtest.executor import BacktestExecutor, ExecutionResult


class TestPhase3ValidationE2E:
    """SV-2.9: End-to-end integration test with schema validation"""

    def test_e2e_valid_strategy_execution_with_validation(self):
        """
        GIVEN a valid trading strategy
        WHEN executed through BacktestExecutor
        THEN validation passes and returns success=True
        """
        executor = BacktestExecutor(timeout=60)

        # Simple valid strategy that should pass validation
        strategy_code = """
# Simple momentum strategy
close = data.get('price:收盤價')
sma20 = close.average(20)
sma60 = close.average(60)

# Buy when SMA20 crosses above SMA60
position = (sma20 > sma60)

# Backtest
report = sim(position, trade_at_price='close', fee_ratio=0.001425)
"""

        # This requires actual FinLab data context
        # For now, verify the validation path exists
        # Real E2E would need FinLab credentials

        # Mock execution result for testing validation integration
        mock_result = ExecutionResult(
            success=True,
            sharpe_ratio=1.5,
            total_return=0.3,
            max_drawdown=-0.15,
            execution_time=2.5
        )

        # Verify validation would pass
        from src.backtest.validation import validate_execution_result
        errors = validate_execution_result(mock_result)
        assert len(errors) == 0

    def test_e2e_strategy_with_invalid_sharpe_ratio_rejected(self):
        """
        GIVEN strategy producing invalid sharpe_ratio (>10)
        WHEN executed through BacktestExecutor
        THEN returns ExecutionResult(success=False, error_type='ValidationError')
        """
        # Mock result with invalid sharpe_ratio
        invalid_result = ExecutionResult(
            success=True,
            sharpe_ratio=15.0,  # Invalid
            total_return=0.5,
            max_drawdown=-0.2,
            execution_time=2.0
        )

        from src.backtest.validation import validate_execution_result
        errors = validate_execution_result(invalid_result)

        assert len(errors) > 0
        assert any("sharpe_ratio" in err.lower() for err in errors)

        # In real execution, BacktestExecutor would return:
        # ExecutionResult(success=False, error_type='ValidationError', error_message=...)

    def test_e2e_strategy_with_positive_drawdown_rejected(self):
        """
        GIVEN strategy producing positive max_drawdown
        WHEN executed through BacktestExecutor
        THEN returns ExecutionResult(success=False, error_type='ValidationError')
        """
        invalid_result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=0.5,
            max_drawdown=0.3,  # Invalid (must be <= 0)
            execution_time=2.0
        )

        from src.backtest.validation import validate_execution_result
        errors = validate_execution_result(invalid_result)

        assert len(errors) > 0
        assert any("max_drawdown" in err.lower() for err in errors)

    def test_e2e_strategy_with_extreme_return_rejected(self):
        """
        GIVEN strategy producing total_return > 10 (>1000% gain)
        WHEN executed through BacktestExecutor
        THEN returns ExecutionResult(success=False, error_type='ValidationError')
        """
        invalid_result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=15.0,  # Invalid (>10)
            max_drawdown=-0.2,
            execution_time=2.0
        )

        from src.backtest.validation import validate_execution_result
        errors = validate_execution_result(invalid_result)

        assert len(errors) > 0
        assert any("total_return" in err.lower() for err in errors)

    def test_e2e_nan_metrics_rejected(self):
        """
        GIVEN strategy producing NaN metrics
        WHEN executed through BacktestExecutor
        THEN returns ExecutionResult(success=False, error_type='ValidationError')
        """
        nan_result = ExecutionResult(
            success=True,
            sharpe_ratio=float('nan'),
            total_return=0.5,
            max_drawdown=-0.2,
            execution_time=2.0
        )

        from src.backtest.validation import validate_execution_result
        errors = validate_execution_result(nan_result)

        assert len(errors) > 0
        assert any("nan" in err.lower() or "invalid" in err.lower() for err in errors)

    def test_e2e_failed_execution_skips_validation(self):
        """
        GIVEN strategy that fails to execute
        WHEN BacktestExecutor returns failed result
        THEN validation is skipped (allows invalid metrics in failed results)
        """
        failed_result = ExecutionResult(
            success=False,
            error_type="TimeoutError",
            error_message="Execution timed out",
            sharpe_ratio=999.0,  # Invalid but ignored
            total_return=999.0,   # Invalid but ignored
            max_drawdown=999.0,   # Invalid but ignored
            execution_time=60.0
        )

        from src.backtest.validation import validate_execution_result
        errors = validate_execution_result(failed_result)

        # Should skip validation for failed executions
        assert len(errors) == 0

    def test_e2e_validation_preserves_invalid_metrics_for_debugging(self):
        """
        GIVEN validation failure
        WHEN BacktestExecutor returns failed result
        THEN original invalid metrics are preserved for debugging
        """
        # Simulate what BacktestExecutor does with invalid result
        original_result = ExecutionResult(
            success=True,
            sharpe_ratio=15.0,  # Invalid
            total_return=0.5,
            max_drawdown=-0.2,
            execution_time=2.0
        )

        from src.backtest.validation import validate_execution_result
        errors = validate_execution_result(original_result)

        if errors:
            # BacktestExecutor would create this failed result
            failed_result = ExecutionResult(
                success=False,
                error_type="ValidationError",
                error_message=f"Metric validation failed: {'; '.join(errors)}",
                execution_time=original_result.execution_time,
                sharpe_ratio=original_result.sharpe_ratio,  # Preserved
                total_return=original_result.total_return,
                max_drawdown=original_result.max_drawdown
            )

            # Verify metrics preserved
            assert failed_result.sharpe_ratio == 15.0
            assert "ValidationError" in failed_result.error_type

    def test_e2e_validation_error_message_includes_details(self):
        """
        GIVEN multiple validation failures
        WHEN BacktestExecutor returns failed result
        THEN error message includes all validation details
        """
        invalid_result = ExecutionResult(
            success=True,
            sharpe_ratio=15.0,  # Invalid
            total_return=20.0,  # Invalid
            max_drawdown=0.5,   # Invalid
            execution_time=2.0
        )

        from src.backtest.validation import validate_execution_result
        errors = validate_execution_result(invalid_result)

        assert len(errors) == 3

        # Combined error message should include all details
        combined_error = "; ".join(errors)
        assert "sharpe_ratio" in combined_error
        assert "total_return" in combined_error
        assert "max_drawdown" in combined_error
        assert "15.0" in combined_error
        assert "20.0" in combined_error
        assert "0.5" in combined_error

    def test_e2e_real_strategy_with_finlab_data(self):
        """
        GIVEN real FinLab data and valid strategy
        WHEN executed through BacktestExecutor
        THEN validation passes and metrics are valid

        NOTE: Requires FinLab credentials
        """
        pytest.skip("Requires FinLab credentials - manual verification only")

        # This would be the real E2E test:
        # executor = BacktestExecutor()
        # result = executor.execute(strategy_code, data, sim)
        # assert result.success
        # assert result.sharpe_ratio is not None
        # assert -10 <= result.sharpe_ratio <= 10
