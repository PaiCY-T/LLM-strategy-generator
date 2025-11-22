# UnifiedLoop 完整重構計畫

**目標**: 直接創建 UnifiedLoop，整合 AutonomousLoop 和 LearningLoop 的所有優勢

---

## 📋 重構目標

### 最終架構
```
UnifiedLoop (< 500 行)
├─ Template Mode (from AutonomousLoop)
├─ JSON Parameter Output (from AutonomousLoop)
├─ Learning Feedback (from LearningLoop)
├─ Modular Architecture (from LearningLoop)
├─ Docker Sandbox (統一)
└─ Monitoring (整合)
```

### 功能完整性檢查表
- [x] ✅ Template Mode - 確保參數一致性
- [x] ✅ JSON Parameter Output - Pydantic 驗證
- [x] ✅ Learning Feedback - 性能反饋循環
- [x] ✅ FeedbackGenerator 整合
- [x] ✅ ChampionTracker 整合
- [x] ✅ IterationHistory 整合
- [x] ✅ Docker Sandbox 支援
- [x] ✅ Monitoring 系統
- [x] ✅ Checkpointing 機制
- [x] ✅ 向後相容 API

---

## 🎯 實施策略

### 核心設計原則

1. **Composition Over Inheritance**
   - UnifiedLoop 使用 LearningLoop 的架構
   - 通過組合而非繼承整合功能

2. **Strategy Pattern**
   - IterationExecutor 可切換策略
   - TemplateIterationExecutor 處理 Template Mode
   - StandardIterationExecutor 處理標準模式

3. **Adapter Pattern**
   - UnifiedLoop 作為 Facade
   - 提供 AutonomousLoop 相容的 API
   - 內部使用 LearningLoop 架構

4. **Dependency Injection**
   - 所有組件可注入替換
   - 便於測試和擴展

---

## 📐 架構設計

### 類別結構

```python
# src/learning/unified_loop.py

class UnifiedLoop:
    """統一的 Loop 實作，整合所有功能。

    Architecture:
    - Facade for LearningLoop (modular architecture)
    - Template Mode via TemplateIterationExecutor
    - JSON Mode via TemplateParameterGenerator
    - Learning Feedback via FeedbackGenerator

    Backward Compatibility:
    - Provides AutonomousLoop-compatible API
    - Can be used as drop-in replacement
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        max_iterations: int = 10,
        history_file: str = "iteration_history.json",
        template_mode: bool = False,
        template_name: str = "Momentum",
        use_json_mode: bool = False,
        enable_learning: bool = True,
        enable_monitoring: bool = True,
        **kwargs
    ):
        # Initialize configuration
        self.config = self._build_config(
            model=model,
            max_iterations=max_iterations,
            history_file=history_file,
            template_mode=template_mode,
            template_name=template_name,
            use_json_mode=use_json_mode,
            enable_learning=enable_learning,
            enable_monitoring=enable_monitoring,
            **kwargs
        )

        # Initialize core components
        self._initialize_components()

    def _build_config(self, **kwargs) -> LearningConfig:
        """Build unified configuration."""
        pass

    def _initialize_components(self):
        """Initialize all components based on configuration."""
        # History and tracking
        self.history = IterationHistory(self.config.history_file)

        # Champion tracking
        self.champion_tracker = ChampionTracker(...)

        # Feedback generator (if learning enabled)
        if self.config.enable_learning:
            self.feedback_generator = FeedbackGenerator(...)

        # Iteration executor (template or standard)
        if self.config.template_mode:
            self.executor = TemplateIterationExecutor(
                template_name=self.config.template_name,
                use_json_mode=self.config.use_json_mode,
                feedback_generator=self.feedback_generator if self.config.enable_learning else None,
                ...
            )
        else:
            self.executor = StandardIterationExecutor(...)

        # Monitoring (if enabled)
        if self.config.enable_monitoring:
            self.monitoring = MonitoringSystem(...)

    def run(self):
        """Execute the unified loop."""
        for iteration in range(self.config.max_iterations):
            # Execute iteration
            result = self.executor.execute(iteration)

            # Track result
            self.history.save(result)

            # Update champion
            self.champion_tracker.update(result)

            # Monitor (if enabled)
            if self.config.enable_monitoring:
                self.monitoring.record(result)

        return self._generate_summary()
```

### TemplateIterationExecutor

