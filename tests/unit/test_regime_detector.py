"""
Unit tests for Market Regime Detection.

TDD RED Phase - P1.1.1: All tests should FAIL initially.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestRegimeDetection:
    """Test suite for RegimeDetector basic functionality."""

    def test_detect_regime_bull_calm(self):
        """GIVEN price data with uptrend and low volatility
           WHEN detecting regime
           THEN return BULL_CALM
        """
        # Import will fail - expected in RED phase
        from src.intelligence.regime_detector import RegimeDetector, MarketRegime

        # Create synthetic data: uptrend + low vol
        dates = pd.date_range('2020-01-01', periods=250, freq='D')
        prices = pd.Series(np.linspace(100, 150, 250), index=dates)

        detector = RegimeDetector()
        regime = detector.detect_regime(prices)

        assert regime == MarketRegime.BULL_CALM

    def test_detect_regime_bull_volatile(self):
        """GIVEN price data with uptrend and high volatility
           WHEN detecting regime
           THEN return BULL_VOLATILE
        """
        from src.intelligence.regime_detector import RegimeDetector, MarketRegime

        # Create synthetic data: uptrend + high vol
        dates = pd.date_range('2020-01-01', periods=250, freq='D')
        trend = np.linspace(100, 150, 250)
        noise = np.random.RandomState(42).randn(250) * 10  # High volatility
        prices = pd.Series(trend + noise, index=dates)

        detector = RegimeDetector()
        regime = detector.detect_regime(prices)

        assert regime == MarketRegime.BULL_VOLATILE

    def test_detect_regime_bear_calm(self):
        """GIVEN price data with downtrend and low volatility
           WHEN detecting regime
           THEN return BEAR_CALM
        """
        from src.intelligence.regime_detector import RegimeDetector, MarketRegime

        # Create synthetic data: downtrend + low vol
        dates = pd.date_range('2020-01-01', periods=250, freq='D')
        prices = pd.Series(np.linspace(150, 100, 250), index=dates)

        detector = RegimeDetector()
        regime = detector.detect_regime(prices)

        assert regime == MarketRegime.BEAR_CALM

    def test_detect_regime_bear_volatile(self):
        """GIVEN price data with downtrend and high volatility
           WHEN detecting regime
           THEN return BEAR_VOLATILE
        """
        from src.intelligence.regime_detector import RegimeDetector, MarketRegime

        # Create synthetic data: downtrend + high vol
        dates = pd.date_range('2020-01-01', periods=250, freq='D')
        trend = np.linspace(150, 100, 250)
        noise = np.random.RandomState(42).randn(250) * 10  # High volatility
        prices = pd.Series(trend + noise, index=dates)

        detector = RegimeDetector()
        regime = detector.detect_regime(prices)

        assert regime == MarketRegime.BEAR_VOLATILE


class TestTrendCalculation:
    """Test suite for trend detection logic."""

    def test_trend_calculation_sma_crossover(self):
        """GIVEN price data
           WHEN calculating SMA(50) vs SMA(200)
           THEN correctly identify bullish/bearish trend
        """
        from src.intelligence.regime_detector import RegimeDetector

        # Create clear uptrend: SMA(50) > SMA(200)
        dates = pd.date_range('2020-01-01', periods=250, freq='D')
        prices = pd.Series(np.linspace(100, 200, 250), index=dates)

        detector = RegimeDetector()
        stats = detector.get_regime_stats(prices)

        assert stats.trend_direction == "bullish"
        assert stats.sma_50 > stats.sma_200


class TestVolatilityCalculation:
    """Test suite for volatility measurement."""

    def test_volatility_annualized_correctly(self):
        """GIVEN daily price returns
           WHEN calculating annualized volatility
           THEN apply correct annualization factor (√252)
        """
        from src.intelligence.regime_detector import RegimeDetector

        # Create data with known volatility
        dates = pd.date_range('2020-01-01', periods=250, freq='D')
        # Daily returns of 1% std → annualized ≈ 15.87% (1% * sqrt(252))
        returns = np.random.RandomState(42).randn(250) * 0.01
        prices = pd.Series(100 * (1 + returns).cumprod(), index=dates)

        detector = RegimeDetector()
        stats = detector.get_regime_stats(prices)

        # Annualized volatility should be around 15-17% given 1% daily
        assert 0.10 < stats.annualized_volatility < 0.25


class TestRegimeStats:
    """Test suite for RegimeStats dataclass."""

    def test_regime_stats_confidence_calculation(self):
        """GIVEN price data
           WHEN getting regime stats
           THEN confidence based on data quality
        """
        from src.intelligence.regime_detector import RegimeDetector

        # Good quality data: exactly 250 points
        dates = pd.date_range('2020-01-01', periods=250, freq='D')
        prices = pd.Series(np.linspace(100, 150, 250), index=dates)

        detector = RegimeDetector()
        stats = detector.get_regime_stats(prices)

        # Confidence should be between 0 and 1
        assert 0.0 <= stats.confidence <= 1.0
        # With 250 points, confidence should be reasonably high
        assert stats.confidence >= 0.7

    def test_regime_stats_returns_dataclass(self):
        """GIVEN price data
           WHEN getting regime stats
           THEN return RegimeStats dataclass with all fields
        """
        from src.intelligence.regime_detector import RegimeDetector, RegimeStats

        dates = pd.date_range('2020-01-01', periods=250, freq='D')
        prices = pd.Series(np.linspace(100, 150, 250), index=dates)

        detector = RegimeDetector()
        stats = detector.get_regime_stats(prices)

        # Verify it's the correct type
        assert isinstance(stats, RegimeStats)

        # Verify all required fields are present
        assert hasattr(stats, 'regime')
        assert hasattr(stats, 'trend_direction')
        assert hasattr(stats, 'volatility_level')
        assert hasattr(stats, 'annualized_volatility')
        assert hasattr(stats, 'sma_50')
        assert hasattr(stats, 'sma_200')
        assert hasattr(stats, 'confidence')


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_insufficient_data_raises_error(self):
        """GIVEN price data with <200 points
           WHEN detecting regime
           THEN raise ValueError
        """
        from src.intelligence.regime_detector import RegimeDetector

        # Only 150 points - insufficient for SMA(200)
        dates = pd.date_range('2020-01-01', periods=150, freq='D')
        prices = pd.Series(np.linspace(100, 150, 150), index=dates)

        detector = RegimeDetector()

        with pytest.raises(ValueError, match="Need ≥200 data points"):
            detector.detect_regime(prices)


class TestRegimeStability:
    """Test suite for regime stability and accuracy."""

    def test_regime_stability_no_rapid_switching(self):
        """GIVEN consecutive time periods
           WHEN detecting regime
           THEN no flipping between consecutive bars
        """
        from src.intelligence.regime_detector import RegimeDetector

        # Create stable uptrend data
        dates = pd.date_range('2020-01-01', periods=300, freq='D')
        prices = pd.Series(np.linspace(100, 150, 300), index=dates)

        detector = RegimeDetector()

        # Detect regime at different windows
        regime_1 = detector.detect_regime(prices[:250])
        regime_2 = detector.detect_regime(prices[10:260])  # Shift by 10 days

        # Should be the same regime (both bull_calm)
        assert regime_1 == regime_2


class TestHistoricalAccuracy:
    """Test suite for historical accuracy requirements."""

    def test_trend_accuracy_above_90_percent(self):
        """GIVEN historical data with known trends
           WHEN detecting trend direction
           THEN achieve ≥90% accuracy
        """
        from src.intelligence.regime_detector import RegimeDetector, MarketRegime

        detector = RegimeDetector()
        correct = 0
        total = 10

        # Generate 10 test cases with known trends
        for i in range(total):
            dates = pd.date_range('2020-01-01', periods=250, freq='D')

            if i < 5:
                # Bullish: SMA(50) should be > SMA(200)
                prices = pd.Series(np.linspace(100, 150, 250), index=dates)
                regime = detector.detect_regime(prices)
                if regime in [MarketRegime.BULL_CALM, MarketRegime.BULL_VOLATILE]:
                    correct += 1
            else:
                # Bearish: SMA(50) should be < SMA(200)
                prices = pd.Series(np.linspace(150, 100, 250), index=dates)
                regime = detector.detect_regime(prices)
                if regime in [MarketRegime.BEAR_CALM, MarketRegime.BEAR_VOLATILE]:
                    correct += 1

        accuracy = correct / total
        assert accuracy >= 0.90, f"Trend accuracy {accuracy:.1%} below 90%"

    def test_volatility_accuracy_above_85_percent(self):
        """GIVEN historical data with known volatility levels
           WHEN detecting volatility
           THEN achieve ≥85% accuracy
        """
        from src.intelligence.regime_detector import RegimeDetector, MarketRegime

        detector = RegimeDetector()
        correct = 0
        total = 10

        # Generate 10 test cases with known volatility
        for i in range(total):
            dates = pd.date_range('2020-01-01', periods=250, freq='D')
            trend = np.linspace(100, 150, 250)

            if i < 5:
                # Low volatility
                noise = np.random.RandomState(i).randn(250) * 1
                prices = pd.Series(trend + noise, index=dates)
                regime = detector.detect_regime(prices)
                if regime in [MarketRegime.BULL_CALM, MarketRegime.BEAR_CALM]:
                    correct += 1
            else:
                # High volatility
                noise = np.random.RandomState(i).randn(250) * 10
                prices = pd.Series(trend + noise, index=dates)
                regime = detector.detect_regime(prices)
                if regime in [MarketRegime.BULL_VOLATILE, MarketRegime.BEAR_VOLATILE]:
                    correct += 1

        accuracy = correct / total
        assert accuracy >= 0.85, f"Volatility accuracy {accuracy:.1%} below 85%"
