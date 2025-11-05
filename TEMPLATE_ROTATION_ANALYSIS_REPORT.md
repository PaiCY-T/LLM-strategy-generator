# Template Rotation Analysis Report

**Date**: 2025-11-01 23:00 UTC
**Purpose**: Verify template rotation to diagnose low diversity (19.17/100)
**Status**: 🔴 **CRITICAL ISSUE FOUND**

---

## Executive Summary

**CRITICAL FINDING**: System is using **LLM for 100% of iterations** instead of configured 5%.

- **Configured**: 5% LLM, 95% Factor Graph templates
- **Actual**: 100% LLM, 0% Factor Graph
- **Impact**: Explains low diversity - no template variety
- **Root Cause**: Factor Graph not being used (TBD: bug or logging issue)

---

## Analysis Methodology

### 1. Configuration Review

**File**: `config/learning_system.yaml`

```yaml
llm:
  enabled: true
  innovation_rate: 0.05  # 5% should use LLM
```

**Expected Behavior**:
- 5% of iterations: LLM-generated strategies
- 95% of iterations: Factor Graph templates (Momentum, Turtle, Mastiff, etc.)

---

### 2. Iteration History Analysis

**File**: `iteration_history.json`

**Total Records**: 626 iterations

**Generation Method Distribution**:
```
LLM (with model field set):     626 (100.0%)
Factor Graph (no model field):    0 (0.0%)
```

**Model Distribution**:
```
google/gemini-2.5-flash:      376 (60.1%)
gemini-2.5-flash:             229 (36.6%)
gemini-2.5-flash-lite:         21 (3.4%)
```

**Mode Distribution**:
```
mode=None:                    626 (100.0%)
mode='template':                0 (0.0%)
mode='factor_graph':            0 (0.0%)
```

---

### 3. Code Review

**File**: `artifacts/working/modules/autonomous_loop.py`

**LLM/Factor Graph Decision Logic** (lines 1093-1096):
```python
# Decide: LLM innovation or Factor Graph mutation?
use_llm = (self.llm_enabled and
           self.innovation_engine is not None and
           random.random() < self.innovation_rate)

generation_method = "llm" if use_llm else "factor_graph"
```

**Logic is CORRECT** - should result in ~5% LLM usage.

**Fallback Logic** (lines 1149-1162):
```python
if llm_failed:
    # LLM failed - fallback to Factor Graph
    print(f"⚠️  LLM innovation failed, falling back to Factor Graph")
    generation_method = "factor_graph_fallback"
```

---

## Root Cause Hypotheses

### Hypothesis 1: Factor Graph Always Fails → Falls Back to LLM ⭐ MOST LIKELY
- Factor Graph attempts fail (bug, missing dependency, config issue)
- System falls back to LLM 100% of the time
- LLM succeeds, so iteration completes successfully
- Fallback is silent or logs are not visible

**Evidence**:
- All 626 records have LLM model set
- No "factor_graph_fallback" in generation_method logs
- Code has fallback logic at line 1151

**Next Steps**:
- Search logs for "falling back to Factor Graph" messages
- Check if Factor Graph code is broken
- Verify Factor Graph dependencies are installed

---

### Hypothesis 2: Factor Graph Not Logging to iteration_history.json
- Factor Graph strategies ARE generated but not logged
- Only LLM strategies get logged to iteration_history

**Evidence**:
- 626 iteration records (LLM) but 200 strategy files exist
- Discrepancy might indicate missing logs

**Counter-Evidence**:
- If Factor Graph was working, we'd expect ~594 Factor Graph records (95% of 626)
- We have 0 Factor Graph records

**Conclusion**: UNLIKELY - would still see failures/attempts logged

---

### Hypothesis 3: Configuration Not Loaded Correctly
- `learning_system.yaml` config not being used
- System using hardcoded defaults with higher LLM rate

**Evidence**:
- innovation_rate might be ignored or overridden

**Counter-Evidence**:
- autonomous_loop.py code explicitly loads `innovation_rate` from config
- Would need to verify actual loaded value during runtime

**Next Steps**:
- Add logging to print loaded `innovation_rate` value
- Check if config file path is correct

---

## Impact on Diversity

**Why 100% LLM Usage Causes Low Diversity**:

1. **No Template Variety**
   - Missing: Momentum, Turtle, Mastiff, Factor templates
   - All strategies come from same LLM source (Gemini)
   - Same prompt template used for all LLM calls

2. **Prompt Convergence**
   - LLM receives similar context/feedback each iteration
   - Tends to converge to similar factor combinations
   - No structural variation from different templates

3. **Missing Factor Graph Diversity**
   - Factor Graph uses predefined templates as starting points
   - Templates have different factor categories and structures
   - Mutations would explore different parts of factor space

**Expected Diversity if Factor Graph Worked**:
- With 95% Factor Graph: Strategies would start from diverse templates
- With template rotation: Guaranteed variety (Momentum, Turtle, Mastiff)
- With mutations: Each template explores different parameter space

