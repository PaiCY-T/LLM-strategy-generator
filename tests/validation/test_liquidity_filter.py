"""
TDD Tests for Liquidity Filter (Spec B P1).

Tests written FIRST following Red-Green-Refactor cycle.
Liquidity Filter for 40M TWD capital size with tier-based classification.

Test Coverage:
- ADV calculation (20-day moving average)
- Tier classification (Forbidden, Warning, Safe, Premium)
- Signal filtering based on tiers
- Position size limits
- Edge cases
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any
from enum import IntEnum


class TestLiquidityFilter:
    """TDD tests for Liquidity Filter - Write FIRST (RED phase)."""

    @pytest.fixture
    def liquidity_filter(self):
        """Create LiquidityFilter with 40M TWD capital."""
        from src.validation.liquidity_filter import LiquidityFilter
        return LiquidityFilter(capital=40_000_000)

    @pytest.fixture
    def sample_volume_amount(self) -> pd.DataFrame:
        """Sample volume amount data (成交金額) in TWD."""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        return pd.DataFrame({
            # High liquidity stock (>5M ADV)
            '2330': np.random.uniform(5_000_000, 10_000_000, 50),
            # Medium liquidity stock (1M-5M ADV)
            '2317': np.random.uniform(1_000_000, 3_000_000, 50),
            # Low liquidity stock (400k-1M ADV)
            '6116': np.random.uniform(400_000, 800_000, 50),
            # Very low liquidity stock (<400k ADV)
            '1234': np.random.uniform(100_000, 300_000, 50),
        }, index=dates)

    def test_calculate_adv(self, liquidity_filter, sample_volume_amount):
        """RED: ADV should be 20-day moving average of volume amount"""
        adv = liquidity_filter.calculate_adv(sample_volume_amount, window=20)

        # ADV should have same shape as input
        assert adv.shape == sample_volume_amount.shape

        # ADV should be non-negative
        assert (adv >= 0).all().all()

        # Manually verify one calculation
        expected_adv_2330 = sample_volume_amount['2330'].rolling(20, min_periods=1).mean()
        pd.testing.assert_series_equal(adv['2330'], expected_adv_2330, check_names=False)

    def test_tier_forbidden_below_400k(self, liquidity_filter):
        """RED: ADV < 400k → Tier 0 (Forbidden)"""
        adv = pd.DataFrame({
            '1234': [300_000],  # < 400k
        }, index=[pd.Timestamp('2023-01-01')])

        tier = liquidity_filter.classify_liquidity(adv)
        assert tier.iloc[0, 0] == 0, "ADV < 400k should be Tier 0 (Forbidden)"

    def test_tier_warning_400k_to_1m(self, liquidity_filter):
        """RED: 400k <= ADV < 1M → Tier 1 (Warning)"""
        adv = pd.DataFrame({
            '6116': [600_000],  # 400k-1M
        }, index=[pd.Timestamp('2023-01-01')])

        tier = liquidity_filter.classify_liquidity(adv)
        assert tier.iloc[0, 0] == 1, "ADV 400k-1M should be Tier 1 (Warning)"

    def test_tier_safe_1m_to_5m(self, liquidity_filter):
        """RED: 1M <= ADV < 5M → Tier 2 (Safe)"""
        adv = pd.DataFrame({
            '2317': [2_000_000],  # 1M-5M
        }, index=[pd.Timestamp('2023-01-01')])

        tier = liquidity_filter.classify_liquidity(adv)
        assert tier.iloc[0, 0] == 2, "ADV 1M-5M should be Tier 2 (Safe)"

    def test_tier_premium_above_5m(self, liquidity_filter):
        """RED: ADV >= 5M → Tier 3 (Premium)"""
        adv = pd.DataFrame({
            '2330': [10_000_000],  # >= 5M
        }, index=[pd.Timestamp('2023-01-01')])

        tier = liquidity_filter.classify_liquidity(adv)
        assert tier.iloc[0, 0] == 3, "ADV >= 5M should be Tier 3 (Premium)"

    def test_tier_boundaries_exact(self, liquidity_filter):
        """RED: Test exact boundary values"""
        adv = pd.DataFrame({
            'at_400k': [400_000],      # Exactly at boundary → Tier 1
            'at_1m': [1_000_000],      # Exactly at boundary → Tier 2
            'at_5m': [5_000_000],      # Exactly at boundary → Tier 3
        }, index=[pd.Timestamp('2023-01-01')])

        tier = liquidity_filter.classify_liquidity(adv)
        assert tier.iloc[0, 0] == 1, "ADV = 400k should be Tier 1"
        assert tier.iloc[0, 1] == 2, "ADV = 1M should be Tier 2"
        assert tier.iloc[0, 2] == 3, "ADV = 5M should be Tier 3"

    def test_max_position_size_by_tier(self, liquidity_filter):
        """RED: Max position size varies by tier"""
        from src.validation.liquidity_filter import LiquidityTier

        # Tier 0: 0%
        assert liquidity_filter.get_max_position_pct(LiquidityTier.FORBIDDEN) == 0.0

        # Tier 1: 1%
        assert liquidity_filter.get_max_position_pct(LiquidityTier.WARNING) == 0.01

        # Tier 2: 5%
        assert liquidity_filter.get_max_position_pct(LiquidityTier.SAFE) == 0.05

        # Tier 3: 10%
        assert liquidity_filter.get_max_position_pct(LiquidityTier.PREMIUM) == 0.10

    def test_signal_multiplier_by_tier(self, liquidity_filter):
        """RED: Signal multiplier varies by tier"""
        from src.validation.liquidity_filter import LiquidityTier

        # Tier 0: 0.0 (forbidden)
        assert liquidity_filter.get_signal_multiplier(LiquidityTier.FORBIDDEN) == 0.0

        # Tier 1: 0.5 (reduced)
        assert liquidity_filter.get_signal_multiplier(LiquidityTier.WARNING) == 0.5

        # Tier 2: 1.0 (full)
        assert liquidity_filter.get_signal_multiplier(LiquidityTier.SAFE) == 1.0

        # Tier 3: 1.0 (full)
        assert liquidity_filter.get_signal_multiplier(LiquidityTier.PREMIUM) == 1.0


class TestLiquidityFilterApplication:
    """Tests for applying liquidity filter to signals."""

    @pytest.fixture
    def liquidity_filter(self):
        from src.validation.liquidity_filter import LiquidityFilter
        return LiquidityFilter(capital=40_000_000)

    def test_apply_filter_zeros_forbidden_signals(self, liquidity_filter):
        """RED: Apply filter should zero out forbidden tier signals"""
        dates = pd.date_range('2023-01-01', periods=30, freq='D')

        # Create volume amount with one forbidden stock
        volume_amount = pd.DataFrame({
            '2330': [5_000_000] * 30,    # Premium tier
            '1234': [200_000] * 30,      # Forbidden tier
        }, index=dates)

        # Create signals
        signals = pd.DataFrame({
            '2330': [1.0] * 30,
            '1234': [1.0] * 30,  # This should be filtered out
        }, index=dates)

        filtered = liquidity_filter.apply_filter(signals, volume_amount)

        # 2330 signals should remain
        assert (filtered['2330'].iloc[-1] > 0), "Premium tier signals should remain"

        # 1234 signals should be zeroed
        assert (filtered['1234'].iloc[-1] == 0), "Forbidden tier signals should be zero"

    def test_apply_filter_reduces_warning_signals(self, liquidity_filter):
        """RED: Apply filter should reduce warning tier signals by 50%"""
        dates = pd.date_range('2023-01-01', periods=30, freq='D')

        volume_amount = pd.DataFrame({
            '6116': [600_000] * 30,  # Warning tier (400k-1M)
        }, index=dates)

        signals = pd.DataFrame({
            '6116': [1.0] * 30,
        }, index=dates)

        filtered = liquidity_filter.apply_filter(signals, volume_amount)

        # Warning tier signals should be reduced to 0.5
        assert abs(filtered['6116'].iloc[-1] - 0.5) < 0.01, \
            "Warning tier signals should be 50%"


class TestLiquidityFilterCustomConfig:
    """Tests for custom configuration."""

    def test_custom_capital(self):
        """RED: Custom capital should work"""
        from src.validation.liquidity_filter import LiquidityFilter

        filter_20m = LiquidityFilter(capital=20_000_000)
        filter_80m = LiquidityFilter(capital=80_000_000)

        assert filter_20m.capital == 20_000_000
        assert filter_80m.capital == 80_000_000

    def test_custom_thresholds(self):
        """RED: Custom thresholds should work"""
        from src.validation.liquidity_filter import LiquidityFilter

        custom_thresholds = {
            'forbidden': 500_000,  # Higher than default 400k
            'warning': 2_000_000,   # Higher than default 1M
            'safe': 10_000_000,     # Higher than default 5M
        }

        filter_custom = LiquidityFilter(
            capital=40_000_000,
            thresholds=custom_thresholds
        )

        # Test with custom thresholds
        adv = pd.DataFrame({
            'test': [1_500_000],  # Would be Safe with default, Warning with custom
        }, index=[pd.Timestamp('2023-01-01')])

        tier = filter_custom.classify_liquidity(adv)
        assert tier.iloc[0, 0] == 1, "Custom thresholds should be applied"


class TestLiquidityFilterEdgeCases:
    """Edge case tests."""

    @pytest.fixture
    def liquidity_filter(self):
        from src.validation.liquidity_filter import LiquidityFilter
        return LiquidityFilter(capital=40_000_000)

    def test_empty_dataframe(self, liquidity_filter):
        """RED: Handle empty DataFrame"""
        adv = pd.DataFrame()
        tier = liquidity_filter.classify_liquidity(adv)
        assert tier.empty

    def test_nan_values(self, liquidity_filter):
        """RED: Handle NaN values gracefully"""
        adv = pd.DataFrame({
            '2330': [5_000_000, np.nan, 5_000_000],
        }, index=pd.date_range('2023-01-01', periods=3, freq='D'))

        tier = liquidity_filter.classify_liquidity(adv)

        # NaN should remain NaN in tier
        assert tier.iloc[0, 0] == 3  # Premium
        assert pd.isna(tier.iloc[1, 0]) or tier.iloc[1, 0] == 0  # NaN or Forbidden
        assert tier.iloc[2, 0] == 3  # Premium

    def test_single_column(self, liquidity_filter):
        """RED: Handle single column DataFrame"""
        adv = pd.DataFrame({
            '2330': [5_000_000] * 10,
        }, index=pd.date_range('2023-01-01', periods=10, freq='D'))

        tier = liquidity_filter.classify_liquidity(adv)
        assert tier.shape == adv.shape

    def test_zero_volume(self, liquidity_filter):
        """RED: Handle zero volume"""
        adv = pd.DataFrame({
            'zero_vol': [0.0] * 10,
        }, index=pd.date_range('2023-01-01', periods=10, freq='D'))

        tier = liquidity_filter.classify_liquidity(adv)

        # Zero volume should be Forbidden
        assert (tier['zero_vol'] == 0).all(), "Zero volume should be Forbidden tier"
