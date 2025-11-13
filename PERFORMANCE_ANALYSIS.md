# 改進策略績效分析報告

## 🚨 績效警示 (Performance Alert)

### 實際績效 vs 預期

| 指標 | 實際結果 | 預期目標 | 達成率 |
|------|---------|---------|-------|
| 年化報酬率 | **6.60%** | 15-20% | ❌ 33-44% |
| 夏普比率 | **0.335** | 1.1-1.4 | ❌ 24-30% |
| 最大回撤 | **-40.24%** | -18%至-23% | ❌ 惡化75% |
| 勝率 | **42.74%** | 60-65% | ❌ 66-71% |

**結論**: 改進策略表現遠低於預期，需要深度診斷。

---

## 🔍 問題診斷 (Root Cause Analysis)

### 假設 1: 數據質量問題 ⭐ 最可能

**可能原因**:
1. **營收/ROE數據缺失** - 月營收和ROE季報數據有時間延遲和缺失
2. **法人數據覆蓋率** - 外資/投信數據可能不是所有股票都有
3. **融資數據缺失** - 部分股票無融資交易

**驗證方法**:
```python
# 檢查數據完整性
print("營收數據覆蓋率:", revenue_yoy.notna().mean())
print("ROE數據覆蓋率:", roe.notna().mean())
print("外資數據覆蓋率:", foreign_buy.notna().mean())
print("融資數據覆蓋率:", margin_balance.notna().mean())
```

**影響**:
- 如果數據覆蓋率<50%，大量股票被排除
- 導致選股池過小，績效惡化

### 假設 2: 因子相關性過高

**可能原因**:
- 9個因子可能高度相關，沒有真正多樣化
- 例如: 外資買超 vs 投信買超相關性可能>0.7

**驗證方法**:
```python
# 計算因子相關性矩陣
import pandas as pd
factor_df = pd.DataFrame({
    'momentum': momentum_factor.mean(axis=1),
    'institution': institution_factor.mean(axis=1),
    'quality': quality_factor.mean(axis=1),
    'sentiment': sentiment_factor.mean(axis=1)
})
print(factor_df.corr())
```

### 假設 3: 權重配置不當

**可能原因**:
- 質量因子(25%)可能與動能因子負相關
- 營收高成長股往往已經大漲(高價股)
- 與動能策略衝突

**驗證方法**:
```python
# 測試不同權重組合
weights_to_test = [
    (0.50, 0.30, 0.10, 0.10),  # 動能主導
    (0.30, 0.40, 0.20, 0.10),  # 法人主導
    (0.25, 0.25, 0.25, 0.25),  # 完全平衡
]
```

### 假設 4: 流動性過濾過於寬鬆

**可能原因**:
- 放寬成交值門檻 (6000萬→4000萬)
- 放寬成交量門檻 (300萬→200萬)
- 選入太多小型股/冷門股

**驗證方法**:
```python
# 檢查實際選股的平均市值和成交值
selected_stocks = position[position == True]
print("選股平均市值:", market_value[selected_stocks].mean())
print("選股平均成交值:", trading_value[selected_stocks].mean())
```

### 假設 5: 市場環境不適合

**可能原因**:
- 回測期間可能是熊市/盤整市
- 多因子策略在趨勢市場表現不佳

**驗證方法**:
```python
# 檢查回測期間大盤表現
benchmark = data.get('benchmark:發行量加權股價報酬指數')
print("回測期間大盤年化報酬:", benchmark.pct_change().mean() * 252)
```

---

## 🔧 修正建議 (Fix Recommendations)

### 緊急修正 (立即執行)

#### 方案 A: 簡化策略 + 提高數據質量門檻

```python
# 1. 只使用數據完整的因子
# 移除: 營收YoY (數據延遲)、ROE (季度數據)、融資 (覆蓋率低)
# 保留: 動能4個 + 法人2個 = 6個因子

# 2. 提高數據質量過濾
# 只選有完整法人數據的股票
has_institutional_data = (
    foreign_buy.notna() &
    investment_buy.notna()
)

# 3. 恢復原始流動性門檻
liquidity_filter = (
    (trading_value.rolling(20).mean() > 60_000_000) &
    (volume.rolling(20).mean() > 3_000_000) &
    (market_value > 10_000_000_000)  # 提高到100億
)
```

