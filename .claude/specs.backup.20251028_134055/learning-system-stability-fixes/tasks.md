# Implementation Tasks: Learning System Stability Fixes

## Task Overview

This implementation follows a **2-phase approach** addressing critical stability issues identified in the 5-iteration Zen Challenge test.

**Phase 1 (Stories 6→5→3→7→8)**: ✅ **COMPLETE** (2025-10-12) - Foundation infrastructure for reliable testing and validation
**Phase 2 (Stories 1→2→4→9)**: ✅ **COMPLETE** (2025-10-12) - Learning system optimization and reliability

**Implementation Strategy**: Atomic tasks organized by functional area, each completable in 15-30 minutes with clear input/output and minimal context switching.

## Steering Document Compliance

**Structure.md Alignment**:
- New validation components → `src/validation/`
- Data pipeline components → `src/data/`
- Monitoring components → `src/monitoring/`
- Configuration management → `src/config/`
- Recovery mechanisms → `src/recovery/`
- Integration tests → `tests/integration/`

**Tech.md Alignment**:
- Type hints for all new classes (Python 3.8+)
- Dataclasses for structured data
- Comprehensive docstrings (Google style)
- Unit tests with pytest
- Integration with existing codebase patterns

## Atomic Task Requirements
- **File Scope**: 1-3 related files maximum
- **Time Boxing**: 15-30 minutes per task
- **Single Purpose**: One testable outcome
- **Specific Files**: Exact file paths specified
- **Agent-Friendly**: Clear dependencies and minimal context switching

## Design v1.1 Integration Notes (P0 Enhancements)

**IMPORTANT**: This task list aligns with design.md v1.1, which includes critical P0 enhancements. During implementation, ensure components follow these contracts:

### Component Interfaces (design.md lines 149-274)
- **Validation Components** (MetricValidator, SemanticValidator, PreservationValidator) must implement:
  - `ValidationHook` Protocol: `validate(code, execution_result, context) -> ValidationReport`
  - Return `ValidationReport` dataclass with: `passed, component, checks_performed, failures, warnings, metadata, timestamp`
  - Raise `ValidationSystemError` for infrastructure failures (not validation failures)

- **Monitoring Components** (VarianceMonitor, DataPipelineIntegrity) must implement:
  - `MonitoringHook` Protocol: `update(iteration_num, metrics, champion) -> Optional[MonitoringAlert]`
  - Return `MonitoringAlert` dataclass with: `severity, component, message, context, timestamp`
  - Never throw exceptions (non-blocking monitoring)

### Error Handling (design.md lines 960-1010)
- **Failure Mode Matrix**: Each component must handle 3 failure types:
  - **Logical Failure**: Validation returns `passed=False` → reject candidate, keep current champion
  - **System Error**: Infrastructure exception → safe state, reject candidate, critical alert
  - **Non-Critical Failure**: Log and continue, no champion impact
- **Safe State Protocol**: On critical errors: reject candidate, preserve champion, log full context, raise alert
- **Retry Strategies**: Finlab API (3x), File I/O (2x), Validation hooks (no retry - fail fast)

### Data Models (design.md lines 886-1225)
- **Enhanced IterationRecord**: Must include:
  - `data_provenance: Optional[DataProvenance]` (Story 7)
  - `config_snapshot: Optional[ExperimentConfig]` (Story 8)
  - `validation_reports: List[ValidationReport]` (Stories 5, 6)
  - `monitoring_alerts: List[MonitoringAlert]` (Story 1)

- **PreservationReport** (Story 2): Use complete schema with:
  - `behavioral_checks: List[BehavioralCheck]` (check_name, passed, champion_value, generated_value, deviation_pct)
  - `behavioral_similarity_score: float` (0.0-1.0)
  - `false_positive_risk: float` (0.0-1.0)

- **Statistical Models** (Story 3): Implement complete schemas:
  - `EffectSizeAnalysis` (cohens_d, interpretation, confidence_interval)
  - `SignificanceTest` (test_name, p_value, is_significant, interpretation)
  - `ProductionReadinessReport` (sample_size, convergence_analysis, effect_size, significance_test, production_ready, decision_confidence)

### Integration with AutonomousLoop
- **Validation Phase**: Use `_run_validations()` helper that iterates through `validation_hooks` list
- **Monitoring Phase**: Use `_run_monitoring()` helper that iterates through `monitoring_hooks` list (best-effort, catch all exceptions)
- **Hook Registration**: Initialize hooks in `__init__()`:
  ```python
  self.validation_hooks: List[ValidationHook] = [MetricValidator(), SemanticValidator()]
  self.monitoring_hooks: List[MonitoringHook] = [VarianceMonitor(), DataPipelineIntegrity()]
  ```

---

## PHASE 1: FOUNDATION (Weeks 1-2) ✅ COMPLETE

**Status**: Complete (2025-10-12)
**All Stories Implemented**: ✅ Story 6, ✅ Story 5, ✅ Story 3, ✅ Story 7, ✅ Story 8
**Integration**: ✅ INT.1, ✅ INT.2 validated

### Story 6: Metric Integrity (F6) - Priority P0 ✅

**Goal**: Fix metric calculation errors and detect impossible combinations
**Status**: Complete - All tasks implemented and tested

- [x] 6.1. Create MetricValidator class structure in src/validation/metric_validator.py
  - File: src/validation/metric_validator.py
  - Create class with __init__ accepting no parameters
  - Add validate_metrics method signature (returns Tuple[bool, List[str]])
  - Import required types from typing, Dict, List, Tuple
  - Purpose: Establish validator foundation for metric checks
  - _Requirements: 1.6.1, F6.1_

