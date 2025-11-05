# Requirements Document: Exit Mutation Redesign

## Introduction

The current AST-based exit mutation system has a **0/41 success rate** due to fundamental design flaws: attempting to modify complex nested AST structures for exit conditions leads to syntax errors and validation failures. This feature **redesigns exit mutation** to use parameter-based genetic operators that mutate numerical parameters (stop_loss_pct, take_profit_pct, trailing_stop_offset) within bounded ranges.

**MEDIUM PRIORITY**: This fixes a known failure mode but is not blocking LLM integration. Can be completed in Week 2-3 after higher priority items.

**Value Proposition**: Achieve >70% exit mutation success rate by shifting from brittle AST manipulation to robust parameter mutation, unlocking exit strategy optimization that currently contributes 0% to strategy evolution.

## Alignment with Product Vision

This feature improves the **Factor Graph mutation** foundation by:
- **Fixing failed mutation type**: Converting 0% success rate to >70% success rate
- **Expanding search space**: Enabling optimization of exit conditions (stop loss, take profit, trailing stops)
- **Complementing LLM innovation**: Providing genetic operators for exit parameter tuning that LLM can leverage
- **Increasing diversity**: Adding working exit mutations to the mutation portfolio

## Requirements

### Requirement 1: Parameter-Based Exit Mutation

**User Story:** As the Factor Graph mutation system, I want to mutate exit condition parameters numerically, so that I can optimize stop losses and take profit levels without AST complexity.

#### Acceptance Criteria

1. WHEN exit mutation is triggered THEN the system SHALL identify parameters: stop_loss_pct, take_profit_pct, trailing_stop_offset, holding_period_days
2. WHEN parameter is selected for mutation THEN the system SHALL use uniform random selection (25% probability each parameter)
3. WHEN a parameter is selected for mutation THEN the system SHALL apply Gaussian noise: new_value = old_value * (1 + N(0, 0.15))
4. WHEN mutated value is generated THEN the system SHALL clamp to bounded ranges: stop_loss [0.01, 0.20], take_profit [0.05, 0.50], trailing_stop [0.005, 0.05], holding_period [1, 60]
5. WHEN mutation is applied THEN the system SHALL update parameter in strategy code using regex replacement
6. WHEN regex replacement succeeds THEN the system SHALL validate updated code with ast.parse() before returning
7. WHEN ast.parse() fails THEN original code SHALL be returned with error logged: "Validation failed: {error_message}"

### Requirement 2: Bounded Range Enforcement

**User Story:** As the system designer, I want strict bounds on exit parameters, so that mutations do not generate unrealistic or invalid values (e.g., 200% stop loss).

#### Acceptance Criteria

1. WHEN stop_loss_pct is mutated THEN new value SHALL be in [0.01, 0.20] (1% to 20% max loss)
2. WHEN take_profit_pct is mutated THEN new value SHALL be in [0.05, 0.50] (5% to 50% profit target)
3. WHEN trailing_stop_offset is mutated THEN new value SHALL be in [0.005, 0.05] (0.5% to 5% trailing offset)
4. WHEN holding_period_days is mutated THEN new value SHALL be in [1, 60] (1 day to 2 months)
5. WHEN clamping occurs THEN the system SHALL log: "Parameter {name} clamped from {old} to {new}"

### Requirement 3: Gaussian Noise Mutation

**User Story:** As the genetic algorithm, I want to apply Gaussian noise for parameter mutation, so that mutations explore nearby values with occasional larger jumps.

#### Acceptance Criteria

1. WHEN Gaussian noise is generated THEN it SHALL use: mean=0, std_dev=0.15 (15% typical change)
2. WHEN noise is applied THEN new_value = old_value * (1 + noise) to preserve sign and scale
3. WHEN noise produces negative value THEN absolute value SHALL be used: new_value = abs(new_value)
4. WHEN noise is sampled THEN 68% of mutations SHALL be within ±15% of original value
5. WHEN noise is sampled THEN 95% of mutations SHALL be within ±30% of original value
6. WHEN extreme values are generated THEN bounds SHALL clamp them to valid ranges

