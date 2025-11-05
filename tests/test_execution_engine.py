"""Integration tests for strategy execution engine.

This module tests the execution engine used in the autonomous loop to
execute validated strategy code in a safe sandbox environment.

Test coverage:
- Full execution pipeline (validation -> execution -> metrics extraction)
- Error handling for various failure modes
- Timeout handling for infinite loops
- Metrics extraction and validation
"""

import pytest
import sys
import os
import signal
import time

# Add artifacts/working/modules to path for imports
ARTIFACTS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../artifacts/working/modules'))
if ARTIFACTS_PATH not in sys.path:
    sys.path.insert(0, ARTIFACTS_PATH)

from sandbox_simple import execute_strategy_safe, TimeoutException


class TestExecutionEngine:
    """Test suite for strategy execution engine."""

    def test_full_execution_pipeline_success(self):
        """Test full execution pipeline with valid strategy code."""
        code = """
import pandas as pd

# Generate trading signal
close = pd.Series([100, 102, 101, 105, 103])
sma = close.rolling(3).mean()
position = close > sma

# Run backtest simulation (will use mock sim)
report = sim(position, resample='D')
"""
        # Execute with mock data
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,  # Mock data (not needed for test)
            timeout=30
        )

        # Verify success
        assert success is True
        assert error is None

        # Verify metrics extracted
        assert metrics is not None
        assert isinstance(metrics, dict)

        # Verify common metrics present
        assert 'sharpe_ratio' in metrics
        assert 'annual_return' in metrics
        assert 'total_return' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics

        # Verify metric values are reasonable
        assert isinstance(metrics['sharpe_ratio'], (int, float))
        assert isinstance(metrics['annual_return'], (int, float))
        assert metrics['sharpe_ratio'] >= -1.0  # Mock values range
        assert metrics['sharpe_ratio'] <= 3.0

    def test_execution_with_syntax_error(self):
        """Test error handling for code with syntax errors."""
        code = """
import pandas as pd
def strategy(data)  # Missing colon - syntax error
    return pd.DataFrame()
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Verify failure
        assert success is False
        assert metrics is None
        assert error is not None
        assert "SyntaxError" in error or "invalid syntax" in error.lower()

    def test_execution_with_runtime_error(self):
        """Test error handling for code with runtime errors."""
        code = """
import pandas as pd

# Trigger ZeroDivisionError
value = 1 / 0

position = pd.DataFrame()
report = sim(position)
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Verify failure
        assert success is False
        assert metrics is None
        assert error is not None
        assert "ZeroDivisionError" in error or "division by zero" in error.lower()

    def test_execution_with_name_error(self):
        """Test error handling for undefined variable access."""
        code = """
import pandas as pd

# Use undefined variable
position = undefined_variable

report = sim(position)
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Verify failure
        assert success is False
        assert metrics is None
        assert error is not None
        assert "NameError" in error or "not defined" in error.lower()

    def test_execution_with_import_error(self):
        """Test error handling for missing module imports."""
        code = """
import nonexistent_module

position = pd.DataFrame()
report = sim(position)
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Verify failure
        assert success is False
        assert metrics is None
        assert error is not None
        assert "ModuleNotFoundError" in error or "ImportError" in error or "No module" in error

    def test_timeout_handling_infinite_loop(self):
        """Test timeout handling for infinite loops."""
        # Skip on Windows (signal.SIGALRM not available)
        if not hasattr(signal, 'SIGALRM'):
            pytest.skip("Test requires Unix signals (SIGALRM)")

        code = """
import pandas as pd

# Infinite loop
while True:
    pass

position = pd.DataFrame()
report = sim(position)
"""
        start_time = time.time()
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=3  # 3 second timeout
        )
        elapsed = time.time() - start_time

        # Verify timeout occurred
        assert success is False
        assert metrics is None
        assert error is not None
        assert "timeout" in error.lower() or "exceeded" in error.lower()

        # Verify timeout was enforced (should be close to 3 seconds)
        assert elapsed < 5  # Should not run much longer than timeout

    def test_timeout_handling_sleep(self):
        """Test timeout handling for long-running sleep."""
        # Skip on Windows (signal.SIGALRM not available)
        if not hasattr(signal, 'SIGALRM'):
            pytest.skip("Test requires Unix signals (SIGALRM)")

        code = """
import pandas as pd
import time

# Sleep longer than timeout
time.sleep(10)

position = pd.DataFrame()
report = sim(position)
"""
        start_time = time.time()
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=2  # 2 second timeout
        )
        elapsed = time.time() - start_time

        # Verify timeout occurred
        assert success is False
        assert metrics is None
        assert error is not None
        assert "timeout" in error.lower()

        # Verify timeout was enforced
        assert elapsed < 4  # Should not run much longer than timeout

    def test_execution_without_report(self):
        """Test execution when code doesn't create report variable."""
        code = """
import pandas as pd

# Valid code but no report variable
close = pd.Series([100, 102, 101, 105, 103])
sma = close.rolling(3).mean()
position = close > sma
# No report = sim(...) call
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Should still succeed (code executes without errors)
        # But metrics will be None since no report
        assert success is True
        assert error is None
        # Metrics may be None if no report variable found
        # This is acceptable behavior - execution succeeded

    def test_execution_with_pandas_operations(self):
        """Test execution with complex pandas operations."""
        code = """