```python
# src/learning/template_iteration_executor.py

class TemplateIterationExecutor(IterationExecutor):
    """Iteration executor with Template Mode support.

    Integrates:
    - TemplateParameterGenerator (JSON or code mode)
    - FeedbackGenerator (optional, for learning)
    - Template-based code generation
    """

    def __init__(
        self,
        template_name: str,
        use_json_mode: bool,
        feedback_generator: Optional[FeedbackGenerator] = None,
        model: str = "gemini-2.5-flash",
        **kwargs
    ):
        self.template_name = template_name
        self.use_json_mode = use_json_mode
        self.feedback_generator = feedback_generator

        # Initialize parameter generator
        self.param_generator = TemplateParameterGenerator(
            template_name=template_name,
            model=model,
            use_json_mode=use_json_mode
        )

        # Initialize code generator
        self.code_generator = TemplateCodeGenerator(
            template_name=template_name
        )

    def execute(self, iteration_num: int, **kwargs) -> IterationResult:
        """Execute one iteration with template mode."""

        # Generate feedback (if enabled and not first iteration)
        feedback = None
        if self.feedback_generator and iteration_num > 0:
            feedback = self.feedback_generator.generate_feedback(
                iteration_num=iteration_num,
                **kwargs
            )

        # Generate parameters
        if self.use_json_mode:
            params, _ = self.param_generator.generate_parameters_json_mode(
                performance_feedback=feedback
            )
            # Generate code from parameters
            code = self.code_generator.generate_code(params)
        else:
            params, code = self.param_generator.generate_parameters_and_code(
                performance_feedback=feedback
            )

        # Execute strategy
        result = self._execute_strategy(code, params)

        return IterationResult(
            iteration_num=iteration_num,
            code=code,
            parameters=params,
            metrics=result.metrics,
            feedback=feedback,
            ...
        )
```

---

## 🛠️ 實施步驟

### Week 1: 核心架構

#### Day 1-2: UnifiedLoop 基礎框架
```
任務:
1. 創建 src/learning/unified_loop.py
2. 實作基本初始化和配置
3. 設計組件注入機制
4. 單元測試: 配置和初始化

交付物:
- UnifiedLoop 類別骨架
- 配置系統
- 基本單元測試
```

#### Day 3-4: TemplateIterationExecutor
```
任務:
1. 創建 src/learning/template_iteration_executor.py
2. 整合 TemplateParameterGenerator
3. 整合 FeedbackGenerator
4. 實作 JSON 和 Code 兩種模式
5. 單元測試: 模板執行邏輯

交付物:
- TemplateIterationExecutor 實作
- JSON/Code 模式切換
- 單元測試覆蓋
```

#### Day 5: 整合測試
```
任務:
1. 集成測試: UnifiedLoop + TemplateIterationExecutor
2. 10 圈測試驗證
3. 對比測試: vs AutonomousLoop
4. 修復發現的問題

交付物:
- 集成測試套件
- 10 圈測試報告
- 功能對比報告
```

### Week 2: ExtendedTestHarness 遷移

#### Day 6-7: 創建 UnifiedTestHarness
```
任務:
1. 創建 tests/integration/unified_test_harness.py
2. 遷移 ExtendedTestHarness 功能
3. 使用 UnifiedLoop 替代 AutonomousLoop
4. 保持向後相容 API

交付物:
- UnifiedTestHarness 實作
- API 相容性測試
```

#### Day 8-9: 100 圈對比測試
```
任務:
1. 運行 100 圈測試 (UnifiedLoop)
2. 對比 100 圈測試 (AutonomousLoop)
3. 功能等價性驗證
4. 性能基準測試

交付物:
- 100 圈測試報告 (UnifiedLoop)
- 對比分析報告
- 性能基準
```

#### Day 10: 文檔和清理
```
任務:
1. 更新使用文檔
2. 創建遷移指南
3. 標記 AutonomousLoop 為 @deprecated
4. Code review 和優化

交付物:
- 完整文檔
- 遷移指南
- Deprecation warnings
```

### Week 3: Monitoring 和 Sandbox 整合

#### Day 11-12: Monitoring 整合
```
任務:
1. 整合 Monitoring 系統到 UnifiedLoop
2. 整合 MetricsCollector
3. 整合 ResourceMonitor
4. 整合 DiversityMonitor

交付物:
- 完整 Monitoring 支援
- Monitoring 測試
```

