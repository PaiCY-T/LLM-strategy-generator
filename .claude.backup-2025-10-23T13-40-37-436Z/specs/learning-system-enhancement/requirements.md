# Requirements Document: Learning System Enhancement

## Introduction

The autonomous trading strategy generation loop currently operates as a "random strategy generator" with a 33% success rate and unpredictable performance regression (Sharpe 0.97 → -0.35 between iterations). This feature transforms the system into an **intelligent learning system** through:

1. **Champion Tracking**: Persistence of best-performing strategies across iterations
2. **Performance Attribution**: Automated analysis identifying success factors and failure patterns
3. **Evolutionary Prompts**: LLM constraints that preserve proven elements while enabling incremental improvements

**Value Proposition**: Increase success rate from 33% to >60%, achieve consistent Sharpe ratio >1.2 by iteration 10, and eliminate >10% performance regressions after establishing a champion strategy.

## Alignment with Product Vision

This feature aligns with the core system goal of **autonomous strategy optimization** by enabling the system to:
- **Learn from success**: Identify and preserve high-performing patterns (ROE smoothing, strict liquidity filters)
- **Avoid regression**: Prevent removal of critical success factors
- **Systematic improvement**: Replace random exploration with guided evolution based on attribution analysis
- **Efficiency**: Achieve better performance in fewer iterations (5-7 vs unpredictable random walk)

## Requirements

### Requirement 1: Champion Strategy Tracking

**User Story:** As the autonomous loop system, I want to track the best-performing strategy generated so far, so that I can preserve successful patterns and prevent regression in future iterations.

#### Acceptance Criteria

1. WHEN a strategy is executed successfully AND its Sharpe ratio is >0.5 AND no champion exists THEN the system SHALL designate it as the champion
2. WHEN a strategy achieves Sharpe ratio ≥5% better than current champion (new_sharpe >= champion_sharpe * 1.05) THEN the system SHALL update the champion to the new strategy
3. WHEN champion is updated THEN the system SHALL persist champion data (code, parameters, metrics, iteration number, timestamp) to JSON file
4. WHEN autonomous loop initializes THEN the system SHALL load champion from JSON file if it exists
5. WHEN champion exists THEN the system SHALL make champion data available for comparison in subsequent iterations

**Data Requirements:**
- Champion code (full Python strategy)
- Extracted parameters (8 key parameters via regex: ROE smoothing, liquidity threshold, revenue handling, etc.)
- Performance metrics (sharpe_ratio, total_return, max_drawdown, etc.)
- Success patterns (descriptive list of proven elements)
- Iteration metadata (iteration_num, timestamp)

### Requirement 2: Performance Attribution Analysis

**User Story:** As the autonomous loop system, I want to compare each new strategy against the champion and identify critical changes, so that I can understand why performance improved or degraded.

#### Acceptance Criteria

1. WHEN a strategy completes execution AND champion exists THEN the system SHALL extract strategy parameters using regex-based attributor
2. WHEN strategy parameters are extracted THEN the system SHALL compare current parameters against champion parameters
3. WHEN parameter comparison completes THEN the system SHALL classify each change as critical (ROE, liquidity), moderate (revenue, value factor), or low (price, volume filters)
4. WHEN performance changes >0.1 Sharpe THEN the system SHALL assess as improved/degraded/similar
5. WHEN critical changes coincide with degradation THEN the system SHALL generate learning directives linking changes to performance impact

**Attribution Output Format:**
```
📊 DETECTED CHANGES (N total):
🔥 CRITICAL CHANGES:
  • liquidity_threshold: 100_000_000 → 50_000_000
  • roe_smoothing: smoothed (window=4) → raw (window=1)

💡 ATTRIBUTION INSIGHTS:
⚠️ Performance degraded after critical changes:
  • Removing ROE smoothing likely increased noise
  • Relaxing liquidity filter likely reduced quality

🎯 LEARNING DIRECTIVE:
  → Review iteration X's successful patterns
  → Preserve proven elements: ROE smoothing, strict filters
```

### Requirement 3: Enhanced Feedback Generation

**User Story:** As the autonomous loop system, I want to provide the LLM with structured attribution feedback instead of simple "Low Sharpe" messages, so that the LLM can learn from past iterations systematically.

#### Acceptance Criteria

1. WHEN iteration completes AND champion exists THEN the system SHALL generate attribution feedback including champion reference
2. WHEN attribution feedback is generated THEN it SHALL include: comparison summary, detected changes (categorized by impact), attribution insights, champion success patterns
3. WHEN no champion exists (iteration 0) THEN the system SHALL use simple feedback as fallback
4. WHEN attribution feedback is complete THEN the system SHALL format it for LLM consumption with clear sections and actionable directives

