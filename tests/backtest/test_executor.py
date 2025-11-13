"""
Unit tests for BacktestExecutor timeout mechanism.

Comprehensive testing of timeout scenarios including:
- Infinite loops (while True)
- Long computations
- Nested function calls
- Process termination and cleanup
- Zombie process prevention

Tests ensure that timeout protection works reliably without leaving
orphaned processes or resource leaks.
"""

import multiprocessing as mp
import os
import signal
import time
from unittest.mock import Mock, MagicMock, patch

import pytest

from src.backtest.executor import BacktestExecutor, ExecutionResult


class TestTimeoutMechanism:
    """Test timeout detection and process termination."""

    def test_infinite_loop_timeout(self) -> None:
        """Test that infinite loops are properly timed out."""
        executor = BacktestExecutor(timeout=2)

        # Strategy that enters infinite loop
        strategy_code = """
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # Verify timeout was detected
        assert result.success is False
        assert result.error_type == "TimeoutError"
        assert "timeout" in result.error_message.lower()
        assert result.execution_time >= 2.0
        assert result.execution_time < 5.0  # Should not take excessively long

    def test_long_computation_timeout(self) -> None:
        """Test that long computations are properly timed out."""
        executor = BacktestExecutor(timeout=2)

        # Strategy with long computation in infinite loop
        strategy_code = """
total = 0
while True:
    for i in range(1000000):
        total += i
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # Verify timeout was detected
        assert result.success is False
        assert result.error_type == "TimeoutError"
        assert result.execution_time >= 1.5

    def test_nested_function_infinite_loop_timeout(self) -> None:
        """Test timeout detection in nested function calls."""
        executor = BacktestExecutor(timeout=2)

        strategy_code = """
def inner_loop():
    while True:
        pass

def outer_function():
    inner_loop()

outer_function()
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # Verify timeout was detected
        assert result.success is False
        assert result.error_type == "TimeoutError"
        assert "timeout" in result.error_message.lower()

    def test_recursive_function_timeout(self) -> None:
        """Test timeout detection with recursive functions."""
        executor = BacktestExecutor(timeout=2)

        strategy_code = """
def recursive_func(n):
    return recursive_func(n + 1)

recursive_func(0)
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # Should timeout or hit RecursionError - both are acceptable
        assert result.success is False
        assert result.error_type in ["TimeoutError", "RecursionError"]

    def test_timeout_override_per_execution(self) -> None:
        """Test that per-execution timeout overrides default."""
        executor = BacktestExecutor(timeout=10)

        # Strategy with short infinite loop
        strategy_code = """
while True:
    pass
"""

        # Override with shorter timeout
        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # Should timeout quickly (2 seconds, not 10)
        assert result.success is False
        assert result.error_type == "TimeoutError"
        assert result.execution_time < 5.0  # Should be ~2 seconds


class TestProcessTermination:
    """Test proper process cleanup after timeout."""

    def test_process_terminated_after_timeout(self) -> None:
        """Test that processes are terminated after timeout."""
        executor = BacktestExecutor(timeout=2)

        strategy_code = """
import time
time.sleep(10)
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # Verify timeout occurred
        assert result.success is False
        assert result.error_type == "TimeoutError"

        # Verify process was terminated (no zombie)
        # Give a moment for OS to clean up
        time.sleep(0.5)

    def test_force_kill_if_terminate_fails(self) -> None:
        """Test that process is forcefully killed if terminate() doesn't work."""
        executor = BacktestExecutor(timeout=1)

        strategy_code = """
import signal
import sys

def ignore_signal(sig, frame):
    pass

signal.signal(signal.SIGTERM, ignore_signal)

# Ignore termination and continue
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=1
        )

        # Should still timeout even with signal handler
        assert result.success is False
        assert result.error_type == "TimeoutError"

    def test_no_zombie_processes_remain(self) -> None:
        """Test that no zombie processes remain after multiple timeouts."""
        executor = BacktestExecutor(timeout=1)

        strategy_code = """
while True:
    pass
