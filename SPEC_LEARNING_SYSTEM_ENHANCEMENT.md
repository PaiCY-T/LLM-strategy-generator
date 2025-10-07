# Learning System Enhancement Specification

**Project**: Autonomous Trading Strategy Learning Loop Enhancement
**Version**: 1.1 (Planning Complete)
**Date**: 2025-10-07
**Status**: Ready for Implementation
**Confidence**: HIGH (90%)

---

## Current Status Summary

### Completed Work
- ✅ **Phase 1**: Performance Attribution System (`performance_attributor.py`)
  - Regex-based parameter extraction (8 key parameters)
  - Strategy comparison and attribution feedback generation
  - Validated with real iteration data (correctly identified iteration 1 success factors and iteration 2 regression causes)

- ✅ **Specification Document**: Comprehensive 3-week implementation plan
  - Detailed breakdown of Phases 2-4
  - 21 specific actions with code examples
  - 25 unit tests + 5 integration scenarios defined
  - Success criteria and validation strategy documented

- ✅ **Planning**: 8-step detailed implementation plan via ZEN Planner
  - Week 1: Feedback Loop Integration (Champion Tracking, Attribution, Enhanced Feedback)
  - Week 2: Evolutionary Prompts (Pattern Extraction, Prompt Construction, Integration)
  - Week 3: Testing & Validation (25 unit tests, 5 integration tests, 10-iteration validation)

### Ready to Begin
- **Next Action**: Start Phase 2.1 (Champion Tracking Implementation)
- **Branch**: `feature/learning-system-enhancement`
- **First File**: `autonomous_loop.py` (add ChampionStrategy dataclass)
- **No Blockers**: All dependencies satisfied, clear implementation path

### Key Files Status
- `performance_attributor.py`: ✅ Complete and tested
- `test_attribution.py`: ✅ Validation passed
- `autonomous_loop.py`: 📝 Requires modification (Phase 2)
- `prompt_builder.py`: 📝 Requires modification (Phase 2-3)
- `SPEC_LEARNING_SYSTEM_ENHANCEMENT.md`: ✅ This document (updated with detailed plan)

---

## Executive Summary

The autonomous learning loop successfully generates high-performing trading strategies (Sharpe 0.97 in iteration 1), but fails to learn from success. This specification outlines a systematic enhancement to transform the system from a "random strategy generator" to an "intelligent learning system" through performance attribution and evolutionary prompting.

**Core Problem**: System generated Sharpe 0.97 (iteration 1) but regressed to -0.35 (iteration 2) because it removed critical success factors (ROE smoothing, strict liquidity filters).

**Solution**: 3-phase enhancement adding champion tracking, performance attribution feedback, and evolutionary prompts with pattern preservation constraints.

---

## Problem Statement

### Current System Behavior

| Iteration | Sharpe Ratio | Status |
|-----------|--------------|--------|
| 0 | 0.36 | Baseline |
| 1 | 0.97 | **Success** |
| 2 | -0.35 | **Regression** |

### Root Cause Analysis

**Proven Capability**: System CAN generate excellent strategies (iteration 1)
**Critical Gap**: System CANNOT learn from success or avoid regression

**Evidence**:
1. Iteration 1 succeeded due to:
   - ROE 4-quarter rolling average (noise reduction)
   - Strict 100M liquidity filter (quality stocks)
   - Forward-filled revenue data

2. Iteration 2 failed because it:
   - Removed ROE smoothing → raw quarterly data (noisy)
   - Relaxed liquidity to 50M → less stable stocks
   - Changed revenue handling → data alignment issues

3. No feedback mechanism to preserve successful patterns

### Impact

- **Wasted iterations**: System cannot build on success
- **Performance volatility**: No protection against regression
- **Learning inefficiency**: Random walk instead of guided improvement

---

## Success Criteria

### Primary Goals

1. **Monotonic Improvement**: Sharpe ratio should not regress >10% after a successful iteration
2. **Pattern Preservation**: Proven elements (ROE smoothing, strict filters) maintained across iterations
3. **Attribution Quality**: System correctly identifies why strategies succeed/fail
4. **Learning Efficiency**: Achieve consistent Sharpe >1.0 by iteration 5-7 (vs random in current system)

### Validation Metrics

- **Technical**:
  - Attribution accuracy: >90% detection of critical parameter changes
  - Regression prevention: <10% degradation in champion patterns

- **Performance**:
  - Best Sharpe after 10 iterations: >1.2 (baseline: 0.97)
  - Successful iterations: >60% (baseline: 33%)
  - Average Sharpe: >0.5 (baseline: 0.33)

---

## Solution Architecture

### Phase 1: Performance Attribution System ✅ COMPLETED

**Status**: Implemented and validated

**Components**:
- `performance_attributor.py`: Regex-based parameter extraction
- Extracts 8 key parameters: ROE smoothing, liquidity threshold, revenue handling, etc.
- Generates structured attribution feedback with impact analysis

**Validation Results**:
- ✅ Correctly identified iteration 1 success factors
- ✅ Correctly attributed iteration 2 regression causes
- ✅ Generated actionable learning directives

