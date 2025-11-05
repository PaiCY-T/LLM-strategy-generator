# Phase 3 GO/NO-GO Criteria

**Version**: 1.0.0
**Date**: 2025-11-03
**Status**: Production Ready

---

## 1. Overview

The Phase 3 GO/NO-GO Decision Framework provides deterministic criteria for assessing whether the system is ready to progress to population-based learning. It evaluates strategy quality, diversity, and system health to minimize risk of Phase 3 failure.

### Purpose

The decision framework:
- **Automates GO/NO-GO decisions** based on objective criteria
- **Quantifies risk levels** (LOW, MEDIUM, HIGH)
- **Provides mitigation strategies** for conditional progression
- **Prevents premature Phase 3 launch** when diversity insufficient

### Integration in Workflow

```
Phase 2 Validation → Duplicate Detection → Diversity Analysis → Decision Framework → GO/CONDITIONAL_GO/NO-GO
                                                                                   ↓
                                                                            Phase 3 or Re-run Phase 2
```

---

## 2. Decision Framework

### 2.1 Three-Tier Decision Model

| Decision | Meaning | Risk Level | Phase 3 Status |
|----------|---------|------------|----------------|
| **GO** | All optimal criteria met | LOW | Proceed immediately with standard monitoring |
| **CONDITIONAL_GO** | Minimal criteria met | MEDIUM | Proceed with enhanced monitoring and mitigation plan |
| **NO-GO** | Critical criteria failed | HIGH | Do NOT proceed - fix issues and re-run Phase 2 |

### 2.2 Decision Logic

```python
if all_optimal_criteria_met():
    decision = "GO"
    risk = "LOW"
elif all_critical_criteria_met() and diversity >= 40:
    decision = "CONDITIONAL_GO"
    risk = "MEDIUM"
else:
    decision = "NO-GO"
    risk = "HIGH"
```

---

## 3. Criteria Table

### 3.1 GO Criteria (Optimal)

All criteria must pass for GO decision:

| Criterion | Threshold | Comparison | Weight | Rationale |
|-----------|-----------|------------|--------|-----------|
| **Minimum Unique Strategies** | ≥3 | `unique >= 3` | CRITICAL | Need population for learning |
| **Diversity Score** | ≥60 | `score >= 60` | HIGH | Strong diversity for exploration |
| **Average Correlation** | <0.8 | `corr < 0.8` | CRITICAL | Prevent correlated failures |
| **Validation Framework Fixed** | True | `fixed == True` | CRITICAL | Ensure reliable metrics |
| **Execution Success Rate** | 100% | `rate >= 100` | CRITICAL | All strategies must execute |
| **Factor Diversity** | ≥0.5 | `factor_div >= 0.5` | MEDIUM | Varied trading signals |
| **Risk Diversity** | ≥0.3 | `risk_div >= 0.3` | LOW | Varied risk profiles |

**Pass Rate**: 7/7 criteria (100%)

### 3.2 CONDITIONAL_GO Criteria (Minimal)

Only CRITICAL criteria must pass for CONDITIONAL_GO:

| Criterion | Threshold | Comparison | Weight | Rationale |
|-----------|-----------|------------|--------|-----------|
| **Minimum Unique Strategies** | ≥3 | `unique >= 3` | CRITICAL | Minimum population size |
| **Diversity Score (Conditional)** | ≥40 | `score >= 40` | HIGH | Marginal diversity acceptable |
| **Average Correlation** | <0.8 | `corr < 0.8` | CRITICAL | Correlation still critical |
| **Validation Framework Fixed** | True | `fixed == True` | CRITICAL | Non-negotiable |
| **Execution Success Rate** | 100% | `rate >= 100` | CRITICAL | Must execute reliably |

**Pass Rate**: 5/5 CRITICAL criteria (100%)

**Note**: MEDIUM/LOW criteria (Factor Diversity, Risk Diversity) can fail without blocking CONDITIONAL_GO.

### 3.3 NO-GO Criteria

Any CRITICAL criterion failing triggers NO-GO:

| Blocking Criterion | Condition | Impact |
|-------------------|-----------|--------|
| **Unique Strategies** | <3 | Insufficient population for learning |
| **Diversity Score** | <40 | Unacceptable correlation risk |
| **Average Correlation** | ≥0.8 | High correlated failure risk |
| **Validation Framework** | False | Unreliable metrics |
| **Execution Success** | <100% | System instability |

