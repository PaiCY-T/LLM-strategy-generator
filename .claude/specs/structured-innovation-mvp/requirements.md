# Requirements Document: Structured Innovation MVP (Phase 2a)

## Introduction

Full Python code generation by LLMs has high hallucination risk and security overhead. This feature implements **YAML/JSON-based structured innovation** where the LLM creates declarative strategy specifications instead of full code. The system then generates Python code from these specifications using templates, reducing hallucination risk by 80% while covering 85% of innovation needs.

**MEDIUM PRIORITY**: This is Phase 2a of LLM innovation, building on the foundation of llm-integration-activation to enable safer, more reliable LLM-driven innovation.

**Value Proposition**: Enable LLM to innovate through structured specifications (indicators, conditions, rules) instead of code, achieving >90% generation success rate vs ~60% for full code generation while maintaining innovation capability.

## Alignment with Product Vision

This feature advances the **LLM Innovation roadmap** by:
- **Safer innovation**: Reducing hallucination and syntax errors through declarative specifications
- **Higher success rate**: Templates ensure syntactically correct code generation
- **Broad coverage**: 85% of strategy variations expressible via YAML/JSON
- **Maintainability**: Strategies as data (YAML) are easier to inspect, version, and modify than full code

## Requirements

### Requirement 1: YAML Schema Definition

**User Story:** As the system designer, I want a comprehensive YAML schema for strategy specifications, so that LLMs can express diverse strategies declaratively.

#### Acceptance Criteria

1. WHEN a YAML strategy spec is created THEN it SHALL contain sections: metadata, indicators, entry_conditions, exit_conditions, position_sizing, risk_management
2. WHEN metadata is defined THEN it SHALL include: name, description, strategy_type (momentum/mean_reversion/factor_combination), rebalancing_frequency (M/W-FRI)
3. WHEN indicators are defined THEN they SHALL support: technical_indicators (RSI, MACD, BB), fundamental_factors (ROE, PB_ratio), custom_calculations (expressions)
4. WHEN entry_conditions are defined THEN they SHALL support: threshold_rules (RSI > 30), ranking_rules (top 20% by momentum), logical_operators (AND/OR/NOT)
5. WHEN exit_conditions are defined THEN they SHALL support: stop_loss_pct, take_profit_pct, trailing_stop, holding_period_days, conditional_exits (if RSI < 70)

### Requirement 2: Code Generation from YAML

**User Story:** As the system, I want to generate syntactically correct Python code from YAML specs, so that LLM-created strategies execute reliably without hallucination errors.

#### Acceptance Criteria

1. WHEN a YAML spec is received THEN the system SHALL validate it against schema using jsonschema library
2. WHEN validation passes THEN the system SHALL generate Python code using Jinja2 templates
3. WHEN indicators are processed THEN generated code SHALL use correct FinLab API calls: data.get('RSI_14'), data.get('revenue_growth')
4. WHEN entry conditions are processed THEN generated code SHALL generate boolean masks: (rsi > 30) & (close > ma_50)
5. WHEN position sizing is processed THEN generated code SHALL implement: equal_weight, factor_weighted, risk_parity, or custom formulas

### Requirement 3: LLM Prompt Engineering for YAML

**User Story:** As the InnovationEngine, I want prompts that guide the LLM to generate valid YAML specs, so that specifications conform to the schema without trial-and-error.

#### Acceptance Criteria

1. WHEN LLM is called THEN prompt SHALL include: full YAML schema with examples, 3 complete strategy examples (momentum, mean reversion, factor combo)
2. WHEN innovation directive is "modify" THEN prompt SHALL request: "Modify the YAML spec by adjusting {parameters} or adding {indicators}"
3. WHEN innovation directive is "create" THEN prompt SHALL request: "Create a novel YAML spec inspired by {champion_approach} using different indicators/conditions"
4. WHEN LLM response is parsed THEN the system SHALL extract YAML using regex: ```yaml\n(.*?)\n``` or ```json\n(.*?)\n```
5. WHEN parsing fails THEN the system SHALL retry with explicit instruction: "Return ONLY the YAML specification, no explanation text"

### Requirement 4: Schema Coverage and Extensibility

**User Story:** As a strategy designer, I want the YAML schema to cover 85% of real-world strategy patterns, so that most innovations can be expressed without falling back to full code generation.

#### Acceptance Criteria

1. WHEN strategy type is "momentum" THEN schema SHALL support: trend indicators (MA, EMA), momentum oscillators (RSI, MACD), volume filters
2. WHEN strategy type is "mean_reversion" THEN schema SHALL support: overbought/oversold thresholds, Bollinger Bands, Z-score calculations
3. WHEN strategy type is "factor_combination" THEN schema SHALL support: multiple factors (value, quality, momentum), composite scores, factor weighting
4. WHEN custom calculations are needed THEN schema SHALL support: mathematical expressions as strings: "ROE * (1 - debt_ratio)"
5. WHEN schema is insufficient THEN system SHALL log: "YAML coverage gap: {strategy_pattern}" and fall back to full code generation

### Requirement 5: Integration with InnovationEngine

**User Story:** As the autonomous loop, I want structured innovation to replace full code generation for 80% of LLM iterations, so that success rate improves while maintaining innovation capability.

