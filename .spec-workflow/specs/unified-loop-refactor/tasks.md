# UnifiedLoop架構重構 - Task List

## Implementation Tasks

### Week 1: UnifiedLoop核心實作

#### Phase 1.1: 基礎架構設置

- [ ] **1.1. 建立UnifiedLoop核心檔案**
    - [ ] 1.1.1. 建立`src/learning/unified_loop.py`
        - *Goal*: 建立UnifiedLoop類別，作為LearningLoop的Facade
        - *Details*:
            - 實作`__init__`方法，接受AutonomousLoop相容參數
            - 實作`_build_learning_config`配置轉換方法
            - 實作`_inject_template_executor`注入機制
            - 實作`run()`方法委派給LearningLoop
            - 實作`champion`和`history`屬性（向後相容）
        - *Requirements*: Requirements#1 (統一的Loop架構), #4 (向後相容性)
        - *Target*: <200行程式碼

    - [ ] 1.1.2. 建立`src/learning/unified_config.py`
        - *Goal*: 定義UnifiedConfig配置類別
        - *Details*:
            - 使用@dataclass定義配置結構
            - 包含所有AutonomousLoop和LearningLoop參數
            - 實作`to_learning_config()`轉換方法
            - 添加配置驗證邏輯
        - *Requirements*: Requirements#1, #4
        - *Target*: <100行程式碼

- [ ] **1.2. 建立TemplateIterationExecutor**
    - [ ] 1.2.1. 建立`src/learning/template_iteration_executor.py`
        - *Goal*: 實作支援Template Mode的IterationExecutor
        - *Details*:
            - 繼承`IterationExecutor`
            - 實作`__init__`，初始化TemplateParameterGenerator和TemplateCodeGenerator
            - 實作`execute()`方法的10步流程
            - 整合FeedbackGenerator到參數生成流程
            - 支援JSON Parameter Output模式
        - *Requirements*: Requirements#1, #2, #3
        - *Target*: <400行程式碼

    - [ ] 1.2.2. 擴展IterationRecord數據模型
        - *Goal*: 添加Template Mode相關欄位
        - *Details*:
            - 在`src/learning/iteration_history.py`的IterationRecord添加：
                - `generation_method: str = "template"`
                - `template_name: Optional[str] = None`
                - `json_mode: bool = False`
            - 更新序列化/反序列化邏輯
        - *Requirements*: Requirements#1
        - *Target*: <20行修改

- [ ] **1.3. 配置驗證和錯誤處理**
    - [ ] 1.3.1. 實作配置驗證函數
        - *Goal*: 啟動時驗證配置合理性
        - *Details*:
            - 在`unified_loop.py`添加`validate_config()`函數
            - 驗證規則：
                - template_mode=True 需要 template_name
                - use_json_mode=True 需要 template_mode=True
                - 必要檔案路徑存在
            - 拋出`ConfigurationError`
        - *Requirements*: Requirements#4, Non-functional#錯誤處理
        - *Target*: <50行程式碼

    - [ ] 1.3.2. 實作TemplateIterationExecutor錯誤處理
        - *Goal*: 完整的執行時錯誤處理和恢復
        - *Details*:
            - `_generate_feedback_safe()`: 失敗不中斷
            - 參數生成錯誤: 捕獲LLMError, ValidationError
            - 程式碼生成錯誤: 捕獲CodeGenerationError
            - `_create_error_record()`: 建立錯誤記錄
            - 所有未預期錯誤: 記錄stack trace
        - *Requirements*: Non-functional#可靠性, #錯誤處理
        - *Target*: 設計文檔Error Handling章節

