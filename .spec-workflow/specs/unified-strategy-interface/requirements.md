# unified-strategy-interface-refactor - Requirements Document

統一策略介面重構：基於架構分析結果，使用 TDD 方法論實現三種生成模式（Template、LLM、Factor Graph）的統一介面抽象，同時完善 Factor Graph 序列化支持。本重構確保持久化邏輯保持在 Repository 層，遵循 Repository Pattern 最佳實踐。架構分析確認當前設計優秀（Domain 層 9/10，Persistence 層 9/10，Interface 層 10/10），Phase 3（序列化）和 Phase 4（介面）可並行執行。

## Core Features

### 1. 統一策略介面 (IStrategy Protocol)

定義 `@runtime_checkable` Protocol 介面，統一三種策略生成模式（Template、LLM、Factor Graph）的領域行為契約：

- **領域方法**：`dominates()`, `get_parameters()`, `get_metrics()`
- **領域屬性**：`id`, `generation`, `metrics`
- **排除持久化方法**：不包含 `save()` 或 `load()` 方法（持久化由 Repository 層負責）

### 2. Factor Graph 序列化支持

擴展 HallOfFameRepository 以支持 Factor Graph DAG 結構的完整序列化和反序列化：

- **DAG 節點序列化**：Strategy, Selection, Filter 等 Factor Graph 節點
- **依賴關係保存**：保留因子圖的拓撲結構
- **元數據保存**：保存 strategy_id, strategy_generation, parent_ids

### 3. Champion Tracker 三模式統一支持

修復 Champion Tracker 對三種生成模式的不一致處理：

- **Template Mode**：已修復 `update_champion()` 調用（✅ Complete）
- **LLM Mode**：現有實現正確
- **Factor Graph Mode**：需要傳遞 `strategy` 參數（⚠️ Bug Fix Required）

### 4. Repository Pattern 架構保持

確保重構後繼續遵循 Repository Pattern 最佳實踐：

- **Domain Layer (ChampionTracker)**：純業務邏輯，零持久化代碼
- **Persistence Layer (HallOfFameRepository)**：純數據訪問，零業務邏輯
- **Model Layer (Strategy, ChampionStrategy)**：領域模型 + 序列化輔助方法
- **Interface Layer (IStrategy, IChampionTracker)**：純領域契約

## User Stories

### US-1: 架構師統一策略介面
**As an** 系統架構師
**I want** 定義統一的 IStrategy Protocol 介面
**So that** 三種策略生成模式可以透過相同的契約進行操作和比較

**Details:**
- IStrategy 介面只包含領域方法（dominates, get_parameters, get_metrics）
- 不包含持久化方法（save, load），遵循 SRP
- 使用 `@runtime_checkable` 支持運行時類型檢查
- 放置於 `src/learning/interfaces.py`

### US-2: 開發者序列化 Factor Graph 策略
**As a** 後端開發者
**I want** Factor Graph 策略可以完整序列化和反序列化
**So that** Champion 可以正確保存和恢復 Factor Graph DAG 結構

**Details:**
- Strategy 類已有 `to_dict()` 和 `from_dict()` 方法（types.py:229-334）
- HallOfFameRepository 需要處理 Strategy 物件的持久化
- 保存 DAG 拓撲結構和節點關係
- 支持反序列化重建完整的 Factor Graph

### US-3: 系統維護者修復 Champion 更新 Bug
**As a** 系統維護者
**I want** Factor Graph 模式的 Champion 更新正確傳遞 strategy 參數
**So that** 所有三種模式的 Champion 更新機制一致且正確

**Details:**
- 修復 `iteration_executor.py:1239` 缺少 `strategy` 參數的問題
- 從 `self._strategy_registry[strategy_id]` 獲取 Strategy 物件
- 傳遞給 `ChampionTracker.update_champion(strategy=strategy_obj)`
- 添加單元測試驗證修復

### US-4: QA 工程師驗證架構完整性
**As a** QA 工程師
**I want** 完整的測試套件驗證三種模式的 Champion 更新
**So that** 確保重構沒有破壞現有功能且架構設計正確

**Details:**
- 單元測試：IStrategy Protocol 契約驗證
- 整合測試：三種模式的 Champion 更新流程
- 架構測試：確認 Domain 層無持久化代碼
- 性能測試：序列化/反序列化性能基準

## Acceptance Criteria

### AC-1: IStrategy Protocol 定義

