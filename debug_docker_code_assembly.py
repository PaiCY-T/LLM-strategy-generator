"""
Debug script to examine what code is actually being sent to Docker.
This will help us understand Issue #5 (Docker mock data initialization failure).
"""

import sys
sys.path.insert(0, '/mnt/c/Users/jnpi/documents/finlab')

# Read the generated strategy from iteration 1
with open('/mnt/c/Users/jnpi/documents/finlab/generated_strategy_loop_iter1.py', 'r') as f:
    llm_generated_code = f.read()

print("=" * 80)
print("LLM-GENERATED STRATEGY CODE (first 500 chars):")
print("=" * 80)
print(llm_generated_code[:500])
print(f"\n... (total length: {len(llm_generated_code)} chars)")
print()

# Now let's recreate what autonomous_loop.py does to assemble the complete code
import pandas as pd
import numpy as np

# This is the data_setup template from autonomous_loop.py:195-333
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
        self._key_map = {{
            'etl:adj_close': self.close,
            'price:成交金額': self.volume,
            'etl:market_value': self.market_value,
            'fundamental_features:ROE稅後': self.roe,
            'monthly_revenue:去年同月增減(%)': self.revenue_yoy,
            'institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)': self.foreign_net_buy,
        }}

    def get(self, key, default=None):
        \"\"\"Mock .get() to map string keys to data attributes.\"\"\"
        if key not in self._key_map:
            # Return a default random DataFrame to prevent crashes on unknown keys
            return pd.DataFrame(
                np.random.rand(252, 10),
                index=self.close.index,
                columns=self.close.columns
            )
        return self._key_map.get(key, default)

    def indicator(self, name):
        \"\"\"Mock .indicator() for technical indicators.\"\"\"
        # For RSI, return a DataFrame between 0 and 100
        if name.upper() == 'RSI':
            return pd.DataFrame(
                np.random.uniform(0, 100, (252, 10)),
                index=self.close.index,
                columns=self.close.columns
            )
        # Default for other indicators
        return pd.DataFrame(
            np.random.randn(252, 10),
            index=self.close.index,
            columns=self.close.columns
        )

data = Data()

# Add FinLab-specific methods to pandas DataFrame
# These methods are used by generated strategies but don't exist in standard pandas
def is_largest(df, n):
    \"\"\"Mock FinLab's is_largest method - returns top N stocks as boolean DataFrame\"\"\"
    # For each row (date), mark top N stocks as True
    result = pd.DataFrame(False, index=df.index, columns=df.columns)
    for date in df.index:
        row = df.loc[date]
        top_n_stocks = row.nlargest(n).index
        result.loc[date, top_n_stocks] = True
    return result

def is_smallest(df, n):
    \"\"\"Mock FinLab's is_smallest method - returns bottom N stocks as boolean DataFrame\"\"\"
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

metrics_extraction = """

# Execute strategy and extract metrics
if 'report' in locals():
    # Extract metrics from report object
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
"""

# Assemble complete code
complete_code = data_setup + "\n" + llm_generated_code + "\n" + metrics_extraction

print("=" * 80)
print("COMPLETE CODE ASSEMBLY CHECK:")
print("=" * 80)
print(f"data_setup length: {len(data_setup)} chars")
print(f"LLM code length: {len(llm_generated_code)} chars")
print(f"metrics_extraction length: {len(metrics_extraction)} chars")
print(f"complete_code length: {len(complete_code)} chars")
print()

# Check for {{}} in complete_code
if '{{' in complete_code or '}}' in complete_code:
    print("⚠️  WARNING: Found {{}} in complete_code!")
    count = complete_code.count('{{') + complete_code.count('}}')
    print(f"   Total occurrences: {count}")
else:
    print("✅ No {{}} found in complete_code")

print()
print("=" * 80)
print("FIRST 1000 CHARS OF COMPLETE CODE:")
print("=" * 80)
print(complete_code[:1000])
print()

# Try to execute the complete code to see if there's a Python error
print("=" * 80)
print("ATTEMPTING TO EXECUTE COMPLETE CODE:")
print("=" * 80)
try:
    exec(complete_code)
    print("✅ Code executed successfully!")
    print(f"   signal = {signal}")
except Exception as e:
    print(f"❌ Execution failed: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
