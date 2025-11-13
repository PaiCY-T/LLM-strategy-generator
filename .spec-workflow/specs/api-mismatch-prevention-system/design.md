# Design Document - API Mismatch Prevention System (Phase 5)

## 1. Overview

### 1.1 Design Philosophy
本設計採用**三層防禦系統** (Three-Layer Defense)，在不同階段攔截API錯誤：
1. **Layer 1 (Compile Time)**: typing.Protocol介面契約定義API規範
2. **Layer 2 (Pre-Commit/CI)**: mypy靜態類型檢查驗證API使用正確性
3. **Layer 3 (Test Time)**: Integration tests驗證真實元件互動

### 1.2 Key Design Decisions

**Decision 1: typing.Protocol over abc.ABC**
- **Rationale**: 結構性類型 (structural typing) vs 名義性繼承 (nominal inheritance)
- **Benefits**:
  - 無需修改現有類別 (不侵入繼承樹)
  - 更Pythonic (duck typing + static safety)
  - 符合「避免過度工程化」原則
- **Trade-off**: 失去runtime `isinstance()` check (可接受，因為重點在static analysis)
- **Source**: Gemini 2.5 Pro review recommendation

**Decision 2: Gradual Typing Strategy**
- **Rationale**: 平衡嚴格度與實用性
- **Implementation**:
  - Phase 1-4模組: `strict = True` (100% enforcement)
  - Legacy模組: `warn_unused_ignores = False` (只警告)
- **Benefits**: 不阻塞現有開發，逐步提升品質

**Decision 3: Critical-Path Integration Testing**
- **Rationale**: 測試關鍵workflow而非追求raw coverage %
- **Focus**: 主要成功路徑 + critical failure modes
- **Target**: 80% coverage but prioritize important interactions
- **Source**: Gemini recommendation on outcome-focused testing

---

## 2. Architecture

### 2.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Developer Workflow                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Interface Contracts (src/learning/interfaces.py)  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  IChampionTracker Protocol                             │ │
│  │  - champion: IterationRecord @property                 │ │
│  │  - update_champion(record, force) -> bool              │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  IIterationHistory Protocol                            │ │
│  │  - save(record) -> None                                │ │
│  │  - get_all() -> List[IterationRecord]                  │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  IErrorClassifier Protocol                             │ │
│  │  - classify_error(type, msg) -> ErrorCategory          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Static Type Checking (mypy + CI/CD)               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Pre-Commit Hook (local)                               │ │
│  │  - mypy --strict --config-file=mypy.ini                │ │
│  │  - Fast feedback (<10s)                                │ │
│  │  - Bypass option for WIP commits                       │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  GitHub Actions CI (remote)                            │ │
│  │  - mypy + pytest + coverage                            │ │
│  │  - Block merge if type errors                          │ │
│  │  - Execution time <2min                                │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Integration Testing (tests/integration/)          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  test_champion_tracker_integration.py                  │ │
│  │  - Test .champion property access                      │ │
│  │  - Test .update_champion() method                      │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  test_iteration_history_integration.py                 │ │
│  │  - Test .save(record) method                           │ │
│  │  - Test .get_all() return type                         │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  test_learning_loop_integration.py                     │ │
│  │  - Test full iteration lifecycle                       │ │
│  │  - Test component orchestration                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Three-Layer Defense Mechanism

| Layer | Stage | Detection Method | Error Prevention | Enforcement |
|-------|-------|------------------|------------------|-------------|
| **Layer 1** | Design Time | Protocol definition | API契約明確化 | IDE autocomplete |
| **Layer 2** | Pre-Commit/CI | mypy static analysis | Property/method confusion | Blocking (CI fail) |
| **Layer 3** | Test Time | Integration tests | Runtime behavior validation | Blocking (test fail) |

**Depth-in-Defense Benefits**:
- Layer 1 failure → IDE warns (immediate feedback)
- Layer 2 failure → Pre-commit blocks or CI fails (prevent merge)
- Layer 3 failure → Tests catch dynamic behavior issues (safety net)

---

## 3. Components and Interfaces

### 3.1 Interface Contracts (Layer 1)

**File**: `src/learning/interfaces.py`

#### 3.1.1 IChampionTracker Protocol

