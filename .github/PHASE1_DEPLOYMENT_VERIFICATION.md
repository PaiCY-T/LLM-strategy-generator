# Phase 1 Deployment Verification Guide

**Phase**: Configuration Priority Enforcement + Error Handling
**Duration**: Week 1 (2-4 days staging + 3-5 days production)
**Feature Flags**: `ENABLE_GENERATION_REFACTORING=true`, `PHASE1_CONFIG_ENFORCEMENT=true`
**Test Count**: 21 tests expected
**Risk Level**: Medium (core configuration logic changes)

---

## Pre-Deployment Verification

### 1. Test Suite Validation

**Command**:
```bash
cd /mnt/c/Users/jnpi/Documents/finlab/LLM-strategy-generator

# Enable Phase 1
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=true
export PHASE2_PYDANTIC_VALIDATION=false
export PHASE3_STRATEGY_PATTERN=false
export PHASE4_AUDIT_TRAIL=false

# Run Phase 1 tests
pytest tests/learning/test_iteration_executor_phase1.py -v
```

**Expected Results**:
```
✅ 21/21 tests passing
✅ Test duration: <30 seconds
✅ No warnings or errors
✅ All 4 configuration scenarios covered:
   - use_factor_graph=True (forces Factor Graph)
   - use_factor_graph=False (forces LLM)
   - use_factor_graph=None (mixed mode)
   - Configuration conflicts (explicit errors)
```

**Validation Checklist**:
- [ ] All 21 Phase 1 tests pass
- [ ] No regression in existing test suite (run `pytest tests/learning/ -v`)
- [ ] Configuration priority logic verified
- [ ] Error handling tests passing (all 4 fallback scenarios)

### 2. Code Quality Verification

**Type Checking**:
```bash
mypy src/learning/iteration_executor.py --ignore-missing-imports
```
Expected: `Success: no issues found`

**Complexity Check**:
```bash
radon cc src/learning/iteration_executor.py -a -nb
```
Expected: All functions <10 cyclomatic complexity

**Coverage Check**:
```bash
pytest tests/learning/test_iteration_executor_phase1.py \
  --cov=src/learning/iteration_executor \
  --cov-report=term \
  --cov-fail-under=95
```
Expected: >95% coverage

### 3. Baseline Metrics Collection

**Before deploying**, record baseline metrics:

```bash
# Run 100 iterations to establish baseline
python scripts/collect_baseline_metrics.py \
  --iterations 100 \
  --output baseline_phase0.json
```

**Metrics to Record**:
- [ ] Average iteration time (ms)
- [ ] Configuration adherence rate (should be ~80-90% before Phase 1)
- [ ] Silent fallback count (may be >0 before Phase 1)
- [ ] Error rate (%)
- [ ] Memory usage (MB)

---

## Staging Deployment Verification

### Stage 1: Deploy and Enable Phase 1

**Deployment Steps**:
```bash
# 1. Deploy code to staging
git checkout main
git pull origin main

# 2. Verify environment variables
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=true
export PHASE2_PYDANTIC_VALIDATION=false
export PHASE3_STRATEGY_PATTERN=false
export PHASE4_AUDIT_TRAIL=false

# 3. Restart application (method depends on infrastructure)
# Example for Docker:
# docker-compose restart learning-service

# 4. Verify application started
curl http://staging.example.com/health
# Expected: {"status": "healthy", "phase1_enabled": true}
```

**Verification Checklist**:
- [ ] Application started without errors
- [ ] Health check passes
- [ ] Phase 1 feature flag detected in logs
- [ ] No immediate crash or error spike

### Stage 2: Configuration Priority Testing

**Test 1: Force Factor Graph (use_factor_graph=True)**

```bash
# Run 10 iterations with Factor Graph forced
python scripts/test_configuration.py \
  --use-factor-graph true \
  --iterations 10 \
  --environment staging

# Expected behavior:
# - All 10 iterations use Factor Graph
# - No LLM calls detected in logs
# - Configuration priority: 100%
# - No silent fallbacks
```