### Phase 2: Feedback Loop Integration (THIS SPEC)

**Objective**: Integrate attribution into the autonomous learning loop

**Components**:

#### 2.1 Champion Tracking System
- Track best-performing strategy ("champion")
- Store: code, parameters, metrics, iteration number
- Update when new strategy beats champion by >5%

#### 2.2 Attribution Integration
- Compare current strategy vs champion after each iteration
- Generate structured diff highlighting critical changes
- Identify: improvements, regressions, neutral changes

#### 2.3 Enhanced Feedback Generation
- Replace simple "Low Sharpe" messages with attribution analysis
- Include: what changed, performance impact, learning directives
- Format for LLM consumption

**File Modifications**:
```
autonomous_loop.py:
  - Add champion tracking state
  - Integrate performance_attributor in Step 5 (Build feedback)
  - Store champion strategy for comparison

prompt_builder.py:
  - Add build_attributed_feedback() method
  - Include champion preservation directives
  - Format structured feedback for LLM
```

### Phase 3: Evolutionary Prompt Engineering

**Objective**: Constrain LLM to preserve successful patterns

**Prompt Enhancements**:

1. **Champion Context**:
   ```
   PREVIOUS BEST ITERATION: {champion_num}
   Achieved Sharpe: {champion_sharpe}

   SUCCESS FACTORS:
   - {success_pattern_1}
   - {success_pattern_2}
   - {success_pattern_3}
   ```

2. **Mandatory Constraints**:
   ```
   REQUIREMENTS:
   1. PRESERVE these proven elements:
      - roe.rolling(window=4).mean()
      - liquidity_filter > 100_000_000

   2. Make ONLY incremental improvements

   3. Explain changes in code comments
   ```

3. **Failure Avoidance**:
   ```
   AVOID (from failed iterations):
   - Removing ROE smoothing
   - Relaxing liquidity filters
   - Over-complicated calculations
   ```

**File Modifications**:
```
prompt_builder.py:
  - Add build_evolutionary_prompt() method
  - Extract success patterns from champion code
  - Generate preservation constraints
  - Include failure pattern warnings
```

### Phase 4: Evolution Manager (Future)

**Objective**: Balance exploitation vs exploration

**Strategy**:
- Iterations 1-3: Explore (diverse approaches)
- After finding Sharpe >1.0: Exploit (refine champion)
- Every 5th iteration: Explore (prevent local optima)

**Deferred to v2.0**

---

## Technical Design

### Data Structures

#### ChampionStrategy
```python
@dataclass
class ChampionStrategy:
    iteration_num: int
    code: str
    parameters: Dict[str, Any]  # From performance_attributor
    metrics: Dict[str, float]
    success_patterns: List[str]
    timestamp: str
```

#### AttributionResult
```python
@dataclass
class AttributionResult:
    changes: List[Dict]           # All detected changes
    critical_changes: List[Dict]  # High-impact changes
    performance_delta: float      # Sharpe difference
    assessment: str               # 'improved'|'degraded'|'similar'
    learning_directives: List[str]
```

### Integration Points

#### autonomous_loop.py Changes

**New State**:
```python
class AutonomousLoop:
    def __init__(self, ...):
        self.champion: Optional[ChampionStrategy] = None
```

**Modified run_iteration()**:
```python
def run_iteration(self, iteration_num, data):
    # ... existing steps 1-4 ...

    # Step 5: Enhanced feedback with attribution
    if self.champion:
        attribution = self._compare_with_champion(code, metrics)
        feedback = self.prompt_builder.build_attributed_feedback(
            attribution,
            iteration_num,
            self.champion
        )
    else:
        feedback = self.prompt_builder.build_simple_feedback(metrics)

    # Step 6: Update champion if improved
    if metrics['sharpe_ratio'] > self.champion.metrics['sharpe_ratio'] * 1.05:
        self._update_champion(iteration_num, code, metrics)
```

#### prompt_builder.py Changes

**New Methods**:
```python
def build_attributed_feedback(
    self,
    attribution: AttributionResult,
    iteration_num: int,
    champion: ChampionStrategy
) -> str:
    """Generate feedback with performance attribution."""

def extract_success_patterns(
    self,
    champion_code: str,
    champion_params: Dict
) -> List[str]:
    """Extract preservation directives from champion."""

def build_evolutionary_prompt(
    self,
    iteration_num: int,
    champion: ChampionStrategy,
    feedback_summary: str
) -> str:
    """Build prompt with champion preservation constraints."""
```

---

## Detailed Implementation Plan

### Overview

