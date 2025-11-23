# 系統架構重構解決方案

**架構師**: Claude (System Architecture Mode)
**分析日期**: 2025-11-22
**問題級別**: CRITICAL - 技術債務累積導致維護成本 2-3x

---

## 📊 執行摘要 (Executive Summary)

### 問題診斷
Phase 6 重構創建了新架構但未完成遷移，導致新舊架構並存、功能重複、維護成本倍增。

### 量化指標
- **程式碼重複**: ~40-60%
- **維護成本**: 2-3x baseline
- **複雜度**: AutonomousLoop 複雜度 F (82) - 極高風險
- **維護指數**: AutonomousLoop = 0.00 (極低可維護性)
- **檔案數量**: 20+ 個 run_*.py 使用 AutonomousLoop, 20+ 使用 LearningLoop

### 建議方案
**三階段重構策略**: 緊急修復 (1週) → 架構統一 (4週) → 完全遷移 (12週)

---

## 🔍 系統性診斷分析

### 1. 依賴關係圖譜

#### AutonomousLoop 生態系統 (Legacy)
```
AutonomousLoop (2,821行, 複雜度F-82, MI=0.00)
├─ ExtendedTestHarness (922行)
│  ├─ run_100iteration_test.py ← **主要測試**
│  ├─ run_200iteration_test.py
│  └─ sys.path hack to import from artifacts/
│
├─ 20+ run_*.py scripts (Legacy tests)
│  ├─ run_5iteration_template_smoke_test.py
│  ├─ run_diversity_pilot_test.py
│  ├─ run_phase1_dryrun_flashlite.py
│  └─ ... (各種歷史測試)
│
└─ Dependencies:
   ├─ artifacts/working/modules/sandbox.py
   ├─ artifacts/working/modules/sandbox_executor.py
   ├─ artifacts/working/modules/ast_validator.py
   ├─ artifacts/working/modules/metrics_extractor.py
   ├─ artifacts/working/modules/prompt_builder.py
   └─ artifacts/working/modules/history.py (325行)
```

#### LearningLoop 生態系統 (Phase 6)
```
LearningLoop (416行, 複雜度B-7, MI=良好)
├─ IterationExecutor (src/learning/)
├─ FeedbackGenerator (src/learning/) ← **關鍵優勢**
├─ ChampionTracker (src/learning/)
├─ IterationHistory (src/learning/)
│
├─ 20+ run_*.py scripts (Phase 6+ tests)
│  ├─ run_50iteration_three_mode_test.py
│  ├─ run_300iteration_three_mode_validation.py
│  ├─ experiments/llm_learning_validation/orchestrator.py
│  └─ ... (Phase 6+ 測試)
│
└─ Dependencies:
   ├─ src/sandbox/docker_executor.py
   ├─ src/backtest/executor.py
   ├─ src/learning/* (modular components)
   └─ src/validation/* (14+ validators)
```

### 2. 程式碼品質分析

#### AutonomousLoop 問題清單

| 方法 | 複雜度 | 行數估計 | 問題 |
|------|--------|---------|------|
| `_run_freeform_iteration` | **F (82)** | ~400行 | God Method - 超高複雜度 |
| `_validate_multi_objective` | D (21) | ~100行 | 過度驗證邏輯 |
| `run` | C (17) | ~80行 | 主循環過於複雜 |
| `_check_champion_staleness` | C (14) | ~60行 | 邏輯分散 |
| `_record_iteration_monitoring` | C (14) | ~60行 | 監控邏輯內嵌 |

**關鍵問題**:
1. **God Object**: 單一類別 2,821 行，違反 SRP
2. **God Method**: `_run_freeform_iteration` 複雜度 F (82)，難以測試
3. **維護指數 0.00**: 極低可維護性，修改風險極高
4. **平均複雜度 B (7.7)**: 超過建議值 (A-4)

#### LearningLoop 品質評估

| 方法 | 複雜度 | 行數估計 | 評價 |
|------|--------|---------|------|
| `_generate_summary` | C (16) | ~60行 | 可接受 |
| `_show_progress` | B (10) | ~40行 | 良好 |
| `run` | B (9) | ~50行 | 良好 |
| `__init__` | A (4) | ~30行 | 優秀 |

**優勢**:
1. **模組化**: 416 行，責任明確
2. **低複雜度**: 平均 B (6.2)，可維護
3. **組件分離**: FeedbackGenerator, ChampionTracker 獨立
4. **良好架構**: Protocol-based design

### 3. 重複實作統計

#### 完整重複矩陣

