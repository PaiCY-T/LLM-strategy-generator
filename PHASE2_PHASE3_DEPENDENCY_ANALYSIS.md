# Phase 2 & Phase 3 Task Dependency Analysis

**Generated**: 2025-10-31
**Source**: Gemini-2.5-Pro Analysis

## Phase 2: Backtest Execution - Dependencies

### Critical Path
**2.1 → 3.1 → 4.1 → 5.1 → 5.2 → 7.1 → 7.2 → 7.3**

### Parallel Execution Groups

#### Group 1: Initial Development (Can start immediately, parallel)

**Stream 1: Execution Core**
- 1.1: Create BacktestExecutor class
  - DependsOn: []
  - ParallelKey: stream_1_execution
- 1.2: Add timeout mechanism testing
  - DependsOn: [1.1]
  - ParallelKey: stream_1_execution
- 1.3: Add error classification patterns
  - DependsOn: []
  - ParallelKey: stream_1_execution

**Stream 2: Metrics Extraction**
- 2.1: Extend MetricsExtractor class
  - DependsOn: []
  - ParallelKey: stream_2_metrics
- 2.2: Add metrics extraction tests
  - DependsOn: [2.1]
  - ParallelKey: stream_2_metrics

**Stream 4: Setup (Independent)**
- 6.1: Verify generated strategies exist
  - DependsOn: []
  - ParallelKey: stream_4_setup
- 6.2: Verify finlab session authentication
  - DependsOn: []
  - ParallelKey: stream_4_setup

#### Group 2: Dependent Development (Requires Stream 2 completion)

**Stream 3: Classification & Reporting**
- 3.1: Create SuccessClassifier
  - DependsOn: [2.1]
  - ParallelKey: stream_3_classification
- 3.2: Add classification tests
  - DependsOn: [3.1]
  - ParallelKey: stream_3_classification
- 4.1: Create ResultsReporter class
  - DependsOn: [2.1, 3.1]
  - ParallelKey: stream_3_classification
- 4.2: Add report generation tests
  - DependsOn: [4.1]
  - ParallelKey: stream_3_classification

#### Group 3: Integration (Requires all components)

- 5.1: Create Phase2TestRunner
  - DependsOn: [1.1, 1.3, 2.1, 3.1, 4.1]
  - ParallelKey: integration
- 5.2: Add runner integration tests
  - DependsOn: [5.1]
  - ParallelKey: integration

#### Group 4: Execution (Sequential)

- 7.1: Run 3-strategy pilot test
  - DependsOn: [5.2, 6.1, 6.2]
  - ParallelKey: execution
- 7.2: Run full 20-strategy execution
  - DependsOn: [7.1]
  - ParallelKey: execution
- 7.3: Analyze results and generate summary
  - DependsOn: [7.2]
  - ParallelKey: execution

#### Group 5: Documentation (Continuous, finalize after 7.3)

- 8.1: Document execution framework
  - DependsOn: [7.3]
  - ParallelKey: documentation
- 8.2: Add API documentation
  - DependsOn: [7.3]
  - ParallelKey: documentation
- 8.3: Code review and optimization
  - DependsOn: [7.3]
  - ParallelKey: documentation

---

## Phase 3: Learning Iteration - Dependencies

### Critical Path
**(1.1 or 4.1) → 2.1 → 5.1 → 6.1 → 7.1 → 7.2 → 7.3**

### Parallel Execution Groups

#### Group 1: Core Independent Components (Can start immediately, all parallel)

**Stream A1: History Management**
- 1.1: Create IterationHistory class
  - DependsOn: []
  - ParallelKey: stream_a1_history
- 1.2: Add history save/load tests
  - DependsOn: [1.1]
  - ParallelKey: stream_a1_history
- 1.3: Add history corruption handling tests
  - DependsOn: [1.1]
  - ParallelKey: stream_a1_history

**Stream A2: LLM Integration**
- 3.1: Create LLMClient wrapper class
  - DependsOn: []
  - ParallelKey: stream_a2_llm
- 3.2: Add LLM retry and fallback tests
  - DependsOn: [3.1]
  - ParallelKey: stream_a2_llm
- 3.3: Add LLM code extraction tests
  - DependsOn: [3.1]
  - ParallelKey: stream_a2_llm

**Stream A3: Champion Tracking**
- 4.1: Create ChampionTracker class
  - DependsOn: []
  - ParallelKey: stream_a3_champion
- 4.2: Add champion update tests
  - DependsOn: [4.1]
  - ParallelKey: stream_a3_champion
- 4.3: Add staleness detection tests
  - DependsOn: [4.1]
  - ParallelKey: stream_a3_champion

#### Group 2: Dependent Component (Requires interfaces from Group 1)

**Stream B: Feedback Generation**
- 2.1: Create FeedbackGenerator class
  - DependsOn: [1.1, 4.1]
  - ParallelKey: stream_b_feedback
- 2.2: Add feedback generation tests
  - DependsOn: [2.1]
  - ParallelKey: stream_b_feedback
- 2.3: Add trend analysis tests
  - DependsOn: [2.1]
  - ParallelKey: stream_b_feedback

#### Group 3: Core Logic Integration (Requires all components)

