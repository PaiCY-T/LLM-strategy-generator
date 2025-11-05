# Tasks Document: LLM Integration Activation

## Phase 1: Core LLM Components (Tasks 1-4)

- [ ] 1. Create LLMProviderInterface abstract base class
  - File: `src/innovation/llm_providers.py`
  - Define abstract interface for LLM API providers
  - Implement OpenRouterProvider, GeminiProvider, OpenAIProvider
  - Add cost estimation method for each provider
  - Purpose: Provider-agnostic LLM API abstraction
  - _Leverage: `requests` library for HTTP calls, existing API patterns_
  - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Backend Developer with expertise in API abstraction and Python ABC | Task: Create LLMProviderInterface with 3 concrete implementations (OpenRouter/Gemini/OpenAI) following requirements 2.1-2.4, ensuring consistent interface across providers | Restrictions: Must handle API errors uniformly, implement timeouts (60s), support environment variable API keys | _Leverage: requests library, ABC module | _Requirements: Requirements 2.1-2.4 (Provider abstraction and implementations) | Success: All 3 providers implement interface correctly, API calls work with proper error handling | Instructions: Set task to [-] in tasks.md, mark [x] when provider tests pass_

- [ ] 2. Create PromptBuilder module
  - File: `src/innovation/prompt_builder.py`
  - Implement modification prompt construction with champion feedback
  - Implement creation prompt construction with innovation guidance
  - Extract success factors from champion code and metrics
  - Extract failure patterns from failure history JSON
  - Purpose: Generate effective LLM prompts with context
  - _Leverage: Existing `failure_patterns.json`, champion tracking from autonomous_loop_
  - _Requirements: 3.1, 3.2, 3.3_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Prompt Engineer with expertise in LLM instruction design and Python | Task: Create PromptBuilder class following requirements 3.1-3.3, constructing modification and creation prompts with champion feedback and failure patterns | Restrictions: Must include FinLab API constraints in prompts, add few-shot examples, keep prompts under 2000 tokens | _Leverage: artifacts/data/failure_patterns.json, champion code from loop | _Requirements: Requirements 3.1-3.3 (Prompt construction with feedback) | Success: Prompts are well-structured with examples, include relevant feedback, guide LLM effectively | Instructions: Set task to [-], mark [x] when PromptBuilder tests pass_

- [ ] 3. Extend InnovationEngine with feedback loop
  - File: `src/innovation/innovation_engine.py` (modify existing)
  - Add `generate_with_feedback()` method using PromptBuilder
  - Integrate LLMProvider for API calls
  - Parse LLM response and extract Python code using regex
  - Handle API errors with retries and fallback signaling
  - Purpose: Complete LLM-driven innovation capability
  - _Leverage: Existing InnovationEngine base, new LLMProvider and PromptBuilder_
  - _Requirements: 1.3, 1.4, 1.5_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: ML Engineer with expertise in LLM integration and Python | Task: Extend existing InnovationEngine with feedback-driven generation following requirements 1.3-1.5, integrating PromptBuilder and LLMProvider with robust error handling | Restrictions: Must retry on rate limits (3 attempts), parse code using regex safely, signal fallback on failures | _Leverage: src/innovation/innovation_engine.py, LLMProvider, PromptBuilder | _Requirements: Requirements 1.3-1.5 (Feedback loop, API calls, error handling) | Success: InnovationEngine generates code via LLM, handles errors gracefully, returns valid Python or signals fallback | Instructions: Set task to [-], mark [x] when InnovationEngine feedback tests pass_

- [ ] 4. Create LLMConfig dataclass
  - File: `src/innovation/llm_config.py`
  - Define LLM configuration dataclass (provider, model, api_key, innovation_rate, etc.)
  - Load from `config/learning_system.yaml`
  - Validate API keys and configuration values
  - Purpose: Centralized LLM configuration management
  - _Leverage: Existing config loading patterns from `config/learning_system.yaml`_
  - _Requirements: 2.1_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps Engineer with expertise in configuration management and Python dataclasses | Task: Create LLMConfig dataclass following requirement 2.1, loading from YAML with validation for API keys and sensible defaults | Restrictions: Must support environment variable substitution for API keys, validate innovation_rate (0.0-1.0), provide defaults | _Leverage: config/learning_system.yaml loading patterns | _Requirements: Requirement 2.1 (LLM configuration) | Success: Config loads from YAML, validates parameters, supports env vars for secrets | Instructions: Set task to [-], mark [x] when LLMConfig tests pass_

