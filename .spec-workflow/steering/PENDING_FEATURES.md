# Pending Features & Deferred Work

**Last Updated**: 2025-10-31
**Purpose**: Track未完成功能開發工作，確保不會遺忘重要任務

---

## 使用說明

本文檔追蹤所有**已規劃但尚未完成**的功能開發工作。每個項目包含：
- **Priority**: P0-P3 優先級
- **Estimated Time**: 預估工時
- **Dependencies**: 依賴關係
- **Spec Location**: 相關規格文件位置
- **Reason for Deferral**: 延遲原因

**建議工作流**：
1. 定期審查本文檔（每月或完成主要 milestone 後）
2. 根據優先級和可用時間選擇任務
3. 完成後移除或標記為 ✅ COMPLETE
4. 使用 GitHub Issues + Labels 追蹤具體執行（可選）

---

## 🔥 P0-P1 High Priority (推薦優先處理)

### 1. phase2-backtest-execution 剩餘工作

**Status**: 13/26 tasks remaining (50% complete)
**Spec**: `.spec-workflow/specs/phase2-backtest-execution/`
**Priority**: P0 CRITICAL
**Estimated Time**: 6-8 hours
**Dependencies**: None (基礎組件已完成)

#### 剩餘任務
- [ ] **Task 7.2**: 全量 20 策略執行（用新 validation framework）（2-3h）
- [ ] **Task 7.3**: 分析結果並生成總結（1-2h）
- [ ] **Task 8.1**: 文檔更新（執行框架使用說明）（1h）
- [ ] **Task 8.2**: API 文檔生成（docstrings + type hints）（1h）
- [ ] **Task 8.3**: 代碼審查與優化（1h）

#### Why Deferred
- 先完成 Phase 1.1 validation framework（已完成）
- 需要使用新的統計驗證工具執行完整測試

#### Next Steps
1. 用 Phase 1.1 validation framework 執行 Task 7.2
2. 分析結果，確認系統可以正常產出策略
3. 完成文檔工作

---

### 2. phase3-learning-iteration 開發

**Status**: 0/42 tasks remaining (0% complete)
**Spec**: `.spec-workflow/specs/phase3-learning-iteration/`
**Priority**: P0 CRITICAL
**Estimated Time**: 20-30 hours
**Dependencies**: phase2-backtest-execution 必須完成

#### 關鍵組件（42 tasks）
1. **Phase 1**: History Management (3 tasks, ~3h)
   - IterationHistory class (JSONL persistence)
   - Record validation
   - History tests

2. **Phase 2**: Feedback Generation (3 tasks, ~3h)
   - FeedbackGenerator class
   - Template management
   - Feedback tests

3. **Phase 3**: LLM Integration (3 tasks, ~4h)
   - LLMClient wrapper (Gemini + OpenRouter)
   - Code extraction from LLM response
   - LLM integration tests

4. **Phase 4**: Champion Tracking (3 tasks, ~3h)
   - ChampionTracker class
   - Staleness detection
   - Champion tests

5. **Phase 5**: Iteration Executor (5 tasks, ~6h)
   - IterationExecutor class (refactored from autonomous_loop.py)
   - Factor Graph fallback integration
   - Fallback tests
   - Output compatibility validation
   - Executor tests

6. **Phase 6**: Main Learning Loop (5 tasks, ~4h)
   - LearningLoop refactoring (autonomous_loop.py 2000+ lines → 200 lines)
   - Configuration management (YAML)
   - Loop resumption logic (SIGINT handling)
   - Interruption/resumption tests
   - Learning loop tests

7. **Phase 7**: E2E Testing (3 tasks, ~4h)
   - 5-iteration smoke test
   - 20-iteration validation test
   - Learning effectiveness analysis

8. **Phase 8**: Documentation (3 tasks, ~2h)
   - README & steering docs updates
   - API documentation
   - Code review & optimization