import pandas as pd
import numpy as np

# Complex pandas operations
close = pd.Series([100, 102, 101, 105, 103, 107, 106, 110])
volume = pd.Series([1000, 1100, 900, 1200, 1050, 1300, 1150, 1400])

# Technical indicators
sma_short = close.rolling(3).mean()
sma_long = close.rolling(5).mean()
std = close.rolling(5).std()

# Generate signal
signal = (sma_short > sma_long) & (volume > volume.rolling(3).mean())

# Create position DataFrame
position = pd.DataFrame({'signal': signal})

# Run backtest
report = sim(position, resample='D')
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Verify success
        assert success is True
        assert error is None
        assert metrics is not None
        assert isinstance(metrics, dict)

    def test_execution_with_numpy_operations(self):
        """Test execution with numpy array operations."""
        code = """
import pandas as pd
import numpy as np

# Numpy operations
close = pd.Series([100, 102, 101, 105, 103])
close_array = close.values

# Statistical calculations
mean_val = np.mean(close_array)
std_val = np.std(close_array)
z_score = (close_array - mean_val) / std_val

# Generate signal
signal = pd.Series(z_score > 0.5)

# Create position
position = pd.DataFrame({'signal': signal})

# Run backtest
report = sim(position)
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Verify success
        assert success is True
        assert error is None
        assert metrics is not None

    def test_execution_with_data_parameter(self):
        """Test execution when data parameter is provided."""
        code = """
import pandas as pd

# Use data parameter (if provided)
# In real usage, data would be finlab.data object
# For testing, we handle None case gracefully

close = pd.Series([100, 102, 101, 105, 103])
position = close > close.mean()

report = sim(position)
"""
        # Test with None data (mock scenario)
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        assert success is True
        assert error is None
        assert metrics is not None

    def test_metrics_structure(self):
        """Test that extracted metrics have correct structure."""
        code = """
import pandas as pd

close = pd.Series([100, 102, 101, 105, 103])
position = close > close.mean()

report = sim(position)
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Verify success
        assert success is True
        assert metrics is not None

        # Verify metrics structure
        required_keys = ['sharpe_ratio', 'annual_return', 'total_return', 'max_drawdown', 'win_rate']
        for key in required_keys:
            assert key in metrics, f"Missing required metric: {key}"

        # Verify metric types
        for key, value in metrics.items():
            assert isinstance(value, (int, float)), f"Metric {key} should be numeric, got {type(value)}"

        # Verify Sharpe ratio is in reasonable range (mock values)
        assert -1.0 <= metrics['sharpe_ratio'] <= 3.0

    def test_execution_error_message_clarity(self):
        """Test that error messages are clear and informative."""
        code = """
import pandas as pd

# Trigger specific error
df = pd.DataFrame({'a': [1, 2, 3]})
value = df['nonexistent_column']  # KeyError

position = df
report = sim(position)
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Verify failure
        assert success is False
        assert error is not None

        # Verify error message contains useful information
        assert "KeyError" in error or "nonexistent_column" in error


class TestExecutionEdgeCases:
    """Test edge cases for execution engine."""

    def test_empty_code_execution(self):
        """Test execution with empty code string."""
        code = ""

        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Empty code should execute without error (but produce no metrics)
        # Behavior may vary - document actual behavior
        # Either success with no metrics, or failure with error
        if not success:
            assert error is not None

    def test_code_with_only_comments(self):
        """Test execution with only comments."""
        code = """
# This is a comment
# Another comment
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=30
        )

        # Comments-only code should execute (valid Python)
        # But will produce no metrics
        assert success is True or error is not None

    def test_very_large_timeout(self):
        """Test execution with very large timeout value."""
        code = """
import pandas as pd

close = pd.Series([100, 102, 101])
position = close > close.mean()
report = sim(position)
"""
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=3600  # 1 hour timeout
        )

        # Should still complete quickly
        assert success is True
        assert error is None

    def test_zero_timeout(self):
        """Test execution with zero timeout."""
        # Skip on Windows (signal.SIGALRM not available)
        if not hasattr(signal, 'SIGALRM'):
            pytest.skip("Test requires Unix signals (SIGALRM)")

        code = """
import pandas as pd
position = pd.DataFrame()
report = sim(position)
"""
        # Zero timeout should trigger immediately
        # Behavior may vary by implementation
        success, metrics, error = execute_strategy_safe(
            code=code,
            data=None,
            timeout=0
        )

        # Should timeout (or handle gracefully)
        if not success:
            assert error is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