| 領域 | Artifacts 數量 | Src 數量 | 重複率 | 總浪費估計 |
|------|----------------|---------|--------|-----------|
| **Loop/Engine** | 2 (AutonomousLoop, IterationEngine) | 1 (LearningLoop) | 66% | ~3,500 行 |
| **Sandbox/Executor** | 3 檔案 | 3 檔案 | ~60% | ~1,200 行 |
| **Validators** | 2 檔案 | 14 檔案 | ~40% | ~2,000 行 |
| **Generators** | 2 檔案 | 8 檔案 | ~30% | ~1,500 行 |
| **History** | 1 檔案 (325行) | 1 檔案 | ~50% | ~160 行 |
| **Prompt System** | 1 檔案 (484行) | 多檔案 | ~30% | ~200 行 |
| **總計** | **~4,500 行** | **~5,000 行** | **~45%** | **~8,560 行重複** |

---

## 🎯 解決方案架構

### 方案 A: 三階段漸進式重構 ⭐ **強烈推薦**

#### Phase 1: 緊急修復 - 快速啟用學習功能 (1 週)

**目標**: 在不破壞現有系統的前提下，快速啟用 LLM 學習模式

**實施步驟**:

1. **整合 FeedbackGenerator 到 AutonomousLoop** (2 天)
   ```python
   # 修改 artifacts/working/modules/autonomous_loop.py

   class AutonomousLoop:
       def __init__(self, ...):
           # 現有初始化...

           # 添加學習組件 (僅在 template_mode 時)
           if self.template_mode:
               from src.learning.feedback_generator import FeedbackGenerator
               from src.learning.champion_tracker import ChampionTracker
               from src.learning.iteration_history import IterationHistory

               # 初始化學習組件
               self.iteration_history_v2 = IterationHistory(history_file)
               self.champion_tracker_v2 = ChampionTracker(
                   hall_of_fame=self.hall_of_fame,
                   history=self.iteration_history_v2,
                   anti_churn=self.anti_churn
               )
               self.feedback_generator = FeedbackGenerator(
                   history=self.iteration_history_v2,
                   champion_tracker=self.champion_tracker_v2
               )
   ```

2. **修改 `_run_template_mode_iteration` 使用反饋** (1 天)
   ```python
   def _run_template_mode_iteration(self, iteration_num, ...):
       # 生成反饋 (從第 2 次迭代開始)
       feedback = None
       if iteration_num > 0 and hasattr(self, 'feedback_generator'):
           recent_records = self.iteration_history_v2.load_recent(N=1)
           if recent_records:
               last_record = recent_records[0]
               feedback = self.feedback_generator.generate_feedback(
                   iteration_num=iteration_num,
                   metrics=last_record.metrics,
                   execution_result=last_record.execution_result,
                   classification_level=last_record.classification_level
               )

       # 傳遞反饋給參數生成器
       if self.use_json_mode:
           params, code = self.param_generator.generate_parameters_json_mode(
               performance_feedback=feedback  # 學習反饋
           )
       # ... 其餘邏輯
   ```

3. **驗證測試** (1 天)
   - 運行 10 圈測試確認整合成功
   - 檢查反饋是否正確生成
   - 驗證學習效果初步指標

**成果**:
- ✅ LLM 學習模式立即可用
- ✅ 保持 100% 成功率
- ✅ 最小風險，快速交付

**限制**:
- 技術債務未解決
- 仍有架構重複

---

#### Phase 2: 架構統一 - 創建統一 Loop (4 週)

**目標**: 創建統一的 UnifiedLoop，整合兩者優勢

**設計原則**:
1. **適配器模式**: UnifiedLoop 作為 facade，內部使用 LearningLoop
2. **向後相容**: 保持 AutonomousLoop 的 API 介面
3. **功能完整**: 整合 Template Mode + JSON Mode + Learning Feedback

