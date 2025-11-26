"""
Liquidity Filter for 40M TWD Capital Size (Spec B P1).

Implements tier-based liquidity classification and signal filtering
for large capital deployment scenarios.

Liquidity Tiers (based on 20-day ADV):
    - Forbidden (0): ADV < 400k TWD → Complete exclusion
    - Warning (1): 400k <= ADV < 1M TWD → Reduced position (1%)
    - Safe (2): 1M <= ADV < 5M TWD → Normal position (5%)
    - Premium (3): ADV >= 5M TWD → Full position (10%)

Usage:
    from src.validation.liquidity_filter import LiquidityFilter

    filter = LiquidityFilter(capital=40_000_000)
    adv = filter.calculate_adv(volume_amount, window=20)
    tier = filter.classify_liquidity(adv)
    filtered_signals = filter.apply_filter(signals, volume_amount)
"""

import logging
from enum import IntEnum
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class LiquidityTier(IntEnum):
    """Liquidity tier classification.

    Tiers are ordered by liquidity quality:
    - FORBIDDEN: Completely illiquid, cannot trade
    - WARNING: Low liquidity, reduced position only
    - SAFE: Normal liquidity, standard position
    - PREMIUM: High liquidity, full position allowed
    """
    FORBIDDEN = 0  # ADV < 400k TWD
    WARNING = 1    # 400k <= ADV < 1M TWD
    SAFE = 2       # 1M <= ADV < 5M TWD
    PREMIUM = 3    # ADV >= 5M TWD


