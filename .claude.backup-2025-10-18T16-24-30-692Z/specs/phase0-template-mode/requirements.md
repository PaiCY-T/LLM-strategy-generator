# Phase 0: Template-Guided Generation - Requirements

**Spec Version**: 1.0
**Created**: 2025-10-17
**Status**: Planning

---

## 📋 Overview

### Purpose
Test hypothesis that template-guided parameter generation can improve champion update rate from 0.5% to ≥5% without complex population-based learning.

### Background
**Current System Issues**:
- Champion update rate: 0.5% (1 update per 200 iterations)
- LLM free-form code generation produces 99.5% strategies worse than champion
- High variance (1.001) and no statistical significance (p=0.1857)

**O3's Hypothesis**:
- Root cause is **generation quality**, not search algorithm
- Template structure + domain knowledge prompts → 10x improvement
- Can avoid expensive population-based learning (80-100 hours)

**Test Approach**:
- Use existing `MomentumTemplate` (8-parameter PARAM_GRID, 10,240 combinations)
- LLM selects parameter combinations instead of generating free-form code
- Add pre-backtest validation gates
- Run 50-iteration test to measure improvement

---

## 🎯 Functional Requirements

### R1: Template Parameter Generator
**Description**: LLM-guided parameter selection from MomentumTemplate.PARAM_GRID

**R1.1: Parameter Space Definition**
- **Requirement**: Expose MomentumTemplate.PARAM_GRID to LLM
- **Details**: 8 parameters with discrete value choices:
  - `momentum_period`: [5, 10, 20, 30] days
  - `ma_periods`: [20, 60, 90, 120] days
  - `catalyst_type`: ['revenue', 'earnings']
  - `catalyst_lookback`: [2, 3, 4, 6] months
  - `n_stocks`: [5, 10, 15, 20] stocks
  - `stop_loss`: [0.08, 0.10, 0.12, 0.15] ratio
  - `resample`: ['W', 'M'] frequency
  - `resample_offset`: [0, 1, 2, 3, 4] days
- **Validation**: Total combinations = 4×4×2×4×4×4×2×5 = 10,240
- **Success Criteria**: Generator produces valid parameter dict with all 8 keys

**R1.2: LLM Prompt Construction**
- **Requirement**: Build prompt with champion context and domain knowledge
- **Prompt Structure**:
  1. Parameter grid with explanations (what each value means)
  2. Champion parameters (if exists) and performance
  3. Previous iteration feedback
  4. Trading domain knowledge (Taiwan market, Finlab data, risk management)
  5. JSON output format specification
- **Validation**: Prompt contains all required sections
- **Success Criteria**: LLM returns valid JSON with parameter selection

**R1.3: Response Parsing**
- **Requirement**: Parse LLM response to extract parameter dictionary
- **Details**:
  - Extract JSON from LLM response (may contain explanatory text)
  - Validate all 8 required keys present
  - Validate all values match PARAM_GRID options
  - Provide clear error messages if parsing fails
- **Success Criteria**: 100% successful parsing of valid LLM responses

**R1.4: Champion-Aware Exploration**
- **Requirement**: Use champion parameters to guide intelligent exploration
- **Strategy**:
  - If no champion: Random exploration from PARAM_GRID
  - If champion exists: Suggest parameters "near" champion (±1 step in parameter space)
  - Every 5th iteration: Force exploration (ignore champion, try distant parameters)
- **Success Criteria**: Parameter diversity >30 unique combinations in 50 iterations

---

### R2: Domain Knowledge Prompt Enhancement
**Description**: Incorporate Finlab-specific trading knowledge into prompts

**R2.1: Dataset Catalog**
- **Requirement**: Provide LLM with Finlab dataset documentation
- **Coverage**:
  - Available datasets (price, fundamental, flow data)
  - Data quality characteristics (update frequency, reliability)
  - Common pitfalls (look-ahead bias, survivorship bias)
