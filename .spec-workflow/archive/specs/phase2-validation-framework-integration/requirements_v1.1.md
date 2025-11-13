# Phase 2 Validation Framework Integration - Requirements v1.1

**Version**: 1.1 (Production Readiness)
**Date**: 2025-10-31
**Based On**: Critical review findings

---

## Version 1.1 Requirements: Production Readiness

### Critical Gaps from Phase 1.0

Phase 1.0 delivered functional implementation but failed production readiness criteria due to:

1. **Statistical Invalidity**: Returns synthesis scientifically unsound
2. **Testing Gaps**: No integration or E2E tests
3. **Arbitrary Thresholds**: No empirical basis

### New Requirements for Phase 1.1

---

## REQ-1.1.1: Actual Returns Extraction (BLOCKING)

**Priority**: P0 CRITICAL
**Acceptance Criteria**:

1. **AC-1.1.1-1**: Bootstrap MUST use actual daily returns from finlab Report
   - Extract from `report.returns`, `report.daily_returns`, `report.equity`, or `report.position`
   - NO synthesis of returns under any circumstances
   - Multi-layered fallback extraction strategy

2. **AC-1.1.1-2**: Minimum 252 trading days REQUIRED
   - Strategies with <252 days MUST be rejected with clear error
   - Error message: "Insufficient data for bootstrap: X days < 252 minimum"

3. **AC-1.1.1-3**: Equity curve differentiation MUST work
   - `report.equity.pct_change()` extraction tested
   - Handle both Series and DataFrame equity formats
   - Dropna() to remove invalid values

**Testing Requirements**:
- Unit tests with mock Reports (4 extraction methods)
- Integration test with real finlab Report
- Edge case: <252 days raises ValueError

---

## REQ-1.1.2: Stationary Bootstrap (BLOCKING)

**Priority**: P0 CRITICAL
**Acceptance Criteria**:

1. **AC-1.1.2-1**: Implement Politis & Romano stationary bootstrap
   - Geometric block lengths (not fixed)
   - Circular wrapping for block continuation
   - Preserves autocorrelation and volatility clustering

2. **AC-1.1.2-2**: Statistical validation REQUIRED
   - Compare against scipy.stats.bootstrap
   - CI widths within 30% of scipy
   - Coverage rates: 95% CI should cover parameter 85-100% of time

3. **AC-1.1.2-3**: Performance acceptable
   - 1000 iterations MUST complete in <5 seconds
   - No memory leaks over repeated execution

**Testing Requirements**:
- Statistical validation vs scipy
- Coverage rate verification (100 experiments)
- Performance benchmark

---

## REQ-1.1.3: Empirical Threshold (BLOCKING)

**Priority**: P0 CRITICAL
**Acceptance Criteria**:

1. **AC-1.1.3-1**: Threshold based on Taiwan market benchmarks
   - Primary: 0050.TW (Yuanta Taiwan 50 ETF)
   - Rolling 3-year Sharpe ratio calculation
   - Margin: +0.2 above benchmark

2. **AC-1.1.3-2**: Dynamic calculation
   - `DynamicThresholdCalculator` class implemented
   - Configurable benchmark ticker, lookback period, margin
   - Floor value: max(calculated, 0.0) for positive returns

3. **AC-1.1.3-3**: Research documented
   - Historical analysis: 2018-2024
   - Market regime variations documented
   - Justification for margin and floor values

**Testing Requirements**:
- Unit tests for threshold calculator
- Different dates produce different thresholds (when data available)
- Floor enforcement verified

---

## REQ-1.1.4: E2E Integration Testing (BLOCKING)

**Priority**: P0 CRITICAL
**Acceptance Criteria**:

1. **AC-1.1.4-1**: Full pipeline test with real finlab
   - Load real data and sim objects
   - Execute actual momentum strategy
   - Run all 5 validators in sequence
   - Generate HTML/JSON reports

2. **AC-1.1.4-2**: Verification of actual returns usage
   - Bootstrap result MUST show `n_days >= 252`
   - No synthesis fallback should occur
   - CI widths reasonable (not suspiciously narrow)

3. **AC-1.1.4-3**: Failure case testing
   - Strategy with negative Sharpe (should fail validations)
   - Strategy with <252 days (should raise ValueError)
   - Strategy with high volatility (may fail stability checks)

**Testing Requirements**:
- E2E test with 1 known-good strategy
- E2E test with 3 failure scenarios
- Verify report generation works end-to-end

---

## REQ-1.1.5: Statistical Validation (BLOCKING)

**Priority**: P0 CRITICAL
**Acceptance Criteria**:

1. **AC-1.1.5-1**: Bootstrap vs scipy comparison
   - Point estimates within reasonable range
   - CI widths comparable (±30%)
   - No systematic bias

2. **AC-1.1.5-2**: Coverage rate verification
   - Run 100 bootstrap experiments
   - 95% CI should cover true parameter 85-100% of time
   - Document actual coverage rate achieved