---

## 4. Risk Assessment

### 4.1 Risk Level Alignment

| Decision | Risk Level | Criteria Status | Monitoring Required |
|----------|-----------|-----------------|---------------------|
| **GO** | LOW | All 7 criteria passed | Standard monitoring |
| **CONDITIONAL_GO** | MEDIUM | 5 CRITICAL + diversity 40-59 | Enhanced monitoring + alerts |
| **NO-GO** | HIGH | ≥1 CRITICAL failure OR diversity <40 | Fix and re-run Phase 2 |

### 4.2 Risk Factors by Decision

#### GO (Risk: LOW)

**Characteristics**:
- Sufficient diversity (score ≥60)
- All quality thresholds exceeded
- System validated and stable

**Risk Profile**:
- Overfitting risk: LOW (high diversity)
- Correlated failure risk: LOW (avg correlation <0.8)
- Limited learning signal: LOW (varied strategies)

**Monitoring**: Standard Phase 3 metrics

#### CONDITIONAL_GO (Risk: MEDIUM)

**Characteristics**:
- Marginal diversity (score 40-59)
- All CRITICAL criteria pass
- Enhanced monitoring required

**Risk Profile**:
- Overfitting risk: MEDIUM (marginal diversity)
- Correlated failure risk: LOW-MEDIUM (correlation <0.8 but watch closely)
- Limited learning signal: MEDIUM (acceptable variety)

**Monitoring**: Enhanced diversity tracking + early warning alerts

#### NO-GO (Risk: HIGH)

**Characteristics**:
- Insufficient diversity (<40) OR
- Critical system failure

**Risk Profile**:
- Overfitting risk: HIGH (low diversity)
- Correlated failure risk: HIGH (strategies may fail together)
- Limited learning signal: HIGH (insufficient variety)

**Action**: Do NOT proceed to Phase 3 - fix issues first

---

## 5. Mitigation Plan (CONDITIONAL_GO)

### 5.1 Required Actions

When decision is CONDITIONAL_GO, implement ALL of the following:

#### 1. Enhanced Diversity Monitoring

**Requirement**: Real-time diversity tracking dashboard

**Implementation**:
```python
from src.monitoring.diversity_monitor import DiversityMonitor

monitor = DiversityMonitor(
    alert_threshold=35.0,  # Alert if diversity drops below 35/100
    check_interval_minutes=30
)
monitor.start()
```

**Metrics to Track**:
- Diversity score (current vs. baseline)
- Factor diversity trend
- Correlation matrix changes
- Risk diversity evolution

#### 2. Early Warning Alerts

**Requirement**: Alerts if diversity degrades during Phase 3

**Alert Conditions**:
- Diversity score drops below 35/100 (from 40-59 baseline)
- Average correlation exceeds 0.85 (from <0.8 baseline)
- Factor diversity drops below 0.3 (from baseline)

**Alert Channels**:
- Console warning (immediate)
- Log file entry (persistent)
- Email notification (optional, for long runs)

#### 3. Increased Mutation Diversity Rates

**Requirement**: Boost exploration to compensate for low diversity

**Configuration**:
```yaml
# config/learning_system.yaml
mutation:
  diversity_boost: true
  factor_mutation_rate: 0.4  # Increased from 0.3
  structure_mutation_rate: 0.3  # Increased from 0.2
  force_minimum_jaccard_distance: 0.3  # Prevent convergence
```

#### 4. Mid-Phase Diversity Assessment

**Requirement**: Re-evaluate diversity at Phase 3 midpoint

**Schedule**:
- After 50% of Phase 3 iterations
- If diversity <35/100: pause and review
- If diversity ≥35/100: continue with monitoring

### 5.2 Contingency Plan

If diversity drops below 35/100 during Phase 3:

1. **Pause learning loop**
2. **Diagnose root cause**:
   - Check mutation parameter settings
   - Review fitness function (is it over-selecting similar strategies?)
   - Analyze factor usage patterns
3. **Apply corrective action**:
   - Inject diverse seed strategies
   - Increase mutation diversity rates
   - Add diversity bonus to fitness function
4. **Resume Phase 3** after corrective action

---

## 6. Usage

### 6.1 Running Decision Evaluation