- **Success Criteria**: Prompt includes dataset reference guide

**R2.2: Proven Success Patterns**
- **Requirement**: Document patterns from successful strategies
- **Source**: Analyze `generated_strategy_loop_iter3.py` (Sharpe 2.37)
- **Patterns to Include**:
  - Multi-factor combination (momentum + quality + value)
  - Rank normalization (.rank(axis=1, pct=True))
  - Essential filters (liquidity, price, market cap)
  - Data smoothing (.rolling().mean() for fundamentals)
- **Success Criteria**: Prompt includes ≥5 proven patterns

**R2.3: Anti-Patterns**
- **Requirement**: Document common failure modes to avoid
- **Source**: Failure pattern analysis from previous iterations
- **Anti-Patterns**:
  - No liquidity filter → unstable execution
  - Un-smoothed fundamentals → noisy signals
  - Negative .shift() → look-ahead bias
  - Daily rebalancing → excessive costs
  - Too many factors (>5) → overfitting
- **Success Criteria**: Prompt includes ≥5 anti-patterns with explanations

**R2.4: Risk Management Guidelines**
- **Requirement**: Provide Taiwan market-specific risk management rules
- **Guidelines**:
  - Position sizing (5-20 stocks recommended)
  - Stop loss ranges (8-15% for momentum strategies)
  - Liquidity thresholds (>50M-100M TWD daily volume)
  - Rebalancing frequency (weekly-monthly for cost efficiency)
- **Success Criteria**: Prompt includes comprehensive risk management section

---

### R3: Strategy Validation Gates
**Description**: Pre-backtest validation to reject obviously flawed parameter combinations

**R3.1: Parameter Bounds Validation**
- **Requirement**: Verify all parameters within PARAM_GRID ranges
- **Checks**:
  - All 8 required keys present
  - Each value matches one option from PARAM_GRID
  - No extra/unknown parameters
- **Success Criteria**: 100% detection of invalid parameter combinations

**R3.2: Risk Management Validation**
- **Requirement**: Validate risk parameters against best practices
- **Checks**:
  - `stop_loss`: 0.05 ≤ value ≤ 0.20 (too tight or too loose is problematic)
  - `n_stocks`: 5 ≤ value ≤ 30 (avoid over-concentration or over-diversification)
  - `resample`: Not 'D' (daily rebalancing too expensive)
- **Success Criteria**: Reject strategies violating risk limits

**R3.3: Logical Consistency Validation**
- **Requirement**: Check parameter combinations make logical sense
- **Checks**:
  - Short momentum_period (5-10) should use shorter ma_periods (20-60)
  - Weekly rebalancing ('W') more suitable for shorter momentum windows
  - Longer catalyst_lookback (4-6) pairs with longer-term strategies
- **Warnings Only**: Flag suspicious combinations but don't reject
- **Success Criteria**: Validation warnings logged for review

**R3.4: Validation Reporting**
- **Requirement**: Clear error messages for validation failures
- **Output Format**:
  ```python
  (is_valid: bool, errors: List[str], warnings: List[str])
  ```
- **Success Criteria**: Each validation failure has actionable error message

---

### R4: Autonomous Loop Integration
**Description**: Integrate template mode into existing AutonomousLoop

**R4.1: Template Mode Flag**
- **Requirement**: Add `template_mode` configuration parameter
- **Behavior**:
  - `template_mode=False`: Original free-form LLM code generation
  - `template_mode=True`: Template-guided parameter generation
- **Success Criteria**: Both modes work without interfering with each other

**R4.2: Mode-Specific Workflow**
- **Requirement**: Route to correct generation workflow based on mode
- **Template Mode Workflow**:
  1. Generate parameters via TemplateParameterGenerator
  2. Validate parameters via StrategyValidator
  3. Generate strategy via MomentumTemplate.generate_strategy(params)
  4. Extract metrics and update champion