**Testing Requirements**:
- test_bootstrap_vs_scipy()
- test_coverage_rate()
- Known returns series validation

---

## REQ-1.1.6: Backward Compatibility (BLOCKING)

**Priority**: P0 CRITICAL
**Acceptance Criteria**:

1. **AC-1.1.6-1**: No breaking API changes
   - All public exports remain accessible
   - Method signatures backward compatible
   - Optional parameters can be added, required cannot change

2. **AC-1.1.6-2**: Regression tests pass
   - Identify existing validation client code
   - Run client tests against new implementation
   - No failures introduced

**Testing Requirements**:
- Import compatibility tests
- Method signature compatibility tests
- Existing client code regression suite

---

## REQ-1.1.7: Performance Benchmarks (HIGH)

**Priority**: P1 HIGH
**Acceptance Criteria**:

1. **AC-1.1.7-1**: Per-strategy overhead <60 seconds
   - Full validation pipeline (all 5 validators)
   - Measured on production hardware
   - Average across 5+ strategies

2. **AC-1.1.7-2**: No memory leaks
   - Stress test with 100 synthetic strategies
   - Memory usage stable over time
   - No unbounded growth

3. **AC-1.1.7-3**: HTML report scalability
   - Generate report with 1000+ strategies
   - File size <5MB
   - Browser can load and render

**Testing Requirements**:
- 20-strategy benchmark
- 100-strategy stress test
- 1000-strategy report generation test

---

## REQ-1.1.8: Failure Mode Handling (HIGH)

**Priority**: P1 HIGH
**Acceptance Criteria**:

1. **AC-1.1.8-1**: Graceful error handling
   - NaN/inf values in returns: Clear error
   - Network timeout (baseline fetch): Fallback or skip
   - Malformed YAML config: Startup error with fix suggestion

2. **AC-1.1.8-2**: Concurrent execution safe
   - Multiple strategies validated in parallel
   - No race conditions in baseline cache
   - Resource conflicts prevented

3. **AC-1.1.8-3**: Error messages actionable
   - All errors include context
   - Suggest remediation steps
   - Include relevant data for debugging

**Testing Requirements**:
- test_nan_in_returns()
- test_concurrent_execution()
- test_network_timeout()
- test_malformed_config()

---

## REQ-1.1.9: Monitoring Integration (HIGH)

**Priority**: P1 HIGH
**Acceptance Criteria**:

1. **AC-1.1.9-1**: Comprehensive logging
   - All validator executions logged
   - Performance metrics logged
   - Errors logged with full context

2. **AC-1.1.9-2**: Metrics collection
   - Validation pass/fail rates
   - Execution time per validator
   - Error frequency by type

3. **AC-1.1.9-3**: Alert hooks ready
   - Hook points for external monitoring
   - Critical failures trigger alerts
   - Performance degradation detection

**Testing Requirements**:
- Verify logging output
- Verify metrics collection
- Test alert hook integration

---

## REQ-1.1.10: Documentation Updates (MEDIUM)

**Priority**: P2
**Acceptance Criteria**:

1. **AC-1.1.10-1**: API documentation current
   - All new parameters documented
   - Examples updated
   - Migration guide from v1.0 to v1.1

2. **AC-1.1.10-2**: Known limitations documented
   - Statistical assumptions listed
   - Performance characteristics documented
   - Edge cases and failure modes listed

**Testing Requirements**:
- Documentation review
- Example code execution

---

## REQ-1.1.11: Production Runbook (MEDIUM)

**Priority**: P2
**Acceptance Criteria**:

1. **AC-1.1.11-1**: Deployment guide created
   - Configuration requirements
   - Environment setup
   - Validation checklist

2. **AC-1.1.11-2**: Troubleshooting procedures
   - Common issues and fixes
   - Performance debugging steps
   - Error diagnosis flowchart

**Testing Requirements**:
- Runbook walkthrough
- Issue scenario testing

---

## Success Criteria - Phase 1.1

Production deployment BLOCKED until:

### Statistical Validity
- [x] REQ-1.1.1: Actual returns extraction
- [x] REQ-1.1.2: Stationary bootstrap
- [x] REQ-1.1.3: Empirical threshold

### Integration Testing
- [x] REQ-1.1.4: E2E pipeline test
- [x] REQ-1.1.5: Statistical validation
- [x] REQ-1.1.6: Backward compatibility

### Performance & Robustness (Recommended)
- [x] REQ-1.1.7: Performance benchmarks
- [x] REQ-1.1.8: Failure mode handling
- [x] REQ-1.1.9: Monitoring integration

### Documentation (Recommended)
- [x] REQ-1.1.10: Documentation updates
- [x] REQ-1.1.11: Production runbook

---

**Version**: 1.1
**Status**: APPROVED
**Next**: Implement tasks_v1.1.md
