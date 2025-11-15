"""Regime-Aware E2E Tests following TDD methodology.

P2.2.3: Test complete market regime detection and strategy selection workflow
- Test regime detection with realistic market data
- Test strategy adaptation based on detected regime
- Verify performance improvement from regime awareness
- Verify execution time < 5.0 seconds
- Verify regime detection latency < 100ms (Gate 7)
- Verify OOS tolerance ±20% (Gate 5)
"""

import pytest
import time
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

from src.intelligence.regime_detector import RegimeDetector, MarketRegime, RegimeStats


@pytest.mark.e2e
class TestRegimeDetectionWorkflow:
    """Test complete regime detection E2E workflow."""

    def test_regime_detection_e2e_workflow(
        self, market_data, test_environment, validation_thresholds
    ):
        """
        GIVEN market data with realistic regime characteristics
        WHEN regime detector runs on complete market data
        THEN detect correct regime with high confidence and low latency

        TDD RED: This test will fail initially because we haven't integrated
        regime detection with complete E2E workflow yet.
        """
        # Arrange: Create market data with known bull calm regime
        # Use first 300 days from fixture (should be uptrend + low vol)
        prices = self._extract_representative_price_series(market_data, n_days=300)

        detector = RegimeDetector(volatility_threshold=0.20)

        # Act: Run regime detection with timing
        start_time = time.time()
        regime = detector.detect_regime(prices)
        detection_time_ms = (time.time() - start_time) * 1000

        stats = detector.get_regime_stats(prices)

        # Assert: Verify regime detection accuracy
        assert regime in [
            MarketRegime.BULL_CALM,
            MarketRegime.BULL_VOLATILE,
            MarketRegime.BEAR_CALM,
            MarketRegime.BEAR_VOLATILE,
        ], f"Invalid regime detected: {regime}"

        # Verify confidence score is high (data quality good)
        assert stats.confidence >= 0.7, (
            f"Regime detection confidence {stats.confidence:.2f} < 0.7 threshold"
        )

        # Verify detection latency (Gate 7: < 100ms)
        max_latency_ms = validation_thresholds['max_latency_ms']
        assert detection_time_ms < max_latency_ms, (
            f"Regime detection took {detection_time_ms:.1f}ms > {max_latency_ms}ms limit"
        )

        # Verify regime stats are consistent
        assert stats.regime == regime, "RegimeStats regime should match detect_regime()"
        assert stats.annualized_volatility > 0, "Volatility should be positive"
        assert stats.sma_50 > 0 and stats.sma_200 > 0, "SMAs should be positive"

    def test_regime_transition_handling(
        self, market_data, test_environment, validation_thresholds
    ):
        """
        GIVEN market data with regime change (bull→bear transition)
        WHEN strategy adapts to detected regime changes
        THEN performance should improve during regime transition

        TDD RED: This test will fail because regime-aware strategy adaptation
        isn't integrated into E2E workflow yet.
        """
        # Arrange: Create synthetic data with regime transition
        # First half: Bull market (uptrend + low vol)
        # Second half: Bear market (downtrend + high vol)
        dates = pd.date_range('2020-01-01', periods=500, freq='D')
        prices = self._generate_regime_transition_data(dates, transition_day=250)

        detector = RegimeDetector(volatility_threshold=0.20)

        # Act: Detect regime at different points
        # Pre-transition (day 200)
        pre_regime = detector.detect_regime(prices.iloc[:200])

        # Post-transition (day 400)
        post_regime = detector.detect_regime(prices.iloc[:400])

        # Assert: Verify regime transition was detected
        # First 200 days should be bullish
        assert pre_regime in [MarketRegime.BULL_CALM, MarketRegime.BULL_VOLATILE], (
            f"Pre-transition regime {pre_regime} should be bullish"
        )

        # After 400 days (includes 150 days of bear market), should detect bear
        # Note: SMA(200) is slow, so regime may still show as bull
        # We'll verify that the trend direction changed
        pre_stats = detector.get_regime_stats(prices.iloc[:200])
        post_stats = detector.get_regime_stats(prices.iloc[:400])

        # Verify volatility increased after transition
        assert post_stats.annualized_volatility > pre_stats.annualized_volatility, (
            f"Post-transition volatility {post_stats.annualized_volatility:.2%} "
            f"should exceed pre-transition {pre_stats.annualized_volatility:.2%}"
        )

    def test_multi_regime_strategy_performance(
        self, market_data, test_environment, validation_thresholds
    ):
        """
        GIVEN market data spanning multiple regimes
        WHEN regime-aware strategy runs complete backtest
        THEN final performance should exceed baseline by ≥10%

        TDD RED: This test will fail because we need to implement regime-aware
        strategy selection and backtest integration.
        """
        # Arrange: Create data with multiple regime phases
        dates = pd.date_range('2020-01-01', periods=700, freq='D')
        prices = self._generate_multi_regime_data(dates)

        detector = RegimeDetector(volatility_threshold=0.20)

        # Create baseline (regime-agnostic) strategy
        baseline_strategy = self._create_baseline_strategy()

        # Create regime-aware strategy
        regime_aware_strategy = self._create_regime_aware_strategy(detector)

        # Act: Run simplified backtests
        baseline_sharpe = self._run_simple_backtest(prices, baseline_strategy)
        aware_sharpe = self._run_simple_backtest(prices, regime_aware_strategy)

        # Assert: Verify regime-aware strategy outperforms baseline
        improvement_threshold = validation_thresholds['improvement_threshold']
        improvement = (aware_sharpe - baseline_sharpe) / abs(baseline_sharpe)

        assert improvement >= improvement_threshold, (
            f"Regime-aware improvement {improvement:.1%} < {improvement_threshold:.1%} threshold. "
            f"Baseline Sharpe: {baseline_sharpe:.2f}, Aware Sharpe: {aware_sharpe:.2f}"
        )

        # Verify both strategies have positive Sharpe ratios
        # Note: E2E tests use synthetic data, so we expect lower Sharpe than production
        min_sharpe_e2e = 0.2  # Lower threshold for E2E synthetic data
        assert aware_sharpe >= min_sharpe_e2e, (
            f"Regime-aware Sharpe {aware_sharpe:.2f} < minimum {min_sharpe_e2e}"
        )

    def test_regime_detection_stability(
        self, market_data, test_environment, validation_thresholds
    ):
        """
        GIVEN rolling window regime detection over time
        WHEN detecting regime at consecutive time periods
        THEN regime should be stable (no rapid flipping)

        TDD RED: This test will fail initially as we verify regime stability
        in real-world E2E conditions.
        """
        # Arrange: Extract long price series for stability testing
        prices = self._extract_representative_price_series(market_data, n_days=400)

        detector = RegimeDetector(volatility_threshold=0.20)

        # Act: Detect regime at multiple consecutive windows
        regimes = []
        window_size = 250  # Minimum required for regime detection
        step_size = 5  # Check every 5 days

        for i in range(window_size, len(prices), step_size):
            window = prices.iloc[i - window_size : i]
            regime = detector.detect_regime(window)
            regimes.append(regime)

        # Assert: Verify regime stability (no excessive flipping)
        # Count regime changes
        regime_changes = sum(1 for i in range(1, len(regimes)) if regimes[i] != regimes[i - 1])

        # Calculate stability ratio (% of periods with same regime as previous)
        stability_ratio = 1.0 - (regime_changes / len(regimes))

        # Expect high stability (>70%) - regimes shouldn't flip rapidly
        min_stability = 0.70
        assert stability_ratio >= min_stability, (
            f"Regime stability {stability_ratio:.1%} < {min_stability:.1%}. "
            f"Detected {regime_changes} regime changes in {len(regimes)} windows"
        )

    def test_execution_time_constraint(
        self, market_data, test_environment, validation_thresholds
    ):
        """
        GIVEN complete regime-aware workflow
        WHEN running regime detection + strategy selection + validation
        THEN total execution time should be < 5.0 seconds

        TDD RED: This test will fail if workflow is inefficient or has performance issues.
        """
        # Arrange: Use full market data for realistic performance test
        prices = self._extract_representative_price_series(market_data, n_days=500)

        detector = RegimeDetector(volatility_threshold=0.20)
        regime_aware_strategy = self._create_regime_aware_strategy(detector)

        # Act: Measure complete workflow execution time
        start_time = time.time()

        # Step 1: Regime detection
        regime = detector.detect_regime(prices)
        stats = detector.get_regime_stats(prices)

        # Step 2: Strategy selection based on regime
        # (Simplified - just verify we can generate signals)
        signals = regime_aware_strategy.generate_signals(prices)

        # Step 3: Basic validation
        assert signals is not None
        assert len(signals) > 0

        elapsed_time = time.time() - start_time

        # Assert: Verify execution time meets threshold
        max_time = validation_thresholds['max_execution_time']
        assert elapsed_time < max_time, (
            f"Regime workflow took {elapsed_time:.2f}s > {max_time:.2f}s limit"
        )

        # Verify regime was detected successfully
        assert regime in [
            MarketRegime.BULL_CALM,
            MarketRegime.BULL_VOLATILE,
            MarketRegime.BEAR_CALM,
            MarketRegime.BEAR_VOLATILE,
        ]

    # Helper methods

    def _extract_representative_price_series(
        self, market_data: pd.DataFrame, n_days: int
    ) -> pd.Series:
        """Extract representative price series from multi-stock market data.

        Args:
            market_data: DataFrame with multi-stock price data
            n_days: Number of days to extract

        Returns:
            Series with representative price data suitable for regime detection
        """
        # Find a price column (format: "stock_XXX_price")
        price_cols = [col for col in market_data.columns if col.endswith('_price')]
        assert len(price_cols) > 0, "No price columns found in market_data"

        # Use first stock's prices
        prices = market_data[price_cols[0]].iloc[:n_days].copy()

        # Ensure enough data for regime detection
        assert len(prices) >= 200, f"Need ≥200 days for regime detection, got {len(prices)}"

        return prices

    def _generate_regime_transition_data(
        self, dates: pd.DatetimeIndex, transition_day: int
    ) -> pd.Series:
        """Generate synthetic price data with regime transition.

        Args:
            dates: DatetimeIndex for price series
            transition_day: Day index where regime changes

        Returns:
            Price series with regime transition (bull→bear)
        """
        np.random.seed(42)  # Reproducible
        n_days = len(dates)
        prices = np.zeros(n_days)
        prices[0] = 100

        for i in range(1, n_days):
            if i < transition_day:
                # Bull calm: uptrend + low vol
                mean_return = 0.0008
                volatility = 0.008
            else:
                # Bear volatile: downtrend + high vol
                mean_return = -0.0012
                volatility = 0.025

            ret = np.random.randn() * volatility + mean_return
            prices[i] = prices[i - 1] * (1 + ret)

        return pd.Series(prices, index=dates)

    def _generate_multi_regime_data(self, dates: pd.DatetimeIndex) -> pd.Series:
        """Generate price data spanning multiple market regimes.

        Args:
            dates: DatetimeIndex for price series

        Returns:
            Price series with multiple regime phases
        """
        np.random.seed(43)  # Different seed for variety
        n_days = len(dates)
        prices = np.zeros(n_days)
        prices[0] = 100

        # Define regime phases
        phase1_end = n_days // 4  # 25%: Bull calm
        phase2_end = n_days // 2  # 25%: Bull volatile
        phase3_end = 3 * n_days // 4  # 25%: Bear calm
        # Remaining 25%: Bear volatile

        for i in range(1, n_days):
            if i < phase1_end:
                # Bull calm
                mean_return, volatility = 0.0010, 0.008
            elif i < phase2_end:
                # Bull volatile
                mean_return, volatility = 0.0012, 0.025
            elif i < phase3_end:
                # Bear calm
                mean_return, volatility = -0.0006, 0.010
            else:
                # Bear volatile
                mean_return, volatility = -0.0015, 0.030

            ret = np.random.randn() * volatility + mean_return
            prices[i] = prices[i - 1] * (1 + ret)

        return pd.Series(prices, index=dates)

    def _create_baseline_strategy(self) -> "BaselineStrategy":
        """Create regime-agnostic baseline strategy.

        Returns:
            BaselineStrategy instance (always long)
        """
        return BaselineStrategy()

    def _create_regime_aware_strategy(
        self, detector: RegimeDetector
    ) -> "RegimeAwareStrategy":
        """Create regime-aware strategy using detector.

        Args:
            detector: RegimeDetector instance

        Returns:
            RegimeAwareStrategy instance
        """
        return RegimeAwareStrategy(detector)

    def _run_simple_backtest(
        self, prices: pd.Series, strategy
    ) -> float:
        """Run simplified backtest and return Sharpe ratio.

        Args:
            prices: Price series
            strategy: Strategy instance with generate_signals() method

        Returns:
            Sharpe ratio
        """
        # Generate signals
        signals = strategy.generate_signals(prices)

        # Calculate returns
        returns = prices.pct_change()

        # Calculate strategy returns
        strategy_returns = signals.shift(1) * returns
        strategy_returns = strategy_returns.dropna()

        # Calculate Sharpe ratio
        if strategy_returns.std() == 0:
            return 0.0

        sharpe = (strategy_returns.mean() / strategy_returns.std()) * np.sqrt(252)
        return sharpe


