"""
Momentum Factors Module
=======================

Momentum-related factors extracted from MomentumTemplate.
Provides reusable momentum calculation, trend filtering, and catalyst detection.

Architecture: Phase 2.0+ Factor Graph System (Matrix-Native)
Source: Extracted from src/templates/momentum_template.py

Available Factors:
-----------------
1. MomentumFactor: Price momentum using rolling mean of returns
2. MAFilterFactor: Moving average filter for trend confirmation
3. RevenueCatalystFactor: Revenue acceleration catalyst detection
4. EarningsCatalystFactor: Earnings momentum catalyst (ROE improvement)

Usage Example (Phase 2.0):
--------------------------
    from src.factor_library.momentum_factors import (
        create_momentum_factor,
        create_ma_filter_factor
    )
    from src.factor_graph.finlab_dataframe import FinLabDataFrame
    from finlab import data

    # Create factors with custom parameters
    momentum = create_momentum_factor(momentum_period=20)
    ma_filter = create_ma_filter_factor(ma_periods=60)

    # Execute factors on FinLabDataFrame container
    container = FinLabDataFrame(data_module=data)
    container = momentum.execute(container)
    container = ma_filter.execute(container)
"""

from typing import Dict, Any
import pandas as pd

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.finlab_dataframe import FinLabDataFrame
from src.templates.data_cache import DataCache


# ============================================================================
# Factor Logic Functions
# ============================================================================

def _momentum_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Calculate price momentum using rolling mean of returns (Matrix-Native Phase 2.0).

    This logic computes momentum score as the rolling mean of daily
    percentage price changes over a specified lookback window.

    Args:
        container: FinLabDataFrame container with 'close' matrix
        parameters: Dictionary with 'momentum_period' (int)

    Modifies:
        Adds 'momentum' matrix to container (Dates×Symbols)

    Implementation:
        1. Get close price matrix from container
        2. Calculate daily returns: close / close.shift() - 1
        3. Apply rolling mean: .rolling(momentum_period).mean()
        4. Add momentum matrix to container

    Example:
        momentum_period=5, returns=[0.02, 0.01, -0.01, 0.03, 0.02]
        → momentum = mean([0.02, 0.01, -0.01, 0.03, 0.02]) = 0.014

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Modifies container in-place (no return)
    """
    momentum_period = parameters['momentum_period']

    # Get close price matrix from container
    close = container.get_matrix('close')

    # Calculate daily percentage changes
    daily_returns = close / close.shift(1) - 1

    # Apply rolling mean to calculate momentum score
    momentum = daily_returns.rolling(window=momentum_period).mean()

    # Add momentum matrix to container
    container.add_matrix('momentum', momentum)


def _ma_filter_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Apply moving average filter for trend confirmation (Matrix-Native Phase 2.0).

    Creates a boolean filter that is True when price is above its moving average,
    indicating an uptrend.

    Args:
        container: FinLabDataFrame container with 'close' matrix
        parameters: Dictionary with 'ma_periods' (int)

    Modifies:
        Adds 'ma_filter' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. Get close price matrix from container
        2. Calculate MA: close.rolling(ma_periods).mean()
        3. Filter: close > MA (boolean matrix)
        4. Add ma_filter matrix to container

    Example:
        ma_periods=60, close=105, MA(60)=100 → ma_filter=True (uptrend)

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Works with Dates×Symbols matrices (not columns)
        - Modifies container in-place (no return)
    """
    ma_periods = parameters['ma_periods']

    # Get close price matrix from container
    close = container.get_matrix('close')

    # Calculate moving average
    ma = close.rolling(window=ma_periods).mean()

    # Create filter: price above MA indicates uptrend
    ma_filter = close > ma

    # Add ma_filter matrix to container
    container.add_matrix('ma_filter', ma_filter)


