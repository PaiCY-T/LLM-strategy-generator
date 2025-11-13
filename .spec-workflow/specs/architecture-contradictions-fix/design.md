# architecture-contradictions-fix - Design Document

## Overview

本设计采用**4阶段渐进式重构策略**，修复 `iteration_executor.py` 中的架构矛盾，消除静默降级，并建立可扩展的代码生成架构。

### 设计原则
1. **避免过度工程化**：遵循项目核心原则，每个阶段只添加必要的复杂度
2. **TDD 驱动**：使用 zen testgen 生成测试，先红后绿
3. **渐进式部署**：通过 feature flags 控制每个阶段的启用
4. **快速回滚**：Master kill switch `ENABLE_GENERATION_REFACTORING` 可立即回退到原实现
5. **可观测性**：审计追踪系统记录所有决策过程

### 4-Phase Architecture

```
Phase 1: Emergency Fix (立即修复)
├── 配置优先级强制执行
├── 消除静默降级
└── Feature Flag: phase1_config_enforcement

Phase 2: Type Safety (类型安全)
├── Pydantic 配置模型
├── 编译时验证
└── Feature Flag: phase2_pydantic_validation

Phase 3: Strategy Pattern (架构重构)
├── LLMStrategy, FactorGraphStrategy
├── StrategyFactory
└── Feature Flag: phase3_strategy_pattern

Phase 4: Audit Trail (审计追踪)
├── GenerationDecision 记录
├── HTML 报告生成
└── Feature Flag: phase4_audit_trail
```

### Kill Switch Design
```python
# src/learning/config.py
ENABLE_GENERATION_REFACTORING = os.getenv("ENABLE_GENERATION_REFACTORING", "false").lower() == "true"

# iteration_executor.py
if not ENABLE_GENERATION_REFACTORING:
    return self._decide_generation_method_legacy()  # 原实现
```

**Default**: `false` in production, `true` in development/testing

---

## Architecture

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                   IterationExecutor                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  execute_iterations()                                 │  │
│  │    ↓                                                  │  │
│  │  _decide_generation_method() ← Phase 1 Fix           │  │
│  │    ↓                                                  │  │
│  │  ┌─────────────────────────┐                         │  │
│  │  │ Phase 3: Strategy?      │                         │  │
│  │  │  Yes → StrategyFactory  │                         │  │
│  │  │  No  → _generate_with_* │                         │  │
│  │  └─────────────────────────┘                         │  │
│  │    ↓                                                  │  │
│  │  Phase 4: AuditLogger.log_decision()                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Phase 1: Emergency Fix Architecture

**File**: `src/learning/iteration_executor.py` (修改)

**Buggy Code (Lines 328-344)**:
```python
def _decide_generation_method(self) -> bool:
    innovation_rate = self.config.get("innovation_rate", 100)
    use_llm = random.random() * 100 < innovation_rate
    return use_llm  # ❌ 完全忽略 use_factor_graph 标志
```

**Fixed Implementation**:
```python
def _decide_generation_method(self) -> bool:
    """Decide generation method with configuration priority enforcement.

    Priority: use_factor_graph > innovation_rate

    Returns:
        True for LLM, False for Factor Graph

    Raises:
        ConfigurationConflictError: If use_factor_graph=True AND innovation_rate=100
    """
    use_factor_graph = self.config.get("use_factor_graph")
    innovation_rate = self.config.get("innovation_rate", 100)

    # ✅ Configuration conflict detection
    if use_factor_graph is True and innovation_rate == 100:
        raise ConfigurationConflictError(
            "Configuration conflict: use_factor_graph=True but innovation_rate=100 "
            "(forces Factor Graph AND forces LLM)"
        )

    # ✅ Priority: use_factor_graph > innovation_rate
    if use_factor_graph is not None:
        return not use_factor_graph  # True=LLM, False=FactorGraph

    # Fallback to innovation_rate (original logic)
    use_llm = random.random() * 100 < innovation_rate
    return use_llm
```

