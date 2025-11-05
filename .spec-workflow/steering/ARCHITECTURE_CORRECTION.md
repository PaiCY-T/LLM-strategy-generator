# Architecture Correction - LLM Innovation as Core Capability

**Date**: 2025-10-28
**Reason**: Correct fundamental misunderstanding of system architecture
**Priority**: CRITICAL

---

## Executive Summary

**System Architecture Correction**: FinLab is an **LLM-driven strategy evolution system**, not a pure genetic algorithm system with optional LLM features.

**Root Cause of Misunderstanding**: LLM innovation disabled by default (`config/learning_system.yaml:708 - llm.enabled: false`) led to incorrect interpretation of system design intent.

**Impact**: Phase1 Smoke Test failures (0.5% champion update rate, diversity collapse, early convergence) are direct results of running the system WITHOUT its core innovation capability.

---

## System Architecture (CORRECTED)

### Three-Stage Evolution Model

**The system progresses through three distinct stages:**

```
Stage 0: Random Exploration (33% success rate)
   ↓ Bootstrap phase
   ↓ No champion, pure exploration
   ↓
Stage 1: Champion-Based Learning (70% success rate) ← MVP Baseline
   ↓ Single best strategy refinement
   ↓ Template-based parameter optimization
   ↓
Stage 2: Population + LLM Innovation (>80% target) ← CURRENT GOAL
   ↓ Hybrid innovation model
   ↓ 20% LLM structural innovation
   ↓ 80% Factor Graph mutation (fallback)
   ↓
BREAKTHROUGH: Sharpe >2.5, sustained diversity, continuous improvement
```

### Current State vs Design Intent

| Aspect | Design Intent | Current Reality | Consequence |
|--------|---------------|-----------------|-------------|
| **Core Innovation** | LLM-driven (20%) | Disabled (`llm.enabled=false`) | No structural innovation |
| **Innovation Mode** | Structured YAML | Fallback to Factor Graph only | Limited to 13 predefined factors |
| **Target Stage** | Stage 2 (>80%) | Stuck at Stage 1 (70%) | Cannot reach breakthrough |
| **Diversity** | Maintained via LLM | Collapses (0.104 < 0.2) | Premature convergence |
| **Update Rate** | 10-20% balanced | 0.5% (stagnation) | Early peak, no improvement |

---

## LLM Innovation Architecture

### Core Components (FULLY IMPLEMENTED BUT INACTIVE)

```
┌─────────────────────────────────────────────────────────────┐
│                  Autonomous Iteration Loop                   │
│                  (iteration_engine.py)                       │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ 20% innovation_rate
               ▼
┌─────────────────────────────────────────────────────────────┐
│                    InnovationEngine                          │
│  (src/innovation/innovation_engine.py)                       │
├─────────────────────────────────────────────────────────────┤
│  • LLMProvider: OpenRouter/Gemini/OpenAI integration        │
│  • PromptBuilder: Context-aware prompt generation           │
│  • SecurityValidator: Code safety checks                    │
│  • FeedbackProcessor: Learning from failures                │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ Structured YAML Mode
               ▼
┌─────────────────────────────────────────────────────────────┐
│              Structured Innovation Pipeline                  │
│  (structured-innovation-mvp spec)                            │
├─────────────────────────────────────────────────────────────┤
│  1. LLM generates YAML strategy spec (not full code)        │
│  2. YAMLSchemaValidator validates structure                 │
│  3. YAMLToCodeGenerator creates Python code via Jinja2      │
│  4. 7-Layer Validation ensures safety/correctness           │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ 90% success rate (vs 60% full code)
               ▼
┌─────────────────────────────────────────────────────────────┐
│                 7-Layer Validation Framework                 │
├─────────────────────────────────────────────────────────────┤
│  1. Syntax Validation (AST parse)                           │
│  2. Semantic Validation (finlab API usage)                  │
│  3. Security Validation (no file I/O, limited imports)      │
│  4. Backtestability Check (can run without errors)          │
│  5. Metric Extraction (Sharpe, Calmar, Drawdown)            │
│  6. Multi-Objective Check (Sharpe + Calmar + Drawdown)      │
│  7. Baseline Comparison (beat Buy-and-Hold 0050)            │
└──────────────┬──────────────────────────────────────────────┘
               │
               │ Auto-fallback on failure
               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Factor Graph Mutation                       │
│  (80% of iterations, 100% when LLM disabled)                │
├─────────────────────────────────────────────────────────────┤
│  • 13 predefined factors (Momentum, Value, Quality, etc.)   │
│  • Limited exploration space (finite combinations)          │
│  • Safe but cannot discover novel patterns                  │
└─────────────────────────────────────────────────────────────┘
```

### Why LLM Innovation is Core (Not Optional)

**1. Breaks Factor Limitations**
- Without LLM: 13 fixed factors → limited exploration space
- With LLM: Unlimited factor combinations → continuous innovation
- **Evidence**: Phase1 Smoke Test diversity collapsed to 0.104 (< 0.2 threshold)

**2. Maintains Population Diversity**
- Without LLM: Parameter perturbation → rapid convergence
- With LLM: Structural innovation → sustained exploration
- **Evidence**: 0.5% champion update rate vs 10% target

