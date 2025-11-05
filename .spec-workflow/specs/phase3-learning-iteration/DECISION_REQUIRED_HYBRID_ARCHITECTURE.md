# DECISION REQUIRED: Hybrid Architecture for Phase 5

**Date**: 2025-11-05
**Status**: ⏸️ **BLOCKED - AWAITING USER DECISION**
**Urgency**: HIGH (blocks Phase 5 implementation)

---

## Quick Summary

The `to_python_code()` method **does not exist** in Factor Graph. Current plan assumed it exists.

**Two options**:
- **Option A**: Write complex code serializer (+2-3 days, HIGH risk)
- **Option B**: Hybrid architecture - store both code strings AND Strategy objects (+1 day, MEDIUM risk)

**Recommendation**: ✅ **Option B** - cleaner, faster, more maintainable

---

## The Problem

### What We Assumed (WRONG)

```python
# Original plan assumed this works:
strategy = add_factor(base_strategy, "exit_factor")
code = strategy.to_python_code()  # ❌ METHOD DOESN'T EXIST
result = execute(code)
```

### What Actually Exists

```python
# Factor Graph only works with DAG objects:
strategy = add_factor(base_strategy, "exit_factor")
result = strategy.to_pipeline(data)  # ✅ Works, but returns DataFrame not code
```

**Incompatibility**: LLM path uses **code strings**, Factor Graph uses **Strategy objects**

---

## Option A: Implement Code Serializer

### What It Requires

Add `to_python_code()` method to Strategy class (~200-300 lines):

```python
def to_python_code(self) -> str:
    """Serialize Strategy DAG to executable Python code."""
    # Complex implementation:
    # - Generate imports for all factors
    # - Serialize factor parameters
    # - Generate factor instantiation code
    # - Generate DAG dependency wiring
    # - Generate execution pipeline
    # - Return as valid Python code string
```

### Pros & Cons

**Pros**:
- ✅ Keeps existing code string architecture
- ✅ LLM and Factor Graph both produce code strings

**Cons**:
- ❌ Complex implementation (200-300 lines)
- ❌ Brittle (breaks when Factor API changes)
- ❌ Hard to maintain
- ❌ +2-3 days implementation time
- ❌ HIGH risk (code generation is error-prone)

### Timeline Impact

**Additional Time**: +2-3 days
**Risk Level**: 🔴 HIGH

---

## Option B: Hybrid Architecture (RECOMMENDED)

### What It Requires

Support **both** generation methods natively:

```python
@dataclass
class ChampionStrategy:
    """Champion can be LLM code OR Factor Graph Strategy."""
    code: Optional[str] = None         # For LLM strategies
    strategy: Optional[Strategy] = None  # For Factor Graph strategies
    generation_method: str = "unknown"  # "llm" or "factor_graph"
    metrics: Dict[str, float] = field(default_factory=dict)
    ...

    def execute(self, data):
        """Execute regardless of generation method."""
        if self.generation_method == "llm":
            return execute_code_string(self.code, data)
        else:
            return self.strategy.to_pipeline(data)
```

### Pros & Cons

**Pros**:
- ✅ Clean architecture (each method native)
- ✅ No brittle code generation
- ✅ Future-proof (easy to add more methods)
- ✅ Easier to test (both paths testable)
- ✅ Only +1 day implementation
- ✅ More maintainable

**Cons**:
- ⚠️ More extensive changes across files
- ⚠️ Need to handle serialization differently
- ⚠️ Slightly more complex champion storage

### Timeline Impact

**Additional Time**: +1 day
**Risk Level**: 🟡 MEDIUM

---

## Implementation Comparison

### Files to Change

| File | Option A | Option B |
|------|----------|----------|
| `strategy.py` | +200 lines | No change |
| `ChampionStrategy` | No change | +10 lines |
| `BacktestExecutor` | No change | +30 lines |
| `ChampionTracker` | No change | +20 lines |
| `IterationHistory` | No change | +15 lines |
| **Total Changes** | 200 lines | 75 lines |
| **Complexity** | HIGH | MEDIUM |
| **Timeline** | +2-3 days | +1 day |

### Code Quality

| Metric | Option A | Option B |
|--------|----------|----------|
| Maintainability | 🔴 LOW | 🟢 HIGH |
| Testability | 🟡 MEDIUM | 🟢 HIGH |
| Brittleness | 🔴 HIGH | 🟢 LOW |
| Future-proof | 🟡 MEDIUM | 🟢 HIGH |

---

## Recommended Decision

### ✅ **Adopt Option B: Hybrid Architecture**

**Reasons**:

1. **Faster**: +1 day vs. +2-3 days
2. **Cleaner**: Each method works natively, no forced conversion
3. **Safer**: Less brittle than code generation
4. **Future-proof**: Easy to add more generation methods later
5. **Maintainable**: 75 lines vs. 200 lines of complex serialization

**Quote from Analysis**:
> "The Factor Graph team likely avoided `to_python_code()` for good reasons: complexity, brittleness, maintenance burden."

---

## Revised Timeline (if Option B approved)

### Day 0 (Today): Hybrid Architecture Foundation (3 hours)

**Tasks**:
1. Update `ChampionStrategy` dataclass (hybrid fields)
2. Update `BacktestExecutor.execute()` to handle Strategy objects
3. Write basic hybrid execution tests
4. Update documentation

**Deliverables**:
- ✅ Hybrid ChampionStrategy working
- ✅ Both code and Strategy execution paths tested
- ✅ Ready for Day 1 implementation

### Day 1-3: Phase 5 Implementation (Original Plan)

**No further changes** - Day 1-3 tasks remain as originally planned, just use hybrid architecture.

**Total Phase 5 Timeline**: 3.5 days (instead of 5-6 days with Option A)

---

## Decision Checklist

### If You Approve Option B

User action required:
- [ ] Say "approve Option B" or "請採用Option B"
- [ ] I will immediately start Day 0 implementation (3 hours)
- [ ] Phase 5 continues with +1 day timeline impact

### If You Want Option A

User action required:
- [ ] Say "prefer Option A" or "選擇Option A"
- [ ] I will implement `to_python_code()` serializer
- [ ] Phase 5 continues with +2-3 day timeline impact

### If You Need More Information

User can ask:
- Details about hybrid execution flow
- Risk analysis for either option
- Alternative approaches
- Timeline breakdown

---

## Quick Q&A

**Q: Why didn't we catch this earlier?**
A: The deep analysis assumed `to_python_code()` existed based on typical DAG serialization patterns. Verification step revealed it doesn't exist.

**Q: Can we skip Factor Graph fallback?**
A: Yes, but Phase 5 spec requires it for robustness when LLM fails repeatedly.

**Q: How does hybrid architecture handle champion comparison?**
A: Both methods produce metrics (Sharpe, returns, etc.) - champion comparison is metric-based, generation-method agnostic.

**Q: What about serialization?**
A: LLM code serializes as-is. Factor Graph Strategy objects serialize as Strategy ID + parameters, stored separately.

**Q: Performance impact?**
A: None - both execution paths have similar performance (<2s overhead target).

---

## Recommendation Summary

**Recommended**: ✅ **Option B (Hybrid Architecture)**

**Rationale**: Faster (+1 day vs +2-3), cleaner (no brittle serialization), more maintainable (75 lines vs 200), future-proof (easy to extend).

**Next Action**: Await user approval to start Day 0 hybrid architecture implementation.

---

**Status**: ⏸️ **AWAITING DECISION**
**Created**: 2025-11-05
**Decision Needed By**: Before starting Phase 5 Day 1
