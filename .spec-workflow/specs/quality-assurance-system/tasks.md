# Quality Assurance System - Implementation Tasks

## Task Organization

Tasks are organized into 3 sequential phases with clear dependencies and checkpoints.

```
Phase 1: Foundation (Day 1)
  ├─> Protocol Interfaces
  ├─> mypy Configuration
  └─> Checkpoint: mypy runs successfully

Phase 2: Type Hints (Day 2)
  ├─> Learning System Types
  ├─> Backtest Executor Types
  ├─> Repository Types
  └─> Checkpoint: mypy passes on all target modules

Phase 3: CI Integration (Day 3)
  ├─> GitHub Actions Workflow
  ├─> E2E Smoke Tests
  └─> Checkpoint: CI green on all commits
```

---

## Phase 1: Foundation (Day 1)

### TASK-QA-001: Create Protocol Interfaces Module
**Priority**: P0 (Blocker)
**Estimated Time**: 2 hours
**Dependencies**: None

**Objective**: Define structural type contracts for all component boundaries

**Steps**:
1. Create `src/interfaces.py` file
2. Define 8 Protocol interfaces:
   - `HistoryProvider` (iteration history management)
   - `BacktestExecutor` (strategy backtesting)
   - `ChampionTracker` (best strategy tracking)
   - `FeedbackGenerator` (LLM feedback generation)
   - `SuccessClassifier` (iteration classification)
   - `HallOfFameRepository` (champion persistence)
   - `IterationExecutor` (single iteration execution)
   - `LearningLoop` (main learning orchestrator)

3. Document each Protocol with:
   - Docstring explaining purpose
   - Method signatures with type hints
   - Parameter descriptions

**Implementation Template**:
```python
# src/interfaces.py

from typing import Protocol, Optional
from dataclasses import dataclass
import pandas as pd

@dataclass
class IterationRecord:
    """Represents a single learning iteration"""
    iteration_num: int
    strategy_code: str
    metrics: dict[str, float]
    classification_level: Optional[str] = None
    champion_updated: bool = False

@dataclass
class BacktestResult:
    """Results from backtesting a strategy"""
    sharpe_ratio: float
    total_return: float
    max_drawdown: float
    annual_return: float

class HistoryProvider(Protocol):
    """Contract for components that provide iteration history"""

    def save(self, record: IterationRecord) -> None:
        """Save iteration record to history"""
        ...

    def load_all(self) -> list[IterationRecord]:
        """Load all iteration records"""
        ...

    def get_champion(self) -> Optional[IterationRecord]:
        """Get current champion strategy"""
        ...

class BacktestExecutor(Protocol):
    """Contract for strategy backtesting components"""

    def execute(
        self,
        strategy_code: str,
        data: pd.DataFrame
    ) -> BacktestResult:
        """Execute backtest for given strategy"""
        ...

# ... (continue for all 8 Protocols)
```

**Acceptance Criteria**:
- [ ] All 8 Protocol interfaces defined
- [ ] Each Protocol has complete docstrings
- [ ] Method signatures match actual usage patterns
- [ ] File imports without errors
- [ ] No runtime dependencies (typing only)

**Validation**:
```bash
python -c "from src.interfaces import *"  # Should import cleanly
mypy src/interfaces.py                     # Should pass
```

---

### TASK-QA-002: Configure mypy for Project
**Priority**: P0 (Blocker)
**Estimated Time**: 1 hour
**Dependencies**: TASK-QA-001

**Objective**: Set up mypy with appropriate strictness for gradual typing

**Steps**:
1. Create `mypy.ini` in project root
2. Configure lenient settings for initial adoption
3. Specify target modules for type checking
4. Add third-party library ignores

**Configuration File**:
```ini
# mypy.ini

[mypy]
# Python version
python_version = 3.10

# Target modules for type checking
files = src/learning, src/backtest, src/repository

# Lenient settings for gradual adoption
disallow_untyped_defs = False        # Allow untyped function definitions
disallow_incomplete_defs = False     # Allow incomplete type annotations
warn_return_any = False              # Don't warn on 'Any' returns
warn_unused_ignores = True           # Warn on unnecessary '# type: ignore'

# Error reporting
show_error_codes = True              # Show error codes (e.g., [arg-type])
pretty = True                        # Colorful output
show_column_numbers = True           # Show column in errors

# Third-party library ignores
[mypy-finlab.*]
ignore_missing_imports = True

[mypy-pandas.*]
ignore_missing_imports = True

[mypy-numpy.*]
ignore_missing_imports = True

[mypy-matplotlib.*]
ignore_missing_imports = True

# Future: Can tighten these settings gradually
# disallow_untyped_defs = True
# disallow_incomplete_defs = True
# warn_return_any = True
```

