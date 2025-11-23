# 可执行实施计划：修复 `use_factor_graph` 标志位架构问题

> **项目编号**: ARCH-FIX-001
> **创建日期**: 2025-11-11
> **状态**: 待执行
> **优先级**: P0（紧急）

---

## 执行摘要

### 项目概览

**项目名称**: 修复 `use_factor_graph` 标志位被忽略的架构问题

**核心问题**: `src/learning/iteration_executor.py` 中 `_decide_generation_method()` 方法完全忽略 `use_factor_graph` 配置标志，导致Stage 2实验100%失败，A/B测试无法可信执行。

**项目目标**:
1. 解除Stage 2部署阻塞（成功率从0% → >80%）
2. 恢复A/B测试可信度（消除Silent Fallback干扰）
3. 降低技术债务（-40%可维护性 → 标准水平）
4. 建立可观测性（Prometheus + Grafana监控）

**时间线**: 3周实施 + 1周稳定期（共4周）

**预期收益**:
- ✅ Stage 2实验可信度: 0% → 100%
- ✅ LLM性能隔离验证: 无法验证 → 可验证
- ✅ 技术债务减少: 70%
- ✅ 可观测性提升: 0 → 完整监控体系

### 根因分析总结

**核心反模式**: "Optimistic Fallback with Hidden State Override"

**技术表现**:
- `use_factor_graph` 标志在 lines 328-344 完全被忽略
- 3个Silent Fallback点在 lines 346-409 掩盖实际执行路径
- 配置声明 `use_factor_graph=false` 但实际运行Factor Graph
- A/B测试结果不可信，无法独立验证LLM性能

**详细分析**: 参见 `ARCHITECTURE_CONTRADICTIONS_ANALYSIS.md`

---

## 执行路线图

```
Week 1              Week 2              Week 3              Week 4
Phase 1 → Phase 2   Phase 3             Phase 4             Stabilization
(2 days) (3 days)   (5 days)            (5 days)            (7 days)
   ↓         ↓          ↓                    ↓                   ↓
  Dev     Staging    Canary 5%          Canary 20%→50%     Prod 100%
  Fix     Config      Deploy              → 100%            7-day watch
   ↓         ↓          ↓                    ↓                   ↓
 100%     Pydantic  Strategy           Prometheus         Full Rollout
 Unit     Config    Pattern            + Grafana          + Monitoring
 Tests    Valid     Refactor           Observability      Stable
```

**关键里程碑**:
- Week 1 Day 2: Phase 1完成，Staging环境验证70%基线
- Week 1 Day 5: Phase 2完成，配置验证机制就位
- Week 2 Day 5: Phase 3完成，Stage 2实验>80%成功率
- Week 3 Day 5: Phase 4完成，监控体系全面部署
- Week 4 Day 7: 生产环境7天无故障，项目验收

---

## Phase 1: 紧急修复（Week 1, Day 1-2）

### 目标

- 修复 `_decide_generation_method()` 核心逻辑
- 移除所有Silent Fallback
- 恢复Stage 1实验70%基线
- 为Stage 2实验打好基础

### 代码修改任务

#### Task 1.1: 修改 `_decide_generation_method()` 逻辑 (4小时)

**文件**: `src/learning/iteration_executor.py` lines 328-344

**修改内容**:
```python
def _decide_generation_method(self) -> str:
    """
    决定使用哪种策略生成方法

    优先级:
    1. 显式 use_factor_graph 标志（用于A/B测试）
    2. 概率性 innovation_rate（生产混合模式）

    Returns:
        "llm" 或 "factor_graph"

    Raises:
        ConfigurationError: 配置冲突时抛出
    """
    # 1. 优先检查显式 use_factor_graph 标志
    use_factor_graph = self.config.get("use_factor_graph")

    if use_factor_graph is False:
        # Stage 2实验：强制100% LLM
        if not self.llm_client.is_enabled():
            raise ConfigurationError(
                "use_factor_graph=false requires LLM to be enabled. "
                "Current LLM enabled status: False. "
                "Please enable LLM in config or set use_factor_graph=true/null."
            )
        logger.info("Using LLM generation (forced by use_factor_graph=false)")
        return "llm"

    if use_factor_graph is True:
        # Stage 1实验：强制100% Factor Graph
        logger.info("Using Factor Graph generation (forced by use_factor_graph=true)")
        return "factor_graph"

    # 2. 回退到概率性 innovation_rate（生产环境混合模式）
    if use_factor_graph is None:
        innovation_rate = self.config.get("innovation_rate", 30)
        use_llm = random.random() * 100 < innovation_rate

        if use_llm and not self.llm_client.is_enabled():
            logger.warning(
                f"innovation_rate={innovation_rate}% selected LLM but LLM not enabled. "
                "Falling back to Factor Graph for this iteration."
            )
            return "factor_graph"

        method = "llm" if use_llm else "factor_graph"
        logger.info(f"Using {method} generation (probabilistic, innovation_rate={innovation_rate}%)")
        return method

    # 3. 未知的 use_factor_graph 值
    raise ConfigurationError(
        f"Invalid use_factor_graph value: {use_factor_graph}. "
        "Must be true, false, or null."
    )
```

**测试用例**: `tests/unit/learning/test_iteration_executor.py::TestDecideGenerationMethod`

---

#### Task 1.2: 移除Silent Fallback逻辑 (3小时)

**文件**: `src/learning/iteration_executor.py` lines 346-409

**修改点1 - LLM禁用检查** (line 350):
```python
# 删除
if not self.llm_client.is_enabled():
    logger.warning("LLM client not enabled, falling back to Factor Graph")
    return self._generate_with_factor_graph(iteration_num)

# 替换为
if not self.llm_client.is_enabled():
    raise ConfigurationError(
        "LLM generation requested but LLM client not enabled. "
        "This indicates a configuration error. "
        "Check use_factor_graph flag and llm.enabled setting."
    )
```

**修改点2 - Template依赖检查** (line 360):
```python
# 删除
if not template_available:
    logger.warning("Template not available, falling back to Factor Graph")
    return self._generate_with_factor_graph(iteration_num)

# 替换为
if not template_available:
    raise TemplateError(
        f"Template required for LLM generation but not available. "
        f"Iteration: {iteration_num}, Template dependencies broken."
    )
```

**修改点3 - LLM API错误处理** (line 380):
```python
# 删除
except OpenAIError as e:
    logger.error(f"LLM API error: {e}, falling back to Factor Graph")
    return self._generate_with_factor_graph(iteration_num)

# 替换为
except OpenAIError as e:
    # 向上传播，由调用方处理（可能重试或终止实验）
    raise OpenAIError(
        f"LLM generation failed at iteration {iteration_num}: {str(e)}"
    ) from e
```

**测试用例**: `tests/unit/learning/test_iteration_executor.py::TestGenerateWithLLM`

---

#### Task 1.3: 添加Generation Metrics (3小时)

**新增方法**: `_execute_generation()`

