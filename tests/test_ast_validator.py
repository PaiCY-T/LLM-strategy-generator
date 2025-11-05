"""Unit tests for AST security validator.

This module tests the AST validator used in the autonomous loop to
validate generated strategy code for security vulnerabilities.

Test coverage:
- Valid code passes validation
- Invalid imports are rejected (os, sys, subprocess, etc.)
- Dangerous builtins are rejected (eval, exec, compile, etc.)
- Unsupported pandas operations are rejected (shift, etc.)
- Private attribute access is rejected
- Magic method access is rejected
"""

import pytest
import sys
import os

# Add artifacts/working/modules to path for imports
ARTIFACTS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../artifacts/working/modules'))
if ARTIFACTS_PATH not in sys.path:
    sys.path.insert(0, ARTIFACTS_PATH)

from ast_validator import validate_strategy_code, get_validation_summary


class TestASTValidator:
    """Test suite for AST security validator."""

    def test_valid_code_passes(self):
        """Test that valid strategy code passes validation."""
        code = """
import pandas as pd
import numpy as np

def strategy(data):
    close = data.get('close')
    sma = close.rolling(20).mean()
    signal = close > sma
    return signal
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is True
        assert error == ""

    def test_invalid_import_os_rejected(self):
        """Test that os module import is rejected."""
        code = """
import os
import pandas as pd

def strategy(data):
    os.system('rm -rf /')  # Dangerous!
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Forbidden module import: 'os'" in error
        assert "system resources" in error.lower()

    def test_invalid_import_sys_rejected(self):
        """Test that sys module import is rejected."""
        code = """
import sys
import pandas as pd

def strategy(data):
    sys.exit(1)  # Dangerous!
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Forbidden module import: 'sys'" in error

    def test_invalid_import_subprocess_rejected(self):
        """Test that subprocess module import is rejected."""
        code = """
import subprocess
import pandas as pd

def strategy(data):
    subprocess.run(['ls', '-la'])  # Dangerous!
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Forbidden module import: 'subprocess'" in error

    def test_invalid_import_requests_rejected(self):
        """Test that requests module (network access) is rejected."""
        code = """
import requests
import pandas as pd

def strategy(data):
    requests.get('http://evil.com')  # Dangerous!
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        # requests is in FORBIDDEN_MODULES, so it should be "Forbidden module import"
        assert ("Forbidden module import: 'requests'" in error or
                "Unauthorized module import: 'requests'" in error)

    def test_eval_usage_rejected(self):
        """Test that eval() usage is rejected."""
        code = """
import pandas as pd

def strategy(data):
    result = eval('1 + 1')  # Dangerous!
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Forbidden function call: 'eval" in error  # May include () or not
        assert "arbitrary code" in error.lower()

    def test_exec_usage_rejected(self):
        """Test that exec() usage is rejected."""
        code = """
import pandas as pd

def strategy(data):
    exec('print("hello")')  # Dangerous!
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Forbidden function call: 'exec" in error  # May include () or not

    def test_compile_usage_rejected(self):
        """Test that compile() usage is rejected."""
        code = """
import pandas as pd

def strategy(data):
    code_obj = compile('print("hello")', '<string>', 'exec')  # Dangerous!
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Forbidden function call: 'compile" in error  # May include () or not

    def test_import_usage_rejected(self):
        """Test that __import__() usage is rejected."""
        code = """
import pandas as pd

def strategy(data):
    os = __import__('os')  # Dangerous bypass!
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Forbidden function call: '__import__" in error  # May include () or not

    def test_open_usage_rejected(self):
        """Test that open() (file I/O) is rejected."""
        code = """
import pandas as pd

def strategy(data):
    with open('/etc/passwd', 'r') as f:  # Dangerous!
        content = f.read()
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Forbidden function call: 'open" in error  # May include () or not

    def test_getattr_usage_rejected(self):
        """Test that getattr() (introspection) is rejected."""
        code = """
import pandas as pd

def strategy(data):
    df = pd.DataFrame()
    method = getattr(df, '__class__')  # Dangerous introspection!
    return df
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Forbidden function call: 'getattr" in error  # May include () or not

    def test_magic_method_access_rejected(self):
        """Test that magic method access is rejected."""
        code = """
