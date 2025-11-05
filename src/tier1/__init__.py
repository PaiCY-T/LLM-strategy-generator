"""
Tier 1: YAML Configuration Layer
=================================

Provides safe, declarative strategy configuration through YAML/JSON.
Enables LLMs to generate strategies without writing code.

Architecture: Structural Mutation Phase 2 - Phase D (Advanced Capabilities)
Tasks: D.1 - YAML Schema Design and Validator
       D.2 - YAML → Factor Interpreter

Components:
-----------
1. yaml_schema.json: JSON Schema definition for strategy configuration
2. YAMLValidator: Validates YAML/JSON against schema with business rules
3. YAMLInterpreter: Interprets validated YAML into Strategy objects
4. FactorFactory: Creates Factor instances from configuration
5. Example configurations: Pre-built strategy templates

Features:
---------
- JSON Schema validation for structure and types
- Custom business rule validation (dependency cycles, factor existence)
- Parameter bounds validation using registry metadata
- Safe interpretation of YAML into executable Strategy objects
- Clear error messages with context
- Support for all 13 registered factors

Usage Example:
-------------
    from src.tier1 import YAMLValidator, YAMLInterpreter

    # Validate YAML file
    validator = YAMLValidator()
    result = validator.validate_file("examples/yaml_strategies/momentum_basic.yaml")

    if result.is_valid:
        print("Configuration is valid!")

        # Interpret YAML into Strategy
        interpreter = YAMLInterpreter()
        strategy = interpreter.from_file("examples/yaml_strategies/momentum_basic.yaml")

        # Execute strategy
        result = strategy.to_pipeline(data)
    else:
        print("Validation errors:")
        for error in result.errors:
            print(f"  - {error}")
"""

from .yaml_validator import YAMLValidator, ValidationResult
from .yaml_interpreter import YAMLInterpreter, InterpretationError
from .factor_factory import FactorFactory, FactorFactoryError

__all__ = [
    "YAMLValidator",
    "ValidationResult",
    "YAMLInterpreter",
    "InterpretationError",
    "FactorFactory",
    "FactorFactoryError"
]