**Stream C: Iteration Executor**
- 5.1: Create IterationExecutor class
  - DependsOn: [1.1, 2.1, 3.1, 4.1, Phase2.5.1]
  - ParallelKey: stream_c_executor
- 5.2.1: Integrate Factor Graph as fallback
  - DependsOn: [5.1]
  - ParallelKey: stream_c_executor
- 5.2.2: Add unit tests for Factor Graph fallback
  - DependsOn: [5.2.1]
  - ParallelKey: stream_c_executor
- 5.2.3: Validate Factor Graph output compatibility
  - DependsOn: [5.2.1]
  - ParallelKey: stream_c_executor
- 5.3: Add iteration executor tests
  - DependsOn: [5.2.1]
  - ParallelKey: stream_c_executor

#### Group 4: Orchestration (Requires executor)

**Stream D: Learning Loop**
- 6.1: Refactor into LearningLoop
  - DependsOn: [5.1]
  - ParallelKey: stream_d_loop
- 6.2: Add configuration loading
  - DependsOn: [6.1]
  - ParallelKey: stream_d_loop
- 6.3: Implement loop resumption logic
  - DependsOn: [6.1, 1.1]
  - ParallelKey: stream_d_loop
- 6.4: Add interruption and resumption tests
  - DependsOn: [6.3]
  - ParallelKey: stream_d_loop
- 6.5: Add learning loop tests
  - DependsOn: [6.1, 6.2]
  - ParallelKey: stream_d_loop

#### Group 5: End-to-End Testing (Sequential)

- 7.1: Create 5-iteration smoke test
  - DependsOn: [6.1]
  - ParallelKey: e2e_testing
- 7.2: Create 20-iteration validation test
  - DependsOn: [7.1]
  - ParallelKey: e2e_testing
- 7.3: Analyze learning effectiveness
  - DependsOn: [7.2]
  - ParallelKey: e2e_testing

#### Group 6: Documentation & Refinement (Continuous)

- 8.1: Update README and Steering Docs
  - DependsOn: [7.3]
  - ParallelKey: documentation
- 8.2: Add architecture documentation
  - DependsOn: [7.3]
  - ParallelKey: documentation
- 8.3: Create learning system guide
  - DependsOn: [7.3]
  - ParallelKey: documentation

- 9.1: Validate refactoring against original
  - DependsOn: [6.1]
  - ParallelKey: validation
- 9.2: Performance comparison tests
  - DependsOn: [6.1]
  - ParallelKey: validation
- 9.3: Create refactoring summary
  - DependsOn: [9.1, 9.2]
  - ParallelKey: validation

---

## Recommended Execution Strategy

### Phase 2 Execution Plan

**Week 1: Parallel Component Development**
- Team A: Stream 1 (Execution Core) - 3 tasks
- Team B: Stream 2 (Metrics) - 2 tasks
- DevOps: Stream 4 (Setup) - 2 tasks

**Week 2: Dependent Development**
- Team A + B: Stream 3 (Classification & Reporting) - 4 tasks

**Week 3: Integration & Testing**
- Combined Team: Integration (2 tasks) + Execution (3 tasks)

**Week 4: Documentation & Finalization**
- All: Documentation (3 tasks)

**Total Estimated Time**: 4 weeks with 2 developers

### Phase 3 Execution Plan

**Week 1-2: Parallel Component Development**
- Developer 1: Stream A1 (History) - 3 tasks
- Developer 2: Stream A2 (LLM) - 3 tasks
- Developer 3: Stream A3 (Champion) - 3 tasks
(9 tasks total, can be done in parallel)

**Week 2-3: Dependent Component**
- Developer 1: Stream B (Feedback) - 3 tasks
(Starts after interfaces from Week 1 are defined)

**Week 3-4: Integration**
- Senior Developer: Stream C (Executor) + Stream D (Loop) - 10 tasks

**Week 5: End-to-End Testing**
- QA Team: E2E Testing - 3 tasks (sequential)

**Week 6: Documentation & Validation**
- All: Documentation + Validation - 6 tasks

**Total Estimated Time**: 6 weeks with 3 developers

---

## Key Insights

### Phase 2
- **Most Parallelizable**: 7 tasks can start immediately (1.1, 1.3, 2.1, 6.1, 6.2)
- **Longest Chain**: 8 tasks on critical path
- **Bottleneck**: MetricsExtractor (2.1) blocks Classification and Reporting

### Phase 3
- **Most Parallelizable**: 9 tasks can start immediately (all Group 1)
- **Longest Chain**: 7 tasks on critical path
- **Bottleneck**: IterationExecutor (5.1) blocks all orchestration work

### Time Savings with Parallelization

**Phase 2**:
- Sequential: ~12 weeks (42 tasks × 2 days avg)
- With 2-3 developers in parallel: ~4 weeks
- **Time Saved**: 67%

**Phase 3**:
- Sequential: ~18 weeks (60+ tasks × 2 days avg)
- With 3-4 developers in parallel: ~6 weeks
- **Time Saved**: 67%

**Combined Project**:
- Sequential: 30 weeks
- Parallel: 10 weeks
- **Total Time Saved**: 67% (20 weeks)
