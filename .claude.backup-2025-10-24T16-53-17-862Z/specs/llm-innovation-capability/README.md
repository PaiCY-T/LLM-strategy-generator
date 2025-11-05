# LLM Innovation Capability Spec

**Created**: 2025-10-23
**Status**: ✅ **APPROVED - READY TO START**
**Timeline**: 12 weeks
**Confidence**: 8/10

---

## 📋 Quick Links

- [STATUS.md](STATUS.md) - Current implementation status
- [PROPOSAL.md](PROPOSAL.md) - Original proposal
- [CONSENSUS_REVIEW.md](CONSENSUS_REVIEW.md) - Expert consensus (o3 + Gemini 2.5 Pro)
- [EXECUTIVE_APPROVAL.md](EXECUTIVE_APPROVAL.md) - Final approval (Opus 4.1)

---

## 🎯 Spec Purpose

Enable LLM to create novel trading strategy factors and exit mechanisms beyond the current fixed pool of 13 factors.

**Current Limitation**: System can only recombine 13 predefined factors
**Proposed Solution**: LLM generates new factors with 7-layer validation
**Expected Outcome**: ≥20 novel innovations, statistically significant performance improvement

---

## ✅ Approval Status

### Expert Review Summary

| Reviewer | Model | Stance | Verdict | Confidence |
|----------|-------|--------|---------|------------|
| Review 1 | OpenAI o3 | Supportive | ✅ Approve with modifications | High |
| Review 2 | Gemini 2.5 Pro | Critical | ✅ Approve with modifications | High |
| **Final** | **Claude Opus 4.1** | **Executive** | **✅ APPROVED WITH CONDITIONS** | **8/10** |

**Consensus**: **UNANIMOUS APPROVAL** with modifications

---

## 🔑 Key Modifications from Original Proposal

### 1. Validation Framework: 5-layer → **7-layer**
- ✅ Added Layer 0: Static Safety & Financial Analysis
- ✅ Added Layer 3.5: Semantic Equivalence Check
- ✅ Added Layer 6: Overfitting Check + Explainability

### 2. Performance Thresholds: Static → **Adaptive**
- ❌ OLD: Sharpe >0.3, MDD <50%
- ✅ NEW: Sharpe ≥baseline×1.2, MDD ≤25%
- ✅ NEW: Multi-metric (Sharpe, Sortino, Calmar, MDD, turnover)
- ✅ NEW: Regime-specific (must pass 2008 GFC, 2020 COVID tests)

### 3. Timeline: 9 weeks → **12 weeks**
- Week 1-2: Risk mitigation infrastructure
- Week 3-5: Core validation (7-layer)
- Week 6-7: Innovation engine
- Week 8-11: Evolutionary features
- Week 12: Final validation

### 4. Data Strategy: Single set → **Three-set partition**
- **Training** (1990-2010): Layer 4 validation
- **Validation** (2011-2018): Evolutionary fitness
- **Final Hold-Out** (2019-2025): NEVER touched until Week 12

### 5. Success Criteria: Fixed 20% → **Statistical significance**
- ❌ OLD: ≥20% performance improvement
- ✅ NEW: Statistically significant (p <0.05) + positive on hold-out set

### 6. Innovation Rate: 20% → **15% with refined adaptive logic**
- Stagnation → Increase to 40% (explore)
- Breakthrough → Decrease to 5% (exploit)
- Stable → Maintain 15%

---

## 🔴 Three Mandatory Conditions

### Condition 1: Pre-Implementation Audit (Before Week 1)
- [ ] Document EXACT data splits with timestamps
- [ ] Lock hold-out set with cryptographic hash
- [ ] Create immutable baseline metrics
- [ ] Establish statistical test protocols

**Deliverable**: `DATA_AUDIT_REPORT.md`

### Condition 2: Kill Switch Implementation (Week 1)
- [ ] Auto-halt if validation rate <15%
- [ ] Auto-halt if complexity trend >150%
- [ ] Auto-halt if diversity <0.2
- [ ] Auto-halt if 10 consecutive failures

**Deliverable**: `src/innovation/kill_switch.py`

### Condition 3: Weekly Executive Checkpoints
- [ ] Week 2: Data partition validation (GO/NO-GO)
- [ ] Week 5: Validation rate >30% required (GO/NO-GO)
- [ ] Week 7: Semantic novelty confirmed (GO/NO-GO)
- [ ] Week 10: Pattern extraction value (GO/NO-GO)

---

## 🚨 Critical Risks & Mitigations

### Risk 1: Meta-Overfitting (HIGHEST PRIORITY)
**Risk**: Evolutionary process overfits to historical data
**Mitigation**: Three-set data partition + complexity penalty

### Risk 2: Innovation Feedback Loop (NEW - identified by Opus)
**Risk**: LLM creates echo chamber by seeing its own innovations
**Mitigation**: Innovation context manager (limit historical context)

### Risk 3: LLM Hallucinations
**Risk**: LLM generates invalid/broken code
**Mitigation**: 7-layer validation with sandbox execution