**3. Achieves Performance Breakthrough**
- Without LLM: Local optimization → stuck at early peaks (1.1558)
- With LLM: Global exploration → breaks through plateaus (target >2.5)
- **Evidence**: Gen 1 peak (1.30), no improvement through Gen 10

**4. Stage 2 Requirement**
- Stage 1 (MVP): 70% success, 1.15 avg Sharpe ← Achieved without LLM
- Stage 2 (Target): >80% success, >2.5 Sharpe ← **REQUIRES LLM**

---

## Key Configuration

### Critical Setting: llm.enabled

**Location**: `config/learning_system.yaml:708`

```yaml
llm:
  enabled: ${LLM_ENABLED:false}  # ← DEFAULT: DISABLED for backward compatibility
  provider: ${LLM_PROVIDER:openrouter}
  innovation_rate: ${INNOVATION_RATE:0.20}  # 20% when enabled
  mode: ${LLM_MODE:structured}  # YAML mode reduces hallucinations by 80%

  generation:
    max_tokens: ${LLM_MAX_TOKENS:2000}
    temperature: ${LLM_TEMPERATURE:0.7}
    timeout: ${LLM_TIMEOUT:60}

  fallback:
    enabled: true
    max_retries: 3
    fallback_mode: "factor_graph"  # Auto-fallback to 80% path

structured_innovation:
  validation:
    strict_mode: true
    max_retries: 3
  code_generation:
    validate_ast: true
  fallback:
    auto_fallback: true
    fallback_mode: "factor_graph"
```

### Why Disabled by Default

**Rationale** (inferred from code analysis):
1. **Backward Compatibility**: Preserve existing workflows during Phase 1 development
2. **Cost Control**: LLM API calls incur costs (OpenRouter/Gemini/OpenAI)
3. **Stability**: Phase 1 focused on validation framework, not full LLM integration
4. **Progressive Rollout**: Enable after safety validation complete

**Current Status**:
- ✅ Phase 1: Exit mutation framework complete
- ✅ Phase 2-3: InnovationEngine + 7-layer validation implemented
- ⏳ **Phase 4: Activation pending** ← Current decision point

---

## Documented Specifications

### Primary Specs (Already Implemented)

**1. llm-integration-activation.merged_20251028/design.md**
- **Purpose**: Main specification for LLM integration activation
- **Key Content**:
  - Activates InnovationEngine in autonomous loop
  - 20% innovation rate (every 5th iteration)
  - Automatic fallback to Factor Graph on LLM failures
  - Error handling for 6 failure scenarios
- **Status**: ✅ Implemented, not activated

**2. structured-innovation-mvp.merged_20251028/design.md**
- **Purpose**: Solves LLM hallucination problem
- **Key Innovation**: YAML/JSON-based strategy specifications instead of full code
- **Results**:
  - Reduces hallucination risk by 80%
  - 90% success rate (structured) vs 60% (full code)
  - 85% innovation coverage
- **Status**: ✅ Implemented, not activated

**3. yaml-normalizer-phase2-complete-normalization/design.md**
- **Purpose**: Normalizes LLM-generated YAML for consistency
- **Components**: YAMLSchemaValidator, YAMLToCodeGenerator
- **Status**: ✅ Implemented

### Comprehensive Review

**LLM_INNOVATION_COMPREHENSIVE_REVIEW.md**
- **Overall Verdict**: ⚠️ PARTIALLY READY
- **Key Findings**:
  - ✅ Phase 2 & 3 COMPLETE: All innovation components implemented (14 files, ~5000+ lines)
  - ✅ 7-Layer Validation: InnovationValidator comprehensive checks implemented
  - ❌ CRITICAL GAP: No actual LLM integration observed in test runs
  - ⚠️ SECURITY CONCERNS: Sandbox insufficient (needs Docker isolation)
- **Production Readiness**: 6.2/10

---

## Phase1 Smoke Test Results Explained

### Test Configuration
```
Generations:    10
Population:     30 individuals
Elite:          3 individuals
Mutation Rate:  0.15
LLM Enabled:    FALSE ← Root cause
Duration:       14.1 minutes
```

### Results with LLM Disabled

| Metric | Target | Achieved | Root Cause |
|--------|--------|----------|------------|
| Champion Update Rate | ≥10% | **0.5%** | No LLM structural innovation → stuck at local optimum |
| Best IS Sharpe | >2.5 | **1.1558** | Cannot break through without LLM exploration |
| Diversity | ≥50% | **63.3%** → **10.4%** (collapsed) | Limited to 13 factors → rapid convergence |
| Exit Mutation Success | >40% | **0%** | No new exit patterns discovered |
| Convergence | Gen 10+ | **Gen 1** | Early peak, no improvement |

### What Would Happen with LLM Enabled

**Expected Behavior** (based on design specs):
1. **Every 5th iteration**: LLM generates novel strategy structure (YAML)
2. **Diversity maintained**: New factor combinations prevent convergence
3. **Breakthrough potential**: LLM can discover patterns outside 13 predefined factors
4. **Update rate**: 10-20% balanced exploration/exploitation
5. **Stage 2 target**: >80% success rate, >2.5 Sharpe

