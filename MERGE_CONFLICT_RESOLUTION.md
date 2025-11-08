# Merge Conflict Resolution Guide

**Branch**: `claude/hybrid-architecture-phase1-011CUpBUu4tdZFSVjXTHTWP9`
**Target**: `main`
**Conflict File**: `src/learning/iteration_executor.py`

---

## 🔍 Conflict Analysis

### Cause
The `main` branch has been updated with changes to `iteration_executor.py` that conflict with our Factor Graph integration changes.

### Key Differences in Main Branch

1. **Import changes**:
   ```python
   # Main added:
   from dataclasses import asdict
   from typing import Any, Callable, Dict, List, Optional, Tuple  # Added List
   from src.backtest.error_classifier import ErrorClassifier  # Changed module

   # Our branch has:
   from typing import Any, Callable, Dict, Optional, Tuple
   from src.backtest.classifier import SuccessClassifier  # Old module
   ```

2. **Class attribute changes**:
   ```python
   # Main changed: success_classifier → error_classifier
   ```

---

## ✅ Resolution Strategy

### Option 1: Rebase on Main (Recommended)

This will replay our changes on top of main's latest changes.

```bash
# 1. Fetch latest main
git fetch origin main

# 2. Rebase our branch on main
git rebase origin/main

# 3. Fix conflicts when they appear (see below)

# 4. Continue rebase
git add src/learning/iteration_executor.py
git rebase --continue

# 5. Force push (rebase rewrites history)
git push -f origin claude/hybrid-architecture-phase1-011CUpBUu4tdZFSVjXTHTWP9
```

### Option 2: Merge Main into Our Branch

```bash
# 1. Merge main into our branch
git merge origin/main

# 2. Fix conflicts (see below)

# 3. Commit merge
git add src/learning/iteration_executor.py
git commit -m "Merge main into factor-graph-integration branch"

# 4. Push
git push origin claude/hybrid-architecture-phase1-011CUpBUu4tdZFSVjXTHTWP9
```

---

## 🔧 How to Fix Conflicts

### Step 1: Accept Main's Import Changes

**Use Main's imports** (they are more up-to-date):

```python
"""Iteration Executor for Phase 5.

Executes a single iteration of the autonomous learning loop with 10-step process:
1. Load recent history
2. Generate feedback
3. Decide LLM or Factor Graph (based on innovation_rate)
4. Generate strategy (call LLM or Factor Graph)
5. Execute strategy (Phase 2 BacktestExecutor)
6. Extract metrics (Phase 2 MetricsExtractor)
7. Classify success (Phase 2 SuccessClassifier)
8. Update champion if better
9. Create IterationRecord
10. Return record

This refactored from autonomous_loop.py (~800 lines extracted).
"""

import logging
import random
from dataclasses import asdict  # ← FROM MAIN
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple  # ← FROM MAIN (added List)

from src.backtest.executor import BacktestExecutor, ExecutionResult
from src.backtest.metrics import MetricsExtractor
from src.backtest.error_classifier import ErrorClassifier  # ← FROM MAIN (renamed)
from src.learning.champion_tracker import ChampionTracker
from src.learning.feedback_generator import FeedbackGenerator
from src.learning.iteration_history import IterationHistory, IterationRecord
from src.learning.llm_client import LLMClient

logger = logging.getLogger(__name__)
```

### Step 2: Keep Our Factor Graph Changes

In `__init__` method, **keep our additions**:

```python
def __init__(
    self,
    llm_client: LLMClient,
    feedback_generator: FeedbackGenerator,
    backtest_executor: BacktestExecutor,
    champion_tracker: ChampionTracker,
    history: IterationHistory,
    config: Dict[str, Any],
):
    # ... existing initialization ...

    # Initialize Phase 2 components
    self.metrics_extractor = MetricsExtractor()
    self.error_classifier = ErrorClassifier()  # ← USE MAIN'S NAME (was success_classifier)

    # Initialize finlab data and sim (lazy loading)
    self.data = None
    self.sim = None
    self._finlab_initialized = False

    # === Factor Graph Support === ← KEEP OUR ADDITIONS
    # Strategy DAG registry (maps strategy_id -> Strategy object)
    # Stores strategies created during iterations for execution
    self._strategy_registry: Dict[str, Any] = {}

    # Factor logic registry (maps factor_id -> logic Callable)
    # Used for Strategy serialization/deserialization (future feature)
    self._factor_logic_registry: Dict[str, Callable] = {}

    logger.info("IterationExecutor initialized")
```

### Step 3: Update All References

Search and replace in the file:

```python
# Change all instances of:
self.success_classifier

# To:
self.error_classifier
```

This includes the line around 494-495:
```python
# Old (our version):
classification_result = self.success_classifier.classify_single(strategy_metrics)

# New (after fix):
classification_result = self.error_classifier.classify_single(strategy_metrics)
```

### Step 4: Keep All Our Factor Graph Methods