**Silent Fallback Elimination**:
```python
def _generate_with_llm(self, feedback: str, iteration_num: int):
    """Generate strategy using LLM with explicit error handling.

    Raises:
        LLMUnavailableError: If LLM client/engine not available
        LLMEmptyResponseError: If LLM returns empty code
        LLMGenerationError: If LLM generation fails
    """
    # ❌ OLD (Line 360-362): Silent fallback
    # if not self.llm_client.is_enabled():
    #     logger.warning("LLM client not enabled, falling back to Factor Graph")
    #     return self._generate_with_factor_graph(iteration_num)

    # ✅ NEW: Explicit error
    if not self.llm_client.is_enabled():
        raise LLMUnavailableError("LLM client is not enabled")

    engine = self.llm_client.get_engine()

    # ❌ OLD (Line 366-368): Silent fallback
    # if not engine:
    #     logger.warning("LLM engine not available")
    #     return self._generate_with_factor_graph(iteration_num)

    # ✅ NEW: Explicit error
    if not engine:
        raise LLMUnavailableError("LLM engine not available")

    try:
        # ... (champion extraction logic unchanged)

        strategy_code = engine.generate_innovation(
            champion_code=champion_code,
            champion_metrics=champion_metrics,
            failure_history=None,
            target_metric="sharpe_ratio"
        )

        # ❌ OLD (Line 398-400): Silent fallback
        # if not strategy_code:
        #     logger.warning("LLM returned empty code")
        #     return self._generate_with_factor_graph(iteration_num)

        # ✅ NEW: Explicit error
        if not strategy_code:
            raise LLMEmptyResponseError("LLM returned empty code")

        return strategy_code, None, None

    # ❌ OLD (Line 406-409): Silent fallback
    # except Exception as e:
    #     logger.error(f"LLM generation failed: {e}", exc_info=True)
    #     return self._generate_with_factor_graph(iteration_num)

    # ✅ NEW: Explicit error with context preservation
    except Exception as e:
        raise LLMGenerationError(f"LLM generation failed: {e}") from e
```

### Phase 2: Pydantic Configuration Models

**New File**: `src/learning/config_models.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional

class GenerationConfig(BaseModel):
    """Configuration for strategy generation with validation.

    Validation Rules:
    1. use_factor_graph has priority over innovation_rate
    2. Cannot set use_factor_graph=True AND innovation_rate=100 (conflict)
    3. innovation_rate must be 0-100
    """
    use_factor_graph: Optional[bool] = Field(
        default=None,
        description="If set, overrides innovation_rate. True=Factor Graph, False=LLM"
    )
    innovation_rate: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Percentage chance to use LLM (0=Factor Graph, 100=LLM)"
    )

    @field_validator("innovation_rate")
    @classmethod
    def validate_innovation_rate(cls, v: int) -> int:
        if not 0 <= v <= 100:
            raise ValueError(f"innovation_rate must be 0-100, got {v}")
        return v

    @field_validator("use_factor_graph")
    @classmethod
    def validate_no_conflict(cls, v: Optional[bool], info) -> Optional[bool]:
        """Prevent configuration conflicts."""
        if v is True and info.data.get("innovation_rate") == 100:
            raise ValueError(
                "Configuration conflict: use_factor_graph=True but innovation_rate=100"
            )
        return v

    def should_use_llm(self) -> bool:
        """Determine generation method with configuration priority.

        Returns:
            True for LLM, False for Factor Graph
        """
        if self.use_factor_graph is not None:
            return not self.use_factor_graph

        # Fallback to innovation_rate
        import random
        return random.random() * 100 < self.innovation_rate
```

**Integration**: `IterationExecutor.__init__()` validates config using Pydantic

### Phase 3: Strategy Pattern Refactoring

