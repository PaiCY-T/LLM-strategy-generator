# Factor Graph Root Cause Analysis

**Date**: 2025-11-01 23:15 UTC
**Status**: 🔴 **ROOT CAUSE IDENTIFIED**

---

## Root Cause: Missing Factor Graph Implementation

### The Bug

**Location**: `artifacts/working/modules/autonomous_loop.py` lines 1093-1203

**Issue**: Decision logic exists to choose between LLM and Factor Graph, but **Factor Graph code path is not implemented**.

---

## Code Flow Analysis

### Step 1: Decision Logic (WORKS)

**File**: `autonomous_loop.py` lines 1093-1099

```python
# Decide: LLM innovation or Factor Graph mutation?
use_llm = (self.llm_enabled and
           self.innovation_engine is not None and
           random.random() < self.innovation_rate)

generation_method = "llm" if use_llm else "factor_graph"
```

**Result**: With `innovation_rate=0.05`:
- `use_llm=True` ~5% of the time
- `use_llm=False` ~95% of the time → should use Factor Graph

---

### Step 2: Generation Call (BROKEN)

**File**: `autonomous_loop.py` lines 1194-1198

```python
code = generate_strategy(
    iteration_num=iteration_num,
    history=feedback_summary or "",
    model=self.model
)
```

**Problem**: Calls `generate_strategy()` for BOTH LLM and Factor Graph cases!

---

### Step 3: generate_strategy() Implementation (LLM ONLY)

**File**: `artifacts/working/modules/poc_claude_test.py` lines 16-49

```python
def generate_strategy(iteration_num=0, history="", model="gemini-2.5-flash"):
    """
    Generate a trading strategy using Google AI API first, with OpenRouter as fallback
    """
    # Try Google AI first (primary)
    try:
        print("🎯 Attempting Google AI (primary)...")
        google_model = model.split('/')[-1] if '/' in model else model
        return _generate_with_google_ai(iteration_num, history, google_model)
    except Exception as e:
        print(f"⚠️ Google AI failed: {e}")
        print("🔄 Falling back to OpenRouter...")

        # Fallback to OpenRouter
        try:
            openrouter_model = f"google/{model}" if '/' not in model else model
            return _generate_with_openrouter(iteration_num, history, openrouter_model)
        except Exception as e2:
            print(f"❌ OpenRouter fallback also failed: {e2}")
            raise RuntimeError(f"Both APIs failed. Google AI: {e}, OpenRouter: {e2}")
```

**Problem**: This function ONLY implements LLM generation (Google AI → OpenRouter)
- No Factor Graph code path
- No template selection
- No mutations
- Always calls external API

**Result**: Even when `use_llm=False`, system calls `generate_strategy()` which uses LLM anyway!

---

## Why 100% LLM Usage

```
Iteration 1: random.random() = 0.92 → use_llm=False → "factor_graph"
  → Calls generate_strategy()
    → Google AI API called
    → Returns LLM-generated code ❌

Iteration 2: random.random() = 0.03 → use_llm=True → "llm"
  → Calls generate_strategy()
    → Google AI API called
    → Returns LLM-generated code ✅

Iteration 3: random.random() = 0.78 → use_llm=False → "factor_graph"
  → Calls generate_strategy()
    → Google AI API called
    → Returns LLM-generated code ❌

... (repeat)

Result: 100% LLM, 0% Factor Graph
```

---

## What Factor Graph SHOULD Do

**Expected behavior when `use_llm=False`**:

```python
# Pseudocode for Factor Graph path
if not use_llm:
    # 1. Select template (rotate between Momentum, Turtle, Mastiff)
    template = select_template(iteration_num)  # Round-robin

    # 2. Create base strategy from template
    strategy = template.create_base_strategy()

    # 3. Mutate strategy (add/remove/replace factors)
    mutated = mutate_strategy(strategy, champion)

    # 4. Generate Python code from strategy DAG
    code = strategy.to_python_code()

    return code
```

