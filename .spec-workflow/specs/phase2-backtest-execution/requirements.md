# Requirements Document

## Introduction

The Phase 2 Backtest Execution feature validates that AI-generated trading strategies actually execute successfully with real finlab data and produce measurable performance metrics. Currently, we have only validated that strategies pass static code validation (correct dataset keys), but we have NOT tested whether they execute without runtime errors or produce valid backtest results. This feature is critical to determine the real success rate of our strategy generation system and unblock Phase 3 learning capabilities.

**Purpose**: Execute 20 previously generated strategies with real finlab data and measure their success rates across three levels: execution completion, valid metrics extraction, and positive performance.

**Value**: Provides factual evidence of system effectiveness, identifies execution bottlenecks, establishes baseline performance metrics for Phase 3 learning, and validates the end-to-end pipeline.

## Alignment with Product Vision

This feature directly supports the iterative learning system vision by:
1. **Validation**: Proving that generated strategies are not just syntactically valid but executionally viable
2. **Measurement**: Establishing quantitative metrics (Sharpe ratio, returns, drawdown) for learning feedback
3. **Quality Control**: Identifying failure patterns that need to be addressed before scaling to 1000+ iterations
4. **Learning Foundation**: Providing the performance data needed to implement Phase 3 feedback loops

## Requirements

### Requirement 1: Strategy Execution Framework

**User Story:** As a system developer, I want to execute generated strategies in a safe sandbox environment, so that I can measure their real-world performance without risking system stability.

#### Acceptance Criteria

1. WHEN a strategy code string is provided THEN the system SHALL execute it within a 7-minute timeout limit
2. IF a strategy fails to complete within timeout THEN the system SHALL classify it as "timeout error" and continue with next strategy
3. WHEN executing strategy code THEN the system SHALL provide access to finlab data context (data.get, data.indicator, sim functions)
4. IF a runtime error occurs THEN the system SHALL catch the exception, log the error details, and classify the failure type
5. WHEN all 20 strategies complete THEN the system SHALL generate a comprehensive results report with success/failure breakdown

### Requirement 2: Performance Metrics Collection

**User Story:** As a system analyst, I want to extract standardized performance metrics from backtest results, so that I can compare strategies objectively and identify successful patterns.

#### Acceptance Criteria

1. WHEN a strategy executes successfully THEN the system SHALL extract Sharpe Ratio from the sim() report
2. WHEN a strategy executes successfully THEN the system SHALL extract Total Return percentage
3. WHEN a strategy executes successfully THEN the system SHALL extract Maximum Drawdown percentage
4. WHEN a strategy executes successfully THEN the system SHALL extract Win Rate (if available)
5. IF metrics are NaN or missing THEN the system SHALL classify as "invalid metrics" failure
6. WHEN metrics are valid THEN the system SHALL store them in structured JSON format with strategy ID

### Requirement 3: Three-Level Success Classification

**User Story:** As a quality engineer, I want strategies classified into three success levels, so that I can understand the quality distribution and set appropriate targets for Phase 3.

#### Acceptance Criteria

1. WHEN a strategy completes without runtime errors THEN it SHALL be classified as "Level 1: Execution Success"
2. WHEN a strategy has valid metrics (Sharpe exists and is not NaN) THEN it SHALL be classified as "Level 2: Valid Metrics"
3. WHEN a strategy has Sharpe Ratio > 0 THEN it SHALL be classified as "Level 3: Positive Performance"
4. WHEN classifying strategies THEN the system SHALL count and report percentages for each level
5. IF Level 1 success rate < 60% THEN the system SHALL flag for investigation before Phase 3
6. IF Level 3 success rate < 40% THEN the system SHALL recommend prompt template improvements

### Requirement 4: Error Handling and Classification

**User Story:** As a system debugger, I want detailed error logs with categorization, so that I can identify and fix common failure patterns.

#### Acceptance Criteria

1. WHEN a runtime error occurs THEN the system SHALL capture the full stack trace
2. WHEN an error is caught THEN the system SHALL classify it into categories: timeout, missing data, calculation error, syntax error, or other
3. WHEN multiple strategies fail with similar errors THEN the system SHALL group them and report the pattern
4. WHEN generating the report THEN the system SHALL include error frequency distribution
5. IF a critical error pattern affects >20% of strategies THEN the system SHALL highlight it as "requires immediate fix"

### Requirement 5: Results Reporting and Analysis

**User Story:** As a project stakeholder, I want a comprehensive results report with visualizations, so that I can make informed decisions about Phase 3 readiness.

#### Acceptance Criteria

1. WHEN all strategies finish THEN the system SHALL generate a JSON results file with all metrics
2. WHEN generating the report THEN the system SHALL include success rate for each level (L1, L2, L3)
3. WHEN generating the report THEN the system SHALL include average Sharpe ratio for successful strategies
4. WHEN generating the report THEN the system SHALL include execution time statistics (min, max, average)
5. IF web search is available THEN the system SHALL compare results to industry benchmarks for quantitative strategies

## Non-Functional Requirements

### Code Architecture and Modularity
- **Single Responsibility Principle**: Separate execution engine, metrics extractor, classifier, and reporter into distinct modules
- **Modular Design**: Create reusable components that can be used in Phase 3 learning loop
- **Dependency Management**: Minimize dependencies on specific finlab versions, use stable API patterns
- **Clear Interfaces**: Define clean contracts between executor and metrics extractor (e.g., ExecutionResult dataclass)

### Performance
- **PERF-1**: Each strategy execution must complete within 7 minutes or timeout
- **PERF-2**: Total test execution (20 strategies) should complete within 140 minutes maximum
- **PERF-3**: Metrics extraction must complete within 5 seconds per strategy
- **PERF-4**: Results report generation must complete within 10 seconds

### Security
- **SEC-1**: Code execution must use Python exec() with restricted globals/locals context
- **SEC-2**: No file I/O operations should be allowed in executed strategies (sandbox restriction)
- **SEC-3**: Network access should be restricted during strategy execution
- **SEC-4**: Finlab data access should use existing authenticated sessions, no credential passing

### Reliability
- **REL-1**: System must handle all 20 strategies without crashing the test runner
- **REL-2**: Failure of one strategy must not affect execution of subsequent strategies
- **REL-3**: Results must be persisted to disk before process termination
- **REL-4**: Re-running the test should produce deterministic results (given same data)

### Usability
- **USE-1**: Progress must be visible during execution (e.g., "Processing strategy 5/20...")
- **USE-2**: Results report must be human-readable markdown in addition to JSON
- **USE-3**: Error messages must be actionable (e.g., "Missing dataset: etl:adj_close - Run data sync")
- **USE-4**: Dashboard integration should show real-time progress (optional enhancement)

## Success Metrics

**Primary Success Criteria**:
- Achieve ≥ 60% Level 1 success rate (execution completes)
- Achieve ≥ 40% Level 3 success rate (positive Sharpe ratio)

**Secondary Success Criteria**:
- Identify and document all error patterns
- Provide baseline metrics for Phase 3 design
- Complete test execution within reasonable time (< 140 minutes)

**Exit Criteria for Phase 2**:
- All 20 strategies tested
- Results report generated and reviewed
- Decision made on Phase 3 readiness based on success rates