## Phase 2: Integration (Tasks 5-6)

- [ ] 5. Integrate LLM into autonomous loop
  - File: `artifacts/working/modules/autonomous_loop.py` (modify)
  - Initialize InnovationEngine with configured LLM provider at loop startup
  - Use LLM for 20% of iterations (iteration % 5 == 0)
  - Implement fallback to Factor Graph on LLM failures
  - Track LLM success/failure rates via metrics
  - Purpose: Activate LLM-driven innovation in production loop
  - _Leverage: Existing autonomous_loop.py, InnovationEngine, FactorGraph mutation_
  - _Requirements: 1.1, 1.2, 5.1, 5.2, 5.3, 5.4, 5.5_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Backend Developer with expertise in system integration and error handling | Task: Integrate InnovationEngine into autonomous_loop.py following requirements 1.1-1.2 and 5.1-5.5, routing 20% of iterations to LLM with automatic fallback to Factor Graph on failures | Restrictions: Must maintain 100% iteration success rate via fallback, log all LLM calls and outcomes, disable LLM if auth fails | _Leverage: artifacts/working/modules/autonomous_loop.py, src/innovation/innovation_engine.py, src/mutation/factor_graph.py | _Requirements: Requirements 1.1-1.2 (LLM integration), 5.1-5.5 (Fallback mechanisms) | Success: 20% iterations use LLM, failures fallback to Factor Graph, loop never stalls | Instructions: Set task to [-], mark [x] when integration tests pass with LLM enabled_

- [ ] 6. Add LLM configuration to learning system config
  - File: `config/learning_system.yaml` (modify)
  - Add `llm` section with provider selection, API keys, innovation rate
  - Add provider-specific subsections (openrouter, gemini, openai)
  - Add generation and fallback settings
  - Document all configuration options
  - Purpose: Enable LLM configuration in production
  - _Leverage: Existing learning_system.yaml structure_
  - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: DevOps Engineer with expertise in YAML configuration and secrets management | Task: Extend learning_system.yaml with LLM configuration section following requirements 2.1-2.4, supporting 3 providers with environment variable API keys | Restrictions: Must maintain backward compatibility (default LLM disabled), use ${ENV_VAR} syntax for secrets, document all options | _Leverage: config/learning_system.yaml | _Requirements: Requirements 2.1-2.4 (Provider configuration) | Success: LLM can be configured and disabled via YAML, API keys from env vars, well-documented | Instructions: Set task to [-], mark [x] when config schema validated_

## Phase 3: Prompt Engineering (Tasks 7-8)

- [x] 7. Create modification prompt template
  - File: `src/innovation/prompts/modification_template.txt`
  - Design prompt template for modifying champion strategies
  - Include placeholders for champion code, metrics, success factors, failure patterns
  - Add FinLab API constraints and few-shot examples
  - Purpose: Guide LLM to make effective strategy modifications
  - _Leverage: Few-shot examples from existing successful strategies_
  - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Prompt Engineer with expertise in LLM instruction design and quantitative finance | Task: Design modification prompt template following requirements 4.1-4.4, including champion context, success factors, failure patterns, and clear constraints | Restrictions: Must include function signature requirements, liquidity constraints (>150M), rebalancing frequency, add 2 few-shot examples | _Leverage: Existing successful strategies for examples | _Requirements: Requirements 4.1-4.4 (Prompt structure and constraints) | Success: Prompt template is clear, includes all placeholders, guides LLM to valid modifications | Instructions: Set task to [-], mark [x] when template reviewed and validated_

