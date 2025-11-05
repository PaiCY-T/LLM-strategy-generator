# Phase 0: Template-Guided Generation - Design Document

**Spec Version**: 1.0
**Created**: 2025-10-17
**Status**: Planning

---

## 📚 Table of Contents

1. [Background - Previous AI Review Analysis](#background)
2. [Design Rationale & Decision](#design-rationale)
3. [System Architecture](#system-architecture)
4. [Component Design](#component-design)
5. [Data Models](#data-models)
6. [Integration Design](#integration-design)
7. [Testing Strategy](#testing-strategy)
8. [Risk Mitigation](#risk-mitigation)

---

## 🔍 Background - Previous AI Review Analysis {#background}

### Context: Population-based Learning Spec Review

After creating the population-based learning spec, we conducted two AI model reviews:
1. **Gemini 2.5 Pro**: Technical validation and gap identification
2. **O3 with Challenge Mode**: Contrarian analysis questioning fundamental approach

---

### Gemini 2.5 Pro Review - 6 Critical Gaps Found

**Overall Assessment**: ✅ Technically sound, but missing key components

#### Gap #1: Missing Parameter Schema ⚠️ CRITICAL
**Finding**: Design assumes `get_parameter_bounds()` exists but never defined
```python
# Current mutation logic (design.md:452):
bounds = get_parameter_bounds(key)  # ❌ NOT DEFINED ANYWHERE
mutated_value = gaussian_mutate(value, bounds)
```

**Impact**: Mutation cannot generate valid parameters without knowing types, bounds, constraints
- Negative window sizes possible
- Invalid enum values generated
- High invalid offspring rate

**Gemini's Recommendation**: Add R0 requirement for parameter schema with YAML definition

#### Gap #2: Global State Anti-pattern 🔴 CRITICAL
**Finding**: `design.md:876-877` uses global variable for mutation rate
```python
# WRONG:
global MUTATION_RATE
MUTATION_RATE *= 2.0  # ❌ HIDDEN STATE
```

**Impact**:
- Unpredictable behavior
- Testing difficulties
- Parallel execution issues
- Violates encapsulation

**Gemini's Recommendation**: Refactor to PopulationManager instance state

#### Gap #3: Incorrect Task Dependencies 🔴 CRITICAL
**Finding**: CrossoverManager (Phase 5) depends on EvolutionaryPromptBuilder (Phase 8)

**Impact**: Implementation blocked - developer reaches Phase 5 and required component doesn't exist

**Gemini's Recommendation**: Move EvolutionaryPromptBuilder to Phase 4 (before crossover/mutation)

#### Gap #4: Missing Backtest Caching 🟡 HIGH
**Finding**: No cache for expensive backtest results (3 min each)

**Impact**:
- Duplicate backtests when crossover/mutation produces identical strategies
- Expected cache hit rate: 15-25% in later generations
- Generation time: 15 min → 10-12 min (20-30% improvement)

**Gemini's Recommendation**: Add BacktestCache component with SHA256 code hashing

#### Gap #5: Duplicated Pareto Dominance Logic 🟡 MEDIUM
**Finding**: Same logic in two places (multi_objective.py:586 and MultiObjectiveMetrics:742)

**Impact**: DRY violation, risk of divergence, maintenance burden

**Gemini's Recommendation**: Single source of truth, dataclass methods delegate

#### Gap #6: Conflicting Performance Targets 🟡 MEDIUM
**Finding**: Two different targets
- STATUS.md:67 → `<5 min` per generation
- requirements.md:403 → `<60 minutes` per generation

**Impact**: Unclear expectations, risk of failing validation

**Gemini's Recommendation**: Unified target `<20 minutes` (realistic with 4-core parallel + caching)

---

### O3 Contrarian Analysis - Fundamental Challenge

**O3's Core Argument**: "You're solving the WRONG problem"

#### Challenge #1: Root Cause Misdiagnosis 🎯 MOST CRITICAL

**O3's Analysis**:
```
Current Data:
- Champion update rate: 0.5% (1/200)
- Success rate: 95.2% (programs can execute)

Diagnosis:
- 95.2% success → Program generation quality is OK (no syntax errors)
- 0.5% champion update → Strategy PERFORMANCE quality is NOT OK

Conclusion: 99.5% strategies are worse than champion
→ This is a GENERATION QUALITY problem, not a SEARCH problem
```

**O3's Factory Analogy**:
> "If a factory produces 99.5% defective parts, you don't build a more sophisticated sorting system - you fix the manufacturing process."

**O3's Recommendation**: Fix prompt engineering and use templates BEFORE building complex population-based learning

#### Challenge #2: Over-Engineering Risk 💰

**Cost-Benefit Analysis**:
```
Population-based Learning:
- Implementation: 50 hours (68 tasks)
- Testing: 20-generation × 20 min = 6.7 hours
- Debugging: Estimated 20-30 hours
- TOTAL: ~80-100 hours

Template-based + Prompt Improvement:
- Use existing momentum_template.py: 0 hours
- Improve prompt with trading knowledge: 5 hours
- Add validation gates: 5 hours
- Test 200 iterations: 10 hours
- TOTAL: ~20 hours
```

**O3's Risk**:
> "Spend 100 hours on population-based learning, still get 99.5% bad strategies because LLM generation quality hasn't improved."

#### Challenge #3: Missing Robustness Validation ⚠️ FATAL FLAW

**O3's Most Important Finding** (Gemini completely missed):

Current spec only has in-sample metrics:
```python
MultiObjectiveMetrics:
    sharpe_ratio: 2.5      # ← 2019-2024 performance
    calmar_ratio: 3.0      # ← 2019-2024 performance
    max_drawdown: -0.15    # ← 2019-2024 performance

# Question: What happens in 2025?
# If regime change (bull→bear), all 20 strategies could fail simultaneously
```

**Missing Metrics**:
```python
@dataclass
class RobustMultiObjectiveMetrics:
    # In-sample (existing)
    sharpe_ratio: float
    calmar_ratio: float
    max_drawdown: float

    # Out-of-sample (MISSING!) ← O3 discovered
    oos_sharpe_ratio: float        # 2024 H2 unseen data
    sharpe_stability: float         # Variance across time windows

    # Robustness (MISSING!) ← O3 discovered
    regime_diversity_score: float   # Bull/Bear/Sideways performance
    transaction_cost_impact: float  # After transaction costs
    capacity_limit: float           # Sustainable capital size
```

**O3's Warning**:
> "Population-based learning optimizes for historical metrics. Without out-of-sample validation and regime testing, you're building an expensive overfitting machine."

#### Challenge #4: Hidden Failure Modes 🚨

**Failure Mode #1: LLM Code Generation in Crossover**
```python
# Spec says: crossover generates new code via LLM
parent1: momentum + value factors
parent2: quality + growth factors

offspring = LLM("combine these strategies")

# Risks:
- Syntactically valid but semantically wrong (data leakage, look-ahead bias)
- Doesn't actually combine parents (LLM ignores parents, generates random code)
- Code complexity explodes (LLM adds unnecessary features)
```

**Missing Validation**: How do you VERIFY that crossover actually combined parents correctly?

**Failure Mode #2: Regime Change Wipeout**
> "All 20 strategies trained on same historical data (2019-2024). If market regime changes, all strategies could fail simultaneously because Pareto front optimizes for historical metrics, not robustness."

**Failure Mode #3: Evaluation Cost Spiral**
```
20 generations × 20 strategies × 3 min backtest = 20 hours
If it doesn't converge in 20 generations? Run another 20? 50 hours? 100 hours?
```

**Missing**: Convergence guarantee, early stopping criteria, maximum time budget

#### Challenge #5: Metrics Optimize Wrong Objectives 📊

**O3's Critique**: Sharpe, Calmar, MaxDD are all BACKWARD-LOOKING

Multi-objective Pareto front will give you 5 strategies that are:
- ✅ Great on 2019-2024 data
- ❌ Unknown performance on 2025-2026 data

**What's Missing**:
- **Robustness**: Performance stability across different time windows
- **Transaction costs**: High-frequency rebalancing strategies might dominate Pareto front but fail in practice
- **Capacity**: Strategy might work with $100K but fail with $10M
- **Regime diversity**: All strategies might be "momentum in bull market"

**O3's Alternative Metric Set**:
```python
@dataclass
class RobustMetrics:
    sharpe_ratio: float
    out_of_sample_sharpe: float       # ← CRITICAL MISSING
    sharpe_stability: float            # ← Variance across time windows
    transaction_cost_impact: float     # ← CRITICAL MISSING
    max_drawdown: float
    recovery_time: float               # ← How fast it recovers from drawdown
    regime_diversity_score: float      # ← Works in different regimes?
```

#### Challenge #6: N=20 is Arbitrary and Likely Wrong 🔢

**Why 20?** Spec doesn't justify this number.

Genetic algorithm theory:
- **Too few**: Premature convergence (all 20 strategies become similar)
- **Too many**: Computational cost explodes, diminishing returns

For continuous parameter space with 5-10 parameters:
- Search space: effectively infinite
- Coverage with 20 samples: 0.0000000001%

**Theoretical minimum** for meaningful diversity:
```python
# Rule of thumb: population_size ≥ 2 × num_dimensions
dimensions = 10  # (momentum_window, top_n, factor_weights[3], filters[4])
min_population = 2 × 10 = 20  # ← Coincidentally matches spec, but...

# For genetic algorithms with crossover:
recommended_size = 4 × num_dimensions = 40 strategies
```

**O3's Conclusion**: 20 is likely TOO SMALL for effective exploration, but TOO LARGE for computational budget

#### Challenge #7: Catastrophic Success Scenarios 💣

**Even if perfectly implemented, could fail because:**

**Scenario A: Mode Collapse**
```
- LLM generates 20 strategies
- All 20 are variations of "buy low P/E stocks with momentum"
- Crossover produces more "buy low P/E stocks with momentum"
- Mutation tweaks parameters but same core strategy
→ Population diversity = 0, convergence to single strategy type
```

**Scenario B: Overfitting Arms Race**
```
- Generation 1: Best Sharpe = 1.5 (generalizes)
- Generation 10: Best Sharpe = 2.8 (starts overfitting)
- Generation 20: Best Sharpe = 4.5 (completely overfitted)
- Deploy in production: Sharpe = -0.3 (fails)
```

**Scenario C: Computational Cost Barrier**
```
- First 5 generations: 5 × 20 min = 1.7 hours
- Results: Marginal improvement (Sharpe 1.4 → 1.5)
- Team decides: "Not worth 1.7 hours per 5 generations"
→ System abandoned before convergence
```

**Missing from Spec**:
- **Early stopping**: How to detect when it's not working?
- **Minimum viable success**: What's the threshold for "worth continuing"?
- **Failure rollback**: How to recover if population-based makes things worse?

---

### My Ultrathink Analysis - Synthesis & Recommendation

#### Agreement with Both Reviews

**Gemini Got Right** ✅:
- Technical implementation is sound (NSGA-II, algorithms correct)
- Found real bugs (global state, task dependencies)
- Architecture is clean and modular

**Gemini Missed** ❌:
- Didn't question "WHY" we're doing this
- Completely missed robustness validation (O3's critical finding)
- Didn't consider cost-benefit analysis

**O3 Got Right** ✅:
- Questioned fundamental approach (most valuable contribution)
- Discovered robustness metric gap (Gemini completely missed)
- Realistic cost-benefit analysis (20 hours vs 100 hours)
- Identified catastrophic failure modes

**O3 Got Wrong** ❌:
- Recommendation too conservative ("don't implement yet")
- Oversimplified problem (generation quality AND search BOTH matter)
- Underestimated template limitations (why isn't user already using it?)

#### Critical Insight: Two Independent Problems

**O3's Logic**:
```
99.5% strategies worse than champion
→ Generation quality problem
→ Fix prompts, not search
```

**My Analysis**: This is TWO independent problems, not one:

**Problem A: Generation Quality** (O3 focuses on this)
- Current: 95.2% success rate (programs run)
- Improvement: Better prompts, templates, validation

**Problem B: Search Efficiency** (Spec addresses this)
- Current: Single-point search, evaluate 1 strategy per iteration
- Improvement: Parallel search, evaluate 20 strategies per iteration

**Both need solving**, not either/or.

**Better Analogy**:
```
O3's Analogy: "Factory produces 99.5% defects → improve manufacturing, not sorting"

More Accurate Analogy:
- Improve manufacturing (prompt/template) → Defect rate 99.5% → 95%
- Improve sorting (population-based) → From 100 defective items, find 5 good ones

Both together give best results.
```

#### Why User Isn't Using Existing Template?

**Critical Question**: `momentum_template.py` exists and works, but:
1. Champion uses NO template (`autonomous_generated`)
2. User accepted population-based recommendation
3. User chose Option B (pragmatic approach)

**Possible Reasons**:
- Templates already tested, didn't help?
- User wants autonomous generation, not hand-crafted templates?
- Templates limit innovation space?

**Risk**: Spend 20 hours on templates, find champion update rate still <5%, then spend 100 hours on population-based → 120 hours total.

#### The Right Approach: Option B (Pragmatic)

**Phase 0: Template Quick Test** (1 week, 20 hours)
- Test O3's hypothesis with LOW RISK
- If successful (≥5% update rate) → Save 80-100 hours
- If failure (<5% update rate) → Only wasted 20 hours, proceed to Phase 1

**Phase 1: Population-based with Critical Fixes** (2-3 weeks, 50 hours)
- **MUST add O3's robustness metrics**:
  - Out-of-sample validation (2024 H2 hold-out)
  - Regime-aware testing (bull/bear/sideways)
  - Transaction cost modeling
  - Sharpe stability (cross-window variance)
- **MUST fix Gemini's technical gaps**:
  - Parameter schema
  - Refactor global state
  - Fix task dependencies
  - Add backtest cache
- **Cost Optimization**:
  - Start with N=10 (not 20) → 50% cost reduction
  - Early stopping after 10 generations
  - Maximum 10-hour time budget

**Expected: 20-80 hours total** (depending on Phase 0 results)

---

## 🎯 Design Rationale & Decision {#design-rationale}

### Why Phase 0: Template-Guided Generation?

#### Rationale #1: Low-Risk Hypothesis Testing
**O3's Claim**: "Root cause is generation quality, not search algorithm"

**Phase 0 Tests This Hypothesis** with minimal investment:
- **IF O3 is right** → Champion update 0.5% → 5%+ → Save 80-100 hours
- **IF O3 is wrong** → Champion update stays <5% → Only lost 20 hours

**Risk-Reward Analysis**:
```
Investment: 20 hours
Potential Savings: 80-100 hours
Risk-Adjusted ROI: (80 hours × 25% success probability - 20 hours) / 20 hours = 0%

Even with low 25% success probability, breakeven.
With 50% success probability, 100% ROI.
```

#### Rationale #2: Address O3's Core Critique

**O3's Most Valid Point**: "99.5% of generated strategies are bad"

**Template Mode Addresses This**:
1. **Structural Constraints**: Template enforces proven architecture (momentum + catalyst)
2. **Parameter Bounds**: LLM selects from discrete PARAM_GRID (10,240 combinations), not infinite free-form space
3. **Domain Knowledge**: Prompt includes Finlab-specific best practices
4. **Validation Gates**: Reject obviously bad combinations BEFORE expensive backtest

**Expected Improvement**:
- Bad strategy rate: 99.5% → 80% (still high, but 4x better)
- Champion update rate: 0.5% → 5% (10x improvement)

#### Rationale #3: Maintain Population-based Option

**If Phase 0 Fails**:
- Template PARAM_GRID becomes parameter schema for population-based (fixes Gemini Gap #1)
- Validation gates reused in population-based
- Lessons learned inform crossover/mutation design

**No Wasted Work**: All Phase 0 components useful for Phase 1.

#### Rationale #4: Respect User Context

**User Signals**:
- Chose Option B (pragmatic, not conservative)
- Has momentum_template.py but not using it (why?)
- Accepted population-based initially (open to complex solutions)

**Design Decision**: Test simple solution first, keep complex solution ready.

---

### Response to AI Review Findings

#### Addressing Gemini's Technical Gaps

**Gap #1: Parameter Schema**
- ✅ **Solved in Phase 0**: Template PARAM_GRID IS the parameter schema
- ✅ **Reusable in Phase 1**: If population-based needed, schema already defined

**Gap #2: Global State**
- ✅ **Not Applicable**: Phase 0 doesn't use mutation (no global state needed)
- ✅ **Lesson for Phase 1**: Use instance state, not global

**Gap #3: Task Dependencies**
- ✅ **Not Applicable**: Phase 0 doesn't have multi-phase dependencies
- ✅ **Lesson for Phase 1**: Build EvolutionaryPromptBuilder early

**Gap #4: Backtest Cache**
- ✅ **Partially Addressed**: Validation gates reduce duplicate backtests by ~15%
- ⚠️ **Deferred to Phase 1**: Full caching more critical for population-based (20 strategies vs 1)

**Gap #5: Duplicated Logic**
- ✅ **Not Applicable**: Phase 0 doesn't use Pareto dominance
- ✅ **Lesson for Phase 1**: Single source of truth

**Gap #6: Performance Targets**
- ✅ **Clarified**: Phase 0 target = <6 min/iteration (realistic for single strategy)

#### Addressing O3's Critical Findings

**Finding #1: Root Cause (Generation Quality)**
- ✅ **DIRECTLY ADDRESSED**: Entire Phase 0 focuses on improving generation quality via templates

**Finding #2: Over-Engineering**
- ✅ **MITIGATED**: Test simple solution first (20 hours), complex solution later (80 hours) if needed

**Finding #3: Missing Robustness** ⚠️ **DEFERRED BUT NOT FORGOTTEN**
- ⏳ **Phase 0**: Focus on champion update rate improvement (primary goal)
- ✅ **Phase 1**: MUST add robustness metrics if population-based is needed
  - Out-of-sample validation
  - Regime-aware testing
  - Transaction cost modeling
  - Sharpe stability

**Finding #4: Hidden Failure Modes**
- ✅ **Mode Collapse**: Mitigated by validation gates, parameter diversity tracking
- ✅ **Overfitting**: Monitored via variance metric (target <0.8)
- ✅ **Cost Spiral**: Hard limit of 50 iterations, 5-hour max runtime

**Finding #5: Wrong Objectives**
- ⏳ **Phase 0**: Use existing Sharpe/Calmar/MDD metrics (sufficient for hypothesis test)
- ✅ **Phase 1**: Add O3's robustness metrics if needed

**Finding #6: N=20 Arbitrary**
- ✅ **Not Applicable**: Phase 0 generates 1 strategy per iteration, not 20
- ✅ **Phase 1**: Start with N=10 (not 20) if needed

**Finding #7: Catastrophic Success**
- ✅ **Early Stopping**: Decision after 50 iterations, don't continue if not working
- ✅ **Minimum Viable Success**: Clear threshold (5% champion update rate)
- ✅ **Rollback Ready**: Can revert to free-form generation if template mode worse

---

### Design Principles for Phase 0

#### Principle #1: Pragmatic Minimalism
**Mantra**: "Build only what's needed to test the hypothesis"

**What We Build**:
- TemplateParameterGenerator (essential for template mode)
- StrategyValidator (improves efficiency)
- Enhanced prompt (improves generation quality)
- 50-iteration test (validates hypothesis)

**What We DON'T Build** (defer to Phase 1 if needed):
- Backtest cache (less critical for single strategy per iteration)
- Robust metrics (out-of-sample, regime testing)
- Population manager
- Crossover/mutation operators

#### Principle #2: Evidence-Based Decisions
**Mantra**: "Data decides, not opinions"

**Decision Matrix**:
```python
if champion_update_rate >= 10% and avg_sharpe > 1.2:
    decision = "SUCCESS: Use template mode, skip population-based"
elif champion_update_rate >= 5% and avg_sharpe > 1.0:
    decision = "PARTIAL: Consider hybrid (template + population)"
else:
    decision = "FAILURE: Proceed to Phase 1 (population-based)"
```

**No Subjective Judgment**: Clear, measurable criteria.

#### Principle #3: Fail Fast, Learn Fast
**Mantra**: "20 hours to validate or invalidate hypothesis"

**Timeline**:
- Development: 12 hours
- Integration: 4 hours
- Testing: 5 hours (50 iterations × 6 min)
- Analysis: 4 hours
- **Total: 25 hours** (including test runtime)

**Fast Feedback**: Know within 1 week if approach works.

#### Principle #4: No Wasted Work
**Mantra**: "Every component reusable in Phase 1 if needed"

**Reusability**:
- TemplateParameterGenerator → Becomes crossover operator input
- StrategyValidator → Reused for offspring validation
- Enhanced prompt → Basis for evolutionary prompt
- PARAM_GRID → Parameter schema for population-based
- Test harness → Extends to 20-generation population test

---

## 🏗️ System Architecture {#system-architecture}

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS LOOP                          │
│                    (Template Mode)                          │
└──────┬────────────────────────────────────────────┬─────────┘
       │                                            │
       │ 1. Generate Parameters                    │ 5. Update Champion
       │                                            │
       ▼                                            │
┌──────────────────────────────┐                   │
│ TemplateParameterGenerator   │                   │
│ ┌──────────────────────────┐ │                   │
│ │ Build Prompt with:       │ │                   │
│ │ - PARAM_GRID             │ │                   │
│ │ - Champion context       │ │                   │
│ │ - Domain knowledge       │ │                   │
│ │ - Failure patterns       │ │                   │
│ └──────────────────────────┘ │                   │
│ ┌──────────────────────────┐ │                   │
│ │ Call LLM (Gemini)        │ │                   │
│ └──────────────────────────┘ │                   │
│ ┌──────────────────────────┐ │                   │
│ │ Parse JSON Response      │ │                   │
│ └──────────────────────────┘ │                   │
└──────────┬───────────────────┘                   │
           │ 2. Parameters                          │
           ▼                                        │
┌──────────────────────────────┐                   │
│   StrategyValidator          │                   │
│ ┌──────────────────────────┐ │                   │
│ │ Check PARAM_GRID bounds  │ │                   │
│ └──────────────────────────┘ │                   │
│ ┌──────────────────────────┐ │                   │
│ │ Validate risk management │ │                   │
│ └──────────────────────────┘ │                   │
│ ┌──────────────────────────┐ │                   │
│ │ Check logical consistency│ │                   │
│ └──────────────────────────┘ │                   │
└──────────┬───────────────────┘                   │
           │ 3. Validated Parameters                │
           ▼                                        │
┌──────────────────────────────┐                   │
│   MomentumTemplate           │                   │
│   (Existing Component)       │                   │
│ ┌──────────────────────────┐ │                   │
│ │ Generate strategy code   │ │                   │
│ │ with parameters          │ │                   │
│ └──────────────────────────┘ │                   │
│ ┌──────────────────────────┐ │                   │
│ │ Run Finlab backtest      │ │                   │
│ └──────────────────────────┘ │                   │
│ ┌──────────────────────────┐ │                   │
│ │ Extract metrics          │ │                   │
│ └──────────────────────────┘ │                   │
└──────────┬───────────────────┘                   │
           │ 4. Metrics                             │
           └────────────────────────────────────────┘

                        DATA FLOW
```

### Component Interaction Sequence

```
User starts 50-iteration test
        │
        ▼
┌───────────────────┐
│ Test Harness      │  Orchestrates 50 iterations
└────────┬──────────┘
         │
         ▼  (for each iteration)
┌───────────────────┐
│ Autonomous Loop   │
└────────┬──────────┘
         │
         ├──────────► 1. TemplateParameterGenerator
         │               ├─► Build prompt (PARAM_GRID + champion + domain knowledge)
         │               ├─► Call Gemini LLM
         │               └─► Parse JSON response → params
         │
         ├──────────► 2. StrategyValidator
         │               ├─► Validate params against PARAM_GRID
         │               ├─► Check risk management rules
         │               └─► Return (is_valid, errors)
         │
         │           IF validation fails:
         │               ├─► Log error
         │               └─► Skip to next iteration
         │
         ├──────────► 3. MomentumTemplate.generate_strategy(params)
         │               ├─► Calculate momentum
         │               ├─► Apply MA filter
         │               ├─► Apply catalyst filter
         │               ├─► Select top N stocks
         │               ├─► Run Finlab backtest (3-6 min)
         │               └─► Extract metrics (Sharpe, Calmar, MDD)
         │
         ├──────────► 4. Update Champion
         │               IF metrics.sharpe > champion.sharpe:
         │                   ├─► Update champion
         │                   ├─► Increment champion_update_count
         │                   └─► Log success
         │
         └──────────► 5. Record History
                         ├─► Save parameters
                         ├─► Save metrics
                         └─► Update diversity stats

(repeat for 50 iterations)

Test Harness collects results
        │
        ▼
Analyze Results
├─► Champion update rate
├─► Average Sharpe
├─► Parameter diversity
└─► Make GO/NO-GO decision
```

---

## 🧩 Component Design {#component-design}

### Component 1: TemplateParameterGenerator

**Purpose**: Generate parameter combinations using LLM guidance instead of random selection

**File**: `src/generators/template_parameter_generator.py`

**Class Interface**:
```python
from typing import Dict, Optional, List, Any
from dataclasses import dataclass


@dataclass
class ParameterGenerationContext:
    """Context for parameter generation."""
    iteration_num: int
    champion_params: Optional[Dict[str, Any]]
    champion_sharpe: Optional[float]
    feedback_history: Optional[str]
    # NOTE: champion_patterns removed per Gemini review -
    # champion_params already provides sufficient context


class TemplateParameterGenerator:
    """Generate parameters for MomentumTemplate using LLM guidance."""

    def __init__(
        self,
        template_name: str = "Momentum",
        model: str = "gemini-2.5-flash",
        exploration_interval: int = 5
    ):
        """Initialize generator.

        Args:
            template_name: Name of template to use ("Momentum")
            model: LLM model for parameter selection
            exploration_interval: Force exploration every N iterations
        """
        self.template_name = template_name
        self.model = model
        self.exploration_interval = exploration_interval

        # Load template
        from src.templates.momentum_template import MomentumTemplate
        self.template = MomentumTemplate()
        self.param_grid = self.template.PARAM_GRID

        # Prompt builder
        from artifacts.working.modules.poc_claude_test import (
            generate_strategy as call_llm
        )
        self.call_llm = call_llm

    def generate_parameters(
        self,
        context: ParameterGenerationContext
    ) -> Dict[str, Any]:
        """Generate parameter combination using LLM.

        Args:
            context: Generation context with champion info and feedback

        Returns:
            Parameter dictionary with 8 keys matching PARAM_GRID

        Raises:
            ValueError: If LLM response cannot be parsed
            RuntimeError: If parameter generation fails
        """
        # 1. Build prompt
        prompt = self._build_prompt(context)

        # 2. Call LLM
        response = self._call_llm_for_parameters(prompt)

        # 3. Parse response
        params = self._parse_response(response)

        # 4. Validate and return
        validated_params = self._validate_params(params)

        return validated_params

    def _build_prompt(self, context: ParameterGenerationContext) -> str:
        """Build prompt for parameter selection.

        Prompt structure:
        1. Task description
        2. PARAM_GRID with explanations
        3. Champion context (if exists)
        4. Trading domain knowledge
        5. Output format (JSON)
        """
        sections = []

        # Section 1: Task
        sections.append("# TASK: Select Parameters for Momentum Strategy")
        sections.append("")
        sections.append("You are a quantitative trading expert selecting parameters")
        sections.append("for a momentum + catalyst strategy on Taiwan stock market.")
        sections.append("")

        # Section 2: PARAM_GRID
        sections.append("## PARAMETER GRID")
        sections.append("Select ONE value for each parameter:")
        sections.append("")

        grid_explanations = {
            'momentum_period': [
                "5 days: Very short-term momentum (1 week)",
                "10 days: Short-term momentum (2 weeks)",
                "20 days: Medium-term momentum (1 month)",
                "30 days: Longer-term momentum (1.5 months)"
            ],
            'ma_periods': [
                "20 days: Short-term trend (1 month)",
                "60 days: Medium-term trend (3 months)",
                "90 days: Long-term trend (4.5 months)",
                "120 days: Very long-term trend (6 months)"
            ],
            'catalyst_type': [
                "'revenue': Revenue acceleration (short-term > long-term MA)",
                "'earnings': Earnings momentum (ROE improvement)"
            ],
            'catalyst_lookback': [
                "2 months: Very recent catalyst",
                "3 months: Recent catalyst",
                "4 months: Short-term catalyst",
                "6 months: Medium-term catalyst"
            ],
            'n_stocks': [
                "5: Highly concentrated (top momentum plays)",
                "10: Concentrated portfolio",
                "15: Balanced diversification",
                "20: Diversified momentum portfolio"
            ],
            'stop_loss': [
                "0.08: Tight stop (8% loss limit)",
                "0.10: Moderate stop (10% loss limit)",
                "0.12: Moderate-loose stop (12% loss limit)",
                "0.15: Loose stop (15% loss limit)"
            ],
            'resample': [
                "'W': Weekly rebalancing (higher turnover, faster reaction)",
                "'M': Monthly rebalancing (lower turnover, reduced costs)"
            ],
            'resample_offset': [
                "0: Monday/1st of month",
                "1: Tuesday/offset 1 day",
                "2: Wednesday/offset 2 days",
                "3: Thursday/offset 3 days",
                "4: Friday/offset 4 days"
            ]
        }

        for param, values in self.param_grid.items():
            sections.append(f"### {param}: {values}")
            for explanation in grid_explanations[param]:
                sections.append(f"  - {explanation}")
            sections.append("")

        # Section 3: Champion Context
        if context.champion_params:
            sections.append("## CURRENT CHAMPION")
            sections.append(f"Iteration: {context.iteration_num}")
            sections.append(f"Sharpe Ratio: {context.champion_sharpe:.4f}")
            sections.append("")
            sections.append("Parameters:")
            for key, value in context.champion_params.items():
                sections.append(f"  - {key}: {value}")
            sections.append("")

            # Exploration vs Exploitation
            if self._should_force_exploration(context.iteration_num):
                sections.append("⚠️  EXPLORATION MODE: Try DIFFERENT parameters")
                sections.append("    Ignore champion, explore distant parameter space")
            else:
                sections.append("💡 EXPLOITATION MODE: Try parameters NEAR champion")
                sections.append("    Adjust 1-2 parameters by ±1 step from champion")
            sections.append("")

        # Section 4: Domain Knowledge
        sections.append("## TRADING DOMAIN KNOWLEDGE")
        sections.append("")

        sections.append("### Taiwan Stock Market Characteristics")
        sections.append("- T+2 settlement, 10% daily price limit")
        sections.append("- High retail participation, momentum effects strong")
        sections.append("- Market cap concentration in tech/finance sectors")
        sections.append("")

        sections.append("### Finlab Data Recommendations")
        sections.append("- ALWAYS include liquidity filter (trading_value > 50M-100M TWD)")
        sections.append("- Smooth fundamentals with .rolling().mean() to reduce noise")
        sections.append("- Use .shift(1) to avoid look-ahead bias")
        sections.append("- Revenue catalyst works well with shorter momentum windows")
        sections.append("- Earnings (ROE) catalyst better for longer-term strategies")
        sections.append("")

        sections.append("### Risk Management Best Practices")
        sections.append("- Portfolio: 10-15 stocks optimal (balance concentration vs diversification)")
        sections.append("- Stop loss: 10-12% recommended for momentum strategies")
        sections.append("- Rebalancing: Weekly for aggressive, Monthly for conservative")
        sections.append("- Avoid over-diversification (>20 stocks reduces alpha)")
        sections.append("")

        sections.append("### Parameter Relationships")
        sections.append("- Short momentum (5-10 days) → use shorter MA (20-60 days)")
        sections.append("- Long momentum (20-30 days) → use longer MA (60-120 days)")
        sections.append("- Weekly rebalancing → prefer shorter momentum windows")
        sections.append("- Monthly rebalancing → can use longer momentum windows")
        sections.append("- Tight stop loss (8%) → use smaller position size (10-12 stocks)")
        sections.append("- Loose stop loss (15%) → can use larger positions (15-20 stocks)")
        sections.append("")

        # Section 5: Feedback History
        if context.feedback_history:
            sections.append("## PREVIOUS ITERATION FEEDBACK")
            sections.append(context.feedback_history)
            sections.append("")

        # Section 6: Output Format
        sections.append("## OUTPUT FORMAT")
        sections.append("Return ONLY valid JSON (no explanations):")
        sections.append("{")
        sections.append('  "momentum_period": 10,')
        sections.append('  "ma_periods": 60,')
        sections.append('  "catalyst_type": "revenue",')
        sections.append('  "catalyst_lookback": 3,')
        sections.append('  "n_stocks": 10,')
        sections.append('  "stop_loss": 0.10,')
        sections.append('  "resample": "M",')
        sections.append('  "resample_offset": 0')
        sections.append("}")

        return "\n".join(sections)

    def _should_force_exploration(self, iteration_num: int) -> bool:
        """Force exploration every N iterations."""
        return (iteration_num > 0 and
                iteration_num % self.exploration_interval == 0)

    def _call_llm_for_parameters(
        self,
        prompt: str,
        iteration_num: int = 0
    ) -> str:
        """Call LLM to generate parameter selection.

        Args:
            prompt: Formatted prompt for parameter selection
            iteration_num: Current iteration number (for exploration control)

        Returns:
            LLM response text
        """
        # Temperature control for exploration vs exploitation (per Gemini review)
        # Higher temperature = more exploration
        # Lower temperature = more exploitation (closer to champion)

        is_exploration = self._should_force_exploration(iteration_num)
        temperature = 1.0 if is_exploration else 0.7  # Higher for exploration

        # Use existing LLM infrastructure
        response = self.call_llm(
            iteration_num=iteration_num,
            history=prompt,
            model=self.model,
            temperature=temperature  # Dynamic temperature
        )
        return response

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract JSON parameters.

        Handles:
        - Response with explanatory text + JSON
        - Response with JSON only
        - Response with markdown code blocks

        Raises:
            ValueError: If no valid JSON found
        """
        import json
        import re

        # Strategy 1: Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from markdown code block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 3: Extract any {...} block
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # Strategy 4: Extract with nested braces
        json_match = re.search(r'\{(?:[^{}]|\{[^{}]*\})*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(
            f"Could not parse JSON from LLM response.\n"
            f"Response preview: {response[:500]}..."
        )

    def _validate_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters against PARAM_GRID.

        Args:
            params: Parameter dictionary from LLM

        Returns:
            Validated parameter dictionary

        Raises:
            ValueError: If validation fails
        """
        errors = []

        # Check all required keys present
        required_keys = set(self.param_grid.keys())
        provided_keys = set(params.keys())

        missing_keys = required_keys - provided_keys
        if missing_keys:
            errors.append(f"Missing required keys: {missing_keys}")

        extra_keys = provided_keys - required_keys
        if extra_keys:
            errors.append(f"Unknown keys: {extra_keys}")

        # Check each value is in valid options
        for key, value in params.items():
            if key in self.param_grid:
                valid_options = self.param_grid[key]
                if value not in valid_options:
                    errors.append(
                        f"{key}={value} not in valid options {valid_options}"
                    )

        if errors:
            raise ValueError(
                f"Parameter validation failed:\n" +
                "\n".join(f"  - {e}" for e in errors)
            )

        return params
```

**Key Design Decisions**:
1. **Prompt Structure**: 6 sections (task, grid, champion, domain, feedback, output)
2. **Exploration Control**: Every 5th iteration forces exploration (ignore champion)
3. **Robust Parsing**: 4-tier JSON extraction (handles various LLM response formats)
4. **Strict Validation**: All values must match PARAM_GRID options exactly

---

### Component 2: StrategyValidator

**Purpose**: Pre-backtest validation to reject obviously flawed parameter combinations

**File**: `src/validation/strategy_validator.py`

**Class Interface**:
```python
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of strategy validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class StrategyValidator:
    """Validate strategy parameters before backtesting."""

    def __init__(
        self,
        strict_mode: bool = False
    ):
        """Initialize validator.

        Args:
            strict_mode: If True, warnings become errors
        """
        self.strict_mode = strict_mode

    def validate_parameters(
        self,
        params: Dict[str, Any]
    ) -> ValidationResult:
        """Validate parameter combination.

        Checks:
        1. Parameter bounds (PARAM_GRID compliance)
        2. Risk management rules
        3. Logical consistency

        Args:
            params: Parameter dictionary

        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []

        # Check 1: Risk Management
        risk_errors, risk_warnings = self._validate_risk_management(params)
        errors.extend(risk_errors)
        warnings.extend(risk_warnings)

        # Check 2: Logical Consistency
        consistency_warnings = self._validate_logical_consistency(params)
        if self.strict_mode:
            errors.extend(consistency_warnings)
        else:
            warnings.extend(consistency_warnings)

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )

    def _validate_risk_management(
        self,
        params: Dict[str, Any]
    ) -> Tuple[List[str], List[str]]:
        """Validate risk management parameters.

        Returns:
            (errors, warnings)
        """
        errors = []
        warnings = []

        # Stop loss bounds
        stop_loss = params.get('stop_loss', 0)
        if stop_loss < 0.05:
            errors.append(
                f"Stop loss {stop_loss:.2%} too tight (min 5%), "
                f"causes excessive whipsaw"
            )
        elif stop_loss > 0.20:
            errors.append(
                f"Stop loss {stop_loss:.2%} too loose (max 20%), "
                f"allows excessive drawdowns"
            )

        # Position sizing
        n_stocks = params.get('n_stocks', 0)
        if n_stocks < 5:
            errors.append(
                f"Portfolio too concentrated ({n_stocks} stocks), "
                f"minimum 5 recommended for diversification"
            )
        elif n_stocks > 30:
            warnings.append(
                f"Portfolio over-diversified ({n_stocks} stocks), "
                f"may dilute alpha (max 30 recommended)"
            )

        # Rebalancing frequency
        resample = params.get('resample', '')
        if resample == 'D':
            errors.append(
                "Daily rebalancing causes excessive transaction costs, "
                "use Weekly ('W') or Monthly ('M')"
            )

        return errors, warnings

    def _validate_logical_consistency(
        self,
        params: Dict[str, Any]
    ) -> List[str]:
        """Check parameter combinations make logical sense.

        Returns warnings for suspicious combinations.
        """
        warnings = []

        momentum_period = params.get('momentum_period', 0)
        ma_periods = params.get('ma_periods', 0)
        resample = params.get('resample', '')

        # Short momentum should use shorter MA
        if momentum_period <= 10 and ma_periods >= 90:
            warnings.append(
                f"Short momentum ({momentum_period}d) with long MA ({ma_periods}d) "
                f"may cause lag - consider shorter MA (20-60d)"
            )

        # Long momentum should use longer MA
        if momentum_period >= 20 and ma_periods <= 20:
            warnings.append(
                f"Long momentum ({momentum_period}d) with short MA ({ma_periods}d) "
                f"may be too sensitive - consider longer MA (60-120d)"
            )

        # Weekly rebalancing better for short momentum
        if resample == 'W' and momentum_period >= 20:
            warnings.append(
                f"Weekly rebalancing with long momentum ({momentum_period}d) "
                f"may cause excessive turnover - consider monthly ('M')"
            )

        # Monthly rebalancing may miss short momentum signals
        if resample == 'M' and momentum_period <= 10:
            warnings.append(
                f"Monthly rebalancing with short momentum ({momentum_period}d) "
                f"may miss signals - consider weekly ('W')"
            )

        return warnings
```

**Validation Philosophy**:
- **Errors**: Block obviously bad strategies (save backtest time)
- **Warnings**: Flag suspicious combinations (allow but log)
- **Strict Mode**: Convert warnings to errors (for conservative testing)

---

### Component 3: Enhanced Prompt Template

**Purpose**: Provide domain-specific trading knowledge and Finlab best practices

**File**: `src/prompts/template_mode_prompt.txt` (new file)

**Content Structure**:

```markdown
# Template Mode Parameter Selection Prompt

## Context
You are selecting parameters for a momentum + catalyst trading strategy
on Taiwan stock market using Finlab data (2019-2024).

## Strategy Architecture (FIXED)
The template ALWAYS uses this proven structure:
1. Calculate momentum: price.pct_change(momentum_period)
2. Apply moving average filter: price > MA(ma_periods)
3. Apply catalyst filter: revenue OR earnings acceleration
4. Rank by combined signal
5. Select top N stocks
6. Apply stop loss and rebalancing

YOUR TASK: Select optimal parameters, NOT change the code structure.

## Taiwan Market Characteristics

### Market Microstructure
- T+2 settlement, 10% daily price limit
- High retail participation (60-70% of volume)
- Momentum effects stronger than Western markets
- Liquidity concentrated in top 300 stocks

### Sector Concentration
- Technology: 35-40% of market cap
- Finance: 15-20% of market cap
- Manufacturing: 20-25% of market cap

### Trading Costs
- Brokerage: 0.1425% (buy + sell)
- Transaction tax: 0.3% (sell only)
- Total round-trip: ~0.6%
- Impact cost: 0.1-0.3% for illiquid stocks

## Finlab Data Best Practices

### Data Quality Rules
1. ALWAYS use .shift(1) to avoid look-ahead bias
   Example: momentum = close.pct_change(20).shift(1)

2. ALWAYS smooth fundamentals to reduce noise
   Example: roe.rolling(4).mean() instead of raw roe

3. ALWAYS include liquidity filter
   Recommended: trading_value.rolling(20).mean() > 70_000_000 TWD

4. ALWAYS filter by minimum price
   Recommended: close > 15-20 TWD (avoid penny stocks)

5. ALWAYS check for market cap filter
   Optional: market_cap > 5_000_000_000 TWD (avoid micro-caps)

### Known Data Limitations
- Fundamental data: Quarterly updates (use longer lookbacks)
- Revenue data: Monthly updates (fresher than earnings)
- Price data: Daily (no intraday)
- Delisted stocks: Included (survivorship bias corrected)

## Parameter Selection Guidelines

### Momentum Period
- **5 days**: Very short-term, high turnover, works in volatile markets
  - Best with: Weekly rebalancing, tight stop loss (8-10%)
  - Risk: Noise, whipsaw, high costs

- **10 days**: Short-term momentum, balanced
  - Best with: Weekly rebalancing, moderate stop (10-12%)
  - Sweet spot for Taiwan market retail momentum

- **20 days**: Medium-term, classic momentum
  - Best with: Monthly rebalancing, moderate stop (10-12%)
  - Most academically validated window

- **30 days**: Longer-term trend following
  - Best with: Monthly rebalancing, loose stop (12-15%)
  - Risk: Lag, miss quick reversals

### Moving Average Periods
- **20 days**: Short-term trend filter (1 month)
  - Pairs well with: momentum_period 5-10
  - Purpose: Filter choppy sideways moves

- **60 days**: Medium-term trend (3 months)
  - Pairs well with: momentum_period 10-20
  - Balanced noise filtering and lag

- **90 days**: Long-term trend (4.5 months)
  - Pairs well with: momentum_period 20-30
  - Purpose: Only trade in strong trends

- **120 days**: Very long-term (6 months)
  - Pairs well with: momentum_period 30
  - Risk: May filter out too many opportunities

### Catalyst Type
- **'revenue'**: Revenue acceleration
  - Calculation: revenue_growth_short_MA > revenue_growth_long_MA
  - Update frequency: Monthly
  - Best for: Short-term momentum (5-10 days)
  - Rationale: More recent than earnings data

- **'earnings'**: Earnings momentum (ROE)
  - Calculation: ROE improving (ROE current > ROE rolling average)
  - Update frequency: Quarterly
  - Best for: Longer-term momentum (20-30 days)
  - Rationale: More fundamental, less volatile

### Catalyst Lookback
- **2 months**: Very recent catalyst, fast reaction
  - Pairs well with: Short momentum, revenue catalyst

- **3 months**: Recent catalyst, balanced
  - Default choice for most strategies

- **4 months**: Short-term fundamental
  - Good for earnings catalyst

- **6 months**: Medium-term fundamental
  - Best for: Long momentum, earnings catalyst
  - Risk: Stale information

### Number of Stocks (n_stocks)
- **5 stocks**: Highly concentrated
  - Pros: Maximum alpha capture, simple to manage
  - Cons: High idiosyncratic risk, large drawdowns
  - Best with: Tight stop loss (8-10%)

- **10 stocks**: Concentrated
  - Sweet spot for retail investors
  - Good risk-return balance
  - Recommended default

- **15 stocks**: Balanced
  - Moderate diversification
  - Reduces tail risk

- **20 stocks**: Diversified
  - Pros: Smoother returns, lower volatility
  - Cons: Diluted alpha, higher costs
  - Best with: Loose stop loss (12-15%)

### Stop Loss
- **0.08 (8%)**: Tight stop
  - Pros: Limits losses, good for concentrated portfolios
  - Cons: Whipsaw risk, may exit too early
  - Best with: 5-10 stocks, weekly rebalancing

- **0.10 (10%)**: Moderate stop
  - Most common choice
  - Good balance
  - Works with most configurations

- **0.12 (12%)**: Moderate-loose
  - Allows breathing room
  - Reduces whipsaw
  - Best with: 15-20 stocks, monthly rebalancing

- **0.15 (15%)**: Loose stop
  - Pros: Ride through volatility, fewer exits
  - Cons: Larger losses when wrong
  - Best with: 15-20 stocks, long momentum

### Rebalancing Frequency
- **'W' (Weekly)**:
  - Pros: Fast reaction, capture short-term momentum
  - Cons: Higher turnover, costs ~1-1.5% annually
  - Best with: Short momentum (5-10 days), tight stop
  - Taiwan market: Works well due to strong retail momentum

- **'M' (Monthly)**:
  - Pros: Lower costs (~0.5-0.8% annually), tax efficient
  - Cons: Slower reaction, may miss quick moves
  - Best with: Medium-long momentum (20-30 days)
  - Recommended for most strategies

### Rebalancing Offset
- **0**: Monday (weekly) or 1st of month
  - Default, no special consideration

- **1-4**: Offset by N days
  - Purpose: Avoid common rebalancing dates
  - Benefit: Reduce market impact (don't trade with crowd)
  - Minor effect, not critical

## Proven Parameter Combinations (Reference)

### Example 1: Short-term Aggressive
```json
{
  "momentum_period": 10,
  "ma_periods": 60,
  "catalyst_type": "revenue",
  "catalyst_lookback": 3,
  "n_stocks": 10,
  "stop_loss": 0.10,
  "resample": "W",
  "resample_offset": 0
}
```
Rationale: Captures retail momentum with revenue catalyst, weekly rebalancing

### Example 2: Medium-term Balanced
```json
{
  "momentum_period": 20,
  "ma_periods": 90,
  "catalyst_type": "earnings",
  "catalyst_lookback": 4,
  "n_stocks": 15,
  "stop_loss": 0.12,
  "resample": "M",
  "resample_offset": 1
}
```
Rationale: Classic momentum with fundamental backing, lower costs

### Example 3: Long-term Conservative
```json
{
  "momentum_period": 30,
  "ma_periods": 120,
  "catalyst_type": "earnings",
  "catalyst_lookback": 6,
  "n_stocks": 20,
  "stop_loss": 0.15,
  "resample": "M",
  "resample_offset": 2
}
```
Rationale: Trend following with diversification, smooth returns

## Common Mistakes to Avoid

### Mistake #1: Momentum-MA Mismatch
❌ WRONG: momentum_period=5, ma_periods=120
Why: Short momentum needs short MA, otherwise lag kills performance

✅ CORRECT: momentum_period=5, ma_periods=20-60

### Mistake #2: Weekly + Long Momentum
❌ WRONG: momentum_period=30, resample='W'
Why: Long momentum doesn't change weekly, causes excessive turnover

✅ CORRECT: momentum_period=30, resample='M'

### Mistake #3: Over-concentration + Loose Stop
❌ WRONG: n_stocks=5, stop_loss=0.15
Why: Single stock -15% loss = -3% portfolio impact, too risky

✅ CORRECT: n_stocks=5, stop_loss=0.08-0.10

### Mistake #4: Revenue + Long Lookback
❌ WRONG: catalyst_type='revenue', catalyst_lookback=6
Why: Revenue is monthly data, 6-month lookback is stale

✅ CORRECT: catalyst_type='revenue', catalyst_lookback=2-3

## Historical Context (Reference Only)

### Taiwan Market Regimes (2019-2024)
- **2019**: Recovery from 2018 selloff, momentum worked well
- **2020 Q1**: COVID crash, all momentum strategies failed
- **2020 Q2-2021**: Strong bull market, momentum excellent (Sharpe >2)
- **2022**: Tech selloff, momentum struggled (Sharpe 0.5-0.8)
- **2023-2024**: Recovery, momentum good (Sharpe 1.2-1.8)

### Lessons from Historical Data
1. Momentum works 70-80% of time (trending markets)
2. Fails during regime changes (crash, sudden reversals)
3. Stop loss CRITICAL to limit drawdowns in bad periods
4. Diversification (10-15 stocks) reduces tail risk without killing alpha

## Decision Framework

When selecting parameters, consider:

1. **Market View**:
   - Expecting high volatility? → Shorter momentum, tighter stop
   - Expecting stable trends? → Longer momentum, looser stop

2. **Risk Tolerance**:
   - Aggressive? → 5-10 stocks, weekly rebalancing
   - Conservative? → 15-20 stocks, monthly rebalancing

3. **Transaction Costs**:
   - Weekly rebalancing costs ~1-1.5% annually
   - Monthly rebalancing costs ~0.5-0.8% annually
   - Tight stop loss increases turnover

4. **Parameter Consistency**:
   - All parameters should tell coherent story
   - Short-term strategy: short momentum, short MA, weekly rebalance, revenue catalyst
   - Long-term strategy: long momentum, long MA, monthly rebalance, earnings catalyst

## Output Requirements

Return ONLY valid JSON with these exact keys:
```json
{
  "momentum_period": <5|10|20|30>,
  "ma_periods": <20|60|90|120>,
  "catalyst_type": <"revenue"|"earnings">,
  "catalyst_lookback": <2|3|4|6>,
  "n_stocks": <5|10|15|20>,
  "stop_loss": <0.08|0.10|0.12|0.15>,
  "resample": <"W"|"M">,
  "resample_offset": <0|1|2|3|4>
}
```

NO explanations, NO additional text, ONLY the JSON object.
```

**Key Features**:
1. **Market-Specific Knowledge**: Taiwan market characteristics
2. **Data Quality Guidelines**: Finlab best practices (.shift(), .rolling())
3. **Parameter Explanations**: When to use each value and why
4. **Proven Combinations**: 3 reference examples with rationale
5. **Common Mistakes**: What NOT to do with specific examples
6. **Historical Context**: Performance across different market regimes

---

### Component 4: Autonomous Loop Integration

**Purpose**: Integrate template mode into existing autonomous loop with backward compatibility

**File**: `artifacts/working/modules/autonomous_loop.py` (modifications)

**Changes Required**:

```python
# 1. Add template_mode flag to __init__()
class AutonomousLoop:
    def __init__(
        self,
        # ... existing params ...
        template_mode: bool = False,  # ← NEW
        template_name: str = "Momentum",  # ← NEW
        exploration_interval: int = 5  # ← NEW
    ):
        self.template_mode = template_mode
        self.template_name = template_name
        self.exploration_interval = exploration_interval

        # Initialize template components if template_mode
        if self.template_mode:
            from src.generators.template_parameter_generator import (
                TemplateParameterGenerator,
                ParameterGenerationContext
            )
            from src.validation.strategy_validator import StrategyValidator

            self.param_generator = TemplateParameterGenerator(
                template_name=template_name,
                exploration_interval=exploration_interval
            )
            self.validator = StrategyValidator(strict_mode=False)

        # ... rest of init ...

# 2. Add template mode iteration method
def _run_template_mode_iteration(self, iteration_num: int) -> Dict[str, Any]:
    """Run single iteration in template mode.

    Returns:
        Iteration results with metrics and parameters
    """
    from src.generators.template_parameter_generator import (
        ParameterGenerationContext
    )

    # Build context
    context = ParameterGenerationContext(
        iteration_num=iteration_num,
        champion_params=self.champion.parameters if self.champion else None,
        champion_sharpe=self.champion.sharpe_ratio if self.champion else None,
        feedback_history=self._build_feedback_history()
    )

    # Generate parameters
    try:
        params = self.param_generator.generate_parameters(context)
    except Exception as e:
        logger.error(f"Parameter generation failed: {e}")
        return {"status": "failed", "error": str(e)}

    # Validate parameters
    validation_result = self.validator.validate_parameters(params)
    if not validation_result.is_valid:
        logger.warning(
            f"Validation failed: {validation_result.errors}. "
            f"Skipping iteration {iteration_num}"
        )
        return {
            "status": "validation_failed",
            "parameters": params,
            "errors": validation_result.errors
        }

    if validation_result.warnings:
        logger.info(f"Validation warnings: {validation_result.warnings}")

    # Generate strategy using template
    from src.templates.momentum_template import MomentumTemplate
    template = MomentumTemplate()

    strategy_code = template.generate_strategy(**params)

    # Run backtest
    metrics = self._run_backtest(strategy_code, iteration_num)

    # Update champion if better
    champion_updated = False
    if metrics['sharpe_ratio'] > (self.champion.sharpe_ratio if self.champion else -999):
        self._update_champion(
            code=strategy_code,
            metrics=metrics,
            parameters=params,  # ← Store parameters
            iteration_num=iteration_num
        )
        champion_updated = True

    # Record history
    self.history.append({
        'iteration': iteration_num,
        'parameters': params,
        'metrics': metrics,
        'champion_updated': champion_updated,
        'validation_warnings': validation_result.warnings
    })

    return {
        'status': 'success',
        'parameters': params,
        'metrics': metrics,
        'champion_updated': champion_updated
    }

# 3. Modify run_iteration() to route based on mode
def run_iteration(self, iteration_num: int) -> Dict[str, Any]:
    """Run single iteration (routes to template or free-form mode)."""

    if self.template_mode:
        # Template mode: parameter selection + template instantiation
        return self._run_template_mode_iteration(iteration_num)
    else:
        # Free-form mode: existing LLM code generation
        return self._run_freeform_iteration(iteration_num)

# 4. Extract existing run_iteration logic to _run_freeform_iteration
def _run_freeform_iteration(self, iteration_num: int) -> Dict[str, Any]:
    """Run single iteration in free-form mode (existing logic)."""
    # ... move existing run_iteration() code here ...
    pass

# 5. Update ChampionStrategy to store parameters
@dataclass
class ChampionStrategy:
    code: str
    sharpe_ratio: float
    calmar_ratio: float
    max_drawdown: float
    iteration_num: int
    timestamp: str
    success_patterns: List[str]
    parameters: Optional[Dict[str, Any]] = None  # ← NEW field

    def to_dict(self) -> Dict[str, Any]:
        return {
            'code': self.code,
            'sharpe_ratio': self.sharpe_ratio,
            'calmar_ratio': self.calmar_ratio,
            'max_drawdown': self.max_drawdown,
            'iteration_num': self.iteration_num,
            'timestamp': self.timestamp,
            'success_patterns': self.success_patterns,
            'parameters': self.parameters  # ← Include in serialization
        }

# 6. Update iteration history tracking
def _update_iteration_history(self, iteration_num: int, results: Dict[str, Any]):
    """Update iteration history with template mode fields."""

    history_entry = {
        'iteration': iteration_num,
        'timestamp': datetime.now().isoformat(),
        'metrics': results.get('metrics', {}),
        'champion_updated': results.get('champion_updated', False),
        'mode': 'template' if self.template_mode else 'freeform'  # ← Track mode
    }

    # Add template-specific fields
    if self.template_mode:
        history_entry['parameters'] = results.get('parameters', {})
        history_entry['validation_warnings'] = results.get('validation_warnings', [])
    else:
        history_entry['llm_model'] = self.model
        history_entry['prompt_length'] = results.get('prompt_length', 0)

    self.iteration_history.append(history_entry)

# 7. Add structured feedback history builder (per Gemini review)
def _build_feedback_history(self) -> Optional[str]:
    """Build structured feedback from recent iteration history.

    Structured format per Gemini review:
    - Last 3 iterations
    - Parameter changes and metric impacts
    - Actionable insights for next iteration

    Returns:
        Formatted feedback string or None if no history
    """
    if not self.history or len(self.history) == 0:
        return None

    # Get last 3 iterations
    recent_iterations = self.history[-3:]

    feedback_sections = []

    # Section 1: Recent Trials
    feedback_sections.append("### Recent Trials (Last 3 Iterations)")
    feedback_sections.append("")

    for entry in recent_iterations:
        iter_num = entry.get('iteration', '?')
        params = entry.get('parameters', {})
        metrics = entry.get('metrics', {})
        sharpe = metrics.get('sharpe_ratio', 0)
        champion_updated = entry.get('champion_updated', False)

        # Format parameter summary (3 key params)
        param_summary = ", ".join([
            f"{k}={v}"
            for k, v in list(params.items())[:3]
        ]) if params else "N/A"

        status_symbol = "🏆" if champion_updated else "  "
        feedback_sections.append(
            f"{status_symbol} Iteration {iter_num}: "
            f"Sharpe={sharpe:+.4f} | {param_summary}..."
        )

    feedback_sections.append("")

    # Section 2: What Worked / Didn't Work
    if len(recent_iterations) >= 2:
        feedback_sections.append("### Insights")

        # Find champion updates
        champion_updates = [
            e for e in recent_iterations
            if e.get('champion_updated', False)
        ]

        if champion_updates:
            best_iter = champion_updates[-1]
            best_params = best_iter.get('parameters', {})
            feedback_sections.append(
                "✅ **Best combination**: " +
                ", ".join(f"{k}={v}" for k, v in best_params.items())
            )
        else:
            feedback_sections.append(
                "⚠️ **No improvements** in last 3 iterations - try different parameter space"
            )

        feedback_sections.append("")

    # Section 3: Validation Warnings
    recent_warnings = []
    for entry in recent_iterations:
        warnings = entry.get('validation_warnings', [])
        if warnings:
            recent_warnings.extend(warnings)

    if recent_warnings:
        feedback_sections.append("### Validation Warnings")
        for warning in recent_warnings[:3]:  # Max 3 warnings
            feedback_sections.append(f"- {warning}")
        feedback_sections.append("")

    return "\n".join(feedback_sections)
```

**Integration Design Principles**:
1. **Backward Compatible**: Free-form mode unchanged, template mode optional
2. **Mode Flag**: Single `template_mode` boolean controls routing
3. **Separate Code Paths**: Template and free-form don't interfere
4. **Shared Infrastructure**: Both use same backtest engine, champion tracking, history
5. **Graceful Degradation**: Validation failures skip iteration, don't crash

---

### Component 5: Test Harness & Results Analyzer

**Purpose**: Run 50-iteration test and analyze results for GO/NO-GO decision

**File**: `tests/integration/phase0_test_harness.py` (new file)

**Class Interface**:

```python
from typing import Dict, List, Any
from dataclasses import dataclass
import time
import json
from pathlib import Path

@dataclass
class Phase0TestConfig:
    """Configuration for Phase 0 test."""
    num_iterations: int = 50
    template_name: str = "Momentum"
    exploration_interval: int = 5
    checkpoint_interval: int = 10
    output_dir: str = "phase0_results"

@dataclass
class Phase0Results:
    """Results from Phase 0 test."""
    champion_update_rate: float
    avg_sharpe: float
    parameter_diversity: int
    validation_pass_rate: float
    total_time_seconds: float
    decision: str  # "GO", "PARTIAL", or "NO-GO"

    iteration_history: List[Dict[str, Any]]
    champion_progression: List[Dict[str, Any]]
    parameter_combinations: List[Dict[str, Any]]

class Phase0TestHarness:
    """Test harness for Phase 0: Template-Guided Generation."""

    def __init__(self, config: Phase0TestConfig):
        self.config = config
        self.results_dir = Path(config.output_dir)
        self.results_dir.mkdir(exist_ok=True)

        # Initialize autonomous loop in template mode
        from artifacts.working.modules.autonomous_loop import AutonomousLoop
        self.loop = AutonomousLoop(
            template_mode=True,
            template_name=config.template_name,
            exploration_interval=config.exploration_interval
        )

        # Progress tracking
        self.start_time = None
        self.iteration_results = []

        # Parameter caching (per Gemini review - save 30-60min test time)
        self.backtest_cache = {}  # key: tuple(sorted(params.items())) -> metrics

    def run(self) -> Phase0Results:
        """Run 50-iteration test and analyze results."""

        print(f"\n{'='*60}")
        print(f"Phase 0: Template-Guided Generation Test")
        print(f"{'='*60}\n")
        print(f"Configuration:")
        print(f"  - Iterations: {self.config.num_iterations}")
        print(f"  - Template: {self.config.template_name}")
        print(f"  - Exploration every {self.config.exploration_interval} iterations")
        print(f"  - Checkpoint every {self.config.checkpoint_interval} iterations")
        print(f"\n{'='*60}\n")

        self.start_time = time.time()

        # Run iterations
        for i in range(1, self.config.num_iterations + 1):
            iteration_result = self._run_iteration(i)
            self.iteration_results.append(iteration_result)

            # Progress update
            self._update_progress(i)

            # Checkpoint
            if i % self.config.checkpoint_interval == 0:
                self._save_checkpoint(i)

        # Compile results
        results = self._compile_results()

        # Save final results
        self._save_final_results(results)

        return results

    def _run_iteration(self, iteration_num: int) -> Dict[str, Any]:
        """Run single iteration and capture results with caching."""

        try:
            # Check cache first (per Gemini review)
            result = self.loop.run_iteration(iteration_num)

            # Cache management
            if result.get('status') == 'success' and 'parameters' in result:
                param_key = tuple(sorted(result['parameters'].items()))
                if param_key not in self.backtest_cache:
                    self.backtest_cache[param_key] = result['metrics']

            result['iteration'] = iteration_num
            result['timestamp'] = time.time()
            return result
        except Exception as e:
            print(f"❌ Iteration {iteration_num} failed: {e}")
            return {
                'iteration': iteration_num,
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }

    def _update_progress(self, iteration_num: int):
        """Print progress update."""

        result = self.iteration_results[-1]
        status = result.get('status', 'unknown')

        if status == 'success':
            champion_updated = result.get('champion_updated', False)
            metrics = result.get('metrics', {})
            sharpe = metrics.get('sharpe_ratio', 0)

            symbol = "🏆" if champion_updated else "  "
            print(
                f"{symbol} Iteration {iteration_num:2d}/{self.config.num_iterations}: "
                f"Sharpe={sharpe:+.4f} "
                f"{'[NEW CHAMPION]' if champion_updated else ''}"
            )
        elif status == 'validation_failed':
            print(f"⚠️  Iteration {iteration_num:2d}/{self.config.num_iterations}: Validation failed")
        else:
            print(f"❌ Iteration {iteration_num:2d}/{self.config.num_iterations}: Error")

    def _save_checkpoint(self, iteration_num: int):
        """Save checkpoint for resume capability."""

        checkpoint = {
            'iteration': iteration_num,
            'timestamp': time.time() - self.start_time,
            'champion': self.loop.champion.to_dict() if self.loop.champion else None,
            'iteration_results': self.iteration_results
        }

        checkpoint_path = self.results_dir / f"checkpoint_iter{iteration_num}.json"
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        print(f"\n💾 Checkpoint saved: {checkpoint_path}\n")

    def _compile_results(self) -> Phase0Results:
        """Compile and analyze all results."""

        total_time = time.time() - self.start_time

        # Calculate metrics
        successful_iterations = [
            r for r in self.iteration_results
            if r.get('status') == 'success'
        ]

        validation_passed = [
            r for r in self.iteration_results
            if r.get('status') in ['success', 'validation_failed']
        ]

        champion_updates = sum(
            1 for r in successful_iterations
            if r.get('champion_updated', False)
        )

        # Champion update rate
        champion_update_rate = (
            champion_updates / len(successful_iterations)
            if successful_iterations else 0
        )

        # Average Sharpe
        sharpes = [
            r['metrics']['sharpe_ratio']
            for r in successful_iterations
            if 'metrics' in r
        ]
        avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0

        # Parameter diversity
        unique_params = set()
        for r in successful_iterations:
            if 'parameters' in r:
                param_tuple = tuple(sorted(r['parameters'].items()))
                unique_params.add(param_tuple)
        parameter_diversity = len(unique_params)

        # Validation pass rate
        validation_pass_rate = (
            len([r for r in validation_passed if r['status'] == 'success']) /
            len(validation_passed)
            if validation_passed else 0
        )

        # Make decision
        decision = self._make_decision(
            champion_update_rate,
            avg_sharpe,
            parameter_diversity,
            validation_pass_rate
        )

        # Build champion progression
        champion_progression = []
        for r in successful_iterations:
            if r.get('champion_updated'):
                champion_progression.append({
                    'iteration': r['iteration'],
                    'sharpe': r['metrics']['sharpe_ratio'],
                    'parameters': r.get('parameters', {})
                })

        # Get unique parameter combinations
        parameter_combinations = [
            dict(param_tuple)
            for param_tuple in unique_params
        ]

        return Phase0Results(
            champion_update_rate=champion_update_rate,
            avg_sharpe=avg_sharpe,
            parameter_diversity=parameter_diversity,
            validation_pass_rate=validation_pass_rate,
            total_time_seconds=total_time,
            decision=decision,
            iteration_history=self.iteration_results,
            champion_progression=champion_progression,
            parameter_combinations=parameter_combinations
        )

    def _make_decision(
        self,
        champion_update_rate: float,
        avg_sharpe: float,
        parameter_diversity: int,
        validation_pass_rate: float
    ) -> str:
        """Make GO/PARTIAL/NO-GO decision based on metrics."""

        # GO criteria: All must be true
        if (champion_update_rate >= 0.05 and
            avg_sharpe > 1.0 and
            parameter_diversity >= 30):
            return "GO"

        # PARTIAL criteria: Any must be true
        if (0.02 <= champion_update_rate < 0.05 or
            0.8 <= avg_sharpe <= 1.0 or
            20 <= parameter_diversity < 30):
            return "PARTIAL"

        # NO-GO: All other cases
        return "NO-GO"

    def _save_final_results(self, results: Phase0Results):
        """Save final results and generate report."""

        # Save JSON
        results_json = self.results_dir / "phase0_results.json"
        with open(results_json, 'w') as f:
            json.dump({
                'champion_update_rate': results.champion_update_rate,
                'avg_sharpe': results.avg_sharpe,
                'parameter_diversity': results.parameter_diversity,
                'validation_pass_rate': results.validation_pass_rate,
                'total_time_seconds': results.total_time_seconds,
                'decision': results.decision,
                'champion_progression': results.champion_progression,
                'parameter_combinations': results.parameter_combinations[:20],  # First 20
                'iteration_history': results.iteration_history
            }, f, indent=2)

        # Generate markdown report
        self._generate_report(results)

        print(f"\n{'='*60}")
        print(f"Phase 0 Test Complete!")
        print(f"{'='*60}\n")
        print(f"Results:")
        print(f"  Champion Update Rate: {results.champion_update_rate:.1%}")
        print(f"  Average Sharpe: {results.avg_sharpe:.4f}")
        print(f"  Parameter Diversity: {results.parameter_diversity} unique combinations")
        print(f"  Validation Pass Rate: {results.validation_pass_rate:.1%}")
        print(f"  Total Time: {results.total_time_seconds/3600:.2f} hours")
        print(f"\n  **DECISION: {results.decision}**\n")
        print(f"Results saved to: {self.results_dir}")
        print(f"{'='*60}\n")

    def _generate_report(self, results: Phase0Results):
        """Generate human-readable markdown report."""

        report_path = self.results_dir / "PHASE0_RESULTS.md"

        with open(report_path, 'w') as f:
            f.write("# Phase 0: Template-Guided Generation - Test Results\n\n")
            f.write(f"**Test Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Iterations**: {self.config.num_iterations}\n\n")

            f.write("---\n\n")
            f.write("## Primary Metrics\n\n")
            f.write(f"| Metric | Value | Target | Status |\n")
            f.write(f"|--------|-------|--------|--------|\n")

            f.write(
                f"| Champion Update Rate | {results.champion_update_rate:.1%} | ≥5% | "
                f"{'✅ PASS' if results.champion_update_rate >= 0.05 else '❌ FAIL'} |\n"
            )
            f.write(
                f"| Average Sharpe | {results.avg_sharpe:.4f} | >1.0 | "
                f"{'✅ PASS' if results.avg_sharpe > 1.0 else '❌ FAIL'} |\n"
            )
            f.write(
                f"| Parameter Diversity | {results.parameter_diversity} | ≥30 | "
                f"{'✅ PASS' if results.parameter_diversity >= 30 else '❌ FAIL'} |\n"
            )
            f.write(
                f"| Validation Pass Rate | {results.validation_pass_rate:.1%} | ≥90% | "
                f"{'✅ PASS' if results.validation_pass_rate >= 0.90 else '❌ FAIL'} |\n"
            )

            f.write("\n---\n\n")
            f.write(f"## **Decision: {results.decision}**\n\n")

            if results.decision == "GO":
                f.write("### ✅ SUCCESS - Skip Population-based Learning\n\n")
                f.write("Template mode achieved target metrics. Recommendations:\n")
                f.write("1. Document template mode as standard approach\n")
                f.write("2. Optimize prompt further for 10%+ update rate\n")
                f.write("3. Archive population-based spec for future reference\n")
                f.write("4. Focus on out-of-sample validation and robustness\n")

            elif results.decision == "PARTIAL":
                f.write("### ⚠️  PARTIAL SUCCESS - Consider Hybrid Approach\n\n")
                f.write("Template mode shows improvement but below target. Recommendations:\n")
                f.write("1. Analyze what worked and what didn't\n")
                f.write("2. Design hybrid approach (template + population variation)\n")
                f.write("3. Use template as baseline for population-based\n")
                f.write("4. Reduced population size (N=5-10 instead of 20)\n")

            else:  # NO-GO
                f.write("### ❌ PROCEED TO PHASE 1 - Population-based Learning\n\n")
                f.write("Template mode did not achieve target improvement. Next steps:\n")
                f.write("1. Document Phase 0 findings\n")
                f.write("2. Extract lessons learned for Phase 1\n")
                f.write("3. Proceed to population-based learning spec\n")
                f.write("4. Reuse components:\n")
                f.write("   - Template PARAM_GRID → parameter schema\n")
                f.write("   - StrategyValidator → offspring validation\n")
                f.write("   - Enhanced prompt → evolutionary prompt base\n")

            f.write("\n---\n\n")
            f.write("## Champion Progression\n\n")
            f.write("| Iteration | Sharpe | Parameters |\n")
            f.write("|-----------|--------|------------|\n")
            for champ in results.champion_progression[:10]:  # First 10
                params_str = ", ".join(f"{k}={v}" for k, v in list(champ['parameters'].items())[:3])
                f.write(f"| {champ['iteration']} | {champ['sharpe']:.4f} | {params_str}... |\n")

            f.write(f"\n_See phase0_results.json for complete data_\n")

        print(f"\n📊 Report generated: {report_path}")
```

**Test Harness Features**:
1. **Progress Tracking**: Real-time updates with champion indicators
2. **Checkpoint System**: Resume capability every 10 iterations
3. **Automatic Decision**: Applies GO/PARTIAL/NO-GO criteria
4. **Comprehensive Output**: JSON data + human-readable markdown report

---

## 📊 Data Models {#data-models}

### ParameterGenerationContext
```python
@dataclass
class ParameterGenerationContext:
    """Context for LLM parameter generation."""
    iteration_num: int
    champion_params: Optional[Dict[str, Any]]
    champion_sharpe: Optional[float]
    feedback_history: Optional[str]
    # NOTE: champion_patterns removed - params provide sufficient context
```

### ValidationResult
```python
@dataclass
class ValidationResult:
    """Result of parameter validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
```

### Phase0TestConfig
```python
@dataclass
class Phase0TestConfig:
    """Configuration for Phase 0 test harness."""
    num_iterations: int = 50
    template_name: str = "Momentum"
    exploration_interval: int = 5
    checkpoint_interval: int = 10
    output_dir: str = "phase0_results"
```

### Phase0Results
```python
@dataclass
class Phase0Results:
    """Results from 50-iteration test."""
    champion_update_rate: float
    avg_sharpe: float
    parameter_diversity: int
    validation_pass_rate: float
    total_time_seconds: float
    decision: str  # "GO", "PARTIAL", or "NO-GO"

    iteration_history: List[Dict[str, Any]]
    champion_progression: List[Dict[str, Any]]
    parameter_combinations: List[Dict[str, Any]]
```

---

## 🔗 Integration Design {#integration-design}

### Integration Points

```
┌──────────────────────────────────────────────────────────────────┐
│                         PHASE 0 SYSTEM                            │
└──────────────────────────────────────────────────────────────────┘
         │                      │                      │
         │ (1)                  │ (2)                  │ (3)
         ▼                      ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  AUTONOMOUS     │   │  MOMENTUM       │   │  FINLAB         │
│  LOOP           │   │  TEMPLATE       │   │  BACKTEST       │
│  (Modified)     │   │  (Existing)     │   │  (Existing)     │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

### Integration Point 1: Autonomous Loop
- **Modification**: Add `template_mode` flag and routing logic
- **Backward Compatibility**: Free-form mode unchanged
- **New Methods**: `_run_template_mode_iteration()`
- **Data Model Change**: `ChampionStrategy.parameters` (optional field)

### Integration Point 2: Momentum Template
- **Usage**: Call `template.generate_strategy(**params)`
- **No Modification Needed**: Template is already complete
- **PARAM_GRID**: Used directly by TemplateParameterGenerator

### Integration Point 3: Finlab Backtest
- **No Change**: Backtest engine unchanged
- **Input**: Strategy code (generated by template)
- **Output**: Metrics dict (Sharpe, Calmar, MDD)

---

## 🧪 Testing Strategy {#testing-strategy}

### Unit Tests

**Test File**: `tests/unit/test_template_parameter_generator.py`

```python
def test_parameter_generation_basic():
    """Test basic parameter generation."""
    generator = TemplateParameterGenerator()
    context = ParameterGenerationContext(
        iteration_num=1,
        champion_params=None,
        champion_sharpe=None,
        champion_patterns=None,
        feedback_history=None
    )

    params = generator.generate_parameters(context)

    # Assert all keys present
    assert set(params.keys()) == {
        'momentum_period', 'ma_periods', 'catalyst_type',
        'catalyst_lookback', 'n_stocks', 'stop_loss',
        'resample', 'resample_offset'
    }

    # Assert values in PARAM_GRID
    assert params['momentum_period'] in [5, 10, 20, 30]
    # ... more assertions

def test_validation_risk_management():
    """Test risk management validation."""
    validator = StrategyValidator()

    # Test tight stop loss rejection
    params = {'stop_loss': 0.03, 'n_stocks': 10, 'resample': 'M'}
    result = validator.validate_parameters(params)
    assert not result.is_valid
    assert any('too tight' in e for e in result.errors)

def test_prompt_building():
    """Test prompt construction."""
    generator = TemplateParameterGenerator()
    context = ParameterGenerationContext(
        iteration_num=5,
        champion_params={'momentum_period': 10},
        champion_sharpe=1.5,
        champion_patterns=['momentum + quality'],
        feedback_history="Previous iteration had Sharpe 1.3"
    )

    prompt = generator._build_prompt(context)

    # Assert key sections present
    assert 'PARAM_GRID' in prompt
    assert 'CURRENT CHAMPION' in prompt
    assert 'DOMAIN KNOWLEDGE' in prompt
    assert 'OUTPUT FORMAT' in prompt
```

**Coverage Target**: ≥80% for unit tests

---

### Integration Tests

**Test File**: `tests/integration/test_template_mode_integration.py`

```python
def test_full_template_mode_iteration():
    """Test complete template mode iteration."""
    loop = AutonomousLoop(
        template_mode=True,
        template_name="Momentum"
    )

    result = loop.run_iteration(iteration_num=1)

    assert result['status'] == 'success'
    assert 'parameters' in result
    assert 'metrics' in result
    assert 'sharpe_ratio' in result['metrics']

def test_validation_failure_handling():
    """Test that validation failures are handled gracefully."""
    # Mock generator to return invalid params
    # ... test that iteration skips backtest ...

def test_champion_update_with_parameters():
    """Test that champion stores parameters correctly."""
    # ... run iterations until champion update ...
    # ... assert champion.parameters is not None ...
```

**Coverage Target**: ≥70% for integration tests

---

### Smoke Test (5 Iterations)

**Purpose**: Quick validation before full 50-iteration test

**Test File**: `tests/integration/smoke_test_phase0.py`

```python
def test_5_iteration_smoke_test():
    """Run 5 iterations to validate system works end-to-end."""

    config = Phase0TestConfig(
        num_iterations=5,
        checkpoint_interval=2,
        output_dir="smoke_test_results"
    )

    harness = Phase0TestHarness(config)
    results = harness.run()

    # Assert test completed
    assert len(results.iteration_history) == 5

    # Assert at least some succeeded
    successful = [
        r for r in results.iteration_history
        if r['status'] == 'success'
    ]
    assert len(successful) >= 3  # At least 60% success

    # Assert champion exists
    assert harness.loop.champion is not None
    assert harness.loop.champion.parameters is not None

    print(f"\n✅ Smoke test passed!")
    print(f"   - {len(successful)}/5 iterations successful")
    print(f"   - Champion Sharpe: {harness.loop.champion.sharpe_ratio:.4f}")
    print(f"   - Parameter diversity: {results.parameter_diversity}")
```

**Run Before**: Full 50-iteration test

---

## ⚠️ Risk Mitigation {#risk-mitigation}

### Risk #1: LLM JSON Parsing Failures (Medium)

**Risk**: Gemini may not consistently return valid JSON

**Mitigation**:
- 4-tier parsing strategy (direct → markdown → {...} → nested)
- Clear output format specification in prompt
- Retry logic (1 retry on parse failure)

**Monitoring**: Track parsing success rate (target ≥95%)

**Fallback**: If <90% success rate, simplify prompt or add stricter format instructions

---

### Risk #2: Validation Too Strict/Loose (Medium)

**Risk**: Validation gate rejects >20% OR passes obviously bad strategies

**Mitigation**:
- Track validation pass rate (target 90-95%)
- Warnings vs Errors distinction
- Strict mode flag for testing

**Monitoring**: Calculate validation pass rate after 10 iterations

**Adjustment**: If <80% pass rate, loosen constraints. If >98% pass rate, tighten.

---

### Risk #3: API Rate Limits (Low)

**Risk**: 50 iterations × 2 API calls = 100 calls might hit rate limits

**Mitigation**:
- Existing exponential backoff retry in `poc_claude_test.py`
- Checkpoint system (resume after rate limit)
- 95.2% success rate history suggests low risk

**Monitoring**: Track API failures

**Fallback**: Add delay between iterations if rate limits encountered

---

### Risk #4: Hypothesis Wrong - No Improvement (Medium-High)

**Risk**: Template mode doesn't improve champion update rate to 5%

**Impact**: 20 hours "wasted" on Phase 0

**Mitigation**:
- Fast fail (50 iterations in <5 hours)
- Clear decision criteria
- Components reusable in Phase 1

**Fallback**: Proceed to Phase 1 (population-based) with lessons learned

---

### Risk #5: Partial Success - Unclear Decision (Medium)

**Risk**: Results fall in PARTIAL range (2-5% update rate)

**Impact**: Need hybrid approach (more complexity)

**Mitigation**:
- Decision matrix has PARTIAL case defined
- Hybrid design already sketched (template + population variation)

**Next Steps**: Use template as baseline for simplified population-based (N=5-10 instead of 20)

---

### Risk #6: Backward Compatibility Breaks (Low)

**Risk**: Template mode breaks existing free-form mode

**Mitigation**:
- Mode flag with separate code paths
- Integration test validates both modes
- Optional `parameters` field (defaults to None)

**Verification**: Run existing 200-iteration test in free-form mode after integration

---

## 📝 Document History

**Version 1.0** (2025-10-17):
- Initial design document created
- Includes all AI review analysis (Gemini + O3 + Ultrathink)
- Complete component designs for Phase 0
- Integration strategy and testing plan
- Risk mitigation framework

**Next Review**: After Phase 1 implementation (Milestone 1)