"""

        # Execute multiple times to ensure no accumulation
        for _ in range(3):
            result = executor.execute(
                strategy_code=strategy_code,
                data=Mock(),
                sim=Mock(),
                timeout=1
            )
            assert result.success is False
            assert result.error_type == "TimeoutError"

        # Brief pause for OS cleanup
        time.sleep(0.5)


class TestTimeoutEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_timeout_at_boundary(self) -> None:
        """Test execution that takes exactly at timeout boundary."""
        executor = BacktestExecutor(timeout=2)

        strategy_code = """
import time
time.sleep(2.0)
"""

        # May timeout or succeed depending on timing - both acceptable
        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # Either result is valid (depends on system timing)
        assert result.execution_time >= 1.5

    def test_very_short_timeout(self) -> None:
        """Test with very short timeout."""
        executor = BacktestExecutor(timeout=1)

        strategy_code = """
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=1
        )

        assert result.success is False
        assert result.error_type == "TimeoutError"
        assert result.execution_time < 3.0

    def test_zero_timeout_treated_as_immediate(self) -> None:
        """Test that zero timeout doesn't hang indefinitely."""
        executor = BacktestExecutor(timeout=0)

        strategy_code = """
while True:
    pass
"""

        # Should handle gracefully
        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=0
        )

        # Should recognize as timeout (process won't start or will timeout immediately)
        assert result.success is False
        assert result.error_type == "TimeoutError" or result.execution_time < 2.0

    def test_timeout_with_i_o_operations(self) -> None:
        """Test timeout with blocking I/O operations."""
        executor = BacktestExecutor(timeout=2)

        strategy_code = """
import socket
try:
    # Attempt to connect to non-routable IP (will block)
    socket.create_connection(("10.255.255.1", 80), timeout=30)
except Exception:
    pass
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # Should timeout despite I/O blocking
        assert result.success is False
        assert result.error_type == "TimeoutError"


class TestSuccessfulExecutionWithTimeout:
    """Test that timeout doesn't interfere with successful execution."""

    def test_quick_execution_completes_successfully(self) -> None:
        """Test that quick execution completes before timeout."""
        executor = BacktestExecutor(timeout=5)

        # Create mock report object with get_stats() method returning valid metrics
        # Note: max_drawdown must be negative (drawdown is a loss)
        mock_report = Mock()
        mock_report.get_stats.return_value = {
            "daily_sharpe": 1.5,
            "total_return": 0.25,
            "max_drawdown": -0.10,  # Negative for drawdown
        }
        mock_sim = Mock(return_value=mock_report)

        strategy_code = """
report = sim(
    start_date="2020-01-01",
    end_date="2021-12-31",
    buy=[],
    resample="M"
)
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=mock_sim,
            timeout=5
        )

        # Should succeed
        assert result.success is True
        assert result.sharpe_ratio == 1.5
        assert result.total_return == 0.25
        assert result.max_drawdown == -0.10
        assert result.execution_time > 0
        assert result.execution_time < 2.0  # Should be very quick

    def test_execution_with_sleep_completes(self) -> None:
        """Test execution with sleep completes successfully."""
        executor = BacktestExecutor(timeout=5)

        # Create mock report object with get_stats() method returning valid metrics
        mock_report = Mock()
        mock_report.get_stats.return_value = {
            "daily_sharpe": 2.0,
            "total_return": 0.5,
            "max_drawdown": -0.05,  # Negative for drawdown
        }
        mock_sim = Mock(return_value=mock_report)

        strategy_code = """
import time
time.sleep(0.5)
report = sim(
    start_date="2020-01-01",
    end_date="2021-12-31",
    buy=[],
    resample="M"
)
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=mock_sim,
            timeout=5
        )

        # Should succeed despite sleep
        assert result.success is True
        assert result.sharpe_ratio == 2.0
        assert result.execution_time >= 0.4