```python
def _execute_generation(self, method: str, iteration_num: int) -> Dict[str, Any]:
    """
    执行策略生成并记录元数据

    Args:
        method: "llm" 或 "factor_graph"
        iteration_num: 当前迭代次数

    Returns:
        包含策略和元数据的字典
    """
    start_time = time.time()

    try:
        if method == "llm":
            result = self._generate_with_llm(iteration_num)
        elif method == "factor_graph":
            result = self._generate_with_factor_graph(iteration_num)
        else:
            raise ValueError(f"Unknown generation method: {method}")

        # 添加元数据
        result["generation_metadata"] = {
            "method": method,
            "iteration": iteration_num,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": time.time() - start_time,
            "use_factor_graph": self.config.get("use_factor_graph"),
            "innovation_rate": self.config.get("innovation_rate"),
        }

        logger.info(
            f"Generation completed: method={method}, "
            f"iteration={iteration_num}, "
            f"duration={result['generation_metadata']['duration_seconds']:.2f}s"
        )

        return result

    except Exception as e:
        logger.error(
            f"Generation failed: method={method}, "
            f"iteration={iteration_num}, "
            f"error={str(e)}"
        )
        raise
```

**测试用例**: `tests/unit/learning/test_iteration_executor.py::TestExecuteGeneration`

---

#### Task 1.4: 更新调用点 (2小时)

**文件**: `src/learning/learning_loop.py`

**修改**: `run_iteration()` 方法

```python
# 原代码
def run_iteration(self, iteration_num: int) -> Dict[str, Any]:
    # ... 省略其他逻辑 ...

    # 旧调用
    use_llm = self.executor._decide_generation_method()
    if use_llm:
        strategy = self.executor._generate_with_llm(iteration_num)
    else:
        strategy = self.executor._generate_with_factor_graph(iteration_num)

# 新代码
def run_iteration(self, iteration_num: int) -> Dict[str, Any]:
    # ... 省略其他逻辑 ...

    # 新调用（统一接口）
    method = self.executor._decide_generation_method()
    strategy = self.executor._execute_generation(method, iteration_num)

    # strategy 现在包含 generation_metadata
    # 可用于后续分析和日志记录
```

---

#### Task 1.5: 更新实验配置 (1小时)

**文件**: `experiments/llm_learning_validation/config_llm_validation_test.yaml`

**验证配置正确性**:
```yaml
llm:
  enabled: true  # ✅ 必须为true（Stage 2需要LLM）
  use_factor_graph: false  # ✅ Stage 2强制LLM
  innovation_rate: 100  # ✅ 可选，use_factor_graph优先级更高
```

**检查Stage 1配置**:
```yaml
# experiments/stage1_baseline.yaml
llm:
  enabled: false  # ✅ Stage 1不需要LLM
  use_factor_graph: true  # ✅ Stage 1强制Factor Graph
```

---

### 测试任务

#### 单元测试 (3小时)

**文件**: `tests/unit/learning/test_iteration_executor.py`

**T1.1: `_decide_generation_method()` 逻辑测试**:
```python
class TestDecideGenerationMethod:
    def test_use_factor_graph_true_returns_factor_graph(self):
        """use_factor_graph=true 强制使用Factor Graph"""
        config = {"use_factor_graph": True}
        executor = IterationExecutor(config, mock_llm_client)
        assert executor._decide_generation_method() == "factor_graph"

    def test_use_factor_graph_false_with_enabled_llm_returns_llm(self):
        """use_factor_graph=false + LLM启用 → 100% LLM"""
        config = {"use_factor_graph": False}
        mock_llm_client.is_enabled.return_value = True
        executor = IterationExecutor(config, mock_llm_client)
        assert executor._decide_generation_method() == "llm"

    def test_use_factor_graph_false_with_disabled_llm_raises_error(self):
        """use_factor_graph=false + LLM禁用 → ConfigurationError"""
        config = {"use_factor_graph": False}
        mock_llm_client.is_enabled.return_value = False
        executor = IterationExecutor(config, mock_llm_client)
        with pytest.raises(ConfigurationError, match="LLM not enabled"):
            executor._decide_generation_method()

    def test_use_factor_graph_null_uses_innovation_rate(self):
        """use_factor_graph=null → 按innovation_rate概率决策"""
        config = {"use_factor_graph": None, "innovation_rate": 30}
        executor = IterationExecutor(config, mock_llm_client)
        # 模拟100次调用，验证约30%返回"llm"
        results = [executor._decide_generation_method() for _ in range(100)]
        llm_count = sum(1 for r in results if r == "llm")
        assert 20 <= llm_count <= 40  # 允许±10%误差
```

**T1.2: Silent Fallback移除验证**:
```python
class TestGenerateWithLLM:
    def test_llm_disabled_raises_error_not_fallback(self):
        """LLM禁用时抛出异常，不再silent fallback"""
        executor = IterationExecutor(config, mock_llm_client)
        mock_llm_client.is_enabled.return_value = False

        with pytest.raises(ConfigurationError, match="LLM not available"):
            executor._generate_with_llm(iteration_num=1)

    def test_llm_api_error_propagates_not_fallback(self):
        """LLM API错误向上传播，不再silent fallback"""
        mock_llm_client.generate.side_effect = OpenAIError("API quota exceeded")
        executor = IterationExecutor(config, mock_llm_client)

        with pytest.raises(OpenAIError):
            executor._generate_with_llm(iteration_num=1)
```

**T1.3: Generation Metrics记录测试**:
```python
class TestExecuteGeneration:
    def test_metrics_recorded_for_llm_path(self):
        """LLM路径记录正确的metrics"""
        executor = IterationExecutor(config, mock_llm_client)
        result = executor._execute_generation("llm", iteration_num=1)

        assert result["generation_metadata"]["method"] == "llm"
        assert result["generation_metadata"]["innovation_rate"] == 30
        assert "timestamp" in result["generation_metadata"]

    def test_metrics_recorded_for_factor_graph_path(self):
        """Factor Graph路径记录正确的metrics"""
        executor = IterationExecutor(config, mock_llm_client)
        result = executor._execute_generation("factor_graph", iteration_num=1)

        assert result["generation_metadata"]["method"] == "factor_graph"
```

**覆盖率目标**: Phase 1修改的328-409行代码 → **100%行覆盖率**

---

#### Staging环境验证 (1小时)

**验证脚本**: `experiments/run_stage1_baseline.py`

```bash
# 运行Stage 1实验（Factor Graph基线）
python experiments/run_stage1_baseline.py

# 预期输出
# ✅ 10次迭代全部使用Factor Graph
# ✅ 成功率 ≥ 70%
# ✅ 日志中无Silent Fallback警告
```

**验证检查点**:
```python
# 检查生成日志
assert all(log["generation_metadata"]["method"] == "factor_graph" for log in results)

# 检查成功率
success_rate = sum(1 for r in results if r["success"]) / len(results)
assert success_rate >= 0.70

# 检查无fallback
assert "falling back" not in combined_logs.lower()
```

---

### 验收标准

Phase 1完成需满足以下条件：

- [ ] **单元测试覆盖率 ≥ 100%**
  - `_decide_generation_method()` 所有分支测试通过
  - Silent Fallback移除验证通过
  - Generation Metrics记录验证通过

- [ ] **Stage 1实验Staging环境70%成功率**
  - 运行10次迭代
  - 成功率在65%-75%范围内
  - 100%使用Factor Graph（验证use_factor_graph=true生效）

- [ ] **日志显示0次Silent Fallback**
  - 搜索日志文件不包含"falling back"关键字
  - 所有错误都显式抛出异常
  - 审计日志记录所有generation决策