**Actual behavior**: None of this exists in `generate_strategy()`.

---

## Available Components (But Not Connected)

### Factor Graph Components Exist:

✅ `src/factor_graph/strategy.py` - Strategy DAG class
✅ `src/factor_graph/mutations.py` - add_factor(), remove_factor(), replace_factor()
✅ `src/factor_graph/factor.py` - Factor class
✅ `src/templates/momentum_template.py` - Momentum template
✅ `src/templates/turtle_template.py` - Turtle template
✅ `src/templates/mastiff_template.py` - Mastiff template
✅ `src/templates/factor_template.py` - Generic factor template

### What's Missing:

❌ Template rotation logic (select which template to use)
❌ Strategy → Python code generator
❌ Integration into autonomous_loop.py
❌ Mutation orchestration (which mutations to apply)

---

## Fix Strategy

### Option 1: Implement Missing Factor Graph Path ⭐ RECOMMENDED

**Create**: `src/generators/factor_graph_generator.py`

```python
def generate_via_factor_graph(iteration_num: int, champion=None):
    """
    Generate strategy using Factor Graph templates and mutations.

    Steps:
    1. Select template (round-robin: Momentum → Turtle → Mastiff → Factor)
    2. Create base strategy from template
    3. Apply mutations based on champion
    4. Generate Python code

    Returns:
        str: Generated Python code
    """
    from src.templates.momentum_template import MomentumTemplate
    from src.templates.turtle_template import TurtleTemplate
    from src.templates.mastiff_template import MastiffTemplate
    from src.templates.factor_template import FactorTemplate
    from src.factor_graph.mutations import add_factor, remove_factor

    # Step 1: Select template (rotate)
    templates = [MomentumTemplate(), TurtleTemplate(), MastiffTemplate(), FactorTemplate()]
    template = templates[iteration_num % len(templates)]

    # Step 2: Create base strategy
    strategy = template.create_base_strategy()

    # Step 3: Mutate (if champion exists, do informed mutations)
    if champion:
        # Intelligent mutations based on champion
        strategy = mutate_with_champion_context(strategy, champion)
    else:
        # Random mutations for exploration
        strategy = random_mutation(strategy)

    # Step 4: Generate Python code
    code = strategy.to_python_code()

    return code
```

**Update**: `autonomous_loop.py` line 1194

```python
# Before (CURRENT - BROKEN):
code = generate_strategy(
    iteration_num=iteration_num,
    history=feedback_summary or "",
    model=self.model
)

# After (FIXED):
if use_llm:
    # LLM path
    code = generate_strategy(
        iteration_num=iteration_num,
        history=feedback_summary or "",
        model=self.model
    )
else:
    # Factor Graph path (NEW)
    from src.generators.factor_graph_generator import generate_via_factor_graph
    code = generate_via_factor_graph(
        iteration_num=iteration_num,
        champion=self.champion
    )
```

**Time**: 2-3 hours
- Create factor_graph_generator.py (1 hour)
- Implement Strategy.to_python_code() (30 min)
- Update autonomous_loop.py (15 min)
- Test with 10 iterations (30 min)
- Debug issues (30 min)

**Impact**: Restores 95% Factor Graph → Diversity 35-45

---

### Option 2: Quick Hack - Force Templates via LLM Prompts

**Update**: `poc_claude_test.py` to include template context

```python
def generate_strategy(iteration_num=0, history="", model="gemini-2.5-flash", template_hint=None):
    """
    Generate strategy with optional template hint
    """
    template = load_prompt_template()

    # Add template guidance to prompt
    if template_hint:
        templates = ["Momentum", "Turtle", "Mastiff", "Factor"]
        suggested_template = templates[iteration_num % len(templates)]

        template = template.replace(
            "Generate a trading strategy",
            f"Generate a {suggested_template}-style trading strategy following these patterns:\n"
            f"[Template-specific guidance here]"
        )

    # Rest of existing code...
```

