"""
Market Regime Detection using SMA Crossover and Volatility.

This module provides functionality to detect market regimes based on:
- Trend direction: SMA(50) vs SMA(200) crossover
- Volatility level: Annualized volatility vs threshold

Market regimes help adapt strategy selection to current market conditions.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class MarketRegime(Enum):
    """Market regime classification based on trend and volatility."""

    BULL_CALM = "bull_calm"  # Uptrend + low volatility
    BULL_VOLATILE = "bull_volatile"  # Uptrend + high volatility
    BEAR_CALM = "bear_calm"  # Downtrend + low volatility
    BEAR_VOLATILE = "bear_volatile"  # Downtrend + high volatility


@dataclass
class RegimeStats:
    """Detailed statistics for detected market regime.

    Attributes:
        regime: Detected market regime classification
        trend_direction: "bullish" or "bearish"
        volatility_level: "calm" or "volatile"
        annualized_volatility: Annualized volatility (0-1 scale)
        sma_50: 50-period simple moving average value
        sma_200: 200-period simple moving average value
        confidence: Confidence score (0-1) based on data quality
    """

    regime: MarketRegime
    trend_direction: str
    volatility_level: str
    annualized_volatility: float
    sma_50: float
    sma_200: float
    confidence: float


class RegimeDetector:
    """Detect market regime using SMA crossover and volatility analysis.

    Uses a dual-factor approach:
    1. Trend: SMA(50) vs SMA(200) crossover
       - Bullish when SMA(50) > SMA(200)
       - Bearish when SMA(50) < SMA(200)

    2. Volatility: Annualized volatility vs threshold
       - Calm when volatility < threshold (default 20%)
       - Volatile when volatility >= threshold

    Examples:
        >>> import pandas as pd
        >>> import numpy as np
        >>> dates = pd.date_range('2020-01-01', periods=250, freq='D')
        >>> prices = pd.Series(np.linspace(100, 150, 250), index=dates)
        >>> detector = RegimeDetector()
        >>> regime = detector.detect_regime(prices)
        >>> print(regime)
        MarketRegime.BULL_CALM
        >>> stats = detector.get_regime_stats(prices)
        >>> print(f"Trend: {stats.trend_direction}, Vol: {stats.volatility_level}")
        Trend: bullish, Vol: calm
    """

    def __init__(self, volatility_threshold: float = 0.20):
        """Initialize regime detector.

        Args:
            volatility_threshold: Annualized volatility threshold (default 0.20 = 20%)
                Above this threshold, regime is considered volatile

        Raises:
            ValueError: If volatility_threshold is not positive
        """
        if volatility_threshold <= 0:
            raise ValueError(f"volatility_threshold must be positive, got {volatility_threshold}")

        self.volatility_threshold = volatility_threshold

    def detect_regime(self, prices: pd.Series) -> MarketRegime:
        """Detect market regime using SMA crossover and volatility.

        Args:
            prices: Price series with DatetimeIndex (daily frequency)

        Returns:
            MarketRegime enum value

        Raises:
            ValueError: If insufficient data (need ≥200 points for SMA(200))

        Examples:
            >>> dates = pd.date_range('2020-01-01', periods=250, freq='D')
            >>> # Uptrend + low vol
            >>> prices = pd.Series(np.linspace(100, 150, 250), index=dates)
            >>> detector = RegimeDetector()
            >>> detector.detect_regime(prices)
            MarketRegime.BULL_CALM
            >>> # Downtrend + high vol
            >>> trend = np.linspace(150, 100, 250)
            >>> noise = np.random.randn(250) * 10
            >>> prices = pd.Series(trend + noise, index=dates)
            >>> detector.detect_regime(prices)
            MarketRegime.BEAR_VOLATILE
        """
        # Validate data
        if len(prices) < 200:
            raise ValueError(f"Need ≥200 data points, got {len(prices)}")

        # Calculate SMAs
        sma_50 = prices.rolling(window=50).mean().iloc[-1]
        sma_200 = prices.rolling(window=200).mean().iloc[-1]

        # Calculate annualized volatility
        returns = prices.pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # Annualize with sqrt(252) trading days

        # Determine trend
        is_bullish = sma_50 > sma_200
        is_volatile = volatility > self.volatility_threshold

        # Map to regime
        if is_bullish and not is_volatile:
            return MarketRegime.BULL_CALM
        elif is_bullish and is_volatile:
            return MarketRegime.BULL_VOLATILE
        elif not is_bullish and not is_volatile:
            return MarketRegime.BEAR_CALM
        else:  # not is_bullish and is_volatile
            return MarketRegime.BEAR_VOLATILE

    def get_regime_stats(self, prices: pd.Series) -> RegimeStats:
        """Get detailed regime statistics.

        Args:
            prices: Price series with DatetimeIndex (daily frequency)

        Returns:
            RegimeStats dataclass with all regime information

        Raises:
            ValueError: If insufficient data (need ≥200 points)

        Examples:
            >>> dates = pd.date_range('2020-01-01', periods=250, freq='D')
            >>> prices = pd.Series(np.linspace(100, 150, 250), index=dates)
            >>> detector = RegimeDetector()
            >>> stats = detector.get_regime_stats(prices)
            >>> print(f"Regime: {stats.regime.value}")
            Regime: bull_calm
            >>> print(f"Confidence: {stats.confidence:.2f}")
            Confidence: 0.83
        """
        # Validate data
        if len(prices) < 200:
            raise ValueError(f"Need ≥200 data points, got {len(prices)}")

        # Calculate SMAs
        sma_50 = prices.rolling(window=50).mean().iloc[-1]
        sma_200 = prices.rolling(window=200).mean().iloc[-1]

        # Calculate annualized volatility
        returns = prices.pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)

        # Determine regime components
        is_bullish = sma_50 > sma_200
        is_volatile = volatility > self.volatility_threshold

        trend_direction = "bullish" if is_bullish else "bearish"
        volatility_level = "volatile" if is_volatile else "calm"

        # Calculate regime
        if is_bullish and not is_volatile:
            regime = MarketRegime.BULL_CALM
        elif is_bullish and is_volatile:
            regime = MarketRegime.BULL_VOLATILE
        elif not is_bullish and not is_volatile:
            regime = MarketRegime.BEAR_CALM
        else:
            regime = MarketRegime.BEAR_VOLATILE

        # Calculate confidence based on data quality
        # Confidence increases with more data beyond minimum requirement
        data_points = len(prices)
        # Max confidence at 500+ points, linear growth from 200 to 500
        confidence = min(0.70 + (data_points - 200) / (300 * 3), 1.0)

        return RegimeStats(
            regime=regime,
            trend_direction=trend_direction,
            volatility_level=volatility_level,
            annualized_volatility=volatility,
            sma_50=sma_50,
            sma_200=sma_200,
            confidence=confidence,
        )
