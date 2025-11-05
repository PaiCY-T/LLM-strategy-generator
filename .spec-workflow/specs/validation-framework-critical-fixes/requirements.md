# Validation Framework Critical Fixes - Requirements

**Created**: 2025-11-01
**Priority**: P0 CRITICAL - BLOCKING Phase 3
**Trigger**: Critical reassessment revealed validation framework still broken

---

## Introduction

After completing Task 7.2 (validation framework repair) and making a Phase 3 GO decision, a critical reassessment using `mcp__zen__challenge` revealed that the validation framework is still fundamentally broken. This spec addresses the critical issues that must be fixed before Phase 3 can proceed.

**Key Problems**:
1. Bonferroni threshold logic uses 0.8 (dynamic_threshold) instead of calculated 0.5
2. Strategies 9 and 13 are duplicates (only variable naming differs)
3. Only 3 unique validated strategies (15%), not 4 (20%)
4. No diversity analysis performed
5. Bonferroni correction not actually being applied

**Key Solution**: Fix the threshold logic bug, remove duplicates, verify data quality, and make an informed Phase 3 GO/NO-GO decision based on accurate validation results.

---

## Alignment with Product Vision

This spec directly supports the Phase 2 goal of "確認能正常產出策略,再來要求品質" (confirm can produce strategies reliably, then demand quality). Without correct validation, we cannot confidently assess strategy quality or make informed Phase 3 decisions.

**Risk of Not Fixing**:
- 70% chance Phase 3 learning system fails to generalize (insufficient unique examples)
- 50% chance Phase 3 needs restart after validation fix
- Biased training data from duplicate strategies

---

## Requirements

### REQ-1: Fix Bonferroni Threshold Logic Bug

**User Story**: As a quant developer, I want the validation framework to use the correct Bonferroni threshold (0.5), so that statistical significance testing accurately identifies strategies that pass the corrected alpha threshold.

#### Problem Statement

The validation framework currently uses `dynamic_threshold` (0.8) instead of the calculated `bonferroni_threshold` (0.5) when determining statistical significance. This means:
- Bonferroni correction is NOT being applied
- Strategies with Sharpe 0.5-0.8 incorrectly show `statistically_significant: false`
- Only testing dynamic threshold, not statistical significance

**Evidence**:
```
Strategy 3  (Sharpe 0.753): statistically_significant = false (should be true)
Strategy 6  (Sharpe 0.756): statistically_significant = false (should be true)
Strategy 10 (Sharpe 0.784): statistically_significant = false (should be true)
Strategy 14 (Sharpe 0.796): statistically_significant = false (should be true)
```

All strategies with Sharpe between 0.5-0.8 fail statistical significance test, proving the logic uses 0.8 threshold instead of 0.5.

#### Acceptance Criteria

1. WHEN validation calculates Bonferroni threshold THEN system SHALL correctly compute `max(0.5, z_score/sqrt(252))` WHERE z_score = norm.ppf(1 - adjusted_alpha/2)

2. WHEN validation logic checks statistical significance THEN system SHALL use `bonferroni_threshold` (0.5) AND NOT `dynamic_threshold` (0.8)

3. WHEN strategy has Sharpe ratio between 0.5 and 0.8 THEN system SHALL set `statistically_significant: true` AND `beats_dynamic_threshold: false`

4. WHEN validation outputs results THEN JSON SHALL contain separate fields `bonferroni_threshold: 0.5` AND `dynamic_threshold: 0.8` with correct values

5. WHEN all 20 strategies re-validated THEN approximately 18 strategies SHALL show `statistically_significant: true` (Sharpe > 0.5) AND 4 strategies SHALL show `validation_passed: true` (Sharpe > 0.8)

---

### REQ-2: Identify and Remove Duplicate Strategies

**User Story**: As a quant developer, I want to detect and remove duplicate strategies, so that the learning system trains on unique, diverse examples rather than biased duplicate data.

#### Problem Statement