**New File**: `src/learning/generation_strategies.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, Optional, Any

@dataclass(frozen=True)
class GenerationContext:
    """Immutable context passed to generation strategies.

    Encapsulates all data needed for strategy execution:
    - Configuration (innovation_rate, use_factor_graph)
    - Champion information (code, metrics, generation_method)
    - LLM client and feedback
    - Iteration metadata

    NOTE: Frozen dataclass for immutability. Will promote to Pydantic
    in Phase 2 if validation needed.
    """
    config: dict
    llm_client: Any  # LLMClient instance
    champion_tracker: Any  # ChampionTracker instance
    feedback: str
    iteration_num: int
    champion_code: str = ""
    champion_metrics: dict = None
    target_metric: str = "sharpe_ratio"

class GenerationStrategy(ABC):
    """Abstract strategy for strategy code generation."""

    @abstractmethod
    def generate(self, context: GenerationContext) -> Tuple[str, Optional[str], Optional[int]]:
        """Generate strategy code.

        Args:
            context: Immutable generation context with all needed data

        Returns:
            Tuple of (code, strategy_id, generation_num)

        Raises:
            LLMGenerationError: If generation fails
        """
        pass

class LLMStrategy(GenerationStrategy):
    """Generate strategies using LLM innovation."""

    def generate(self, context: GenerationContext) -> Tuple[str, Optional[str], Optional[int]]:
        if not context.llm_client.is_enabled():
            raise LLMUnavailableError("LLM client is not enabled")

        engine = context.llm_client.get_engine()
        if not engine:
            raise LLMUnavailableError("LLM engine not available")

        try:
            strategy_code = engine.generate_innovation(
                champion_code=context.champion_code,
                champion_metrics=context.champion_metrics,
                failure_history=None,
                target_metric=context.target_metric
            )

            if not strategy_code:
                raise LLMEmptyResponseError("LLM returned empty code")

            return strategy_code, None, None

        except Exception as e:
            raise LLMGenerationError(f"LLM generation failed: {e}") from e

class FactorGraphStrategy(GenerationStrategy):
    """Generate strategies using Factor Graph combinations."""

    def __init__(self, factor_graph_generator):
        self.generator = factor_graph_generator

    def generate(self, context: GenerationContext) -> Tuple[str, Optional[str], Optional[int]]:
        return self.generator.generate(context.iteration_num)

class MixedStrategy(GenerationStrategy):
    """Probabilistic mix of LLM and Factor Graph based on innovation_rate."""

    def __init__(self, llm_strategy: LLMStrategy, fg_strategy: FactorGraphStrategy):
        self.llm = llm_strategy
        self.fg = fg_strategy

    def generate(self, context: GenerationContext) -> Tuple[str, Optional[str], Optional[int]]:
        import random
        innovation_rate = context.config.get("innovation_rate", 100)

        if random.random() * 100 < innovation_rate:
            return self.llm.generate(context)
        else:
            return self.fg.generate(context)

class StrategyFactory:
    """Factory for creating generation strategies based on configuration."""

    @staticmethod
    def create_strategy(
        config: dict,
        llm_client,
        factor_graph_generator
    ) -> GenerationStrategy:
        """Create strategy based on configuration.

        Priority: use_factor_graph > innovation_rate
        """
        use_factor_graph = config.get("use_factor_graph")

        if use_factor_graph is True:
            return FactorGraphStrategy(factor_graph_generator)
        elif use_factor_graph is False:
            return LLMStrategy()
        else:
            # Mixed strategy based on innovation_rate
            return MixedStrategy(
                LLMStrategy(),
                FactorGraphStrategy(factor_graph_generator)
            )
```

**Integration**: `IterationExecutor` uses `StrategyFactory.create_strategy()` when Phase 3 enabled

### Phase 4: Audit Trail System

**New File**: `src/learning/audit_trail.py`

```python
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List
import json
from pathlib import Path

@dataclass
class GenerationDecision:
    """Record of a single generation decision."""
    timestamp: str
    iteration_num: int
    decision: str  # "llm", "factor_graph"
    reason: str
    config_snapshot: dict
    use_factor_graph: Optional[bool]
    innovation_rate: int
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

class AuditLogger:
    """Logger for generation decisions with HTML report generation."""

    def __init__(self, log_dir: str = "logs/generation_audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.decisions: List[GenerationDecision] = []

    def log_decision(
        self,
        iteration_num: int,
        decision: str,
        reason: str,
        config: dict,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log a generation decision."""
        record = GenerationDecision(
            timestamp=datetime.now().isoformat(),
            iteration_num=iteration_num,
            decision=decision,
            reason=reason,
            config_snapshot=config.copy(),
            use_factor_graph=config.get("use_factor_graph"),
            innovation_rate=config.get("innovation_rate", 100),
            success=success,
            error=error
        )
        self.decisions.append(record)

        # Write to JSON
        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.json"
        with open(log_file, 'a') as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def generate_html_report(self, output_file: str = "audit_report.html"):
        """Generate HTML report of all decisions."""
        # ... (HTML generation logic)
        pass
```

**Integration Approach (Gemini Recommendation: Option B)**:
- `IterationExecutor` wraps `strategy.generate()` calls with audit logging
- Follows Single Responsibility Principle (SRP)
- Strategy focuses on generation, IterationExecutor handles logging

