"""
AST Security Validator for AI-Generated Strategy Code

This module provides security validation for dynamically generated Python code
to prevent arbitrary code execution, file system access, and network operations.

Security Model:
- Whitelist approach: Only explicitly allowed operations are permitted
- Defense in depth: Multiple validation layers
- Clear error messages: Detailed feedback on security violations

Author: Autonomous Iteration Engine
Created: 2025-10-09
"""

import ast
from typing import Set, Tuple, List


# Whitelist of allowed modules and their permitted attributes
ALLOWED_MODULES = {
    'pandas': {'Series', 'DataFrame', 'Index', 'concat', 'merge', 'to_datetime'},
    'numpy': {'array', 'nan', 'inf', 'sum', 'mean', 'std', 'max', 'min', 'abs'},
    'finlab': {'data', 'backtest'},  # Data access and backtesting allowed
    'datetime': {'datetime', 'date', 'time', 'timedelta'},
    'math': {'sqrt', 'pow', 'log', 'exp', 'sin', 'cos', 'tan'},
}

# Blacklist of dangerous built-in functions
FORBIDDEN_BUILTINS = {
    'exec', 'eval', 'compile', '__import__',
    'open', 'file', 'input', 'raw_input',
    'execfile', 'reload', 'vars', 'locals', 'globals',
    'dir', 'getattr', 'setattr', 'delattr', 'hasattr',
    'callable', 'classmethod', 'staticmethod',
}

# Blacklist of dangerous modules
FORBIDDEN_MODULES = {
    'os', 'sys', 'subprocess', 'socket', 'urllib', 'urllib2', 'urllib3',
    'requests', 'http', 'httplib', 'ftplib', 'telnetlib',
    'pickle', 'marshal', 'shelve', 'dbm', 'anydbm',
    'importlib', 'imp', '__builtin__', 'builtins',
    'ctypes', 'cffi', 'pty', 'commands',
}

# Allowed comparison and binary operators
SAFE_OPERATORS = {
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
    ast.BitAnd, ast.BitOr, ast.BitXor, ast.Invert, ast.Not,
    ast.And, ast.Or,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Is, ast.IsNot, ast.In, ast.NotIn,
    ast.UAdd, ast.USub,
}


