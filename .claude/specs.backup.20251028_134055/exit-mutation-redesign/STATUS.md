# Spec Status: Exit Mutation Redesign

**Spec Name**: exit-mutation-redesign
**Status**: 🔴 Not Started
**Progress**: 0/8 tasks (0%)
**Created**: 2025-10-25
**Last Updated**: 2025-10-25

---

## Overview

Redesign exit mutation from brittle AST manipulation (0/41 success rate) to robust parameter-based genetic operators that mutate numerical parameters (stop_loss, take_profit, trailing_stop) within bounded ranges using Gaussian noise.

**Key Goals**:
- Improve exit mutation success rate from 0% to >70%
- Enable optimization of exit conditions (stop loss, take profit, trailing stops)
- Use parameter-based mutation instead of AST manipulation
- Integrate with Factor Graph mutation system

---

## Phase Breakdown

### Phase 1: Core Parameter Mutation (Tasks 1-3) - 0/3 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 1. ExitParameterMutator module | ⬜ Not Started | `src/mutation/exit_parameter_mutator.py` | Critical |
| 2. Parameter bounds configuration | ⬜ Not Started | `config/mutation_config.yaml` | High |
| 3. Integration with Factor Graph | ⬜ Not Started | `src/mutation/factor_graph.py` | Critical |

**Phase Goal**: Implement parameter-based mutation with bounded ranges and Gaussian noise

### Phase 2: Testing (Tasks 4-6) - 0/3 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 4. ExitParameterMutator unit tests | ⬜ Not Started | `tests/mutation/test_exit_parameter_mutator.py` | High |
| 5. Integration tests with real code | ⬜ Not Started | `tests/integration/test_exit_mutation_integration.py` | Critical |
| 6. Performance benchmark tests | ⬜ Not Started | `tests/performance/test_exit_mutation_performance.py` | Medium |

**Phase Goal**: Validate >70% success rate and performance targets

### Phase 3: Documentation & Monitoring (Tasks 7-8) - 0/2 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 7. User documentation | ⬜ Not Started | `docs/EXIT_MUTATION.md` | Medium |
| 8. Metrics tracking | ⬜ Not Started | `src/mutation/factor_graph.py` | Medium |

**Phase Goal**: Complete documentation and monitoring infrastructure

---

## Success Criteria

### Must Have (P0)
- [ ] Success rate improves from 0% to >70%
- [ ] All 4 parameters supported (stop_loss, take_profit, trailing_stop, holding_period)
- [ ] 100% of mutations stay within defined bounds
- [ ] AST validation passes after all mutations
- [ ] Integration tests pass with real strategy code

### Should Have (P1)
- [ ] Exit mutation used in 20% of Factor Graph iterations
- [ ] Gaussian distribution verified (68% within ±15%, 95% within ±30%)
- [ ] Mutation latency <100ms per mutation
- [ ] Metrics tracked (exit_mutations_total, success_rate)

### Nice to Have (P2)
- [ ] Performance comparison vs old AST approach documented
- [ ] Parameter bounds configurable via YAML
- [ ] Graceful handling of missing parameters with clear logs

---

## Dependencies

### External
- Python `numpy` library (≥1.24.0) for Gaussian noise
- `random` module for noise generation
- `re` module for regex-based replacement

### Internal
- `src/mutation/factor_graph.py` (mutation system integration)
- `src/mutation/unified_mutation_operator.py` (mutation type selection)
- `src/monitoring/metrics_collector.py` (Prometheus metrics)
- `config/learning_system.yaml` (configuration patterns)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Regex fails to find parameters | Medium | Medium | Skip gracefully, log missing parameters, success=False |
| Bounded ranges too tight | Low | Medium | Calibrate bounds based on domain expertise (1-20% stop loss realistic) |
| Success rate <70% target | Low | High | Fall back to original code on validation failure, iterate on regex patterns |
| Performance overhead | Low | Low | Regex matching is fast (<10ms), use simple string replacement |
| Breaking existing mutations | Low | High | Integration tests verify backward compatibility, 20% weight minimizes disruption |

---

## Timeline Estimate

- **Phase 1**: 4-6 hours (Core mutation implementation)
- **Phase 2**: 4-6 hours (Testing and validation)
- **Phase 3**: 2-3 hours (Docs and metrics)

**Total**: 1-2 days (full-time) or 3-5 days (part-time)

**Priority**: MEDIUM (Week 2-3 after llm-integration-activation)

---

## Notes

- **Why Redesign**: Current AST-based approach has 0/41 success rate due to complex nested structure manipulation
- **Key Innovation**: Parameter-based mutation with Gaussian noise + bounded ranges avoids AST complexity
- **Integration**: Exit mutation becomes 20% weighted mutation type alongside add/remove/modify
- **Validation**: All mutations validated with ast.parse() before acceptance
- **Backward Compatible**: Strategies without exit parameters are skipped gracefully

---

## Next Steps

1. ✅ Spec complete (requirements, design, tasks)
2. ⬜ Implement Phase 1: ExitParameterMutator (Task 1)
3. ⬜ Define parameter bounds configuration (Task 2)
4. ⬜ Integrate with Factor Graph (Task 3)
5. ⬜ Write unit tests and validate >70% success rate (Task 4-5)

---

**Document Version**: 1.0
**Maintainer**: Personal Project
**Related Specs**: llm-integration-activation (LLM can leverage exit mutation for parameter tuning)