- [x] 6.2. Implement cross_validate_sharpe method in MetricValidator
  - File: src/validation/metric_validator.py (continue from 6.1)
  - Add cross_validate_sharpe(total_return, volatility, sharpe, periods_per_year) method
  - Calculate expected Sharpe: (annualized_return - risk_free_rate) / annualized_volatility
  - Use risk_free_rate = 0.01 (1% default)
  - Return (is_valid, error_message) with tolerance check: abs(calculated - expected) > 0.1 * expected
  - Purpose: Validate Sharpe ratio calculation accuracy
  - _Leverage: Industry standard formula_
  - _Requirements: 1.6.1, F6.1_

- [x] 6.3. Implement check_impossible_combinations method in MetricValidator
  - File: src/validation/metric_validator.py (continue from 6.2)
  - Add check_impossible_combinations(metrics: Dict[str, float]) method
  - Check: negative return + high positive Sharpe (|ratio| > 0.3)
  - Check: zero volatility + non-zero Sharpe
  - Check: max drawdown > 100%
  - Return List[str] of detected anomalies with specific descriptions
  - Purpose: Catch mathematically impossible metric combinations
  - _Leverage: Zen challenge finding (negative return + positive Sharpe)_
  - _Requirements: 1.6.2, F6.3_

- [x] 6.4. Implement generate_audit_trail method in MetricValidator
  - File: src/validation/metric_validator.py (continue from 6.3)
  - Add generate_audit_trail(report: FinlabReport) method
  - Extract intermediate values: daily_returns, cumulative_returns, rolling_volatility
  - Calculate annualized metrics step-by-step
  - Return Dict[str, Any] with all intermediate calculation values
  - Purpose: Enable debugging of metric calculation issues
  - _Requirements: 1.6.3, F6.4_

- [x] 6.5. Integrate MetricValidator into AutonomousLoop.run_iteration()
  - File: autonomous_loop.py (modify existing, line ~260)
  - Import MetricValidator at top of file
  - After execute_strategy_safe() success (line 267), add validation:
    ```python
    validator = MetricValidator()
    is_valid, errors = validator.validate_metrics(metrics, report)
    if not is_valid:
        execution_success = False
        execution_error = f"Metric validation failed: {'; '.join(errors)}"
    ```
  - Purpose: Catch metric errors before champion comparison
  - _Leverage: autonomous_loop.py lines 259-277_
  - _Requirements: 1.6.1, F6.1_

- [x] 6.6. Write unit tests for MetricValidator
  - File: tests/validation/test_metric_validator.py
  - Test cross_validate_sharpe with correct/incorrect calculations
  - Test impossible combinations: negative return + positive Sharpe, zero volatility
  - Test audit trail generation with mock FinlabReport
  - Use pytest fixtures for test data
  - Purpose: Ensure metric validation reliability
  - _Leverage: tests/conftest.py for fixtures_
  - _Requirements: 1.6.4_

### Story 5: Semantic Validation (F5) - Priority P0 ✅

**Goal**: Add behavioral checks beyond AST syntax validation
**Status**: Complete - All tasks implemented and tested

- [x] 5.1. Create SemanticValidator class structure in src/validation/semantic_validator.py
  - File: src/validation/semantic_validator.py
  - Create class with __init__ accepting no parameters
  - Add validate_strategy method signature (returns Tuple[bool, List[str]])
  - Import pandas, typing, Dict, List, Tuple, Optional
  - Purpose: Establish foundation for behavioral validation
  - _Requirements: 1.5.1, F5_

- [x] 5.2. Implement check_position_concentration in SemanticValidator
  - File: src/validation/semantic_validator.py (continue from 5.1)
  - Add check_position_concentration(position_df: pd.DataFrame) method
  - Calculate max position weight per stock across all dates
  - Rule: max_weight <= 0.20 (20% per stock)
  - Return (is_valid, error_message) with stock ticker if violation
  - Purpose: Ensure portfolio diversification
  - _Leverage: position DataFrame from sandbox execution_
  - _Requirements: 1.5.1, F5.1_

- [x] 5.3. Implement check_portfolio_turnover in SemanticValidator
  - File: src/validation/semantic_validator.py (continue from 5.2)
  - Add check_portfolio_turnover(position_df: pd.DataFrame, rebalance_freq: str) method
  - Calculate position changes between rebalance dates
  - Annualize turnover based on rebalance_freq ('Q' = quarterly, 'M' = monthly)
  - Rule: annual_turnover <= 5.0 (500%)
  - Return (is_valid, error_message) with calculated turnover
  - Purpose: Prevent excessive trading costs
  - _Requirements: 1.5.2, F5.2_

- [x] 5.4. Implement check_portfolio_size in SemanticValidator
  - File: src/validation/semantic_validator.py (continue from 5.3)
  - Add check_portfolio_size(position_df: pd.DataFrame) method
  - Calculate average number of positions across dates
  - Rule: 5 <= avg_positions <= 50
  - Return (is_valid, error_message) with actual size
  - Purpose: Ensure effective diversification range
  - _Requirements: 1.5.3, F5.3_

- [x] 5.5. Implement check_always_empty_or_full in SemanticValidator
  - File: src/validation/semantic_validator.py (continue from 5.4)
  - Add check_always_empty_or_full(position_df: pd.DataFrame) method
  - Check if position count is 0 for all dates (always empty)
  - Check if position count equals universe size for all dates (always full)
  - Return (is_valid, error_message) describing the pattern
  - Purpose: Detect non-trading or never-exiting strategies
  - _Requirements: 1.5.4, F5.4_

- [x] 5.6. Integrate SemanticValidator into AutonomousLoop.run_iteration()
  - File: autonomous_loop.py (modify existing, line ~280)
  - Import SemanticValidator at top of file
  - After metric validation (from task 6.5), add semantic validation:
    ```python
    if execution_success and metrics:
        sem_validator = SemanticValidator()
        is_valid, errors = sem_validator.validate_strategy(code, report)
        if not is_valid:
            execution_success = False
            execution_error = f"Semantic validation failed: {'; '.join(errors)}"
    ```
  - Purpose: Add behavioral checks after execution
  - _Leverage: autonomous_loop.py lines 280-310_
  - _Requirements: 1.5.1, F5_