- [ ] **1.4. 單元測試（目標覆蓋率>80%）**
    - [ ] 1.4.1. UnifiedLoop單元測試
        - *Goal*: 完整測試UnifiedLoop功能
        - *Details*:
            - 建立`tests/unit/test_unified_loop.py`
            - 測試案例：
                - `test_initialization_standard_mode()`: 標準模式初始化
                - `test_initialization_template_mode()`: Template模式初始化
                - `test_config_validation_template_name_required()`: 配置驗證
                - `test_backward_compatibility_api()`: API相容性
                - `test_inject_template_executor()`: Executor注入
            - 使用mock組件進行隔離測試
        - *Requirements*: Acceptance#單元測試覆蓋率>80%
        - *Target*: >10個測試案例

    - [ ] 1.4.2. TemplateIterationExecutor單元測試
        - *Goal*: 測試Template執行邏輯
        - *Details*:
            - 建立`tests/unit/test_template_iteration_executor.py`
            - 測試案例：
                - `test_execute_first_iteration_no_feedback()`: 第一次迭代無反饋
                - `test_execute_with_feedback()`: 第二次迭代有反饋
                - `test_parameter_generation_error_handling()`: 參數錯誤處理
                - `test_code_generation_error_handling()`: 程式碼錯誤處理
                - `test_json_mode_parameter_generation()`: JSON模式
                - `test_feedback_integration()`: 反饋整合
            - Mock所有外部依賴
        - *Requirements*: Acceptance#單元測試覆蓋率>80%
        - *Target*: >15個測試案例

    - [ ] 1.4.3. UnifiedConfig單元測試
        - *Goal*: 測試配置轉換和驗證
        - *Details*:
            - 建立`tests/unit/test_unified_config.py`
            - 測試案例：
                - `test_to_learning_config_conversion()`: 配置轉換
                - `test_config_validation_success()`: 有效配置
                - `test_config_validation_failures()`: 無效配置
                - `test_default_values()`: 預設值
        - *Requirements*: Acceptance#單元測試覆蓋率>80%
        - *Target*: >8個測試案例

- [ ] **1.5. 驗收檢查點（Week 1結束）**
    - [ ] 1.5.1. 功能驗證
        - *Checklist*:
            - ✅ UnifiedLoop可初始化（標準模式和Template模式）
            - ✅ TemplateIterationExecutor可執行單一迭代
            - ✅ FeedbackGenerator整合正常運作
            - ✅ JSON Parameter Output模式正常運作
            - ✅ 配置驗證正確攔截無效配置

    - [ ] 1.5.2. 測試驗證
        - *Checklist*:
            - ✅ 所有單元測試通過
            - ✅ 測試覆蓋率>80%
            - ✅ 無mypy類型錯誤
            - ✅ 無pylint警告（重要性≥WARNING）

    - [ ] 1.5.3. 程式碼品質驗證
        - *Checklist*:
            - ✅ UnifiedLoop複雜度<B(6.0)
            - ✅ TemplateIterationExecutor複雜度<B(8.0)
            - ✅ 無God Method（單一方法<50行，複雜度<10）
            - ✅ 所有公開API有docstring

---

### Week 2: 測試框架遷移

#### Phase 2.1: UnifiedTestHarness建立

- [ ] **2.1. 建立UnifiedTestHarness**
    - [ ] 2.1.1. 建立`tests/integration/unified_test_harness.py`
        - *Goal*: 提供與ExtendedTestHarness相容的API
        - *Details*:
            - 實作`__init__`：接受與ExtendedTestHarness相同參數
            - 實作`run_test()`：執行UnifiedLoop並返回結果
            - 實作`_generate_statistics()`：統計分析（成功率、更新率、Sharpe、Cohen's d）
            - 實作checkpoint機制（每N次迭代保存）
            - 實作resume機制（從checkpoint恢復）
        - *Requirements*: Requirements#5 (測試基礎設施升級)
        - *Target*: <300行程式碼

    - [ ] 2.1.2. 統計分析功能
        - *Goal*: 完整的統計分析和報告
        - *Details*:
            - 成功率計算
            - Champion更新率計算
            - 平均Sharpe ratio計算
            - Cohen's d效果量計算
            - 統計顯著性檢驗（t-test）
            - 生成HTML報告（可選）
        - *Requirements*: Acceptance#學習效果指標
        - *Target*: <200行程式碼

