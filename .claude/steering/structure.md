# Structure Steering Document

## Project Organization

```
finlab/
├── .claude/                    # Claude Code workspace
│   ├── specs/                 # Specification documents
│   │   └── learning-system-enhancement/
│   │       ├── requirements.md
│   │       ├── design.md
│   │       └── tasks.md
│   └── steering/              # Steering documents (this directory)
│       ├── product.md         # Product vision and features
│       ├── tech.md           # Technology stack and decisions
│       └── structure.md      # File organization (this file)
│
├── src/                       # Source code organized by domain
│   ├── analysis/             # AI-powered strategy analysis
│   │   ├── __init__.py
│   │   ├── claude_client.py  # OpenRouter/Claude API client
│   │   ├── engine.py         # Analysis orchestration
│   │   ├── fallback.py       # Fallback logic when AI unavailable
│   │   ├── generator.py      # Strategy code generation
│   │   ├── learning.py       # Learning system integration
│   │   ├── ranking.py        # Strategy ranking and selection
│   │   └── visualizer.py     # Analysis visualization
│   │
│   ├── backtest/             # Backtesting engine
│   │   ├── __init__.py
│   │   ├── engine.py         # Finlab backtest integration
│   │   ├── metrics.py        # Performance metrics calculation
│   │   ├── sandbox.py        # Code execution sandbox
│   │   ├── validation.py     # Look-ahead bias detection
│   │   └── visualizer.py     # Backtest result visualization
│   │
│   ├── data/                 # Data management
│   │   ├── __init__.py
│   │   ├── cache.py          # Multi-layer caching
│   │   ├── downloader.py     # Finlab API integration
│   │   └── freshness.py      # Data staleness detection
│   │
│   ├── storage/              # Persistence layer
│   │   ├── __init__.py
│   │   ├── backup.py         # Data backup utilities
│   │   └── manager.py        # DuckDB integration
│   │
│   ├── ui/                   # User interface (planned)
│   │   └── __init__.py
│   │
│   ├── utils/                # Shared utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py     # Custom exceptions
│   │   ├── init_db.py        # Database initialization
│   │   └── logger.py         # Logging configuration
│   │
│   ├── constants.py          # System-wide constants
│   └── failure_tracker.py    # Failure pattern tracking
│
├── tests/                    # Test suite
│   ├── analysis/             # Analysis module tests
│   │   ├── test_claude_client.py
│   │   ├── test_engine.py
│   │   ├── test_fallback.py
│   │   ├── test_generator.py
│   │   ├── test_learning.py
│   │   ├── test_ranking.py
│   │   └── test_visualizer.py
│   │
│   ├── backtest/             # Backtest module tests
│   │   └── test_engine.py
│   │
│   ├── storage/              # Storage module tests
│   │   └── test_manager.py
│   │
│   ├── conftest.py           # Pytest fixtures
│   ├── test_data.py          # Data module tests
│   ├── test_evolutionary_prompts.py    # Prompt construction tests (7 tests)
│   ├── test_feedback_generation.py     # Feedback generation tests (4 tests)
│   ├── test_infrastructure.py          # Infrastructure tests
│   ├── test_integration_scenarios.py   # End-to-end tests (5 scenarios)
│   └── test_pattern_extraction.py      # Pattern extraction tests (20 tests)
│
├── config/                   # Configuration files
│   └── settings.py           # System settings
│
├── autonomous_loop.py        # Main autonomous optimization loop
├── performance_attributor.py # Performance attribution engine
├── prompt_builder.py         # LLM prompt construction
├── history.py               # Iteration history tracking
├── sandbox.py               # Code execution sandbox
├── validate_code.py         # Code validation utilities
│
├── README.md                # Project documentation (bilingual)
├── requirements.txt         # Python dependencies
└── .gitignore              # Git ignore rules
```

## File Organization Principles

### 1. **Domain-Driven Structure**
Organize by business domain (analysis, backtest, data) rather than technical layer (models, views, controllers)

**Rationale**:
- Easier to understand "what the system does"
- Natural boundaries for code changes
- Aligns with product features (data infrastructure, backtest engine, learning system)

### 2. **Top-Level Workflow Files**
Core workflow files (autonomous_loop.py, performance_attributor.py, prompt_builder.py) live at project root

**Rationale**:
- These are the "entry points" to the system
- Frequently modified during development
- Easy to find and run: `python autonomous_loop.py`

### 3. **Tests Mirror Source Structure**
Test files organized to match src/ structure exactly

