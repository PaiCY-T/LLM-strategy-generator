"""Debug script to inspect finlab report object structure"""
from finlab import data
from finlab.backtest import sim
import pandas as pd

# Load a simple strategy
close = data.get('etl:adj_close')
position = close.pct_change(20).is_largest(10)

# Run backtest
report = sim(position, resample="Q", upload=False)

# Inspect the report object
print("="*80)
print("FINLAB REPORT OBJECT INSPECTION")
print("="*80)
print(f"\nReport type: {type(report)}")
print(f"Report class: {report.__class__.__name__}")

print("\n" + "="*80)
print("AVAILABLE ATTRIBUTES AND METHODS:")
print("="*80)
attrs = [attr for attr in dir(report) if not attr.startswith('_')]
for attr in sorted(attrs):
    print(f"  - {attr}")

print("\n" + "="*80)
print("CHECKING METRIC ATTRIBUTES:")
print("="*80)

# Try different possible attribute names for Sharpe ratio
sharpe_attrs = ['sharpe_ratio', 'sharpe', 'sharp_ratio', '_sharpe', 'get_sharpe']
for attr_name in sharpe_attrs:
    if hasattr(report, attr_name):
        value = getattr(report, attr_name)
        print(f"  ✓ {attr_name}: {value} (type: {type(value).__name__})")
        # If it's a method, try calling it
        if callable(value):
            try:
                result = value()
                print(f"    Called {attr_name}(): {result}")
            except Exception as e:
                print(f"    Error calling {attr_name}(): {e}")

# Try different possible attribute names for total return
return_attrs = ['total_return', 'return', 'returns', 'cumulative_return', 'cum_return', 'get_return']
for attr_name in return_attrs:
    if hasattr(report, attr_name):
        value = getattr(report, attr_name)
        print(f"  ✓ {attr_name}: {value} (type: {type(value).__name__})")
        if callable(value):
            try:
                result = value()
                print(f"    Called {attr_name}(): {result}")
            except Exception as e:
                print(f"    Error calling {attr_name}(): {e}")

# Try different possible attribute names for max drawdown
dd_attrs = ['max_drawdown', 'drawdown', 'maximum_drawdown', 'maxdrawdown', 'get_drawdown']
for attr_name in dd_attrs:
    if hasattr(report, attr_name):
        value = getattr(report, attr_name)
        print(f"  ✓ {attr_name}: {value} (type: {type(value).__name__})")
        if callable(value):
            try:
                result = value()
                print(f"    Called {attr_name}(): {result}")
            except Exception as e:
                print(f"    Error calling {attr_name}(): {e}")

# Try different possible attribute names for win rate
wr_attrs = ['win_rate', 'winning_rate', 'win_pct', 'winrate', 'win_percentage']
for attr_name in wr_attrs:
    if hasattr(report, attr_name):
        value = getattr(report, attr_name)
        print(f"  ✓ {attr_name}: {value} (type: {type(value).__name__})")
        if callable(value):
            try:
                result = value()
                print(f"    Called {attr_name}(): {result}")
            except Exception as e:
                print(f"    Error calling {attr_name}(): {e}")

print("\n" + "="*80)
print("CHECKING COMMON PROPERTIES:")
print("="*80)

common_props = ['stats', 'summary', 'metrics', 'performance', 'df', 'data']
for prop in common_props:
    if hasattr(report, prop):
        value = getattr(report, prop)
        print(f"\n  {prop}:")
        print(f"    Type: {type(value).__name__}")
        if isinstance(value, (pd.DataFrame, pd.Series)):
            print(f"    Shape: {value.shape}")
            print(f"    Columns: {list(value.columns) if hasattr(value, 'columns') else 'N/A'}")
        elif callable(value):
            print(f"    (callable method)")
        else:
            print(f"    Value: {value}")

print("\n" + "="*80)
