"""
BacktestExecutor: Isolated cross-platform backtest execution with timeout protection.

This module provides safe execution of trading strategy code in isolated processes
using multiprocessing for cross-platform timeout handling. Strategies are executed
with restricted globals containing only necessary finlab context (data, sim, pandas, numpy).

Key Features:
    - Cross-platform timeout protection (Windows, macOS, Linux)
    - Process isolation to prevent resource leaks
    - Queue-based inter-process communication
    - Comprehensive error handling with stack traces
    - ExecutionResult dataclass for structured output

Timeout Strategy:
    - Uses multiprocessing.Process with join(timeout) for portable timeout handling
    - Default timeout: 420 seconds (7 minutes)
    - Automatically terminates runaway processes
    - Captures all exceptions with full stack traces
"""

import multiprocessing as mp
import sys
import time
import traceback
from dataclasses import dataclass, field
from queue import Empty
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class ExecutionResult:
    """Result from isolated strategy execution.

    Attributes:
        success: Whether execution completed without errors
        error_type: Type of error if failed (e.g., 'TimeoutError', 'SyntaxError')
        error_message: Human-readable error message
        execution_time: Total execution time in seconds
        sharpe_ratio: Sharpe ratio from backtest (if successful)
        total_return: Total return percentage (if successful)
        max_drawdown: Maximum drawdown (if successful)
        report: Finlab backtest report object (if successful) - not serialized across processes
        stack_trace: Full stack trace if error occurred
    """

    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    sharpe_ratio: Optional[float] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    report: Optional[Any] = field(default=None, repr=False)  # Not serialized across processes
    stack_trace: Optional[str] = None


