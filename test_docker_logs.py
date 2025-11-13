#!/usr/bin/env python3
"""
Test to capture actual Docker container logs for debugging.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.sandbox.docker_executor import DockerExecutor

# Create the same code that autonomous_loop sends to Docker
data_setup = """
import pandas as pd
import numpy as np

# Mock data object for sandbox execution
class Data:
    def __init__(self):
        # Create mock data for 10 stocks across 252 trading days
        dates = pd.date_range('2020-01-01', periods=252, freq='D')
        stocks = ['STOCK_{:04d}'.format(i) for i in range(10)]

        # Create DataFrames (stocks x dates) instead of Series
        # This matches the real FinLab data structure
        self.close = pd.DataFrame(
            np.random.randn(252, 10).cumsum(axis=0) + 100,
            index=dates,
            columns=stocks
        )
        self.open = self.close + np.random.randn(252, 10) * 0.5
        self.high = self.close + abs(np.random.randn(252, 10)) * 1.0
        self.low = self.close - abs(np.random.randn(252, 10)) * 1.0
        self.volume = pd.DataFrame(
            np.random.randint(1000000, 10000000, (252, 10)),
            index=dates,
            columns=stocks
        )

        # Simple mock for market value and other dataframes
        self.market_value = self.close * self.volume
        self.roe = pd.DataFrame(
            np.random.uniform(5, 20, (252, 10)),
            index=dates,
            columns=stocks
        )
        self.revenue_yoy = pd.DataFrame(
            np.random.uniform(-10, 30, (252, 10)),
            index=dates,
            columns=stocks
        )
        self.foreign_net_buy = pd.DataFrame(
            np.random.randint(-1e6, 1e6, (252, 10)),
            index=dates,
            columns=stocks
        )

        # Key mapping for the .get() method
        self._key_map = {
            'etl:adj_close': self.close,
            'price:成交金額': self.volume,
            'etl:market_value': self.market_value,
            'fundamental_features:ROE稅後': self.roe,
            'monthly_revenue:去年同月增減(%)': self.revenue_yoy,
            'institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)': self.foreign_net_buy,
        }

    def get(self, key, default=None):
        if key not in self._key_map:
            return pd.DataFrame(
                np.random.rand(252, 10),
                index=self.close.index,
                columns=self.close.columns
            )
        return self._key_map.get(key, default)

    def indicator(self, name, *args, **kwargs):
        if name.upper() == 'RSI':
            return pd.DataFrame(
                np.random.uniform(0, 100, (252, 10)),
                index=self.close.index,
                columns=self.close.columns
            )
        return pd.DataFrame(
            np.random.randn(252, 10),
            index=self.close.index,
            columns=self.close.columns
        )

data = Data()

# Add FinLab-specific methods to pandas DataFrame
def is_largest(df, n):
    result = pd.DataFrame(False, index=df.index, columns=df.columns)
    for date in df.index:
        row = df.loc[date]
        top_n_stocks = row.nlargest(n).index
        result.loc[date, top_n_stocks] = True
    return result

def is_smallest(df, n):
    result = pd.DataFrame(False, index=df.index, columns=df.columns)
    for date in df.index:
        row = df.loc[date]
        bottom_n_stocks = row.nsmallest(n).index
        result.loc[date, bottom_n_stocks] = True
    return result

# Monkey patch DataFrame to add FinLab methods
pd.DataFrame.is_largest = is_largest
pd.DataFrame.is_smallest = is_smallest

# Mock sim function for sandbox execution
def sim(position, resample='D', upload=False, stop_loss=None):
    report = type('obj', (object,), {
        'total_return': float(np.random.randn() * 0.5),
        'annual_return': float(np.random.randn() * 0.3),
        'sharpe_ratio': float(abs(np.random.randn() * 2)),
        'max_drawdown': float(-abs(np.random.randn() * 0.5)),
        'win_rate': float(abs(np.random.randn() * 0.3 + 0.5)),
        'position_count': 252
    })()
    return report

"""

# Read the actual strategy from iter1
with open('generated_strategy_loop_iter1.py', 'r') as f:
    strategy_code = f.read()

metrics_extraction = """
import json

# Execute strategy and extract metrics
if 'report' in locals():
    signal = {
        'total_return': getattr(report, 'total_return', 0.0),
        'annual_return': getattr(report, 'annual_return', 0.0),
        'sharpe_ratio': getattr(report, 'sharpe_ratio', 0.0),
        'max_drawdown': getattr(report, 'max_drawdown', 0.0),
        'win_rate': getattr(report, 'win_rate', 0.0),
        'position_count': getattr(report, 'position_count', 0)
    }
else:
    signal = {}

# Output signal in parseable format for DockerExecutor (Issue #5 fix)
print(f"__SIGNAL_JSON_START__{json.dumps(signal)}__SIGNAL_JSON_END__")
"""

complete_code = data_setup + "\n" + strategy_code + "\n" + metrics_extraction

print("=" * 80)
print("TESTING DOCKER EXECUTION WITH COMPLETE CODE")
print("=" * 80)
print(f"Complete code length: {len(complete_code)}")
print(f"Has 'data = Data()': {'data = Data()' in complete_code}")
print(f"Has 'class Data': {'class Data' in complete_code}")
print()

# Execute with Docker
executor = DockerExecutor()
result = executor.execute(code=complete_code, timeout=60, validate=True)

print("=" * 80)
print("DOCKER EXECUTION RESULT:")
print("=" * 80)
print(f"Success: {result.get('success')}")
print(f"Signal: {result.get('signal')}")
print(f"Error: {result.get('error')}")
print()
print("=" * 80)
print("CONTAINER LOGS:")
print("=" * 80)
print(result.get('logs', 'NO LOGS CAPTURED'))
print("=" * 80)

if not result.get('success'):
    print("\n❌ Docker execution FAILED")
    print("This is the actual error we need to fix!")
else:
    print("\n✅ Docker execution SUCCEEDED")
    print("Issue #5 fix is working correctly!")
