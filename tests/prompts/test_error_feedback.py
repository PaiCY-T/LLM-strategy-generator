"""
Tests for Error Feedback Loop - Task 24.3
TDD implementation for LLM config generation validation retry mechanism

Test Coverage:
1. format_validation_errors() function
2. generate_retry_prompt() function
3. ErrorFeedbackLoop class
4. Integration with SchemaValidator
5. Max retry enforcement
6. Error history tracking
"""

import pytest
from typing import List, Dict, Optional, Tuple, Callable
from unittest.mock import Mock, MagicMock

from src.execution.schema_validator import (
    SchemaValidator,
    ValidationError,
    ValidationSeverity
)


class TestFormatValidationErrors:
    """Test format_validation_errors() function - RED phase"""

    def test_format_single_error(self):
        """Should format single error with all fields"""
        from src.prompts.error_feedback import format_validation_errors

        errors = [
            ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Missing required key: 'name'",
                field_path="<root>",
                line_number=1,
                suggestion="Add 'name' to the top level of your YAML"
            )
        ]

        result = format_validation_errors(errors)

        # Should include all error details
        assert "ERROR" in result
        assert "Missing required key: 'name'" in result
        assert "Field: <root>" in result
        assert "Line: 1" in result
        assert "Suggestion: Add 'name'" in result

    def test_format_multiple_errors_grouped_by_severity(self):
        """Should group errors by severity (ERROR, WARNING, INFO)"""
        from src.prompts.error_feedback import format_validation_errors

        errors = [
            ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Missing required key: 'name'",
                field_path="<root>"
            ),
            ValidationError(
                severity=ValidationSeverity.WARNING,
                message="Unknown key: 'extra_field'",
                field_path="<root>"
            ),
            ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Invalid type for 'type'",
                field_path="type"
            ),
            ValidationError(
                severity=ValidationSeverity.INFO,
                message="Consider adding description",
                field_path="description"
            )
        ]

        result = format_validation_errors(errors)

        # Should group by severity
        assert "=== ERRORS (2) ===" in result
        assert "=== WARNINGS (1) ===" in result
        assert "=== INFO (1) ===" in result

        # Errors should appear first
        error_pos = result.index("=== ERRORS")
        warning_pos = result.index("=== WARNINGS")
        info_pos = result.index("=== INFO")
        assert error_pos < warning_pos < info_pos

    def test_format_errors_without_line_numbers(self):
        """Should handle errors without line numbers gracefully"""
        from src.prompts.error_feedback import format_validation_errors

        errors = [
            ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Invalid field type",
                field_path="parameters[0].type",
                line_number=None,
                suggestion=None
            )
        ]

        result = format_validation_errors(errors)

        # Should not include Line/Suggestion when None
        assert "Invalid field type" in result
        assert "Field: parameters[0].type" in result
        assert "Line:" not in result
        assert "Suggestion:" not in result

    def test_format_empty_errors_list(self):
        """Should return empty string for empty errors list"""
        from src.prompts.error_feedback import format_validation_errors

        result = format_validation_errors([])
        assert result == ""

    def test_format_suggestions_when_available(self):
        """Should include suggestions when available"""
        from src.prompts.error_feedback import format_validation_errors

        errors = [
            ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Invalid strategy type: 'invalid'",
                field_path="type",
                suggestion="Valid types are: factor_graph, llm_generated, hybrid"
            )
        ]

        result = format_validation_errors(errors)

        assert "Suggestion: Valid types are:" in result
        assert "factor_graph" in result