- [ ] **2.2. 遷移測試腳本**
    - [ ] 2.2.1. 更新`run_100iteration_test.py`
        - *Goal*: 支援UnifiedLoop和AutonomousLoop切換
        - *Details*:
            - 添加`--loop-type`參數（autonomous, unified）
            - 根據loop-type選擇相應的Loop類別
            - 保持現有的參數介面不變
            - 添加`--template-mode`和`--use-json-mode`參數
        - *Requirements*: Requirements#4 (向後相容性)
        - *Target*: <50行修改

    - [ ] 2.2.2. 建立`run_100iteration_unified_test.py`
        - *Goal*: UnifiedLoop專用的100圈測試腳本
        - *Details*:
            - 使用UnifiedTestHarness
            - 配置Template Mode + JSON Mode
            - 啟用Learning Feedback
            - 自動統計分析和報告生成
        - *Requirements*: Requirements#5
        - *Target*: <200行程式碼

- [ ] **2.3. 整合測試**
    - [ ] 2.3.1. UnifiedLoop組件整合測試
        - *Goal*: 驗證UnifiedLoop與真實組件的整合
        - *Details*:
            - 建立`tests/integration/test_unified_loop_integration.py`
            - 測試案例：
                - `test_template_mode_with_real_components()`: Template模式5圈測試
                - `test_json_mode_with_real_components()`: JSON模式5圈測試
                - `test_feedback_integration()`: 反饋整合測試
                - `test_champion_update_logic()`: Champion更新邏輯
            - 使用真實組件（不是mock）
            - 使用臨時檔案路徑
        - *Requirements*: Acceptance#10圈集成測試100%通過
        - *Target*: >10個測試案例

    - [ ] 2.3.2. 向後相容性測試
        - *Goal*: 驗證ExtendedTestHarness可使用UnifiedLoop
        - *Details*:
            - 建立`tests/integration/test_backward_compatibility.py`
            - 測試案例：
                - `test_extended_test_harness_with_unified_loop()`: ExtendedTestHarness相容性
                - `test_api_compatibility()`: API介面相容性
                - `test_file_format_compatibility()`: 檔案格式相容性
                - `test_config_compatibility()`: 配置參數相容性
            - 確保無需修改ExtendedTestHarness
        - *Requirements*: Requirements#4, Acceptance#向後相容性
        - *Target*: >8個測試案例

- [ ] **2.4. 100圈對比測試**
    - [ ] 2.4.1. 執行AutonomousLoop 100圈基準測試
        - *Goal*: 建立AutonomousLoop性能基準
        - *Details*:
            - 執行`run_100iteration_test.py --loop-type autonomous`
            - 記錄性能指標：
                - 總執行時間
                - 成功率
                - Champion更新率
                - 平均Sharpe ratio
            - 保存結果到`baseline_autonomous_100iter.json`
        - *Requirements*: Acceptance#性能測試
        - *Target*: 獲得基準數據

    - [ ] 2.4.2. 執行UnifiedLoop 100圈測試
        - *Goal*: 驗證UnifiedLoop性能和功能
        - *Details*:
            - 執行`run_100iteration_unified_test.py`
            - 記錄相同的性能指標
            - 保存結果到`results_unified_100iter.json`
        - *Requirements*: Acceptance#100圈長期測試成功率≥95%
        - *Target*: 成功率≥95%

    - [ ] 2.4.3. 對比分析和報告
        - *Goal*: 比較UnifiedLoop和AutonomousLoop性能
        - *Details*:
            - 建立`scripts/compare_loop_performance.py`
            - 比較指標：
                - 執行時間: UnifiedLoop ≤ AutonomousLoop * 1.1
                - 成功率: UnifiedLoop ≥ AutonomousLoop * 0.95
                - Champion更新率: UnifiedLoop > AutonomousLoop（因為有FeedbackGenerator）
                - Cohen's d: UnifiedLoop > 0.4
            - 生成對比報告
        - *Requirements*: Acceptance#性能測試, #學習效果指標
        - *Target*: 所有指標達標