class LiquidityFilter:
    """Liquidity Filter for 40M TWD Capital Size.

    Classifies securities by liquidity tier and applies appropriate
    position limits and signal adjustments.

    Attributes:
        capital (float): Total capital in TWD
        thresholds (dict): ADV thresholds for each tier boundary
        position_limits (dict): Max position % for each tier
        signal_multipliers (dict): Signal adjustment for each tier

    Example:
        >>> filter = LiquidityFilter(capital=40_000_000)
        >>> adv = filter.calculate_adv(volume_amount)
        >>> tier = filter.classify_liquidity(adv)
        >>> filtered = filter.apply_filter(signals, volume_amount)
    """

    # Default thresholds (in TWD)
    DEFAULT_THRESHOLDS = {
        'forbidden': 400_000,    # < 400k → Forbidden
        'warning': 1_000_000,    # 400k - 1M → Warning
        'safe': 5_000_000,       # 1M - 5M → Safe
        # >= 5M → Premium
    }

    # Position limits by tier (as percentage of capital)
    DEFAULT_POSITION_LIMITS = {
        LiquidityTier.FORBIDDEN: 0.00,  # 0%
        LiquidityTier.WARNING: 0.01,    # 1%
        LiquidityTier.SAFE: 0.05,       # 5%
        LiquidityTier.PREMIUM: 0.10,    # 10%
    }

    # Signal multipliers by tier
    DEFAULT_SIGNAL_MULTIPLIERS = {
        LiquidityTier.FORBIDDEN: 0.0,   # No signal
        LiquidityTier.WARNING: 0.5,     # 50% signal
        LiquidityTier.SAFE: 1.0,        # Full signal
        LiquidityTier.PREMIUM: 1.0,     # Full signal
    }

    def __init__(
        self,
        capital: float = 40_000_000,
        thresholds: Optional[Dict[str, float]] = None,
        position_limits: Optional[Dict[LiquidityTier, float]] = None,
        signal_multipliers: Optional[Dict[LiquidityTier, float]] = None
    ):
        """Initialize LiquidityFilter.

        Args:
            capital: Total capital in TWD (default: 40M)
            thresholds: Custom ADV thresholds (default: see DEFAULT_THRESHOLDS)
            position_limits: Custom position limits by tier
            signal_multipliers: Custom signal multipliers by tier
        """
        self.capital = capital
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
        self.position_limits = position_limits or self.DEFAULT_POSITION_LIMITS.copy()
        self.signal_multipliers = signal_multipliers or self.DEFAULT_SIGNAL_MULTIPLIERS.copy()

        logger.info(
            f"LiquidityFilter initialized: capital={capital:,.0f} TWD, "
            f"thresholds={self.thresholds}"
        )

    def calculate_adv(
        self,
        volume_amount: pd.DataFrame,
        window: int = 20
    ) -> pd.DataFrame:
        """Calculate Average Daily Volume (ADV).

        ADV is the rolling mean of daily volume amount over the specified window.

        Args:
            volume_amount: DataFrame of daily volume amounts (Dates x Symbols)
            window: Rolling window size (default: 20 trading days)

        Returns:
            DataFrame of ADV values (same shape as input)

        Note:
            Uses min_periods=1 to avoid excessive NaN at start of data.
        """
        adv = volume_amount.rolling(window=window, min_periods=1).mean()
        return adv

    def classify_liquidity(
        self,
        adv: pd.DataFrame
    ) -> pd.DataFrame:
        """Classify securities into liquidity tiers.

        Args:
            adv: DataFrame of ADV values (Dates x Symbols)

        Returns:
            DataFrame of LiquidityTier values (same shape as input)
                - 0: Forbidden (ADV < 400k)
                - 1: Warning (400k <= ADV < 1M)
                - 2: Safe (1M <= ADV < 5M)
                - 3: Premium (ADV >= 5M)
        """
        if adv.empty:
            return pd.DataFrame()

        # Initialize with Forbidden tier
        tier = pd.DataFrame(
            LiquidityTier.FORBIDDEN,
            index=adv.index,
            columns=adv.columns
        )

        # Classify by thresholds
        forbidden_threshold = self.thresholds['forbidden']
        warning_threshold = self.thresholds['warning']
        safe_threshold = self.thresholds['safe']

        # Warning tier: 400k <= ADV < 1M
        tier = tier.where(
            ~((adv >= forbidden_threshold) & (adv < warning_threshold)),
            LiquidityTier.WARNING
        )

        # Safe tier: 1M <= ADV < 5M
        tier = tier.where(
            ~((adv >= warning_threshold) & (adv < safe_threshold)),
            LiquidityTier.SAFE
        )

        # Premium tier: ADV >= 5M
        tier = tier.where(
            ~(adv >= safe_threshold),
            LiquidityTier.PREMIUM
        )

        # Handle NaN values (keep as NaN or set to Forbidden)
        tier = tier.where(~adv.isna(), np.nan)

        return tier

    def get_max_position_pct(self, tier: LiquidityTier) -> float:
        """Get maximum position size percentage for a tier.

        Args:
            tier: LiquidityTier value

        Returns:
            Maximum position as percentage of capital (e.g., 0.05 = 5%)
        """
        return self.position_limits.get(tier, 0.0)

    def get_signal_multiplier(self, tier: LiquidityTier) -> float:
        """Get signal multiplier for a tier.

        Args:
            tier: LiquidityTier value

        Returns:
            Signal multiplier (e.g., 0.5 = 50% of original signal)
        """
        return self.signal_multipliers.get(tier, 0.0)

    def apply_filter(
        self,
        signals: pd.DataFrame,
        volume_amount: pd.DataFrame,
        window: int = 20,
        strict_mode: bool = False
    ) -> pd.DataFrame:
        """Apply liquidity filter to trading signals.

        Adjusts signals based on liquidity tier:
        - Forbidden: Signal zeroed
        - Warning: Signal reduced to 50%
        - Safe/Premium: Signal unchanged

        Args:
            signals: DataFrame of trading signals (Dates x Symbols)
            volume_amount: DataFrame of volume amounts for ADV calculation
            window: ADV calculation window (default: 20)
            strict_mode: If True, Warning tier signals are also zeroed

        Returns:
            DataFrame of filtered signals (same shape as input)
        """
        # Calculate ADV and classify
        adv = self.calculate_adv(volume_amount, window=window)
        tier = self.classify_liquidity(adv)

        # Align indices
        signals = signals.copy()
        common_idx = signals.index.intersection(tier.index)
        common_cols = signals.columns.intersection(tier.columns)

        if len(common_cols) == 0:
            logger.warning("No common columns between signals and volume_amount")
            return signals

        # Apply multipliers
        filtered = signals.copy()

        for col in common_cols:
            for idx in common_idx:
                tier_value = tier.loc[idx, col]

                if pd.isna(tier_value):
                    multiplier = 0.0  # NaN tier treated as Forbidden
                else:
                    tier_enum = LiquidityTier(int(tier_value))

                    if strict_mode and tier_enum == LiquidityTier.WARNING:
                        multiplier = 0.0
                    else:
                        multiplier = self.get_signal_multiplier(tier_enum)

                filtered.loc[idx, col] = signals.loc[idx, col] * multiplier

        logger.debug(
            f"Applied liquidity filter: {len(common_cols)} symbols, "
            f"strict_mode={strict_mode}"
        )

        return filtered

    def get_position_limits_df(
        self,
        adv: pd.DataFrame
    ) -> pd.DataFrame:
        """Get position limit DataFrame based on ADV.

        Args:
            adv: DataFrame of ADV values

        Returns:
            DataFrame of position limits (same shape as input)
            Values represent max position as fraction of capital
        """
        tier = self.classify_liquidity(adv)

        # Map tiers to position limits
        limits = tier.replace({
            LiquidityTier.FORBIDDEN: self.position_limits[LiquidityTier.FORBIDDEN],
            LiquidityTier.WARNING: self.position_limits[LiquidityTier.WARNING],
            LiquidityTier.SAFE: self.position_limits[LiquidityTier.SAFE],
            LiquidityTier.PREMIUM: self.position_limits[LiquidityTier.PREMIUM],
        })

        return limits.astype(float)

    def get_max_trade_size(
        self,
        adv: pd.DataFrame,
        participation_rate: float = 0.10
    ) -> pd.DataFrame:
        """Get maximum trade size based on ADV and participation rate.

        To minimize market impact, trade size should be limited to a
        fraction of ADV.

        Args:
            adv: DataFrame of ADV values
            participation_rate: Max fraction of ADV to trade (default: 10%)

        Returns:
            DataFrame of max trade sizes in TWD
        """
        return adv * participation_rate
