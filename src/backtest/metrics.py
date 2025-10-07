"""
Performance metrics calculation for backtest results.

Calculates standard trading performance metrics using finlab's
built-in metrics functions and pandas operations.
"""

import logging
from typing import Tuple

import numpy as np
import pandas as pd

from ..backtest import BacktestResult, PerformanceMetrics

# Configure logging
logger = logging.getLogger(__name__)


def calculate_metrics(backtest_result: BacktestResult) -> PerformanceMetrics:
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
        logger.warning(f"Failed to calculate Sharpe ratio: {e}")
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


def _calculate_metrics_fallback(backtest_result: BacktestResult) -> PerformanceMetrics:
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

    # Annualized Sharpe (assuming daily returns)
    mean_return = float(returns.mean())
    std_return = float(returns.std())
    sharpe = (mean_return / std_return) * np.sqrt(252)

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