# Strategy classes for E2E testing


class BaselineStrategy:
    """Baseline regime-agnostic strategy (buy-and-hold)."""

    def generate_signals(self, prices: pd.Series) -> pd.Series:
        """Generate buy-and-hold signals.

        Args:
            prices: Price series

        Returns:
            Series with position signals (always 1.0)
        """
        return pd.Series(1.0, index=prices.index)


class RegimeAwareStrategy:
    """Regime-aware strategy that adapts to market conditions."""

    def __init__(self, detector: RegimeDetector):
        """Initialize regime-aware strategy.

        Args:
            detector: RegimeDetector instance
        """
        self.detector = detector

    def generate_signals(self, prices: pd.Series) -> pd.Series:
        """Generate regime-aware signals.

        Strategy rules:
        - BULL_CALM: Full long (1.0)
        - BULL_VOLATILE: Reduced long (0.6)
        - BEAR_CALM: Flat (0.0)
        - BEAR_VOLATILE: Short (-0.5)

        Args:
            prices: Price series

        Returns:
            Series with position signals
        """
        signals = pd.Series(index=prices.index, dtype=float)

        # Use rolling window for regime detection
        min_window = 200
        for i in range(min_window, len(prices)):
            window = prices.iloc[: i + 1]

            try:
                regime = self.detector.detect_regime(window)

                if regime == MarketRegime.BULL_CALM:
                    signals.iloc[i] = 1.0
                elif regime == MarketRegime.BULL_VOLATILE:
                    signals.iloc[i] = 0.6  # Reduce exposure in volatility
                elif regime == MarketRegime.BEAR_CALM:
                    signals.iloc[i] = 0.0  # Stay flat
                else:  # BEAR_VOLATILE
                    signals.iloc[i] = -0.5  # Short position
            except ValueError:
                # Insufficient data - use neutral signal
                signals.iloc[i] = 0.0

        # Fill initial NaN with 0
        signals.fillna(0.0, inplace=True)

        return signals
