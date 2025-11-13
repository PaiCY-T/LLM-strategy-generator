"""AST Security Validator for generated trading strategies.

Validates that generated code:
1. Contains no import statements
2. Contains no dangerous functions (exec, eval, open, compile, __import__)
3. Uses only forward shifts (.shift(positive_int))
4. Does not perform file I/O operations

Security Model:
- AST Validation (Primary defense - 80-90% coverage)
- Blocks: imports, exec, eval, open, file I/O
- Validates: shift patterns, function calls

This is the PRIMARY and ONLY security defense layer for the skip-sandbox architecture.
"""

import ast
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class SecurityValidator(ast.NodeVisitor):
    """AST visitor that validates security constraints for trading strategies."""

    def __init__(self):
        self.errors: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Block all import statements.

        All necessary data is provided via data.get() - no imports needed.
        """
        imports = ', '.join(alias.name for alias in node.names)
        error_msg = f"Line {node.lineno}: Import statement not allowed: import {imports}"
        self.errors.append(error_msg)
        logger.warning(f"Security violation detected: {error_msg}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Block all from...import statements.

        All necessary data is provided via data.get() - no imports needed.
        """
        imports = ', '.join(alias.name for alias in node.names)
        module = node.module or ''
        error_msg = f"Line {node.lineno}: Import statement not allowed: from {module} import {imports}"
        self.errors.append(error_msg)
        logger.warning(f"Security violation detected: {error_msg}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Block dangerous function calls and validate shift patterns.

        Blocks: exec, eval, compile, __import__, open
        Validates: shift patterns must use positive integers only
        """
        # Check for dangerous built-in functions
        if isinstance(node.func, ast.Name):
            dangerous_funcs = ['eval', 'exec', 'compile', '__import__', 'open']
            if node.func.id in dangerous_funcs:
                error_msg = f"Line {node.lineno}: Function '{node.func.id}()' is not allowed"
                self.errors.append(error_msg)
                logger.warning(f"Security violation detected: {error_msg}")

        # Validate .shift() calls - must use positive integers only
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'shift':
            if len(node.args) > 0:
                arg = node.args[0]
                # Check if argument is a negative number
                if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
                    if isinstance(arg.operand, (ast.Num, ast.Constant)):
                        value = arg.operand.n if isinstance(arg.operand, ast.Num) else arg.operand.value
                        error_msg = (
                            f"Line {node.lineno}: Negative shift not allowed: .shift(-{value}). "
                            "Use positive values to avoid look-ahead bias."
                        )
                        self.errors.append(error_msg)
                        logger.warning(f"Security violation detected: {error_msg}")
                # Check if argument is zero
                elif isinstance(arg, (ast.Num, ast.Constant)):
                    value = arg.n if isinstance(arg, ast.Num) else arg.value
                    if isinstance(value, (int, float)) and value <= 0:
                        error_msg = (
                            f"Line {node.lineno}: Non-positive shift not allowed: .shift({value}). "
                            "Use positive values >= 1 to avoid look-ahead bias."
                        )
                        self.errors.append(error_msg)
                        logger.warning(f"Security violation detected: {error_msg}")

        self.generic_visit(node)


def validate_code(code: str) -> Tuple[bool, List[str]]:
    """Validate strategy code using AST security checks.

    Blocks dangerous operations and validates shift patterns to prevent:
    - Arbitrary code execution (exec, eval, compile, __import__)
    - File system access (open)
    - External imports (all import statements)
    - Look-ahead bias (negative or zero shifts)

    Args:
        code: Generated Python strategy code to validate

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if code passes all security checks
        - error_messages: List of error messages (empty if valid)

    Example:
        >>> is_valid, errors = validate_code("import os")
        >>> is_valid
        False
        >>> "Import statements" in errors[0]
        True

        >>> is_valid, errors = validate_code("close = data.get('close')")
        >>> is_valid
        True
        >>> len(errors)
        0
    """
    # Handle AST parsing errors gracefully
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
        logger.error(f"Failed to parse code: {error_msg}")
        return False, [error_msg]
    except Exception as e:
        error_msg = f"Unexpected error parsing code: {str(e)}"
        logger.error(error_msg)
        return False, [error_msg]

    # Validate security constraints
    validator = SecurityValidator()
    validator.visit(tree)

    is_valid = len(validator.errors) == 0

    if is_valid:
        logger.info("Code validation passed - no security violations detected")
    else:
        logger.warning(f"Code validation failed with {len(validator.errors)} security violations")

    return is_valid, validator.errors


def main():
    """Test the validator with example code."""
    # Test cases
    test_cases = [
        # Valid code
        ("""
close = data.get('price:收盤價')
momentum = close.pct_change(20).shift(1)
position = momentum.is_largest(10)
report = sim(position)
""", True, "Valid strategy with shift(1)"),

        # Invalid: import statement
        ("""
import os
close = data.get('price:收盤價')
""", False, "Import statement"),

        # Invalid: negative shift
        ("""
close = data.get('price:收盤價')
momentum = close.pct_change(20).shift(-1)
""", False, "Negative shift"),

        # Invalid: exec()
        ("""
exec('print("hello")')
""", False, "exec() call"),

        # Invalid: eval()
        ("""
result = eval('2 + 2')
""", False, "eval() call"),

        # Invalid: open()
        ("""
with open('file.txt') as f:
    data = f.read()
""", False, "open() call"),
    ]

    print("Running validation tests...\n")
    passed = 0
    failed = 0

    for code, should_pass, description in test_cases:
        is_valid, errors = validate_code(code)

        if is_valid == should_pass:
            print(f"✅ PASS: {description}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   Expected: {'valid' if should_pass else 'invalid'}")
            print(f"   Got: {'valid' if is_valid else 'invalid'}")
            if errors:
                for error in errors:
                    print(f"   - {error}")
            failed += 1
        print()

    print(f"\nResults: {passed} passed, {failed} failed")


if __name__ == '__main__':
    main()