**Example**:
- `src/analysis/engine.py` → `tests/analysis/test_engine.py`
- `src/backtest/engine.py` → `tests/backtest/test_engine.py`
- `autonomous_loop.py` → `tests/test_integration_scenarios.py`

### 4. **Specifications in .claude/specs/**
Detailed spec documents (requirements, design, tasks) kept in Claude Code workspace

**Rationale**:
- Integration with Claude Code spec workflow
- Version controlled with code
- Easy to reference during implementation

## Naming Conventions

### Python Files
- **Modules**: lowercase_with_underscores.py
- **Classes**: PascalCase (class ChampionStrategy)
- **Functions**: lowercase_with_underscores (def extract_strategy_params)
- **Constants**: UPPERCASE_WITH_UNDERSCORES (METRIC_SHARPE)

### Test Files
- **Pattern**: `test_<module_name>.py`
- **Example**: `test_champion_tracking.py`, `test_evolutionary_prompts.py`
- **Integration tests**: `test_integration_<feature>.py`

### JSON Files
- **Champion**: `champion_strategy.json`
- **Failure patterns**: `failure_patterns.json`
- **Iteration history**: `iteration_history.json`

### Generated Strategy Files
- **Pattern**: `generated_strategy_loop_iter<N>.py`
- **Example**: `generated_strategy_loop_iter0.py`, `generated_strategy_loop_iter5.py`

## Module Dependencies

### Import Rules

**✅ Allowed**:
```python
# Absolute imports from src/
from src.constants import METRIC_SHARPE
from src.analysis.engine import AnalysisEngine
from src.backtest.engine import BacktestEngine

# Absolute imports from root
from autonomous_loop import AutonomousLoop
from performance_attributor import extract_strategy_params
```

**❌ Avoid**:
```python
# Relative imports (breaks clarity)
from ..constants import METRIC_SHARPE

# Circular dependencies
# autonomous_loop.py → prompt_builder.py → autonomous_loop.py
```

### Dependency Graph
```
┌─────────────────────────────────────────────────┐
│ autonomous_loop.py (Main Orchestrator)          │
│   ├─> prompt_builder.py (Prompt construction)  │
│   ├─> performance_attributor.py (Attribution)  │
│   ├─> history.py (Iteration tracking)          │
│   └─> src/failure_tracker.py (Failure learning)│
└─────────────────────────────────────────────────┘
           │
           ├─> src/analysis/ (Strategy generation)
           │     └─> claude_client.py → OpenRouter API
           │
           ├─> src/backtest/ (Validation & execution)
           │     ├─> sandbox.py → Code execution
           │     ├─> validation.py → Safety checks
           │     └─> engine.py → Finlab backtesting
           │
           └─> src/data/ (Data infrastructure)
                 └─> downloader.py → Finlab API
```

## Code Patterns

### 1. **Dataclass for Data Structures**
```python
from dataclasses import dataclass, asdict
from typing import Dict, List, Any

@dataclass
class ChampionStrategy:
    """Best-performing strategy across iterations."""
    iteration_num: int
    code: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    success_patterns: List[str]
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)
```

### 2. **Atomic Persistence Pattern**
```python
import tempfile
import os
import json

def _save_champion(self):
    """Save champion with atomic write."""
    dir_path = os.path.dirname(CHAMPION_FILE)

    # Write to temporary file
    temp_fd, temp_path = tempfile.mkstemp(
        dir=dir_path or '.',
        prefix='.champion_',
        suffix='.tmp'
    )

    try:
        with os.fdopen(temp_fd, 'w') as f:
            json.dump(self.champion.to_dict(), f, indent=2)

        # Atomic rename
        os.replace(temp_path, CHAMPION_FILE)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise RuntimeError(f"Save failed: {e}")
```

### 3. **Logging Pattern**
```python
import logging

logger = logging.getLogger(__name__)

def run_iteration(self, iteration_num: int, data):
    logger.info(f"Starting iteration {iteration_num}")

    try:
        result = self._execute_strategy(data)
        logger.info(f"Iteration {iteration_num} complete: Sharpe {result.sharpe:.4f}")
    except Exception as e:
        logger.error(f"Iteration {iteration_num} failed: {e}")
        raise
```

