# Requirements Document

## Introduction

The Phase 3 Learning Iteration feature implements a true **iterative learning system** where AI-generated strategies learn from previous execution results. Unlike Phase 1 (static validation) and Phase 2 (execution testing), Phase 3 enables the system to **improve strategies over multiple iterations** by feeding backtest performance metrics back to the LLM as learning signals.

**Purpose**: Enable the autonomous learning loop to generate progressively better trading strategies by learning from execution history, using real LLM APIs to incorporate feedback from Sharpe ratios, returns, and failure patterns.

**Value**: Transforms the system from a one-shot generator to an adaptive learning system that can discover high-performing strategies through iterative refinement, validating the core hypothesis that LLM-based evolution can improve quantitative trading strategies.

## Alignment with Product Vision

This feature directly implements the **iterative learning system vision**:

1. **Autonomous Evolution**: LLM learns from previous iterations without human intervention
2. **Performance-Driven**: Sharpe ratio and returns guide strategy improvements
3. **Failure Learning**: Execution errors inform constraint refinement
4. **Champion Tracking**: Best strategies serve as reference points for future iterations
5. **Scalability**: System can run hundreds of iterations to find optimal strategies

This is the **critical capability** that distinguishes this system from static strategy generators.

## Requirements

### Requirement 1: Iteration History Management

**User Story:** As the learning system, I want to persist and retrieve iteration history, so that LLMs can learn from past successes and failures across multiple runs.

#### Acceptance Criteria

1. WHEN an iteration completes THEN the system SHALL save strategy code, execution result, metrics, and classification level to history
2. WHEN history is saved THEN the system SHALL use JSONL format (one JSON object per line) for efficient append operations
3. WHEN retrieving history THEN the system SHALL load the N most recent successful iterations (configurable, default N=5)
4. WHEN loading history THEN the system SHALL include champion strategy prominently if it exists
5. WHEN history file doesn't exist THEN the system SHALL create it and start with iteration 0
6. WHEN history is corrupted THEN the system SHALL log error and continue with empty history (degraded mode)

### Requirement 2: Feedback Generation

**User Story:** As the LLM, I want clear, actionable feedback from previous iterations, so that I can understand what worked, what failed, and how to improve.

#### Acceptance Criteria

1. WHEN generating feedback THEN the system SHALL include:
   - Previous strategy's Sharpe Ratio (if available)
   - Classification level reached (Level 0/1/2/3)
   - Execution outcome (success, timeout, error)
   - Error category and message (if failed)
2. WHEN strategy succeeded with positive Sharpe THEN feedback SHALL highlight successful patterns (e.g., "factor combinations", "filters used")
3. WHEN strategy failed THEN feedback SHALL provide actionable guidance (e.g., "avoid infinite loops", "check dataset availability")
4. WHEN multiple iterations exist THEN feedback SHALL summarize trend (e.g., "improving Sharpe from 0.5 to 0.8")
5. WHEN champion exists THEN feedback SHALL reference champion's Sharpe as target to beat
6. WHEN feedback exceeds 500 words THEN the system SHALL summarize to prevent prompt overflow

### Requirement 3: LLM Integration for Learning

**User Story:** As the system operator, I want the learning loop to use real LLM APIs (Google AI, OpenRouter), so that genuine learning occurs through natural language feedback.

#### Acceptance Criteria

1. WHEN generating a new strategy THEN the system SHALL call LLM API with iteration history as context
2. WHEN LLM call succeeds THEN the system SHALL extract Python code from response
3. WHEN LLM call fails THEN the system SHALL retry up to 3 times with exponential backoff
4. WHEN all retries fail THEN the system SHALL fall back to Factor Graph mutation
5. WHEN using Google AI THEN the system SHALL try Gemini first, fall back to OpenRouter if quota exceeded
6. WHEN LLM returns invalid code THEN the system SHALL classify as generation failure and try again with stronger constraints
7. WHEN LLM cost tracking is enabled THEN the system SHALL log token usage and estimated cost per iteration

### Requirement 4: Champion Strategy Tracking

**User Story:** As the learning system, I want to track the best-performing strategy (champion), so that I can use it as a reference point and prevent regression.

#### Acceptance Criteria

1. WHEN an iteration achieves higher Sharpe Ratio than current champion THEN the system SHALL update champion
2. WHEN champion is updated THEN the system SHALL save strategy code, metrics, and timestamp to `champion.json`
3. WHEN no champion exists THEN the system SHALL use first Level 3 strategy (Sharpe > 0) as initial champion
4. WHEN generating feedback THEN the system SHALL include champion's Sharpe as improvement target
5. WHEN champion has been stale for N iterations (default 20) THEN the system SHALL flag for review
6. WHEN multiple strategies have equal Sharpe THEN the system SHALL prefer the one with lower Max Drawdown

