# LLM Field Validation Fix - Three-Layered Defense - Requirements Document

Fix LLM strategy generation failure (0% success rate) through three-layered defense with Test-Driven Development methodology. Root cause: 29.4% invalid field rate (5/17 fields). Solution: Enhanced data field manifest (Layer 1), pattern-based validator (Layer 2), and configuration-based architecture (Layer 3). Timeline: 21 days. Target: 0% → 70-85% success rate with 0% field errors.

## Core Features

### Layer 1: Enhanced Data Field Manifest (Days 3-4)
創建完整的 finlab API 數據字段清單系統，包含：
- **規範字段名稱映射**: 將所有 finlab API 字段標準化（如 `price:收盤價`、`price:成交金額`）
- **別名解析功能**: 支持常見別名自動轉換（`close` → `price:收盤價`, `volume` → `price:成交股數`, `成交量` → `price:成交金額`）
- **字段元數據管理**: 包含 category（價格/基本面/技術指標）、frequency（日頻/週頻/月頻）、dtype（float/int/str）、description（中英文描述）
- **驗證機制**: 對照 finlab API 實時驗證字段有效性

### Layer 2: Pattern-Based Validator (Days 5-6)
實現智能字段驗證與自動修正系統：
- **模式匹配驗證**: 自動檢測 LLM 生成代碼中的 `data.get('field_name')` 模式
- **常見錯誤自動修正**: 針對 top 20 常見錯誤（如 `price:成交量` → `price:成交金額`）提供自動修正建議
- **結構化錯誤反饋**: 提供清晰的錯誤訊息和修正建議（"Did you mean 'price:成交金額'?"）
- **Layer 1 整合**: 使用 Layer 1 manifest 進行即時驗證

### Layer 3: Configuration-Based Architecture (Days 8-21)
遷移至配置驅動的策略生成架構：
- **YAML 策略配置**: 定義 top 5 成功模式的 YAML schema（SMA Crossover, Momentum+Value, Quality Score, Reversal, Breakout）
- **Factory 執行器**: 實現 StrategyFactory 解析並執行 YAML configs
- **LLM → Config 生成**: 引導 LLM 生成結構化 YAML 而非直接生成 Python 代碼
- **兩階段提示**: 先選擇字段，再生成配置（降低複雜度）

## User Stories

### As a System Architect
- **需求**: 我需要 LLM 生成的策略代碼使用正確的 finlab API 字段名稱
- **目的**: 避免 29.4% 的字段錯誤率導致策略執行失敗
- **驗收**: Layer 1 實施後字段錯誤率降至 0%

### As a Strategy Generator Developer
- **需求**: 我需要自動檢測並修正 LLM 生成代碼中的常見字段錯誤
- **目的**: 提升 LLM Only 模式從 0% 到 25-45% 的成功率
- **驗收**: Layer 2 實施後 90%+ 常見錯誤被自動修正

### As a QA Engineer
- **需求**: 我需要完整的測試覆蓋率（≥90%）確保三層防禦正常運作
- **目的**: 在每個 checkpoint 驗證改進效果，確保不引入新問題
- **驗收**: 所有層級的單元測試、整合測試、20 迭代驗證測試通過

### As a Product Owner
- **需求**: 我需要看到 LLM 成功率的漸進式提升（0% → 25-45% → 40-60% → 70-85%）
- **目的**: 驗證三層防禦策略的有效性，確保投資回報
- **驗收**: Day 7、Day 18、Day 21 checkpoints 達成預期成功率目標

### As a Maintenance Developer
- **需求**: 我需要清晰的配置架構，避免直接修改 Python 代碼生成邏輯
- **目的**: 降低維護成本，提升策略模式擴展性
- **驗收**: Layer 3 實施後，新增策略模式只需添加 YAML config，無需修改核心代碼

## Acceptance Criteria

### Phase 1: Foundation Week (Days 1-7)