**Validation**:
- [ ] All 10 iterations used Factor Graph
- [ ] Logs show: "Configuration: use_factor_graph=True (explicit)"
- [ ] No LLM strategy executions
- [ ] Average iteration time within acceptable range

**Test 2: Force LLM (use_factor_graph=False)**

```bash
# Run 10 iterations with LLM forced
python scripts/test_configuration.py \
  --use-factor-graph false \
  --iterations 10 \
  --environment staging

# Expected behavior:
# - All 10 iterations use LLM
# - No Factor Graph calls detected
# - Configuration priority: 100%
# - No silent fallbacks
```

**Validation**:
- [ ] All 10 iterations used LLM
- [ ] Logs show: "Configuration: use_factor_graph=False (explicit)"
- [ ] No Factor Graph strategy executions
- [ ] Average iteration time within acceptable range

**Test 3: Mixed Mode (use_factor_graph=None)**

```bash
# Run 20 iterations in mixed mode
python scripts/test_configuration.py \
  --use-factor-graph null \
  --iterations 20 \
  --environment staging

# Expected behavior:
# - Mix of Factor Graph and LLM based on innovation_rate
# - Probabilistic selection working correctly
# - Configuration priority: 100%
# - No silent fallbacks
```

**Validation**:
- [ ] Both strategies used (ratio depends on innovation_rate)
- [ ] Logs show: "Configuration: use_factor_graph=None (mixed mode)"
- [ ] Strategy selection follows innovation_rate probability
- [ ] No unexpected fallbacks

**Test 4: Configuration Conflict Detection**

```bash
# Attempt to set conflicting configuration
python scripts/test_configuration.py \
  --use-factor-graph true \
  --force-llm-fallback true \
  --environment staging

# Expected behavior:
# - Configuration validation fails at startup
# - Explicit error message raised
# - Application refuses to start with conflicting config
```

**Validation**:
- [ ] Configuration conflict detected
- [ ] Explicit error message: "Configuration conflict: use_factor_graph=True conflicts with force_llm_fallback=True"
- [ ] Application startup blocked
- [ ] No silent fallback to default behavior

### Stage 3: Error Handling Verification

**Test 5: Graceful Error Handling**

```bash
# Simulate various error scenarios
python scripts/test_error_handling.py \
  --scenarios all \
  --environment staging

# Scenarios to test:
# 1. LLM API timeout → explicit error, no silent fallback
# 2. Factor Graph validation failure → explicit error, clear message
# 3. Invalid configuration values → startup blocked
# 4. Missing required parameters → explicit error
```

**Validation**:
- [ ] All errors explicit and clear
- [ ] No silent fallbacks detected
- [ ] Error messages actionable
- [ ] Logs contain full context for debugging

### Stage 4: Load Testing (Staging)

**Run sustained load test**:
```bash
# Run 100 iterations to verify stability
python scripts/load_test.py \
  --iterations 100 \
  --concurrent 5 \
  --environment staging \
  --output staging_load_test.json

# Monitor for:
# - Memory leaks
# - Performance degradation
# - Error rate increase
# - Configuration drift
```

**Validation**:
- [ ] 100 iterations completed successfully
- [ ] Configuration priority maintained at 100%
- [ ] Zero silent fallbacks
- [ ] Memory usage stable
- [ ] Performance within acceptable range (±10% of baseline)

### Stage 5: Monitoring (24-48 hours)

**Metrics to Monitor**:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Configuration Priority Adherence | 100% | <100% |
| Silent Fallback Count | 0 | >0 |
| Error Rate | <1% | >1% |
| Average Iteration Time | ≤baseline × 1.1 | >baseline × 1.2 |
| Memory Usage | <500MB | >750MB |

