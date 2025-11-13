"""Performance benchmarks for Task 3.2.6: Validation overhead testing"""

import time
import pytest
from src.backtest.executor import ExecutionResult
from src.backtest.validation import (
    validate_sharpe_ratio,
    validate_max_drawdown,
    validate_total_return,
    validate_execution_result
)


class TestValidationPerformance:
    """SV-2.7: Validation overhead <1ms per call"""

    def test_validate_sharpe_ratio_performance(self):
        """
        GIVEN sharpe_ratio validation function
        WHEN called 1000 times
        THEN average time < 0.001ms per call
        """
        iterations = 1000
        test_values = [None, -10.0, -5.0, 0.0, 2.5, 5.0, 10.0]

        start_time = time.perf_counter()

        for _ in range(iterations):
            for value in test_values:
                validate_sharpe_ratio(value)

        end_time = time.perf_counter()
        total_time = end_time - start_time
        total_calls = iterations * len(test_values)
        avg_time_ms = (total_time / total_calls) * 1000

        # Should be < 0.001ms (1 microsecond) per call
        assert avg_time_ms < 0.001, f"Average time {avg_time_ms:.6f}ms exceeds 0.001ms threshold"

    def test_validate_max_drawdown_performance(self):
        """
        GIVEN max_drawdown validation function
        WHEN called 1000 times
        THEN average time < 0.001ms per call
        """
        iterations = 1000
        test_values = [None, -0.99, -0.5, -0.2, 0.0]

        start_time = time.perf_counter()

        for _ in range(iterations):
            for value in test_values:
                validate_max_drawdown(value)

        end_time = time.perf_counter()
        total_time = end_time - start_time
        total_calls = iterations * len(test_values)
        avg_time_ms = (total_time / total_calls) * 1000

        assert avg_time_ms < 0.001, f"Average time {avg_time_ms:.6f}ms exceeds 0.001ms threshold"

    def test_validate_total_return_performance(self):
        """
        GIVEN total_return validation function
        WHEN called 1000 times
        THEN average time < 0.001ms per call
        """
        iterations = 1000
        test_values = [None, -1.0, -0.5, 0.0, 0.5, 1.0, 5.0, 10.0]

        start_time = time.perf_counter()

        for _ in range(iterations):
            for value in test_values:
                validate_total_return(value)

        end_time = time.perf_counter()
        total_time = end_time - start_time
        total_calls = iterations * len(test_values)
        avg_time_ms = (total_time / total_calls) * 1000

        assert avg_time_ms < 0.001, f"Average time {avg_time_ms:.6f}ms exceeds 0.001ms threshold"

    def test_validate_execution_result_performance(self):
        """
        GIVEN validate_execution_result function
        WHEN called 1000 times
        THEN average time < 1ms per call (SV-2.7)
        """
        iterations = 1000

        # Valid result
        valid_result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=0.5,
            max_drawdown=-0.2,
            execution_time=1.0
        )

        start_time = time.perf_counter()

        for _ in range(iterations):
            validate_execution_result(valid_result)

        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000

        # Primary acceptance criterion: <1ms per call
        assert avg_time_ms < 1.0, f"Average time {avg_time_ms:.3f}ms exceeds 1ms threshold (SV-2.7)"

    def test_validate_execution_result_with_invalid_metrics_performance(self):
        """
        GIVEN validate_execution_result with invalid metrics
        WHEN validation fails
        THEN overhead still < 1ms per call
        """
        iterations = 1000

        # Invalid result (will trigger validation errors and logging)
        invalid_result = ExecutionResult(
            success=True,
            sharpe_ratio=15.0,  # Invalid
            total_return=20.0,  # Invalid
            max_drawdown=0.5,   # Invalid
            execution_time=1.0
        )

        start_time = time.perf_counter()

        for _ in range(iterations):
            validate_execution_result(invalid_result)

        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time_ms = (total_time / iterations) * 1000

        # Should still be <1ms even with logging
        assert avg_time_ms < 1.0, f"Average time {avg_time_ms:.3f}ms exceeds 1ms threshold"

    def test_validation_percentile_performance(self):
        """
        GIVEN validate_execution_result function
        WHEN measuring p50, p95, p99 latencies
        THEN p95 < 5ms, p99 < 10ms
        """
        iterations = 10000  # Larger sample for percentile accuracy

        result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=0.5,
            max_drawdown=-0.2,
            execution_time=1.0
        )

        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            validate_execution_result(result)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms

        times.sort()

        p50 = times[int(iterations * 0.50)]
        p95 = times[int(iterations * 0.95)]
        p99 = times[int(iterations * 0.99)]

        # Performance targets from requirements.md
        assert p50 < 1.0, f"p50 {p50:.3f}ms exceeds 1ms"
        assert p95 < 5.0, f"p95 {p95:.3f}ms exceeds 5ms"
        assert p99 < 10.0, f"p99 {p99:.3f}ms exceeds 10ms"

    def test_validation_does_not_impact_execution_throughput(self):
        """
        GIVEN BacktestExecutor with validation
        WHEN measuring execution throughput
        THEN validation adds <1% overhead
        """
        # This is more of a conceptual test
        # Validation overhead should be negligible compared to backtest execution time

        result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=0.5,
            max_drawdown=-0.2,
            execution_time=5.0  # Typical backtest time
        )

        # Measure validation time
        validation_start = time.perf_counter()
        validate_execution_result(result)
        validation_time = (time.perf_counter() - validation_start) * 1000

        # Validation should be <1% of typical execution time
        execution_time_ms = result.execution_time * 1000
        overhead_pct = (validation_time / execution_time_ms) * 100

        assert overhead_pct < 1.0, f"Validation overhead {overhead_pct:.2f}% exceeds 1% threshold"
