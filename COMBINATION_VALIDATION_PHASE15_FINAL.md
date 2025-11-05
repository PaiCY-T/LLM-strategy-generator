# CombinationTemplate 10-Generation Smoke Test

**Generated**: 2025-10-20 12:48:52
**Configuration**: Population=10, Generations=10, Elite=2
**Template**: CombinationTemplate
**Status**: ❌ **FAILED**

---

## Executive Summary

This smoke test validates CombinationTemplate integration with the population-based evolution system.
The test uses minimal configuration (N=10, 10 generations) to verify basic functionality and stability.

⚠️ **Some criteria not met. Investigation required.**

---

## Success Criteria Results

### 1. Test Completion Without Crashes

- **Status**: ✅ PASS
- **Result**: Test completed all 10 generations
- **Interpretation**: System stability validated

### 2. No Exceptions During Evolution

- **Status**: ✅ PASS
- **Result**: No exceptions raised
- **Interpretation**: Clean execution path

### 3. At Least 50% Strategies Have Sharpe >0

- **Status**: ✅ PASS
- **Actual**: 100.0% (2/2 strategies)
- **Threshold**: ≥50%
- **Interpretation**: Majority of strategies produce positive risk-adjusted returns

### 4. Best Strategy Sharpe >1.0

- **Status**: ✅ PASS
- **Actual**: 1.378
- **Threshold**: >1.0
- **Interpretation**: Strong best-case performance achieved

### 5. Diversity Maintained Throughout Evolution

- **Status**: ❌ FAIL
- **Minimum Diversity**: 0.000
- **Threshold**: ≥0.3
- **Interpretation**: Premature convergence detected

---

## Generation History

| Gen | Diversity | Pareto Size | Champion Updated | Best Sharpe | Time (s) |
|-----|-----------|-------------|------------------|-------------|----------|
|  1  | 0.000     |           2 |                  |       1.378 |   299.01 |
|  2  | 0.000     |           2 |                  |       1.378 |     0.23 |
|  3  | 0.000     |           2 |                  |       1.378 |     0.17 |
|  4  | 0.000     |           2 |                  |       1.378 |     0.20 |
|  5  | 0.000     |           2 |                  |       1.378 |     0.12 |
|  6  | 0.000     |           2 |                  |       1.378 |     0.06 |
|  7  | 0.000     |           2 |                  |       1.378 |     0.06 |
|  8  | 0.000     |           2 |                  |       1.378 |     0.06 |
|  9  | 0.000     |           2 |                  |       1.378 |     0.06 |
| 10  | 0.000     |           2 |                  |       1.378 |     0.07 |
| 11  | 0.000     |           2 |                  |       1.378 |     0.06 |
| 12  | 0.000     |           2 |                  |       1.378 |     0.06 |
| 13  | 0.000     |           2 |                  |       1.378 |     0.07 |
| 14  | 0.000     |           2 |                  |       1.378 |     0.08 |
| 15  | 0.000     |           2 |                  |       1.378 |     0.07 |
| 16  | 0.000     |           2 |                  |       1.378 |     0.07 |
| 17  | 0.000     |           2 |                  |       1.378 |     0.07 |
| 18  | 0.000     |           2 |                  |       1.378 |     0.07 |
| 19  | 0.000     |           2 |                  |       1.378 |     0.08 |
| 20  | 0.000     |           2 |                  |       1.378 |     0.07 |


---

## Performance Analysis

### Diversity Trend
- **Average Diversity**: 0.000
- **Minimum Diversity**: 0.000
- **Maximum Diversity**: 0.000
- **Trend**: Stable

### Sharpe Distribution (Final Generation)
- **Mean Sharpe**: 1.377
- **Median Sharpe**: 1.377
- **Std Dev**: 0.001
- **Range**: [1.376, 1.378]

### Timing Analysis
- **Total Runtime**: 300.72 seconds (5.01 minutes)
- **Average Generation Time**: 15.04 seconds
- **Estimated 100-gen Runtime**: 25.1 minutes

---

## Recommendations

⚠️ **Issues Detected**

- **Diversity**: Minimum diversity 0.000 <0.3. Risk of premature convergence.

**Next Steps**:
1. Review logs for detailed error information
2. Apply fixes based on identified issues
3. Re-run smoke test

---

## Appendix

### Test Configuration
- **Population Size**: 10
- **Generations**: 10
- **Elite Count**: 2
- **Tournament Size**: 3 (default)
- **Template**: CombinationTemplate
- **Checkpoint Directory**: combination_validation_checkpoints_final
- **Log File**: combination_smoke_test.log

### Template Information
- **Name**: Combination
- **Type**: Multi-template weighted combination
- **Sub-templates**: turtle, momentum, mastiff
- **Rebalancing**: Monthly ('M') or Weekly ('W-FRI')
- **Weight Options**: [0.5, 0.5], [0.7, 0.3], [0.4, 0.4, 0.2]

---

**End of Smoke Test Report**
