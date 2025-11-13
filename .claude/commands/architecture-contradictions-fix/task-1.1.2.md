# architecture-contradictions-fix - Task 1.1.2

Execute task 1.1.2 for the architecture-contradictions-fix specification.

## Task Description
验证静默降级消除测试

## Usage
```
/Task:1.1.2-architecture-contradictions-fix
```

## Instructions

Execute with @spec-task-executor agent the following task: "验证静默降级消除测试"

```
Use the @spec-task-executor agent to implement task 1.1.2: "验证静默降级消除测试" for the architecture-contradictions-fix specification and include all the below context.

# Steering Context
## Steering Documents Context

No steering documents found.

# Specification Context
## Specification Context (Pre-loaded): architecture-contradictions-fix

### Requirements
# architecture-contradictions-fix - Requirements Document

修复LLM策略生成系统中7个架构矛盾，通过TDD驱动的4阶段渐进式重构，解决use_factor_graph配置标志被忽略导致的100%试点测试失败问题

## Introduction

本系统通过4周的渐进式TDD重构修复架构级设计与实现不一致问题，恢复实验系统的可信度，为Stage 2生产部署扫清障碍。

**核心问题**：`iteration_executor.py:328-344` 的决策逻辑完全忽略 `use_factor_graph` 配置标志，导致：
- 100%试点测试失败（所有配置被静默覆盖）
- 实验结果不可信（声称"LLM测试"实际运行"Factor Graph测试"）
- Stage 2部署被阻塞（无法验证LLM能否突破80% Sharpe Ratio基线）

**根本原因**：单个实现bug触发连锁反应，引发7个架构矛盾，技术债务评分8-9/10。

**价值主张**：3周重构（非完全重写）targeting ~500行代码，实现70%技术债务削减，低风险渐进部署。

## Alignment with Product Vision

本功能符合 `product.md` 原则：

1. **避免过度工程化**：
   - 使用标准Python工具（Pydantic, pytest, zen testgen）
   - 无自定义框架或复杂基础设施
   - 聚焦核心bug修复（80/20原则）
   - 项目原则："這是個專給我個人使用，交易週期為週/月的交易系統，請勿過度工程化"

2. **系统质量指标**：
   - 当前：Phase 8测试通过，但配置逻辑有bug
   - 目标：配置强制执行 + Pydantic验证 + Strategy Pattern重构

3. **自主学习系统可靠性**：
   - 当前Stage 1重构（2807行→8模块）引入集成风险
   - 目标：通过静态类型检查确保组件契约稳定
   - 支持长期自主运行无需人工干预

## Core Features

### Feature 1: 配置优先级强制执行（Phase 1）

**描述**：修复 `_decide_generation_method()` 忽略 `use_factor_graph` 标志的核心bug

**关键变更**：
```python
# Before (Lines 328-344)
def _decide_generation_method(self) -> bool:
    innovation_rate = self.config.get("innovation_rate", 100)
    use_llm = random.random() * 100 < innovation_rate
    return use_llm  # ❌ 完全忽略 use_factor_graph

# After (Phase 1)
def _decide_generation_method(self) -> bool:
    # ✅ 优先级：use_factor_graph > innovation_rate
    if self.config.get("use_factor_graph") is True:
        return False  # Force Factor Graph
    elif self.config.get("use_factor_graph") is False:
        return True   # Force LLM
    else:
        # Mixed mode fallback to innovation_rate
        innovation_rate = self.config.get("innovation_rate", 100)
        return random.random() * 100 < innovation_rate
```

**影响范围**：
- 文件：`src/learning/iteration_executor.py`
- 行数：Lines 328-344（核心决策逻辑）
- 依赖：无外部依赖变更

### Feature 2: 错误显式化（Phase 1）

**描述**：消除3个静默降级点，将fallback改为显式错误

**关键变更**：
```python
# Before (Lines 360-362, 366-368, 398-400, 406-409)
if not self.llm_client.is_enabled():
    logger.warning("Fallback")  # ❌ 静默降级
    return self._generate_with_factor_graph()

