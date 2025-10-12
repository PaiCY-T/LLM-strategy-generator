# Iteration 0: Simple 20-day Momentum
# Testing basic price momentum with liquidity filter

from finlab import data
from finlab import backtest

close = data.get('price:收盤價')
vol = data.get('price:成交股數')

# Momentum factor: 20-day return
momentum_20d = (close / close.shift(20) - 1)

# Liquidity filter (CRITICAL: 150M TWD minimum daily value)
liquidity_filter = (close * vol).average(20) > 150_000_000

# Price filter (avoid penny stocks)
price_filter = close > 10

# Combine conditions
cond_all = liquidity_filter & price_filter
cond_all = cond_all * momentum_20d  # Weight by momentum score
cond_all = cond_all[cond_all > 0].is_largest(10)  # Select top 10 positive momentum

# Set as position signal for iteration engine
position = cond_all

# Backtest with realistic parameters
report = backtest.sim(
    position,
    resample="M",
    fee_ratio=1.425/1000/3,  # 0.1425% transaction cost
    stop_loss=0.08,
    take_profit=0.5,
    position_limit=0.10,  # Max 10% per position
    name="Momentum_20d_Iter0"
)

print(f"年化報酬率: {report.metrics.annual_return():.2%}")
print(f"夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"最大回撤: {report.metrics.max_drawdown():.2%}")