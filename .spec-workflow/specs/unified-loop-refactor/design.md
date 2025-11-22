# UnifiedLoop架構重構 - Design Document

## Overview

UnifiedLoop是整合AutonomousLoop和LearningLoop優勢的統一架構，採用**Composition over Inheritance**設計模式，以LearningLoop為基礎架構，透過組合TemplateIterationExecutor實現Template Mode和JSON Parameter Output功能，同時保留完整的Learning Feedback能力。

### 設計理念

1. **組合優於繼承**: UnifiedLoop是LearningLoop的薄包裝層（Facade），透過組合而非繼承實現功能整合
2. **策略模式**: IterationExecutor可在StandardIterationExecutor和TemplateIterationExecutor之間切換
3. **向後相容**: 提供與AutonomousLoop完全相同的API介面，確保現有測試腳本無縫遷移
4. **依賴注入**: 所有組件可透過配置注入，提高可測試性和擴展性
5. **單一責任**: 每個組件專注單一功能，複雜度<B(6.0)

### 核心優勢

| 特性 | AutonomousLoop | LearningLoop | UnifiedLoop |
|------|----------------|--------------|-------------|
| 程式碼行數 | 2,821 | 416 | ~600 (目標) |
| 平均複雜度 | B(7.7) | B(6.2) | <B(6.0) (目標) |
| 維護指數 | 0.00 | >60 | >60 (目標) |
| Template Mode | ✅ | ❌ | ✅ |
| JSON Parameter Output | ✅ | ❌ | ✅ |
| Learning Feedback | ❌ | ✅ | ✅ |
| 模組化設計 | ❌ | ✅ | ✅ |
| Protocol Validation | ❌ | ✅ | ✅ |

## Architecture

### 系統架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                      UnifiedLoop                            │
│  (Facade Pattern - 提供AutonomousLoop API相容介面)          │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │         LearningLoop (Core Orchestrator)         │      │
│  │  - 迭代循環管理                                  │      │
│  │  - 組件生命週期                                  │      │
│  │  - SIGINT處理                                    │      │
│  │  - 進度顯示                                      │      │
│  │  - 摘要報告                                      │      │
│  └──────────────────┬───────────────────────────────┘      │
│                     │                                        │
│         ┌───────────┴────────────┐                          │
│         ▼                        ▼                          │
│  ┌─────────────────┐    ┌──────────────────────┐          │
│  │  Standard       │    │  Template            │          │
│  │  Iteration      │◄───┤  Iteration           │          │
│  │  Executor       │    │  Executor            │          │
│  │                 │    │  (新增Template支援)  │          │
│  └────────┬────────┘    └──────────┬───────────┘          │
│           │                        │                        │
└───────────┼────────────────────────┼────────────────────────┘
            │                        │
            ▼                        ▼
