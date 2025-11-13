# Spec Status: Structured Innovation MVP (Phase 2a)

**Spec Name**: structured-innovation-mvp
**Status**: 🔴 Not Started
**Progress**: 0/13 tasks (0%)
**Created**: 2025-10-25
**Last Updated**: 2025-10-25

---

## Overview

Implement YAML/JSON-based structured innovation where LLMs create declarative strategy specifications instead of full code. Templates generate syntactically correct Python code, reducing hallucination risk by 80% while maintaining 85% innovation coverage.

**Key Goals**:
- Define comprehensive YAML schema for strategy specifications
- Implement code generation from YAML using Jinja2 templates
- Guide LLM to generate valid YAML specs through prompt engineering
- Achieve >90% generation success rate vs ~60% for full code generation

---

## Phase Breakdown

### Phase 1: YAML Schema & Validation (Tasks 1-2) - 0/2 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 1. YAML strategy schema | ⬜ Not Started | `schemas/strategy_schema_v1.json` | Critical |
| 2. YAMLSchemaValidator module | ⬜ Not Started | `src/generators/yaml_schema_validator.py` | Critical |

**Phase Goal**: Define formal schema and validation for LLM-generated YAML strategies

### Phase 2: Code Generation from YAML (Tasks 3-4) - 0/2 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 3. Jinja2 code generation templates | ⬜ Not Started | `src/generators/yaml_to_code_template.py` | Critical |
| 4. YAMLToCodeGenerator module | ⬜ Not Started | `src/generators/yaml_to_code_generator.py` | Critical |

**Phase Goal**: Generate syntactically correct Python from validated YAML specs

### Phase 3: LLM Prompt Engineering (Tasks 5-6) - 0/2 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 5. StructuredPromptBuilder module | ⬜ Not Started | `src/innovation/structured_prompt_builder.py` | High |
| 6. YAML strategy examples library | ⬜ Not Started | `examples/yaml_strategies/*.yaml` | High |

**Phase Goal**: Guide LLM to generate valid YAML specs with examples

### Phase 4: Integration with InnovationEngine (Tasks 7-8) - 0/2 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 7. Extend InnovationEngine | ⬜ Not Started | `src/innovation/innovation_engine.py` | Critical |
| 8. Structured mode configuration | ⬜ Not Started | `config/learning_system.yaml` | High |

**Phase Goal**: Enable structured YAML generation mode with fallback to full code

### Phase 5: Testing (Tasks 9-11) - 0/3 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 9. YAML validation and generation tests | ⬜ Not Started | `tests/generators/test_yaml_*.py` | High |
| 10. LLM YAML generation integration tests | ⬜ Not Started | `tests/integration/test_structured_innovation.py` | Critical |
| 11. Success rate comparison tests | ⬜ Not Started | `tests/integration/test_structured_vs_code_success_rate.py` | Critical |

**Phase Goal**: Validate >90% success rate and demonstrate value proposition

### Phase 6: Documentation (Tasks 12-13) - 0/2 ⬜

| Task | Status | File | Priority |
|------|--------|------|----------|
| 12. User documentation | ⬜ Not Started | `docs/STRUCTURED_INNOVATION.md` | Medium |
| 13. YAML schema documentation | ⬜ Not Started | `schemas/SCHEMA_GUIDE.md` | Medium |

**Phase Goal**: Complete documentation for YAML specs and mode usage

---

## Success Criteria

### Must Have (P0)
- [ ] Schema coverage ≥85% of historical successful strategies
- [ ] YAML validation success rate >95%
- [ ] Code generation success rate 100% for valid YAML
- [ ] End-to-end success rate >90% (YAML → Code → Execution)
- [ ] 50-generation test shows improved success rate vs full code generation

### Should Have (P1)
- [ ] 3 complete YAML strategy examples (momentum, mean reversion, factor combo)
- [ ] Hybrid mode supports configurable YAML/code ratio (default 80/20)
- [ ] YAML parsing and validation <50ms
- [ ] Code generation from template <200ms

### Nice to Have (P2)
- [ ] Schema extensible via plugins (future: custom indicator definitions)
- [ ] Metrics tracked (yaml_generation_total, validation_success_rate)
- [ ] Schema coverage gap logging for patterns requiring full code
- [ ] Automatic retry on YAML parsing failures

---

## Dependencies

### External
- Python libraries: `pyyaml>=6.0`, `jsonschema>=4.17.0`, `jinja2>=3.1.0`
- JSON Schema v7 specification

### Internal
- `src/innovation/innovation_engine.py` (from llm-integration-activation)
- `src/innovation/llm_providers.py` (LLM API abstraction)
- `src/mutation/factor_graph.py` (fallback mutation system)
- `src/validation/ast_validator.py` (code validation)
- `config/learning_system.yaml` (configuration patterns)

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema coverage <85% | Medium | High | Iteratively expand schema based on failed patterns, provide full code fallback |
| LLM generates invalid YAML | Medium | Medium | Retry with explicit instructions, include schema in prompt, fall back to Factor Graph |
| Template generation errors | Low | High | Extensive Jinja2 template testing, AST validation after generation |
| Success rate <90% target | Medium | Medium | Iterate on prompt engineering, add more few-shot examples, improve schema clarity |
| Performance overhead (>300ms) | Low | Low | Optimize Jinja2 templates, cache parsed schemas, use efficient YAML parsing |
| YAML parsing failures | Medium | Medium | Robust regex extraction, retry logic, fallback to full code generation |

---

## Timeline Estimate

- **Phase 1**: 3-4 hours (Schema and validation)
- **Phase 2**: 4-5 hours (Code generation templates)
- **Phase 3**: 3-4 hours (Prompt engineering)
- **Phase 4**: 3-4 hours (Integration)
- **Phase 5**: 6-8 hours (Testing)
- **Phase 6**: 2-3 hours (Documentation)

**Total**: 2-3 days (full-time) or 2-3 weeks (part-time)

**Priority**: MEDIUM (Phase 2a - Week 3-4 after llm-integration-activation validated)

**Critical Path**: 1→2→4→7→10→12

---

## Notes

- **Why Medium Priority**: Phase 2a builds on llm-integration-activation foundation, not blocking initial LLM testing
- **Interpreter Pattern**: Parse YAML specs, interpret into Python using Jinja2 templates (80% hallucination reduction)
- **3 Strategy Types**: Momentum, mean reversion, factor combination (covers 85% of patterns)
- **3 Modes**: structured (YAML only), code (full Python), hybrid (80% YAML, 20% code)
- **Template Method**: Jinja2 templates ensure syntactically correct code generation (100% success on valid YAML)
- **Value Proposition**: >90% success rate vs ~60% for full code generation, safer innovation

---

## Next Steps

1. ✅ Spec complete (requirements, design, tasks)
2. ⬜ Complete llm-integration-activation spec first (dependency)
3. ⬜ Implement Phase 1: YAML strategy schema (Task 1)
4. ⬜ Implement Phase 1: YAMLSchemaValidator (Task 2)
5. ⬜ Implement Phase 2: Jinja2 templates (Task 3)
6. ⬜ Implement Phase 2: YAMLToCodeGenerator (Task 4)
7. ⬜ Create 3 YAML strategy examples (Task 6)

---

**Document Version**: 1.0
**Maintainer**: Personal Project
**Related Specs**:
- llm-integration-activation (dependency - base LLM integration)
- docker-sandbox-security (provides secure execution environment)