```python
# In IterationExecutor.execute_iterations()
try:
    code, sid, sgen = strategy.generate(context)
    self.audit_logger.log_decision(
        iteration_num=iteration_num,
        decision="llm" if isinstance(strategy, LLMStrategy) else "factor_graph",
        reason=f"Config: use_factor_graph={config.get('use_factor_graph')}, innovation_rate={config.get('innovation_rate')}",
        config=config,
        success=True
    )
except Exception as e:
    self.audit_logger.log_decision(
        iteration_num=iteration_num,
        decision="unknown",
        reason="Generation failed",
        config=config,
        success=False,
        error=str(e)
    )
    raise
```

---

## Components and Interfaces

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ IterationExecutor                                           │
│  - config: dict                                             │
│  - llm_client: LLMClient                                    │
│  - champion_tracker: ChampionTracker                        │
│  - audit_logger: AuditLogger (Phase 4)                      │
│  - strategy: GenerationStrategy (Phase 3)                   │
│                                                             │
│  + execute_iterations()                                     │
│  + _decide_generation_method() → bool (Phase 1)             │
│  + _generate_with_llm() → Tuple (Phase 1)                   │
│  + _generate_with_factor_graph() → Tuple                    │
└─────────────────────────────────────────────────────────────┘
         ↓ uses (Phase 3)
┌─────────────────────────────────────────────────────────────┐
│ StrategyFactory                                             │
│  + create_strategy(config, llm_client, fg_gen) → Strategy   │
└─────────────────────────────────────────────────────────────┘
         ↓ creates
┌─────────────────────────────────────────────────────────────┐
│ <<interface>> GenerationStrategy                            │
│  + generate(context: GenerationContext) → Tuple             │
└─────────────────────────────────────────────────────────────┘
         ↑ implements
    ┌────┴────┬────────────┐
    │         │            │
┌─────────┐ ┌──────────────┐ ┌──────────────┐
│ LLM     │ │ FactorGraph  │ │ Mixed        │
│ Strategy│ │ Strategy     │ │ Strategy     │
└─────────┘ └──────────────┘ └──────────────┘
```

### Interface Specifications

#### GenerationStrategy Interface
```python
class GenerationStrategy(ABC):
    @abstractmethod
    def generate(self, context: GenerationContext) -> Tuple[str, Optional[str], Optional[int]]:
        """Generate strategy code.

        Args:
            context: GenerationContext containing:
                - config: dict
                - llm_client: LLMClient
                - champion_tracker: ChampionTracker
                - feedback: str
                - iteration_num: int
                - champion_code: str
                - champion_metrics: dict
                - target_metric: str

        Returns:
            Tuple[str, Optional[str], Optional[int]]:
                - code: Generated strategy code
                - strategy_id: ID if from factor graph, None if from LLM
                - generation_num: Generation number if from factor graph

        Raises:
            LLMGenerationError: Base exception for all generation failures
            LLMUnavailableError: LLM client/engine not available
            LLMEmptyResponseError: LLM returned empty code
            ConfigurationConflictError: Invalid configuration
        """
        pass