```python
from typing import Protocol, Optional
from src.learning.iteration_history import IterationRecord

class IChampionTracker(Protocol):
    """Protocol for champion strategy tracking.

    Defines the contract for components that manage the best-performing strategy.
    This is a READ-ONLY property contract for champion access.

    Example:
        >>> tracker: IChampionTracker = ChampionTracker(...)
        >>> current_champion = tracker.champion  # ✅ Property access
        >>> current_champion = tracker.get_champion()  # ❌ Type error
    """

    @property
    def champion(self) -> Optional[IterationRecord]:
        """Get current champion strategy (READ-ONLY property).

        Returns:
            Current best strategy or None if no champion yet.

        Note:
            This is a PROPERTY, not a method. Access with:
            `tracker.champion` NOT `tracker.get_champion()`
        """
        ...

    def update_champion(
        self,
        record: IterationRecord,
        force: bool = False
    ) -> bool:
        """Attempt to update champion with new record.

        Args:
            record: New iteration record to compare
            force: If True, override current champion regardless of metrics

        Returns:
            True if champion was updated, False otherwise
        """
        ...
```

**Key Design Points**:
- `champion` is `@property` (NOT method) - addresses Error #5
- Explicit docstring warning about property vs method
- Usage example in docstring prevents confusion
- Type hints for all parameters and returns

#### 3.1.2 IIterationHistory Protocol

```python
from typing import Protocol, List, Optional
from src.learning.iteration_history import IterationRecord

class IIterationHistory(Protocol):
    """Protocol for iteration persistence.

    Defines the contract for components that store and retrieve
    iteration records across learning loop executions.

    Example:
        >>> history: IIterationHistory = IterationHistory(...)
        >>> history.save(record)  # ✅ Correct method name
        >>> history.save_record(record)  # ❌ Type error
    """

    def save(self, record: IterationRecord) -> None:
        """Persist iteration record to storage.

        Args:
            record: IterationRecord to save

        Note:
            Method name is `save`, NOT `save_record` (historical rename)
        """
        ...

    def get_all(self) -> List[IterationRecord]:
        """Retrieve all stored iteration records.

        Returns:
            List of all iteration records, ordered by iteration_num
        """
        ...

    def get_by_iteration(self, iteration_num: int) -> Optional[IterationRecord]:
        """Retrieve specific iteration record.

        Args:
            iteration_num: Iteration number to retrieve

        Returns:
            IterationRecord if found, None otherwise
        """
        ...
```

**Key Design Points**:
- `save(record)` not `save_record()` - addresses Error #7
- Explicit note about historical method rename
- Complete method signature with type hints

#### 3.1.3 IErrorClassifier Protocol

```python
from typing import Protocol
from src.backtest.error_classifier import ErrorCategory

class IErrorClassifier(Protocol):
    """Protocol for error classification.

    Defines the contract for components that categorize errors
    into actionable categories (SYNTAX, TIMEOUT, RUNTIME, etc.).

    Example:
        >>> classifier: IErrorClassifier = ErrorClassifier()
        >>> category = classifier.classify_error("SyntaxError", "invalid syntax")  # ✅
        >>> category = classifier.classify_single(metrics)  # ❌ Wrong classifier
    """

    def classify_error(
        self,
        error_type: str,
        error_message: str
    ) -> ErrorCategory:
        """Classify error into category for feedback generation.

        Args:
            error_type: Exception type name (e.g., "SyntaxError")
            error_message: Error message text

        Returns:
            ErrorCategory enum value

        Note:
            This is ErrorClassifier.classify_error(), NOT
            SuccessClassifier.classify_single() (different classifier)
        """
        ...
```

**Key Design Points**:
- `classify_error(type, msg)` not `classify_single(metrics)` - addresses Error #6
- Docstring clarifies difference between ErrorClassifier vs SuccessClassifier
- Prevents cross-classifier confusion

### 3.2 Concrete Implementations

**No Changes Required** to existing classes:
- `ChampionTracker` already implements `IChampionTracker` (structural typing)
- `IterationHistory` already implements `IIterationHistory`
- `ErrorClassifier` already implements `IErrorClassifier`

**Type Checker Validation**:
```python
# mypy automatically validates without explicit inheritance:
tracker = ChampionTracker(...)  # Concrete class
history: IIterationHistory = IterationHistory(...)  # Protocol type hint

# mypy verifies IterationHistory has:
# - save(record: IterationRecord) -> None
# - get_all() -> List[IterationRecord]
# - get_by_iteration(int) -> Optional[IterationRecord]
```

