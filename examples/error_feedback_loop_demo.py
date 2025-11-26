#!/usr/bin/env python3
"""
Error Feedback Loop Demo - Task 24.3

This script demonstrates the error feedback loop mechanism for LLM-generated
YAML configuration validation and retry.

Usage:
    python3 examples/error_feedback_loop_demo.py

Requirements:
    - src/prompts/error_feedback.py
    - src/execution/schema_validator.py
    - src/config/data_fields.py (optional for field validation)

Features Demonstrated:
    1. Basic error feedback formatting
    2. Retry prompt generation
    3. Complete validation and retry workflow
    4. Error history tracking
    5. Max retry handling
    6. Integration with SchemaValidator
"""

from typing import Callable
from src.prompts.error_feedback import (
    ErrorFeedbackLoop,
    format_validation_errors,
    generate_retry_prompt
)
from src.execution.schema_validator import (
    SchemaValidator,
    ValidationError,
    ValidationSeverity
)


# ============================================================================
# Demo 1: Error Formatting
# ============================================================================

def demo_error_formatting():
    """Demonstrate format_validation_errors() function"""
    print("=" * 70)
    print("DEMO 1: Error Formatting")
    print("=" * 70)

    # Create sample validation errors
    errors = [
        ValidationError(
            severity=ValidationSeverity.ERROR,
            message="Missing required key: 'name'",
            field_path="<root>",
            line_number=None,
            suggestion="Add 'name' to the top level of your YAML"
        ),
        ValidationError(
            severity=ValidationSeverity.ERROR,
            message="Invalid strategy type: 'invalid_type'",
            field_path="type",
            line_number=5,
            suggestion="Valid types are: factor_graph, llm_generated, hybrid"
        ),
        ValidationError(
            severity=ValidationSeverity.WARNING,
            message="Unknown key: 'extra_field'",
            field_path="<root>",
            line_number=None,
            suggestion="Valid keys are: name, type, required_fields, parameters, logic"
        ),
        ValidationError(
            severity=ValidationSeverity.INFO,
            message="Consider adding 'description' field",
            field_path="description",
            line_number=None,
            suggestion="Description helps document strategy purpose"
        )
    ]

    # Format errors
    formatted = format_validation_errors(errors)
    print("\nFormatted Errors:")
    print(formatted)
    print()


# ============================================================================
# Demo 2: Retry Prompt Generation
# ============================================================================

def demo_retry_prompt():
    """Demonstrate generate_retry_prompt() function"""
    print("=" * 70)
    print("DEMO 2: Retry Prompt Generation")
    print("=" * 70)

    # Original YAML with errors
    original_yaml = """
name: "Test Strategy"
type: "invalid_type"
required_fields: []
parameters: []
logic:
  entry: "test"
  exit: "test"
"""

    # Validation errors
    errors = [
        ValidationError(
            severity=ValidationSeverity.ERROR,
            message="Invalid strategy type: 'invalid_type'",
            field_path="type",
            suggestion="Valid types are: factor_graph, llm_generated, hybrid"
        ),
        ValidationError(
            severity=ValidationSeverity.ERROR,
            message="Invalid field name: 'close'",
            field_path="required_fields[0]",
            suggestion="Did you mean: 'price:收盤價'?"
        )
    ]

    # Generate retry prompt
    retry_prompt = generate_retry_prompt(original_yaml, errors, attempt_number=1)
    print("\nRetry Prompt:")
    print(retry_prompt)
    print()


# ============================================================================
# Demo 3: Complete Validation Workflow with Mock LLM
# ============================================================================

