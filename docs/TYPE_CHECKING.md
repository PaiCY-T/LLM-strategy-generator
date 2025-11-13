# Type Checking Guide - API Mismatch Prevention System

**Version**: 1.0
**Status**: Phase 5A Complete
**Last Updated**: 2025-11-12

## Table of Contents

1. [Quick Start](#quick-start)
2. [Setup Instructions](#setup-instructions)
3. [Usage Guide](#usage-guide)
4. [Configuration Details](#configuration-details)
5. [CI/CD Integration](#cicd-integration)
6. [Migration Guide](#migration-guide)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Quick Start

**Goal**: Catch API mismatches (like `.get_champion()` vs `.champion`) at development time, not runtime.

**3-Step Setup**:
```bash
# 1. Install mypy locally
pip install mypy

# 2. Run type checking
mypy src/learning/

# 3. Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

**Expected Result**: 0 errors on Phase 1-4 modules, warnings only on legacy code.

---

## Setup Instructions

### 1. Installing mypy Locally

**Prerequisites**: Python 3.11+, virtual environment activated

```bash
# Option 1: Install from requirements-dev.txt (recommended)
pip install -r requirements-dev.txt

# Option 2: Install mypy directly
pip install mypy==1.11.0

# Verify installation
mypy --version
# Expected: mypy 1.11.0 (compiled: yes)
```

### 2. Installing Pre-commit Hooks

**Why**: Catch type errors before committing code (fast feedback loop)

**Note**: GitHub Actions and pre-commit hooks are not yet configured. This section describes the planned setup.

**Planned Setup** (Phase 5A.2 & 5A.3):
```bash
# Install pre-commit framework
pip install pre-commit

# Install hooks from .pre-commit-config.yaml (when available)
pre-commit install

# Test hooks manually
pre-commit run --all-files

# Expected output:
# mypy.................................................................Passed
```

**Bypass when needed** (for WIP commits):
```bash
git commit --no-verify -m "WIP: Work in progress"
```

### 3. IDE Integration

#### VS Code Setup

**Install Extension**:
1. Open VS Code Extensions (Ctrl+Shift+X)
2. Search for "Pylance" (Microsoft's Python language server)
3. Install and reload

**Configure** (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.mypyEnabled": true,
  "python.linting.mypyArgs": [
    "--config-file=mypy.ini",
    "--show-error-codes"
  ],
  "python.analysis.typeCheckingMode": "strict"
}
```

**Usage**:
- Errors appear as red squiggles in editor
- Hover over error for details
- Click "Quick Fix" for suggestions

#### PyCharm Setup

**Enable mypy**:
1. Settings → Tools → External Tools
2. Click "+" to add new tool
3. Configure:
   - Name: `mypy`
   - Program: `$PyInterpreterDirectory$/mypy`
   - Arguments: `--config-file=mypy.ini $FilePath$`
   - Working directory: `$ProjectFileDir$`

**Usage**:
- Right-click file → External Tools → mypy
- View errors in "Run" tool window

---

## Usage Guide

### Running Type Checks Locally

**Check specific module**:
```bash
# Check learning modules (strict mode)
mypy src/learning/

# Expected: 0 errors on Phase 1-4 code
```

**Check legacy modules** (warnings only):
```bash
# Check backtest modules (lenient mode)
mypy src/backtest/

# Expected: Warnings only, no blocking errors
```

**Check entire project**:
```bash
mypy src/

# Expected: 0 errors on Phase 1-4, warnings on legacy
```

**Performance**: <30s for full check (target met)

### Understanding Error Messages

#### Example 1: Property vs Method Confusion

**Error**:
```python
# src/learning/feedback_generator.py:45
error: "IChampionTracker" has no attribute "get_champion"  [attr-defined]
    champion = self.tracker.get_champion()
                            ^~~~~~~~~~~~~
```

**Diagnosis**:
- **Problem**: Trying to call `.get_champion()` method, but Protocol defines `.champion` property
- **Error Code**: `[attr-defined]` - Attribute not found
- **Line**: 45 in `feedback_generator.py`

**Fix**:
```python
# Before (WRONG - method call)
champion = self.tracker.get_champion()

# After (CORRECT - property access)
champion = self.tracker.champion
```

#### Example 2: Missing Type Annotation

**Error**:
```python
# src/learning/iteration_executor.py:102
error: Function is missing a return type annotation  [no-untyped-def]
def execute_iteration(self, iteration_num):
                                           ^
```

**Diagnosis**:
- **Problem**: Function signature lacks type hints for parameters and return value
- **Error Code**: `[no-untyped-def]` - Untyped function definition
- **Line**: 102 in `iteration_executor.py`

**Fix**:
```python
# Before (WRONG - no type hints)
def execute_iteration(self, iteration_num):
    ...

# After (CORRECT - full type hints)
def execute_iteration(self, iteration_num: int) -> IterationResult:
    ...
```

#### Example 3: Type Mismatch

**Error**:
```python
# src/learning/champion_tracker.py:67
error: Incompatible return value type (got "None", expected "IterationRecord")  [return-value]
    return None
           ^^^^
```

**Diagnosis**:
- **Problem**: Function declared to return `IterationRecord`, but returns `None`
- **Error Code**: `[return-value]` - Return type mismatch
- **Solution**: Use `Optional[IterationRecord]` if `None` is valid return

**Fix**:
```python
# Before (WRONG - return type mismatch)
def get_latest_record(self) -> IterationRecord:
    if not self.records:
        return None  # ❌ Type error

# After (CORRECT - Optional return type)
def get_latest_record(self) -> Optional[IterationRecord]:
    if not self.records:
        return None  # ✅ Allowed
    return self.records[-1]
```

### Common Error Codes Reference

| Error Code | Meaning | Common Fix |
|------------|---------|------------|
| `[attr-defined]` | Attribute doesn't exist | Check Protocol definition, fix method/property confusion |
| `[no-untyped-def]` | Missing type annotations | Add type hints to function signature |
| `[return-value]` | Return type mismatch | Use `Optional[T]` if `None` is valid, or fix logic |
| `[arg-type]` | Argument type wrong | Check function signature, pass correct type |
| `[assignment]` | Assignment type mismatch | Verify variable types match assigned value |
| `[call-arg]` | Missing/extra arguments | Check function signature, fix call site |

**Full error code reference**: https://mypy.readthedocs.io/en/stable/error_codes.html

### Fixing Common Type Errors

#### Error Pattern 1: Protocol Violations (API Mismatches)

**Symptom**: Runtime `AttributeError` caught by mypy

```python
# WRONG: Calling method that doesn't exist in Protocol
champion_record = tracker.get_champion()  # ❌ [attr-defined]

# CORRECT: Using property defined in Protocol
champion_record = tracker.champion  # ✅
```

**How to detect**: Search for Protocol definition in `src/learning/interfaces.py`

#### Error Pattern 2: Missing Runtime Validation

**Symptom**: Legacy module passes incompatible object

```python
# WRONG: No validation at boundary
self.tracker = legacy_tracker  # ❌ May not implement Protocol

# CORRECT: Runtime validation at initialization
from src.learning.validation import validate_protocol_compliance
from src.learning.interfaces import IChampionTracker

self.tracker = validate_protocol_compliance(
    legacy_tracker,
    IChampionTracker,
    "ChampionTracker initialization"
)  # ✅ Catches violations early
```

**When to use**: At module boundaries when integrating legacy code

#### Error Pattern 3: Untyped Legacy Code

**Symptom**: Warnings about missing type annotations in `src/backtest/*`

```python
# In legacy modules (src/backtest/*), this is ALLOWED (warnings only)
def run_backtest(data, strategy):  # ⚠️ Warning, not error
    ...

# In new modules (src/learning/*), this is BLOCKED
def run_iteration(iteration_num):  # ❌ [no-untyped-def]
    ...
```

**Strategy**: Add type hints incrementally to legacy code (see Migration Guide)

---

## Configuration Details

### mypy.ini Structure

**Location**: `/mnt/c/Users/jnpi/Documents/finlab/LLM-strategy-generator/mypy.ini`

**Philosophy**: Gradual migration with strict enforcement on new code

```ini
[mypy]
# Global strict settings (applied to all modules by default)
python_version = 3.11
strict = True
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

# Error reporting configuration
show_error_codes = True          # Show [error-code] tags
pretty = True                     # Color output
show_column_numbers = True        # Precise error location
show_error_context = True         # Show surrounding code

# Helpful warnings
warn_unused_ignores = True        # Warn about unused # type: ignore
warn_redundant_casts = True       # Warn about unnecessary casts
warn_unreachable = True           # Warn about unreachable code
warn_no_return = True             # Warn about missing return
```

### Strict vs Lenient Zones

#### Strict Zone: `src/learning/*` (Phase 1-4 modules)

**Purpose**: Full type safety for new Protocol-based architecture

```ini
[mypy-src.learning.*]
strict = True                     # All strict checks enabled
disallow_untyped_defs = True      # All functions MUST have type hints
warn_return_any = True            # Warn if returning Any type
disallow_incomplete_defs = True   # No partial type hints allowed
check_untyped_defs = True         # Check bodies of untyped functions
```

**Expected Errors**: 0 errors (100% compliance required)

#### Lenient Zone: `src/backtest/*` (Legacy modules)

**Purpose**: Allow gradual migration without blocking development

```ini
[mypy-src.backtest.*]
strict = False                    # Relaxed checking
warn_unused_ignores = False       # Don't warn about ignored errors
check_untyped_defs = False        # Don't check untyped function bodies
disallow_untyped_defs = False     # Allow untyped functions
disallow_incomplete_defs = False  # Allow partial type hints
```

**Expected Errors**: Warnings only, no blocking errors

**Gemini Recommendation**: `check_untyped_defs = False` reduces noise from legacy code

### Third-Party Library Ignores

**Problem**: Some libraries lack type stubs (`.pyi` files)

**Solution**: Ignore missing imports to prevent false positives

```ini
[mypy-finlab.*]
ignore_missing_imports = True     # Finlab API library

[mypy-pandas.*]
ignore_missing_imports = True     # Pandas data analysis

[mypy-numpy.*]
ignore_missing_imports = True     # NumPy arrays

[mypy-matplotlib.*]
ignore_missing_imports = True     # Plotting library

[mypy-anthropic.*]
ignore_missing_imports = True     # Claude API

[mypy-openai.*]
ignore_missing_imports = True     # OpenAI API
```

**Alternative**: Install type stubs when available
```bash
pip install types-requests types-PyYAML
```

---

## CI/CD Integration

**Status**: GitHub Actions workflow and pre-commit hooks are **not yet configured** (Phase 5A.2 & 5A.3 pending).

### Planned GitHub Actions Workflow

**File**: `.github/workflows/ci.yml` (to be created)

**Design** (from Phase 5A.2):
```yaml
name: Type Checking & Testing

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  type-check-and-test:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'  # Cache pip dependencies

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run mypy type checking
        run: |
          mypy src/ --show-error-codes --config-file=mypy.ini

      - name: Run pytest with coverage
        run: |
          pytest tests/ -v --cov=src --cov-report=term-missing
```

**Performance Target**: <2 minutes total execution time

**Optimization Techniques**:
- Pip dependency caching (saves ~30s on subsequent runs)
- Scoped mypy to `src/` directory only (Gemini recommendation)
- Parallel job execution (if needed)

### Planned Pre-commit Hooks

**File**: `.pre-commit-config.yaml` (to be created)

**Design** (from Phase 5A.3):
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
        files: ^src/  # Only check src/ directory (Gemini optimization)
        pass_filenames: false
        always_run: false
        stages: [commit]
        verbose: true
```

**Performance**: <10s for typical commit (target: 5s)

**Optimization**: `files: ^src/` scopes mypy to source directory only

---

## Migration Guide

### Adding Types to Legacy Code

**Strategy**: Incremental migration using the "Boy Scout Rule" - improve code whenever you touch it

#### Step 1: Start with Public Interfaces (3-5 hours per module)

**Before** (untyped):
```python
# src/backtest/executor.py
def execute_strategy(data, config):
    ...
```

**After** (typed public interface):
```python
from typing import Dict, Any
import pandas as pd

def execute_strategy(data: pd.DataFrame, config: Dict[str, Any]) -> BacktestResult:
    ...
```

#### Step 2: Enable Partial Checking

**Update mypy.ini**:
```ini
# When ready, enable checking for specific legacy module
[mypy-src.backtest.executor]
check_untyped_defs = True  # Start checking this module
```

**Run mypy**:
```bash
mypy src/backtest/executor.py
# Fix errors discovered
```

#### Step 3: Gradually Increase Strictness

**Timeline** (example for `src/backtest.executor`):

| Week | Action | mypy Setting | Expected Errors |
|------|--------|--------------|-----------------|
| 1 | Add type hints to public functions | `check_untyped_defs = True` | 10-20 errors |
| 2 | Fix errors, add hints to internal functions | Same | 5-10 errors |
| 3 | Enable incomplete defs check | `disallow_incomplete_defs = True` | 2-5 errors |
| 4 | Full strict mode | `strict = True` | 0 errors ✅ |

#### Step 4: Final Goal - Full Strict Mode

**Final mypy.ini** (all modules):
```ini
[mypy]
strict = True  # Strict mode for entire codebase

# All module-specific overrides removed
```

**Estimated Timeline**: 6-12 months for full migration
**Priority**: Core modules first (executor, engine, classifier)

### Migration Workflow Example

**Scenario**: Migrating `src/backtest/executor.py` to strict mode

**Step-by-Step**:
```bash
# 1. Baseline: Run mypy to see current state
mypy src/backtest/executor.py > baseline.txt
# Expected: Many warnings, no errors (lenient mode)

# 2. Add type hints to public functions
# Edit executor.py, add type annotations

# 3. Enable checking for this module
# Edit mypy.ini:
[mypy-src.backtest.executor]
check_untyped_defs = True

# 4. Run mypy and fix errors
mypy src/backtest/executor.py
# Fix errors one by one

# 5. Gradually increase strictness
# Repeat steps 3-4 with stricter settings

# 6. Final validation
mypy src/backtest/executor.py --strict
# Expected: 0 errors ✅
```

**Completion Criteria**:
- 0 mypy errors with `--strict` flag
- All public functions have type hints
- All internal functions have type hints
- No `# type: ignore` comments (or justified with comments)

---

## Troubleshooting

### Issue: "mypy: command not found"

**Cause**: mypy not installed or not in PATH

**Solution**:
```bash
# Check if mypy is installed
pip list | grep mypy

# If missing, install
pip install mypy

# Verify installation
mypy --version
```

### Issue: "Cannot find implementation or library stub for module named 'finlab'"

**Cause**: Third-party library lacks type stubs

**Solution 1**: Verify library is in mypy.ini ignores
```ini
# Add to mypy.ini if missing
[mypy-finlab.*]
ignore_missing_imports = True
```

**Solution 2**: Install type stubs (if available)
```bash
pip install types-finlab  # If exists
```

### Issue: "Function is missing a type annotation for one or more arguments"

**Cause**: Function signature incomplete

**Wrong**:
```python
def process(data, config: dict):  # ❌ 'data' missing type
    ...
```

**Correct**:
```python
import pandas as pd
def process(data: pd.DataFrame, config: dict):  # ✅ All params typed
    ...
```

### Issue: Too many errors in legacy code

**Temporary Solution**: Use `# type: ignore` sparingly

```python
# Acceptable: Temporary workaround with explanation
result = legacy_function()  # type: ignore  # TODO: Add types to legacy_function
```

**Permanent Solution**: Follow migration guide to add types incrementally

### Issue: Pre-commit hook too slow (>10s)

**Cause**: Checking too many files or unoptimized configuration

**Solution**: Scope to changed files only
```yaml
# .pre-commit-config.yaml
hooks:
  - id: mypy
    files: ^src/  # Only src/ directory
    pass_filenames: true  # Pass only changed files
```

### Issue: CI/CD pipeline timeout (>2min)

**Cause**: Slow dependency installation or large codebase

**Solutions**:
1. Enable pip caching (already configured in planned workflow)
2. Scope mypy to specific directories:
   ```bash
   mypy src/learning/ src/backtest/  # Skip tests/
   ```
3. Parallelize type checking and testing:
   ```yaml
   jobs:
     type-check:
       ...
     test:
       ...
   # Run both in parallel
   ```

---

## Best Practices

### 1. Write Type Hints as You Code

**Good Practice**:
```python
# Write type hints immediately when creating function
def calculate_sharpe(returns: pd.Series) -> float:
    ...
```

**Bad Practice**:
```python
# Write untyped function, add types later (technical debt)
def calculate_sharpe(returns):
    ...
```

### 2. Use Protocol for Duck Typing

**Good Practice**:
```python
from typing import Protocol

class Runnable(Protocol):
    def run(self) -> None: ...

def execute(task: Runnable) -> None:
    task.run()  # ✅ Works with any object that has .run()
```

**Bad Practice**:
```python
# Using concrete class (tight coupling)
def execute(task: SpecificTask) -> None:
    task.run()  # ❌ Only works with SpecificTask
```

### 3. Prefer `Optional[T]` over `T | None`

**Good Practice**:
```python
from typing import Optional

def get_champion(self) -> Optional[IterationRecord]:
    ...  # Clear intent: may return None
```

**Bad Practice** (Python 3.10+ syntax, less clear):
```python
def get_champion(self) -> IterationRecord | None:
    ...  # Works but less conventional
```

### 4. Document Type Constraints in Docstrings

**Good Practice**:
```python
def update_champion(self, record: IterationRecord, force: bool = False) -> bool:
    """Update champion with new record.

    Args:
        record: Iteration record with valid metrics (sharpe_ratio not None)
        force: Override anti-churn checks if True

    Returns:
        True if champion was updated, False otherwise

    Pre-conditions:
        - record.metrics['sharpe_ratio'] must exist
    """
    ...
```

### 5. Run mypy Before Committing

**Workflow**:
```bash
# 1. Make changes to code
# 2. Run mypy to catch errors
mypy src/learning/

# 3. Fix any errors
# 4. Run tests
pytest tests/

# 5. Commit (pre-commit hook will run mypy again when configured)
git add .
git commit -m "feat: Add type hints to champion tracker"
```

### 6. Use Type Aliases for Complex Types

**Good Practice**:
```python
from typing import Dict, List, TypeAlias

MetricsDict: TypeAlias = Dict[str, float]
StrategyList: TypeAlias = List[IterationRecord]

def analyze_strategies(strategies: StrategyList) -> MetricsDict:
    ...  # ✅ Clear, reusable type
```

**Bad Practice**:
```python
def analyze_strategies(strategies: List[IterationRecord]) -> Dict[str, float]:
    ...  # ❌ Repetitive, harder to change
```

### 7. Avoid `Any` Type

**Good Practice**:
```python
from typing import Union

def process(data: Union[pd.DataFrame, pd.Series]) -> pd.DataFrame:
    ...  # ✅ Explicit types
```

**Bad Practice**:
```python
from typing import Any

def process(data: Any) -> Any:
    ...  # ❌ Defeats purpose of type checking
```

---

## Resources

### Official Documentation
- **mypy docs**: https://mypy.readthedocs.io/
- **Python typing module**: https://docs.python.org/3/library/typing.html
- **PEP 484** (Type Hints): https://peps.python.org/pep-0484/
- **PEP 544** (Protocols): https://peps.python.org/pep-0544/

### Project-Specific Resources
- **Design Improvements**: `.spec-workflow/specs/api-mismatch-prevention-system/DESIGN_IMPROVEMENTS.md`
- **Requirements**: `.spec-workflow/specs/api-mismatch-prevention-system/requirements.md`
- **Task List**: `.spec-workflow/specs/api-mismatch-prevention-system/tasks.md`

### Type Checking Tools
- **mypy**: https://github.com/python/mypy
- **pyright**: https://github.com/microsoft/pyright (alternative)
- **pyre**: https://pyre-check.org/ (Facebook's type checker)

---

## Summary

**Type Checking System Goals**:
1. ✅ Catch API mismatches at development time (not runtime)
2. ✅ Enable gradual migration from legacy to typed code
3. ✅ Provide fast feedback loop (<30s local, <2min CI)
4. ✅ Prevent regressions through automated checks

**Developer Workflow**:
1. Write code with type hints
2. Run `mypy src/learning/` locally (<30s)
3. Fix errors before committing
4. (Planned) Pre-commit hook validates on commit (<10s)
5. (Planned) GitHub Actions validates on push/PR (<2min)

**Performance Targets** (Phase 5A):
- ✅ Local mypy: <30s for full check
- ⏳ Pre-commit hook: <10s (target: 5s) - Pending Phase 5A.3
- ⏳ GitHub Actions: <2min total - Pending Phase 5A.2

**Migration Timeline**:
- **Phase 5A** (Week 1): CI/CD infrastructure ⏳ In Progress
- **Phase 5B** (Week 2): Protocol interfaces ⏳ Pending
- **Phase 5C** (Week 3): Integration tests ⏳ Pending
- **Phase 5D** (6-12 months): Full legacy migration ⏳ Planned

For questions or issues, refer to the [Troubleshooting](#troubleshooting) section or create an issue in the project repository.
