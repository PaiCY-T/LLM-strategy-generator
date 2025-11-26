# 如何啟用 LLM 學習模式 (Template Mode + JSON Mode + Learning Feedback)

## 當前狀態總結

### ✅ 已完成（Phase 1.1 JSON Parameter Output）
1. **Template Mode**: 使用 Momentum 黃金模板確保參數一致性
2. **JSON Parameter Output**: LLM 輸出 JSON 格式參數
3. **Pydantic Validation**: 嚴格的參數驗證（8 個 Literal 類型欄位）
4. **100% 成功率**: 100/100 次迭代全部成功

### ❌ 尚未啟用（LLM 學習功能）
- **FeedbackGenerator**: 未整合到 AutonomousLoop 迭代循環
- **性能反饋**: LLM 沒有收到前幾次迭代的性能指標反饋
- **學習優化**: 參數選擇是隨機探索，不是基於學習的優化

## 為什麼當前測試不是 "LLM Learning Mode"

當前的 100 圈測試使用：
```python
# run_100iteration_test.py
harness = ExtendedTestHarness(
    model='google/gemini-2.5-flash',
    template_mode=True,              # ✅ Template Mode 啟用
    template_name="Momentum",
    use_json_mode=True              # ✅ JSON Mode 啟用
)
```

但是 `AutonomousLoop` **沒有使用** `FeedbackGenerator`，所以：
- ❌ LLM 不知道之前的策略表現如何
- ❌ LLM 沒有收到 Sharpe ratio、champion 比較等反饋
- ❌ 參數選擇是隨機的，不是基於學習優化

## 配置檔案說明

`config/learning_system.yaml` 中的 LLM 設定：

```yaml
llm:
  # LLM 創新已啟用（預設）
  enabled: true

  # 提供商: openrouter, gemini, or openai
  provider: openrouter

  # 創新率: 30% 的迭代使用 LLM
  innovation_rate: 0.30

  # 模型選擇
  model: ${LLM_MODEL:google/gemini-2.5-flash}
```

**重要**: 這個設定控制的是 **LLM 驅動的策略創新**（與 Factor Graph 突變相對），**不是學習反饋循環**。

## LLM 學習模式的三種可能架構

### 選項 1: 整合 FeedbackGenerator 到 AutonomousLoop ⭐ **推薦**

**優點**:
- 保持現有的 Template Mode + JSON Mode
- 最小的程式碼變更
- 可以復用現有的測試基礎設施

**需要修改的檔案**:
1. `artifacts/working/modules/autonomous_loop.py`
   - 導入 `FeedbackGenerator`
   - 在 `__init__` 中初始化 FeedbackGenerator
   - 在每次迭代後生成反饋
   - 將反饋傳遞給下一次的 LLM 呼叫

**修改示例**:
```python
# 在 AutonomousLoop.__init__ 中
from src.learning.feedback_generator import FeedbackGenerator
from src.learning.champion_tracker import ChampionTracker
from src.learning.iteration_history import IterationHistory

# 初始化學習組件
self.iteration_history = IterationHistory(history_file)
self.champion_tracker = ChampionTracker(
    hall_of_fame=self.hall_of_fame,
    history=self.iteration_history,
    anti_churn=self.anti_churn
)
self.feedback_generator = FeedbackGenerator(
    history=self.iteration_history,
    champion_tracker=self.champion_tracker
)

# 在迭代循環中
for iteration in range(self.max_iterations):
    # 生成反饋（基於歷史表現）
    feedback = self.feedback_generator.generate_feedback(
        iteration_num=iteration,
        metrics=last_metrics,
        execution_result=last_execution_result,
        classification_level=last_classification
    )

    # 將反饋傳遞給參數生成器
    params, code = self.param_generator.generate_parameters_json_mode(
        performance_feedback=feedback  # 學習反饋
    )

    # 執行、評估、記錄...
```

### 選項 2: 使用 LearningLoop 替換 AutonomousLoop

**優點**:
- `LearningLoop` 已經整合了所有學習組件
- 程式碼更乾淨，責任分離更明確

**缺點**:
- ❌ `LearningLoop` 目前不支援 Template Mode
- ❌ `LearningLoop` 目前不支援 JSON Mode
- ❌ 需要重構 `ExtendedTestHarness`

**需要修改的檔案**:
1. `src/learning/iteration_executor.py` - 添加 Template Mode 支援
2. `src/learning/iteration_executor.py` - 添加 JSON Mode 支援
3. `tests/integration/extended_test_harness.py` - 使用 LearningLoop

### 選項 3: 修改 TemplateParameterGenerator 直接調用 FeedbackGenerator