### 3.3 Component Interaction Flow

```
LearningLoop (Orchestrator)
    │
    ├─> IChampionTracker (champion tracker instance)
    │   └─> .champion (property access) ✅
    │   └─> .update_champion(record) ✅
    │
    ├─> IIterationHistory (history instance)
    │   └─> .save(record) ✅
    │   └─> .get_all() ✅
    │
    └─> IterationExecutor
        └─> IErrorClassifier (error classifier instance)
            └─> .classify_error(type, msg) ✅
```

---

## 4. Static Type Checking Configuration (Layer 2)

### 4.1 mypy Configuration (`mypy.ini`)

```ini
[mypy]
# Global settings
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
strict = True

# Phase 1-4 modules: Full strict enforcement
[mypy-src.learning.champion_tracker]
strict = True
disallow_untyped_defs = True
warn_return_any = True

[mypy-src.learning.iteration_history]
strict = True
disallow_untyped_defs = True

[mypy-src.learning.iteration_executor]
strict = True
disallow_untyped_defs = True

[mypy-src.learning.learning_loop]
strict = True
disallow_untyped_defs = True

[mypy-src.learning.interfaces]
strict = True
disallow_untyped_defs = True

# Legacy modules: Warnings only (gradual migration)
[mypy-src.backtest.*]
strict = False
warn_unused_ignores = False
warn_return_any = False

# Third-party libraries without stubs
[mypy-finlab.*]
ignore_missing_imports = True

[mypy-anthropic.*]
ignore_missing_imports = True
```

**Configuration Rationale**:
- **Strict on Phase 1-4**: Enforces complete type safety on refactored modules
- **Lenient on Legacy**: Allows gradual improvement without blocking development
- **Third-party Ignore**: Handles external dependencies without type stubs

### 4.2 Pre-Commit Hook Configuration (`.pre-commit-config.yaml`)

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        name: mypy type checking
        args:
          - --strict
          - --config-file=mypy.ini
        additional_dependencies:
          - types-requests
          - types-PyYAML
        pass_filenames: false
        always_run: false
        stages: [commit]
        verbose: true
```

**Hook Behavior**:
- Runs on `git commit` (not push)
- Can bypass with `git commit --no-verify` (WIP commits)
- Shows detailed error messages
- Fast execution (<10s) using mypy daemon

### 4.3 GitHub Actions CI Workflow (`.github/workflows/ci.yml`)

```yaml
name: CI - Type Check & Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  type-check-and-test:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install mypy pytest pytest-cov

      - name: Run mypy type checking
        run: |
          echo "::group::mypy type checking"
          mypy src/learning/ --config-file=mypy.ini --show-error-codes
          echo "::endgroup::"

      - name: Run pytest with coverage
        run: |
          echo "::group::pytest execution"
          pytest tests/ -v --cov=src --cov-report=term --cov-report=html
          echo "::endgroup::"

      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: htmlcov/
```

**CI Features**:
- Parallel execution (mypy and pytest can run concurrently)
- Dependency caching (speeds up subsequent runs)
- Detailed error reporting (show-error-codes)
- Coverage reports as artifacts
- Timeout protection (10 minutes max)

### 4.4 Error Classification and Handling

**mypy Error Categories**:

| Error Code | Category | Example | Fix Strategy |
|------------|----------|---------|--------------|
| `attr-defined` | Attribute access | `obj.get_champion()` on property | Change to `obj.champion` |
| `call-arg` | Function call | `save_record(x)` vs `save(x)` | Rename method call |
| `assignment` | Type mismatch | `str = int` | Fix type annotation |
| `return-value` | Return type | `-> int` returns `None` | Add return or fix annotation |

**Error Message Enhancement**:
```python
# Example mypy error for property/method confusion:
# error: "ChampionTracker" has no attribute "get_champion"  [attr-defined]
#        Did you mean: "champion"?
#        Note: If this is supposed to be a method, use .champion property instead
```

---

## 5. Integration Testing Strategy (Layer 3)

### 5.1 Testing Pyramid

```
         ┌─────────────┐
         │   E2E Tests │  (1 test - full iteration loop)
         └─────────────┘
       ┌───────────────────┐
       │ Integration Tests │  (4 test files - component boundaries)
       └───────────────────┘
   ┌─────────────────────────────┐
   │      Unit Tests (111)       │  (existing - keep as is)
   └─────────────────────────────┘
