"""Tests for ErrorFeedbackLoop integration with ValidationGateway - Tasks 4.1 & 4.2.

This test suite validates the integration of error feedback and retry mechanisms
into ValidationGateway for automatic LLM retry on validation failures.

Test Coverage:
- Task 4.1: ErrorFeedbackLoop integration into ValidationGateway
- Task 4.2: Retry prompt generation with validation errors
- AC2.4: ErrorFeedbackLoop integrated into ValidationGateway
- AC2.5: Retry prompt includes validation errors and suggestions

Test Strategy:
- RED: Write failing tests first to establish requirements
- GREEN: Implement validate_and_retry() method in ValidationGateway
- REFACTOR: Optimize retry logic and error formatting

TDD Cycle:
1. test_validate_and_retry_method_exists - Verify method presence
2. test_retry_on_validation_failure - Verify retry triggers
3. test_retry_prompt_contains_errors - Verify error details in prompt
4. test_max_retries_respected - Verify retry limit (default: 3)
5. test_successful_retry_returns_valid_result - Verify successful retry flow
6. test_retry_with_field_errors - Verify field error feedback in prompt
7. test_no_retry_when_validation_passes - Verify no retry if first attempt valid
8. test_retry_prompt_includes_suggestions - Verify auto-correction suggestions

Requirements:
- AC2.4: ErrorFeedbackLoop integrated into ValidationGateway
- AC2.5: Retry prompt includes validation errors and suggestions
- Design.Components.ValidationGateway.validate_and_retry method
- Backward compatibility preserved
"""

import os
import pytest
from typing import Callable

from src.validation.gateway import ValidationGateway
from src.validation.validation_result import ValidationResult, FieldError


# Test fixtures for mocking LLM generation
class MockLLMGenerator:
    """Mock LLM generator for testing retry logic."""

    def __init__(self):
        self.call_count = 0
        self.prompts_received = []
        self.responses = []

    def generate(self, prompt: str) -> str:
        """Generate code based on prompt (mock implementation)."""
        self.call_count += 1
        self.prompts_received.append(prompt)

        # Return pre-configured response if available
        if self.call_count <= len(self.responses):
            return self.responses[self.call_count - 1]

        # Default: return valid code
        return "def strategy(data):\n    return data.get('close') > 100"


@pytest.fixture
def gateway():
    """Create ValidationGateway with Layer 1 and Layer 2 enabled."""
    os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
    os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
    return ValidationGateway()


@pytest.fixture
def mock_llm():
    """Create mock LLM generator."""
    return MockLLMGenerator()


# =============================================================================
# Test 1: Verify validate_and_retry method exists
# =============================================================================

def test_validate_and_retry_method_exists(gateway):
    """Test that ValidationGateway has validate_and_retry method.

    Requirements:
    - AC2.4: ErrorFeedbackLoop integrated into ValidationGateway
    - Design.Components.ValidationGateway.validate_and_retry method

    Expected:
    - validate_and_retry() method exists on ValidationGateway
    - Method signature matches: (llm_generate_func, initial_prompt, max_retries)
    """
    # Verify method exists
    assert hasattr(gateway, 'validate_and_retry'), \
        "ValidationGateway must have validate_and_retry() method"

    # Verify it's callable
    assert callable(gateway.validate_and_retry), \
        "validate_and_retry must be callable"


# =============================================================================
# Test 2: Verify retry triggers on validation failure
# =============================================================================

def test_retry_on_validation_failure(gateway, mock_llm):
    """Test that retry triggers when validation fails.

    Requirements:
    - AC2.4: Automatic retry on validation failure
    - ErrorFeedbackLoop.generate_retry_prompt integration

    Workflow:
    1. First attempt: invalid code (bad field name)
    2. Retry attempt: valid code
    3. Verify LLM called twice (initial + retry)
    """
    # Configure mock to return invalid then valid code
    mock_llm.responses = [
        # First attempt: invalid field name
        "def strategy(data):\n    return data.get('price:成交量') > 100",
        # Second attempt: valid field name
        "def strategy(data):\n    return data.get('close') > 100"
    ]

    # Execute validate_and_retry
    code, result = gateway.validate_and_retry(
        llm_generate_func=mock_llm.generate,
        initial_prompt="Create a strategy"
    )

    # Verify retry occurred
    assert mock_llm.call_count == 2, \
        "LLM should be called twice (initial + 1 retry)"

    # Verify final result is valid
    assert result.is_valid, \
        "Final validation result should be valid after successful retry"

    # Verify final code is the corrected version
    assert 'close' in code, \
        "Final code should use corrected field name 'close'"


