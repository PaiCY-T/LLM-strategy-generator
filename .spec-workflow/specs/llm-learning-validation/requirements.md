# LLM Learning Validation - Requirements Specification

## 1. Overview

### 1.1 Purpose
Scientifically validate that LLM-driven learning can breakthrough Factor Graph template limitations through rigorous experimental design, novelty quantification, and statistical testing.

### 1.2 Success Criteria
- Prove LLM generates strategies that exceed template-based patterns
- Quantify innovation through 3-layer novelty metrics
- Achieve statistical significance (p < 0.05) in comparative analysis
- Demonstrate learning trends in LLM-driven iterations

### 1.3 Hypothesis
**H0**: LLM-Only strategies perform equivalently to Factor Graph templates
**H1**: LLM-Only strategies demonstrate superior novelty and learning capability

## 2. Functional Requirements

### 2.1 Experimental Framework
**REQ-EXP-001**: System shall support three experimental groups:
- Group A: Hybrid (30% LLM innovation rate)
- Group B: FG-Only (0% LLM innovation rate)
- Group C: LLM-Only (100% LLM innovation rate)

**REQ-EXP-002**: System shall execute experiments in two phases:
- Pilot: 50 iterations × 2 runs × 3 groups = 300 total iterations
- Full Study (conditional): 200 iterations × 5 runs × 3 groups = 3000 total iterations

**REQ-EXP-003**: Each experimental group shall run independently with isolated configuration

**REQ-EXP-004**: System shall aggregate results across all groups for comparative analysis

### 2.2 Novelty Quantification System
**REQ-NOV-001**: Layer 1 - Factor Diversity Analyzer shall:
- Extract unique factors used in strategy code
- Calculate Jaccard distance between factor sets
- Score deviation from Factor Graph template library
- Output scores in range [0, 1]

**REQ-NOV-002**: Layer 2 - Combination Pattern Detector shall:
- Identify factor combinations in strategies
- Detect novel combinations not present in templates
- Quantify combination complexity
- Output scores in range [0, 1]

**REQ-NOV-003**: Layer 3 - Logic Complexity Analyzer shall:
- Parse strategy code into Abstract Syntax Tree (AST)
- Measure cyclomatic complexity
- Detect non-linear logic patterns (np.where, custom functions, nested conditions)
- Score deviation from linear template baseline
- Output scores in range [0, 1]

**REQ-NOV-004**: Novelty Scorer shall:
- Aggregate 3-layer scores with weights: Layer1 30%, Layer2 40%, Layer3 30%
- Ensure layer correlation < 0.7 (independence validation)
- Distinguish champion strategies from templates (p < 0.05)

### 2.3 Statistical Analysis Pipeline
**REQ-STAT-001**: System shall implement Mann-Whitney U test:
- Compare Sharpe ratio distributions between groups
- Support one-tailed and two-tailed tests
- Report U-statistic, p-value, and effect size

**REQ-STAT-002**: System shall implement Mann-Kendall trend test:
- Detect monotonic trends in time-series data
- Report trend direction (increasing/decreasing/no trend)
- Calculate p-value and tau statistic

**REQ-STAT-003**: System shall perform sliding window analysis:
- 20-iteration window size
- Calculate rolling statistics (mean, std, Sharpe)
- Identify temporal patterns in learning curves

**REQ-STAT-004**: System shall generate visualizations:
- Learning curves (Sharpe over iterations) per group
- Novelty comparison box plots
- Sharpe distribution KDE overlays
- Publication-ready quality (300 DPI, clear labels)

### 2.4 Data Collection & Persistence
**REQ-DATA-001**: Extended IterationRecord shall include:
- novelty_scores: Dict[str, float] with layer breakdown
- experiment_group: str identifying A/B/C assignment
- All existing fields preserved (iteration_num, strategy_code, metrics, etc.)

**REQ-DATA-002**: System shall serialize all experimental data to JSON:
- Individual iteration records per group
- Aggregated summary statistics
- Statistical test results
- Novelty score distributions

**REQ-DATA-003**: System shall maintain data integrity:
- Atomic writes to prevent corruption
- Validation of data schema
- Backup before Pilot and Full Study execution

