"""
BacktestResult Data Structure

Defines the result structure for strategy backtest execution.
Used by StrategyFactory.execute() to return backtest metrics and errors.

Task: 19.3 - Implement execute() Method
Integration: BacktestExecutor, StrategyFactory

Data Structure:
    - BacktestResult: Comprehensive backtest metrics with error handling

Usage:
    from src.execution.backtest_result import BacktestResult

    # Successful execution
    result = BacktestResult(
        success=True,
        sharpe_ratio=1.5,
        total_return=0.25,
        max_drawdown=-0.10,
        win_rate=0.65,
        num_trades=150,
        execution_time=3.2
    )

    # Failed execution
    result = BacktestResult(
        success=False,
        error="Strategy validation failed: missing required field 'close'"
    )

See Also:
    - src/backtest/executor.py: ExecutionResult (lower-level execution result)
    - src/execution/strategy_factory.py: Uses BacktestResult
    - tests/execution/test_strategy_execution.py: Tests
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BacktestResult:
    """
    Result from strategy backtest execution.

    Encapsulates all metrics and error information from strategy backtest.
    Used by StrategyFactory.execute() to return results to calling code.

    Attributes:
        success: Whether backtest completed without errors
        sharpe_ratio: Annualized Sharpe ratio (higher is better, >1.0 is good)
        total_return: Total return percentage (e.g., 0.25 = 25% return)
        max_drawdown: Maximum drawdown (negative value, e.g., -0.10 = -10%)
        win_rate: Percentage of profitable trades (0.0-1.0, e.g., 0.65 = 65%)
        num_trades: Total number of trades executed
        execution_time: Backtest execution time in seconds
        error: Optional error message if backtest failed

    Example:
        >>> # Successful backtest
        >>> result = BacktestResult(
        ...     success=True,
        ...     sharpe_ratio=1.5,
        ...     total_return=0.25,
        ...     max_drawdown=-0.10,
        ...     win_rate=0.65,
        ...     num_trades=150,
        ...     execution_time=3.2
        ... )
        >>> assert result.success
        >>> assert result.sharpe_ratio == 1.5

        >>> # Failed backtest
        >>> result = BacktestResult(
        ...     success=False,
        ...     error="TimeoutError: Backtest exceeded 420s timeout"
        ... )
        >>> assert not result.success
        >>> assert "TimeoutError" in result.error

    Validation:
        - success must be boolean
        - If success=True, sharpe_ratio/total_return/max_drawdown should be set
        - If success=False, error should be set
        - win_rate must be in [0.0, 1.0] if specified
        - num_trades must be non-negative if specified
        - execution_time must be non-negative

    Integration:
        - StrategyFactory.execute() returns BacktestResult
        - Converted from ExecutionResult (from BacktestExecutor)
        - Used by learning iteration and validation logic
    """

    success: bool
    sharpe_ratio: Optional[float] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    num_trades: Optional[int] = None
    execution_time: float = 0.0
    error: Optional[str] = None

    def __post_init__(self):
        """
        Validate BacktestResult after initialization.

        Raises:
            ValueError: If any field is invalid
        """
        # Validate success
        if not isinstance(self.success, bool):
            raise ValueError(f"success must be a boolean, got: {self.success}")

        # Validate win_rate if specified
        if self.win_rate is not None:
            if not isinstance(self.win_rate, (int, float)):
                raise ValueError(f"win_rate must be numeric, got: {self.win_rate}")

            if not 0.0 <= self.win_rate <= 1.0:
                raise ValueError(
                    f"win_rate must be in [0.0, 1.0], got: {self.win_rate}"
                )

        # Validate num_trades if specified
        if self.num_trades is not None:
            if not isinstance(self.num_trades, int):
                raise ValueError(
                    f"num_trades must be an integer, got: {self.num_trades}"
                )

            if self.num_trades < 0:
                raise ValueError(
                    f"num_trades must be non-negative, got: {self.num_trades}"
                )

        # Validate execution_time
        if not isinstance(self.execution_time, (int, float)):
            raise ValueError(
                f"execution_time must be numeric, got: {self.execution_time}"
            )

        if self.execution_time < 0:
            raise ValueError(
                f"execution_time must be non-negative, got: {self.execution_time}"
            )

        # Validate logical consistency
        if self.success and self.error:
            raise ValueError(
                "success=True is inconsistent with error message being set"
            )

        if not self.success and not self.error:
            raise ValueError(
                "success=False requires error message to be set"
            )


__all__ = ["BacktestResult"]