**優點**:
- 不需要修改 AutonomousLoop
- 所有學習邏輯封裝在 TemplateParameterGenerator 內部

**缺點**:
- ❌ 違反單一責任原則
- ❌ TemplateParameterGenerator 需要依賴過多組件
- ❌ 難以測試和維護

## 推薦方案: 選項 1 的實現步驟

### Step 1: 修改 AutonomousLoop 添加 FeedbackGenerator

編輯 `artifacts/working/modules/autonomous_loop.py`:

1. 在 `__init__` 方法中初始化學習組件:
```python
from src.learning.feedback_generator import FeedbackGenerator
from src.learning.champion_tracker import ChampionTracker
from src.learning.iteration_history import IterationHistory

# 在 __init__ 中添加
if self.template_mode:
    # 初始化學習組件
    self.iteration_history = IterationHistory(history_file)
    self.champion_tracker = ChampionTracker(
        hall_of_fame=self.hall_of_fame,
        history=self.iteration_history,
        anti_churn=self.anti_churn
    )
    self.feedback_generator = FeedbackGenerator(
        history=self.iteration_history,
        champion_tracker=self.champion_tracker
    )
```

2. 在迭代循環中生成並使用反饋:
```python
# 在每次迭代開始時生成反饋
feedback = None
if iteration_num > 0 and self.template_mode:
    # 獲取上一次迭代的結果
    recent_records = self.iteration_history.load_recent(N=1)
    if recent_records:
        last_record = recent_records[0]
        feedback = self.feedback_generator.generate_feedback(
            iteration_num=iteration_num,
            metrics=last_record.metrics,
            execution_result=last_record.execution_result,
            classification_level=last_record.classification_level,
            error_msg=last_record.execution_result.get('error')
        )

# 將反饋傳遞給參數生成
if self.template_mode:
    params, code = self.param_generator.generate_parameters_json_mode(
        performance_feedback=feedback  # 學習反饋
    )
```

### Step 2: 修改 TemplateParameterGenerator 接收反饋

編輯 `src/generators/template_parameter_generator.py`:

```python
def generate_parameters_json_mode(
    self,
    performance_feedback: Optional[str] = None
) -> tuple[dict, str]:
    """Generate parameters using JSON mode with optional performance feedback.

    Args:
        performance_feedback: Learning feedback from FeedbackGenerator

    Returns:
        Tuple of (parameters dict, generated code)
    """
    # 構建提示，包含性能反饋
    prompt = self.prompt_builder.build_prompt(
        template_name=self.template_name,
        feedback_context=performance_feedback,  # 學習反饋
        performance_context="Generate optimal parameters based on feedback"
    )

    # ... rest of generation logic
```

### Step 3: 運行測試

```bash
# 清除舊的歷史
rm -f iteration_history.json champion.json

# 運行測試
PYTHONPATH=. python3 run_100iteration_test.py
```

### 預期結果

1. **第0次迭代**: 沒有反饋（初始探索）
2. **第1-10次迭代**:
   - 收到上一次的性能反饋
   - LLM 根據反饋調整參數選擇
3. **第10+次迭代**:
   - 明顯的學習趨勢
   - Champion 更新頻率增加
   - Sharpe ratio 逐步提升

## 驗證 LLM 學習是否有效

查看日誌中的反饋內容:
```bash
grep "feedback" logs/100iteration_test_*.log
```

應該看到類似這樣的反饋:
```
Iteration 5: SUCCESS
Performance:
- Sharpe: 0.654
- Classification: LEVEL_2

Trend: Sharpe improving: 0.45 → 0.52 → 0.65

Champion target: 0.85
Gap to champion: 24.7% below

Keep this direction! Consider incremental improvements while maintaining risk controls.
```

## 測試學習效果的指標

1. **Champion 更新頻率**: 應該從 1% 提升到 10-20%
2. **Sharpe ratio 趨勢**: 應該看到逐步提升的趨勢
3. **參數探索**: 應該看到參數選擇越來越接近 champion
4. **Cohen's d effect size**: 應該從 0.247 提升到 >0.4

## 總結

當前的 100 圈測試只使用了：
- ✅ Template Mode（降低 LLM 錯誤率）
- ✅ JSON Parameter Output（確保格式正確性）
- ❌ **沒有** LLM 學習反饋循環

要啟用完整的 LLM 學習模式，需要：
1. 整合 FeedbackGenerator 到 AutonomousLoop
2. 在每次迭代後生成性能反饋
3. 將反饋傳遞給下一次的 LLM 呼叫

**Template Mode 的主要作用是降低 LLM 錯誤機率**，確保生成的程式碼結構一致，但不會阻止 LLM 學習。學習反饋循環是獨立的功能，可以與 Template Mode 共同使用。
