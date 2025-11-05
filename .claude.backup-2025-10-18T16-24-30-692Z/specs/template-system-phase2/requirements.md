# Requirements Document: Strategy Template Library & Hall of Fame System

## Introduction

This specification defines Phase 2 of the Taiwan Stock Strategy Generation System: implementing a reusable strategy template library and Hall of Fame repository system. The goal is to enable robust, reproducible strategy generation by encoding successful patterns into parameterized templates and maintaining a curated repository of validated high-performance strategies.

**Phase Context**: This builds directly on Phase 1 (Grid Search Validation), which achieved 80% success rate (40/50 turtle variations with Sharpe >1.5), proving that template-based parameterization is viable for discovering high-Sharpe strategies.

**Value Proposition**: By creating reusable templates with validated parameter ranges, we eliminate the 90% strategy generator oversimplification that caused 150-iteration failure (130/150 iterations used identical P/E strategy). Templates enable systematic exploration with proven architecture patterns.

## Alignment with Product Vision

This feature supports the documented strategy generation system goals:

1. **Autonomous High-Sharpe Discovery**: Templates encode proven 6-layer AND filtering and contrarian selection patterns from benchmark strategies (Sharpe 2.09 turtle, innovative mastiff)

2. **Knowledge Accumulation**: Hall of Fame system builds institutional memory by preserving successful strategies with parameter metadata, success patterns, and robustness scores

3. **Reproducibility**: Templates with explicit parameter ranges enable systematic testing and validation, replacing ad-hoc strategy generation

4. **Scalability**: Template library grows over time as new patterns emerge from successful strategies, creating positive feedback loop

## Requirements

### Requirement 1: Four Core Strategy Templates

**User Story**: As a strategy researcher, I want four validated strategy templates (Turtle, Mastiff, Factor, Momentum) with explicit parameter ranges, so that I can systematically generate and test strategy variations without starting from scratch.

#### Acceptance Criteria

1. **WHEN** the template library is loaded **THEN** the system **SHALL** provide exactly 4 template classes: `TurtleTemplate`, `MastiffTemplate`, `FactorTemplate`, `MomentumTemplate`

2. **WHEN** any template is instantiated **THEN** it **SHALL** include:
   - Template name and description
   - Architecture pattern type (multi_layer_and | contrarian_reversal | factor_ranking | momentum_catalyst)
   - Complete PARAM_GRID dictionary with validated ranges
   - Expected performance metrics (sharpe_range, return_range, mdd_range)
   - Data caching integration via `get_cached_data()`
   - Strategy generation function `generate_strategy(params) -> (report, metrics)`

3. **WHEN** a template's `generate_strategy()` is called with valid parameters **THEN** it **SHALL** return:
   - Finlab backtest report object
   - Metrics dictionary with at minimum: `{'sharpe_ratio': float, 'annual_return': float, 'max_drawdown': float, 'success': bool}`

4. **IF** the template is TurtleTemplate **THEN** it **SHALL** implement 6-layer AND filtering with layers for: yield, technical, revenue, quality, insider, liquidity

5. **IF** the template is MastiffTemplate **THEN** it **SHALL** implement contrarian selection using `.is_smallest(n_stocks)` for volume ranking

6. **IF** the template is FactorTemplate **THEN** it **SHALL** use cross-sectional ranking `.rank(axis=1, pct=True)` for factor scoring

7. **IF** the template is MomentumTemplate **THEN** it **SHALL** include revenue acceleration catalyst using `revenue.average(short) > revenue.average(long)`

8. **WHEN** parameter validation is performed **THEN** each template **SHALL** enforce:
   - Type validation (int, float, str as specified)
   - Range validation (min/max bounds from PARAM_GRID)
   - Interdependency validation (e.g., ma_short < ma_long)

### Requirement 2: Hall of Fame Repository System

**User Story**: As a strategy researcher, I want a persistent Hall of Fame repository that stores validated strategies with their complete genome (code, parameters, metrics, success patterns), so that I can track the best-performing strategies and learn from their patterns over time.

#### Acceptance Criteria

1. **WHEN** a strategy is added to Hall of Fame **THEN** it **SHALL** store:
   - Strategy genome: `{iteration_num, code, parameters, metrics, success_patterns, timestamp}`
   - Performance data: Sharpe, Return, MDD, Win Rate
   - Robustness data: Parameter sensitivity scores, out-of-sample metrics
   - Novelty score: Cosine distance from existing strategies

2. **WHEN** storage tier is determined **THEN** strategies **SHALL** be classified as:
   - **Champions** (Sharpe ≥2.0): Stored in `hall_of_fame/champions/`
   - **Contenders** (Sharpe 1.5-2.0): Stored in `hall_of_fame/contenders/`
   - **Archive** (Sharpe <1.5 but novel): Stored in `hall_of_fame/archive/`