- [x] 5.7. Write unit tests for SemanticValidator
  - File: tests/validation/test_semantic_validator.py
  - Test position concentration: pass (diversified), fail (concentrated)
  - Test portfolio turnover: pass (normal), fail (excessive)
  - Test portfolio size: pass (10 stocks), fail (<5 or >50)
  - Test always empty/full detection
  - Use pandas DataFrame fixtures for position data
  - Purpose: Ensure semantic validation catches all error types
  - _Leverage: tests/conftest.py for fixtures_
  - _Requirements: 1.5.1-1.5.4, F5.1-F5.4_

### Story 3: Extended Test Harness (F3) - Priority P0 ✅

**Goal**: Build 50-200 iteration testing infrastructure with statistical analysis
**Status**: Complete - All tasks implemented and tested

- [x] 3.1. Create ExtendedTestHarness class structure in tests/integration/extended_test_harness.py ✅ COMPLETE
  - File: tests/integration/extended_test_harness.py
  - Create class with __init__(model, target_iterations, checkpoint_interval, checkpoint_dir)
  - Initialize AutonomousLoop instance
  - Initialize result tracking: sharpes[], durations[], champion_updates[]
  - Import AutonomousLoop, logging, json, datetime, pathlib
  - Purpose: Establish test harness foundation
  - _Leverage: run_5iteration_test.py structure (lines 70-232)_
  - _Requirements: 1.3.1, F3.1_

- [x] 3.2. Implement checkpoint save/resume in ExtendedTestHarness
  - File: tests/integration/extended_test_harness.py (continue from 3.1)
  - Add save_checkpoint(iteration: int) method:
    - Save iteration history, champion state, metrics list to JSON
    - Filename: f"{checkpoint_dir}/checkpoint_iter_{iteration}.json"
    - Return checkpoint file path
  - Add load_checkpoint(filepath: str) method:
    - Restore iteration history, champion, metrics from JSON
    - Resume from iteration number in checkpoint
  - Purpose: Enable long test runs with resume capability
  - _Requirements: 1.3.1, F3.2_

- [x] 3.3. Implement statistical analysis methods in ExtendedTestHarness
  - File: tests/integration/extended_test_harness.py (continue from 3.2)
  - Add calculate_cohens_d(sharpes: List[float]) method:
    - Cohen's d = (mean_after_10 - mean_first_10) / pooled_std
    - Return effect size and interpretation (small/medium/large)
  - Add calculate_significance(sharpes: List[float]) method:
    - Use scipy.stats.ttest_rel for paired t-test
    - Return p-value and is_significant (p < 0.05)
  - Add calculate_confidence_intervals(sharpes: List[float]) method:
    - Use scipy.stats.t.interval for 95% CI
    - Return (lower, upper) bounds
  - Import scipy.stats, numpy
  - Purpose: Provide statistical validation for learning effect
  - _Leverage: Industry standard statistical tests_
  - _Requirements: 1.3.2, 1.3.3, F3.3_

- [x] 3.4. Implement generate_statistical_report in ExtendedTestHarness
  - File: tests/integration/extended_test_harness.py (continue from 3.3)
  - Add generate_statistical_report() method
  - Calculate all statistics: Cohen's d, p-value, 95% CI, rolling variance
  - Determine production readiness:
    - READY if: p < 0.05 AND d >= 0.4 AND σ < 0.5 (after iter 10)
    - NOT READY if any criterion fails, with specific reasoning
  - Return Dict with all statistics and readiness decision
  - Purpose: Automated go/no-go decision for production
  - _Requirements: 1.3.4, F3.4_

- [x] 3.5. Implement run_test method in ExtendedTestHarness
  - File: tests/integration/extended_test_harness.py (continue from 3.4)
  - Add run_test(data, resume_from_checkpoint) method
  - Main loop: for i in range(target_iterations):
    - Run AutonomousLoop.run_iteration(i, data)
    - Track metrics: sharpes, durations, champion_updates
    - Save checkpoint every checkpoint_interval iterations
    - Handle exceptions with retry logic (max 3 retries per iteration)
  - After loop completes, call generate_statistical_report()
  - Return comprehensive results dict
  - Purpose: Execute long test runs with automatic checkpointing
  - _Leverage: run_5iteration_test.py run_5iteration_test() (lines 70-232)_
  - _Requirements: 1.3.1, F3.1, F3.2_

- [x] 3.6. Create run_50iteration_test.py script for production testing
  - File: run_50iteration_test.py
  - Import ExtendedTestHarness, load_finlab_data (from run_5iteration_test.py)
  - Setup logging with timestamp-based log file
  - Initialize ExtendedTestHarness with target_iterations=50
  - Call run_test() with real Finlab data
  - Print statistical report to console and log file
  - Handle KeyboardInterrupt gracefully (save checkpoint)
  - Purpose: Provide production-ready 50-iteration test script
  - _Leverage: run_5iteration_test.py main() (lines 235-264)_
  - _Requirements: 1.3.1, F3.1_

- [x] 3.7. Write unit tests for ExtendedTestHarness statistical methods
  - File: tests/integration/test_extended_test_harness.py
  - Test calculate_cohens_d with known effect sizes
  - Test calculate_significance with significant/non-significant data
  - Test calculate_confidence_intervals with normal distribution
  - Test generate_statistical_report production readiness logic
  - Use numpy to generate test data with known properties
  - Purpose: Ensure statistical calculations are correct
  - _Requirements: 1.3.2, 1.3.3, F3.3_

### Story 7: Data Pipeline Integrity (F7) - Priority P1 ✅

**Goal**: Ensure data consistency and reproducibility across iterations
**Status**: Complete - All tasks implemented and tested