class TestGenerateRetryPrompt:
    """Test generate_retry_prompt() function - RED phase"""

    def test_generate_basic_retry_prompt(self):
        """Should generate retry prompt with original YAML and errors"""
        from src.prompts.error_feedback import generate_retry_prompt

        original_yaml = """
name: Test Strategy
type: invalid_type
required_fields: []
"""
        errors = [
            ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Invalid strategy type: 'invalid_type'",
                field_path="type",
                suggestion="Valid types are: factor_graph, llm_generated, hybrid"
            )
        ]

        result = generate_retry_prompt(original_yaml, errors, attempt_number=1)

        # Should include original YAML
        assert "name: Test Strategy" in result
        assert "type: invalid_type" in result

        # Should include error details
        assert "Invalid strategy type" in result
        assert "Valid types are:" in result

        # Should include attempt number
        assert "Attempt: 1" in result or "retry" in result.lower()

    def test_retry_prompt_shows_remaining_attempts(self):
        """Should show remaining attempts in retry prompt"""
        from src.prompts.error_feedback import generate_retry_prompt

        original_yaml = "name: Test"
        errors = [
            ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Missing required key: 'type'",
                field_path="<root>"
            )
        ]

        result = generate_retry_prompt(original_yaml, errors, attempt_number=2)

        # Should indicate this is attempt 2
        assert "2" in result

    def test_retry_prompt_includes_fix_instructions(self):
        """Should include clear instructions for fixing issues"""
        from src.prompts.error_feedback import generate_retry_prompt

        original_yaml = "name: Test"
        errors = [
            ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Missing required key: 'type'",
                field_path="<root>",
                suggestion="Add 'type' to the top level of your YAML"
            )
        ]

        result = generate_retry_prompt(original_yaml, errors, attempt_number=1)

        # Should have instructions to fix
        assert "fix" in result.lower() or "correct" in result.lower()
        assert "Add 'type'" in result

    def test_retry_prompt_requests_yaml_output(self):
        """Should explicitly request YAML output"""
        from src.prompts.error_feedback import generate_retry_prompt

        original_yaml = "name: Test"
        errors = [
            ValidationError(
                severity=ValidationSeverity.ERROR,
                message="Missing required key: 'type'",
                field_path="<root>"
            )
        ]

        result = generate_retry_prompt(original_yaml, errors, attempt_number=1)

        # Should request YAML format
        assert "yaml" in result.lower() or "YAML" in result


class TestErrorFeedbackLoop:
    """Test ErrorFeedbackLoop class - RED phase"""

    def test_feedback_loop_initialization(self):
        """Should initialize with max_retries parameter"""
        from src.prompts.error_feedback import ErrorFeedbackLoop

        loop = ErrorFeedbackLoop(max_retries=3)
        assert loop.max_retries == 3

    def test_feedback_loop_default_max_retries(self):
        """Should default to 3 retries"""
        from src.prompts.error_feedback import ErrorFeedbackLoop

        loop = ErrorFeedbackLoop()
        assert loop.max_retries == 3

    def test_validate_and_retry_with_valid_yaml_first_attempt(self):
        """Should return success on first attempt with valid YAML"""
        from src.prompts.error_feedback import ErrorFeedbackLoop

        # Create valid YAML
        yaml_str = """
name: "Test Strategy"
type: "factor_graph"
required_fields: ["price:收盤價"]
parameters:
  - name: "period"
    type: "int"
    value: 20
logic:
  entry: "close > 100"
  exit: "close < 90"
"""

        validator = SchemaValidator()
        llm_generate_mock = Mock()  # Should not be called

        loop = ErrorFeedbackLoop(max_retries=3)
        success, validated_config, error_history = loop.validate_and_retry(
            yaml_str,
            validator,
            llm_generate_mock
        )

        # Should succeed on first attempt
        assert success is True
        assert validated_config is not None
        assert validated_config["name"] == "Test Strategy"
        assert len(error_history) == 0  # No errors
        assert llm_generate_mock.call_count == 0  # No retry needed

    def test_validate_and_retry_with_invalid_yaml_retries(self):
        """Should retry with feedback when YAML is invalid"""
        from src.prompts.error_feedback import ErrorFeedbackLoop
        import yaml

        # First attempt: invalid YAML
        invalid_yaml = """
name: "Test Strategy"
type: "invalid_type"
required_fields: []
"""

        # Second attempt: valid YAML (LLM fixes the error)
        valid_yaml = """
name: "Test Strategy"
type: "factor_graph"
required_fields: ["price:收盤價"]
parameters:
  - name: "period"
    type: "int"
    value: 20
logic:
  entry: "close > 100"
  exit: "close < 90"
"""

        validator = SchemaValidator()

        # Mock LLM generate function - returns valid YAML on retry
        llm_generate_mock = Mock(return_value=valid_yaml)

        loop = ErrorFeedbackLoop(max_retries=3)
        success, validated_config, error_history = loop.validate_and_retry(
            invalid_yaml,
            validator,
            llm_generate_mock
        )

        # Should succeed after retry
        assert success is True
        assert validated_config is not None
        assert validated_config["type"] == "factor_graph"

        # Should have called LLM once for retry
        assert llm_generate_mock.call_count == 1

        # Should track error from first attempt
        assert len(error_history) >= 1
        # Error should mention validation failure (could be invalid_type, missing parameters, etc.)
        assert "error" in error_history[0].lower() or "missing" in error_history[0].lower()

    def test_validate_and_retry_max_retries_exceeded(self):
        """Should stop after max_retries and return failure"""
        from src.prompts.error_feedback import ErrorFeedbackLoop

        # Always invalid YAML
        invalid_yaml = """
name: "Test Strategy"
type: "invalid_type"
"""

        validator = SchemaValidator()

        # Mock LLM that keeps returning invalid YAML
        llm_generate_mock = Mock(return_value=invalid_yaml)

        loop = ErrorFeedbackLoop(max_retries=2)
        success, validated_config, error_history = loop.validate_and_retry(
            invalid_yaml,
            validator,
            llm_generate_mock
        )

        # Should fail after max retries
        assert success is False
        assert validated_config is None

        # Should have retried max_retries times
        assert llm_generate_mock.call_count == 2

        # Should track errors from all attempts
        assert len(error_history) >= 2

    def test_validate_and_retry_error_history_tracking(self):
        """Should track all errors in error_history"""
        from src.prompts.error_feedback import ErrorFeedbackLoop

        # First: missing type
        yaml_attempt_1 = """
name: "Test Strategy"
required_fields: []
parameters: []
logic:
  entry: "test"
  exit: "test"
"""

        # Second: invalid type
        yaml_attempt_2 = """
name: "Test Strategy"
type: "invalid_type"
required_fields: []
parameters: []
logic:
  entry: "test"
  exit: "test"
"""

        # Third: valid
        yaml_attempt_3 = """
name: "Test Strategy"
type: "factor_graph"
required_fields: ["price:收盤價"]
parameters:
  - name: "period"
    type: "int"
    value: 20
logic:
  entry: "close > 100"
  exit: "close < 90"
"""

        validator = SchemaValidator()

        # Mock LLM returns different YAML on each call
        llm_generate_mock = Mock(side_effect=[yaml_attempt_2, yaml_attempt_3])

        loop = ErrorFeedbackLoop(max_retries=3)
        success, validated_config, error_history = loop.validate_and_retry(
            yaml_attempt_1,
            validator,
            llm_generate_mock
        )

        # Should succeed after 2 retries
        assert success is True

        # Should track errors from first two attempts
        assert len(error_history) >= 2
        # First error: missing 'type'
        assert any("type" in err.lower() for err in error_history)

    def test_validate_and_retry_llm_callback_receives_retry_prompt(self):
        """Should pass formatted retry prompt to LLM callback"""
        from src.prompts.error_feedback import ErrorFeedbackLoop

        invalid_yaml = """
name: "Test Strategy"
type: "invalid_type"
"""

        valid_yaml = """
name: "Test Strategy"
type: "factor_graph"
required_fields: ["price:收盤價"]
parameters:
  - name: "period"
    type: "int"
    value: 20
logic:
  entry: "close > 100"
  exit: "close < 90"
"""

        validator = SchemaValidator()
        llm_generate_mock = Mock(return_value=valid_yaml)

        loop = ErrorFeedbackLoop(max_retries=3)
        success, _, _ = loop.validate_and_retry(
            invalid_yaml,
            validator,
            llm_generate_mock
        )

        # Should have called LLM with retry prompt
        assert llm_generate_mock.call_count == 1
        retry_prompt = llm_generate_mock.call_args[0][0]

        # Retry prompt should contain original YAML and error details
        assert "Test Strategy" in retry_prompt
        assert "invalid_type" in retry_prompt.lower() or "error" in retry_prompt.lower()