Keep these complete methods (no changes from main):
- `_generate_with_factor_graph()` (lines 368-474)
- `_create_template_strategy()` (lines 476-527)
- `_cleanup_old_strategies()` (lines 529-596)
- Factor Graph execution path in `_execute_strategy()` (lines 562-595)
- Champion update fix in `_update_champion_if_better()` (lines 714-723)

---

## 📝 Detailed Conflict Resolution Steps

### Step-by-Step Commands

```bash
# 1. Start fresh
cd /home/user/LLM-strategy-generator
git status  # Make sure working tree is clean

# 2. Fetch latest
git fetch origin main

# 3. Start merge
git merge origin/main

# 4. You'll see conflict message. Open the file:
# The file will have conflict markers:
# <<<<<<< HEAD (our changes)
# =======
# >>>>>>> origin/main (their changes)

# 5. Edit the file to resolve conflicts
# Use the resolution strategy above

# 6. After fixing, mark as resolved
git add src/learning/iteration_executor.py

# 7. Complete the merge
git commit -m "Merge main: resolve iteration_executor.py conflicts

- Accept main's import changes (asdict, List, ErrorClassifier)
- Keep our Factor Graph integration (6 changes)
- Update success_classifier → error_classifier references
- All Factor Graph methods preserved
"

# 8. Push
git push origin claude/hybrid-architecture-phase1-011CUpBUu4tdZFSVjXTHTWP9
```

---

## 🔍 What to Keep from Each Branch

### From Main Branch (Accept These)
- ✅ `from dataclasses import asdict`
- ✅ `List` in typing imports
- ✅ `from src.backtest.error_classifier import ErrorClassifier`
- ✅ `self.error_classifier` (renamed from success_classifier)

### From Our Branch (Keep These)
- ✅ `Callable` in typing imports
- ✅ Internal registries (`_strategy_registry`, `_factor_logic_registry`)
- ✅ All Factor Graph methods:
  - `_generate_with_factor_graph()`
  - `_create_template_strategy()`
  - `_cleanup_old_strategies()`
- ✅ Factor Graph execution path
- ✅ Champion update fix (critical!)
- ✅ Registry cleanup call in `execute_iteration()`

---

## ⚠️ Critical Points

### 1. success_classifier → error_classifier

**Must change ALL occurrences**:
```python
# Line ~91: Initialization
self.error_classifier = ErrorClassifier()  # Was: success_classifier

# Line ~494: Usage
classification_result = self.error_classifier.classify_single(strategy_metrics)  # Was: success_classifier
```

### 2. Import List

Main branch uses `List` type hint somewhere, so keep it:
```python
from typing import Any, Callable, Dict, List, Optional, Tuple
```

### 3. asdict Import

Main branch added `from dataclasses import asdict`. Keep it even if we don't use it.

---

## ✅ Verification After Resolution

### 1. Syntax Check
```bash
python3 -m py_compile src/learning/iteration_executor.py
```

### 2. Check No Conflict Markers Left
```bash
grep -n "<<<<<<< HEAD\|=======\|>>>>>>>" src/learning/iteration_executor.py
# Should return nothing
```

### 3. Verify Factor Graph Methods Still Present
```bash
grep -n "def _generate_with_factor_graph" src/learning/iteration_executor.py
grep -n "def _create_template_strategy" src/learning/iteration_executor.py
grep -n "def _cleanup_old_strategies" src/learning/iteration_executor.py
# Should all return line numbers
```

### 4. Verify error_classifier Used
```bash
grep -n "self.success_classifier" src/learning/iteration_executor.py
# Should return nothing (all changed to error_classifier)

grep -n "self.error_classifier" src/learning/iteration_executor.py
# Should return 2 lines (initialization and usage)
```

---

## 🚨 If You Get Stuck

### Abort and Start Over
```bash
git merge --abort  # or git rebase --abort
# Then try again with this guide
```

### Ask for Help
Provide these details:
1. Output of `git status`
2. Conflict markers in the file
3. Which resolution strategy you chose (rebase or merge)

---

## 📋 Final Checklist

After resolving conflicts:

- [ ] All conflict markers removed (`<<<<<<<`, `=======`, `>>>>>>>`)
- [ ] Main's imports accepted (asdict, List, ErrorClassifier)
- [ ] All our Factor Graph code preserved
- [ ] `success_classifier` → `error_classifier` everywhere
- [ ] Syntax validation passed
- [ ] No grep warnings
- [ ] Committed and pushed

---

## 🎯 Expected Result

After successful resolution:

```python
# Top of file (merged imports)
from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, Tuple
from src.backtest.error_classifier import ErrorClassifier

# In __init__ (merged initialization)
self.error_classifier = ErrorClassifier()
self._strategy_registry: Dict[str, Any] = {}
self._factor_logic_registry: Dict[str, Callable] = {}

# Our Factor Graph methods (preserved)
def _generate_with_factor_graph(...)  # Line ~368
def _create_template_strategy(...)    # Line ~476
def _cleanup_old_strategies(...)      # Line ~529

# Updated reference
self.error_classifier.classify_single(...)  # Line ~494
```

---

**Good luck with the merge!** 🚀

If you encounter any issues, feel free to ask for help.