#### Day 1-2: finlab Field Discovery
- [ ] **測試通過**: `test_finlab_api_field_availability()` 驗證所有字段存在於 finlab API
- [ ] **字段清單完整**: 發現並記錄 ≥17 個字段（包含 5 個之前無效的字段）
- [ ] **緩存建立**: `tests/fixtures/finlab_fields.json` 創建並包含完整字段元數據
- [ ] **錯誤率**: 字段發現階段達成 0% 錯誤率

#### Day 3-4: Layer 1 - Enhanced Manifest
- [ ] **別名解析測試**: `test_alias_resolution()` 通過，常見別名 100% 正確解析
- [ ] **元數據測試**: `test_field_metadata_access()` 通過，category/frequency/dtype/aliases 全部可查詢
- [ ] **文件創建**: `src/config/data_fields.py` 包含完整的 17+ 字段 manifest
- [ ] **驗證通過**: 所有字段對照 finlab API 驗證成功

#### Day 5-6: Layer 2 - Pattern Validator
- [ ] **自動修正測試**: `test_common_mistake_autocorrection()` 通過，"close" → "price:收盤價" 等修正生效
- [ ] **錯誤檢測測試**: `test_invalid_field_detection()` 通過，無效字段被捕獲並提供建議
- [ ] **整合測試**: `test_integration_with_manifest()` 通過，驗證器正確使用 Layer 1 manifest
- [ ] **修正率**: 90%+ 的常見字段錯誤被自動修正

#### Day 7: Integration Checkpoint (DECISION GATE 1)
- [ ] **20 迭代測試**: `test_20iteration_llm_improvement()` 通過
- [ ] **成功率**: LLM Only 模式達成 25-45% 成功率（從 0% 提升）
- [ ] **字段錯誤率**: 0% 字段錯誤（從 29.4% 降低）
- [ ] **性能**: 平均每次迭代執行時間 <30 秒
- [ ] **決策閘門**: 如果成功率 <25%，停止 Layer 3 實施，debug Layer 1+2

### Phase 2: Configuration Migration (Days 8-21)

#### Day 8-10: Top 5 Pattern Selection
- [ ] **模式覆蓋測試**: `test_top5_pattern_coverage()` 通過，5 個模式覆蓋 ≥60% Factor Graph 成功案例
- [ ] **模式識別**: 確認 5 個模式（SMA Crossover, Momentum+Value, Quality Score, Reversal, Breakout）
- [ ] **Schema 定義**: 為 5 個模式創建 YAML schema 定義
- [ ] **文件創建**: `src/config/strategy_schema.yaml` 包含完整 schema

#### Day 11-14: YAML Schema + Factory
- [ ] **解析測試**: `test_yaml_config_parsing()` 通過，5 個 configs 全部成功解析
- [ ] **執行測試**: `test_factory_execution()` 通過，StrategyFactory 成功執行 configs
- [ ] **Factory 實現**: `src/execution/config_executor.py` 創建並通過所有測試
- [ ] **範例 configs**: 5 個可執行的 YAML config 範例創建於 `examples/configs/`
- [ ] **執行成功**: 所有 5 個 configs 執行無錯誤且產生交易訊號

#### Day 15-18: LLM → Config Generation (DECISION GATE 2)
- [ ] **YAML 生成測試**: `test_llm_generates_valid_yaml()` 通過，LLM 輸出有效 YAML（非 Python 代碼）
- [ ] **20 迭代 Config 測試**: `test_20iteration_config_mode()` 通過
- [ ] **成功率**: 達成 40-60% 成功率（從 25-45% 提升）
- [ ] **YAML 有效性**: 100% 生成的 configs 可成功解析（0% 解析錯誤）
- [ ] **決策閘門**: 如果成功率 <40%，診斷問題（configs 有效性 vs 執行失敗 vs 格式錯誤）