### 2.5 Execution & Monitoring
**REQ-EXEC-001**: Orchestrator shall:
- Load experiment configuration from YAML
- Initialize 3 LearningSystem instances with correct innovation_rates
- Execute groups sequentially to avoid resource contention
- Log progress in real-time

**REQ-EXEC-002**: System shall monitor execution:
- Track iteration success/failure rates
- Log novelty scores per iteration
- Detect anomalies (execution time, error patterns)
- Generate progress reports

**REQ-EXEC-003**: System shall implement error handling:
- Graceful degradation on iteration failures
- Retry logic for transient errors
- Maximum failure threshold: 5% per group
- Detailed error logging for debugging

## 3. Non-Functional Requirements

### 3.1 Performance
**REQ-PERF-001**: Pilot execution shall complete within 3 hours (150% buffer on 2-hour estimate)

**REQ-PERF-002**: Full Study execution shall complete within 21 hours (150% buffer on 14-hour estimate)

**REQ-PERF-003**: Statistical analysis shall complete within 5 minutes for Pilot data

**REQ-PERF-004**: Novelty scoring shall process 100 strategies per minute minimum

### 3.2 Reliability
**REQ-REL-001**: System shall achieve < 5% iteration failure rate across all groups

**REQ-REL-002**: Data persistence shall be atomic and crash-resistant

**REQ-REL-003**: System shall validate all outputs against schema before saving

### 3.3 Maintainability
**REQ-MAINT-001**: All novel code shall have unit test coverage > 80%

**REQ-MAINT-002**: Novelty quantification system shall be modular (independent layers)

**REQ-MAINT-003**: Statistical pipeline shall use established libraries (scipy, pymannkendall)

### 3.4 Usability
**REQ-USE-001**: Orchestrator shall provide clear CLI interface:
```bash
python orchestrator.py --phase [pilot|full] [--dry-run]
```

**REQ-USE-002**: System shall generate human-readable HTML reports

**REQ-USE-003**: Progress logging shall be real-time and informative

## 4. Acceptance Criteria

### 4.1 Infrastructure Track
- [ ] Config YAML loads without errors
- [ ] Orchestrator initializes 3 groups with correct innovation_rates [0.30, 0.00, 1.00]
- [ ] Extended IterationRecord serializes with new fields
- [ ] All infrastructure unit tests pass

### 4.2 Novelty System Track
- [ ] Champion strategy scores > 0.3 total novelty
- [ ] Template strategy scores < 0.15 total novelty
- [ ] All layer scores in range [0, 1]
- [ ] Layer correlation < 0.7
- [ ] Statistical discrimination: champion vs template (p < 0.05)
- [ ] AST parser handles various code patterns without errors

### 4.3 Statistical Pipeline Track
- [ ] Mann-Whitney U matches scipy reference implementation
- [ ] Mann-Kendall detects known monotonic trends
- [ ] Visualizations generate without errors
- [ ] Reports include all required sections

### 4.4 Pilot Execution Track
- [ ] 300 iterations complete successfully
- [ ] < 5% failure rate across all groups
- [ ] Execution time < 3 hours
- [ ] At least 1 strategy per group achieves Sharpe > 0.5
- [ ] Novelty scores collected for all iterations

### 4.5 Go/No-Go Decision Criteria
At least 2 of 4 criteria must be met to proceed to Full Study:

1. **Statistical Signal**: Mann-Whitney U p < 0.10 between any two groups OR Mann-Kendall trend p < 0.10 in LLM-Only
2. **Novelty Signal**: LLM-Only avg novelty > Hybrid by ≥ 15%
3. **Execution Stability**: < 5% failure rate, execution time within 150% estimate
4. **Champion Emergence**: ≥ 1 strategy per group with Sharpe > 0.5

### 4.6 Full Study Success Criteria
- [ ] Primary: LLM-Only Sharpe > FG-Only (Mann-Whitney U p < 0.05, one-tailed)
- [ ] Secondary: LLM-Only avg novelty > FG-Only by ≥ 25% (p < 0.05)
- [ ] Tertiary: LLM-Only shows upward Sharpe trend (Mann-Kendall p < 0.05)
- [ ] Champion: LLM-generated strategy with Sharpe > 1.0 and novelty > 0.5

## 5. Constraints & Assumptions