- [ ] **2.5. 驗收檢查點（Week 2結束）**
    - [ ] 2.5.1. 功能驗證
        - *Checklist*:
            - ✅ UnifiedTestHarness API與ExtendedTestHarness相容
            - ✅ 100圈測試成功率≥95%
            - ✅ Champion更新率>5%
            - ✅ 統計分析正確生成

    - [ ] 2.5.2. 性能驗證
        - *Checklist*:
            - ✅ 執行時間≤AutonomousLoop * 1.1
            - ✅ 記憶體使用合理（峰值<1GB）
            - ✅ 無記憶體洩漏

    - [ ] 2.5.3. 學習效果驗證
        - *Checklist*:
            - ✅ Champion更新率>5% (baseline: 1%)
            - ✅ Cohen's d >0.4 (baseline: 0.247)
            - ✅ FeedbackGenerator正常運作
            - ✅ 反饋傳遞給TemplateParameterGenerator

---

### Week 3: Monitoring和Sandbox整合

#### Phase 3.1: Monitoring系統整合

- [ ] **3.1. 整合MetricsCollector**
    - [ ] 3.1.1. 在UnifiedLoop中整合MetricsCollector
        - *Goal*: 收集完整的性能指標
        - *Details*:
            - 在`UnifiedLoop.__init__`初始化MetricsCollector
            - 在每次迭代後收集指標
            - 支援配置開關（enable_monitoring）
            - 定期保存指標到檔案
        - *Requirements*: Requirements#1, Non-functional#可觀察性
        - *Target*: <50行修改

    - [ ] 3.1.2. 整合ResourceMonitor
        - *Goal*: 監控資源使用（CPU、記憶體）
        - *Details*:
            - 在`UnifiedLoop`啟動時初始化ResourceMonitor
            - 定期記錄資源使用
            - 檢測記憶體洩漏
            - 生成資源使用報告
        - *Requirements*: Non-functional#性能要求, #可靠性
        - *Target*: <50行修改

    - [ ] 3.1.3. 整合DiversityMonitor
        - *Goal*: 追蹤策略多樣性
        - *Details*:
            - 在`UnifiedLoop`初始化DiversityMonitor
            - 追蹤參數多樣性、程式碼多樣性
            - 檢測過擬合和欠探索
            - 生成多樣性報告
        - *Requirements*: 學習效果提升
        - *Target*: <50行修改

- [ ] **3.2. 整合Docker Sandbox**
    - [ ] 3.2.1. 在TemplateIterationExecutor整合DockerExecutor
        - *Goal*: 在Docker容器中安全執行策略
        - *Details*:
            - 修改`TemplateIterationExecutor.execute()`
            - 使用DockerExecutor替代直接執行
            - 配置資源限制（CPU、記憶體、時間）
            - 處理Docker相關錯誤
        - *Requirements*: Non-functional#安全性
        - *Target*: <100行修改

    - [ ] 3.2.2. Docker配置和測試
        - *Goal*: 驗證Docker環境正確設置
        - *Details*:
            - 建立`docker/Dockerfile.strategy_executor`
            - 配置必要的Python套件
            - 測試Docker image建置
            - 測試策略在Docker中執行
        - *Requirements*: Non-functional#安全性
        - *Target*: Docker image <500MB

- [ ] **3.3. 200圈穩定性測試**
    - [ ] 3.3.1. 建立200圈測試腳本
        - *Goal*: 長期穩定性驗證
        - *Details*:
            - 建立`run_200iteration_stability_test.py`
            - 使用UnifiedLoop + Template Mode + JSON Mode
            - 啟用所有Monitoring組件
            - 啟用Docker Sandbox
            - 每50次迭代checkpoint
        - *Requirements*: Acceptance#200圈穩定性測試
        - *Target*: <200行程式碼

    - [ ] 3.3.2. 執行200圈穩定性測試
        - *Goal*: 驗證長期穩定性和性能
        - *Details*:
            - 執行200圈測試
            - 監控資源使用趨勢
            - 檢測記憶體洩漏
            - 驗證checkpoint/resume機制
        - *Requirements*: Acceptance#200圈穩定性測試無記憶體洩漏
        - *Target*: 執行時間約8-12小時

    - [ ] 3.3.3. 穩定性分析報告
        - *Goal*: 分析200圈測試結果
        - *Details*:
            - 資源使用趨勢分析
            - 記憶體洩漏檢測
            - 性能退化檢測
            - 錯誤模式分析
            - 生成穩定性報告
        - *Requirements*: Acceptance#200圈穩定性測試
        - *Target*: 無crash，無記憶體洩漏