- [x] 定義 `IStrategy` Protocol 在 `src/learning/interfaces.py`
- [x] 包含 `@runtime_checkable` 裝飾器
- [x] 定義領域屬性：`id`, `generation`, `metrics`
- [x] 定義領域方法：`dominates(other: IStrategy) -> bool`
- [x] 定義領域方法：`get_parameters() -> Dict[str, Any]`
- [x] **不包含**持久化方法：`save()`, `load()`
- [x] 添加完整的 docstring 和行為契約說明

### AC-2: Factor Graph 序列化支持

- [x] `Strategy.to_dict()` 已實現（types.py:229-272）
- [x] `Strategy.from_dict()` 已實現（types.py:274-334）
- [ ] HallOfFameRepository 支持保存 Strategy 物件
- [ ] HallOfFameRepository 支持加載 Strategy 物件
- [ ] 序列化保留 DAG 拓撲結構
- [ ] 序列化保留元數據（strategy_id, generation, parent_ids）
- [ ] 添加 Strategy 序列化往返測試（roundtrip test）

### AC-3: Champion Tracker Bug 修復

- [x] Template Mode: 已修復 `update_champion()` 調用
- [x] LLM Mode: 現有實現正確
- [ ] Factor Graph Mode: 修復 `iteration_executor.py:1239`
  - [ ] 從 `_strategy_registry` 獲取 Strategy 物件
  - [ ] 傳遞 `strategy=strategy_obj` 參數
  - [ ] 添加單元測試驗證修復
  - [ ] 驗證 ChampionTracker.update_champion() 正確接收參數

### AC-4: 架構完整性驗證

- [x] ChampionTracker 無直接文件 I/O 代碼
- [x] HallOfFameRepository 無業務邏輯代碼
- [x] IStrategy Protocol 無持久化方法
- [x] Strategy 序列化方法僅做數據轉換（無 I/O）
- [ ] 添加架構測試驗證層級分離
- [ ] 添加文檔說明 Repository Pattern 設計決策

### AC-5: 測試覆蓋率

- [ ] IStrategy Protocol 單元測試：`isinstance()` 檢查
- [ ] Strategy 序列化測試：往返測試（to_dict → from_dict）
- [ ] Champion 更新整合測試：三種模式的完整流程
- [ ] Factor Graph 反序列化測試：DAG 結構完整性
- [ ] 測試覆蓋率 ≥ 90% for 新增代碼

## Non-functional Requirements

### NFR-1: 性能要求

- **序列化性能**：Strategy.to_dict() < 10ms per strategy
- **反序列化性能**：Strategy.from_dict() < 20ms per strategy
- **Champion 更新性能**：< 100ms per update（包含持久化）
- **內存占用**：序列化後 JSON 大小 < 100KB per strategy

### NFR-2: 可維護性要求

- **代碼覆蓋率**：≥ 90% for 新增代碼
- **文檔完整性**：所有 Protocol 方法包含完整 docstring
- **架構清晰度**：Domain/Persistence 層級零耦合
- **測試可讀性**：測試名稱遵循 TDD 命名約定（`test_<scenario>_<expected_behavior>`）

### NFR-3: 兼容性要求

- **向後兼容**：現有 Template/LLM 模式的 Champion 更新流程不受影響
- **數據兼容**：現有的 champion_strategy.json 可以正常加載
- **介面兼容**：IStrategy 不破壞現有 Strategy 類的使用方式

### NFR-4: 安全性要求

- **輸入驗證**：反序列化時驗證必要欄位存在
- **類型安全**：使用 Protocol 提供類型檢查
- **錯誤處理**：序列化失敗時備份到 backup/ 目錄（現有機制）

### NFR-5: 可測試性要求

- **依賴注入**：ChampionTracker 透過建構子注入 HallOfFameRepository
- **Mock 支持**：所有 Protocol 介面可以輕易 Mock
- **測試隔離**：單元測試不依賴文件系統（使用 Mock Repository）
- **測試速度**：單元測試套件執行時間 < 5 秒

## Implementation Priorities

### Phase 3: Factor Graph Serialization (可並行執行)

**Priority: HIGH**
**Estimated Effort: 2-3 days**

1. 擴展 HallOfFameRepository 支持 Strategy 物件
2. 實現 DAG 結構的完整序列化
3. 實現反序列化並重建 Factor Graph
4. 添加序列化往返測試

### Phase 4: Unified Interface (可並行執行)

**Priority: HIGH**
**Estimated Effort: 2-3 days**

1. 定義 IStrategy Protocol（interfaces.py）
2. 更新三種策略類實現 IStrategy 契約
3. 修復 Factor Graph Champion 更新 Bug（iteration_executor.py:1239）
4. 添加 Protocol 單元測試和整合測試