### Risk 4: Semantic Equivalence Gaming
**Risk**: LLM games novelty check with syntactic variations
**Mitigation**: AST-based semantic equivalence checker (Layer 3.5)

---

## 📊 Implementation Phases

### Phase 0: Baseline (Week 1)
**Goal**: Establish performance benchmark
- Task 0.1: 20-generation baseline test
- Measure: Sharpe, MDD, factor usage, parameter ranges
- Document: Evolution paths and limitations

### Phase 2: Innovation MVP (Week 2-7)
**Goal**: Enable basic innovation capability
- Task 2.1: Enhanced Prompt Template (2 days)
- Task 2.2: InnovationValidator 7-layer (5 days)
- Task 2.3: InnovationRepository (3 days)
- Task 2.4: Integration (2 days)
- Task 2.5: 20-gen smoke test (1 day)

### Phase 3: Evolutionary Innovation (Week 8-11)
**Goal**: Add intelligent exploration
- Task 3.1: Pattern Extraction (5 days)
- Task 3.2: Diversity Rewards (3 days)
- Task 3.3: Innovation Lineage (3 days)
- Task 3.4: Adaptive Exploration (4 days)

### Phase 3: Final Validation (Week 12)
**Goal**: Full-scale validation
- Task 3.5: 100-generation final test
- Hold-out set validation
- Statistical significance testing

---

## 🎯 Success Criteria (Revised)

### Phase 2 Success (Week 7)
- [ ] ≥5 novel innovations validated
- [ ] Innovation success rate ≥30%
- [ ] At least 1 innovation in top-3 strategies
- [ ] Performance ≥ baseline (no regression)

### Phase 3 Success (Week 12)
- [ ] ≥20 novel innovations created
- [ ] ≥5 innovations adopted in top-10 strategies
- [ ] **Statistical significance** (p <0.05) vs baseline
- [ ] **Positive Sharpe on hold-out set** (2019-2025)
- [ ] Diversity maintained >0.3

---

## 🛠️ Technical Components

### 7-Layer Validation Pipeline
```
Layer 0: Static Safety & Financial Analysis
    ├─ Banned imports check
    ├─ Look-ahead bias detection
    └─ Complexity limits

Layer 1: Syntax Validation
    └─ AST parse success

Layer 2: Semantic Validation
    ├─ Type checking
    └─ Data availability

Layer 3: Execution Validation
    └─ Sandbox (Firecracker/gVisor, 2s timeout, 256MB)

Layer 3.5: Semantic Equivalence (NEW)
    └─ AST-based duplicate detection

Layer 4: Performance Validation
    ├─ Adaptive thresholds
    ├─ Multi-metric
    └─ Regime-specific

Layer 5: Novelty Validation
    └─ Not in InnovationRepository

Layer 6: Overfitting & Explainability (NEW)
    ├─ Permutation test
    └─ Economic rationale validation
```

### Three-Set Data Partition
```python
DATA_PARTITION = {
    'training': '1990-01 to 2010-12',    # Layer 4 validation
    'validation': '2011-01 to 2018-12',  # Evolutionary fitness
    'final_holdout': '2019-01 to 2025-12'  # LOCKED until Week 12
}
```

### Enhanced Fitness Function
```python
fitness = (0.65 * performance +
           0.25 * novelty +
           0.10 * complexity_penalty)
```

---

## 📈 Progress Tracking

| Phase | Status | Start Date | End Date | Progress |
|-------|--------|------------|----------|----------|
| Phase 0: Baseline | ⏳ NEXT | TBD | TBD | 0% |
| Phase 2: MVP | 📋 PLANNED | TBD | TBD | 0% |
| Phase 3: Evolutionary | 📋 PLANNED | TBD | TBD | 0% |
| Final Validation | 📋 PLANNED | TBD | TBD | 0% |

---

## 🔗 Dependencies

**Depends On**:
- ✅ `structural-mutation-phase2` (Phase D Complete)
  - Factor Graph System (NetworkX DAG)
  - Three-Tier Mutation System
  - 13 base factors
  - Performance: 0.16ms compilation, 4.3ms execution

**Provides For**:
- Future specs requiring innovation capability
- Production deployment with full innovation stack

---

## 📞 Contact & Support

**Spec Owner**: User + Claude Code
**Review Team**: OpenAI o3, Gemini 2.5 Pro, Claude Opus 4.1
**Status**: ✅ Approved with conditions
**Next Action**: Complete pre-implementation audit (Condition 1)

---

## 📚 Additional Resources

- `LLM_INNOVATION_CAPABILITY.md` - Original motivation document
- `structural-mutation-phase2/STATUS.md` - Previous spec status
- `PROD2_PERFORMANCE_BENCHMARK_REPORT.md` - Current system performance

---

**Last Updated**: 2025-10-23
**Spec Status**: ✅ **APPROVED - READY TO START**
**Confidence**: **8/10**
**Next Milestone**: Week 1 - Pre-implementation audit + Task 0.1 baseline test

---

**🚀 You may proceed with implementation.**
