# Value factor testing phase

from finlab import data
from finlab import backtest

close = data.get('price:收盤價')
vol = data.get('price:成交股數')
pe_ratio = data.get('price_earning_ratio:本益比')

# Value factor: Low P/E stocks
value_score = 1 / (pe_ratio + 1)  # Inverse P/E (avoid division by zero)

# Liquidity filter
liquidity_filter = (close * vol).average(20) > 150_000_000
price_filter = close > 10

# Combine
cond_all = liquidity_filter & price_filter
cond_all = cond_all * value_score
cond_all = cond_all[cond_all > 0].is_largest(10)

# Set as position signal for iteration engine
position = cond_all

report = backtest.sim(position, resample="M", fee_ratio=1.425/1000/3,
                      stop_loss=0.08, take_profit=0.5, position_limit=0.10,
                      name="Value_PE")

print(f"年化報酬率: {report.metrics.annual_return():.2%}")
print(f"夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"最大回撤: {report.metrics.max_drawdown():.2%}")