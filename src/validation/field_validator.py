"""Field validator with structured error feedback.

This module implements AST-based field validation for finlab API code.
It provides structured error messages with line numbers, column positions,
and helpful suggestions for common mistakes.

Key Features:
- AST parsing for accurate line/column tracking
- Integration with DataFieldManifest for field validation
- Structured error feedback with suggestions
- Support for data.get('field_name') pattern detection

Architecture:
- Uses Python AST for parsing and analysis
- Leverages ValidationResult for structured error reporting
- Integrates with COMMON_CORRECTIONS for helpful suggestions

Usage:
    from src.validation.field_validator import FieldValidator
    from src.config.data_fields import DataFieldManifest

    # Initialize validator
    manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
    validator = FieldValidator(manifest)

    # Validate code
    code = '''
    def strategy(data):
        price = data.get('price:成交量')  # Invalid field
        return price > 100
    '''

    result = validator.validate(code)
    print(result.is_valid)  # False
    print(result.errors[0].line)  # 3
    print(result.errors[0].suggestion)  # "Did you mean 'price:成交金額'?"

Performance:
- AST parsing overhead: ~1-5ms for typical strategy functions
- Field validation: O(1) dict lookups via DataFieldManifest
- Total validation time: <10ms for typical code

See Also:
    - src.validation.validation_result: ValidationResult, FieldError structures
    - src.config.data_fields: DataFieldManifest for field validation
    - tests.test_structured_error_feedback: TDD test suite
"""

import ast
from typing import Optional, Tuple
from src.config.data_fields import DataFieldManifest
from src.validation.validation_result import ValidationResult


class FieldValidator:
    """
    AST-based field validator with structured error feedback.

    Validates Python code for finlab API field usage and provides
    structured error messages with line numbers and suggestions.

    This validator parses Python code using AST (Abstract Syntax Tree)
    to accurately track line numbers and column positions. It detects
    data.get('field_name') patterns and validates field names against
    the DataFieldManifest.

    Attributes:
        manifest: DataFieldManifest instance for field validation

    Example:
        >>> manifest = DataFieldManifest()
        >>> validator = FieldValidator(manifest)
        >>>
        >>> code = "price = data.get('price:成交量')"
        >>> result = validator.validate(code)
        >>>
        >>> assert len(result.errors) == 1
        >>> assert result.errors[0].line == 1
        >>> assert "Did you mean" in result.errors[0].suggestion
    """

    def __init__(self, manifest: DataFieldManifest):
        """
        Initialize validator with field manifest.

        Args:
            manifest: DataFieldManifest instance containing valid field names
                     and COMMON_CORRECTIONS for suggestions

        Example:
            >>> manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
            >>> validator = FieldValidator(manifest)
        """
        self.manifest = manifest

    def validate(self, code: str) -> ValidationResult:
        """
        Validate Python code for field usage errors.

        Parses the code using AST and checks all data.get() calls for
        valid field names. Returns structured validation results with
        line numbers, column positions, and helpful suggestions.

        Args:
            code: Python code string to validate

        Returns:
            ValidationResult containing errors and warnings

        Example:
            >>> validator = FieldValidator(manifest)
            >>> code = '''
            ... def strategy(data):
            ...     price = data.get('price:成交量')  # Invalid
            ...     return price > 100
            ... '''
            >>> result = validator.validate(code)
            >>> assert len(result.errors) == 1
            >>> assert result.errors[0].line == 3
            >>> assert "Did you mean 'price:成交金額'?" in result.errors[0].suggestion
        """
        result = ValidationResult()

        # Try to parse code
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            # Add syntax error to results
            result.add_error(
                line=e.lineno or 1,
                column=e.offset or 0,
                field_name='<syntax>',
                error_type='syntax_error',
                message=f'Syntax error: {e.msg}'
            )
            return result

        # Walk AST and find data.get() calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if it's data.get('field_name')
                field_info = self._extract_field_from_call(node)
                if field_info:
                    field_name, line, column = field_info
                    self._validate_field_usage(field_name, line, column, result)

        return result

    def _extract_field_from_call(self, node: ast.Call) -> Optional[Tuple[str, int, int]]:
        """
        Extract field name from data.get('field_name') calls.

        Detects the pattern:
            data.get('field_name')
            data.get("field_name")

        Args:
            node: AST Call node to analyze

        Returns:
            Tuple of (field_name, line, column) if pattern matches, None otherwise

        Example:
            >>> # For code: data.get('close')
            >>> # Returns: ('close', 1, 0)
        """
        # Check if call is data.get(...)
        if (isinstance(node.func, ast.Attribute) and
            node.func.attr == 'get' and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id == 'data'):

            # Get first argument (field name)
            if node.args and isinstance(node.args[0], ast.Constant):
                field_name = node.args[0].value
                if isinstance(field_name, str):
                    return (field_name, node.lineno, node.col_offset)

        return None

    def _validate_field_usage(
        self,
        field_name: str,
        line: int,
        column: int,
        result: ValidationResult
    ) -> None:
        """
        Validate a single field usage and add errors if invalid.

        Uses DataFieldManifest.validate_field_with_suggestion() to check
        field validity and get helpful suggestions for common mistakes.

        Args:
            field_name: Field name to validate
            line: Line number where field appears (1-indexed)
            column: Column offset where field appears (0-indexed)
            result: ValidationResult to add errors to

        Example:
            >>> result = ValidationResult()
            >>> validator._validate_field_usage('price:成交量', 3, 15, result)
            >>> assert len(result.errors) == 1
            >>> assert result.errors[0].suggestion is not None
        """
        # Validate field and get suggestion
        is_valid, suggestion = self.manifest.validate_field_with_suggestion(field_name)

        if is_valid:
            return  # Valid field, no error

        # Field is invalid, add error with suggestion
        result.add_error(
            line=line,
            column=column,
            field_name=field_name,
            error_type='invalid_field',
            message=f"Invalid field name: '{field_name}'",
            suggestion=suggestion
        )