- [x] 7.1. Create DataPipelineIntegrity class in src/data/pipeline_integrity.py ✅ COMPLETE
  - File: src/data/pipeline_integrity.py
  - Create class with __init__ accepting no parameters
  - Import hashlib, json, datetime, finlab
  - Add _get_dataset_dict helper to serialize key datasets to dict
  - Purpose: Establish data integrity foundation
  - _Requirements: 1.7.1, F7.1_

- [x] 7.2. Implement compute_dataset_checksum in DataPipelineIntegrity
  - File: src/data/pipeline_integrity.py (continue from 7.1)
  - Add compute_dataset_checksum(data: FinlabData) method
  - Load key datasets: price:收盤價, price:成交金額, fundamental_features:ROE稅後
  - Serialize to JSON string (sorted keys for determinism)
  - Compute SHA-256 hash, return hex digest
  - Purpose: Create reproducible data fingerprint
  - _Requirements: 1.7.1, F7.1_

- [x] 7.3. Implement validate_data_consistency in DataPipelineIntegrity
  - File: src/data/pipeline_integrity.py (continue from 7.2)
  - Add validate_data_consistency(data, expected_checksum) method
  - Compute current checksum using compute_dataset_checksum
  - Compare with expected_checksum
  - Return (is_valid, error_message) with checksums if mismatch
  - Purpose: Detect data corruption or changes
  - _Requirements: 1.7.3, F7.3_

- [x] 7.4. Implement record_data_provenance in DataPipelineIntegrity
  - File: src/data/pipeline_integrity.py (continue from 7.3)
  - Add record_data_provenance(iteration_num) method
  - Capture: dataset_checksum, finlab_version (finlab.__version__)
  - Capture: data_pull_timestamp (current time), dataset_row_counts
  - Return Dict[str, Any] with all provenance data
  - Purpose: Enable full reproducibility of results
  - _Requirements: 1.7.2, 1.7.4, F7.2, F7.4_

- [x] 7.5. Extend IterationRecord dataclass with data provenance fields
  - File: history.py (modify existing IterationRecord dataclass)
  - Add optional fields to IterationRecord:
    - data_checksum: Optional[str] = None
    - data_version: Optional[Dict[str, str]] = None
  - Update to_dict() and from_dict() to handle new fields
  - Purpose: Store data provenance in iteration history
  - _Leverage: history.py existing IterationRecord (lines ~15-40)_
  - _Requirements: 1.7.2, F7.2_

- [x] 7.6. Integrate DataPipelineIntegrity into AutonomousLoop.run_iteration()
  - File: autonomous_loop.py (modify existing, line ~120)
  - Import DataPipelineIntegrity at top of file
  - After finlab data load, before generation (line 126):
    ```python
    integrity = DataPipelineIntegrity()
    provenance = integrity.record_data_provenance(iteration_num)
    checksum = provenance['dataset_checksum']
    # Validate against previous iteration's checksum if exists
    if iteration_num > 0:
        prev = self.history.get_record(iteration_num - 1)
        if prev and prev.data_checksum:
            is_valid, msg = integrity.validate_data_consistency(data, prev.data_checksum)
            if not is_valid:
                logger.warning(f"Data checksum changed: {msg}")
    ```
  - Store provenance in IterationRecord (line 325)
  - Purpose: Track data provenance for every iteration
  - _Leverage: autonomous_loop.py lines 120-336_
  - _Requirements: 1.7.3, 1.7.4, F7.3, F7.4_

- [x] 7.7. Write unit tests for DataPipelineIntegrity
  - File: tests/data/test_pipeline_integrity.py
  - Test compute_dataset_checksum determinism (same data = same hash)
  - Test validate_data_consistency detection (modified data = different hash)
  - Test record_data_provenance completeness (all fields present)
  - Mock Finlab data objects for testing
  - Purpose: Ensure data integrity system works correctly
  - _Requirements: 1.7.1-1.7.4, F7.1-F7.4_

### Story 8: Experiment Config Tracking (F8) - Priority P1 ✅

**Goal**: Track all hyperparameters and settings for reproducibility
**Status**: Complete - All tasks implemented and tested

- [x] 8.1. Create ExperimentConfig dataclass in src/config/experiment_config_manager.py
  - File: src/config/experiment_config_manager.py
  - Define ExperimentConfig dataclass with fields:
    - model, temperature, prompt_template, prompt_version
    - anti_churn_threshold, probation_period
    - liquidity_threshold, stop_loss, rebalance_frequency
    - python_version, package_versions (Dict), api_endpoints (Dict)
    - timestamp
  - Add to_dict() and from_dict() methods for serialization
  - Import dataclasses, sys, pkg_resources, datetime
  - Purpose: Complete configuration snapshot structure
  - _Requirements: 1.8.1, F8.1_

- [x] 8.2. Create ExperimentConfigManager class in src/config/experiment_config_manager.py
  - File: src/config/experiment_config_manager.py (continue from 8.1)
  - Create class with __init__ accepting no parameters
  - Add _get_package_versions() helper:
    - Get versions for: finlab, pandas, numpy, scipy
  - Add _get_python_version() helper: return sys.version
  - Purpose: Establish config management foundation
  - _Requirements: 1.8.3, F8.3_

- [x] 8.3. Implement capture_config_snapshot in ExperimentConfigManager
  - File: src/config/experiment_config_manager.py (continue from 8.2)
  - Add capture_config_snapshot(iteration_num) method
  - Read current configuration from:
    - AutonomousLoop attributes (model, temperature from prompt_builder)
    - Prompt template file (read prompt_template_v1.txt)
    - Anti-churn config (hardcoded values from autonomous_loop.py lines 434-437)
  - Get environment: python_version, package_versions, api_endpoints
  - Return ExperimentConfig instance with all fields populated
  - Purpose: Capture complete config state
  - _Requirements: 1.8.1, F8.1_

