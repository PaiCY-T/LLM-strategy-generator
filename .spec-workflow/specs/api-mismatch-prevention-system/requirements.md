# Requirements - API Mismatch Prevention System (Phase 5)

## 1. Overview

### 1.1 Purpose
建立三層防禦系統以系統性預防API不匹配錯誤，解決Phase 1-4重構後pilot測試中發現的property/method混淆問題。此系統透過typing.Protocol介面契約、mypy靜態類型檢查、以及整合測試，在開發階段就攔截API錯誤。

### 1.2 Problem Statement
**Current Issues** (Pilot測試發現8個API錯誤):
- Error #5: `ChampionTracker.get_champion()` 不存在 (實際是 `.champion` property) - 6處
- Error #6: `ErrorClassifier.classify_single()` 不存在 (實際是 `.classify_error()`) - 1處
- Error #7: `IterationHistory.save_record()` 不存在 (實際是 `.save()`) - 1處

**Root Causes**:
1. **無強制介面契約**: 元件獨立演化，無正式API規範
2. **無靜態類型檢查**: Python動態類型允許錯誤到runtime才顯現
3. **整合測試覆蓋缺口**: 單元測試使用mock，隱藏實際API不匹配

**Impact**:
- 所有30次pilot迭代失敗
- 開發時間浪費在runtime錯誤修復
- 生產環境潛在風險

### 1.3 Core Philosophy
- **Prevention > Detection**: 在開發階段攔截，而非runtime發現
- **Static > Dynamic**: 靜態分析優於動態測試
- **Pragmatic > Perfect**: 避免過度工程化 (personal trading system)
- **Gradual > Big Bang**: 漸進式導入，不干擾現有開發流程

### 1.4 Success Criteria
**Quantitative**:
- ✅ mypy --strict 100% 通過在Phase 1-4模組
- ✅ Pilot測試30次迭代零API錯誤
- ✅ 整合測試覆蓋率≥80% (元件邊界)
- ✅ CI/CD pipeline執行時間<2分鐘

**Qualitative**:
- ✅ 介面契約有文件和範例
- ✅ 開發工作流包含類型檢查
- ✅ Pre-commit hooks防止類型錯誤進入repository

---

## 2. Functional Requirements

### FR-1: typing.Protocol Interface Contracts
**Priority**: P0 - Critical
**User Story**: 作為開發者，我需要明確的介面契約來理解元件API

**Acceptance Criteria**:
- AC-1.1: 定義 `IChampionTracker` Protocol (`.champion` property, `.update_champion()` method)
- AC-1.2: 定義 `IIterationHistory` Protocol (`.save()`, `.get_all()`, `.get_by_iteration()`)
- AC-1.3: 定義 `IErrorClassifier` Protocol (`.classify_error()`)
- AC-1.4: 使用 `@property` decorator清楚標記property vs method
- AC-1.5: Protocol包含完整type hints (參數、返回值)
- AC-1.6: 每個Protocol有docstring說明用途和範例

**Technical Notes**:
- 使用 `typing.Protocol` (結構性類型，非名義性繼承)
- 檔案位置: `src/learning/interfaces.py`
- 不需修改現有類別繼承 (Protocol自動驗證)

**Rationale** (Gemini 2.5 Pro recommendation):
- 較ABC更少侵入性 (無需修改現有類別)
- 更Pythonic (擁抱duck typing + 靜態安全)
- 符合「避免過度工程化」原則

---

### FR-2: Static Type Checking with mypy
**Priority**: P0 - Critical
**User Story**: 作為開發者，我需要在commit前發現類型錯誤

**Acceptance Criteria**:
- AC-2.1: 配置 `mypy.ini` 使用漸進式嚴格模式
  - Phase 1-4模組: `strict = True` (完整檢查)
  - Legacy模組: `warn_unused_ignores = False` (只警告)
- AC-2.2: mypy檢查涵蓋:
  - Property vs method正確使用
  - 參數名稱匹配
  - 返回類型匹配
  - Optional類型處理
- AC-2.3: 支援gradual typing (允許現有代碼逐步添加type hints)
- AC-2.4: 提供清楚錯誤訊息和修正建議