#### Day 13-14: Docker Sandbox 整合
```
任務:
1. 統一 Sandbox 實作到 src/sandbox/docker_executor.py
2. 遷移 UnifiedLoop 使用統一 Sandbox
3. 安全性測試
4. 性能測試

交付物:
- 統一 Sandbox 實作
- 安全性測試報告
```

#### Day 15: 完整測試
```
任務:
1. 運行完整測試套件
2. 200 圈長期測試
3. 性能回歸測試
4. 修復發現的問題

交付物:
- 完整測試報告
- 性能基準
- Bug fix list
```

### Week 4: 遷移和廢棄

#### Day 16-18: 測試腳本遷移
```
任務:
1. 更新 run_100iteration_test.py 使用 UnifiedTestHarness
2. 更新 run_200iteration_test.py
3. 創建遷移工具自動更新其他腳本
4. 驗證所有測試腳本

交付物:
- 遷移的測試腳本
- 遷移工具
- 驗證報告
```

#### Day 19-20: 標記和文檔
```
任務:
1. 在 AutonomousLoop 添加 @deprecated decorator
2. 添加 deprecation warnings
3. 更新所有文檔
4. 創建完整的遷移時間表

交付物:
- Deprecation 實作
- 完整文檔更新
- 遷移時間表
```

---

## 🧪 測試策略

### 單元測試
```python
# tests/learning/test_unified_loop.py

def test_unified_loop_initialization():
    """測試 UnifiedLoop 初始化"""
    loop = UnifiedLoop(
        model="gemini-2.5-flash",
        max_iterations=10,
        template_mode=True,
        use_json_mode=True,
        enable_learning=True
    )
    assert loop.config.template_mode is True
    assert loop.config.use_json_mode is True
    assert loop.feedback_generator is not None

def test_template_mode_execution():
    """測試 Template Mode 執行"""
    loop = UnifiedLoop(template_mode=True)
    result = loop.executor.execute(iteration_num=0)
    assert result.parameters is not None
    assert result.code is not None

def test_learning_feedback_generation():
    """測試學習反饋生成"""
    loop = UnifiedLoop(enable_learning=True, template_mode=True)
    # First iteration - no feedback
    result1 = loop.executor.execute(iteration_num=0)
    assert result1.feedback is None

    # Second iteration - should have feedback
    loop.history.save(result1)
    result2 = loop.executor.execute(iteration_num=1)
    assert result2.feedback is not None
```

### 集成測試
```python
# tests/integration/test_unified_loop_integration.py

def test_10_iteration_run():
    """測試 10 圈完整執行"""
    loop = UnifiedLoop(
        max_iterations=10,
        template_mode=True,
        use_json_mode=True,
        enable_learning=True
    )
    summary = loop.run()

    assert summary['total_iterations'] == 10
    assert summary['success_rate'] >= 0.9
    assert 'champion' in summary

def test_backward_compatibility():
    """測試向後相容性"""
    # UnifiedLoop should work like AutonomousLoop
    loop = UnifiedLoop(
        model="gemini-2.5-flash",
        max_iterations=5,
        history_file="test_history.json",
        template_mode=True,
        template_name="Momentum",
        use_json_mode=True
    )

    # Should have same API as AutonomousLoop
    assert hasattr(loop, 'run')
    assert hasattr(loop, 'history')
```

### 對比測試
```python
# tests/integration/test_unified_vs_autonomous.py

def test_100_iteration_comparison():
    """對比 UnifiedLoop vs AutonomousLoop (100 圈)"""

    # Run with AutonomousLoop
    autonomous = AutonomousLoop(
        model="gemini-2.5-flash",
        max_iterations=100,
        template_mode=True,
        use_json_mode=True
    )
    autonomous_results = autonomous.run()

    # Run with UnifiedLoop
    unified = UnifiedLoop(
        model="gemini-2.5-flash",
        max_iterations=100,
        template_mode=True,
        use_json_mode=True,
        enable_learning=True
    )
    unified_results = unified.run()

    # Compare
    assert unified_results['success_rate'] >= autonomous_results['success_rate']
    # Learning should improve performance
    assert unified_results['avg_sharpe'] >= autonomous_results['avg_sharpe']
```

---

## 📊 驗收標準