```

**Test Distribution**:
- Unit Tests: 111 existing (no changes)
- Integration Tests: ~20 new tests (component interactions)
- E2E Test: 1 comprehensive test (full workflow)

### 5.2 Integration Test Files

#### 5.2.1 `tests/integration/test_champion_tracker_integration.py`

```python
"""Integration tests for ChampionTracker API compliance.

Validates:
- .champion property access (not method)
- .update_champion() method signature
- Interaction with IterationHistory
"""

def test_champion_property_access():
    """Test champion is accessed as property, not method."""
    tracker = ChampionTracker(...)

    # ✅ Should work - property access
    current_champion = tracker.champion
    assert current_champion is None or isinstance(current_champion, IterationRecord)

    # ❌ Should fail at type-check time (mypy error)
    # current_champion = tracker.get_champion()  # AttributeError

def test_update_champion_signature():
    """Test update_champion method accepts correct parameters."""
    tracker = ChampionTracker(...)
    record = IterationRecord(...)

    # ✅ Should work - correct signature
    updated = tracker.update_champion(record, force=False)
    assert isinstance(updated, bool)
```

#### 5.2.2 `tests/integration/test_iteration_history_integration.py`

```python
"""Integration tests for IterationHistory API compliance.

Validates:
- .save(record) method (not save_record)
- .get_all() return type
- Persistence across instances
"""

def test_save_method_signature():
    """Test save method uses correct name and signature."""
    history = IterationHistory(filepath="test.jsonl")
    record = IterationRecord(...)

    # ✅ Should work - correct method name
    history.save(record)

    # ❌ Should fail at type-check time
    # history.save_record(record)  # AttributeError

def test_get_all_return_type():
    """Test get_all returns List[IterationRecord]."""
    history = IterationHistory(filepath="test.jsonl")

    # ✅ Type checker validates return type
    records: List[IterationRecord] = history.get_all()
    assert isinstance(records, list)
```

#### 5.2.3 `tests/integration/test_component_interaction.py`

```python
"""Integration tests for multi-component interactions.

Validates:
- LearningLoop + ChampionTracker + IterationHistory
- IterationExecutor + ErrorClassifier
- Data flow between components
"""

def test_learning_loop_component_integration():
    """Test LearningLoop correctly uses all component APIs."""
    config = LearningConfig(...)
    loop = LearningLoop(config)

    # Validate component initialization
    assert loop.champion_tracker.champion is None  # ✅ Property access
    assert len(loop.history.get_all()) == 0  # ✅ Method call

    # Run single iteration
    # This validates entire component interaction chain
    loop.run()  # Should complete without AttributeError
```

#### 5.2.4 `tests/integration/test_learning_loop_integration.py`

```python
"""End-to-end integration test for complete iteration lifecycle.

Validates:
- Full iteration execution
- All component APIs used correctly
- No runtime AttributeErrors
"""

def test_full_iteration_lifecycle():
    """Test complete iteration from generation to champion update."""
    # Setup (minimal config for fast execution)
    config = LearningConfig(
        max_iterations=1,
        use_factor_graph=True,  # Fast generation
        timeout_seconds=30
    )

    loop = LearningLoop(config)
    loop.run()

    # Validate all APIs were used correctly
    # (If any API mismatch, this test would fail at runtime)
    champion = loop.champion_tracker.champion  # ✅ Property
    records = loop.history.get_all()  # ✅ Method

    assert len(records) == 1
    assert records[0].iteration_num == 0
```

### 5.3 Test Execution Strategy

**Local Development**:
```bash
# Run only integration tests (fast)
pytest tests/integration/ -v

# Run integration tests with coverage
pytest tests/integration/ --cov=src/learning --cov-report=term

# Run all tests (unit + integration)
pytest tests/ -v
```

**CI/CD Execution**:
```yaml
# GitHub Actions runs both sequentially
- name: Run unit tests
  run: pytest tests/ --ignore=tests/integration/ -v

- name: Run integration tests
  run: pytest tests/integration/ -v --cov=src/learning
