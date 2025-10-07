"""
改進版策略：多因子多樣化 + 法人動向 + 質量因子
基於719個Finlab資料集的完整分析
"""
import os
import sys

# Set API token in environment
os.environ['FINLAB_API_TOKEN'] = 'MfwPfl1ZRDJYEPCZbYH5ZQ9nHCfZW3T4ZeI1PuVakeimy5j717UDyXXRbvScfaO#vip_m'

# Bypass interactive input
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

# ==================== 原有因子組 (動能/趨勢) ====================
print("Loading momentum factors...")
top15_buy = data.get("etl:broker_transactions:top15_buy")
top15_sell = data.get("etl:broker_transactions:top15_sell")
balance_index = data.get("etl:broker_transactions:balance_index")
net_volume = top15_buy - top15_sell

sharpe20_net_volume = net_volume.rolling(20).mean() / std(net_volume, 20)
sharpe20_balance_index = balance_index.rolling(20).mean() / std(balance_index, 20)

rsi = data.indicator("RSI", timeperiod=14)
adx = data.indicator("ADX", timeperiod=27)

# ==================== 新增因子 1: 法人動向 ====================
print("Loading institutional factors...")
foreign_buy = data.get('institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)')
investment_buy = data.get('institutional_investors_trading_summary:投信買賣超股數')

# 法人買超強度 (20日累積)
foreign_strength = foreign_buy.rolling(20).sum()
investment_strength = investment_buy.rolling(20).sum()

# ==================== 新增因子 2: 質量因子 ====================
print("Loading quality factors...")
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
roe = data.get('fundamental_features:ROE稅後')  # 稅後ROE

# ==================== 新增因子 3: 市場情緒 (融資警示) ====================
print("Loading sentiment factors...")
margin_balance = data.get('margin_transactions:融資今日餘額')
# 融資使用率 (低 = 散戶不追高 = 好訊號)
margin_ratio = margin_balance / margin_balance.rolling(60).mean()
low_margin_score = 1 - margin_ratio  # 反轉：低融資 = 高分

# ==================== 改進的流動性過濾 ====================
print("Setting up liquidity filters...")
trading_value = data.get("price:成交金額")
volume = data.get("price:成交股數")
market_value = data.get('etl:market_value')

# 更智能的過濾：放寬交易量，但要求最低市值
liquidity_filter = (
    (trading_value.rolling(20).mean() > 40_000_000) &  # 降低到4000萬
    (volume.rolling(20).mean() > 2_000_000) &          # 降低到200萬
    (market_value > 5_000_000_000)  # 新增：市值>50億 (過濾微型股)
)

# ==================== 因子標準化與組合 ====================
print("Combining factors...")

# Rank 所有因子 (0-1之間)
ranked_sharpe_net_volume = sharpe20_net_volume.rank(axis=1, pct=True)
ranked_sharpe_balance = sharpe20_balance_index.rank(axis=1, pct=True)
ranked_rsi = rsi.rank(axis=1, pct=True)
ranked_adx = adx.rank(axis=1, pct=True)
ranked_foreign = foreign_strength.rank(axis=1, pct=True)
ranked_investment = investment_strength.rank(axis=1, pct=True)
ranked_revenue_yoy = revenue_yoy.rank(axis=1, pct=True)
ranked_roe = roe.rank(axis=1, pct=True)
ranked_low_margin = low_margin_score.rank(axis=1, pct=True)

# 組合成因子群組
momentum_factor = (
    ranked_sharpe_net_volume +
    ranked_sharpe_balance +
    ranked_rsi +
    ranked_adx
) / 4

institution_factor = (
    ranked_foreign +
    ranked_investment
) / 2

quality_factor = (
    ranked_revenue_yoy +
    ranked_roe
) / 2

sentiment_factor = ranked_low_margin

# ==================== 因子權重配置 ====================
# 版本1: 固定權重
combined_factor = (
    momentum_factor * 0.30 +      # 動能群組 (券商+技術指標)
    institution_factor * 0.30 +   # 法人群組 (外資+投信)
    quality_factor * 0.25 +       # 質量群組 (營收+ROE)
    sentiment_factor * 0.15       # 市場情緒 (融資)
)

print("\nFactor weights:")
print("  Momentum (broker + technical): 30%")
print("  Institution (foreign + trust): 30%")
print("  Quality (revenue + ROE): 25%")
print("  Sentiment (low margin): 15%")

# ==================== 選股與風控 ====================
# 選出前8檔 (比原來6檔更分散)
position = combined_factor[liquidity_filter].is_largest(8)

# 停損設定 (稍微放寬，避免過度交易)
stop_loss_percent = 0.10  # 10%

# ==================== 回測 ====================
print("\nRunning backtest...")
report = sim(
    position,
    resample="Q",           # 季度再平衡
    upload=False,           # 不上傳
    stop_loss=stop_loss_percent
)

# ==================== 績效報告 ====================
print("\n" + "="*50)
print("改進策略績效報告")
print("="*50)
print(f"年化報酬率: {report.metrics.annual_return():.2%}")
print(f"夏普比率: {report.metrics.sharpe_ratio():.3f}")
print(f"最大回撤: {report.metrics.max_drawdown():.2%}")
print(f"勝率: {report.metrics.win_rate():.2%}")
# print(f"平均持有天數: {report.metrics.avg_holding_period():.1f}")  # 方法不存在
print("="*50)

print("\n策略改進要點:")
print("1. 因子多樣化：從4個→9個，4類")
print("2. 加入法人動向：外資+投信買超")
print("3. 加入質量因子：營收成長+ROE")
print("4. 加入情緒因子：低融資使用率")
print("5. 流動性放寬但要求市值>50億")
print("6. 持股從6檔→8檔 (更分散)")