**Acceptance Criteria**:
- [ ] `mypy.ini` created in project root
- [ ] mypy runs without configuration errors
- [ ] Third-party imports don't cause failures
- [ ] Configuration documented in file

**Validation**:
```bash
mypy --version  # Ensure mypy ≥ 1.18.0 installed
mypy src/interfaces.py  # Should pass (baseline)
```

---

### TASK-QA-003: Add Type Hints to IterationHistory
**Priority**: P0 (Blocker)
**Estimated Time**: 1.5 hours
**Dependencies**: TASK-QA-001, TASK-QA-002

**Objective**: Type the first module as proof-of-concept

**Steps**:
1. Open `src/learning/iteration_history.py`
2. Import necessary types from `src.interfaces`
3. Add type hints to all public methods
4. Add type hints to `__init__` parameters
5. Update dataclass fields with types (if not already)
6. Run mypy and fix any errors

**Example**:
```python
# src/learning/iteration_history.py

from typing import Optional
from src.interfaces import IterationRecord, HistoryProvider

class IterationHistory(HistoryProvider):  # Implements Protocol
    """Manages iteration history persistence"""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.records: list[IterationRecord] = []

    def save(self, record: IterationRecord) -> None:
        """Save iteration record to JSON file"""
        self.records.append(record)
        # ... implementation

    def load_all(self) -> list[IterationRecord]:
        """Load all records from JSON file"""
        # ... implementation
        return self.records

    def get_champion(self) -> Optional[IterationRecord]:
        """Get best performing strategy"""
        if not self.records:
            return None
        return max(self.records, key=lambda r: r.metrics["sharpe_ratio"])
```

**Common Issues to Fix**:

**Issue 1: Parameter name mismatch**
```python
# Before (Phase 8 error)
def __init__(self, filepath: str):  # Wrong parameter name
    ...

# After
def __init__(self, file_path: str):  # Matches call sites
    ...
```

**Issue 2: Missing return type**
```python
# Before
def get_champion(self):
    ...

# After
def get_champion(self) -> Optional[IterationRecord]:
    ...
```

**Acceptance Criteria**:
- [ ] All public methods have type hints
- [ ] Parameter names match actual usage
- [ ] Return types specified
- [ ] mypy passes on this module
- [ ] Implements `HistoryProvider` Protocol

**Validation**:
```bash
mypy src/learning/iteration_history.py  # 0 errors
python -m pytest tests/learning/test_iteration_history.py  # All pass
```

---

### TASK-QA-004: Checkpoint - Foundation Complete
**Priority**: P0 (Blocker)
**Estimated Time**: 30 minutes
**Dependencies**: TASK-QA-001, TASK-QA-002, TASK-QA-003

**Objective**: Validate foundation is solid before proceeding

**Validation Steps**:
1. Run mypy on interfaces module
2. Run mypy on iteration_history module
3. Run all existing tests (926 tests)
4. Document any `# type: ignore` uses

**Success Criteria**:
- [ ] mypy passes on `src/interfaces.py`
- [ ] mypy passes on `src/learning/iteration_history.py`
- [ ] All 926 existing tests pass
- [ ] Zero regressions introduced
- [ ] Ready to proceed to Phase 2

**Checkpoint Command**:
```bash
# Run comprehensive validation
mypy src/interfaces.py src/learning/iteration_history.py
pytest tests/ -v
```

**Expected Output**:
```
mypy: Success: no issues found in 2 source files
pytest: 926 passed in X seconds
```

---

## Phase 2: Type Hints on Public APIs (Day 2)

### TASK-QA-005: Type Hints for Champion Tracker
**Priority**: P0 (Blocker)
**Estimated Time**: 1 hour
**Dependencies**: TASK-QA-004

**Objective**: Add types to champion management component

**Target File**: `src/learning/champion_tracker.py`

**Steps**:
1. Import `ChampionTracker` Protocol from interfaces
2. Add type hints to `__init__`
3. Add type hints to `update_if_better()`
4. Add type hints to `get_current_champion()`
5. Fix parameter name issues (champion vs champion_tracker)

