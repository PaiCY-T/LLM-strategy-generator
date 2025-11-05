"""
Momentum Strategy Composition Example

Demonstrates how to compose a Strategy DAG that replicates MomentumTemplate behavior
using the Factor Graph architecture. This example shows how to:
1. Define Factor logic for momentum, MA filter, catalyst, selection, and position signals
2. Compose Factors into a Strategy DAG with proper dependencies
3. Execute the Strategy pipeline on backtest data

This composition mimics MomentumTemplate with the following Factor DAG:
- momentum_factor → selection_factor
- ma_filter_factor → selection_factor
- catalyst_factor → selection_factor
- selection_factor → position_signal_factor

Architecture: Phase 2.0+ Factor Graph System
"""

import pandas as pd
from typing import Dict, Any

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.strategy import Strategy
from src.templates.data_cache import DataCache


# ==================== Factor Logic Functions ====================

def momentum_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate price momentum using rolling returns.

    Replicates MomentumTemplate._calculate_momentum logic:
    - Calculate daily percentage changes from close price
    - Apply rolling mean over momentum_period

    Args:
        data: DataFrame with 'close' column
        params: Dict with 'momentum_period' (int)

    Returns:
        DataFrame with 'momentum' column added
    """
    period = params['momentum_period']

    # Calculate daily returns
    daily_returns = data['close'] / data['close'].shift(1) - 1

    # Apply rolling mean to get momentum score
    data['momentum'] = daily_returns.rolling(window=period).mean()

    return data


def ma_filter_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply moving average filter for trend confirmation.

    Replicates MomentumTemplate MA filter logic:
    - Calculate moving average of close price
    - Create boolean filter: close > MA

    Args:
        data: DataFrame with 'close' column
        params: Dict with 'ma_period' (int)

    Returns:
        DataFrame with 'ma_filter' boolean column added
    """
    period = params['ma_period']

    # Calculate moving average
    ma = data['close'].rolling(window=period).mean()

    # Create boolean filter
    data['ma_filter'] = (data['close'] > ma).astype(int)

    return data


def catalyst_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Apply catalyst filter (revenue or earnings).

    Replicates MomentumTemplate catalyst logic:
    - For revenue: short-term MA > long-term MA (acceleration)
    - For earnings: short-term ROE MA > long-term ROE MA (improvement)

    Args:
        data: DataFrame (catalyst data loaded from cache internally)
        params: Dict with 'catalyst_type' (str), 'catalyst_lookback' (int)

    Returns:
        DataFrame with 'catalyst_filter' boolean column added
    """
    cache = DataCache.get_instance()
    catalyst_type = params['catalyst_type']
    lookback = params['catalyst_lookback']

    if catalyst_type == 'revenue':
        # Load revenue data
        revenue = cache.get('monthly_revenue:當月營收', verbose=False)

        # Calculate short-term and long-term MAs
        revenue_short_ma = revenue.average(lookback)
        revenue_long_ma = revenue.average(12)  # 12-month baseline

        # Revenue acceleration condition
        catalyst_condition = revenue_short_ma > revenue_long_ma

    elif catalyst_type == 'earnings':
        # Load ROE data
        roe = cache.get('fundamental_features:ROE綜合損益', verbose=False)

        # Calculate short-term and long-term MAs
        roe_short_ma = roe.average(lookback)
        roe_long_ma = roe.average(8)  # 8-quarter baseline (2 years)

        # Earnings improvement condition
        catalyst_condition = roe_short_ma > roe_long_ma
    else:
        raise ValueError(f"Invalid catalyst_type: {catalyst_type}")

    # Convert finlab data structure to pandas boolean series
    # Align with data index
    data['catalyst_filter'] = catalyst_condition.reindex(data.index, fill_value=0).fillna(0).astype(int)

    return data


def selection_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Select top N stocks by momentum score, filtered by conditions.

    Replicates MomentumTemplate selection logic:
    - Combine MA filter and catalyst filter (both must be True)
    - Select top N stocks by momentum score among filtered stocks

    Args:
        data: DataFrame with 'momentum', 'ma_filter', 'catalyst_filter' columns
        params: Dict with 'n_stocks' (int)

    Returns:
        DataFrame with 'selected' boolean column added
    """
    n_stocks = params['n_stocks']

    # Combine filters: both MA filter and catalyst filter must be True
    all_conditions = (data['ma_filter'] == 1) & (data['catalyst_filter'] == 1)

    # Initialize selected column
    data['selected'] = 0

    # For each timestamp, select top N by momentum where conditions are True
    for timestamp in data.index.get_level_values(0).unique():
        timestamp_data = data.loc[timestamp]

        # Apply conditions filter
        filtered = timestamp_data[all_conditions.loc[timestamp]]

        # Select top N by momentum
        if len(filtered) > 0:
            top_n = filtered.nlargest(n_stocks, 'momentum')
            data.loc[(timestamp, top_n.index), 'selected'] = 1

    return data


