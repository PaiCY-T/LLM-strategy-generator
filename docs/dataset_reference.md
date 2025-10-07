# Finlab 資料集參考手冊 (Dataset Reference Guide)

## 資料集識別符格式 (Dataset Identifier Format)

```
{category}:{subcategory}:{dataset_name}
```

## 完整資料集分類 (Complete Dataset Categories)

### 1. ETL - 加工數據 (ETL Processed Data)

#### 券商交易數據 (Broker Transactions)
```python
# 前15大券商交易數據
data.get('etl:broker_transactions:top15_buy')       # 前15大買進
data.get('etl:broker_transactions:top15_sell')      # 前15大賣出
data.get('etl:broker_transactions:balance_index')   # 平衡指數
data.get('etl:broker_transactions:net_volume')      # 淨買賣量
```

### 2. Price - 價格數據 (Price Data)

#### 基本價格 (Basic Price)
```python
data.get('price:收盤價')        # Close price
data.get('price:開盤價')        # Open price
data.get('price:最高價')        # High price
data.get('price:最低價')        # Low price
```

#### 交易量數據 (Volume Data)
```python
data.get('price:成交量')        # Trading volume
data.get('price:成交值')        # Trading value
data.get('price:成交筆數')      # Number of trades
```

### 3. Indicator - 技術指標 (Technical Indicators)

```python
data.get('indicator:rsi')              # RSI 相對強弱指標
data.get('indicator:adx')              # ADX 趨向指標
data.get('indicator:macd')             # MACD 指標
data.get('indicator:bollinger_bands')  # 布林通道
data.get('indicator:kd')               # KD 隨機指標
```

### 4. Fundamental Features - 基本面特徵 (Fundamental Features)

#### 融資融券 (Margin Trading)
```python
data.get('fundamental_features:融資餘額')    # Margin balance
data.get('fundamental_features:融券餘額')    # Short balance
data.get('fundamental_features:資券比')      # Margin-to-short ratio
```

#### 外資與法人 (Foreign & Institutional)
```python
data.get('fundamental_features:外資持股')    # Foreign holdings
data.get('fundamental_features:投信持股')    # Fund holdings
data.get('fundamental_features:自營商持股')  # Dealer holdings
```

## 使用示例 (Usage Examples)

### 完整策略下載範例 (Complete Strategy Download Example)

```python
from src.data import DataManager
import pandas as pd

# 初始化數據管理器
dm = DataManager(
    cache_dir="data",
    max_retries=4,
    freshness_days=7  # 7天內的緩存視為新鮮
)

# 下載策略所需的所有數據集
datasets = {
    # 券商籌碼數據
    'broker_buy': 'etl:broker_transactions:top15_buy',
    'broker_sell': 'etl:broker_transactions:top15_sell',
    'broker_balance': 'etl:broker_transactions:balance_index',

    # 技術指標
    'rsi': 'indicator:rsi',
    'adx': 'indicator:adx',

    # 基本市場數據
    'volume': 'price:成交量',
    'value': 'price:成交值',
    'close': 'price:收盤價',
}

# 批量下載
data = {}
for name, dataset_id in datasets.items():
    print(f"下載 {name}...")
    data[name] = dm.download_data(dataset_id)
    print(f"✓ {name}: {data[name].shape}")

# 使用數據
print(f"\n券商買超數據預覽:")
print(data['broker_buy'].head())
```

### 檢查數據新鮮度 (Check Data Freshness)

```python
from src.data import DataManager

dm = DataManager()

# 檢查特定數據集的新鮮度
is_fresh, last_updated, message = dm.check_data_freshness('price:收盤價')
print(f"新鮮度: {is_fresh}")
print(f"最後更新: {last_updated}")
print(f"訊息: {message}")
```

### 強制刷新數據 (Force Refresh Data)

```python
from src.data import DataManager

dm = DataManager()

# 強制從API下載最新數據（忽略緩存）
fresh_data = dm.download_data('price:收盤價', force_refresh=True)
print(f"已下載最新數據: {fresh_data.shape}")
```

## 資料集命名規則 (Dataset Naming Conventions)

### 1. 英文命名 (English Names)
用於API和程式碼：
```python
'etl:broker_transactions:top15_buy'
'indicator:rsi'
```

### 2. 中文命名 (Chinese Names)
用於基本數據查詢：
```python
'price:收盤價'
'price:成交量'
'fundamental_features:融資餘額'
```

### 3. 檔案系統轉換 (Filesystem Conversion)
自動轉換為檔案安全格式：
```python
# 識別符 → 檔案名
'etl:broker_transactions:top15_buy'
→ 'etl_broker_transactions_top15_buy_20250106T143022.parquet'
```

## 常見問題 (FAQ)

### Q1: 如何找到所有可用的資料集？
**A**: 訪問 [Finlab API 文檔](https://doc.finlab.tw) 或使用 `list_available_datasets()` 查看已緩存的資料集。

### Q2: 資料集的更新頻率是多少？
**A**:
- 價格數據：每日收盤後更新
- 券商數據：每日更新
- 技術指標：每日計算

### Q3: 如何知道數據是否最新？
**A**: 使用 `check_data_freshness()` 方法檢查：
```python
is_fresh, last_updated, message = dm.check_data_freshness('price:收盤價')
```

### Q4: 資料集格式是什麼？
**A**: 所有資料集都以 `pandas.DataFrame` 格式返回，索引為日期，列為股票代碼。

### Q5: 如何清理舊緩存？
**A**: 使用 `cleanup_old_cache()` 方法：
```python
removed_count = dm.cleanup_old_cache(days_threshold=30)
print(f"已移除 {removed_count} 個舊緩存檔案")
```

## 您的策略使用的資料集 (Datasets in Your Strategy)

根據您提供的策略代碼，您正在使用以下資料集：

```python
# 您的多因子策略使用的資料集
strategy_datasets = [
    'etl:broker_transactions:top15_buy',       # 券商買超
    'etl:broker_transactions:top15_sell',      # 券商賣超
    'etl:broker_transactions:balance_index',   # 券商平衡
    'price:成交值',                             # 成交值（流動性過濾）
    'price:成交量',                             # 成交量（流動性過濾）
    'indicator:rsi',                           # RSI（因子4）
    'indicator:adx',                           # ADX（因子5）
]
```

### 資料集用途對照表 (Dataset Usage Map)

| 資料集 | 用途 | 策略中的角色 |
|--------|------|--------------|
| `top15_buy` | 券商買超數據 | 因子1: sharpe20_net_volume |
| `top15_sell` | 券商賣超數據 | 因子1: sharpe20_net_volume |
| `balance_index` | 券商平衡指數 | 因子2: sharpe20_balance_index |
| `成交值` | 日成交金額 | 流動性過濾 (>6000萬) |
| `成交量` | 日成交股數 | 流動性過濾 (>300萬) |
| `rsi` | RSI 技術指標 | 因子3: rsi |
| `adx` | ADX 趨向指標 | 因子4: adx |

## 下一步建議 (Next Steps)

1. **下載完整資料集列表**: 訪問 https://doc.finlab.tw 查看所有可用資料集
2. **測試數據下載**: 使用上述示例代碼測試下載您需要的資料集
3. **驗證數據質量**: 檢查下載的數據是否符合預期格式和範圍
4. **優化緩存策略**: 根據您的交易週期調整 `freshness_days` 參數