Strategies 9 and 13 have **identical** Sharpe ratios (0.9443348034803672) and functionally identical code:
- Only difference: variable naming (`oversold_indicator` vs `oversold_signal`)
- Same logic, same backtest results
- Duplicate contaminating validation statistics (20% → 15% actual rate)

**Impact**:
- Only 3 unique validated strategies, not 4
- Learning system will see duplicate "successes", biasing training
- Insufficient diversity for robust Phase 3 learning

#### Acceptance Criteria

1. WHEN system analyzes all 20 strategies THEN SHALL identify all strategy pairs with identical Sharpe ratios (tolerance 1e-8)

2. WHEN two strategies have identical Sharpe THEN system SHALL perform code similarity analysis using AST comparison with variable name normalization

3. WHEN code similarity > 95% THEN system SHALL flag as duplicate AND mark lower-index strategy to KEEP and higher-index to REMOVE

4. WHEN duplicate detection completes THEN system SHALL generate report with:
   - List of all duplicate groups
   - Code diff for each duplicate pair
   - Recommendation (keep/remove) for each strategy

5. WHEN duplicates removed from validation results THEN system SHALL recalculate statistics:
   - Total validated strategies (unique count)
   - Validation rate (unique/total * 100%)
   - Updated list of validated strategies

---

### REQ-3: Verify Data Quality and Diversity

**User Story**: As a quant developer, I want to verify that validated strategies are sufficiently diverse, so that Phase 3 learning system can generalize effectively rather than overfit to narrow patterns.

#### Problem Statement

No diversity analysis was performed before Phase 3 GO decision. With only 3 unique validated strategies, need to assess:
- Factor diversity (which FinLab factors used?)
- Logic diversity (entry/exit conditions, position sizing)
- Return correlation (are strategies highly correlated?)
- Risk profile diversity (drawdown, volatility spread)

**Industry Standard**: Minimum 5-10 unique, diverse strategies for robust ML training.

#### Acceptance Criteria

1. WHEN system analyzes validated strategies THEN SHALL extract factor usage from each strategy code (data.get() calls) AND calculate Jaccard similarity matrix

2. WHEN system calculates diversity metrics THEN SHALL compute:
   - Factor diversity score (unique factors / total factors)
   - Return correlation matrix (pairwise correlations)
   - Average correlation (mean of all pairs)
   - Risk profile diversity (CV of max drawdowns)

3. IF average return correlation > 0.8 THEN system SHALL flag "HIGH CORRELATION WARNING" AND recommend generating more strategies

4. IF factor diversity score < 0.5 THEN system SHALL flag "LOW FACTOR DIVERSITY" AND recommend broader factor exploration

5. WHEN diversity analysis completes THEN system SHALL generate report with:
   - Factor usage heatmap
   - Correlation matrix visualization
   - Diversity score (0-100 scale)
   - Recommendation: SUFFICIENT / MARGINAL / INSUFFICIENT for Phase 3

---

### REQ-4: Re-run Full Validation with Fixed Framework

**User Story**: As a quant developer, I want to re-validate all 20 strategies with the corrected framework, so that Phase 3 GO/NO-GO decision is based on accurate validation statistics.

#### Acceptance Criteria

1. WHEN validation framework fixes are complete THEN system SHALL re-execute all 20 strategies with corrected threshold logic

2. WHEN re-validation executes THEN system SHALL maintain 100% execution success rate (20/20 strategies complete)

3. WHEN re-validation completes THEN results JSON SHALL contain:
   - `bonferroni_threshold: 0.5` (correct value)
   - `dynamic_threshold: 0.8` (unchanged)
   - `statistically_significant` count approximately 18 (90%)
   - `validation_passed` count 3-4 unique strategies
   - Execution time < 350 seconds total (17.5s/strategy average)

4. WHEN comparing before/after results THEN system SHALL generate comparison report showing:
   - Threshold values (before: 0.8, after: 0.5)
   - Statistical significance counts (before: 4, after: ~18)
   - Validation pass counts (before: 4, after: 3 unique)
   - Duplicate identification results