```

### 5.4 Coverage Targets

| Test Type | Target Coverage | Rationale |
|-----------|----------------|-----------|
| Unit Tests | 90%+ (existing) | Individual component logic |
| Integration Tests | 80%+ (new) | Component boundary interactions |
| E2E Test | Critical path | Full workflow validation |

**Critical Path Definition**:
- Strategy generation (LLM or Factor Graph)
- Backtest execution
- Metrics extraction
- Champion comparison and update
- History persistence

---

## 6. Data Models

### 6.1 Protocol Type Definitions

All Protocols use existing data models (no new types needed):

| Protocol | Uses Types |
|----------|-----------|
| `IChampionTracker` | `IterationRecord` (existing) |
| `IIterationHistory` | `IterationRecord`, `List[IterationRecord]` |
| `IErrorClassifier` | `ErrorCategory` (existing enum) |

### 6.2 Type Alias Definitions (for clarity)

```python
# src/learning/interfaces.py

from typing import TypeAlias, Optional, List
from src.learning.iteration_history import IterationRecord
from src.backtest.error_classifier import ErrorCategory

# Type aliases for Protocol signatures
ChampionRecord: TypeAlias = Optional[IterationRecord]
RecordList: TypeAlias = List[IterationRecord]
ErrorType: TypeAlias = str
ErrorMessage: TypeAlias = str
```

---

## 7. Error Handling

### 7.1 mypy Error Handling Workflow

```
Developer commits code
    │
    ▼
Pre-commit hook runs mypy
    │
    ├─> No errors ✅
    │   └─> Commit succeeds
    │
    └─> Type errors ❌
        └─> Display error + fix suggestion
            └─> Developer fixes or bypasses with --no-verify
```

### 7.2 CI Error Handling Workflow

```
PR created/updated
    │
    ▼
GitHub Actions runs CI
    │
    ├─> mypy + pytest pass ✅
    │   └─> Allow merge
    │
    └─> mypy or pytest fail ❌
        └─> Block merge
            └─> Display error details in PR comment
                └─> Developer fixes and pushes
