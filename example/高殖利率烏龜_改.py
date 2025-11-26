from finlab import data
from finlab import backtest
from finlab import analysis

close = data.get("price:收盤價")
vol = data.get("price:成交股數")
sma20 = close.average(20)
sma60 = close.average(60)
rev = data.get("monthly_revenue:當月營收")

ope_earn = data.get("fundamental_features:營業利益率")
yield_ratio = data.get("price_earning_ratio:殖利率(%)")
boss_hold = data.get("internal_equity_changes:董監持有股數占比")
去年同月增減 = data.get("monthly_revenue:去年同月增減(%)")

# Optimized parameters from Optuna
yield_ratio_threshold = 5
sma_short_period = 26 # Optimized
sma_long_period = 61 # Optimized
ope_earn_threshold = 10
boss_hold_threshold = 10
vol_min_threshold = 38 * 1000
vol_max_threshold = 12890 * 1000
num_stocks = 20
stop_loss_param = 0.04
take_profit_param = 0.25
position_limit_param = 0.2
momentum_period = 80 # Optimized from experiment

sma_short = close.average(sma_short_period)
sma_long = close.average(sma_long_period)

cond1 = yield_ratio >= yield_ratio_threshold
cond2 = (close > sma_short) & (close > sma_long)
cond3 = rev.average(3) > rev.average(12)
cond4 = ope_earn >= ope_earn_threshold
cond5 = boss_hold >= boss_hold_threshold
cond6 = (vol.average(5) >= vol_min_threshold) & (vol.average(5) <= vol_max_threshold)

# Relative Strength Momentum
momentum_return = close.pct_change(momentum_period)
cond7 = momentum_return.rank(axis=1, pct=True) > 0.7 # Top 30% by relative strength

cond_all = cond1 & cond2 & cond3 & cond4 & cond5 & cond6 & cond7
cond_all = cond_all * 去年同月增減
position = cond_all[cond_all > 0].is_largest(num_stocks)

report = backtest.sim(position, resample="M", fee_ratio=1.425/1000/3, stop_loss=stop_loss_param, take_profit=take_profit_param, position_limit=position_limit_param, name="高殖利率烏龜_Optimized_Momentum", upload=True)
report.display()
print(f"年化報酬率: {report.metrics.annual_return():.2f}")
print(f"夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"最大回撤: {report.metrics.max_drawdown():.2f}")