**Daily Checks**:
```bash
# Day 1 and Day 2 - Run health check
python scripts/staging_health_check.py \
  --environment staging \
  --output staging_health_day{1,2}.json

# Review logs for:
# - Configuration violations (should be 0)
# - Silent fallbacks (should be 0)
# - Unexpected errors
# - Performance anomalies
```

**Validation Checklist**:
- [ ] 24 hours stable with no critical issues
- [ ] 48 hours stable with no critical issues
- [ ] All metrics within acceptable thresholds
- [ ] Zero configuration violations detected
- [ ] Zero silent fallbacks detected

---

## Production Deployment Verification

### Prerequisites

- [ ] Staging validation complete (24-48 hours stable)
- [ ] No critical issues found in staging
- [ ] Rollback plan tested in staging
- [ ] Team approval obtained
- [ ] Deployment window scheduled
- [ ] Stakeholder notification sent

### Production Deployment Steps

```bash
# 1. Deploy code to production
git checkout main
git pull origin main

# 2. Verify production environment
# DO NOT enable Phase 1 yet - deploy code first

# 3. Restart application with Phase 1 DISABLED
export ENABLE_GENERATION_REFACTORING=false  # Master kill switch OFF

# 4. Verify application health
curl https://production.example.com/health
# Expected: {"status": "healthy", "refactoring_enabled": false}
```

### Phase 1.1: Canary Deployment (10% Traffic)

**Enable Phase 1 for 10% of traffic**:
```bash
# Configure load balancer to route 10% traffic to Phase 1 instance
# Or use feature flag service with 10% rollout

# For Phase 1 instance(s):
export ENABLE_GENERATION_REFACTORING=true
export PHASE1_CONFIG_ENFORCEMENT=true

# Restart Phase 1 instances only
```

**Immediate Validation (First 1 hour)**:
```bash
# Monitor Phase 1 traffic closely
python scripts/production_monitor.py \
  --environment production \
  --phase1-traffic-percentage 10 \
  --interval 60 \
  --output prod_phase1_10pct_hour1.json
```

**Checks**:
- [ ] 10% traffic routed correctly
- [ ] Configuration priority working (100%)
- [ ] No silent fallbacks detected
- [ ] Error rate comparable to baseline (<1%)
- [ ] Performance within acceptable range (±10%)

**Day 1-2 Monitoring**:

| Metric | Baseline | Phase 1 (10%) | Status |
|--------|----------|---------------|--------|
| Configuration Priority | N/A | 100% | Monitor |
| Silent Fallbacks | N/A | 0 | Alert if >0 |
| Error Rate | X% | ≤X% × 1.1 | Alert if >1.1X |
| Avg Iteration Time | Xms | ≤Xms × 1.1 | Alert if >1.2X |

**Rollback Trigger Conditions** (10% phase):
- Error rate increase >50%
- Any silent fallbacks detected
- Configuration priority <100%
- Performance degradation >20%
- Critical bugs reported

### Phase 1.2: Increased Rollout (50% Traffic)

**Prerequisites**:
- [ ] 10% traffic stable for 24-48 hours
- [ ] No rollback triggers activated
- [ ] Metrics within acceptable thresholds

**Enable Phase 1 for 50% of traffic**:
```bash
# Configure load balancer for 50% traffic split

# Verify traffic distribution
python scripts/verify_traffic_split.py \
  --expected-percentage 50 \
  --environment production
```

**Day 3-4 Monitoring**:
- [ ] 50% traffic routed correctly
- [ ] Configuration priority maintained at 100%
- [ ] Zero silent fallbacks across all requests
- [ ] Error rate stable
- [ ] Performance comparable to baseline

**Validation Commands**:
```bash
# Run comprehensive validation
python scripts/production_validation.py \
  --phase1-percentage 50 \
  --duration-hours 24 \
  --output prod_phase1_50pct_validation.json

# Check for:
# - Configuration violations: 0 expected
# - Silent fallbacks: 0 expected
# - Error rate: within baseline ±10%
# - Performance: within baseline ±10%
```

