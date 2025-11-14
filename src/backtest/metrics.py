"""
Performance metrics calculation for backtest results.

Calculates standard trading performance metrics using finlab's
built-in metrics functions and pandas operations.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from . import BacktestResult, PerformanceMetrics

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class StrategyMetrics:
    """Extracted metrics from finlab backtest reports.

    This dataclass represents key performance metrics extracted from
    finlab backtest report objects. All metrics are optional to handle
    cases where metrics cannot be extracted or are unavailable.

    Attributes:
        sharpe_ratio: Sharpe ratio of strategy returns (risk-adjusted return)
        total_return: Total return percentage (0.25 = 25% return)
        max_drawdown: Maximum peak-to-trough decline (negative value)
        win_rate: Percentage of winning trades (0.65 = 65% win rate)
        execution_success: Whether metrics were successfully extracted from report

    Examples:
        >>> metrics = StrategyMetrics(
        ...     sharpe_ratio=1.5,
        ...     total_return=0.25,
        ...     max_drawdown=-0.15,
        ...     win_rate=0.55,
        ...     execution_success=True
        ... )
        >>> print(f"Sharpe: {metrics.sharpe_ratio}, Return: {metrics.total_return:.1%}")
        Sharpe: 1.5, Return: 25.0%
    """

    sharpe_ratio: Optional[float] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    execution_success: bool = False

    def __post_init__(self):
        """Validate metrics after initialization."""
        # Ensure NaN values are converted to None
        if pd.isna(self.sharpe_ratio):
            self.sharpe_ratio = None
        if pd.isna(self.total_return):
            self.total_return = None
        if pd.isna(self.max_drawdown):
            self.max_drawdown = None
        if pd.isna(self.win_rate):
            self.win_rate = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert StrategyMetrics to dictionary format.

        Returns a dictionary representation of the metrics suitable for
        JSON serialization and backward compatibility with existing code
        that expects Dict[str, float] format.

        Returns:
            Dictionary with metric names as keys and values as numbers or bool

        Examples:
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5, total_return=0.25)
            >>> metrics.to_dict()
            {'sharpe_ratio': 1.5, 'total_return': 0.25, 'max_drawdown': None,
             'win_rate': None, 'execution_success': False}
        """
        return {
            'sharpe_ratio': self.sharpe_ratio,
            'total_return': self.total_return,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'execution_success': self.execution_success
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get() method for backward compatibility.

        Allows StrategyMetrics to be accessed like a dictionary while
        maintaining dataclass type safety benefits. Enables legacy code
        patterns like metrics.get('sharpe_ratio', 0) to work seamlessly.

        Special behavior: Returns default if attribute value is None,
        which is useful for empty metrics in comparison logic.

        Args:
            key: Metric attribute name ('sharpe_ratio', 'max_drawdown',
                 'win_rate', 'total_return', 'execution_success')
            default: Value to return if attribute not found or is None

        Returns:
            Attribute value if found and not None, otherwise default value

        Examples:
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5)
            >>> metrics.get('sharpe_ratio', 0)
            1.5
            >>> metrics = StrategyMetrics()  # All None
            >>> metrics.get('sharpe_ratio', 0)
            0
        """
        value = getattr(self, key, default)
        # Return default if value is None (for empty metrics)
        return value if value is not None else default

    def __getitem__(self, key: str) -> Any:
        """Dict-like bracket access for backward compatibility.

        Enables metrics['sharpe_ratio'] syntax for legacy code that
        expects dictionary-style access patterns.

        Args:
            key: Metric attribute name

        Returns:
            Attribute value

        Raises:
            KeyError: If attribute does not exist

        Examples:
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5)
            >>> metrics['sharpe_ratio']
            1.5
        """
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(f"Metric '{key}' not found")

    def __contains__(self, key: str) -> bool:
        """Dict-like 'in' operator for backward compatibility.

        Enables 'sharpe_ratio' in metrics syntax for checking if
        a metric attribute exists.

        Args:
            key: Metric attribute name

        Returns:
            True if attribute exists, False otherwise

        Examples:
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5)
            >>> 'sharpe_ratio' in metrics
            True
        """
        return hasattr(self, key)

    def keys(self) -> List[str]:
        """Dict-like keys() method for iteration compatibility.

        Returns list of all metric attribute names, matching dict.keys()
        behavior for code that iterates over metrics.

        Returns:
            List of metric attribute names

        Examples:
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5)
            >>> metrics.keys()
            ['sharpe_ratio', 'total_return', 'max_drawdown',
             'win_rate', 'execution_success']
        """
        return ['sharpe_ratio', 'total_return', 'max_drawdown',
                'win_rate', 'execution_success']

    def values(self) -> List[Any]:
        """Dict-like values() method for iteration compatibility.

        Returns list of all metric values in the same order as keys(),
        matching dict.values() behavior for code that iterates over values.

        Returns:
            List of metric values (Optional[float] or bool)

        Examples:
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5, total_return=0.25)
            >>> values = list(metrics.values())
            >>> 1.5 in values
            True
        """
        return [self.sharpe_ratio, self.total_return, self.max_drawdown,
                self.win_rate, self.execution_success]

    def items(self) -> List[Tuple[str, Any]]:
        """Dict-like items() method for iteration compatibility.

        Returns list of (key, value) tuples for all metrics, matching
        dict.items() behavior for code that iterates over key-value pairs.

        Returns:
            List of (key, value) tuples where value is Optional[float] or bool

        Examples:
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5)
            >>> items = list(metrics.items())
            >>> ('sharpe_ratio', 1.5) in items
            True
        """
        return [(key, getattr(self, key)) for key in self.keys()]

    def __len__(self) -> int:
        """Dict-like len() method for compatibility.

        Returns the number of metric fields (always 5), matching dict
        behavior for code that checks metric count.

        Returns:
            Number of metric fields (5)

        Examples:
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5)
            >>> len(metrics)
            5
        """
        return len(self.keys())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyMetrics':
        """Create StrategyMetrics from dictionary format.

        Supports backward compatibility by accepting dict-format metrics
        from historical JSONL files or legacy code. Missing fields use
        default values (None for metrics, False for execution_success).

        Args:
            data: Dictionary with metric names and values

        Returns:
            StrategyMetrics instance with values from dictionary

        Examples:
            >>> data = {'sharpe_ratio': 1.5, 'total_return': 0.25}
            >>> metrics = StrategyMetrics.from_dict(data)
            >>> metrics.sharpe_ratio
            1.5
        """
        return cls(
            sharpe_ratio=data.get('sharpe_ratio'),
            total_return=data.get('total_return'),
            max_drawdown=data.get('max_drawdown'),
            win_rate=data.get('win_rate'),
            execution_success=data.get('execution_success', False)
        )


def calculate_max_drawdown(equity_curve: list) -> float:
    """Calculate maximum drawdown from equity curve.

    Computes the peak-to-trough decline in portfolio value, representing
    the largest loss from a historical high. Returns negative value.

    The maximum drawdown measures the largest cumulative loss during a
    specific period, useful for understanding downside risk and capital
    preservation requirements.

    Formula: max_drawdown = min((equity - cummax(equity)) / cummax(equity))

    Args:
        equity_curve: List of equity values over time (e.g., portfolio values)

    Returns:
        Maximum drawdown as negative decimal (e.g., -0.25 for 25% drawdown)

    Notes:
        - Returns 0.0 for empty or single-value lists
        - Returns 0.0 if no drawdown occurred (monotonically increasing)
        - Uses numpy cumulative maximum for efficiency
        - Always returns non-positive values (0 or negative)

    Examples:
        >>> calculate_max_drawdown([100, 110, 105, 120, 90])
        -0.25  # 25% drawdown from 120 to 90
        >>> calculate_max_drawdown([100, 110, 120, 130])
        0.0  # No drawdown (always increasing)
        >>> calculate_max_drawdown([100])
        0.0  # Single value, no drawdown
        >>> calculate_max_drawdown([])
        0.0  # Empty list
    """
    # Convert to numpy array for efficient computation
    equity_array = np.array(equity_curve, dtype=float)

    # Handle edge cases
    if equity_array.size == 0 or len(equity_array) < 2:
        return 0.0

    # Handle NaN or infinite values
    if np.any(np.isnan(equity_array)) or np.any(np.isinf(equity_array)):
        return 0.0

    # Calculate running maximum using numpy cumulative max
    running_max = np.maximum.accumulate(equity_array)

    # Calculate drawdown at each point
    # drawdown = (current_value - peak_value) / peak_value
    drawdown = (equity_array - running_max) / running_max

    # Get maximum drawdown (most negative value)
    max_dd = float(np.min(drawdown))

    return max_dd


def calculate_calmar_ratio(annual_return: float, max_drawdown: float) -> Optional[float]:
    """Calculate Calmar Ratio: annual return divided by maximum drawdown.

    The Calmar ratio measures risk-adjusted return focusing on downside risk.
    Higher values indicate better risk-adjusted performance.

    Formula: calmar_ratio = annual_return / abs(max_drawdown)

    Args:
        annual_return: Annualized return as decimal (e.g., 0.15 for 15%)
        max_drawdown: Maximum drawdown as negative decimal (e.g., -0.20 for -20%)

    Returns:
        Calmar ratio as float, or None if inputs are invalid

    Notes:
        - Returns None for zero or near-zero drawdown (< 1e-10)
        - Returns None for NaN inputs
        - Can return negative values if annual_return is negative
        - Typical interpretation: >3.0 excellent, 2.0-3.0 good, 1.0-2.0 acceptable

    Examples:
        >>> calculate_calmar_ratio(0.15, -0.20)
        0.75
        >>> calculate_calmar_ratio(0.30, -0.10)
        3.0
        >>> calculate_calmar_ratio(0.10, 0.0)  # Zero drawdown
        None
        >>> calculate_calmar_ratio(-0.05, -0.10)  # Negative return
        -0.5
        >>> calculate_calmar_ratio(float('nan'), -0.10)  # Invalid input
        None
    """
    # Handle NaN inputs
    if pd.isna(annual_return) or pd.isna(max_drawdown):
        return None

    # Handle infinite inputs
    if np.isinf(annual_return) or np.isinf(max_drawdown):
        return None

    # Convert drawdown to absolute value
    abs_drawdown = abs(max_drawdown)

    # Handle zero or near-zero drawdown (epsilon threshold)
    if abs_drawdown < 1e-10:
        return None

    # Calculate Calmar ratio
    calmar_ratio = annual_return / abs_drawdown

    return float(calmar_ratio)


def calculate_metrics(backtest_result: "BacktestResult") -> "PerformanceMetrics":
    """Calculate performance metrics from backtest results.

    Computes standard performance metrics including:
    - Annualized return
    - Sharpe ratio
    - Maximum drawdown
    - Win rate
    - Profit factor
    - Total trades
    - Average holding period
    - Best/worst trades

    Args:
        backtest_result: Result from backtest execution

    Returns:
        PerformanceMetrics with calculated values

    Example:
        >>> metrics = calculate_metrics(backtest_result)
        >>> print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    """
    try:
        # Import finlab metrics
        from finlab.report import metrics as finlab_metrics  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("finlab.report.metrics not available, using fallback calculations")
        return _calculate_metrics_fallback(backtest_result)

    equity_curve = backtest_result.equity_curve
    trade_records = backtest_result.trade_records

    # Calculate annualized return
    try:
        annualized_return = finlab_metrics.annual_return(equity_curve)
        if pd.isna(annualized_return):
            annualized_return = 0.0
    except Exception as e:
        logger.warning(f"Failed to calculate annualized return: {e}")
        annualized_return = _calculate_annualized_return_fallback(equity_curve)

    # Calculate Sharpe ratio
    try:
        sharpe_ratio = finlab_metrics.sharpe_ratio(equity_curve)
        if pd.isna(sharpe_ratio):
            sharpe_ratio = 0.0
    except Exception as e:
        logger.warning(
            f"Failed to calculate Sharpe ratio using finlab metrics: {e}. "
            f"Using fallback calculation (may be inaccurate if equity_curve lacks DatetimeIndex)"
        )
        sharpe_ratio = _calculate_sharpe_ratio_fallback(equity_curve)

    # Calculate max drawdown
    try:
        max_drawdown = finlab_metrics.max_drawdown(equity_curve)
        if pd.isna(max_drawdown):
            max_drawdown = 0.0
    except Exception as e:
        logger.warning(f"Failed to calculate max drawdown: {e}")
        max_drawdown = _calculate_max_drawdown_fallback(equity_curve)

    # Calculate trade-based metrics
    total_trades = len(trade_records)

    if total_trades > 0:
        win_rate = _calculate_win_rate(trade_records)
        profit_factor = _calculate_profit_factor(trade_records)
        avg_holding_period = _calculate_avg_holding_period(trade_records)
        best_trade, worst_trade = _calculate_best_worst_trades(trade_records)
    else:
        win_rate = 0.0
        profit_factor = 0.0
        avg_holding_period = 0.0
        best_trade = 0.0
        worst_trade = 0.0

    # Import at runtime to avoid circular import
    from . import PerformanceMetrics

    return PerformanceMetrics(
        annualized_return=float(annualized_return),
        sharpe_ratio=float(sharpe_ratio),
        max_drawdown=float(max_drawdown),
        total_trades=int(total_trades),
        win_rate=float(win_rate),
        profit_factor=float(profit_factor),
        avg_holding_period=float(avg_holding_period),
        best_trade=float(best_trade),
        worst_trade=float(worst_trade)
    )


def _calculate_win_rate(trade_records: pd.DataFrame) -> float:
    """Calculate percentage of winning trades.

    Args:
        trade_records: DataFrame of trade records

    Returns:
        Win rate as percentage (0-1)
    """
    if len(trade_records) == 0:
        return 0.0

    # Try common column names for profit/loss
    pnl_col = None
    for col in ['pnl', 'profit_loss', 'return_pct', 'returns']:
        if col in trade_records.columns:
            pnl_col = col
            break

    if pnl_col is None:
        logger.warning("No P&L column found in trade records")
        return 0.0

    winning_trades = (trade_records[pnl_col] > 0).sum()
    return winning_trades / len(trade_records)


def _calculate_profit_factor(trade_records: pd.DataFrame) -> float:
    """Calculate profit factor (gross profits / gross losses).

    Args:
        trade_records: DataFrame of trade records

    Returns:
        Profit factor ratio
    """
    if len(trade_records) == 0:
        return 0.0

    # Try common column names for profit/loss
    pnl_col = None
    for col in ['pnl', 'profit_loss', 'return_pct', 'returns']:
        if col in trade_records.columns:
            pnl_col = col
            break

    if pnl_col is None:
        logger.warning("No P&L column found in trade records")
        return 0.0

    gross_profits = trade_records[trade_records[pnl_col] > 0][pnl_col].sum()
    gross_losses = abs(trade_records[trade_records[pnl_col] < 0][pnl_col].sum())

    if gross_losses == 0:
        return float('inf') if gross_profits > 0 else 0.0

    return float(gross_profits / gross_losses)


def _calculate_avg_holding_period(trade_records: pd.DataFrame) -> float:
    """Calculate average holding period in days.

    Args:
        trade_records: DataFrame of trade records

    Returns:
        Average holding period in days
    """
    if len(trade_records) == 0:
        return 0.0

    # Try to find entry and exit date columns
    entry_col = None
    exit_col = None

    for col in ['entry_date', 'entry_time', 'open_date']:
        if col in trade_records.columns:
            entry_col = col
            break

    for col in ['exit_date', 'exit_time', 'close_date']:
        if col in trade_records.columns:
            exit_col = col
            break

    if entry_col is None or exit_col is None:
        logger.warning("Entry/exit date columns not found in trade records")
        return 0.0

    # Calculate holding periods
    try:
        entry_dates = pd.to_datetime(trade_records[entry_col])
        exit_dates = pd.to_datetime(trade_records[exit_col])
        holding_periods = (exit_dates - entry_dates).dt.days
        return float(holding_periods.mean())
    except Exception as e:
        logger.warning(f"Failed to calculate holding period: {e}")
        return 0.0


def _calculate_best_worst_trades(trade_records: pd.DataFrame) -> Tuple[float, float]:
    """Calculate best and worst trade returns.

    Args:
        trade_records: DataFrame of trade records

    Returns:
        Tuple of (best_trade, worst_trade) as percentages
    """
    if len(trade_records) == 0:
        return 0.0, 0.0

    # Try common column names for profit/loss
    pnl_col = None
    for col in ['pnl', 'profit_loss', 'return_pct', 'returns']:
        if col in trade_records.columns:
            pnl_col = col
            break

    if pnl_col is None:
        logger.warning("No P&L column found in trade records")
        return 0.0, 0.0

    best_trade = float(trade_records[pnl_col].max())
    worst_trade = float(trade_records[pnl_col].min())

    return best_trade, worst_trade


def _calculate_metrics_fallback(backtest_result: "BacktestResult") -> "PerformanceMetrics":
    """Fallback metrics calculation when finlab metrics unavailable.

    Args:
        backtest_result: Result from backtest execution

    Returns:
        PerformanceMetrics with basic calculations
    """
    equity_curve = backtest_result.equity_curve
    trade_records = backtest_result.trade_records

    annualized_return = _calculate_annualized_return_fallback(equity_curve)
    sharpe_ratio = _calculate_sharpe_ratio_fallback(equity_curve)
    max_drawdown = _calculate_max_drawdown_fallback(equity_curve)

    total_trades = len(trade_records)
    if total_trades > 0:
        win_rate = _calculate_win_rate(trade_records)
        profit_factor = _calculate_profit_factor(trade_records)
        avg_holding_period = _calculate_avg_holding_period(trade_records)
        best_trade, worst_trade = _calculate_best_worst_trades(trade_records)
    else:
        win_rate = 0.0
        profit_factor = 0.0
        avg_holding_period = 0.0
        best_trade = 0.0
        worst_trade = 0.0

    # Import at runtime to avoid circular import
    from . import PerformanceMetrics

    return PerformanceMetrics(
        annualized_return=float(annualized_return),
        sharpe_ratio=float(sharpe_ratio),
        max_drawdown=float(max_drawdown),
        total_trades=int(total_trades),
        win_rate=float(win_rate),
        profit_factor=float(profit_factor),
        avg_holding_period=float(avg_holding_period),
        best_trade=float(best_trade),
        worst_trade=float(worst_trade)
    )


def _calculate_annualized_return_fallback(equity_curve: pd.Series) -> float:
    """Fallback calculation for annualized return.

    Args:
        equity_curve: Series of equity values over time

    Returns:
        Annualized return as decimal
    """
    if len(equity_curve) < 2:
        return 0.0

    total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1

    # Check if index is DatetimeIndex
    if isinstance(equity_curve.index, pd.DatetimeIndex):
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
    else:
        # Assume daily frequency if no datetime index
        days = len(equity_curve)

    if days <= 0:
        return 0.0

    years = days / 365.25
    annualized = (1 + total_return) ** (1 / years) - 1

    return float(annualized)


def _calculate_sharpe_ratio_fallback(equity_curve: pd.Series) -> float:
    """Fallback calculation for Sharpe ratio.

    Args:
        equity_curve: Series of equity values over time

    Returns:
        Sharpe ratio
    """
    if len(equity_curve) < 2:
        return 0.0

    returns = equity_curve.pct_change().dropna()

    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    # Infer data frequency and use correct annualization factor
    if isinstance(equity_curve.index, pd.DatetimeIndex):
        freq = pd.infer_freq(equity_curve.index)
        if freq is None:
            # Try to infer from first few periods
            if len(equity_curve) >= 2:
                days_diff = (equity_curve.index[1] - equity_curve.index[0]).days
                if days_diff >= 25:  # Monthly (~30 days)
                    annualization_factor = np.sqrt(12)
                elif days_diff >= 5:  # Weekly (~7 days)
                    annualization_factor = np.sqrt(52)
                else:  # Daily
                    annualization_factor = np.sqrt(252)
            else:
                annualization_factor = np.sqrt(252)  # Default to daily
        elif 'M' in freq or 'ME' in freq:  # Monthly
            annualization_factor = np.sqrt(12)
        elif 'W' in freq:  # Weekly
            annualization_factor = np.sqrt(52)
        else:  # Daily or other
            annualization_factor = np.sqrt(252)
    else:
        # Non-datetime index, default to daily assumption
        annualization_factor = np.sqrt(252)

    # Annualized Sharpe ratio
    mean_return = float(returns.mean())
    std_return = float(returns.std())
    sharpe = (mean_return / std_return) * annualization_factor

    return float(sharpe)


def _calculate_max_drawdown_fallback(equity_curve: pd.Series) -> float:
    """Fallback calculation for maximum drawdown.

    Args:
        equity_curve: Series of equity values over time

    Returns:
        Maximum drawdown as decimal (negative value)
    """
    if len(equity_curve) < 2:
        return 0.0

    # Calculate running maximum
    running_max = equity_curve.expanding().max()

    # Calculate drawdown
    drawdown = (equity_curve - running_max) / running_max

    max_dd = float(drawdown.min())

    return max_dd


class MetricsExtractor:
    """Extract metrics from finlab backtest report objects.

    Provides a unified interface for extracting key performance metrics
    from finlab.backtest report objects. Handles various report formats
    and gracefully manages missing/NaN values using pd.isna() checks.

    The extractor attempts to access metrics through multiple common
    attribute/method names to support different finlab versions and
    report structures.

    Example:
        >>> from finlab.backtest import sim
        >>> # Execute backtest to get report
        >>> report = sim(...)
        >>> extractor = MetricsExtractor()
        >>> metrics = extractor.extract_metrics(report)
        >>> if metrics.execution_success:
        ...     print(f"Sharpe: {metrics.sharpe_ratio}")
    """

    def extract_metrics(self, report: Any) -> StrategyMetrics:
        """Extract metrics from finlab backtest report.

        Uses the official finlab API methods (get_stats() and get_metrics())
        to extract performance metrics. These methods return dictionaries with
        standardized metric keys.

        Primary extraction method:
        - report.get_stats() - Returns comprehensive statistics dict

        Fallback extraction method:
        - report.get_metrics() - Returns structured dict with categories
          (profitability, risk, ratio, winrate, liquidity)

        Args:
            report: Finlab backtest report object (result from finlab.backtest.sim)

        Returns:
            StrategyMetrics dataclass with extracted metrics. All metrics will be
            None if extraction fails. execution_success will be True only if at
            least one metric was successfully extracted.

        Notes:
            - NaN values are converted to None
            - Non-numeric values are ignored and converted to None
            - If report is None or has no extractable metrics, returns
              StrategyMetrics with execution_success=False
            - All percentage-based metrics are returned as decimals
              (e.g., 0.15 for 15% return)
        """
        if report is None:
            logger.warning("Report is None, returning empty metrics")
            return StrategyMetrics(execution_success=False)

        # Initialize metrics container
        metrics = StrategyMetrics(execution_success=False)
        extracted_count = 0

        # Try to extract using get_stats() first (primary method)
        stats_dict = None
        try:
            if hasattr(report, 'get_stats'):
                stats_dict = report.get_stats()
                logger.debug(f"Retrieved stats dict with keys: {list(stats_dict.keys()) if stats_dict else None}")
        except Exception as e:
            logger.debug(f"Failed to call get_stats(): {type(e).__name__}: {e}")

        # If get_stats() worked, extract metrics from it
        if stats_dict and isinstance(stats_dict, dict):
            # Extract Sharpe Ratio (daily_sharpe or sharpe_ratio)
            sharpe = self._extract_from_dict(
                stats_dict,
                ['daily_sharpe', 'sharpe_ratio', 'sharpe', 'annual_sharpe']
            )
            if sharpe is not None:
                metrics.sharpe_ratio = sharpe
                extracted_count += 1
                logger.debug(f"Extracted sharpe_ratio: {sharpe}")

            # Extract Total Return
            total_return = self._extract_from_dict(
                stats_dict,
                ['total_return', 'cumulative_return', 'cum_return', 'return']
            )
            if total_return is not None:
                metrics.total_return = total_return
                extracted_count += 1
                logger.debug(f"Extracted total_return: {total_return}")

            # Extract Max Drawdown
            max_drawdown = self._extract_from_dict(
                stats_dict,
                ['max_drawdown', 'maximum_drawdown', 'mdd', 'drawdown']
            )
            if max_drawdown is not None:
                metrics.max_drawdown = max_drawdown
                extracted_count += 1
                logger.debug(f"Extracted max_drawdown: {max_drawdown}")

            # Extract Win Rate (win_ratio or win_rate)
            win_rate = self._extract_from_dict(
                stats_dict,
                ['win_ratio', 'win_rate', 'winning_rate', 'winrate']
            )
            if win_rate is not None:
                # Ensure value is between 0 and 1
                if 0 <= win_rate <= 1:
                    metrics.win_rate = win_rate
                    extracted_count += 1
                    logger.debug(f"Extracted win_rate: {win_rate}")
                else:
                    logger.warning(f"Invalid win_rate value {win_rate}, ignoring")

        # If get_stats() didn't work or didn't have all metrics, try get_metrics()
        if extracted_count == 0:
            try:
                if hasattr(report, 'get_metrics'):
                    metrics_dict = report.get_metrics()
                    logger.debug(f"Retrieved metrics dict with keys: {list(metrics_dict.keys()) if metrics_dict else None}")

                    if metrics_dict and isinstance(metrics_dict, dict):
                        # get_metrics() returns structured dict with categories
                        # Try to extract from 'ratio' category for Sharpe
                        if 'ratio' in metrics_dict:
                            sharpe = self._extract_from_dict(
                                metrics_dict['ratio'],
                                ['sharpe_ratio', 'sharpe', 'daily_sharpe']
                            )
                            if sharpe is not None:
                                metrics.sharpe_ratio = sharpe
                                extracted_count += 1

                        # Try to extract from 'profitability' category for return
                        if 'profitability' in metrics_dict:
                            total_return = self._extract_from_dict(
                                metrics_dict['profitability'],
                                ['total_return', 'annual_return', 'return']
                            )
                            if total_return is not None:
                                metrics.total_return = total_return
                                extracted_count += 1

                        # Try to extract from 'risk' category for drawdown
                        if 'risk' in metrics_dict:
                            max_drawdown = self._extract_from_dict(
                                metrics_dict['risk'],
                                ['max_drawdown', 'maximum_drawdown', 'mdd']
                            )
                            if max_drawdown is not None:
                                metrics.max_drawdown = max_drawdown
                                extracted_count += 1

                        # Try to extract from 'winrate' category
                        if 'winrate' in metrics_dict:
                            win_rate = self._extract_from_dict(
                                metrics_dict['winrate'],
                                ['win_ratio', 'win_rate', 'winning_rate']
                            )
                            if win_rate is not None and 0 <= win_rate <= 1:
                                metrics.win_rate = win_rate
                                extracted_count += 1

            except Exception as e:
                logger.debug(f"Failed to call get_metrics(): {type(e).__name__}: {e}")

        # Set execution_success if at least one metric was extracted
        metrics.execution_success = extracted_count > 0

        if metrics.execution_success:
            logger.info(f"Successfully extracted {extracted_count} metrics from report")
        else:
            logger.warning("Failed to extract any metrics from report")

        return metrics

    def _extract_attribute(
        self,
        obj: Any,
        attribute_names: list
    ) -> Optional[float]:
        """Extract numeric attribute from object using multiple possible names.

        Tries to access an attribute/property using multiple possible names.
        Handles both attributes and callable methods. Uses pd.isna() to check
        for NaN values.

        Args:
            obj: Object to extract attribute from
            attribute_names: List of possible attribute/method names to try

        Returns:
            Extracted float value, or None if:
            - Object is None
            - All attribute names fail
            - Extracted value is NaN
            - Extracted value is not numeric
            - Extraction raises exception

        Examples:
            >>> extractor = MetricsExtractor()
            >>> class Report:
            ...     sharpe_ratio = 1.5
            >>> report = Report()
            >>> val = extractor._extract_attribute(report, ['sharpe_ratio', 'sharpe'])
            >>> print(val)
            1.5
        """
        if obj is None:
            return None

        for attr_name in attribute_names:
            try:
                # Try to access as attribute
                value = getattr(obj, attr_name, None)

                # If not found as attribute, skip
                if value is None:
                    continue

                # If it's callable, call it
                if callable(value):
                    value = value()

                # Check if value is NaN
                if pd.isna(value):
                    logger.debug(f"Attribute {attr_name} is NaN, skipping")
                    continue

                # Try to convert to float
                float_value = float(value)

                # Check if converted value is NaN or infinite
                if np.isnan(float_value) or np.isinf(float_value):
                    logger.debug(
                        f"Attribute {attr_name} converted to invalid float "
                        f"({float_value}), skipping"
                    )
                    continue

                logger.debug(f"Successfully extracted {attr_name}: {float_value}")
                return float_value

            except (AttributeError, TypeError, ValueError) as e:
                logger.debug(f"Failed to extract {attr_name}: {type(e).__name__}")
                continue
            except Exception as e:
                logger.warning(
                    f"Unexpected error extracting {attr_name}: {type(e).__name__}: {e}"
                )
                continue

        return None

    def _extract_from_dict(
        self,
        data_dict: dict,
        key_names: list
    ) -> Optional[float]:
        """Extract numeric value from dictionary using multiple possible keys.

        Tries to access a value using multiple possible key names.
        Uses pd.isna() to check for NaN values.

        Args:
            data_dict: Dictionary to extract value from
            key_names: List of possible key names to try

        Returns:
            Extracted float value, or None if:
            - Dictionary is None or not a dict
            - All key names fail
            - Extracted value is NaN
            - Extracted value is not numeric
            - Extraction raises exception

        Examples:
            >>> extractor = MetricsExtractor()
            >>> stats = {'daily_sharpe': 1.5, 'total_return': 0.25}
            >>> val = extractor._extract_from_dict(stats, ['daily_sharpe', 'sharpe'])
            >>> print(val)
            1.5
        """
        if not isinstance(data_dict, dict):
            return None

        for key_name in key_names:
            try:
                # Try to access as dictionary key
                if key_name not in data_dict:
                    continue

                value = data_dict[key_name]

                # If value is None, skip
                if value is None:
                    continue

                # Check if value is NaN
                if pd.isna(value):
                    logger.debug(f"Key {key_name} is NaN, skipping")
                    continue

                # Try to convert to float
                float_value = float(value)

                # Check if converted value is NaN or infinite
                if np.isnan(float_value) or np.isinf(float_value):
                    logger.debug(
                        f"Key {key_name} converted to invalid float "
                        f"({float_value}), skipping"
                    )
                    continue

                logger.debug(f"Successfully extracted {key_name}: {float_value}")
                return float_value

            except (KeyError, TypeError, ValueError) as e:
                logger.debug(f"Failed to extract {key_name}: {type(e).__name__}")
                continue
            except Exception as e:
                logger.warning(
                    f"Unexpected error extracting {key_name}: {type(e).__name__}: {e}"
                )
                continue

        return None
