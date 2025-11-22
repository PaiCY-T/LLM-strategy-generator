# JSON Parameter Output Architecture - Requirements Document

重構 LLM 策略生成系統，從直接生成代碼改為輸出結構化 JSON 參數。使用 Pydantic Schema 驗證參數，中介層負責將驗證後的參數注入模板生成代碼。此改進預計可消除 ~50% 的 PreservationValidator 失敗（當前佔總失敗的 59.2%）。

## 問題背景
- 100次迭代測試成功率僅 20.6%
- 59.2% 失敗來自 PreservationValidator（參數保留驗證）
- 根本原因：LLM 直接生成代碼時容易改變結構，導致參數提取失敗
- 現有系統缺乏從 validation failures 學習的閉環機制

## 解決方案
1. **Pydantic Schema**: 定義嚴格的參數類型和約束
2. **JSON 輸出**: LLM 只輸出 JSON 參數，不輸出代碼
3. **中介層**: 驗證 JSON 並注入模板生成代碼
4. **結構化錯誤反饋**: 驗證失敗時提供精確的錯誤信息

## 預期效果
- 成功率從 20% 提升到 60-80%
- 錯誤更容易診斷和自動修復
- LLM 專注於參數優化而非代碼語法

## Core Features

### F1: Pydantic 參數 Schema
定義策略參數的嚴格類型和約束，支援多種策略模板。

- **F1.1**: `MomentumStrategyParams` Schema - 動量策略參數定義
  - `roe_type`: Literal["raw", "smoothed_4q", "yoy"]
  - `roe_smoothing_window`: int (1-12)
  - `liquidity_threshold`: float (1000-1000000)
  - `holding_period`: Literal[5, 10, 20, 60]
  - `top_percentile`: int (5-50)

- **F1.2**: `StrategyParamRequest` Schema - LLM 輸出格式
  - `reasoning`: str - 參數選擇理由
  - `params`: MomentumStrategyParams - 策略參數

- **F1.3**: Schema 註冊機制 - 支援多種策略模板的 Schema 映射

### F2: JSON 輸出 Prompt 設計
設計要求 LLM 輸出 JSON 格式的 prompt 模板。

- **F2.1**: JSON-only 輸出指令 - 明確要求 LLM 只輸出 JSON
- **F2.2**: Schema 說明 - 在 prompt 中提供參數 Schema 定義
- **F2.3**: 約束說明 - 列出所有參數的取值範圍和類型約束
- **F2.4**: Few-shot 範例 - 提供正確 JSON 輸出的範例

### F3: 中介層 (TemplateCodeGenerator)
驗證 LLM 輸出的 JSON 並生成策略代碼。

- **F3.1**: JSON 解析 - 從 LLM 輸出中提取 JSON
- **F3.2**: Pydantic 驗證 - 使用 Schema 驗證參數
- **F3.3**: 模板注入 - 將驗證後的參數注入策略模板
- **F3.4**: 錯誤收集 - 收集並格式化驗證錯誤

### F4: 結構化錯誤反饋
驗證失敗時生成 LLM 可理解的錯誤反饋。

- **F4.1**: 錯誤分類 - 區分 JSON 格式錯誤、類型錯誤、範圍錯誤
- **F4.2**: 錯誤定位 - 指出具體哪個參數出錯
- **F4.3**: 修正建議 - 提供正確的取值範圍或類型
- **F4.4**: Prompt 整合 - 將錯誤反饋整合到下次 LLM 調用的 prompt 中

## User Stories

- As a **策略進化系統**, I want **LLM 輸出結構化 JSON 參數**, so that **避免代碼結構被意外修改**
- As a **策略進化系統**, I want **Pydantic 驗證參數**, so that **在代碼生成前捕獲無效參數**
- As a **策略進化系統**, I want **結構化錯誤反饋**, so that **LLM 能從驗證失敗中學習**
- As a **開發者**, I want **清晰的 Schema 定義**, so that **容易擴展支援新的策略模板**

## Acceptance Criteria

### AC1: Pydantic Schema 驗證
- [ ] `MomentumStrategyParams` 能正確驗證所有參數類型和範圍
- [ ] 無效參數觸發 `ValidationError` 並提供詳細錯誤信息
- [ ] Schema 支援 JSON Schema 導出（供 prompt 使用）

### AC2: JSON 輸出格式
- [ ] LLM prompt 明確要求 JSON-only 輸出
- [ ] prompt 包含完整的 Schema 說明和約束
- [ ] 提供至少 2 個 few-shot 範例

### AC3: 中介層功能
- [ ] 能正確解析 LLM 輸出中的 JSON（處理 markdown 包裝等情況）
- [ ] Pydantic 驗證通過後生成正確的策略代碼
- [ ] 驗證失敗時返回結構化錯誤列表

### AC4: 錯誤反饋整合
- [ ] 錯誤反饋格式清晰、LLM 可理解
- [ ] 錯誤反饋包含參數名、錯誤類型、正確範圍
- [ ] 錯誤反饋能整合到下次 LLM 調用的 prompt 中

### AC5: 成功率提升
- [ ] 單元測試覆蓋率 ≥ 90%
- [ ] 整合測試驗證端到端流程
- [ ] 5 次迭代 smoke test 成功率 ≥ 60%

## Non-functional Requirements

### 性能要求
- JSON 解析和 Pydantic 驗證 < 100ms
- 模板注入和代碼生成 < 50ms
- 錯誤反饋生成 < 10ms

### 兼容性要求
- 與現有 `TemplateParameterGenerator` 兼容
- 與現有 `AutonomousLoop` 兼容
- 與現有 `PreservationValidator` 兼容（作為備用驗證層）

### 可擴展性要求
- Schema 註冊機制支援新增策略模板
- 錯誤反饋格式可自定義
- 模板注入機制可擴展

### 測試要求
- TDD 開發：先寫測試，後寫實現
- 單元測試覆蓋所有 Schema 驗證邊界條件
- 整合測試覆蓋完整的 LLM → JSON → Code 流程