### 5.1 Constraints
- Single WSL machine for execution (no distributed computing)
- Budget: $3 (Pilot) to $12 (Pilot + Full Study)
- Timeline: 5-7 days development + execution
- Existing learning system infrastructure must be preserved

### 5.2 Assumptions
- Factor Graph template library is accessible and documented
- Existing learning system accepts innovation_rate parameter
- Python packages available: scipy, pymannkendall, matplotlib, ast (built-in)
- Champion strategy JSON is accessible for validation
- Backtesting engine is stable and reliable

### 5.3 Out of Scope
- Multi-machine distributed execution
- Real-time dashboard (console logging only)
- Automated hyperparameter tuning
- Integration with production trading system
- Automated report publication

## 6. Dependencies

### 6.1 Internal Dependencies
- `src/learning/iteration_history.py` - IterationRecord dataclass
- `config/learning_system.yaml` - LLM configuration
- `artifacts/data/champion_strategy.json` - Validation baseline
- Existing backtesting engine
- Factor Graph template library

### 6.2 External Dependencies
- scipy >= 1.7.0 (Mann-Whitney U test)
- pymannkendall >= 1.4.0 (Mann-Kendall trend test)
- matplotlib >= 3.5.0 (Visualization)
- Python 3.8+ (AST parsing, type hints)

### 6.3 Data Dependencies
- Historical market data for backtesting
- Factor Graph template definitions
- Champion strategy baseline for novelty validation

## 7. Validation Strategy

### 7.1 Pre-Execution Validation
- [ ] Confirm Factor Graph template library location/format
- [ ] Verify champion strategy JSON accessible
- [ ] Test innovation_rate parameter acceptance
- [ ] Check all Python packages installed
- [ ] Backup learning_system.yaml configuration

### 7.2 Novelty System Validation (Checkpoint: End Day 3)
- [ ] Test against champion strategy (novelty > 0.3)
- [ ] Test against template strategy (novelty < 0.15)
- [ ] Validate all layer scores in [0, 1]
- [ ] Confirm layer independence (correlation < 0.7)
- [ ] Statistical discrimination test (p < 0.05)

### 7.3 Dry Run Validation (Checkpoint: End Day 4)
- [ ] Execute 5 iterations per group (15 total)
- [ ] Verify novelty scoring works end-to-end
- [ ] Validate data collection and serialization
- [ ] Confirm execution time estimates
- [ ] Check for errors/exceptions

### 7.4 Pilot Validation (Checkpoint: End Day 5)
- [ ] Review go/no-go decision criteria
- [ ] Analyze Pilot results comprehensively
- [ ] Calculate statistical power achieved
- [ ] Document decision rationale
- [ ] Prepare Full Study plan if GO decision

## 8. Risk Management

### 8.1 High Risk: Novelty System Validation Failure
- **Impact**: Cannot quantify innovation accurately
- **Probability**: Medium (novel implementation)
- **Mitigation**: Extensive unit testing Days 2-3
- **Contingency**: Simplify to Layer 1 only (factor diversity)
- **Decision Point**: End of Day 3

### 8.2 Medium Risk: Execution Time Overrun
- **Impact**: Delays Full Study decision
- **Probability**: Low (dry run validation)
- **Mitigation**: Dry run on Day 4, 50% time buffer
- **Contingency**: Reduce Pilot to 30×2 iterations
- **Decision Point**: End of Day 4

### 8.3 Low Risk: Statistical Test Implementation Error
- **Impact**: Invalid results, need rework
- **Probability**: Very Low (using scipy/pymannkendall)
- **Mitigation**: Unit tests with known distributions
- **Contingency**: Manual calculation verification
- **Decision Point**: Day 4 validation

## 9. Success Metrics Summary

### 9.1 Minimum Viable Success
- Pilot completes with < 5% failure rate
- Novelty system distinguishes champion from templates
- At least 1 group shows learning signal

### 9.2 Target Success
- Pilot → Full Study executed
- LLM-Only shows higher novelty (p < 0.05)
- Learning trend detected (p < 0.05)
- Champion strategy with Sharpe > 1.0

### 9.3 Stretch Success
- Publication-grade statistical results
- Novelty patterns reveal innovation mechanisms
- Results guide Phase 4 development priorities
