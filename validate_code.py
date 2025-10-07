"""AST Security Validator for generated trading strategies.

Validates that generated code:
1. Contains no import statements
2. Contains no dangerous functions (exec, eval, open, compile, __import__)
3. Uses only forward shifts (.shift(positive_int))
4. Does not perform file I/O operations
"""

import ast
from typing import List, Tuple


class SecurityValidator(ast.NodeVisitor):
    """AST visitor that validates security constraints for trading strategies."""

    def __init__(self):
        self.errors: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Block all import statements."""
        imports = ', '.join(alias.name for alias in node.names)
        self.errors.append(f"Line {node.lineno}: Import statement not allowed: import {imports}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Block all from...import statements."""
        imports = ', '.join(alias.name for alias in node.names)
        module = node.module or ''
        self.errors.append(f"Line {node.lineno}: Import statement not allowed: from {module} import {imports}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Block dangerous function calls and validate shift patterns."""
        # Check for dangerous built-in functions
        if isinstance(node.func, ast.Name):
            dangerous_funcs = ['eval', 'exec', 'compile', '__import__', 'open']
            if node.func.id in dangerous_funcs:
                self.errors.append(f"Line {node.lineno}: Function '{node.func.id}()' is not allowed")

        # Validate .shift() calls - must use positive integers only
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'shift':
            if len(node.args) > 0:
                arg = node.args[0]
                # Check if argument is a negative number
                if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
                    if isinstance(arg.operand, (ast.Num, ast.Constant)):
                        value = arg.operand.n if isinstance(arg.operand, ast.Num) else arg.operand.value
                        self.errors.append(
                            f"Line {node.lineno}: Negative shift not allowed: .shift(-{value}). "
                            "Use positive values to avoid look-ahead bias."
                        )
                # Check if argument is zero
                elif isinstance(arg, (ast.Num, ast.Constant)):
                    value = arg.n if isinstance(arg, ast.Num) else arg.value
                    if isinstance(value, (int, float)) and value <= 0:
                        self.errors.append(
                            f"Line {node.lineno}: Non-positive shift not allowed: .shift({value}). "
                            "Use positive values >= 1 to avoid look-ahead bias."
                        )

        self.generic_visit(node)


def validate_code(code: str) -> Tuple[bool, List[str]]:
    """Validate that code meets security constraints.

    Args:
        code: Python code string to validate

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if code passes all security checks
        - error_messages: List of error messages (empty if valid)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"Syntax error at line {e.lineno}: {e.msg}"]

    validator = SecurityValidator()
    validator.visit(tree)

    is_valid = len(validator.errors) == 0
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