### 功能完整性
- [ ] Template Mode 正常運作
- [ ] JSON Parameter Output 正常運作
- [ ] Learning Feedback 正常運作
- [ ] FeedbackGenerator 整合成功
- [ ] ChampionTracker 整合成功
- [ ] Docker Sandbox 整合成功
- [ ] Monitoring 系統整合成功

### 性能指標
- [ ] 100 圈測試通過率 ≥ 95%
- [ ] 學習效果: Champion 更新率 > 5%
- [ ] 學習效果: Cohen's d > 0.4
- [ ] 性能: 執行時間 ≤ AutonomousLoop * 1.1

### 品質指標
- [ ] 程式碼複雜度: 平均 < B (6.0)
- [ ] 維護指數: > 60
- [ ] 測試覆蓋率: > 80%
- [ ] 文檔完整性: 100%

### 向後相容性
- [ ] API 相容: ExtendedTestHarness 無需修改即可使用
- [ ] 配置相容: 所有參數向後相容
- [ ] 檔案格式相容: history.json, champion.json 格式相同

---

## 🚀 部署計畫

### Phase 1: Soft Launch (Week 1-2)
- UnifiedLoop 可用但標記為 Beta
- AutonomousLoop 仍為預設
- 提供並行測試能力

### Phase 2: Migration (Week 3)
- UnifiedTestHarness 成為預設
- AutonomousLoop 標記為 Deprecated
- 提供遷移工具和指南

### Phase 3: Deprecation (Week 4)
- 所有新測試使用 UnifiedLoop
- AutonomousLoop 添加 deprecation warnings
- 設定 6 個月後完全移除時間表

---

## 📝 交付物清單

### 程式碼
- [ ] src/learning/unified_loop.py
- [ ] src/learning/template_iteration_executor.py
- [ ] src/learning/unified_config.py
- [ ] tests/integration/unified_test_harness.py

### 測試
- [ ] tests/learning/test_unified_loop.py
- [ ] tests/learning/test_template_iteration_executor.py
- [ ] tests/integration/test_unified_loop_integration.py
- [ ] tests/integration/test_unified_vs_autonomous.py

### 文檔
- [ ] docs/unified_loop_guide.md
- [ ] docs/migration_guide.md
- [ ] docs/api_reference.md
- [ ] CHANGELOG.md 更新

### 工具
- [ ] scripts/migrate_to_unified_loop.py
- [ ] scripts/validate_migration.py

---

## ⚠️ 風險和緩解

### 風險 1: API 不相容
- **機率**: 中
- **影響**: 高
- **緩解**: 完整的向後相容性測試，保持 AutonomousLoop API

### 風險 2: 性能下降
- **機率**: 低
- **影響**: 中
- **緩解**: 性能基準測試，優化關鍵路徑

### 風險 3: 學習效果不佳
- **機率**: 中
- **影響**: 低
- **緩解**: 調整 FeedbackGenerator 策略，參數優化

### 風險 4: 測試失敗
- **機率**: 中
- **影響**: 高
- **緩解**: 漸進式遷移，保留 AutonomousLoop 作為 fallback

---

## 📅 時間表

| Week | 重點 | 交付物 |
|------|------|--------|
| **Week 1** | 核心架構 | UnifiedLoop, TemplateIterationExecutor |
| **Week 2** | TestHarness 遷移 | UnifiedTestHarness, 100 圈測試 |
| **Week 3** | 整合和優化 | Monitoring, Sandbox, 200 圈測試 |
| **Week 4** | 遷移和部署 | Deprecation, 文檔, 遷移工具 |

**總時間**: 4 週 (160 小時)
**團隊規模**: 1 位資深工程師全職

---

## ✅ 成功標準

### 技術標準
1. 所有測試通過 (單元 + 集成 + E2E)
2. 100 圈測試: 成功率 ≥ 95%, 學習效果可見
3. 200 圈測試: 性能穩定，無記憶體洩漏
4. 程式碼品質: 複雜度 < B, 覆蓋率 > 80%

### 業務標準
1. 學習功能立即可用
2. 向後相容，現有測試無需修改
3. 文檔完整，遷移路徑清晰
4. 維護成本降低 30%

### 時間標準
1. Week 1 完成核心架構
2. Week 2 完成 TestHarness 遷移
3. Week 3 完成整合測試
4. Week 4 完成部署和文檔

---

**總結**: 4 週完整重構，創建統一的 UnifiedLoop，整合所有優勢功能，提供清晰的遷移路徑。