**Technical Notes**:
```ini
[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
strict = True

[mypy-src.learning.*]
strict = True

[mypy-src.backtest.*]
warn_unused_ignores = False
```

---

### FR-3: CI/CD Pipeline Integration
**Priority**: P0 - Critical
**User Story**: 作為團隊，我們需要自動化類型檢查防止錯誤進入main branch

**Acceptance Criteria**:
- AC-3.1: GitHub Actions workflow執行mypy (每次push/PR)
- AC-3.2: mypy失敗 → CI失敗 → block merge
- AC-3.3: Pipeline執行時間<2分鐘
- AC-3.4: Caching策略加速重複執行
- AC-3.5: 提供清楚失敗報告和修正指引

**Technical Notes**:
- 檔案位置: `.github/workflows/ci.yml`
- 包含: mypy + pytest + coverage report
- 平行執行: mypy檢查 & pytest測試

---

### FR-4: Pre-commit Hooks
**Priority**: P1 - High
**User Story**: 作為開發者，我想在commit前就發現類型錯誤

**Acceptance Criteria**:
- AC-4.1: 配置 `.pre-commit-config.yaml` 執行mypy
- AC-4.2: 類型錯誤 → block commit (可bypass但有警告)
- AC-4.3: Hooks執行時間<10秒
- AC-4.4: 提供bypass指令 (`--no-verify`) 用於WIP commits

**Technical Notes**:
```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        args: [--strict, --config-file=mypy.ini]
        additional_dependencies: [...]
```

---

### FR-5: Integration Testing Suite
**Priority**: P0 - Critical
**User Story**: 作為開發者，我需要驗證元件實際整合時API使用正確

**Acceptance Criteria**:
- AC-5.1: 整合測試使用真實元件實例 (不使用mock)
- AC-5.2: 測試ChampionTracker整合:
  - ✅ 驗證 `.champion` property存取
  - ✅ 驗證 `.update_champion()` method呼叫
  - ✅ 驗證與IterationHistory互動
- AC-5.3: 測試IterationHistory整合:
  - ✅ 驗證 `.save(record)` method
  - ✅ 驗證 `.get_all()` 返回正確類型
- AC-5.4: 測試LearningLoop完整迭代:
  - ✅ 驗證所有元件協同工作
  - ✅ 驗證數據流經各層
- AC-5.5: 覆蓋率≥80% for component boundaries

**Technical Notes**:
- 檔案位置: `tests/integration/`
- 測試檔案:
  - `test_champion_tracker_integration.py`
  - `test_iteration_history_integration.py`
  - `test_learning_loop_integration.py`
  - `test_component_interaction.py`

**Rationale** (Gemini recommendation):
- 重點測試關鍵workflow而非追求raw coverage數字
- 優先驗證主要成功路徑和critical failure modes

---

## 3. Non-Functional Requirements

### NFR-1: Performance
- **NFR-1.1**: CI/CD pipeline總執行時間<2分鐘
- **NFR-1.2**: mypy檢查時間<30秒 (使用cache)
- **NFR-1.3**: Pre-commit hooks執行時間<10秒
- **NFR-1.4**: 整合測試套件執行時間<1分鐘

### NFR-2: Maintainability
- **NFR-2.1**: 所有Protocol有完整docstring和使用範例
- **NFR-2.2**: mypy.ini有註解說明各設定用途
- **NFR-2.3**: CI/CD workflow有step-by-step註解
- **NFR-2.4**: 整合測試有清楚命名和文檔

### NFR-3: Developer Experience
- **NFR-3.1**: 清楚錯誤訊息指出問題和修正方式
- **NFR-3.2**: 開發者指南文檔化工作流程
- **NFR-3.3**: 支援本地開發環境快速迭代
- **NFR-3.4**: Pre-commit hooks可選擇性bypass (WIP commits)

### NFR-4: Compatibility
- **NFR-4.1**: Python 3.11+ 支援
- **NFR-4.2**: 不影響Phase 1-4已有功能
- **NFR-4.3**: 向後相容現有測試套件
- **NFR-4.4**: 支援WSL2開發環境

---

## 4. Constraints