```

### 7.3 Error Recovery Strategies

**mypy Error Types & Fixes**:

1. **Property/Method Confusion** (attr-defined)
   ```python
   # Error: "ChampionTracker" has no attribute "get_champion"
   # Fix: Change to property access
   champion = tracker.champion  # NOT tracker.get_champion()
   ```

2. **Method Rename** (attr-defined)
   ```python
   # Error: "IterationHistory" has no attribute "save_record"
   # Fix: Use correct method name
   history.save(record)  # NOT history.save_record(record)
   ```

3. **Wrong Classifier** (attr-defined)
   ```python
   # Error: "ErrorClassifier" has no attribute "classify_single"
   # Fix: Use correct classifier method
   error_classifier.classify_error(type, msg)  # NOT classify_single(metrics)
   ```

### 7.4 Gradual Migration Error Handling

**Legacy Module Warnings** (not errors):
```bash
# mypy output for legacy modules (non-blocking)
src/backtest/reporter.py:45: note: By default the bodies of untyped functions are not checked
src/backtest/reporter.py:120: note: Consider using --check-untyped-defs
```

**Migration Strategy**:
1. Phase 5: Warnings only (no blocking)
2. Phase 6: Gradually add type hints to high-value legacy modules
3. Phase 7: Enable strict mode on migrated modules

---

## 8. Testing Strategy

### 8.1 Test Coverage Goals

**Phase 5A**: 0% → 0% (setup only, no new tests)
**Phase 5B**: 0% → 60% (interface validation tests)
**Phase 5C**: 60% → 80%+ (full integration coverage)

### 8.2 Test Execution Performance

| Test Suite | Target Time | Optimization |
|------------|-------------|--------------|
| Unit Tests (111) | <30s | Parallel execution |
| Integration Tests (20) | <45s | Fast config, real components |
| E2E Test (1) | <60s | Minimal iterations |
| **Total** | **<2min** | CI pipeline caching |

### 8.3 Test Quality Metrics

**Effectiveness Metrics**:
- ✅ Zero API mismatch errors in pilot test (30 iterations)
- ✅ 100% of known error patterns prevented (8/8 errors)
- ✅ mypy catches errors before runtime (measured by CI failure rate)

**Efficiency Metrics**:
- ✅ Pre-commit hook execution <10s
- ✅ CI pipeline execution <2min
- ✅ Integration test suite <45s

### 8.4 Continuous Monitoring

**CI Dashboard Metrics** (GitHub Actions):
- mypy error trend (should be 0 on Phase 1-4)
- Integration test pass rate (target 100%)
- Coverage percentage (target 80%+)
- Pipeline execution time (target <2min)

---

## 9. Deployment and Rollout

### 9.1 Phase 5A: Infrastructure Setup (Week 1)
1. Configure `mypy.ini` (gradual typing)
2. Setup GitHub Actions workflow
3. Configure pre-commit hooks
4. Validate with test commits
5. Document developer workflow

### 9.2 Phase 5B: Interface Contracts (Week 2)
1. Create `src/learning/interfaces.py`
2. Define IChampionTracker Protocol
3. Define IIterationHistory Protocol
4. Define IErrorClassifier Protocol
5. Validate mypy compliance

### 9.3 Phase 5C: Integration Testing (Week 3)
1. Implement ChampionTracker integration tests
2. Implement IterationHistory integration tests
3. Implement component interaction tests
4. Implement E2E iteration test
5. Validate 80%+ coverage

### 9.4 Rollout Checkpoints

**Milestone 1 (End of Week 1)**:
- ✅ Zero type errors on Phase 1-4 modules
- ✅ CI/CD pipeline operational

**Milestone 2 (End of Week 2)**:
- ✅ All Phase 1-4 components implement Protocols
- ✅ mypy strict passes

**Milestone 3 (End of Week 3)**:
- ✅ 80% integration coverage
- ✅ Zero API mismatches in pilot test
- ✅ Production ready

---

## 10. Documentation and Training

### 10.1 Developer Documentation

**CI/CD Workflow Guide** (`docs/ci-cd-workflow.md`):
- Pre-commit hook usage
- Local mypy execution
- CI pipeline interpretation
- Error resolution examples

**Interface Contract Guide** (`docs/interface-contracts.md`):
- Protocol vs ABC explanation
- Property vs method patterns
- Usage examples for each Protocol
- Common mistakes and fixes

**Integration Testing Strategy** (`docs/integration-testing.md`):
- Test pyramid explanation
- Writing integration tests
- Mock vs real components
- Coverage interpretation

### 10.2 Quick Reference

**mypy Quick Commands**:
```bash
# Check specific module
mypy src/learning/iteration_executor.py --config-file=mypy.ini

# Check all Phase 1-4 modules
mypy src/learning/ --config-file=mypy.ini

# Check with detailed error context
mypy src/learning/ --config-file=mypy.ini --show-error-context
```

**Pre-commit Quick Commands**:
```bash
# Run pre-commit checks manually
pre-commit run --all-files

# Bypass pre-commit for WIP
git commit --no-verify -m "WIP: testing changes"

# Update pre-commit hooks
pre-commit autoupdate
```

---

## 11. Appendix

### 11.1 Design Trade-offs

| Decision | Benefit | Cost | Justification |
|----------|---------|------|---------------|
| Protocol over ABC | Less invasive | No runtime isinstance() | Static analysis primary goal |
| Gradual typing | No development blocking | Incomplete coverage | Pragmatic for personal project |
| Integration tests | Catch real issues | Slower than unit tests | Critical for API validation |
| Pre-commit hooks | Fast feedback | Can be bypassed | Optional for WIP commits |

### 11.2 Future Enhancements (Out of Scope)

- **Runtime type checking** (beartype, typeguard): Adds overhead, not needed if static analysis works
- **Automatic type annotation** (MonkeyType): Useful for legacy modules in Phase 6+
- **Property-based testing** (Hypothesis): Advanced testing strategy for Phase 7+
- **API compatibility monitoring**: Detect breaking changes automatically

### 11.3 References

- **PEP 544**: Protocols - Structural Subtyping (Static Duck Typing)
- **mypy Documentation**: https://mypy.readthedocs.io/en/stable/
- **typing Module**: https://docs.python.org/3/library/typing.html
- **Pre-commit Framework**: https://pre-commit.com/
- **GitHub Actions**: https://docs.github.com/en/actions
- **Gemini 2.5 Pro Review**: Conditional Approval with Protocol recommendation

---

**Design Approval**: Pending user review
**Next Phase**: Task breakdown and implementation planning
