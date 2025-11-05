# Project Structure Steering Document

## Directory Organization

### Root Structure
```
/finlab/
├── src/                          # Source code (layered architecture)
├── .claude/                      # Claude Code configuration and specs
├── tests/                        # Test suites (mirrors src/ structure)
├── docs/                         # Documentation and guides
├── .finlab_cache/                # L2 disk cache (Parquet files)
├── *.json                        # Persistent data files
├── generated_strategy_iter*.py   # Generated strategy artifacts
├── README.md                     # Quick start and overview
├── STATUS.md                     # Current status and metrics
└── requirements.txt              # Python dependencies
```

### Source Code Organization (`src/`)

**Layered Architecture**: Domain-driven organization with clear separation of concerns

```
src/
├── __init__.py                   # Package initialization
├── constants.py                  # System-wide constants and configuration
├── failure_tracker.py            # Failure pattern recognition across iterations
├── liquidity_calculator.py       # Market liquidity analysis (1-4 week turnover)
│
├── data/                         # Data access layer (L2 disk cache)
│   ├── __init__.py               # DataManager: unified data access interface
│   ├── cache.py                  # Disk cache: persistent Parquet storage
│   ├── downloader.py             # Finlab API downloader with freshness checks
│   └── freshness.py              # FreshnessChecker: timestamp-based validation
│
├── validation/                   # Multi-stage validation system
│   ├── data_validator.py         # Dataset key verification (50 curated datasets)
│   ├── code_validator.py         # AST + Data + Backtest validation orchestrator
│   ├── ast_validator.py          # AST-based syntax/semantic validation
│   └── sensitivity_tester.py     # Optional parameter sensitivity testing (50-75 min)
│
├── repository/                   # Strategy and pattern storage
│   ├── hall_of_fame.py           # Three-tier strategy repository (Champions/Contenders/Archive)
│   ├── novelty_scorer.py         # Vector-based duplicate detection with caching
│   └── genome.py                 # StrategyGenome data structure
│
├── feedback/                     # Learning and attribution system
│   ├── performance_attributor.py # Parameter comparison and success pattern extraction
│   ├── nl_summary.py             # Natural language performance explanations
│   └── feedback_builder.py       # Structured feedback generation for LLM
│
├── templates/                    # Template system and memory cache
│   ├── base_template.py          # BaseTemplate: strategy template abstraction
│   ├── data_cache.py             # L1 memory cache: runtime performance optimization
│   └── template_*.py             # Specific strategy templates (multi-factor, momentum, etc.)
│
├── analysis/                     # Performance analysis and reporting
│   ├── performance_analyzer.py   # Backtest result analysis and metrics calculation
│   └── report_generator.py       # Performance report generation
│
├── backtest/                     # Backtesting infrastructure
│   ├── engine.py                 # Finlab backtesting engine wrapper
│   └── metrics.py                # Performance metric calculations (Sharpe, drawdown)
│
├── storage/                      # Data persistence utilities
│   ├── history.py                # IterationHistory: iteration results tracking
│   └── serializer.py             # JSON serialization helpers
│
├── ui/                           # User interface (future)
│   └── dashboard.py              # Web dashboard (planned)
│
└── utils/                        # Shared utilities
    ├── logging.py                # Logging configuration
    └── helpers.py                # Common helper functions
```

### Spec Organization (`.claude/specs/`)

**Spec-Driven Development**: Requirements → Design → Tasks → Implementation

```
.claude/specs/
├── learning-system-enhancement/  # Main learning system spec (MVP complete)
│   ├── requirements.md            # User stories and acceptance criteria
│   ├── design.md                  # Architecture and implementation design
│   └── tasks.md                   # Task breakdown with POST-MVP section
│
├── autonomous-iteration-engine/   # Iteration loop optimization
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
│
├── template-system-phase2/        # Template library and Hall of Fame integration
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
│
├── liquidity-monitoring-enhancements/  # Market liquidity analysis
│   └── tasks.md
│
└── system-fix-validation-enhancement/  # Validation system improvements
    └── tasks.md
```

### Test Organization (`tests/`)

**Mirror Structure**: Tests mirror `src/` directory organization

```
tests/
├── test_data.py                  # Data layer tests (cache, downloader, freshness)
├── test_validation.py            # Validation system tests (AST, data, code)
├── test_repository.py            # Repository tests (Hall of Fame, novelty scorer)
├── test_feedback.py              # Feedback system tests (attribution, patterns)
├── test_integration.py           # Integration tests (end-to-end workflows)
└── feedback/                     # Feedback system test fixtures
    └── test_*.py                 # Individual feedback component tests
```

## File Naming Conventions

