"""
Backtest execution engine with async support.

Provides async backtest execution using finlab.backtest.sim()
with validation, sandboxing, and result processing.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from .sandbox import create_safe_globals, execute_with_limits
from .validation import validate_strategy_code
from ..backtest import BacktestResult

# Configure logging
logger = logging.getLogger(__name__)


class BacktestEngineImpl:
    """Implementation of backtest execution engine.

    Provides async backtest execution with safety validation,
    metrics calculation, and zero trades detection.
    """

    def __init__(self, timeout: int = 120, memory_limit_mb: int = 500) -> None:
        """Initialize backtest engine.

        Args:
            timeout: Maximum execution time in seconds (default: 120)
            memory_limit_mb: Maximum memory usage in MB (default: 500)
        """
        self.timeout = timeout
        self.memory_limit_mb = memory_limit_mb
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._is_shutdown = False

    def validate_strategy_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate strategy code for safety and correctness.

        Args:
            code: Python code to validate

        Returns:
            Tuple of (is_valid, error_message)
            error_message is None if valid
        """
        return validate_strategy_code(code)

    async def run_backtest(
        self,
        strategy_code: str,
        data_config: Dict[str, Any],
        backtest_params: Dict[str, Any]
    ) -> BacktestResult:
        """Execute backtest asynchronously.

        Args:
            strategy_code: Python code defining trading strategy
            data_config: Configuration for data retrieval (unused for now)
            backtest_params: Backtest execution parameters

        Returns:
            BacktestResult containing positions, trades, and equity curve

        Raises:
            ValueError: If strategy code is invalid or unsafe
            RuntimeError: If backtest execution fails or produces zero trades
        """
        # Validate strategy code
        is_valid, error = self.validate_strategy_code(strategy_code)
        if not is_valid:
            logger.error(f"Strategy validation failed: {error}")
            raise ValueError(f"Invalid strategy code: {error}")

        # Execute backtest in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self._executor,
                self._execute_backtest_sync,
                strategy_code,
                backtest_params
            )
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}")
            raise RuntimeError(f"Backtest execution failed: {e}") from e

        # Check for zero trades
        total_trades = len(result.trade_records)
        if total_trades == 0:
            logger.warning("Backtest produced zero trades")
            error_msg = (
                "Backtest produced zero trades. "
                "Please review your entry/exit conditions. "
                "Consider:\n"
                "- Widening entry signal thresholds\n"
                "- Checking data availability for the backtest period\n"
                "- Verifying position generation logic"
            )
            raise RuntimeError(error_msg)

        logger.info(f"Backtest completed successfully with {total_trades} trades")
        return result

    def _execute_backtest_sync(
        self,
        strategy_code: str,
        backtest_params: Dict[str, Any]
    ) -> BacktestResult:
        """Execute backtest synchronously (called from thread pool).

        Args:
            strategy_code: Python code defining trading strategy
            backtest_params: Backtest execution parameters

        Returns:
            BacktestResult containing positions, trades, and equity curve

        Raises:
            RuntimeError: If execution fails
        """
        # Create safe execution environment
        safe_globals = create_safe_globals()

        # Add backtest parameters to environment
        safe_globals.update(backtest_params)

        # Execute strategy code in sandbox
        try:
            result_globals = execute_with_limits(
                strategy_code,
                timeout=self.timeout,
                memory_limit_mb=self.memory_limit_mb,
                globals_dict=safe_globals
            )
        except Exception as e:
            raise RuntimeError(f"Strategy execution failed: {e}") from e

        # Extract position DataFrame from result
        # Strategy should create 'position' variable
        if 'position' not in result_globals:
            raise RuntimeError(
                "Strategy code must define 'position' variable "
                "containing position DataFrame"
            )

        position_df = result_globals['position']
        if not isinstance(position_df, pd.DataFrame):
            raise RuntimeError(
                f"'position' must be a pandas DataFrame, "
                f"got {type(position_df).__name__}"
            )

        # Execute backtest using finlab
        try:
            import finlab  # type: ignore[import-untyped]  # noqa: F401
            from finlab import backtest

            # Run simulation
            sim_result = backtest.sim(
                position_df,
                **backtest_params.get('sim_params', {})
            )

        except ImportError as e:
            raise RuntimeError(
                "finlab package not available. "
                "Please install with: pip install finlab"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Finlab backtest simulation failed: {e}"
            ) from e

        # Extract results from sim object
        try:
            # Get trade records
            if hasattr(sim_result, 'trades'):
                trade_records = sim_result.trades
            elif hasattr(sim_result, 'get_trades'):
                trade_records = sim_result.get_trades()
            else:
                # Create empty trade records
                trade_records = pd.DataFrame()

            # Get equity curve
            if hasattr(sim_result, 'equity_curve'):
                equity_curve = sim_result.equity_curve
            elif hasattr(sim_result, 'get_equity_curve'):
                equity_curve = sim_result.get_equity_curve()
            else:
                # Create empty equity curve
                equity_curve = pd.Series(dtype=float)

            # Portfolio positions (original input)
            portfolio_positions = position_df

        except Exception as e:
            logger.error(f"Failed to extract backtest results: {e}")
            raise RuntimeError(
                f"Failed to extract backtest results: {e}"
            ) from e

        return BacktestResult(
            portfolio_positions=portfolio_positions,
            trade_records=trade_records,
            equity_curve=equity_curve,
            raw_result=sim_result
        )

    def close(self) -> None:
        """Shutdown the thread pool executor gracefully.

        This method ensures all pending tasks complete before shutdown.
        Safe to call multiple times.

        Example:
            >>> engine = BacktestEngineImpl()
            >>> try:
            ...     result = await engine.run_backtest(code, config, params)
            ... finally:
            ...     engine.close()
        """
        if not self._is_shutdown:
            self._executor.shutdown(wait=True)
            self._is_shutdown = True
            logger.debug("BacktestEngine shutdown complete")

    def __enter__(self) -> "BacktestEngineImpl":
        """Enter context manager.

        Returns:
            Self for context manager usage

        Example:
            >>> async with BacktestEngineImpl() as engine:
            ...     result = await engine.run_backtest(code, config, params)
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Optional[Any]
    ) -> None:
        """Exit context manager and cleanup resources.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        self.close()
