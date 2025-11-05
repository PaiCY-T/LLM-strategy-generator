# template-system-phase2 - Task 14

Execute task 14 for the template-system-phase2 specification.

## Task Description
Implement FactorTemplate generate_strategy() method

## Requirements Reference
**Requirements**: 1.2, 1.3, 1.6

## Usage
```
/Task:14-template-system-phase2
```

## Instructions

Execute with @spec-task-executor agent the following task: "Implement FactorTemplate generate_strategy() method"

```
Use the @spec-task-executor agent to implement task 14: "Implement FactorTemplate generate_strategy() method" for the template-system-phase2 specification and include all the below context.

# Steering Context
## Steering Documents Context

No steering documents found or all are empty.

# Specification Context
## Specification Context (Pre-loaded): template-system-phase2

### Requirements
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

---

### Design
# Design Document: Strategy Template Library & Hall of Fame System

## Overview

This design implements a reusable strategy template library and Hall of Fame repository system for the Taiwan Stock Strategy Generation System. Building on Phase 1 validation (80% success rate with turtle variations), this system provides:

1. **Four Core Templates**: Parameterized strategy patterns (Turtle, Mastiff, Factor, Momentum) with validated ranges
2. **Hall of Fame Repository**: Persistent storage for validated strategies with complete genome tracking
3. **Template Validation**: Automated verification of generated strategies against specifications
4. **Intelligent Feedback**: Template recommendation system for iterative learning

**Key Innovation**: Shifts from ad-hoc strategy generation to systematic, template-based approach that eliminates the 90% oversimplification problem that caused 150-iteration failure (130/150 identical P/E strategies).

## Steering Document Alignment

### Technical Standards (tech.md)
- **Python Type Hints**: All functions use comprehensive type annotations
- **Data Caching Pattern**: Leverage existing `get_cached_data()` pattern from `turtle_strategy_generator.py`
- **YAML Serialization**: Human-readable strategy storage format
- **Error Handling**: Robust exception handling with context logging
- **Performance Budget**: <30s per strategy generation including backtest

### Project Structure (structure.md)
- **Templates Module**: `src/templates/` for strategy template classes
- **Repository Module**: `src/repository/` for Hall of Fame persistence
- **Validation Module**: `src/validation/` for template compliance checking
- **Integration**: Extends existing `performance_attributor.py` for pattern extraction

## Code Reuse Analysis

### Existing Components to Leverage

**1. `turtle_strategy_generator.py` (Phase 1 Implementation)**
- **Data Caching Pattern** (lines 71-76): Reuse `get_cached_data()` function pattern
  ```python
  _cached_data = {}
  def get_cached_data(key: str):
      if key not in _cached_data:
          _cached_data[key] = data.get(key)
      return _cached_data[key]
  ```
- **Parameter Grid Definition** (lines 29-61): Template for `PARAM_GRID` structure
- **Strategy Generation Function** (lines 83-159): Pattern for `generate_strategy()` implementation
- **6-Layer Filtering Logic** (lines 106-132): Core architecture for TurtleTemplate
- **Metrics Extraction** (lines 148-158): Standard metrics dictionary format

**2. `performance_attributor.py` (Complete Implementation)**
- **Parameter Extraction** (lines 14-214): `extract_strategy_params()` for validation
- **Success Pattern Extraction** (lines 486-569): `extract_success_patterns()` for Hall of Fame
- **Pattern Prioritization** (lines 572-605): `_prioritize_patterns()` for criticality scoring
- **Strategy Comparison** (lines 268-368): `compare_strategies()` for template matching

**3. `example/高殖利率烏龜.py` (Benchmark Strategy)**
- **6-Layer AND Filtering**: Reference architecture for TurtleTemplate
- **Revenue Growth Weighting**: `cond_all = cond_all * rev_growth_rate` pattern
- **Selection Logic**: `.is_largest(n_stocks)` for ranking

**4. `example/藏獒.py` (Innovative Strategy)**
- **Contrarian Selection**: `buy.is_smallest(n_stocks)` for MastiffTemplate
- **Volume Weighting**: `buy = vol_ma * buy` pattern
- **Strict Risk Controls**: `position_limit=1/3, stop_loss=0.08` for concentrated holdings

### Integration Points

**1. Existing `learning-system-enhancement` Spec**
- **Champion Tracking**: Template system provides genome data for champion preservation
- **Feedback Loop**: Template recommendations integrate with existing feedback mechanism
- **Performance Attribution**: Hall of Fame stores success patterns extracted by `performance_attributor.py`

**2. Data Layer**
- **Finlab Data API**: All templates use standardized `data.get()` calls
- **Caching Strategy**: Shared cache across all template instances for performance

**3. Validation Layer**
- **AST Validation**: Future migration from regex to AST parsing (existing plan)
- **Sandbox Execution**: Templates generate code executed in existing sandbox environment

## Architecture

### System Architecture Diagram

```mermaid
graph TD
    A[Strategy Generation Loop] --> B[Template Selector]
    B --> C[Template Library]
    C --> D1[TurtleTemplate]
    C --> D2[MastiffTemplate]
    C --> D3[FactorTemplate]
    C --> D4[MomentumTemplate]

    D1 --> E[Strategy Generator]
    D2 --> E
    D3 --> E
    D4 --> E

    E --> F[Template Validator]
    F --> G{Validation Pass?}

    G -->|Yes| H[Backtest Executor]
    G -->|No| I[Error Reporter]
    I --> B

    H --> J[Performance Metrics]
    J --> K[Novelty Scorer]
    K --> L{Meets Criteria?}

    L -->|Yes| M[Hall of Fame]
    L -->|No| N[Archive]

    M --> O1[Champions ≥2.0]
    M --> O2[Contenders 1.5-2.0]
    N --> O3[Archive <1.5]

    O1 --> P[Success Pattern Extractor]
    O2 --> P
    P --> Q[Feedback Generator]
    Q --> B

    style C fill:#e1f5ff
    style M fill:#d4f1f4
    style F fill:#fff3cd
    style P fill:#d1ecf1