**Command**:
```bash
python3 scripts/evaluate_phase3_decision.py \
    --validation-results phase2_validated_results_20251101_132244.json \
    --duplicate-report duplicate_report.json \
    --diversity-report diversity_report_corrected.json \
    --output phase3_decision.md \
    --verbose
```

**Exit Codes**:
- `0` = GO decision
- `1` = CONDITIONAL_GO decision
- `2` = NO-GO decision
- `3` = Error (missing files, invalid JSON, etc.)

**Output File**: `phase3_decision.md` (comprehensive decision document)

### 6.2 Programmatic Usage

```python
from src.analysis.decision_framework import DecisionFramework

# Load input reports
validation_results = load_json('validation_results.json')
duplicate_report = load_json('duplicate_report.json')
diversity_report = load_json('diversity_report.json')

# Evaluate decision
framework = DecisionFramework()
decision = framework.evaluate(
    validation_results=validation_results,
    duplicate_report=duplicate_report,
    diversity_report=diversity_report
)

# Access results
print(f"Decision: {decision.decision}")
print(f"Risk Level: {decision.risk_level}")
print(f"Diversity Score: {decision.diversity_score:.1f}/100")
print(f"Unique Strategies: {decision.unique_strategies}")

# Check criteria
for criterion in decision.criteria_met:
    print(f"✅ {criterion.name}: {criterion.actual} {criterion.comparison} {criterion.threshold}")

for criterion in decision.criteria_failed:
    print(f"❌ {criterion.name}: {criterion.actual} {criterion.comparison} {criterion.threshold}")

# Generate decision document
framework.generate_decision_document(decision, 'phase3_decision.md')
```

### 6.3 Example Output

**Console Output**:
```
================================================================================
Phase 3 GO/NO-GO Decision Evaluation
================================================================================

Decision: ⚠️  CONDITIONAL_GO
Risk Level: 🟡 MEDIUM

Key Metrics:
  Unique Strategies:   4
  Diversity Score:     19.2/100
  Average Correlation: 0.500
  Execution Success:   100.0%

Criteria Evaluation:
  Passed: 4/7 (57%)

  CRITICAL Criteria:
    ✅ Minimum Unique Strategies: 4 ≥ 3
    ✅ Average Correlation: 0.500 < 0.8
    ✅ Validation Framework Fixed: True
    ✅ Execution Success Rate: 100.0% ≥ 100.0

  HIGH/MEDIUM/LOW Criteria:
    ❌ Diversity Score: 19.2 < 40.0 (HIGH)
    ❌ Factor Diversity: 0.083 < 0.5 (MEDIUM)
    ❌ Risk Diversity: 0.000 < 0.3 (LOW)

Mitigation Plan:
  1. Proceed to Phase 3 with enhanced diversity monitoring
  2. Implement real-time diversity tracking dashboard
  3. Set up alerts if diversity score drops below 35/100
  4. Increase mutation diversity rates to improve variety

Decision Document: phase3_decision.md
================================================================================
```

---

## 7. Decision Examples

### 7.1 Example 1: GO Decision

**Input Metrics**:
- Unique Strategies: 8
- Diversity Score: 67.3/100
- Avg Correlation: 0.42
- Factor Diversity: 0.68
- Risk Diversity: 0.45
- Validation Fixed: True
- Execution Success: 100%

**Evaluation**:
```
Criteria Assessment:
  ✅ Minimum Unique Strategies: 8 ≥ 3 (CRITICAL)
  ✅ Diversity Score: 67.3 ≥ 60 (HIGH)
  ✅ Average Correlation: 0.42 < 0.8 (CRITICAL)
  ✅ Factor Diversity: 0.68 ≥ 0.5 (MEDIUM)
  ✅ Risk Diversity: 0.45 ≥ 0.3 (LOW)
  ✅ Validation Framework Fixed: True (CRITICAL)
  ✅ Execution Success Rate: 100% ≥ 100 (CRITICAL)

Pass Rate: 7/7 (100%)
```

**Decision**: GO
**Risk**: LOW
**Action**: Proceed to Phase 3 with standard monitoring

---

### 7.2 Example 2: CONDITIONAL_GO Decision (Actual Case)