**Key Fix** (Phase 8 error):
```python
# Before (Phase 8 error)
def update_if_better(self, champion: IterationRecord) -> bool:
    # Parameter named 'champion' but called with champion_tracker
    ...

# After
def update_if_better(self, record: IterationRecord) -> bool:
    # Clear parameter name
    ...
```

**Acceptance Criteria**:
- [ ] Implements `ChampionTracker` Protocol
- [ ] All public methods typed
- [ ] Parameter names consistent with call sites
- [ ] mypy passes
- [ ] Tests pass

**Validation**:
```bash
mypy src/learning/champion_tracker.py
pytest tests/learning/test_champion_tracker.py
```

---

### TASK-QA-006: Type Hints for Iteration Executor
**Priority**: P0 (Blocker)
**Estimated Time**: 1.5 hours
**Dependencies**: TASK-QA-004

**Objective**: Add types to iteration execution component

**Target File**: `src/learning/iteration_executor.py`

**Steps**:
1. Import necessary Protocols (BacktestExecutor, SuccessClassifier, FeedbackGenerator)
2. Add type hints to `__init__` parameters
3. Add type hints to `execute_iteration()`
4. Fix method signature issues (execute_code vs execute)

**Key Fix** (Phase 8 error):
```python
# Before (Phase 8 error)
def execute_iteration(self, strategy: str) -> IterationRecord:
    result = self.backtest.execute_code(strategy, self.data)  # Wrong method name
    ...

# After
def execute_iteration(self, strategy: str) -> IterationRecord:
    result = self.backtest.execute(strategy, self.data)  # Correct method
    ...
```

**Acceptance Criteria**:
- [ ] Implements `IterationExecutor` Protocol
- [ ] All dependencies typed correctly
- [ ] Method names match actual implementations
- [ ] mypy passes
- [ ] Tests pass

**Validation**:
```bash
mypy src/learning/iteration_executor.py
pytest tests/learning/test_iteration_executor.py
```

---

### TASK-QA-007: Type Hints for Feedback Generator
**Priority**: P0 (Blocker)
**Estimated Time**: 1 hour
**Dependencies**: TASK-QA-004

**Objective**: Add types to LLM feedback component

**Target File**: `src/learning/feedback_generator.py`

**Steps**:
1. Import `FeedbackGenerator` Protocol
2. Add type hints to `generate_feedback()`
3. Ensure parameter types match IterationRecord

**Implementation**:
```python
# src/learning/feedback_generator.py

from src.interfaces import FeedbackGenerator, IterationRecord

class LLMFeedbackGenerator(FeedbackGenerator):

    def generate_feedback(
        self,
        record: IterationRecord,
        history: list[IterationRecord]
    ) -> str:
        """Generate LLM feedback for iteration"""
        # ... implementation
        return feedback_text
```

**Acceptance Criteria**:
- [ ] Implements `FeedbackGenerator` Protocol
- [ ] Parameters typed correctly
- [ ] Return type specified
- [ ] mypy passes

**Validation**:
```bash
mypy src/learning/feedback_generator.py
```

---

### TASK-QA-008: Type Hints for Learning Loop
**Priority**: P0 (Blocker)
**Estimated Time**: 2 hours
**Dependencies**: TASK-QA-005, TASK-QA-006, TASK-QA-007

**Objective**: Add types to main orchestration component

**Target File**: `src/learning/learning_loop.py`

**Steps**:
1. Import all relevant Protocols
2. Add type hints to `__init__` parameters
3. Add type hints to `run_iterations()`
4. Ensure all component dependencies are typed

**Key Focus** (integrates all components):
```python
# src/learning/learning_loop.py

from src.interfaces import (
    LearningLoop as LearningLoopProtocol,
    HistoryProvider,
    ChampionTracker,
    IterationExecutor
)

class LearningLoop(LearningLoopProtocol):

    def __init__(
        self,
        history: HistoryProvider,
        champion: ChampionTracker,
        executor: IterationExecutor
    ) -> None:
        self.history = history
        self.champion = champion
        self.executor = executor

    def run_iterations(self, num_iterations: int) -> None:
        """Run specified number of learning iterations"""
        for i in range(num_iterations):
            record = self.executor.execute_iteration(f"iteration_{i}")
            self.history.save(record)
            self.champion.update_if_better(record)
```

