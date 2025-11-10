# API Audit Tool

**自動化 API 審計工具** - 檢測代碼中的 API 不匹配問題

## 📋 功能

基於 `docs/API_FIXES_DEBUG_HISTORY.md` 中記錄的問題，這個工具可以：

✅ 自動掃描代碼中的方法調用
✅ 檢測方法名是否正確
✅ 驗證參數名稱和數量
✅ 識別已知的 API 錯誤模式
✅ 生成詳細的審計報告

## 🚀 快速開始

### 基本用法

```bash
# 掃描整個 src/ 目錄
python tools/api_audit.py

# 指定專案根目錄
python tools/api_audit.py --root /path/to/project

# 生成文本報告
python tools/api_audit.py --output tools/reports/audit_report.txt

# 生成 JSON 報告
python tools/api_audit.py --json tools/reports/audit_report.json

# 詳細輸出
python tools/api_audit.py --verbose
```

### 在 CI/CD 中使用

```bash
# 在 CI pipeline 中運行（如果有錯誤會 exit 1）
python tools/api_audit.py --json audit_results.json
```

## 📊 報告範例

### 文本格式

```
================================================================================
API AUDIT REPORT
================================================================================

Summary:
  Total method calls scanned: 1247
  Errors found: 3
  Warnings found: 5

--------------------------------------------------------------------------------
🔴 ERRORS
--------------------------------------------------------------------------------

1. METHOD_NOT_FOUND
   File: src/learning/learning_loop.py:193
   Call: self.history.save_record()
   Message: Method 'save_record' not found in IterationHistory.
            Available methods: save, get_recent, load_all
   Expected signature: save(record)

2. WRONG_PARAMS
   File: src/learning/iteration_executor.py:372
   Call: engine.generate_strategy(feedback)
   Message: Method 'generate_strategy' not found in InnovationEngine.
            Did you mean: generate_innovation()?
   Expected signature: generate_innovation(champion_code, champion_metrics,
                                           failure_history=None,
                                           target_metric="sharpe_ratio")

3. MISSING_REQUIRED_PARAMS
   File: src/learning/iteration_executor.py:755
   Call: self.error_classifier.classify_single(strategy_metrics)
   Message: Wrong classifier used. ErrorClassifier is for error types,
            not strategy performance. Use SuccessClassifier instead.
```

### JSON 格式

```json
{
  "summary": {
    "total_calls": 1247,
    "total_mismatches": 8,
    "errors": 3,
    "warnings": 5
  },
  "mismatches": [
    {
      "severity": "error",
      "type": "method_not_found",
      "file": "src/learning/learning_loop.py",
      "line": 193,
      "class": "IterationHistory",
      "method": "save_record",
      "message": "Method 'save_record' not found...",
      "expected_signature": {
        "method": "save",
        "params": ["record"],
        "required": ["record"]
      }
    }
  ]
}
```

## 🔍 檢測的 API 錯誤類型

### 1. 方法名錯誤 (METHOD_NOT_FOUND)

```python
# ❌ 錯誤
self.history.save_record(record)

# ✅ 正確
self.history.save(record)
```

### 2. 錯誤的類別 (WRONG_CLASS)

```python
# ❌ 錯誤 - ErrorClassifier 是用來分類錯誤類型的
self.error_classifier = ErrorClassifier()
result = self.error_classifier.classify_single(metrics)

# ✅ 正確 - SuccessClassifier 才是用來分類策略性能的
self.success_classifier = SuccessClassifier()
result = self.success_classifier.classify_single(metrics)
```

### 3. 參數名稱錯誤 (WRONG_PARAMS)

```python
# ❌ 錯誤
self.history = IterationHistory(file_path=config.history_file)

# ✅ 正確
self.history = IterationHistory(filepath=config.history_file)
```

### 4. 缺少必需參數 (MISSING_REQUIRED_PARAMS)