#### Acceptance Criteria

1. WHEN llm_mode is "structured" in config THEN InnovationEngine SHALL use YAML generation prompts
2. WHEN llm_mode is "code" THEN InnovationEngine SHALL use full code generation prompts (existing behavior)
3. WHEN llm_mode is "hybrid" THEN InnovationEngine SHALL use structured 80%, code 20% (randomly selected)
4. WHEN YAML validation fails THEN system SHALL log error and fall back to Factor Graph mutation
5. WHEN YAML generation succeeds THEN generated Python code SHALL be validated using existing AST validation

## Non-Functional Requirements

### Performance
- YAML parsing and validation: <50ms per specification
- Code generation from template: <200ms per specification
- Zero performance regression vs full code generation

### Reliability
- YAML validation success rate: >95% (strict schema prevents malformed specs)
- Code generation success rate: 100% (templates guarantee syntactically correct code)
- End-to-end LLM → YAML → Code → Execution success rate: >90%

### Maintainability
- YAML schema versioned in config/strategy_schema_v1.yaml
- Jinja2 templates in src/generators/yaml_to_code_template.py
- Schema extensible via plugins (future: custom indicator definitions)

### Observability
- Log every YAML spec generated: timestamp, indicators used, conditions, parameters
- Export metrics: yaml_generation_total, yaml_validation_success_rate, code_generation_success_rate
- Track schema coverage gaps (patterns requiring full code generation)

## Dependencies

- Completed specs: docker-sandbox-security, llm-integration-activation
- Python libraries: `pip install pyyaml>=6.0 jsonschema>=4.17.0 jinja2>=3.1.0`
- Configuration: config/learning_system.yaml with llm_mode (structured/code/hybrid)
- Existing code: InnovationEngine implementation, FinLab API wrappers
- Templates: Jinja2 templates for momentum, mean reversion, factor combination strategies

## Timeline

- **Total Effort**: 2-3 weeks (schema design 3 days, code gen 5 days, integration 3 days, testing 3 days)
- **Priority**: MEDIUM (Phase 2a - after base LLM integration validated)
- **Week 3-4 Target**: Complete implementation and validate with 50-generation test
- **Dependency Chain**: docker-sandbox-security → llm-integration-activation → THIS → Task 3.5

## Success Metrics

1. **Schema Coverage**: ≥85% of historical successful strategies expressible in YAML
2. **Validation Success**: >95% of LLM-generated YAML specs pass schema validation
3. **Code Generation Success**: 100% of valid YAML specs generate executable Python code
4. **End-to-End Success**: >90% of structured innovation iterations produce valid, executable strategies
5. **Production Validation**: 50-generation test with structured innovation shows improved success rate vs full code generation

## Out of Scope

- Multi-strategy ensembles in single YAML (one strategy per spec)
- Custom Python code injection in YAML (pure declarative specifications only)
- Automatic schema expansion from failed patterns (manual schema updates only)
- Version migration for schema changes (breaking changes require new schema version)
- Visual editor for YAML specs (text-based only)

## YAML Schema Example

```yaml
metadata:
  name: "High ROE Momentum Strategy"
  description: "Select top 20% stocks by ROE, filter by momentum, equal weight"
  strategy_type: "factor_combination"
  rebalancing_frequency: "M"

indicators:
  fundamental:
    - name: "roe"
      source: "data.get('ROE')"
    - name: "revenue_growth"
      source: "data.get('revenue_growth')"
  technical:
    - name: "rsi_14"
      source: "data.get('RSI_14')"
    - name: "ma_50"
      source: "data.get('MA_50')"
  custom:
    - name: "quality_score"
      expression: "roe * (1 + revenue_growth)"

entry_conditions:
  ranking:
    - field: "quality_score"
      top_percent: 20
      ascending: false
  filters:
    - condition: "rsi_14 > 30"
    - condition: "close > ma_50"
    - condition: "average_volume_20d > 150_000_000"
  logic: "AND"

exit_conditions:
  stop_loss_pct: 0.10
  take_profit_pct: 0.25
  trailing_stop_offset: 0.02
  holding_period_days: 30

position_sizing:
  method: "equal_weight"
  max_positions: 20

risk_management:
  max_position_pct: 0.10
  max_sector_exposure: 0.30
  rebalance_threshold: 0.15
```

This YAML would generate Python code:
```python
def strategy(data):
    # Load indicators
    roe = data.get('ROE')
    revenue_growth = data.get('revenue_growth')
    rsi_14 = data.get('RSI_14')
    ma_50 = data.get('MA_50')
    close = data.get('price:收盤價')
    volume = data.get('price:成交股數')

    # Calculate custom indicators
    quality_score = roe * (1 + revenue_growth)

    # Apply filters
    filter_mask = (rsi_14 > 30) & (close > ma_50) & (volume.rolling(20).mean() > 150_000_000)

    # Rank by quality score
    rank = quality_score.rank(ascending=False, pct=True)
    entry_mask = (rank <= 0.20) & filter_mask

    # Equal weight position sizing
    position = entry_mask.astype(float) / entry_mask.sum()

    return position
```
