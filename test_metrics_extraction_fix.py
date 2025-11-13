"""Test script to verify the fixed MetricsExtractor works correctly"""
from finlab import data
from finlab.backtest import sim
from src.backtest.metrics import MetricsExtractor

print("="*80)
print("Testing Fixed MetricsExtractor")
print("="*80)

# Load a simple strategy
close = data.get('etl:adj_close')
position = close.pct_change(20).is_largest(10)

# Run backtest
print("\n[1] Running backtest...")
report = sim(position, resample="Q", upload=False)
print("✓ Backtest completed")

# Test the fixed MetricsExtractor
print("\n[2] Testing MetricsExtractor...")
extractor = MetricsExtractor()
metrics = extractor.extract_metrics(report)

print(f"\n[3] Extraction Results:")
print(f"  execution_success: {metrics.execution_success}")
print(f"  sharpe_ratio: {metrics.sharpe_ratio}")
print(f"  total_return: {metrics.total_return}")
print(f"  max_drawdown: {metrics.max_drawdown}")
print(f"  win_rate: {metrics.win_rate}")

# Verify against direct get_stats() call
print(f"\n[4] Verification against get_stats():")
stats = report.get_stats()
print(f"  direct daily_sharpe: {stats.get('daily_sharpe')}")
print(f"  direct total_return: {stats.get('total_return')}")
print(f"  direct max_drawdown: {stats.get('max_drawdown')}")
print(f"  direct win_ratio: {stats.get('win_ratio')}")

# Check if extraction matches
print(f"\n[5] Match Check:")
sharpe_match = metrics.sharpe_ratio == stats.get('daily_sharpe')
return_match = metrics.total_return == stats.get('total_return')
dd_match = metrics.max_drawdown == stats.get('max_drawdown')
wr_match = metrics.win_rate == stats.get('win_ratio')

print(f"  Sharpe ratio match: {sharpe_match} ✓" if sharpe_match else f"  Sharpe ratio match: {sharpe_match} ✗")
print(f"  Total return match: {return_match} ✓" if return_match else f"  Total return match: {return_match} ✗")
print(f"  Max drawdown match: {dd_match} ✓" if dd_match else f"  Max drawdown match: {dd_match} ✗")
print(f"  Win rate match: {wr_match} ✓" if wr_match else f"  Win rate match: {wr_match} ✗")

if all([sharpe_match, return_match, dd_match, wr_match]):
    print("\n" + "="*80)
    print("✅ SUCCESS: MetricsExtractor is working correctly!")
    print("="*80)
else:
    print("\n" + "="*80)
    print("❌ FAILURE: MetricsExtractor has issues")
    print("="*80)