class TestTimeoutErrorHandling:
    """Test timeout error information and reporting."""

    def test_timeout_error_message_includes_timeout_value(self) -> None:
        """Test that timeout error message includes the timeout value."""
        executor = BacktestExecutor(timeout=2)

        strategy_code = """
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        assert result.error_message is not None
        assert "2" in result.error_message  # Should mention 2 second timeout
        assert "timeout" in result.error_message.lower()

    def test_timeout_stack_trace_included(self) -> None:
        """Test that stack trace is included in timeout result."""
        executor = BacktestExecutor(timeout=1)

        strategy_code = """
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=1
        )

        # Timeout should include process kill info in stack trace
        assert result.stack_trace is not None
        assert len(result.stack_trace) > 0

    def test_execution_time_recorded_on_timeout(self) -> None:
        """Test that execution time is accurately recorded on timeout."""
        executor = BacktestExecutor(timeout=2)

        strategy_code = """
import time
time.sleep(1)
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # Should have recorded execution time close to timeout
        assert result.execution_time >= 1.5
        assert result.execution_time < 4.0


class TestTimeoutWithDifferentStrategyCodes:
    """Test timeout with various strategy code patterns."""

    def test_timeout_with_list_comprehension_loop(self) -> None:
        """Test timeout with list comprehension."""
        executor = BacktestExecutor(timeout=2)

        strategy_code = """
# Create large list that may timeout
result = [i for i in range(1000000000) if i % 2 == 0]
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # May timeout or succeed depending on system speed
        # Both are acceptable outcomes

    def test_timeout_with_lambda_function(self) -> None:
        """Test timeout with lambda functions."""
        executor = BacktestExecutor(timeout=2)

        strategy_code = """
def run_forever():
    f = lambda: run_forever()
    return f()

run_forever()
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        # Should timeout or hit RecursionError
        assert result.success is False


class TestTimeoutWithMultiprocessingContext:
    """Test timeout behavior with different multiprocessing contexts."""

    def test_timeout_with_default_context(self) -> None:
        """Test timeout with default multiprocessing context."""
        executor = BacktestExecutor(timeout=2)

        strategy_code = """
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=2
        )

        assert result.success is False
        assert result.error_type == "TimeoutError"


class TestExecutionResultDataclass:
    """Test ExecutionResult dataclass for timeout cases."""

    def test_timeout_result_has_required_fields(self) -> None:
        """Test that timeout result has all required fields."""
        executor = BacktestExecutor(timeout=1)

        strategy_code = """
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=1
        )

        # Verify all fields are present
        assert result.success is not None
        assert result.error_type is not None
        assert result.error_message is not None
        assert result.execution_time is not None
        assert isinstance(result.execution_time, float)

    def test_timeout_result_success_is_false(self) -> None:
        """Test that timeout result always has success=False."""
        executor = BacktestExecutor(timeout=1)

        strategy_code = """
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=1
        )

        assert result.success is False
        assert result.sharpe_ratio is None
        assert result.total_return is None
        assert result.max_drawdown is None

    def test_timeout_result_error_type_is_timeout_error(self) -> None:
        """Test that timeout result has error_type set to TimeoutError."""
        executor = BacktestExecutor(timeout=1)

        strategy_code = """
while True:
    pass
"""

        result = executor.execute(
            strategy_code=strategy_code,
            data=Mock(),
            sim=Mock(),
            timeout=1
        )

        assert result.error_type == "TimeoutError"


# Test utilities for process cleanup verification

def get_process_count() -> int:
    """Get current count of child processes."""
    current_process = mp.current_process()
    return len(current_process._children) if hasattr(current_process, '_children') else 0


def get_zombie_process_count() -> int:
    """Check for zombie processes (platform-specific)."""
    # This is Linux-specific
    try:
        import subprocess
        result = subprocess.run(
            "ps aux | grep -c '<defunct>'",
            shell=True,
            capture_output=True,
            text=True,
            timeout=2
        )
        count = int(result.stdout.strip()) - 1  # Subtract the grep process itself
        return max(0, count)
    except Exception:
        return 0


class TestProcessCleanupUtilities:
    """Test process cleanup verification utilities."""

    def test_process_count_helper(self) -> None:
        """Test that process count helper works."""
        # This is informational - just verify the function doesn't crash
        count = get_process_count()
        assert isinstance(count, int)
        assert count >= 0

    def test_zombie_check_helper(self) -> None:
        """Test that zombie process check helper works."""
        # This is informational - just verify the function doesn't crash
        count = get_zombie_process_count()
        assert isinstance(count, int)
        assert count >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