**Feedback Components:**
- Performance summary (previous Sharpe, current Sharpe, delta)
- Detected changes with impact classification
- Attribution insights linking changes to outcomes
- Champion context (iteration number, Sharpe ratio, success patterns)
- Learning directives for next iteration

### Requirement 4: Evolutionary Prompt Engineering

**User Story:** As the autonomous loop system, I want to constrain the LLM to preserve successful strategy elements while exploring improvements, so that the system builds upon success rather than randomly regenerating strategies.

#### Acceptance Criteria

1. WHEN generating prompt for iteration >=3 AND champion exists THEN the system SHALL include champion preservation constraints
2. WHEN preservation constraints are added THEN they SHALL specify mandatory elements to preserve (e.g., "roe.rolling(window=4).mean()", "liquidity > 100_000_000")
3. WHEN prompt includes constraints THEN it SHALL have 4 distinct sections: Champion Context, Mandatory Preservation, Failure Avoidance, Exploration Focus
4. WHEN iteration is multiple of 5 THEN the system SHALL force exploration mode (disable preservation constraints) to prevent local optima
5. WHEN exploration mode is forced THEN the system SHALL log diversity forcing activation

**Prompt Structure:**
```
LEARNING FROM SUCCESS
CURRENT CHAMPION: Iteration X, Sharpe Y

MANDATORY REQUIREMENTS:
1. PRESERVE these proven success factors:
   1. roe.rolling(window=4).mean() - 4-quarter smoothing reduces noise
   2. liquidity_filter > 100_000_000 - strict filter selects stable stocks

2. Make ONLY INCREMENTAL improvements
   - Adjust weights/thresholds by ±10-20%
   - Add complementary factors WITHOUT removing proven ones

AVOID (from failed iterations):
   - Removing data smoothing (increases noise)
   - Relaxing liquidity filters (reduces stability)

EXPLORE these improvements (while preserving above):
   - Fine-tune factor weights
   - Add quality filters (debt ratio, margin stability)
```

### Requirement 5: Success Pattern Extraction

**User Story:** As the autonomous loop system, I want to automatically extract success patterns from high-performing strategies, so that I can generate preservation directives for future iterations.

#### Acceptance Criteria

1. WHEN strategy achieves Sharpe >0.8 THEN the system SHALL extract success patterns from parameters
2. WHEN extracting patterns THEN the system SHALL prioritize critical patterns (ROE smoothing, liquidity filters) over moderate/low impact patterns
3. WHEN patterns are extracted THEN each SHALL include: parameter name, value, impact description, code snippet to preserve
4. WHEN champion is updated THEN success patterns SHALL be stored with champion data
5. WHEN multiple patterns exist THEN they SHALL be sorted by criticality (critical > moderate > low)

**Pattern Examples:**
- "ROE 4-quarter rolling average (noise reduction)"
- "Strict liquidity filter (≥100,000,000 TWD)"
- "Forward-filled revenue data (simple and effective)"

## Non-Functional Requirements

### Performance
- Attribution analysis SHALL complete in <100ms to avoid iteration slowdown
- Champion persistence (save/load) SHALL complete in <50ms
- Pattern extraction SHALL process within 200ms for typical strategy code
- Overall enhancement overhead SHALL be <500ms per iteration

### Reliability
- Champion persistence SHALL survive system crashes and restarts
- JSON serialization SHALL handle all Python data types in parameters
- Regex parameter extraction SHALL achieve >90% successful extraction rate on critical parameters (ROE, liquidity) across test strategies, with fallback to simple feedback when extraction fails
- Champion JSON schema SHALL be validated on load with proper error handling
- System SHALL gracefully handle missing or corrupted champion JSON file (log error and proceed with None champion)

### Security
- Champion JSON SHALL be stored in project directory (no external dependencies)
- Parameter extraction SHALL not execute arbitrary code
- Attribution feedback SHALL not expose sensitive system internals to LLM

### Maintainability
- Code SHALL follow existing project patterns (JSON persistence like IterationHistory)
- Attribution logic SHALL be isolated in performance_attributor.py (Phase 1 complete)
- Champion tracking SHALL integrate into autonomous_loop.py with minimal changes to existing flow
- Future AST migration SHALL be feasible by replacing regex extraction module

### Testing
- Unit test coverage SHALL be >80% for new code
- Test data SHALL include historical strategies for regression testing
- Each edge case SHALL have corresponding test scenario