### Requirement 4: Regex-Based Code Update

**User Story:** As the mutation system, I want to use regex replacement to update parameters, so that I avoid complex AST manipulation that causes syntax errors.

#### Acceptance Criteria

1. WHEN stop_loss_pct is mutated THEN regex SHALL match: `stop_loss_pct\s*=\s*([\d.]+)` and replace value
2. WHEN take_profit_pct is mutated THEN regex SHALL match: `take_profit_pct\s*=\s*([\d.]+)` and replace value
3. WHEN trailing_stop_offset is mutated THEN regex SHALL match: `trailing_stop[_a-z]*\s*=\s*([\d.]+)` and replace value (non-greedy pattern)
4. WHEN holding_period_days is mutated THEN regex SHALL match: `holding_period[_a-z]*\s*=\s*(\d+)` and replace value (non-greedy pattern)
5. WHEN holding_period mutation is applied THEN new value SHALL be rounded: int(round(new_value))
6. WHEN parameter appears multiple times THEN first occurrence SHALL be mutated
7. WHEN regex replacement fails to find parameter THEN mutation SHALL be skipped and logged: "Parameter {name} not found in code"

### Requirement 5: Integration with Factor Graph

**User Story:** As the Factor Graph mutation system, I want exit mutation to be a first-class mutation operator, so that it is used alongside add/remove/modify mutations.

#### Acceptance Criteria

1. WHEN mutation type is selected THEN exit mutation SHALL have 20% probability (alongside add 30%, remove 20%, modify 30%)
2. WHEN exit mutation is executed THEN it SHALL return mutated code and metadata: {"mutation_type": "exit_param", "parameter": "stop_loss_pct", "old_value": 0.10, "new_value": 0.12}
3. WHEN exit mutation fails THEN it SHALL return original code and log failure reason
4. WHEN exit mutation succeeds THEN it SHALL be tracked in mutation statistics: exit_mutations_total, exit_mutation_success_rate
5. WHEN strategy history is analyzed THEN successful exit mutations SHALL be extractable from metadata

## Non-Functional Requirements

### Performance
- Mutation latency: <100ms per exit parameter mutation
- Regex matching: <10ms per parameter lookup
- Zero performance impact to other mutation types

### Reliability
- Success rate: ≥70% for strategies with extractable exit parameters
- No crashes from regex failures (all exceptions caught)
- Backward compatible with strategies lacking exit parameters (skip gracefully)

### Maintainability
- Bounded ranges configurable in config/learning_system.yaml
- Gaussian std_dev configurable (default 0.15)
- Clear logging of all mutations: parameter, old value, new value, result

## Dependencies

- Existing code: `src/mutation/factor_graph.py` or equivalent mutation system
- Python libraries: `pip install numpy>=1.24.0` (for Gaussian noise)
- Configuration: config/learning_system.yaml with exit_mutation.bounds and exit_mutation.gaussian_stddev
- Validation: existing AST validation and syntax checking

## Timeline

- **Total Effort**: 3-5 days
- **Priority**: MEDIUM (improves mutation quality but not blocking)
- **Week 2-3 Target**: Complete after llm-integration-activation
- **Dependency Chain**: Independent of other critical path items, can run in parallel

## Success Metrics

1. **Success Rate**: ≥70% of exit mutations pass validation (vs 0% currently)
2. **Coverage**: All 4 exit parameters supported (stop_loss, take_profit, trailing_stop, holding_period)
3. **Bounded Mutation**: 100% of mutations stay within defined ranges
4. **Integration**: Exit mutation used in 20% of Factor Graph iterations
5. **Validation**: 20-generation test shows exit mutations contributing to strategy diversity

## Out of Scope

- Multi-parameter mutation (mutate one parameter per iteration)
- Adaptive bounds based on performance (static bounds only)
- Correlation-aware mutation (independent parameter changes)
- Exit condition reordering or logic changes (parameter values only)
- Learning optimal parameter ranges (predefined bounds only)
