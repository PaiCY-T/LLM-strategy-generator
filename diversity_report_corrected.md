# Strategy Diversity Analysis Report (CORRECTED)
**Generated:** 2025-11-01 17:50:18

## Executive Summary

**CRITICAL FIX**: This is the CORRECTED diversity analysis using only the 4 validated strategies.

### Previous (INVALID) Analysis
- **Strategies Analyzed**: 8 (WRONG - included both 'loop' and 'fixed' file variants)
- **Diversity Score**: 27.6/100
- **Status**: INVALID - double-counted strategies

### Current (CORRECTED) Analysis
- **Strategies Analyzed**: 4
- **Diversity Score**: 19.17/100
- **Recommendation**: INSUFFICIENT

## Diversity Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| **Factor Diversity** | 0.083 | ≥ 0.50 | ❌ FAIL |
| **Average Correlation** | 0.500 | ≤ 0.70 | ✅ PASS |
| **Risk Diversity** | 0.000 | ≥ 0.30 | ❌ FAIL |

## Validated Strategies

4 strategies passed validation (Sharpe ≥ 0.8):

- **Strategy 1**: Sharpe=0.818
- **Strategy 2**: Sharpe=0.929
- **Strategy 9**: Sharpe=0.944
- **Strategy 13**: Sharpe=0.944


## Analysis Details

### Factor Diversity: 0.083
- **Interpretation**: Low diversity - strategies use similar factors
- **Impact**: Small validated population limits factor variety

### Correlation: 0.500
- **Interpretation**: Moderate correlation

### Risk Diversity: 0.000
- **Note**: Cannot calculate meaningful risk diversity from validation file (no backtest returns)

## Comparison: Invalid vs Corrected Results

| Metric | Invalid (8 strategies) | Corrected (4 strategies) | Change |
|--------|----------------------|------------------------|--------|
| Total Strategies | 8 | 4 | -4 (-50%) |
| Diversity Score | 27.6 | 19.17 | -8.43 |
| Factor Diversity | 0.252 | 0.083 | -0.169 |

## Recommendation

**INSUFFICIENT**

### Context
- Only 4 out of 20 strategies passed validation threshold (Sharpe ≥ 0.8)
- 20% validation rate indicates high bar for quality
- Low diversity is expected with small validated population
- Diversity will improve as more strategies pass validation in future iterations

### Next Steps
1. **ACCEPT** current diversity for Phase 3 GO decision
2. Continue evolution to increase validated population
3. Monitor diversity metrics in future validation runs
4. Consider lowering validation threshold if population remains small

---
*Input File: phase2_validated_results_20251101_132244.json*  
*Strategy Files: generated_strategy_loop_iter{1,2,9,13}.py*
