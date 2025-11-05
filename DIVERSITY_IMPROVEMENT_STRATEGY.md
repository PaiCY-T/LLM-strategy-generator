# Diversity Improvement Strategy for Phase 2

**Created**: 2025-11-01 22:15 UTC
**Updated**: 2025-11-01 22:45 UTC (Gemini 2.5 Pro Expert Review)
**Goal**: Achieve diversity score ≥40 (CONDITIONAL GO) or ≥60 (GO)
**Current**: 19.17/100 (INSUFFICIENT)
**Target**: 40+/100 within 4-5 hours

---

## ⭐ Expert Review Summary (Gemini 2.5 Pro)

**Validation Status**: ✅ **PLAN APPROVED** with critical refinements

**Key Refinements Added**:
1. **CRITICAL MISSING**: Prompt engineering for diversity - guide LLM with population context
2. Tighten correlation rejection threshold: 0.90 → 0.75
3. Increase risk_diversity weight in fitness: 0.2 → 0.3
4. Make all weights configurable in YAML
5. Verify template rotation FIRST before any changes
6. Confirm Phase A → pilot → Phase B sequencing

**Expert Consensus**: Weighted sum (70/30) is appropriate, avoid NSGA-II complexity

---

## Executive Summary

Analysis of Phase 2 configuration reveals **low LLM innovation rate (5%)** and **lack of explicit diversity optimization** as primary causes of low diversity score (19.17/100). This document provides a comprehensive remediation strategy to achieve diversity score ≥40 through multi-objective optimization and increased factor space exploration.

**After expert review**: Plan validated with 6 critical refinements that increase probability of success while maintaining time/complexity budget.

---

## Root Cause Analysis

### Current Configuration Issues

**From `config/learning_system.yaml`**:

1. **Low LLM Innovation Rate (5%)**
   ```yaml
   llm:
     enabled: true
     provider: gemini
     innovation_rate: 0.05  # ❌ ONLY 5% use LLM, 95% use Factor Graph
   ```
   - Impact: 95% of strategies use Factor Graph templates
   - Result: Limited diversity, template convergence

2. **No Diversity Fitness Component**
   ```yaml
   anti_churn:
     min_sharpe_for_champion: 0.5  # ❌ Only Sharpe optimization
   ```
   - Impact: Optimization focuses solely on Sharpe ratio
   - Result: Strategies converge to similar high-Sharpe patterns

3. **Conservative Mutation Parameters**
   ```yaml
   mutation:
     exit_mutation:
       gaussian_std_dev: 0.15  # 15% mutation
       weight: 0.20            # 20% of mutations
   ```
   - Impact: Limited exploration of exit parameter space
   - Result: Exit strategies become similar

### Diversity Breakdown

**Current validated strategies (4 total)**:

| Strategy | Sharpe | Factor Overlap | Exit Type |
|----------|--------|----------------|-----------|
| 1 | 0.818 | High | Similar |
| 2 | 0.929 | High | Similar |
| 9 | 0.944 | High | Similar |
| 13 | 0.944 | High | Similar |

**Issues**:
- Factor diversity: 0.083 (target: >0.5)
- All strategies use similar factor combinations
- Zero risk diversity (all strategies have same drawdown profile)

---

## Diversity Improvement Plan

### Strategy 1: Increase LLM Innovation Rate + Diversity Prompting ⭐ PRIMARY

**Objective**: Increase factor space exploration via LLM with diversity-aware prompting

**Change 1A: Increase Innovation Rate**:
```yaml
llm:
  innovation_rate: 0.05  # Current
  ↓
  innovation_rate: 0.30  # New (30% of strategies use LLM)
```

**Change 1B: Add Diversity-Aware Prompting** 🔥 **CRITICAL ADDITION**:
```python
# Modify LLM prompt to include population context
def generate_llm_prompt(existing_population):
    """
    Generate diversity-aware prompt for LLM strategy generation.
    """
    # Extract factor sets from top strategies
    existing_factor_sets = [s.get_factors() for s in existing_population[:5]]
    rare_factors = identify_underused_factors(existing_factor_sets)

    prompt = f"""You are a quantitative trading strategy generator.

    EXISTING POPULATION:
    - Top 5 strategies use these factor sets: {existing_factor_sets}
    - Most common factors: {get_most_common_factors(existing_factor_sets)}

    YOUR TASK:
    Generate a NEW, NOVEL strategy that is **structurally different** and likely to be
    **uncorrelated** with existing strategies.

    DIVERSITY REQUIREMENTS:
    - Prioritize using UNDERREPRESENTED factors: {rare_factors}
    - Avoid factor combinations similar to existing population
    - Explore different exit parameter ranges
    - Create unique risk profile

    Generate a strategy that expands the diversity of the population.
    """
    return prompt
```

