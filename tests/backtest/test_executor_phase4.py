"""Phase 4: BacktestExecutor execute_strategy() Verification Tests

Verifies that the existing execute_strategy() method correctly handles
Factor Graph Strategy DAG objects and returns consistent ExecutionResult format.

Tests verify:
- Basic Strategy execution via to_pipeline() → sim()
- Parameter passing (timeout, dates, fees, resample)
- Error handling and timeout protection
- ExecutionResult format consistency with execute_code()
- Metrics extraction from backtest report
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import time
from typing import Any, Dict

from src.backtest.executor import BacktestExecutor, ExecutionResult


class MockStrategy:
    """Mock Strategy DAG object for testing."""

    def __init__(self, strategy_id: str = "test_strategy", generation: int = 1,
                 should_fail: bool = False, execution_time: float = 0.1):
        self.id = strategy_id
        self.generation = generation
        self.should_fail = should_fail
        self.execution_time = execution_time
        self.to_pipeline_called = False

    def to_pipeline(self, data: Any) -> pd.DataFrame:
        """Mock to_pipeline() that returns position signals DataFrame."""
        self.to_pipeline_called = True

        if self.should_fail:
            raise ValueError("Mock strategy failure")

        # Simulate execution time
        time.sleep(self.execution_time)

        # Return mock position signals DataFrame
        dates = pd.date_range('2018-01-01', '2024-12-31', freq='M')
        stocks = ['2330', '2317', '2454']  # Mock Taiwan stock codes

        # Create position signals (1 = buy, 0 = no position)
        positions = pd.DataFrame(
            index=dates,
            columns=stocks,
            data=1  # Simple buy-and-hold for testing
        )

        return positions


class MockReport:
    """Mock finlab backtest report object."""

    def __init__(self, sharpe: float = 1.5, total_return: float = 0.25,
                 max_drawdown: float = -0.10):
        self.sharpe = sharpe
        self.total_return = total_return
        self.max_drawdown = max_drawdown

    def get_stats(self) -> Dict[str, float]:
        """Return mock backtest statistics."""
        return {
            'daily_sharpe': self.sharpe,
            'total_return': self.total_return,
            'max_drawdown': self.max_drawdown,
        }


def mock_sim(positions_df: pd.DataFrame, fee_ratio: float = 0.001425,
             tax_ratio: float = 0.003, resample: str = "M") -> MockReport:
    """Mock finlab.backtest.sim() function."""
    return MockReport()


class TestExecuteStrategyBasic(unittest.TestCase):
    """Test basic execute_strategy() functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = BacktestExecutor(timeout=30)
        self.mock_data = Mock()  # Mock finlab.data

    def test_execute_strategy_success(self):
        """Test successful Strategy execution returns ExecutionResult."""
        strategy = MockStrategy()

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim
        )

        # Verify result structure
        self.assertIsInstance(result, ExecutionResult)
        self.assertTrue(result.success)
        self.assertTrue(strategy.to_pipeline_called)

        # Verify metrics extracted
        self.assertIsNotNone(result.sharpe_ratio)
        self.assertIsNotNone(result.total_return)
        self.assertIsNotNone(result.max_drawdown)

        # Verify execution time tracked
        self.assertIsNotNone(result.execution_time)
        self.assertGreater(result.execution_time, 0)

    def test_execute_strategy_calls_to_pipeline(self):
        """Test that execute_strategy() calls strategy.to_pipeline(data)."""
        strategy = MockStrategy()

        self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim
        )

        # Verify to_pipeline was called
        self.assertTrue(strategy.to_pipeline_called)

    def test_execute_strategy_returns_report(self):
        """Test that ExecutionResult includes backtest report."""
        strategy = MockStrategy()

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim
        )

        # Verify report included
        self.assertIsNotNone(result.report)
        self.assertIsInstance(result.report, MockReport)