### Data Integrity
- Champion JSON schema SHALL be validated on load with jsonschema or equivalent validation
- Parameter extraction SHALL validate extracted values against expected types/ranges
- Performance metrics SHALL be validated for numerical sanity (e.g., -10 < Sharpe < 10)
- System SHALL reject champion data with missing critical fields (code, sharpe_ratio, iteration_num)
- Champion tracking SHALL have 10 unit tests covering update logic, persistence, edge cases
- Attribution integration SHALL have 8 unit tests for comparison logic, first iteration handling
- Evolutionary prompts SHALL have 7 unit tests for pattern extraction, prompt structure
- Integration tests SHALL validate 5 end-to-end scenarios (success case, regression prevention, first iteration, champion update cascade, premature convergence)
- 10-iteration validation run SHALL achieve 3/4 success criteria (Sharpe >1.2, success rate >60%, avg Sharpe >0.5, no regression >10%)

## Edge Cases and Constraints

### Edge Cases
1. **No successful iterations**: If no strategy achieves Sharpe >0.5, champion remains None
2. **Threshold boundary**: If new_sharpe >= champion_sharpe * 1.05 (including equality), update champion
3. **Negative Sharpe champion**: System SHALL update champion even if Sharpe is negative (if it's ≥5% better than previous negative)
4. **Corrupted champion file**: System SHALL log error and proceed with None champion (fresh start)
5. **Regex extraction failure**: System SHALL use simple feedback fallback for that iteration

### Constraints
- **Regex limitations**: Parameter extraction is MVP-quality (80/20 solution); AST migration planned for v2.0
- **LLM compliance risk**: No guarantee LLM will follow preservation directives; diversity forcing every 5th iteration mitigates
- **Backward compatibility**: Existing autonomous_loop.py behavior (simple feedback) SHALL remain when champion is None
- **Manual intervention**: No user-facing UI; system operates fully autonomously

## Success Criteria

A successful implementation SHALL demonstrate:

1. **Technical Validation** (Unit + Integration Tests)
   - ✓ All 25 unit tests passing (10 champion + 8 attribution + 7 evolutionary)
   - ✓ All 5 integration scenarios passing
   - ✓ Code coverage >80%

2. **Functional Validation** (10-iteration run)
   - ✓ Champion tracking functional across iterations
   - ✓ Attribution feedback generated correctly
   - ✓ Evolutionary prompts include preservation constraints
   - ✓ Pattern extraction identifies critical success factors

3. **Performance Validation** (Success Criteria - need 3/4 to pass)
   - ✓ Best Sharpe after 10 iterations: >1.2 (baseline: 0.97)
   - ✓ Successful iterations: >60% (baseline: 33%)
   - ✓ Average Sharpe: >0.5 (baseline: 0.33)
   - ✓ No regression >10% after establishing champion

4. **Quality Validation**
   - ✓ Attribution accuracy: >90% detection of critical parameter changes
   - ✓ Regression prevention: <10% degradation in champion patterns preserved

## Dependencies and Risks

### Dependencies
- **Phase 1 (Complete)**: `performance_attributor.py` with extract_strategy_params(), compare_strategies(), generate_attribution_feedback(), extract_success_patterns()
- **Existing Modules**: autonomous_loop.py, prompt_builder.py, history.py (no changes needed for compatibility)
- **Python Standard Library**: json, dataclasses, datetime, re, typing

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|---------|-----------|
| LLM ignores preservation directives | Medium | High | Test prompt effectiveness; add stronger constraints; diversity forcing |
| Regex parsing fails on unexpected code | Medium | Medium | Comprehensive test coverage; Phase 1 validation; future AST migration |
| Over-preservation stifles exploration | Medium | High | Diversity forcing every 5th iteration; incremental improvement guidelines |
| Attribution misidentifies critical changes | Low | High | Extensive testing with historical data; manual validation |
| Performance impact from attribution overhead | Low | Low | Profiling shows <100ms overhead; negligible vs 30-120s generation time |

## Validation Strategy

### Unit Testing
- Champion tracking: 10 tests (initialization, update threshold, persistence, edge cases)
- Attribution integration: 8 tests (comparison logic, first iteration, regression detection)
- Evolutionary prompts: 7 tests (pattern extraction, prompt structure, exploration mode)

### Integration Testing
- Scenario 1: Full learning loop (success case)
- Scenario 2: Regression prevention
- Scenario 3: First iteration edge case
- Scenario 4: Champion update cascade
- Scenario 5: Premature convergence (diversity forcing)

### Validation Run
- 10-iteration test with real finlab data
- Metrics tracking across all iterations
- Success criteria evaluation (3/4 must pass)
- Comparison vs baseline performance

---

**Document Version**: 1.0
**Status**: Ready for Design Phase
**Confidence**: HIGH (90%) - Phase 1 validates approach
