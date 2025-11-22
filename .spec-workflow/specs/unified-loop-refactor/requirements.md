# UnifiedLoop架構重構 - Requirements Document

整合AutonomousLoop和LearningLoop的優勢，創建統一的UnifiedLoop架構，實現Template Mode、JSON Parameter Output和Learning Feedback的完整整合，同時保持向後相容性並提供清晰的遷移路徑。此重構將解決Phase 6重構不完全導致的技術債務問題，降低維護成本30-60%，並為未來擴展奠定基礎。

## Core Features

### 1. 統一的Loop架構
創建單一的UnifiedLoop類別，取代目前並存的AutonomousLoop (2,821行) 和 LearningLoop (416行)，整合兩者的優勢功能。

**關鍵功能整合**:
- ✅ Template Mode (from AutonomousLoop) - 使用黃金模板確保參數一致性
- ✅ JSON Parameter Output (from AutonomousLoop) - LLM輸出JSON格式參數，Pydantic驗證
- ✅ Learning Feedback (from LearningLoop) - 完整的性能反饋學習循環
- ✅ Modular Architecture (from LearningLoop) - 組件化設計，責任分離
- ✅ Docker Sandbox (統一實作) - 安全的策略執行環境
- ✅ Monitoring System (整合) - 完整的監控和指標收集

### 2. TemplateIterationExecutor
專門處理Template Mode的迭代執行器，支援JSON模式和Code模式。

**功能需求**:
- 整合TemplateParameterGenerator進行參數生成
- 支援JSON Parameter Output模式（Phase 1.1）
- 整合FeedbackGenerator提供學習反饋
- 支援Template-based code generation
- 與現有的template system完全相容

### 3. 學習反饋系統整合
完整整合FeedbackGenerator、ChampionTracker和IterationHistory，實現真正的LLM學習模式。

**學習功能**:
- 自動生成性能反饋（Sharpe ratio趨勢、champion比較）
- 傳遞反饋給下一次LLM呼叫
- 追蹤champion更新和性能改進
- 支援多目標優化反饋

### 4. 向後相容性
確保現有測試腳本和工作流無需修改即可使用UnifiedLoop。

**相容性需求**:
- 提供與AutonomousLoop相同的API介面
- 支援ExtendedTestHarness無縫遷移
- 配置參數向後相容
- 檔案格式相容（history.json, champion.json）

### 5. 測試基礎設施升級
創建UnifiedTestHarness，支援長期測試（50-200圈）和統計分析。

**測試功能**:
- Checkpointing和resume能力
- 統計分析（Cohen's d, significance tests）
- 性能基準測試
- 對比測試（vs AutonomousLoop）

## User Stories

### 作為系統架構師
- **需求**: 我需要一個統一的Loop架構，消除重複實作
- **目的**: 降低維護成本30-60%，提高程式碼品質
- **驗收**: 程式碼重複率從45%降至<20%，平均複雜度<B(6.0)

### 作為AI研究員
- **需求**: 我需要啟用LLM學習功能，讓系統從過去的迭代中學習
- **目的**: 提升策略品質，加速收斂到高性能策略
- **驗收**: Champion更新頻率>5% (baseline: 1%), Cohen's d >0.4 (baseline: 0.247)

### 作為測試工程師
- **需求**: 我需要能運行100-200圈長期測試，並獲得統計分析
- **目的**: 驗證學習效果和系統穩定性
- **驗收**: 100圈測試成功率≥95%，統計分析自動生成

### 作為維護工程師
- **需求**: 我需要清晰的遷移路徑，從AutonomousLoop遷移到UnifiedLoop
- **目的**: 平滑升級，不破壞現有功能
- **驗收**: 所有測試腳本可透過簡單配置切換使用UnifiedLoop

### 作為新加入的開發者
- **需求**: 我需要理解系統架構，快速上手
- **目的**: 降低學習曲線，提高開發效率
- **驗收**: Onboarding時間<1天（baseline: >3天）