**Acceptance Criteria**:
- [ ] Implements `LearningLoop` Protocol
- [ ] All dependencies typed with Protocols
- [ ] Constructor parameters match actual usage
- [ ] mypy passes
- [ ] Integration tests pass

**Validation**:
```bash
mypy src/learning/learning_loop.py
pytest tests/learning/test_learning_loop.py
```

---

### TASK-QA-009: Type Hints for Backtest Executor
**Priority**: P0 (Blocker)
**Estimated Time**: 1 hour
**Dependencies**: TASK-QA-004

**Objective**: Add types to backtesting component

**Target File**: `src/backtest/executor.py`

**Steps**:
1. Import `BacktestExecutor` Protocol and `BacktestResult`
2. Add type hints to `execute()` method
3. Ensure pandas DataFrame typing

**Key Fix** (Phase 8 error - missing parameters):
```python
# Before (Phase 8 error)
def execute(self, strategy_code: str) -> BacktestResult:
    # Missing 'data' parameter!
    ...

# After
def execute(
    self,
    strategy_code: str,
    data: pd.DataFrame
) -> BacktestResult:
    """Execute backtest with provided data"""
    ...
```

**Acceptance Criteria**:
- [ ] Implements `BacktestExecutor` Protocol
- [ ] All required parameters present
- [ ] Return type matches BacktestResult
- [ ] mypy passes

**Validation**:
```bash
mypy src/backtest/executor.py
pytest tests/backtest/test_executor.py
```

---

### TASK-QA-010: Type Hints for Hall of Fame Repository
**Priority**: P0 (Blocker)
**Estimated Time**: 1 hour
**Dependencies**: TASK-QA-004

**Objective**: Add types to champion persistence component

**Target File**: `src/repository/hall_of_fame.py`

**Steps**:
1. Import `HallOfFameRepository` Protocol
2. Add type hints to `save_champion()`
3. Add type hints to `load_champion()`

**Implementation**:
```python
# src/repository/hall_of_fame.py

from typing import Optional
from src.interfaces import HallOfFameRepository, IterationRecord

class HallOfFame(HallOfFameRepository):

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def save_champion(self, record: IterationRecord) -> None:
        """Persist champion to file"""
        # ... implementation

    def load_champion(self) -> Optional[IterationRecord]:
        """Load champion from file"""
        # ... implementation
        return champion
```

**Acceptance Criteria**:
- [ ] Implements `HallOfFameRepository` Protocol
- [ ] Type hints on all methods
- [ ] mypy passes

**Validation**:
```bash
mypy src/repository/hall_of_fame.py
pytest tests/repository/test_hall_of_fame.py
```

---

### TASK-QA-011: Checkpoint - Type Hints Complete
**Priority**: P0 (Blocker)
**Estimated Time**: 30 minutes
**Dependencies**: All TASK-QA-005 through TASK-QA-010

**Objective**: Validate all type hints before CI integration

**Validation Steps**:
1. Run mypy on all target modules
2. Run full test suite
3. Document any `# type: ignore` uses with rationale
4. Verify IDE autocomplete working

**Success Criteria**:
- [ ] mypy passes on all learning/ modules
- [ ] mypy passes on backtest/ module
- [ ] mypy passes on repository/ module
- [ ] All 926 tests pass
- [ ] < 5 `# type: ignore` suppressions
- [ ] IDE shows proper type hints

**Checkpoint Command**:
```bash
# Comprehensive type check
mypy src/learning/ src/backtest/ src/repository/

# Full test suite
pytest tests/ -v

# Count type ignores
grep -r "# type: ignore" src/ | wc -l  # Should be < 5
```

**Expected Output**:
```
mypy: Success: no issues found in 10 source files
pytest: 926 passed in X seconds
Type ignores: 2 (documented)
```

---

## Phase 3: CI Integration (Day 3)

### TASK-QA-012: Create GitHub Actions Workflow
**Priority**: P0 (Blocker)
**Estimated Time**: 1 hour
**Dependencies**: TASK-QA-011

**Objective**: Automate type checking on every commit

**Steps**:
1. Create `.github/workflows/` directory (if not exists)
2. Create `type-safety.yml` workflow
3. Configure mypy job
4. Configure E2E smoke test job