3. **WHEN** a strategy is serialized **THEN** it **SHALL** use YAML format with:
   - Human-readable structure
   - Complete parameter dictionary
   - Success patterns as bullet list
   - Timestamp in ISO 8601 format

4. **WHEN** novelty scoring is calculated **THEN** it **SHALL**:
   - Extract factor usage vector from strategy code
   - Calculate cosine distance from all existing strategies
   - Return `novelty_score = min_distance` (0.0 = duplicate, 1.0 = completely novel)
   - Reject strategies with `novelty_score < 0.2` as duplicates

5. **WHEN** Hall of Fame is queried for similar strategies **THEN** it **SHALL**:
   - Accept `max_distance` parameter (default: 0.3)
   - Return list of strategies within distance threshold
   - Include similarity score and shared factors

6. **WHEN** success patterns are extracted **THEN** the system **SHALL**:
   - Call `extract_success_patterns()` from performance_attributor
   - Prioritize patterns by criticality (using `_prioritize_patterns()`)
   - Store patterns with human-readable descriptions
   - Enable pattern search across Hall of Fame

7. **IF** JSON serialization fails **THEN** the system **SHALL**:
   - Log error with full context
   - Attempt write to backup location `hall_of_fame/backup/`
   - Return error status without crashing

8. **WHEN** Hall of Fame size exceeds 100 strategies **THEN** the system **SHALL**:
   - Archive lowest-performing 20% of Contenders to Archive tier
   - Compress strategies older than 6 months
   - Maintain full index for fast lookup

### Requirement 3: Template Validation System

**User Story**: As a strategy researcher, I want automated validation of generated strategies against template specifications, so that I can catch errors early and ensure generated code matches intended architecture patterns.

#### Acceptance Criteria

1. **WHEN** a strategy is generated from a template **THEN** validation **SHALL** check:
   - All required parameters are present
   - Parameter values are within specified ranges
   - Generated code includes expected data.get() calls
   - Backtest configuration matches template specs

2. **WHEN** TurtleTemplate validation runs **THEN** it **SHALL** verify:
   - Exactly 6 boolean conditions (cond1-cond6) are defined
   - All conditions are combined with AND operator (`&`)
   - Revenue growth weighting is applied
   - `.is_largest(n_stocks)` selection is used

3. **WHEN** MastiffTemplate validation runs **THEN** it **SHALL** verify:
   - Volume weighting is applied (`vol_ma * buy`)
   - `.is_smallest(n_stocks)` contrarian selection is used
   - Concentrated holdings (n_stocks ≤10)
   - Strict stop loss (≥6%)

4. **WHEN** validation detects errors **THEN** the system **SHALL**:
   - Generate detailed error report with line numbers
   - Categorize errors by severity (CRITICAL | MODERATE | LOW)
   - Provide fix suggestions for common errors
   - Return validation status: PASS | NEEDS_FIX | FAIL

5. **IF** critical validation errors exist **THEN** the system **SHALL**:
   - Block strategy from execution
   - Log error to validation failure log
   - Optionally trigger template regeneration with stronger constraints

6. **WHEN** parameter sensitivity testing is performed **THEN** it **SHALL**:
   - Vary each parameter by ±20%
   - Run backtest for each variation
   - Calculate stability score: `avg_sharpe / baseline_sharpe`
   - Report parameters with stability < 0.6 as sensitive

### Requirement 4: Template-Based Feedback Integration

**User Story**: As a strategy researcher, I want the feedback system to suggest optimal templates based on current performance, so that the AI can intelligently select the right template for the next iteration.

#### Acceptance Criteria

1. **WHEN** feedback is generated after iteration N **THEN** the system **SHALL**:
   - Analyze current strategy's architecture pattern
   - Calculate match score for each template (0.0-1.0)
   - Recommend template with highest match score
   - Include template rationale in feedback

2. **WHEN** performance is below target **THEN** template recommendation **SHALL** prioritize:
   - TurtleTemplate if Sharpe 0.5-1.0 (proven 80% success rate)
   - MastiffTemplate if concentrated risk appetite detected
   - FactorTemplate if stability is priority
   - MomentumTemplate if fast iteration is needed

3. **WHEN** champion exists and performance degraded **THEN** the system **SHALL**:
   - Recommend same template as champion
   - Suggest parameter adjustments within ±20% of champion
   - Include champion's success patterns in feedback
   - Enforce preservation constraints (from learning-system-enhancement)

4. **WHEN** forced exploration mode activates (iteration % 5 == 0) **THEN** the system **SHALL**:
   - Recommend different template than previous 4 iterations
   - Expand parameter ranges to +30%/-30% of defaults
   - Include diversity rationale in feedback