- **Free-Form Mode Workflow** (unchanged):
  1. Generate code via LLM
  2. Validate code via existing validators
  3. Execute code and extract metrics
  4. Update champion
- **Success Criteria**: Correct workflow executed based on mode

**R4.3: History Tracking**
- **Requirement**: Track parameter history separately from code history
- **Data Structure**:
  ```python
  {
    'iteration': int,
    'mode': 'template' | 'freeform',
    'parameters': Dict[str, Any],  # For template mode
    'code': str,  # For free-form mode
    'metrics': Dict[str, float],
    'validation_passed': bool,
    'template_name': str  # 'Momentum'
  }
  ```
- **Success Criteria**: Full history exportable for analysis

**R4.4: Champion Management**
- **Requirement**: Champion tracking works seamlessly across both modes
- **Champion Fields**:
  - `iteration_num`: int
  - `metrics`: Dict[str, float]
  - `parameters`: Dict[str, Any] (template mode) OR None
  - `code`: str (free-form mode) OR None
  - `mode`: 'template' | 'freeform'
- **Success Criteria**: Champion updates correctly regardless of mode

---

### R5: 50-Iteration Test Harness
**Description**: Automated test to evaluate Phase 0 hypothesis

**R5.1: Test Configuration**
- **Requirement**: Configurable test parameters
- **Configuration**:
  - `max_iterations`: 50
  - `template_mode`: True
  - `template_name`: "Momentum"
  - `model`: "gemini-2.5-flash"
  - `save_checkpoints`: True
  - `checkpoint_interval`: 10 iterations
- **Success Criteria**: Test runs to completion

**R5.2: Progress Monitoring**
- **Requirement**: Real-time progress updates during test
- **Metrics to Display**:
  - Current iteration number
  - Champion update count
  - Current champion Sharpe
  - Cumulative update rate
  - Estimated time remaining
- **Success Criteria**: Clear progress indicators throughout test

**R5.3: Checkpoint Management**
- **Requirement**: Save state every 10 iterations for recovery
- **Checkpoint Data**:
  - Current champion
  - Iteration history
  - Parameter diversity stats
  - Cumulative metrics
- **Success Criteria**: Test can resume from checkpoint after interruption

**R5.4: Error Handling**
- **Requirement**: Graceful handling of individual iteration failures
- **Strategy**:
  - Log error details
  - Mark iteration as failed
  - Continue to next iteration
  - Track failure rate
- **Success Criteria**: Test completes even if some iterations fail

---

### R6: Results Analysis Framework
**Description**: Comprehensive analysis to support Go/No-Go decision

**R6.1: Primary Metrics Calculation**
- **Requirement**: Calculate key decision metrics
- **Metrics**:
  - **Champion Update Rate**: (updates / total_iterations) × 100
  - **Average Sharpe**: Mean Sharpe across all successful strategies
  - **Best Sharpe**: Maximum Sharpe achieved
  - **Variance**: Variance of Sharpe across iterations
  - **Parameter Diversity**: Unique parameter combinations / total_iterations
- **Success Criteria**: All metrics calculated correctly

**R6.2: Comparison to Baseline**
- **Requirement**: Compare against free-form generation baseline
- **Baseline Metrics** (from 200-iteration test):
  - Champion update rate: 0.5%
  - Average Sharpe: 1.3728
  - Variance: 1.001
- **Improvement Calculation**:
  - Update rate improvement: (template_rate / 0.5) × 100
  - Variance improvement: (1.001 - template_variance) / 1.001 × 100
- **Success Criteria**: Clear improvement metrics vs baseline

**R6.3: Parameter Exploration Analysis**
- **Requirement**: Analyze which parameters were explored
- **Metrics**:
  - Unique combinations count
  - Most/least explored parameter values
  - Parameter correlation with success
  - Exploration vs exploitation balance
- **Success Criteria**: Insights into parameter space coverage