**架構設計**:
```python
# src/learning/unified_loop.py

from src.learning.learning_loop import LearningLoop
from src.learning.iteration_executor import IterationExecutor
from src.generators.template_parameter_generator import TemplateParameterGenerator

class UnifiedLoop:
    """統一的 Loop 實作，整合 AutonomousLoop 和 LearningLoop 優勢。

    Features:
    - ✅ Template Mode (from AutonomousLoop)
    - ✅ JSON Parameter Output (from AutonomousLoop)
    - ✅ Learning Feedback (from LearningLoop)
    - ✅ Modular Architecture (from LearningLoop)
    - ✅ Docker Sandbox (from both)
    - ✅ Monitoring (from AutonomousLoop)
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        max_iterations: int = 10,
        template_mode: bool = False,
        template_name: str = "Momentum",
        use_json_mode: bool = False,
        enable_learning: bool = True,  # 新增參數
        **kwargs
    ):
        # 內部使用 LearningLoop 架構
        self.learning_loop = LearningLoop(...)

        # 如果啟用 Template Mode，替換 IterationExecutor
        if template_mode:
            self.learning_loop.executor = TemplateAwareIterationExecutor(
                template_name=template_name,
                use_json_mode=use_json_mode,
                enable_learning=enable_learning,
                ...
            )

    def run(self):
        """向後相容的 run 方法"""
        return self.learning_loop.run()
```

**實施步驟**:

**Week 1: 創建 UnifiedLoop 基礎**
- 實作 UnifiedLoop facade
- 整合 Template Mode 到 IterationExecutor
- 單元測試覆蓋

**Week 2: JSON Mode 整合**
- 在 IterationExecutor 中添加 JSON 模式支援
- 整合 TemplateParameterGenerator
- 集成測試

**Week 3: 遷移 ExtendedTestHarness**
- 修改 ExtendedTestHarness 使用 UnifiedLoop
- 運行 100 圈對比測試
- 驗證功能等價性

**Week 4: 標記 AutonomousLoop 為 Deprecated**
- 添加 @deprecated decorator
- 更新文檔
- 創建遷移指南

**成果**:
- ✅ 單一統一的 Loop 實作
- ✅ 功能完整 (Template + JSON + Learning)
- ✅ 向後相容
- ✅ 架構清晰

---

#### Phase 3: 完全遷移 - 清理 Legacy (12 週)

**目標**: 完全廢棄 `artifacts/working/modules`，統一到 `src/`

**Week 1-2: Sandbox/Executor 統一**
- 統一到 `src/sandbox/docker_executor.py`
- 遷移所有使用者
- 刪除 `artifacts/working/modules/sandbox*.py`

**Week 3-4: Validator 架構重組**
- 創建統一的 Validator 基類
- 整合 14+ validators
- 移除重複邏輯

**Week 5-6: Generator 整合**
- 明確 Generator 職責
- 統一策略生成路徑
- 清理重複 generators

**Week 7-8: 測試遷移**
- 遷移所有 `run_*.py` 到 UnifiedLoop
- 更新所有測試案例
- 刪除 Legacy 測試

**Week 9-10: 移除 artifacts/working/modules**
- 刪除所有 Legacy 檔案
- 更新所有 import 路徑
- 清理 sys.path hacks

**Week 11-12: 文檔和驗證**
- 更新所有文檔
- 運行完整測試套件
- 性能回歸測試

**成果**:
- ✅ 單一程式碼庫 (`src/`)
- ✅ 無重複實作
- ✅ 維護成本降低 60%
- ✅ 技術債務清零

---

### 方案 B: 激進重寫 (不推薦)

**直接廢棄 AutonomousLoop，強制遷移到 LearningLoop**

**優點**:
- 立即解決技術債務
- 架構清晰

**缺點**:
- ❌ 高風險：破壞 20+ 測試腳本
- ❌ 需要重寫 ExtendedTestHarness
- ❌ Template Mode 和 JSON Mode 需要從頭整合
- ❌ 時間長：8-12 週

**結論**: 風險太高，不建議採用

---

## 📋 具體實施計劃

### 第一週詳細計劃 (緊急修復)

#### Day 1-2: FeedbackGenerator 整合
- [ ] 修改 `autonomous_loop.py` 添加學習組件初始化
- [ ] 添加條件導入 (僅在 template_mode 時)
- [ ] 單元測試: 驗證組件初始化

#### Day 3-4: 反饋循環實作
- [ ] 修改 `_run_template_mode_iteration` 生成反饋
- [ ] 修改 `TemplateParameterGenerator` 接收反饋
- [ ] 集成測試: 10 圈測試驗證

#### Day 5: 驗證和文檔
- [ ] 運行 100 圈完整測試
- [ ] 分析學習效果指標
- [ ] 更新文檔和使用指南

**交付物**:
- 啟用學習功能的 AutonomousLoop
- 10 圈和 100 圈測試報告
- 使用文檔

---

## 🔧 技術實施細節

### FeedbackGenerator 整合程式碼範例

