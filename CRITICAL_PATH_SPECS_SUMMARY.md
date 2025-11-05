# Critical Path Specs - 5-Week Implementation Roadmap

**Created**: 2025-10-24
**Based on**: EXECUTIVE_SUMMARY_DEEP_ANALYSIS.md + CRITICAL_BASELINE_REVIEW_O3.md + LLM_INNOVATION_COMPREHENSIVE_REVIEW.md
**Goal**: Production-ready LLM Innovation System (7.5/10 → 9.0/10)
**Timeline**: 5 weeks to Task 3.5 (100-generation LLM test)

---

## 🎯 Executive Summary

This document outlines **5 new specs** created to address critical gaps identified in the comprehensive system review. These specs form a **critical path** to production readiness, with clear dependencies and timeline.

### Current State vs Target:
```
Task 0.1 Baseline:      7.5/10 ✅ APPROVED (valid for comparison)
Current System:         6.2/10 ⚠️ NOT PRODUCTION READY
After 5-Week Plan:      9.0/10 ✅ PRODUCTION READY
```

### Critical Finding:
**Task 0.1 baseline is VALID** - All 3 O3-identified issues resolved (2 were design features, 1 is known limitation). System ready for baseline comparison but NOT ready for 100-gen LLM test without security hardening.

---

## 📊 The 5 Critical Path Specs

### 1. docker-sandbox-security (CRITICAL)
**Priority**: HIGHEST - BLOCKING
**Timeline**: 8-12 days (Week 1)
**Effort**: High
**Risk Level**: CRITICAL

**Purpose**: Implement Docker-based isolated execution environment for LLM-generated code

**Key Requirements**:
- Docker container isolation (python:3.9-slim)
- Resource limits: 2GB memory, 0.5 CPU
- Network isolation (network_disabled=True)
- Read-only filesystem
- Security controls: seccomp profiles, AppArmor
- Timeout enforcement (300s max)

**Threat Mitigation**:
- ✅ Code injection attacks
- ✅ Resource exhaustion (memory bombs, CPU DoS)
- ✅ Sandbox escape attempts
- ✅ Network-based attacks
- ✅ Filesystem manipulation

**Success Criteria**:
- [ ] All LLM-generated code executes in isolated containers
- [ ] Resource limits enforced (validated with stress tests)
- [ ] Zero network access from sandbox
- [ ] Filesystem immutability verified
- [ ] Comprehensive error handling and cleanup

**Dependencies**: None (start immediately)
**Blocks**: llm-integration-activation, structured-innovation-mvp

---

### 2. resource-monitoring-system (HIGH)
**Priority**: HIGH
**Timeline**: 2-3 days (Week 1)
**Effort**: Medium
**Risk Level**: HIGH

**Purpose**: Implement comprehensive resource monitoring with Prometheus metrics and Grafana dashboards

**Key Requirements**:
- Prometheus metrics exporter
  - Memory usage (RSS, VMS, swap)
  - CPU utilization (per-process, system-wide)
  - Container-level stats (if Docker available)
  - Diversity metrics (real-time)
  - Innovation success rate
- Grafana dashboard templates
  - Evolution progress visualization
  - Resource utilization graphs
  - Alert history timeline
- Alerting system
  - Memory > 80% threshold
  - Diversity < 0.1 (severe collapse)
  - Orphaned process detection
  - Container escape attempts
- Process cleanup mechanism
  - Orphaned process termination
  - Zombie process reaping
  - Resource leak detection

**Current Gap**: 6+ orphaned validation processes detected, no monitoring/cleanup

