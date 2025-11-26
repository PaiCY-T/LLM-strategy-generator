"""
Strategy Configuration Data Structures

Defines dataclasses for strategy configuration parsing and validation.
These structures support the YAML-based strategy schema defined in
src/config/strategy_schema.yaml and integrate with Layer 1 field manifest.

Task: 18.3 - Define StrategyConfig Data Structure
Integration: Layer 1 (FieldMetadata), Layer 2 (Field Validation)

Data Structures:
    - FieldMapping: Maps canonical fields to aliases with usage documentation
    - ParameterConfig: Strategy parameter with type, range, and default values
    - LogicConfig: Entry/exit logic with dependencies
    - ConstraintConfig: Validation constraints with severity levels
    - StrategyConfig: Complete strategy configuration (main structure)

Usage:
    from src.execution.strategy_config import StrategyConfig, FieldMapping
    from src.config.field_metadata import FieldMetadata

    # Define field mapping
    field = FieldMapping(
        canonical_name="price:收盤價",
        alias="close",
        usage="Signal generation - momentum calculation"
    )

    # Create parameter config
    param = ParameterConfig(
        name="momentum_period",
        type="integer",
        value=20,
        default=20,
        range=(10, 60),
        unit="trading_days"
    )

    # Build complete config
    config = StrategyConfig(
        name="Pure Momentum",
        type="momentum",
        description="Fast breakout strategy",
        fields=[field],
        parameters=[param],
        logic=LogicConfig(...),
        constraints=[...]
    )

See Also:
    - src/config/strategy_schema.yaml: YAML schema definition
    - src/config/field_metadata.py: Layer 1 field metadata
    - tests/execution/test_strategy_config.py: Comprehensive tests
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple, Dict, Union


@dataclass
class FieldMapping:
    """
    Maps a canonical field name to an alias with usage documentation.

    Integrates with Layer 1 FieldMetadata to ensure canonical names are valid
    and aliases are recognized. Used in strategy configuration to document
    which fields are required/optional and how they're used.

    Attributes:
        canonical_name: Canonical finlab API field name (e.g., "price:收盤價")
                       Must match Layer 1 FieldMetadata.canonical_name
        alias: Alias used in strategy logic (e.g., "close", "volume")
               Must be in Layer 1 FieldMetadata.aliases list
        usage: Human-readable description of field usage in strategy
               (e.g., "Signal generation - momentum calculation")

    Example:
        >>> field = FieldMapping(
        ...     canonical_name="price:收盤價",
        ...     alias="close",
        ...     usage="Signal generation - momentum calculation"
        ... )
        >>> assert field.canonical_name == "price:收盤價"
        >>> assert field.alias == "close"

    Validation:
        - canonical_name must be non-empty string
        - alias must be non-empty string
        - usage must be non-empty string (documentation requirement)

    Integration:
        - Layer 1: canonical_name validated against DataFieldManifest
        - Layer 2: alias resolved via FieldValidator.resolve_alias()
        - Execution: Used to build field lookup tables for strategy code
    """

    canonical_name: str
    alias: str
    usage: str

    def __post_init__(self):
        """
        Validate FieldMapping after initialization.

        Raises:
            ValueError: If any required field is empty or invalid
        """
        if not self.canonical_name or not isinstance(self.canonical_name, str):
            raise ValueError(
                f"canonical_name must be a non-empty string, got: {self.canonical_name}"
            )

        if not self.alias or not isinstance(self.alias, str):
            raise ValueError(f"alias must be a non-empty string, got: {self.alias}")

        if not self.usage or not isinstance(self.usage, str):
            raise ValueError(f"usage must be a non-empty string, got: {self.usage}")


@dataclass
class ParameterConfig:
    """
    Strategy parameter configuration with type, value, range, and metadata.

    Defines a configurable parameter for strategy execution with validation
    constraints. Supports integer, float, boolean, and string types with
    optional range validation for numeric types.

    Attributes:
        name: Parameter name (e.g., "momentum_period", "entry_threshold")
        type: Parameter data type ("integer", "float", "boolean", "string")
        value: Current parameter value (must match type)
        default: Default parameter value (must match type)
        range: Optional (min, max) tuple for numeric validation
               Required for integer/float types
        unit: Optional unit descriptor (e.g., "trading_days", "percentage")

    Example:
        >>> param = ParameterConfig(
        ...     name="momentum_period",
        ...     type="integer",
        ...     value=20,
        ...     default=20,
        ...     range=(10, 60),
        ...     unit="trading_days"
        ... )
        >>> assert param.name == "momentum_period"
        >>> assert param.value == 20
        >>> assert param.is_in_range()

    Validation:
        - name must be non-empty string
        - type must be in {"integer", "float", "boolean", "string"}
        - value must match specified type
        - default must match specified type
        - range required for numeric types (integer, float)
        - value must be within range if specified

    Methods:
        is_in_range(): Check if value is within valid range
        validate_type(val): Validate that a value matches parameter type
    """

    name: str
    type: str  # "integer", "float", "boolean", "string"
    value: Any
    default: Any
    range: Optional[Tuple[Union[int, float], Union[int, float]]] = None
    unit: Optional[str] = None

    def __post_init__(self):
        """
        Validate ParameterConfig after initialization.

        Raises:
            ValueError: If any field is invalid or type mismatches
        """
        # Validate name
        if not self.name or not isinstance(self.name, str):
            raise ValueError(f"name must be a non-empty string, got: {self.name}")

        # Validate type
        valid_types = {"integer", "float", "boolean", "string"}
        if self.type not in valid_types:
            raise ValueError(f"type must be one of {valid_types}, got: {self.type}")

        # Validate value matches type
        if not self.validate_type(self.value):
            raise ValueError(
                f"value {self.value} does not match type {self.type}"
            )

        # Validate default matches type
        if not self.validate_type(self.default):
            raise ValueError(
                f"default {self.default} does not match type {self.type}"
            )

        # Validate range for numeric types
        if self.type in {"integer", "float"}:
            if self.range is None:
                raise ValueError(
                    f"range is required for numeric type {self.type}"
                )

            if not isinstance(self.range, tuple) or len(self.range) != 2:
                raise ValueError(
                    f"range must be a tuple of (min, max), got: {self.range}"
                )

            min_val, max_val = self.range
            if not isinstance(min_val, (int, float)) or not isinstance(
                max_val, (int, float)
            ):
                raise ValueError(
                    f"range values must be numeric, got: {self.range}"
                )

            if min_val >= max_val:
                raise ValueError(
                    f"range min must be less than max, got: {self.range}"
                )

        # Validate value is in range
        if not self.is_in_range():
            raise ValueError(
                f"value {self.value} is not in valid range {self.range}"
            )

    def validate_type(self, val: Any) -> bool:
        """
        Validate that a value matches the parameter type.

        Args:
            val: Value to validate

        Returns:
            True if value matches type, False otherwise

        Example:
            >>> param = ParameterConfig(
            ...     name="test", type="integer", value=10, default=5, range=(1, 100)
            ... )
            >>> param.validate_type(20)
            True
            >>> param.validate_type(20.5)
            False
        """
        if self.type == "integer":
            return isinstance(val, int) and not isinstance(val, bool)
        elif self.type == "float":
            return isinstance(val, (int, float)) and not isinstance(val, bool)
        elif self.type == "boolean":
            return isinstance(val, bool)
        elif self.type == "string":
            return isinstance(val, str)
        return False

    def is_in_range(self) -> bool:
        """
        Check if current value is within valid range.

        Returns:
            True if value is in range (or no range specified), False otherwise

        Example:
            >>> param = ParameterConfig(
            ...     name="threshold", type="float", value=0.5,
            ...     default=0.5, range=(0.0, 1.0)
            ... )
            >>> param.is_in_range()
            True
        """
        if self.range is None:
            return True

        min_val, max_val = self.range
        try:
            numeric_value = float(self.value)
            return min_val <= numeric_value <= max_val
        except (ValueError, TypeError):
            return False


@dataclass
class LogicConfig:
    """
    Strategy entry/exit logic configuration with dependencies.

    Defines the entry and exit logic for strategy execution including
    formula descriptions and data field dependencies. Used to validate
    that all required fields are available before strategy execution.

    Attributes:
        entry: Entry logic description or formula
               Can be human-readable description or Python expression
        exit: Exit logic description or formula
              Use "None" or empty string for strategies without explicit exits
        dependencies: List of canonical field names required for logic
                     Must match Layer 1 canonical names (e.g., "price:收盤價")

    Example:
        >>> logic = LogicConfig(
        ...     entry="(price.pct_change(20) > 0.02) & (volume > 1000000)",
        ...     exit="price < peak_price * 0.9",
        ...     dependencies=["price:收盤價", "price:成交金額"]
        ... )
        >>> assert len(logic.dependencies) == 2

    Validation:
        - entry must be non-empty string
        - exit must be a string (can be empty for no exit logic)
        - dependencies must be a list of strings
        - Each dependency should be a valid canonical field name

    Integration:
        - Layer 1: dependencies validated against DataFieldManifest
        - Execution: Used to ensure required data is loaded before execution
    """

    entry: str
    exit: str
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self):
        """
        Validate LogicConfig after initialization.

        Raises:
            ValueError: If any field is invalid
        """
        # Validate entry
        if not self.entry or not isinstance(self.entry, str):
            raise ValueError(f"entry must be a non-empty string, got: {self.entry}")

        # Validate exit (can be empty string or "None" for no exit logic)
        if not isinstance(self.exit, str):
            raise ValueError(f"exit must be a string, got: {self.exit}")

        # Validate dependencies
        if not isinstance(self.dependencies, list):
            raise ValueError(
                f"dependencies must be a list, got: {self.dependencies}"
            )

        if not all(isinstance(dep, str) for dep in self.dependencies):
            raise ValueError(f"all dependencies must be strings")

        if not all(dep.strip() for dep in self.dependencies):
            raise ValueError(f"dependencies cannot contain empty strings")


@dataclass
class ConstraintConfig:
    """
    Validation constraint configuration with severity level.

    Defines a validation constraint for strategy execution with severity
    classification. Used to enforce data quality, parameter validity,
    logic correctness, and performance requirements.

    Attributes:
        type: Constraint category
              One of: "data_quality", "parameter", "logic", "performance"
        condition: Constraint condition or check description
                  Human-readable or evaluable expression
        severity: Severity level - "critical", "high", "medium", "low", "warning"
        message: Optional custom error message for constraint violations
        tolerance: Optional tolerance for numeric comparisons (default: 0.0)
        max_nan_pct: Optional maximum NaN percentage for data quality (0.0-1.0)

    Example:
        >>> constraint = ConstraintConfig(
        ...     type="parameter",
        ...     condition="momentum_period > 0",
        ...     severity="critical",
        ...     message="Momentum period must be positive"
        ... )
        >>> assert constraint.severity == "critical"

    Validation:
        - type must be valid constraint category
        - condition must be non-empty string
        - severity must be valid severity level
        - tolerance must be non-negative if specified
        - max_nan_pct must be in [0.0, 1.0] if specified

    Constraint Types:
        - data_quality: Data integrity checks (NaN, outliers, consistency)
        - parameter: Parameter range and validity checks
        - logic: Strategy logic correctness checks
        - performance: Performance requirements and thresholds
    """

    type: str  # "data_quality", "parameter", "logic", "performance"
    condition: str
    severity: str  # "critical", "high", "medium", "low", "warning"
    message: Optional[str] = None
    tolerance: float = 0.0
    max_nan_pct: Optional[float] = None

    def __post_init__(self):
        """
        Validate ConstraintConfig after initialization.

        Raises:
            ValueError: If any field is invalid
        """
        # Validate type
        valid_types = {"data_quality", "parameter", "logic", "performance"}
        if self.type not in valid_types:
            raise ValueError(f"type must be one of {valid_types}, got: {self.type}")

        # Validate condition
        if not self.condition or not isinstance(self.condition, str):
            raise ValueError(
                f"condition must be a non-empty string, got: {self.condition}"
            )

        # Validate severity
        valid_severities = {"critical", "high", "medium", "low", "warning"}
        if self.severity not in valid_severities:
            raise ValueError(
                f"severity must be one of {valid_severities}, got: {self.severity}"
            )

        # Validate tolerance
        if not isinstance(self.tolerance, (int, float)):
            raise ValueError(
                f"tolerance must be numeric, got: {self.tolerance}"
            )

        if self.tolerance < 0:
            raise ValueError(
                f"tolerance must be non-negative, got: {self.tolerance}"
            )

        # Validate max_nan_pct if specified
        if self.max_nan_pct is not None:
            if not isinstance(self.max_nan_pct, (int, float)):
                raise ValueError(
                    f"max_nan_pct must be numeric, got: {self.max_nan_pct}"
                )

            if not 0.0 <= self.max_nan_pct <= 1.0:
                raise ValueError(
                    f"max_nan_pct must be in [0.0, 1.0], got: {self.max_nan_pct}"
                )


@dataclass
class StrategyConfig:
    """
    Complete strategy configuration data structure.

    Main dataclass for strategy configuration supporting YAML-based strategy
    schema definition. Integrates with Layer 1 field manifest for field
    validation and provides comprehensive parameter and constraint validation.

    Attributes:
        name: Strategy name (e.g., "Pure Momentum", "Turtle Breakout")
        type: Strategy type/pattern (e.g., "momentum", "breakout", "hybrid")
        description: Human-readable strategy description
        fields: List of FieldMapping objects (required + optional fields)
        parameters: List of ParameterConfig objects
        logic: LogicConfig for entry/exit logic
        constraints: List of ConstraintConfig objects
        coverage: Optional pattern coverage percentage (0.0-1.0)
        metadata: Optional additional metadata dictionary

    Example:
        >>> from src.execution.strategy_config import (
        ...     StrategyConfig, FieldMapping, ParameterConfig,
        ...     LogicConfig, ConstraintConfig
        ... )
        >>>
        >>> config = StrategyConfig(
        ...     name="Pure Momentum",
        ...     type="momentum",
        ...     description="Fast breakout strategy",
        ...     fields=[
        ...         FieldMapping(
        ...             canonical_name="price:收盤價",
        ...             alias="close",
        ...             usage="Signal generation"
        ...         )
        ...     ],
        ...     parameters=[
        ...         ParameterConfig(
        ...             name="momentum_period",
        ...             type="integer",
        ...             value=20,
        ...             default=20,
        ...             range=(10, 60),
        ...             unit="trading_days"
        ...         )
        ...     ],
        ...     logic=LogicConfig(
        ...         entry="close.pct_change(20) > 0.02",
        ...         exit="None",
        ...         dependencies=["price:收盤價"]
        ...     ),
        ...     constraints=[
        ...         ConstraintConfig(
        ...             type="parameter",
        ...             condition="momentum_period > 0",
        ...             severity="critical"
        ...         )
        ...     ]
        ... )
        >>> assert config.name == "Pure Momentum"
        >>> assert len(config.fields) == 1

    Validation:
        - name must be non-empty string
        - type must be non-empty string
        - description must be non-empty string
        - fields must be non-empty list of FieldMapping objects
        - parameters must be list of ParameterConfig objects
        - logic must be LogicConfig object
        - constraints must be list of ConstraintConfig objects
        - coverage must be in [0.0, 1.0] if specified

    Integration:
        - Layer 1: Field mappings validated against DataFieldManifest
        - Layer 2: Constraints enforced via FieldValidator
        - Execution: Used to configure strategy execution engine

    See Also:
        - src/config/strategy_schema.yaml: YAML schema definition
        - tests/execution/test_strategy_config.py: Comprehensive tests
    """

    name: str
    type: str
    description: str
    fields: List[FieldMapping]
    parameters: List[ParameterConfig]
    logic: LogicConfig
    constraints: List[ConstraintConfig]
    coverage: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """
        Validate StrategyConfig after initialization.

        Raises:
            ValueError: If any field is invalid or violates constraints
        """
        # Validate name
        if not self.name or not isinstance(self.name, str):
            raise ValueError(f"name must be a non-empty string, got: {self.name}")

        # Validate type
        if not self.type or not isinstance(self.type, str):
            raise ValueError(f"type must be a non-empty string, got: {self.type}")

        # Validate description
        if not self.description or not isinstance(self.description, str):
            raise ValueError(
                f"description must be a non-empty string, got: {self.description}"
            )

        # Validate fields
        if not self.fields or not isinstance(self.fields, list):
            raise ValueError(
                f"fields must be a non-empty list, got: {self.fields}"
            )

        if not all(isinstance(f, FieldMapping) for f in self.fields):
            raise ValueError(f"all fields must be FieldMapping objects")

        # Validate parameters
        if not isinstance(self.parameters, list):
            raise ValueError(
                f"parameters must be a list, got: {self.parameters}"
            )

        if not all(isinstance(p, ParameterConfig) for p in self.parameters):
            raise ValueError(f"all parameters must be ParameterConfig objects")

        # Validate logic
        if not isinstance(self.logic, LogicConfig):
            raise ValueError(
                f"logic must be a LogicConfig object, got: {self.logic}"
            )

        # Validate constraints
        if not isinstance(self.constraints, list):
            raise ValueError(
                f"constraints must be a list, got: {self.constraints}"
            )

        if not all(isinstance(c, ConstraintConfig) for c in self.constraints):
            raise ValueError(f"all constraints must be ConstraintConfig objects")

        # Validate coverage if specified
        if self.coverage is not None:
            if not isinstance(self.coverage, (int, float)):
                raise ValueError(
                    f"coverage must be numeric, got: {self.coverage}"
                )

            if not 0.0 <= self.coverage <= 1.0:
                raise ValueError(
                    f"coverage must be in [0.0, 1.0], got: {self.coverage}"
                )

        # Validate metadata if specified
        if self.metadata is not None:
            if not isinstance(self.metadata, dict):
                raise ValueError(
                    f"metadata must be a dictionary, got: {self.metadata}"
                )

    def get_required_fields(self) -> List[str]:
        """
        Get list of canonical field names required by this strategy.

        Returns:
            List of canonical field names from all FieldMappings

        Example:
            >>> config = StrategyConfig(...)
            >>> fields = config.get_required_fields()
            >>> assert "price:收盤價" in fields
        """
        return [f.canonical_name for f in self.fields]

    def get_parameter_by_name(self, name: str) -> Optional[ParameterConfig]:
        """
        Get parameter configuration by name.

        Args:
            name: Parameter name to search for

        Returns:
            ParameterConfig object if found, None otherwise

        Example:
            >>> config = StrategyConfig(...)
            >>> param = config.get_parameter_by_name("momentum_period")
            >>> assert param is not None
            >>> assert param.value == 20
        """
        for param in self.parameters:
            if param.name == name:
                return param
        return None

    def get_critical_constraints(self) -> List[ConstraintConfig]:
        """
        Get all critical severity constraints.

        Returns:
            List of ConstraintConfig objects with severity="critical"

        Example:
            >>> config = StrategyConfig(...)
            >>> critical = config.get_critical_constraints()
            >>> assert all(c.severity == "critical" for c in critical)
        """
        return [c for c in self.constraints if c.severity == "critical"]

    def validate_dependencies(self) -> bool:
        """
        Validate that all logic dependencies are in field mappings.

        Checks that every field referenced in logic.dependencies has a
        corresponding FieldMapping in the fields list.

        Returns:
            True if all dependencies are satisfied, False otherwise

        Example:
            >>> config = StrategyConfig(...)
            >>> assert config.validate_dependencies()
        """
        available_fields = set(self.get_required_fields())
        required_deps = set(self.logic.dependencies)
        return required_deps.issubset(available_fields)


# Module-level type hints for better IDE support
StrategyConfigDict = Dict[str, Any]
FieldMappingDict = Dict[str, str]
ParameterConfigDict = Dict[str, Any]