- [ ] **3.4. 驗收檢查點（Week 3結束）**
    - [ ] 3.4.1. 監控系統驗證
        - *Checklist*:
            - ✅ MetricsCollector正常收集指標
            - ✅ ResourceMonitor正常監控資源
            - ✅ DiversityMonitor正常追蹤多樣性
            - ✅ 所有指標可正常保存和查詢

    - [ ] 3.4.2. Docker Sandbox驗證
        - *Checklist*:
            - ✅ Docker image成功建置
            - ✅ 策略在Docker中正常執行
            - ✅ 資源限制正確生效
            - ✅ 錯誤隔離正確運作

    - [ ] 3.4.3. 穩定性驗證
        - *Checklist*:
            - ✅ 200圈測試成功完成
            - ✅ 無crash，無記憶體洩漏
            - ✅ 資源使用穩定（無持續增長）
            - ✅ Checkpoint/resume機制正常

---

### Week 4: 測試遷移和Deprecation

#### Phase 4.1: 測試腳本遷移

- [ ] **4.1. 批量遷移測試腳本**
    - [ ] 4.1.1. 分析所有測試腳本依賴
        - *Goal*: 識別所有使用AutonomousLoop的腳本
        - *Details*:
            - 使用grep搜尋`from.*autonomous_loop import`
            - 列出所有測試腳本（run_*.py）
            - 分析每個腳本的配置和依賴
            - 建立遷移優先級列表
        - *Requirements*: Requirements#4
        - *Target*: 遷移計劃文檔

    - [ ] 4.1.2. 更新高優先級腳本
        - *Goal*: 遷移最常用的測試腳本
        - *Details*:
            - 更新以下腳本添加`--loop-type`參數：
                - `run_100iteration_test.py`
                - `run_5iteration_template_smoke_test.py`
                - `run_phase1_dryrun_flashlite.py`
                - `run_diversity_pilot_test.py`
            - 添加配置示例（使用UnifiedLoop）
            - 更新README說明
        - *Requirements*: Acceptance#向後相容性
        - *Target*: 4個腳本遷移完成

    - [ ] 4.1.3. 建立遷移工具腳本
        - *Goal*: 自動化遷移輔助工具
        - *Details*:
            - 建立`scripts/migrate_to_unified_loop.py`
            - 功能：
                - 掃描測試腳本中的AutonomousLoop使用
                - 生成UnifiedLoop等價配置
                - 提供遷移建議
            - 生成遷移報告
        - *Requirements*: 降低遷移成本
        - *Target*: <300行工具腳本

- [ ] **4.2. AutonomousLoop Deprecation**
    - [ ] 4.2.1. 標記AutonomousLoop為@deprecated
        - *Goal*: 警告使用者AutonomousLoop即將廢棄
        - *Details*:
            - 在`artifacts/working/modules/autonomous_loop.py`添加：
                - `@deprecated`裝飾器
                - Deprecation警告訊息
                - 指向UnifiedLoop的遷移指南
            - 保持所有功能不變（向後相容）
        - *Requirements*: Requirements#4
        - *Target*: <20行修改

    - [ ] 4.2.2. 添加DeprecationWarning
        - *Goal*: 運行時警告使用者
        - *Details*:
            - 在`AutonomousLoop.__init__`添加warnings.warn
            - 警告訊息：
                - "AutonomousLoop is deprecated"
                - "Please migrate to UnifiedLoop"
                - "See migration guide: docs/migration_guide.md"
            - 警告類別：DeprecationWarning
        - *Requirements*: 平滑遷移
        - *Target*: <10行修改

