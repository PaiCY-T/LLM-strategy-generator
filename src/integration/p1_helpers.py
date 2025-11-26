"""
P1 Components Integration Helpers

Utility functions to facilitate integration of Spec B P1 components
with existing LLM strategy generation workflow.

Provides:
- Data format conversions (Series ↔ DataFrame)
- Metric extraction from backtest results
- Batch processing helpers
- Common usage patterns

Example:
    from src.integration.p1_helpers import (
        prepare_factor_data,
        extract_scoring_metrics,
        calculate_batch_slippage
    )

    # Prepare data for factors
    close_df, volume_df = prepare_factor_data(close_series, volume_series)

    # Extract metrics for scoring
    metrics = extract_scoring_metrics(backtest_result)

    # Calculate slippage for multiple trades
    slippages = calculate_batch_slippage(model, trades, advs, vols)
"""

import logging
from typing import Any, Dict, List, Union, Tuple

import numpy as np
import pandas as pd

from src.validation.execution_cost import ExecutionCostModel
from src.validation.liquidity_filter import LiquidityFilter
from src.validation.comprehensive_scorer import ComprehensiveScorer

logger = logging.getLogger(__name__)


def ensure_dataframe(
    data: Union[pd.Series, pd.DataFrame],
    column_name: str = 'value'
) -> pd.DataFrame:
    """Convert Series to single-column DataFrame if needed.

    Args:
        data: Input Series or DataFrame
        column_name: Column name if converting from Series

    Returns:
        DataFrame (unchanged if already DataFrame, converted if Series)

    Example:
        >>> series = pd.Series([1, 2, 3], index=dates)
        >>> df = ensure_dataframe(series, 'close')
        >>> assert isinstance(df, pd.DataFrame)
        >>> assert 'close' in df.columns
    """
    if isinstance(data, pd.Series):
        return pd.DataFrame({column_name: data})
    return data