┌───────────────────────────────────────────────────────────┐
│                  共享組件層                                │
├───────────────────────────────────────────────────────────┤
│  FeedbackGenerator  │  ChampionTracker  │  IterationHistory │
│  BacktestExecutor   │  MetricsExtractor │  LLMClient        │
│  TemplateParameterGenerator  │  TemplateCodeGenerator       │
│  DockerSandbox      │  MonitoringSystem │  AntiChurnManager │
└───────────────────────────────────────────────────────────┘
```

### 架構層次

#### Layer 1: UnifiedLoop (Facade層)
**責任**: 提供統一的API介面，向後相容AutonomousLoop
- 配置轉換: 將AutonomousLoop配置轉換為LearningConfig
- API適配: 提供與AutonomousLoop相同的方法簽名
- 模式選擇: 根據配置選擇IterationExecutor類型
- 行數目標: <200行（薄包裝層）

#### Layer 2: LearningLoop (Orchestrator層)
**責任**: 輕量級編排器，協調所有組件
- 組件初始化: 依賴順序初始化所有組件
- 迭代循環: 控制迭代流程和狀態
- 錯誤處理: 統一的異常處理和恢復
- 進度追蹤: 實時進度顯示和checkpoint
- 行數目標: <250行（保持現有）

#### Layer 3: IterationExecutor (Execution層)
**責任**: 執行單一迭代的10步流程

##### StandardIterationExecutor (現有)
- LLM策略生成（Freeform或Factor Graph）
- 回測執行
- 指標提取
- Champion更新

##### TemplateIterationExecutor (新增)
- Template Mode參數生成
- JSON Parameter Output模式
- 反饋整合到TemplateParameterGenerator
- Template-based code generation
- 行數目標: <400行

#### Layer 4: 共享組件層
所有組件已在Phase 1-6實現，無需修改：
- FeedbackGenerator: 自然語言反饋生成
- ChampionTracker: Champion策略追蹤
- IterationHistory: 迭代記錄管理
- BacktestExecutor: 回測執行
- TemplateParameterGenerator: Template參數生成
- TemplateCodeGenerator: Template程式碼生成
- DockerSandbox: 安全執行環境
- MonitoringSystem: 監控和指標收集

## Components and Interfaces

### 1. UnifiedLoop (Facade)

```python
class UnifiedLoop:
    """統一的Loop實作，整合Template Mode和Learning Feedback。

    採用Facade Pattern，內部委派給LearningLoop，提供AutonomousLoop相容API。

    Attributes:
        learning_loop: 底層LearningLoop實例
        config: UnifiedConfig配置
        template_mode: 是否啟用Template Mode
        use_json_mode: 是否啟用JSON Parameter Output
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        max_iterations: int = 10,
        template_mode: bool = False,
        template_name: str = "Momentum",
        use_json_mode: bool = False,
        enable_learning: bool = True,
        history_file: str = "iteration_history.json",
        config_file: str = "strategy_config.yaml",
        **kwargs
    ):
        """初始化UnifiedLoop。

        Args:
            model: LLM模型名稱
            max_iterations: 最大迭代次數
            template_mode: 啟用Template Mode
            template_name: Template名稱（Template Mode時使用）
            use_json_mode: 啟用JSON Parameter Output
            enable_learning: 啟用Learning Feedback
            history_file: 迭代歷史檔案路徑
            config_file: 配置檔案路徑
            **kwargs: 其他配置參數
        """
        # 建構LearningConfig
        self.config = self._build_learning_config(
            model=model,
            max_iterations=max_iterations,
            template_mode=template_mode,
            template_name=template_name,
            use_json_mode=use_json_mode,
            enable_learning=enable_learning,
            history_file=history_file,
            config_file=config_file,
            **kwargs
        )

        # 初始化LearningLoop
        self.learning_loop = LearningLoop(config=self.config)

        # 如果是Template Mode，替換IterationExecutor為TemplateIterationExecutor
        if template_mode:
            self._inject_template_executor()

    def _build_learning_config(self, **kwargs) -> LearningConfig:
        """將UnifiedLoop配置轉換為LearningConfig。"""
        # 配置轉換邏輯
        pass

    def _inject_template_executor(self):
        """注入TemplateIterationExecutor替換StandardIterationExecutor。"""
        # 建立TemplateIterationExecutor
        template_executor = TemplateIterationExecutor(
            llm_client=self.learning_loop.llm_client,
            feedback_generator=self.learning_loop.feedback_generator,
            backtest_executor=self.learning_loop.backtest_executor,
            champion_tracker=self.learning_loop.champion_tracker,
            history=self.learning_loop.history,
            template_name=self.config.template_name,
            use_json_mode=self.config.use_json_mode,
            config=self.config.to_dict()
        )

        # 替換executor
        self.learning_loop.iteration_executor = template_executor

    def run(self) -> Dict[str, Any]:
        """執行迭代循環（委派給LearningLoop）。

        Returns:
            包含執行結果的字典
        """
        return self.learning_loop.run()

    @property
    def champion(self):
        """向後相容: 訪問champion屬性。"""
        return self.learning_loop.champion_tracker.champion

    @property
    def history(self):
        """向後相容: 訪問history屬性。"""
        return self.learning_loop.history
```

### 2. TemplateIterationExecutor

```python
class TemplateIterationExecutor(IterationExecutor):
    """支援Template Mode的Iteration Executor。

    整合TemplateParameterGenerator和FeedbackGenerator，實現Template-based
    參數生成和學習反饋循環。

    10步流程:
    1. 載入近期歷史
    2. 生成反饋（如果啟用學習且不是第一次迭代）
    3. Template模式決策（不需要LLM vs Factor Graph選擇）
    4. 生成參數（透過TemplateParameterGenerator，傳入反饋）
    5. 生成策略程式碼（透過TemplateCodeGenerator）
    6. 執行策略（透過BacktestExecutor）
    7. 提取指標（透過MetricsExtractor）
    8. 分類成功（透過SuccessClassifier）
    9. 更新Champion（如果更好）
    10. 建立IterationRecord並返回

    Attributes:
        template_param_generator: Template參數生成器
        template_code_generator: Template程式碼生成器
        use_json_mode: 是否使用JSON Parameter Output模式
    """

    def __init__(
        self,
        llm_client: LLMClient,
        feedback_generator: FeedbackGenerator,
        backtest_executor: BacktestExecutor,
        champion_tracker: ChampionTracker,
        history: IterationHistory,
        template_name: str,
        use_json_mode: bool,
        config: Dict[str, Any],
        **kwargs
    ):
        """初始化TemplateIterationExecutor。

        Args:
            llm_client: LLM客戶端
            feedback_generator: 反饋生成器
            backtest_executor: 回測執行器
            champion_tracker: Champion追蹤器
            history: 迭代歷史
            template_name: Template名稱
            use_json_mode: 是否使用JSON模式
            config: 配置字典
            **kwargs: 其他參數
        """
        # 初始化父類
        super().__init__(
            llm_client=llm_client,
            feedback_generator=feedback_generator,
            backtest_executor=backtest_executor,
            champion_tracker=champion_tracker,
            history=history,
            config=config,
            **kwargs
        )

        # Template特有組件
        self.template_name = template_name
        self.use_json_mode = use_json_mode

        # 初始化TemplateParameterGenerator
        self.template_param_generator = TemplateParameterGenerator(
            template_name=template_name,
            model=llm_client.model,
            use_json_mode=use_json_mode
        )

        # 初始化TemplateCodeGenerator
        from src.templates.momentum_template import MomentumTemplate
        template = MomentumTemplate()  # TODO: 根據template_name動態選擇
        self.template_code_generator = TemplateCodeGenerator(template)

        logger.info(f"TemplateIterationExecutor initialized: {template_name}, JSON mode: {use_json_mode}")

    def execute(self, iteration_num: int, **kwargs) -> IterationRecord:
        """執行單一迭代的10步流程（Template Mode版本）。

        Args:
            iteration_num: 迭代次數
            **kwargs: 其他參數

        Returns:
            IterationRecord: 迭代記錄
        """
        logger.info(f"=== Iteration {iteration_num} (Template Mode) ===")

        # Step 1: 載入近期歷史
        recent_history = self.history.get_recent(window=self.config.get("history_window", 10))

        # Step 2: 生成反饋（如果啟用且不是第一次）
        feedback = None
        if self.feedback_generator and iteration_num > 0:
            last_record = recent_history[-1] if recent_history else None
            if last_record:
                feedback = self.feedback_generator.generate_feedback(
                    iteration_num=iteration_num,
                    metrics=last_record.metrics,
                    execution_result=last_record.execution_result,
                    classification_level=last_record.classification_level,
                    error_msg=last_record.error_msg
                )
                logger.info(f"Generated feedback: {feedback[:100]}...")

        # Step 3-4: 生成參數（傳入反饋）
        try:
            if self.use_json_mode:
                # JSON Parameter Output模式
                params, generation_details = self.template_param_generator.generate_parameters_json_mode(
                    iteration_num=iteration_num,
                    champion_params=self.champion_tracker.champion.params if self.champion_tracker.champion else None,
                    champion_sharpe=self.champion_tracker.champion.metrics.get("sharpe_ratio") if self.champion_tracker.champion else None,
                    performance_feedback=feedback
                )
            else:
                # 標準Template模式
                params = self.template_param_generator.generate_parameters(
                    iteration_num=iteration_num,
                    champion_params=self.champion_tracker.champion.params if self.champion_tracker.champion else None,
                    champion_sharpe=self.champion_tracker.champion.metrics.get("sharpe_ratio") if self.champion_tracker.champion else None,
                    feedback_history=feedback
                )
                generation_details = None

            logger.info(f"Generated parameters: {params}")

        except Exception as e:
            logger.error(f"Parameter generation failed: {e}")
            return self._create_error_record(iteration_num, f"Parameter generation error: {e}")

        # Step 5: 生成策略程式碼
        try:
            code_result = self.template_code_generator.generate_code(params)
            strategy_code = code_result.code
            logger.info("Strategy code generated")

        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return self._create_error_record(iteration_num, f"Code generation error: {e}")

        # Step 6-10: 執行、提取、分類、更新、返回（與StandardIterationExecutor相同）
        # ... (後續流程與父類相同)

    def _create_error_record(self, iteration_num: int, error_msg: str) -> IterationRecord:
        """建立錯誤記錄。"""
        return IterationRecord(
            iteration_num=iteration_num,
            timestamp=datetime.now().isoformat(),
            code="",
            params={},
            metrics=None,
            execution_result={"status": "error"},
            classification_level=None,
            error_msg=error_msg,
            champion_updated=False
        )
```

### 3. 配置系統整合

```python
@dataclass
class UnifiedConfig:
    """UnifiedLoop統一配置。

    整合AutonomousLoop和LearningLoop配置參數。
    """
    # LearningLoop參數
    model: str = "gemini-2.5-flash"
    max_iterations: int = 10
    history_file: str = "iteration_history.json"
    config_file: str = "strategy_config.yaml"

    # Template Mode參數
    template_mode: bool = False
    template_name: str = "Momentum"

    # JSON Parameter Output參數
    use_json_mode: bool = False

    # Learning Feedback參數
    enable_learning: bool = True
    history_window: int = 10

    # Monitoring參數
    enable_monitoring: bool = True

    # Docker Sandbox參數
    use_docker: bool = True

    def to_learning_config(self) -> LearningConfig:
        """轉換為LearningConfig。"""
        return LearningConfig(
            model=self.model,
            max_iterations=self.max_iterations,
            history_file=self.history_file,
            config_file=self.config_file,
            # 傳遞Template相關配置
            template_mode=self.template_mode,
            template_name=self.template_name,
            use_json_mode=self.use_json_mode,
            enable_learning=self.enable_learning,
            history_window=self.history_window
        )
```

## Data Models

### IterationRecord (現有，無需修改)

```python
@dataclass
class IterationRecord:
    """單一迭代的完整記錄。"""
    iteration_num: int
    timestamp: str
    code: str
    params: Dict[str, Any]
    metrics: Optional[StrategyMetrics]
    execution_result: Dict[str, Any]
    classification_level: Optional[str]
    error_msg: Optional[str]
    champion_updated: bool
    generation_method: str = "template"  # 新增: "template", "freeform", "factor_graph"
    template_name: Optional[str] = None  # 新增: Template名稱
    json_mode: bool = False  # 新增: 是否使用JSON模式
```

### ChampionRecord (現有，無需修改)

```python
@dataclass
class ChampionRecord:
    """Champion策略記錄。"""
    iteration_num: int
    code: str
    params: Dict[str, Any]
    metrics: Dict[str, float]
    timestamp: str
    template_name: Optional[str] = None  # 新增: 如果是Template生成
```

### FeedbackContext (現有，擴展)

```python
@dataclass
class FeedbackContext:
    """反饋生成的上下文資訊。"""
    iteration_num: int
    recent_history: List[IterationRecord]
    champion: Optional[ChampionRecord]
    current_metrics: Optional[StrategyMetrics]
    error_msg: Optional[str]
    template_mode: bool = False  # 新增: 是否為Template模式
    json_mode: bool = False  # 新增: 是否為JSON模式
```

## Error Handling

### 錯誤層次架構

```
Level 1: UnifiedLoop層錯誤
├── ConfigurationError: 配置錯誤
│   ├── 不相容的配置組合（如template_mode=True但無template_name）
│   └── 缺少必要配置參數
└── InitializationError: 初始化錯誤
    ├── LearningLoop初始化失敗
    └── TemplateIterationExecutor注入失敗

Level 2: LearningLoop層錯誤（現有，保持不變）
├── ComponentInitializationError: 組件初始化錯誤
├── InterruptionError: SIGINT中斷
└── ExecutionError: 執行錯誤

Level 3: IterationExecutor層錯誤
├── ParameterGenerationError: 參數生成錯誤
│   ├── LLM API錯誤
│   ├── JSON解析錯誤
│   └── Pydantic驗證錯誤
├── CodeGenerationError: 程式碼生成錯誤
│   ├── Template渲染錯誤
│   └── AST驗證錯誤
├── BacktestExecutionError: 回測執行錯誤（現有）
└── MetricsExtractionError: 指標提取錯誤（現有）
```

### 錯誤處理策略

#### 1. 配置驗證（啟動時）

```python
def validate_config(config: UnifiedConfig) -> None:
    """驗證配置合理性。

    Raises:
        ConfigurationError: 配置不合理時
    """
    # Template Mode驗證
    if config.template_mode and not config.template_name:
        raise ConfigurationError("template_mode=True requires template_name")

    # JSON Mode只在Template Mode下有效
    if config.use_json_mode and not config.template_mode:
        raise ConfigurationError("use_json_mode=True requires template_mode=True")

    # 檔案路徑驗證
    if not config.history_file:
        raise ConfigurationError("history_file is required")
```

#### 2. 運行時錯誤恢復

```python
class TemplateIterationExecutor:
    def execute(self, iteration_num: int, **kwargs) -> IterationRecord:
        """執行單一迭代，帶有完整錯誤處理。"""
        try:
            # Step 2: 反饋生成（可選，失敗不中斷）
            feedback = self._generate_feedback_safe(iteration_num)

            # Step 3-4: 參數生成（關鍵步驟，失敗則記錄並返回）
            try:
                params = self._generate_parameters(iteration_num, feedback)
            except (LLMError, ValidationError) as e:
                logger.error(f"Parameter generation failed: {e}")
                return self._create_error_record(iteration_num, str(e))

            # Step 5: 程式碼生成（關鍵步驟）
            try:
                code = self._generate_code(params)
            except CodeGenerationError as e:
                logger.error(f"Code generation failed: {e}")
                return self._create_error_record(iteration_num, str(e))

            # Step 6-10: 執行、提取、分類、更新、返回
            # ... (使用父類方法，已有完整錯誤處理)

        except Exception as e:
            # 未預期錯誤: 記錄完整stack trace並返回
            logger.exception(f"Unexpected error in iteration {iteration_num}")
            return self._create_error_record(iteration_num, f"Unexpected error: {e}")

    def _generate_feedback_safe(self, iteration_num: int) -> Optional[str]:
        """安全生成反饋（失敗不中斷）。"""
        try:
            if self.feedback_generator and iteration_num > 0:
                return self.feedback_generator.generate_feedback(...)
        except Exception as e:
            logger.warning(f"Feedback generation failed, continuing without feedback: {e}")
        return None
```

#### 3. 錯誤分類和報告

```python
class ErrorReporter:
    """統一的錯誤報告器。"""

    @staticmethod
    def categorize_error(error: Exception) -> str:
        """分類錯誤為可操作的類別。"""
        if isinstance(error, LLMError):
            return "LLM_API_ERROR"
        elif isinstance(error, ValidationError):
            return "VALIDATION_ERROR"
        elif isinstance(error, CodeGenerationError):
            return "CODE_GENERATION_ERROR"
        # ...
        else:
            return "UNKNOWN_ERROR"

    @staticmethod
    def generate_error_report(iteration_num: int, error: Exception) -> Dict[str, Any]:
        """生成詳細錯誤報告。"""
        return {
            "iteration_num": iteration_num,
            "error_category": ErrorReporter.categorize_error(error),
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "stack_trace": traceback.format_exc()
        }
```

## Testing Strategy

### 測試金字塔

```
                    ┌─────────────────┐
                    │  E2E Tests      │  5%
                    │  (100圈測試)    │
                    └─────────────────┘
                ┌──────────────────────────┐
                │  Integration Tests       │  15%
                │  (組件整合測試)         │
                └──────────────────────────┘
            ┌──────────────────────────────────┐
            │  Unit Tests                      │  80%
            │  (組件單元測試)                  │
            └──────────────────────────────────┘
```

### 單元測試 (80%覆蓋率)

#### 1. UnifiedLoop測試

```python
# tests/unit/test_unified_loop.py

class TestUnifiedLoop:
    """UnifiedLoop單元測試。"""

    def test_initialization_standard_mode(self):
        """測試標準模式初始化。"""
        loop = UnifiedLoop(
            model="gemini-2.5-flash",
            max_iterations=10,
            template_mode=False
        )
        assert isinstance(loop.learning_loop, LearningLoop)
        assert isinstance(loop.learning_loop.iteration_executor, StandardIterationExecutor)

    def test_initialization_template_mode(self):
        """測試Template模式初始化。"""
        loop = UnifiedLoop(
            model="gemini-2.5-flash",
            max_iterations=10,
            template_mode=True,
            template_name="Momentum"
        )
        assert isinstance(loop.learning_loop.iteration_executor, TemplateIterationExecutor)

    def test_config_validation_template_name_required(self):
        """測試Template模式需要template_name。"""
        with pytest.raises(ConfigurationError):
            UnifiedLoop(template_mode=True)  # 缺少template_name

    def test_backward_compatibility_api(self):
        """測試向後相容API。"""
        loop = UnifiedLoop(max_iterations=10)

        # 驗證AutonomousLoop API存在
        assert hasattr(loop, "run")
        assert hasattr(loop, "champion")
        assert hasattr(loop, "history")
```

#### 2. TemplateIterationExecutor測試

```python
# tests/unit/test_template_iteration_executor.py

class TestTemplateIterationExecutor:
    """TemplateIterationExecutor單元測試。"""

    @pytest.fixture
    def executor(self, mock_components):
        """建立測試用executor。"""
        return TemplateIterationExecutor(
            llm_client=mock_components["llm_client"],
            feedback_generator=mock_components["feedback_generator"],
            backtest_executor=mock_components["backtest_executor"],
            champion_tracker=mock_components["champion_tracker"],
            history=mock_components["history"],
            template_name="Momentum",
            use_json_mode=False,
            config={}
        )

    def test_execute_first_iteration_no_feedback(self, executor):
        """測試第一次迭代不生成反饋。"""
        record = executor.execute(iteration_num=0)
        # 驗證沒有調用feedback_generator
        executor.feedback_generator.generate_feedback.assert_not_called()

    def test_execute_with_feedback(self, executor):
        """測試第二次迭代生成並使用反饋。"""
        # 設置mock history
        executor.history.get_recent.return_value = [mock_iteration_record]

        record = executor.execute(iteration_num=1)

        # 驗證調用了feedback_generator
        executor.feedback_generator.generate_feedback.assert_called_once()

        # 驗證反饋傳遞給parameter generator
        # ...

    def test_parameter_generation_error_handling(self, executor):
        """測試參數生成錯誤處理。"""
        # Mock參數生成失敗
        executor.template_param_generator.generate_parameters.side_effect = ValidationError("Invalid params")

        record = executor.execute(iteration_num=0)

        # 驗證返回錯誤記錄
        assert record.execution_result["status"] == "error"
        assert "Invalid params" in record.error_msg
```

### 整合測試 (15%)

#### 1. UnifiedLoop與組件整合

```python
# tests/integration/test_unified_loop_integration.py

class TestUnifiedLoopIntegration:
    """UnifiedLoop整合測試。"""

    @pytest.mark.integration
    def test_template_mode_with_real_components(self, tmp_path):
        """測試Template模式與真實組件整合。"""
        # 使用真實組件（不是mock）
        loop = UnifiedLoop(
            model="gemini-2.5-flash",
            max_iterations=5,
            template_mode=True,
            template_name="Momentum",
            use_json_mode=True,
            history_file=str(tmp_path / "history.json")
        )

        # 執行少量迭代
        result = loop.run()

        # 驗證結果
        assert result["iterations_completed"] >= 1
        assert len(loop.history.load()) >= 1

    @pytest.mark.integration
    def test_feedback_integration(self, tmp_path):
        """測試反饋整合。"""
        loop = UnifiedLoop(
            max_iterations=3,
            template_mode=True,
            template_name="Momentum",
            enable_learning=True,
            history_file=str(tmp_path / "history.json")
        )

        result = loop.run()

        # 驗證第2次迭代有使用反饋
        history = loop.history.load()
        if len(history) >= 2:
            # 檢查parameter generator是否收到反饋
            # ...
```

#### 2. 向後相容性測試

```python
# tests/integration/test_backward_compatibility.py

class TestBackwardCompatibility:
    """向後相容性測試。"""

    @pytest.mark.integration
    def test_extended_test_harness_compatibility(self):
        """測試ExtendedTestHarness可直接使用UnifiedLoop。"""
        from tests.integration.extended_test_harness import ExtendedTestHarness

        # 創建harness，使用UnifiedLoop替換AutonomousLoop
        harness = ExtendedTestHarness(
            loop_class=UnifiedLoop,  # 替換原本的AutonomousLoop
            max_iterations=10,
            checkpoint_interval=5
        )

        # 執行測試
        result = harness.run_test()

        # 驗證所有功能正常
        assert result["success_rate"] > 0
        assert "checkpoints" in result
```

### E2E測試 (5%)

#### 1. 100圈長期測試

```python
# tests/e2e/test_100iteration_unified.py

@pytest.mark.e2e
@pytest.mark.slow
def test_100_iteration_template_json_mode(tmp_path):
    """100圈Template + JSON模式E2E測試。"""
    loop = UnifiedLoop(
        model="gemini-2.5-flash",
        max_iterations=100,
        template_mode=True,
        template_name="Momentum",
        use_json_mode=True,
        enable_learning=True,
        history_file=str(tmp_path / "history.json")
    )

    result = loop.run()

    # 驗收標準
    assert result["iterations_completed"] >= 95  # ≥95%成功率
    assert result.get("champion") is not None

    # 學習效果驗證
    history = loop.history.load()
    champion_updates = sum(1 for r in history if r.champion_updated)
    champion_update_rate = champion_updates / len(history)
    assert champion_update_rate > 0.05  # >5%更新率
```

#### 2. 對比測試（vs AutonomousLoop）

```python
# tests/e2e/test_comparison_autonomous_vs_unified.py

@pytest.mark.e2e
@pytest.mark.slow
def test_performance_comparison(tmp_path):
    """UnifiedLoop vs AutonomousLoop性能對比測試。"""
    iterations = 50

    # AutonomousLoop baseline
    autonomous_result = run_autonomous_loop(
        max_iterations=iterations,
        template_mode=True,
        use_json_mode=True
    )

    # UnifiedLoop
    unified_result = run_unified_loop(
        max_iterations=iterations,
        template_mode=True,
        use_json_mode=True
    )

    # 性能對比
    assert unified_result["execution_time"] <= autonomous_result["execution_time"] * 1.1  # ≤110%
    assert unified_result["success_rate"] >= autonomous_result["success_rate"] * 0.95  # ≥95%

    # 學習效果對比（UnifiedLoop應該更好，因為有FeedbackGenerator）
    assert unified_result["champion_update_rate"] > autonomous_result["champion_update_rate"]
```

### 測試工具

#### UnifiedTestHarness

```python
# tests/integration/unified_test_harness.py

class UnifiedTestHarness:
    """UnifiedLoop測試框架（替換ExtendedTestHarness）。

    提供與ExtendedTestHarness完全相同的API，內部使用UnifiedLoop。
    """

    def __init__(
        self,
        max_iterations: int = 100,
        template_mode: bool = True,
        use_json_mode: bool = True,
        checkpoint_interval: int = 10,
        **kwargs
    ):
        """初始化測試框架。"""
        self.config = {
            "max_iterations": max_iterations,
            "template_mode": template_mode,
            "use_json_mode": use_json_mode,
            **kwargs
        }
        self.checkpoint_interval = checkpoint_interval
        self.checkpoints = []

    def run_test(self) -> Dict[str, Any]:
        """執行測試並返回結果。"""
        loop = UnifiedLoop(**self.config)

        # 執行
        result = loop.run()

        # 統計分析
        statistics = self._generate_statistics(loop.history.load())

        return {
            **result,
            "statistics": statistics,
            "checkpoints": self.checkpoints
        }

    def _generate_statistics(self, history: List[IterationRecord]) -> Dict[str, Any]:
        """生成統計分析。"""
        return {
            "success_rate": len([r for r in history if r.metrics]) / len(history),
            "champion_update_rate": len([r for r in history if r.champion_updated]) / len(history),
            "avg_sharpe": np.mean([r.metrics["sharpe_ratio"] for r in history if r.metrics]),
            "cohens_d": self._calculate_cohens_d(history)
        }
```

### 測試執行策略

```bash
# 快速測試（開發時）
pytest tests/unit -v --cov=src/learning --cov-report=html

# 整合測試
pytest tests/integration -v -m "not slow"

# 完整測試（CI/CD）
pytest tests/ -v --cov=src --cov-report=xml

# E2E測試（手動或nightly）
pytest tests/e2e -v -m e2e --timeout=7200
```

## 遷移路徑

### Phase 1: UnifiedLoop核心實作（Week 1）

**目標**: 建立UnifiedLoop和TemplateIterationExecutor核心架構

**任務**:
1. 建立`src/learning/unified_loop.py`
2. 建立`src/learning/template_iteration_executor.py`
3. 建立`src/learning/unified_config.py`
4. 單元測試覆蓋率>80%

**驗收**:
- UnifiedLoop可初始化
- Template Mode可正常運作
- JSON Parameter Output可正常運作
- 所有單元測試通過

### Phase 2: 測試框架遷移（Week 2）

**目標**: 建立UnifiedTestHarness並驗證100圈測試

**任務**:
1. 建立`tests/integration/unified_test_harness.py`
2. 遷移`run_100iteration_test.py`使用UnifiedLoop
3. 執行100圈對比測試（UnifiedLoop vs AutonomousLoop）
4. 驗證功能等價性

**驗收**:
- UnifiedTestHarness API與ExtendedTestHarness相容
- 100圈測試成功率≥95%
- 性能≤AutonomousLoop * 1.1

### Phase 3: 整合Monitoring和Sandbox（Week 3）

**目標**: 整合完整的監控和沙箱系統

**任務**:
1. 整合MetricsCollector到UnifiedLoop
2. 整合ResourceMonitor
3. 整合DiversityMonitor
4. 整合DockerExecutor
5. 執行200圈穩定性測試

**驗收**:
- 所有監控指標正常收集
- Docker sandbox正常運作
- 200圈測試無crash，無記憶體洩漏

### Phase 4: 測試遷移和Deprecation（Week 4）

**目標**: 遷移所有測試腳本並標記AutonomousLoop為廢棄

**任務**:
1. 更新所有run_*.py腳本配置（添加loop_class選項）
2. 在AutonomousLoop添加@deprecated標記
3. 建立遷移指南文檔
4. 建立API Reference文檔

**驗收**:
- 所有測試腳本可透過配置切換UnifiedLoop
- 遷移指南完整
- API文檔完整
- AutonomousLoop標記為deprecated

## 效能考量

### 目標指標

| 指標 | 目標值 | 測量方法 |
|------|--------|----------|
| 執行時間 | ≤AutonomousLoop * 1.1 | 100圈對比測試 |
| 記憶體使用 | ≤1GB (100圈) | ResourceMonitor |
| 啟動時間 | <2秒 | time.time()測量 |
| 單次迭代 | <30秒（不含LLM API） | per-iteration profiling |

### 效能優化策略

1. **延遲初始化**: 組件按需初始化
2. **快取機制**: LLM prompt快取，Template程式碼快取
3. **並行處理**: 獨立組件的初始化並行化
4. **記憶體管理**: 定期清理迭代歷史舊記錄

## 風險評估

### 高風險項目

1. **API不相容** (機率: 40%, 影響: 高)
   - **緩解**: 完整的向後相容性測試套件
   - **備用方案**: 提供adapter層進行API轉換

2. **性能下降** (機率: 20%, 影響: 中)
   - **緩解**: 性能基準測試，profiling分析
   - **備用方案**: 效能優化Sprint

### 中風險項目

3. **學習效果不佳** (機率: 30%, 影響: 低)
   - **緩解**: A/B測試，調整FeedbackGenerator策略
   - **備用方案**: 參數調優

4. **遷移時間超出預期** (機率: 40%, 影響: 中)
   - **緩解**: 漸進式遷移，保留AutonomousLoop作為fallback
   - **備用方案**: 延長Phase 4時程