- [ ] **4.3. 文檔完成**
    - [ ] 4.3.1. 撰寫API Reference
        - *Goal*: 完整的UnifiedLoop API文檔
        - *Details*:
            - 建立`docs/api/unified_loop.md`
            - 包含：
                - UnifiedLoop類別文檔
                - TemplateIterationExecutor文檔
                - UnifiedConfig文檔
                - 所有公開方法的參數和返回值
                - 使用範例
        - *Requirements*: Acceptance#API Reference完整
        - *Target*: >50頁API文檔

    - [ ] 4.3.2. 撰寫遷移指南
        - *Goal*: 清晰的遷移路徑文檔
        - *Details*:
            - 建立`docs/migration_guide.md`
            - 包含：
                - 為什麼要遷移
                - AutonomousLoop vs UnifiedLoop對比
                - 逐步遷移指南
                - 配置對照表
                - 常見問題FAQ
                - 疑難排解
        - *Requirements*: Acceptance#遷移指南
        - *Target*: >30頁遷移指南

    - [ ] 4.3.3. 撰寫使用指南
        - *Goal*: Getting Started Guide
        - *Details*:
            - 建立`docs/getting_started.md`
            - 包含：
                - 快速開始（5分鐘教學）
                - 基本使用範例
                - Template Mode教學
                - JSON Parameter Output教學
                - Learning Feedback教學
                - 最佳實踐
        - *Requirements*: Acceptance#使用指南
        - *Target*: >20頁使用指南

    - [ ] 4.3.4. 撰寫架構設計文檔
        - *Goal*: 架構設計說明
        - *Details*:
            - 建立`docs/architecture.md`
            - 包含：
                - 系統架構圖
                - 組件職責說明
                - 設計模式（Facade, Strategy）
                - 依賴注入機制
                - 錯誤處理架構
                - 擴展點說明
        - *Requirements*: Acceptance#架構設計文檔
        - *Target*: >40頁架構文檔

    - [ ] 4.3.5. 撰寫故障排除指南
        - *Goal*: Troubleshooting Guide
        - *Details*:
            - 建立`docs/troubleshooting.md`
            - 包含：
                - 常見錯誤和解決方案
                - 性能問題診斷
                - 配置問題診斷
                - 日誌分析指南
                - 聯繫支援
        - *Requirements*: Acceptance#故障排除指南
        - *Target*: >15頁故障排除指南

- [ ] **4.4. 最終驗收**
    - [ ] 4.4.1. 完整功能驗收
        - *Checklist*:
            - ✅ Template Mode 100%運作
            - ✅ JSON Parameter Output 100%運作
            - ✅ Learning Feedback正常生成
            - ✅ Champion更新邏輯正確
            - ✅ Docker Sandbox正常運作
            - ✅ Monitoring系統完整

    - [ ] 4.4.2. 測試驗收
        - *Checklist*:
            - ✅ 單元測試覆蓋率>80%
            - ✅ 10圈集成測試100%通過
            - ✅ 100圈測試成功率≥95%
            - ✅ 200圈測試無crash
            - ✅ 性能測試達標（≤110%）

    - [ ] 4.4.3. 學習效果驗收
        - *Checklist*:
            - ✅ Champion更新率>5%
            - ✅ Cohen's d >0.4
            - ✅ Sharpe ratio平均提升>10%
            - ✅ 統計顯著性p<0.05

    - [ ] 4.4.4. 程式碼品質驗收
        - *Checklist*:
            - ✅ 平均循環複雜度<B(6.0)
            - ✅ 維護指數>60
            - ✅ 無God Class（<500行）
            - ✅ 無God Method（<50行，<10複雜度）

    - [ ] 4.4.5. 文檔驗收
        - *Checklist*:
            - ✅ API Reference完整
            - ✅ 使用指南完整
            - ✅ 遷移指南完整
            - ✅ 架構設計文檔完整
            - ✅ 故障排除指南完整

---

## Task Dependencies

### 依賴關係圖

