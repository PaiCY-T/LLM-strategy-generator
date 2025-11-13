"""
Pydantic Validator Module

Wraps Pydantic Strategy model for YAML validation with detailed error messages.
Provides type-safe validation with field paths for debugging.

Task 4 of yaml-normalizer-phase2-complete-normalization spec.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import logging
from typing import Dict, Any, List, Tuple, Optional

try:
    from pydantic import ValidationError
except ImportError:
    raise ImportError(
        "pydantic library required. Install with: pip install pydantic"
    )

from src.models.strategy_models import StrategySpecification

logger = logging.getLogger(__name__)


class PydanticValidator:
    """
    Validates YAML strategy specifications using Pydantic models.

    Provides type-safe validation with detailed error messages showing field paths.
    This is a wrapper around the StrategySpecification Pydantic model to provide
    a consistent API with YAMLSchemaValidator.

    Features:
    - Type-safe validation via Pydantic
    - Detailed error messages with field paths
    - Cross-field validation (indicator references)
    - Automatic type coercion where appropriate
    - Double-insurance for name and type normalization

    Example:
        validator = PydanticValidator()
        strategy, errors = validator.validate(yaml_spec)
        if strategy is None:
            for error in errors:
                print(f"Validation error: {error}")
        else:
            print(f"Valid strategy: {strategy.metadata.name}")
    """

    def __init__(self):
        """Initialize the Pydantic validator."""
        self.model = StrategySpecification
        logger.info("PydanticValidator initialized with StrategySpecification model")

    def validate(
        self,
        yaml_spec: Dict[str, Any]
    ) -> Tuple[Optional[StrategySpecification], List[str]]:
        """
        Validate a parsed YAML specification using Pydantic.

        Args:
            yaml_spec: Parsed YAML specification as dictionary

        Returns:
            Tuple of (strategy_instance, error_messages)
            - strategy_instance: StrategySpecification instance if valid, None if invalid
            - error_messages: List of formatted error messages (empty if valid)

        Example:
            >>> validator = PydanticValidator()
            >>> spec = {
            ...     "metadata": {
            ...         "name": "Test Strategy",
            ...         "strategy_type": "momentum",
            ...         "rebalancing_frequency": "M"
            ...     },
            ...     "indicators": {
            ...         "technical_indicators": [
            ...             {"name": "rsi", "type": "RSI", "period": 14}
            ...         ]
            ...     },
            ...     "entry_conditions": {
            ...         "threshold_rules": [{"condition": "rsi < 30"}]
            ...     }
            ... }
            >>> strategy, errors = validator.validate(spec)
            >>> if strategy:
            ...     print(f"Valid: {strategy.metadata.name}")
            ... else:
            ...     print(f"Errors: {errors}")
        """
        # Check for basic structure
        if not isinstance(yaml_spec, dict):
            error_msg = "YAML specification must be a dictionary/object"
            logger.warning(error_msg)
            return None, [error_msg]

        # Attempt Pydantic validation
        try:
            strategy = self.model(**yaml_spec)
            logger.info(f"YAML specification is valid: {strategy.metadata.name}")
            return strategy, []

        except ValidationError as e:
            # Format Pydantic validation errors
            errors = self._format_pydantic_errors(e)
            logger.warning(f"Pydantic validation failed with {len(errors)} error(s)")
            return None, errors

        except Exception as e:
            # Catch unexpected errors
            error_msg = f"Unexpected validation error: {str(e)}"
            logger.error(error_msg)
            return None, [error_msg]

    def _format_pydantic_errors(self, validation_error: ValidationError) -> List[str]:
        """
        Format Pydantic validation errors into readable messages with field paths.

        Args:
            validation_error: Pydantic ValidationError exception

        Returns:
            List of formatted error messages

        Requirements: 2.2 (Clear error messages with field paths)
        """
        formatted_errors = []

        for error in validation_error.errors():
            # Build field path from error location
            field_path = self._build_field_path(error.get('loc', ()))
            error_type = error.get('type', 'unknown')
            error_msg = error.get('msg', 'Validation error')
            error_ctx = error.get('ctx', {})

            # Format based on error type (requirement 2.2)
            formatted_msg = self._format_error_by_type(
                field_path, error_type, error_msg, error_ctx
            )
            formatted_errors.append(formatted_msg)

        return formatted_errors

    def _build_field_path(self, location: tuple) -> str:
        """
        Build a readable field path from Pydantic error location.

        Args:
            location: Tuple of location parts from Pydantic error

        Returns:
            Formatted field path string (e.g., "metadata.name", "indicators.0.type")

        Example:
            >>> _build_field_path(('metadata', 'name'))
            'metadata.name'
            >>> _build_field_path(('indicators', 0, 'type'))
            'indicators.0.type'
        """
        if not location:
            return "(root)"

        path_parts = []
        for part in location:
            if isinstance(part, int):
                # Array index
                path_parts.append(f"[{part}]")
            else:
                # Field name
                if path_parts and not path_parts[-1].startswith('['):
                    path_parts.append('.')
                path_parts.append(str(part))

        return ''.join(path_parts)

    def _format_error_by_type(
        self,
        field_path: str,
        error_type: str,
        error_msg: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Format error message based on error type for better readability.

        Args:
            field_path: Field path (e.g., "metadata.name")
            error_type: Pydantic error type (e.g., "missing", "string_type")
            error_msg: Original error message
            context: Error context dictionary

        Returns:
            Formatted error message string

        Requirement 2.2: Clear, actionable error messages
        """
        # Missing field errors
        if error_type in ('missing', 'value_error.missing'):
            return f"{field_path}: Field required but missing"

        # Type errors
        elif error_type.startswith('type_error') or '_type' in error_type:
            expected = context.get('expected_type', 'unknown')
            return f"{field_path}: Invalid type. {error_msg}"

        # String pattern/format errors
        elif error_type in ('string_pattern_mismatch', 'value_error.str.regex'):
            pattern = context.get('pattern', 'unknown pattern')
            return f"{field_path}: Value does not match required pattern {pattern}"

        # Enum/literal errors
        elif error_type in ('enum', 'literal_error', 'type_error.enum'):
            allowed = context.get('expected', context.get('permitted', 'unknown values'))
            return f"{field_path}: Invalid value. {error_msg}. Allowed values: {allowed}"

        # Numeric constraint errors
        elif error_type.startswith('greater_than'):
            limit = context.get('gt', context.get('ge', 'unknown'))
            return f"{field_path}: Value must be greater than {limit}"

        elif error_type.startswith('less_than'):
            limit = context.get('lt', context.get('le', 'unknown'))
            return f"{field_path}: Value must be less than {limit}"

        # String length errors
        elif error_type.startswith('string_too'):
            min_len = context.get('min_length')
            max_len = context.get('max_length')
            if min_len is not None:
                return f"{field_path}: String too short (minimum {min_len} characters)"
            elif max_len is not None:
                return f"{field_path}: String too long (maximum {max_len} characters)"

        # List length errors
        elif error_type.startswith('list_'):
            if 'max_length' in context:
                return f"{field_path}: Too many items (maximum {context['max_length']})"
            elif 'min_length' in context:
                return f"{field_path}: Too few items (minimum {context['min_length']})"

        # Value errors (custom validators)
        elif error_type.startswith('value_error'):
            return f"{field_path}: {error_msg}"

        # Assertion errors (model validators)
        elif error_type == 'assertion_error':
            return f"{field_path}: Validation failed - {error_msg}"

        # Generic fallback
        else:
            return f"{field_path}: {error_msg}"

    def get_model_schema(self) -> Dict[str, Any]:
        """
        Get the JSON schema representation of the Pydantic model.

        Returns:
            Dictionary containing the model's JSON schema

        Example:
            >>> validator = PydanticValidator()
            >>> schema = validator.get_model_schema()
            >>> print(schema.keys())
            dict_keys(['title', 'type', 'properties', 'required'])
        """
        return self.model.model_json_schema()

    def validate_and_raise(self, yaml_spec: Dict[str, Any]) -> StrategySpecification:
        """
        Validate YAML spec and raise exception if invalid.

        Useful for scenarios where you want exception-based error handling
        instead of tuple return values.

        Args:
            yaml_spec: Parsed YAML specification as dictionary

        Returns:
            StrategySpecification instance if valid

        Raises:
            ValidationError: If validation fails

        Example:
            >>> validator = PydanticValidator()
            >>> try:
            ...     strategy = validator.validate_and_raise(spec)
            ...     print(f"Valid: {strategy.metadata.name}")
            ... except ValidationError as e:
            ...     print(f"Invalid: {e}")
        """
        return self.model(**yaml_spec)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_yaml_with_pydantic(
    yaml_spec: Dict[str, Any]
) -> Tuple[Optional[StrategySpecification], List[str]]:
    """
    Convenience function for one-off Pydantic validation.

    Args:
        yaml_spec: Parsed YAML specification as dictionary

    Returns:
        Tuple of (strategy_instance, error_messages)

    Example:
        >>> from src.generators.pydantic_validator import validate_yaml_with_pydantic
        >>> strategy, errors = validate_yaml_with_pydantic(yaml_spec)
        >>> if strategy:
        ...     print("Valid!")
    """
    validator = PydanticValidator()
    return validator.validate(yaml_spec)
