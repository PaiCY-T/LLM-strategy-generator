# Extended Validation Analysis (30 Iterations)

## Executive Summary

**Date**: 2025-10-08
**Model**: gemini-2.5-flash (via Google AI)
**Duration**: ~20 minutes
**Result**: ❌ **CRITICAL FAILURE** - 0/4 criteria passed

### Performance Metrics

- **Iterations Completed**: 30/30 (100%)
- **Successful Iterations**: 1/30 (3.3%)
- **Best Sharpe Ratio**: 0.9929
- **Average Sharpe Ratio**: 0.0331
- **Worst Regression**: -100.0%
- **Champion**: Iteration 6 (Sharpe 2.4751)

### MVP Criteria Results

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| Best Sharpe >1.2 | >1.2 | 0.9929 | ❌ FAIL |
| Success rate >60% | >60% | 3.3% | ❌ FAIL |
| Avg Sharpe >0.5 | >0.5 | 0.0331 | ❌ FAIL |
| No regression >10% | <10% | -100.0% | ❌ FAIL |

**Critical Finding**: Performance dramatically degraded from 10-iteration MVP validation (3/4 criteria passed, 70% success rate) to extended validation (0/4 criteria passed, 3.3% success rate).

---

## Root Cause Analysis

### Primary Issue: Dataset Key Hallucination

The LLM is generating code with **non-existent Finlab dataset keys** that are not available in the API. This is the main cause of the 96.7% failure rate.

#### Unavailable Datasets Attempted

1. **`foreign_main_force_buy_sell_summary`** (multiple iterations)
   - **Status**: Does not exist
   - **Correct Alternative**: `institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)`

2. **`fundamental_features:EPS`** (iterations 14, 18, 20, 25)
   - **Status**: Does not exist
   - **Correct Alternative**: `financial_statement:每股盈餘`

3. **`investment_trust_buy_sell_summary`** (iteration 19)
   - **Status**: Does not exist
   - **Correct Alternative**: `institutional_investors_trading_summary:投信買賣超股數`

4. **`three_main_forces_buy_sell_summary`** (iteration 22)
   - **Status**: Does not exist
   - **Correct Alternative**: Must be computed from individual components

5. **`etl:foreign_main_force_buy_sell_summary:strength`** (iteration 15)
   - **Status**: Does not exist
   - **Correct Alternative**: Not available, must be computed

6. **`indicator:RSI`** (iteration 26)
   - **Status**: Does not exist
   - **Correct Alternative**: Not available in dataset, must be computed manually

### Secondary Issue: Auto-Fix Limitations

The auto-fix mechanism successfully corrected known patterns:
- ✅ `etl:monthly_revenue:revenue_yoy` → `monthly_revenue:去年同月增減(%)`
- ✅ `fundamental_features:本益比` → `price_earning_ratio:本益比`

However, it **failed to detect** the hallucinated dataset names because they were not in the known-bad-keys list.

### Preservation System Performance

The preservation validation system performed well:
- **Successful Catches**: Iterations 8, 10, 13, 16, 22, 28
- **Retry Success Rate**: ~83% (5/6 violations successfully corrected on retry)
- **Fallback Handling**: Iteration 22 correctly fell back after exhausting retries

---

## Failure Pattern Collection

**Total Patterns Collected**: 4 patterns

### Pattern Breakdown

| Pattern Type | Count | Description |
|--------------|-------|-------------|
| `liquidity_threshold` | 2 | Violations of minimum 50M TWD liquidity requirement |
| `roe_smoothing` | 2 | Changes to ROE rolling window parameters |

**Note**: Failure pattern collection is working but only captures P0 parameter violations, not dataset key errors.

---

## Comparison: 10-Iteration MVP vs. 30-Iteration Extended

| Metric | MVP (10 iter) | Extended (30 iter) | Change |
|--------|---------------|-------------------|---------|
| Success Rate | 70% | 3.3% | **-66.7 pp** ❌ |
| Best Sharpe | 2.4751 | 0.9929 | **-59.9%** ❌ |
| Avg Sharpe | 1.1677 | 0.0331 | **-97.2%** ❌ |
| Criteria Passed | 3/4 | 0/4 | **-3** ❌ |

**Critical Degradation**: Extended validation shows system instability and inability to generate valid strategies consistently.

---

## Technical Analysis

### Gemini API Performance

- **Total API Calls**: ~90 (3 per iteration × 30 iterations)
- **Safety Filter Triggers**: ~5-7 occurrences (finish_reason=2)
- **Retry Success Rate**: ~90% (safety filter handled successfully)
- **Generation Failures**: Iteration 22 required 2 retries, eventually succeeded with fallback