- [x] 8.4. Implement compute_config_diff in ExperimentConfigManager
  - File: src/config/experiment_config_manager.py (continue from 8.3)
  - Add compute_config_diff(prev_config, curr_config) method
  - Compare all fields between configs
  - Return Dict[str, Tuple[Any, Any]] with {field: (old_value, new_value)}
  - Only include fields that changed
  - Purpose: Highlight configuration changes between iterations
  - _Requirements: 1.8.2, F8.2_

- [x] 8.5. Implement export/import config methods in ExperimentConfigManager
  - File: src/config/experiment_config_manager.py (continue from 8.4)
  - Add export_config(config, filepath) method:
    - Serialize ExperimentConfig to JSON
    - Write to filepath with pretty formatting (indent=2)
  - Add import_config(filepath) method:
    - Read JSON from filepath
    - Deserialize to ExperimentConfig instance
  - Purpose: Enable experiment reproduction
  - _Requirements: 1.8.4, F8.4_

- [x] 8.6. Extend IterationRecord dataclass with config fields
  - File: history.py (modify existing IterationRecord dataclass)
  - Add optional fields to IterationRecord:
    - config_snapshot: Optional[Dict[str, Any]] = None
    - config_diff: Optional[Dict[str, Tuple[Any, Any]]] = None
  - Update to_dict() and from_dict() to handle new fields
  - Purpose: Store config in iteration history
  - _Leverage: history.py existing IterationRecord (lines ~15-40)_
  - _Requirements: 1.8.1, F8.1_

- [x] 8.7. Integrate ExperimentConfigManager into AutonomousLoop.run_iteration()
  - File: autonomous_loop.py (modify existing, line ~126)
  - Import ExperimentConfigManager at top of file
  - After building prompt (line 139):
    ```python
    config_mgr = ExperimentConfigManager()
    config = config_mgr.capture_config_snapshot(iteration_num)
    # Compute diff if previous iteration exists
    config_diff = None
    if iteration_num > 0:
        prev = self.history.get_record(iteration_num - 1)
        if prev and prev.config_snapshot:
            prev_config = ExperimentConfig.from_dict(prev.config_snapshot)
            config_diff = config_mgr.compute_config_diff(prev_config, config)
    ```
  - Store config and diff in IterationRecord (line 325)
  - Purpose: Track config for every iteration
  - _Leverage: autonomous_loop.py lines 126-336_
  - _Requirements: 1.8.1, 1.8.2, F8.1, F8.2_

- [x] 8.8. Write unit tests for ExperimentConfigManager
  - File: tests/config/test_experiment_config_manager.py
  - Test capture_config_snapshot completeness (all fields present)
  - Test compute_config_diff detection (changed vs unchanged fields)
  - Test export/import round-trip (export then import = identical config)
  - Mock sys.version and pkg_resources for deterministic tests
  - Purpose: Ensure config tracking works correctly
  - _Requirements: 1.8.1-1.8.4, F8.1-F8.4_

---

## PHASE 2: TUNING (Weeks 3-4) ✅ COMPLETE

**Status**: Complete (2025-10-12)
**All Stories Implemented**: ✅ Story 1, ✅ Story 2, ✅ Story 4, ✅ Story 9
**Integration**: test_phase2_integration.py validated

### Story 1: Convergence Monitoring (F1) - Priority P1 ✅

**Goal**: Track variance and detect learning convergence
**Status**: Complete - All tasks implemented and tested

- [x] 1.1. Create VarianceMonitor class in src/monitoring/variance_monitor.py
  - File: src/monitoring/variance_monitor.py
  - Create class with __init__(alert_threshold: float = 0.8)
  - Initialize: sharpes deque (maxlen=10 for rolling window)
  - Initialize: all_sharpes list for full history
  - Import collections.deque, numpy, typing
  - Purpose: Establish variance monitoring foundation
  - _Requirements: 1.1.1, F1.1_

- [x] 1.2. Implement rolling variance calculation in VarianceMonitor
  - File: src/monitoring/variance_monitor.py (continue from 1.1)
  - Add update(iteration_num, sharpe) method:
    - Append sharpe to sharpes deque and all_sharpes list
  - Add get_rolling_variance(window=10) method:
    - Calculate standard deviation of last 'window' sharpes
    - Return float (σ) or 0.0 if insufficient data
  - Purpose: Track Sharpe ratio variance over time
  - _Requirements: 1.1.1, F1.1_

- [x] 1.3. Implement alert condition checking in VarianceMonitor
  - File: src/monitoring/variance_monitor.py (continue from 1.2)
  - Add check_alert_condition() method:
    - Get current rolling variance
    - Check if σ > self.alert_threshold for 5+ consecutive iterations
    - Track consecutive high variance count
    - Return (alert_triggered, context_message)
  - Purpose: Detect instability and alert user
  - _Requirements: 1.1.2, F1.2_

- [x] 1.4. Implement convergence report generation in VarianceMonitor
  - File: src/monitoring/variance_monitor.py (continue from 1.3)
  - Add generate_convergence_report() method:
    - Calculate variance trend: σ over time (rolling window)
    - Detect convergence: first iteration where σ < 0.5 after iter 10
    - Check current status: converged, converging, unstable
    - Return Dict with: variance_trend, convergence_status, recommendations
  - Purpose: Comprehensive convergence analysis
  - _Requirements: 1.1.3, F1.3_

- [x] 1.5. Integrate VarianceMonitor into iteration_engine.py main_loop()
  - File: autonomous_loop.py (modify existing, line ~320)
  - Initialize self.variance_monitor in __init__ (line 100)
  - After champion update (line 322), add:
    ```python
    if execution_success and metrics:
        sharpe = metrics.get(METRIC_SHARPE, 0)
        self.variance_monitor.update(iteration_num, sharpe)
        alert, msg = self.variance_monitor.check_alert_condition()
        if alert:
            logger.warning(f"Variance alert: {msg}")
    ```
  - Purpose: Track variance in real-time during iterations
  - _Leverage: autonomous_loop.py lines 100, 316-322_
  - _Requirements: 1.1.1, 1.1.2, F1.1, F1.2_