### Python Files
- **Modules**: `snake_case.py` (e.g., `data_validator.py`, `novelty_scorer.py`)
- **Classes**: `PascalCase` (e.g., `DataValidator`, `NoveltyScorer`, `HallOfFame`)
- **Functions**: `snake_case()` (e.g., `extract_parameters()`, `calculate_novelty_score()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DUPLICATE_THRESHOLD`, `KNOWN_DATASETS`)

### Data Files
- **JSON Persistence**: `snake_case.json` (e.g., `champion_strategy.json`, `iteration_history.json`)
- **Generated Strategies**: `generated_strategy_iter{N}.py` (e.g., `generated_strategy_iter0.py`)
- **Grid Search Results**: `{strategy_name}_grid_search_{type}_{timestamp}.json`
- **Backup Files**: `{original_name}_backup_{timestamp}.{ext}`

### Documentation
- **Markdown**: `UPPER_SNAKE_CASE.md` for project-level, `PascalCase.md` for phase-level
  - Project: `README.md`, `STATUS.md`, `CHANGELOG.md`
  - Spec: `requirements.md`, `design.md`, `tasks.md`
  - Summary: `{TOPIC}_SUMMARY.md`, `{PHASE}_COMPLETE.md`

## Code Organization Patterns

### Module Structure Pattern
```python
"""
Module docstring: Purpose and key features
==========================================

Detailed description of module functionality.

Examples:
    >>> from module import Class
    >>> obj = Class()
"""

# Standard library imports
import json
from typing import Dict, List, Optional

# Third-party imports
import pandas as pd
import numpy as np

# Local imports
from src.constants import THRESHOLD
from src.utils.helpers import helper_function

# Constants
MODULE_CONSTANT = "value"

# Classes
class MainClass:
    """Class docstring with usage examples."""

    def __init__(self):
        """Initialize with clear parameter documentation."""
        pass

    def public_method(self) -> ReturnType:
        """Public method with type hints and docstring."""
        pass

    def _private_method(self) -> ReturnType:
        """Private method for internal use only."""
        pass

# Module-level functions
def utility_function() -> ReturnType:
    """Utility function with clear purpose."""
    pass
```

### Class Organization Pattern
```python
class ClassName:
    """
    Class purpose and usage.

    Attributes:
        attr1: Description of attribute
        attr2: Description of attribute

    Example:
        >>> obj = ClassName()
        >>> obj.method()
    """

    # Class-level constants
    CLASS_CONSTANT = "value"

    def __init__(self, param: Type):
        """Initialize instance."""
        # Public attributes
        self.public_attr = param

        # Private attributes
        self._private_attr = self._initialize()

    # Public methods (alphabetical order)
    def public_method(self) -> ReturnType:
        """Public interface method."""
        pass

    # Private methods (alphabetical order)
    def _private_method(self) -> ReturnType:
        """Internal helper method."""
        pass

    # Static methods
    @staticmethod
    def static_helper() -> ReturnType:
        """Utility method without instance access."""
        pass

    # Class methods
    @classmethod
    def from_dict(cls, data: Dict) -> 'ClassName':
        """Alternative constructor."""
        pass
```

### Function Organization Pattern
```python
def function_name(
    param1: Type,
    param2: Type,
    optional_param: Optional[Type] = None
) -> ReturnType:
    """
    Function purpose and behavior.

    Args:
        param1: Description of param1
        param2: Description of param2
        optional_param: Description of optional parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When and why this is raised
        TypeError: When and why this is raised

    Example:
        >>> result = function_name("value1", "value2")
        >>> print(result)
    """
    # Input validation
    if not param1:
        raise ValueError("param1 cannot be empty")

    # Main logic
    result = process(param1, param2)

    # Optional parameter handling
    if optional_param:
        result = enhance(result, optional_param)

    return result
```

## Architecture Patterns

### 1. Two-Tier Cache Pattern (L1/L2)
```python
# L1: Memory cache for runtime performance
from src.templates.data_cache import DataCache
cache = DataCache.get_instance()
data = cache.get('price:收盤價')  # Lazy loading with statistics

# L2: Disk cache for persistence
from src.data import DataManager
manager = DataManager()
data = manager.get_data('price:收盤價')  # Load from disk or download
```

### 2. Repository Pattern (Hall of Fame)
```python
# Three-tier strategy storage
from src.repository.hall_of_fame import HallOfFame

hall = HallOfFame()
hall.add_strategy(genome, metrics)  # Automatic tier assignment
champions = hall.get_champions()    # Sharpe > 1.5
contenders = hall.get_contenders()  # 1.0 < Sharpe < 1.5
```

### 3. Validation Pipeline Pattern
```python
# Multi-stage validation with early exit
from src.validation.code_validator import CodeValidator

validator = CodeValidator()
result = validator.validate(code)  # AST → Data → Backtest

if not result.is_valid:
    print(result.error_message)
    # Early exit without executing code
```