### 4. **Test Fixtures Pattern**
```python
import pytest
from unittest.mock import Mock
from datetime import datetime

@pytest.fixture
def sample_champion() -> ChampionStrategy:
    """Sample champion strategy for testing."""
    return ChampionStrategy(
        iteration_num=3,
        code="# Champion code",
        parameters={
            'roe_type': 'smoothed',
            'roe_smoothing_window': 4,
            'liquidity_threshold': 150_000_000
        },
        metrics={'sharpe_ratio': 0.97, 'annual_return': 0.18},
        success_patterns=[
            "roe.rolling(window=4).mean() - 4-quarter smoothing",
            "liquidity_filter > 150,000,000 TWD - Stable stocks"
        ],
        timestamp=datetime.now().isoformat()
    )

def test_champion_update_with_improvement(sample_champion):
    """Test champion updates with 5% improvement."""
    loop = AutonomousLoop(model='test-model')
    loop.champion = sample_champion

    # Test with 6% improvement (should update)
    new_sharpe = 0.97 * 1.06
    updated = loop._update_champion(5, "# New code", {'sharpe_ratio': new_sharpe})

    assert updated is True
    assert loop.champion.iteration_num == 5
```

## Configuration

### Settings Pattern
```python
# config/settings.py

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# API configuration
FINLAB_API_TOKEN = os.getenv("FINLAB_API_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# System settings
MAX_ITERATIONS = 10
DEFAULT_MODEL = "google/gemini-2.5-flash"
BACKTEST_TIMEOUT = 120  # seconds

# Performance thresholds
MIN_SHARPE_FOR_CHAMPION = 0.5
CHAMPION_UPDATE_THRESHOLD = 1.05  # 5% improvement
PROBATION_THRESHOLD = 1.10  # 10% for new champions
```

### Constants Pattern
```python
# src/constants.py

# Metric keys (standardized)
METRIC_SHARPE = "sharpe_ratio"
METRIC_RETURN = "total_return"
METRIC_DRAWDOWN = "max_drawdown"
METRIC_WIN_RATE = "win_rate"

# File paths
CHAMPION_FILE = "champion_strategy.json"
FAILURE_PATTERNS_FILE = "failure_patterns.json"
HISTORY_FILE = "iteration_history.json"

# Parameter criticality levels
CRITICAL_PARAMS = ['roe_type', 'roe_smoothing_window', 'liquidity_threshold']
MODERATE_PARAMS = ['revenue_handling', 'value_factor']
LOW_PARAMS = ['price_filter', 'volume_threshold']
```

## Documentation Standards

### Module Docstrings (Bilingual)
```python
"""
Failure Tracker Module

Tracks failed parameter configurations and generates learning directives
to avoid repeating unsuccessful changes.

This module implements dynamic failure pattern tracking that replaces static
AVOID lists in optimization prompts, enabling the system to learn from past
mistakes and accumulate optimization knowledge over time.

失敗追蹤模組

追蹤失敗的參數配置並生成學習指令，避免重複不成功的變更。
此模組實現動態失敗模式追蹤，替代優化提示中的靜態避免清單。
"""
```

### Function Docstrings
```python
def extract_strategy_params(code: str) -> Dict[str, Any]:
    """Extract strategy parameters from generated code using regex.

    Extracts 8 key parameters: ROE smoothing, liquidity threshold,
    revenue handling, value factor, price filter, volume threshold,
    portfolio size, and rebalance frequency.

    Args:
        code: Generated Python strategy code to analyze

    Returns:
        Dictionary mapping parameter names to extracted values.
        Uses None for missing parameters and fallback defaults.

    Example:
        >>> code = "roe_smoothed = roe.rolling(window=4).mean()"
        >>> params = extract_strategy_params(code)
        >>> params['roe_type']
        'smoothed'
        >>> params['roe_smoothing_window']
        4
    """
```

### README Structure
```markdown
# Finlab Autonomous Trading Strategy Optimizer

> 台灣股市自主交易策略優化系統 | Taiwan Stock Market Autonomous Strategy Optimization

[English] | [中文]

## Features (功能)
- 自主策略生成 (Autonomous strategy generation)
- 智能回測驗證 (Intelligent backtest validation)
- 學習系統增強 (Learning system enhancement)

## Quick Start (快速開始)
...
```

## Migration Guidelines

### Adding New Modules
1. Create directory in `src/<domain>/`
2. Add `__init__.py` for package
3. Create test directory `tests/<domain>/`
4. Update this structure.md

### Deprecating Old Code
1. Mark as deprecated in docstring
2. Add migration guide in comments
3. Update tests to new pattern
4. Remove after 2 releases

### Refactoring Guidelines
1. Keep file names stable (breaks imports)
2. Use `@deprecated` decorator for functions
3. Run full test suite after refactor
4. Update steering docs if architecture changes
