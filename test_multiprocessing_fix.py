#!/usr/bin/env python3
"""
快速測試 Multiprocessing Fix

驗證修復後的 BacktestExecutor 能否在合理時間內完成測試
預期時間：~20-30秒（vs 修復前的 900秒+ timeout）
"""

import sys
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, '.')

from finlab import data, backtest
from src.backtest.executor import BacktestExecutor
from src.factor_graph.strategy import Strategy
from src.factor_library.registry import FactorRegistry

def create_template_strategy():
    """Create template Factor Graph strategy (momentum + breakout + trailing stop)."""
    registry = FactorRegistry.get_instance()

    # Create strategy
    strategy = Strategy(id="template_test", generation=0)

    # Add momentum factor (root)
    momentum_factor = registry.create_factor(
        "momentum_factor",
        parameters={"momentum_period": 20}
    )
    strategy.add_factor(momentum_factor, depends_on=[])

    # Add breakout factor (entry signal)
    breakout_factor = registry.create_factor(
        "breakout_factor",
        parameters={"entry_window": 20}
    )
    strategy.add_factor(breakout_factor, depends_on=[])

    # Add rolling trailing stop factor (stateless exit - Phase 2 fix)
    trailing_stop_factor = registry.create_factor(
        "rolling_trailing_stop_factor",
        parameters={"trail_percent": 0.10, "lookback_periods": 20}
    )
    strategy.add_factor(
        trailing_stop_factor,
        depends_on=[momentum_factor.id, breakout_factor.id]
    )

    return strategy

def main():
    print("=" * 80)
    print("Multiprocessing Fix 快速驗證測試")
    print("=" * 80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create template strategy
    print("創建 template 策略...")
    strategy = create_template_strategy()
    print(f"✓ 策略創建完成: {strategy.id}")
    print(f"  因子數量: {len(strategy.factors)}")
    print()

    # Create executor with 60s timeout (should be enough if fix works)
    print("執行 Factor Graph 回測 (timeout=60s)...")
    executor = BacktestExecutor(timeout=60)

    start_time = time.time()
    result = executor.execute_strategy(
        strategy=strategy,
        data=data,  # This is still passed but not used in subprocess
        sim=backtest.sim,
        resample="M"  # Monthly rebalancing (was causing 900s+ timeout)
    )
    elapsed = time.time() - start_time

    print()
    print("=" * 80)
    print("測試結果")
    print("=" * 80)
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"執行時間: {elapsed:.2f}秒")
    print()

    if result.success:
        print("✅ 回測成功！")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.4f}" if result.sharpe_ratio else "  Sharpe Ratio: N/A")
        print(f"  Total Return: {result.total_return:.4f}" if result.total_return else "  Total Return: N/A")
        print(f"  Max Drawdown: {result.max_drawdown:.4f}" if result.max_drawdown else "  Max Drawdown: N/A")
        print()

        if elapsed < 60:
            print(f"🎉 修復成功！執行時間從 900秒+ 降至 {elapsed:.2f}秒")
            print(f"   效能提升: {900 / elapsed:.1f}x faster!")
        else:
            print(f"⚠️  執行時間仍然較長: {elapsed:.2f}秒")
    else:
        print(f"❌ 回測失敗")
        print(f"  錯誤類型: {result.error_type}")
        print(f"  錯誤訊息: {result.error_message}")
        if result.stack_trace:
            print(f"  堆疊追蹤:")
            print(f"    {result.stack_trace[:200]}...")

    print("=" * 80)

    return 0 if result.success else 1

if __name__ == "__main__":
    sys.exit(main())