# After (Phase 1)
if not self.llm_client.is_enabled():
    raise ConfigurationError(  # ✅ 显式错误
        "LLM generation selected but LLM client is disabled. "
        "Set use_factor_graph=True or enable LLM client."
    )
```

**影响范围**：
- 文件：`src/learning/iteration_executor.py`
- 方法：`_generate_with_llm()` (Lines 346-409)
- 新增：`ConfigurationError`, `LLMGenerationError` 异常类

### Feature 3: Pydantic配置验证（Phase 2）

**描述**：使用Pydantic实现编译时配置验证，防止无效配置进入系统

**关键变更**：
```python
# 新增文件：src/learning/config_models.py
from pydantic import BaseModel, Field, model_validator

class GenerationConfig(BaseModel):
    use_factor_graph: Optional[bool] = None
    innovation_rate: Annotated[int, Field(ge=0, le=100)] = 100

    @model_validator(mode='after')
    def check_conflicts(self):
        if self.use_factor_graph is True and self.innovation_rate == 100:
            raise ValueError("配置冲突: use_factor_graph=True 与 innovation_rate=100 冲突")
        return self
```

**影响范围**：
- 新增：`src/learning/config_models.py`
- 修改：`iteration_executor.py.__init__()` 使用Pydantic验证
- 依赖：`pydantic >= 2.0.0`

### Feature 4: Strategy Pattern重构（Phase 3）

**描述**：解耦LLM和Factor Graph实现，符合开闭原则

**关键变更**：
```python
# 新增文件：src/learning/generation_strategies.py
class GenerationStrategy(ABC):
    @abstractmethod
    def generate(...) -> Tuple[str, Optional[str], Optional[int]]:
        pass

class LLMStrategy(GenerationStrategy):
    def generate(...):
        # LLM逻辑移至此处

class FactorGraphStrategy(GenerationStrategy):
    def generate(...):
        # Factor Graph逻辑移至此处

class StrategyFactory:
    @staticmethod
    def create_strategy(config: GenerationConfig) -> GenerationStrategy:
        if config.use_factor_graph is True:
            return FactorGraphStrategy()
        elif config.use_factor_graph is False:
            return LLMStrategy()
        else:
            return MixedStrategy()
```

**影响范围**：
- 新增：`src/learning/generation_strategies.py`
- 修改：`iteration_executor.py` 使用Strategy Pattern
- 删除：`_decide_generation_method()`, `_generate_with_llm()`, `_generate_with_factor_graph()`

### Feature 5: 审计追踪系统（Phase 4）

**描述**：引入审计日志，彻底消除静默状态覆盖

**关键变更**：
```python
# 新增文件：src/learning/audit_trail.py
@dataclass
class GenerationDecision:
    timestamp: datetime
    config_snapshot: dict
    intended_method: Literal["llm", "factor_graph", "mixed"]
    actual_method: str
    actual_code_hash: Optional[str]

class AuditLogger:
    def log_decision(self, decision: GenerationDecision):
        # 记录到JSONL文件

    def detect_violations(self) -> List[GenerationDecision]:
        # 检测静默覆盖
        return [d for d in self.decisions if d.is_silent_override()]