```python
# ❌ 錯誤 - 缺少必需的 champion_metrics 參數
engine.generate_innovation(champion_code)

# ✅ 正確
engine.generate_innovation(
    champion_code=code,
    champion_metrics=metrics,
    failure_history=None,
    target_metric="sharpe_ratio"
)
```

### 5. 方法 vs 屬性 (METHOD_VS_PROPERTY)

```python
# ❌ 錯誤 - champion 是 property，不是方法
champion = self.champion_tracker.get_champion()

# ✅ 正確
champion = self.champion_tracker.champion
```

## 📁 追蹤的 API 類別

工具會自動檢查以下類別的 API 調用：

- `IterationHistory` - 迭代歷史管理
- `ChampionTracker` - Champion 追蹤
- `FeedbackGenerator` - 反饋生成
- `ErrorClassifier` - 錯誤分類器（用於執行錯誤）
- `SuccessClassifier` - 成功分類器（用於策略性能）
- `InnovationEngine` - LLM 策略生成
- `IterationExecutor` - 迭代執行器
- `LearningLoop` - 學習循環主控制器

## 🛠️ 配置

編輯 `tools/api_audit_config.yaml` 來自訂：

- 已知 API 問題列表
- 要掃描的目錄
- 排除模式
- 報告格式

## 🧪 測試審計工具

```bash
# 運行審計並驗證結果
python tools/api_audit.py --output tools/reports/test_audit.txt

# 檢查特定文件
python -c "
from tools.api_audit import APIAuditor
auditor = APIAuditor()
calls = auditor._scan_file('src/learning/learning_loop.py')
print(f'Found {len(calls)} method calls')
"
```

## 📈 整合到開發工作流程

### Pre-commit Hook

在 `.git/hooks/pre-commit` 中添加：

```bash
#!/bin/bash
echo "Running API audit..."
python tools/api_audit.py
if [ $? -ne 0 ]; then
    echo "❌ API audit failed. Please fix the errors before committing."
    exit 1
fi
echo "✅ API audit passed"
```

### GitHub Actions

在 `.github/workflows/api-audit.yml` 中添加：

```yaml
name: API Audit
on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Run API Audit
        run: |
          python tools/api_audit.py --json audit_results.json
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: api-audit-results
          path: audit_results.json
```

## 🔧 擴展工具

### 添加新的 API 類別

在 `api_audit.py` 的 `api_classes` 字典中添加：

```python
self.api_classes = {
    # ... existing classes ...
    "YourNewClass": "src.your.module.path",
}
```

### 自定義檢查規則

繼承 `APIAuditor` 並覆寫 `audit_call` 方法：

```python
class CustomAPIAuditor(APIAuditor):
    def audit_call(self, call: MethodCall) -> Optional[APIMismatch]:
        # Your custom logic
        mismatch = super().audit_call(call)

        # Add custom checks
        if call.method_name == "deprecated_method":
            return APIMismatch(
                severity='warning',
                type='deprecated',
                call=call,
                message="This method is deprecated"
            )

        return mismatch
```

## 📚 相關文檔

- [`docs/API_FIXES_DEBUG_HISTORY.md`](../docs/API_FIXES_DEBUG_HISTORY.md) - 已修復的 API 問題歷史
- [`tools/api_audit_config.yaml`](./api_audit_config.yaml) - 審計工具配置

## 🐛 已知問題

1. **動態方法調用**: 工具目前無法檢測使用 `getattr()` 或其他動態方式的方法調用
2. **第三方庫**: 僅檢查專案內部的 API，不檢查第三方庫
3. **型別推斷**: 對於複雜的型別推斷可能不準確

## 🤝 貢獻

如果你發現新的 API 問題模式，請：

1. 更新 `docs/API_FIXES_DEBUG_HISTORY.md`
2. 在 `api_audit_config.yaml` 中添加檢測規則
3. 提交 PR

## 📝 License

MIT License - 與專案主體相同