- [ ] **代码审查通过**
  - 2名开发工程师code review
  - 无遗留TODO或FIXME
  - 符合项目代码规范

---

### 回滚计划

**触发条件**: Staging实验成功率 < 65%

**回滚步骤**:
```bash
# 1. Git回滚
git revert HEAD

# 2. 重新部署Staging环境
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml up -d --force-recreate

# 3. 验证回滚成功
python experiments/run_stage1_baseline.py
# 预期：恢复到70%基线
```

**RTO (Recovery Time Objective)**: 10分钟

---

## Phase 2: 配置验证（Week 1, Day 3-5）

### 目标

- 建立Pydantic配置验证机制
- 防止未来配置冲突
- 确保所有配置文件兼容性
- 启动时自动检测配置错误

### 代码修改任务

#### Task 2.1: 创建Pydantic配置模型 (6小时)

**新文件**: `src/config/learning_config.py`

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any

class LLMConfig(BaseModel):
    """LLM相关配置"""
    enabled: bool = Field(default=False, description="是否启用LLM功能")
    use_factor_graph: Optional[bool] = Field(
        default=None,
        description=(
            "策略生成方法控制标志。\n"
            "- true: 强制使用Factor Graph（Stage 1基线实验）\n"
            "- false: 强制使用LLM（Stage 2 LLM验证实验）\n"
            "- null: 按innovation_rate概率混合（生产环境）"
        )
    )
    innovation_rate: float = Field(
        default=30.0,
        ge=0.0,
        le=100.0,
        description="LLM创新比例（仅在use_factor_graph=null时生效）"
    )

    @validator("use_factor_graph")
    def validate_llm_requirement(cls, v, values):
        """验证use_factor_graph=false时LLM必须启用"""
        if v is False and not values.get("enabled", False):
            raise ValueError(
                "Configuration conflict: use_factor_graph=false requires llm.enabled=true. "
                "Cannot force LLM generation when LLM is disabled. "
                "Fix: Either set llm.enabled=true or set use_factor_graph=true/null."
            )
        return v

    class Config:
        extra = "forbid"  # 禁止未定义的字段

class LearningLoopConfig(BaseModel):
    """学习循环配置"""
    max_iterations: int = Field(default=50, ge=1, le=1000)
    success_threshold: float = Field(default=0.70, ge=0.0, le=1.0)

    class Config:
        extra = "forbid"

class LearningConfig(BaseModel):
    """完整学习系统配置"""
    llm: LLMConfig = Field(default_factory=LLMConfig)
    learning_loop: LearningLoopConfig = Field(default_factory=LearningLoopConfig)

    @validator("llm")
    def validate_stage_configs(cls, v):
        """验证Stage实验配置的一致性"""
        # Stage 1验证: use_factor_graph=true 不应启用LLM
        if v.use_factor_graph is True and v.enabled is True:
            import warnings
            warnings.warn(
                "Stage 1 configuration detected: use_factor_graph=true with llm.enabled=true. "
                "LLM is enabled but will not be used. Consider setting llm.enabled=false for clarity."
            )

        # Stage 2验证: 已在LLMConfig.validate_llm_requirement()中处理

        return v

    class Config:
        extra = "allow"  # 允许其他配置字段（如monitoring, data等）
```

---

#### Task 2.2: 集成配置加载验证 (4小时)

**修改文件**: `src/config/config_loader.py`

```python
import yaml
from pathlib import Path
from typing import Dict, Any
from .learning_config import LearningConfig

def load_learning_config(config_path: str | Path) -> LearningConfig:
    """
    加载并验证学习系统配置

    Args:
        config_path: YAML配置文件路径

    Returns:
        验证后的LearningConfig对象

    Raises:
        ValidationError: 配置验证失败
        FileNotFoundError: 配置文件不存在
        yaml.YAMLError: YAML格式错误
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    # 加载YAML
    with open(config_path, 'r', encoding='utf-8') as f:
        raw_config = yaml.safe_load(f)

    # Pydantic验证（自动触发所有validators）
    try:
        validated_config = LearningConfig(**raw_config)
        return validated_config
    except ValidationError as e:
        # 美化错误信息
        error_msg = f"Configuration validation failed for {config_path}:\n"
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            error_msg += f"  - {field}: {error['msg']}\n"
        raise ValueError(error_msg) from e

def load_raw_config(config_path: str | Path) -> Dict[str, Any]:
    """加载原始配置字典（向后兼容，不验证）"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
```

**更新使用方**:
```python
# src/learning/learning_loop.py
from src.config.config_loader import load_learning_config

class LearningLoop:
    def __init__(self, config_path: str):
        # 旧代码
        # self.config = yaml.safe_load(open(config_path))

        # 新代码（自动验证）
        self.validated_config = load_learning_config(config_path)
        self.config = self.validated_config.dict()  # 转回字典供旧代码使用
```

---

#### Task 2.3: 配置文件兼容性修复 (4小时)

**验证脚本**: `scripts/validate_all_configs.py`

```python
#!/usr/bin/env python3
"""验证所有配置文件的Pydantic兼容性"""

import sys
from pathlib import Path
from src.config.config_loader import load_learning_config
from pydantic import ValidationError

def validate_all_configs():
    """验证项目中所有YAML配置文件"""
    project_root = Path(__file__).parent.parent
    config_files = [
        # 主配置文件
        project_root / "config" / "learning_system.yaml",

        # 实验配置文件
        *project_root.glob("experiments/**/*.yaml"),
    ]

    results = {"passed": [], "failed": []}

    for config_file in config_files:
        try:
            load_learning_config(config_file)
            results["passed"].append(str(config_file))
            print(f"✅ {config_file.relative_to(project_root)}")
        except ValidationError as e:
            results["failed"].append((str(config_file), str(e)))
            print(f"❌ {config_file.relative_to(project_root)}")
            print(f"   Error: {e}\n")

    # 输出摘要
    print(f"\n{'='*60}")
    print(f"Total: {len(config_files)} configs")
    print(f"Passed: {len(results['passed'])}")
    print(f"Failed: {len(results['failed'])}")

    if results['failed']:
        print(f"\nFailed configs require fixes:")
        for config_path, error in results['failed']:
            print(f"  - {config_path}")
        sys.exit(1)
    else:
        print(f"\n✅ All configs validated successfully!")
        sys.exit(0)

if __name__ == "__main__":
    validate_all_configs()
```

**运行验证**:
```bash
python scripts/validate_all_configs.py
```

**修复不兼容配置**（如果有）:
```yaml
# 例如修复 config/learning_system.yaml
llm:
  enabled: true  # 确保与use_factor_graph一致
  use_factor_graph: null  # 生产环境混合模式
  innovation_rate: 30
