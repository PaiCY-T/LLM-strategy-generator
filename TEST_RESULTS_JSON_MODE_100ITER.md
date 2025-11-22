# 100-Iteration Test Results - JSON Parameter Output Mode

**Test Date**: 2025-11-22 06:08-06:24 (UTC+8)
**Duration**: 16 minutes (0.27 hours)
**Configuration**: Template Mode + JSON Mode (Phase 1.1)

---

## 🎯 SUCCESS METRICS

### Validation Success Rate
- **Total Iterations**: 100
- **Validation Passed**: 100/100 (100.0%)
- **Execution Success**: 100/100 (100.0%)
- **Overall Success**: 100/100 (100.0%)

### Performance Improvement
- **Baseline (Old System)**: 20.6% success rate
- **JSON Mode (New System)**: 100.0% success rate
- **Improvement**: **4.9x** (from 20.6% → 100%)

---

## 📊 PERFORMANCE METRICS

### Sharpe Ratio Statistics
- **Sample Size**: 100
- **Min Sharpe**: -0.2740
- **Max Sharpe**: 0.9451
- **Mean Sharpe**: 0.3545
- **Std Sharpe**: 0.3852

### Convergence Analysis
- **Rolling Variance**: 0.349
- **Convergence Achieved**: ✅ Yes (σ < 0.5)

### Champion Updates
- **Update Frequency**: 1.0%
- **Avg Duration per Iteration**: 9.76s
- **Total Test Duration**: 0.27 hours

---

## 🎯 PARAMETER EXPLORATION

### Diversity Metrics
- **Unique Parameter Combinations**: 11
- **Total Iterations**: 100
- **Exploration Rate**: 11% unique combinations

### Sample Parameters (First 5 Iterations)
```
Iter 0: ✅ momentum=5,  ma=20,  catalyst=earnings, n_stocks=20
Iter 1: ✅ momentum=10, ma=60,  catalyst=earnings, n_stocks=15
Iter 2: ✅ momentum=20, ma=60,  catalyst=revenue,  n_stocks=15
Iter 3: ✅ momentum=20, ma=60,  catalyst=revenue,  n_stocks=10
Iter 4: ✅ momentum=10, ma=60,  catalyst=revenue,  n_stocks=15
```

---

## ✅ CODE REVIEW FIXES APPLIED

### 1. HIGH: StructuredErrorFeedback Integration
- **Status**: ✅ Fixed
- **Change**: Wired `StructuredErrorFeedback` into retry loop
- **Impact**: Richer error context for LLM retry attempts

### 2. MEDIUM: DRY Violation (PARAM_ALLOWED_VALUES)
- **Status**: ✅ Fixed
- **Change**: Centralized parameter constants in `src/schemas/param_constants.py`
- **Impact**: Eliminated duplication in 3 files

### 3. MEDIUM: Duplicated LLM API Call Logic
- **Status**: ✅ Fixed
- **Change**: Created unified `_call_llm_api()` method
- **Impact**: Reduced code duplication by ~40 lines

---

## 📈 SYSTEM COMPONENTS

### Enabled Features
- ✅ **Template Mode**: ENABLED (Momentum golden template)
- ✅ **JSON Mode**: ENABLED (Phase 1.1 JSON Parameter Output)
- ✅ **Pydantic Validation**: MomentumStrategyParams with Literal types
- ✅ **Retry Logic**: MAX_RETRIES = 3 with structured feedback
- ✅ **API Fallback**: Google AI → OpenRouter (quota-aware)

### Architecture Layers
1. **JsonPromptBuilder**: JSON-only prompts with schema + few-shot examples
2. **TemplateCodeGenerator**: JSON extraction → Pydantic validation → Code generation
3. **StructuredErrorFeedback**: Rich error context for retry loops
4. **TemplateParameterGenerator**: Unified retry logic with error feedback integration

---

## 🔍 STATISTICAL ANALYSIS

### Learning Effect
- **Cohen's d**: 0.247 (small effect)
- **P-value**: 0.3430 (not significant)
- **95% Confidence Interval**: [0.278, 0.431]

### Production Readiness Assessment
- **Status**: ⚠️ NOT READY FOR PRODUCTION
- **Reasons**:
  - Statistical significance NOT met (p-value = 0.3430 ≥ 0.05)
  - Effect size too small (Cohen's d = 0.247 < 0.4)
- **Criteria Met**:
  - ✅ Convergence achieved (rolling variance = 0.349 < 0.5)
  - ✅ 100% validation success rate

---

## 💡 KEY FINDINGS

### Validation Success
1. **100% validation rate** across all 100 iterations
2. **Zero PreservationValidator failures** (baseline: 59.2% failures)
3. **Consistent parameter preservation** with template mode

### Performance Characteristics
1. **Fast execution**: 9.76s per iteration average
2. **Stable convergence**: Rolling variance below 0.5 threshold
3. **Low champion update rate**: 1.0% (highly stable)

### System Reliability
1. **Quota management**: Automatic Google AI → OpenRouter fallback
2. **Error handling**: Structured feedback with 3 retry attempts
3. **Checkpoint system**: Automatic checkpointing every 10 iterations

---

## 🚀 NEXT STEPS

### Immediate Actions
1. ✅ Validate 100% success rate at scale (COMPLETED)
2. ✅ Apply code review fixes (COMPLETED)
3. ⏭️ Address production readiness gaps:
   - Investigate low effect size (Cohen's d = 0.247)
   - Analyze low champion update rate (1.0%)
   - Consider longer test runs for statistical significance

### Future Improvements
1. Tune exploration vs exploitation balance
2. Increase parameter space diversity
3. Optimize learning rate for faster convergence

---

## 📝 TEST FILES

- **Test Script**: `run_100iteration_test.py`
- **Test Harness**: `tests/integration/extended_test_harness.py`
- **Iteration History**: `iteration_history.json`
- **Checkpoints**: `checkpoints_100iteration/checkpoint_iter_*.json`
- **Log File**: `logs/100iteration_test_20251122_060834.log`

---

**Generated**: 2025-11-22 06:30:00 (UTC+8)
**Test Environment**: WSL2 Ubuntu + Python 3.10 + Finlab Taiwan Stock Data