import pandas as pd

def strategy(data):
    df = pd.DataFrame()
    df.__class__.__bases__  # Dangerous introspection!
    return df
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "__class__" in error or "__bases__" in error
        assert "magic" in error.lower() or "forbidden" in error.lower()

    def test_private_attribute_access_rejected(self):
        """Test that private attribute access is rejected."""
        code = """
import pandas as pd

def strategy(data):
    df = pd.DataFrame()
    df._data  # Private attribute access!
    return df
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "_data" in error
        assert "private" in error.lower() or "forbidden" in error.lower()

    def test_wildcard_import_rejected(self):
        """Test that wildcard imports are rejected."""
        code = """
from pandas import *  # Wildcard import not allowed

def strategy(data):
    return DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Wildcard imports are not allowed" in error

    def test_empty_code_rejected(self):
        """Test that empty code is rejected."""
        code = ""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "empty" in error.lower()

    def test_comments_only_rejected(self):
        """Test that code with only comments is rejected."""
        code = """
# This is a comment
# Another comment
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "only comments" in error.lower()

    def test_syntax_error_rejected(self):
        """Test that code with syntax errors is rejected."""
        code = """
import pandas as pd
def strategy(data)  # Missing colon
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Syntax error" in error or "parse" in error.lower()

    def test_allowed_pandas_operations(self):
        """Test that common pandas operations are allowed."""
        code = """
import pandas as pd
import numpy as np

def strategy(data):
    close = data.get('close')

    # Common pandas operations
    sma = close.rolling(20).mean()
    std = close.rolling(20).std()
    upper = sma + 2 * std
    lower = sma - 2 * std

    # Boolean operations
    signal = (close < lower) | (close > upper)

    # Data manipulation
    result = pd.concat([close, signal], axis=1)
    merged = pd.merge(result, pd.DataFrame(), how='left', on='date')

    return signal
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is True
        assert error == ""

    def test_allowed_numpy_operations(self):
        """Test that common numpy operations are allowed."""
        code = """
import numpy as np
import pandas as pd

def strategy(data):
    close = data.get('close')

    # Numpy operations
    values = close.values
    mean_val = np.mean(values)
    std_val = np.std(values)
    max_val = np.max(values)
    min_val = np.min(values)
    abs_val = np.abs(values)

    # Create signal
    signal = close > mean_val
    return signal
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is True
        assert error == ""

    def test_allowed_math_operations(self):
        """Test that math module operations are allowed."""
        code = """
import math
import pandas as pd

def strategy(data):
    close = data.get('close')

    # Math operations
    value = 100.0
    sqrt_val = math.sqrt(value)
    log_val = math.log(value)
    exp_val = math.exp(1.0)

    signal = close > sqrt_val
    return signal
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is True
        assert error == ""

    def test_validation_summary(self):
        """Test that validation summary provides complete security model info."""
        summary = get_validation_summary()

        # Check required keys
        assert 'allowed_modules' in summary
        assert 'forbidden_modules' in summary
        assert 'forbidden_builtins' in summary
        assert 'security_model' in summary
        assert 'validation_layers' in summary

        # Check security model
        assert summary['security_model'] == 'whitelist'

        # Check allowed modules
        assert 'pandas' in summary['allowed_modules']
        assert 'numpy' in summary['allowed_modules']
        assert 'finlab' in summary['allowed_modules']

        # Check forbidden modules
        assert 'os' in summary['forbidden_modules']
        assert 'sys' in summary['forbidden_modules']
        assert 'subprocess' in summary['forbidden_modules']

        # Check forbidden builtins
        assert 'eval' in summary['forbidden_builtins']
        assert 'exec' in summary['forbidden_builtins']
        assert 'compile' in summary['forbidden_builtins']

    def test_unauthorized_pandas_import(self):
        """Test that unauthorized pandas imports are rejected."""
        code = """
from pandas import read_pickle  # Not in whitelist

def strategy(data):
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Unauthorized import from 'pandas'" in error
        assert "read_pickle" in error

    def test_relative_imports_rejected(self):
        """Test that relative imports are rejected."""
        code = """
from . import something  # Relative import

def strategy(data):
    return pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert "Relative imports are not allowed" in error


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