def _revenue_catalyst_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Apply revenue acceleration catalyst filter (Matrix-Native Phase 2.0).

    Detects stocks showing revenue acceleration: short-term revenue MA
    greater than long-term revenue MA (12-month baseline).

    Args:
        container: FinLabDataFrame container (revenue loaded from DataCache)
        parameters: Dictionary with 'catalyst_lookback' (int) in months

    Modifies:
        Adds 'revenue_catalyst' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. Load monthly revenue data from DataCache
        2. Calculate short-term MA: revenue.average(catalyst_lookback)
        3. Calculate long-term MA: revenue.average(12) as baseline
        4. Condition: short_ma > long_ma (acceleration)
        5. Add revenue_catalyst matrix to container

    Note:
        Uses DataCache to avoid redundant data loading.
        The 12-month baseline is fixed as annual revenue performance.

    Example:
        catalyst_lookback=3, 3M_MA=500M, 12M_MA=450M
        → revenue_catalyst=True (accelerating)

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Modifies container in-place (no return)
    """
    catalyst_lookback = parameters['catalyst_lookback']

    # Load revenue data from cache
    cache = DataCache.get_instance()
    revenue = cache.get('monthly_revenue:當月營收', verbose=False)

    # Calculate short-term and long-term revenue moving averages
    revenue_short_ma = revenue.average(catalyst_lookback)
    revenue_long_ma = revenue.average(12)

    # Revenue acceleration: short-term > long-term
    revenue_catalyst = revenue_short_ma > revenue_long_ma

    # Add revenue_catalyst matrix to container
    container.add_matrix('revenue_catalyst', revenue_catalyst)


def _earnings_catalyst_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """
    Apply earnings momentum catalyst filter using ROE (Matrix-Native Phase 2.0).

    Detects stocks showing earnings momentum: current ROE improving
    compared to 8-quarter (2-year) baseline.

    Args:
        container: FinLabDataFrame container (ROE loaded from DataCache)
        parameters: Dictionary with 'catalyst_lookback' (int) in quarters

    Modifies:
        Adds 'earnings_catalyst' matrix to container (Dates×Symbols, boolean)

    Implementation:
        1. Load ROE data from DataCache
        2. Calculate short-term ROE MA: roe.average(catalyst_lookback)
        3. Calculate long-term ROE MA: roe.average(8) as baseline
        4. Condition: short_ma > long_ma (improving)
        5. Add earnings_catalyst matrix to container

    Note:
        Uses DataCache to avoid redundant data loading.
        The 8-quarter baseline represents 2 years of earnings history.

    Example:
        catalyst_lookback=3, 3Q_ROE=15%, 8Q_ROE=12%
        → earnings_catalyst=True (improving profitability)

    Phase 2.0 Changes:
        - Input: FinLabDataFrame container (not DataFrame)
        - Modifies container in-place (no return)
    """
    catalyst_lookback = parameters['catalyst_lookback']

    # Load ROE data from cache
    cache = DataCache.get_instance()
    roe = cache.get('fundamental_features:ROE綜合損益', verbose=False)

    # Calculate short-term and long-term ROE moving averages
    roe_short_ma = roe.average(catalyst_lookback)
    roe_long_ma = roe.average(8)

    # Earnings momentum: short-term ROE > long-term ROE
    earnings_catalyst = roe_short_ma > roe_long_ma

    # Add earnings_catalyst matrix to container
    container.add_matrix('earnings_catalyst', earnings_catalyst)


# ============================================================================
# Factor Classes
# ============================================================================

class MomentumFactor(Factor):
    """
    Price momentum factor using rolling mean of returns.

    Calculates momentum score as the rolling mean of daily percentage
    price changes over a specified lookback window. Higher momentum scores
    indicate stronger recent price appreciation.

    Category: MOMENTUM
    Inputs: ["close"]
    Outputs: ["momentum"]
    Parameters:
        - momentum_period (int): Lookback period for momentum calculation
          Common values: 5 (1 week), 10 (2 weeks), 20 (1 month), 30 (1.5 months)

    Example:
        >>> momentum = MomentumFactor(momentum_period=20)
        >>> data = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
        >>> result = momentum.execute(data)
        >>> "momentum" in result.columns
        True
    """

    def __init__(self, momentum_period: int = 20):
        """
        Initialize MomentumFactor.

        Args:
            momentum_period: Lookback period for momentum calculation (default: 20)
        """
        super().__init__(
            id=f"momentum_{momentum_period}",
            name=f"Momentum ({momentum_period}d)",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["momentum"],
            logic=_momentum_logic,
            parameters={"momentum_period": momentum_period},
            description=f"Price momentum using {momentum_period}-day rolling mean of returns"
        )


class MAFilterFactor(Factor):
    """
    Moving average filter for trend confirmation.

    Creates a boolean filter that is True when price is above its moving
    average, indicating an uptrend. Used to filter trades to trend direction.

    Category: MOMENTUM
    Inputs: ["close"]
    Outputs: ["ma_filter"]
    Parameters:
        - ma_periods (int): Moving average period for trend filter
          Common values: 20 (1 month), 60 (3 months), 90 (4.5 months), 120 (6 months)

    Example:
        >>> ma_filter = MAFilterFactor(ma_periods=60)
        >>> data = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
        >>> result = ma_filter.execute(data)
        >>> "ma_filter" in result.columns
        True
    """

    def __init__(self, ma_periods: int = 60):
        """
        Initialize MAFilterFactor.

        Args:
            ma_periods: Moving average period for trend filter (default: 60)
        """
        super().__init__(
            id=f"ma_filter_{ma_periods}",
            name=f"MA Filter ({ma_periods}d)",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["ma_filter"],
            logic=_ma_filter_logic,
            parameters={"ma_periods": ma_periods},
            description=f"Trend filter using {ma_periods}-day moving average"
        )


class RevenueCatalystFactor(Factor):
    """
    Revenue acceleration catalyst detection.

    Detects stocks showing revenue acceleration: short-term revenue MA
    must be greater than long-term revenue MA (12-month baseline),
    indicating improving business fundamentals.

    Category: VALUE
    Inputs: ["_dummy"] (placeholder, uses cached data internally)
    Outputs: ["revenue_catalyst"]
    Parameters:
        - catalyst_lookback (int): Lookback window for short-term MA in months
          Common values: 2 (very recent), 3 (recent), 4 (short-term), 6 (medium-term)

    Note:
        Uses DataCache to load monthly revenue data. The 12-month baseline
        is fixed as it represents annual revenue performance.
        The "_dummy" input is a placeholder required by Factor validation;
        actual data is loaded from DataCache internally.

    Example:
        >>> catalyst = RevenueCatalystFactor(catalyst_lookback=3)
        >>> data = pd.DataFrame({"_dummy": [True]})
        >>> result = catalyst.execute(data)
        >>> "revenue_catalyst" in result.columns
        True
    """

    def __init__(self, catalyst_lookback: int = 3):
        """
        Initialize RevenueCatalystFactor.

        Args:
            catalyst_lookback: Lookback window for catalyst detection in months (default: 3)
        """
        super().__init__(
            id=f"revenue_catalyst_{catalyst_lookback}",
            name=f"Revenue Catalyst ({catalyst_lookback}M)",
            category=FactorCategory.VALUE,
            inputs=["_dummy"],  # Placeholder input; actual data from DataCache
            outputs=["revenue_catalyst"],
            logic=_revenue_catalyst_logic,
            parameters={"catalyst_lookback": catalyst_lookback},
            description=f"Revenue acceleration detection using {catalyst_lookback}-month lookback"
        )


class EarningsCatalystFactor(Factor):
    """
    Earnings momentum catalyst detection using ROE.

    Detects stocks showing earnings momentum: current ROE improving
    compared to 8-quarter (2-year) baseline, indicating improving
    profitability and capital efficiency.

    Category: QUALITY
    Inputs: ["_dummy"] (placeholder, uses cached data internally)
    Outputs: ["earnings_catalyst"]
    Parameters:
        - catalyst_lookback (int): Lookback window for short-term ROE MA in quarters
          Common values: 2 (very recent), 3 (recent), 4 (short-term), 6 (medium-term)

    Note:
        Uses DataCache to load ROE data. The 8-quarter baseline represents
        2 years of earnings history.
        The "_dummy" input is a placeholder required by Factor validation;
        actual data is loaded from DataCache internally.

    Example:
        >>> catalyst = EarningsCatalystFactor(catalyst_lookback=3)
        >>> data = pd.DataFrame({"_dummy": [True]})
        >>> result = catalyst.execute(data)
        >>> "earnings_catalyst" in result.columns
        True
    """

    def __init__(self, catalyst_lookback: int = 3):
        """
        Initialize EarningsCatalystFactor.

        Args:
            catalyst_lookback: Lookback window for catalyst detection in quarters (default: 3)
        """
        super().__init__(
            id=f"earnings_catalyst_{catalyst_lookback}",
            name=f"Earnings Catalyst ({catalyst_lookback}Q)",
            category=FactorCategory.QUALITY,
            inputs=["_dummy"],  # Placeholder input; actual data from DataCache
            outputs=["earnings_catalyst"],
            logic=_earnings_catalyst_logic,
            parameters={"catalyst_lookback": catalyst_lookback},
            description=f"Earnings momentum (ROE) detection using {catalyst_lookback}-quarter lookback"
        )


# ============================================================================
# Factory Functions
# ============================================================================

def create_momentum_factor(momentum_period: int = 20) -> Factor:
    """
    Create a momentum factor with custom period.

    Factory function for creating MomentumFactor instances with
    configurable momentum period.

    Args:
        momentum_period: Lookback period for momentum calculation
            Common values: 5 (1 week), 10 (2 weeks), 20 (1 month), 30 (1.5 months)

    Returns:
        Factor: Configured MomentumFactor instance

    Example:
        >>> momentum = create_momentum_factor(momentum_period=20)
        >>> momentum.parameters
        {'momentum_period': 20}
    """
    return MomentumFactor(momentum_period=momentum_period)


def create_ma_filter_factor(ma_periods: int = 60) -> Factor:
    """
    Create a moving average filter factor with custom period.

    Factory function for creating MAFilterFactor instances with
    configurable MA period.

    Args:
        ma_periods: Moving average period for trend filter
            Common values: 20 (1 month), 60 (3 months), 90 (4.5 months), 120 (6 months)

    Returns:
        Factor: Configured MAFilterFactor instance

    Example:
        >>> ma_filter = create_ma_filter_factor(ma_periods=60)
        >>> ma_filter.parameters
        {'ma_periods': 60}
    """
    return MAFilterFactor(ma_periods=ma_periods)


def create_revenue_catalyst_factor(catalyst_lookback: int = 3) -> Factor:
    """
    Create a revenue catalyst factor with custom lookback.

    Factory function for creating RevenueCatalystFactor instances with
    configurable lookback window.

    Args:
        catalyst_lookback: Lookback window for catalyst detection in months
            Common values: 2 (very recent), 3 (recent), 4 (short-term), 6 (medium-term)

    Returns:
        Factor: Configured RevenueCatalystFactor instance

    Example:
        >>> catalyst = create_revenue_catalyst_factor(catalyst_lookback=3)
        >>> catalyst.parameters
        {'catalyst_lookback': 3}
    """
    return RevenueCatalystFactor(catalyst_lookback=catalyst_lookback)


def create_earnings_catalyst_factor(catalyst_lookback: int = 3) -> Factor:
    """
    Create an earnings catalyst factor with custom lookback.

    Factory function for creating EarningsCatalystFactor instances with
    configurable lookback window.

    Args:
        catalyst_lookback: Lookback window for catalyst detection in quarters
            Common values: 2 (very recent), 3 (recent), 4 (short-term), 6 (medium-term)

    Returns:
        Factor: Configured EarningsCatalystFactor instance

    Example:
        >>> catalyst = create_earnings_catalyst_factor(catalyst_lookback=3)
        >>> catalyst.parameters
        {'catalyst_lookback': 3}
    """
    return EarningsCatalystFactor(catalyst_lookback=catalyst_lookback)