- [x] 1.6. Write unit tests for VarianceMonitor
  - File: tests/monitoring/test_variance_monitor.py
  - Test rolling variance calculation with known data
  - Test alert triggering with high variance sequence
  - Test convergence detection (σ crosses 0.5 threshold)
  - Test generate_convergence_report output format
  - Purpose: Ensure variance monitoring works correctly
  - _Requirements: 1.1.1-1.1.4, F1.1-F1.4_

### Story 2: Enhanced Preservation (F2) - Priority P0 ✅

**Goal**: Fix preservation validation false positives with behavioral checks
**Status**: Complete - All tasks implemented and tested

- [x] 2.1. Create PreservationValidator class in src/validation/preservation_validator.py
  - File: src/validation/preservation_validator.py
  - Create class with __init__ accepting no parameters
  - Add validate_preservation method signature:
    - (generated_code, champion, execution_metrics) -> Tuple[bool, Dict]
  - Import pandas, performance_attributor, ChampionStrategy
  - Purpose: Establish enhanced preservation foundation
  - _Requirements: 1.2.1, F2.1_

- [x] 2.2. Implement check_behavioral_similarity in PreservationValidator
  - File: src/validation/preservation_validator.py (continue from 2.1)
  - Add check_behavioral_similarity(champion_metrics, generated_metrics, champion_positions, generated_positions) method
  - Check Sharpe within ±10%: abs(gen - champ) / champ <= 0.10
  - Check portfolio turnover within ±20%: calculate turnover from positions
  - Check position concentration patterns maintained: max concentration similar
  - Return (is_similar, deviation_details Dict[str, str])
  - Purpose: Validate behavioral similarity beyond parameters
  - _Requirements: 1.2.1, F2.1_

- [x] 2.3. Create PreservationReport dataclass in src/validation/preservation_validator.py
  - File: src/validation/preservation_validator.py (continue from 2.2)
  - Define PreservationReport dataclass with fields:
    - is_preserved: bool
    - parameter_checks: Dict[str, Tuple[bool, str]]
    - behavioral_checks: Dict[str, Tuple[bool, str]]
    - false_positive_risk: float (0.0-1.0)
    - recommendations: List[str]
    - timestamp: str
  - Add to_dict() method for serialization
  - Purpose: Detailed preservation validation report
  - _Requirements: 1.2.4, F2.4_

- [x] 2.4. Implement validate_preservation in PreservationValidator
  - File: src/validation/preservation_validator.py (continue from 2.3)
  - Add complete validate_preservation method:
    - Extract parameters from generated_code (reuse existing logic)
    - Check parameter preservation (ROE type, liquidity threshold) - from autonomous_loop.py lines 588-628
    - If execution_metrics provided, call check_behavioral_similarity
    - Calculate false_positive_risk based on parameter-only vs behavioral agreement
    - Generate recommendations list with specific guidance
    - Return (is_preserved, PreservationReport)
  - Purpose: Complete preservation validation with behavioral checks
  - _Leverage: autonomous_loop.py _validate_preservation (lines 561-631)_
  - _Requirements: 1.2.1, 1.2.2, F2.1, F2.2_

- [x] 2.5. Replace existing _validate_preservation in autonomous_loop.py
  - File: autonomous_loop.py (modify existing, line ~561)
  - Import PreservationValidator, PreservationReport at top
  - Replace _validate_preservation method (lines 561-631) with:
    ```python
    def _validate_preservation(self, generated_code: str, execution_metrics: Optional[Dict] = None) -> Tuple[bool, PreservationReport]:
        validator = PreservationValidator()
        return validator.validate_preservation(generated_code, self.champion, execution_metrics)
    ```
  - Update call sites (line 158, 186) to handle PreservationReport return
  - Log preservation report details for debugging
  - Purpose: Use enhanced preservation validator
  - _Leverage: autonomous_loop.py lines 561-631, 158, 186_
  - _Requirements: 1.2.1, F2.1_

- [x] 2.6. Write unit tests for PreservationValidator
  - File: tests/validation/test_preservation_validator.py
  - Test parameter preservation: pass (maintained), fail (violated)
  - Test behavioral similarity: pass (within bounds), fail (excessive deviation)
  - Test false_positive_risk calculation
  - Test PreservationReport generation and serialization
  - Mock ChampionStrategy and execution metrics
  - Purpose: Ensure preservation validation catches false positives
  - _Requirements: 1.2.1-1.2.3, F2.1-F2.3_

### Story 4: Anti-Churn Configuration (F4) - Priority P1

**Goal**: Externalize anti-churn thresholds for easy tuning

- [x] 4.1. Create config/learning_system.yaml with anti-churn parameters
  - File: config/learning_system.yaml
  - Define YAML structure:
    ```yaml
    anti_churn:
      probation_period: 2
      probation_threshold: 0.10
      post_probation_threshold: 0.05
      min_sharpe_for_champion: 0.5
      target_update_frequency: 0.15
      tuning_range:
        probation_period: [1, 3]
        probation_threshold: [0.05, 0.15]
        post_probation_threshold: [0.03, 0.10]
    ```
  - Include inline documentation comments
  - Purpose: Externalized configuration for easy tuning
  - _Requirements: 1.4.4, F4.4_

- [x] 4.2. Create AntiChurnManager class in src/config/anti_churn_manager.py
  - File: src/config/anti_churn_manager.py
  - Create class with __init__(config_file: str = "config/learning_system.yaml")
  - Load YAML config using PyYAML
  - Store config dict and initialize update tracking: champion_updates list
  - Import yaml, pathlib, typing
  - Purpose: Manage anti-churn configuration
  - _Requirements: 1.4.4, F4.4_

