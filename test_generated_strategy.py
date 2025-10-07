import os
import sys

# Set API token in environment BEFORE importing finlab
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'

# Import finlab with token already set
from finlab import data
from finlab.backtest import sim
import pandas as pd

print("=" * 60)
print("Testing Generated Strategy - Iteration 0")
print("=" * 60)

try:
    # Load data
    close = data.get('price:收盤價')
    volume = data.get('price:成交股數')
    trading_value = data.get('price:成交金額')
    foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')
    revenue_yoy = data.get('etl:monthly_revenue:revenue_yoy')

    # Calculate momentum factor
    returns_20d = close.pct_change(20)
    momentum_factor = returns_20d.shift(1)

    # Calculate volume surge factor
    avg_volume_60d = volume.rolling(60).mean()
    volume_surge = (volume / avg_volume_60d).shift(1)

    # Calculate foreign institutional strength factor
    foreign_factor = foreign_strength.rolling(10).mean().shift(1)

    # Calculate revenue growth factor
    revenue_factor = revenue_yoy.rolling(3).mean().shift(1)

    # Combine factors with weights
    combined_factor = (momentum_factor * 0.3 +
                      volume_surge * 0.2 +
                      foreign_factor * 0.3 +
                      revenue_factor * 0.2)

    # Apply liquidity filter
    liquidity_filter = trading_value.rolling(20).mean() > 100_000_000

    # Apply additional filters
    price_filter = close > 20  # Avoid penny stocks
    volume_filter = volume.rolling(20).mean() > 1_000_000  # Minimum volume

    # Combine all filters
    final_filter = liquidity_filter & price_filter & volume_filter

    # Select top 10 stocks based on combined factor
    position = combined_factor[final_filter].is_largest(10)

    # Run backtest
    report = sim(position, resample="Q", upload=False, stop_loss=0.08)

    # Print results
    print("\n✅ Strategy executed successfully!")
    print(f"Annual Return: {report.metrics.annual_return():.2%}")
    print(f"Sharpe Ratio: {report.metrics.sharpe_ratio():.3f}")
    print(f"Max Drawdown: {report.metrics.max_drawdown():.2%}")
    print(f"Win Rate: {report.metrics.win_rate():.2%}")
    print(f"Total Trades: {len(report.trades)}")

    # Record result
    result = {
        "iteration": 0,
        "status": "success",
        "annual_return": report.metrics.annual_return(),
        "sharpe_ratio": report.metrics.sharpe_ratio(),
        "max_drawdown": report.metrics.max_drawdown(),
        "win_rate": report.metrics.win_rate(),
        "total_trades": len(report.trades)
    }

except Exception as e:
    print(f"\n❌ Strategy execution failed!")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

    # Record failure
    result = {
        "iteration": 0,
        "status": "failed",
        "error": str(e)
    }
