"""
Factor Library Module
=====================

Reusable factor library for the Factor Graph architecture.
Provides pre-built factors extracted from templates, organized by category.

Architecture: Phase 2.0+ Factor Graph System

Available Factors:
-----------------
Momentum Factors (from MomentumTemplate):
    - MomentumFactor: Price momentum calculation using rolling returns
    - MAFilterFactor: Moving average filter for trend confirmation
    - RevenueCatalystFactor: Revenue acceleration catalyst detection
    - EarningsCatalystFactor: Earnings momentum catalyst (ROE improvement)

Turtle Factors (from TurtleTemplate):
    - ATRFactor: Average True Range calculation for volatility measurement
    - BreakoutFactor: N-day high/low breakout detection for entry signals
    - DualMAFilterFactor: Dual moving average filter for trend confirmation
    - ATRStopLossFactor: ATR-based stop loss calculation for risk management

Exit Factors (from Phase 1 Exit Mutation Framework):
    - TrailingStopFactor: Trailing stop loss that follows price
    - TimeBasedExitFactor: Exit positions after N periods
    - VolatilityStopFactor: Volatility-based stop using standard deviation
    - ProfitTargetFactor: Fixed profit target exit
    - CompositeExitFactor: Combines multiple exit signals with OR logic

Factory Functions:
-----------------
    - create_momentum_factor: Create momentum factor with custom period
    - create_ma_filter_factor: Create MA filter factor with custom period
    - create_revenue_catalyst_factor: Create revenue catalyst with custom lookback
    - create_earnings_catalyst_factor: Create earnings catalyst with custom lookback
    - create_atr_factor: Create ATR factor with custom period
    - create_breakout_factor: Create breakout factor with custom entry window
    - create_dual_ma_filter_factor: Create dual MA filter with custom periods
    - create_atr_stop_loss_factor: Create ATR stop loss with custom multiplier
    - create_trailing_stop_factor: Create trailing stop with custom parameters
    - create_time_based_exit_factor: Create time-based exit with custom holding period
    - create_volatility_stop_factor: Create volatility stop with custom parameters
    - create_profit_target_factor: Create profit target with custom percentage
    - create_composite_exit_factor: Create composite exit combining multiple signals

Example Usage:
-------------
    from src.factor_library import (
        create_momentum_factor,
        create_ma_filter_factor,
        create_revenue_catalyst_factor,
        create_trailing_stop_factor,
        create_profit_target_factor,
        create_composite_exit_factor
    )

    # Create individual factors
    momentum = create_momentum_factor(momentum_period=20)
    ma_filter = create_ma_filter_factor(ma_periods=60)
    catalyst = create_revenue_catalyst_factor(catalyst_lookback=3)

    # Create exit factors
    trailing_stop = create_trailing_stop_factor(trail_percent=0.10, activation_profit=0.05)
    profit_target = create_profit_target_factor(target_percent=0.30)
    composite_exit = create_composite_exit_factor(
        exit_signals=["trailing_stop_signal", "profit_target_signal"]
    )

    # Use in factor graph
    from src.factor_graph import FactorGraph
    graph = FactorGraph()
    graph.add_factor(momentum)
    graph.add_factor(ma_filter)
    graph.add_factor(catalyst)
    graph.add_factor(trailing_stop)
    graph.add_factor(profit_target)
    graph.add_factor(composite_exit)
"""

from .momentum_factors import (
    MomentumFactor,
    MAFilterFactor,
    RevenueCatalystFactor,
    EarningsCatalystFactor,
    create_momentum_factor,
    create_ma_filter_factor,
    create_revenue_catalyst_factor,
    create_earnings_catalyst_factor,
)

from .turtle_factors import (
    ATRFactor,
    BreakoutFactor,
    DualMAFilterFactor,
    ATRStopLossFactor,
    create_atr_factor,
    create_breakout_factor,
    create_dual_ma_filter_factor,
    create_atr_stop_loss_factor,
)

from .exit_factors import (
    TrailingStopFactor,
    TimeBasedExitFactor,
    VolatilityStopFactor,
    ProfitTargetFactor,
    CompositeExitFactor,
    create_trailing_stop_factor,
    create_time_based_exit_factor,
    create_volatility_stop_factor,
    create_profit_target_factor,
    create_composite_exit_factor,
)

from .registry import (
    FactorRegistry,
    FactorMetadata,
)

__all__ = [
    # Momentum factor classes
    "MomentumFactor",
    "MAFilterFactor",
    "RevenueCatalystFactor",
    "EarningsCatalystFactor",
    # Turtle factor classes
    "ATRFactor",
    "BreakoutFactor",
    "DualMAFilterFactor",
    "ATRStopLossFactor",
    # Exit factor classes
    "TrailingStopFactor",
    "TimeBasedExitFactor",
    "VolatilityStopFactor",
    "ProfitTargetFactor",
    "CompositeExitFactor",
    # Momentum factory functions
    "create_momentum_factor",
    "create_ma_filter_factor",
    "create_revenue_catalyst_factor",
    "create_earnings_catalyst_factor",
    # Turtle factory functions
    "create_atr_factor",
    "create_breakout_factor",
    "create_dual_ma_filter_factor",
    "create_atr_stop_loss_factor",
    # Exit factory functions
    "create_trailing_stop_factor",
    "create_time_based_exit_factor",
    "create_volatility_stop_factor",
    "create_profit_target_factor",
    "create_composite_exit_factor",
    # Registry
    "FactorRegistry",
    "FactorMetadata",
]
