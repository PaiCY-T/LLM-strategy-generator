"""
Strategy code validation using AST parsing.

Provides security validation to prevent execution of malicious or
invalid code by analyzing the Abstract Syntax Tree.

Also provides field validators for ExecutionResult metrics - Phase 3.2 Schema Validation.
"""

import ast
import math
from typing import List, Optional, Set, Tuple


# Allowed module imports for strategy code
ALLOWED_IMPORTS: Set[str] = {
    'pandas',
    'numpy',
    'finlab',
    'datetime',
    'pd',
    'np',
}

# Restricted builtin functions that pose security risks
RESTRICTED_BUILTINS: Set[str] = {
    'open',
    'exec',
    'eval',
    '__import__',
    'compile',
    'input',
    'file',
    '__builtins__',
    'execfile',
    'reload',
    'vars',
    'globals',
    'locals',
}

# Restricted attribute names that could access internals
RESTRICTED_ATTRIBUTES: Set[str] = {
    '__dict__',
    '__class__',
    '__bases__',
    '__subclasses__',
    '__globals__',
    '__code__',
}


class CodeValidator:
    """Validates strategy code for safety and correctness."""

    def __init__(self) -> None:
        """Initialize validator."""
        self.errors: List[str] = []

    def validate_strategy_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate strategy code using AST parsing.

        Checks for:
        - Syntax errors
        - Restricted imports
        - Forbidden builtins
        - File I/O operations
        - Dangerous attribute access

        Args:
            code: Python code string to validate

        Returns:
            Tuple of (is_valid, error_message)
            error_message is None if code is valid
        """
        self.errors = []

        # Parse code into AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Parse error: {str(e)}"

        # Walk the AST and check for security violations
        for node in ast.walk(tree):
            self._check_imports(node)
            self._check_builtins(node)
            self._check_file_operations(node)
            self._check_attribute_access(node)

        if self.errors:
            return False, "; ".join(self.errors)

        return True, None

    def _check_imports(self, node: ast.AST) -> None:
        """Check for restricted imports.

        Args:
            node: AST node to check
        """
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]
                if module_name not in ALLOWED_IMPORTS:
                    self.errors.append(
                        f"Forbidden import: '{alias.name}'. "
                        f"Allowed imports: {', '.join(sorted(ALLOWED_IMPORTS))}"
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]
                if module_name not in ALLOWED_IMPORTS:
                    self.errors.append(
                        f"Forbidden import from: '{node.module}'. "
                        f"Allowed imports: {', '.join(sorted(ALLOWED_IMPORTS))}"
                    )

    def _check_builtins(self, node: ast.AST) -> None:
        """Check for restricted builtin usage.

        Args:
            node: AST node to check
        """
        if isinstance(node, ast.Name):
            if node.id in RESTRICTED_BUILTINS:
                self.errors.append(
                    f"Forbidden builtin: '{node.id}'. "
                    "This function is restricted for security"
                )

        # Check function calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in RESTRICTED_BUILTINS:
                    self.errors.append(
                        f"Forbidden function call: '{node.func.id}()'. "
                        "This function is restricted for security"
                    )

    def _check_file_operations(self, node: ast.AST) -> None:
        """Check for file I/O operations.

        Args:
            node: AST node to check
        """
        if isinstance(node, ast.Call):
            # Check for open() calls
            if isinstance(node.func, ast.Name) and node.func.id == 'open':
                self.errors.append(
                    "File I/O operations not allowed. "
                    "Cannot use open() for security reasons"
                )

            # Check for write/read methods
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ('write', 'read', 'writelines', 'readlines'):
                    self.errors.append(
                        f"File I/O method '{node.func.attr}' not allowed"
                    )

    def _check_attribute_access(self, node: ast.AST) -> None:
        """Check for dangerous attribute access.

        Args:
            node: AST node to check
        """
        if isinstance(node, ast.Attribute):
            if node.attr in RESTRICTED_ATTRIBUTES:
                self.errors.append(
                    f"Restricted attribute access: '{node.attr}'. "
                    "Cannot access internal attributes"
                )


def validate_strategy_code(code: str) -> Tuple[bool, Optional[str]]:
    """Validate strategy code for safety and correctness.

    Convenience function wrapping CodeValidator.

    Args:
        code: Python code string to validate

    Returns:
        Tuple of (is_valid, error_message)
        error_message is None if code is valid

    Example:
        >>> is_valid, error = validate_strategy_code("import pandas as pd")
        >>> assert is_valid is True
        >>> assert error is None
    """
    validator = CodeValidator()
    return validator.validate_strategy_code(code)


# Field validators for ExecutionResult metrics

def validate_sharpe_ratio(value: Optional[float]) -> Optional[str]:
    """Validate sharpe_ratio is within acceptable range [-10, 10].

    Args:
        value: Sharpe ratio to validate (None is valid)

    Returns:
        Error message if invalid, None if valid
    """
    if value is None:
        return None

    if math.isnan(value):
        return "sharpe_ratio must be a valid number, got NaN"

    if math.isinf(value):
        return f"sharpe_ratio must be finite, got {'inf' if value > 0 else '-inf'}"

    if value < -10.0 or value > 10.0:
        return f"sharpe_ratio {value} is out of valid range [-10, 10]"

    return None