## Acceptance Criteria

### 功能完整性
- [ ] Template Mode正常運作，參數保存率100%
- [ ] JSON Parameter Output正常運作，Pydantic驗證100%通過
- [ ] Learning Feedback正常運作，反饋在第2次迭代開始生成
- [ ] FeedbackGenerator整合成功，反饋內容包含Sharpe趨勢和champion比較
- [ ] ChampionTracker整合成功，champion更新邏輯正確
- [ ] IterationHistory整合成功，所有迭代記錄完整
- [ ] Docker Sandbox整合成功，安全執行策略
- [ ] Monitoring系統整合成功，指標收集完整

### 測試通過標準
- [ ] 單元測試覆蓋率>80%
- [ ] 10圈集成測試100%通過
- [ ] 100圈長期測試成功率≥95%
- [ ] 200圈穩定性測試無記憶體洩漏
- [ ] 性能測試：執行時間≤AutonomousLoop * 1.1

### 學習效果指標
- [ ] Champion更新頻率>5% (baseline: 1%)
- [ ] Cohen's d效果量>0.4 (baseline: 0.247)
- [ ] Sharpe ratio平均值提升>10%
- [ ] 統計顯著性: p-value <0.05

### 向後相容性
- [ ] ExtendedTestHarness無需修改即可使用UnifiedLoop
- [ ] run_100iteration_test.py透過簡單配置切換
- [ ] 所有配置參數向後相容
- [ ] history.json和champion.json格式相同

### 程式碼品質
- [ ] 平均循環複雜度<B(6.0)
- [ ] 維護指數>60
- [ ] 無God Class（單一類別<500行）
- [ ] 無God Method（單一方法<50行，複雜度<10）

### 文檔完整性
- [ ] API Reference完整
- [ ] 使用指南（Getting Started Guide）
- [ ] 遷移指南（Migration Guide）
- [ ] 架構設計文檔
- [ ] 故障排除指南

## Non-functional Requirements

### 性能要求
- **執行速度**: UnifiedLoop執行時間≤AutonomousLoop * 1.1
- **記憶體使用**: 峰值記憶體≤1GB (100圈測試)
- **啟動時間**: Loop初始化時間<2秒
- **回應時間**: 單次迭代執行時間<30秒（不含LLM API呼叫）

### 可靠性要求
- **穩定性**: 200圈測試無crash，無記憶體洩漏
- **錯誤處理**: 所有錯誤有清晰的錯誤訊息和恢復策略
- **資料完整性**: 所有迭代記錄正確保存，可replay
- **向後相容**: 現有測試腳本100%相容

### 可維護性要求
- **程式碼複雜度**: 平均循環複雜度<B(6.0)
- **維護指數**: >60（良好可維護性）
- **模組化**: 所有組件可獨立測試和替換
- **文檔覆蓋**: 所有公開API有docstring和範例

### 擴展性要求
- **策略模式**: 支援新的IterationExecutor實作
- **依賴注入**: 所有組件可透過配置注入
- **Hook機制**: 支援在關鍵點插入自定義邏輯
- **配置驅動**: 所有行為可透過配置調整

### 安全性要求
- **Sandbox隔離**: 所有策略在Docker容器中執行
- **輸入驗證**: 所有LLM輸出經過Pydantic嚴格驗證
- **AST驗證**: 所有生成的程式碼經過AST安全檢查
- **錯誤隔離**: 單一迭代失敗不影響整體執行

### 相容性要求
- **Python版本**: 支援Python 3.10+
- **依賴版本**: 相容現有的依賴版本
- **API相容**: 提供與AutonomousLoop相同的API
- **檔案格式**: 與現有檔案格式100%相容

### 可觀察性要求
- **日誌記錄**: 所有關鍵操作有日誌記錄
- **指標收集**: 支援MetricsCollector、ResourceMonitor、DiversityMonitor
- **進度顯示**: 清晰的進度條和狀態顯示
- **錯誤追蹤**: 所有錯誤有完整的stack trace