```
PHASE 1: Performance Attribution [COMPLETED]
   |
   v
PHASE 2: Feedback Loop Integration [Week 1]
   |
   +-- Champion Tracking (Days 1-2)
   +-- Attribution Integration (Days 3-4)
   +-- Enhanced Feedback (Day 5)
   |
   v
PHASE 3: Evolutionary Prompts [Week 2]
   |
   +-- Pattern Extraction (Days 1-2)
   +-- Prompt Construction (Days 3-4)
   +-- Full Integration (Day 5)
   |
   v
PHASE 4: Testing & Validation [Week 3]
   |
   +-- Unit Tests (Days 1-2): 25 tests
   +-- Integration Tests (Day 3): 5 scenarios
   +-- Validation Run (Day 4): 10-iteration test
   +-- Documentation (Day 5): Polish & deploy
```

### Week 1: Phase 2 - Feedback Loop Integration

#### Day 1-2: Champion Tracking Foundation

**Goal**: Track best-performing strategy as baseline for comparison

**Action 1**: Create ChampionStrategy dataclass (30 min)
```python
@dataclass
class ChampionStrategy:
    iteration_num: int
    code: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    success_patterns: List[str]
    timestamp: str

    def to_dict(self) -> Dict
    @staticmethod
    def from_dict(data: Dict) -> 'ChampionStrategy'
```

**Action 2**: Modify `__init__()` method (20 min)
- Initialize `self.champion = None`
- Add `_load_champion()` call for persistence

**Action 3**: Implement `_update_champion()` method (1 hour)
- Compare current Sharpe vs champion Sharpe * 1.05 (5% threshold)
- Extract parameters using `extract_strategy_params()`
- Extract success patterns using `extract_success_patterns()`
- Update champion if threshold met
- Log champion updates

**Action 4**: Add persistence methods (30 min)
- `_save_champion()`: Serialize to JSON
- `_load_champion()`: Load on initialization

**Action 5**: Unit tests (3 hours)
- Create `tests/test_champion_tracking.py`
- 10 unit tests covering update logic, persistence, edge cases

**Deliverables**:
- [ ] Champion tracking functional
- [ ] 10 unit tests passing
- [ ] Champion persists across sessions

#### Day 3-4: Attribution Integration

**Goal**: Connect attribution analysis to feedback loop

**Action 6**: Implement `_compare_with_champion()` (1 hour)
```python
def _compare_with_champion(
    self,
    current_code: str,
    current_metrics: Dict[str, float]
) -> Dict[str, Any]:
    """Compare current strategy with champion."""
    if not self.champion:
        return None

    curr_params = extract_strategy_params(current_code)
    return compare_strategies(
        prev_params=self.champion.parameters,
        curr_params=curr_params,
        prev_metrics=self.champion.metrics,
        curr_metrics=current_metrics
    )
```

**Action 7**: Enhance `run_iteration()` Step 5 (45 min)
```python
# Step 5: Enhanced feedback with attribution
if self.champion:
    attribution = self._compare_with_champion(code, metrics)
    feedback = self.prompt_builder.build_attributed_feedback(
        attribution, iteration_num, self.champion
    )
else:
    feedback = self.prompt_builder.build_simple_feedback(metrics)

# Step 5.5: Update champion
champion_updated = self._update_champion(iteration_num, code, metrics)
```

**Action 8**: Unit tests (4 hours)
- Create `tests/test_attribution_integration.py`
- 8 unit tests for comparison logic, first iteration handling, edge cases

**Deliverables**:
- [ ] Attribution integrated into loop
- [ ] 8 unit tests passing
- [ ] First iteration handled correctly

#### Day 5: Enhanced Feedback Generation

**Goal**: Generate actionable feedback for LLM

**Action 9**: Create `build_attributed_feedback()` (2 hours)
```python
def build_attributed_feedback(
    self,
    attribution: Dict[str, Any],
    iteration_num: int,
    champion: ChampionStrategy
) -> str:
    """Generate feedback with performance attribution."""
    feedback = generate_attribution_feedback(
        attribution, iteration_num, champion.iteration_num
    )

    # Add champion context
    feedback += f"\n\nCURRENT CHAMPION: Iteration {champion.iteration_num}\n"
    feedback += f"Champion Sharpe: {champion.metrics['sharpe_ratio']:.4f}\n"
    feedback += "\nSUCCESS PATTERNS TO PRESERVE:\n"
    for pattern in champion.success_patterns:
        feedback += f"  - {pattern}\n"

    return feedback
```

**Action 10**: Add `build_simple_feedback()` (30 min)
- Fallback for first iteration (no champion)
- Provide basic guidance

**Action 11**: Testing (2 hours)
- Test feedback generation with real attribution results
- Verify format suitable for LLM consumption

**Deliverables**:
- [ ] Attributed feedback working
- [ ] Simple feedback fallback working
- [ ] Feedback format validated

### Week 2: Phase 3 - Evolutionary Prompts

#### Day 1-2: Success Pattern Extraction

**Goal**: Extract preservation directives from champion code