def demo_validation_workflow():
    """Demonstrate complete ErrorFeedbackLoop workflow"""
    print("=" * 70)
    print("DEMO 3: Complete Validation Workflow")
    print("=" * 70)

    # Initialize components
    validator = SchemaValidator()
    loop = ErrorFeedbackLoop(max_retries=3)

    # Mock LLM that corrects errors on retry
    attempt_count = [0]  # Use list to modify in nested function

    def mock_llm_generate(prompt: str) -> str:
        """Mock LLM that generates invalid YAML first, then valid on retry"""
        attempt_count[0] += 1

        if attempt_count[0] == 1:
            # First attempt: invalid YAML
            print(f"\n[Mock LLM] Attempt {attempt_count[0]}: Generating invalid YAML...")
            return """
name: "Test Strategy"
type: "invalid_type"
required_fields: []
"""
        else:
            # Retry: valid YAML
            print(f"\n[Mock LLM] Attempt {attempt_count[0]}: Generating corrected YAML...")
            return """
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

    # Start with invalid YAML
    print("\nStarting validation workflow...")
    initial_yaml = mock_llm_generate("")

    # Validate with automatic retry
    success, validated_config, error_history = loop.validate_and_retry(
        initial_yaml,
        validator,
        mock_llm_generate
    )

    # Display results
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"Success: {success}")
    print(f"Total attempts: {attempt_count[0]}")
    print(f"Errors encountered: {len(error_history)}")

    if success:
        print(f"\n✓ Validation successful!")
        print(f"Config name: {validated_config['name']}")
        print(f"Config type: {validated_config['type']}")
    else:
        print(f"\n✗ Validation failed after max retries")

    print(f"\nError History:")
    for i, error in enumerate(error_history, 1):
        print(f"  {i}. {error}")
    print()


# ============================================================================
# Demo 4: Max Retry Limit Enforcement
# ============================================================================

def demo_max_retry_limit():
    """Demonstrate max retry limit enforcement"""
    print("=" * 70)
    print("DEMO 4: Max Retry Limit Enforcement")
    print("=" * 70)

    # Initialize components
    validator = SchemaValidator()
    loop = ErrorFeedbackLoop(max_retries=2)

    # Mock stubborn LLM that always generates invalid YAML
    attempt_count = [0]

    def stubborn_llm(prompt: str) -> str:
        """Mock LLM that never corrects errors"""
        attempt_count[0] += 1
        print(f"\n[Stubborn LLM] Attempt {attempt_count[0]}: Generating invalid YAML again...")
        return """
name: "Test Strategy"
type: "invalid_type"
"""

    # Start validation
    print("\nStarting validation with stubborn LLM...")
    initial_yaml = stubborn_llm("")

    # Validate with automatic retry (will fail after max retries)
    success, validated_config, error_history = loop.validate_and_retry(
        initial_yaml,
        validator,
        stubborn_llm
    )

    # Display results
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"Success: {success}")
    print(f"Max retries: {loop.max_retries}")
    print(f"Total attempts: {attempt_count[0]}")
    print(f"Errors encountered: {len(error_history)}")

    if not success:
        print(f"\n✗ Validation failed after max retries exceeded")
        print(f"\nError History:")
        for i, error in enumerate(error_history, 1):
            print(f"  {i}. {error}")
    print()


# ============================================================================
# Demo 5: YAML Parse Error Handling
# ============================================================================

def demo_yaml_parse_errors():
    """Demonstrate YAML parse error handling"""
    print("=" * 70)
    print("DEMO 5: YAML Parse Error Handling")
    print("=" * 70)

    # Initialize components
    validator = SchemaValidator()
    loop = ErrorFeedbackLoop(max_retries=2)

    # Mock LLM that fixes syntax errors
    attempt_count = [0]

    def mock_llm_with_syntax_fix(prompt: str) -> str:
        """Mock LLM that generates syntax error first, then valid YAML"""
        attempt_count[0] += 1

        if attempt_count[0] == 1:
            print(f"\n[Mock LLM] Attempt {attempt_count[0]}: Generating YAML with syntax error...")
            return """
name: Test Strategy
type: factor_graph
  invalid_indent: true
"""
        else:
            print(f"\n[Mock LLM] Attempt {attempt_count[0]}: Fixing syntax error...")
            return """
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

    # Start validation
    print("\nStarting validation with YAML syntax error...")
    initial_yaml = mock_llm_with_syntax_fix("")

    # Validate with automatic retry
    success, validated_config, error_history = loop.validate_and_retry(
        initial_yaml,
        validator,
        mock_llm_with_syntax_fix
    )

    # Display results
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"Success: {success}")
    print(f"Total attempts: {attempt_count[0]}")

    if success:
        print(f"\n✓ Validation successful after fixing syntax error!")
    else:
        print(f"\n✗ Validation failed")

    print(f"\nError History:")
    for i, error in enumerate(error_history, 1):
        print(f"  {i}. {error}")
    print()


# ============================================================================
# Main Demo Runner
# ============================================================================

def main():
    """Run all demos"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Error Feedback Loop Demo - Task 24.3" + " " * 17 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    try:
        # Run all demos
        demo_error_formatting()
        demo_retry_prompt()
        demo_validation_workflow()
        demo_max_retry_limit()
        demo_yaml_parse_errors()

        print("=" * 70)
        print("✓ All demos completed successfully!")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"\n✗ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
