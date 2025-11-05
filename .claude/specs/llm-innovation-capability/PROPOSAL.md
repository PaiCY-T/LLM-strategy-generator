# LLM Innovation Capability - Spec Proposal

**Date**: 2025-10-23
**Author**: User + Claude Code
**Status**: 🔍 PROPOSAL - Awaiting Consensus Review

---

## Executive Summary

**Purpose**: Enable LLM to create novel trading strategy factors and exit mechanisms beyond the current fixed pool of 13 factors.

**Problem**:
- Current system limited to 13 predefined factors (momentum, turtle, exit factors)
- 100-generation evolution runs plateau due to limited search space
- Cannot create breakthrough innovations like "ROE × Revenue Growth / P/E" or "5MA stop loss"

**Solution**:
- Add innovation layer with 5-layer validation
- Build InnovationRepository for knowledge accumulation
- Implement evolutionary pattern extraction for guided exploration

**Expected Outcome**:
- ≥20% performance improvement over baseline
- ≥20 novel, validated innovations in 100 generations
- Diverse exploration of strategy space
- Breakthrough strategies impossible with fixed factor pool

---

## Background

### Current System Capabilities (structural-mutation-phase2)

✅ **Implemented**:
- Factor Graph System (NetworkX DAG architecture)
- 13 predefined factors across 3 categories:
  - Momentum: momentum_factor, ma_filter_factor, revenue_catalyst_factor, earnings_catalyst_factor
  - Turtle: atr_factor, breakout_factor, dual_ma_filter_factor, atr_stop_loss_factor
  - Exit: trailing_stop_factor, time_based_exit_factor, volatility_stop_factor, profit_target_factor, composite_exit_factor
- Three-Tier Mutation System:
  - Tier 1 (YAML): Configuration-based mutations (~80% success rate)
  - Tier 2 (Factor Ops): add_factor, remove_factor, replace_factor (~60% success rate)
  - Tier 3 (AST): Code-level mutations (~50% success rate)
- Performance: 0.16ms DAG compilation, 4.3ms strategy execution (far exceeds targets)
- Validation: 146+ tests, 100% pass rate

❌ **Limitations**:
- Cannot create NEW factors (only recombine existing 13)
- Cannot create NEW exit mechanisms (only adjust parameters)
- Evolution limited to parameter optimization in fixed factor space
- 100-generation runs expected to plateau without innovation capability

### Motivation (from LLM_INNOVATION_CAPABILITY.md)

**User's Original Question**: Can LLM create completely new factors and exit strategies?

**Analysis Result**:
- ❌ Current system: No innovation capability
- ✅ Technical feasibility: Completely viable with proper validation
- 🎯 Implementation: 2-week MVP + 1-month advanced features

**Key Insight**: LLM has code generation capability and domain knowledge. The missing piece is comprehensive validation framework to prevent hallucinations and ensure production quality.

---

## Proposed Solution

### Architecture Stack

```
Current System (structural-mutation-phase2):
┌─────────────────────────────────┐
│   Population Manager            │
├─────────────────────────────────┤
│   Three-Tier Mutation System    │
│   (13 fixed factors)             │
├─────────────────────────────────┤
│   Factor Graph System            │
└─────────────────────────────────┘

Proposed System (+ llm-innovation-capability):
┌─────────────────────────────────┐
│   Population Manager            │
├─────────────────────────────────┤
│ 🆕 Evolutionary Innovation       │  ← Phase 3 (Week 5-8)
│   - Pattern Extraction          │
│   - Diversity Rewards           │
│   - Innovation Lineage          │
│   - Adaptive Exploration        │
├─────────────────────────────────┤
│ 🆕 Innovation MVP                │  ← Phase 2 (Week 2-3)
│   - InnovationValidator (5-layer)│
│   - InnovationRepository        │
│   - Enhanced Prompt Template    │
├─────────────────────────────────┤
│   Three-Tier Mutation System    │  ← EXISTING
├─────────────────────────────────┤
│   Factor Graph System            │  ← EXISTING
└─────────────────────────────────┘
```

### Phase 2: Innovation MVP (Week 2-3)

**Goal**: Enable basic innovation capability with robust validation

**Components**:

1. **InnovationValidator (5-layer pipeline)**
   ```python
   class InnovationValidator:
       def validate(self, innovation_code: str) -> ValidationResult:
           # Layer 1: Syntax - Can Python parse it?
           # Layer 2: Semantic - Type checking, valid imports?
           # Layer 3: Execution - Runs in sandbox without errors?
           # Layer 4: Performance - Sharpe >0.3, MDD <50%?
           # Layer 5: Novelty - Not duplicate in repository?
   ```

2. **InnovationRepository (JSONL knowledge base)**
   ```python
   class InnovationRepository:
       def add_innovation(self, code, performance, metadata)
       def get_top_innovations(self, n=10)
       def search_similar(self, innovation)
       def cleanup_low_performers()  # Remove bottom 20% every 50 gens
   ```

3. **Enhanced Prompt Template**
   - Add "Innovation Encouragement" section
   - Provide examples of successful innovations
   - Include validation guidelines
   - Pass top innovations as context

