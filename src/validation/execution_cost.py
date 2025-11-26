"""
Execution Cost Model with Square Root Law Slippage (Spec B P1).

Implements market impact model for large order execution,
following the Square Root Law observed in empirical studies.

Slippage Formula:
    Slippage (bps) = Base_Cost + α × sqrt(Trade_Size/ADV) × Volatility

Penalty Tiers:
    - < 20 bps: No penalty
    - 20-50 bps: Linear penalty (slippage - 20) / 60
    - > 50 bps: Quadratic penalty 0.5 + (slippage - 50)² / 10000

Usage:
    from src.validation.execution_cost import ExecutionCostModel

    model = ExecutionCostModel(base_cost_bps=10, impact_coeff=50)
    slippage = model.calculate_slippage(trade_size, adv, returns)
    penalty = model.calculate_liquidity_penalty(strategy_return, avg_slippage)
"""

import logging
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ExecutionCostModel:
    """Execution Cost Model with Square Root Law Slippage.

    Based on empirical market microstructure research:
    - Almgren & Chriss (2000): Optimal execution framework
    - Square Root Law: Impact ∝ sqrt(volume/ADV)

    Attributes:
        base_cost_bps (float): Fixed execution cost in basis points
        impact_coeff (float): Market impact coefficient (α)
        volatility_window (int): Window for volatility calculation

    Example:
        >>> model = ExecutionCostModel(base_cost_bps=10)
        >>> slippage = model.calculate_slippage(trade_size, adv, returns)
        >>> net_return = model.calculate_net_return(gross_return, avg_slippage)
    """

    def __init__(
        self,
        base_cost_bps: float = 10.0,
        impact_coeff: float = 50.0,
        volatility_window: int = 20
    ):
        """Initialize ExecutionCostModel.

        Args:
            base_cost_bps: Fixed execution cost in basis points (default: 10)
            impact_coeff: Market impact coefficient α (default: 50)
            volatility_window: Window for volatility calculation (default: 20)
        """
        self.base_cost_bps = base_cost_bps
        self.impact_coeff = impact_coeff
        self.volatility_window = volatility_window

        logger.info(
            f"ExecutionCostModel initialized: base_cost={base_cost_bps}bps, "
            f"impact_coeff={impact_coeff}, vol_window={volatility_window}"
        )

    def calculate_slippage(
        self,
        trade_size: pd.DataFrame,
        adv: pd.DataFrame,
        returns: pd.DataFrame
    ) -> pd.DataFrame:
        """Calculate execution slippage using Square Root Law.

        Formula:
            Slippage (bps) = Base_Cost + α × sqrt(Trade_Size/ADV) × Volatility

        Where:
            - Base_Cost: Fixed commission/spread cost
            - α: Impact coefficient (typically 30-100)
            - Trade_Size/ADV: Participation rate (fraction of daily volume)
            - Volatility: Rolling standard deviation of returns

        Args:
            trade_size: DataFrame of trade sizes in TWD (Dates x Symbols)
            adv: DataFrame of average daily volume (Dates x Symbols)
            returns: DataFrame of daily returns (Dates x Symbols)

        Returns:
            DataFrame of slippage in basis points (Dates x Symbols)

        See Also:
            calculate_single_slippage: Scalar version for single trade calculation
        """
        # Handle empty DataFrames
        if trade_size.empty or adv.empty or returns.empty:
            return pd.DataFrame()

        # Calculate participation rate: Trade_Size / ADV
        participation = trade_size / adv

        # Handle division by zero (ADV = 0)
        participation = participation.replace([np.inf, -np.inf], np.nan)
        participation = participation.fillna(0)

        # Calculate square root of participation (core of Square Root Law)
        sqrt_participation = np.sqrt(participation)

        # Calculate volatility (rolling standard deviation of returns)
        volatility = returns.rolling(
            window=self.volatility_window,
            min_periods=1
        ).std()

        # Handle NaN volatility
        volatility = volatility.fillna(0)

        # Convert volatility to annualized basis points
        # Daily vol × sqrt(252) × 10000 to get annualized bps
        vol_bps = volatility * np.sqrt(252) * 10000

        # Calculate market impact component
        # Impact = α × sqrt(Trade_Size/ADV) × Volatility
        impact_bps = self.impact_coeff * sqrt_participation * volatility * 100

        # Total slippage = Base + Impact
        slippage = self.base_cost_bps + impact_bps

        # Ensure non-negative
        slippage = slippage.clip(lower=0)

        return slippage

    def calculate_single_slippage(
        self,
        trade_size: float,
        adv: float,
        volatility: float
    ) -> float:
        """Calculate slippage for a single trade (scalar version).

        Convenience method for single trade slippage calculation without
        needing to create DataFrames.

        Formula:
            Slippage (bps) = Base_Cost + α × sqrt(Trade_Size/ADV) × Volatility

        Args:
            trade_size: Trade size in TWD
            adv: Average daily volume in TWD
            volatility: Daily return volatility (annualized)

        Returns:
            Slippage in basis points

        Example:
            >>> model = ExecutionCostModel()
            >>> slippage = model.calculate_single_slippage(
            ...     trade_size=1_000_000,
            ...     adv=50_000_000,
            ...     volatility=0.02
            ... )
            >>> print(f"Slippage: {slippage:.2f} bps")
        """
        # Validate inputs
        if adv <= 0:
            logger.warning(f"Invalid ADV: {adv}, returning base cost only")
            return self.base_cost_bps

        if trade_size <= 0:
            return 0.0

        # Calculate participation rate
        participation = trade_size / adv

        # Square root of participation
        sqrt_participation = np.sqrt(participation)

        # Market impact component
        # Use absolute volatility value, convert to bps
        impact_bps = self.impact_coeff * sqrt_participation * abs(volatility) * 100

        # Total slippage
        slippage = self.base_cost_bps + impact_bps

        return max(0.0, slippage)

    def calculate_liquidity_penalty(
        self,
        strategy_return: float,
        avg_slippage_bps: float
    ) -> float:
        """Calculate liquidity penalty for strategy evaluation.

        Penalty Tiers:
            - < 20 bps: No penalty (0.0)
            - 20-50 bps: Linear penalty = (slippage - 20) / 60
            - > 50 bps: Quadratic penalty = 0.5 + (slippage - 50)² / 10000

        Args:
            strategy_return: Gross strategy return (e.g., 0.20 for 20%)
            avg_slippage_bps: Average slippage in basis points

        Returns:
            Liquidity penalty as a fraction (0.0 to ~1.0)
        """
        if avg_slippage_bps < 20:
            # No penalty for low slippage
            return 0.0
        elif avg_slippage_bps <= 50:
            # Linear penalty: 0 at 20 bps, 0.5 at 50 bps
            return (avg_slippage_bps - 20) / 60
        else:
            # Quadratic penalty above 50 bps
            # 0.5 (from linear region) + quadratic component
            linear_penalty = 0.5
            quadratic_penalty = ((avg_slippage_bps - 50) ** 2) / 10000
            return linear_penalty + quadratic_penalty

    def calculate_net_return(
        self,
        gross_return: float,
        avg_slippage_bps: float
    ) -> float:
        """Calculate net return after deducting slippage.

        Simple formula:
            Net Return = Gross Return - Slippage

        Args:
            gross_return: Gross strategy return (e.g., 0.20 for 20%)
            avg_slippage_bps: Average slippage in basis points

        Returns:
            Net return after slippage deduction
        """
        slippage_decimal = avg_slippage_bps / 10000
        return gross_return - slippage_decimal

    def estimate_annual_cost(
        self,
        annual_turnover: float,
        avg_slippage_bps: float
    ) -> float:
        """Estimate annual execution cost.

        Args:
            annual_turnover: Annual portfolio turnover (e.g., 2.0 for 200%)
            avg_slippage_bps: Average slippage per trade in basis points

        Returns:
            Annual cost as fraction of portfolio
        """
        return annual_turnover * (avg_slippage_bps / 10000)

    def get_optimal_trade_horizon(
        self,
        trade_size: float,
        adv: float,
        urgency_factor: float = 1.0
    ) -> int:
        """Estimate optimal trade horizon to minimize impact.

        Based on Almgren & Chriss optimal execution framework.
        Longer horizons reduce impact but increase timing risk.

        Args:
            trade_size: Total trade size in TWD
            adv: Average daily volume in TWD
            urgency_factor: Higher = faster execution (1.0 = balanced)

        Returns:
            Recommended number of days to complete trade
        """
        # Participation target: 10% of ADV
        target_participation = 0.10 / urgency_factor

        # Days needed at target participation
        daily_trade = adv * target_participation
        if daily_trade <= 0:
            return 1

        days = int(np.ceil(trade_size / daily_trade))
        return max(1, days)

    def simulate_execution_path(
        self,
        trade_size: float,
        adv: float,
        volatility: float,
        n_days: int = 5
    ) -> pd.DataFrame:
        """Simulate execution path with daily slippage.

        Args:
            trade_size: Total trade size in TWD
            adv: Average daily volume in TWD
            volatility: Daily return volatility
            n_days: Number of days to execute

        Returns:
            DataFrame with daily execution details
        """
        daily_trade = trade_size / n_days
        participation = daily_trade / adv

        execution_data = []
        cumulative_cost = 0

        for day in range(1, n_days + 1):
            # Calculate daily slippage
            impact = self.impact_coeff * np.sqrt(participation) * volatility * 100
            daily_slippage = self.base_cost_bps + impact
            daily_cost = daily_trade * (daily_slippage / 10000)
            cumulative_cost += daily_cost

            execution_data.append({
                'day': day,
                'daily_trade': daily_trade,
                'participation_rate': participation,
                'slippage_bps': daily_slippage,
                'daily_cost': daily_cost,
                'cumulative_cost': cumulative_cost
            })

        return pd.DataFrame(execution_data)