class TestIntegrationWithSchemaValidator:
    """Test integration with existing SchemaValidator"""

    def test_integration_with_real_validator(self):
        """Should work with real SchemaValidator instance"""
        from src.prompts.error_feedback import ErrorFeedbackLoop
        import yaml

        # Valid config matching schema
        valid_yaml = """
name: "Test Momentum Strategy"
type: "factor_graph"
required_fields:
  - "price:收盤價"
  - "price:成交金額"
parameters:
  - name: "momentum_period"
    type: "int"
    value: 20
    range: [10, 60]
  - name: "entry_threshold"
    type: "float"
    value: 0.02
    range: [0.01, 0.10]
logic:
  entry: "close.pct_change(20) > 0.02"
  exit: "close.pct_change(20) < -0.02"
"""

        validator = SchemaValidator()
        llm_generate_mock = Mock()

        loop = ErrorFeedbackLoop(max_retries=3)
        success, validated_config, error_history = loop.validate_and_retry(
            valid_yaml,
            validator,
            llm_generate_mock
        )

        # Should validate successfully
        assert success is True
        assert validated_config is not None
        assert validated_config["name"] == "Test Momentum Strategy"
        assert validated_config["type"] == "factor_graph"
        assert len(error_history) == 0

    def test_integration_handles_yaml_parse_errors(self):
        """Should handle YAML parse errors gracefully"""
        from src.prompts.error_feedback import ErrorFeedbackLoop

        # Invalid YAML syntax
        invalid_yaml = """
name: Test Strategy
type: factor_graph
  invalid_indent: true
"""

        valid_yaml = """
name: "Fixed Strategy"
type: "factor_graph"
required_fields: ["price:收盤價"]
parameters:
  - name: "period"
    type: "int"
    value: 20
logic:
  entry: "close > 100"
  exit: "close < 90"
"""

        validator = SchemaValidator()
        llm_generate_mock = Mock(return_value=valid_yaml)

        loop = ErrorFeedbackLoop(max_retries=3)
        success, validated_config, error_history = loop.validate_and_retry(
            invalid_yaml,
            validator,
            llm_generate_mock
        )

        # Should retry and succeed
        assert success is True
        assert validated_config is not None

        # Should track YAML parse error
        assert len(error_history) >= 1
        assert any("yaml" in err.lower() or "parse" in err.lower() for err in error_history)