**Workflow File**:
```yaml
# .github/workflows/type-safety.yml

name: Type Safety & E2E Smoke Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  mypy-type-check:
    name: Static Type Checking (mypy)
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install mypy
          pip install -r requirements.txt

      - name: Run mypy
        run: |
          mypy src/learning/ src/backtest/ src/repository/

      - name: Report results
        if: always()
        run: |
          echo "mypy type checking complete"

  e2e-smoke-tests:
    name: E2E Integration Smoke Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.10
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest

      - name: Run E2E smoke tests
        run: |
          pytest tests/integration/test_phase8_e2e_smoke.py -v

      - name: Report results
        if: always()
        run: |
          echo "E2E smoke tests complete"
```

**Acceptance Criteria**:
- [ ] Workflow file created
- [ ] Runs on push to main/develop
- [ ] Runs on pull requests
- [ ] mypy job configured
- [ ] E2E test job configured
- [ ] Jobs run independently

**Validation**:
```bash
# Test workflow locally with act (optional)
act -j mypy-type-check

# Or push to trigger CI
git add .github/workflows/type-safety.yml
git commit -m "Add type safety CI workflow"
git push
```

---

### TASK-QA-013: Create E2E Smoke Test Suite
**Priority**: P0 (Blocker)
**Estimated Time**: 2 hours
**Dependencies**: TASK-QA-011

**Objective**: Test Phase 8 scenarios to prevent regression

**Steps**:
1. Create `tests/integration/test_phase8_e2e_smoke.py`
2. Write smoke test for each Phase 8 error
3. Use actual components (not mocks)
4. Keep tests fast (< 10 seconds total)

**Test File**:
```python
# tests/integration/test_phase8_e2e_smoke.py

"""
E2E Smoke Tests - Prevent Phase 8 API Mismatches

These tests validate the 8 specific errors discovered in Phase 8:
1. Parameter name mismatch (file_path vs filepath)
2. Method signature error (execute_code vs execute)
3. Missing required parameter (data not provided)
4. Wrong classifier usage (ErrorClassifier vs SuccessClassifier)
5. Deserialization field mismatch
6. Champion parameter name (champion vs champion_tracker)
7. Missing sim parameter
8. Return type mismatch
"""

import pytest
import pandas as pd
from src.learning.iteration_history import IterationHistory
from src.learning.champion_tracker import ChampionTracker
from src.learning.iteration_executor import IterationExecutor
from src.backtest.executor import BacktestExecutor
from src.interfaces import IterationRecord

class TestPhase8Regressions:
    """Smoke tests for Phase 8 API contract errors"""

    def test_iteration_history_parameter_name(self):
        """ERROR 1: file_path parameter name consistency"""
        # This should work without TypeError
        history = IterationHistory(file_path="test.json")  # Not 'filepath'
        assert history.file_path == "test.json"

    def test_backtest_executor_method_signature(self):
        """ERROR 2: BacktestExecutor.execute() method name"""
        executor = BacktestExecutor()
        data = pd.DataFrame({"close": [100, 101, 102]})

        # Should use execute(), not execute_code()
        result = executor.execute("lambda df: df['close'] > 100", data)
        assert hasattr(result, "sharpe_ratio")

    def test_backtest_executor_required_parameters(self):
        """ERROR 3: Missing 'data' parameter in execute()"""
        executor = BacktestExecutor()
        data = pd.DataFrame({"close": [100, 101, 102]})

        # Must provide both strategy_code AND data
        result = executor.execute(
            strategy_code="lambda df: df['close'] > 100",
            data=data  # Required parameter
        )
        assert result is not None

    def test_success_classifier_usage(self):
        """ERROR 4: Correct classifier (SuccessClassifier, not ErrorClassifier)"""
        from src.learning.success_classifier import SuccessClassifier

        classifier = SuccessClassifier()
        record = IterationRecord(
            iteration_num=1,
            strategy_code="test",
            metrics={"sharpe_ratio": 1.5}
        )

        # Should use SuccessClassifier
        level = classifier.classify(record)
        assert level in ["poor", "good", "excellent"]

    def test_iteration_record_deserialization(self):
        """ERROR 5: IterationRecord field names match"""
        record_dict = {
            "iteration_num": 1,
            "strategy_code": "lambda df: df['close'] > 100",
            "metrics": {"sharpe_ratio": 1.5},
            "classification_level": "excellent",
            "champion_updated": True
        }

        # Should deserialize without KeyError
        record = IterationRecord(**record_dict)
        assert record.iteration_num == 1

    def test_champion_tracker_parameter_name(self):
        """ERROR 6: update_if_better() parameter name"""
        tracker = ChampionTracker()
        record = IterationRecord(
            iteration_num=1,
            strategy_code="test",
            metrics={"sharpe_ratio": 1.5}
        )

        # Parameter should be 'record', not 'champion' or 'champion_tracker'
        updated = tracker.update_if_better(record=record)
        assert isinstance(updated, bool)

    def test_iteration_executor_all_dependencies(self):
        """ERROR 7 & 8: All required dependencies provided"""
        # Mock dependencies
        history = IterationHistory(file_path="test.json")
        backtest = BacktestExecutor()
        data = pd.DataFrame({"close": [100, 101, 102]})

        executor = IterationExecutor(
            history=history,
            backtest=backtest,
            data=data  # Required: data
            # sim parameter if needed
        )

        # Should initialize without missing parameter errors
        assert executor.history is not None
        assert executor.backtest is not None
        assert executor.data is not None

    def test_end_to_end_learning_iteration(self):
        """Full E2E test: One learning iteration without errors"""
        # Setup
        history = IterationHistory(file_path="test_e2e.json")
        champion = ChampionTracker()
        backtest = BacktestExecutor()
        data = pd.DataFrame({"close": [100, 101, 102, 103, 104]})

        executor = IterationExecutor(
            history=history,
            backtest=backtest,
            data=data
        )

        # Execute one iteration
        record = executor.execute_iteration("lambda df: df['close'] > 100")

        # Validate all API contracts
        assert isinstance(record, IterationRecord)
        assert record.iteration_num >= 0
        assert "sharpe_ratio" in record.metrics

        # Save to history
        history.save(record)

        # Update champion
        champion.update_if_better(record)

        # Should complete without TypeError, AttributeError, or KeyError
```