- [x] 8. Create creation prompt template
  - File: `src/innovation/prompts/creation_template.txt`
  - Design prompt template for creating novel strategies
  - Include placeholders for champion approach, failure patterns, innovation directive
  - Add FinLab API constraints and few-shot examples
  - Purpose: Guide LLM to create novel viable strategies
  - _Leverage: Few-shot examples from successful novel strategies_
  - _Requirements: 4.1, 4.2, 4.3, 4.4_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Prompt Engineer with expertise in creative LLM prompting and strategy design | Task: Design creation prompt template following requirements 4.1-4.4, inspiring novel approaches while maintaining constraints and viability | Restrictions: Must include clear novelty directive, FinLab API constraints, function signature, add 2 few-shot examples of novel strategies | _Leverage: Existing novel successful strategies for examples | _Requirements: Requirements 4.1-4.4 (Prompt structure and constraints) | Success: Prompt template guides LLM to novel but valid strategies, clear constraints included | Instructions: Set task to [-], mark [x] when template reviewed and validated_

## Phase 4: Testing (Tasks 9-12)

- [ ] 9. Write LLMProvider unit tests
  - File: `tests/innovation/test_llm_providers.py`
  - Mock API responses for all 3 providers (OpenRouter, Gemini, OpenAI)
  - Test timeout enforcement (60s)
  - Test retry logic on rate limits (exponential backoff)
  - Test error handling (auth errors, network errors, invalid responses)
  - Coverage target: >85%
  - _Leverage: `pytest`, `unittest.mock` or `responses` library for HTTP mocking_
  - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer with expertise in API testing and mocking | Task: Create unit tests for all 3 LLMProvider implementations following requirements 2.1-2.4, mocking HTTP calls and testing error scenarios | Restrictions: Must mock all API calls (no real LLM calls), test timeout and retry logic, achieve >85% coverage | _Leverage: pytest, unittest.mock or responses library | _Requirements: Requirements 2.1-2.4 (Provider implementations) | Success: All providers tested with mocks, error scenarios covered, >85% coverage | Instructions: Set task to [-], mark [x] when tests pass with >85% coverage_

- [ ] 10. Write PromptBuilder unit tests
  - File: `tests/innovation/test_prompt_builder.py`
  - Test modification prompt generation with champion data
  - Test creation prompt generation with failure patterns
  - Test success factor extraction from code and metrics
  - Test failure pattern extraction from JSON
  - Coverage target: >90%
  - _Leverage: `pytest`, mock champion data and failure patterns_
  - _Requirements: 3.1, 3.2, 3.3_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: QA Engineer with expertise in unit testing and data transformation | Task: Create unit tests for PromptBuilder following requirements 3.1-3.3, testing prompt generation with various champion and failure data | Restrictions: Must test with realistic champion/failure data, verify prompt structure, achieve >90% coverage | _Leverage: pytest, mock data fixtures | _Requirements: Requirements 3.1-3.3 (Prompt construction) | Success: Prompts generated correctly for all scenarios, success/failure extraction works, >90% coverage | Instructions: Set task to [-], mark [x] when tests pass with >90% coverage_

- [ ] 11. Write InnovationEngine integration tests with LLM
  - File: `tests/integration/test_llm_innovation.py`
  - Test 1: Call real LLM API (1 test call), verify code extraction
  - Test 2: Mock API failure, verify fallback signaling
  - Test 3: Mock timeout, verify retry and eventual fallback
  - Test 4: Mock rate limit, verify exponential backoff
  - _Leverage: Real API for Test 1 (manual/optional), mocks for Tests 2-4_
  - _Requirements: 1.3, 1.4, 1.5, 5.1, 5.2, 5.3_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Test Engineer with expertise in LLM testing and error scenarios | Task: Create integration tests for InnovationEngine with LLM following requirements 1.3-1.5 and 5.1-5.3, testing real API call and error handling | Restrictions: Limit real API calls to 1 (cost), mock all error scenarios, verify fallback signaling | _Leverage: Real LLM API (1 call), unittest.mock for errors | _Requirements: Requirements 1.3-1.5 (LLM calls), 5.1-5.3 (Error handling and fallback) | Success: Real API call works and returns valid code, error scenarios trigger correct fallbacks | Instructions: Set task to [-], mark [x] when integration tests pass_

