"""
Test Suite for StructuredErrorFeedback (TDD RED Phase)

Tests for error formatting and prompt integration.
Following TDD methodology: these tests are written FIRST before implementation.

Requirements: F4.1, F4.2, F4.3, F4.4, AC4
"""

import pytest


class TestValidationErrorDetail:
    """Test suite for ValidationErrorDetail dataclass."""

    def test_validation_error_detail_structure(self):
        """
        GIVEN ValidationErrorDetail with all fields
        WHEN accessing fields
        THEN all fields are accessible
        """
        from src.feedback.structured_error import ValidationErrorDetail

        error = ValidationErrorDetail(
            field_path="params.momentum_period",
            error_type="invalid_value",
            given_value=25,
            allowed_values=[5, 10, 20, 30],
            suggestion="Use 20 (closest valid value)"
        )

        assert error.field_path == "params.momentum_period"
        assert error.error_type == "invalid_value"
        assert error.given_value == 25
        assert error.allowed_values == [5, 10, 20, 30]
        assert error.suggestion == "Use 20 (closest valid value)"

    def test_validation_error_detail_type_error(self):
        """
        GIVEN ValidationErrorDetail for type error
        WHEN creating instance
        THEN stores type error information correctly
        """
        from src.feedback.structured_error import ValidationErrorDetail

        error = ValidationErrorDetail(
            field_path="params.stop_loss",
            error_type="type_error",
            given_value="10%",
            allowed_values=[0.08, 0.10, 0.12, 0.15],
            suggestion="Use 0.10 instead of '10%'"
        )

        assert error.error_type == "type_error"
        assert error.given_value == "10%"


class TestFormatErrors:
    """Test suite for format_errors method."""

    def test_format_single_error(self):
        """
        GIVEN a single ValidationErrorDetail
        WHEN calling format_errors
        THEN returns formatted error string
        """
        from src.feedback.structured_error import (
            StructuredErrorFeedback,
            ValidationErrorDetail
        )

        feedback = StructuredErrorFeedback()
        errors = [
            ValidationErrorDetail(
                field_path="params.momentum_period",
                error_type="invalid_value",
                given_value=25,
                allowed_values=[5, 10, 20, 30],
                suggestion="Use 20 (closest valid value)"
            )
        ]

        result = feedback.format_errors(errors)

        assert isinstance(result, str)
        assert "momentum_period" in result
        assert "25" in result
        assert "5" in result or "10" in result or "20" in result or "30" in result
        assert "20" in result  # suggestion

    def test_format_multiple_errors(self):
        """
        GIVEN multiple ValidationErrorDetail objects
        WHEN calling format_errors
        THEN returns formatted string with all errors
        """
        from src.feedback.structured_error import (
            StructuredErrorFeedback,
            ValidationErrorDetail
        )

        feedback = StructuredErrorFeedback()
        errors = [
            ValidationErrorDetail(
                field_path="params.momentum_period",
                error_type="invalid_value",
                given_value=25,
                allowed_values=[5, 10, 20, 30],
                suggestion="Use 20"
            ),
            ValidationErrorDetail(
                field_path="params.stop_loss",
                error_type="type_error",
                given_value="10%",
                allowed_values=[0.08, 0.10, 0.12, 0.15],
                suggestion="Use 0.10"
            )
        ]

        result = feedback.format_errors(errors)

        assert "momentum_period" in result
        assert "stop_loss" in result
        assert "25" in result
        assert "10%" in result

    def test_format_errors_includes_field_path(self):
        """
        GIVEN ValidationErrorDetail with nested field path
        WHEN calling format_errors
        THEN field path is clearly shown
        """
        from src.feedback.structured_error import (
            StructuredErrorFeedback,
            ValidationErrorDetail
        )

        feedback = StructuredErrorFeedback()
        errors = [
            ValidationErrorDetail(
                field_path="params.catalyst_type",
                error_type="invalid_value",
                given_value="growth",
                allowed_values=["revenue", "earnings"],
                suggestion="Use 'revenue' or 'earnings'"
            )
        ]

        result = feedback.format_errors(errors)

        assert "params.catalyst_type" in result or "catalyst_type" in result

    def test_format_errors_includes_allowed_values(self):
        """
        GIVEN ValidationErrorDetail with allowed values
        WHEN calling format_errors
        THEN allowed values are displayed
        """
        from src.feedback.structured_error import (
            StructuredErrorFeedback,
            ValidationErrorDetail
        )

        feedback = StructuredErrorFeedback()
        errors = [
            ValidationErrorDetail(
                field_path="params.resample",
                error_type="invalid_value",
                given_value="D",
                allowed_values=["W", "M"],
                suggestion="Use 'W' for weekly or 'M' for monthly"
            )
        ]

        result = feedback.format_errors(errors)

        # Should show allowed values
        assert "W" in result
        assert "M" in result

    def test_format_errors_includes_suggestion(self):
        """
        GIVEN ValidationErrorDetail with suggestion
        WHEN calling format_errors
        THEN suggestion is included in output
        """
        from src.feedback.structured_error import (
            StructuredErrorFeedback,
            ValidationErrorDetail
        )

        feedback = StructuredErrorFeedback()
        errors = [
            ValidationErrorDetail(
                field_path="reasoning",
                error_type="string_too_short",
                given_value="Short",
                allowed_values=[],
                suggestion="Provide at least 50 characters of reasoning"
            )
        ]

        result = feedback.format_errors(errors)

        assert "50" in result or "characters" in result.lower()