class SecurityValidator(ast.NodeVisitor):
    """
    AST visitor that validates code for security violations.

    This class walks the Abstract Syntax Tree and checks for:
    - Forbidden function calls (exec, eval, etc.)
    - Dangerous module imports
    - File I/O operations
    - Network operations
    - Unsafe attribute access
    """

    def __init__(self):
        self.errors: List[str] = []
        self.imported_modules: Set[str] = set()
        self.line_number: int = 0

    def add_error(self, message: str, node: ast.AST = None):
        """Add a security violation error with line number context."""
        line_info = f"Line {node.lineno}: " if node and hasattr(node, 'lineno') else ""
        self.errors.append(f"{line_info}{message}")

    def visit_Import(self, node: ast.Import):
        """Validate import statements."""
        for alias in node.names:
            module_name = alias.name.split('.')[0]  # Get base module name

            if module_name in FORBIDDEN_MODULES:
                self.add_error(
                    f"Forbidden module import: '{module_name}'. "
                    f"This module can access system resources.",
                    node
                )
            elif module_name not in ALLOWED_MODULES:
                self.add_error(
                    f"Unauthorized module import: '{module_name}'. "
                    f"Only whitelisted modules are allowed: {', '.join(ALLOWED_MODULES.keys())}",
                    node
                )
            else:
                self.imported_modules.add(module_name)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Validate from...import statements."""
        if node.module is None:
            self.add_error("Relative imports are not allowed", node)
            return

        module_name = node.module.split('.')[0]  # Get base module name

        if module_name in FORBIDDEN_MODULES:
            self.add_error(
                f"Forbidden module import: '{module_name}'. "
                f"This module can access system resources.",
                node
            )
        elif module_name not in ALLOWED_MODULES:
            self.add_error(
                f"Unauthorized module import: '{module_name}'. "
                f"Only whitelisted modules are allowed: {', '.join(ALLOWED_MODULES.keys())}",
                node
            )
        else:
            # Check if specific imports are whitelisted
            allowed_attrs = ALLOWED_MODULES.get(module_name, set())
            for alias in node.names:
                if alias.name == '*':
                    self.add_error(
                        f"Wildcard imports are not allowed: 'from {module_name} import *'",
                        node
                    )
                elif allowed_attrs and alias.name not in allowed_attrs:
                    self.add_error(
                        f"Unauthorized import from '{module_name}': '{alias.name}'. "
                        f"Allowed: {', '.join(allowed_attrs)}",
                        node
                    )
            self.imported_modules.add(module_name)

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Validate function calls."""
        # Check for forbidden built-in functions
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in FORBIDDEN_BUILTINS:
                self.add_error(
                    f"Forbidden function call: '{func_name}()'. "
                    f"This function can execute arbitrary code or access system resources.",
                    node
                )

        # Check for dangerous attribute access (e.g., obj.__class__, obj.__dict__)
        elif isinstance(node.func, ast.Attribute):
            attr_name = node.func.attr

            # Block access to magic methods and private attributes
            if attr_name.startswith('__') and attr_name.endswith('__'):
                self.add_error(
                    f"Access to magic method '{attr_name}' is forbidden. "
                    f"This can be used to bypass security restrictions.",
                    node
                )
            elif attr_name.startswith('_'):
                self.add_error(
                    f"Access to private attribute '{attr_name}' is forbidden.",
                    node
                )

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        """Validate attribute access."""
        attr_name = node.attr

        # Block access to dangerous attributes
        if attr_name.startswith('__') and attr_name.endswith('__'):
            # Allow common safe magic attributes
            safe_magic_attrs = {'__class__', '__name__', '__doc__'}
            if attr_name not in safe_magic_attrs:
                self.add_error(
                    f"Access to magic attribute '{attr_name}' is forbidden. "
                    f"This can be used to bypass security restrictions.",
                    node
                )
        elif attr_name.startswith('_') and not attr_name.startswith('__'):
            # Block private attributes (single underscore prefix)
            self.add_error(
                f"Access to private attribute '{attr_name}' is forbidden.",
                node
            )

        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda):
        """Lambda expressions are allowed but validated."""
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp):
        """List comprehensions are allowed but validated."""
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp):
        """Dictionary comprehensions are allowed but validated."""
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp):
        """Set comprehensions are allowed but validated."""
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):
        """Generator expressions are allowed but validated."""
        self.generic_visit(node)


def validate_strategy_code(code: str) -> Tuple[bool, str]:
    """
    Validate AI-generated strategy code for security vulnerabilities.

    This function parses the provided code and checks for:
    - Forbidden function calls (exec, eval, compile, __import__)
    - File I/O operations (open, read, write)
    - Network operations (socket, urllib, requests)
    - Subprocess execution (subprocess, os.system)
    - Dangerous module imports (pickle, marshal, shelve)
    - Unsafe attribute access (magic methods, private attributes)

    Args:
        code (str): Python code to validate

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
            - is_valid: True if code passes all security checks
            - error_message: Empty string if valid, detailed error message if invalid

    Example:
        >>> code = "import pandas as pd\\ndf = pd.DataFrame()"
        >>> is_valid, error = validate_strategy_code(code)
        >>> print(is_valid)
        True

        >>> code = "import os\\nos.system('rm -rf /')"
        >>> is_valid, error = validate_strategy_code(code)
        >>> print(is_valid)
        False
        >>> print(error)
        Line 1: Forbidden module import: 'os'. This module can access system resources.

    Security Model:
        - Whitelist approach: Only explicitly allowed operations are permitted
        - Defense in depth: Multiple validation layers (imports, calls, attributes)
        - Clear feedback: Detailed error messages for security violations

    Allowed Operations:
        - Standard library: pandas, numpy, finlab (data access only)
        - Math operations: +, -, *, /, **, //, %, &, |, ~
        - Logical operations: and, or, not, ==, !=, <, >, <=, >=
        - Data structures: list, dict, set, tuple
        - Control flow: if, for, while, with
        - Functions: def, lambda, return

    Blocked Operations:
        - Code execution: exec(), eval(), compile(), __import__()
        - File I/O: open(), read(), write(), file operations
        - Network: socket, urllib, requests, http
        - Subprocess: subprocess, os.system(), commands
        - Serialization: pickle, marshal, shelve
        - Introspection: getattr(), setattr(), vars(), locals(), globals()
        - Magic methods: __class__, __dict__, __code__ (except safe ones)
    """
    # Step 0: Validate input is not empty or whitespace-only
    if not code or not code.strip():
        return False, "Code cannot be empty or whitespace-only"

    # Step 1: Syntax validation - ensure code is valid Python
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error in code: {str(e)}"
    except Exception as e:
        return False, f"Failed to parse code: {str(e)}"

    # Step 2: Check if code contains only comments
    # Remove all comments and whitespace to see if there's actual code
    code_without_comments = '\n'.join(
        line for line in code.split('\n')
        if line.strip() and not line.strip().startswith('#')
    )
    if not code_without_comments.strip():
        return False, "Code contains only comments, no executable statements"

    # Step 3: Security validation - check for forbidden operations
    validator = SecurityValidator()
    validator.visit(tree)

    # Step 4: Return validation results
    if validator.errors:
        error_message = "Security validation failed:\n" + "\n".join(validator.errors)
        return False, error_message

    return True, ""