**Acceptance Criteria**:
- [ ] All 8 Phase 8 errors have test coverage
- [ ] Tests run in < 10 seconds
- [ ] Tests use real components (minimal mocking)
- [ ] All tests pass
- [ ] Clear test names and documentation

**Validation**:
```bash
pytest tests/integration/test_phase8_e2e_smoke.py -v
```

---

### TASK-QA-014: Document Type System Usage
**Priority**: P1 (Important)
**Estimated Time**: 1 hour
**Dependencies**: TASK-QA-011

**Objective**: Create developer guide for type system

**Steps**:
1. Create `docs/TYPE_SYSTEM.md`
2. Document how to add types to new code
3. Document when to use `# type: ignore`
4. Provide examples

**Documentation File**:
```markdown
# Type System Usage Guide

## Overview

This project uses Python type hints with mypy static type checking to catch API contract violations at development time.

## Quick Start

### Adding Type Hints to New Code

```python
from typing import Optional
from src.interfaces import IterationRecord, HistoryProvider

class MyNewComponent(HistoryProvider):
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.records: list[IterationRecord] = []

    def save(self, record: IterationRecord) -> None:
        self.records.append(record)

    def load_all(self) -> list[IterationRecord]:
        return self.records

    def get_champion(self) -> Optional[IterationRecord]:
        if not self.records:
            return None
        return max(self.records, key=lambda r: r.metrics["sharpe_ratio"])
```

### Running mypy

```bash
# Check specific file
mypy src/learning/my_module.py

# Check all target modules
mypy src/learning/ src/backtest/ src/repository/

# In CI (automatic)
# Runs on every commit via GitHub Actions
```

### Protocol Interfaces

Use Protocol types for component dependencies:

```python
from src.interfaces import BacktestExecutor, HistoryProvider

class MyComponent:
    def __init__(
        self,
        backtest: BacktestExecutor,  # Protocol type, not concrete class
        history: HistoryProvider
    ) -> None:
        self.backtest = backtest
        self.history = history
```

### When to Use `# type: ignore`

Use sparingly and with rationale:

```python
# OK: Third-party library without type stubs
import some_untyped_library  # type: ignore

# OK: Dynamic attribute access
result = getattr(obj, dynamic_name)  # type: ignore[attr-defined]

# NOT OK: Avoiding fixing actual type error
def broken(x):  # type: ignore  # BAD: Fix the signature instead!
    ...
```

### Common Patterns

**Optional Parameters**:
```python
def process(data: Optional[pd.DataFrame] = None) -> None:
    if data is None:
        data = load_default_data()
    ...
```

