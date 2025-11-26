"""
StructuredErrorFeedback - Generate LLM-friendly error feedback

This module provides structured error formatting for validation failures,
making it easy for LLMs to understand and correct their parameter outputs.

Requirements: F4.1, F4.2, F4.3, F4.4, AC4
"""

from dataclasses import dataclass
from typing import Any, List, Optional

from pydantic import ValidationError

from src.schemas.param_constants import PARAM_ALLOWED_VALUES


@dataclass
class ValidationErrorDetail:
    """
    Single validation error with context.

    Attributes:
        field_path: Dot-separated path to the field (e.g., "params.momentum_period")
        error_type: Type of error ("invalid_value", "missing_field", "type_error")
        given_value: The value that was provided by the LLM
        allowed_values: List of valid options for this field
        suggestion: Human-readable fix suggestion
    """
    field_path: str
    error_type: str
    given_value: Any
    allowed_values: List[Any]
    suggestion: str


class StructuredErrorFeedback:
    """
    Generates LLM-friendly error feedback.

    This class formats validation errors into clear, actionable feedback
    that helps LLMs understand what went wrong and how to fix it.
    """

    # Use centralized param constants (DRY)
    PARAM_ALLOWED_VALUES = PARAM_ALLOWED_VALUES

    def format_errors(self, errors: List[ValidationErrorDetail]) -> str:
        """
        Format errors as retry prompt.

        Args:
            errors: List of ValidationErrorDetail objects

        Returns:
            str: Formatted error string for LLM consumption
        """
        lines = ["## VALIDATION ERRORS (Please Fix)\n"]

        for i, error in enumerate(errors, 1):
            lines.append(f"{i}. **{error.field_path}**: {error.error_type.replace('_', ' ').title()}")
            lines.append(f"   - Given: {error.given_value}")

            if error.allowed_values:
                lines.append(f"   - Allowed: {error.allowed_values}")

            lines.append(f"   - Suggestion: {error.suggestion}")
            lines.append("")

        lines.append("Please output corrected JSON with valid values.")

        return "\n".join(lines)

    def integrate_with_prompt(
        self,
        original_prompt: str,
        errors: List[ValidationErrorDetail]
    ) -> str:
        """
        Add error feedback to next LLM prompt.

        Combines the original prompt with structured error feedback
        to create a retry prompt that guides the LLM to correct its output.

        Args:
            original_prompt: The original generation prompt
            errors: List of validation errors to include

        Returns:
            str: Combined prompt with error feedback appended
        """
        error_feedback = self.format_errors(errors)

        combined_prompt = f"""{original_prompt}

---

{error_feedback}"""

        return combined_prompt

    def from_pydantic_error(self, error: ValidationError) -> List[ValidationErrorDetail]:
        """
        Convert Pydantic ValidationError to list of ValidationErrorDetail.

        Args:
            error: Pydantic ValidationError

        Returns:
            List[ValidationErrorDetail]: Converted error details
        """
        error_details = []

        for err in error.errors():
            # Build field path from location
            field_path = ".".join(str(loc) for loc in err['loc'])
            error_type = err['type']

            # Extract given value from input
            given_value = err.get('input', None)

            # Get allowed values for this field
            field_name = str(err['loc'][-1]) if err['loc'] else ""
            allowed_values = self.PARAM_ALLOWED_VALUES.get(field_name, [])

            # Determine error type and suggestion
            if error_type == 'literal_error':
                error_type_str = "invalid_value"
                suggestion = self._generate_suggestion_for_literal(
                    field_name, given_value, allowed_values
                )
            elif error_type == 'missing':
                error_type_str = "missing_field"
                suggestion = f"Please provide a value for {field_name}. Allowed: {allowed_values}"
            elif 'type' in error_type:
                error_type_str = "type_error"
                suggestion = f"Expected a value from {allowed_values}"
            elif error_type == 'string_too_short':
                error_type_str = "string_too_short"
                suggestion = "Provide at least 50 characters of reasoning"
                allowed_values = []
            elif error_type == 'string_too_long':
                error_type_str = "string_too_long"
                suggestion = "Limit reasoning to 500 characters"
                allowed_values = []
            else:
                error_type_str = error_type
                suggestion = err.get('msg', 'Please correct this value')

            error_detail = ValidationErrorDetail(
                field_path=field_path,
                error_type=error_type_str,
                given_value=given_value,
                allowed_values=allowed_values,
                suggestion=suggestion
            )
            error_details.append(error_detail)

        return error_details

    def _generate_suggestion_for_literal(
        self,
        field_name: str,
        given_value: Any,
        allowed_values: List[Any]
    ) -> str:
        """
        Generate a suggestion for invalid literal values.

        Attempts to find the closest valid value if possible.

        Args:
            field_name: Name of the field
            given_value: The invalid value that was provided
            allowed_values: List of valid options

        Returns:
            str: Suggestion message
        """
        if not allowed_values:
            return f"Please provide a valid value for {field_name}"

        # Try to find closest value for numeric fields
        if isinstance(given_value, (int, float)) and all(
            isinstance(v, (int, float)) for v in allowed_values
        ):
            closest = min(allowed_values, key=lambda x: abs(x - given_value))
            return f"Use {closest} (closest valid value)"

        # For non-numeric, just show options
        return f"Use one of: {allowed_values}"