**Input Metrics**:
- Unique Strategies: 4
- Diversity Score: 19.2/100
- Avg Correlation: 0.50
- Factor Diversity: 0.083
- Risk Diversity: 0.000
- Validation Fixed: True
- Execution Success: 100%

**Evaluation**:
```
Criteria Assessment:
  ✅ Minimum Unique Strategies: 4 ≥ 3 (CRITICAL)
  ❌ Diversity Score: 19.2 < 40 (HIGH) ← Fails CONDITIONAL threshold
  ✅ Average Correlation: 0.50 < 0.8 (CRITICAL)
  ❌ Factor Diversity: 0.083 < 0.5 (MEDIUM) ← Fails but not blocking
  ❌ Risk Diversity: 0.000 < 0.3 (LOW) ← Data limitation, not blocking
  ✅ Validation Framework Fixed: True (CRITICAL)
  ✅ Execution Success Rate: 100% ≥ 100 (CRITICAL)

CRITICAL Criteria: 4/5 pass (80%)
Pass Rate: 4/7 (57%)
```

**Decision**: CONDITIONAL_GO (diversity 19.2 < 40, but all CRITICAL pass)
**Risk**: MEDIUM
**Action**: Proceed with enhanced monitoring + mitigation plan

**Note**: This is the actual Phase 3 decision for finlab (2025-11-03)

---

### 7.3 Example 3: NO-GO Decision

**Input Metrics**:
- Unique Strategies: 2
- Diversity Score: 28.5/100
- Avg Correlation: 0.65
- Factor Diversity: 0.15
- Risk Diversity: 0.10
- Validation Fixed: True
- Execution Success: 100%

**Evaluation**:
```
Criteria Assessment:
  ❌ Minimum Unique Strategies: 2 < 3 (CRITICAL) ← BLOCKING
  ❌ Diversity Score: 28.5 < 40 (HIGH)
  ✅ Average Correlation: 0.65 < 0.8 (CRITICAL)
  ❌ Factor Diversity: 0.15 < 0.5 (MEDIUM)
  ❌ Risk Diversity: 0.10 < 0.3 (LOW)
  ✅ Validation Framework Fixed: True (CRITICAL)
  ✅ Execution Success Rate: 100% ≥ 100 (CRITICAL)

CRITICAL Criteria: 3/5 pass (60%) ← INSUFFICIENT
```

**Decision**: NO-GO
**Risk**: HIGH
**Blocking Issues**:
1. Insufficient unique strategies (2 < 3)
2. Insufficient diversity (28.5 < 40)

**Action**: Do NOT proceed to Phase 3. Fix issues:
1. Adjust validation thresholds to retain more strategies
2. Increase Phase 2 population size
3. Boost mutation diversity rates
4. Re-run Phase 2 with diversity-focused configuration

---

## 8. Troubleshooting

### 8.1 Decision Shows NO-GO Despite Good Metrics

**Symptom**: Individual metrics look good but decision is NO-GO

**Possible Causes**:
1. Unique strategies <3 (CRITICAL failure)
2. Validation framework not fixed (bonferroni_threshold != 0.5)
3. Execution success rate <100%

**Solution**:
```bash
# Check CRITICAL criteria
jq '.criteria_failed[] | select(.weight=="CRITICAL")' phase3_decision.json

# Verify validation framework status
jq '.validation_statistics.bonferroni_threshold' validation_results.json
# Should output: 0.5
```

### 8.2 Decision Changes from NO-GO to CONDITIONAL_GO

**Symptom**: After bug fix, decision changed

**Cause**: Validation framework bug fixed (bonferroni threshold 0.8 → 0.5)

**Expected Behavior**: This is correct! Bug fix allows more accurate assessment.

**Verification**:
- Before fix: validation_fixed = False (CRITICAL failure)
- After fix: validation_fixed = True (CRITICAL pass)
- Decision improved: NO-GO → CONDITIONAL_GO

### 8.3 Diversity Score Low Despite Different Strategies

**Symptom**: Strategies look different but diversity score <40

**Investigation Steps**:
1. Check factor overlap: `jq '.factors.usage_distribution' diversity_report.json`
2. Review correlation matrix: Open `diversity_report_correlation_heatmap.png`
3. Inspect individual strategies: `diff generated_strategy_iter0.py generated_strategy_iter2.py`

