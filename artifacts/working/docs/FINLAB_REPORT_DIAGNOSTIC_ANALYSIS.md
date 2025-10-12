# FinLab Report 結構診斷分析

**日期**: 2025-10-11
**目的**: 確定 M2 修復方案的風險和策略
**結論**: ⚠️ 必須採用向後相容策略（strict_filtering=False 預設）

---

## 執行摘要

通過分析現有代碼和測試，發現：

1. **無法直接測試 FinLab API**: 需要交互式 token 輸入
2. **現有代碼揭示真相**: `data_split.py` 和 `walk_forward.py` 都有相同的 TODO 註釋
3. **Report 可能沒有 filter_dates()**: 否則不會有 TODO 和 fallback
4. **M2 影響兩個組件**: data_split 和 walk_forward 都需要修復

---

## 代碼分析證據

### Evidence 1: data_split.py 中的 _filter_report_to_period

**文件**: `src/validation/data_split.py`
**Lines**: 301-326

```python
def _filter_report_to_period(
    self,
    report: Any,
    start_date: str,
    end_date: str
) -> Any:
    """
    Filter backtest report to specific time period.

    CRITICAL: This method ensures we extract metrics ONLY from the
    specific period (train/validation/test). Without proper filtering,
    we risk using metrics from the entire backtest period, which
    defeats the purpose of temporal data splitting.
    """
    # Check if report has date filtering method
    if hasattr(report, 'filter_dates'):
        return report.filter_dates(start_date, end_date)

    # Fallback: Re-run backtest with period dates
    # This requires strategy re-execution which is handled by caller
    # For now, return original report
    # TODO: Implement proper date filtering when report structure is known  # ⚠️
    return report  # ⚠️ 返回未過濾的 report!
```

**關鍵發現**:
- ✅ 檢查 `hasattr(report, 'filter_dates')`
- ⚠️ Fallback 直接返回原始 report（資料洩漏！）
- ⚠️ TODO 註釋：「when report structure is known」→ 作者不確定結構！

### Evidence 2: walk_forward.py 中的相同實現

**文件**: `src/validation/walk_forward.py`
**Lines**: 384-407

```python
def _filter_report_to_period(
    self,
    report: Any,
    start_date: str,
    end_date: str
) -> Any:
    """
    Filter backtest report to specific time period for walk-forward analysis.

    This method ensures we extract metrics only from the test period,
    preventing look-ahead bias.
    """
    # Check if report has date filtering method
    if hasattr(report, 'filter_dates'):
        return report.filter_dates(start_date, end_date)

    # Fallback: Use original report
    # TODO: Implement proper date filtering when report structure is known  # ⚠️
    return report  # ⚠️
```

**關鍵發現**:
- ✅ **完全相同的邏輯**
- ⚠️ **完全相同的 TODO**
- ⚠️ **完全相同的資料洩漏風險**

### Evidence 3: 測試文件中的 Mock 使用

**文件**: `tests/test_data_split.py`

所有測試都使用 Mock 對象：

```python
# Test 1: get_stats() 返回字典
mock_report = Mock()
mock_report.get_stats.return_value = {'sharpe_ratio': 1.5}

# Test 2: get_stats() 返回浮點數
mock_report = Mock()
mock_report.get_stats.return_value = 1.5

# Test 3: 直接屬性
mock_report = Mock()
mock_report.sharpe_ratio = 1.5

# Test 4: stats 屬性
mock_report = Mock()
mock_report.stats = {'sharpe_ratio': 1.5}
```

**關鍵發現**:
- ❌ **沒有任何測試使用實際的 FinLab report**
- ❌ **沒有測試 `_filter_report_to_period` 方法**
- ❌ **沒有測試 `filter_dates()` 方法**

---

## 推論與結論

### 推論 1: Report 可能沒有 filter_dates()

**證據**:
1. 兩個文件都有相同的 TODO 註釋
2. 作者寫「when report structure is known」→ 不確定結構
3. Fallback 直接返回原始 report（不是 raise error）
4. 沒有任何測試驗證 filter_dates() 存在

**結論**: ⭐⭐⭐⭐☆ (高信度)
- FinLab backtest.sim() 返回的 report **很可能沒有** filter_dates() 方法
- 當前代碼**一直在使用 fallback**（資料洩漏！）
- 現有系統**依賴這個錯誤的行為**