### 4. Attribution Pattern (Performance Analysis)
```python
# Compare strategies and extract insights
from src.feedback.performance_attributor import PerformanceAttributor

attributor = PerformanceAttributor()
changes = attributor.compare_strategies(champion_code, new_code)
patterns = attributor.extract_success_patterns(champion_params)
feedback = attributor.generate_attribution_feedback(changes, metrics)
```

### 5. Novelty Detection Pattern (Duplicate Prevention)
```python
# Vector-based similarity with caching
from src.repository.novelty_scorer import NoveltyScorer

scorer = NoveltyScorer()
# Pre-compute vectors once
existing_vectors = scorer.extract_vectors_batch(existing_codes)
# Fast comparison with cached vectors
novelty_score, info = scorer.calculate_novelty_score_with_cache(
    new_code, existing_vectors
)
if scorer.is_duplicate(novelty_score):
    print(f"Duplicate detected: {info}")
```

## Import Conventions

### Import Order (PEP 8)
```python
# 1. Standard library imports
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 2. Third-party imports (alphabetical)
import numpy as np
import pandas as pd
from finlab import data

# 3. Local imports (absolute, organized by layer)
from src.constants import THRESHOLD
from src.data import DataManager
from src.repository.hall_of_fame import HallOfFame
from src.validation.code_validator import CodeValidator
```

### Import Styles
- **Absolute imports**: Always use `from src.module import Class`
- **No star imports**: Avoid `from module import *`
- **Explicit imports**: Prefer `from module import Class` over `import module`
- **Type hints**: Import types from `typing` module

## Configuration Management

### Environment Variables
```bash
# OpenRouter API key
export OPENROUTER_API_KEY='sk-or-v1-...'

# Finlab API token
export FINLAB_API_TOKEN='...'

# Google API key (for Gemini)
export GOOGLE_API_KEY='AIzaSy...'
```

### Constants (`src/constants.py`)
```python
# System-wide constants
DEFAULT_LIQUIDITY_THRESHOLD = 100_000_000  # TWD
CHAMPION_UPDATE_THRESHOLD = 1.05           # 5% improvement required
NOVELTY_DUPLICATE_THRESHOLD = 0.2          # Similarity threshold

# File paths
CACHE_DIR = Path('.finlab_cache')
CHAMPION_FILE = Path('champion_strategy.json')
HISTORY_FILE = Path('iteration_history.json')
```

## Error Handling Conventions

### Exception Hierarchy
```python
# Custom exceptions for domain errors
class FinlabError(Exception):
    """Base exception for all finlab errors."""
    pass

class ValidationError(FinlabError):
    """Raised when validation fails."""
    pass

class DataError(FinlabError):
    """Raised when data access fails."""
    pass

class RepositoryError(FinlabError):
    """Raised when repository operation fails."""
    pass
```

### Error Handling Pattern
```python
def validate_strategy(code: str) -> ValidationResult:
    """
    Validate strategy code with comprehensive error handling.

    Returns:
        ValidationResult with success flag and error details

    Note:
        Never raises exceptions - always returns ValidationResult
    """
    try:
        # Validation logic
        ast_result = validate_ast(code)
        if not ast_result.is_valid:
            return ValidationResult(False, ast_result.error)

        data_result = validate_data(code)
        if not data_result.is_valid:
            return ValidationResult(False, data_result.error)

        return ValidationResult(True, None)

    except Exception as e:
        # Graceful degradation
        logger.error(f"Unexpected validation error: {e}")
        return ValidationResult(False, f"Internal error: {str(e)}")
```

## Testing Conventions

### Test File Structure
```python
"""
Test module for {module_name}
================================

Test coverage for {module_name} functionality.
"""

import pytest
from src.module import Class

# Fixtures
@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value"}

# Test classes (one per class being tested)
class TestClassName:
    """Test suite for ClassName."""

    def test_basic_functionality(self):
        """Test basic operation."""
        obj = Class()
        result = obj.method()
        assert result == expected

    def test_edge_case(self):
        """Test edge case handling."""
        obj = Class()
        with pytest.raises(ValueError):
            obj.method(invalid_input)

    def test_integration(self):
        """Test integration with other components."""
        pass

# Module-level tests
def test_utility_function():
    """Test module-level utility function."""
    pass
```

### Test Naming
- **Test files**: `test_{module_name}.py`
- **Test classes**: `Test{ClassName}`
- **Test methods**: `test_{functionality}__{scenario}` or `test_{functionality}`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-11
**Structure Review**: Post-Zen Debug Optimization
**Next Review**: Post-AST Migration (Phase 5)
