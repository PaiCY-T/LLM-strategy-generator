# Steering Update 2025-11-24: Template Mode 架構修復

**日期**: 2025-11-24
**類型**: 架構修復與文檔化
**影響範圍**: Template Mode 執行流程, UnifiedLoop, TemplateIterationExecutor
**重要性**: 🔴 **Critical** - 修復核心執行邏輯錯誤

---

## 執行摘要

完成 Template Mode 架構的重大修復 (Bug #5),糾正了錯誤的代碼生成假設,改為正確的直接執行模式。此修復解決了所有 20 次迭代煙霧測試失敗的問題,並透過 Zen tracer 進行了完整的架構追蹤分析。

**關鍵成果**:
- ✅ 修復 Bug #5 (3個子問題: 方法不存在, 錯誤API, 結構不匹配)
- ✅ 20 次迭代煙霧測試 100% 通過
- ✅ 完整架構追蹤與文檔化
- ✅ 明確 Template Mode vs LLM Mode 執行差異

---

## 問題背景

### Bug #5: Template 執行架構根本性錯誤

**發現時間**: 2025-11-24
**症狀**: 所有 20 次迭代測試失敗,錯誤訊息 `'MomentumTemplate' object has no attribute 'generate_code'`

**根本原因**: 架構設計錯誤假設 Template Mode 與 LLM Mode 使用相同的執行流程:
```python
# 錯誤假設
Parameters → template.generate_code() → code_string → BacktestExecutor → MetricsExtractor
```

**實際情況**: Template Mode 應該直接執行,無需代碼生成:
```python
# 正確流程
Parameters → template.generate_strategy() → (report, metrics_dict) → StrategyMetrics
```

### 子問題分解

**Bug #5a: 呼叫不存在的方法**
- 位置: `template_iteration_executor.py:438`
- 錯誤: `code = self.template_param_generator.template.generate_code(params)`
- 事實: `MomentumTemplate` 只有 `generate_strategy(params)` 方法

**Bug #5b: 錯誤的 metrics 提取方法**
- 位置: `template_iteration_executor.py:293`
- 錯誤: `metrics = self.metrics_extractor.extract(execution_result)`
- 事實: `MetricsExtractor` 只有 `extract_metrics(report)` 方法
- 更重要: Template 已經提取 metrics,無需再次提取

**Bug #5c: execution_result 結構不匹配**
- 問題: Template 執行回傳的結構與 `SuccessClassifier` 期望不符
- 需要: 建構符合 classifier 要求的 `execution_result` dict

---

## 解決方案

### 1. 完整重寫 Template 執行流程

**檔案**: `src/learning/template_iteration_executor.py`

**修改位置**: Lines 263-292 (Step 5: Template execution)

```python
# Step 5: Execute strategy directly via template (no code generation in template mode)
try:
    logger.info(f"Executing template strategy with params: {params}")
    report, metrics_dict = self.template_param_generator.template.generate_strategy(params)

    # Metrics already extracted by template - convert to StrategyMetrics format
    from src.backtest.metrics import StrategyMetrics
    metrics = StrategyMetrics.from_dict(metrics_dict)

    # Build execution_result for compatibility with SuccessClassifier
    execution_result = {
        'success': metrics_dict.get('success', False),
        'sharpe_ratio': metrics_dict.get('sharpe_ratio'),
        'total_return': metrics_dict.get('annual_return'),
        'max_drawdown': metrics_dict.get('max_drawdown'),
        'report': report,
        'template_executed': True
    }
    logger.info(f"✓ Template execution successful (Sharpe={metrics.sharpe_ratio:.3f})")

    # No strategy_code for template mode - store parameters as reference
    strategy_code = f"# Template: {self.template_name}\n# Parameters: {params}"

except Exception as e:
    logger.error(f"Template execution failed: {e}")
    return self._create_error_record(
        iteration_num,
        f"Template execution error: {e}",
        params=params
    )
```

**關鍵改變**:
1. ❌ 移除: `template.generate_code()` 呼叫
2. ✅ 新增: 直接呼叫 `template.generate_strategy(params)`
3. ✅ 新增: 使用 `StrategyMetrics.from_dict()` 轉換 metrics
4. ✅ 新增: 建構符合 `SuccessClassifier` 的 `execution_result`
5. ❌ 移除: `MetricsExtractor.extract()` 呼叫 (不需要)

### 2. 移除未使用的代碼生成方法

**刪除**: `_generate_code()` 方法 (lines 386-405)

**理由**: Template Mode 完全不需要代碼生成步驟,此方法永遠不會被呼叫

---

## 架構分析 (Zen Tracer)

### 完整執行流程圖

```
[UnifiedLoop::__init__] (unified_loop.py:104)
↓
[UnifiedLoop::_inject_template_executor] (unified_loop.py:233) ? if template_mode == True
  ↓
  [TemplateIterationExecutor::__init__] (template_iteration_executor.py:113)
    ↓
    [TemplateParameterGenerator::__init__] (template_parameter_generator.py:85)
      ↓
      [MomentumTemplate::__init__] (momentum_template.py:145)
↓
[UnifiedLoop::run] (unified_loop.py:361)
↓
[LearningLoop::run] (learning_loop.py:162)
  ↓
  [TemplateIterationExecutor::execute_iteration] (template_iteration_executor.py:202)
    ↓
    [TemplateIterationExecutor::_generate_parameters] (template_iteration_executor.py:348)
      ↓
      [TemplateParameterGenerator::generate_parameters] (template_parameter_generator.py:162)
    ↓
    [MomentumTemplate::generate_strategy] (momentum_template.py:447) ⚠️ Bug #5 修復核心
      ↓
      [finlab.backtest::sim] (external library)
      ↓
      [MomentumTemplate::_extract_metrics] (momentum_template.py:589)
    ↓
    [StrategyMetrics::from_dict] (backtest/metrics.py:134)
    ↓
    [SuccessClassifier::classify] (backtest/classifier.py:78)
    ↓
    [ChampionTracker::update_if_better] (champion_tracker.py:89) ? if LEVEL_3
  ↓
  [IterationHistory::save] (iteration_history.py:135)
```

### 關鍵資料轉換

#### 1. 參數生成
```
ParameterGenerationContext
  ├─ iteration_num: int
  ├─ champion_params: Optional[Dict]
  ├─ champion_sharpe: Optional[float]
  └─ feedback_history: Optional[str]
     ↓
Dict[str, Any] (parameters)
```

#### 2. Template 執行 (修復後)
```
Dict[str, Any] (parameters)
     ↓
MomentumTemplate.generate_strategy(params)
     ↓
Tuple[object, Dict]
  ├─ report: finlab.backtest.Report
  └─ metrics_dict: Dict
       ├─ 'annual_return': float
       ├─ 'sharpe_ratio': float
       ├─ 'max_drawdown': float
       └─ 'success': bool
```

#### 3. Metrics 轉換
```
metrics_dict: Dict
     ↓
StrategyMetrics.from_dict(metrics_dict)
     ↓
StrategyMetrics (dataclass)
```

#### 4. 執行結果建構
```
execution_result: Dict
  ├─ 'success': bool
  ├─ 'sharpe_ratio': float
  ├─ 'total_return': float
  ├─ 'max_drawdown': float
  ├─ 'report': finlab.backtest.Report
  └─ 'template_executed': True
```

### 副作用 (Side Effects)

- **[filesystem]** 儲存 iteration history 到 JSONL (`iteration_history.py:135-145`)
- **[filesystem]** 儲存 champion 到 JSON (`champion_tracker.py:110-125`)
- **[filesystem]** 儲存 Hall of Fame 策略 (`repository.py:125-148`)
- **[state]** 更新 ChampionTracker 內部狀態 (`champion_tracker.py:95-108`)
- **[state]** DataCache singleton 快取市場數據 (`data_cache.py:35-95`)
- **[network]** finlab API 呼叫獲取市場數據 (`data_cache.py:58-85`)

---

## Template Mode vs LLM Mode 比較

| 面向 | Template Mode | LLM Mode |
|------|---------------|----------|
| **策略生成** | 直接執行 Template | LLM 生成代碼字串 |
| **主要方法** | `template.generate_strategy(params)` | `llm_client.generate_code(prompt)` |
| **回傳格式** | `(report, metrics_dict)` tuple | `code_string` |
| **執行方式** | Template 內部呼叫 `finlab.backtest.sim()` | `BacktestExecutor.execute(code)` |
| **Metrics 提取** | Template 內部完成 | `MetricsExtractor.extract_metrics()` |
| **代碼儲存** | 參數註解 (無實際代碼) | 完整 Python 代碼 |
| **靈活性** | 受限於 Template 參數空間 | 完全自由,受限於 LLM 能力 |
| **穩定性** | 高 (預定義邏輯) | 中 (LLM 可能產生錯誤代碼) |
| **速度** | 快 (無 LLM 呼叫) | 慢 (需等待 LLM 回應) |

---

## 設計模式應用

### 1. Strategy Pattern (策略模式)
- **Context**: `LearningLoop`
- **Strategy Interface**: `IterationExecutor` (抽象)
- **Concrete Strategies**:
  - `StandardIterationExecutor`: LLM/Factor Graph 模式
  - `TemplateIterationExecutor`: Template 模式
- **切換機制**: `UnifiedLoop._inject_template_executor()`

### 2. Facade Pattern (外觀模式)
- **Facade**: `UnifiedLoop`
- **Subsystem**: `LearningLoop` + 所有組件
- **簡化API**: `__init__()` 和 `run()`

### 3. Template Method Pattern (模板方法模式)
- **Abstract Class**: `BaseTemplate`
- **Template Method**: `generate_strategy(params)` (abstract)
- **Concrete Implementation**: `MomentumTemplate`

### 4. Singleton Pattern (單例模式)
- **Class**: `DataCache`
- **目的**: 確保 finlab 數據快取唯一性
- **方法**: `get_instance()` class method

---

## 測試驗證

### 20 次迭代煙霧測試

**測試腳本**: `run_20iteration_smoke_test.py`

**測試配置**:
- Template Mode: Enabled
- Template Name: Momentum
- JSON Mode: False (使用預設參數生成)
- Docker Sandbox: Disabled

**測試結果**:
```
✅ 20/20 iterations passed (100% success rate)
✅ Exit code: 0
✅ Duration: ~30 minutes
✅ No errors or exceptions
```

**關鍵驗證點**:
1. ✅ UnifiedLoop 正確初始化 TemplateIterationExecutor
2. ✅ Template 直接執行無錯誤
3. ✅ Metrics 正確提取與轉換
4. ✅ SuccessClassifier 正確分類
5. ✅ Champion 更新機制正常運作
6. ✅ Iteration history 正確儲存

---

## 技術決策記錄

### 決策 #1: 為什麼 Template Mode 不生成代碼?

**理由**:
1. **效能**: 直接執行比生成代碼再執行快得多
2. **可靠性**: 避免代碼字串解析和執行的潛在錯誤
3. **簡潔性**: Template 已經是 Python 代碼,無需再次生成
4. **類型安全**: 直接方法呼叫有完整的型別檢查

**權衡**:
- ❌ 失去: 代碼可視化 (無法看到完整策略代碼)
- ✅ 獲得: 更高執行效率和穩定性
- 📝 解決: 在 `strategy_code` 欄位儲存參數註解

### 決策 #2: 為什麼 Template 內部提取 Metrics?

**理由**:
1. **一致性**: Template 已經呼叫 `finlab.backtest.sim()`,擁有原始 report
2. **效率**: 避免重複的 metrics 提取邏輯
3. **封裝**: Template 負責完整的策略執行與結果提取
4. **靈活性**: 不同 template 可以提取不同的 metrics

**權衡**:
- ❌ 失去: Metrics 提取邏輯的集中管理
- ✅ 獲得: Template 的完整自主性
- 📝 標準化: 透過 `BaseTemplate` 定義統一介面

### 決策 #3: 為什麼使用 StrategyMetrics.from_dict()?

**理由**:
1. **類型安全**: Dataclass 提供完整的型別檢查
2. **一致性**: 與 LLM Mode 使用相同的 metrics 格式
3. **驗證**: Dataclass 可以在建構時進行驗證
4. **IDE 支援**: 自動完成和型別提示

**權衡**:
- ❌ 需要: 轉換步驟 (dict → dataclass)
- ✅ 獲得: 型別安全和一致性
- 📝 效能: 轉換開銷可忽略

---

## 影響分析

### 影響範圍

**直接影響**:
- ✅ `src/learning/template_iteration_executor.py` (重大重構)
- ✅ `src/learning/unified_loop.py` (無變更,正確委派)
- ✅ `src/templates/momentum_template.py` (已正確實作,無需變更)

**間接影響**:
- ✅ `run_20iteration_smoke_test.py` (測試通過,無需變更)
- ✅ 所有使用 Template Mode 的實驗和測試

**無影響**:
- ✅ LLM Mode 執行流程 (完全獨立)
- ✅ Factor Graph Mode (如未來實作)
- ✅ Standard Mode 的任何功能

### 向後相容性

**完全相容**: Template Mode 之前未正確運作,此修復讓它首次正確執行。

**API 穩定性**:
- ✅ UnifiedLoop 公開 API 無變更
- ✅ LearningLoop API 無變更
- ✅ Template 介面已正確定義,無變更

---

## 未來改進建議

### 1. Template 代碼可視化

**問題**: 目前 Template Mode 不儲存實際策略代碼,只儲存參數註解

**建議**:
- 選項 A: Template 生成等效的代碼字串 (僅用於顯示)
- 選項 B: 在 UI/報告中顯示 Template 類別名稱和參數
- 選項 C: 提供 "Explain" API,由 Template 生成自然語言描述

**優先級**: 低 (功能性問題,非阻塞)

### 2. Metrics 提取標準化

**問題**: 不同 Template 可能提取不同格式的 metrics

**建議**:
- 在 `BaseTemplate` 定義 `_extract_metrics()` 的標準格式
- 提供 metrics schema 驗證
- 考慮使用 Pydantic model 替代 dataclass

**優先級**: 中 (未來新增更多 Template 時重要)

### 3. Template Mode 文檔化

**問題**: Template Mode 的使用方式和限制缺乏文檔

**建議**:
- 在 `docs/` 新增 Template Mode 使用指南
- 新增 Template 開發教學
- 新增 Template vs LLM Mode 選擇指南

**優先級**: 高 (此 steering update 已部分完成)

---

## 檢查清單

- [x] Bug #5 完整修復 (3個子問題)
- [x] 20 次迭代煙霧測試 100% 通過
- [x] Zen tracer 架構追蹤完成
- [x] 執行流程圖文檔化
- [x] 資料轉換流程文檔化
- [x] Template Mode vs LLM Mode 比較表
- [x] 設計模式分析
- [x] 技術決策記錄
- [x] 影響分析
- [x] 向後相容性確認
- [x] 未來改進建議
- [ ] 200 次迭代穩定性測試 (Week 3.3.2 pending)
- [ ] 穩定性分析報告 (Week 3.3.3 pending)

---

## 結論

Template Mode 架構修復 (Bug #5) 是一次重大的架構糾正,解決了錯誤的代碼生成假設,改為正確的直接執行模式。此修復讓 Template Mode 首次正確運作,20 次迭代煙霧測試 100% 通過。

透過 Zen tracer 的完整架構追蹤,我們現在對 Template Mode 的執行流程有了清晰的理解,並將其完整文檔化。這為未來開發更多 Template 和優化系統提供了堅實的基礎。

**關鍵教訓**:
1. 📖 **不要假設**: 仔細閱讀代碼,確認實際實作
2. 🎯 **介面優先**: 從介面定義入手,理解設計意圖
3. 🔍 **系統追蹤**: 使用工具 (如 Zen tracer) 驗證執行流程
4. 📝 **及時文檔**: 重大架構變更立即文檔化

**下一步**:
- Week 3.3.2: 執行 200 次迭代穩定性測試
- Week 3.3.3: 生成穩定性分析報告
- Week 3.4: Week 3 acceptance checkpoint 驗證