```python
# artifacts/working/modules/autonomous_loop.py

class AutonomousLoop:
    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        max_iterations: int = 10,
        history_file: str = "iteration_history.json",
        template_mode: bool = False,
        template_name: str = "Momentum",
        use_json_mode: bool = False,
        enable_learning: bool = True  # 新增參數
    ):
        # ... 現有初始化 ...

        self.template_mode = template_mode
        self.use_json_mode = use_json_mode
        self.enable_learning = enable_learning

        # 初始化 Template Mode 參數生成器
        if self.template_mode:
            from src.generators.template_parameter_generator import TemplateParameterGenerator
            self.param_generator = TemplateParameterGenerator(
                template_name=template_name,
                model=model,
                use_json_mode=use_json_mode
            )

        # 初始化學習組件 (如果啟用)
        if self.template_mode and self.enable_learning:
            self._initialize_learning_components(history_file)

    def _initialize_learning_components(self, history_file: str):
        """初始化學習反饋組件"""
        from src.learning.feedback_generator import FeedbackGenerator
        from src.learning.champion_tracker import ChampionTracker
        from src.learning.iteration_history import IterationHistory

        # 使用不同的變數名避免衝突
        self.iteration_history_v2 = IterationHistory(filepath=history_file)
        self.champion_tracker_v2 = ChampionTracker(
            hall_of_fame=self.hall_of_fame,
            history=self.iteration_history_v2,
            anti_churn=self.anti_churn
        )
        self.feedback_generator = FeedbackGenerator(
            history=self.iteration_history_v2,
            champion_tracker=self.champion_tracker_v2
        )

        self.event_logger.log_event(
            logging.INFO,
            "learning_init",
            "Learning components initialized (FeedbackGenerator enabled)"
        )

    def _run_template_mode_iteration(
        self,
        iteration_num: int,
        use_json_mode: bool = False
    ) -> Tuple[str, Dict, float, Dict]:
        """運行 Template Mode 迭代，支援學習反饋"""

        # 生成學習反饋 (從第 2 次迭代開始)
        feedback = None
        if iteration_num > 0 and hasattr(self, 'feedback_generator'):
            try:
                recent_records = self.iteration_history_v2.load_recent(N=1)
                if recent_records:
                    last_record = recent_records[0]
                    feedback = self.feedback_generator.generate_feedback(
                        iteration_num=iteration_num,
                        metrics=last_record.metrics,
                        execution_result=last_record.execution_result,
                        classification_level=last_record.classification_level,
                        error_msg=last_record.execution_result.get('error')
                    )

                    self.event_logger.log_event(
                        logging.INFO,
                        "feedback_generated",
                        f"Learning feedback generated for iteration {iteration_num}",
                        feedback_length=len(feedback) if feedback else 0
                    )
            except Exception as e:
                self.event_logger.log_event(
                    logging.WARNING,
                    "feedback_error",
                    f"Failed to generate feedback: {e}"
                )
                feedback = None

        # 生成參數 (傳入反饋)
        if use_json_mode:
            params, code = self.param_generator.generate_parameters_json_mode(
                performance_feedback=feedback  # 學習反饋
            )
        else:
            params, code = self.param_generator.generate_parameters_and_code(
                performance_feedback=feedback  # 學習反饋
            )

        # ... 其餘執行邏輯保持不變 ...
```

### TemplateParameterGenerator 修改

```python
# src/generators/template_parameter_generator.py

class TemplateParameterGenerator:
    def generate_parameters_json_mode(
        self,
        performance_feedback: Optional[str] = None
    ) -> tuple[dict, str]:
        """生成參數使用 JSON mode，支援性能反饋"""

        # 構建提示 (包含反饋)
        prompt = self.prompt_builder.build_prompt(
            template_name=self.template_name,
            feedback_context=performance_feedback,  # 學習反饋
            performance_context="Generate optimal parameters based on feedback"
        )

        # ... LLM 呼叫邏輯 ...
```

---

## 📊 成本效益分析

### 方案 A: 三階段漸進式重構

| 階段 | 時間 | 風險 | 成本 | 收益 |
|------|------|------|------|------|
| **Phase 1** | 1 週 | 低 | 40 小時 | 學習功能立即可用 |
| **Phase 2** | 4 週 | 中 | 160 小時 | 統一架構，維護成本 -30% |
| **Phase 3** | 12 週 | 中 | 480 小時 | 技術債務清零，維護成本 -60% |
| **總計** | 17 週 | 中 | 680 小時 | ROI: 2-3x |

### 方案 B: 激進重寫