```

### Template Inheritance Hierarchy

```mermaid
classDiagram
    class BaseTemplate {
        <<abstract>>
        +str name
        +str pattern_type
        +Dict PARAM_GRID
        +Dict expected_performance
        +generate_strategy(params) (report, metrics)
        +validate_params(params) bool
        +get_default_params() Dict
        #_get_cached_data(key) DataFrame
    }

    class TurtleTemplate {
        +pattern_type: "multi_layer_and"
        +expected_sharpe: (1.5, 2.5)
        +generate_strategy(params)
        -_create_6_layer_filter(params)
        -_apply_revenue_weighting()
    }

    class MastiffTemplate {
        +pattern_type: "contrarian_reversal"
        +expected_sharpe: (1.2, 2.0)
        +generate_strategy(params)
        -_create_contrarian_conditions(params)
        -_apply_volume_weighting()
    }

    class FactorTemplate {
        +pattern_type: "factor_ranking"
        +expected_sharpe: (0.8, 1.3)
        +generate_strategy(params)
        -_calculate_factor_score(params)
        -_apply_cross_sectional_rank()
    }

    class MomentumTemplate {
        +pattern_type: "momentum_catalyst"
        +expected_sharpe: (0.8, 1.5)
        +generate_strategy(params)
        -_calculate_momentum(params)
        -_apply_revenue_catalyst(params)
    }

    BaseTemplate <|-- TurtleTemplate
    BaseTemplate <|-- MastiffTemplate
    BaseTemplate <|-- FactorTemplate
    BaseTemplate <|-- MomentumTemplate