### Requirement 5: Iteration Control and Configuration

**User Story:** As a system operator, I want to configure iteration count, LLM model, and learning parameters, so that I can control execution costs and experiment with different settings.

#### Acceptance Criteria

1. WHEN starting the loop THEN the system SHALL read configuration from YAML file (`config/learning_system.yaml`)
2. WHEN configuration specifies max iterations THEN the system SHALL stop after reaching that limit
3. WHEN configuration specifies LLM model THEN the system SHALL use that model for all generations
4. WHEN configuration enables innovation mode THEN the system SHALL use LLM-based generation (vs pure Factor Graph)
5. WHEN configuration specifies innovation rate THEN the system SHALL use LLM for X% of iterations, Factor Graph for (100-X)%
6. WHEN iteration limit is reached THEN the system SHALL save final results and generate summary report

### Requirement 6: Learning Loop Integration

**User Story:** As the autonomous loop, I want to integrate Phase 2 execution with Phase 3 learning seamlessly, so that execution results automatically feed back into strategy generation.

#### Acceptance Criteria

1. WHEN loop starts iteration N THEN the system SHALL:
   - Load history from previous N-1 iterations
   - Generate feedback from history
   - Call LLM or Factor Graph with feedback
   - Execute generated strategy (Phase 2)
   - Extract metrics and classify (Phase 2)
   - Save to history for next iteration
2. WHEN execution fails THEN the system SHALL continue to next iteration (not crash entire loop)
3. WHEN generating strategy THEN the system SHALL use timeout to prevent LLM API hangs (default 60 seconds)
4. WHEN loop completes THEN the system SHALL generate summary with champion, success rates, and Sharpe progression
5. WHEN loop is interrupted THEN the system SHALL save progress and allow resumption from last completed iteration

## Non-Functional Requirements

### Code Architecture and Modularity

- **Single Responsibility**: Separate history management, feedback generation, LLM integration, and champion tracking
- **Modular Design**: Create reusable components that work with existing Phase 2 executor
- **Clear Interfaces**: Define dataclasses for IterationRecord, FeedbackContext, ChampionStrategy
- **Dependency Management**: Minimize new dependencies, reuse existing LLM client code

### Performance

- **PERF-1**: History loading must complete in <1 second for 1000 iterations
- **PERF-2**: LLM API call (with retries) must complete within 60 seconds or timeout
- **PERF-3**: Feedback generation must complete in <2 seconds
- **PERF-4**: Champion update check must complete in <0.5 seconds

### Reliability

- **REL-1**: History file corruption must not crash the system (degrade gracefully)
- **REL-2**: LLM API failures must fall back to Factor Graph (no iteration lost)
- **REL-3**: Iteration failures must not prevent subsequent iterations from running
- **REL-4**: Loop interruption must save state cleanly for resumption

### Security

- **SEC-1**: LLM API keys must be loaded from environment variables, never hardcoded
- **SEC-2**: History files must not contain API keys or credentials
- **SEC-3**: Generated strategies must be validated before execution (Phase 2 validation)
- **SEC-4**: LLM prompts must not include sensitive user data

### Usability

- **USE-1**: Progress must show iteration number, success rate, and current champion Sharpe
- **USE-2**: Feedback must be human-readable for debugging (not just machine-optimized)
- **USE-3**: Configuration errors must provide clear guidance (e.g., "Invalid model name: gpt-6, use gpt-5 or gemini-2.5-flash")
- **USE-4**: Final summary must be actionable (e.g., "Champion Sharpe: 1.2, recommend production deployment")

## Success Metrics

**Primary Success Criteria**:
- Achieve measurable Sharpe Ratio improvement over 20 iterations (e.g., from 0.5 to 1.0+)
- Maintain ≥70% execution success rate (Level 1+) across iterations
- LLM-based learning outperforms pure Factor Graph mutation (A/B test)

**Secondary Success Criteria**:
- Champion strategy remains stable for last 10 iterations (convergence)
- Execution errors decrease over time (learning from failures)
- Average Sharpe Ratio increases monotonically or with minor fluctuations

**Exit Criteria for Phase 3**:
- Complete 20+ iteration run successfully
- Demonstrate clear learning (Sharpe improvement or error reduction)
- Generate comprehensive results report with champion strategy
- System ready for 100+ iteration production runs

## Phased Implementation Strategy

**Decision**: Hybrid Approach (Option C) - Week 1 Refactoring + Week 2+ Feature Development

**Rationale**: Deep code analysis revealed that `autonomous_loop.py` is **2,981 lines** (50% larger than estimated ~2,000), exhibiting God Object anti-pattern with 12+ concerns. Direct feature development on this codebase carries high risk of introducing bugs and increasing technical debt.

