from finlab import data
from finlab import backtest

close = data.get('price:收盤價')
vol = data.get('price:成交股數')
sma20 = close.average(20)
sma60 = close.average(60)
rev = data.get('monthly_revenue:當月營收')
ope_earn = data.get('fundamental_features:營業利益率')
yield_ratio = data.get('price_earning_ratio:殖利率(%)')
boss_hold = data.get("internal_equity_changes:董監持有股數占比")
rev_growth_rate = data.get('monthly_revenue:去年同月增減(%)')

cond1 = yield_ratio >= 6
cond2 = (close > sma20) & (close > sma60)
cond3 = rev.average(3) > rev.average(12)
cond4 = ope_earn >= 3
cond5 = boss_hold >= 10
cond6 = (vol.average(5) >= 50*1000) & (vol.average(5) <= 10000*1000)
cond_all = cond1 & cond2 & cond3 & cond4 & cond5 & cond6
cond_all = cond_all*rev_growth_rate
cond_all = cond_all[cond_all>0].is_largest(10)

report = backtest.sim(cond_all, resample='M',fee_ratio=1.425/1000/3, stop_loss=0.06, take_profit=0.5, position_limit=0.125,name='高殖利率烏龜', live_performance_start='2022-05-01')

# 輸出績效指標
print("=" * 80)
print("高殖利率烏龜策略 績效報告")
print("=" * 80)
print(f"\n📊 核心績效:")
print(f"  年化報酬率: {report.metrics.annual_return():.2%}")
print(f"  夏普比率: {report.metrics.sharpe_ratio():.2f}")
print(f"  最大回撤: {report.metrics.max_drawdown():.2%}")

print(f"\n📈 與我們的策略對比:")
print(f"  單因子最佳 (Iter 14): 年化 2.56% | Sharpe 0.15 | MDD -54.50%")
print(f"  V1 多因子基準線:      年化 5.38% | Sharpe 0.35 | MDD -26.35%")
print(f"  V2 激進優化:          年化 7.12% | Sharpe 0.43 | MDD -32.92%")
print(f"  V3 超集中Moonshot:    年化 16.76% | Sharpe 0.57 | MDD -85.91%")
print(f"  V4 風控強化:          年化 4.20% | Sharpe 0.21 | MDD -49.25%")
print(f"  V5 籌碼主導:          年化 2.96% | Sharpe 0.15 | MDD -36.69%")
print(f"  高殖利率烏龜:         年化 {report.metrics.annual_return():.2%} | Sharpe {report.metrics.sharpe_ratio():.2f} | MDD {report.metrics.max_drawdown():.2%}")

print(f"\n🎯 目標達成狀況:")
print(f"  Sharpe > 2.0:  [{report.metrics.sharpe_ratio():.2f}] {'✅ 達標!' if report.metrics.sharpe_ratio() >= 2.0 else '❌ 未達標'}")
print(f"  報酬 > 30%:    [{report.metrics.annual_return():.2%}] {'✅ 達標!' if report.metrics.annual_return() >= 0.30 else '❌ 未達標'}")
print(f"  MDD < -20%:    [{report.metrics.max_drawdown():.2%}] {'✅ 達標!' if report.metrics.max_drawdown() >= -0.20 else '❌ 未達標'}")

print(f"\n💡 策略特色:")
print(f"  • 殖利率篩選: >= 6%")
print(f"  • 技術面確認: 股價>均線20日+60日")
print(f"  • 營收成長: 近3月營收>近12月營收")
print(f"  • 獲利能力: 營業利益率>=3%")
print(f"  • 內部人持股: 董監持股>=10%")
print(f"  • 流動性: 5日均量 50K~10M股")
print(f"  • 排名: 營收成長率最高前10檔")
print(f"  • 風控: 停損6%, 停利50%, 單股上限12.5%")
print(f"  • 調倉: 月度調倉")

print("=" * 80)