### 4.1 Technical Constraints
- **TC-1**: 使用typing.Protocol而非abc.ABC (減少侵入性)
- **TC-2**: 漸進式typing (Phase 1-4 strict, legacy warnings)
- **TC-3**: 不修改Phase 1-4核心邏輯 (only add type hints if needed)
- **TC-4**: CI/CD使用GitHub Actions (現有基礎設施)

### 4.2 Resource Constraints
- **RC-1**: 實施時間≤3週 (56小時)
- **RC-2**: 單人開發 (避免複雜協作流程)
- **RC-3**: Personal project (避免企業級過度工程)
- **RC-4**: Weekly/monthly trading cycles (可容忍適度中斷)

### 4.3 Process Constraints
- **PC-1**: 必須通過Phase 1-4所有111個測試
- **PC-2**: 不影響現有開發workflow (optional pre-commit)
- **PC-3**: 文檔使用中文 (開發者母語)
- **PC-4**: 遵循現有代碼風格

---

## 5. Dependencies

### 5.1 Upstream Dependencies (Must完成才能開始)
- ✅ Phase 1-4 Architecture Refactoring (已完成, 111/111 tests passing)
- ✅ Pilot測試錯誤分析 (已完成, 8個API錯誤已識別並修復)

### 5.2 External Dependencies (需安裝)
- `mypy>=1.11.0` (靜態類型檢查器)
- `pre-commit>=3.5.0` (pre-commit framework)
- `pytest>=8.0.0` (測試框架, 已有)
- `pytest-cov>=5.0.0` (coverage報告)

### 5.3 Internal Dependencies (Phase 5內部)
- Phase 5A (CI/CD Pipeline) → Phase 5B (Interfaces)
- Phase 5B (Interfaces) → Phase 5C (Integration Tests)

---

## 6. Risk Assessment

### High Risks
**R1: mypy strict reveals 100+ type errors in legacy code**
- **Probability**: High (70%)
- **Impact**: Critical (blocks development)
- **Mitigation**: 漸進式typing (strict on Phase 1-4, warnings on legacy)
- **Contingency**: 2h buffer per new issue discovered

**R2: Integration tests reveal new architectural issues**
- **Probability**: Medium (40%)
- **Impact**: High (requires refactoring)
- **Mitigation**: Go/no-go decision at Milestone 2
- **Contingency**: Escalate to architectural review

### Medium Risks
**R3: CI/CD pipeline performance overhead >2min**
- **Probability**: Medium (50%)
- **Impact**: Medium (slows development)
- **Mitigation**: Caching dependencies, parallel test execution
- **Contingency**: Optimize slow steps, split workflows

**R4: Interface design requires multiple iterations**
- **Probability**: Medium (40%)
- **Impact**: Medium (延遲timeline)
- **Mitigation**: Start with 3 core interfaces, expand incrementally
- **Contingency**: Buffer 4h for design iteration

**R5: Process Fatigue & Maintenance Overhead** (Gemini identified)
- **Probability**: Medium (50%)
- **Impact**: Medium (reduces iteration speed)
- **Mitigation**:
  - Pragmatic strictness (disable specific flags if excessive pain)
  - Focus on critical-path testing (not raw coverage %)
  - Automate dependency updates (Dependabot)
- **Contingency**: Re-evaluate strictness levels per module

### Low Risks
**R6: Pre-commit hooks rejected by developers**
- **Probability**: Low (20%)
- **Impact**: Low (optional feature)
- **Mitigation**: Clear documentation, easy bypass for WIP
- **Contingency**: Make fully optional

---

## 7. Acceptance Criteria (Overall)

### Phase 5A: CI/CD Pipeline & Enforcement
- [ ] `mypy.ini` configured with gradual typing strategy
- [ ] GitHub Actions workflow operational (mypy + pytest + coverage)
- [ ] Pre-commit hooks configured and documented
- [ ] CI/CD pipeline validated with test commits
- [ ] Developer workflow guide documented
- [ ] **Milestone 1**: Zero type errors on Phase 1-4, CI/CD operational