**Result**: Diversity would likely be 35-50 instead of 19.17

---

## Recommended Actions

### Immediate (Next 30 minutes)

1. **Check Logs for Factor Graph Failures**
   ```bash
   grep -i "factor graph" iteration_history.json
   grep -i "fallback" iteration_history.json
   ```

2. **Verify Factor Graph Code Exists and Works**
   ```bash
   python3 -c "from src.factor_graph.strategy import Strategy; print('OK')"
   python3 -c "from src.factor_graph.mutations import add_factor; print('OK')"
   ```

3. **Test Factor Graph in Isolation**
   ```python
   # Create simple test to verify Factor Graph works
   from src.factor_graph.strategy import Strategy
   from src.factor_graph.mutations import add_factor

   strategy = Strategy()  # Create empty strategy
   mutated = add_factor(strategy, "momentum_factor", {}, "leaf")
   print("Factor Graph works!")
   ```

---

### Short-term (1-2 hours)

4. **Fix Factor Graph Issue**
   - If missing dependency: Install it
   - If code bug: Fix the bug
   - If config issue: Correct configuration

5. **Add Logging to Autonomous Loop**
   - Log "Using Factor Graph" message when Factor Graph is chosen
   - Log Factor Graph failure details if fallback occurs
   - Count LLM vs Factor Graph usage during run

6. **Re-run Phase 2 with Working Factor Graph**
   - 20-30 iterations with 5% LLM, 95% Factor Graph
   - Monitor generation method distribution
   - Verify diversity improves

---

### Medium-term (2-4 hours)

7. **Implement Diversity-Aware Prompting** (from Gemini recommendation)
   - Even if using 100% LLM, add population context to prompts
   - Guide LLM to create diverse strategies
   - May achieve diversity ≥40 without fixing Factor Graph

8. **Increase LLM Innovation Rate** (interim solution)
   - If Factor Graph is broken and can't be fixed quickly
   - Increase innovation_rate to 30% (from 5%)
   - Use diversity-aware prompting to compensate

---

## Critical Questions

### Q1: Is Factor Graph actually installed/available?
**How to Check**:
```python
import sys
sys.path.insert(0, '/mnt/c/Users/jnpi/documents/finlab')
from src.factor_graph.strategy import Strategy
from src.factor_graph.mutations import add_factor, remove_factor
print("Factor Graph is available!")
```

### Q2: Are there error logs showing Factor Graph failures?
**How to Check**:
```bash
# Search for error messages
grep -i "error" iteration_history.json | grep -i "factor"
grep -i "failed" iteration_history.json | grep -i "graph"
```

### Q3: What happens if we force Factor Graph usage?
**How to Test**:
```python
# Temporarily set innovation_rate to 0.0 (force Factor Graph)
# Run 5 iterations
# Check if strategies are generated successfully
```

---

## Revised Diversity Improvement Strategy

### Option A: Fix Factor Graph (RECOMMENDED)
**Time**: 1-2 hours
**Impact**: HIGH - restores intended design
**Approach**:
1. Diagnose Factor Graph failure
2. Fix root cause
3. Re-run Phase 2 with 5% LLM, 95% Factor Graph
4. Expected diversity: 35-45

---

### Option B: Compensate with Diversity-Aware Prompting
**Time**: 1.5-2 hours
**Impact**: MEDIUM - works around Factor Graph issue
**Approach**:
1. Keep 100% LLM (accept Factor Graph is broken)
2. Implement population-aware prompts
3. Increase innovation_rate to 30%
4. Expected diversity: 30-40

---

### Option C: Hybrid Approach
**Time**: 3-4 hours
**Impact**: HIGHEST - both fixes
**Approach**:
1. Fix Factor Graph (1-2 hours)
2. Add diversity-aware prompting (1-2 hours)
3. Use 30% LLM, 70% Factor Graph
4. Expected diversity: 45-55

---

## Files Referenced

- `config/learning_system.yaml` (config file)
- `iteration_history.json` (626 iteration records)
- `artifacts/working/modules/autonomous_loop.py` (LLM/Factor Graph logic)
- `src/factor_graph/mutations.py` (Factor Graph code)
- `src/factor_graph/strategy.py` (Factor Graph strategy class)
- `src/templates/*.py` (Template files: Momentum, Turtle, Mastiff)

---

## Next Action

**CRITICAL DECISION POINT**: Choose approach:
- `A` - Diagnose and fix Factor Graph (recommended)
- `B` - Compensate with diversity-aware prompting
- `C` - Hybrid (fix Factor Graph + diversity prompting)

**Recommendation**: Start with **Option A** - diagnose Factor Graph issue. This is likely a simple fix (missing import, config issue) and will restore the intended design. If diagnosis reveals complex issue, fall back to Option B.

---

**Generated**: 2025-11-01 23:00 UTC
**Priority**: 🔴 **P0 CRITICAL**
**Blocks**: Diversity improvement, Phase 3 progression
**Status**: **AWAITING USER DECISION**
