"""Debug script to inspect finlab metrics object structure"""
from finlab import data
from finlab.backtest import sim

# Load a simple strategy
close = data.get('etl:adj_close')
position = close.pct_change(20).is_largest(10)

# Run backtest
report = sim(position, resample="Q", upload=False)

# Get the metrics object
metrics = report.metrics

print("="*80)
print("FINLAB METRICS OBJECT INSPECTION")
print("="*80)
print(f"\nMetrics type: {type(metrics)}")
print(f"Metrics class: {metrics.__class__.__name__}")

print("\n" + "="*80)
print("AVAILABLE ATTRIBUTES AND METHODS:")
print("="*80)
attrs = [attr for attr in dir(metrics) if not attr.startswith('_')]
for attr in sorted(attrs):
    if hasattr(metrics, attr):
        value = getattr(metrics, attr)
        is_method = callable(value)
        type_name = type(value).__name__
        print(f"  - {attr:30s} {'[METHOD]' if is_method else '[ATTR]':10s} (type: {type_name})")

        # If it's not a method and not a complex type, show the value
        if not is_method and type_name in ['int', 'float', 'str', 'bool', 'NoneType']:
            print(f"      Value: {value}")

print("\n" + "="*80)
print("TRYING TO ACCESS KEY METRICS:")
print("="*80)

# Sharpe ratio
print("\n1. Sharpe Ratio:")
if hasattr(metrics, 'sharpe'):
    sharpe = metrics.sharpe
    print(f"   metrics.sharpe = {sharpe} (type: {type(sharpe).__name__})")
    if callable(sharpe):
        try:
            result = sharpe()
            print(f"   metrics.sharpe() = {result}")
        except Exception as e:
            print(f"   Error calling sharpe(): {e}")

# Total return
print("\n2. Total Return:")
if hasattr(metrics, 'total_return'):
    total_return = metrics.total_return
    print(f"   metrics.total_return = {total_return} (type: {type(total_return).__name__})")
elif hasattr(metrics, 'cagr'):
    cagr = metrics.cagr
    print(f"   metrics.cagr = {cagr} (type: {type(cagr).__name__})")

# Max drawdown
print("\n3. Max Drawdown:")
if hasattr(metrics, 'max_drawdown'):
    max_dd = metrics.max_drawdown
    print(f"   metrics.max_drawdown = {max_dd} (type: {type(max_dd).__name__})")
elif hasattr(metrics, 'mdd'):
    mdd = metrics.mdd
    print(f"   metrics.mdd = {mdd} (type: {type(mdd).__name__})")

# Win rate
print("\n4. Win Rate:")
if hasattr(metrics, 'win_rate'):
    win_rate = metrics.win_rate
    print(f"   metrics.win_rate = {win_rate} (type: {type(win_rate).__name__})")

print("\n" + "="*80)
print("CALLING get_stats() METHOD:")
print("="*80)
try:
    stats = report.get_stats()
    print(f"Type: {type(stats).__name__}")
    if hasattr(stats, 'to_dict'):
        stats_dict = stats.to_dict()
        print("Stats dictionary keys:")
        for key in sorted(stats_dict.keys()):
            print(f"  - {key}: {stats_dict[key]}")
    else:
        print(stats)
except Exception as e:
    print(f"Error calling get_stats(): {e}")

print("\n" + "="*80)