```

### Hall of Fame System Architecture

```mermaid
graph LR
    A[Strategy Result] --> B[Novelty Scorer]
    B --> C{Novel?}
    C -->|No < 0.2| D[Reject Duplicate]
    C -->|Yes ≥ 0.2| E[Performance Classifier]

    E --> F{Sharpe Ratio?}
    F -->|≥2.0| G[Champions Tier]
    F -->|1.5-2.0| H[Contenders Tier]
    F -->|<1.5| I[Archive Tier]

    G --> J[Serialize to YAML]
    H --> J
    I --> J

    J --> K[Store Genome]
    K --> L[hall_of_fame/champions/]
    K --> M[hall_of_fame/contenders/]
    K --> N[hall_of_fame/archive/]

    L --> O[Index Update]
    M --> O
    N --> O

    O --> P[Success Pattern Extraction]
    P --> Q[Pattern Database]

    style G fill:#d4edda
    style H fill:#fff3cd
    style I fill:#f8d7da
    style Q fill:#d1ecf1
```

## Components and Interfaces

### Component 1: BaseTemplate (Abstract Base)

**Purpose**: Abstract base class defining common template interface and utilities

**Public Interface**:
```python
class BaseTemplate(ABC):
    """Abstract base class for strategy templates."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Template name (e.g., 'Turtle', 'Mastiff')."""
        pass

    @property
    @abstractmethod
    def pattern_type(self) -> str:
        """Architecture pattern (multi_layer_and|contrarian_reversal|factor_ranking|momentum_catalyst)."""
        pass

    @property
    @abstractmethod
    def PARAM_GRID(self) -> Dict[str, List[Any]]:
        """Parameter grid with validated ranges."""
        pass

    @property
    @abstractmethod
    def expected_performance(self) -> Dict[str, Tuple[float, float]]:
        """Expected performance ranges: sharpe_range, return_range, mdd_range."""
        pass

    @abstractmethod
    def generate_strategy(self, params: Dict[str, Any]) -> Tuple[object, Dict[str, Any]]:
        """Generate strategy from parameters.

        Returns:
            (report, metrics) where metrics contains:
            - sharpe_ratio: float
            - annual_return: float
            - max_drawdown: float
            - success: bool
        """
        pass

    def validate_params(self, params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate parameters against PARAM_GRID.

        Returns:
            (is_valid, error_messages)
        """
        pass

    def get_default_params(self) -> Dict[str, Any]:
        """Get default parameters (midpoint of PARAM_GRID ranges)."""
        pass

    @staticmethod
    def _get_cached_data(key: str) -> Any:
        """Load and cache data to avoid repeated data.get() calls."""
        pass
```

**Dependencies**:
- `finlab.data` for data loading
- `finlab.backtest` for strategy execution
- `typing` for type hints

**Reuses**: Data caching pattern from `turtle_strategy_generator.py:71-76`

---

### Component 2: TurtleTemplate

**Purpose**: Implements 6-layer AND filtering strategy pattern with validated parameter ranges

**Public Interface**:
```python
class TurtleTemplate(BaseTemplate):
    """High dividend yield turtle strategy with 6-layer filtering."""

    name = "Turtle"
    pattern_type = "multi_layer_and"

    PARAM_GRID = {
        'yield_threshold': [4.0, 5.0, 6.0, 7.0, 8.0],
        'ma_short': [10, 20, 30],
        'ma_long': [40, 60, 80],
        'rev_short': [3, 6],
        'rev_long': [12, 18],
        'op_margin_threshold': [0, 3, 5],
        'director_threshold': [5, 10, 15],
        'vol_min': [30, 50, 100],
        'vol_max': [5000, 10000, 15000],
        'n_stocks': [5, 10, 15, 20],
        'stop_loss': [0.06, 0.08, 0.10],
        'take_profit': [0.3, 0.5, 0.7],
        'position_limit': [0.10, 0.125, 0.15, 0.20],
        'resample': ['M', 'W-FRI']
    }

    expected_performance = {
        'sharpe_range': (1.5, 2.5),
        'return_range': (0.20, 0.35),
        'mdd_range': (-0.25, -0.10)
    }

    def generate_strategy(self, params: Dict[str, Any]) -> Tuple[object, Dict]:
        """Generate turtle strategy with 6-layer filtering."""
        pass

    def _create_6_layer_filter(self, params: Dict) -> Any:
        """Create 6-layer AND filter: yield, technical, revenue, quality, insider, liquidity."""
        pass

    def _apply_revenue_weighting(self, conditions: Any, rev_growth: Any) -> Any:
        """Weight conditions by revenue growth rate."""
        pass
```

**Dependencies**:
- Inherits from `BaseTemplate`
- Uses Finlab datasets: `price:收盤價`, `price:成交股數`, `monthly_revenue:當月營收`, etc.

**Reuses**:
- Architecture from `example/高殖利率烏龜.py`
- Parameter grid from `turtle_strategy_generator.py:29-61`
- 6-layer logic from `turtle_strategy_generator.py:106-132`

---

### Component 3: MastiffTemplate

**Purpose**: Implements contrarian reversal strategy with low-volume selection

**Public Interface**:
```python
class MastiffTemplate(BaseTemplate):
    """Contrarian strategy targeting ignored stocks with revenue recovery."""

    name = "Mastiff"
    pattern_type = "contrarian_reversal"

    PARAM_GRID = {
        'lookback_period': [180, 250, 300],
        'rev_decline_threshold': [-10, -15, -20],
        'rev_growth_threshold': [50, 60, 70],
        'rev_bottom_ratio': [0.7, 0.8, 0.9],
        'rev_mom_threshold': [-40, -30, -20],
        'vol_min': [100, 200, 300],
        'n_stocks': [3, 5, 8, 10],
        'stop_loss': [0.06, 0.08, 0.10],
        'position_limit': [0.20, 0.25, 0.33],
        'resample': ['M']
    }

    expected_performance = {
        'sharpe_range': (1.2, 2.0),
        'return_range': (0.15, 0.30),
        'mdd_range': (-0.30, -0.15)
    }

    def generate_strategy(self, params: Dict[str, Any]) -> Tuple[object, Dict]:
        """Generate mastiff contrarian strategy."""
        pass

    def _create_contrarian_conditions(self, params: Dict) -> Any:
        """Create contrarian filters: price high, revenue recovery, ignored stocks."""
        pass

    def _apply_volume_weighting(self, conditions: Any, vol_ma: Any) -> Any:
        """Weight by volume and select LOWEST volume (contrarian)."""
        pass
```

**Dependencies**:
- Inherits from `BaseTemplate`
- Uses Finlab datasets: `price:收盤價`, `price:成交股數`, `monthly_revenue:*`

**Reuses**:
- Contrarian pattern from `example/藏獒.py`
- `.is_smallest(n_stocks)` selection logic
- Volume weighting pattern

---

### Component 4: FactorTemplate

**Purpose**: Single-factor ranking strategy for stable, low-turnover returns

**Public Interface**:
```python
class FactorTemplate(BaseTemplate):
    """Single factor ranking with cross-sectional selection."""

    name = "Factor"
    pattern_type = "factor_ranking"

    PARAM_GRID = {
        'factor_type': ['roe', 'operating_margin', 'dividend_yield', 'revenue_growth'],
        'factor_threshold': [0.5, 0.6, 0.7, 0.8],
        'ma_periods': [20, 60, 120],
        'vol_min': [100, 200, 500],
        'vol_momentum': [True, False],
        'n_stocks': [10, 15, 20, 30],
        'resample': ['M', 'Q']
    }

    expected_performance = {
        'sharpe_range': (0.8, 1.3),
        'return_range': (0.10, 0.20),
        'mdd_range': (-0.20, -0.10)
    }

    def generate_strategy(self, params: Dict[str, Any]) -> Tuple[object, Dict]:
        """Generate factor ranking strategy."""
        pass

    def _calculate_factor_score(self, params: Dict) -> Any:
        """Calculate factor score with normalization."""
        pass

    def _apply_cross_sectional_rank(self, factor: Any, params: Dict) -> Any:
        """Apply cross-sectional ranking using .rank(axis=1, pct=True)."""
        pass
```

**Dependencies**:
- Inherits from `BaseTemplate`
- Uses Finlab fundamental datasets

**Reuses**:
- Cross-sectional ranking pattern from STRATEGY_GENERATION_SYSTEM_SPEC.md
- Factor calculation patterns

---

### Component 5: MomentumTemplate

**Purpose**: Momentum + catalyst strategy for fast reaction to market trends

**Public Interface**:
```python
class MomentumTemplate(BaseTemplate):
    """Momentum strategy with revenue acceleration catalyst."""

    name = "Momentum"
    pattern_type = "momentum_catalyst"

    PARAM_GRID = {
        'momentum_window': [20, 60, 120],
        'ma_periods': [20, 60],
        'catalyst_type': ['revenue_accel', 'earnings_surprise', 'director_buy'],
        'catalyst_lookback': [1, 3, 6],
        'n_stocks': [10, 15, 20],
        'stop_loss': [0.08, 0.10, 0.12],
        'resample': ['W-FRI', 'M'],
        'resample_offset': ['0D', '11D']
    }

    expected_performance = {
        'sharpe_range': (0.8, 1.5),
        'return_range': (0.12, 0.25),
        'mdd_range': (-0.25, -0.12)
    }

    def generate_strategy(self, params: Dict[str, Any]) -> Tuple[object, Dict]:
        """Generate momentum + catalyst strategy."""
        pass

    def _calculate_momentum(self, params: Dict) -> Any:
        """Calculate price momentum indicator."""
        pass

    def _apply_revenue_catalyst(self, params: Dict) -> Any:
        """Apply revenue acceleration catalyst filter."""
        pass
```

**Dependencies**:
- Inherits from `BaseTemplate`
- Uses Finlab price and revenue datasets

**Reuses**:
- Momentum calculation patterns
- Revenue catalyst from `example/月營收與動能策略選股.py`

---

### Component 6: HallOfFameRepository

**Purpose**: Persistent storage and retrieval of validated strategies with genome tracking

**Public Interface**:
```python
class HallOfFameRepository:
    """Repository for storing and querying validated strategies."""

    def __init__(self, base_path: str = "hall_of_fame"):
        """Initialize repository with base storage path."""
        pass

    def add_strategy(
        self,
        iteration_num: int,
        code: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, float],
        success_patterns: List[str]
    ) -> bool:
        """Add strategy to Hall of Fame.

        Returns:
            True if added successfully, False if duplicate or error
        """
        pass

    def get_champions(self, limit: int = 10) -> List[Dict]:
        """Retrieve champion strategies (Sharpe ≥2.0)."""
        pass

    def get_contenders(self, limit: int = 20) -> List[Dict]:
        """Retrieve contender strategies (Sharpe 1.5-2.0)."""
        pass

    def query_similar(
        self,
        strategy_code: str,
        max_distance: float = 0.3
    ) -> List[Dict]:
        """Find similar strategies within distance threshold."""
        pass

    def calculate_novelty_score(
        self,
        strategy_code: str
    ) -> float:
        """Calculate novelty score (0.0=duplicate, 1.0=novel)."""
        pass

    def _classify_tier(self, sharpe: float) -> str:
        """Classify strategy tier based on Sharpe ratio."""
        pass

    def _serialize_to_yaml(self, genome: Dict) -> str:
        """Serialize strategy genome to YAML format."""
        pass

    def _extract_factor_vector(self, code: str) -> np.ndarray:
        """Extract factor usage vector for novelty calculation."""
        pass
```

**Dependencies**:
- `pyyaml` for serialization
- `numpy` for cosine distance calculation
- `performance_attributor.py` for success pattern extraction

**Reuses**:
- `extract_success_patterns()` from `performance_attributor.py:486-569`
- `_prioritize_patterns()` from `performance_attributor.py:572-605`

---

### Component 7: TemplateValidator

**Purpose**: Automated validation of generated strategies against template specifications

**Public Interface**:
```python
class TemplateValidator:
    """Validates generated strategies against template specifications."""

    def validate_strategy(
        self,
        code: str,
        template: BaseTemplate,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate strategy against template specification.

        Returns:
            {
                'status': 'PASS' | 'NEEDS_FIX' | 'FAIL',
                'errors': List[Dict[str, Any]],
                'warnings': List[Dict[str, Any]],
                'suggestions': List[str]
            }
        """
        pass

    def validate_turtle(self, code: str, params: Dict) -> List[Dict]:
        """Validate TurtleTemplate specific requirements."""
        pass

    def validate_mastiff(self, code: str, params: Dict) -> List[Dict]:
        """Validate MastiffTemplate specific requirements."""
        pass

    def test_parameter_sensitivity(
        self,
        template: BaseTemplate,
        baseline_params: Dict[str, Any]
    ) -> Dict[str, float]:
        """Test parameter sensitivity with ±20% variations.

        Returns:
            {param_name: stability_score} where <0.6 is sensitive
        """
        pass

    def _categorize_error(self, error: Dict) -> str:
        """Categorize error severity: CRITICAL | MODERATE | LOW."""
        pass

    def _generate_fix_suggestion(self, error: Dict) -> str:
        """Generate fix suggestion for common errors."""
        pass
```

**Dependencies**:
- Uses `performance_attributor.extract_strategy_params()` for validation
- Uses AST parsing (future migration)

**Reuses**:
- Parameter extraction from `performance_attributor.py:14-214`
- Validation patterns

---

### Component 8: TemplateFeedbackIntegrator

**Purpose**: Integrates template recommendations into existing feedback loop

**Public Interface**:
```python
class TemplateFeedbackIntegrator:
    """Integrates template system with feedback loop."""

    def __init__(
        self,
        hall_of_fame: HallOfFameRepository,
        templates: Dict[str, BaseTemplate]
    ):
        """Initialize with Hall of Fame and template registry."""
        pass

    def recommend_template(
        self,
        current_metrics: Dict[str, float],
        iteration_num: int,
        previous_template: Optional[str] = None
    ) -> Dict[str, Any]:
        """Recommend optimal template for next iteration.

        Returns:
            {
                'template_name': str,
                'rationale': str,
                'match_score': float,
                'suggested_params': Dict[str, Any]
            }
        """
        pass

    def calculate_template_match_score(
        self,
        strategy_code: str,
        template: BaseTemplate
    ) -> float:
        """Calculate how well strategy matches template (0.0-1.0)."""
        pass

    def get_champion_template_params(self) -> Optional[Dict[str, Any]]:
        """Get parameters from champion strategy if exists."""
        pass

    def _should_force_exploration(self, iteration_num: int) -> bool:
        """Check if forced exploration mode (iteration % 5 == 0)."""
        pass
```

**Dependencies**:
- `HallOfFameRepository` for champion retrieval
- Template registry
- Existing feedback mechanism

**Reuses**:
- Champion tracking from `learning-system-enhancement` spec
- Feedback patterns

---

## Data Models

### Strategy Genome (YAML Storage Format)

```yaml
iteration_num: 42
timestamp: "2025-10-10T14:23:45.123456"
template_name: "Turtle"
pattern_type: "multi_layer_and"

parameters:
  yield_threshold: 6.0
  ma_short: 20
  ma_long: 60
  rev_short: 3
  rev_long: 12
  op_margin_threshold: 3
  director_threshold: 10
  vol_min: 50
  vol_max: 10000
  n_stocks: 10
  stop_loss: 0.06
  take_profit: 0.5
  position_limit: 0.125
  resample: "M"

metrics:
  sharpe_ratio: 2.15
  annual_return: 0.2925
  max_drawdown: -0.1541
  win_rate: 0.65
  total_trades: 120

robustness:
  parameter_sensitivity:
    yield_threshold: 0.85
    ma_short: 0.92
    n_stocks: 0.78
  out_of_sample_sharpe: 1.98

novelty_score: 0.45

success_patterns:
  - "roe.rolling(window=4).mean() - 4-quarter smoothing reduces quarterly noise"
  - "liquidity_filter > 100,000,000 TWD - Selects stable, high-volume stocks"
  - "revenue_yoy.ffill() - Forward-filled revenue data handles missing values"

code: |
  from finlab import data
  from finlab.backtest import sim

  close = data.get("price:收盤價")
  # ... strategy code ...
```

### Template Registry Configuration

```python
TemplateConfig = {
    'name': str,                    # Template name
    'class': Type[BaseTemplate],    # Template class
    'pattern_type': str,            # Architecture pattern
    'expected_sharpe': Tuple[float, float],
    'success_rate_phase1': float,   # Historical success rate
    'use_cases': List[str],         # When to recommend
    'characteristics': List[str]    # Key features
}
```

### Validation Result Schema

```python
ValidationResult = {
    'status': str,                  # PASS | NEEDS_FIX | FAIL
    'errors': List[{
        'severity': str,            # CRITICAL | MODERATE | LOW
        'category': str,            # parameter | architecture | data | backtest
        'message': str,
        'line_number': Optional[int],
        'suggestion': str
    }],
    'warnings': List[{
        'category': str,
        'message': str
    }],
    'parameter_sensitivity': Dict[str, float],
    'timestamp': str
}
```

## Error Handling

### Error Scenarios

**1. Template Instantiation Failure**
- **Scenario**: Invalid PARAM_GRID definition or missing required attributes
- **Handling**: Raise `TemplateConfigurationError` with detailed message
- **User Impact**: System logs error and falls back to default parameters
- **Recovery**: Load backup parameter grid from configuration file

**2. Data Loading Failure**
- **Scenario**: `data.get()` call fails due to API timeout or missing dataset
- **Handling**: Retry 3x with exponential backoff, then raise `DataLoadError`
- **User Impact**: Strategy generation skipped for this iteration
- **Recovery**: Cache successful data loads, use stale cache if available

**3. Strategy Generation Exception**
- **Scenario**: Exception during strategy code execution (division by zero, NaN values)
- **Handling**: Catch exception, log full traceback, mark strategy as failed
- **User Impact**: Iteration marked as failed, feedback suggests parameter adjustments
- **Recovery**: Adjust parameters to avoid problematic conditions

**4. Validation Critical Errors**
- **Scenario**: Generated strategy fails critical validation checks
- **Handling**: Block execution, generate detailed error report
- **User Impact**: Strategy not executed, feedback includes fix suggestions
- **Recovery**: Trigger template regeneration with stronger constraints

**5. Hall of Fame Serialization Failure**
- **Scenario**: YAML serialization fails due to invalid data types or file permissions
- **Handling**: Log error, attempt write to backup location `hall_of_fame/backup/`
- **User Impact**: Strategy not persisted but iteration continues
- **Recovery**: Retry serialization on next successful strategy

**6. Novelty Calculation Failure**
- **Scenario**: Cosine distance calculation fails due to empty Hall of Fame or invalid vectors
- **Handling**: Return default novelty score of 1.0 (assume novel)
- **User Impact**: Strategy accepted even if might be duplicate
- **Recovery**: Manual review of Hall of Fame for duplicates

**7. Hall of Fame Size Overflow**
- **Scenario**: Hall of Fame exceeds 100 strategies
- **Handling**: Archive lowest 20% of Contenders, compress old strategies
- **User Impact**: Transparent maintenance operation
- **Recovery**: Full index maintained for fast lookup

**8. Parameter Sensitivity Test Timeout**
- **Scenario**: Sensitivity testing exceeds time budget (>5 minutes)
- **Handling**: Abort remaining tests, return partial results
- **User Impact**: Incomplete sensitivity scores reported
- **Recovery**: Mark parameters as "sensitivity_unknown"

## Testing Strategy

### Unit Testing

**Template Tests** (`tests/templates/test_*.py`):
- Valid parameter generation from PARAM_GRID
- Invalid parameter rejection (out of range, wrong type)
- Strategy generation success with default parameters
- Data caching functionality
- Metrics extraction accuracy

**Hall of Fame Tests** (`tests/repository/test_hall_of_fame.py`):
- Strategy genome serialization/deserialization
- Novelty score calculation accuracy
- Tier classification logic
- Query similarity functionality
- Duplicate rejection

**Validation Tests** (`tests/validation/test_validator.py`):
- Template-specific validation rules
- Error categorization logic
- Fix suggestion generation
- Parameter sensitivity calculation

**Coverage Target**: ≥80% for all template and repository modules

### Integration Testing

**Template Integration** (`tests/integration/test_templates.py`):
- Full strategy generation pipeline
- Template → Generation → Validation → Backtest → Metrics
- Data caching across multiple strategy generations
- Error handling and recovery

**Hall of Fame Integration** (`tests/integration/test_repository.py`):
- Multi-tier storage and retrieval
- Concurrent write operations
- Index consistency after archival
- Success pattern extraction integration

**Feedback Integration** (`tests/integration/test_feedback.py`):
- Template recommendation logic
- Champion-based parameter suggestions
- Forced exploration mode triggering

### End-to-End Testing

**Complete Workflow** (`tests/e2e/test_workflow.py`):
1. Initialize template library
2. Generate strategy from each template
3. Validate generated strategies
4. Execute backtests
5. Store successful strategies in Hall of Fame
6. Extract success patterns
7. Generate feedback recommendations
8. Verify feedback influences next iteration

**Performance Testing**:
- Template instantiation: <100ms per template
- Strategy generation: <30s including backtest
- Data caching: <10s for all datasets
- Hall of Fame query: <500ms for 100 strategies
- Validation: <5s per strategy

**Stress Testing**:
- Generate 50 strategies concurrently
- Hall of Fame with 200+ strategies
- Query similarity with 500+ strategies

## Implementation Phases

### Phase 1: Core Template Library (Tasks 1-15)
- BaseTemplate abstract class
- Four concrete template implementations
- Data caching infrastructure
- Basic parameter validation

### Phase 2: Hall of Fame System (Tasks 16-25)
- Repository implementation
- YAML serialization
- Novelty scoring
- Tier classification
- Success pattern extraction integration

### Phase 3: Validation System (Tasks 26-35)
- Template validator implementation
- Template-specific validation rules
- Error reporting and suggestions
- Parameter sensitivity testing

### Phase 4: Feedback Integration (Tasks 36-45)
- Template recommendation logic
- Champion parameter suggestions
- Forced exploration mode
- Integration with existing feedback loop

### Phase 5: Testing & Documentation (Tasks 46-50)
- Comprehensive unit tests
- Integration tests
- End-to-end tests
- Documentation and examples

---

**Document Version**: 1.0
**Status**: Ready for Review
**Next Action**: User approval before proceeding to Tasks Phase
**Dependencies**: Requires approved requirements.md

**Key Design Decisions**:
1. **Template inheritance**: Abstract base class ensures consistent interface
2. **YAML storage**: Human-readable format for strategy genomes
3. **Three-tier Hall of Fame**: Champions, Contenders, Archive for scalability
4. **Novelty scoring**: Cosine distance prevents duplicate strategies
5. **Reuse existing code**: Leverages validated Phase 1 patterns and performance_attributor.py
6. **Graceful degradation**: System continues with reduced functionality on non-critical errors

**Note**: Specification documents have been pre-loaded. Do not use get-content to fetch them again.

## Task Details
- Task ID: 14
- Description: Implement FactorTemplate generate_strategy() method
- Requirements: 1.2, 1.3, 1.6

## Instructions
- Implement ONLY task 14: "Implement FactorTemplate generate_strategy() method"
- Follow all project conventions and leverage existing code
- Mark the task as complete using: claude-code-spec-workflow get-tasks template-system-phase2 14 --mode complete
- Provide a completion summary
```

## Task Completion
When the task is complete, mark it as done:
```bash
claude-code-spec-workflow get-tasks template-system-phase2 14 --mode complete
```

## Next Steps
After task completion, you can:
- Execute the next task using /template-system-phase2-task-[next-id]
- Check overall progress with /spec-status template-system-phase2