- [x] 12. Write autonomous loop integration tests with LLM
  - File: `tests/integration/test_autonomous_loop_llm.py` (existing - 10 iterations)
  - File: `tests/integration/test_autonomous_loop_e2e.py` (NEW - comprehensive 20 iteration E2E tests)
  - Run 10 iterations with LLM enabled (innovation_rate=0.20)
  - Verify ~2 iterations use LLM, ~8 use Factor Graph
  - Mock some LLM failures, verify automatic fallback works
  - Verify all 10 iterations complete successfully
  - **E2E Tests (Task 6 - NEW)**: 7 comprehensive test scenarios:
    1. 20-iteration mixed mode (main test) with champion tracking
    2. LLM disabled baseline (backward compatibility)
    3. Cost tracking validation
    4. Fallback mechanism test
    5. Champion update tracking (LLM vs Factor Graph)
    6. Execution time performance (< 60s requirement)
    7. Statistics accuracy validation
  - _Leverage: Existing loop test patterns, LLM mocks_
  - _Requirements: 1.1, 1.2, 5.4, 5.5_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Integration Test Engineer with expertise in end-to-end system testing | Task: Create autonomous loop integration tests with LLM following requirements 1.1-1.2 and 5.4-5.5, running 10 iterations and verifying LLM usage and fallback behavior | Restrictions: Must test real loop with LLM mocks, verify iteration success rate 100%, limit to 10 iterations for speed | _Leverage: Existing loop test patterns, LLM provider mocks | _Requirements: Requirements 1.1-1.2 (LLM integration), 5.4-5.5 (Reliability and fallback) | Success: 10 iterations complete with ~20% LLM usage, fallbacks work correctly, 100% success rate | Instructions: Set task to [-], mark [x] when integration test passes_

## Phase 5: Documentation & Deployment (Tasks 13-14)

- [ ] 13. Create user documentation
  - File: `docs/LLM_INTEGRATION.md`
  - Document API provider setup (API keys, environment variables)
  - Document configuration options (provider selection, innovation rate, etc.)
  - Document monitoring LLM usage (metrics, costs)
  - Provide troubleshooting guide (auth errors, rate limits, fallback issues)
  - _Leverage: Existing documentation structure_
  - _Requirements: All_
  - _Prompt: Implement the task for spec llm-integration-activation, first run spec-workflow-guide to get the workflow guide then implement the task: Role: Technical Writer with expertise in API documentation and configuration guides | Task: Create comprehensive LLM integration documentation covering API setup, configuration, monitoring, and troubleshooting | Restrictions: Must be clear for both novice and experienced users, include security best practices for API keys, maintain consistent structure | _Leverage: Existing documentation structure and style | _Requirements: All requirements (complete LLM setup and usage) | Success: Documentation is complete, clear, users can set up LLM integration successfully | Instructions: Set task to [-], mark [x] when documentation review passes_

- [x] 14. Create LLM setup validation script
  - File: `scripts/validate_llm_setup.sh` ✓
  - Verify API keys are configured (check environment variables) ✓
  - Test API connectivity for configured provider ✓
  - Validate configuration in learning_system.yaml ✓
  - Provide clear diagnostic messages ✓
  - _Leverage: Shell scripting, curl for API testing_
  - _Requirements: All configuration requirements_
  - _Deliverables: 600+ line bash script with 6 validation checks, color output, supports 3 providers_
  - _Completed: 2025-10-27_

## Summary

**Total Tasks**: 14
**Estimated Time**: 2-3 days (full-time)

**Phase Breakdown**:
- Phase 1 (Core LLM): Tasks 1-4 → 6-8 hours
- Phase 2 (Integration): Tasks 5-6 → 3-4 hours
- Phase 3 (Prompts): Tasks 7-8 → 2-3 hours
- Phase 4 (Testing): Tasks 9-12 → 6-8 hours
- Phase 5 (Docs): Tasks 13-14 → 2-3 hours

**Dependencies**:
- Tasks 1-2 can run in parallel
- Task 3 depends on Tasks 1-2 (needs LLMProvider and PromptBuilder)
- Task 4 can run in parallel with Tasks 1-3
- Task 5 depends on Tasks 1-4 complete
- Task 6 can run in parallel
- Tasks 7-8 can run in parallel
- Tasks 9-12 depend on respective implementation tasks
- Tasks 13-14 depend on all previous tasks

**Critical Path**: 1→3→5→11→14