class TestIntegrateWithPrompt:
    """Test suite for integrate_with_prompt method."""

    def test_integrate_appends_to_original_prompt(self):
        """
        GIVEN original prompt and error feedback
        WHEN calling integrate_with_prompt
        THEN returns combined prompt with errors appended
        """
        from src.feedback.structured_error import (
            StructuredErrorFeedback,
            ValidationErrorDetail
        )

        feedback = StructuredErrorFeedback()
        original_prompt = "Generate strategy parameters for momentum strategy."
        errors = [
            ValidationErrorDetail(
                field_path="params.momentum_period",
                error_type="invalid_value",
                given_value=25,
                allowed_values=[5, 10, 20, 30],
                suggestion="Use 20"
            )
        ]

        result = feedback.integrate_with_prompt(original_prompt, errors)

        # Original prompt should be present
        assert "Generate strategy parameters" in result
        # Error information should be present
        assert "momentum_period" in result
        assert "25" in result

    def test_integrate_maintains_original_prompt(self):
        """
        GIVEN original prompt
        WHEN calling integrate_with_prompt
        THEN original prompt is preserved intact
        """
        from src.feedback.structured_error import (
            StructuredErrorFeedback,
            ValidationErrorDetail
        )

        feedback = StructuredErrorFeedback()
        original_prompt = "This is the original prompt with specific instructions."
        errors = [
            ValidationErrorDetail(
                field_path="params.n_stocks",
                error_type="invalid_value",
                given_value=7,
                allowed_values=[5, 10, 15, 20],
                suggestion="Use 5 or 10"
            )
        ]

        result = feedback.integrate_with_prompt(original_prompt, errors)

        assert "original prompt with specific instructions" in result

    def test_integrate_format_is_llm_friendly(self):
        """
        GIVEN errors
        WHEN calling integrate_with_prompt
        THEN format uses clear headers and structure for LLM
        """
        from src.feedback.structured_error import (
            StructuredErrorFeedback,
            ValidationErrorDetail
        )

        feedback = StructuredErrorFeedback()
        original_prompt = "Generate params."
        errors = [
            ValidationErrorDetail(
                field_path="params.momentum_period",
                error_type="invalid_value",
                given_value=25,
                allowed_values=[5, 10, 20, 30],
                suggestion="Use 20"
            )
        ]

        result = feedback.integrate_with_prompt(original_prompt, errors)

        # Should have clear section markers
        assert "ERROR" in result.upper() or "VALIDATION" in result.upper()
        # Should request correction
        assert "correct" in result.lower() or "fix" in result.lower()


class TestFromPydanticError:
    """Test suite for creating ValidationErrorDetail from Pydantic errors."""

    def test_from_pydantic_literal_error(self):
        """
        GIVEN Pydantic ValidationError for literal field
        WHEN calling from_pydantic_error
        THEN creates ValidationErrorDetail with correct info
        """
        from src.feedback.structured_error import StructuredErrorFeedback
        from src.schemas.strategy_params import MomentumStrategyParams
        from pydantic import ValidationError

        try:
            MomentumStrategyParams(
                momentum_period=25,  # Invalid
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )
        except ValidationError as e:
            feedback = StructuredErrorFeedback()
            error_details = feedback.from_pydantic_error(e)

            assert len(error_details) >= 1
            error = error_details[0]
            assert "momentum_period" in error.field_path
            assert error.given_value == 25

    def test_from_pydantic_missing_field_error(self):
        """
        GIVEN Pydantic ValidationError for missing field
        WHEN calling from_pydantic_error
        THEN creates ValidationErrorDetail with missing error type
        """
        from src.feedback.structured_error import StructuredErrorFeedback
        from src.schemas.strategy_params import MomentumStrategyParams
        from pydantic import ValidationError

        try:
            MomentumStrategyParams(
                # momentum_period missing
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )
        except ValidationError as e:
            feedback = StructuredErrorFeedback()
            error_details = feedback.from_pydantic_error(e)

            assert len(error_details) >= 1
            error = error_details[0]
            assert "momentum_period" in error.field_path
            assert error.error_type == "missing_field"