5. **IF** template validation failed in previous iteration **THEN** feedback **SHALL**:
   - Include specific validation errors
   - Suggest parameter constraint adjustments
   - Optionally recommend simpler template (e.g., Factor instead of Turtle)

## Non-Functional Requirements

### Performance

1. **Template Instantiation**: Each template shall instantiate in <100ms
2. **Strategy Generation**: `generate_strategy()` shall complete in <30s (includes data loading + backtest)
3. **Data Caching**: Pre-loading all datasets shall complete in <10s
4. **Hall of Fame Query**: Searching 100 strategies by similarity shall complete in <500ms
5. **Validation**: Template validation shall complete in <5s per strategy

### Security

1. **Code Execution**: All generated strategies shall pass AST validation before execution
2. **File Permissions**: Hall of Fame files shall be write-protected (read-only after creation)
3. **Input Validation**: All user-provided parameters shall be sanitized and type-checked
4. **Backup**: Hall of Fame shall maintain rolling backups (last 7 days)

### Reliability

1. **Error Handling**: 100% of exceptions shall be caught and logged with context
2. **Graceful Degradation**: System shall continue with reduced functionality if Hall of Fame unavailable
3. **Data Integrity**: YAML serialization errors shall not corrupt existing Hall of Fame data
4. **Recovery**: System shall auto-recover from transient file system errors (3 retry attempts)

### Usability

1. **Clear Naming**: Template names shall match documented strategy names (Turtle, Mastiff, Factor, Momentum)
2. **Comprehensive Docs**: Each template shall include docstring with:
   - Architecture pattern description
   - Expected performance ranges
   - Parameter tuning guidelines
   - Usage examples
3. **Progress Tracking**: Grid search shall display real-time progress (current/total, ETA, success count)
4. **Result Export**: All results shall be exportable to JSON for external analysis

### Maintainability

1. **Extensibility**: Adding new templates shall require <2 hours of development time
2. **Backward Compatibility**: New template versions shall support legacy parameter formats
3. **Testing**: Each template shall have ≥3 unit tests covering:
   - Valid parameter generation
   - Invalid parameter rejection
   - Strategy execution success
4. **Documentation**: Code comments shall explain ALL magic numbers and thresholds

---

## Success Criteria

### Functional Validation
- [  ] All 4 templates implemented (Turtle, Mastiff, Factor, Momentum)
- [  ] Hall of Fame stores strategies in 3 tiers (Champions, Contenders, Archive)
- [  ] Template validation catches >90% of common errors
- [  ] Feedback system recommends templates with >80% accuracy

### Performance Validation
- [  ] 30 turtle variations tested: ≥20/30 (67%) achieve Sharpe >1.5
- [  ] Template instantiation: <100ms (target: 50ms)
- [  ] Strategy generation: <30s (target: 15s with caching)
- [  ] Hall of Fame query: <500ms for 100 strategies

### Quality Validation
- [  ] Template code coverage: ≥80%
- [  ] Parameter validation: 100% type safety
- [  ] YAML serialization: 100% success rate
- [  ] Novelty detection: <5% false positives (duplicates marked novel)

---

## Appendix: Template Specifications Summary

### TurtleTemplate
- **Pattern**: Multi-Layer AND Filtering
- **Expected Sharpe**: 1.5-2.5
- **Parameters**: 14 (yield_threshold, ma_short, ma_long, rev_short, rev_long, op_margin_threshold, director_threshold, vol_min, vol_max, n_stocks, stop_loss, take_profit, position_limit, resample)
- **Validated**: Phase 1 (80% success rate)

### MastiffTemplate
- **Pattern**: Contrarian Reversal
- **Expected Sharpe**: 1.2-2.0
- **Parameters**: 10 (lookback_period, rev_decline_threshold, rev_growth_threshold, rev_bottom_ratio, rev_mom_threshold, vol_min, n_stocks, stop_loss, position_limit, resample)
- **Innovation**: Lowest volume selection

### FactorTemplate
- **Pattern**: Single Factor Focus
- **Expected Sharpe**: 0.8-1.3
- **Parameters**: 8 (factor_type, factor_threshold, ma_periods, vol_min, vol_momentum, n_stocks, resample)
- **Use Case**: Low turnover, stable returns

### MomentumTemplate
- **Pattern**: Momentum + Catalyst
- **Expected Sharpe**: 0.8-1.5
- **Parameters**: 9 (momentum_window, ma_periods, catalyst_type, catalyst_lookback, n_stocks, stop_loss, resample, resample_offset)
- **Use Case**: Fast reaction, higher turnover

---

**Document Version**: 1.0
**Status**: Ready for Review
**Next Action**: User approval before proceeding to Design Phase