- [x] 4.3. Implement get_required_improvement in AntiChurnManager
  - File: src/config/anti_churn_manager.py (continue from 4.2)
  - Add get_required_improvement(iteration_num, champion_iteration) method:
    - Calculate iterations since champion: delta = iteration_num - champion_iteration
    - If delta <= config['probation_period']: return config['probation_threshold']
    - Else: return config['post_probation_threshold']
  - Purpose: Dynamic threshold based on probation period
  - _Leverage: autonomous_loop.py lines 434-437 logic_
  - _Requirements: 1.4.1, F4.1_

- [x] 4.4. Implement champion update tracking in AntiChurnManager
  - File: src/config/anti_churn_manager.py (continue from 4.3)
  - Add track_champion_update(iteration_num, updated: bool) method:
    - Append (iteration_num, updated) to champion_updates list
  - Add analyze_update_frequency(window=50) method:
    - Calculate update frequency: sum(updated) / len(champion_updates) for last 'window' iterations
    - Check if within target: 0.10 <= frequency <= 0.20
    - Generate recommendations if outside target:
      - Too high: increase thresholds
      - Too low: decrease thresholds
    - Return Dict with: update_frequency, within_target, recommendations
  - Purpose: Monitor and tune champion update frequency
  - _Requirements: 1.4.2, F4.2, F4.3_

- [x] 4.5. Replace hardcoded thresholds in autonomous_loop.py
  - File: autonomous_loop.py (modify existing, line ~434)
  - Import AntiChurnManager at top
  - Initialize self.anti_churn_mgr in __init__ (line 100)
  - Replace hardcoded thresholds (lines 434-437) with:
    ```python
    required_improvement = self.anti_churn_mgr.get_required_improvement(
        iteration_num, self.champion.iteration_num
    )
    ```
  - After champion update (line 447), add:
    ```python
    self.anti_churn_mgr.track_champion_update(iteration_num, champion_updated)
    ```
  - Purpose: Use externalized config instead of hardcoded values
  - _Leverage: autonomous_loop.py lines 100, 434-447_
  - _Requirements: 1.4.4, F4.4_

- [x] 4.6. Write unit tests for AntiChurnManager
  - File: tests/config/test_anti_churn_manager.py
  - Test config loading from YAML
  - Test get_required_improvement: probation vs post-probation
  - Test analyze_update_frequency: within/outside target range
  - Test recommendations generation
  - Mock YAML config file for testing
  - Purpose: Ensure anti-churn manager works correctly
  - _Requirements: 1.4.1-1.4.4, F4.1-F4.4_

### Story 9: Rollback Mechanism (F9) - Priority P2

**Goal**: Enable restoration of previous champion states

- [x] 9.1. Create RollbackManager class in src/recovery/rollback_manager.py
  - File: src/recovery/rollback_manager.py
  - Create class with __init__(hall_of_fame: HallOfFameRepository)
  - Store hall_of_fame reference
  - Initialize rollback_log: List[RollbackRecord]
  - Import HallOfFameRepository, ChampionStrategy, typing
  - Purpose: Establish rollback foundation
  - _Requirements: 1.9.1, F9.1_

- [x] 9.2. Implement get_champion_history in RollbackManager
  - File: src/recovery/rollback_manager.py (continue from 9.1)
  - Add get_champion_history(limit=10) method:
    - Query Hall of Fame for all Champions tier strategies
    - Sort by created_at timestamp descending (newest first)
    - Convert StrategyGenome to ChampionStrategy format
    - Return List[ChampionStrategy] with limit applied
  - Purpose: Retrieve champion history for rollback selection
  - _Leverage: HallOfFameRepository.query_strategies()_
  - _Requirements: 1.9.1, F9.1_

- [x] 9.3. Implement rollback_to_iteration in RollbackManager
  - File: src/recovery/rollback_manager.py (continue from 9.2)
  - Add rollback_to_iteration(target_iteration, reason) method:
    - Get champion history
    - Find champion matching target_iteration
    - If not found, return (False, "Champion not found for iteration X")
    - Call validate_rollback_champion to ensure it still works
    - If validation fails, return (False, validation error message)
    - Update current champion in Hall of Fame (mark as current)
    - Call record_rollback to log operation
    - Return (True, "Successfully rolled back to iteration X")
  - Purpose: Execute rollback with validation
  - _Requirements: 1.9.2, F9.2_

- [x] 9.4. Implement validate_rollback_champion in RollbackManager
  - File: src/recovery/rollback_manager.py (continue from 9.3)
  - Add validate_rollback_champion(champion, data) method:
    - Import execute_strategy_safe from sandbox_simple
    - Execute champion.code with data
    - Check execution success
    - Verify metrics are reasonable (Sharpe > 0.5)
    - Return (is_valid, validation_report Dict)
  - Purpose: Ensure rolled-back champion still executes
  - _Leverage: sandbox_simple.execute_strategy_safe_
  - _Requirements: 1.9.3, F9.3_

- [x] 9.5. Create RollbackRecord dataclass and record_rollback in RollbackManager
  - File: src/recovery/rollback_manager.py (continue from 9.4)
  - Define RollbackRecord dataclass:
    - rollback_id, from_iteration, to_iteration, reason, operator
    - timestamp, validation_passed, validation_report
  - Add record_rollback(from_iteration, to_iteration, reason, operator) method:
    - Generate rollback_id (UUID)
    - Create RollbackRecord with all details
    - Append to self.rollback_log
    - Save to rollback_history.json file
  - Purpose: Audit trail for rollback operations
  - _Requirements: 1.9.4, F9.4_

- [x] 9.6. Create rollback_champion.py command-line tool
  - File: rollback_champion.py
  - Implement CLI with argparse:
    - --target-iteration: Required, iteration number to rollback to
    - --reason: Required, reason for rollback
    - --operator: Optional, operator name (default: system)
  - Load Finlab data
  - Initialize RollbackManager with HallOfFameRepository
  - Display champion history for selection
  - Execute rollback_to_iteration with user confirmation
  - Print result and validation report
  - Purpose: User-friendly rollback tool
  - _Requirements: 1.9.2, F9.2_