5. WHEN re-validation produces results THEN system SHALL NOT proceed to Phase 3 decision UNTIL duplicate removal and diversity analysis are complete

---

### REQ-5: Make Informed Phase 3 GO/NO-GO Decision

**User Story**: As a product manager, I want an evidence-based Phase 3 GO/NO-GO decision using corrected validation statistics, so that we proceed with confidence or address blockers before Phase 3.

#### Decision Framework

**GO Criteria** (all must be true):
- Validation framework correctly applies Bonferroni correction (threshold = 0.5)
- Minimum 3 unique validated strategies with Sharpe > 0.8
- Diversity score >= 60/100 (sufficient variety)
- No high-correlation clusters (avg correlation < 0.8)
- Execution framework stable (100% success rate maintained)

**CONDITIONAL GO Criteria** (with risk mitigation):
- 3 unique validated strategies (minimum acceptable)
- Diversity score 40-60/100 (marginal variety)
- Parallel strategy generation to increase diversity
- Aggressive Phase 3 monitoring for overfitting

**NO-GO Criteria** (any true):
- Less than 3 unique validated strategies
- Diversity score < 40/100
- Validation framework still broken
- Average correlation > 0.8 (strategies too similar)

#### Acceptance Criteria

1. WHEN validation fixes complete AND duplicate removal complete AND diversity analysis complete THEN system SHALL evaluate all GO criteria

2. WHEN all GO criteria met THEN system SHALL generate GO decision document with:
   - Validation statistics summary
   - Diversity analysis results
   - Risk assessment: LOW
   - Recommendation: PROCEED to Phase 3 Task 2.1

3. WHEN CONDITIONAL GO criteria met THEN system SHALL generate CONDITIONAL GO document with:
   - Identified gaps (e.g., marginal diversity)
   - Mitigation strategies (e.g., parallel strategy generation)
   - Risk assessment: MEDIUM
   - Monitoring plan for Phase 3

4. WHEN NO-GO criteria met THEN system SHALL generate NO-GO document with:
   - Blocking issues list
   - Required remediation actions
   - Estimated time to readiness
   - Alternative approaches

5. WHEN decision document generated THEN system SHALL NOT proceed to Phase 3 implementation UNTIL user explicitly approves the decision

---

## Non-Functional Requirements

### Code Architecture and Modularity

