"""
YAML Strategy Configuration Interpreter
========================================

Interprets validated YAML/JSON strategy configurations into executable Strategy objects.
Converts declarative YAML configs into Factor Graph DAG with proper dependency resolution.

Architecture: Structural Mutation Phase 2 - Phase D.2
Task: D.2 - YAML → Factor Interpreter

Features:
---------
1. Convert validated YAML configs to Strategy objects
2. Instantiate Factor objects from FactorRegistry
3. Build Strategy DAG with proper dependency resolution
4. Safe parameter binding with type validation
5. Clear, actionable error messages with context
6. Integration with existing Factor Graph architecture

Usage Example:
-------------
    from src.tier1.yaml_interpreter import YAMLInterpreter

    # Create interpreter (auto-initializes validator and registry)
    interpreter = YAMLInterpreter()

    # Load YAML file and create Strategy
    strategy = interpreter.from_file("examples/yaml_strategies/momentum_basic.yaml")

    # Validate and execute strategy
    strategy.validate()
    result = strategy.to_pipeline(data)

    # Or interpret from dictionary
    config = {
        "strategy_id": "test-strategy",
        "factors": [
            {"id": "mom", "type": "momentum_factor", "parameters": {"momentum_period": 20}}
        ]
    }
    strategy = interpreter.from_dict(config)
"""

import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path

from src.tier1.yaml_validator import YAMLValidator
from src.tier1.factor_factory import FactorFactory, FactorFactoryError
from src.factor_library import FactorRegistry
from src.factor_graph import Strategy


class InterpretationError(Exception):
    """
    Raised when YAML interpretation fails.

    This exception includes contextual information to help diagnose issues:
    - The specific error that occurred
    - The context where the error happened (file, factor, line, etc.)
    - Suggestions for fixing the problem (when possible)

    Attributes:
        message: Human-readable error message
        context: Dictionary with error context (file, factor_id, etc.)
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """
        Initialize InterpretationError with message and context.

        Args:
            message: Error message describing what went wrong
            context: Dictionary with error context (optional)
                Common keys: 'file', 'factor_id', 'factor_type', 'parameter', 'line'
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """Format error message with context."""
        msg = self.message

        # Add context information if available
        if self.context:
            context_parts = []
            if 'file' in self.context:
                context_parts.append(f"File: {self.context['file']}")
            if 'factor_id' in self.context:
                context_parts.append(f"Factor ID: {self.context['factor_id']}")
            if 'factor_type' in self.context:
                context_parts.append(f"Factor Type: {self.context['factor_type']}")

            if context_parts:
                msg += f"\nContext: {', '.join(context_parts)}"

        return msg


