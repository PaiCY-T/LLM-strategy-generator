#!/usr/bin/env python3
"""Demo script for FieldValidator with structured error feedback.

This script demonstrates the FieldValidator's ability to provide
clear, actionable error messages with line numbers and suggestions.
"""

from src.validation.field_validator import FieldValidator
from src.config.data_fields import DataFieldManifest


def main():
    """Run FieldValidator demonstration."""
    # Initialize validator
    manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
    validator = FieldValidator(manifest)

    # Example 1: Valid code
    print("=" * 70)
    print("Example 1: Valid Code")
    print("=" * 70)
    valid_code = """
def strategy(data):
    close_price = data.get('close')
    volume = data.get('volume')
    return close_price > 100 and volume > 1000000
"""
    result = validator.validate(valid_code)
    print(f"Code:\n{valid_code}")
    print(f"\nResult: {result}")
    print()

    # Example 2: Single error with suggestion
    print("=" * 70)
    print("Example 2: Single Error with Suggestion")
    print("=" * 70)
    error_code = """
def strategy(data):
    price = data.get('price:成交量')  # Wrong! Should be price:成交金額
    return price > 100
"""
    result = validator.validate(error_code)
    print(f"Code:\n{error_code}")
    print(f"\nResult:\n{result}")
    print()

    # Example 3: Multiple errors
    print("=" * 70)
    print("Example 3: Multiple Errors")
    print("=" * 70)
    multi_error_code = """
def strategy(data):
    field1 = data.get('price:成交量')      # Line 3 - Invalid
    field2 = data.get('completely_xyz')   # Line 4 - Invalid
    field3 = data.get('close')            # Line 5 - Valid
    field4 = data.get('turnover')         # Line 6 - Invalid but has suggestion
    return True
"""
    result = validator.validate(multi_error_code)
    print(f"Code:\n{multi_error_code}")
    print(f"\nResult:\n{result}")
    print()

    # Example 4: Detailed error inspection
    print("=" * 70)
    print("Example 4: Detailed Error Information")
    print("=" * 70)
    if result.errors:
        for i, error in enumerate(result.errors, 1):
            print(f"Error {i}:")
            print(f"  Line: {error.line}")
            print(f"  Column: {error.column}")
            print(f"  Field Name: '{error.field_name}'")
            print(f"  Error Type: {error.error_type}")
            print(f"  Message: {error.message}")
            print(f"  Suggestion: {error.suggestion}")
            print()

    # Example 5: Syntax error handling
    print("=" * 70)
    print("Example 5: Syntax Error Handling")
    print("=" * 70)
    syntax_error_code = """
def strategy(data)
    price = data.get('close')  # Missing colon
    return price > 100
"""
    result = validator.validate(syntax_error_code)
    print(f"Code:\n{syntax_error_code}")
    print(f"\nResult:\n{result}")
    print()


if __name__ == "__main__":
    main()