**R6.4: Validation Analysis**
- **Requirement**: Analyze validation gate effectiveness
- **Metrics**:
  - Validation pass rate
  - Common validation failures
  - Time saved by early rejection
- **Success Criteria**: Validation effectiveness quantified

**R6.5: Decision Matrix**
- **Requirement**: Automated decision recommendation
- **Decision Logic**:
  ```python
  if champion_update_rate >= 10% and avg_sharpe > 1.2:
      return "SUCCESS: Use template mode, skip population-based"
  elif champion_update_rate >= 5% and avg_sharpe > 1.0:
      return "PARTIAL: Template shows promise, consider hybrid"
  else:
      return "FAILURE: Proceed to Phase 1 (population-based)"
  ```
- **Success Criteria**: Clear, automated decision recommendation

---

## 🎯 Non-Functional Requirements

### NFR1: Performance
- **R-NFR1.1**: Parameter generation <5 seconds per iteration
- **R-NFR1.2**: Validation <1 second per strategy
- **R-NFR1.3**: 50-iteration test completes in <5 hours (average 6 min/iteration)

### NFR2: Reliability
- **R-NFR2.1**: Validation pass rate ≥90% (reject only truly bad strategies)
- **R-NFR2.2**: LLM response parsing success rate ≥95%
- **R-NFR2.3**: Checkpoint recovery 100% successful

### NFR3: Maintainability
- **R-NFR3.1**: Modular design (TemplateParameterGenerator, StrategyValidator separate)
- **R-NFR3.2**: Comprehensive logging (all decisions, validations, metrics)
- **R-NFR3.3**: Clear error messages for debugging

### NFR4: Compatibility
- **R-NFR4.1**: Works with existing MomentumTemplate without modification
- **R-NFR4.2**: Compatible with both Gemini and OpenRouter APIs
- **R-NFR4.3**: Template mode and free-form mode coexist without conflict

---

## ✅ Success Criteria

### Primary Success Criteria (Must Meet All)
1. ✅ **Champion Update Rate**: ≥5% (10x improvement from 0.5% baseline)
2. ✅ **Test Completion**: 50 iterations complete successfully
3. ✅ **Parameter Diversity**: ≥30 unique parameter combinations explored
4. ✅ **Validation Pass Rate**: ≥90%

### Secondary Success Criteria (Nice to Have)
1. ⭐ **Average Sharpe**: >1.0 (vs baseline 1.3728)
2. ⭐ **Variance Reduction**: <0.8 (vs baseline 1.001)
3. ⭐ **Best Sharpe**: >2.0 (match or exceed historical best)
4. ⭐ **Execution Time**: <4 hours for 50 iterations

### Failure Criteria (Any Triggers Failure)
1. ❌ **Champion Update Rate**: <2% (less than 4x improvement)
2. ❌ **Parameter Convergence**: <20 unique combinations (insufficient exploration)
3. ❌ **Validation Failure Rate**: >20% (validation too strict or generator too poor)
4. ❌ **Test Incompletion**: Cannot complete 50 iterations due to errors

---

## 📊 Validation Plan

### Unit Testing
- **TemplateParameterGenerator**:
  - Test prompt construction with/without champion
  - Test LLM response parsing (valid/invalid JSON)
  - Test parameter validation against PARAM_GRID
  - Test exploration vs exploitation logic
- **StrategyValidator**:
  - Test parameter bounds validation
  - Test risk management validation
  - Test logical consistency checks
  - Test error message clarity
- **Coverage Target**: ≥80% for new components

### Integration Testing
- **Template Mode Workflow**:
  - Test end-to-end: parameter generation → validation → backtest → metrics
  - Test champion update logic
  - Test iteration history tracking
  - Test checkpoint save/restore
- **Coverage Target**: All critical paths tested

### System Testing
- **5-Iteration Smoke Test**:
  - Quick validation that template mode works
  - Expected: 0-1 champion updates (not enough iterations for statistics)
  - Duration: ~30 minutes