class YAMLInterpreter:
    """
    Interprets validated YAML/JSON strategy configurations into Strategy objects.

    Workflow:
    1. Validate config (using YAMLValidator from D.1)
    2. Create Factor instances (using FactorFactory)
    3. Build Strategy DAG with dependencies
    4. Validate Strategy integrity
    5. Return executable Strategy

    The interpreter provides a safe bridge between declarative YAML configs
    and executable Factor Graph strategies. It handles:
    - Configuration validation
    - Factor instantiation with parameter binding
    - Dependency resolution and DAG construction
    - Comprehensive error handling with actionable messages

    Example:
        >>> interpreter = YAMLInterpreter()
        >>>
        >>> # Load and interpret YAML file
        >>> strategy = interpreter.from_file("examples/yaml_strategies/momentum_basic.yaml")
        >>> strategy.validate()
        True
        >>>
        >>> # Execute strategy pipeline
        >>> result = strategy.to_pipeline(data)
        >>>
        >>> # Interpret from dictionary
        >>> config = {
        ...     "strategy_id": "test-strategy",
        ...     "factors": [
        ...         {
        ...             "id": "momentum_20",
        ...             "type": "momentum_factor",
        ...             "parameters": {"momentum_period": 20}
        ...         }
        ...     ]
        ... }
        >>> strategy = interpreter.from_dict(config)
    """

    def __init__(
        self,
        schema_path: Optional[str] = None,
        registry: Optional[FactorRegistry] = None
    ):
        """
        Initialize YAML interpreter with validator and registry.

        Args:
            schema_path: Path to JSON schema for validation
                If None, uses default schema from src/tier1/yaml_schema.json
            registry: FactorRegistry instance for factor creation
                If None, uses singleton registry instance

        Raises:
            FileNotFoundError: If schema file not found
            json.JSONDecodeError: If schema file is not valid JSON
        """
        # Initialize validator (handles config validation)
        self.validator = YAMLValidator(schema_path)

        # Initialize registry (provides factor metadata and creation)
        self.registry = registry or FactorRegistry.get_instance()

        # Initialize factory (handles factor instantiation)
        self.factory = FactorFactory(self.registry)

    def from_file(self, yaml_path: str) -> Strategy:
        """
        Load and interpret YAML configuration file.

        This method loads a YAML file, validates it against the schema,
        and interprets it into an executable Strategy object.

        Args:
            yaml_path: Path to YAML or JSON configuration file

        Returns:
            Strategy object with all factors configured

        Raises:
            InterpretationError: If file loading, validation, or interpretation fails
                The exception includes context about where the error occurred

        Example:
            >>> interpreter = YAMLInterpreter()
            >>> strategy = interpreter.from_file("examples/yaml_strategies/momentum_basic.yaml")
            >>> print(f"Strategy: {strategy.id}, Factors: {len(strategy.factors)}")
            Strategy: momentum-basic-v1, Factors: 3
        """
        file_path = Path(yaml_path)

        # Step 1: Validate configuration
        try:
            validation_result = self.validator.validate_file(yaml_path)
        except Exception as e:
            raise InterpretationError(
                f"Failed to validate YAML file: {str(e)}",
                context={'file': yaml_path}
            ) from e

        # Check validation result
        if not validation_result.is_valid:
            error_msg = f"Invalid configuration:\n" + "\n".join(
                f"  - {error}" for error in validation_result.errors
            )
            raise InterpretationError(
                error_msg,
                context={'file': yaml_path}
            )

        # Step 2: Interpret validated configuration
        try:
            strategy = self.from_dict(validation_result.config)
        except InterpretationError as e:
            # Add file context if not already present
            if 'file' not in e.context:
                e.context['file'] = yaml_path
            raise
        except Exception as e:
            raise InterpretationError(
                f"Failed to interpret configuration: {str(e)}",
                context={'file': yaml_path}
            ) from e

        return strategy

    def from_dict(self, config: Dict[str, Any]) -> Strategy:
        """
        Interpret configuration dictionary into Strategy object.

        This method takes a validated configuration dictionary and creates
        an executable Strategy with all factors properly configured and
        connected in a DAG.

        Args:
            config: Configuration dictionary (should be pre-validated)

        Returns:
            Strategy object with all factors configured

        Raises:
            InterpretationError: If interpretation fails
                Common causes: unknown factor type, invalid parameters,
                missing dependencies, cycle detection

        Example:
            >>> interpreter = YAMLInterpreter()
            >>> config = {
            ...     "strategy_id": "momentum-basic",
            ...     "factors": [
            ...         {
            ...             "id": "momentum_20",
            ...             "type": "momentum_factor",
            ...             "parameters": {"momentum_period": 20},
            ...             "depends_on": []
            ...         }
            ...     ]
            ... }
            >>> strategy = interpreter.from_dict(config)
            >>> len(strategy.factors)
            1
        """
        # Validate basic structure
        if 'strategy_id' not in config:
            raise InterpretationError("Configuration missing 'strategy_id' field")
        if 'factors' not in config or not config['factors']:
            raise InterpretationError("Configuration missing 'factors' field or factors list is empty")

        # Build strategy
        try:
            strategy = self._build_strategy(config)
        except InterpretationError:
            # Re-raise interpretation errors as-is
            raise
        except Exception as e:
            raise InterpretationError(
                f"Failed to build strategy: {str(e)}",
                context={'strategy_id': config['strategy_id']}
            ) from e

        return strategy

    def _build_strategy(self, config: Dict[str, Any]) -> Strategy:
        """
        Build Strategy from validated configuration.

        This internal method orchestrates strategy construction:
        1. Create Strategy object
        2. Create all Factor instances
        3. Add factors to strategy with dependencies
        4. Validate final strategy structure

        Args:
            config: Validated configuration dictionary

        Returns:
            Strategy object with all factors configured

        Raises:
            InterpretationError: If strategy construction fails
        """
        # Step 1: Create Strategy object
        strategy_id = config['strategy_id']
        description = config.get('description', '')

        try:
            strategy = Strategy(
                id=strategy_id,
                generation=0  # Initial generation for YAML-created strategies
            )
        except Exception as e:
            raise InterpretationError(
                f"Failed to create strategy: {str(e)}",
                context={'strategy_id': strategy_id}
            ) from e

        # Step 2: Create all Factor instances
        factor_configs = config['factors']
        factor_map = {}  # Map factor_id -> Factor instance

        for factor_config in factor_configs:
            factor_id = factor_config['id']
            factor_type = factor_config['type']
            parameters = factor_config.get('parameters', {})
            enabled = factor_config.get('enabled', True)

            # Skip disabled factors
            if not enabled:
                continue

            # Create factor instance
            try:
                factor = self.factory.create_factor(
                    factor_id=factor_id,
                    factor_type=factor_type,
                    parameters=parameters
                )
                factor_map[factor_id] = factor
            except FactorFactoryError as e:
                raise InterpretationError(
                    str(e),
                    context={
                        'strategy_id': strategy_id,
                        'factor_id': factor_id,
                        'factor_type': factor_type
                    }
                ) from e
            except Exception as e:
                raise InterpretationError(
                    f"Failed to create factor: {str(e)}",
                    context={
                        'strategy_id': strategy_id,
                        'factor_id': factor_id,
                        'factor_type': factor_type
                    }
                ) from e

        # Step 3: Add factors to strategy with dependencies
        # We need to add factors in an order that respects dependencies
        # Build a simple dependency order by repeatedly adding factors with satisfied dependencies
        added_factors = set()
        remaining_configs = list(factor_configs)
        max_iterations = len(factor_configs) * 2  # Prevent infinite loop
        iteration = 0

        while remaining_configs and iteration < max_iterations:
            iteration += 1
            made_progress = False

            for factor_config in remaining_configs[:]:  # Iterate over copy
                factor_id = factor_config['id']
                enabled = factor_config.get('enabled', True)

                # Skip disabled factors
                if not enabled:
                    remaining_configs.remove(factor_config)
                    made_progress = True
                    continue

                # Check if factor is already added
                if factor_id in added_factors:
                    remaining_configs.remove(factor_config)
                    made_progress = True
                    continue

                # Check if all dependencies are satisfied
                depends_on = factor_config.get('depends_on', [])
                dependencies_satisfied = all(dep in added_factors for dep in depends_on)

                if dependencies_satisfied:
                    # Add factor to strategy
                    try:
                        factor = factor_map[factor_id]
                        strategy.add_factor(factor, depends_on=depends_on)
                        added_factors.add(factor_id)
                        remaining_configs.remove(factor_config)
                        made_progress = True
                    except Exception as e:
                        raise InterpretationError(
                            f"Failed to add factor to strategy: {str(e)}",
                            context={
                                'strategy_id': strategy_id,
                                'factor_id': factor_id,
                                'depends_on': depends_on
                            }
                        ) from e

            # Check if we made progress
            if not made_progress:
                # No progress means we have unresolvable dependencies
                unresolved_factors = [fc['id'] for fc in remaining_configs]
                raise InterpretationError(
                    f"Cannot resolve dependencies for factors: {unresolved_factors}. "
                    "This may indicate a circular dependency or missing factor.",
                    context={'strategy_id': strategy_id}
                )

        # Check if all factors were added
        if remaining_configs:
            unresolved_factors = [fc['id'] for fc in remaining_configs]
            raise InterpretationError(
                f"Failed to add all factors to strategy. Remaining: {unresolved_factors}",
                context={'strategy_id': strategy_id}
            )

        # Step 4: Validate strategy structure
        try:
            strategy.validate()
        except Exception as e:
            raise InterpretationError(
                f"Strategy validation failed: {str(e)}",
                context={'strategy_id': strategy_id}
            ) from e

        return strategy

    def get_registry(self) -> FactorRegistry:
        """
        Get the FactorRegistry used by this interpreter.

        Returns:
            FactorRegistry instance

        Example:
            >>> interpreter = YAMLInterpreter()
            >>> registry = interpreter.get_registry()
            >>> factor_types = registry.list_factors()
            >>> len(factor_types) >= 13
            True
        """
        return self.registry

    def get_validator(self) -> YAMLValidator:
        """
        Get the YAMLValidator used by this interpreter.

        Returns:
            YAMLValidator instance

        Example:
            >>> interpreter = YAMLInterpreter()
            >>> validator = interpreter.get_validator()
            >>> factor_types = validator.list_factor_types()
            >>> len(factor_types) >= 13
            True
        """
        return self.validator
