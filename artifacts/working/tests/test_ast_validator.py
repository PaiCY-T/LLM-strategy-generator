"""
Test Suite for AST Security Validator

Tests edge cases and security boundary conditions for the validator.
"""

import ast_validator


def test_valid_operations():
    """Test that valid operations pass validation."""
    print("\n" + "="*60)
    print("VALID OPERATIONS - Should Pass")
    print("="*60)

    test_cases = [
        ("Basic pandas operations", """
import pandas as pd
import numpy as np

def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    sma = close.rolling(20).mean()
    return (close > sma) & (volume > volume.rolling(20).mean())
"""),
        ("Math operations", """
import numpy as np

def calculate(x, y):
    result = (x + y) * 2 - 3 / 4
    power = x ** 2
    return result + power
"""),
        ("List comprehensions", """
import pandas as pd

def process(data):
    values = [x * 2 for x in range(10)]
    squares = [x**2 for x in values if x > 5]
    return pd.Series(squares)
"""),
        ("Lambda functions", """
import pandas as pd

def strategy(data):
    close = data.get('close')
    transformed = close.apply(lambda x: x * 1.1)
    return transformed > 100
"""),
        ("Datetime operations", """
import datetime
import pandas as pd

def time_filter(data):
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    return data.get('close') > 100
"""),
    ]

    for name, code in test_cases:
        is_valid, error = ast_validator.validate_strategy_code(code)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"\n{status} - {name}")
        if error:
            print(f"  Unexpected error: {error}")


def test_security_violations():
    """Test that security violations are properly blocked."""
    print("\n" + "="*60)
    print("SECURITY VIOLATIONS - Should Fail")
    print("="*60)

    test_cases = [
        ("exec() call", """
exec('malicious_code()')
"""),
        ("eval() call", """
result = eval('1 + 1')
"""),
        ("compile() call", """
code_obj = compile('print("x")', '<string>', 'exec')
"""),
        ("__import__() call", """
os = __import__('os')
os.system('ls')
"""),
        ("open() file access", """
with open('/etc/passwd', 'r') as f:
    data = f.read()
"""),
        ("os module import", """
import os
os.system('rm -rf /')
"""),
        ("subprocess module", """
import subprocess
subprocess.call(['ls', '-l'])
"""),
        ("socket module", """
import socket
s = socket.socket()
"""),
        ("requests module", """
import requests
requests.get('http://evil.com')
"""),
        ("pickle module", """
import pickle
data = pickle.loads(malicious_data)
"""),
        ("getattr introspection", """
import pandas as pd
df = pd.DataFrame()
cls = getattr(df, '__class__')
"""),
        ("Magic method access", """
import pandas as pd
df = pd.DataFrame()
bases = df.__class__.__bases__
"""),
        ("Private attribute access", """
import pandas as pd
df = pd.DataFrame()
internal = df._data
"""),
        ("Wildcard import", """
from pandas import *
"""),
        ("Unauthorized module", """
import json
data = json.loads('{}')
"""),
        ("sys module", """
import sys
sys.exit(0)
"""),
        ("urllib module", """
import urllib
urllib.request.urlopen('http://evil.com')
"""),
        ("Unauthorized pandas attribute", """
from pandas import read_csv
df = read_csv('/etc/passwd')
"""),
    ]

    for name, code in test_cases:
        is_valid, error = ast_validator.validate_strategy_code(code)
        status = "✅ PASS" if not is_valid else "❌ FAIL"
        print(f"\n{status} - {name}")
        if is_valid:
            print(f"  ERROR: Should have been blocked!")
        else:
            print(f"  Blocked: {error.split(':')[0]}...")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n" + "="*60)
    print("EDGE CASES")
    print("="*60)

    test_cases = [
        ("Empty code", "", False),
        ("Whitespace only", "   \n\n   ", False),
        ("Comments only", "# This is a comment\n# Another comment", False),
        ("Syntax error", "def broken(", False),
        ("Invalid Python", "this is not python code", False),
        ("Nested function definitions", """
def outer():
    def inner():
        return 42
    return inner()
""", True),
        ("Complex nested expressions", """
import pandas as pd

def strategy(data):
    close = data.get('close')
    result = (
        (close > close.rolling(20).mean()) &
        (close < close.rolling(50).mean()) &
        (close.shift(1) < close)
    )
    return result
""", True),
        ("Dictionary comprehension", """
import pandas as pd

def process(data):
    mapping = {k: v*2 for k, v in enumerate(range(10))}
    return pd.Series(mapping)
""", True),
        ("Generator expression", """
import pandas as pd

def process(data):
    gen = (x**2 for x in range(10))
    return pd.Series(list(gen))
""", True),
        ("Multiple imports", """
import pandas as pd
import numpy as np
from datetime import datetime
from math import sqrt

def strategy(data):
    return data.get('close') > sqrt(100)
""", True),
    ]

    for name, code, should_pass in test_cases:
        is_valid, error = ast_validator.validate_strategy_code(code)
        expected = "PASS" if should_pass else "FAIL"
        actual = "PASS" if is_valid else "FAIL"
        status = "✅" if (should_pass == is_valid) else "❌"
        print(f"\n{status} - {name}")
        print(f"  Expected: {expected}, Got: {actual}")
        if error and not should_pass:
            print(f"  Error: {error.split(chr(10))[0]}...")


def test_real_world_strategies():
    """Test realistic trading strategy code."""
    print("\n" + "="*60)
    print("REAL-WORLD STRATEGY EXAMPLES")
    print("="*60)

    test_cases = [
        ("Moving Average Crossover", """
import pandas as pd
import numpy as np

def strategy(data):
    close = data.get('close')
    fast_ma = close.rolling(10).mean()
    slow_ma = close.rolling(30).mean()
    return fast_ma > slow_ma
"""),
        ("RSI Strategy", """
import pandas as pd
import numpy as np

def strategy(data):
    close = data.get('close')
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return (rsi < 30) | (rsi > 70)
"""),
        ("Bollinger Bands", """
import pandas as pd
import numpy as np

def strategy(data):
    close = data.get('close')
    sma = close.rolling(20).mean()
    std = close.rolling(20).std()
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    return (close < lower) | (close > upper)
"""),
        ("Volume-Price Strategy", """
import pandas as pd
import numpy as np

def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    price_change = close.pct_change()
    volume_ma = volume.rolling(20).mean()
    high_volume = volume > volume_ma * 1.5
    return high_volume & (price_change > 0.02)
"""),
    ]

    for name, code in test_cases:
        is_valid, error = ast_validator.validate_strategy_code(code)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"\n{status} - {name}")
        if error:
            print(f"  Error: {error}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("AST SECURITY VALIDATOR - COMPREHENSIVE TEST SUITE")
    print("="*60)

    test_valid_operations()
    test_security_violations()
    test_edge_cases()
    test_real_world_strategies()

    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