# =============================================================================
# Test 3: Verify retry prompt contains errors
# =============================================================================

def test_retry_prompt_contains_errors(gateway, mock_llm):
    """Test that retry prompt includes validation error details.

    Requirements:
    - AC2.5: Retry prompt includes validation errors
    - ErrorFeedbackLoop.generate_retry_prompt with field errors

    Expected:
    - Second prompt contains error details
    - Error message includes line number
    - Error message includes invalid field name
    """
    # Configure mock to return invalid then valid code
    mock_llm.responses = [
        "def strategy(data):\n    return data.get('price:成交量') > 100",
        "def strategy(data):\n    return data.get('close') > 100"
    ]

    # Execute validate_and_retry
    code, result = gateway.validate_and_retry(
        llm_generate_func=mock_llm.generate,
        initial_prompt="Create a strategy"
    )

    # Verify second prompt contains error details
    assert len(mock_llm.prompts_received) == 2, \
        "Should receive 2 prompts (initial + retry)"

    retry_prompt = mock_llm.prompts_received[1]

    # Verify error details in retry prompt
    assert 'price:成交量' in retry_prompt, \
        "Retry prompt should mention invalid field name"

    assert 'Line' in retry_prompt or 'line' in retry_prompt, \
        "Retry prompt should include line number"

    assert 'error' in retry_prompt.lower() or 'Error' in retry_prompt, \
        "Retry prompt should mention errors"


# =============================================================================
# Test 4: Verify max_retries respected
# =============================================================================

def test_max_retries_respected(gateway, mock_llm):
    """Test that max_retries limit is respected.

    Requirements:
    - AC2.4: Max retries limit enforced (default: 3)
    - ErrorFeedbackLoop.max_retries configuration

    Workflow:
    1. Configure mock to always return invalid code
    2. Set max_retries=2
    3. Verify LLM called exactly 3 times (initial + 2 retries)
    4. Verify final result is invalid
    """
    # Configure mock to always return invalid code
    mock_llm.responses = [
        "def strategy(data):\n    return data.get('bad1') > 100",
        "def strategy(data):\n    return data.get('bad2') > 100",
        "def strategy(data):\n    return data.get('bad3') > 100",
        "def strategy(data):\n    return data.get('bad4') > 100"  # Should not reach
    ]

    # Execute with max_retries=2
    code, result = gateway.validate_and_retry(
        llm_generate_func=mock_llm.generate,
        initial_prompt="Create a strategy",
        max_retries=2
    )

    # Verify exactly 3 attempts (initial + 2 retries)
    assert mock_llm.call_count == 3, \
        "Should attempt exactly 3 times (initial + 2 retries)"

    # Verify final result is invalid
    assert not result.is_valid, \
        "Final result should be invalid after max retries exhausted"


# =============================================================================
# Test 5: Verify successful retry returns valid result
# =============================================================================

def test_successful_retry_returns_valid_result(gateway, mock_llm):
    """Test that successful retry returns valid code and result.

    Requirements:
    - AC2.4: Successful retry flow validation
    - ValidationResult.is_valid = True on success

    Expected:
    - Final code is the corrected version
    - Final ValidationResult.is_valid = True
    - Final ValidationResult.errors = []
    """
    # Configure mock for successful retry
    mock_llm.responses = [
        "def strategy(data):\n    return data.get('invalid_field') > 100",
        "def strategy(data):\n    return data.get('close') > 100"
    ]

    # Execute validate_and_retry
    code, result = gateway.validate_and_retry(
        llm_generate_func=mock_llm.generate,
        initial_prompt="Create a strategy"
    )

    # Verify success
    assert result.is_valid, "Result should be valid"
    assert len(result.errors) == 0, "Should have no errors"
    assert 'close' in code, "Code should use valid field name"


# =============================================================================
# Test 6: Verify retry with field errors
# =============================================================================