**Success Criteria**:
- [ ] Prometheus metrics endpoint active (http://localhost:9090/metrics)
- [ ] Grafana dashboard deployed with 5+ panels
- [ ] Alerts triggered successfully on test violations
- [ ] Orphaned process count = 0 after cleanup run
- [ ] Production stability validated (24h continuous run)

**Dependencies**: None (parallel with docker-sandbox-security)
**Blocks**: None (but highly recommended for all long runs)

---

### 3. llm-integration-activation (HIGH)
**Priority**: HIGH
**Timeline**: 1-2 days (Week 2)
**Effort**: Low-Medium
**Risk Level**: MEDIUM

**Purpose**: Connect InnovationEngine to iteration loop with 20% innovation rate

**Key Requirements**:
- API key configuration
  - OpenRouter API (primary)
  - Gemini API (fallback)
  - OpenAI API (optional)
  - Secure key storage (.env file, not in repo)
- Innovation pipeline connection
  - Integrate InnovationEngine into evolve_generation()
  - Set innovation_rate = 0.2 (20% of population)
  - Implement selection logic (which strategies to innovate)
- Feedback loop implementation
  - Success/failure tracking
  - Pattern extraction from successful innovations
  - Adaptive explorer integration
- Prompt engineering
  - Strategy modification vs creation decision logic
  - Context injection (performance history, diversity state)
  - Error handling for invalid responses
- Fallback mechanism
  - LLM failure → Factor Graph mutation
  - API rate limit → queue management
  - Invalid response → regeneration with stricter prompt

**Current Gap**: All components exist but not activated (0 LLM calls in baseline test)

**Success Criteria**:
- [ ] API keys configured and tested (all 3 providers)
- [ ] 20% innovation rate achieved in test run (4/20 strategies)
- [ ] InnovationEngine successfully generates valid strategies
- [ ] Feedback loop captures successful patterns
- [ ] Fallback mechanism tested (simulated LLM failure)
- [ ] Zero API key leaks (security audit)

**Dependencies**: docker-sandbox-security (MUST complete first)
**Blocks**: structured-innovation-mvp

---

### 4. exit-mutation-redesign (MEDIUM)
**Priority**: MEDIUM
**Timeline**: 3-5 days (Week 2-3)
**Effort**: Medium
**Risk Level**: LOW (isolated component)

**Purpose**: Redesign exit mutation from AST-based to parameter-based genetic operators

**Current Issue**: 0/41 success rate (100% failure) - operates on placeholder code

**Root Cause Analysis**:
- Current approach: AST mutation on placeholder code strings
- Problem: Placeholder code has no exit mechanisms to analyze
- Real exit logic: In template-generated code (runtime)
- Wrong abstraction level: Should mutate parameters, not code

**New Design - Parameter-Based Mutation**:
```python
# Old (BROKEN): AST mutation on code strings
code = "# Placeholder code..."
mutated_code = ast_mutate(code)  # ❌ Fails - no exit mechanisms

# New (CORRECT): Parameter mutation
parameters = {
    'stop_loss_pct': 0.05,
    'take_profit_pct': 0.10,
    'trailing_stop_offset': 0.02
}
mutated_params = {
    'stop_loss_pct': gaussian_noise(0.05, sigma=0.01, bounds=(0.01, 0.15)),
    'take_profit_pct': gaussian_noise(0.10, sigma=0.02, bounds=(0.05, 0.30)),
    'trailing_stop_offset': gaussian_noise(0.02, sigma=0.005, bounds=(0.005, 0.05))
}
```

**Implementation Details**:
- Gaussian noise mutation (mean=current, sigma=configurable)
- Bounded ranges (prevent invalid values)
- Validation before mutation
- Mutation rate tuning (adaptive based on success rate)

**Success Criteria**:
- [ ] Parameter-based mutation implemented for all exit strategies
- [ ] Success rate > 50% (vs current 0%)
- [ ] Generated parameters within valid ranges (100% compliance)
- [ ] Performance improvement vs baseline (A/B test)
- [ ] Integration with existing evolution pipeline

**Dependencies**: None (isolated refactor)
**Blocks**: None (quality improvement, not blocking)

---

### 5. structured-innovation-mvp (MEDIUM)
**Priority**: MEDIUM
**Timeline**: 2-3 weeks (Week 3-4)
**Effort**: High
**Risk Level**: MEDIUM

**Purpose**: Implement YAML/JSON-based structured innovation (Phase 2a)

**Rationale**:
- **Lower risk** than full code generation (Phase 2b)
- **Covers 85%** of innovation needs
- **Reduced hallucination** risk (structured schema)
- **Easier validation** (schema-based checks)

**Schema Design**:
```yaml
innovation:
  type: "factor_combination"  # vs "full_code"
  metadata:
    name: "Novel Momentum-Value Hybrid"
    description: "Combines momentum with value factors"
    category: "hybrid"

  indicators:
    - name: "momentum_score"
      type: "technical"
      calculation: "close.pct_change(20).rank()"
    - name: "value_score"
      type: "fundamental"
      calculation: "eps / price"

  entry_conditions:
    logic: "AND"
    conditions:
      - indicator: "momentum_score"
        operator: ">"
        threshold: 0.7
      - indicator: "value_score"
        operator: ">"
        threshold: 0.5

  exit_conditions:
    stop_loss_pct: 0.05
    take_profit_pct: 0.15
    trailing_stop: true
    trailing_offset: 0.02

  position_sizing:
    method: "equal_weight"  # or "risk_parity", "kelly"
    max_position_size: 0.1

  risk_management:
    max_drawdown: 0.15
    max_correlation: 0.7
```

**LLM Task**: Generate YAML, not Python code
- **Pros**: Structured output, easier validation, no syntax errors
- **Cons**: Limited to schema-defined operations

**Implementation Phases**:
1. **Schema Definition** (3-4 days)
   - YAML schema design
   - JSON schema validation
   - Error message templates
2. **LLM Prompt Engineering** (2-3 days)
   - YAML generation prompts
   - Few-shot examples
   - Constraint enforcement
3. **Validator Implementation** (5-7 days)
   - Schema validation
   - Semantic checks (e.g., threshold ranges)
   - Novelty detection (vs existing strategies)
4. **Code Generator** (5-7 days)
   - YAML → Python strategy code
   - Template-based generation
   - Integration with existing templates
5. **Testing & Iteration** (5-7 days)
   - 20-generation test with structured innovation
   - A/B test vs Factor Graph mutation
   - Success rate analysis

**Success Criteria**:
- [ ] YAML schema defined and documented
- [ ] LLM generates valid YAML (>80% success rate)
- [ ] Schema validator catches all invalid specs
- [ ] Code generator produces runnable strategies (100% success)
- [ ] 20-gen test shows innovation diversity > 0.3
- [ ] At least 5 novel factor combinations discovered
- [ ] Performance competitive with baseline (Sharpe ≥ 1.145)

**Dependencies**: llm-integration-activation (MUST complete first)
**Blocks**: Task 3.5 (100-generation final test)

---

## 🔄 Dependency Graph

```
Week 1: Security & Monitoring Foundation
  ┌─────────────────────────────┐
  │ docker-sandbox-security (1) │ ◄── START HERE (CRITICAL)
  │      8-12 days              │
  └──────────────┬──────────────┘
                 │
                 │ BLOCKS
                 ▼
Week 2: Integration & Mutation      ┌────────────────────────────┐
  ┌─────────────────────────────┐   │ resource-monitoring (2)    │
  │ llm-integration-activation  │   │      2-3 days              │
  │ (3)  1-2 days               │   └────────────────────────────┘
  └──────────────┬──────────────┘   (parallel, no dependencies)
                 │
                 │ BLOCKS          ┌────────────────────────────┐
                 ▼                 │ exit-mutation-redesign (4) │
Week 3-4: Structured Innovation     │      3-5 days              │
  ┌─────────────────────────────┐   └────────────────────────────┘
  │ structured-innovation-mvp   │   (parallel, quality improvement)
  │ (5)  2-3 weeks              │
  └──────────────┬──────────────┘
                 │
                 │ ENABLES
                 ▼
Week 5: Production Readiness
  ┌─────────────────────────────┐
  │ Task 3.5: 100-gen LLM Test  │
  │  (Final Validation)         │
  └─────────────────────────────┘
```

### Critical Path (Longest Chain):
```
docker-sandbox (12d) → llm-integration (2d) → structured-innovation (21d) → Task 3.5
= 35 days (~5 weeks)
```

### Parallel Work Opportunities:
- **Week 1**: docker-sandbox + resource-monitoring (parallel)
- **Week 2-3**: llm-integration → structured-innovation (sequential), exit-mutation (parallel)

---

## 📅 Week-by-Week Breakdown

### Week 1: Security Hardening (Days 1-7)
**Goal**: Production-ready execution environment

**Tasks**:
- [ ] Day 1-3: Docker sandbox implementation
  - Container creation logic
  - Resource limit enforcement
  - Security profile configuration
- [ ] Day 2-4: Resource monitoring setup (parallel)
  - Prometheus exporter
  - Grafana dashboard
  - Alert rules
- [ ] Day 4-7: Docker sandbox completion
  - Error handling
  - Process cleanup
  - Integration testing
- [ ] Day 7: Week 1 validation
  - Security audit
  - Stress testing (memory/CPU bombs)
  - Orphaned process cleanup verification

**Deliverables**:
- ✅ Docker sandbox operational
- ✅ Monitoring stack deployed
- ✅ Security validated (no escapes)
- ✅ All orphaned processes cleaned

**Success Metrics**:
- Docker isolation: 100% (all code in containers)
- Resource violations: 0 (enforced limits)
- Monitoring uptime: 100%
- Orphaned processes: 0

---

### Week 2: Integration & Activation (Days 8-14)
**Goal**: LLM innovation pipeline operational

**Tasks**:
- [ ] Day 8-9: LLM integration activation
  - API key configuration
  - InnovationEngine connection
  - 20% innovation rate implementation
- [ ] Day 10-11: Feedback loop implementation
  - Success tracking
  - Pattern extraction
  - Adaptive explorer integration
- [ ] Day 11-14: Exit mutation redesign (parallel)
  - Parameter-based mutation design
  - Gaussian noise implementation
  - Bounded range validation
- [ ] Day 14: Week 2 validation
  - 5-gen test with LLM innovations
  - Exit mutation A/B test
  - Fallback mechanism test

**Deliverables**:
- ✅ LLM integration active (20% rate)
- ✅ Exit mutation redesigned (>50% success)
- ✅ 5-gen test complete with innovations

**Success Metrics**:
- LLM call success rate: >80%
- Innovation rate: 20% (4/20 strategies)
- Exit mutation success: >50% (vs 0%)
- API failures handled: 100%

---

### Week 3-4: Structured Innovation MVP (Days 15-28)
**Goal**: YAML-based innovation operational

**Tasks**:
- [ ] Day 15-18: Schema design & validation
  - YAML schema definition
  - JSON schema validator
  - Error templates
- [ ] Day 19-21: LLM prompt engineering
  - YAML generation prompts
  - Few-shot examples
  - Constraint enforcement
- [ ] Day 22-28: Code generator & testing
  - YAML → Python converter
  - Template integration
  - 20-gen validation test
- [ ] Day 28: Week 3-4 validation
  - 20-gen test with structured innovation
  - Diversity analysis (target >0.3)
  - Novel factor discovery (target ≥5)

**Deliverables**:
- ✅ YAML schema documented
- ✅ LLM generates valid YAML (>80%)
- ✅ Code generator operational
- ✅ 20-gen test shows diversity >0.3

**Success Metrics**:
- YAML validation success: >80%
- Code generation success: 100%
- Diversity improvement: >0.3 (vs 0.104 baseline)
- Novel factors: ≥5 unique combinations

---

### Week 5: Production Readiness (Days 29-35)
**Goal**: Final validation and deployment

**Tasks**:
- [ ] Day 29-30: Walk-forward validation integration
  - Multi-regime testing
  - Out-of-sample validation
  - Robustness checks
- [ ] Day 31-32: Monitoring stack deployment
  - Production Prometheus setup
  - Grafana alerts configuration
  - Runbook documentation
- [ ] Day 33: Security audit
  - Penetration testing
  - Code review
  - Threat model validation
- [ ] Day 34-35: 100-generation final test (Task 3.5)
  - Full LLM innovation enabled
  - Comprehensive monitoring
  - Performance comparison vs baseline

**Deliverables**:
- ✅ Walk-forward validation active
- ✅ Production monitoring deployed
- ✅ Security audit passed
- ✅ 100-gen test complete

**Success Metrics**:
- Best Sharpe: ≥1.374 (+20% vs baseline 1.145)
- Innovations: ≥20 novel factors
- Champion updates: >10% (vs 0% baseline)
- Diversity: >0.3 (vs 0.104 baseline)
- System stability: Zero crashes
- Security incidents: Zero

---

## 🎯 Success Metrics by Component

### docker-sandbox-security
| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Isolation rate | 100% | All code runs in containers |
| Resource enforcement | 100% | Stress test with memory/CPU bombs |
| Escape attempts blocked | 100% | Penetration testing |
| Network access | 0% | Network monitoring |
| Cleanup success | 100% | Zero orphaned containers |

### resource-monitoring-system
| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Monitoring uptime | 99.9% | Prometheus availability |
| Alert accuracy | >95% | False positive rate <5% |
| Orphaned processes | 0 | Process cleanup validation |
| Metrics coverage | 100% | All critical metrics tracked |
| Dashboard latency | <5s | User experience testing |

### llm-integration-activation
| Metric | Target | Validation Method |
|--------|--------|-------------------|
| API call success | >80% | Success/failure tracking |
| Innovation rate | 20% | 4/20 strategies in test |
| Fallback activation | 100% | Simulated API failures |
| API key security | 100% | Security audit (no leaks) |
| Response validation | >90% | 7-layer validator pass rate |

### exit-mutation-redesign
| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Success rate | >50% | vs 0% baseline |
| Parameter validity | 100% | All values within bounds |
| Performance improvement | ≥baseline | A/B test comparison |
| Mutation diversity | >0.2 | Parameter space coverage |
| Integration compatibility | 100% | Zero breaking changes |

### structured-innovation-mvp
| Metric | Target | Validation Method |
|--------|--------|-------------------|
| YAML generation success | >80% | Schema validation pass rate |
| Code generation success | 100% | All YAML → runnable Python |
| Diversity improvement | >0.3 | vs 0.104 baseline |
| Novel factors discovered | ≥5 | Novelty detector count |
| Performance competitive | ≥1.145 | Sharpe ratio comparison |

---

## ⚠️ Risk Mitigation

### High-Risk Items:

**1. Docker Sandbox Escape**
- **Risk**: Container breakout, privilege escalation
- **Mitigation**:
  - Seccomp profiles (syscall restrictions)
  - AppArmor/SELinux enforcement
  - Read-only filesystem
  - Non-root user execution
  - Regular security audits
- **Fallback**: Immediate shutdown on suspicious activity

**2. LLM Hallucination**
- **Risk**: Invalid strategies, look-ahead bias, overfitting
- **Mitigation**:
  - 7-layer validation (all layers enforced)
  - Walk-forward testing (multiple regimes)
  - Structured innovation (schema constraints)
  - Human review for production deployment
- **Fallback**: Factor Graph mutation (proven safe)

**3. Resource Exhaustion**
- **Risk**: Memory leaks, CPU DoS, storage overflow
- **Mitigation**:
  - Hard limits (2GB mem, 0.5 CPU, 300s timeout)
  - Monitoring with alerts (>80% threshold)
  - Process cleanup automation
  - Storage quotas
- **Fallback**: Automatic process termination

### Medium-Risk Items:

**4. API Rate Limits**
- **Risk**: LLM provider throttling, cost overruns
- **Mitigation**:
  - Multi-provider fallback (OpenRouter → Gemini → OpenAI)
  - Request queueing
  - Cost monitoring
  - Rate limit awareness
- **Fallback**: Reduce innovation rate temporarily

**5. Integration Bugs**
- **Risk**: Pipeline failures, data corruption
- **Mitigation**:
  - Comprehensive testing (unit, integration, E2E)
  - Checkpoint validation
  - Rollback capability
  - Staged rollout (5-gen → 20-gen → 100-gen)
- **Fallback**: Revert to baseline system

---

## 📈 Production Readiness Scorecard

### Current State (Oct 24, 2025):
| Component | Score | Status |
|-----------|-------|--------|
| Core Evolution | 8/10 | ✅ Stable, bug-free |
| Data Integrity | 10/10 | ✅ All bugs fixed |
| Innovation Pipeline | 6/10 | ⚠️ Not activated |
| Validation Framework | 7/10 | ⚠️ Sandbox weak |
| Safety/Security | 3/10 | ❌ CRITICAL gap |
| Monitoring | 5/10 | ⚠️ Basic logging only |
| **Overall** | **6.2/10** | ⚠️ **NOT READY** |

### After Week 1 (Security Hardening):
| Component | Score | Status |
|-----------|-------|--------|
| Safety/Security | 8/10 | ✅ Docker sandbox |
| Monitoring | 8/10 | ✅ Full stack |
| **Overall** | **7.5/10** | ⚠️ **Basic Safety** |

### After Week 2 (Integration):
| Component | Score | Status |
|-----------|-------|--------|
| Innovation Pipeline | 8/10 | ✅ LLM active |
| **Overall** | **8.0/10** | ✅ **Functional** |

### After Week 4 (Structured Innovation):
| Component | Score | Status |
|-----------|-------|--------|
| Innovation Pipeline | 9/10 | ✅ YAML MVP |
| Validation Framework | 8/10 | ✅ Comprehensive |
| **Overall** | **8.5/10** | ✅ **Validated** |

### After Week 5 (Production):
| Component | Score | Status |
|-----------|-------|--------|
| All Components | 9/10 | ✅ Production ready |
| **Overall** | **9.0/10** | ✅ **PRODUCTION READY** |

---

## 🚀 Next Steps

### Immediate (This Week):
1. **Execute create_critical_path_specs.sh** to create all 5 specs
   ```bash
   chmod +x create_critical_path_specs.sh
   ./create_critical_path_specs.sh
   ```

2. **Review generated specs** in .spec-workflow/specs/
   - docker-sandbox-security/
   - resource-monitoring-system/
   - llm-integration-activation/
   - exit-mutation-redesign/
   - structured-innovation-mvp/

3. **Update STATUS.md** with:
   - Task 0.1 APPROVED status
   - 5-week critical path
   - Production readiness scorecard

4. **Kill orphaned processes** (6+ background validation runs)
   ```bash
   pkill -f "run_20generation_validation.py"
   ```

### Week 1 Priority:
1. Start docker-sandbox-security implementation (CRITICAL)
2. Setup resource-monitoring-system (parallel)
3. Daily security reviews
4. End-of-week validation

### Long-term (Weeks 2-5):
Follow the week-by-week breakdown above, ensuring:
- Dependencies respected (no jumping ahead)
- Success metrics validated (each week)
- Risk mitigation in place (before production)
- Comprehensive testing (staged rollout)

---

## 📞 Stakeholder Communication

### For Management:
- **Good News**: Task 0.1 baseline VALID (7.5/10), ready for comparison
- **Timeline**: 5 weeks to production-ready LLM innovation
- **Investment**: ~35 days of focused development
- **ROI**: 20%+ performance improvement, novel factor discovery
- **Risk**: Managed with staged rollout and comprehensive validation

### For Development Team:
- **Clear Roadmap**: 5 specs with dependencies and timeline
- **Parallel Work**: Week 1 offers parallel opportunities
- **Critical Path**: Focus on docker-sandbox first (blocking)
- **Testing Strategy**: Staged (5-gen → 20-gen → 100-gen)
- **Documentation**: Each spec has detailed requirements.md and tasks.md

### For QA/Security:
- **Security Audit**: End of Week 1 and Week 5
- **Penetration Testing**: Docker sandbox (Week 1)
- **Validation Testing**: Each week has validation checkpoint
- **Monitoring**: Comprehensive metrics from Week 1 onwards
- **Rollback Plan**: Checkpoint system enables instant rollback

---

**Created**: 2025-10-24
**Author**: Based on zen:thinkdeep analysis (Gemini 2.5 Flash) + Expert Validation
**Status**: READY FOR EXECUTION
**Next Action**: Run create_critical_path_specs.sh to create all 5 specs

**Timeline to Production**: 5 weeks (35 days)
**Confidence Level**: VERY HIGH (95%+)
**Risk Level**: MANAGED (comprehensive mitigation in place)

---

## 📎 Reference Documents

1. **EXECUTIVE_SUMMARY_DEEP_ANALYSIS.md** - Concise findings and recommendations
2. **DEEP_ANALYSIS_FINAL_REPORT.md** - Complete 12,000+ word analysis
3. **CRITICAL_BASELINE_REVIEW_O3.md** - O3 review identifying 3 issues
4. **LLM_INNOVATION_COMPREHENSIVE_REVIEW.md** - Comprehensive neutral review
5. **THIRD_ROUND_AUDIT_REPORT.md** - Final validation of Task 0.1

**All findings synthesized into this critical path roadmap.**