```

---

### 测试任务

#### 集成测试 (3小时)

**文件**: `tests/integration/config/test_learning_config_validation.py`

**T2.1: Pydantic配置验证测试**:
```python
class TestLearningConfigValidation:
    def test_use_factor_graph_false_requires_llm_enabled(self):
        """use_factor_graph=false时必须LLM启用"""
        invalid_config = {
            "llm": {"enabled": False, "use_factor_graph": False}
        }
        with pytest.raises(ValidationError, match="use_factor_graph=false requires llm.enabled=true"):
            LearningConfig(**invalid_config)

    def test_innovation_rate_validation(self):
        """innovation_rate必须在0-100范围内"""
        invalid_config = {"llm": {"innovation_rate": 150}}
        with pytest.raises(ValidationError, match="innovation_rate must be 0-100"):
            LearningConfig(**invalid_config)

    def test_config_file_loading_validation(self):
        """从YAML加载配置文件时自动验证"""
        config_path = "config/learning_system.yaml"
        config = load_learning_config(config_path)  # 应自动触发Pydantic验证
        assert isinstance(config, LearningConfig)
```

**T2.2: 配置冲突检测测试**:
```python
class TestConfigConflictDetection:
    def test_stage1_config_valid(self):
        """Stage 1配置（use_factor_graph=true）必须有效"""
        stage1_config = load_learning_config("experiments/stage1_baseline.yaml")
        assert stage1_config.llm.use_factor_graph is True

    def test_stage2_config_valid(self):
        """Stage 2配置（use_factor_graph=false + LLM enabled）必须有效"""
        stage2_config = load_learning_config("experiments/stage2_llm_validation.yaml")
        assert stage2_config.llm.use_factor_graph is False
        assert stage2_config.llm.enabled is True
```

**测试数据**: 创建 `tests/fixtures/configs/`:
- `valid_stage1.yaml` (use_factor_graph=true)
- `valid_stage2.yaml` (use_factor_graph=false, enabled=true)
- `invalid_conflict.yaml` (use_factor_graph=false, enabled=false) - 应触发ValidationError

---

#### 配置文件全量验证 (2小时)

**验证所有配置文件**:
```bash
# 验证所有config/*.yaml
python scripts/validate_all_configs.py

# 验证所有experiments/**/*.yaml
find experiments -name "*.yaml" -exec python -c "
from src.config.config_loader import load_learning_config
load_learning_config('{}')
print('✅ {}')
" \;
```

---

### 验收标准

Phase 2完成需满足以下条件：

- [ ] **Pydantic验证测试100%通过**
  - T2.1-T2.2所有测试用例通过
  - 配置冲突正确检测并抛出ValidationError
  - 边界值测试通过（innovation_rate 0-100）

- [ ] **所有配置文件加载无ValidationError**
  - `scripts/validate_all_configs.py` 零失败
  - 主配置文件 `config/learning_system.yaml` 验证通过
  - 所有实验配置文件验证通过

- [ ] **冲突配置正确抛出异常**
  - `use_factor_graph=false` + `enabled=false` → ValidationError
  - `innovation_rate=150` → ValidationError
  - 错误信息清晰，包含修复建议

- [ ] **向后兼容性保持**
  - 旧代码仍可使用 `config.dict()` 获取字典
  - 现有功能无破坏性变更
  - 可选启用验证（通过load函数选择）

---

### 回滚计划

**触发条件**: 生产配置文件验证失败

**回滚步骤**:
```python
# 临时禁用Pydantic验证
def load_learning_config(config_path: str | Path) -> Dict[str, Any]:
    # 回退到原YAML加载逻辑
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
```

**RTO (Recovery Time Objective)**: 5分钟

---

## Phase 3: Strategy Pattern重构（Week 2, Day 1-5）

### 目标

- 应用Strategy Pattern解耦生成逻辑
- 提升代码可维护性和可测试性
- 为未来新策略（如多LLM支持）打好基础
- 确保Stage 2实验成功率>80%

### 代码修改任务

#### Task 3.1: 创建策略接口 (4小时)

**新文件**: `src/generation/strategy.py`

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class GenerationStrategy(ABC):
    """策略生成接口"""

    @abstractmethod
    def generate(self, feedback: str, iteration: int) -> Dict[str, Any]:
        """
        生成交易策略

        Args:
            feedback: 来自回测的反馈信息
            iteration: 当前迭代次数

        Returns:
            包含策略内容的字典
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查该策略是否可用

        Returns:
            True 如果策略可用，否则 False
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        获取策略名称

        Returns:
            策略名称字符串
        """
        pass
```

---

#### Task 3.2: 实现LLM策略 (8小时)

**新文件**: `src/generation/llm_strategy.py`

```python
from .strategy import GenerationStrategy
from src.llm.openai_client import OpenAIClient
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class LLMGenerationStrategy(GenerationStrategy):
    """基于LLM的策略生成"""

    def __init__(self, llm_client: OpenAIClient, config: Dict[str, Any]):
        self.llm_client = llm_client
        self.config = config

    def generate(self, feedback: str, iteration: int) -> Dict[str, Any]:
        """使用LLM生成策略"""
        if not self.is_available():
            raise RuntimeError(
                "LLM strategy not available. "
                "Check LLM client enabled status before calling generate()."
            )

        # 构建prompt
        prompt = self._build_prompt(feedback, iteration)

        # 调用LLM
        try:
            response = self.llm_client.generate(prompt)
            strategy = self._parse_response(response)

            logger.info(f"LLM strategy generated successfully (iteration {iteration})")
            return strategy

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise  # 向上传播，不fallback

    def is_available(self) -> bool:
        """检查LLM客户端是否可用"""
        return self.llm_client.is_enabled()

    def get_name(self) -> str:
        return "LLMGenerationStrategy"

    def _build_prompt(self, feedback: str, iteration: int) -> str:
        """构建LLM prompt"""
        # ... prompt构建逻辑 ...
        pass

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        # ... 解析逻辑 ...
        pass
```

---

#### Task 3.3: 实现Factor Graph策略 (6小时)

**新文件**: `src/generation/factor_graph_strategy.py`

```python
from .strategy import GenerationStrategy
from src.factor_graph.template_engine import TemplateEngine
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class FactorGraphGenerationStrategy(GenerationStrategy):
    """基于Factor Graph的策略生成"""

    def __init__(self, template_engine: TemplateEngine, config: Dict[str, Any]):
        self.template_engine = template_engine
        self.config = config

    def generate(self, feedback: str, iteration: int) -> Dict[str, Any]:
        """使用Factor Graph生成策略"""
        if not self.is_available():
            raise RuntimeError(
                "Factor Graph strategy not available. "
                "Check template engine status before calling generate()."
            )

        # 从template生成策略
        try:
            strategy = self.template_engine.generate_from_template(
                feedback=feedback,
                iteration=iteration
            )

            logger.info(f"Factor Graph strategy generated successfully (iteration {iteration})")
            return strategy

        except Exception as e:
            logger.error(f"Factor Graph generation failed: {e}")
            raise  # 向上传播，不fallback

    def is_available(self) -> bool:
        """检查template engine是否可用"""
        return self.template_engine.is_ready()

    def get_name(self) -> str:
        return "FactorGraphGenerationStrategy"
```

---

#### Task 3.4: 重构IterationExecutor (8小时)

**修改文件**: `src/learning/iteration_executor.py`