```
Week 1: UnifiedLoop核心實作
├── 1.1 基礎架構設置 (並行)
│   ├── 1.1.1 UnifiedLoop核心檔案
│   └── 1.1.2 UnifiedConfig
├── 1.2 TemplateIterationExecutor (依賴1.1)
│   ├── 1.2.1 TemplateIterationExecutor實作
│   └── 1.2.2 數據模型擴展
├── 1.3 配置驗證和錯誤處理 (依賴1.1, 1.2)
│   ├── 1.3.1 配置驗證
│   └── 1.3.2 錯誤處理
├── 1.4 單元測試 (依賴1.1, 1.2, 1.3)
│   ├── 1.4.1 UnifiedLoop測試
│   ├── 1.4.2 TemplateIterationExecutor測試
│   └── 1.4.3 UnifiedConfig測試
└── 1.5 驗收檢查點 (依賴所有1.x任務)

Week 2: 測試框架遷移 (依賴Week 1完成)
├── 2.1 UnifiedTestHarness建立 (並行)
│   ├── 2.1.1 UnifiedTestHarness實作
│   └── 2.1.2 統計分析功能
├── 2.2 遷移測試腳本 (依賴2.1)
│   ├── 2.2.1 更新run_100iteration_test.py
│   └── 2.2.2 建立run_100iteration_unified_test.py
├── 2.3 整合測試 (依賴2.1, 2.2)
│   ├── 2.3.1 組件整合測試
│   └── 2.3.2 向後相容性測試
├── 2.4 100圈對比測試 (依賴2.2, 2.3)
│   ├── 2.4.1 AutonomousLoop基準測試
│   ├── 2.4.2 UnifiedLoop測試
│   └── 2.4.3 對比分析
└── 2.5 驗收檢查點 (依賴所有2.x任務)

Week 3: Monitoring和Sandbox整合 (依賴Week 2完成)
├── 3.1 Monitoring系統整合 (並行)
│   ├── 3.1.1 MetricsCollector整合
│   ├── 3.1.2 ResourceMonitor整合
│   └── 3.1.3 DiversityMonitor整合
├── 3.2 Docker Sandbox整合 (並行)
│   ├── 3.2.1 DockerExecutor整合
│   └── 3.2.2 Docker配置和測試
├── 3.3 200圈穩定性測試 (依賴3.1, 3.2)
│   ├── 3.3.1 建立200圈測試腳本
│   ├── 3.3.2 執行200圈測試
│   └── 3.3.3 穩定性分析報告
└── 3.4 驗收檢查點 (依賴所有3.x任務)

Week 4: 測試遷移和Deprecation (依賴Week 3完成)
├── 4.1 測試腳本遷移 (並行)
│   ├── 4.1.1 分析所有測試腳本依賴
│   ├── 4.1.2 更新高優先級腳本
│   └── 4.1.3 建立遷移工具腳本
├── 4.2 AutonomousLoop Deprecation (並行)
│   ├── 4.2.1 標記@deprecated
│   └── 4.2.2 添加DeprecationWarning
├── 4.3 文檔完成 (並行)
│   ├── 4.3.1 API Reference
│   ├── 4.3.2 遷移指南
│   ├── 4.3.3 使用指南
│   ├── 4.3.4 架構設計文檔
│   └── 4.3.5 故障排除指南
└── 4.4 最終驗收 (依賴所有4.x任務)
```

### 並行執行建議

**Week 1**:
- 1.1.1 和 1.1.2 可並行
- 1.4.1, 1.4.2, 1.4.3 可並行

**Week 2**:
- 2.1.1 和 2.1.2 可並行
- 2.3.1 和 2.3.2 可並行

**Week 3**:
- 3.1.1, 3.1.2, 3.1.3 可並行
- 3.2.1 和 3.2.2 可並行
- 3.1 和 3.2 整體可並行

**Week 4**:
- 4.1, 4.2, 4.3 可並行（由不同人員執行）

---

## Estimated Timeline

### Week 1: UnifiedLoop核心實作
- **1.1 基礎架構設置**: 16小時
  - 1.1.1 UnifiedLoop核心檔案: 8小時
  - 1.1.2 UnifiedConfig: 4小時
  - 1.2.1 TemplateIterationExecutor: 12小時
  - 1.2.2 數據模型擴展: 2小時