class TestExecuteStrategyParameters(unittest.TestCase):
    """Test execute_strategy() parameter handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = BacktestExecutor(timeout=30)
        self.mock_data = Mock()

    def test_execute_strategy_with_timeout_override(self):
        """Test that timeout parameter overrides default."""
        strategy = MockStrategy()

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim,
            timeout=60  # Override default 30s timeout
        )

        self.assertTrue(result.success)

    def test_execute_strategy_with_date_range(self):
        """Test execute_strategy() with custom date range."""
        strategy = MockStrategy()

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim,
            start_date="2020-01-01",
            end_date="2023-12-31"
        )

        self.assertTrue(result.success)

    def test_execute_strategy_with_custom_fees(self):
        """Test execute_strategy() with custom fee/tax ratios."""
        strategy = MockStrategy()

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim,
            fee_ratio=0.002,  # Custom fee
            tax_ratio=0.004   # Custom tax
        )

        self.assertTrue(result.success)

    def test_execute_strategy_with_resample(self):
        """Test execute_strategy() with different resample frequencies."""
        strategy = MockStrategy()

        # Test weekly rebalancing
        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim,
            resample="W"
        )

        self.assertTrue(result.success)


class TestExecuteStrategyErrorHandling(unittest.TestCase):
    """Test execute_strategy() error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = BacktestExecutor(timeout=5)
        self.mock_data = Mock()

    def test_execute_strategy_handles_exception(self):
        """Test that execute_strategy() catches strategy exceptions."""
        strategy = MockStrategy(should_fail=True)

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim
        )

        # Verify error captured
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_type)
        self.assertEqual(result.error_type, "ValueError")
        self.assertIsNotNone(result.error_message)
        self.assertIn("Mock strategy failure", result.error_message)
        self.assertIsNotNone(result.stack_trace)

    def test_execute_strategy_timeout_protection(self):
        """Test that execute_strategy() enforces timeout."""
        # Create strategy that takes longer than timeout
        strategy = MockStrategy(execution_time=10)  # 10 seconds

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim,
            timeout=2  # Only 2 seconds allowed
        )

        # Verify timeout error
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, "TimeoutError")
        self.assertIn("timeout", result.error_message.lower())

    def test_execute_strategy_execution_time_tracking(self):
        """Test that execution_time is always recorded."""
        # Test successful execution
        strategy_success = MockStrategy()
        result_success = self.executor.execute_strategy(
            strategy=strategy_success,
            data=self.mock_data,
            sim=mock_sim
        )
        self.assertIsNotNone(result_success.execution_time)
        self.assertGreater(result_success.execution_time, 0)

        # Test failed execution
        strategy_fail = MockStrategy(should_fail=True)
        result_fail = self.executor.execute_strategy(
            strategy=strategy_fail,
            data=self.mock_data,
            sim=mock_sim
        )
        self.assertIsNotNone(result_fail.execution_time)
        self.assertGreater(result_fail.execution_time, 0)


class TestExecutionResultConsistency(unittest.TestCase):
    """Test ExecutionResult format consistency between execute_strategy() and execute_code()."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = BacktestExecutor(timeout=30)
        self.mock_data = Mock()

    def test_execution_result_same_structure(self):
        """Test that execute_strategy() returns same ExecutionResult structure as execute_code()."""
        strategy = MockStrategy()

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim
        )

        # Verify ExecutionResult has expected attributes
        self.assertTrue(hasattr(result, 'success'))
        self.assertTrue(hasattr(result, 'sharpe_ratio'))
        self.assertTrue(hasattr(result, 'total_return'))
        self.assertTrue(hasattr(result, 'max_drawdown'))
        self.assertTrue(hasattr(result, 'execution_time'))
        self.assertTrue(hasattr(result, 'error_type'))
        self.assertTrue(hasattr(result, 'error_message'))
        self.assertTrue(hasattr(result, 'stack_trace'))
        self.assertTrue(hasattr(result, 'report'))

    def test_execution_result_success_format(self):
        """Test successful ExecutionResult has correct format."""
        strategy = MockStrategy()

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim
        )

        # Success case
        self.assertTrue(result.success)
        self.assertIsNotNone(result.sharpe_ratio)
        self.assertIsNotNone(result.total_return)
        self.assertIsNotNone(result.max_drawdown)
        self.assertIsNone(result.error_type)
        self.assertIsNone(result.error_message)
        self.assertIsNone(result.stack_trace)

    def test_execution_result_error_format(self):
        """Test error ExecutionResult has correct format."""
        strategy = MockStrategy(should_fail=True)

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim
        )

        # Error case
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_type)
        self.assertIsNotNone(result.error_message)
        self.assertIsNotNone(result.stack_trace)
        # Metrics may be None for errors
        self.assertIsNone(result.sharpe_ratio)


class TestExecuteStrategyIntegration(unittest.TestCase):
    """Test execute_strategy() integration with hybrid architecture."""

    def setUp(self):
        """Set up test fixtures."""
        self.executor = BacktestExecutor(timeout=30)
        self.mock_data = Mock()

    def test_execute_strategy_compatible_with_champion_tracker(self):
        """Test that ExecutionResult from execute_strategy() works with ChampionTracker."""
        strategy = MockStrategy(strategy_id="momentum_v1", generation=1)

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim
        )

        # Verify result can be used for champion update
        self.assertTrue(result.success)

        # Build metrics dict for ChampionTracker
        metrics = {
            'sharpe_ratio': result.sharpe_ratio,
            'total_return': result.total_return,
            'max_drawdown': result.max_drawdown
        }

        # Verify metrics dict is complete
        self.assertIn('sharpe_ratio', metrics)
        self.assertIn('total_return', metrics)
        self.assertIn('max_drawdown', metrics)
        self.assertIsNotNone(metrics['sharpe_ratio'])

    def test_execute_strategy_isolation(self):
        """Test that execute_strategy() runs in isolated process (basic check)."""
        strategy = MockStrategy()

        result = self.executor.execute_strategy(
            strategy=strategy,
            data=self.mock_data,
            sim=mock_sim
        )

        # If isolation works, we get result back
        self.assertIsNotNone(result)
        self.assertTrue(result.success)


if __name__ == '__main__':
    unittest.main()