```python
from src.generation.strategy import GenerationStrategy
from src.generation.llm_strategy import LLMGenerationStrategy
from src.generation.factor_graph_strategy import FactorGraphGenerationStrategy

class IterationExecutor:
    def __init__(self, config: Dict[str, Any], llm_client: OpenAIClient):
        self.config = config
        self.llm_client = llm_client

        # 初始化策略
        self.strategies: Dict[str, GenerationStrategy] = {
            "llm": LLMGenerationStrategy(llm_client, config),
            "factor_graph": FactorGraphGenerationStrategy(template_engine, config),
        }

    def _execute_generation(self, method: str, iteration_num: int, feedback: str = "") -> Dict[str, Any]:
        """
        使用策略模式执行生成

        Args:
            method: "llm" 或 "factor_graph"
            iteration_num: 迭代次数
            feedback: 反馈信息

        Returns:
            包含策略和元数据的字典
        """
        start_time = time.time()

        # 获取策略
        strategy = self.strategies.get(method)
        if strategy is None:
            raise ValueError(f"Unknown generation method: {method}")

        # 检查可用性
        if not strategy.is_available():
            raise RuntimeError(
                f"{strategy.get_name()} not available. "
                f"Cannot execute generation with method={method}."
            )

        # 执行生成
        try:
            result = strategy.generate(feedback, iteration_num)

            # 添加元数据
            result["generation_metadata"] = {
                "method": method,
                "strategy": strategy.get_name(),
                "iteration": iteration_num,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": time.time() - start_time,
                "use_factor_graph": self.config.get("use_factor_graph"),
                "innovation_rate": self.config.get("innovation_rate"),
            }

            logger.info(
                f"Generation completed: strategy={strategy.get_name()}, "
                f"iteration={iteration_num}, "
                f"duration={result['generation_metadata']['duration_seconds']:.2f}s"
            )

            return result

        except Exception as e:
            logger.error(
                f"Generation failed: strategy={strategy.get_name()}, "
                f"iteration={iteration_num}, "
                f"error={str(e)}"
            )
            raise
```

**好处**:
- ✅ 单一职责：每个策略类只负责一种生成方法
- ✅ 开闭原则：新增策略无需修改现有代码
- ✅ 依赖注入：策略通过构造函数注入，易于测试
- ✅ 统一接口：所有策略遵循相同接口，易于替换

---

### 测试任务

#### E2E测试 (8小时)

**文件**: `tests/e2e/test_generation_strategies.py`

**T3.1: LLM Strategy隔离测试**:
```python
class TestLLMGenerationStrategy:
    def test_stage2_experiment_100_percent_llm(self):
        """Stage 2实验：100%使用LLM策略"""
        config = load_config("experiments/stage2_llm_validation.yaml")
        loop = LearningLoop(config)

        # 运行10次迭代
        results = loop.run_iterations(num_iterations=10)

        # 验证所有迭代都使用LLM
        for result in results:
            assert result["generation_metadata"]["method"] == "llm"
            assert result["generation_metadata"]["strategy"] == "LLMGenerationStrategy"

        # 验证成功率 > 80%（Stage 2目标）
        success_rate = calculate_success_rate(results)
        assert success_rate > 0.80, f"Stage 2 success rate {success_rate} below 80% target"
```

**T3.2: Factor Graph Strategy隔离测试**:
```python
class TestFactorGraphStrategy:
    def test_stage1_baseline_100_percent_factor_graph(self):
        """Stage 1实验：100%使用Factor Graph策略"""
        config = load_config("experiments/stage1_baseline.yaml")
        loop = LearningLoop(config)

        results = loop.run_iterations(num_iterations=10)

        for result in results:
            assert result["generation_metadata"]["method"] == "factor_graph"
            assert result["generation_metadata"]["strategy"] == "FactorGraphGenerationStrategy"

        # 验证70%基线
        success_rate = calculate_success_rate(results)
        assert success_rate >= 0.70, f"Stage 1 baseline {success_rate} below 70%"
```

**T3.3: 混合模式测试**:
```python
class TestMixedModeProduction:
    def test_production_mixed_mode_respects_innovation_rate(self):
        """生产环境：use_factor_graph=null，按innovation_rate=30混合"""
        config = load_config("config/learning_system.yaml")  # production config
        loop = LearningLoop(config)

        results = loop.run_iterations(num_iterations=100)

        # 验证约30%使用LLM
        llm_count = sum(1 for r in results if r["generation_metadata"]["method"] == "llm")
        assert 20 <= llm_count <= 40, f"LLM usage {llm_count}% not in 20-40% range"
```

**Mock策略**:
- LLM API调用使用 `responses` library mock OpenAI endpoints
- Factor Graph使用 `pytest-mock` mock内部逻辑
- 避免真实API调用以防quota超限

---

#### Staging Stage 2实验 (2小时)

**运行Stage 2实验**:
```bash
python experiments/run_stage2_llm_validation.py
```

**预期结果**:
- ✅ 10次迭代全部使用LLM
- ✅ 成功率 > 80%（解除部署阻塞）
- ✅ 日志显示LLMGenerationStrategy

**成功标准**:
```python
# 检查生成策略
assert all(log["generation_metadata"]["strategy"] == "LLMGenerationStrategy" for log in results)

# 检查成功率（关键指标）
success_rate = sum(1 for r in results if r["success"]) / len(results)
assert success_rate > 0.80, f"Stage 2 failed: success rate {success_rate} ≤ 80%"
```

---

### 部署任务

#### Canary部署(5%流量) (2小时)

**配置文件**: `k8s/canary-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-strategy-canary
  labels:
    app: llm-strategy
    version: phase3
spec:
  replicas: 1  # 5%流量（假设总共20个实例）
  selector:
    matchLabels:
      app: llm-strategy
      version: phase3
  template:
    metadata:
      labels:
        app: llm-strategy
        version: phase3
    spec:
      containers:
      - name: llm-strategy
        image: llm-strategy:phase3-canary
        env:
        - name: CONFIG_PATH
          value: "/config/learning_system.yaml"
```

**部署步骤**:
```bash
# 1. 构建Docker镜像
docker build -t llm-strategy:phase3-canary .

# 2. 部署Canary
kubectl apply -f k8s/canary-deployment.yaml

# 3. 验证Canary运行
kubectl get pods -l version=phase3

# 4. 检查日志
kubectl logs -l version=phase3 --tail=100
```

---

#### 监控24小时观察期

**Canary监控指标**:

| 指标 | 阈值 | 监控频率 |
|-----|------|---------|
| 成功率 | Canary vs Baseline差异 < 5% | 每5分钟 |
| P99延迟 | 增长 < 10% | 每5分钟 |
| 错误率 | < 0.1% | 每1分钟 |
| Fallback率 | 0% (因为已移除) | 每1分钟 |

**监控脚本**: `scripts/monitor_canary.sh`

```bash
#!/bin/bash
# 监控Canary部署健康状况

while true; do
    # 检查错误率
    ERROR_RATE=$(kubectl logs -l version=phase3 --tail=1000 | grep "ERROR" | wc -l)

    if [ $ERROR_RATE -gt 10 ]; then
        echo "⚠️  High error rate detected: $ERROR_RATE errors in last 1000 logs"
        echo "Consider rollback!"
    fi

    # 检查成功率
    SUCCESS_RATE=$(curl -s http://canary-metrics:8000/metrics | grep "success_rate" | awk '{print $2}')

    echo "Canary success rate: $SUCCESS_RATE"

    sleep 300  # 每5分钟检查一次
done
```

---

### 验收标准

Phase 3完成需满足以下条件：