### Phase 5B: Interface Contracts
- [ ] `src/learning/interfaces.py` created with 3 Protocols
- [ ] `IChampionTracker` Protocol implemented with property annotations
- [ ] `IIterationHistory` and `IErrorClassifier` Protocols implemented
- [ ] All Protocols have complete docstrings and examples
- [ ] mypy strict compliance validated on new interfaces
- [ ] **Milestone 2**: All Phase 1-4 components comply with Protocols

### Phase 5C: Integration Test Suite
- [ ] Integration test strategy documented
- [ ] ChampionTracker integration tests implemented (4h)
- [ ] IterationHistory integration tests implemented (4h)
- [ ] Component interaction tests implemented (6h)
- [ ] End-to-end iteration flow test implemented (5h)
- [ ] ≥80% integration test coverage achieved and validated
- [ ] **Milestone 3**: Zero API mismatches in CI, production-ready

### Final Validation
- [ ] Pilot validation test runs 30 iterations with ZERO API errors
- [ ] mypy --strict passes 100% on Phase 1-4 modules
- [ ] All 111 existing tests still pass
- [ ] CI/CD pipeline execution time <2 minutes
- [ ] Documentation complete (CI/CD guide + Interface guide + Test strategy)

---

## 8. Out of Scope

以下項目**不在Phase 5範圍內**:

### 8.1 Not Included
- ❌ Runtime type checking (beartype, typeguard) - 增加overhead
- ❌ 100% type coverage on legacy code - 過度工程化
- ❌ Abstract Base Classes (ABC) - 使用Protocol instead
- ❌ 自動類型推斷工具 (MonkeyType, PyAnnotate) - 額外複雜度
- ❌ UI/Web dashboard for CI results - 非必要
- ❌ 完整重寫legacy模組 - 超出scope

### 8.2 Future Considerations (Phase 6+)
- Phase 6可能: 逐步提升legacy模組類型覆蓋率
- Phase 6可能: 添加property-based testing (Hypothesis)
- Phase 7可能: Performance profiling integration
- Phase 7可能: 自動化API compatibility monitoring

---

## 9. Success Metrics

### 9.1 Quantitative Metrics
| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| API Mismatch Errors | 8 (pilot) | 0 | Pilot validation test |
| mypy Strict Coverage | 0% | 100% (Phase 1-4) | mypy report |
| Integration Test Coverage | 0% | ≥80% | pytest-cov |
| CI/CD Execution Time | N/A | <2min | GitHub Actions logs |
| Type Error Prevention | 0 | 100% | Pre-commit hooks |

### 9.2 Qualitative Metrics
| Aspect | Evaluation Criteria |
|--------|-------------------|
| Developer Experience | Clear error messages, easy setup, fast feedback |
| Code Quality | Self-documenting interfaces, consistent patterns |
| Maintainability | Documented workflows, easy troubleshooting |
| Stability | Zero regressions in existing functionality |

---

## 10. Appendix

### 10.1 Error Catalog (Reference)
已修復的8個API錯誤 (作為測試案例參考):

**Error #5: ChampionTracker API (6 locations)**
```python
# WRONG
champion = self.champion_tracker.get_champion()  # ❌ Method不存在

# CORRECT
champion = self.champion_tracker.champion  # ✅ Property access
```

**Error #6: ErrorClassifier API (1 location)**
```python
# WRONG
result = self.error_classifier.classify_single(metrics)  # ❌ Method renamed

# CORRECT
result = self.error_classifier.classify_error(error_type, error_msg)  # ✅
```

**Error #7: IterationHistory API (1 location)**
```python
# WRONG
self.history.save_record(record)  # ❌ Method renamed

# CORRECT
self.history.save(record)  # ✅
```

### 10.2 Terminology
- **Protocol**: typing.Protocol, 結構性類型檢查
- **ABC**: Abstract Base Class, 名義性繼承 (本專案不使用)
- **Gradual Typing**: 漸進式加入type hints
- **Strict Mode**: mypy最嚴格檢查模式
- **Integration Test**: 測試真實元件互動 (no mocks)

### 10.3 References
- PEP 544: Protocols (Structural Subtyping)
- mypy Documentation: https://mypy.readthedocs.io/
- Gemini 2.5 Pro Review: Conditional Approval (typing.Protocol recommendation)
- Phase 1-4 Architecture: Exception hierarchy, Pydantic models, Strategy Pattern
