"""
Execution Layer - Strategy Execution and Configuration

This module provides data structures and utilities for strategy execution:
- StrategyConfig: Main configuration dataclass for strategy patterns
- Field mapping and validation integration with Layer 1 manifest
- Parameter configuration with type safety and range validation
- Logic and constraint definitions for strategy execution
- StrategyFactory: Factory for creating and executing strategies
- BacktestResult: Comprehensive backtest result structure
- SchemaValidator: Comprehensive YAML schema validation

Integration:
    - Layer 1: Uses FieldMetadata from src/config/field_metadata.py
    - Layer 2: Supports field validation via src/validation/field_validator.py
    - Execution: Configuration for strategy execution engine

Usage:
    from src.execution.strategy_config import StrategyConfig, FieldMapping
    from src.execution.strategy_factory import StrategyFactory
    from src.execution.backtest_result import BacktestResult
    from src.execution.schema_validator import SchemaValidator

    # Create config
    config = StrategyConfig(
        name="Pure Momentum",
        type="momentum",
        description="Fast breakout strategy",
        fields=[...],
        parameters=[...],
        logic=LogicConfig(...),
        constraints=[...]
    )

    # Validate YAML schema
    validator = SchemaValidator()
    errors = validator.validate(yaml_dict)

    # Execute strategy
    factory = StrategyFactory()
    result = factory.execute(config)
"""

from src.execution.strategy_config import (
    FieldMapping,
    ParameterConfig,
    LogicConfig,
    ConstraintConfig,
    StrategyConfig,
)
from src.execution.backtest_result import BacktestResult
from src.execution.strategy_factory import StrategyFactory
from src.execution.schema_validator import (
    SchemaValidator,
    ValidationError,
    ValidationSeverity,
)

__all__ = [
    'FieldMapping',
    'ParameterConfig',
    'LogicConfig',
    'ConstraintConfig',
    'StrategyConfig',
    'BacktestResult',
    'StrategyFactory',
    'SchemaValidator',
    'ValidationError',
    'ValidationSeverity',
]