### Phase 1.3: Full Rollout (100% Traffic)

**Prerequisites**:
- [ ] 50% traffic stable for 48 hours
- [ ] No rollback triggers activated
- [ ] Team confidence high

**Enable Phase 1 for 100% of traffic**:
```bash
# Route all traffic to Phase 1

# Verify all instances running Phase 1
python scripts/verify_all_instances.py \
  --expected-phase1 true \
  --environment production
```

**Day 5-7 Monitoring**:
- [ ] 100% traffic on Phase 1
- [ ] Configuration priority = 100% across all requests
- [ ] Zero silent fallbacks system-wide
- [ ] Error rate stable
- [ ] Performance stable

**Final Validation**:
```bash
# Run full regression test suite in production
pytest tests/learning/ -v --environment production

# Collect final metrics
python scripts/collect_production_metrics.py \
  --phase1 true \
  --duration-days 3 \
  --output prod_phase1_final_metrics.json
```

### Production Verification Checklist

- [ ] All production instances running Phase 1
- [ ] Configuration priority = 100%
- [ ] Silent fallback count = 0
- [ ] Error rate ≤ baseline
- [ ] Performance within baseline × 1.1
- [ ] Memory usage stable
- [ ] No configuration violations detected

---

## Rollback Verification

### Test Rollback Procedure (Staging First)

**Simulate rollback in staging**:
```bash
# IMMEDIATE ROLLBACK TEST
export ENABLE_GENERATION_REFACTORING=false

# Restart application
# Verify system reverts to legacy behavior

# Expected results:
# - Application starts successfully
# - Legacy behavior active (Phase 0)
# - No Phase 1 logic executing
# - Existing functionality intact
```

**Validation**:
- [ ] Rollback completes in <10 seconds
- [ ] Application starts successfully
- [ ] Legacy behavior confirmed
- [ ] No data loss or corruption
- [ ] All existing tests pass

### Production Rollback Triggers

**Critical Issues** (Immediate Rollback):
- Silent fallbacks detected (should NEVER happen)
- Configuration priority violations
- Error rate spike >50%
- Critical production bug
- Data corruption detected

**Warning Issues** (Evaluate for Rollback):
- Error rate increase >20%
- Performance degradation >20%
- Configuration adherence <100%
- Memory leak detected
- User-reported issues

### Rollback Execution (Production)

```bash
# EMERGENCY ROLLBACK (if critical issue detected)
export ENABLE_GENERATION_REFACTORING=false

# Restart all production instances
# (restart command depends on infrastructure)

# Verify rollback success
python scripts/verify_rollback.py \
  --environment production \
  --expected-phase 0
```

**Post-Rollback Validation**:
- [ ] All instances reverted to Phase 0
- [ ] Error rates normalized
- [ ] Performance restored to baseline
- [ ] Configuration correctness verified
- [ ] Logs reviewed for root cause

---

## Success Criteria

### Phase 1 Deployment Success Defined As:

**Staging Success**:
- [x] 21/21 Phase 1 tests passing
- [x] 24-48 hours stable operation
- [x] Configuration priority = 100%
- [x] Silent fallback count = 0
- [x] No critical issues detected

**Production Success**:
- [x] 10% rollout stable for 24-48 hours
- [x] 50% rollout stable for 48 hours
- [x] 100% rollout stable for 3-5 days
- [x] Configuration priority = 100% system-wide
- [x] Zero silent fallbacks across all requests
- [x] Error rate ≤ baseline
- [x] Performance within baseline × 1.1
- [x] Zero configuration violations
- [x] Rollback tested and verified

### Key Performance Indicators

| KPI | Target | Status |
|-----|--------|--------|
| Configuration Priority Adherence | 100% | ✅ Track |
| Silent Fallback Count | 0 | ✅ Track |
| Error Rate | ≤baseline | ✅ Track |
| Average Iteration Time | ≤baseline × 1.1 | ✅ Track |
| Test Pass Rate | 100% (21/21) | ✅ Track |
| Code Coverage | >95% | ✅ Track |
| Rollback Time | <10 seconds | ✅ Track |