def position_signal_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert selection to position signals.

    Final step: convert 'selected' boolean to 'positions' column for backtest.

    Args:
        data: DataFrame with 'selected' column
        params: Dict (no parameters needed)

    Returns:
        DataFrame with 'positions' column added
    """
    # Convert selected flag to positions (1 = hold, 0 = no position)
    data['positions'] = data['selected']

    return data


# ==================== Strategy Composition ====================

def create_momentum_strategy(params: Dict[str, Any]) -> Strategy:
    """
    Create momentum strategy DAG from parameters.

    Composes a Strategy that replicates MomentumTemplate behavior:
    1. momentum_factor: Calculate price momentum
    2. ma_filter_factor: Apply moving average filter
    3. catalyst_factor: Apply revenue/earnings catalyst
    4. selection_factor: Select top N stocks by momentum (depends on 1, 2, 3)
    5. position_signal_factor: Convert selection to positions (depends on 4)

    Args:
        params: Parameter dictionary with keys:
            - momentum_period (int): Momentum calculation period
            - ma_period (int): Moving average period
            - catalyst_type (str): 'revenue' or 'earnings'
            - catalyst_lookback (int): Catalyst detection window
            - n_stocks (int): Number of stocks to select

    Returns:
        Strategy instance with composed Factor DAG

    Example:
        >>> params = {
        ...     'momentum_period': 10,
        ...     'ma_period': 60,
        ...     'catalyst_type': 'revenue',
        ...     'catalyst_lookback': 3,
        ...     'n_stocks': 10
        ... }
        >>> strategy = create_momentum_strategy(params)
        >>> strategy.validate()
        True
    """
    # Create strategy instance
    strategy = Strategy(
        id=f"momentum_dag_{params['momentum_period']}_{params['ma_period']}",
        generation=0
    )

    # 1. Momentum factor (no dependencies)
    momentum_factor = Factor(
        id="momentum_factor",
        name="Momentum Calculator",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["momentum"],
        logic=momentum_logic,
        parameters={'momentum_period': params['momentum_period']},
        description=f"Calculate {params['momentum_period']}-period rolling momentum"
    )
    strategy.add_factor(momentum_factor)

    # 2. MA filter factor (no dependencies)
    ma_filter_factor = Factor(
        id="ma_filter_factor",
        name="Moving Average Filter",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["ma_filter"],
        logic=ma_filter_logic,
        parameters={'ma_period': params['ma_period']},
        description=f"Apply {params['ma_period']}-period MA filter"
    )
    strategy.add_factor(ma_filter_factor)

    # 3. Catalyst factor (no dependencies)
    catalyst_factor = Factor(
        id="catalyst_factor",
        name=f"{params['catalyst_type'].capitalize()} Catalyst",
        category=FactorCategory.QUALITY,
        inputs=["close"],  # Close needed for index alignment
        outputs=["catalyst_filter"],
        logic=catalyst_logic,
        parameters={
            'catalyst_type': params['catalyst_type'],
            'catalyst_lookback': params['catalyst_lookback']
        },
        description=f"Apply {params['catalyst_type']} catalyst filter"
    )
    strategy.add_factor(catalyst_factor)

    # 4. Selection factor (depends on momentum, ma_filter, catalyst_filter)
    selection_factor = Factor(
        id="selection_factor",
        name="Top N Stock Selection",
        category=FactorCategory.SIGNAL,
        inputs=["momentum", "ma_filter", "catalyst_filter"],
        outputs=["selected"],
        logic=selection_logic,
        parameters={'n_stocks': params['n_stocks']},
        description=f"Select top {params['n_stocks']} stocks by momentum"
    )
    strategy.add_factor(
        selection_factor,
        depends_on=["momentum_factor", "ma_filter_factor", "catalyst_factor"]
    )

    # 5. Position signal factor (depends on selection)
    position_signal_factor = Factor(
        id="position_signal_factor",
        name="Position Signal Generator",
        category=FactorCategory.ENTRY,
        inputs=["selected"],
        outputs=["positions"],
        logic=position_signal_logic,
        parameters={},
        description="Convert selection to position signals"
    )
    strategy.add_factor(
        position_signal_factor,
        depends_on=["selection_factor"]
    )

    return strategy


# ==================== Example Usage ====================

def main():
    """
    Example: Create and validate momentum strategy.
    """
    # Define parameters matching MomentumTemplate defaults
    params = {
        'momentum_period': 10,
        'ma_period': 60,
        'catalyst_type': 'revenue',
        'catalyst_lookback': 3,
        'n_stocks': 10
    }

    print("=" * 60)
    print("Momentum Strategy Composition Example")
    print("=" * 60)

    # Create strategy
    print("\n1. Creating momentum strategy DAG...")
    strategy = create_momentum_strategy(params)

    print(f"   Strategy ID: {strategy.id}")
    print(f"   Factors: {len(strategy.factors)}")

    # Validate strategy
    print("\n2. Validating strategy...")
    try:
        is_valid = strategy.validate()
        print(f"   ✓ Strategy validation passed: {is_valid}")
    except ValueError as e:
        print(f"   ✗ Strategy validation failed: {e}")
        return

    # Show factor execution order
    print("\n3. Factor execution order:")
    factors = strategy.get_factors()
    for i, factor in enumerate(factors, 1):
        print(f"   {i}. {factor.name} ({factor.id})")
        print(f"      - Inputs: {factor.inputs}")
        print(f"      - Outputs: {factor.outputs}")

    # Show DAG structure
    print("\n4. DAG dependencies:")
    for factor_id in strategy.dag.nodes():
        predecessors = list(strategy.dag.predecessors(factor_id))
        if predecessors:
            print(f"   {factor_id} depends on: {predecessors}")
        else:
            print(f"   {factor_id} (root factor, no dependencies)")

    print("\n" + "=" * 60)
    print("Strategy composition complete!")
    print("=" * 60)

    print("\nNext steps:")
    print("1. Run validation script to compare with MomentumTemplate")
    print("2. Execute backtest using strategy.to_pipeline(data)")
    print("3. Compare metrics (annual_return, sharpe_ratio, max_drawdown)")


if __name__ == "__main__":
    main()
