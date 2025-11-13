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


def validate_total_return(value: Optional[float]) -> Optional[str]:
    """Validate total_return is within acceptable range [-1, 10].

    Args:
        value: Total return to validate (None is valid)

    Returns:
        Error message if invalid, None if valid
    """
    if value is None:
        return None

    if math.isnan(value):
        return "total_return must be a valid number, got NaN"

    if math.isinf(value):
        return "total_return must be finite, got inf"

    if value < -1.0 or value > 10.0:
        return f"total_return {value} is out of valid range [-1, 10]"

    return None


# =============================================================================
# ExecutionResult Metric Validators - Phase 3.2 Schema Validation
# =============================================================================

def validate_sharpe_ratio(value):
    """Validate sharpe_ratio field is within expected range [-10, 10].

    Args:
        value: Sharpe ratio to validate (None is valid)

    Returns:
        Error message if invalid, None if valid
    """
    if value is None:
        return None

    if math.isnan(value):
        return f"sharpe_ratio is NaN (not a number)"

    if math.isinf(value):
        return f"sharpe_ratio is infinite ({value})"

    if value < -10.0 or value > 10.0:
        return f"sharpe_ratio {value} is out of valid range [-10, 10]"

    return None


def validate_total_return(value):
    """Validate total_return field is within acceptable range [-1, 10].

    Total return represents cumulative performance from -100% (total loss)
    to +1000% (10x gain). Values outside this range indicate anomalies.

    Args:
        value: Total return value to validate (None is valid for optional field)

    Returns:
        Error message if invalid, None if valid

    Examples:
        >>> validate_total_return(0.25)
        None
        >>> validate_total_return(-1.0)
        None
        >>> validate_total_return(-1.5)
        'total_return -1.5 is out of valid range [-1, 10]. Expected: -1 <= total_return <= 10.'
    """
    # None is valid (optional field)
    if value is None:
        return None

    # Check for NaN
    if math.isnan(value):
        return (
            "total_return must be a valid number, got NaN. "
            "Suggestion: Check for invalid calculations in return computation."
        )

    # Check for infinity
    if math.isinf(value):
        inf_str = 'inf' if value > 0 else '-inf'
        return (
            f"total_return must be finite, got {inf_str}. "
            f"Suggestion: Check for division by zero in return calculation."
        )

    # Check range [-1, 10] (allows -100% loss to +1000% gain)
    if value < -1.0 or value > 10.0:
        return (
            f"total_return {value} is out of valid range [-1, 10]. "
            f"Expected: -1 <= total_return <= 10. "
            f"Suggestion: Verify backtest logic and check for data corruption."
        )

    return None


def validate_max_drawdown(value):
    """Validate max_drawdown field is non-positive (drawdown <= 0).

    Args:
        value: Max drawdown to validate (None is valid)

    Returns:
        Error message if invalid, None if valid
    """
    if value is None:
        return None

    if math.isnan(value):
        return f"max_drawdown is NaN (not a number)"

    if math.isinf(value):
        return f"max_drawdown is infinite ({value})"

    if value > 0:
        return f"max_drawdown {value} must be <= 0 (drawdown cannot be positive)"

    return None


def log_validation_error(field_name: str, value, error_message: str) -> None:
    """Log validation error with field, value, and constraint details.

    Args:
        field_name: Name of the field that failed validation (e.g., 'sharpe_ratio')
        value: Actual value that failed validation (can be any type including None, NaN, Inf)
        error_message: Detailed error message from the validator function

    Examples:
        >>> log_validation_error("sharpe_ratio", 15.0, "sharpe_ratio 15.0 is out of valid range [-10, 10]")
        # Logs: WARNING - Validation failed for sharpe_ratio: sharpe_ratio 15.0 is out of valid range [-10, 10] (value=15.0)
    """
    import logging
    logger = logging.getLogger(__name__)

    # Format special float values for clarity
    if isinstance(value, float):
        if math.isnan(value):
            value_str = "NaN"
        elif math.isinf(value):
            value_str = "inf" if value > 0 else "-inf"
        else:
            value_str = str(value)
    else:
        value_str = str(value)

    logger.warning(
        f"Validation failed for {field_name}: {error_message} (value={value_str})"
    )


def validate_execution_result(result):
    """Validate all metrics in ExecutionResult.

    Args:
        result: ExecutionResult to validate

    Returns:
        List of error messages (empty if all valid)
    """
    # Skip validation for failed executions
    if not result.success:
        return []

    errors = []

    # Validate sharpe_ratio
    sharpe_error = validate_sharpe_ratio(result.sharpe_ratio)
    if sharpe_error:
        errors.append(sharpe_error)

    # Validate total_return
    return_error = validate_total_return(result.total_return)
    if return_error:
        errors.append(return_error)

    # Validate max_drawdown
    drawdown_error = validate_max_drawdown(result.max_drawdown)
    if drawdown_error:
        errors.append(drawdown_error)

    return errors
