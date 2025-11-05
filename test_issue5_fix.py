"""
Test Issue #5 fix - Docker result capture
"""

import sys
sys.path.insert(0, '/mnt/c/Users/jnpi/documents/finlab')

from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig
import pandas as pd
import numpy as np

# Read the generated strategy
with open('/mnt/c/Users/jnpi/documents/finlab/generated_strategy_loop_iter1.py', 'r') as f:
    llm_generated_code = f.read()

# Rebuild data_setup with the FIXED template
data_setup = f"""
import pandas as pd
import numpy as np

# Mock data object for sandbox execution
class Data:
    def __init__(self):
        # Create mock data for 10 stocks across 252 trading days
        dates = pd.date_range('2020-01-01', periods=252, freq='D')
        stocks = ['STOCK_{{:04d}}'.format(i) for i in range(10)]

        # Create DataFrames (stocks x dates) instead of Series
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

        self._key_map = {{
            'etl:adj_close': self.close,
            'price:成交金額': self.volume,
            'etl:market_value': self.market_value,
            'fundamental_features:ROE稅後': self.roe,
            'monthly_revenue:去年同月增減(%)': self.revenue_yoy,
            'institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)': self.foreign_net_buy,
        }}

    def get(self, key, default=None):
        if key not in self._key_map:
            return pd.DataFrame(
                np.random.rand(252, 10),
                index=self.close.index,
                columns=self.close.columns
            )
        return self._key_map.get(key, default)

    def indicator(self, name):
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

pd.DataFrame.is_largest = is_largest
pd.DataFrame.is_smallest = is_smallest

def sim(position, resample='D', upload=False, stop_loss=None):
    report = type('obj', (object,), {{
        'total_return': float(np.random.randn() * 0.5),
        'annual_return': float(np.random.randn() * 0.3),
        'sharpe_ratio': float(abs(np.random.randn() * 2)),
        'max_drawdown': float(-abs(np.random.randn() * 0.5)),
        'win_rate': float(abs(np.random.randn() * 0.3 + 0.5)),
        'position_count': 252
    }})()
    return report

"""

# NEW FIXED metrics_extraction template
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

# Assemble complete code
complete_code = data_setup + "\n" + llm_generated_code + "\n" + metrics_extraction

print("=" * 80)
print("TESTING ISSUE #5 FIX - DOCKER RESULT CAPTURE")
print("=" * 80)
print(f"Code length: {len(complete_code)} chars")
print()

# Initialize Docker executor
config = DockerConfig.from_yaml()
executor = DockerExecutor(config)

print("Executing code in Docker container with fixed result parsing...")
print()

result = executor.execute(
    code=complete_code,
    timeout=60,
    validate=True
)

print("=" * 80)
print("DOCKER EXECUTION RESULT (AFTER FIX):")
print("=" * 80)
print(f"Success: {result['success']}")
print(f"Signal: {result.get('signal')}")
print(f"Error: {result.get('error')}")
print(f"Execution time: {result.get('execution_time'):.2f}s")
print()

# Verify the fix
if result['success'] and result.get('signal') is not None:
    print("✅ SUCCESS: Signal is now properly parsed from Docker logs!")
    print(f"   Signal keys: {list(result['signal'].keys())}")
    print(f"   Total return: {result['signal'].get('total_return')}")
    print()
    print("Issue #5 is FIXED! ✅")
else:
    print("❌ FAILED: Signal is still None")
    print()
    if 'logs' in result:
        print("Container logs:")
        print(result['logs'][:500])