**Action 12**: Implement `extract_success_patterns()` (2 hours)
```python
def extract_success_patterns(
    self,
    champion_code: str,
    champion_params: Dict[str, Any]
) -> List[str]:
    """Extract preservation directives from champion strategy."""
    patterns = []

    # Pattern 1: ROE smoothing
    if champion_params['roe_type'] == 'smoothed':
        window = champion_params['roe_smoothing_window']
        patterns.append(
            f"PRESERVE: roe.rolling(window={window}).mean() - "
            f"Reduces quarterly noise with {window}-quarter average"
        )

    # Pattern 2: Liquidity threshold
    if champion_params['liquidity_threshold']:
        threshold = champion_params['liquidity_threshold']
        patterns.append(
            f"PRESERVE: liquidity_filter > {threshold:,} TWD - "
            f"Selects stable, high-volume stocks"
        )

    # ... extract other patterns ...

    return patterns
```

**Action 13**: Add pattern prioritization (30 min)
- Sort patterns by criticality (critical > moderate > low)
- Critical: ROE smoothing, liquidity filters
- Moderate: Revenue handling, price filters

**Action 14**: Unit tests (4 hours)
- Create `tests/test_evolutionary_prompts.py`
- Test pattern extraction from iteration 1 code
- Verify all key patterns detected

**Deliverables**:
- [ ] Pattern extraction working
- [ ] Validated with iteration 1 code
- [ ] Prioritization logic functional

#### Day 3-4: Evolutionary Prompt Construction

**Goal**: Build prompts that preserve successful patterns

**Action 15**: Implement `build_evolutionary_prompt()` (3 hours)
```python
def build_evolutionary_prompt(
    self,
    iteration_num: int,
    champion: ChampionStrategy,
    feedback_summary: str,
    base_prompt: str
) -> str:
    """Build prompt with champion preservation constraints."""

    # Exploration mode (iter 0-2) vs exploitation mode (iter 3+)
    if iteration_num < 3 or champion is None:
        return base_prompt

    sections = []

    # Section A: Champion Context
    sections.append("LEARNING FROM SUCCESS")
    sections.append(f"CURRENT CHAMPION: Iteration {champion.iteration_num}")
    sections.append(f"Champion Sharpe: {champion.metrics['sharpe_ratio']:.4f}")

    # Section B: Mandatory Preservation Constraints
    sections.append("\nMANDATORY REQUIREMENTS:")
    sections.append("1. PRESERVE these proven success factors:")
    patterns = self._prioritize_patterns(champion.success_patterns)
    for i, pattern in enumerate(patterns, 1):
        sections.append(f"   {i}. {pattern}")

    sections.append("\n2. Make ONLY INCREMENTAL improvements")
    sections.append("   - Adjust weights/thresholds by ±10-20%")
    sections.append("   - Add complementary factors WITHOUT removing proven ones")

    # Section C: Failure Pattern Avoidance
    if iteration_num > 3:
        sections.append("\nAVOID (from failed iterations):")
        sections.append("   - Removing data smoothing (increases noise)")
        sections.append("   - Relaxing liquidity filters (reduces stability)")

    # Section D: Improvement Focus Areas
    sections.append("\nEXPLORE these improvements (while preserving above):")
    sections.append("   - Fine-tune factor weights")
    sections.append("   - Add quality filters (debt ratio, margin stability)")

    return "\n".join(sections) + "\n\n" + base_prompt
```

**Action 16**: Integrate into prompt building (1 hour)
- Modify `build_prompt()` to call evolutionary prompt builder
- Apply constraints for iterations 3+

**Action 17**: Add diversity forcing (45 min)
```python
def should_force_exploration(self, iteration_num: int) -> bool:
    """Every 5th iteration: force exploration to prevent local optima."""
    return iteration_num > 0 and iteration_num % 5 == 0
```

**Action 18**: Unit tests (4 hours)
- 7 unit tests for evolutionary prompts
- Verify 4-section structure
- Test exploration vs exploitation modes

**Deliverables**:
- [ ] Evolutionary prompts generating correctly
- [ ] 7 unit tests passing
- [ ] Diversity forcing functional

#### Day 5: End-to-End Integration

**Goal**: Full system integration with validation

**Action 19**: Update `autonomous_loop.py` (1 hour)
```python
def run_iteration(self, iteration_num: int, data):
    # Step 1: Build enhanced prompt
    force_exploration = self.prompt_builder.should_force_exploration(iteration_num)

    champion_for_prompt = None if force_exploration else self.champion

    prompt = self.prompt_builder.build_prompt(
        iteration_num, previous_feedback, champion=champion_for_prompt
    )
    # ... rest of workflow ...
```

**Action 20**: Create integration test script (2 hours)
- `test_full_learning_loop.py`
- Test complete 5-iteration workflow
- Verify champion tracking, attribution, preservation

**Action 21**: Manual validation (2 hours)
- Run test script with historical data
- Verify no regression >10%
- Document any issues

**Deliverables**:
- [ ] Full system integrated
- [ ] 5-iteration test passing
- [ ] No severe regression detected

### Week 3: Phase 4 - Testing & Validation

#### Day 1-2: Comprehensive Unit Testing

**Goal**: Complete 25 unit tests across all components

**Day 1 Morning**: Champion tracking tests (10 tests)
- Champion initializes as None
- Updates when Sharpe improves >5%
- Doesn't update when improvement <5%
- Persists to/from JSON correctly
- Handles negative Sharpe
- First good strategy becomes champion