### Phase 5: Architecture Validation

**Priority: MEDIUM**
**Estimated Effort: 1-2 days**

1. 添加架構測試驗證層級分離
2. 更新文檔說明 Repository Pattern 設計決策
3. 性能基準測試
4. 完整的回歸測試

## Architecture Constraints

### CONSTRAINT-1: Repository Pattern 必須保持

**Rationale:** 架構分析確認當前 Repository Pattern 實現優秀（9-10/10 分），且符合 SOLID 原則。

**具體要求:**
- IStrategy Protocol **不得**包含 `save()` 或 `load()` 方法
- ChampionTracker **不得**直接進行文件 I/O
- HallOfFameRepository **不得**包含業務邏輯（如 Sharpe 比較）
- Strategy 類的 `to_dict()`/`from_dict()` 僅做數據轉換，不進行 I/O

### CONSTRAINT-2: 序列化與持久化分離

**Rationale:** 序列化（數據格式轉換）和持久化（存儲機制）是兩個不同的關注點。

**具體要求:**
- Strategy.to_dict() 只做 object → dict 轉換
- Strategy.from_dict() 只做 dict → object 轉換
- HallOfFameRepository 負責調用序列化方法並進行文件 I/O
- IStrategy Protocol 不要求實現 to_dict()/from_dict()（實現細節）

### CONSTRAINT-3: 依賴方向遵循 DIP

**Rationale:** 依賴倒置原則（Dependency Inversion Principle）確保架構靈活性。

**具體要求:**
- ChampionTracker 依賴 HallOfFameRepository **介面**（抽象）
- ChampionTracker 不依賴 HallOfFameRepository **實現**（具體類）
- Strategy 類不依賴任何持久化機制
- 所有依賴透過建構子注入（Constructor Injection）

### CONSTRAINT-4: TDD 開發流程

**Rationale:** 確保代碼質量和測試覆蓋率。

**具體要求:**
- 遵循 RED → GREEN → REFACTOR 循環
- 先寫測試，再寫實現
- 每個 User Story 對應至少一個整合測試
- 每個 Acceptance Criteria 對應至少一個單元測試

## Risk Assessment

### RISK-1: Factor Graph DAG 序列化複雜度

**Impact:** HIGH
**Probability:** MEDIUM
**Mitigation:**
- 利用現有的 Strategy.to_dict() 作為基礎
- 遞迴序列化 DAG 節點和邊
- 添加完整的往返測試驗證結構完整性

### RISK-2: 向後兼容性破壞

**Impact:** HIGH
**Probability:** LOW
**Mitigation:**
- IStrategy 作為新介面，不修改現有類別的公開 API
- 現有 Template/LLM 模式測試作為回歸測試基準
- 分階段部署，先驗證 Template/LLM 模式不受影響

### RISK-3: 性能回歸

**Impact:** MEDIUM
**Probability:** LOW
**Mitigation:**
- 建立性能基準測試（序列化/反序列化時間）
- 使用 HallOfFameRepository 的內存緩存機制
- 避免不必要的序列化操作

### RISK-4: 測試覆蓋率不足

**Impact:** MEDIUM
**Probability:** MEDIUM
**Mitigation:**
- 使用 TDD 流程確保測試先行
- 設定 90% 測試覆蓋率目標
- Code review 檢查測試品質

## Success Metrics

1. **功能完整性**：三種模式的 Champion 更新全部通過整合測試
2. **架構品質**：架構測試驗證 Domain/Persistence 層級零耦合
3. **代碼覆蓋率**：≥ 90% for 新增代碼
4. **性能達標**：序列化 < 10ms, 反序列化 < 20ms
5. **向後兼容**：現有 Template/LLM 測試全部通過

## References

- **架構分析報告**：Zen Analysis - ChampionTracker & HallOfFameRepository Architecture
- **現有實現**：
  - `src/learning/champion_tracker.py` - ChampionTracker 實現
  - `src/repository/hall_of_fame.py` - HallOfFameRepository 實現
  - `src/learning/interfaces.py` - IChampionTracker Protocol
  - `src/evolution/types.py` - Strategy 類（含 to_dict/from_dict）
- **Bug 報告**：
  - Issue #1: Template Mode update_if_better method missing (✅ Fixed)
  - Issue #2: StrategyMetrics JSON serialization failure (✅ Fixed)
  - Issue #3: Factor Graph champion update missing strategy parameter (⚠️ Pending)