```

#### AuditLogger Interface
```python
class AuditLogger:
    def log_decision(
        self,
        iteration_num: int,
        decision: str,  # "llm" | "factor_graph"
        reason: str,
        config: dict,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """Log a generation decision with full context."""
        pass

    def generate_html_report(self, output_file: str = "audit_report.html") -> None:
        """Generate HTML report of all decisions."""
        pass
```

---

## Data Models

### GenerationContext (Phase 3)
```python
@dataclass(frozen=True)
class GenerationContext:
    """Immutable context for generation strategies.

    Design Decision (Gemini Audit):
    - Use frozen dataclass for Phase 3
    - Promote to Pydantic in Phase 2 if validation needed
    - Immutability prevents accidental state mutation
    """
    config: dict
    llm_client: Any  # LLMClient
    champion_tracker: Any  # ChampionTracker
    feedback: str
    iteration_num: int
    champion_code: str = ""
    champion_metrics: dict = None
    target_metric: str = "sharpe_ratio"
```

### GenerationConfig (Phase 2)
```python
class GenerationConfig(BaseModel):
    """Pydantic model for configuration validation."""
    use_factor_graph: Optional[bool] = None
    innovation_rate: int = Field(default=100, ge=0, le=100)

    @field_validator("use_factor_graph")
    @classmethod
    def validate_no_conflict(cls, v, info):
        if v is True and info.data.get("innovation_rate") == 100:
            raise ValueError("Configuration conflict")
        return v

    def should_use_llm(self) -> bool:
        """Decision logic with priority enforcement."""
        if self.use_factor_graph is not None:
            return not self.use_factor_graph
        return random.random() * 100 < self.innovation_rate
```

### GenerationDecision (Phase 4)
```python
@dataclass
class GenerationDecision:
    """Audit record for a single decision."""
    timestamp: str
    iteration_num: int
    decision: str  # "llm" | "factor_graph"
    reason: str
    config_snapshot: dict
    use_factor_graph: Optional[bool]
    innovation_rate: int
    success: bool
    error: Optional[str] = None
```

---

## Error Handling

### Exception Hierarchy

```python
class GenerationError(Exception):
    """Base exception for all generation-related errors."""
    pass

class ConfigurationError(GenerationError):
    """Base exception for configuration-related errors."""
    pass

class ConfigurationConflictError(ConfigurationError):
    """Raised when configuration has conflicting settings.

    Example: use_factor_graph=True AND innovation_rate=100
    """
    pass

class LLMGenerationError(GenerationError):
    """Base exception for LLM generation failures."""
    pass

class LLMUnavailableError(LLMGenerationError):
    """Raised when LLM client or engine is not available.

    Replaces silent fallback at lines 360-362, 366-368
    """
    pass

class LLMEmptyResponseError(LLMGenerationError):
    """Raised when LLM returns empty code.

    Replaces silent fallback at lines 398-400
    """
    pass
```

### Error Handling Strategy

**Phase 1 Changes**:
1. **Lines 360-362**: `if not llm_client.is_enabled()` → raise `LLMUnavailableError`
2. **Lines 366-368**: `if not engine` → raise `LLMUnavailableError`
3. **Lines 398-400**: `if not strategy_code` → raise `LLMEmptyResponseError`
4. **Lines 406-409**: `except Exception` → raise `LLMGenerationError` (preserve stack trace with `from e`)

**Error Context Preservation**:
```python
try:
    strategy_code = engine.generate_innovation(...)
except Exception as e:
    # ✅ Preserve original exception with 'from e'
    raise LLMGenerationError(f"LLM generation failed: {e}") from e
```

**Caller Responsibility**:
- `IterationExecutor.execute_iterations()` catches these exceptions
- Logs error with `audit_logger.log_decision(..., success=False, error=str(e))`
- Decides whether to retry, skip iteration, or fail fast based on error type

---

## Testing Strategy

### Test-Driven Development Workflow

**Tools**: zen testgen (Gemini 2.5 Pro)

**Process**:
1. **Generate Tests**: Use zen testgen to create comprehensive test suite for each phase
2. **Run Tests (Red)**: Verify tests fail with current implementation
3. **Implement Fix (Green)**: Make minimal changes to pass tests
4. **Refactor**: Clean up code while keeping tests green
5. **Coverage Validation**: Ensure >95% coverage before phase completion

### Phase 1 Test Suite

**File**: `tests/learning/test_iteration_executor_phase1.py` (Already created by zen testgen)

**Coverage Targets**:
- `_decide_generation_method()`: 100% (configuration priority logic)
- `_generate_with_llm()`: 100% (silent fallback elimination)

**Key Test Cases**:
```python
class TestDecideGenerationMethod:
    def test_use_factor_graph_has_priority_over_innovation_rate()
    def test_configuration_conflict_raises_error()
    def test_probabilistic_decision_with_innovation_rate()

class TestGenerateWithLLM:
    def test_llm_unavailable_raises_error()  # No silent fallback
    def test_llm_engine_none_raises_error()   # No silent fallback
    def test_empty_code_raises_error()        # No silent fallback
    def test_exception_raises_error()         # No silent fallback
```

### Shadow Mode Testing (Gemini Recommendation)

**Strategy**: Combination of Pytest Fixture + CI Regression Check

**Pytest Fixture (Phase 3 Testing)**:
```python
# tests/conftest.py
import pytest

@pytest.fixture
def shadow_mode_strategies(config, llm_client, fg_generator):
    """Run both old and new implementations in parallel for comparison."""
    old_executor = IterationExecutor(config, llm_client, ...)
    new_strategy = StrategyFactory.create_strategy(config, llm_client, fg_generator)

    context = GenerationContext(
        config=config,
        llm_client=llm_client,
        champion_tracker=...,
        feedback="test feedback",
        iteration_num=1
    )

    # Run both implementations
    old_result = old_executor._generate_with_llm("test", 1)
    new_result = new_strategy.generate(context)

    # Compare results
    assert old_result[0] == new_result[0], "Code mismatch between old and new"

    return old_result, new_result
```

**CI Regression Check (Modified Option A)**:
```yaml
# .github/workflows/quality-checks.yml
jobs:
  shadow-mode-validation:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - name: Run Shadow Mode Tests
        run: pytest tests/learning/test_shadow_mode.py -v

      - name: Compare Outputs
        run: |
          python scripts/compare_shadow_outputs.py \
            --old logs/old_generation.json \
            --new logs/new_generation.json \
            --threshold 0.95
```

### Coverage Requirements

**Targets** (Gemini Recommendation):
- Unit Tests: **>95%** (radon cyclomatic complexity < 10 for new code)
- Integration Tests: **>70%**
- E2E Tests: Critical paths only

**Tools**:
- `pytest-cov` for coverage reporting
- `radon` for cyclomatic complexity analysis

**CI Enforcement**:
```yaml
- name: Check Coverage
  run: |
    pytest --cov=src/learning --cov-report=term --cov-fail-under=95
    radon cc src/learning/generation_strategies.py -a -nb
```

### Technical Debt Metrics (Gemini Recommendation)

**Goal**: Reduce complexity from 8-9/10 → 3-4/10

**Measurement**:
1. **Cyclomatic Complexity**: Use `radon cc` to measure complexity score
   - Target: <10 per function, <5 average
2. **Test Coverage**: >95% for new code
3. **Team Vote**: Fist of Five vote after each phase
   - 0 fingers = not acceptable (8-9/10 complexity)
   - 5 fingers = excellent (3-4/10 complexity)

**Tracking**:
```bash
# Before Phase 1
radon cc src/learning/iteration_executor.py -a
# Average complexity: 8.2 (High)

# After Phase 1
radon cc src/learning/iteration_executor.py -a
# Target: <5.0 (Moderate)
```

---

## Deployment Strategy

### Feature Flags

**Master Kill Switch**:
```python
# src/learning/config.py
ENABLE_GENERATION_REFACTORING = os.getenv("ENABLE_GENERATION_REFACTORING", "false").lower() == "true"
```

**Phase-Specific Flags**:
```python
PHASE1_CONFIG_ENFORCEMENT = os.getenv("PHASE1_CONFIG_ENFORCEMENT", "false").lower() == "true"
PHASE2_PYDANTIC_VALIDATION = os.getenv("PHASE2_PYDANTIC_VALIDATION", "false").lower() == "true"
PHASE3_STRATEGY_PATTERN = os.getenv("PHASE3_STRATEGY_PATTERN", "false").lower() == "true"
PHASE4_AUDIT_TRAIL = os.getenv("PHASE4_AUDIT_TRAIL", "false").lower() == "true"
```

**Usage**:
```python
def _decide_generation_method(self) -> bool:
    if not ENABLE_GENERATION_REFACTORING:
        return self._decide_generation_method_legacy()

    if not PHASE1_CONFIG_ENFORCEMENT:
        return self._decide_generation_method_legacy()

    # Phase 1 implementation
    use_factor_graph = self.config.get("use_factor_graph")
    # ...
```

### Rollback Plan

**Scenario 1: Phase 1 breaks production**
1. Set `ENABLE_GENERATION_REFACTORING=false` in environment
2. Restart service (no code deployment needed)
3. System reverts to original implementation
4. Fix bugs in development, re-enable after validation

**Scenario 2: Phase 3 causes performance regression**
1. Set `PHASE3_STRATEGY_PATTERN=false`
2. System falls back to Phase 1/2 implementation
3. Investigate performance issue offline
4. Re-enable after optimization

**Validation**: Shadow mode tests run in CI for every phase to catch regressions early

### Deployment Sequence

```
Week 1: Phase 1 (Emergency Fix)
├── Day 1-2: zen testgen → test_iteration_executor_phase1.py
├── Day 3-4: Implement fixes, run tests (Red → Green)
├── Day 5: PR review, merge to staging
└── Week 1 End: Deploy to production with PHASE1_CONFIG_ENFORCEMENT=true

Week 2: Phase 2 (Pydantic Validation)
├── Day 1-2: zen testgen → test_config_models.py
├── Day 3-4: Implement Pydantic models, run tests
├── Day 5: PR review, merge to staging
└── Week 2 End: Deploy with PHASE2_PYDANTIC_VALIDATION=true

Week 3: Phase 3 (Strategy Pattern)
├── Day 1-3: zen testgen → test_generation_strategies.py
├── Day 4-5: Implement Strategy Pattern, shadow mode tests
├── Week 3 End: PR review, merge to staging

Week 4: Phase 4 (Audit Trail)
├── Day 1-2: zen testgen → test_audit_trail.py
├── Day 3-4: Implement audit logging, HTML reports
├── Day 5: Full system integration test
└── Week 4 End: Deploy all phases to production
```

---

## CI/CD Integration

**Reference**: `.spec-workflow/specs/quality-assurance-system/`

### GitHub Actions Workflow

**File**: `.github/workflows/architecture-refactoring.yml`

```yaml
name: Architecture Refactoring Quality Checks

on:
  pull_request:
    branches: [main]
    paths:
      - 'src/learning/iteration_executor.py'
      - 'src/learning/config_models.py'
      - 'src/learning/generation_strategies.py'
      - 'src/learning/audit_trail.py'
      - 'tests/learning/test_*.py'
  push:
    branches: [main]

jobs:
  type-check:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install mypy pydantic

      - name: Run type checks
        run: |
          mypy src/learning/iteration_executor.py
          mypy src/learning/config_models.py
          mypy src/learning/generation_strategies.py

  unit-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov radon

      - name: Run Phase 1 Tests
        run: |
          pytest tests/learning/test_iteration_executor_phase1.py -v --cov=src/learning/iteration_executor --cov-report=term --cov-fail-under=95

      - name: Check Cyclomatic Complexity
        run: |
          radon cc src/learning/iteration_executor.py -a -nb
          radon cc src/learning/generation_strategies.py -a -nb

  shadow-mode-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Shadow Mode Validation
        env:
          ENABLE_GENERATION_REFACTORING: "true"
          PHASE3_STRATEGY_PATTERN: "true"
        run: |
          pytest tests/learning/test_shadow_mode.py -v

      - name: Compare Outputs
        run: |
          python scripts/compare_shadow_outputs.py \
            --old logs/old_generation.json \
            --new logs/new_generation.json \
            --threshold 0.95

  integration-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Integration Tests
        env:
          ENABLE_GENERATION_REFACTORING: "true"
          PHASE1_CONFIG_ENFORCEMENT: "true"
          PHASE2_PYDANTIC_VALIDATION: "true"
        run: |
          pytest tests/integration/test_iteration_execution.py -v
```

### Quality Gates

**PR Merge Requirements**:
1. ✅ All type checks pass (mypy)
2. ✅ All unit tests pass (>95% coverage)
3. ✅ Shadow mode tests pass (>95% equivalence)
4. ✅ Cyclomatic complexity <10 per function
5. ✅ Manual code review approval

**Performance Target**: <5 minutes total CI runtime (parallel jobs)

---

## Summary

本设计通过4阶段渐进式重构解决了 `iteration_executor.py` 中的7个架构矛盾：

1. **Phase 1 (Emergency Fix)**: 修复配置优先级和静默降级 → 立即解决 pilot 测试 100% 失败问题
2. **Phase 2 (Type Safety)**: Pydantic 配置验证 → 编译时捕获配置错误
3. **Phase 3 (Strategy Pattern)**: 解耦 LLM 和 Factor Graph → 提升可维护性和可测试性
4. **Phase 4 (Audit Trail)**: 审计追踪系统 → 检测静默覆盖，生成分析报告

**关键设计决策**:
- **Kill Switch**: `ENABLE_GENERATION_REFACTORING` 允许快速回滚
- **Feature Flags**: 每个阶段独立控制，降低部署风险
- **Shadow Mode**: Pytest fixture + CI regression check 验证等价性
- **TDD**: zen testgen 生成测试 → Red-Green-Refactor 循环
- **Technical Debt Reduction**: radon 测量复杂度，>95% 覆盖率，Fist of Five 团队投票

**遵循项目原则**: 避免过度工程化，每个阶段只添加必要的复杂度。