**Day 1 Afternoon**: Attribution integration tests (8 tests)
- Detects critical changes (ROE, liquidity)
- First iteration uses simple feedback
- Regression triggers learning directive
- Improvement reinforces patterns
- Handles identical strategies

**Day 2**: Evolutionary prompt tests (7 tests)
- Extracts patterns from iteration 1 code
- ROE smoothing window=4 preserved
- Liquidity 100M threshold preserved
- 4-section prompt structure present
- Exploration mode (iter 0-2) vs exploitation (iter 3+)
- Diversity forcing works

**Deliverables**:
- [ ] All 25 unit tests passing
- [ ] Code coverage >80%

#### Day 3: Integration Testing

**Goal**: Test 5 comprehensive end-to-end scenarios

**Scenario 1**: Full Learning Loop (Success Case)
- Iteration 0: No champion
- Iteration 1: Sharpe 0.97 → becomes champion
- Iteration 3: LLM preserves ROE + liquidity
- Expected: No >10% regression

**Scenario 2**: Regression Prevention
- Champion at Sharpe 0.97
- LLM attempts to remove ROE smoothing
- Constraints prevent change OR feedback identifies issue

**Scenario 3**: First Iteration Edge Case
- No champion, exploration mode
- Simple feedback only

**Scenario 4**: Champion Update Cascade
- Champion updates when better strategy found
- New champion becomes comparison baseline

**Scenario 5**: Premature Convergence
- All iterations preserve exact patterns
- Diversity forcing triggers

**Deliverables**:
- [ ] All 5 integration scenarios passing
- [ ] Edge cases handled correctly

#### Day 4: 10-Iteration Validation Run

**Goal**: Validate against success criteria

**Validation Script**: `run_10iteration_validation.py`
```python
def run_validation_test():
    """Run 10-iteration validation against success criteria."""

    loop = AutonomousLoop(model='google/gemini-2.5-flash', max_iterations=10)

    sharpes = []
    for i in range(10):
        success, feedback = loop.run_iteration(i, data)
        metrics = loop.history.get_metrics(i)
        sharpes.append(metrics['sharpe_ratio'])

    # Validate success criteria
    best_sharpe = max(sharpes)
    success_rate = sum(1 for s in sharpes if s > 0.5) / len(sharpes)
    avg_sharpe = sum(sharpes) / len(sharpes)

    # Check regression
    if loop.champion:
        champion_idx = loop.champion.iteration_num
        post_champion = sharpes[champion_idx+1:]
        regression = (min(post_champion) - loop.champion.metrics['sharpe_ratio'])
                    / loop.champion.metrics['sharpe_ratio']

    # Report results
    print(f"1. Best Sharpe >1.2: {best_sharpe:.4f} {'PASS' if best_sharpe > 1.2 else 'FAIL'}")
    print(f"2. Success rate >60%: {success_rate:.1%} {'PASS' if success_rate > 0.6 else 'FAIL'}")
    print(f"3. Average Sharpe >0.5: {avg_sharpe:.4f} {'PASS' if avg_sharpe > 0.5 else 'FAIL'}")
    print(f"4. No regression >10%: {regression:.1%} {'PASS' if regression > -0.10 else 'FAIL'}")
```

**Success Criteria** (need 3/4):
1. Best Sharpe after 10 iterations: >1.2 (baseline: 0.97)
2. Successful iterations: >60% (baseline: 33%)
3. Average Sharpe: >0.5 (baseline: 0.33)
4. No regression >10% after establishing champion

**Deliverables**:
- [ ] Validation report with metrics
- [ ] Comparison: baseline vs enhanced
- [ ] 3/4 success criteria met minimum

#### Day 5: Documentation & Final Review

**Goal**: Production-ready system with complete documentation

**Documentation Updates**:
1. **README.md** (1 hour)
   - Add "Learning System Enhancement" section
   - Explain champion tracking, attribution, evolutionary prompts
   - Usage examples and quick start guide

2. **ARCHITECTURE.md** (1 hour)
   - Document new components: ChampionStrategy, attribution flow
   - Update workflow diagrams
   - Explain Phase 2 & 3 architecture

3. **API_REFERENCE.md** (30 min)
   - Document new methods:
     * `_update_champion()`
     * `_compare_with_champion()`
     * `build_attributed_feedback()`
     * `build_evolutionary_prompt()`

4. **TESTING.md** (30 min)
   - Document test suite structure
   - How to run unit tests, integration tests, validation
   - Success criteria explanation

**Final Code Review** (2 hours):
- Review all modified files for quality
- Check for code smells, potential bugs
- Verify error handling and edge cases
- Ensure consistent code style

**Bug Fixes & Polish** (3 hours):
- Fix any issues discovered during validation
- Performance optimization if needed
- Add helpful logging and error messages

**Deliverables**:
- [ ] Documentation complete and updated
- [ ] Code review passed
- [ ] All bugs fixed
- [ ] System ready for deployment

