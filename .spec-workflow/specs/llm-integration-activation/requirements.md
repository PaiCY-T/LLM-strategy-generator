# Requirements Document: LLM Integration Activation

## Introduction

The InnovationEngine (Task 3.1-3.3) has been implemented but is currently disabled in the iteration loop. This feature **activates LLM integration** by connecting InnovationEngine to the autonomous loop with proper configuration, error handling, and fallback to Factor Graph mutation on LLM failures.

**HIGH PRIORITY**: This is the critical enabler for Task 3.5 (100-generation LLM test) and the entire LLM Innovation roadmap.

**Value Proposition**: Enable the system to leverage LLM innovation for 20% of iterations while maintaining stability through Factor Graph fallback, unlocking the potential for novel strategy discovery beyond predefined templates.

## Alignment with Product Vision

This feature is the **key milestone** for the LLM Innovation Critical Path by:
- **Innovation activation**: Transitioning from pure Factor Graph mutation to hybrid LLM+Factor Graph approach
- **Controlled rollout**: Limiting LLM usage to 20% of iterations to contain risk
- **Resilience**: Maintaining 100% iteration success rate through automatic fallback
- **Foundation for Phase 2a**: Enabling structured innovation (YAML/JSON) once base LLM integration is validated

## Requirements

### Requirement 1: InnovationEngine Integration

**User Story:** As the autonomous loop system, I want to use InnovationEngine for 20% of iterations, so that the system can discover novel strategies beyond Factor Graph templates.

#### Acceptance Criteria

1. WHEN the iteration loop starts THEN it SHALL initialize InnovationEngine with configured API provider and key
2. WHEN iteration number % 5 == 0 (every 5th iteration) THEN the system SHALL use InnovationEngine instead of Factor Graph mutation
3. WHEN InnovationEngine is called THEN it SHALL receive champion strategy code, performance metrics, and innovation directive
4. WHEN InnovationEngine returns a strategy THEN the system SHALL validate it using existing validation pipeline
5. WHEN validation passes THEN the system SHALL execute the LLM-generated strategy normally

### Requirement 2: API Provider Configuration

**User Story:** As a system operator, I want to configure LLM API providers flexibly, so that I can use OpenRouter, Gemini, or OpenAI based on cost and availability.

#### Acceptance Criteria

1. WHEN config/learning_system.yaml is read THEN it SHALL contain: llm_provider (openrouter/gemini/openai), api_key, model_name, innovation_rate (0.0-1.0)
2. WHEN llm_provider is "openrouter" THEN InnovationEngine SHALL use OpenRouter API with model "anthropic/claude-3.5-sonnet"
3. WHEN llm_provider is "gemini" THEN InnovationEngine SHALL use Gemini API with model "gemini-2.0-flash-thinking-exp"
4. WHEN llm_provider is "openai" THEN InnovationEngine SHALL use OpenAI API with model "gpt-4o"
5. WHEN api_key is missing or invalid THEN the system SHALL log error and fall back to Factor Graph for 100% of iterations

### Requirement 3: Feedback Loop Implementation

**User Story:** As the InnovationEngine, I want to receive performance feedback from previous iterations, so that I can learn from successes and failures when generating new strategies.

#### Acceptance Criteria

1. WHEN InnovationEngine is called THEN it SHALL receive: champion_code, champion_metrics (sharpe, max_drawdown, win_rate), failure_history (last 3 failed strategies)
2. WHEN champion exists THEN the feedback SHALL include: "Current champion: Sharpe {sharpe}, Max Drawdown {mdd}. Preserve: {success_factors}"
3. WHEN failures exist THEN the feedback SHALL include: "Avoid: {failure_patterns}" extracted from failure_patterns.json
4. WHEN innovation directive is "modify" THEN prompt SHALL be: "Modify this strategy to improve {target_metric}"
5. WHEN innovation directive is "create" THEN prompt SHALL be: "Create a novel strategy inspired by {champion_approach}"

### Requirement 4: Prompt Engineering

**User Story:** As the system designer, I want carefully engineered prompts, so that the LLM generates valid, executable strategies with clear modifications.

