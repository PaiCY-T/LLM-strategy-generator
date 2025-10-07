import os
import sys

# Set API token in environment
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'

import finlab
try:
    import finlab.login_process as lp
    lp.api_token = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'
    finlab.login(api_token='MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m')
except (EOFError, Exception):
    pass

from finlab import data
from finlab.backtest import sim
import pandas as pd

def std(series, window):
    return series.rolling(window).std()

# 1. Get the required data
top15_buy = data.get("etl:broker_transactions:top15_buy")
top15_sell = data.get("etl:broker_transactions:top15_sell")
balance_index = data.get("etl:broker_transactions:balance_index")

# 2. Calculate net_volume
net_volume = top15_buy - top15_sell

# 3. Generate Sharpe factors
sharpe20_net_volume = net_volume.rolling(20).mean() / std(net_volume, 20)
sharpe20_balance_index = balance_index.rolling(20).mean() / std(balance_index, 20)

# 4. 流動性篩選
trading_value = data.get("price:成交金額")
volume = data.get("price:成交股數")
issued_shares = data.get("internal_equity_changes:發行股數")
turnover_rate = (volume / issued_shares) * 100 # Calculate turnover rate as percentage

# Optimized liquidity filter parameters (from baseline)
tv_threshold = 60_000_000
volume_threshold = 3_000_000
turnover_rate_threshold = 1.0

liquidity_filter_tv = trading_value.rolling(20).mean() > tv_threshold
liquidity_filter_volume = volume.rolling(20).mean() > volume_threshold
liquidity_filter_turnover = turnover_rate.rolling(20).mean() > turnover_rate_threshold

liquidity_filter = liquidity_filter_tv & liquidity_filter_volume & liquidity_filter_turnover

# 5. Get RSI
rsi = data.indicator("RSI", timeperiod=14)

# Best ADX parameters from Optuna (from baseline)
adx_timeperiod = 27
adx = data.indicator("ADX", timeperiod=adx_timeperiod)

# Equal weighting for factors
num_factors = 4 # sharpe20_net_volume, sharpe20_balance_index, rsi, adx
equal_weight = 1 / num_factors

normalized_weight_net_volume = equal_weight
normalized_weight_balance_index = equal_weight
normalized_weight_rsi = equal_weight
normalized_weight_adx = equal_weight

# Rank factors before combining to ensure similar scale
ranked_sharpe20_net_volume = sharpe20_net_volume.rank(axis=1, pct=True)
ranked_sharpe20_balance_index = sharpe20_balance_index.rank(axis=1, pct=True)
ranked_rsi = rsi.rank(axis=1, pct=True)
ranked_adx = adx.rank(axis=1, pct=True)

combined_factor = (ranked_sharpe20_net_volume * normalized_weight_net_volume) + \
                  (ranked_sharpe20_balance_index * normalized_weight_balance_index) + \
                  (ranked_rsi * normalized_weight_rsi) + \
                  (ranked_adx * normalized_weight_adx)

# 6. Apply liquidity filter and select top stocks
position = combined_factor[liquidity_filter].is_largest(6)

# 7. Introduce stop-loss mechanism
stop_loss_percent = 0.08483336985698559 # Optimized stop-loss percentage from baseline

# 8. Run a backtest with quarterly rebalancing and upload=True
report = sim(position, resample="Q", upload=True, stop_loss=stop_loss_percent)

# 9. Report the metrics
print("年化報酬率:", report.metrics.annual_return())
print("夏普比率:", report.metrics.sharpe_ratio())
print("最大回撤:", report.metrics.max_drawdown())