**Time**: 30 minutes
**Impact**: Limited - still using LLM, just with template hints
**Diversity**: 25-30 (marginal improvement)

---

### Option 3: Disable Factor Graph, Optimize LLM Diversity

**Accept**: Factor Graph is incomplete, use 100% LLM
**Implement**: Diversity-aware prompting (Gemini recommendation)
**Increase**: innovation_rate to 30% (more varied prompts)

**Time**: 1.5 hours
**Impact**: Compensates for missing Factor Graph
**Diversity**: 30-40

---

## Recommendation

### Immediate Fix (Next 30 minutes): Option 3
- Accept Factor Graph is incomplete feature
- Implement diversity-aware prompting for LLM
- Update DIVERSITY_IMPROVEMENT_STRATEGY.md to reflect this finding
- Re-run Phase 2 with improved prompts

**Rationale**:
- Factor Graph implementation is 2-3 hours of work
- Not sure if Strategy.to_python_code() exists or needs implementation
- Unknown how mature the template classes are
- Quicker to optimize what's working (LLM) than fix what's broken

### Long-term Fix (Future): Option 1
- Implement complete Factor Graph path
- Full template rotation
- Proper mutation orchestration
- Test thoroughly

---

## Files to Create/Modify

### Option 1 (Factor Graph):
- **CREATE**: `src/generators/factor_graph_generator.py` (new file)
- **MODIFY**: `artifacts/working/modules/autonomous_loop.py` (line 1194)
- **VERIFY**: `src/factor_graph/strategy.py` has `to_python_code()` method
- **VERIFY**: Templates have `create_base_strategy()` method

### Option 3 (LLM Optimization):
- **MODIFY**: `artifacts/working/modules/poc_claude_test.py` (add population context)
- **MODIFY**: `artifacts/working/modules/prompt_builder.py` (diversity-aware prompts)
- **MODIFY**: `config/learning_system.yaml` (increase innovation_rate to 30%)

---

## Testing Plan

### For Option 1:
```bash
# Test Factor Graph in isolation
python3 -c "
from src.generators.factor_graph_generator import generate_via_factor_graph
code = generate_via_factor_graph(iteration_num=0)
print('Generated code length:', len(code))
print('First 500 chars:', code[:500])
"

# Test in autonomous loop (5 iterations)
python3 -c "
from artifacts.working.modules.autonomous_loop import AutonomousLoop
loop = AutonomousLoop(...)
loop.run(max_iterations=5)
"

# Verify usage distribution
python3 -c "
import json
with open('iteration_history.json', 'r') as f:
    data = json.load(f)
records = data['records'][-5:]  # Last 5
llm_count = sum(1 for r in records if r.get('model'))
factor_count = len(records) - llm_count
print(f'LLM: {llm_count}, Factor Graph: {factor_count}')
# Expected: LLM: 0-1, Factor Graph: 4-5
"
```

---

## Conclusion

**Root Cause**: `generate_strategy()` only implements LLM, no Factor Graph code path exists.

**Impact**: 100% LLM usage → low diversity (19.17/100)

**Fix Options**:
1. ⭐ Implement Factor Graph (2-3 hours, high impact)
2. Quick hack with templates (30 min, low impact)
3. Optimize LLM diversity (1.5 hours, medium impact)

**Recommendation**: Option 3 for immediate progress, Option 1 for long-term fix.

---

**Next Action**: Choose fix approach
- `A` - Option 1: Implement Factor Graph (2-3 hours)
- `B` - Option 3: Optimize LLM diversity (1.5 hours)
- `C` - Hybrid: Start Option 3 now, Option 1 later

---

**Generated**: 2025-11-01 23:15 UTC
**Status**: 🔴 **BLOCKING ISSUE IDENTIFIED**
**Priority**: P0 CRITICAL