### Implementation Summary

**Files to Modify**:

Week 1:
- `autonomous_loop.py`: Champion tracking, attribution integration
- `prompt_builder.py`: Enhanced feedback generation
- `tests/test_champion_tracking.py`: New
- `tests/test_attribution_integration.py`: New

Week 2:
- `prompt_builder.py`: Pattern extraction, evolutionary prompts
- `autonomous_loop.py`: Integrate evolutionary prompts
- `tests/test_evolutionary_prompts.py`: New
- `test_full_learning_loop.py`: New

Week 3:
- All test files: Complete 25 unit tests
- `run_10iteration_validation.py`: New
- `README.md`, `ARCHITECTURE.md`, `API_REFERENCE.md`, `TESTING.md`: Updates

**Code Volume Estimate**:
- Production code: ~800 lines
- Test code: ~1200 lines
- Documentation: ~500 lines
- **Total**: ~2500 lines

**First Implementation Session**:
```bash
# 1. Create feature branch
git checkout -b feature/learning-system-enhancement

# 2. Start with champion tracking (Phase 2.1)
# Modify: autonomous_loop.py
# - Add ChampionStrategy dataclass
# - Add champion state to __init__
# - Implement _update_champion()
# - Add persistence methods

# 3. Create initial tests
# Create: tests/test_champion_tracking.py
# - Implement 10 unit tests

# 4. Run tests
pytest tests/test_champion_tracking.py -v

# 5. Commit progress
git add autonomous_loop.py tests/test_champion_tracking.py
git commit -m "feat: Add champion tracking system (Phase 2.1)"
```

---

## Testing Strategy

### Unit Tests

**performance_attributor.py**:
- [x] extract_strategy_params() with various code patterns
- [x] compare_strategies() with improvement/degradation scenarios
- [x] generate_attribution_feedback() output format

**autonomous_loop.py**:
- [ ] Champion update logic (threshold, better performance)
- [ ] Attribution integration in run_iteration()
- [ ] First iteration handling (no champion)

**prompt_builder.py**:
- [ ] build_attributed_feedback() with various attribution results
- [ ] extract_success_patterns() with champion code
- [ ] build_evolutionary_prompt() constraint generation

### Integration Tests

**End-to-End Learning**:
- [ ] 10-iteration run captures attribution feedback
- [ ] Champion updates correctly when performance improves
- [ ] Prompts include preservation directives after finding champion
- [ ] No regression >10% after establishing champion

### Validation Tests

**Comparison with Baseline**:
- [ ] Run current system (10 iterations) - baseline metrics
- [ ] Run enhanced system (10 iterations) - new metrics
- [ ] Compare: best Sharpe, success rate, regression frequency

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|-----------|
| Regex parsing fails on unexpected code | Medium | Medium | Add fallback to simple feedback; plan AST migration |
| Over-preservation stifles exploration | Medium | High | Add diversity forcing every Nth iteration (Phase 4) |
| Attribution misidentifies critical changes | Low | High | Extensive testing with historical data; manual validation |
| LLM ignores preservation directives | Medium | High | Test prompt effectiveness; add stronger constraints |

### Performance Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|-----------|
| No improvement over baseline | Low | High | Validate attribution logic before full integration |
| Local optima (stuck at Sharpe ~1.0) | Medium | Medium | Phase 4: Evolution manager with explore mode |
| Slower iteration time due to analysis | Low | Low | Attribution is fast (<100ms); negligible impact |

---

## Success Validation

### Acceptance Criteria

**Phase 2 (Feedback Integration)**:
- [x] Attribution system implemented and tested
- [ ] Champion tracking functional
- [ ] Feedback includes structured attribution
- [ ] Test run shows attribution in iteration logs

**Phase 3 (Evolutionary Prompts)**:
- [ ] Prompts include champion context
- [ ] Preservation directives present when champion exists
- [ ] Failure patterns included in prompts
- [ ] LLM generates code preserving key elements

**System-Level Validation**:
- [ ] 10-iteration test: best Sharpe >1.2
- [ ] 10-iteration test: success rate >60%
- [ ] No regression >10% after iteration 3
- [ ] Attribution feedback actionable and accurate

---

## Future Enhancements (v2.0)

### Phase 4: Evolution Manager
- Exploit/explore mode switching
- Diversity tracking and forcing
- Multi-objective optimization

### Phase 5: Advanced Attribution
- Migrate from regex to AST parsing
- Factor interaction analysis
- Incremental value attribution

### Phase 6: Meta-Learning
- Learn which preservation strategies work
- Adapt constraint strength based on results
- Transfer learning across market regimes

### Phase 7: Knowledge Graph Integration (Hybrid Approach)
- **Objective**: Enhance long-term knowledge retention and reasoning
- **Approach**: Hybrid JSON + Graphiti MCP Server

**Immediate Access Layer (JSON)**:
- `champion_strategy.json`: Current best strategy
- `mvp_final_clean_history.json`: Recent iteration history
- Response time: <100ms
- Use case: Real-time iteration feedback