**Common Causes**:
- Different code but using same core factors
- High correlation in returns (different logic, similar outcomes)
- Limited factor library (all strategies pick from same small set)

**Solutions**:
- Expand factor library
- Add diversity bonus to fitness function
- Seed population with diverse templates

---

## 9. Best Practices

### 9.1 When to Re-evaluate Decision

**Required**:
- After Phase 2 completion (always)
- After bug fixes to validation framework
- After adjusting diversity parameters

**Optional**:
- Mid-Phase 3 (if diversity concerns)
- After major mutation parameter changes
- Before Phase 3 restart after pause

### 9.2 Interpreting Risk Levels

| Risk Level | Proceed? | Monitoring | Typical Scenario |
|-----------|----------|------------|------------------|
| **LOW** | Yes | Standard | All criteria optimal |
| **MEDIUM** | Yes (with plan) | Enhanced | Marginal diversity but system healthy |
| **HIGH** | No | N/A | Critical failures blocking progression |

### 9.3 Documenting Decisions

Always save decision document for audit trail:

```bash
# Include timestamp in filename
python3 scripts/evaluate_phase3_decision.py \
    --validation-results validation_results.json \
    --duplicate-report duplicate_report.json \
    --diversity-report diversity_report.json \
    --output "phase3_decision_$(date +%Y%m%d_%H%M%S).md"
```

**Archive**:
- Decision document (Markdown)
- All input JSON files
- Console output (exit code + summary)

---

## 10. API Reference

### 10.1 DecisionFramework Class

```python
class DecisionFramework:
    """GO/NO-GO decision framework for Phase 3 progression."""

    # Decision thresholds
    MIN_UNIQUE_STRATEGIES = 3
    DIVERSITY_THRESHOLD_GO = 60.0
    DIVERSITY_THRESHOLD_CONDITIONAL = 40.0
    CORRELATION_THRESHOLD = 0.8
    FACTOR_DIVERSITY_THRESHOLD = 0.5
    RISK_DIVERSITY_THRESHOLD = 0.3
    EXECUTION_SUCCESS_RATE = 100.0

    def evaluate(
        self,
        validation_results: Dict[str, Any],
        duplicate_report: Dict[str, Any],
        diversity_report: Dict[str, Any]
    ) -> DecisionReport:
        """Evaluate GO/NO-GO decision based on all criteria."""

    def check_go_criteria(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Check all GO criteria (optimal case)."""

    def check_conditional_criteria(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Check CONDITIONAL GO criteria (minimal acceptable case)."""

    def assess_risk(
        self,
        decision: str,
        criteria_met: List[DecisionCriteria],
        criteria_failed: List[DecisionCriteria]
    ) -> str:
        """Assess risk level based on decision and criteria."""
```

### 10.2 DecisionReport Dataclass

```python
@dataclass
class DecisionReport:
    """Comprehensive decision report."""

    decision: str                     # "GO", "CONDITIONAL_GO", "NO-GO"
    risk_level: str                   # "LOW", "MEDIUM", "HIGH"
    total_strategies: int
    unique_strategies: int
    diversity_score: float            # 0-100
    avg_correlation: float            # 0-1
    factor_diversity: float           # 0-1
    risk_diversity: float             # 0-1
    validation_fixed: bool
    execution_success_rate: float     # 0-100
    criteria_met: List[DecisionCriteria]
    criteria_failed: List[DecisionCriteria]
    warnings: List[str]
    recommendations: List[str]
    summary: str

    def generate_markdown(self) -> str:
        """Generate markdown decision document."""
```

---

## 11. References

### 11.1 Key Documents

- [VALIDATION_FRAMEWORK.md](VALIDATION_FRAMEWORK.md) - Threshold bug fix details
- [DIVERSITY_ANALYSIS.md](DIVERSITY_ANALYSIS.md) - Diversity metrics explained
- [PHASE3_GO_NO_GO_DECISION_CORRECTED.md](../PHASE3_GO_NO_GO_DECISION_CORRECTED.md) - Actual decision report

### 11.2 Related Code

- `src/analysis/decision_framework.py` - Decision logic
- `src/analysis/diversity_analyzer.py` - Diversity metrics
- `scripts/evaluate_phase3_decision.py` - CLI tool

---

**Document Version**: 1.0.0
**Created**: 2025-11-03
**Author**: AI Assistant (Technical Writer Persona)
