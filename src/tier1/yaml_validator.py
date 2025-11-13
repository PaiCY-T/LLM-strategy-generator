"""
YAML Strategy Configuration Validator
======================================

Validates YAML/JSON strategy configurations against JSON Schema and business rules.
Provides comprehensive validation including dependency checking, factor existence,
and parameter bounds validation.

Architecture: Structural Mutation Phase 2 - Phase D.1
Task: D.1 - YAML Schema Design and Validator

Features:
---------
1. JSON Schema validation for structure and types
2. Dependency cycle detection using graph analysis
3. Factor type existence checking against FactorRegistry
4. Parameter bounds validation using registry metadata
5. Clear, actionable error messages with context
6. Support for both YAML and JSON formats

Usage Example:
-------------
    from src.tier1.yaml_validator import YAMLValidator

    # Create validator
    validator = YAMLValidator()

    # Validate YAML file
    result = validator.validate_file("strategy.yaml")
    if result.is_valid:
        print(f"Valid strategy: {result.config['strategy_id']}")
    else:
        for error in result.errors:
            print(f"Error: {error}")

    # Validate dictionary directly
    config = {
        "strategy_id": "my-strategy",
        "factors": [...]
    }
    result = validator.validate(config)
"""

import json
import yaml
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from pathlib import Path
import networkx as nx
from jsonschema import validate, ValidationError as JSONSchemaValidationError, Draft7Validator


