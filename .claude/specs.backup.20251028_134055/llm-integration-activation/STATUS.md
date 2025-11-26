# Spec Status: LLM Integration Activation

**Spec Name**: llm-integration-activation
**Status**: 🔴 Not Started
**Progress**: 0/14 tasks (0%)
**Created**: 2025-10-25
**Last Updated**: 2025-10-25

---

## Overview

Activate the InnovationEngine in the autonomous iteration loop, enabling LLM-driven strategy innovation for 20% of iterations with automatic fallback to Factor Graph mutation on failures. This is the critical enabler for LLM Innovation roadmap.

**Key Goals**:
- Enable LLM innovation for 20% of iterations
- Provide API provider abstraction (OpenRouter, Gemini, OpenAI)
- Implement feedback loop with champion performance and failure patterns
- Maintain 100% iteration success rate through automatic fallback

---

## Phase Breakdown

### Phase 1: Core LLM Components (Tasks 1-4) - 0/4 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 1. LLMProviderInterface ABC | ⬜ Not Started | `src/innovation/llm_providers.py` | Critical |
| 2. PromptBuilder module | ⬜ Not Started | `src/innovation/prompt_builder.py` | Critical |
| 3. InnovationEngine extension | ⬜ Not Started | `src/innovation/innovation_engine.py` | Critical |
| 4. LLMConfig dataclass | ⬜ Not Started | `src/innovation/llm_config.py` | High |

**Phase Goal**: Create foundational LLM abstraction and prompt engineering infrastructure

### Phase 2: Integration (Tasks 5-6) - 0/2 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 5. Integrate into autonomous loop | ⬜ Not Started | `artifacts/working/modules/autonomous_loop.py` | Critical |
| 6. Add LLM configuration | ⬜ Not Started | `config/learning_system.yaml` | High |

**Phase Goal**: Activate LLM in production loop with 20% innovation rate

### Phase 3: Prompt Engineering (Tasks 7-8) - 0/2 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 7. Modification prompt template | ⬜ Not Started | `src/innovation/prompts/modification_template.txt` | High |
| 8. Creation prompt template | ⬜ Not Started | `src/innovation/prompts/creation_template.txt` | High |

**Phase Goal**: Design effective prompts with constraints and few-shot examples

### Phase 4: Testing (Tasks 9-12) - 0/4 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 9. LLMProvider unit tests | ⬜ Not Started | `tests/innovation/test_llm_providers.py` | High |
| 10. PromptBuilder unit tests | ⬜ Not Started | `tests/innovation/test_prompt_builder.py` | High |
| 11. InnovationEngine integration tests | ⬜ Not Started | `tests/integration/test_llm_innovation.py` | Critical |
| 12. Autonomous loop LLM integration tests | ⬜ Not Started | `tests/integration/test_autonomous_loop_llm.py` | Critical |

**Phase Goal**: Comprehensive testing with mocked and real API calls

### Phase 5: Documentation & Deployment (Tasks 13-14) - 0/2 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 13. User documentation | ⬜ Not Started | `docs/LLM_INTEGRATION.md` | Medium |
| 14. Setup validation script | ⬜ Not Started | `scripts/validate_llm_setup.sh` | Medium |

**Phase Goal**: Complete documentation and deployment validation tools

---

## Success Criteria

### Must Have (P0)
- [ ] InnovationEngine called every 5th iteration (20% rate)
- [ ] ≥60% of LLM-generated strategies pass validation
- [ ] Zero iteration stalls due to LLM failures (100% fallback coverage)
- [ ] All 3 API providers supported (OpenRouter, Gemini, OpenAI)
- [ ] 20-generation test runs successfully with LLM active

### Should Have (P1)
- [ ] LLM latency <60s per generation
- [ ] Feedback loop includes champion metrics and failure patterns
- [ ] Metrics tracked (llm_calls_total, success_rate, latency)
- [ ] Graceful degradation on auth failures (disable LLM automatically)

### Nice to Have (P2)
- [ ] Cost per iteration <$0.10
- [ ] Retry logic on rate limits (exponential backoff, 3 attempts)
- [ ] High failure rate warning (>50% over 10 iterations)
- [ ] Automatic innovation_rate reduction on failures

---

## Dependencies

### External
- Python libraries: `openai>=1.0.0`, `google-generativeai>=0.3.0`, `anthropic>=0.7.0`
- API keys: OpenRouter, Gemini, or OpenAI (environment variables)
- Network connectivity for API calls

### Internal
- `src/innovation/innovation_engine.py` (existing implementation from Tasks 3.1-3.3)
- `src/mutation/factor_graph.py` (fallback mutation system)
- `src/validation/ast_validator.py` (code validation)
- `artifacts/data/failure_patterns.json` (failure feedback)
- `config/learning_system.yaml` (configuration patterns)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| API authentication failures | Medium | High | Validate API keys at startup, disable LLM gracefully, fallback to Factor Graph |
| High API costs | Medium | Medium | Limit to 20% innovation rate, use cost-effective models, monitor spend |
| LLM validation failures | High | Medium | Fallback to Factor Graph on validation errors, log rejection reasons |
| API timeout/rate limits | Medium | Medium | 60s timeout, exponential backoff retries (3 attempts), fallback on exhaustion |
| Low LLM success rate (<60%) | Medium | Medium | Iterate on prompt templates, add more few-shot examples, adjust temperature |
| Network connectivity issues | Low | Medium | Retry once after 2s, fallback to Factor Graph on network errors |

---

## Timeline Estimate

- **Phase 1**: 6-8 hours (Core LLM components)
- **Phase 2**: 3-4 hours (Integration)
- **Phase 3**: 2-3 hours (Prompt templates)
- **Phase 4**: 6-8 hours (Testing)
- **Phase 5**: 2-3 hours (Docs and validation)

**Total**: 2-3 days (full-time)

**Priority**: HIGH (Week 2 - enables Task 3.5 testing)

**Critical Path**: 1→2→3→5→11→14

---

## Notes

- **Why High Priority**: This is the critical enabler for the entire LLM Innovation roadmap (Task 3.5 and Phase 2a)
- **Innovation Rate**: 20% (every 5th iteration) to balance exploration vs stability
- **Fallback Essential**: 100% Factor Graph fallback ensures iterations never stall
- **Provider Flexibility**: Support 3 providers (OpenRouter/Gemini/OpenAI) for cost optimization
- **Feedback Loop**: Champion metrics + failure patterns guide LLM improvements
- **Cost Management**: Limit to cost-effective models (<$0.10 per iteration)

---

## Next Steps

1. ✅ Spec complete (requirements, design, tasks)
2. ⬜ Implement Phase 1: LLMProviderInterface (Task 1)
3. ⬜ Implement Phase 1: PromptBuilder (Task 2)
4. ⬜ Extend InnovationEngine with feedback loop (Task 3)
5. ⬜ Integrate into autonomous loop (Task 5)
6. ⬜ Run 20-generation test with LLM active

---

**Document Version**: 1.0
**Maintainer**: Personal Project
**Related Specs**:
- docker-sandbox-security (security foundation)
- structured-innovation-mvp (next phase after LLM activation)
- exit-mutation-redesign (complementary mutation capability)
