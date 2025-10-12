# Iteration 5: SMA20/SMA60 crossover momentum

from finlab import data
from finlab import backtest

close = data.get('price:收盤價')
vol = data.get('price:成交股數')

# Moving average crossover momentum
sma20 = close.average(20)
sma60 = close.average(60)
crossover_strength = (sma20 / sma60 - 1)  # Strength of crossover

# Liquidity filter
liquidity_filter = (close * vol).average(20) > 150_000_000
price_filter = close > 10

# Price above both MAs (uptrend confirmation)
uptrend_filter = (close > sma20) & (close > sma60)

# Combine
cond_all = liquidity_filter & price_filter & uptrend_filter
cond_all = cond_all * crossover_strength
cond_all = cond_all[cond_all > 0].is_largest(10)

# Set as position signal for iteration engine
position = cond_all

report = backtest.sim(position, resample="M", fee_ratio=1.425/1000/3,
                      stop_loss=0.08, take_profit=0.5, position_limit=0.10,
                      name="MA_Crossover_Iter5")

print(f"年化報酬率: {report.metrics.annual_return():.2%}")
print(f"夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"最大回撤: {report.metrics.max_drawdown():.2%}")