**Rationale**:
- LLM generates strategies beyond predefined Factor Graph templates
- **Diversity-aware prompting is high-impact, low-cost lever** (Gemini recommendation)
- Directly guides LLM to avoid convergence
- Increases factor combination diversity
- Proven to work (LLM integration is stable)

**Expected Impact**:
- Factor diversity: 0.083 → 0.35+ (4x improvement with prompting)
- More unique factor combinations
- Novel strategy patterns
- **Prompt engineering alone may be as impactful as rate increase**

**Risk**: Higher LLM API costs
**Mitigation**: Run for limited iterations (50 instead of 200)

---

### Strategy 2: Add Diversity to Fitness Function ⭐ PRIMARY

**Objective**: Explicitly reward diverse strategies

**Implementation**: Create multi-objective fitness function

**Pseudocode**:
```python
def fitness(strategy, population):
    sharpe_score = strategy.sharpe_ratio
    diversity_score = calculate_diversity(strategy, population)

    # Weighted fitness: 70% Sharpe + 30% Diversity
    fitness = 0.7 * sharpe_score + 0.3 * diversity_score
    return fitness

def calculate_diversity(strategy, population):
    # Factor diversity: Jaccard distance from population
    factor_diversity = jaccard_distance(strategy.factors, population.factors)

    # Return correlation: Low correlation = high diversity
    correlation_diversity = 1.0 - abs_correlation(strategy, population)

    # Risk diversity: Different max drawdown
    risk_diversity = coefficient_of_variation([strategy.mdd, *population.mdds])

    # Combined diversity score (UPDATED per Gemini 2.5 Pro recommendation)
    # Increased risk_diversity weight from 0.2 to 0.3 to address zero risk diversity issue
    return 0.4 * factor_diversity + 0.3 * correlation_diversity + 0.3 * risk_diversity
```

**Changes Required**:
1. Modify `src/learning/fitness_evaluator.py` (if exists) OR
2. Modify champion selection logic in autonomous loop
3. Track population diversity during evolution

**Expected Impact**:
- Diversity score: 19.17 → 40-50 (2-2.5x improvement)
- Prevents convergence to similar strategies
- Balances quality and variety

**Risk**: May reduce peak Sharpe ratio
**Mitigation**: Use 70/30 weight (prioritize quality over diversity)

---

### Strategy 3: Increase Mutation Diversity

**Objective**: Explore wider parameter space

**Changes**:
```yaml
mutation:
  exit_mutation:
    gaussian_std_dev: 0.15  # Current: 15% change
    ↓
    gaussian_std_dev: 0.25  # New: 25% change (larger mutations)

    weight: 0.20  # Current
    ↓
    weight: 0.30  # New: 30% of mutations (more frequent)
```

**Rationale**:
- Larger mutations → more exploration
- Higher mutation rate → more variants tested
- Breaks out of local optima

**Expected Impact**:
- Risk diversity: 0.000 → 0.15+ (exit parameter variation)
- More diverse exit strategies
- Wider Sharpe distribution

**Risk**: Lower average quality
**Mitigation**: Multi-objective fitness filters poor mutations

---

### Strategy 4: Enforce Diversity Thresholds

**Objective**: Reject too-similar strategies during evolution

**Implementation**:
```python
def is_too_similar(new_strategy, validated_strategies):
    """
    Reject strategy if too similar to existing validated strategies.

    UPDATED per Gemini 2.5 Pro recommendation:
    - Tightened correlation threshold from 0.90 to 0.75
    - Aligns with target average correlation <0.70
    """
    for validated in validated_strategies:
        # Factor similarity check
        jaccard_sim = jaccard_similarity(new_strategy.factors, validated.factors)
        if jaccard_sim > 0.80:  # >80% factor overlap
            return True

        # Return correlation check (TIGHTENED from 0.90 to 0.75)
        correlation = calculate_correlation(new_strategy, validated)
        if abs(correlation) > 0.75:  # >75% correlated (was 0.90)
            return True

    return False

# In evolution loop
if strategy.sharpe_ratio > threshold and not is_too_similar(strategy, validated):
    validated_strategies.append(strategy)
else:
    logger.info(f"Rejected strategy: Too similar to existing (Sharpe={strategy.sharpe_ratio})")
```

