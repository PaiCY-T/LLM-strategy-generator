"""
Parameter Search Spaces for Strategy Templates

Defines Optuna-compatible parameter search spaces for 6 diverse strategy templates.
Each template represents a distinct trading approach with appropriate parameter ranges.

Templates:
1. Momentum: Trend-following with trailing stops
2. Mean Reversion: RSI-based oversold/overbought
3. Breakout Trend: Volume-confirmed breakouts
4. Volatility Adaptive: Bollinger Band based
5. Dual Momentum: Moving average crossovers
6. Regime Adaptive: Efficiency ratio based

All parameters use trial.suggest_*() methods for TPE optimization.
"""

import optuna
from typing import Dict, Any


def momentum_search_space(trial: optuna.Trial) -> Dict[str, Any]:
    """
    Define parameter search space for Momentum template.

    Strategy: Trend-following with momentum indicators and trailing stops.

    Parameters:
        lookback_days: Period for momentum calculation (20-60 days)
        entry_threshold: Minimum momentum strength for entry (0.5-2.0)
        exit_lookback: Period for reverse momentum detection (10-30 days)
        trailing_stop_pct: Trailing stop loss percentage (2-10%)
        position_size_pct: Position size as % of portfolio (5-20%)

    Returns:
        Dictionary of parameters compatible with Optuna trial
    """
    return {
        'lookback_days': trial.suggest_int('lookback_days', 20, 60),
        'entry_threshold': trial.suggest_float('entry_threshold', 0.5, 2.0),
        'exit_lookback': trial.suggest_int('exit_lookback', 10, 30),
        'trailing_stop_pct': trial.suggest_float('trailing_stop_pct', 0.02, 0.10),
        'position_size_pct': trial.suggest_float('position_size_pct', 0.05, 0.20)
    }


def mean_reversion_search_space(trial: optuna.Trial) -> Dict[str, Any]:
    """
    Define parameter search space for Mean Reversion template.

    Strategy: RSI-based mean reversion with oversold/overbought zones.

    Parameters:
        rsi_period: Period for RSI calculation (10-30 days)
        rsi_oversold: RSI level for entry (20-40)
        rsi_overbought: RSI level for short entry (60-80)
        rsi_neutral_low: Lower bound of neutral exit zone (45-50)
        rsi_neutral_high: Upper bound of neutral exit zone (50-55)
        position_size_pct: Position size as % of portfolio (3-15%)

    Returns:
        Dictionary of parameters compatible with Optuna trial
    """
    return {
        'rsi_period': trial.suggest_int('rsi_period', 10, 30),
        'rsi_oversold': trial.suggest_int('rsi_oversold', 20, 40),
        'rsi_overbought': trial.suggest_int('rsi_overbought', 60, 80),
        'rsi_neutral_low': trial.suggest_int('rsi_neutral_low', 45, 50),
        'rsi_neutral_high': trial.suggest_int('rsi_neutral_high', 50, 55),
        'position_size_pct': trial.suggest_float('position_size_pct', 0.03, 0.15)
    }


def breakout_trend_search_space(trial: optuna.Trial) -> Dict[str, Any]:
    """
    Define parameter search space for Breakout Trend template.

    Strategy: Price breakouts confirmed by volume spikes with ATR-based stops.

    Parameters:
        breakout_lookback: Period for breakout level (20-60 days)
        volume_multiplier: Volume confirmation threshold (1.2-3.0x average)
        atr_period: Period for ATR calculation (10-30 days)
        atr_stop_multiplier: ATR multiplier for stop loss (1.5-4.0x)
        position_size_pct: Position size as % of portfolio (5-20%)

    Returns:
        Dictionary of parameters compatible with Optuna trial
    """
    return {
        'breakout_lookback': trial.suggest_int('breakout_lookback', 20, 60),
        'volume_multiplier': trial.suggest_float('volume_multiplier', 1.2, 3.0),
        'atr_period': trial.suggest_int('atr_period', 10, 30),
        'atr_stop_multiplier': trial.suggest_float('atr_stop_multiplier', 1.5, 4.0),
        'position_size_pct': trial.suggest_float('position_size_pct', 0.05, 0.20)
    }