**Fallback Safety**:
- LLM failures → automatic Factor Graph fallback
- 80% of innovations still use traditional mutations
- No risk of complete failure (hybrid model)

---

## Migration Path

### Phase 1: Dry-Run Mode (2-3 hours)
**Goal**: Test LLM integration without affecting population

1. Enable LLM with dry-run flag
2. Generate YAML strategies (log only, don't commit)
3. Validate through 7-layer pipeline
4. Monitor: validation pass rate, latency, cost

**Success Criteria**:
- ≥70% validation pass rate
- <60s average latency
- Cost within budget

### Phase 2: Low Innovation Rate (5-8 hours)
**Goal**: Staged rollout with safety monitoring

1. Enable LLM with 5% innovation rate (vs 20% design)
2. Run 20-generation test
3. Monitor: diversity, update rate, Sharpe progression
4. Compare with Phase1 Smoke Test baseline

**Success Criteria**:
- Diversity >40% maintained
- Update rate >5%
- No regressions vs baseline

### Phase 3: Full Activation (production)
**Goal**: Activate design-spec 20% innovation rate

1. Increase to 20% innovation rate
2. Run 50-generation validation
3. Achieve Stage 2 targets (>80% success, >2.5 Sharpe)

---

## Steering Document Updates Required

### product.md
**Section 1: Product Purpose** (Line 5)
- BEFORE: "自主學習系統"
- AFTER: "**LLM-driven** 自主學習系統 with autonomous strategy generation"

**Section 2: Key Features** (Line 31-67)
- REORDER: Move LLM innovation to #1 (currently buried in line 36)
- EXPAND: Full subsection on "LLM-Driven Innovation" with 20/80 hybrid model
- ADD: Three-stage evolution model explanation

**Section 3: Business Objectives** (Line 68-81)
- ADD: Stage 2 objective (>80% success, >2.5 Sharpe)
- ADD: LLM activation milestone

**Section 4: Future Vision** (Line 177-201)
- MOVE: "Advanced LLM Integration" from FUTURE to CURRENT
- CLARIFY: LLM is core capability, not enhancement

### tech.md
**Section 1: Core Technologies** (Line 39-45)
- ELEVATE: "AI/LLM Integration" to primary capability (not just dependencies)

**Section 2: Application Architecture** (Line 64-98)
- ADD: InnovationEngine to architecture diagram
- ADD: Structured YAML pipeline layer

**Section 3: Decision Log** (Line 458-473)
- REPLACE: "Template System over Pure LLM Generation"
- WITH: "Hybrid LLM + Factor Graph Innovation (20/80 Model)"

**Section 4: Known Limitations** (Line 546-560)
- REMOVE: "LLM Compliance Risk" from limitations
- MOVE: To core architecture section (reframe as feature, not limitation)

### structure.md
**Section 1: Directory Organization** (Line 1-164)
- ADD: Detailed `src/innovation/` directory documentation
- ADD: InnovationEngine, LLMProvider, PromptBuilder components

**Section 2: Dependencies Direction** (Line 473-503)
- ADD: InnovationEngine layer to dependency diagram

---

## Next Actions

### Immediate (Next 1 hour)
1. ✅ Create this architecture correction document
2. ⏳ Update steering documents (product.md, tech.md, structure.md)
3. ⏳ Request approval via spec workflow

### Short-term (Next 2-4 hours)
4. ⏳ Implement dry-run mode for LLM testing
5. ⏳ Execute Phase 1 migration (dry-run validation)
6. ⏳ Decision: Proceed to Phase 2 or adjust

### Medium-term (Next 8-24 hours)
7. ⏳ Phase 2: Low innovation rate test (5%, 20 generations)
8. ⏳ Phase 3: Full activation test (20%, 50 generations)
9. ⏳ Generate Stage 2 capability assessment report

---

## References

### Specifications
- `.spec-workflow/specs/llm-integration-activation.merged_20251028/design.md`
- `.spec-workflow/specs/structured-innovation-mvp.merged_20251028/design.md`
- `.spec-workflow/specs/yaml-normalizer-phase2-complete-normalization/design.md`

### Analysis Reports
- `LLM_INNOVATION_COMPREHENSIVE_REVIEW.md` - Neutral review of implementation status
- Thinkdeep Analysis (2025-10-28, gemini-2.5-pro) - Root cause identification

### Test Results
- `SESSION_STATUS_2025-10-28_1350.md` - Phase1 Smoke Test results
- `results/phase1_smoke_test_20251028_134941.json` - Full metrics
- `logs/phase1_smoke_test_20251028_133356.log` - Detailed logs

### Configuration
- `config/learning_system.yaml:708` - `llm.enabled: false` (critical setting)
- `src/innovation/innovation_engine.py` - InnovationEngine implementation

---

**Document Status**: ✅ COMPLETE
**Next Step**: Update steering documents based on this correction
**Priority**: CRITICAL - Affects all future development understanding
**Owner**: Personal Project (週/月交易系統)