- **1.3 配置驗證和錯誤處理**: 8小時
  - 1.3.1 配置驗證: 4小時
  - 1.3.2 錯誤處理: 4小時
- **1.4 單元測試**: 16小時
  - 1.4.1 UnifiedLoop測試: 6小時
  - 1.4.2 TemplateIterationExecutor測試: 8小時
  - 1.4.3 UnifiedConfig測試: 4小時
- **1.5 驗收檢查點**: 4小時
- **Week 1 Total**: 48小時 (6工作天)

### Week 2: 測試框架遷移
- **2.1 UnifiedTestHarness建立**: 12小時
  - 2.1.1 UnifiedTestHarness實作: 8小時
  - 2.1.2 統計分析功能: 4小時
- **2.2 遷移測試腳本**: 6小時
  - 2.2.1 更新run_100iteration_test.py: 2小時
  - 2.2.2 建立run_100iteration_unified_test.py: 4小時
- **2.3 整合測試**: 12小時
  - 2.3.1 組件整合測試: 6小時
  - 2.3.2 向後相容性測試: 6小時
- **2.4 100圈對比測試**: 16小時
  - 2.4.1 AutonomousLoop基準測試: 4小時（執行時間）
  - 2.4.2 UnifiedLoop測試: 4小時（執行時間）
  - 2.4.3 對比分析: 4小時
- **2.5 驗收檢查點**: 4小時
- **Week 2 Total**: 50小時 (6.25工作天)

### Week 3: Monitoring和Sandbox整合
- **3.1 Monitoring系統整合**: 12小時
  - 3.1.1 MetricsCollector整合: 4小時
  - 3.1.2 ResourceMonitor整合: 4小時
  - 3.1.3 DiversityMonitor整合: 4小時
- **3.2 Docker Sandbox整合**: 8小時
  - 3.2.1 DockerExecutor整合: 4小時
  - 3.2.2 Docker配置和測試: 4小時
- **3.3 200圈穩定性測試**: 20小時
  - 3.3.1 建立200圈測試腳本: 4小時
  - 3.3.2 執行200圈測試: 12小時（執行時間）
  - 3.3.3 穩定性分析報告: 4小時
- **3.4 驗收檢查點**: 4小時
- **Week 3 Total**: 44小時 (5.5工作天)

### Week 4: 測試遷移和Deprecation
- **4.1 測試腳本遷移**: 12小時
  - 4.1.1 分析測試腳本依賴: 4小時
  - 4.1.2 更新高優先級腳本: 4小時
  - 4.1.3 建立遷移工具腳本: 4小時
- **4.2 AutonomousLoop Deprecation**: 4小時
  - 4.2.1 標記@deprecated: 2小時
  - 4.2.2 添加DeprecationWarning: 2小時
- **4.3 文檔完成**: 24小時
  - 4.3.1 API Reference: 6小時
  - 4.3.2 遷移指南: 6小時
  - 4.3.3 使用指南: 4小時
  - 4.3.4 架構設計文檔: 6小時
  - 4.3.5 故障排除指南: 4小時
- **4.4 最終驗收**: 8小時
- **Week 4 Total**: 48小時 (6工作天)

---

### 總計時程

- **總開發時間**: 190小時
- **總工作天**: 23.75天 (約4週)
- **建議團隊規模**: 2-3人
  - 1人專注核心開發（Week 1-2）
  - 1人專注測試和整合（Week 2-3）
  - 1人專注文檔和遷移（Week 4）

### 關鍵里程碑

1. **Week 1結束**: UnifiedLoop核心功能完成，單元測試通過
2. **Week 2結束**: 100圈測試驗證通過，性能達標
3. **Week 3結束**: 200圈穩定性驗證通過，監控和沙箱完整
4. **Week 4結束**: 所有文檔完成，遷移工具就緒，專案交付

### 風險緩衝

- 每週預留10%緩衝時間（約4小時）應對未預期問題
- 100圈和200圈測試需要大量執行時間，建議overnight執行
- 如遇到重大問題，可延長1-2天完成驗收