class BacktestExecutor:
    """Execute trading strategies in isolated processes with timeout protection.

    Provides safe execution of dynamically generated strategy code using:
    - Multiprocessing for process isolation (prevents resource leaks)
    - Cross-platform timeout via join(timeout)
    - Queue-based IPC for result passing
    - Restricted globals containing only finlab context

    The executor handles all exception types and returns structured ExecutionResult
    with comprehensive error information for debugging.

    Example:
        executor = BacktestExecutor(timeout=420)
        data = finlab.data  # Loaded separately
        sim = finlab.backtest.sim
        strategy_code = "buy = data.get(...) > data.get(...); return sim(...)"

        result = executor.execute(
            strategy_code=strategy_code,
            data=data,
            sim=sim,
            timeout=420
        )

        if result.success:
            print(f"Sharpe: {result.sharpe_ratio}")
        else:
            print(f"Error: {result.error_message}")
    """

    def __init__(self, timeout: int = 420):
        """Initialize BacktestExecutor.

        Args:
            timeout: Default timeout in seconds (default: 420 = 7 minutes)
                Can be overridden per execution via execute() call
        """
        self.timeout = timeout

    def execute(
        self,
        strategy_code: str,
        data: Any,
        sim: Any,
        timeout: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fee_ratio: Optional[float] = None,
        tax_ratio: Optional[float] = None,
    ) -> ExecutionResult:
        """Execute strategy code in isolated process with timeout protection.

        Executes the provided strategy code in a separate process with restricted
        globals containing only finlab context. All exceptions are caught and
        returned in ExecutionResult with full stack traces.

        Args:
            strategy_code: Python code to execute (must call sim() and return report)
            data: finlab.data object for strategy to use
            sim: finlab.backtest.sim function for backtesting
            timeout: Execution timeout in seconds (overrides default)
            start_date: Backtest start date (YYYY-MM-DD, default: 2018-01-01)
            end_date: Backtest end date (YYYY-MM-DD, default: 2024-12-31)
            fee_ratio: Transaction fee ratio (default: 0.001425 for Taiwan brokers)
            tax_ratio: Transaction tax ratio (default: 0.003 for Taiwan securities tax)

        Returns:
            ExecutionResult with execution status, metrics, and any errors

        Example:
            result = executor.execute(
                strategy_code='''
                    close = data.get("price:收盤價")
                    position = close > close.rolling(20).mean()

                    # Filter by date range (required for finlab API)
                    position = position.loc[start_date:end_date]

                    report = sim(
                        position,
                        fee_ratio=fee_ratio,
                        tax_ratio=tax_ratio,
                        resample="M",
                        position_limit=0.1,
                        stop_loss=0.08
                    )
                ''',
                data=data,
                sim=sim,
                start_date="2020-01-01",
                end_date="2021-12-31",
                fee_ratio=0.0,
                tax_ratio=0.003
            )
        """
        execution_timeout = timeout if timeout is not None else self.timeout

        # Create result queue for inter-process communication
        result_queue = mp.Queue()  # type: mp.Queue

        # Create process that will execute strategy in isolation
        process = mp.Process(
            target=self._execute_in_process,
            args=(strategy_code, data, sim, result_queue, start_date, end_date, fee_ratio, tax_ratio),
        )

        start_time = time.time()
        process.start()

        # Wait for process to complete or timeout
        process.join(timeout=execution_timeout)
        execution_time = time.time() - start_time

        # Check if process completed or timed out
        if process.is_alive():
            # Process is still running - timeout occurred
            process.terminate()
            process.join(timeout=5)  # Give it 5 seconds to clean up

            if process.is_alive():
                # Still running after terminate, force kill
                process.kill()
                process.join(timeout=2)

            return ExecutionResult(
                success=False,
                error_type="TimeoutError",
                error_message=f"Backtest execution exceeded timeout of {execution_timeout} seconds",
                execution_time=execution_time,
                stack_trace=f"Process killed after timeout ({execution_timeout}s)",
            )

        # Process completed - check for result
        try:
            result = result_queue.get(timeout=2)
            # Add final execution time if not already set
            if result.execution_time <= 0:
                result.execution_time = execution_time
            return result
        except Empty:
            # Process completed but no result in queue (unexpected error)
            return ExecutionResult(
                success=False,
                error_type="UnexpectedError",
                error_message="Process completed but produced no result",
                execution_time=execution_time,
                stack_trace="Queue was empty after process completion",
            )

    @staticmethod
    def _execute_in_process(
        strategy_code: str,
        data: Any,
        sim: Any,
        result_queue: Any,  # mp.Queue - using Any to avoid import issues
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fee_ratio: Optional[float] = None,
        tax_ratio: Optional[float] = None,
    ) -> None:
        """Execute strategy code in isolated process with restricted globals.

        This method runs in a separate process. It sets up restricted execution
        globals containing only finlab context, executes the strategy code,
        and passes results back via Queue.

        Args:
            strategy_code: Python code to execute
            data: finlab.data object
            sim: finlab.backtest.sim function
            result_queue: Queue for passing ExecutionResult back to parent (mp.Queue)
            start_date: Optional backtest start date (YYYY-MM-DD format)
            end_date: Optional backtest end date (YYYY-MM-DD format)
            fee_ratio: Optional transaction fee ratio (Taiwan default: 0.001425)
            tax_ratio: Optional transaction tax ratio (Taiwan default: 0.003)

        Note:
            - Runs in separate process (isolated from parent)
            - Execution globals restricted to: data, sim, pd, np, date ranges, fees
            - All exceptions caught and returned as ExecutionResult
            - Results passed via Queue (multiprocessing safe)
            - Date filtering: Strategy code must use position.loc[start_date:end_date]
        """
        start_time = time.time()

        try:
            # Set up restricted execution globals
            # Only provide finlab context + standard libraries
            execution_globals = {
                "data": data,
                "sim": sim,
                "pd": pd,
                "np": np,
                "start_date": start_date or "2018-01-01",  # Default: 7-year range for validation
                "end_date": end_date or "2024-12-31",      # Supports train/val/test split
                "fee_ratio": fee_ratio if fee_ratio is not None else 0.001425,  # Taiwan broker default
                "tax_ratio": tax_ratio if tax_ratio is not None else 0.003,     # Taiwan securities tax
                "__name__": "__main__",
                "__builtins__": __builtins__,
            }

            # Execute strategy code in isolated namespace
            exec(strategy_code, execution_globals)

            # If code executes successfully, it should have called sim()
            # and created a 'report' variable. Extract it.
            report = execution_globals.get("report")

            if report is None:
                result = ExecutionResult(
                    success=False,
                    error_type="ValueError",
                    error_message="Strategy code did not create 'report' variable. "
                    "Ensure code calls sim() and assigns result to 'report'.",
                    execution_time=time.time() - start_time,
                )
            else:
                # Extract metrics from report using finlab's get_stats() API
                sharpe_ratio = float("nan")
                total_return = float("nan")
                max_drawdown = float("nan")

                try:
                    if hasattr(report, 'get_stats'):
                        stats = report.get_stats()
                        if stats and isinstance(stats, dict):
                            # Extract metrics using finlab's standard key names
                            sharpe_ratio = stats.get('daily_sharpe', float("nan"))
                            total_return = stats.get('total_return', float("nan"))
                            max_drawdown = stats.get('max_drawdown', float("nan"))
                except Exception:
                    # If get_stats() fails, metrics remain as NaN
                    pass

                result = ExecutionResult(
                    success=True,
                    execution_time=time.time() - start_time,
                    # Note: report object is not serialized across process boundary
                    # Only the extracted metrics are passed back to parent
                    report=None,
                    sharpe_ratio=sharpe_ratio,
                    total_return=total_return,
                    max_drawdown=max_drawdown,
                )

        except SyntaxError as e:
            result = ExecutionResult(
                success=False,
                error_type="SyntaxError",
                error_message=f"Invalid Python syntax: {str(e)} at line {e.lineno}",
                execution_time=time.time() - start_time,
                stack_trace=traceback.format_exc(),
            )

        except TimeoutError as e:
            result = ExecutionResult(
                success=False,
                error_type="TimeoutError",
                error_message=str(e),
                execution_time=time.time() - start_time,
                stack_trace=traceback.format_exc(),
            )

        except Exception as e:
            # Catch all other exceptions with full stack trace
            result = ExecutionResult(
                success=False,
                error_type=type(e).__name__,
                error_message=str(e),
                execution_time=time.time() - start_time,
                stack_trace=traceback.format_exc(),
            )

        # Pass result back to parent via Queue
        result_queue.put(result)

    def execute_strategy(
        self,
        strategy: Any,  # Factor Graph Strategy object
        data: Any,
        sim: Any,
        timeout: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fee_ratio: Optional[float] = None,
        tax_ratio: Optional[float] = None,
        resample: str = "M",
    ) -> ExecutionResult:
        """Execute Factor Graph Strategy object in isolated process with timeout.

        This method handles Factor Graph Strategy DAG objects (not code strings).
        It calls strategy.to_pipeline() to get position signals, then passes them
        to finlab.backtest.sim() to generate a backtest report.

        Args:
            strategy: Factor Graph Strategy object (from src.factor_graph.strategy)
            data: finlab.data object for strategy to use
            sim: finlab.backtest.sim function for backtesting
            timeout: Execution timeout in seconds (overrides default)
            start_date: Backtest start date (YYYY-MM-DD, default: 2018-01-01)
            end_date: Backtest end date (YYYY-MM-DD, default: 2024-12-31)
            fee_ratio: Transaction fee ratio (default: 0.001425 for Taiwan brokers)
            tax_ratio: Transaction tax ratio (default: 0.003 for Taiwan securities tax)
            resample: Rebalancing frequency (default: "M" for monthly, can be "W" for weekly, "D" for daily)

        Returns:
            ExecutionResult with execution status, metrics, and any errors

        Example:
            >>> from src.factor_graph.strategy import Strategy
            >>> executor = BacktestExecutor(timeout=420)
            >>> strategy = Strategy(id="momentum_v1", generation=1)
            >>> # ... add factors to strategy ...
            >>> result = executor.execute_strategy(
            ...     strategy=strategy,
            ...     data=data,
            ...     sim=sim
            ... )
            >>> if result.success:
            ...     print(f"Sharpe: {result.sharpe_ratio}")
        """
        execution_timeout = timeout if timeout is not None else self.timeout

        # Create result queue for inter-process communication
        result_queue = mp.Queue()  # type: mp.Queue

        # Create process that will execute strategy in isolation
        process = mp.Process(
            target=self._execute_strategy_in_process,
            args=(strategy, data, sim, result_queue, start_date, end_date, fee_ratio, tax_ratio, resample),
        )

        start_time = time.time()
        process.start()

        # Wait for process to complete or timeout
        process.join(timeout=execution_timeout)
        execution_time = time.time() - start_time

        # Check if process completed or timed out
        if process.is_alive():
            # Process is still running - timeout occurred
            process.terminate()
            process.join(timeout=5)  # Give it 5 seconds to clean up

            if process.is_alive():
                # Still running after terminate, force kill
                process.kill()
                process.join(timeout=2)

            return ExecutionResult(
                success=False,
                error_type="TimeoutError",
                error_message=f"Strategy execution exceeded timeout of {execution_timeout} seconds",
                execution_time=execution_time,
                stack_trace=f"Process killed after timeout ({execution_timeout}s)",
            )

        # Process completed - check for result
        try:
            result = result_queue.get(timeout=2)
            # Add final execution time if not already set
            if result.execution_time <= 0:
                result.execution_time = execution_time
            return result
        except Empty:
            # Process completed but no result in queue (unexpected error)
            return ExecutionResult(
                success=False,
                error_type="UnexpectedError",
                error_message="Process completed but produced no result",
                execution_time=execution_time,
                stack_trace="Queue was empty after process completion",
            )

    @staticmethod
    def _execute_strategy_in_process(
        strategy: Any,  # Factor Graph Strategy object
        data: Any,
        sim: Any,
        result_queue: Any,  # mp.Queue
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fee_ratio: Optional[float] = None,
        tax_ratio: Optional[float] = None,
        resample: str = "M",
    ) -> None:
        """Execute Factor Graph Strategy in isolated process (Phase 2.0 Compatible).

        This method runs in a separate process. It executes the strategy DAG
        via to_pipeline() to get position signals, then calls sim() to backtest.

        Phase 2.0 Changes:
            - Strategy.to_pipeline() now accepts data module (not DataFrame)
            - Returns Dates×Symbols position matrix directly
            - Uses FinLabDataFrame container internally

        Args:
            strategy: Factor Graph Strategy object (Phase 2.0 matrix-native)
            data: finlab.data module (passed to strategy.to_pipeline())
            sim: finlab.backtest.sim function
            result_queue: Queue for passing ExecutionResult back to parent
            start_date: Optional backtest start date
            end_date: Optional backtest end date
            fee_ratio: Optional transaction fee ratio
            tax_ratio: Optional transaction tax ratio
            resample: Rebalancing frequency (default: "M" for monthly)
        """
        start_time = time.time()

        try:
            # Step 1: Execute strategy DAG to get position signals (Phase 2.0)
            # to_pipeline() now accepts data module and returns position matrix
            positions_df = strategy.to_pipeline(data)

            # Step 2: Filter by date range
            start = start_date or "2018-01-01"
            end = end_date or "2024-12-31"
            positions_df = positions_df.loc[start:end]

            # Step 3: Run backtest via sim()
            report = sim(
                positions_df,
                fee_ratio=fee_ratio if fee_ratio is not None else 0.001425,
                tax_ratio=tax_ratio if tax_ratio is not None else 0.003,
                resample=resample,  # Configurable rebalancing frequency
            )

            # Step 4: Extract metrics from report
            sharpe_ratio = float("nan")
            total_return = float("nan")
            max_drawdown = float("nan")

            try:
                if hasattr(report, 'get_stats'):
                    stats = report.get_stats()
                    if stats and isinstance(stats, dict):
                        sharpe_ratio = stats.get('daily_sharpe', float("nan"))
                        total_return = stats.get('total_return', float("nan"))
                        max_drawdown = stats.get('max_drawdown', float("nan"))
            except Exception:
                # If get_stats() fails, metrics remain as NaN
                pass

            # Create success result
            result = ExecutionResult(
                success=True,
                sharpe_ratio=sharpe_ratio if not pd.isna(sharpe_ratio) else None,
                total_return=total_return if not pd.isna(total_return) else None,
                max_drawdown=max_drawdown if not pd.isna(max_drawdown) else None,
                execution_time=time.time() - start_time,
                report=report,  # Include report for further analysis
            )

        except Exception as e:
            # Catch all exceptions with full stack trace
            result = ExecutionResult(
                success=False,
                error_type=type(e).__name__,
                error_message=str(e),
                execution_time=time.time() - start_time,
                stack_trace=traceback.format_exc(),
            )

        # Pass result back to parent via Queue
        result_queue.put(result)


def _extract_metric(
    report: Any,
    metric_name: str,
    default: Any = None,
) -> Any:
    """Safely extract metric from finlab backtest report object.

    Handles different report object types and missing attributes gracefully.

    Args:
        report: Finlab backtest report object
        metric_name: Name of metric to extract
        default: Default value if metric not found

    Returns:
        Metric value or default if not found
    """
    try:
        # Try dictionary-style access
        if isinstance(report, dict):
            return report.get(metric_name, default)

        # Try attribute access
        if hasattr(report, metric_name):
            return getattr(report, metric_name)

        # Try lowercase attribute
        if hasattr(report, metric_name.lower()):
            return getattr(report, metric_name.lower())

        # Try underscore-prefixed attribute
        underscore_name = "_" + metric_name
        if hasattr(report, underscore_name):
            return getattr(report, underscore_name)

        return default

    except (AttributeError, KeyError, TypeError):
        return default


__all__ = [
    "BacktestExecutor",
    "ExecutionResult",
]
