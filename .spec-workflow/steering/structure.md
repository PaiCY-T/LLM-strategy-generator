# Project Structure

## Directory Organization

```
finlab/                           # Project root
├── .claude/                      # Legacy spec system (DEPRECATED)
│   └── specs/                    # 19 historical specs
├── .spec-workflow/               # New spec workflow system (ACTIVE)
│   ├── specs/                    # Spec documents (requirements, design, tasks)
│   ├── steering/                 # This directory - project guidance
│   ├── templates/                # Document templates
│   └── approvals/                # Approval workflow tracking
│
├── src/                          # Source code (153 Python files, 4.8MB)
│   ├── analysis/                 # Strategy analysis and reporting
│   ├── backtest/                 # Backtesting metrics and utilities
│   │   ├── executor.py           # Backtest execution engine
│   │   ├── metrics.py            # StrategyMetrics dataclass (Bug #5b fix location)
│   │   └── classifier.py         # SuccessClassifier (requires execution_result structure)
│   ├── config/                   # Configuration management
│   │   └── anti_churn_manager.py
│   ├── data/                     # Data layer (Finlab API integration)
│   │   ├── downloader.py
│   │   ├── cache.py
│   │   └── freshness.py
│   ├── evolution/                # Evolution system
│   │   └── population_manager.py
│   ├── innovation/               # 🤖 LLM-driven innovation (CORE CAPABILITY)
│   │   ├── innovation_engine.py  # Core InnovationEngine orchestration
│   │   ├── llm_provider.py       # Multi-provider LLM abstraction (OpenRouter/Gemini/OpenAI)
│   │   ├── prompt_builder.py     # Context-aware prompt generation
│   │   ├── security_validator.py # Code safety checks (file I/O, imports, exec)
│   │   ├── feedback_processor.py # Learning from validation failures
│   │   ├── baseline_metrics.py   # Performance baseline tracking
│   │   └── validators/           # 7-layer validation framework
│   │       ├── innovation_validator.py  # Comprehensive validation pipeline
│   │       ├── yaml_schema_validator.py # YAML structure validation
│   │       └── yaml_to_code_generator.py # Jinja2 template-based code generation
│   ├── factor_graph/             # Factor Graph system (Phase 2 Matrix-Native ✅ 2025-11-01)
│   │   ├── finlab_dataframe.py   # ✅ Matrix-Native container (Dates×Symbols data, lazy loading)
│   │   ├── strategy.py           # Strategy composition with FinLabDataFrame
│   │   ├── factor.py             # Factor base class
│   │   └── pipeline.py           # Execution pipeline
│   ├── factor_library/           # 13 reusable factors
│   │   ├── registry.py           # Factor discovery
│   │   ├── momentum/             # Momentum factors
│   │   ├── value/                # Value factors
│   │   ├── quality/              # Quality factors
│   │   ├── risk/                 # Risk factors
│   │   ├── entry/                # Entry signal factors
│   │   └── exit/                 # Exit strategy factors
│   ├── learning/                 # ⚙️ Autonomous Learning Loop (EXECUTION ENGINE)
│   │   ├── unified_loop.py       # ✅ UnifiedLoop - Facade Pattern (450 lines, A grade)
│   │   │                         #    - Wraps LearningLoop complexity
│   │   │                         #    - Template Mode injection via Strategy Pattern
│   │   │                         #    - Production ready (2025-11-24)
│   │   ├── template_iteration_executor.py  # ✅ Template Mode Executor (417 lines)
│   │   │                         #    - Strategy Pattern implementation
│   │   │                         #    - Direct template execution (no code generation)
│   │   │                         #    - Bug #5 fixed: generate_strategy() not generate_code()
│   │   │                         #    - 100% success rate (20/20 smoke test)
│   │   ├── learning_loop.py      # Main orchestrator (372 lines) - 10-step process
│   │   ├── iteration_executor.py # Iteration execution engine (519 lines) - Step-by-step execution
│   │   ├── champion_tracker.py   # Best strategy tracking (1,138 lines) - Performance history
│   │   ├── iteration_history.py  # JSONL persistence (651 lines) - Complete record management
│   │   ├── feedback_generator.py # Context generation for LLM (408 lines) - Pattern extraction
│   │   ├── learning_config.py    # Configuration management (457 lines) - 21-parameter config
│   │   ├── unified_config.py     # UnifiedConfig dataclass (NEW - 2025-11-24)
│   │   │                         #    - Template Mode configuration support
│   │   ├── llm_client.py        # LLM provider abstraction (420 lines) - Multi-provider support
│   │   └── config_manager.py     # Config loading and validation
│   ├── feedback/                 # Learning system feedback
│   │   ├── loop_integration.py
│   │   ├── rationale_generator.py
│   │   ├── template_analytics.py
│   │   └── template_feedback_integrator.py
│   ├── generators/               # Code generation utilities
│   ├── innovation/               # Innovation tracking
│   │   └── validators/
│   ├── monitoring/               # System monitoring
│   │   └── variance_monitor.py
│   ├── mutation/                 # Strategy mutation operators
│   │   ├── tier2/                # Structural mutations
│   │   ├── tier3/                # Relational mutations
│   │   └── tier_selection/       # Tier selection logic
│   ├── population/               # Population-based learning
│   ├── recovery/                 # Rollback and recovery
│   │   └── rollback_manager.py
│   ├── repository/               # Data persistence
│   │   ├── hall_of_fame.py       # Champion storage
│   │   ├── hall_of_fame_yaml.py  # YAML export
│   │   ├── index_manager.py      # Indexing
│   │   └── pattern_search.py     # Pattern search
│   ├── storage/                  # Database layer (future)
│   ├── templates/                # ✅ Strategy Templates (4 templates) - Template Mode Ready
│   │   ├── base_template.py      # ✅ Abstract interface (Template Method Pattern)
│   │   │                         #    - generate_strategy(params) → (report, metrics_dict)
│   │   │                         #    - NOT generate_code() (Bug #5a fix)
│   │   ├── turtle_template.py    # 6-layer AND filtering
│   │   ├── mastiff_template.py   # Contrarian reversal
│   │   ├── factor_template.py    # Single-factor ranking
│   │   └── momentum_template.py  # ✅ Momentum + catalyst (Production ready)
│   │                             #    - 100% success rate in Template Mode
│   │                             #    - generate_strategy() returns (report, metrics_dict)
│   │                             #    - Direct finlab backtest execution
│   ├── tier1/                    # Tier 1 YAML-based strategy generation
│   │   ├── yaml_validator.py     # YAML schema validation
│   │   ├── yaml_interpreter.py   # YAML to code interpretation
│   │   └── factor_factory.py     # Factor instantiation from YAML
│   ├── intelligence/             # Advanced decision intelligence (2025-11-15)
│   │   ├── multi_objective.py    # Multi-objective validation (Sharpe + MDD + Calmar)
│   │   ├── portfolio_optimizer.py # Portfolio optimization algorithms
│   │   └── regime_detector.py    # Market regime detection
│   ├── ui/                       # User interface (future)
│   ├── utils/                    # Utilities
│   │   ├── logger.py
│   │   ├── exceptions.py
│   │   ├── json_logger.py
│   │   └── template_registry.py
│   ├── validation/               # Multi-layer validation (v1.1 Production Ready)
│   │   ├── stationary_bootstrap.py    # 📊 Stationary bootstrap (Politis & Romano 1994)
│   │   ├── dynamic_threshold.py       # 🎯 Taiwan market benchmark thresholds (0.8)
│   │   ├── integration.py             # 🔗 Bonferroni & Bootstrap integrators
│   │   ├── returns_extraction.py      # 📈 Direct returns extraction (no synthesis)
│   │   ├── data_split.py              # Train/Val/Test split
│   │   ├── walk_forward.py            # Walk-forward analysis
│   │   ├── bootstrap.py               # Bootstrap CI (legacy)
│   │   ├── baseline.py                # Baseline comparison
│   │   ├── multiple_comparison.py     # Bonferroni correction
│   │   ├── preservation_validator.py
│   │   ├── metric_validator.py
│   │   └── template_validator.py
│   ├── constants.py              # System constants
│   ├── failure_tracker.py        # Failure pattern tracking
│   └── liquidity_calculator.py   # Liquidity analysis
│
├── tests/                        # Test suite (134 Python files, 926 tests)
│   ├── backtest/
│   ├── config/
│   ├── data/
│   ├── evolution/
│   ├── factor_graph/
│   ├── factor_library/
│   ├── feedback/
│   ├── generators/
│   ├── innovation/
│   ├── integration/              # End-to-end tests
│   │   ├── phase0_test_harness.py
│   │   ├── phase1_test_harness.py
│   │   └── extended_test_harness.py
│   ├── monitoring/
│   ├── mutation/
│   ├── performance/
│   ├── population/
│   ├── recovery/
│   ├── templates/
│   ├── tier1/
│   ├── utils/
│   └── validation/
│
├── artifacts/                    # Runtime artifacts
│   ├── data/                     # JSON data files
│   │   ├── failure_patterns.json
│   │   ├── innovations.jsonl
│   │   └── template_analytics.json
│   └── working/                  # Working modules
│       └── modules/
│           ├── autonomous_loop.py
│           ├── claude_code_strategy_generator.py
│           ├── history.py
│           ├── iteration_engine.py
│           └── poc_claude_test.py
│
├── config/                       # Configuration files
│   ├── learning_system.yaml      # Learning system config
│   ├── 50gen_three_tier_validation.yaml
│   └── grafana_dashboard.json
│
├── docs/                         # Documentation
│   ├── architecture/             # Architecture documentation
│   │   ├── FEEDBACK_SYSTEM.md
│   │   ├── TEMPLATE_SYSTEM.md
│   │   └── ...
│   ├── API_CHANGELOG.md
│   ├── LEARNING_SYSTEM_API.md
│   ├── MONITORING.md
│   ├── TROUBLESHOOTING.md
│   └── YAML_CONFIGURATION_GUIDE.md
│
├── examples/                     # Usage examples
│   ├── ast_mutation_examples.py
│   ├── factor_registry_usage.py
│   ├── logging_integration_example.py
│   └── yaml_strategies/
│
├── scripts/                      # Utility scripts
│   ├── analyze_metrics.py
│   ├── run_50gen_three_tier_validation.py
│   ├── test_baseline_metrics.py
│   └── validate_momentum_strategy.py
│
├── data/                         # Data cache (ignored by git)
│   └── [cached Finlab API responses]
│
├── logs/                         # Application logs (ignored by git)
├── checkpoints/                  # Iteration checkpoints (ignored by git)
├── hall_of_fame/                 # Champion strategies (JSON)
│
├── .env                          # Environment variables (ignored by git)
├── .gitignore
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
└── README.md                     # Project overview
```

