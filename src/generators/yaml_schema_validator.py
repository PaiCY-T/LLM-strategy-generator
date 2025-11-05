"""
YAML Schema Validator Module

Validates YAML strategy specifications against the JSON Schema.
Provides clear error messages with field paths for debugging.

Task 2 of structured-innovation-mvp spec.
Requirements: 2.1 (YAML validation), 2.2 (error reporting)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import yaml

try:
    from jsonschema import Draft7Validator, ValidationError as JSONSchemaValidationError
    from jsonschema.exceptions import best_match
except ImportError:
    raise ImportError(
        "jsonschema library required. Install with: pip install jsonschema"
    )

logger = logging.getLogger(__name__)


class YAMLSchemaValidator:
    """
    Validates YAML strategy specifications against JSON Schema.

    Features:
    - Schema validation with draft-07 support
    - Clear error messages with field paths
    - YAML parsing error handling
    - Schema caching for performance
    - Multiple validation modes (strict, permissive)

    Example:
        validator = YAMLSchemaValidator()
        is_valid, errors = validator.validate(yaml_spec)
        if not is_valid:
            for error in errors:
                print(f"Validation error: {error}")
    """

    def __init__(
        self,
        schema_path: Optional[Path] = None,
        strict_mode: bool = True,
        use_pydantic: bool = True
    ):
        """
        Initialize the YAML schema validator.

        Args:
            schema_path: Path to JSON Schema file. If None, uses default path.
            strict_mode: If True, require all recommended fields. If False, only required fields.
            use_pydantic: If True, enable Pydantic validation when normalize=True. If False, use JSON Schema only.
        """
        self.strict_mode = strict_mode
        self.use_pydantic = use_pydantic
        self._schema: Optional[Dict] = None
        self._validator: Optional[Draft7Validator] = None
        self._pydantic_validator = None

        # Set default schema path if not provided
        if schema_path is None:
            # Default to schemas/strategy_schema_v1.json in project root
            current_dir = Path(__file__).resolve()
            project_root = current_dir.parent.parent.parent
            schema_path = project_root / "schemas" / "strategy_schema_v1.json"

        self.schema_path = Path(schema_path)

        # Load and cache schema
        self._load_schema()

        # Initialize Pydantic validator if enabled (lazy import for optional dependency)
        if self.use_pydantic:
            try:
                from src.generators.pydantic_validator import PydanticValidator
                self._pydantic_validator = PydanticValidator()
                logger.info("Pydantic validator enabled for enhanced validation")
            except ImportError:
                logger.warning("Pydantic validator not available. Install pydantic for enhanced validation.")
                self.use_pydantic = False

    def _load_schema(self) -> None:
        """
        Load and cache the JSON Schema.

        Raises:
            FileNotFoundError: If schema file doesn't exist
            json.JSONDecodeError: If schema file is invalid JSON
        """
        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Schema file not found: {self.schema_path}\n"
                f"Expected location: schemas/strategy_schema_v1.json"
            )

        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self._schema = json.load(f)

            # Create validator with schema
            self._validator = Draft7Validator(self._schema)

            logger.info(f"Loaded JSON Schema from {self.schema_path}")

        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in schema file: {e.msg}",
                e.doc,
                e.pos
            )

    def validate(
        self,
        yaml_spec: Dict[str, Any],
        return_detailed_errors: bool = True,
        normalize: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Validate a parsed YAML specification against the schema.

        Args:
            yaml_spec: Parsed YAML specification as dictionary
            return_detailed_errors: If True, return detailed error messages with paths
            normalize: If True, apply YAML normalization before validation (Task 4 integration)

        Returns:
            Tuple of (is_valid, error_messages)
            - is_valid: True if validation passes
            - error_messages: List of error messages (empty if valid)

        Example:
            >>> validator = YAMLSchemaValidator()
            >>> spec = {'metadata': {'name': 'Test', 'strategy_type': 'momentum'}}
            >>> is_valid, errors = validator.validate(spec)
            >>> print(is_valid)
            False
            >>> print(errors[0])
            metadata: 'rebalancing_frequency' is a required property
        """
        if self._validator is None:
            raise RuntimeError("Schema not loaded. Call _load_schema() first.")

        # Step 1: Apply normalization if requested (requirement 3.1)
        if normalize:
            try:
                from src.generators.yaml_normalizer import normalize_yaml
                from src.utils.exceptions import NormalizationError

                yaml_spec = normalize_yaml(yaml_spec)
                logger.info("YAML normalization successful")

            except NormalizationError as e:
                # Graceful degradation: log warning and continue with original YAML (requirement 3.2)
                logger.warning(f"Normalization failed: {e}. Falling back to direct validation.")

            except Exception as e:
                # Unexpected error: log error and continue (requirement 3.2)
                logger.error(f"Unexpected normalization error: {e}. Falling back to direct validation.")

            # Step 2: Apply Pydantic validation if normalize=True and Pydantic is available (Task 5)
            if self.use_pydantic and self._pydantic_validator is not None:
                try:
                    strategy_instance, pydantic_errors = self._pydantic_validator.validate(yaml_spec)

                    if strategy_instance is not None:
                        # Pydantic validation successful
                        logger.info("Pydantic validation successful")
                        return True, []
                    else:
                        # Pydantic validation failed - return formatted errors
                        logger.warning(f"Pydantic validation failed with {len(pydantic_errors)} error(s)")
                        return False, pydantic_errors

                except Exception as e:
                    # Unexpected error in Pydantic validation - fall back to JSON Schema
                    logger.error(f"Unexpected Pydantic validation error: {e}. Falling back to JSON Schema validation.")

        errors = []

        # Check for basic structure
        if not isinstance(yaml_spec, dict):
            return False, ["YAML specification must be a dictionary/object"]

        # Collect all validation errors
        validation_errors = sorted(
            self._validator.iter_errors(yaml_spec),
            key=lambda e: e.path
        )

        if not validation_errors:
            logger.info("YAML specification is valid")
            return True, []

        # Convert validation errors to readable messages
        for error in validation_errors:
            error_msg = self._format_error(error, return_detailed_errors)
            errors.append(error_msg)

        logger.warning(f"YAML validation failed with {len(errors)} error(s)")
        return False, errors

    def load_and_validate(
        self,
        yaml_path: str,
        return_detailed_errors: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Load YAML file and validate against schema.

        Args:
            yaml_path: Path to YAML file
            return_detailed_errors: If True, return detailed error messages

        Returns:
            Tuple of (is_valid, error_messages)

        Example:
            >>> validator = YAMLSchemaValidator()
            >>> is_valid, errors = validator.load_and_validate('strategy.yaml')
            >>> if not is_valid:
            ...     for error in errors:
            ...         print(f"Error: {error}")
        """
        yaml_path = Path(yaml_path)

        # Check if file exists
        if not yaml_path.exists():
            return False, [f"YAML file not found: {yaml_path}"]

        # Try to load YAML file
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_spec = yaml.safe_load(f)
        except yaml.YAMLError as e:
            error_msg = f"YAML parsing error in {yaml_path}: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]
        except Exception as e:
            error_msg = f"Error reading file {yaml_path}: {str(e)}"
            logger.error(error_msg)
            return False, [error_msg]

        # Validate the loaded spec
        return self.validate(yaml_spec, return_detailed_errors)

    def get_validation_errors(
        self,
        spec: Dict[str, Any]
    ) -> List[str]:
        """
        Get only the validation error messages (without success/failure bool).

        Args:
            spec: Parsed YAML specification

        Returns:
            List of error messages (empty if valid)

        Example:
            >>> validator = YAMLSchemaValidator()
            >>> errors = validator.get_validation_errors(spec)
            >>> for error in errors:
            ...     print(f"Validation error: {error}")
        """
        _, errors = self.validate(spec, return_detailed_errors=True)
        return errors

    def _format_error(
        self,
        error: JSONSchemaValidationError,
        detailed: bool = True
    ) -> str:
        """
        Format a validation error into a readable message with field path.

        Args:
            error: JSONSchema validation error
            detailed: If True, include detailed context

        Returns:
            Formatted error message string
        """
        # Build field path from error path
        path_parts = list(error.absolute_path)
        if path_parts:
            field_path = ".".join(str(part) for part in path_parts)
        else:
            field_path = "(root)"

        # Get the error message
        error_message = error.message

        # Format based on error type
        if error.validator == "required":
            # Missing required field
            missing_field = error.message.split("'")[1]
            if field_path == "(root)":
                return f"Missing required field: '{missing_field}'"
            else:
                return f"{field_path}: Missing required field '{missing_field}'"

        elif error.validator == "enum":
            # Invalid enum value
            allowed = error.validator_value
            return f"{field_path}: {error_message}. Allowed values: {allowed}"

        elif error.validator == "type":
            # Wrong type
            expected_type = error.validator_value
            return f"{field_path}: Expected type '{expected_type}', got {type(error.instance).__name__}"

        elif error.validator == "pattern":
            # Pattern mismatch
            pattern = error.validator_value
            return f"{field_path}: Value '{error.instance}' does not match required pattern: {pattern}"

        elif error.validator in ("minimum", "maximum"):
            # Numeric bounds
            limit = error.validator_value
            return f"{field_path}: {error_message} (limit: {limit})"

        elif error.validator in ("minLength", "maxLength"):
            # String length
            limit = error.validator_value
            return f"{field_path}: {error_message} (limit: {limit} characters)"

        elif error.validator in ("minItems", "maxItems"):
            # Array size
            limit = error.validator_value
            return f"{field_path}: {error_message} (limit: {limit} items)"

        elif error.validator == "minProperties":
            # Minimum properties in object
            return f"{field_path}: Must have at least {error.validator_value} properties"

        elif error.validator == "additionalProperties":
            # Extra properties not allowed
            return f"{field_path}: Additional properties not allowed. Found unexpected field."

        else:
            # Generic error
            if detailed:
                return f"{field_path}: {error_message}"
            else:
                return error_message

    def validate_indicator_references(
        self,
        spec: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all indicator references in conditions exist in indicators section.

        This is a semantic validation beyond JSON Schema (cross-field validation).

        Args:
            spec: Parsed YAML specification

        Returns:
            Tuple of (is_valid, error_messages)

        Example:
            >>> validator = YAMLSchemaValidator()
            >>> is_valid, errors = validator.validate_indicator_references(spec)
            >>> if not is_valid:
            ...     print(f"Reference errors: {errors}")
        """
        errors = []

        # Get all defined indicator names
        defined_indicators = set()
        indicators = spec.get("indicators", {})

        # Collect technical indicators
        for tech in indicators.get("technical_indicators", []):
            if "name" in tech:
                defined_indicators.add(tech["name"])

        # Collect fundamental factors
        for fund in indicators.get("fundamental_factors", []):
            if "name" in fund:
                defined_indicators.add(fund["name"])

        # Collect custom calculations
        for calc in indicators.get("custom_calculations", []):
            if "name" in calc:
                defined_indicators.add(calc["name"])

        # Collect volume filters
        for vol in indicators.get("volume_filters", []):
            if "name" in vol:
                defined_indicators.add(vol["name"])

        # Check entry conditions ranking rules
        entry = spec.get("entry_conditions", {})
        # entry_conditions can be either object or array per schema
        if isinstance(entry, dict):
            for rank_rule in entry.get("ranking_rules", []):
                field = rank_rule.get("field")
                if field and field not in defined_indicators:
                    errors.append(
                        f"entry_conditions.ranking_rules: Field '{field}' not found in indicators"
                    )
        elif isinstance(entry, list):
            # Array format - check field references in array items
            for condition in entry:
                if isinstance(condition, dict):
                    field = condition.get("field")
                    if field and field not in defined_indicators:
                        errors.append(
                            f"entry_conditions: Field '{field}' not found in indicators"
                        )

        # Check position sizing weighting field
        position_sizing = spec.get("position_sizing", {})
        if position_sizing.get("method") == "factor_weighted":
            weight_field = position_sizing.get("weighting_field")
            if weight_field and weight_field not in defined_indicators:
                errors.append(
                    f"position_sizing.weighting_field: Field '{weight_field}' not found in indicators"
                )

        if errors:
            return False, errors
        else:
            return True, []

    @property
    def schema(self) -> Dict:
        """Get the loaded JSON Schema."""
        return self._schema

    @property
    def schema_version(self) -> str:
        """Get the schema version."""
        return self._schema.get("version", "unknown")