- **50-Iteration Full Test**:
  - Primary validation test for decision making
  - Expected: 2-5 champion updates if hypothesis holds
  - Duration: 2.5-5 hours

### Acceptance Testing
- **Baseline Comparison**:
  - Compare 50-iteration template mode to 50-iteration free-form mode
  - Metrics: champion update rate, average Sharpe, variance, diversity
- **Decision Validation**:
  - Verify decision matrix produces correct recommendation
  - Verify all analysis metrics calculated correctly

---

## 📈 Metrics & Measurement

### Key Performance Indicators (KPIs)

| Metric | Baseline | Target | Stretch Goal | Measurement |
|--------|----------|--------|--------------|-------------|
| Champion Update Rate | 0.5% | 5% | 10% | (updates / 50) × 100 |
| Average Sharpe | 1.37 | 1.0+ | 1.5+ | Mean of all strategies |
| Parameter Diversity | N/A | 30 | 40 | Unique combinations |
| Validation Pass Rate | N/A | 90% | 95% | Passed / total |
| Time per Iteration | 3-6 min | <6 min | <4 min | Average runtime |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| LLM Parsing Success | ≥95% | Valid JSON extractions / total |
| Validation Accuracy | ≥95% | True positives + true negatives / total |
| Code Coverage | ≥80% | Unit test coverage |
| Error Rate | <5% | Failed iterations / total |

---

## 🔄 Dependencies

### Internal Dependencies
- ✅ **MomentumTemplate**: Existing, functional
- ✅ **AutonomousLoop**: Existing, needs extension
- ✅ **Gemini API Integration**: Working (95.2% success rate)
- ✅ **Finlab Backtest**: Existing, functional

### External Dependencies
- ✅ **Gemini API**: Primary LLM (gemini-2.5-flash)
- ✅ **OpenRouter API**: Fallback LLM
- ✅ **Finlab Data API**: Strategy evaluation

### New Components Required
- ⏳ **TemplateParameterGenerator**: To be implemented
- ⏳ **StrategyValidator**: To be implemented
- ⏳ **Enhanced Prompt Template**: To be created
- ⏳ **50-Iteration Test Script**: To be created
- ⏳ **Analysis Framework**: To be implemented

---

## 📅 Timeline & Milestones

### Phase 0.1: Component Development (12 hours)
- **Milestone**: All new components implemented and unit tested
- **Deliverables**:
  - TemplateParameterGenerator (4h)
  - Enhanced prompt template with domain knowledge (3h)
  - StrategyValidator (3h)
  - Unit tests (2h)

### Phase 0.2: Integration (4 hours)
- **Milestone**: Template mode integrated into AutonomousLoop
- **Deliverables**:
  - Modified AutonomousLoop with template_mode support (3h)
  - 5-iteration smoke test (1h)

### Phase 0.3: Full Testing (4 hours + test time)
- **Milestone**: 50-iteration test completed and analyzed
- **Deliverables**:
  - 50-iteration test script (2h)
  - Test execution (2.5-5h)
  - Results analysis (2h)

### Total Duration: ~20 hours development + 5 hours testing = ~25 hours (~1 week)

---

## 🎯 Decision Framework

### Go/No-Go Criteria

**GO (Skip Population-based Learning)**:
- Champion update rate ≥5% AND
- Average Sharpe >1.0 AND
- Parameter diversity ≥30 combinations

**PARTIAL (Consider Hybrid)**:
- Champion update rate 2-5% OR
- Average Sharpe 0.8-1.0 OR
- Parameter diversity 20-30 combinations

**NO-GO (Proceed to Population-based)**:
- Champion update rate <2% OR
- Average Sharpe <0.8 OR
- Parameter diversity <20 combinations OR
- Any failure criteria met

---

**Document Version**: 1.0
**Last Updated**: 2025-10-17
**Next Review**: After 50-iteration test completion