#### 方案 B: 回歸原始策略 + 微調

```python
# 只加入法人因子，移除質量和情緒因子
combined_factor = (
    momentum_factor * 0.60 +      # 動能 60%
    institution_factor * 0.40     # 法人 40%
)

# 持股恢復到6檔
position = combined_factor[liquidity_filter].is_largest(6)
```

#### 方案 C: 動態權重

```python
# 根據市場狀態動態調整權重
market_trend = close.pct_change(60).mean(axis=1)  # 60日大盤趨勢

# 牛市: 提高動能權重
# 熊市: 提高質量權重
weight_momentum = 0.30 + 0.30 * (market_trend > 0)
weight_quality = 0.25 + 0.25 * (market_trend < 0)
```

### 中期優化 (1-2週)

1. **數據完整性分析**
   ```python
   # 建立數據質量報告
   data_quality = {
       'revenue_yoy': revenue_yoy.notna().mean(),
       'roe': roe.notna().mean(),
       'foreign': foreign_buy.notna().mean(),
       'investment': investment_buy.notna().mean(),
       'margin': margin_balance.notna().mean()
   }
   ```

2. **因子有效性測試**
   ```python
   # 單獨測試每個因子的IC (Information Coefficient)
   # IC > 0.05 才納入策略
   ```

3. **參數網格搜索**
   ```python
   # 使用Optuna優化:
   # - 因子權重 (4個參數)
   # - 持股數 (6-10)
   # - 流動性門檻 (3個參數)
   ```

---

## 📊 診斷腳本 (Diagnostic Script)

建議您運行以下腳本診斷問題:

```python
"""
診斷改進策略問題
"""
import os
os.environ['FINLAB_API_TOKEN'] = 'YOUR_TOKEN'

from finlab import data
from finlab.backtest import sim
import pandas as pd
import numpy as np

# ==================== 載入數據 ====================
print("載入數據...")
# [載入所有因子數據的代碼]

# ==================== 診斷 1: 數據完整性 ====================
print("\n" + "="*50)
print("診斷 1: 數據完整性分析")
print("="*50)

data_coverage = {
    'sharpe20_net_volume': sharpe20_net_volume.notna().mean().mean(),
    'sharpe20_balance_index': sharpe20_balance_index.notna().mean().mean(),
    'rsi': rsi.notna().mean().mean(),
    'adx': adx.notna().mean().mean(),
    'foreign_strength': foreign_strength.notna().mean().mean(),
    'investment_strength': investment_strength.notna().mean().mean(),
    'revenue_yoy': revenue_yoy.notna().mean().mean(),
    'roe': roe.notna().mean().mean(),
    'margin_ratio': margin_ratio.notna().mean().mean(),
}

for factor, coverage in data_coverage.items():
    status = "✅" if coverage > 0.7 else "⚠️" if coverage > 0.5 else "❌"
    print(f"{status} {factor}: {coverage:.2%}")

# ==================== 診斷 2: 因子相關性 ====================
print("\n" + "="*50)
print("診斷 2: 因子相關性分析")
print("="*50)

# 計算每日所有股票的因子平均值
factor_series = pd.DataFrame({
    'momentum': momentum_factor.mean(axis=1),
    'institution': institution_factor.mean(axis=1),
    'quality': quality_factor.mean(axis=1),
    'sentiment': sentiment_factor.mean(axis=1)
})

correlation = factor_series.corr()
print(correlation)

print("\n高相關性警示 (>0.7):")
for i in range(len(correlation)):
    for j in range(i+1, len(correlation)):
        if abs(correlation.iloc[i, j]) > 0.7:
            print(f"⚠️ {correlation.index[i]} vs {correlation.columns[j]}: {correlation.iloc[i, j]:.3f}")

# ==================== 診斷 3: 選股分析 ====================
print("\n" + "="*50)
print("診斷 3: 選股分析")
print("="*50)

# 統計每期選了多少股票
selected_count = position.sum(axis=1)
print(f"平均選股數: {selected_count.mean():.1f} (目標: 8)")
print(f"選股數標準差: {selected_count.std():.1f}")
print(f"最少選股數: {selected_count.min()}")
print(f"最多選股數: {selected_count.max()}")

# 如果選股數<8，表示流動性過濾太嚴格或數據缺失
if selected_count.mean() < 6:
    print("⚠️ 警告: 平均選股數過少，可能是:")
    print("   1. 流動性過濾太嚴格")
    print("   2. 數據缺失導致無法計算因子")

# ==================== 診斷 4: 個別因子績效 ====================
print("\n" + "="*50)
print("診斷 4: 個別因子績效測試")
print("="*50)

# 測試每個因子群組單獨使用的績效
factor_groups = {
    'momentum_only': momentum_factor,
    'institution_only': institution_factor,
    'quality_only': quality_factor,
    'sentiment_only': sentiment_factor,
}

for name, factor in factor_groups.items():
    print(f"\n測試 {name}...")
    test_position = factor[liquidity_filter].is_largest(8)

    if test_position.sum().sum() < 100:  # 如果總共選不到100次
        print(f"  ❌ 數據不足，跳過")
        continue

    try:
        test_report = sim(test_position, resample="Q", upload=False, stop_loss=0.10)
        print(f"  年化報酬: {test_report.metrics.annual_return():.2%}")
        print(f"  夏普比率: {test_report.metrics.sharpe_ratio():.3f}")
        print(f"  最大回撤: {test_report.metrics.max_drawdown():.2%}")
    except Exception as e:
        print(f"  ❌ 回測失敗: {e}")

# ==================== 診斷 5: 權重敏感性分析 ====================
print("\n" + "="*50)
print("診斷 5: 權重敏感性分析")
print("="*50)

weight_configs = [
    ("原始配置", 0.30, 0.30, 0.25, 0.15),
    ("動能主導", 0.50, 0.30, 0.10, 0.10),
    ("法人主導", 0.20, 0.50, 0.20, 0.10),
    ("質量主導", 0.20, 0.20, 0.40, 0.20),
    ("完全平衡", 0.25, 0.25, 0.25, 0.25),
]

for name, w1, w2, w3, w4 in weight_configs:
    print(f"\n測試 {name} ({w1:.0%}/{w2:.0%}/{w3:.0%}/{w4:.0%})...")

    test_combined = (
        momentum_factor * w1 +
        institution_factor * w2 +
        quality_factor * w3 +
        sentiment_factor * w4
    )

    test_position = test_combined[liquidity_filter].is_largest(8)

    try:
        test_report = sim(test_position, resample="Q", upload=False, stop_loss=0.10)
        print(f"  年化報酬: {test_report.metrics.annual_return():.2%}")
        print(f"  夏普比率: {test_report.metrics.sharpe_ratio():.3f}")
        print(f"  最大回撤: {test_report.metrics.max_drawdown():.2%}")
    except Exception as e:
        print(f"  ❌ 回測失敗: {e}")

print("\n" + "="*50)
print("診斷完成")
print("="*50)
```

---

## 🎯 下一步行動 (Next Actions)

### 立即執行 (今天)

1. **運行診斷腳本** - 找出根本原因
2. **檢查數據覆蓋率** - 確認是否數據缺失問題
3. **測試簡化方案** - 先用6因子 (動能4 + 法人2)

### 短期 (本週)

1. **如果是數據問題** → 採用方案A (簡化策略)
2. **如果是權重問題** → 採用方案B (回歸原始+法人)
3. **如果都不是** → 深度分析市場環境

### 中期 (2週內)

1. **參數優化** - 使用Optuna尋找最佳參數
2. **樣本外測試** - 驗證策略穩定性
3. **風險管理加強** - 加入動態停損/止盈

---

## 📌 關鍵教訓 (Key Learnings)

1. **數據質量 > 因子數量**
   - 9個低質量因子 < 4個高質量因子

2. **多樣化需驗證**
   - 不能假設更多因子 = 更好分散
   - 需要計算實際相關性

3. **簡單優於複雜**
   - 複雜策略容易過度擬合
   - 簡單策略更穩健

4. **先回測再實盤**
   - 理論預期 ≠ 實際績效
   - 必須用歷史數據驗證

---

**建議**: 立即運行診斷腳本，根據結果選擇修正方案。不要直接實盤使用當前改進策略。