9. **Phase 9**: Refactoring Validation (2 tasks, ~1h)
   - autonomous_loop.py refactoring verification
   - Refactoring completion report

#### Why Deferred
- 依賴 Phase 2 的執行框架（BacktestExecutor, MetricsExtractor, SuccessClassifier）
- 用戶優先級：先確認系統能正常產出策略，再建立學習迭代

#### Next Steps
1. 確保 phase2-backtest-execution 完成並穩定
2. 開始 Phase 3 development（從 Phase 1: History Management 開始）
3. 逐步重構 autonomous_loop.py（2000+ 行 → 6 個模組 ~1050 行）

---

### 3. phase2-validation-framework-integration P1-P2 任務

**Status**: 6/11 tasks complete (P0 complete, P1-P2 deferred)
**Spec**: `.spec-workflow/specs/phase2-validation-framework-integration/`
**Priority**: P1 HIGH (enhancement, not blocking)
**Estimated Time**: 6-8 hours
**Dependencies**: None

#### 延遲任務（P1-P2）
- [ ] **Task 1.1.7**: Performance benchmarks（2-3h）
  - 在生產數據集上基準測試驗證性能
  - 目標：每個策略 <60 秒
  - 記憶體洩漏檢測

- [ ] **Task 1.1.8**: Chaos testing（2-3h）
  - NaN 處理
  - 並發執行安全性
  - 網路超時處理

- [ ] **Task 1.1.9**: Monitoring integration（2h）
  - 添加日誌和指標
  - 性能追蹤
  - 錯誤警報鉤子

- [ ] **Task 1.1.10**: Documentation updates（1h）
  - API 文檔
  - 已知限制
  - 生產部署指南

- [ ] **Task 1.1.11**: Production deployment runbook（1h）
  - 部署檢查清單
  - 回滾程序
  - 監控設定

#### Why Deferred
- P0 統計有效性問題已解決（97 tests passing）
- 這些是**品質提升**，不是**功能啟用**
- 用戶優先級：先確認能產出策略

#### Resumption Criteria
1. phase2-backtest-execution 完成
2. phase3-learning-iteration 功能正常
3. 系統可以正常產出有效策略
4. 有空閒時間進行品質改進

---

## 🟡 P2 Medium Priority (次要功能)

### 4. Docker Sandbox 進階功能

**Status**: 基礎功能完成，進階功能pending
**Spec**: `.spec-workflow/specs/docker-sandbox-security/`
**Priority**: P2 MEDIUM
**Estimated Time**: 4-6 hours

#### Pending Tasks
- [ ] **資源限制調優**: CPU/Memory 根據實際使用優化
- [ ] **多容器並行執行**: 加速批量回測
- [ ] **容器健康檢查**: 自動重啟失敗的容器
- [ ] **日誌聚合**: 集中式日誌收集與分析

#### Why Deferred
- 基礎 sandbox 已可用且安全
- 進階功能非核心需求

---

### 5. 監控系統增強

**Status**: 基礎監控完成，Dashboard pending
**Spec**: Multiple monitoring-related specs
**Priority**: P2 MEDIUM
**Estimated Time**: 3-4 hours

#### Pending Tasks
- [ ] **Grafana Dashboard**: 即時可視化學習進度
- [ ] **Prometheus Metrics**: 更細緻的指標收集
- [ ] **Alert Manager**: 自動警報系統（Sharpe 下降、錯誤率上升）
- [ ] **Performance Profiling**: 系統性能瓶頸分析

#### Why Deferred
- 基礎日誌和監控已足夠
- Dashboard 非必需（可用 JSONL 手動分析）

---

### 6. LLM Integration 進階功能

**Status**: 基礎 LLM integration 完成，進階功能 pending
**Spec**: `.spec-workflow/specs/llm-integration-activation/`
**Priority**: P2 MEDIUM
**Estimated Time**: 4-6 hours

