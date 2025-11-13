"""
Backtesting Engine Layer.

Executes trading strategies asynchronously and calculates performance metrics.
Integrates with Finlab backtesting framework for accurate simulation.

Key Components:
    - BacktestEngine: Core backtesting execution engine
    - Strategy validation and code safety checks
    - Performance metrics calculation
    - Visualization generation
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import pandas as pd

if TYPE_CHECKING:
    from plotly.graph_objs import Figure  # type: ignore[import-not-found]
else:
    Figure = Any


@dataclass
class BacktestResult:
    """Result data from a backtest execution.

    Attributes:
        portfolio_positions: DataFrame of portfolio positions over time
        trade_records: DataFrame of individual trade details
        equity_curve: Series of cumulative returns over time
        raw_result: Raw result object from finlab.backtest.sim()
    """
    portfolio_positions: pd.DataFrame
    trade_records: pd.DataFrame
    equity_curve: pd.Series
    raw_result: Any  # finlab backtest result object


@dataclass
class PerformanceMetrics:
    """Standard performance metrics from backtest results.

    Attributes:
        annualized_return: Annual return percentage
        sharpe_ratio: Risk-adjusted return metric
        max_drawdown: Maximum peak-to-trough decline
        total_trades: Total number of trades executed
        win_rate: Percentage of winning trades
        profit_factor: Ratio of gross profits to gross losses
        avg_holding_period: Average days per position
        best_trade: Best single trade return percentage
        worst_trade: Worst single trade return percentage
    """
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    profit_factor: float
    avg_holding_period: float = 0.0
    best_trade: float = 0.0
    worst_trade: float = 0.0


# Import metrics functions after dataclasses are defined to avoid circular import
from .classifier import ClassificationResult, SuccessClassifier
from .error_classifier import ErrorCategory, ErrorClassifier
from .executor import BacktestExecutor, ExecutionResult
from .metrics import (
    MetricsExtractor,
    StrategyMetrics,
    calculate_calmar_ratio,
    calculate_max_drawdown,
)
from .reporter import ReportMetrics, ResultsReporter


class BacktestEngine:
    """Core backtest execution engine.

    Provides async backtest execution with safety validation,
    metrics calculation, and visualization generation.
    """

    async def run_backtest(
        self,
        strategy_code: str,
        data_config: Dict[str, Any],
        backtest_params: Dict[str, Any]
    ) -> BacktestResult:
        """Execute backtest asynchronously.

        Args:
            strategy_code: Python code defining trading strategy
            data_config: Configuration for data retrieval
            backtest_params: Backtest execution parameters

        Returns:
            BacktestResult containing positions, trades, and equity curve

        Raises:
            ValueError: If strategy code is invalid or unsafe
            RuntimeError: If backtest execution fails
        """
        raise NotImplementedError("Implemented in engine.py")

    def validate_strategy_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate strategy code for safety and correctness.

        Args:
            code: Python code to validate

        Returns:
            Tuple of (is_valid, error_message)
            error_message is None if valid
        """
        raise NotImplementedError("Implemented in engine.py")

    def calculate_metrics(self, backtest_result: BacktestResult) -> PerformanceMetrics:
        """Calculate performance metrics from backtest results.

        Args:
            backtest_result: Result from run_backtest()

        Returns:
            PerformanceMetrics with calculated values
        """
        raise NotImplementedError("Implemented in metrics.py")

    def generate_visualizations(
        self,
        backtest_result: BacktestResult
    ) -> Dict[str, Figure]:
        """Generate visualization charts for backtest results.

        Args:
            backtest_result: Result from run_backtest()

        Returns:
            Dictionary mapping chart names to Plotly figures
        """
        raise NotImplementedError("Implemented in visualizer.py")


__all__ = [
    "BacktestEngine",
    "BacktestResult",
    "BacktestExecutor",
    "ClassificationResult",
    "ErrorCategory",
    "ErrorClassifier",
    "ExecutionResult",
    "MetricsExtractor",
    "PerformanceMetrics",
    "ReportMetrics",
    "ResultsReporter",
    "StrategyMetrics",
    "SuccessClassifier",
    "calculate_calmar_ratio",
    "calculate_max_drawdown"
]