```

**影响范围**：
- 新增：`src/learning/audit_trail.py`
- 修改：`iteration_executor.py` 集成审计日志
- 输出：`generation_audit.jsonl` + HTML报告

## User Stories

### Story 1: 配置标志优先级修复（P0 - Critical）

**作为** LLM策略研究员
**我想要** `use_factor_graph` 配置标志被正确遵循
**这样** 我才能进行可信的对照实验

**验收标准**：
- [ ] WHEN `use_factor_graph=True` THEN 系统仅使用Factor Graph，无论`innovation_rate`值
- [ ] WHEN `use_factor_graph=False` THEN 系统仅使用LLM，无论`innovation_rate`值
- [ ] WHEN `use_factor_graph=None` THEN 系统使用混合模式，根据`innovation_rate`概率决策
- [ ] WHEN 配置冲突 THEN 系统在启动时抛出`ConfigurationError`，不是运行时静默降级

**理由**：这是触发7个架构矛盾的根本原因，修复后立即恢复50%实验可信度。

### Story 2: 静默降级消除（P0 - Critical）

**作为** 系统维护者
**我想要** 所有运行时错误都显式抛出
**这样** 我才能快速诊断问题，而不是调试神秘的静默降级

**验收标准**：
- [ ] WHEN LLM client disabled 且 `use_factor_graph=False` THEN 抛出`ConfigurationError`，不是fallback
- [ ] WHEN LLM engine unavailable THEN 抛出`LLMGenerationError`，不是fallback
- [ ] WHEN LLM returns empty code THEN 抛出`LLMGenerationError`，不是fallback
- [ ] WHEN LLM generation exception THEN 抛出带context的`LLMGenerationError`，不是捕获后fallback

**理由**：3个静默降级点是实验结果不可信的直接原因，每个都需要显式错误。

### Story 3: Pydantic配置验证（P1 - High）

**作为** 开发者
**我想要** 在系统启动时就发现配置错误
**这样** 我不需要等到运行时才发现问题

**验收标准**：
- [ ] WHEN `innovation_rate` 不在0-100范围 THEN Pydantic抛出`ValidationError`
- [ ] WHEN 配置冲突（如`use_factor_graph=True` + `innovation_rate=100`） THEN 抛出`ValidationError`
- [ ] WHEN 配置缺失必需字段 THEN 抛出`ValidationError`并提示缺失字段
- [ ] WHEN 配置类型错误 THEN Pydantic提供清晰的类型错误消息

**理由**：编译时验证比运行时捕获更早发现问题，减少调试时间。

### Story 4: Strategy Pattern重构（P1 - High）

**作为** 未来功能开发者
**我想要** 添加新生成策略（如HybridStrategy）时无需修改现有代码
**这样** 系统符合开闭原则，降低集成风险

**验收标准**：
- [ ] WHEN 添加新策略 THEN 仅需实现`GenerationStrategy`接口，无需修改`iteration_executor.py`
- [ ] WHEN 切换策略 THEN 通过配置即可，无需改代码
- [ ] WHEN 测试策略 THEN 可独立mock测试，无需依赖完整系统
- [ ] WHEN 查看代码 THEN `iteration_executor.py` 不包含if-else分支选择生成方法

**理由**：当前if-else实现违反开闭原则，Strategy Pattern使系统更可扩展。

### Story 5: 审计追踪系统（P2 - Medium）

**作为** 质量保证工程师
**我想要** 完整的生成决策审计日志
**这样** 我可以验证系统按预期配置运行，并快速诊断异常

**验收标准**：
- [ ] WHEN 每次生成 THEN 记录配置快照、决策方法、实际方法、代码hash
- [ ] WHEN 检测静默覆盖 THEN 自动标记violations（intended ≠ actual）
- [ ] WHEN 生成审计报告 THEN 输出HTML报告，可视化违规记录
- [ ] WHEN 查看日志 THEN JSONL格式便于机器解析和人工检查

**理由**：审计追踪是"验证配置被遵循"的最后防线，完全消除静默降级风险。

### Story 6: TDD测试先行（P1 - High）

**作为** 开发者
**我想要** 在实现前先有完整测试套件
**这样** 我可以确信重构不会破坏现有功能

**验收标准**：
- [ ] WHEN Phase 1开始 THEN 已有`test_iteration_executor_phase1.py`（15+ tests）
- [ ] WHEN Phase 2开始 THEN 已有`test_config_models.py`（20+ tests）
- [ ] WHEN Phase 3开始 THEN 已有`test_generation_strategies.py`（25+ tests）
- [ ] WHEN Phase 4开始 THEN 已有`test_audit_trail.py`（15+ tests）

**理由**：TDD确保重构安全，测试定义预期行为，代码实现满足测试。

### Story 7: CI/CD自动化（P1 - High）

**作为** 团队成员
**我想要** 每个Phase部署都自动化测试和验证
**这样** 我可以快速检测回归，安全回滚失败部署

**验收标准**：
- [ ] WHEN PR创建 THEN GitHub Actions自动运行mypy类型检查
- [ ] WHEN PR创建 THEN GitHub Actions自动运行E2E回归测试
- [ ] WHEN 测试失败 THEN PR被阻塞，无法合并到main
- [ ] WHEN CI完成 THEN <5分钟反馈，包含清晰错误消息

**理由**：自动化防止人为错误，<5分钟反馈循环加速开发迭代。

## Acceptance Criteria

### Phase 1: 紧急修复（Week 1）

- [ ] **配置优先级测试**：`test_generation_method_decision_priority()` 通过（5个参数化测试）
- [ ] **配置冲突检测**：`test_decide_generation_method_raises_on_conflict()` 通过
- [ ] **错误显式化测试**：4个fallback测试改为验证抛出异常，而非静默降级
- [ ] **回归测试**：现有926个单元测试仍然全部通过
- [ ] **试点测试**：`use_factor_graph=True/False/None` 三种配置的试点测试成功率达到100%

### Phase 2: Pydantic验证（Week 2）

- [ ] **类型验证测试**：`innovation_rate=-1/101` 抛出`ValidationError`
- [ ] **冲突检测测试**：`use_factor_graph=True` + `innovation_rate=100` 抛出`ValidationError`
- [ ] **向后兼容测试**：旧dict配置仍可通过`GenerationConfig.from_dict()`验证
- [ ] **错误消息测试**：中英文双语错误提示清晰可读
- [ ] **集成测试**：`IterationExecutor.__init__()` 使用Pydantic验证，拒绝无效配置

### Phase 3: Strategy Pattern（Week 3前半）

- [ ] **接口测试**：`LLMStrategy`, `FactorGraphStrategy`, `MixedStrategy` 实现`GenerationStrategy`接口
- [ ] **工厂模式测试**：`StrategyFactory.create_strategy()` 根据配置返回正确策略
- [ ] **行为等价测试**：新Strategy Pattern实现与旧if-else实现行为等价
- [ ] **可扩展性验证**：添加Mock新策略无需修改`iteration_executor.py`
- [ ] **代码简化验证**：`iteration_executor.py` 删除决策分支，行数减少>100行

### Phase 4: 审计追踪（Week 3后半）

- [ ] **决策日志测试**：每次生成记录到`generation_audit.jsonl`
- [ ] **违规检测测试**：`detect_violations()` 正确识别静默覆盖
- [ ] **报告生成测试**：`generate_html_report()` 输出包含violations表格的HTML
- [ ] **完整循环测试**：运行100次迭代，审计日志记录100条，violations=0
- [ ] **哈希验证测试**：代码hash匹配，防止生成代码被篡改

## Non-functional Requirements

### Code Architecture and Modularity

- **Single Responsibility Principle**：
  - `config_models.py`: 配置验证逻辑
  - `generation_strategies.py`: 策略实现
  - `audit_trail.py`: 审计日志
  - `iteration_executor.py`: 策略编排（不包含决策逻辑）

- **Modular Design**：
  - Phase 1-4 每阶段独立部署
  - 使用feature flags控制激活
  - 失败可快速回滚到上一稳定版本

- **Dependency Management**：
  - Phase 2: 新增`pydantic >= 2.0.0`（开发依赖）
  - Phase 1,3,4: 无新依赖
  - 防止循环导入：通过接口抽象解耦

- **Clear Interfaces**：
  - `GenerationStrategy` Protocol定义策略契约
  - `GenerationConfig` Pydantic模型定义配置契约
  - `AuditLogger` 定义审计接口

### Performance

- **类型检查速度**：mypy检查 `src/learning/` 模块应在<10秒完成
- **CI Pipeline速度**：总CI运行时间应<5分钟（包括mypy + pytest）
- **运行时影响**：
  - Pydantic验证仅在启动时执行（<1ms）
  - Strategy Pattern相比if-else无性能损失
  - 审计日志异步写入，不阻塞生成（<5ms overhead）
- **单次迭代耗时**：重构后单次迭代耗时 ≤ 基线值 × 1.1（允许10%性能损失）

### Security

- **配置验证安全**：Pydantic防止注入攻击（验证输入类型和范围）
- **审计日志安全**：JSONL文件权限限制，防止篡改
- **错误消息安全**：错误消息不暴露内部实现细节或敏感数据
- **依赖安全**：Pydantic 2.0.0+ 无已知CVE漏洞

### Reliability

- **向后兼容性**：
  - Phase 1: 100%向后兼容（仅修复bug，不改API）
  - Phase 2: 向后兼容（dict配置通过`from_dict()`仍可用）
  - Phase 3: 向后兼容（Strategy Pattern内部重构，外部API不变）
  - Phase 4: 向后兼容（审计日志为新增功能，不影响现有流程）

- **失败模式**：
  - Phase 1失败：回滚feature flag，系统恢复到旧逻辑
  - Phase 2失败：禁用Pydantic验证，使用dict配置
  - Phase 3失败：回滚Strategy Pattern，恢复if-else实现
  - Phase 4失败：禁用审计日志，核心功能不受影响

- **渐进部署**：
  - 每周独立部署一个Phase
  - 使用feature flags控制激活（`phase1_config_enforcement=true/false`）
  - 每个Phase部署后运行完整回归测试
  - Pilot test验证无回归后全量启用

### Usability

- **开发者体验**：
  - Pydantic提供清晰的验证错误消息（中英文）
  - IDE自动补全支持（VSCode, PyCharm识别类型）
  - 审计报告HTML可视化，便于人工检查

- **学习曲线**：
  - Pydantic是Python标准工具（成熟社区，文档完善）
  - Strategy Pattern是设计模式教科书内容
  - TDD是Python社区最佳实践

- **文档**：
  - 每个Phase包含详细设计文档和测试用例
  - 错误消息包含修复建议（如"Set use_factor_graph=True or enable LLM client"）
  - 审计报告自文档化（HTML表格显示violations）

## Success Criteria

### Week 1（Phase 1）达成标准

| 指标 | 目标 | 验证方法 |
|------|------|----------|
| 配置优先级遵循率 | 100% | Pilot test with use_factor_graph=True/False/None |
| 静默降级次数 | 0 | 代码审查 + 错误测试覆盖 |
| 单元测试通过率 | >95% (926/976) | pytest test_iteration_executor_phase1.py |
| 试点测试成功率 | 100% | 实际运行3种配置各10次迭代 |

### Week 2（Phase 2）达成标准

| 指标 | 目标 | 验证方法 |
|------|------|----------|
| Pydantic验证错误拦截率 | 100% | 测试20+无效配置，全部被拦截 |
| 配置迁移完成率 | >80% | 现有配置文件转换为Pydantic模型 |
| 向后兼容性 | 100% | 旧dict配置仍可通过from_dict()验证 |
| CI集成 | mypy 0 errors | GitHub Actions type-check job通过 |

### Week 3（Phase 3 + 4）达成标准

| 指标 | 目标 | 验证方法 |
|------|------|----------|
| Strategy Pattern覆盖率 | 100% | 所有生成路径使用Strategy |
| 代码行数削减 | >100行 | iteration_executor.py删除决策分支 |
| 审计追踪完整性 | 100% | 100次迭代=100条审计记录 |
| 静默覆盖检测 | 0 violations | detect_violations()返回空列表 |
| 技术债务分数 | ≤4/10 | 从当前8-9/10降至3-4/10 |

### 最终验收标准（Week 3结束）

- [ ] **Zero Configuration Violations**: 配置标志遵循率=100%
- [ ] **Zero Silent Fallbacks**: 静默降级次数=0（所有错误显式抛出）
- [ ] **100% Audit Coverage**: 审计日志覆盖所有生成决策
- [ ] **CI Automation**: GitHub Actions在每个PR上运行type check + E2E tests
- [ ] **<5 Minutes Feedback**: CI总运行时间<5分钟
- [ ] **Technical Debt Reduction**: 技术债务评分从8-9/10降至3-4/10（约70%改善）

## Out of Scope

以下内容明确**不包含**在本spec中：

1. **完全重写**：仅重构 `iteration_executor.py`（~500行），不改其他模块
2. **LLM模板修复**：假设LLM客户端和模板正常工作，本spec不修复LLM生成质量问题
3. **100%类型覆盖**：仅添加关键API的类型提示（80/20原则）
4. **Pre-commit Hooks**：保持开发工作流简单（避免摩擦）
5. **性能优化**：重构目标是正确性，不是性能（允许10%性能损失）
6. **UI/Dashboard**：审计报告仅HTML，无交互式Dashboard

## Dependencies and Assumptions

**依赖**：
- Python 3.10+（当前项目要求）
- Pydantic ≥2.0.0（Phase 2新增，成熟稳定）
- pytest ≥8.4.0（已在 `requirements-dev.txt`）
- mypy ≥1.18.0（已在 `requirements-dev.txt`）
- GitHub repository with Actions enabled

**假设**：
- 开发在main分支进行（GitHub Flow模型）
- PR-based代码评审工作流
- 测试套件维护（现有926个单元测试）
- zen testgen工具可用于生成TDD测试套件
- 每个Phase独立部署，失败可快速回滚

## Risks and Mitigations

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| Phase 1修复引入新bug | 系统不稳定 | 中 | TDD先行，现有926测试回归，Pilot test验证 |
| Pydantic验证过严 | 误拒绝合法配置 | 低 | 宽松基础配置，渐进启用严格模式 |
| Strategy Pattern重构破坏行为等价性 | 功能回归 | 低 | A/B测试验证行为等价，完整E2E测试 |
| CI变慢影响开发速度 | 反馈延迟 | 低 | 优化mypy缓存，并行任务，<5分钟目标 |
| 开发者抵制类型提示 | 采用缓慢 | 低 | 类型提示可选，渐进采用，IDE益处明显 |

## Future Enhancements

不在当前范围但潜在未来增强：

1. **运行时类型验证**：使用pydantic模型验证运行时数据（独立spec）
2. **严格模式扩展**：逐步启用所有模块的严格类型检查（持续）
3. **类型覆盖率指标**：跟踪已类型化函数百分比（监控）
4. **IDE集成指南**：VSCode/PyCharm设置文档（文档）
5. **Pre-commit Hook（可选）**：本地提交前类型检查（未来选择性加入）

---

**Document Version**: 1.0
**Status**: Draft - Pending Approval
**Last Updated**: 2025-11-11
**Author**: Development Team
**Reviewers**: TBD
**Related Docs**:
- Architecture Contradictions Analysis (`docs/ARCHITECTURE_CONTRADICTIONS_ANALYSIS.md`)
- Tech Stack (`steering/tech.md`)
- Project Structure (`steering/structure.md`)
- Quality Assurance System (`specs/quality-assurance-system/`)

---

### Design
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

**Note**: Specification documents have been pre-loaded. Do not use get-content to fetch them again.

## Task Details
- Task ID: 1.1.2
- Description: 验证静默降级消除测试

## Instructions
- Implement ONLY task 1.1.2: "验证静默降级消除测试"
- Follow all project conventions and leverage existing code
- Mark the task as complete using: claude-code-spec-workflow get-tasks architecture-contradictions-fix 1.1.2 --mode complete
- Provide a completion summary
```

## Task Completion
When the task is complete, mark it as done:
```bash
claude-code-spec-workflow get-tasks architecture-contradictions-fix 1.1.2 --mode complete
```

## Next Steps
After task completion, you can:
- Execute the next task using /architecture-contradictions-fix-task-[next-id]
- Check overall progress with /spec-status architecture-contradictions-fix