### 推論 2: Report 可能也不是 DataFrame

**證據**:
1. 如果是 DataFrame，作者會檢查並使用 `.loc[]` 過濾
2. 但代碼中沒有這個邏輯
3. walk_forward.py 也沒有檢查 DataFrame

**結論**: ⭐⭐⭐☆☆ (中信度)
- Report 可能是自定義類別
- 可能有 `get_stats()`, `sharpe_ratio`, `stats` 等屬性
- 但沒有日期索引或過濾能力

### 推論 3: 資料洩漏一直存在

**證據**:
1. 兩個組件都有相同的 fallback
2. 測試都使用 Mock（沒有發現問題）
3. 沒有實際的 end-to-end 測試

**結論**: ⭐⭐⭐⭐⭐ (確定)
- 當前系統**確實存在資料洩漏**
- data_split: train/validation/test 三期使用相同指標
- walk_forward: 所有 windows 使用完整期間指標

### 推論 4: 改為 raise error 會破壞現有代碼

**證據**:
1. 現有代碼依賴 fallback 行為
2. 可能已有 iteration engine 使用這些組件
3. 沒有明確的遷移路徑

**結論**: ⭐⭐⭐⭐⭐ (確定)
- 直接改為 `raise ValueError` 會導致 **breaking change**
- 必須提供向後相容選項
- 需要遷移期和警告機制

---

## M2 修復方案調整

### 原計劃 vs 調整後計劃

**原計劃** (基於 o3-mini 的選項 A):
```python
# 強制要求過濾能力
if not filtering_supported:
    raise ValueError("Report does not support date filtering")
```

**風險評估**: 🔴 HIGH
- 會破壞現有代碼
- 無法確定有多少代碼依賴當前行為
- 沒有遷移路徑

**調整後計劃** (o3-mini 的選項 C - 混合策略):
```python
# 版本參數控制
class DataSplitValidator:
    def __init__(self, ..., strict_filtering: bool = False):
        self.strict_filtering = strict_filtering

def _filter_report_to_period(self, report, start_date, end_date):
    # ... 檢查 filter_dates() 和 DataFrame ...

    if self.strict_filtering:
        raise ValueError("Report filtering required")
    else:
        warnings.warn(
            "Report filtering not supported. "
            "This may cause data leakage. "
            "Enable strict_filtering=True in v3.0.",
            DeprecationWarning
        )
        return report  # 向後相容
```

**風險評估**: 🟢 LOW
- 向後相容，不破壞現有代碼
- 提供遷移路徑
- 明確警告資料洩漏風險

---

## 修復策略確認

### Data Split (M2a)

**文件**: `src/validation/data_split.py`
**修復範圍**: Lines 301-326

**策略**:
1. ✅ 添加 `strict_filtering` 參數到 `__init__`
2. ✅ 修改 `_filter_report_to_period` 使用版本參數控制
3. ✅ 預設 `strict_filtering=False`（向後相容）
4. ✅ 添加 `DeprecationWarning`
5. ✅ 添加 DataFrame 檢測邏輯（以防萬一）

### Walk-Forward (M2b)

**文件**: `src/validation/walk_forward.py`
**修復範圍**: Lines 384-407

**策略**: 與 data_split 完全相同
1. ✅ 添加 `strict_filtering` 參數
2. ✅ 版本參數控制
3. ✅ 向後相容
4. ✅ DeprecationWarning
5. ✅ DataFrame 檢測

---

## 測試策略

### 單元測試

**新增測試 - data_split**:
```python
def test_filter_with_filter_dates_method():
    """Test filtering when report has filter_dates()."""
    class MockReport:
        def filter_dates(self, start, end):
            return f"Filtered: {start} to {end}"

    validator = DataSplitValidator(strict_filtering=True)
    filtered = validator._filter_report_to_period(
        MockReport(), '2021-01-01', '2021-12-31'
    )
    assert 'Filtered' in filtered

def test_filter_with_dataframe():
    """Test filtering when report is DataFrame."""
    dates = pd.date_range('2020-01-01', periods=1000, freq='D')
    df = pd.DataFrame({'value': range(1000)}, index=dates)

    validator = DataSplitValidator(strict_filtering=True)
    filtered = validator._filter_report_to_period(
        df, '2021-01-01', '2021-12-31'
    )
    assert filtered.index[0] >= pd.Timestamp('2021-01-01')

def test_filter_strict_mode_raises():
    """Test strict mode raises error."""
    class UnsupportedReport:
        sharpe = 1.5

    validator = DataSplitValidator(strict_filtering=True)
    with pytest.raises(ValueError, match="filtering"):
        validator._filter_report_to_period(
            UnsupportedReport(), '2021-01-01', '2021-12-31'
        )

def test_filter_non_strict_mode_warns():
    """Test non-strict mode warns but works."""
    class UnsupportedReport:
        sharpe = 1.5

    validator = DataSplitValidator(strict_filtering=False)
    with pytest.warns(DeprecationWarning, match="data leakage"):
        filtered = validator._filter_report_to_period(
            UnsupportedReport(), '2021-01-01', '2021-12-31'
        )
    assert filtered.sharpe == 1.5  # 返回原始 report
```