**Expected Impact**:
- Forces diversity by rejecting duplicates
- Ensures validated strategies are unique
- May reduce validation count (acceptable trade-off)

**Risk**: Fewer validated strategies
**Mitigation**: Run more iterations to compensate

---

### Strategy 5: Use Multiple Factor Graph Templates

**Objective**: Seed evolution with diverse starting points

**Current**: Uses `momentum_template.py`, `turtle_template.py`, `mastiff_template.py`

**Enhancement**: Rotate templates explicitly during evolution

```python
templates = [
    MomentumTemplate,
    TurtleTemplate,
    MastiffTemplate,
    FactorTemplate,  # Add more if available
]

def select_template(iteration):
    # Round-robin selection ensures all templates used
    return templates[iteration % len(templates)]
```

**Expected Impact**:
- Factor diversity: Guaranteed minimum from template variety
- Different starting points → different convergence
- Balanced exploration across strategy types

**Risk**: None (templates already exist)
**Mitigation**: N/A

---

## Implementation Priority

### Phase A: Quick Wins (1 hour)

**Tasks**:
0. 🔥 **VERIFY TEMPLATE ROTATION FIRST** (Gemini critical recommendation)
   - Check if templates are rotated in autonomous loop
   - Examine template selection in current population
   - If stuck on one template → explains low diversity
   - **DO THIS BEFORE ANY CONFIG CHANGES**

1. ✅ **Increase LLM innovation rate** (0.05 → 0.30)
   - Edit: `config/learning_system.yaml` line 768
   - No code changes needed

2. 🔥 **Add diversity-aware prompting** (NEW - Gemini critical addition)
   - Modify LLM prompt generation
   - Include population context in prompts
   - Guide LLM to create diverse strategies
   - **High-impact, low-cost improvement**

3. ✅ **Increase mutation diversity**
   - Edit: `config/learning_system.yaml` lines 455, 449
   - `gaussian_std_dev: 0.15 → 0.25`
   - `weight: 0.20 → 0.30`

4. 🔥 **Make all weights configurable** (NEW - Gemini recommendation)
   - Add fitness weights to YAML config
   - Add diversity sub-weights to YAML config
   - Add similarity thresholds to YAML config
   - Enable easy tuning without code changes

**Estimated Time**: 1.5-2 hours (includes new tasks)
**Expected Impact**: Diversity 19.17 → 35-40 (increased from 30-35 due to prompt engineering)

---

### Phase B: Multi-Objective Fitness (2-3 hours)

**Tasks**:
1. ⏳ **Implement diversity calculation function**
   - File: `src/analysis/diversity_calculator.py` (NEW)
   - Calculate Jaccard, correlation, risk diversity

2. ⏳ **Add diversity to fitness function**
   - File: Autonomous loop or fitness evaluator
   - Combine Sharpe + diversity (70/30 weight)

3. ⏳ **Add similarity rejection logic**
   - File: Champion selection logic
   - Reject strategies with >80% factor overlap

4. ⏳ **Test with 10-iteration pilot**
   - Verify diversity improves
   - Check Sharpe doesn't degrade too much

**Estimated Time**: 2-3 hours (implementation + testing)
**Expected Impact**: Diversity 30-35 → 45-55

---

### Phase C: Full Re-validation (1-2 hours)

**Tasks**:
1. ⏳ **Run Phase 2 with improved configuration**
   - 30-50 iterations (not full 200, too expensive)
   - Monitor diversity during run
   - Target: 5+ validated strategies with diversity ≥40

2. ⏳ **Re-run diversity analysis**
   - Use corrected validation file
   - Verify diversity score ≥40

3. ⏳ **Update GO/NO-GO decision**
   - If diversity ≥40 → CONDITIONAL GO
   - If diversity ≥60 → GO

**Estimated Time**: 1-2 hours (execution + analysis)
**Expected Impact**: Diversity 45-55 → FINAL SCORE

---

## Success Metrics

### Minimum Acceptable (CONDITIONAL GO)

- ✅ Diversity score: ≥40/100
- ✅ Factor diversity: ≥0.25
- ✅ Average correlation: <0.70
- ✅ Risk diversity: ≥0.15
- ✅ Unique validated strategies: ≥3

### Optimal (GO)

- ⭐ Diversity score: ≥60/100
- ⭐ Factor diversity: ≥0.50
- ⭐ Average correlation: <0.60
- ⭐ Risk diversity: ≥0.30
- ⭐ Unique validated strategies: ≥5

---