**Deep Knowledge Layer (Graphiti MCP Server)**:
- Knowledge graph of strategy patterns
- Cross-iteration relationships and causality
- Market regime adaptation patterns
- Response time: 1-5 seconds
- Use case: Strategic analysis, pattern discovery

**Integration Architecture**:
```python
class HybridKnowledgeManager:
    def __init__(self):
        self.json_cache = JSONCache()      # Fast access
        self.graphiti = GraphitiMCP()      # Deep reasoning

    def get_champion(self) -> ChampionStrategy:
        """Fast: Load from JSON cache."""
        return self.json_cache.load_champion()

    def sync_to_graph(self, iteration_data):
        """Async: Sync to knowledge graph after iteration."""
        self.graphiti.add_node('strategy', iteration_data)
        self.graphiti.add_relations(attribution_results)

    def query_patterns(self, query: str):
        """Deep: Query knowledge graph for insights."""
        return self.graphiti.query(query)
```

**Knowledge Graph Schema**:
```
Nodes:
- Strategy (iteration_num, code, metrics)
- Parameter (name, value, type)
- Pattern (description, success_rate)
- MarketRegime (period, characteristics)

Edges:
- USED (Strategy -> Parameter)
- CAUSED (Parameter -> Performance)
- SUCCEEDED_BY (Strategy -> Strategy)
- EFFECTIVE_IN (Pattern -> MarketRegime)
- LEARNED_FROM (Strategy -> Pattern)
```

**Sync Strategy**:
1. **Real-time**: JSON for current iteration
2. **Post-iteration**: Async sync to Graphiti (non-blocking)
3. **Daily**: Batch analysis and pattern extraction
4. **On-demand**: Deep queries for strategy insights

**Benefits**:
- Fast iteration performance (JSON)
- Long-term knowledge accumulation (Graphiti)
- Cross-session learning and pattern transfer
- Market regime adaptation insights

**Implementation Timeline**: Phase 7 (v2.0) after Phase 2-3 completion

---

## Dependencies

### Existing Components
- `performance_attributor.py` ✅ (completed)
- `autonomous_loop.py` (requires modification)
- `prompt_builder.py` (requires modification)
- `history.py` (no changes needed)
- `validate_code.py` (no changes needed)
- `sandbox_simple.py` (no changes needed)

### External Dependencies

**Phase 2-3 (Current)**:
- No new packages required
- Uses existing: regex, typing, dataclasses, json, datetime

**Phase 7 (Future - Graphiti Integration)**:
- Graphiti MCP Server (knowledge graph management)
- Installation: Via MCP server configuration
- Optional dependency: System works without Graphiti

---

## Rollout Strategy

### Development Environment
1. Implement Phase 2 in development branch
2. Test with historical iteration data
3. Run 3-iteration smoke test

### Staging Environment
1. Run 10-iteration validation test
2. Compare metrics vs baseline
3. Fix any critical issues

### Production Deployment
1. Merge to main branch
2. Run live 10-iteration test with real data
3. Monitor attribution quality
4. Iterate based on findings

---

## Appendix

### A. Iteration 1 Success Analysis

**Code Characteristics**:
```python
# Critical Success Factors
roe_avg = roe.rolling(window=4, min_periods=1).mean().ffill().shift(1)
revenue_yoy_daily = revenue_yoy.ffill().shift(1)
liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000

# Factor Combination
combined_factor = (momentum * 0.4 + revenue_yoy_daily * 0.3 +
                  roe_avg * 0.2 + inverse_pe * 0.1)
```

**Performance**:
- Sharpe: 0.97
- Annual Return: 31.85%
- Win Rate: 69.51%
- Max Drawdown: -46.11%

### B. Attribution System Output Example

```
============================================================
PERFORMANCE ATTRIBUTION - Iteration 2
============================================================

❌ REGRESSION: Sharpe ratio degraded
  Previous: 0.9700
  Current:  -0.3500
  Delta:    -1.3200

📊 DETECTED CHANGES (4 total):

🔥 CRITICAL CHANGES (High Impact):
  • liquidity_threshold:
      From: 100000000
      To:   50000000
  • roe_smoothing:
      From: smoothed (window=4)
      To:   raw (window=1)

💡 ATTRIBUTION INSIGHTS:

⚠️  Performance degraded after critical changes:
  • Relaxing liquidity filter likely reduced quality
    → Higher threshold (100000000) selects more stable stocks
  • Removing ROE smoothing likely increased noise
    → 4-quarter rolling average provides stable signal

🎯 LEARNING DIRECTIVE:
  → Review iteration 1's successful patterns
  → Preserve proven elements: ROE smoothing, strict filters
  → Make INCREMENTAL improvements, not revolutionary changes
============================================================
```

### C. References

- Original MVP implementation: `autonomous_loop.py`
- Attribution system: `performance_attributor.py`
- Test validation: `test_attribution.py`
- Historical results: `mvp_final_clean_history.json`

---

**Document Status**: Planning Complete - Ready for Implementation
**Version**: 1.1 (Updated with detailed implementation plan)
**Planning Date**: 2025-10-07
**Confidence Level**: HIGH (90%)