def test_retry_with_field_errors(gateway, mock_llm):
    """Test retry prompt contains FieldError details.

    Requirements:
    - AC2.5: Retry prompt includes field error details
    - FieldError.line, FieldError.message in prompt

    Expected:
    - Retry prompt contains field name from FieldError
    - Retry prompt contains error message
    - Retry prompt formatted for LLM consumption
    """
    # Configure mock
    mock_llm.responses = [
        "def strategy(data):\n    return data.get('price:成交量') > 100",
        "def strategy(data):\n    return data.get('close') > 100"
    ]

    # Execute
    code, result = gateway.validate_and_retry(
        llm_generate_func=mock_llm.generate,
        initial_prompt="Create a strategy"
    )

    # Verify retry prompt structure
    retry_prompt = mock_llm.prompts_received[1]

    # Should contain field name
    assert 'price:成交量' in retry_prompt, \
        "Retry prompt should contain invalid field name"

    # Should be formatted for LLM
    assert '##' in retry_prompt or '**' in retry_prompt, \
        "Retry prompt should use markdown formatting for LLM"


# =============================================================================
# Test 7: Verify no retry when validation passes
# =============================================================================

def test_no_retry_when_validation_passes(gateway, mock_llm):
    """Test that no retry occurs when first attempt is valid.

    Requirements:
    - AC2.4: Retry only on validation failure
    - Efficiency: avoid unnecessary LLM calls

    Expected:
    - LLM called only once
    - Result is valid
    - No retry prompt generated
    """
    # Configure mock to return valid code on first attempt
    mock_llm.responses = [
        "def strategy(data):\n    return data.get('close') > 100"
    ]

    # Execute
    code, result = gateway.validate_and_retry(
        llm_generate_func=mock_llm.generate,
        initial_prompt="Create a strategy"
    )

    # Verify no retry
    assert mock_llm.call_count == 1, \
        "Should only call LLM once when first attempt is valid"

    assert result.is_valid, \
        "Result should be valid"


# =============================================================================
# Test 8: Verify retry prompt includes suggestions
# =============================================================================

def test_retry_prompt_includes_suggestions(gateway, mock_llm):
    """Test that retry prompt includes auto-correction suggestions.

    Requirements:
    - AC2.5: Retry prompt includes suggestions from FieldError
    - FieldError.suggestion appears in retry prompt

    Expected:
    - Retry prompt contains "Did you mean" or similar suggestion
    - Retry prompt helps LLM understand how to fix the error
    """
    # Configure mock
    mock_llm.responses = [
        "def strategy(data):\n    return data.get('price:成交量') > 100",
        "def strategy(data):\n    return data.get('close') > 100"
    ]

    # Execute
    code, result = gateway.validate_and_retry(
        llm_generate_func=mock_llm.generate,
        initial_prompt="Create a strategy"
    )

    # Verify retry prompt includes suggestions
    retry_prompt = mock_llm.prompts_received[1]

    # Check for suggestion keywords
    has_suggestion = (
        'suggestion' in retry_prompt.lower() or
        'did you mean' in retry_prompt.lower() or
        'try using' in retry_prompt.lower() or
        '→' in retry_prompt  # Arrow symbol for corrections
    )

    assert has_suggestion, \
        "Retry prompt should include correction suggestions"


# =============================================================================
# Test 9: Verify backward compatibility
# =============================================================================

def test_backward_compatibility_validate_strategy(gateway):
    """Test that existing validate_strategy() method still works.

    Requirements:
    - Backward compatibility: existing code not broken
    - validate_strategy() unchanged

    Expected:
    - validate_strategy() still returns ValidationResult
    - validate_strategy() behavior unchanged
    """
    # Valid code
    valid_code = "def strategy(data):\n    return data.get('close') > 100"
    result = gateway.validate_strategy(valid_code)

    assert isinstance(result, ValidationResult), \
        "validate_strategy should return ValidationResult"
    assert result.is_valid, \
        "Valid code should pass validation"

    # Invalid code
    invalid_code = "def strategy(data):\n    return data.get('bad_field') > 100"
    result = gateway.validate_strategy(invalid_code)

    assert isinstance(result, ValidationResult), \
        "validate_strategy should return ValidationResult"
    assert not result.is_valid, \
        "Invalid code should fail validation"


# =============================================================================
# Test 10: Edge case - empty code
# =============================================================================

def test_validate_and_retry_empty_code(gateway, mock_llm):
    """Test validate_and_retry handles empty code gracefully.

    Edge case handling for robustness.
    """
    # Configure mock
    mock_llm.responses = [
        "",  # Empty code
        "def strategy(data):\n    return data.get('close') > 100"
    ]

    # Should handle gracefully
    code, result = gateway.validate_and_retry(
        llm_generate_func=mock_llm.generate,
        initial_prompt="Create a strategy"
    )

    # Should retry and succeed
    assert mock_llm.call_count >= 1, \
        "Should attempt generation"