## Risk Assessment

### Risk 1: Quality Degradation

**Description**: Adding diversity may reduce peak Sharpe ratio

**Likelihood**: Medium
**Impact**: Medium

**Mitigation**:
- Use 70/30 Sharpe/Diversity weight (prioritize quality)
- Set minimum Sharpe threshold (0.5) unchanged
- Monitor Sharpe distribution during evolution

**Acceptance Criteria**:
- Average validated Sharpe ≥0.7 (currently 0.909)
- At least 1 strategy with Sharpe ≥0.9

---

### Risk 2: Increased LLM Costs

**Description**: 30% LLM rate → 6x more API calls

**Likelihood**: High (certain)
**Impact**: Low-Medium

**Mitigation**:
- Run only 30-50 iterations (not 200)
- Use cost-effective model (Gemini 2.5 Flash, already configured)
- Monitor API costs during run

**Cost Estimate**:
- Current (5% × 200 iter): 10 LLM calls
- New (30% × 50 iter): 15 LLM calls
- Incremental cost: ~$0.15-0.30 (acceptable)

---

### Risk 3: Implementation Time Overrun

**Description**: Phase B implementation takes longer than expected

**Likelihood**: Medium
**Impact**: Medium

**Mitigation**:
- **Fallback Plan**: Skip Phase B, only do Phase A
- Phase A alone may achieve diversity 30-35 (below threshold but improved)
- Can iterate in future sessions

**Decision Point**: After Phase A pilot test
- If diversity ≥35 → Continue to Phase B
- If diversity <30 → Reassess approach

---

## Alternative Approaches (If Plan Fails)

### Option 1: Lower Validation Threshold

**Change**: Sharpe ≥0.8 → Sharpe ≥0.7

**Impact**:
- More validated strategies (4 → 8-10)
- Higher diversity (more variety in 0.7-0.8 range)

**Risk**: Lower quality strategies
**Decision**: Last resort only

---

### Option 2: Template-Based Diversity

**Change**: Force each template to contribute 1-2 validated strategies

**Implementation**:
- Run separate evolutions per template
- Combine results
- Guaranteed template diversity

**Risk**: More complex, longer runtime
**Decision**: If multi-objective fitness doesn't work

---

### Option 3: Diversity-First Evolution

**Change**: Evolve for diversity first, filter for quality second

**Implementation**:
1. Generate 100 strategies optimized for diversity
2. Filter for Sharpe ≥0.8
3. Select top 5 by diversity score

**Risk**: May not find high-quality diverse strategies
**Decision**: If other approaches fail

---

## Execution Plan (Recommended)

### Session 1: Phase A + Pilot (1.5 hours)

1. **Update configuration** (15 min)
   - LLM innovation_rate: 0.05 → 0.30
   - Mutation std_dev: 0.15 → 0.25
   - Mutation weight: 0.20 → 0.30

2. **Run 10-iteration pilot** (30 min)
   - Quick test of configuration changes
   - Monitor diversity metrics
   - Check Sharpe doesn't degrade

3. **Analyze pilot results** (15 min)
   - Calculate diversity score
   - Compare to baseline (19.17)
   - Decide: Continue to Phase B or iterate

4. **Run 30-iteration evolution** (30 min)
   - If pilot successful, run longer evolution
   - Target: 5+ validated strategies
   - Monitor diversity during run

**Expected Outcome**: Diversity 30-40 (close to threshold)

---

### Session 2: Phase B (if needed) (2 hours)

**Only if Session 1 diversity <40**

1. **Implement diversity calculator** (45 min)
2. **Add multi-objective fitness** (45 min)
3. **Run 20-iteration test** (30 min)

**Expected Outcome**: Diversity 45-55 (exceeds threshold)

---

## Monitoring Dashboard

**During Evolution, Track**:

1. **Diversity Metrics** (every 10 iterations)
   - Factor diversity (Jaccard)
   - Average correlation
   - Risk diversity (CV of max drawdown)
   - Overall diversity score

2. **Quality Metrics**
   - Average validated Sharpe
   - Validation count
   - Execution success rate

3. **Exploration Metrics**
   - LLM usage rate (should be ~30%)
   - Unique factor combinations
   - Template distribution

**Alert Thresholds**:
- ⚠️ Factor diversity <0.20 after 20 iterations → Increase LLM rate
- ⚠️ Average Sharpe <0.70 → Reduce diversity weight
- ⚠️ Validation count <2 after 30 iterations → Relax validation threshold

---

## Success Criteria Checklist

Before declaring victory:

- [ ] Diversity score ≥40 (CONDITIONAL GO) or ≥60 (GO)
- [ ] Factor diversity ≥0.25 (COND) or ≥0.50 (GO)
- [ ] Average correlation <0.70
- [ ] Risk diversity ≥0.15 (COND) or ≥0.30 (GO)
- [ ] Minimum 3 unique validated strategies
- [ ] Average validated Sharpe ≥0.70
- [ ] At least 1 strategy with Sharpe ≥0.9
- [ ] Zero execution failures
- [ ] Diversity analysis run on correct validation file
- [ ] GO/NO-GO decision documented

---

## File Modifications Required

### Phase A (Quick Wins)

**File**: `config/learning_system.yaml`
```yaml
# Line 768: LLM innovation rate
llm:
  innovation_rate: 0.30  # Changed from 0.05

# Lines 449, 455: Mutation parameters
mutation:
  exit_mutation:
    weight: 0.30           # Changed from 0.20
    gaussian_std_dev: 0.25  # Changed from 0.15

# NEW: Multi-objective fitness configuration (Gemini recommendation)
fitness:
  multi_objective_weights:
    sharpe: 0.7    # 70% Sharpe ratio
    diversity: 0.3  # 30% Diversity score
  diversity_calculation:
    factor_weight: 0.4       # Factor diversity (Jaccard)
    correlation_weight: 0.3  # Return correlation
    risk_weight: 0.3         # Risk diversity (increased from 0.2)
  similarity_rejection:
    factor_overlap_threshold: 0.80  # Jaccard similarity
    correlation_threshold: 0.75     # Return correlation (tightened from 0.90)
```

### Phase B (Multi-Objective)

**New File**: `src/analysis/diversity_calculator.py`
- DiversityCalculator class
- calculate_jaccard_diversity()
- calculate_correlation_diversity()
- calculate_risk_diversity()

**Modified File**: Autonomous loop (TBD - need to find file)
- Add diversity calculation to fitness
- Add similarity rejection logic
- Track population diversity

---

**Next Action**: Ready to implement Phase A configuration changes?

**Command to execute**:
```bash
# Update config/learning_system.yaml with Phase A changes
# Then run 10-iteration pilot test
```

**Estimated Time to GO/CONDITIONAL GO**: 1-3 hours

---

## Gemini 2.5 Pro Expert Recommendations Summary

**Validation Date**: 2025-11-01 22:45 UTC
**Model**: Gemini 2.5 Pro via MCP zen:chat
**Overall Assessment**: ✅ **Plan Validated with Critical Refinements**

### Key Recommendations Implemented

1. **Prompt Engineering for Diversity** 🔥 **HIGHEST IMPACT**
   - Add population context to LLM prompts
   - Guide LLM to avoid convergence
   - Identify and use underrepresented factors
   - **Impact**: May be as effective as rate increase alone
   - **Cost**: Minimal (prompt modification only)

2. **Tighten Correlation Threshold**
   - Changed from 0.90 to 0.75
   - Aligns with target average correlation <0.70
   - More aggressive diversity enforcement

3. **Increase Risk Diversity Weight**
   - Changed from 0.2 to 0.3 in diversity calculation
   - Addresses zero risk diversity issue
   - More balanced diversity scoring

4. **Make Weights Configurable**
   - Move all weights to YAML config
   - Enable rapid tuning without code changes
   - Better experimental control

5. **Verify Template Rotation First**
   - Critical diagnostic step
   - Must check before making changes
   - May reveal root cause immediately

6. **Confirm Phase Sequencing**
   - Phase A → pilot test → Phase B
   - Do NOT combine phases
   - Enables causal attribution

### Avoided Complexity

- **DO NOT use NSGA-II or Pareto optimization** - weighted sum is sufficient
- **DO NOT add multiple LLM providers** - focus on rate and prompting
- **DO NOT increase LLM rate to 50%** - measure 30% impact first

### Updated Estimates

- **Phase A Time**: 1.5-2 hours (was 1 hour)
- **Expected Impact**: Diversity 35-40 (was 30-35)
- **Probability of Success**: HIGH (with prompt engineering)

---

**Generated**: 2025-11-01 22:15 UTC
**Updated**: 2025-11-01 22:45 UTC (Gemini 2.5 Pro refinements)
**Decision**: NO-GO with Validated Remediation Plan
**Target**: Diversity ≥40 within 4-5 hours
**Status**: 🟢 **EXPERT-VALIDATED, READY TO IMPLEMENT**