**Expected Outcome**:
- ✅ LLM can create new factors (e.g., "ROE × Revenue Growth")
- ✅ LLM can create new exit mechanisms (e.g., "5MA stop loss")
- ✅ Innovations automatically validated and stored
- ✅ Performance ≥ baseline (13-factor system)

### Phase 3: Evolutionary Innovation (Week 5-8)

**Goal**: Add intelligent exploration guided by successful patterns

**Components**:

1. **Pattern Extraction**
   - Analyze top 10% strategies for common patterns
   - Extract: factor combinations, parameter ranges, code patterns
   - Store in PatternLibrary
   - Pass as context: "Winners use these patterns, try variations"

2. **Diversity Rewards**
   - Calculate novelty score vs population
   - Combined fitness: 70% performance + 30% novelty
   - Prevent population convergence
   - Maintain exploration in strategy space

3. **Innovation Lineage Tracking**
   - Build ancestry graph: which innovations led to breakthroughs
   - Identify "golden lineages"
   - Visualize evolution tree
   - Guide future exploration toward promising branches

4. **Adaptive Exploration Rate**
   - Default innovation rate: 20% of iterations
   - Breakthrough detected → increase to 40%
   - Stagnation (5 gens no improvement) → increase to 50%
   - Stable improvement → maintain 20%

**Expected Outcome**:
- ✅ Directed exploration (not random innovation)
- ✅ Performance >baseline by ≥20%
- ✅ Diverse population maintained
- ✅ Evolutionary learning from success

---

## Implementation Timeline

| Week | Phase | Tasks | Deliverables |
|------|-------|-------|--------------|
| 1 | Phase 0: Baseline | Task 0.1 | 20-gen baseline test results |
| 2-3 | Phase 2: Innovation MVP | Tasks 2.1-2.4 | InnovationValidator, Repository, Prompt |
| 4 | Phase 2: Validation | Task 2.5 | 20-gen smoke test with innovation |
| 5-8 | Phase 3: Evolutionary | Tasks 3.1-3.4 | Pattern extraction, diversity, lineage, adaptive |
| 9 | Phase 3: Final | Task 3.5 | 100-gen final validation |

**Total Duration**: 9 weeks
**Dependencies**: structural-mutation-phase2 (Phase D Complete ✅)

---

## Success Criteria

### Phase 2 Success (Week 4)
- [ ] ≥5 novel innovations validated
- [ ] Innovation success rate ≥30% (of validation attempts)
- [ ] Performance ≥ baseline (Task 0.1)
- [ ] Zero system crashes or validation failures
- [ ] At least 1 innovation used in top-3 strategies

### Phase 3 Success (Week 9)
- [ ] 100 generations complete successfully
- [ ] Performance improvement ≥20% vs baseline
- [ ] ≥20 total novel innovations created
- [ ] Diversity metric >0.3 maintained (no convergence)
- [ ] At least 3 "breakthrough" innovations documented
- [ ] Innovation lineage graph generated

### Overall Success
- [ ] System demonstrates TRUE innovation (beyond 13-factor recombination)
- [ ] LLM-generated innovations outperform fixed-factor evolution
- [ ] InnovationRepository grows autonomously
- [ ] Evolutionary search explores novel strategy space
- [ ] No performance regression vs current system

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM generates invalid/broken code | **High** | Medium | 5-layer validation with sandbox execution |
| Innovations overfit historical data | Medium | **High** | Out-of-sample testing (70% threshold in Layer 4) |
| Innovation too aggressive, poor performance | Medium | Medium | Performance threshold (Sharpe >0.3, MDD <50%) |
| Repository grows too large | High | Low | Auto-cleanup: remove bottom 20% every 50 generations |
| No performance improvement over baseline | **Low** | **High** | Maintain fallback to Factor Graph mutations |
| Innovation validation too slow | Medium | Medium | Parallel validation, timeout limits |
| LLM stuck in local patterns | Medium | Medium | Diversity rewards, pattern variation prompts |

**Overall Risk Level**: 🟡 **MEDIUM** - Mitigatable with proper validation and fallback mechanisms

---

## Resource Requirements

### Computational
- Same as current system (0.16ms compilation, 4.3ms execution)
- Additional: Validation overhead (~100ms per innovation)
- Innovation rate: 20% of iterations → minimal impact

### Storage
- InnovationRepository: ~10MB per 100 generations (JSONL)
- PatternLibrary: ~1MB per 100 generations
- Lineage graph: ~5MB per 100 generations

### Dependencies (Already Satisfied)
- ✅ Python 3.x
- ✅ pandas, numpy, networkx
- ✅ finlab API
- ✅ AST parsing capabilities

**No new infrastructure required** - builds on existing stack.

---

## Alternative Approaches Considered

### Alternative 1: Expand Fixed Factor Pool
**Description**: Manually add 100+ factors to cover more cases

**Pros**:
- No validation complexity
- Deterministic behavior

**Cons**:
- ❌ Still finite search space
- ❌ Manual effort to create factors
- ❌ Cannot discover truly novel combinations
- ❌ Combinatorial explosion testing