def prepare_factor_data(
    close: Union[pd.Series, pd.DataFrame],
    volume: Union[pd.Series, pd.DataFrame] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare price and volume data for factor calculation.

    Ensures data is in correct DataFrame format expected by P1 factors.

    Args:
        close: Close prices (Series or DataFrame)
        volume: Trading volume (Series or DataFrame, optional)

    Returns:
        Tuple of (close_df, volume_df) in DataFrame format

    Example:
        >>> close_series = pd.Series([100, 101, 102])
        >>> volume_series = pd.Series([1M, 2M, 1.5M])
        >>> close_df, vol_df = prepare_factor_data(close_series, volume_series)
    """
    close_df = ensure_dataframe(close, 'close')

    if volume is not None:
        volume_df = ensure_dataframe(volume, 'volume')
    else:
        volume_df = None

    return close_df, volume_df


def extract_scoring_metrics(
    backtest_result: Any,
    monthly_returns: pd.Series = None
) -> Dict[str, Any]:
    """Extract metrics from backtest result for comprehensive scoring.

    Args:
        backtest_result: Backtest result object with metrics
        monthly_returns: Optional pre-calculated monthly returns

    Returns:
        Dict with metrics in format expected by ComprehensiveScorer

    Example:
        >>> metrics = extract_scoring_metrics(result)
        >>> scorer = ComprehensiveScorer()
        >>> score = scorer.compute_score(metrics)
    """
    # Extract basic metrics
    metrics = {
        'calmar_ratio': getattr(backtest_result, 'calmar_ratio', 0.0),
        'sortino_ratio': getattr(backtest_result, 'sortino_ratio', 0.0),
        'annual_turnover': getattr(backtest_result, 'annual_turnover', 2.0),
        'avg_slippage_bps': getattr(backtest_result, 'avg_slippage_bps', 25.0)
    }

    # Handle monthly returns
    if monthly_returns is not None:
        metrics['monthly_returns'] = monthly_returns
    elif hasattr(backtest_result, 'returns'):
        # Try to calculate from daily returns
        daily_returns = backtest_result.returns
        if isinstance(daily_returns, pd.Series):
            metrics['monthly_returns'] = daily_returns.resample('M').sum()
        else:
            # Default to empty Series
            metrics['monthly_returns'] = pd.Series()
    else:
        metrics['monthly_returns'] = pd.Series()

    return metrics


def calculate_batch_slippage(
    model: ExecutionCostModel,
    trade_sizes: Union[List[float], np.ndarray],
    advs: Union[List[float], np.ndarray],
    volatilities: Union[List[float], np.ndarray]
) -> List[float]:
    """Calculate slippage for multiple trades using scalar method.

    Convenience function for batch processing individual trades.

    Args:
        model: ExecutionCostModel instance
        trade_sizes: List/array of trade sizes
        advs: List/array of average daily volumes
        volatilities: List/array of volatility values

    Returns:
        List of slippage values in basis points

    Example:
        >>> model = ExecutionCostModel()
        >>> slippages = calculate_batch_slippage(
        ...     model,
        ...     [1M, 2M, 1.5M],
        ...     [50M, 60M, 55M],
        ...     [0.02, 0.025, 0.022]
        ... )
    """
    slippages = []
    for size, adv, vol in zip(trade_sizes, advs, volatilities):
        slippage = model.calculate_single_slippage(size, adv, vol)
        slippages.append(slippage)
    return slippages


def apply_liquidity_filter_simple(
    signals: pd.DataFrame,
    dollar_volumes: pd.DataFrame,
    capital: float = 40_000_000
) -> pd.DataFrame:
    """Apply liquidity filter with standard settings.

    Convenience wrapper for common liquidity filtering use case.

    Args:
        signals: Trading signals DataFrame (Dates x Symbols)
        dollar_volumes: Dollar volume DataFrame (Dates x Symbols)
        capital: Portfolio capital in TWD (default: 40M)

    Returns:
        Filtered signals DataFrame

    Example:
        >>> filtered = apply_liquidity_filter_simple(signals, dollar_vol)
    """
    filter = LiquidityFilter(capital=capital)
    return filter.apply_filter(signals, dollar_volumes)


def score_strategy_simple(
    calmar_ratio: float,
    sortino_ratio: float,
    monthly_returns: pd.Series,
    annual_turnover: float = 2.0,
    avg_slippage_bps: float = 25.0
) -> Dict[str, Any]:
    """Score strategy using comprehensive scorer with simple interface.

    Args:
        calmar_ratio: Calmar ratio (return/max_drawdown)
        sortino_ratio: Sortino ratio (return/downside_deviation)
        monthly_returns: Series of monthly returns
        annual_turnover: Annual portfolio turnover (default: 2.0)
        avg_slippage_bps: Average slippage in bps (default: 25)

    Returns:
        Scoring result dict with total_score and components

    Example:
        >>> result = score_strategy_simple(
        ...     calmar_ratio=2.5,
        ...     sortino_ratio=3.0,
        ...     monthly_returns=monthly_ret
        ... )
        >>> print(f"Score: {result['total_score']:.4f}")
    """
    scorer = ComprehensiveScorer()
    return scorer.compute_score({
        'calmar_ratio': calmar_ratio,
        'sortino_ratio': sortino_ratio,
        'monthly_returns': monthly_returns,
        'annual_turnover': annual_turnover,
        'avg_slippage_bps': avg_slippage_bps
    })


def combine_factor_signals(
    signals_dict: Dict[str, pd.DataFrame],
    weights_dict: Dict[str, float] = None
) -> pd.DataFrame:
    """Combine multiple factor signals with weights.

    Args:
        signals_dict: Dict mapping factor names to signal DataFrames
        weights_dict: Dict mapping factor names to weights (default: equal)

    Returns:
        Combined signals DataFrame

    Example:
        >>> signals = {
        ...     'rsi': rsi_result['signal'],
        ...     'rvol': rvol_result['signal']
        ... }
        >>> weights = {'rsi': 0.6, 'rvol': 0.4}
        >>> combined = combine_factor_signals(signals, weights)
    """
    if weights_dict is None:
        # Equal weighting
        n = len(signals_dict)
        weights_dict = {name: 1.0/n for name in signals_dict.keys()}

    # Normalize weights
    total_weight = sum(weights_dict.values())
    normalized_weights = {k: v/total_weight for k, v in weights_dict.items()}

    # Combine signals
    combined = pd.DataFrame(0.0, index=None, columns=None)
    for name, signal_df in signals_dict.items():
        weight = normalized_weights.get(name, 0.0)
        if combined.empty:
            combined = signal_df * weight
        else:
            combined = combined + (signal_df * weight)

    return combined


def calculate_strategy_volatility(
    returns: pd.Series,
    window: int = 20,
    annualize: bool = True
) -> float:
    """Calculate strategy volatility for execution cost estimation.

    Args:
        returns: Daily returns Series
        window: Rolling window for volatility (default: 20)
        annualize: Whether to annualize volatility (default: True)

    Returns:
        Volatility as float

    Example:
        >>> vol = calculate_strategy_volatility(daily_returns)
        >>> slippage = model.calculate_single_slippage(size, adv, vol)
    """
    rolling_std = returns.rolling(window=window, min_periods=1).std()
    current_vol = rolling_std.iloc[-1] if len(rolling_std) > 0 else 0.0

    if annualize and current_vol > 0:
        return current_vol * np.sqrt(252)

    return current_vol


def validate_p1_inputs(
    close: Any,
    volume: Any = None,
    signals: Any = None
) -> Tuple[bool, str]:
    """Validate inputs for P1 components.

    Args:
        close: Close prices data
        volume: Volume data (optional)
        signals: Trading signals (optional)

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        >>> valid, msg = validate_p1_inputs(close, volume)
        >>> if not valid:
        ...     raise ValueError(msg)
    """
    # Check close data
    if close is None:
        return False, "Close prices cannot be None"

    if isinstance(close, (pd.Series, pd.DataFrame)):
        if len(close) == 0:
            return False, "Close prices cannot be empty"
    else:
        return False, f"Close must be Series or DataFrame, got {type(close)}"

    # Check volume if provided
    if volume is not None:
        if isinstance(volume, (pd.Series, pd.DataFrame)):
            if len(volume) == 0:
                return False, "Volume cannot be empty"
            if len(volume) != len(close):
                return False, f"Volume length ({len(volume)}) != Close length ({len(close)})"
        else:
            return False, f"Volume must be Series or DataFrame, got {type(volume)}"

    # Check signals if provided
    if signals is not None:
        if isinstance(signals, (pd.Series, pd.DataFrame)):
            if len(signals) == 0:
                return False, "Signals cannot be empty"
        else:
            return False, f"Signals must be Series or DataFrame, got {type(signals)}"

    return True, ""