#### Acceptance Criteria

1. WHEN innovation directive is "modify" THEN prompt SHALL request: parameter adjustments, factor additions/removals, entry/exit refinements
2. WHEN innovation directive is "create" THEN prompt SHALL request: novel indicator combinations, alternative position sizing, new risk management
3. WHEN prompt is constructed THEN it SHALL include: FinLab API constraints, required function signature, liquidity requirements (>150M), rebalancing frequency
4. WHEN prompt is sent THEN it SHALL include few-shot examples: 1 successful modification, 1 successful creation
5. WHEN LLM response is parsed THEN the system SHALL extract Python code using regex: ```python\n(.*?)\n```

### Requirement 5: Fallback to Factor Graph

**User Story:** As the autonomous loop system, I want automatic fallback to Factor Graph mutation when LLM fails, so that iterations never stall due to LLM errors.

#### Acceptance Criteria

1. WHEN InnovationEngine API call fails (timeout, auth error, rate limit) THEN the system SHALL log error and use Factor Graph mutation for that iteration
2. WHEN InnovationEngine returns invalid code (syntax error, AST validation fails) THEN the system SHALL log rejection reason and use Factor Graph mutation
3. WHEN InnovationEngine-generated strategy fails execution (runtime error) THEN the system SHALL log failure and increment llm_failure_total metric
4. WHEN LLM failures exceed 50% over 10 iterations THEN the system SHALL log warning: "High LLM failure rate, consider reducing innovation_rate"
5. WHEN Factor Graph fallback is used THEN the system SHALL log: "LLM unavailable for iteration {n}, falling back to Factor Graph mutation"

## Non-Functional Requirements

### Performance
- LLM API call timeout: 60 seconds (longer strategies need more generation time)
- Fallback latency: <1 second from LLM failure to Factor Graph mutation
- Zero impact to iteration throughput when LLM is disabled (innovation_rate=0.0)

### Reliability
- Iteration success rate: ≥80% when LLM is active (20% may fail during initial tuning)
- Graceful degradation: 100% Factor Graph fallback when LLM unavailable
- No crashes from LLM API errors (all exceptions caught and logged)

### Cost Management
- LLM API cost per iteration: <$0.10 (use cost-effective models)
- Innovation rate: 0.20 (20%) to limit API costs during testing
- Batch API calls when possible (future optimization)

### Observability
- Log every LLM call: timestamp, model, prompt length, response length, latency
- Export metrics: llm_calls_total, llm_success_rate, llm_failure_rate, llm_latency_seconds
- Log rejection reasons for validation failures
- Track cost per iteration (if API provides usage data)

## Dependencies

- Completed specs: docker-sandbox-security (security foundation)
- Existing code: InnovationEngine implementation (Task 3.1-3.3)
- Python libraries: `pip install openai>=1.0.0 google-generativeai>=0.3.0 anthropic>=0.7.0`
- Configuration: config/learning_system.yaml with llm_provider, api_key, innovation_rate
- Validation: existing AST validation and syntax checking

## Timeline

- **Total Effort**: 1-2 days
- **Priority**: HIGH (enables Task 3.5 testing)
- **Week 2 Target**: Complete implementation and validate with 20-generation test
- **Dependency Chain**: docker-sandbox-security → THIS → structured-innovation-mvp → Task 3.5

## Success Metrics

1. **Integration**: InnovationEngine called every 5th iteration (20% rate)
2. **Success Rate**: ≥60% of LLM-generated strategies pass validation
3. **Fallback**: Zero iteration stalls due to LLM failures (100% fallback coverage)
4. **Performance**: LLM latency <60s per generation
5. **Validation**: 20-generation test runs successfully with LLM active

## Out of Scope

- Multi-model ensemble (single model per iteration)
- Online learning from iteration results (static few-shot prompts only)
- Automatic prompt tuning (manual prompt engineering only)
- Structured innovation (YAML/JSON) - see structured-innovation-mvp spec
- Cost optimization beyond model selection (no token caching, streaming, etc.)
