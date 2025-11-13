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