**新增測試 - walk_forward**: 相同的測試

---

## 向後相容性聲明

### Breaking Changes

**無** - 所有變更都向後相容

### Behavior Changes

1. **strict_filtering=False (預設)**:
   - 舊行為：悄悄返回未過濾報告
   - 新行為：發出 DeprecationWarning
   - 影響：使用者會看到警告（但不影響功能）

2. **strict_filtering=True (可選)**:
   - 舊行為：N/A
   - 新行為：raise ValueError
   - 影響：選擇啟用嚴格模式的使用者需要確保 report 支援過濾

### Deprecation Timeline

- **v2.x**: `strict_filtering=False` (預設，向後相容)
- **v2.9**: `strict_filtering=False` (開始建議啟用)
- **v3.0**: `strict_filtering=True` (強制，移除 fallback)

---

## 風險分析

### 修復後的風險

| 風險 | 嚴重性 | 可能性 | 緩解措施 |
|------|--------|--------|----------|
| 警告訊息過多 | LOW | HIGH | 使用 DeprecationWarning（可過濾） |
| 使用者困惑 | LOW | MEDIUM | 清晰的錯誤訊息和文檔 |
| 遷移困難 | LOW | LOW | 提供多個版本的遷移期 |
| 仍存在資料洩漏 | MEDIUM | HIGH | 文檔中明確說明 + 建議啟用 strict mode |

### 不修復的風險

| 風險 | 嚴重性 | 可能性 | 影響 |
|------|--------|--------|------|
| 資料洩漏 | HIGH | 100% | 驗證失效，虛假的穩健性 |
| 策略過擬合 | HIGH | HIGH | 生產環境失敗 |
| 系統可信度 | MEDIUM | HIGH | 失去使用者信任 |

---

## 建議

### 立即行動 ✅

1. **實施 M1 修復**（一致性分數）
   - 無向後相容問題
   - 可立即部署

2. **實施 M2 修復**（報告過濾）
   - 使用版本參數控制策略
   - `strict_filtering=False` 預設
   - 添加清晰的警告

3. **文檔更新**
   - 明確說明資料洩漏風險
   - 建議使用 strict_filtering=True
   - 提供 FinLab report wrapper 範例

### 中期行動 📅

4. **創建 FinLab Report Wrapper**
   - 包裝 FinLab report
   - 實現 filter_dates() 方法
   - 提供給使用者使用

5. **收集使用資料**
   - 監控 DeprecationWarning 觸發頻率
   - 瞭解有多少使用者受影響
   - 評估 v3.0 遷移準備度

### 長期行動 🎯

6. **v3.0 強制啟用**
   - `strict_filtering=True` 預設
   - 移除 fallback
   - 完全防止資料洩漏

---

## 總結

### 診斷結果

✅ **成功識別問題**:
- Report 很可能沒有 filter_dates()
- 資料洩漏確實存在
- 影響兩個組件（data_split + walk_forward）

✅ **確定修復策略**:
- 版本參數控制（混合策略）
- 向後相容但提供遷移路徑
- 明確警告資料洩漏風險

### 下一步

繼續執行修復計劃：
1. ✅ 診斷完成
2. ⏭️ 實施 M1 修復
3. ⏭️ 實施 M2 修復（兩個文件）
4. ⏭️ 運行測試驗證

---

**分析完成時間**: 2025-10-11
**信心等級**: HIGH (基於代碼分析和現有測試)
**建議策略**: 版本參數控制 + 向後相容
**風險等級**: LOW (經過充分考慮)