#### Pending Tasks
- [ ] **Token Usage Tracking**: 成本追蹤和預算控制
- [ ] **Model Performance Comparison**: A/B 測試不同 LLM models
- [ ] **Prompt Engineering Optimization**: 自動調優 prompt templates
- [ ] **Multi-Model Ensemble**: 結合多個 LLM 的輸出

#### Why Deferred
- 基礎 LLM generation 已可用
- 成本優化和性能比較可後續進行

---

## 🟢 P3 Low Priority (Nice-to-have)

### 7. 文檔系統完善

**Priority**: P3 LOW
**Estimated Time**: 6-8 hours

#### Pending Tasks
- [ ] **API Reference Auto-generation**: 從 docstrings 自動生成
- [ ] **Architecture Diagrams**: 系統架構視覺化
- [ ] **Tutorial Videos**: 錄製使用教學影片
- [ ] **FAQ Document**: 常見問題集

#### Why Deferred
- 基礎文檔已足夠（README + steering docs + system docs）
- 可隨時間逐步補充

---

### 8. 測試覆蓋率提升

**Current Coverage**: ~85-90%
**Target**: >95%
**Priority**: P3 LOW
**Estimated Time**: 4-6 hours

#### Pending Tasks
- [ ] **Integration Test Coverage**: 更多 E2E 測試場景
- [ ] **Edge Case Testing**: 極端情況測試
- [ ] **Performance Regression Tests**: 性能回歸測試
- [ ] **Mutation Testing**: 測試品質評估

#### Why Deferred
- 當前覆蓋率已足夠（關鍵路徑 100%）
- 可在遇到 bug 時補充特定測試

---

## 📋 使用 GitHub Issues 追蹤（可選）

如果決定使用 GitHub Issues，建議的 Labels：

### 按階段/模組
- `phase:validation` - 驗證框架相關
- `phase:backtest` - 回測執行相關
- `phase:learning-loop` - 學習迭代相關
- `subsystem:monitoring` - 監控系統
- `subsystem:sandbox` - Docker sandbox

### 按優先級
- `P0-critical` - 阻塞生產的問題
- `P1-high` - 重要但非阻塞
- `P2-medium` - 次要功能
- `P3-low` - Nice-to-have

### 按類型
- `feature` - 新功能開發
- `bug` - Bug 修復
- `refactor` - 代碼重構
- `chore` - 維護工作
- `research` - 研究性任務

### 示例 Issue 創建
```bash
# Example: Create issue for Task 7.2
gh issue create \
  --title "Task 7.2: 全量 20 策略執行（用新 validation）" \
  --body "執行 phase2-backtest-execution Task 7.2..." \
  --label "phase:backtest,P0-critical,feature"
```

---

## 📊 統計摘要

### 按優先級
- **P0 Critical**: 2 項（phase2 完成 + phase3 開發）
- **P1 High**: 1 項（validation P1-P2 任務）
- **P2 Medium**: 3 項（Docker, 監控, LLM 進階）
- **P3 Low**: 2 項（文檔, 測試覆蓋率）

### 按時間估算
- **P0-P1 Total**: 32-46 hours
- **P2 Total**: 11-16 hours
- **P3 Total**: 10-14 hours
- **Grand Total**: 53-76 hours

### 建議優先順序
1. ✅ **Immediate**: phase2-backtest-execution 完成（6-8h）
2. ✅ **Next**: phase3-learning-iteration 開發（20-30h）
3. ⏸️ **Later**: validation P1-P2 + 其他 P2-P3 任務（依需求和時間）

---

## 🔄 維護策略

### 每月審查
- 審查本文檔，更新狀態
- 根據最新優先級調整任務順序
- 刪除或標記已完成的任務

### 新任務添加
- 發現新的延遲任務時，添加到相應優先級區塊
- 包含 Priority, Time, Dependencies, Reason

### 完成任務
- 標記為 ✅ COMPLETE（保留一段時間作為記錄）
- 或直接刪除（如果不需要歷史記錄）

---

**Last Review**: 2025-10-31
**Next Review**: 2025-11-30（建議）