- [ ] **E2E测试覆盖3种模式**
  - LLM-only模式测试通过（T3.1）
  - Factor Graph-only模式测试通过（T3.2）
  - 混合模式测试通过（T3.3）
  - 所有测试100%通过率

- [ ] **Stage 2实验成功率 > 80%**
  - Staging环境运行10次迭代
  - 成功率稳定在80%-90%范围
  - 100%使用LLMGenerationStrategy
  - 解除部署阻塞（关键里程碑）

- [ ] **Canary 24小时无异常**
  - 错误率 < 0.1%
  - 成功率与baseline差异 < 5%
  - P99延迟增长 < 10%
  - 无Silent Fallback事件

- [ ] **代码质量**
  - 策略模式正确实现（符合SOLID原则）
  - 单元测试覆盖率 ≥ 90%
  - 代码审查通过（2名工程师）

---

### 回滚计划

**触发条件**:
- Canary错误率 > 0.5%
- P99延迟增长 > 20%
- 成功率下降 > 10%

**自动回滚步骤**:
```bash
# Kubernetes自动rollback
kubectl rollout undo deployment/llm-strategy-canary

# 立即切换流量回稳定版本
kubectl delete deployment/llm-strategy-canary

# 验证回滚成功
kubectl get deployments
# 应只看到llm-strategy-main运行
```

**RTO (Recovery Time Objective)**: 2分钟（Kubernetes自动rollback）

---

## Phase 4: 可观测性（Week 3, Day 1-5）

### 目标

- 部署Prometheus + Grafana监控体系
- 建立审计日志系统
- 实时监控generation决策过程
- 为生产环境长期运营打好基础

### 基础设施任务

#### Task 4.1: 部署Prometheus (4小时)

**配置文件**: `k8s/prometheus.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s

    scrape_configs:
      - job_name: 'llm-strategy'
        static_configs:
          - targets: ['llm-strategy:8000']
        metrics_path: '/metrics'
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:v2.40.0
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: config
          mountPath: /etc/prometheus
      volumes:
      - name: config
        configMap:
          name: prometheus-config
```

**告警规则**: `prometheus/alerts.yml`

```yaml
groups:
- name: llm_strategy_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(generation_errors_total[5m]) > 0.01
    for: 5m
    annotations:
      summary: "Generation error rate > 1%"
      description: "Error rate {{ $value }} exceeds threshold"

  - alert: SuccessRateDrop
    expr: rate(generation_success_total[1h]) < 0.65
    for: 15m
    annotations:
      summary: "Success rate dropped below 65%"
      description: "Current success rate {{ $value }}"

  - alert: UnexpectedFallback
    expr: increase(silent_fallback_total[5m]) > 0
    for: 1m
    annotations:
      summary: "Silent fallback detected (should be 0)"
      description: "Fallback count {{ $value }} indicates regression"
```

**部署Prometheus**:
```bash
kubectl apply -f k8s/prometheus.yaml
kubectl apply -f prometheus/alerts.yml

# 验证Prometheus运行
kubectl port-forward svc/prometheus 9090:9090
# 访问 http://localhost:9090
```

---

#### Task 4.2: 部署Grafana (4小时)

**配置文件**: `k8s/grafana.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:9.3.0
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          value: "admin"  # 生产环境使用Secret
```

**Dashboard配置**: `grafana/llm_strategy_dashboard.json`

```json
{
  "dashboard": {
    "title": "LLM Strategy Generation Monitoring",
    "panels": [
      {
        "title": "Generation Method Distribution",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum by (method) (generation_method_total)"
          }
        ]
      },
      {
        "title": "Success Rate Trend",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(generation_success_total{method=\"llm\"}[5m])",
            "legendFormat": "LLM Success Rate"
          },
          {
            "expr": "rate(generation_success_total{method=\"factor_graph\"}[5m])",
            "legendFormat": "Factor Graph Success Rate"
          }
        ]
      },
      {
        "title": "P50/P95/P99 Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(generation_duration_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(generation_duration_seconds_bucket[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(generation_duration_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ]
      },
      {
        "title": "Error Rate and Fallback Events",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(generation_errors_total[5m])",
            "legendFormat": "Error Rate"
          },
          {
            "expr": "rate(silent_fallback_total[5m])",
            "legendFormat": "Silent Fallback (should be 0)"
          }
        ]
      },
      {
        "title": "Innovation Rate: Actual vs Configured",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(generation_method_total{method=\"llm\"}[1h]) / (rate(generation_method_total{method=\"llm\"}[1h]) + rate(generation_method_total{method=\"factor_graph\"}[1h]))",
            "legendFormat": "Actual LLM Usage %"
          }
        ]
      }
    ]
  }
}
```

**部署Grafana**:
```bash
kubectl apply -f k8s/grafana.yaml

# 导入Dashboard
kubectl port-forward svc/grafana 3000:3000
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana/llm_strategy_dashboard.json

# 访问 http://localhost:3000
```

---

#### Task 4.3: 配置审计日志 (3小时)

**配置文件**: `logging/audit_config.yaml`

```yaml
version: 1
formatters:
  audit:
    format: '%(asctime)s - AUDIT - %(name)s - %(levelname)s - %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'

handlers:
  audit_file:
    class: logging.handlers.RotatingFileHandler
    filename: /var/log/llm_strategy/audit.log
    maxBytes: 10485760  # 10MB
    backupCount: 30
    formatter: audit

  console:
    class: logging.StreamHandler
    formatter: audit

loggers:
  audit:
    level: INFO
    handlers: [audit_file, console]
    propagate: false
```

**审计日志结构**:
```python
# src/logging/audit_logger.py
import logging
import json
from datetime import datetime

audit_logger = logging.getLogger('audit')

def log_generation_decision(
    method: str,
    use_factor_graph: bool | None,
    innovation_rate: float,
    llm_enabled: bool,
    iteration: int
):
    """记录generation决策到审计日志"""
    audit_event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "generation_decision",
        "method": method,
        "use_factor_graph": use_factor_graph,
        "innovation_rate": innovation_rate,
        "llm_enabled": llm_enabled,
        "iteration": iteration,
    }
    audit_logger.info(json.dumps(audit_event))

def log_generation_result(
    method: str,
    iteration: int,
    success: bool,
    duration: float,
    error: str | None = None
):
    """记录generation结果到审计日志"""
    audit_event = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "generation_result",
        "method": method,
        "iteration": iteration,
        "success": success,
        "duration_seconds": duration,
        "error": error,
    }
    audit_logger.info(json.dumps(audit_event))
```

---

### 代码修改任务

#### Task 4.4: 添加Prometheus Metrics (6小时)

**修改文件**: `src/learning/iteration_executor.py`