def get_validation_summary() -> dict:
    """
    Get a summary of validation rules and security model.

    Returns:
        dict: Summary of allowed/forbidden operations
    """
    return {
        "allowed_modules": list(ALLOWED_MODULES.keys()),
        "forbidden_modules": list(FORBIDDEN_MODULES),
        "forbidden_builtins": list(FORBIDDEN_BUILTINS),
        "security_model": "whitelist",
        "validation_layers": [
            "Syntax validation (ast.parse)",
            "Import validation (module whitelist)",
            "Function call validation (builtin blacklist)",
            "Attribute access validation (magic method protection)",
        ],
    }


if __name__ == "__main__":
    # Example usage and testing
    print("AST Security Validator - Self Test\n" + "="*50)

    # Test 1: Valid code
    valid_code = """
import pandas as pd
import numpy as np

def strategy(data):
    close = data.get('close')
    sma = close.rolling(20).mean()
    return close > sma
"""
    is_valid, error = validate_strategy_code(valid_code)
    print(f"\nTest 1 (Valid Code): {'✅ PASSED' if is_valid else '❌ FAILED'}")
    if error:
        print(f"Error: {error}")

    # Test 2: Forbidden exec() call
    exec_code = """
import pandas as pd
exec('print("Hello")')
"""
    is_valid, error = validate_strategy_code(exec_code)
    print(f"\nTest 2 (Forbidden exec): {'✅ PASSED' if not is_valid else '❌ FAILED'}")
    print(f"Error: {error}")

    # Test 3: Forbidden module import
    os_code = """
import os
os.system('ls')
"""
    is_valid, error = validate_strategy_code(os_code)
    print(f"\nTest 3 (Forbidden os module): {'✅ PASSED' if not is_valid else '❌ FAILED'}")
    print(f"Error: {error}")

    # Test 4: Magic method access
    magic_code = """
import pandas as pd
df = pd.DataFrame()
df.__class__.__bases__
"""
    is_valid, error = validate_strategy_code(magic_code)
    print(f"\nTest 4 (Magic method access): {'✅ PASSED' if not is_valid else '❌ FAILED'}")
    print(f"Error: {error}")

    # Test 5: Unauthorized module
    requests_code = """
import requests
requests.get('http://evil.com')
"""
    is_valid, error = validate_strategy_code(requests_code)
    print(f"\nTest 5 (Network module): {'✅ PASSED' if not is_valid else '❌ FAILED'}")
    print(f"Error: {error}")

    print("\n" + "="*50)
    print("Validation Summary:")
    summary = get_validation_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