**List/Dict Types**:
```python
records: list[IterationRecord] = []
metrics: dict[str, float] = {}
```

**Union Types**:
```python
from typing import Union

def handle(value: Union[int, str]) -> None:
    ...
```

## Troubleshooting

### Error: "Missing return statement"
Add return type hint and ensure all code paths return a value.

### Error: "Incompatible type in argument"
Check parameter names match between function definition and call sites.

### Error: "Module has no attribute"
Add `# type: ignore[import]` if third-party library lacks stubs.

## References

- PEP 484: Type Hints
- PEP 544: Protocol (Structural Subtyping)
- mypy documentation: https://mypy.readthedocs.io/
```

**Acceptance Criteria**:
- [ ] Developer guide created
- [ ] Common patterns documented
- [ ] Troubleshooting section included
- [ ] Examples provided

---

### TASK-QA-015: Final Validation & Cleanup
**Priority**: P0 (Blocker)
**Estimated Time**: 1 hour
**Dependencies**: All previous tasks

**Objective**: Ensure entire system works end-to-end

**Validation Checklist**:
1. [ ] mypy passes on all target modules (0 errors)
2. [ ] All 926 existing tests pass
3. [ ] All 8 E2E smoke tests pass
4. [ ] CI workflow runs successfully
5. [ ] Documentation complete
6. [ ] No regressions introduced

**Validation Commands**:
```bash
# 1. Type checking
mypy src/learning/ src/backtest/ src/repository/

# 2. Unit tests
pytest tests/ -v

# 3. E2E smoke tests
pytest tests/integration/test_phase8_e2e_smoke.py -v

# 4. CI simulation (if using act)
act

# 5. Check documentation
ls docs/TYPE_SYSTEM.md
```

**Success Criteria**:
```
✓ mypy: Success: no issues found in 10 source files
✓ pytest: 926 passed
✓ E2E smoke tests: 8 passed
✓ CI: All jobs passed
✓ Documentation: Complete
```

**Cleanup Tasks**:
- [ ] Remove any debug print statements
- [ ] Remove unused imports
- [ ] Format code consistently
- [ ] Update README if needed

---

## Summary

### Timeline

```
Day 1: Foundation (4-6 hours)
├─ TASK-QA-001: Protocol Interfaces (2h)
├─ TASK-QA-002: mypy Configuration (1h)
├─ TASK-QA-003: Type Hints IterationHistory (1.5h)
└─ TASK-QA-004: Checkpoint (0.5h)

Day 2: Type Hints (6-8 hours)
├─ TASK-QA-005: Champion Tracker (1h)
├─ TASK-QA-006: Iteration Executor (1.5h)
├─ TASK-QA-007: Feedback Generator (1h)
├─ TASK-QA-008: Learning Loop (2h)
├─ TASK-QA-009: Backtest Executor (1h)
├─ TASK-QA-010: Hall of Fame (1h)
└─ TASK-QA-011: Checkpoint (0.5h)

Day 3: CI Integration (4-6 hours)
├─ TASK-QA-012: GitHub Actions (1h)
├─ TASK-QA-013: E2E Smoke Tests (2h)
├─ TASK-QA-014: Documentation (1h)
└─ TASK-QA-015: Final Validation (1h)

Total: 14-20 hours (2-3 days)
```

### Critical Path

```
QA-001 → QA-002 → QA-003 → QA-004 (Foundation)
                               ↓
            All Day 2 tasks (Type Hints)
                               ↓
            QA-011 (Checkpoint)
                               ↓
            All Day 3 tasks (CI)
                               ↓
            QA-015 (Complete)
```

### Resource Requirements

**Developer Time**: 14-20 hours over 2-3 days
**Computational Resources**: None (all development-time)
**Dependencies**: mypy ≥ 1.18.0 (dev dependency only)
**Risk**: Low (non-breaking changes, gradual adoption)

### Success Metrics

**Code Quality**:
- mypy: 0 errors on target modules
- Test coverage: Maintained >80%
- Type coverage: 100% on public APIs

**Reliability**:
- Phase 8 errors: Cannot recur (prevented by CI)
- Regression rate: 0 (CI blocks bad commits)

**Developer Experience**:
- IDE autocomplete: Working perfectly
- Error detection: < 1 second (in IDE)
- Debugging time: Reduced 30%