#### Day 19-21: Iterative Expansion
- [ ] **擴展策略**: 根據 Day 18 結果決定擴展路徑（40-60%: 添加 patterns 6-10; <40%: debug prompts; >60%: 加速至 patterns 11-15）
- [ ] **最終成功率**: 目標 70-85%（stretch goal）或至少維持 40-60%（realistic goal）
- [ ] **穩定性**: 擴展後的模式庫維持 0% 字段錯誤率
- [ ] **文檔完成**: 創建 `docs/LAYER3_CONFIG_SPEC.md` 記錄配置架構

## Non-functional Requirements

### Performance Requirements
- **Layer 1 查詢性能**: 字段別名解析 <1ms
- **Layer 2 驗證性能**: 單次代碼驗證 <10ms
- **Layer 3 執行性能**: Config 解析並執行 <100ms
- **迭代測試性能**: 20 次迭代測試總時長 <10 分鐘（平均 <30s/次）
- **整體性能**: 不影響 Factor Graph 模式性能（維持 ~10s/迭代）

### Quality Requirements
- **測試覆蓋率**: ≥90% 代碼覆蓋率（unit + integration tests）
- **字段錯誤率**: 0% 字段錯誤（非妥協標準）
- **自動修正準確率**: 90%+ 常見錯誤被正確修正
- **向後兼容性**: Factor Graph 模式 100% 成功率維持（不得退化）
- **測試方法論**: 嚴格遵循 TDD（Test-Driven Development），測試先行

### Security Requirements
- **字段驗證**: 所有 LLM 生成的字段名稱必須通過 manifest 驗證，拒絕無效字段
- **代碼注入防護**: Layer 2 驗證器必須檢測惡意代碼模式
- **Config 驗證**: YAML configs 必須通過 schema 驗證，防止任意代碼執行

### Maintainability Requirements
- **模組化設計**: Layer 1/2/3 獨立實現，低耦合高內聚
- **文檔完整性**: 每層級創建獨立規格文檔（LAYER1_MANIFEST_SPEC.md, LAYER2_VALIDATOR_SPEC.md, LAYER3_CONFIG_SPEC.md）
- **擴展性**: 新增策略模式只需添加 YAML config，無需修改核心代碼
- **代碼風格**: 遵循 PEP 8，使用 type hints，完整 docstrings

### Risk Management Requirements
- **Critical Risk Mitigation**:
  - finlab API 字段發現失敗 → 使用 Factor Graph 字段列表作為後備
  - Layer 1+2 成功率 <25% → 停止 Layer 3，實施 regex/AST validator
  - 字段錯誤率 >0% → 立即回滾並進行根因分析
- **Decision Gates**:
  - Day 7: 成功率 <25% 則停止 Layer 3 實施
  - Day 18: 成功率 <40% 則進行診斷修復
  - Day 21: 評估是否進入 Phase 3（AST validator 或模式擴展）

### Compatibility Requirements
- **Python 版本**: ≥3.8
- **finlab API**: 與現有 API 版本完全兼容
- **依賴項**: pytest ≥7.0.0, pytest-cov ≥3.0.0, pyyaml ≥6.0
- **CI/CD 整合**: 支持 GitHub Actions 自動化測試（可選但建議）

### Timeline Requirements
- **Phase 1 完成**: Day 7（Foundation Week）
- **Phase 2 完成**: Day 21（Configuration Migration）
- **Total Timeline**: 21 天（3 週）
- **Checkpoints**: Day 2, Day 4, Day 6, Day 7 (Gate 1), Day 10, Day 14, Day 18 (Gate 2), Day 21

### Success Metrics
- **字段錯誤率**: 29.4% → 0%（Day 4 達成）
- **LLM 成功率**: 0% → 25-45%（Day 7）→ 40-60%（Day 18）→ 70-85%（Day 21 stretch）
- **測試覆蓋率**: 維持 ≥90%（所有 phases）
- **向後兼容性**: Factor Graph 成功率維持 100%（不得退化）