```python
from prometheus_client import Counter, Histogram, Gauge

# 定义Metrics
generation_method_counter = Counter(
    'generation_method_total',
    'Total number of generations by method',
    ['method', 'status']  # labels: method=llm/factor_graph, status=success/failure
)

generation_duration_histogram = Histogram(
    'generation_duration_seconds',
    'Generation duration in seconds',
    ['method'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

innovation_rate_gauge = Gauge(
    'innovation_rate_configured',
    'Configured innovation rate percentage'
)

silent_fallback_counter = Counter(
    'silent_fallback_total',
    'Number of silent fallback events (should be 0)'
)

class IterationExecutor:
    def _execute_generation(self, method: str, iteration_num: int, feedback: str = "") -> Dict[str, Any]:
        """执行生成并记录Prometheus metrics"""
        start_time = time.time()

        # 记录配置的innovation_rate
        innovation_rate_gauge.set(self.config.get("innovation_rate", 30))

        try:
            # 执行生成
            strategy = self.strategies[method]
            result = strategy.generate(feedback, iteration_num)

            # 记录成功
            duration = time.time() - start_time
            generation_method_counter.labels(method=method, status='success').inc()
            generation_duration_histogram.labels(method=method).observe(duration)

            # 添加元数据
            result["generation_metadata"] = {
                "method": method,
                "strategy": strategy.get_name(),
                "iteration": iteration_num,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": duration,
                "use_factor_graph": self.config.get("use_factor_graph"),
                "innovation_rate": self.config.get("innovation_rate"),
            }

            return result

        except Exception as e:
            # 记录失败
            generation_method_counter.labels(method=method, status='failure').inc()
            raise
```

**暴露Metrics端点**:
```python
# src/api/metrics_server.py
from flask import Flask
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app = Flask(__name__)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
```

---

#### Task 4.5: 增强审计日志 (4小时)

**修改文件**: `src/learning/iteration_executor.py`

```python
from src.logging.audit_logger import log_generation_decision, log_generation_result

class IterationExecutor:
    def _decide_generation_method(self) -> str:
        """决定生成方法（增强审计日志）"""
        use_factor_graph = self.config.get("use_factor_graph")
        innovation_rate = self.config.get("innovation_rate", 30)
        llm_enabled = self.llm_client.is_enabled()

        # ... 决策逻辑（与Phase 1相同）...

        method = # ... 决策结果 ...

        # 记录审计日志
        log_generation_decision(
            method=method,
            use_factor_graph=use_factor_graph,
            innovation_rate=innovation_rate,
            llm_enabled=llm_enabled,
            iteration=iteration_num
        )

        return method

    def _execute_generation(self, method: str, iteration_num: int, feedback: str = "") -> Dict[str, Any]:
        """执行生成（增强审计日志）"""
        start_time = time.time()

        try:
            result = # ... 执行生成 ...

            # 记录成功结果
            log_generation_result(
                method=method,
                iteration=iteration_num,
                success=True,
                duration=time.time() - start_time
            )

            return result

        except Exception as e:
            # 记录失败结果
            log_generation_result(
                method=method,
                iteration=iteration_num,
                success=False,
                duration=time.time() - start_time,
                error=str(e)
            )
            raise
```

**审计日志示例输出**:
```json
{"timestamp": "2025-11-11T10:30:15", "event_type": "generation_decision", "method": "llm", "use_factor_graph": false, "innovation_rate": 100, "llm_enabled": true, "iteration": 1}
{"timestamp": "2025-11-11T10:30:18", "event_type": "generation_result", "method": "llm", "iteration": 1, "success": true, "duration_seconds": 2.35, "error": null}
```

---

### 部署任务

#### Canary扩展到20% → 50% → 100%

**Week 3 Day 3: Canary 20%**:
```bash
# 扩展到3个replicas（20%流量）
kubectl scale deployment/llm-strategy-canary --replicas=3

# 等待24小时观察
# 监控指标：错误率、成功率、延迟
```

**Week 3 Day 4: Canary 50%**:
```bash
# 扩展到7个replicas（50%流量）
kubectl scale deployment/llm-strategy-canary --replicas=7

# 等待24小时观察
```

**Week 3 Day 5: Production-Full 100%**:
```bash
# 删除旧的main deployment
kubectl delete deployment/llm-strategy-main

# 部署新版本为main
kubectl apply -f k8s/production-deployment.yaml

# 验证100%流量切换
kubectl get deployments
# 应只看到llm-strategy-production运行
```

---

### 验收标准

Phase 4完成需满足以下条件：

- [ ] **Grafana仪表板实时显示**
  - 5个Panel全部正常显示
  - Generation Method分布正确（约30% LLM）
  - 成功率趋势图稳定在70%以上
  - P99延迟 < 10秒
  - Innovation Rate实际值与配置值匹配

- [ ] **告警规则测试通过**
  - 手动触发错误率告警（验证告警系统工作）
  - 手动触发成功率下降告警
  - UnexpectedFallback告警保持0次触发

- [ ] **审计日志完整记录**
  - 每次generation都有decision和result日志
  - 日志格式为JSON可解析
  - 日志文件自动轮转（每10MB）
  - 保留30天历史日志

- [ ] **生产环境7天无故障**
  - 错误率 < 0.1%
  - 成功率 ≥ 70%
  - 无Silent Fallback事件
  - 无Kubernetes pod重启

---

### 回滚计划

**触发条件**: 告警规则连续触发 > 3次

**回滚步骤**:
```bash
# 1. 重新部署Phase 3版本
kubectl apply -f k8s/phase3-deployment.yaml

# 2. 删除Phase 4版本
kubectl delete deployment/llm-strategy-production

# 3. 验证回滚成功
kubectl get deployments
kubectl logs -l version=phase3 --tail=100
```

**RTO (Recovery Time Objective)**: 5分钟

---

## 风险评估与缓解措施

| 风险类型 | 影响 | 概率 | 缓解措施 | 责任人 |
|---------|-----|------|---------|-------|
| Phase 1修改破坏现有逻辑 | 高 | 低 | 100%单元测试覆盖 + Staging验证 | 开发工程师 |
| Pydantic验证阻塞配置加载 | 中 | 中 | 临时禁用开关 + 配置文件预验证 | 开发工程师 |
| Strategy重构引入新bug | 高 | 中 | E2E测试 + Canary部署 + 24h监控 | QA工程师 |
| Prometheus/Grafana性能开销 | 低 | 低 | 采样率控制 + 指标聚合 | DevOps工程师 |
| Stage 2实验仍然失败 | 高 | 低 | 如失败则定位LLM本身问题，非架构问题 | 技术负责人 |
| Canary部署失败 | 高 | 低 | 自动回滚机制 + 24h观察期 | DevOps工程师 |
| 监控系统不稳定 | 中 | 低 | 独立部署 + 健康检查 | DevOps工程师 |

**总风险评分**: **中等**（可接受范围）

**风险缓解策略**:
1. **技术风险**: 通过分阶段部署和100%测试覆盖降低
2. **业务风险**: 通过Canary部署和快速回滚机制保护生产环境
3. **运维风险**: 通过监控告警和审计日志及早发现问题

---

## 项目启动检查表

### 开发环境准备
- [ ] Python 3.9+ 环境
- [ ] Docker + docker-compose
- [ ] pytest, pytest-cov, pytest-mock
- [ ] responses library (HTTP mock)
- [ ] Git access to repository

### 权限与访问
- [ ] GitHub/GitLab仓库写权限
- [ ] Staging环境部署权限
- [ ] Production Kubernetes集群访问
- [ ] OpenAI API密钥（用于测试）

### 基础设施
- [ ] Kubernetes集群(3 nodes, 16GB RAM each)
- [ ] Prometheus + Grafana服务器(4GB RAM, 50GB storage)
- [ ] CI/CD Pipeline配置