- **Single Responsibility**: Threshold calculation, duplicate detection, diversity analysis, and decision logic SHALL be separate modules
- **Modular Design**: Each component (threshold fix, duplicate detection, diversity analysis) SHALL be independently testable
- **Dependency Management**: Minimize changes to existing code; focus on bug fixes and new analysis tools
- **Clear Interfaces**: Validation results format SHALL remain backward compatible (add fields, don't remove)

### Performance

- **Re-validation Execution**: Total time < 350 seconds (17.5s/strategy average) for 20 strategies
- **Duplicate Detection**: Pairwise comparison < 30 seconds for 20 strategies (O(n²) acceptable for small n)
- **Diversity Analysis**: Factor extraction and correlation calculation < 60 seconds
- **Overall**: Complete workflow (fix + re-validate + analyze + decide) < 10 minutes

### Reliability

- **Threshold Calculation**: Unit tests SHALL verify correct calculation for N=1,5,10,20,50 strategies
- **Edge Case Handling**: System SHALL gracefully handle strategies with NaN Sharpe, zero trades, or missing data
- **Validation Errors**: Failures in diversity analysis SHALL NOT block threshold fix or re-validation
- **Rollback Plan**: Preserve original validation results JSON for comparison

### Security

- **Code Injection**: Duplicate detection SHALL NOT execute strategy code (parse AST only)
- **File Access**: Analysis tools SHALL only read from designated strategy directories
- **Data Validation**: Input validation on Sharpe ratios, correlation values, diversity scores

### Usability

- **Clear Reporting**: All reports SHALL use plain language explaining technical findings
- **Actionable Recommendations**: Decision documents SHALL include specific next steps
- **Traceability**: All analyses SHALL reference source data (which strategies, which metrics)
- **Visualization**: Diversity analysis SHALL include charts (correlation matrix, factor heatmap)

---

## Dependencies

**Required Completions**:
- Task 7.2 validation framework repair (COMPLETE - but has bugs to fix)
- 20-strategy validation dataset (COMPLETE)
- Execution framework (COMPLETE - 100% success rate)

**Existing Infrastructure**:
- `run_phase2_with_validation.py` (needs threshold logic fix)
- `src/validation/integration.py` (BonferroniIntegrator - needs bug fix)
- `phase2_validated_results_20251101_060315.json` (baseline for comparison)

**New Tools Required**:
- Duplicate detection script (AST-based code similarity)
- Diversity analysis script (factor extraction, correlation calculation)
- Decision framework script (evaluate GO criteria)

---

## Out of Scope

- Generating additional strategies (focus on fixing validation of existing 20)
- Implementing p-value-based validation (threshold-based is acceptable if correct)
- Creating new validation frameworks (fix existing implementation)
- Phase 3 implementation (blocked until GO decision)
- UI/dashboard for validation results (use existing JSON + markdown reports)

---

## Success Criteria

**Spec Complete When**:
1. ✅ Bonferroni threshold logic uses correct value (0.5)
2. ✅ Duplicate strategies identified and removed from statistics
3. ✅ Diversity analysis performed on unique validated strategies
4. ✅ Re-validation executed with corrected framework
5. ✅ Phase 3 GO/NO-GO decision made based on evidence

**Quality Gates**:
- Validation framework correctly identifies ~18 strategies as statistically significant (Sharpe > 0.5)
- Validation framework correctly identifies 3-4 unique strategies as passing both thresholds
- Diversity score calculated and assessed (target: >= 60/100 for GO)
- No regressions in execution framework (maintain 100% success rate)
- Decision document includes clear rationale and next steps

**User Acceptance**:
- User reviews and approves the corrected validation statistics
- User reviews and approves the diversity analysis findings
- User reviews and approves the Phase 3 GO/NO-GO decision
- User understands risk profile of proceeding (if CONDITIONAL GO)

---

## Timeline Estimate

**Total Time**: 8-12 hours (1-1.5 days)

**Breakdown**:
- REQ-1 (Threshold Fix): 2-3 hours (investigate, fix, verify)
- REQ-2 (Duplicate Detection): 1-2 hours (implement, run, report)
- REQ-3 (Diversity Analysis): 1-2 hours (implement, analyze, visualize)
- REQ-4 (Re-validation): 1-2 hours (execute, compare, document)
- REQ-5 (Decision): 1 hour (evaluate criteria, generate decision doc)
- Testing & Documentation: 2-3 hours (unit tests, integration tests, reports)

**Critical Path**: REQ-1 → REQ-4 → REQ-5 (threshold fix blocks re-validation blocks decision)
**Parallel Work**: REQ-2 and REQ-3 can execute in parallel with REQ-1

---

## Risk Assessment

**HIGH Risk**: Proceeding to Phase 3 without these fixes
- 70% chance learning system fails to generalize
- 50% chance Phase 3 needs restart after validation fix
- Biased training data from duplicates

**MEDIUM Risk**: Threshold fix introduces regressions
- Mitigation: Comprehensive unit tests before deployment
- Mitigation: Compare before/after results for sanity check

**LOW Risk**: Insufficient unique strategies after duplicate removal
- Current: 3 unique validated strategies
- Minimum acceptable: 3 strategies
- Ideal: 5-10 strategies
- Mitigation: CONDITIONAL GO with parallel strategy generation if only 3

---

## References

- `CRITICAL_REASSESSMENT_PHASE3_GO.md` - Detailed analysis of issues
- `TASK_7.2_FINAL_COMPLETION_REPORT.md` - Original (flawed) GO decision
- `phase2_validated_results_20251101_060315.json` - Current validation results
- `PILOT_TEST_VALIDATION_REPAIR_SUCCESS.md` - Pilot test results
- `VALIDATION_FRAMEWORK_FINDINGS.md` - Root cause analysis from Task 7.2