## 技術債務解決目標

### 程式碼重複消除
- **目標**: 程式碼重複率從45%降至<20%
- **策略**: 統一到單一UnifiedLoop實作，移除重複的sandbox/executor/validator

### 複雜度降低
- **目標**: 消除God Class和God Method
- **策略**: AutonomousLoop._run_freeform_iteration (F-82複雜度) 分解為多個小方法

### 維護成本降低
- **目標**: 維護成本降低30-60%
- **策略**: 統一架構，消除雙重維護，提高程式碼品質

### 架構清晰化
- **目標**: 單一清晰的架構，無歧義
- **策略**: UnifiedLoop作為唯一入口，AutonomousLoop標記為@deprecated

## 成功指標 (KPI)

### 交付時程
- [ ] Week 1: UnifiedLoop核心架構完成
- [ ] Week 2: UnifiedTestHarness遷移完成，100圈測試通過
- [ ] Week 3: Monitoring和Sandbox整合完成，200圈測試通過
- [ ] Week 4: 測試遷移和deprecation完成，文檔完整

### 品質指標
- [ ] 單元測試覆蓋率>80%
- [ ] 平均循環複雜度<B(6.0)
- [ ] 維護指數>60
- [ ] 程式碼重複率<20%

### 學習效果指標
- [ ] Champion更新頻率>5%
- [ ] Cohen's d >0.4
- [ ] Sharpe ratio提升>10%
- [ ] p-value <0.05

### 業務影響指標
- [ ] Onboarding時間<1天
- [ ] 維護成本降低30-60%
- [ ] Bug修復時間降低50%
- [ ] 新功能開發速度提升30%

## 風險與緩解

### 風險1: API不相容導致測試失敗
- **機率**: 中 (40%)
- **影響**: 高
- **緩解策略**: 完整的向後相容性測試，保持AutonomousLoop API介面，提供adapter層

### 風險2: 性能下降
- **機率**: 低 (20%)
- **影響**: 中
- **緩解策略**: 性能基準測試，profiling分析，優化關鍵路徑

### 風險3: 學習效果不佳
- **機率**: 中 (30%)
- **影響**: 低
- **緩解策略**: 調整FeedbackGenerator策略，參數優化，A/B測試

### 風險4: 遷移時間超出預期
- **機率**: 中 (40%)
- **影響**: 中
- **緩解策略**: 漸進式遷移，保留AutonomousLoop作為fallback，分階段部署

## 依賴與前置條件

### 必要依賴
- Python 3.10+
- 現有的src/learning組件（FeedbackGenerator, ChampionTracker, IterationHistory）
- 現有的src/generators組件（TemplateParameterGenerator, TemplateCodeGenerator）
- 現有的src/sandbox組件（DockerExecutor）
- 現有的src/monitoring組件（MetricsCollector, ResourceMonitor）

### 前置條件
- AutonomousLoop功能完整且穩定
- LearningLoop架構已驗證
- Template Mode和JSON Mode已驗證（100%成功率）
- 測試基礎設施已建立（ExtendedTestHarness）

## 排除範圍 (Out of Scope)

### 不包含的功能
- ❌ Phase 3完全遷移（移除artifacts/working/modules）- 留待後續
- ❌ 所有run_*.py測試腳本自動遷移 - 僅提供遷移工具和指南
- ❌ 新的策略生成算法 - 保持現有算法不變
- ❌ UI介面 - 純後端重構

### 保持不變的部分
- LLM API呼叫邏輯
- Backtest執行邏輯
- Metrics計算邏輯
- Champion評分邏輯

## 後續計畫

### Phase 5: 完全遷移 (後續6-12週)
- 遷移所有run_*.py測試腳本
- 統一所有Sandbox/Executor實作
- 統一所有Validator架構
- 完全移除artifacts/working/modules
- 技術債務清零

### Phase 6: 優化和擴展 (後續)
- 性能優化
- 新的學習算法
- 多目標優化增強
- UI介面開發