### 团队分工确认
- [ ] 开发工程师x2分配具体任务
- [ ] QA工程师测试计划确认
- [ ] DevOps工程师部署流程确认
- [ ] 技术负责人回滚决策流程确认

### 文档准备
- [ ] 阅读 `ARCHITECTURE_CONTRADICTIONS_ANALYSIS.md`
- [ ] 阅读 `VALIDATION_PLAN.md`
- [ ] 理解3种验证场景（Stage 1, Stage 2, Production）

---

## 立即执行的Next Actions（前3天）

### Day 1 - 开发环境搭建

```bash
# Action 1: 克隆仓库并创建feature分支
git clone <repository-url>
cd LLM-strategy-generator
git checkout -b fix/use-factor-graph-flag

# Action 2: 设置Python虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock responses

# Action 3: 运行现有测试套件（建立baseline）
pytest tests/ -v --cov=src --cov-report=html
# 记录当前覆盖率和失败测试

# Action 4: 阅读核心文件
# - src/learning/iteration_executor.py (lines 328-409)
# - config/learning_system.yaml
# - experiments/llm_learning_validation/config_llm_validation_test.yaml
```

### Day 2 - Phase 1 Task 1.1实现

```bash
# Action 1: 修改 _decide_generation_method()
# 打开 src/learning/iteration_executor.py line 328
# 实现上述Task 1.1中的代码逻辑

# Action 2: 编写单元测试
# 创建 tests/unit/learning/test_iteration_executor.py
# 实现T1.1测试用例

# Action 3: 本地测试验证
pytest tests/unit/learning/test_iteration_executor.py::TestDecideGenerationMethod -v

# Action 4: 提交代码
git add src/learning/iteration_executor.py tests/unit/learning/test_iteration_executor.py
git commit -m "fix: enforce use_factor_graph flag in _decide_generation_method()"
```

### Day 3 - Phase 1 Task 1.2-1.3实现

```bash
# Action 1: 移除Silent Fallback逻辑
# 修改 src/learning/iteration_executor.py lines 346-409

# Action 2: 添加Generation Metrics
# 实现 _execute_generation() 方法

# Action 3: 编写单元测试
# 实现T1.2-T1.3测试用例

# Action 4: 本地测试验证
pytest tests/unit/learning/test_iteration_executor.py -v --cov

# Action 5: 提交代码
git add .
git commit -m "fix: remove silent fallback and add generation metrics"
```

---

## 成功指标（KPIs）

### 技术指标
- [ ] **Stage 1实验成功率**: 维持70%基线
- [ ] **Stage 2实验成功率**: 从0% → >80%
- [ ] **单元测试覆盖率**: Phase 1修改代码100%
- [ ] **E2E测试通过率**: 100%
- [ ] **生产环境错误率**: <0.1%
- [ ] **Silent Fallback事件**: 0次

### 业务指标
- [ ] **A/B测试可信度**: 从0% → 100%
- [ ] **LLM性能验证**: 可独立评估
- [ ] **技术债务减少**: 70%
- [ ] **部署阻塞解除**: Stage 2可上线

### 时间指标
- [ ] **Phase 1完成**: Week 1 Day 2
- [ ] **Phase 2完成**: Week 1 Day 5
- [ ] **Phase 3完成**: Week 2 Day 5
- [ ] **Phase 4完成**: Week 3 Day 5
- [ ] **稳定性达成**: Week 4 Day 7

---

## 项目完成标志

**Phase 4验收后，以下条件全部满足则项目完成**:

1. ✅ 所有4个Phase的代码变更已合并到main分支
2. ✅ 生产环境100%流量运行新版本7天无故障
3. ✅ Stage 2实验成功率稳定在80%以上
4. ✅ Grafana仪表板显示正常监控指标
5. ✅ 审计日志完整记录所有generation决策
6. ✅ 技术负责人签署验收报告

### 项目交付物
- [ ] 修改后的源代码（约500行）
- [ ] 完整测试套件（单元、集成、E2E、回归）
- [ ] Prometheus + Grafana监控配置
- [ ] 部署文档和回滚手册
- [ ] 项目总结报告

---

## 后续优化建议（Phase 5+）

**不在本次范围，但值得考虑的改进**:

1. **性能优化**: LLM调用并行化（当前串行）
   - 批量生成策略
   - 异步API调用
   - 预期收益: 30% 性能提升

2. **缓存机制**: 相似策略LLM响应缓存
   - Redis缓存层
   - 语义相似度匹配
   - 预期收益: 50% API成本降低

3. **A/B测试平台**: 统一实验框架
   - 实验管理UI
   - 自动化A/B测试
   - 结果可视化分析

4. **自动化回滚**: 基于监控指标的自动回滚
   - 告警触发自动回滚
   - 无需人工干预
   - 预期RTO: < 1分钟

5. **多LLM支持**: 集成Claude、Gemini等其他模型
   - 多模型策略选择
   - 成本优化
   - 性能对比

---

## 附录

### A. 回滚决策矩阵

| 监控指标 | 阈值 | 回滚决策 | 责任人 | RTO |
|---------|------|---------|--------|-----|
| 错误率 > 1% | 持续5分钟 | 自动回滚 | Kubernetes | 2分钟 |
| 成功率 < 65% | 持续15分钟 | 手动回滚 | 运维团队 | 10分钟 |
| P99延迟 > 10s | 持续10分钟 | 人工审核 | 技术负责人 | 30分钟 |
| Silent Fallback > 0 | 单次触发 | 立即回滚 | 自动 | 2分钟 |
| Canary失败 | 24小时内 | 自动回滚 | Kubernetes | 2分钟 |

### B. 联系人清单

| 角色 | 姓名 | 联系方式 | 职责 |
|-----|------|---------|------|
| 技术负责人 | - | - | 总体技术决策、验收签署 |
| 开发工程师1 | - | - | Phase 1-2代码实现 |
| 开发工程师2 | - | - | Phase 3-4代码实现 |
| QA工程师 | - | - | 测试策略执行、质量把关 |
| DevOps工程师 | - | - | 部署和监控配置 |

### C. 相关文档

- [架构矛盾分析](./ARCHITECTURE_CONTRADICTIONS_ANALYSIS.md)
- [验证计划](./VALIDATION_PLAN.md)
- [产品需求](../.spec-workflow/steering/product.md)
- [技术规范](../.spec-workflow/steering/tech.md)

---

## 总结

本执行计划通过4个阶段，用3周时间系统性解决 `use_factor_graph` 标志被忽略的架构问题：

1. **Phase 1 (2天)**: 紧急修复核心逻辑，恢复A/B测试能力
2. **Phase 2 (3天)**: 建立配置验证机制，防止未来冲突
3. **Phase 3 (5天)**: Strategy Pattern重构，提升可维护性
4. **Phase 4 (5天)**: 建立可观测性，持续监控系统健康

**关键成功因素**:
- ✅ 分阶段部署降低风险
- ✅ 100%测试覆盖保证质量
- ✅ Canary部署策略保护生产环境
- ✅ 完整监控体系支撑持续运营

**立即开始**: 执行上述Next Actions，启动Phase 1开发。

---

**文档版本**: v1.0
**最后更新**: 2025-11-11
**审核状态**: 待审核