**Verdict**: ❌ Rejected - Does not solve fundamental limitation

### Alternative 2: Hyperparameter Tuning Only
**Description**: Focus on optimizing parameters of existing 13 factors

**Pros**:
- Simple implementation
- Low risk

**Cons**:
- ❌ Cannot escape 13-factor search space
- ❌ Will plateau at local optimum
- ❌ No breakthrough innovations possible

**Verdict**: ❌ Rejected - User explicitly wants innovation capability

### Alternative 3: This Proposal (LLM Innovation)
**Description**: Enable LLM to create novel factors with validation

**Pros**:
- ✅ Infinite search space
- ✅ Breakthrough innovations possible
- ✅ Automated factor discovery
- ✅ Evolutionary learning

**Cons**:
- 🟡 Validation complexity
- 🟡 9-week implementation

**Verdict**: ✅ **SELECTED** - Best aligns with user goals and technical feasibility

---

## Questions for Consensus Review

### Technical Questions
1. **Validation Rigor**: Is 5-layer validation sufficient to prevent LLM hallucinations? Should we add more layers?
2. **Performance Thresholds**: Are Sharpe >0.3, MDD <50% appropriate for Layer 4 validation?
3. **Innovation Rate**: Is 20% default innovation rate appropriate? Too conservative or too aggressive?
4. **Repository Cleanup**: Remove bottom 20% every 50 generations - too aggressive or too conservative?

### Architectural Questions
5. **Layer Separation**: Should innovation layer be separate spec or added to structural-mutation-phase2?
6. **Fallback Strategy**: When validation fails, fallback to Factor Graph mutations - correct approach?
7. **Phase 2 vs Phase 3**: Can we skip Phase 2 and go directly to Phase 3, or is incremental approach better?

### Risk Questions
8. **Biggest Risk**: What is the most concerning risk not adequately mitigated?
9. **Success Criteria**: Are Phase 3 success criteria (≥20% improvement, ≥20 innovations) achievable or too ambitious?
10. **Timeline**: Is 9-week timeline realistic or should it be adjusted?

---

## Recommendation

**Proposed Decision**: ✅ **APPROVE** this spec and proceed with implementation

**Rationale**:
1. ✅ Builds on proven Factor Graph architecture (structural-mutation-phase2)
2. ✅ Addresses fundamental limitation (13-factor search space)
3. ✅ Incremental approach reduces risk (Phase 0 baseline → Phase 2 MVP → Phase 3 advanced)
4. ✅ Comprehensive validation mitigates LLM hallucination risk
5. ✅ Timeline aligns with user's plan (9 weeks total)
6. ✅ No new infrastructure required
7. ✅ Fallback to existing system if innovation underperforms

**Alternative**: 🟡 If concerns arise, consider starting with Phase 0 + Phase 2 only (4 weeks), then re-evaluate before Phase 3.

---

## Next Steps (If Approved)

1. **Week 1**: Run Task 0.1 (20-gen baseline test) to establish performance benchmark
2. **Week 2-3**: Implement Phase 2 MVP (Tasks 2.1-2.4)
3. **Week 4**: Validate Phase 2 with 20-gen smoke test (Task 2.5)
4. **Decision Gate**: If Phase 2 successful → proceed to Phase 3; else debug/revise
5. **Week 5-8**: Implement Phase 3 (Tasks 3.1-3.4)
6. **Week 9**: Final 100-gen validation (Task 3.5)

---

**Proposal Status**: 🔍 **AWAITING CONSENSUS REVIEW**
**Review Models**: OpenAI o3, Google Gemini 2.5 Pro
**Expected Review Date**: 2025-10-23

---

## Appendix: Example Innovations Expected

### Example 1: Novel Factor Combination
```python
# Current system CAN'T create this (not in 13 factors)
def roe_revenue_pe_factor(data):
    """Fundamental combo: Quality × Growth / Valuation"""
    roe = data['fundamental_features:ROE稅後']
    revenue_growth = data['fundamental_features:營收成長率']
    pe = data['fundamental_features:本益比']

    # Novel combination
    factor = (roe * revenue_growth) / pe
    return factor
```

### Example 2: Novel Exit Mechanism
```python
# Current system CAN'T create this (5MA not in exit mechanisms)
def ma5_stop_loss_exit(data, positions):
    """Exit when price crosses below 5-day MA"""
    close = data['close']
    ma5 = close.rolling(5).mean()

    # Novel exit logic
    exit_signal = (positions > 0) & (close < ma5)
    return exit_signal
```

### Example 3: Novel Momentum Variant
```python
# Current system CAN'T create this (volume-weighted momentum not in 13)
def volume_weighted_momentum(data):
    """Momentum weighted by volume intensity"""
    returns = data['close'].pct_change(20)
    volume_ratio = data['volume'] / data['volume'].rolling(60).mean()

    # Novel weighting scheme
    momentum = returns * volume_ratio
    return momentum
```

These innovations are **impossible** with current 13-factor system, demonstrating need for innovation capability.

---

**END OF PROPOSAL**