- [x] 9.7. Write unit tests for RollbackManager
  - File: tests/recovery/test_rollback_manager.py
  - Test get_champion_history returns correct champions
  - Test rollback_to_iteration: success case, not found case
  - Test validate_rollback_champion: pass (valid), fail (execution error)
  - Test record_rollback audit trail
  - Mock HallOfFameRepository and execute_strategy_safe
  - Purpose: Ensure rollback system works correctly
  - _Requirements: 1.9.1-1.9.4, F9.1-F9.4_

---

## Integration Tasks

### Phase 1 Integration ✅ COMPLETE

- [x] INT.1. Update IterationRecord dataclass with all new fields ✅
  - File: history.py (consolidated all dataclass changes)
  - ✅ Added data_checksum, data_version fields (Story 7)
  - ✅ Added config_snapshot field (Story 8)
  - ✅ Backward compatibility maintained (all new fields Optional with None default)
  - ✅ Updated to_dict() and from_dict() for complete serialization
  - Purpose: Single integration point for IterationRecord changes
  - _Leverage: Tasks 7.5, 8.6_
  - _Requirements: All Phase 1 stories_
  - **Status**: Complete - All Phase 1 fields integrated

- [x] INT.2. Create comprehensive integration test for Phase 1 ✅
  - File: tests/integration/test_phase1_integration.py (created, 915 lines, 12 tests)
  - ✅ Story 7 tests: data checksums, consistency validation, provenance recording
  - ✅ Story 8 tests: config snapshots, diffs, environment tracking
  - ✅ Cross-story tests: IterationRecord validation, data+config together
  - ✅ All 12 tests passing, validates all Phase 1 features work together
  - ✅ Single iteration test confirmed all Phase 1 fields present in history
  - Purpose: Ensure all Phase 1 components work together
  - _Requirements: All Phase 1 stories_
  - **Status**: Complete - Integration validated

### Phase 2 Integration (Pending)

- [ ] INT.3. Create comprehensive integration test for Phase 2
  - File: tests/integration/test_phase2_integration.py
  - Test 20-iteration run with all Phase 2 features enabled:
    - Variance monitoring tracks convergence
    - Enhanced preservation catches behavioral deviations
    - Anti-churn config loaded and applied correctly
    - Rollback mechanism can restore previous champion
  - Verify complete system stability
  - Purpose: Ensure all Phase 2 components work together
  - _Requirements: All Phase 2 stories_

- [~] INT.4. Update run_50iteration_test.py to use all stability features (Phase 1 ✅, Phase 2 pending)
  - File: run_50iteration_test.py (enhanced with Phase 1 features)
  - ✅ Phase 1 Complete:
    - validate_phase1_features() added to check module availability on startup
    - extract_phase1_metrics() added to extract data integrity and config tracking metrics
    - Enhanced print_colored_report() to display Phase 1 metrics
    - Integrated validation and metrics extraction into main test flow
  - [ ] Phase 2 Pending:
    - Enable Phase 2 monitoring: variance, preservation, anti-churn
    - Generate comprehensive final report with all Phase 1 + Phase 2 statistics
  - Purpose: Production-ready 50-iteration test with all features
  - _Leverage: Tasks 3.6, all Phase 1 and Phase 2 tasks_
  - _Requirements: All stories_
  - **Status**: Phase 1 portion complete

---

## Task Dependencies

**Phase 1 Dependencies**:
- Tasks 6.1-6.5 → 6.6 (tests depend on implementation)
- Tasks 5.1-5.5 → 5.6 → 5.7 (integration depends on components)
- Tasks 3.1-3.4 → 3.5 → 3.6 (script depends on harness)
- Tasks 7.1-7.4 → 7.5 → 7.6 → 7.7 (integration depends on dataclass)
- Tasks 8.1-8.5 → 8.6 → 8.7 → 8.8 (integration depends on dataclass)
- INT.1 depends on tasks 7.5, 8.6
- INT.2 depends on all Phase 1 tasks

**Phase 2 Dependencies**:
- Tasks 1.1-1.4 → 1.5 → 1.6
- Tasks 2.1-2.4 → 2.5 → 2.6 (replacement depends on new validator)
- Tasks 4.1-4.4 → 4.5 → 4.6 (integration depends on manager)
- Tasks 9.1-9.5 → 9.6 → 9.7 (CLI depends on manager)
- INT.3 depends on all Phase 2 tasks
- INT.4 depends on INT.2, INT.3

---

**Tasks Version**: 1.2
**Last Updated**: 2025-10-12
**Status**: Phase 1 Complete ✅ | Phase 2 In Progress
**Phase 1 Completed**: 2025-10-12 (Stories 3, 5, 6, 7, 8 + INT.1, INT.2)
**Aligned with**: design.md v1.1 (P0 enhancements: interfaces, error handling, data models)
**Total Tasks**: 66 atomic tasks (37 Phase 1 ✅, 25 Phase 2, 4 Integration - 2 complete)
**Estimated Duration**: 3-4 weeks (Foundation: 1.5-2 weeks ✅ COMPLETE, Tuning: 1-1.5 weeks, Integration: 0.5 week)
**Phase 1 Deliverables**:
- MetricValidator: Sharpe validation, impossible combination detection
- BehavioralValidator: Position concentration, turnover, portfolio size checks
- ExtendedTestHarness: 50-200 iteration testing with statistical analysis
- DataPipelineIntegrity: Checksums, provenance tracking, consistency validation
- ExperimentConfigManager: Config snapshots, diffs, reproducibility
- Integration Tests: 12 comprehensive tests validating all Phase 1 features
- Enhanced run_50iteration_test.py with Phase 1 validation and metrics
**Next Step**: Begin Phase 2 implementation (Stories 1, 2, 4, 9)