### Preservation Enforcement

**Violations Detected**: 6 iterations (8, 10, 13, 16, 22, 28)

**Retry Outcomes**:
- Iteration 8: ✅ Success on retry 1
- Iteration 10: ✅ Success on retry 1
- Iteration 13: ✅ Success on retry 1
- Iteration 16: ✅ Success on retry 1
- Iteration 22: ❌ Failed both retries, fell back with monitoring
- Iteration 28: ✅ Success on retry 1

**Fallback Handling**: Working correctly - iteration 22 proceeded with monitoring after retry exhaustion.

### Champion Tracking

**Champion Evolution**:
- Iteration 6: Sharpe 2.4751 (champion established)
- Iterations 7-29: No new champions (all failed or underperformed)

**Champion Preservation**: ✅ Working correctly - champion from MVP validation (iteration 6) maintained throughout extended validation.

---

## Recommendations

### 1. **URGENT: Fix Dataset Key Validation** (P0)

**Problem**: LLM hallucinates non-existent dataset keys, causing 96.7% failure rate.

**Solution Options**:

**A. Provide Available Dataset Reference in Prompt** (Recommended)
- Include the 307 available datasets from `/mnt/c/Users/jnpi/ML4T/epic-finlab-data-downloader/example/finlab_database_cleaned.csv` in the prompt template
- Add explicit instruction: "ONLY use dataset keys from this list"
- Estimated Impact: 70-90% reduction in dataset key errors

**B. Enhance Auto-Fix with Comprehensive Mapping**
- Expand `KNOWN_BAD_KEYS` to include all common hallucinations
- Add semantic mapping (e.g., "foreign" → "institutional_investors_trading_summary:外陸資...")
- Estimated Impact: 50-70% reduction in dataset key errors

**C. Pre-Generation Validation** (Long-term)
- Validate all `data.get()` calls against available datasets before execution
- Reject and regenerate if invalid keys detected
- Estimated Impact: 90-95% reduction in dataset key errors

### 2. **Expand Failure Pattern Tracking** (P1)

**Problem**: Current failure tracker only captures P0 parameter violations, missing dataset key errors.

**Solution**:
- Add new failure pattern category: `dataset_key_errors`
- Track which dataset keys are repeatedly attempted but fail
- Use this information to strengthen prompt guidance

### 3. **Investigate MVP vs Extended Degradation** (P1)

**Problem**: 10-iteration validation passed 3/4 criteria, but 30-iteration validation passed 0/4.

**Investigation Needed**:
- Why did iteration 6 succeed but later iterations fail?
- Is there exploration drift causing dataset key hallucination?
- Should exploration mode be tuned to stay within known datasets?

###4. **Model Selection Analysis** (P2)

**Question**: Would OpenRouter's Claude Sonnet 4 perform better with dataset key accuracy?

**Next Steps**:
- Re-run 10-iteration validation with Claude Sonnet 4
- Compare dataset key error rates between gemini-2.5-flash and Claude Sonnet 4

---

## Conclusion

The extended validation **failed critically** due to systematic dataset key hallucination by the LLM. While the preservation enforcement and champion tracking systems worked correctly, the fundamental issue is that the LLM generates non-existent dataset keys that cause immediate execution failures.

**System is NOT production-ready** until dataset key validation is implemented.

**Recommended Next Actions**:
1. Implement Solution A (provide available datasets in prompt) - **URGENT**
2. Re-run 30-iteration validation with fixed prompt
3. Verify success rate returns to >60% threshold
4. Proceed with STATUS.md update only after fix validated

---

## Appendix: Example Failure Logs

### Iteration 15 (failed - hallucinated dataset)
```python
foreign_strength = data.get('etl:foreign_main_force_buy_sell_summary:strength')
```
**Error**: `Exception: **Error: etl:foreign_main_force_buy_sell_summary:strength not exists`

### Iteration 14 (failed - hallucinated dataset)
```python
eps = data.get('fundamental_features:EPS')
```
**Error**: `Exception: **Error: fundamental_features:EPS not exists`

### Iteration 6 (success - valid datasets only)
```python
close = data.get('price:收盤價')
pe_ratio = data.get('price_earning_ratio:本益比')
revenue_yoy = data.get('monthly_revenue:去年同月增減(%)')
foreign_flow = data.get('foreign_main_force_buy_sell_summary')  # ⚠️ Also invalid but iteration succeeded
trading_value = data.get('price:成交金額')
```

**Note**: Iteration 6's success despite using `foreign_main_force_buy_sell_summary` suggests this dataset may have existed in an earlier Finlab API version, or the error was suppressed differently.