### Phase 1: Foundation Refactoring (Week 1, Days 1-5)

**Objective**: Extract critical infrastructure modules to eliminate code duplication and establish clean boundaries before feature development.

**Scope**:
1. **ConfigManager Extraction** (Day 1)
   - **Problem**: Config loading duplicated 6 times (60 lines)
   - **Solution**: Singleton pattern for centralized config management
   - **Impact**: Eliminates 60 lines of duplication, simplifies testing
   - **Tests**: 8 unit tests, 90% coverage target

2. **LLMClient Extraction** (Days 2-3)
   - **Problem**: LLM initialization logic (lines 637-781, ~145 lines) embedded in monolithic class
   - **Solution**: Extract to `src/learning/llm_client.py`
   - **Impact**: Cleanly separates LLM concerns, uses ConfigManager
   - **Tests**: 12 unit tests, 95% coverage target

3. **IterationHistory Verification** (Days 4-5)
   - **Status**: Already extracted, needs verification
   - **Scope**: Validate existing tests, add missing scenarios (concurrent access, error handling)
   - **Tests**: 6+ unit tests, 90% coverage target

**Success Criteria for Week 1**:
- [ ] ConfigManager: 60 lines duplication eliminated, 8 tests passing
- [ ] LLMClient: 145 lines extracted, 12 tests passing, uses ConfigManager
- [ ] IterationHistory: 6+ tests passing, API documentation complete
- [ ] autonomous_loop.py: Reduced by ~205 lines (60 + 145)
- [ ] All integration tests passing
- [ ] Overall test coverage: >88%

### Phase 2: Feature Development (Week 2+, Days 6+)

**Objective**: Implement Phase 3 learning iteration features on refactored foundation.

**Approach**: Develop new features using clean, modular components:
- Use ConfigManager for all configuration loading
- Use LLMClient for all LLM interactions
- Use IterationHistory for persistence
- Follow modular design patterns established in Week 1

**Benefits**:
- Lower risk of bugs (clean interfaces)
- Faster development (reusable components)
- Better testability (isolated concerns)
- Easier maintenance (single responsibility)

**Scope**: All original Phase 3 requirements (Req 1-6) implemented on refactored base.

### Parallel Execution Opportunities

**Fully Parallel** (can start simultaneously):
- ConfigManager extraction
- IterationHistory verification

**Semi-Parallel** (can start but benefits from waiting):
- LLMClient extraction (recommended after ConfigManager to use it directly)

**Recommended Execution**:
```
Day 1: ConfigManager (blocking) + IterationHistory (parallel)
Days 2-3: LLMClient (uses ConfigManager)
Days 4-5: Integration testing, documentation, Week 1 checkpoint
Week 2+: Feature development on clean foundation
```

### Deferred Refactoring (Post-Phase 3)

**Not in immediate scope**:
- ChampionTracker extraction (~865 lines) - can develop features alongside existing code
- IterationExecutor decomposition (556-line method) - revisit after Phase 3 feature validation
- Full LearningLoop extraction (~200 lines) - final step after all features working

**Rationale**: Week 1 refactoring provides sufficient foundation to safely develop Phase 3 features. Additional refactoring can proceed incrementally as needed.

---

## Dependencies

**Required Before Phase 3**:
- Phase 2 backtest execution framework completed
- `BacktestExecutor`, `MetricsExtractor`, `SuccessClassifier` operational
- Generated strategies from Phase 1 available (for initial testing)

**External Dependencies**:
- Google AI API (Gemini) with valid API key
- OpenRouter API with valid API key (fallback)
- Finlab session authenticated
- `artifacts/data/innovations.jsonl` for history storage (will be created)
- `champion.json` for champion tracking (will be created)

## Risks and Mitigation

**Risk 1**: LLM generates strategies that always fail
- **Mitigation**: Strong prompt engineering with examples, fallback to Factor Graph

**Risk 2**: LLM API costs exceed budget
- **Mitigation**: Token usage tracking, configurable innovation rate, model selection

**Risk 3**: No learning observed (Sharpe stays flat)
- **Mitigation**: Increase iteration count to 50+, try stronger models (GPT-5, Claude Opus)

**Risk 4**: History file grows too large (>100MB)
- **Mitigation**: Implement history rotation (keep last 1000 iterations), compress old data

## Future Enhancements (Out of Scope for Phase 3)

- Multi-objective optimization (Sharpe + Drawdown + Win Rate)
- Ensemble strategies (combine top 5 champions)
- Transfer learning (use champion from one market as seed for another)
- Real-time learning dashboard with Sharpe progression charts
- Automated hyperparameter tuning for LLM prompts