### Key Directory Purposes

**Core System** (`src/`):
- **analysis/**: Performance analysis and reporting
- **backtest/**: Backtesting metrics extraction
- **data/**: Finlab API integration, caching, freshness checking
- **templates/**: 4 strategy templates with 80%+ success rates

**🤖 LLM Innovation System** (`src/innovation/`) ⭐ **CORE CAPABILITY - Intelligence Source**:
- **innovation_engine.py**: Orchestrates LLM-driven strategy generation (20% innovation rate)
- **llm_provider.py**: Multi-provider abstraction (OpenRouter, Gemini, OpenAI)
- **prompt_builder.py**: Context-aware prompts (champion data, feedback, failure patterns)
- **security_validator.py**: Safety checks (no file I/O, limited imports, sandbox exec)
- **validators/**: 7-layer validation (Syntax → Semantic → Security → Backtestability → Metrics → Multi-Objective → Baseline)
- **Status**: ✅ Fully implemented (Phase 2-3, ~5000+ lines), ⏳ Activation pending

**⚙️ Autonomous Learning Loop** (`src/learning/`) ⭐ **EXECUTION ENGINE - Orchestration Layer**:
Phase 3-6 implementation (4,200 lines, 7 modules) + **UnifiedLoop & Template Mode** (2025-11-24) - The system's execution backbone

**UnifiedLoop & Template Mode** ✅ **Production Ready** (2025-11-24):
- **unified_loop.py** (450 lines, A grade):
  - **Facade Pattern**: Wraps LearningLoop complexity, provides unified API
  - **Template Mode Support**: `template_mode=True` activates TemplateIterationExecutor
  - **Strategy Pattern**: Switches between StandardIterationExecutor and TemplateIterationExecutor
  - **Backward Compatible**: Maintains AutonomousLoop-compatible API
  - **100% Success Rate**: 20/20 iterations in smoke test (2025-11-24)

- **template_iteration_executor.py** (417 lines):
  - **10-Step Template Execution Flow**: Parameter generation → Template execution → Metrics classification
  - **Bug #5 Complete Fix** (2025-11-24):
    - Bug #5a: Call `template.generate_strategy(params)` not `generate_code(params)`
    - Bug #5b: Use `StrategyMetrics.from_dict()` instead of `metrics_extractor.extract()`
    - Bug #5c: Build execution_result with correct structure for SuccessClassifier
  - **Direct Execution**: Templates execute via `generate_strategy()` returning `(report, metrics_dict)`
  - **No Code Generation**: Unlike LLM mode, no code string involved
  - **Learning Integration**: Full feedback, champion tracking, history management

**Core Orchestration**:
- **learning_loop.py** (372 lines):
  - Main orchestrator managing 10-step autonomous iteration process
  - LLM/Factor Graph decision logic (20/80 innovation split)
  - Signal handling (SIGINT/SIGTERM) for graceful shutdown
  - Integration point: Calls InnovationEngine for LLM innovation (Step 3)
  - **Used by UnifiedLoop**: Delegates execution to LearningLoop in both modes

- **iteration_executor.py** (519 lines):
  - Implements complete 10-step iteration workflow:
    - Steps 1-2: Load history → Generate feedback
    - **Step 3**: Decide LLM (20%) or Factor Graph (80%) innovation
    - Steps 4-7: Backtest execution → Metrics extraction → Success classification
    - Step 8: Champion update logic with validation
    - Steps 9-10: Create iteration record → Save to history
  - Manages execution flow without business logic (pure orchestration)

**State Management**:
- **champion_tracker.py** (1,138 lines):
  - Tracks best-performing strategy across iterations
  - Performance history analysis and staleness detection (>7 days without improvement)
  - Champion update criteria validation (Sharpe improvement, success threshold)
  - Provides champion data to InnovationEngine for context-aware generation

- **iteration_history.py** (651 lines):
  - JSONL-based persistence for complete iteration records
  - Efficient incremental appends (no full file rewrites)
  - Query capabilities: Recent iterations, successful strategies, failure patterns
  - Used by FeedbackGenerator to extract learning patterns

**LLM Integration**:
- **feedback_generator.py** (408 lines):
  - Analyzes iteration history to identify success/failure patterns
  - Generates actionable feedback for next LLM generation
  - Pattern extraction: What worked, what failed, why
  - Context provider for InnovationEngine's PromptBuilder

- **llm_client.py** (420 lines):
  - Multi-provider abstraction (OpenRouter/Gemini/OpenAI)
  - Structured YAML response parsing and validation
  - Auto-retry logic and error handling
  - Rate limiting and cost tracking
  - Used by InnovationEngine for actual LLM API calls

**Configuration**:
- **learning_config.py** (457 lines):
  - 21-parameter configuration management (YAML-based)
  - Environment variable override support (`${VAR:default}` syntax)
  - Validation and default value handling
  - Critical config: `llm.enabled`, `innovation_rate`, `max_iterations`

- **config_manager.py**:
  - YAML file loading and parsing
  - Configuration validation and type checking

**Implementation Quality**:
- ✅ Code Quality: A (97/100) - Production-ready
- ✅ Test Coverage: 88% (148+ tests: unit, integration, E2E scenarios)
- ✅ Architecture: A+ (100/100) - Clean separation of concerns
- ✅ Complexity Reduction: 86.7% (autonomous_loop.py: 2,807 → 372 lines)

**Status**: ⚙️ **Learning Loop ENGINE fully operational, orchestrates LLM CORE activation**

**Legacy Learning System** (`src/feedback/`, `src/repository/`):
- **feedback/**: Template recommendation, rationale generation
- **repository/**: Hall of Fame, iteration history, pattern search
- **monitoring/**: Variance tracking, convergence detection

**Validation** (`src/validation/`):
- **data_split.py**: Train/Val/Test periods (2018-2020/2021-2022/2023-2024)
- **walk_forward.py**: Rolling window validation (252-day windows)
- **bootstrap.py**: Statistical significance (1000 iterations)
- **baseline.py**: Buy-and-Hold 0050, Equal-Weight, Risk Parity

**Factor System** (`src/factor_graph/`, `src/factor_library/`) ✅ **Phase 2 Matrix-Native (2025-11-01)**:
- **factor_graph/**: Strategy composition framework with FinLabDataFrame matrix-native architecture
  - `finlab_dataframe.py`: Matrix container (Dates×Symbols), lazy loading, type safety, immutability
  - Resolves Phase 1 DataFrame vs Matrix incompatibility (ValueError on 2D assignment)
  - 170 tests passing, 6/6 E2E with real FinLab API (2025-11-11)
- **factor_library/**: 13 reusable factors (Momentum, Value, Quality, Risk, Entry, Exit)
  - All factors refactored to matrix-native operations (`container.get_matrix()`, `container.add_matrix()`)

**Configuration** (`config/`):
- **learning_system.yaml**: Anti-churn, multi-objective validation, exit mutation

**Testing** (`tests/`):
- 926 tests across 23 modules
- Unit tests: Component-level validation
- Integration tests: End-to-end workflows
- Performance tests: Benchmark critical paths

## Naming Conventions

### Files
- **Modules**: `snake_case.py` (e.g., `iteration_engine.py`, `hall_of_fame.py`)
- **Templates**: `{name}_template.py` (e.g., `turtle_template.py`, `mastiff_template.py`)
- **Tests**: `test_{module}.py` (e.g., `test_data_split.py`, `test_template_validator.py`)
- **Scripts**: `{action}_{target}.py` (e.g., `run_50gen_three_tier_validation.py`)
- **Examples**: `{concept}_examples.py` or `{concept}_usage.py`

### Code
- **Classes/Types**: `PascalCase` (e.g., `TurtleTemplate`, `HallOfFameRepository`, `DataCache`)
- **Functions/Methods**: `snake_case` (e.g., `recommend_template()`, `validate_strategy()`, `get_champion()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_ITERATIONS`, `MIN_SHARPE_THRESHOLD`, `DEFAULT_PARAMS`)
- **Private members**: `_leading_underscore` (e.g., `_extract_params()`, `_validate_internal()`)
- **Variables**: `snake_case` (e.g., `sharpe_ratio`, `iteration_num`, `champion_strategy`)

### Spec Names
- **Format**: `kebab-case` (e.g., `learning-system-enhancement`, `docker-sandbox-security`)
- **Branches**: `feature/{spec-name}`, `bugfix/{issue}`, `docs/{update}`
- **Files**: `requirements.md`, `design.md`, `tasks.md`

## Import Patterns

### Import Order (isort + PEP 8)
1. **Standard library**: `import json`, `import re`, `from typing import Dict`
2. **Third-party packages**: `import pandas as pd`, `import numpy as np`, `from finlab import data`
3. **Local application**: `from src.templates import TurtleTemplate`, `from src.repository import HallOfFameRepository`
4. **Relative imports**: `from .base_template import BaseTemplate` (within same package only)

**Example**:
```python
# Standard library
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

# Third-party packages
import pandas as pd
import numpy as np
from finlab import data

# Local application
from src.templates import TurtleTemplate
from src.repository import HallOfFameRepository
from src.validation import TemplateValidator

# Relative imports (within templates/ package)
from .base_template import BaseTemplate
from .data_cache import DataCache
```

### Module/Package Organization
- **Absolute imports**: Preferred for cross-package imports
  ```python
  from src.feedback import TemplateFeedbackIntegrator  # ✅ Preferred
  from ..feedback import TemplateFeedbackIntegrator    # ❌ Avoid
  ```
- **Relative imports**: Only within same package
  ```python
  # In src/templates/turtle_template.py
  from .base_template import BaseTemplate  # ✅ OK (same package)
  from ..repository import HallOfFameRepository  # ❌ Use absolute instead
  ```
- **Package exports**: Use `__init__.py` to expose public API
  ```python
  # src/templates/__init__.py
  __all__ = ['BaseTemplate', 'TurtleTemplate', 'MastiffTemplate', ...]
  ```

## Code Structure Patterns

### Module/File Organization
Standard order within Python files:

1. **Shebang + Encoding** (if needed)
   ```python
   #!/usr/bin/env python3
   # -*- coding: utf-8 -*-
   ```

2. **Module docstring**
   ```python
   """
   Module description (Google-style).

   Detailed explanation of module purpose, usage, and key components.
   """
   ```

3. **Imports** (isort order)

4. **Constants**
   ```python
   MAX_ITERATIONS = 200
   MIN_SHARPE_THRESHOLD = 0.5
   DEFAULT_PARAMS = {...}
   ```

5. **Type definitions** (if applicable)
   ```python
   from typing import TypedDict

   class ChampionData(TypedDict):
       code: str
       metrics: Dict[str, float]
       iteration: int
   ```

6. **Main classes**
   ```python
   class TurtleTemplate(BaseTemplate):
       """Template class with full docstring."""

       def __init__(self):
           ...

       def public_method(self):
           ...

       def _private_method(self):
           ...
   ```

7. **Helper functions**
   ```python
   def extract_strategy_params(code: str) -> Dict[str, Any]:
       """Standalone helper function."""
       ...
   ```

8. **Main execution** (if script)
   ```python
   if __name__ == "__main__":
       main()
   ```

### Function/Method Organization

**Principles**:
1. **Input validation first**: Check preconditions, validate types
2. **Core logic in middle**: Main algorithm/business logic
3. **Error handling throughout**: Try/except with specific exceptions
4. **Clear return points**: Single return preferred, multiple if clearer

**Example**:
```python
def recommend_template(
    self,
    current_metrics: Optional[Dict[str, Any]] = None,
    iteration: int = 1,
    validation_result: Any = None
) -> TemplateRecommendation:
    """
    Generate template recommendation.

    Args:
        current_metrics: Performance metrics (sharpe_ratio, max_drawdown)
        iteration: Current iteration number
        validation_result: ValidationResult object

    Returns:
        TemplateRecommendation with template_name, rationale, params

    Raises:
        ValueError: If iteration < 1
    """
    # 1. Input validation
    if iteration < 1:
        raise ValueError(f"Iteration must be >= 1, got {iteration}")

    # 2. Core logic
    sharpe = current_metrics.get('sharpe_ratio', 0.0) if current_metrics else 0.0

    # Check exploration mode
    if self._should_force_exploration(iteration):
        return self._select_exploration_template(iteration)

    # Performance-based selection
    template_name = self._select_by_performance_tier(sharpe)

    # 3. Enhancement and return
    params = self._enhance_with_champion_params(template_name)
    rationale = self._generate_rationale(template_name, sharpe)

    return TemplateRecommendation(
        template_name=template_name,
        rationale=rationale,
        suggested_params=params
    )
```

### File Organization Principles
1. **One primary class per file**: `TurtleTemplate` in `turtle_template.py`
2. **Related helpers in same file**: Template-specific helpers with template class
3. **Shared utilities in utils/**: Generic helpers in `src/utils/`
4. **Public API at top**: Main class/function before internal helpers
5. **Private details at bottom**: `_private_methods()` after public API

## Code Organization Principles

### 1. **Single Responsibility**
Each file/class/function has one clear, well-defined purpose.

**Good Examples**:
- `turtle_template.py`: Only TurtleTemplate implementation
- `hall_of_fame.py`: Only champion strategy storage
- `variance_monitor.py`: Only convergence monitoring

**Anti-patterns to avoid**:
- Mixed concerns (e.g., template + validation in same class)
- God classes (e.g., single class doing generation + backtest + analysis)

### 2. **Modularity**
Code organized into reusable, composable modules.

**Examples**:
- Factor library: 13 independent factors composable into strategies
- Validation components: 5 validators usable individually or together
- Templates: 4 templates with shared base class

### 3. **Testability**
Structure code to facilitate testing.

**Patterns**:
- Dependency injection: Pass dependencies via constructor
  ```python
  def __init__(self, repository: HallOfFameRepository):
      self.repository = repository  # ✅ Testable (can mock)
  ```
- Pure functions: Input → Output, no side effects
  ```python
  def calculate_sharpe(returns: pd.Series) -> float:
      return returns.mean() / returns.std()  # ✅ Pure function
  ```
- Clear interfaces: Type hints, docstrings, explicit contracts

### 4. **Consistency**
Follow established patterns throughout codebase.

**Established Patterns**:
- Repository pattern: `HallOfFameRepository`, `IterationHistory`
- Manager suffix: `AntiChurnManager`, `RollbackManager`
- Validator suffix: `TemplateValidator`, `PreservationValidator`
- Generator suffix: `RationaleGenerator`

### 5. **避免過度工程化** (Project Principle)
Keep implementation simple and pragmatic.

**Applications**:
- JSON persistence instead of PostgreSQL (sufficient for personal use)
- Regex parameter extraction instead of AST (80/20 solution, 90% accuracy)
- CLI-based instead of web dashboard (faster development)

## Module Boundaries

### Core vs Plugins
- **Core**: src/templates/, src/factor_graph/, src/validation/
- **Plugins**: Custom templates can be added (future extensibility)
- **Boundary**: BaseTemplate interface defines plugin contract

### Public API vs Internal
- **Public API**: Exported via `__all__` in `__init__.py`
  ```python
  # src/templates/__init__.py
  __all__ = ['BaseTemplate', 'TurtleTemplate', 'MastiffTemplate', ...]
  ```
- **Internal**: `_private_methods()`, `_helper_functions()`
- **Boundary**: Leading underscore convention

### Stable vs Experimental
- **Stable**: src/templates/, src/validation/, src/repository/ (tested, documented)
- **Experimental**: src/innovation/, new mutation operators (subject to change)
- **Boundary**: Documented in module docstrings, STATUS.md files

### Dependencies Direction
**Allowed dependencies** (acyclic, layered):

**Three-Layer Architecture**:
```
┌───────────────────────────────────────────┐
│ ⚙️ Learning Loop (EXECUTION ENGINE)      │
│ src/learning/learning_loop.py             │
│ - Orchestrates 10-step iteration process  │
│ - Manages LLM/Factor Graph decision       │
└────────┬──────────────────────────────────┘
         │
         │ 20% innovation_rate (Step 3)
         ▼
┌───────────────────────────────────────────┐
│  🤖 LLM Innovation (CORE - Intelligence)  │
│  src/innovation/innovation_engine.py      │
│  - Structural strategy generation         │
│  - Breaks framework limitations           │
└────────┬──────────────────────────────────┘
         │
         ├──────────────┐
         │              │
    ┌────▼────┐    ┌───▼────────┐
    │LLM      │    │YAML        │
    │Provider │    │Validator   │
    └────┬────┘    └───┬────────┘
         │             │
         └──────┬──────┘
                │
     ┌──────────┼───────────┬──────────────┐
     │          │           │              │
┌────▼────┐ ┌──▼────┐  ┌──▼──────┐  ┌───▼──────────────────────────┐
│Templates│ │Factor │  │Feedback │  │📊 Validation (QUALITY GATE)  │
│         │ │ Graph │  │         │  │src/validation/                │
└────┬────┘ └──┬────┘  └────┬────┘  │- Bootstrap confidence         │
     │          │            │       │- Walk-forward analysis        │
     └──────────┴────┬───────┴───────┤- Baseline comparison          │
                     │               └───┬──────────────────────────┘
                ┌────▼─────┐             │
                │Repository│             │
                │          │             │
                └────┬─────┘             │
                     │                   │
                     └──────┬────────────┘
                            │
                       ┌────▼────┐
                       │Backtest │
                       │ (finlab)│
                       └────┬────┘
                            │
                       ┌────▼────┐
                       │  Data   │
                       └─────────┘
```

**Key Relationships**:
- **Learning Loop** (⚙️ ENGINE) orchestrates entire iteration process
- **LLM Innovation** (🤖 CORE) provides structural intelligence (20% rate)
- **Validation** (📊 GATE) ensures quality through statistical checks
- **Factor Graph** serves as 80% fallback when LLM unavailable

**Forbidden dependencies** (circular):
- ❌ Repository → Templates (would create cycle)
- ❌ Data → Validation (too high-level)
- ❌ Backtest → Feedback (layers crossed)

## Code Size Guidelines

### File Size
- **Target**: <500 lines per file
- **Maximum**: 1000 lines (consider splitting)
- **Exceptions**: Large validation modules (1200-1700 lines acceptable if cohesive)

**Current Stats**:
- Average file size: ~300 lines
- Largest files: validation modules (1200-1700 lines)
- Smallest files: constants, simple utilities (<100 lines)

### Function/Method Size
- **Target**: <50 lines per function
- **Maximum**: 100 lines (consider extracting helpers)
- **Ideal**: 10-30 lines (single responsibility)

### Class Complexity
- **Target**: <10 public methods per class
- **Maximum**: 20 methods (consider splitting responsibilities)
- **Private methods**: No strict limit (implementation details)

### Nesting Depth
- **Target**: ≤2 levels of nesting
- **Maximum**: 3 levels (consider early returns or extraction)

**Example** (good):
```python
def process_iteration(iteration: int) -> Result:
    if not is_valid(iteration):  # Level 1
        return error_result

    for strategy in strategies:  # Level 1
        if meets_criteria(strategy):  # Level 2
            results.append(process(strategy))

    return results
```

**Example** (avoid):
```python
def process_iteration(iteration: int) -> Result:
    if is_valid(iteration):  # Level 1
        for strategy in strategies:  # Level 2
            if meets_criteria(strategy):  # Level 3
                if passes_validation(strategy):  # Level 4 ❌ Too deep!
                    results.append(process(strategy))
```

## Dashboard/Monitoring Structure

### Current Structure (CLI-based)
```
# No dashboard yet - CLI logging only
artifacts/working/modules/
├── autonomous_loop.py         # Main iteration loop
├── iteration_engine.py        # Execution engine
└── history.py                 # Iteration history tracking
```

**Monitoring**:
- Structured JSON logging (`src/utils/json_logger.py`)
- Rich terminal output (`rich` library)
- Progress bars (`tqdm`)
- Metrics export (JSON, Prometheus)

### Future Dashboard Structure (Planned)
```
src/
└── dashboard/                 # Self-contained subsystem
    ├── server/                # FastAPI backend
    │   ├── api/
    │   ├── services/
    │   └── main.py
    ├── client/                # React frontend (or Streamlit)
    │   ├── components/
    │   ├── pages/
    │   └── App.tsx
    ├── shared/                # Shared types/utilities
    │   └── types.ts
    └── public/                # Static assets
```

### Separation of Concerns
- **Dashboard isolated from core**: Can be disabled without affecting autonomous loop
- **Own CLI entry point**: `python -m src.dashboard` (independent operation)
- **Minimal dependencies**: Only depends on repository layer (read-only access)
- **API-first design**: REST API can be used by other tools

## Documentation Standards

### Code Documentation
- **All public APIs**: Must have Google-style docstrings
  ```python
  def recommend_template(
      self,
      current_metrics: Optional[Dict[str, Any]] = None
  ) -> TemplateRecommendation:
      """
      Generate template recommendation based on performance metrics.

      Args:
          current_metrics: Dictionary with 'sharpe_ratio', 'max_drawdown', etc.

      Returns:
          TemplateRecommendation with template_name, rationale, params

      Raises:
          ValueError: If current_metrics is invalid

      Example:
          >>> recommendation = integrator.recommend_template({'sharpe_ratio': 0.8})
          >>> print(recommendation.template_name)
          'TurtleTemplate'
      """
  ```

- **Complex logic**: Inline comments explaining "why", not "what"
  ```python
  # Use hybrid threshold to prevent stagnation at high Sharpe (>2.0)
  # Relative threshold becomes too strict (5% of 2.5 = 2.625 impossible)
  relative_met = new_sharpe >= old_sharpe * (1 + relative_threshold)
  absolute_met = new_sharpe >= old_sharpe + additive_threshold
  ```

- **Module-level**: Comprehensive docstring at file top
  ```python
  """
  Template Feedback Integration System
  =====================================

  Intelligent template recommendation and feedback for autonomous learning.

  Key Components:
      - TemplateFeedbackIntegrator: Performance-based template selection
      - RationaleGenerator: Natural language explanations
      - TemplateAnalytics: Usage tracking and statistics

  Usage:
      from src.feedback import TemplateFeedbackIntegrator

      integrator = TemplateFeedbackIntegrator()
      recommendation = integrator.recommend_template(metrics, iteration=1)
  """
  ```

### Architecture Documentation
- **Major modules**: README.md in subdirectory
- **System architecture**: `docs/architecture/` (FEEDBACK_SYSTEM.md, TEMPLATE_SYSTEM.md, etc.)
- **API documentation**: `docs/*_API.md` (LEARNING_SYSTEM_API.md, etc.)
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`

### Spec Documentation
- **Requirements**: `.spec-workflow/specs/{spec}/requirements.md`
- **Design**: `.spec-workflow/specs/{spec}/design.md`
- **Tasks**: `.spec-workflow/specs/{spec}/tasks.md`
- **Status**: `.spec-workflow/specs/{spec}/STATUS.md`

### Language
- **Code comments**: English
- **Documentation**: 中英雙語 (bilingual Chinese/English)
- **README**: Comprehensive sections in both languages
- **Inline comments**: English preferred, Chinese acceptable for complex domain logic

## Special Conventions

### Iteration Numbering
- **0-indexed internally**: `iteration_num = 0` is first iteration
- **1-indexed in logs**: Display as "Iteration 1" for user clarity
- **Conversion**: `display_num = iteration_num + 1`

### Checkpoint Naming
- **Format**: `{prefix}_checkpoints/`, `{prefix}_checkpoint_{iteration}.json`
- **Examples**: `baseline_checkpoints/`, `validation_checkpoints/`, `phase1_checkpoints/`

### Metrics Naming
- **snake_case**: `sharpe_ratio`, `max_drawdown`, `calmar_ratio`
- **Negative values**: Drawdowns are negative (e.g., `-0.15` for 15% drawdown)
- **Percentages**: Use decimals (0.05 = 5%), not integers (5)

### Template Names
- **Suffix**: Always end with "Template" (e.g., `TurtleTemplate`, not `Turtle`)
- **PascalCase**: Class names in code
- **Title Case**: Display names ("Turtle Template")

### File Timestamps
- **Format**: ISO 8601 (`2025-10-25T14:53:26.979Z`)
- **Timezone**: UTC for consistency
- **Filenames**: `YYYY-MM-DD` format if needed (e.g., `backup_2025-10-25.json`)

---

**Document Version**: 1.2
**Last Updated**: 2025-11-24
**Status**: Production
**Maintainer**: Personal Project
**Latest Changes**:
- **Template Mode Architecture Complete** (2025-11-24):
  - Added `unified_loop.py` (Facade Pattern, 450 lines, A grade)
  - Added `template_iteration_executor.py` (Strategy Pattern, 417 lines, 100% success)
  - Added `unified_config.py` for Template Mode configuration
  - Updated `base_template.py` interface documentation (generate_strategy not generate_code)
  - Updated `momentum_template.py` production status (100% success rate)
- **Bug #5 Fix Documentation**:
  - Bug #5a: generate_code() → generate_strategy()
  - Bug #5b: metrics_extractor.extract() → StrategyMetrics.from_dict()
  - Bug #5c: execution_result structure compatibility with SuccessClassifier
- Added src/learning/ module documentation (4,200 lines, 7 modules) - Missing EXECUTION ENGINE
- Updated Three-Layer Architecture diagram: Learning Loop → LLM Innovation → Validation
- Clarified component relationships: ENGINE (⚙️) orchestrates CORE (🤖) with GATE (📊) validation
- Marked legacy feedback system components for clarity