---

## Quick Reference Guide

### For Implementation Start (重開機後快速啟動)

**1. Context Recovery**:
```bash
# Navigate to project
cd /mnt/c/Users/jnpi/Documents/finlab

# Check current status
git status
ls -la *.py *.json

# Review completed work
cat performance_attributor.py  # Phase 1: DONE
cat test_attribution.py        # Validation: PASSED
```

**2. Start Implementation**:
```bash
# Create feature branch
git checkout -b feature/learning-system-enhancement

# Start with Phase 2.1: Champion Tracking
# Edit: autonomous_loop.py
# - Add ChampionStrategy dataclass (line ~10)
# - Add self.champion = None in __init__
# - Implement _update_champion() method
# - Add _save_champion() and _load_champion()

# Create tests
# Create: tests/test_champion_tracking.py
# Implement 10 unit tests

# Run tests
pytest tests/test_champion_tracking.py -v
```

**3. Key Implementation Files** (in order):
- Week 1: `autonomous_loop.py`, `prompt_builder.py`
- Week 2: `prompt_builder.py` (evolutionary prompts)
- Week 3: Test files, validation scripts

**4. Success Criteria Reminder**:
- Best Sharpe after 10 iterations: >1.2
- Successful iterations: >60%
- Average Sharpe: >0.5
- No regression >10% after champion
- Need 3/4 criteria to pass

### Critical Code Snippets (Copy-Paste Ready)

**ChampionStrategy Dataclass**:
```python
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass
class ChampionStrategy:
    iteration_num: int
    code: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    success_patterns: List[str]
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'ChampionStrategy':
        return ChampionStrategy(**data)
```

**Import Performance Attributor**:
```python
from performance_attributor import (
    extract_strategy_params,
    compare_strategies,
    extract_success_patterns,
    generate_attribution_feedback
)
```

### Knowledge Persistence (Mixed Approach)

**Current Phase (2-3)**: JSON-based (Fast)
```python
# Save champion
with open('champion_strategy.json', 'w') as f:
    json.dump(champion.to_dict(), f, indent=2)

# Load champion
with open('champion_strategy.json', 'r') as f:
    data = json.load(f)
    champion = ChampionStrategy.from_dict(data)
```

**Future Phase (7)**: Graphiti Integration (Deep Analysis)
```python
# Async sync to knowledge graph (non-blocking)
hybrid_manager.sync_to_graph(iteration_data)

# Deep queries
patterns = hybrid_manager.query_patterns(
    "Find successful strategies with ROE smoothing"
)
```

### Testing Quick Commands

```bash
# Run specific test file
pytest tests/test_champion_tracking.py -v

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Run integration tests
python test_full_learning_loop.py

# Run validation
python run_10iteration_validation.py
```

### Debugging Tips

**Check Attribution System**:
```bash
python test_attribution.py
# Should show: Iteration 1 success factors, Iteration 2 regression causes
```

**Verify Champion Tracking**:
```python
loop = AutonomousLoop(...)
print(f"Champion: {loop.champion}")  # Should be None initially
# After iteration with Sharpe > 0.5
print(f"Champion: Iter {loop.champion.iteration_num}, Sharpe {loop.champion.metrics['sharpe_ratio']:.4f}")
```

**Check JSON Persistence**:
```bash
cat champion_strategy.json
# Should show: iteration_num, code, parameters, metrics, success_patterns, timestamp
```

### Implementation Checklist (重開機後確認)

- [ ] Phase 1 完成：`performance_attributor.py` 存在且測試通過
- [ ] 規格書已更新：`SPEC_LEARNING_SYSTEM_ENHANCEMENT.md` 包含詳細計劃
- [ ] 歷史數據存在：`generated_strategy_loop_iter0/1/2.py`, `mvp_final_clean_history.json`
- [ ] 測試腳本存在：`test_attribution.py` 可執行
- [ ] Git 狀態乾淨：無未提交的重要變更
- [ ] 環境就緒：Python packages, Finlab API token 已設定

### Next Session Workflow (下次啟動)

1. **Review**: 閱讀規格書 "Current Status Summary" 和 "Quick Reference Guide"
2. **Verify**: 執行 `python test_attribution.py` 確認 Phase 1 正常
3. **Branch**: 建立 `feature/learning-system-enhancement` 分支
4. **Implement**: 從 Phase 2.1 Action 1 開始（ChampionStrategy dataclass）
5. **Test**: 每個 action 完成後執行對應測試
6. **Commit**: 每個小階段完成後提交（參考規格書的 commit message 格式）

---

## End of Specification

**Total Pages**: ~50 (estimated)
**Total Actions**: 21 detailed implementation steps
**Total Tests**: 25 unit + 5 integration + 1 validation
**Estimated Code**: ~2500 lines (800 production + 1200 test + 500 docs)
**Timeline**: 3 weeks (15 working days)
**Confidence**: HIGH (90%) - Phase 1 validates the approach