---

## Post-Deployment Review

### Week 1 Retrospective

**Questions to Answer**:
1. Did Phase 1 deployment meet all success criteria?
2. Were there any unexpected issues or behaviors?
3. How did actual deployment duration compare to plan?
4. What lessons were learned for Phase 2-4 deployments?
5. Are there any improvements needed to the deployment process?

**Documentation Required**:
- [ ] Final metrics report (staging + production)
- [ ] Issues encountered and resolutions
- [ ] Rollback test results
- [ ] Performance benchmark comparison
- [ ] Lessons learned document

### Ready for Phase 2?

**Prerequisites for Phase 2 Deployment**:
- [ ] Phase 1 stable in production for 1+ week
- [ ] No outstanding Phase 1 issues
- [ ] Configuration priority = 100% consistently
- [ ] Zero silent fallbacks confirmed
- [ ] Team approval for Phase 2
- [ ] Phase 2 tests ready (41/41 expected)

---

## Troubleshooting Guide

### Issue: Configuration Priority <100%

**Symptoms**:
- Logs show unexpected strategy selection
- Configuration not being respected

**Investigation**:
```bash
# Check configuration loading
grep "Configuration loaded" /var/log/learning-service.log

# Verify environment variables
env | grep PHASE

# Review configuration validation logic
```

**Resolution**:
- Verify feature flags set correctly
- Check configuration parsing logic
- Review logs for configuration conflicts

### Issue: Silent Fallbacks Detected

**THIS SHOULD NEVER HAPPEN IN PHASE 1**

**Immediate Actions**:
1. Trigger rollback immediately
2. Collect all logs and error details
3. Review configuration priority logic
4. File critical bug report

**Investigation**:
```bash
# Search logs for fallback indicators
grep -i "fallback" /var/log/learning-service.log
grep -i "default" /var/log/learning-service.log

# Review configuration enforcement code
```

### Issue: Performance Degradation >10%

**Investigation**:
```bash
# Profile iteration execution
python scripts/profile_iteration.py \
  --environment staging \
  --iterations 100

# Compare with baseline
python scripts/compare_performance.py \
  --baseline baseline_phase0.json \
  --current current_phase1.json
```

**Common Causes**:
- Configuration validation overhead
- Additional logging
- Error handling overhead

**Resolution**:
- Review configuration validation performance
- Optimize hot paths
- Consider caching configuration decisions

### Issue: Error Rate Increase >10%

**Investigation**:
```bash
# Analyze error patterns
python scripts/analyze_errors.py \
  --log-file /var/log/learning-service.log \
  --output error_analysis.json

# Compare error types with baseline
```

**Common Causes**:
- Configuration validation too strict
- New error handling revealing existing issues
- Integration problems

**Resolution**:
- Review error logs for patterns
- Verify configuration validation logic
- Consider if errors were previously silently swallowed

---

## Contacts and Escalation

**Technical Lead**: [TBD]
**QA Lead**: [TBD]
**DevOps Lead**: [TBD]
**Product Owner**: [TBD]

**Escalation Path**:
1. Monitor alerts → Technical Lead
2. Critical issues → QA Lead + DevOps Lead
3. Production incidents → Product Owner notification

---

**Document Version**: 1.0
**Last Updated**: 2025-11-11
**Related Documents**:
- `.github/DEPLOYMENT_CHECKLIST.md` (Overall deployment strategy)
- `.github/workflows/architecture-refactoring.yml` (CI/CD pipeline)
- `.github/BRANCH_PROTECTION.md` (Branch protection rules)
- `.spec-workflow/specs/architecture-contradictions-fix/PHASE1_COMPLETION_SUMMARY.md` (Phase 1 completion status)