def volatility_adaptive_search_space(trial: optuna.Trial) -> Dict[str, Any]:
    """
    Define parameter search space for Volatility Adaptive template.

    Strategy: Bollinger Band-based mean reversion with adaptive position sizing.

    Parameters:
        bb_period: Period for Bollinger Bands (15-40 days)
        bb_std_dev: Standard deviations for bands (1.5-3.0)
        entry_percentb_low: Lower %B threshold for entry (0.0-0.2)
        entry_percentb_high: Upper %B threshold for entry (0.8-1.0)
        exit_percentb_low: Lower %B neutral zone (0.4-0.5)
        exit_percentb_high: Upper %B neutral zone (0.5-0.6)
        base_position_pct: Base position size (2-10%, scales with volatility)

    Returns:
        Dictionary of parameters compatible with Optuna trial
    """
    return {
        'bb_period': trial.suggest_int('bb_period', 15, 40),
        'bb_std_dev': trial.suggest_float('bb_std_dev', 1.5, 3.0),
        'entry_percentb_low': trial.suggest_float('entry_percentb_low', 0.0, 0.2),
        'entry_percentb_high': trial.suggest_float('entry_percentb_high', 0.8, 1.0),
        'exit_percentb_low': trial.suggest_float('exit_percentb_low', 0.4, 0.5),
        'exit_percentb_high': trial.suggest_float('exit_percentb_high', 0.5, 0.6),
        'base_position_pct': trial.suggest_float('base_position_pct', 0.02, 0.10)
    }


def dual_momentum_search_space(trial: optuna.Trial) -> Dict[str, Any]:
    """
    Define parameter search space for Dual Momentum template.

    Strategy: Moving average crossovers with stop losses.

    Parameters:
        short_ma_period: Short moving average period (5-20 days)
        long_ma_period: Long moving average period (20-60 days)
        stop_loss_pct: Fixed stop loss percentage (5-15%)
        confirmation_bars: Bars to confirm crossover (1-5)
        position_size_pct: Position size as % of portfolio (5-20%)

    Returns:
        Dictionary of parameters compatible with Optuna trial
    """
    return {
        'short_ma_period': trial.suggest_int('short_ma_period', 5, 20),
        'long_ma_period': trial.suggest_int('long_ma_period', 20, 60),
        'stop_loss_pct': trial.suggest_float('stop_loss_pct', 0.05, 0.15),
        'confirmation_bars': trial.suggest_int('confirmation_bars', 1, 5),
        'position_size_pct': trial.suggest_float('position_size_pct', 0.05, 0.20)
    }


def regime_adaptive_search_space(trial: optuna.Trial) -> Dict[str, Any]:
    """
    Define parameter search space for Regime Adaptive template.

    Strategy: Efficiency Ratio-based regime detection (trending vs mean-reverting).

    Parameters:
        er_period: Period for Efficiency Ratio calculation (10-40 days)
        er_trending_threshold: ER threshold for trending regime (0.3-0.7)
        er_meanrev_threshold: ER threshold for mean-reverting regime (0.2-0.5)
        trend_lookback: Lookback for trend strength (15-45 days)
        position_size_pct: Position size as % of portfolio (5-20%)

    Returns:
        Dictionary of parameters compatible with Optuna trial
    """
    return {
        'er_period': trial.suggest_int('er_period', 10, 40),
        'er_trending_threshold': trial.suggest_float('er_trending_threshold', 0.3, 0.7),
        'er_meanrev_threshold': trial.suggest_float('er_meanrev_threshold', 0.2, 0.5),
        'trend_lookback': trial.suggest_int('trend_lookback', 15, 45),
        'position_size_pct': trial.suggest_float('position_size_pct', 0.05, 0.20)
    }
