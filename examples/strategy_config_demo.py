"""
Strategy Configuration Demo

Demonstrates the usage of StrategyConfig dataclasses for defining
strategy patterns with Layer 1 field integration.

Task: 18.3 - Define StrategyConfig Data Structure
Usage: python examples/strategy_config_demo.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.execution.strategy_config import (
    StrategyConfig,
    FieldMapping,
    ParameterConfig,
    LogicConfig,
    ConstraintConfig,
)


def create_pure_momentum_config() -> StrategyConfig:
    """Create Pure Momentum strategy configuration."""
    return StrategyConfig(
        name="Pure Momentum",
        type="momentum",
        description="Fast breakout strategy using price momentum with rolling mean returns",
        fields=[
            FieldMapping(
                canonical_name="price:收盤價",
                alias="close",
                usage="Signal generation - momentum calculation"
            ),
            FieldMapping(
                canonical_name="price:成交金額",
                alias="volume",
                usage="Volume filtering - minimum liquidity requirement"
            )
        ],
        parameters=[
            ParameterConfig(
                name="momentum_period",
                type="integer",
                value=20,
                default=20,
                range=(10, 60),
                unit="trading_days"
            ),
            ParameterConfig(
                name="entry_threshold",
                type="float",
                value=0.02,
                default=0.02,
                range=(0.01, 0.10),
                unit="percentage"
            ),
            ParameterConfig(
                name="min_volume",
                type="float",
                value=1000000.0,
                default=1000000.0,
                range=(100000.0, 10000000.0),
                unit="currency"
            )
        ],
        logic=LogicConfig(
            entry="(price.pct_change(momentum_period).rolling(5).mean() > entry_threshold) & (volume > min_volume)",
            exit="None",
            dependencies=["price:收盤價", "price:成交金額"]
        ),
        constraints=[
            ConstraintConfig(
                type="data_quality",
                condition="No NaN values in price field",
                severity="critical"
            ),
            ConstraintConfig(
                type="parameter",
                condition="momentum_period < total_backtest_days",
                severity="critical"
            ),
            ConstraintConfig(
                type="performance",
                condition="min_volume filter must exclude <5% of universe",
                severity="warning"
            )
        ],
        coverage=0.18
    )


def create_turtle_breakout_config() -> StrategyConfig:
    """Create Turtle Breakout strategy configuration."""
    return StrategyConfig(
        name="Turtle Breakout",
        type="breakout",
        description="N-day high/low breakout with ATR-based position sizing and stop loss",
        fields=[
            FieldMapping(
                canonical_name="price:收盤價",
                alias="close",
                usage="Breakout detection and stop loss"
            ),
            FieldMapping(
                canonical_name="price:最高價",
                alias="high",
                usage="N-day high for entry breakout"
            ),
            FieldMapping(
                canonical_name="price:最低價",
                alias="low",
                usage="N-day low for exit breakout and ATR calculation"
            ),
            FieldMapping(
                canonical_name="price:成交金額",
                alias="volume",
                usage="Volume confirmation"
            )
        ],
        parameters=[
            ParameterConfig(
                name="breakout_period",
                type="integer",
                value=20,
                default=20,
                range=(10, 55),
                unit="trading_days"
            ),
            ParameterConfig(
                name="atr_period",
                type="integer",
                value=14,
                default=14,
                range=(7, 30),
                unit="trading_days"
            ),
            ParameterConfig(
                name="atr_stop_multiplier",
                type="float",
                value=2.0,
                default=2.0,
                range=(1.0, 4.0),
                unit="multiplier"
            ),
            ParameterConfig(
                name="min_volume",
                type="float",
                value=1000000.0,
                default=1000000.0,
                range=(100000.0, 10000000.0),
                unit="currency"
            )
        ],
        logic=LogicConfig(
            entry="(close > high.rolling(breakout_period).max().shift(1)) & (volume > min_volume)",
            exit="close < (entry_price - atr * atr_stop_multiplier)",
            dependencies=["price:收盤價", "price:最高價", "price:最低價", "price:成交金額"]
        ),
        constraints=[
            ConstraintConfig(
                type="data_quality",
                condition="High >= Low >= Close for all periods",
                severity="critical"
            ),
            ConstraintConfig(
                type="parameter",
                condition="breakout_period > atr_period for stability",
                severity="warning"
            ),
            ConstraintConfig(
                type="logic",
                condition="ATR calculation requires minimum history of atr_period + 1",
                severity="critical"
            )
        ],
        coverage=0.16
    )


def print_config_summary(config: StrategyConfig):
    """Print summary of strategy configuration."""
    print(f"\n{'='*70}")
    print(f"Strategy: {config.name}")
    print(f"Type: {config.type}")
    print(f"Coverage: {config.coverage:.1%}")
    print(f"{'='*70}")

    print(f"\nDescription:")
    print(f"  {config.description}")

    print(f"\nRequired Fields ({len(config.fields)}):")
    for field in config.fields:
        print(f"  - {field.canonical_name} (alias: {field.alias})")
        print(f"    Usage: {field.usage}")

    print(f"\nParameters ({len(config.parameters)}):")
    for param in config.parameters:
        range_str = f"{param.range}" if param.range else "N/A"
        unit_str = f" {param.unit}" if param.unit else ""
        print(f"  - {param.name}: {param.value}{unit_str}")
        print(f"    Type: {param.type}, Range: {range_str}, Default: {param.default}")

    print(f"\nLogic:")
    print(f"  Entry: {config.logic.entry}")
    print(f"  Exit: {config.logic.exit}")
    print(f"  Dependencies: {', '.join(config.logic.dependencies)}")

    print(f"\nConstraints ({len(config.constraints)}):")
    for constraint in config.constraints:
        print(f"  - [{constraint.severity.upper()}] {constraint.type}")
        print(f"    Condition: {constraint.condition}")

    # Validation checks
    print(f"\nValidation:")
    print(f"  Dependencies satisfied: {config.validate_dependencies()}")
    print(f"  Critical constraints: {len(config.get_critical_constraints())}")

    # Parameter validation
    all_valid = all(p.is_in_range() for p in config.parameters)
    print(f"  All parameters in range: {all_valid}")


def main():
    """Run demo of strategy configuration structures."""
    print("Strategy Configuration Demo")
    print("="*70)
    print("Demonstrates StrategyConfig dataclasses for strategy pattern definition")
    print("Task 18.3 - Define StrategyConfig Data Structure")

    # Create and display Pure Momentum config
    momentum_config = create_pure_momentum_config()
    print_config_summary(momentum_config)

    # Create and display Turtle Breakout config
    turtle_config = create_turtle_breakout_config()
    print_config_summary(turtle_config)

    # Demonstrate helper methods
    print(f"\n{'='*70}")
    print("Helper Methods Demo")
    print(f"{'='*70}")

    # Get specific parameter
    param = momentum_config.get_parameter_by_name("momentum_period")
    print(f"\nGet parameter 'momentum_period':")
    print(f"  Value: {param.value}, Range: {param.range}, In range: {param.is_in_range()}")

    # Get required fields
    fields = turtle_config.get_required_fields()
    print(f"\nTurtle Breakout required fields:")
    for field in fields:
        print(f"  - {field}")

    # Get critical constraints
    critical = momentum_config.get_critical_constraints()
    print(f"\nPure Momentum critical constraints ({len(critical)}):")
    for c in critical:
        print(f"  - {c.condition}")

    print(f"\n{'='*70}")
    print("Demo completed successfully!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