class TestThreadSafety:
    """Test thread safety for concurrent usage"""

    def test_multiple_feedback_loops_independent(self):
        """Should allow multiple independent ErrorFeedbackLoop instances"""
        from src.prompts.error_feedback import ErrorFeedbackLoop

        loop1 = ErrorFeedbackLoop(max_retries=2)
        loop2 = ErrorFeedbackLoop(max_retries=5)

        assert loop1.max_retries == 2
        assert loop2.max_retries == 5

    def test_validate_and_retry_stateless(self):
        """Should be stateless - no side effects between calls"""
        from src.prompts.error_feedback import ErrorFeedbackLoop

        valid_yaml = """
name: "Test Strategy"
type: "factor_graph"
required_fields: ["price:收盤價"]
parameters:
  - name: "period"
    type: "int"
    value: 20
logic:
  entry: "close > 100"
  exit: "close < 90"
"""

        validator = SchemaValidator()
        llm_generate_mock = Mock()

        loop = ErrorFeedbackLoop(max_retries=3)

        # First call
        success1, config1, history1 = loop.validate_and_retry(
            valid_yaml,
            validator,
            llm_generate_mock
        )

        # Second call
        success2, config2, history2 = loop.validate_and_retry(
            valid_yaml,
            validator,
            llm_generate_mock
        )

        # Both should succeed independently
        assert success1 is True
        assert success2 is True
        assert len(history1) == 0
        assert len(history2) == 0


class TestUsageExamples:
    """Documentation and usage examples"""

    def test_example_complete_workflow(self):
        """Example: Complete two-stage workflow with error feedback"""
        from src.prompts.error_feedback import ErrorFeedbackLoop
        from src.prompts.prompt_formatter import (
            generate_field_selection_prompt,
            generate_config_creation_prompt
        )

        # Simulate LLM that generates invalid YAML first, then valid
        invalid_yaml = """
name: "Momentum Strategy"
type: "momentum"
required_fields: ["close"]
"""

        valid_yaml = """
name: "Momentum Strategy"
type: "factor_graph"
required_fields: ["price:收盤價"]
parameters:
  - name: "period"
    type: "int"
    value: 20
logic:
  entry: "close.pct_change(20) > 0.02"
  exit: "close.pct_change(20) < -0.02"
"""

        def mock_llm_generate(prompt: str) -> str:
            """Mock LLM that corrects errors on retry"""
            if "Attempt" in prompt or "retry" in prompt.lower():
                return valid_yaml
            return invalid_yaml

        validator = SchemaValidator()
        loop = ErrorFeedbackLoop(max_retries=3)

        # Stage 2: LLM generates config (with retry on validation failure)
        success, validated_config, error_history = loop.validate_and_retry(
            invalid_yaml,
            validator,
            mock_llm_generate
        )

        # Should succeed after retry
        assert success is True
        assert validated_config["type"] == "factor_graph"
        assert len(error_history) >= 1  # Tracked first error

    def test_example_max_retries_failure(self):
        """Example: Handle max retries exceeded gracefully"""
        from src.prompts.error_feedback import ErrorFeedbackLoop

        # LLM keeps generating invalid YAML
        def stubborn_llm(prompt: str) -> str:
            return "name: Test\ntype: invalid"

        validator = SchemaValidator()
        loop = ErrorFeedbackLoop(max_retries=2)

        invalid_yaml = "name: Test\ntype: invalid"
        success, validated_config, error_history = loop.validate_and_retry(
            invalid_yaml,
            validator,
            stubborn_llm
        )

        # Should fail gracefully
        assert success is False
        assert validated_config is None
        assert len(error_history) >= 2

        # User can inspect errors and decide next action
        print(f"Validation failed after {len(error_history)} attempts:")
        for i, error in enumerate(error_history, 1):
            print(f"  Attempt {i}: {error}")