@dataclass
class ValidationResult:
    """
    Result of configuration validation.

    Attributes:
        is_valid: True if configuration passes all validation checks
        errors: List of error messages (empty if valid)
        warnings: List of warning messages (non-blocking issues)
        config: The validated configuration dictionary (None if validation fails)
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    config: Optional[Dict[str, Any]] = None

    def __bool__(self) -> bool:
        """Allow truthiness checking: if result: ..."""
        return self.is_valid

    def __str__(self) -> str:
        """Human-readable string representation."""
        if self.is_valid:
            status = "VALID"
            details = f"Strategy: {self.config.get('strategy_id', 'unknown')}"
            if self.config:
                details += f", Factors: {len(self.config.get('factors', []))}"
            if self.warnings:
                details += f", Warnings: {len(self.warnings)}"
            return f"[{status}] {details}"
        else:
            status = "INVALID"
            details = f"{len(self.errors)} error(s)"
            return f"[{status}] {details}"


class YAMLValidator:
    """
    Validates YAML/JSON strategy configurations against schema and business rules.

    Performs multi-stage validation:
    1. JSON Schema validation (structure, types, required fields)
    2. Custom business rules (dependencies, factor existence)
    3. Parameter validation (bounds checking using registry)

    The validator uses jsonschema for structural validation and implements
    custom logic for domain-specific rules like dependency cycle detection
    and factor registry validation.

    Example:
        >>> validator = YAMLValidator()
        >>> result = validator.validate_file("examples/yaml_strategies/momentum_basic.yaml")
        >>> if result.is_valid:
        ...     print(f"Valid: {result.config['strategy_id']}")
        ... else:
        ...     for error in result.errors:
        ...         print(f"Error: {error}")
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize YAMLValidator with schema.

        Args:
            schema_path: Path to JSON schema file. If None, uses default schema
                        from src/tier1/yaml_schema.json

        Raises:
            FileNotFoundError: If schema file not found
            json.JSONDecodeError: If schema file is not valid JSON
        """
        if schema_path is None:
            # Default to schema in same directory
            schema_path = Path(__file__).parent / "yaml_schema.json"
        else:
            schema_path = Path(schema_path)

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, 'r', encoding='utf-8') as f:
            self.schema = json.load(f)

        # Create validator for better error messages
        self.validator = Draft7Validator(self.schema)

        # Cache for factor registry (lazy loaded)
        self._registry = None

    @property
    def registry(self):
        """Lazy-load FactorRegistry to avoid circular imports."""
        if self._registry is None:
            from src.factor_library.registry import FactorRegistry
            self._registry = FactorRegistry.get_instance()
        return self._registry

    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate configuration dictionary against schema and business rules.

        Performs comprehensive validation including:
        - JSON Schema validation (structure, types, required fields)
        - Dependency cycle detection
        - Factor type existence checking
        - Parameter bounds validation
        - Duplicate factor ID detection

        Args:
            config: Configuration dictionary to validate

        Returns:
            ValidationResult with validation status, errors, warnings, and config

        Example:
            >>> validator = YAMLValidator()
            >>> config = {
            ...     "strategy_id": "test-strategy",
            ...     "factors": [
            ...         {"id": "mom", "type": "momentum_factor", "parameters": {"momentum_period": 20}}
            ...     ]
            ... }
            >>> result = validator.validate(config)
            >>> result.is_valid
            True
        """
        errors = []
        warnings = []

        # Stage 1: JSON Schema validation
        schema_errors = self._validate_schema(config)
        if schema_errors:
            return ValidationResult(
                is_valid=False,
                errors=schema_errors,
                warnings=warnings,
                config=None
            )

        # Stage 2: Custom business rule validation
        factors = config.get('factors', [])

        # Check for duplicate factor IDs
        duplicate_errors = self._check_duplicate_ids(factors)
        errors.extend(duplicate_errors)

        # Check dependencies
        dependency_errors = self._validate_dependencies(factors)
        errors.extend(dependency_errors)

        # Check factor types exist in registry
        factor_type_errors = self._validate_factor_types(factors)
        errors.extend(factor_type_errors)

        # Stage 3: Parameter validation (only if no critical errors so far)
        if not errors:
            param_errors, param_warnings = self._validate_parameters(factors)
            errors.extend(param_errors)
            warnings.extend(param_warnings)

        # Build result
        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            config=config if is_valid else None
        )

    def validate_file(self, yaml_path: str) -> ValidationResult:
        """
        Validate YAML/JSON configuration file.

        Loads configuration from file and validates it. Supports both YAML and JSON formats.
        File format is detected by extension (.yaml, .yml, .json).

        Args:
            yaml_path: Path to YAML or JSON configuration file

        Returns:
            ValidationResult with validation status and details

        Raises:
            FileNotFoundError: If file does not exist (wrapped in ValidationResult)
            yaml.YAMLError: If YAML parsing fails (wrapped in ValidationResult)
            json.JSONDecodeError: If JSON parsing fails (wrapped in ValidationResult)

        Example:
            >>> validator = YAMLValidator()
            >>> result = validator.validate_file("examples/yaml_strategies/momentum_basic.yaml")
            >>> if result.is_valid:
            ...     print(f"Strategy: {result.config['strategy_id']}")
        """
        file_path = Path(yaml_path)

        # Check file exists
        if not file_path.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"File not found: {yaml_path}"],
                warnings=[],
                config=None
            )

        # Load configuration
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Detect format by extension
                if file_path.suffix.lower() == '.json':
                    config = json.load(f)
                else:
                    # Default to YAML for .yaml, .yml, and unknown extensions
                    config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"YAML parsing error: {str(e)}"],
                warnings=[],
                config=None
            )
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"JSON parsing error: {str(e)}"],
                warnings=[],
                config=None
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Error loading file: {str(e)}"],
                warnings=[],
                config=None
            )

        # Validate loaded configuration
        return self.validate(config)

    def _validate_schema(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate configuration against JSON schema.

        Args:
            config: Configuration dictionary

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Use Draft7Validator for better error messages
        for error in self.validator.iter_errors(config):
            # Build path to error location
            path = " -> ".join(str(p) for p in error.path) if error.path else "root"

            # Format error message
            message = f"Schema error at '{path}': {error.message}"
            errors.append(message)

        return errors

    def _check_duplicate_ids(self, factors: List[Dict[str, Any]]) -> List[str]:
        """
        Check for duplicate factor IDs.

        Args:
            factors: List of factor configurations

        Returns:
            List of error messages for duplicate IDs
        """
        errors = []
        seen_ids = set()

        for factor in factors:
            factor_id = factor.get('id')
            if factor_id in seen_ids:
                errors.append(f"Duplicate factor ID: '{factor_id}' (each factor must have unique ID)")
            seen_ids.add(factor_id)

        return errors

    def _validate_dependencies(self, factors: List[Dict[str, Any]]) -> List[str]:
        """
        Validate factor dependencies.

        Checks:
        1. All dependency references exist (refer to valid factor IDs)
        2. No circular dependencies (dependency graph is acyclic - DAG)

        Args:
            factors: List of factor configurations

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Build factor ID set
        factor_ids = {factor['id'] for factor in factors}

        # Check dependency references exist
        for factor in factors:
            factor_id = factor['id']
            depends_on = factor.get('depends_on', [])

            for dep_id in depends_on:
                if dep_id not in factor_ids:
                    errors.append(
                        f"Factor '{factor_id}' depends on non-existent factor '{dep_id}'"
                    )

        # Check for circular dependencies using graph analysis
        if not errors:  # Only check cycles if references are valid
            cycle_error = self._detect_dependency_cycles(factors)
            if cycle_error:
                errors.append(cycle_error)

        return errors

    def _detect_dependency_cycles(self, factors: List[Dict[str, Any]]) -> Optional[str]:
        """
        Detect circular dependencies in factor dependency graph.

        Uses networkx to build directed graph and detect cycles.
        A cycle means factors have circular dependencies, which is invalid.

        Args:
            factors: List of factor configurations

        Returns:
            Error message describing cycle if found, None otherwise
        """
        # Build directed graph
        G = nx.DiGraph()

        # Add nodes
        for factor in factors:
            G.add_node(factor['id'])

        # Add edges (dependency -> dependent)
        for factor in factors:
            factor_id = factor['id']
            depends_on = factor.get('depends_on', [])
            for dep_id in depends_on:
                # Edge from dependency to dependent
                G.add_edge(dep_id, factor_id)

        # Check for cycles
        try:
            cycle = nx.find_cycle(G, orientation='original')
            # Format cycle for error message
            cycle_path = " -> ".join(edge[0] for edge in cycle) + f" -> {cycle[0][0]}"
            return f"Circular dependency detected: {cycle_path}"
        except nx.NetworkXNoCycle:
            # No cycle found - this is good!
            return None

    def _validate_factor_types(self, factors: List[Dict[str, Any]]) -> List[str]:
        """
        Validate that all factor types exist in FactorRegistry.

        Args:
            factors: List of factor configurations

        Returns:
            List of error messages for unknown factor types
        """
        errors = []

        # Get registered factor types
        registered_types = set(self.registry.list_factors())

        for factor in factors:
            factor_id = factor['id']
            factor_type = factor['type']

            if factor_type not in registered_types:
                available = ", ".join(sorted(registered_types))
                errors.append(
                    f"Factor '{factor_id}' has unknown type '{factor_type}'. "
                    f"Available types: {available}"
                )

        return errors

    def _validate_parameters(
        self,
        factors: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[str]]:
        """
        Validate factor parameters against registry metadata.

        Checks:
        1. All required parameters are present
        2. Parameter values are within valid ranges
        3. Parameter types match expected types

        Args:
            factors: List of factor configurations

        Returns:
            Tuple of (errors, warnings)
            - errors: List of critical parameter errors
            - warnings: List of non-critical parameter warnings
        """
        errors = []
        warnings = []

        for factor in factors:
            factor_id = factor['id']
            factor_type = factor['type']
            parameters = factor.get('parameters', {})

            # Get metadata from registry
            metadata = self.registry.get_metadata(factor_type)
            if not metadata:
                # This should have been caught by _validate_factor_types
                continue

            # Check required parameters
            expected_params = set(metadata['parameters'].keys())
            provided_params = set(parameters.keys())

            missing_params = expected_params - provided_params
            if missing_params:
                errors.append(
                    f"Factor '{factor_id}' (type: {factor_type}) missing required parameters: "
                    f"{', '.join(sorted(missing_params))}"
                )

            # Check for unknown parameters
            unknown_params = provided_params - expected_params
            if unknown_params:
                warnings.append(
                    f"Factor '{factor_id}' (type: {factor_type}) has unknown parameters: "
                    f"{', '.join(sorted(unknown_params))} (will be ignored)"
                )

            # Validate parameter bounds using registry
            is_valid, error_msg = self.registry.validate_parameters(factor_type, parameters)
            if not is_valid:
                errors.append(f"Factor '{factor_id}' (type: {factor_type}): {error_msg}")

        return errors, warnings

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get information about the schema.

        Returns:
            Dictionary with schema metadata:
            - title: Schema title
            - description: Schema description
            - version: Schema version (from $id)
            - factor_types: List of supported factor types
        """
        factor_types = self.schema['definitions']['Factor']['properties']['type']['enum']

        return {
            'title': self.schema.get('title', 'Unknown'),
            'description': self.schema.get('description', ''),
            'version': self.schema.get('$id', 'unknown'),
            'factor_types': sorted(factor_types),
            'max_factors': self.schema['properties']['factors']['maxItems']
        }

    def list_factor_types(self) -> List[str]:
        """
        Get list of supported factor types from schema.

        Returns:
            List of factor type names
        """
        return sorted(
            self.schema['definitions']['Factor']['properties']['type']['enum']
        )

    def get_parameter_schema(self, factor_type: str) -> Optional[Dict[str, Any]]:
        """
        Get parameter schema for a specific factor type.

        Args:
            factor_type: Factor type name

        Returns:
            Parameter schema dictionary, or None if type not found
        """
        param_schemas = self.schema['definitions'].get('parameter_schemas', {})
        return param_schemas.get(factor_type)