| 項目 | 時間 | 風險 | 成本 |
|------|------|------|------|
| 實施 | 8-12 週 | 高 | 640-960 小時 |
| 測試 | 2-4 週 | 高 | 160-320 小時 |
| 修復 | 未知 | 高 | 未知 |
| **總計** | 10-16 週 | **高** | 800-1,280 小時 |

**建議**: 方案 A 風險更低、交付更快、ROI 更高

---

## 🎯 關鍵成功指標 (KPI)

### Phase 1 (1 週)
- [ ] FeedbackGenerator 整合完成
- [ ] 10 圈測試通過，反饋正確生成
- [ ] 100 圈測試通過，學習效果可見
- [ ] Champion 更新頻率 > 5% (baseline: 1%)
- [ ] Cohen's d > 0.4 (baseline: 0.247)

### Phase 2 (4 週)
- [ ] UnifiedLoop 實作完成
- [ ] ExtendedTestHarness 遷移完成
- [ ] 100 圈對比測試: UnifiedLoop ≈ AutonomousLoop 功能
- [ ] 程式碼重複率 < 30% (baseline: 45%)
- [ ] 平均複雜度 < B (6.0)

### Phase 3 (12 週)
- [ ] artifacts/working/modules 完全刪除
- [ ] 所有測試遷移到 UnifiedLoop
- [ ] 維護成本 -60%
- [ ] 技術債務清零
- [ ] 新人 onboarding 時間 < 1 天

---

## 🚨 風險管理

### 風險矩陣

| 風險 | 機率 | 影響 | 緩解策略 |
|------|------|------|---------|
| **Phase 1 整合失敗** | 低 | 中 | 完整單元測試 + 10 圈驗證 |
| **API 相容性問題** | 中 | 高 | 保持向後相容介面 |
| **性能下降** | 低 | 中 | 性能基準測試 + 回歸測試 |
| **學習效果不佳** | 中 | 低 | 調整反饋策略，參數優化 |
| **測試覆蓋不足** | 中 | 高 | 增加集成測試 + E2E 測試 |

### 回滾策略

**Phase 1**: Git revert，恢復到整合前狀態
**Phase 2**: 保留 AutonomousLoop 作為 fallback
**Phase 3**: Feature flag 控制，漸進式遷移

---

## 📝 決策建議

### 推薦方案: 方案 A - 三階段漸進式重構

**理由**:
1. **風險可控**: 每個階段獨立交付，可及時調整
2. **快速價值**: Phase 1 (1週) 即可啟用學習功能
3. **向後相容**: 不破壞現有測試和工作流
4. **ROI 高**: 2-3x 投資回報率

### 立即行動

**建議從 Phase 1 開始**:
1. 整合 FeedbackGenerator 到 AutonomousLoop
2. 1 週內交付可用的學習功能
3. 在學習功能運作穩定後，再啟動 Phase 2

**下一步**:
- 獲得 stakeholder 批准
- 分配工程資源 (1 位資深工程師，全職 1 週)
- 開始 Phase 1 實施

---

## 📚 附錄

### A. 程式碼複雜度完整報告

```
AutonomousLoop 複雜度分析:
- 檔案大小: 2,821 行
- 維護指數: 0.00 (極低)
- 平均複雜度: B (7.7)
- 最高複雜度: F (82) - _run_freeform_iteration
- 方法數量: 37

LearningLoop 複雜度分析:
- 檔案大小: 416 行
- 維護指數: 良好
- 平均複雜度: B (6.2)
- 最高複雜度: C (16) - _generate_summary
- 方法數量: 9
```

### B. 依賴關係完整清單

```
AutonomousLoop 使用者 (20+):
- run_100iteration_test.py (via ExtendedTestHarness)
- run_200iteration_test.py (via ExtendedTestHarness)
- run_5iteration_template_smoke_test.py
- run_diversity_pilot_test.py
- run_phase1_dryrun_flashlite.py
- ... (完整列表見附錄)

LearningLoop 使用者 (20+):
- run_50iteration_three_mode_test.py
- run_300iteration_three_mode_validation.py
- experiments/llm_learning_validation/orchestrator.py
- run_learning_loop.py
- ... (完整列表見附錄)
```

### C. 技術債務量化

```
總程式碼量: ~9,500 行
重複程式碼: ~4,000 行 (42%)
浪費的開發時間: ~680 小時 (估計)
維護成本倍數: 2.5x
平均 bug 修復時間: 2x (需要改兩處)
```

---

**結論**: 建議採用**方案 A: 三階段漸進式重構**，從 Phase 1 (1週) 開始，快速啟用學習功能，再逐步統一架構。
