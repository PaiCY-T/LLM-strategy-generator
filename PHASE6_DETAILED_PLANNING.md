# Phase 6: Main Learning Loop - 详细规划

**规划日期**: 2025-11-05
**规划者**: Claude (Sonnet 4.5)
**方法**: Ultra-Deep Thinking (考虑所有边界情况、错误场景、集成点)

---

## 🎯 Phase 6 总体目标

将 `autonomous_loop.py` (2,981 行) 重构为轻量级 `LearningLoop` 编排器：
- **输入**: 2,981 行单体文件
- **输出**: ~200 行编排逻辑 + 6 个专门模块 (~2,000 行已提取)
- **减少**: 33% 代码量，大幅提升可维护性

---

## 📋 Phase 6 子任务详细分解

### Task 6.1: 创建 LearningLoop 编排器

#### 6.1.1 核心职责定义

**LearningLoop 唯一职责：编排**
- ✅ **应该做**:
  1. 加载配置 (从 YAML 或默认值)
  2. 初始化所有组件 (History, Executor, Champion等)
  3. 确定起始迭代号 (新运行或恢复)
  4. 循环调用 IterationExecutor.execute_iteration()
  5. 保存 IterationRecord 到 History
  6. 显示进度信息
  7. 处理 SIGINT 中断
  8. 生成最终摘要报告

- ❌ **不应该做**:
  1. 任何策略生成逻辑 → IterationExecutor
  2. 任何 LLM 调用逻辑 → LLMClient
  3. 任何回测执行逻辑 → BacktestExecutor
  4. 任何指标计算逻辑 → MetricsExtractor
  5. 任何 Champion 更新逻辑 → ChampionTracker
  6. 任何反馈生成逻辑 → FeedbackGenerator

#### 6.1.2 与 IterationExecutor 的接口设计

```python
# IterationExecutor 接口 (Phase 5 已实现)
class IterationExecutor:
    def execute_iteration(
        self,
        iteration_num: int,
        config: Dict[str, Any],  # 传递配置参数
    ) -> IterationRecord:
        """执行单次迭代，返回记录"""
        pass

# LearningLoop 调用示例
for iteration_num in range(start_iteration, config.max_iterations):
    try:
        record = executor.execute_iteration(iteration_num, config)
        history.save_record(record)
        self._show_progress(iteration_num, record)
    except Exception as e:
        logger.error(f"Iteration {iteration_num} failed: {e}")
        # 决定是继续还是停止
```

#### 6.1.3 组件初始化顺序

```python
def __init__(self, config: LearningConfig):
    # 1. 配置验证 (立即失败)
    self.config = self._validate_config(config)

    # 2. 日志设置
    self.logger = self._setup_logging()

    # 3. 历史记录 (依赖: 无)
    self.history = IterationHistory(
        file_path=self.config.history_file
    )

    # 4. Champion 追踪 (依赖: History)
    self.champion_tracker = ChampionTracker(
        history=self.history
    )

    # 5. LLM 客户端 (依赖: 无)
    self.llm_client = LLMClient(
        model=self.config.llm_model,
        api_key=self.config.api_key
    )

    # 6. 反馈生成器 (依赖: History, Champion)
    self.feedback_generator = FeedbackGenerator(
        history=self.history,
        champion=self.champion_tracker
    )

    # 7. 回测执行器 (依赖: 无)
    self.backtest_executor = BacktestExecutor(
        timeout=self.config.timeout_seconds
    )

    # 8. 迭代执行器 (依赖: 所有上述组件)
    self.iteration_executor = IterationExecutor(
        llm_client=self.llm_client,
        feedback_generator=self.feedback_generator,
        backtest_executor=self.backtest_executor,
        champion_tracker=self.champion_tracker,
        history=self.history,
        config=self.config
    )
```

#### 6.1.4 主循环结构

```python
def run(self) -> None:
    """运行学习循环"""
    # 1. 设置信号处理
    self._setup_signal_handlers()

    # 2. 确定起始迭代
    start_iteration = self._get_start_iteration()

    # 3. 显示启动信息
    self._show_startup_info(start_iteration)

    # 4. 主循环
    for iteration_num in range(start_iteration, self.config.max_iterations):
        if self.interrupted:
            logger.info(f"Interrupted at iteration {iteration_num}")
            break

        try:
            # 执行迭代
            record = self.iteration_executor.execute_iteration(
                iteration_num=iteration_num,
                config=self.config
            )

            # 保存记录 (原子写入)
            self.history.save_record(record)

            # 显示进度
            self._show_progress(iteration_num, record)

        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt received, finishing current iteration...")
            self.interrupted = True
            break

        except Exception as e:
            logger.error(f"Iteration {iteration_num} failed: {e}", exc_info=True)
            # 根据配置决定是否继续
            if not self.config.continue_on_error:
                raise

    # 5. 生成摘要
    self._generate_summary()
```

#### 6.1.5 进度报告格式

```
=== Iteration 5/20 ===
Strategy: LLM (Factor Graph fallback: 0 times)
Execution: SUCCESS (8.2s)
Metrics: Sharpe=1.85, Return=0.32, MaxDD=-0.15
Classification: LEVEL_3 (Success)
Champion: UPDATED (prev=1.45, new=1.85)
Success Rate: 80.0% (4/5 iterations Level 1+, 60.0% Level 3+)
---
```

#### 6.1.6 错误处理策略

| 错误类型 | 处理方式 | 是否继续 |
|---------|---------|---------|
| 配置错误 | 立即退出，清晰错误消息 | ❌ 否 |
| 组件初始化失败 | 立即退出，堆栈跟踪 | ❌ 否 |
| IterationExecutor 异常 | 记录错误，可配置继续/停止 | ⚠️ 可配置 |
| History 写入失败 | 重试 3 次，失败则退出 | ❌ 否 (数据损失风险) |
| SIGINT 中断 | 完成当前迭代，优雅退出 | ✅ 是 (中断) |

#### 6.1.7 日志记录策略

```python
# 日志级别使用
logger.debug("Detailed iteration state: ...")       # 开发调试
logger.info("Iteration 5/20 completed")             # 正常进度
logger.warning("LLM timeout, using Factor Graph")   # 值得注意但非错误
logger.error("Failed to save history", exc_info=True)  # 错误需修复
logger.critical("Config validation failed")         # 致命错误

# 日志输出
- 控制台: INFO 及以上 (带颜色)
- 文件: DEBUG 及以上 (logs/learning_loop_{timestamp}.log)
- 结构化: JSON Lines 格式 (可选，用于分析)
```

#### 6.1.8 文件大小目标

```python
# LearningLoop 目标结构 (~200 行)
class LearningLoop:                    # ~20 行 (类定义+文档)
    def __init__(self, config):        # ~40 行 (组件初始化)
    def run(self):                     # ~50 行 (主循环)
    def _setup_signal_handlers(self):  # ~15 行
    def _get_start_iteration(self):    # ~15 行
    def _show_startup_info(self):      # ~10 行
    def _show_progress(self):          # ~20 行
    def _generate_summary(self):       # ~30 行
# 总计: ~200 行 ✅
```

---

### Task 6.2: 配置管理

#### 6.2.1 完整配置参数列表

```python
@dataclass
class LearningConfig:
    """学习循环配置"""

    # === 循环控制 ===
    max_iterations: int = 20              # 最大迭代次数
    continue_on_error: bool = False       # 迭代失败后是否继续

    # === LLM 配置 ===
    llm_model: str = "gemini-2.5-flash"   # LLM 模型名称
    api_key: Optional[str] = None         # API 密钥 (环境变量优先)
    llm_timeout: int = 60                 # LLM 调用超时 (秒)
    llm_temperature: float = 0.7          # LLM 温度参数
    llm_max_tokens: int = 4000            # LLM 最大输出 token

    # === 创新模式 ===
    innovation_mode: bool = True          # 是否启用创新模式
    innovation_rate: int = 100            # LLM vs Factor Graph 比例 (0-100)
                                          # 100 = 总是 LLM, 0 = 总是 Factor Graph
    llm_retry_count: int = 3              # LLM 失败后重试次数

    # === 回测配置 ===
    timeout_seconds: int = 420            # 回测超时 (秒)
    start_date: str = "2018-01-01"        # 回测起始日期
    end_date: str = "2024-12-31"          # 回测结束日期
    fee_ratio: float = 0.001425           # 手续费率
    tax_ratio: float = 0.003              # 税率
    resample: str = "M"                   # 再平衡频率 (M/W/D)

    # === 历史记录 ===
    history_file: str = "artifacts/data/innovations.jsonl"
    history_window: int = 5               # 反馈生成的历史窗口

    # === 文件路径 ===
    champion_file: str = "artifacts/data/champion.json"
    log_dir: str = "logs"
    config_file: str = "config/learning_system.yaml"

    # === 日志配置 ===
    log_level: str = "INFO"               # DEBUG/INFO/WARNING/ERROR
    log_to_file: bool = True              # 是否写入文件
    log_to_console: bool = True           # 是否输出到控制台

    def __post_init__(self):
        """配置验证"""
        self._validate()

    def _validate(self):
        """验证配置参数"""
        # 1. 迭代次数
        if self.max_iterations <= 0:
            raise ValueError(f"max_iterations must be > 0, got {self.max_iterations}")
        if self.max_iterations > 1000:
            raise ValueError(f"max_iterations too large (> 1000): {self.max_iterations}")

        # 2. 创新率
        if not 0 <= self.innovation_rate <= 100:
            raise ValueError(f"innovation_rate must be 0-100, got {self.innovation_rate}")

        # 3. 超时
        if self.timeout_seconds < 60:
            raise ValueError(f"timeout_seconds must be >= 60, got {self.timeout_seconds}")
        if self.llm_timeout < 10:
            raise ValueError(f"llm_timeout must be >= 10, got {self.llm_timeout}")

        # 4. 日期格式
        try:
            datetime.strptime(self.start_date, "%Y-%m-%d")
            datetime.strptime(self.end_date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format (use YYYY-MM-DD): {e}")

        # 5. 再平衡频率
        if self.resample not in ("D", "W", "M"):
            raise ValueError(f"resample must be D/W/M, got '{self.resample}'")

        # 6. 费率
        if not 0 <= self.fee_ratio < 0.1:
            raise ValueError(f"fee_ratio must be 0-0.1, got {self.fee_ratio}")
        if not 0 <= self.tax_ratio < 0.1:
            raise ValueError(f"tax_ratio must be 0-0.1, got {self.tax_ratio}")

        # 7. 历史窗口
        if self.history_window < 1:
            raise ValueError(f"history_window must be >= 1, got {self.history_window}")

        # 8. 日志级别
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if self.log_level not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got '{self.log_level}'")
```

#### 6.2.2 YAML 配置文件格式

```yaml
# config/learning_system.yaml

# 循环控制
max_iterations: 20
continue_on_error: false

# LLM 配置
llm_model: "gemini-2.5-flash"
# api_key: "..."  # 建议使用环境变量 GEMINI_API_KEY
llm_timeout: 60
llm_temperature: 0.7
llm_max_tokens: 4000

# 创新模式
innovation_mode: true
innovation_rate: 100  # 100 = 总是 LLM, 0 = 总是 Factor Graph
llm_retry_count: 3

# 回测配置
timeout_seconds: 420
start_date: "2018-01-01"
end_date: "2024-12-31"
fee_ratio: 0.001425
tax_ratio: 0.003
resample: "M"  # M=月度, W=周度, D=日度

# 历史记录
history_file: "artifacts/data/innovations.jsonl"
history_window: 5

# 文件路径
champion_file: "artifacts/data/champion.json"
log_dir: "logs"

# 日志配置
log_level: "INFO"
log_to_file: true
log_to_console: true
```

#### 6.2.3 配置加载策略

```python
@classmethod
def from_yaml(cls, config_path: str) -> "LearningConfig":
    """从 YAML 文件加载配置"""
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return cls()  # 使用默认值

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)

        # 环境变量优先
        if 'api_key' not in config_dict or not config_dict['api_key']:
            config_dict['api_key'] = os.getenv('GEMINI_API_KEY')

        return cls(**config_dict)

    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format in {config_path}: {e}")
    except TypeError as e:
        raise ValueError(f"Invalid config parameters: {e}")
```

---

### Task 6.3: 循环恢复逻辑

#### 6.3.1 恢复场景分析

| 场景 | 描述 | 处理方式 |
|-----|------|---------|
| **新运行** | history 文件不存在或为空 | 从 iteration 0 开始 |
| **正常恢复** | history 有 N 条记录，全部有效 | 从 iteration N 开始 |
| **中断恢复** | CTRL+C 中断，当前迭代完成 | 从下一个迭代开始 |
| **部分损坏** | history 有部分无效行 | 跳过无效行，从最后有效迭代+1 开始 |
| **完全损坏** | history 文件无法解析 | 警告用户，备份文件，从 0 开始 |
| **迭代号不连续** | history 中迭代号跳跃 | 从最大迭代号+1 开始 |

#### 6.3.2 起始迭代确定逻辑

```python
def _get_start_iteration(self) -> int:
    """确定起始迭代号"""
    try:
        # 1. 读取所有历史记录
        records = self.history.get_all()

        # 2. 空历史
        if not records:
            logger.info("No previous iterations found, starting from 0")
            return 0

        # 3. 找到最大迭代号
        max_iteration = max(r.iteration_num for r in records)
        next_iteration = max_iteration + 1

        # 4. 检查是否已完成
        if next_iteration >= self.config.max_iterations:
            logger.warning(
                f"All {self.config.max_iterations} iterations already completed. "
                f"Increase max_iterations in config or start fresh."
            )
            return self.config.max_iterations  # 循环会立即结束

        # 5. 恢复信息
        logger.info(
            f"Resuming from iteration {next_iteration} "
            f"(found {len(records)} previous iterations)"
        )
        return next_iteration

    except Exception as e:
        logger.error(f"Failed to determine start iteration: {e}")
        logger.warning("Starting from iteration 0 as fallback")
        return 0
```

#### 6.3.3 SIGINT 处理

```python
def _setup_signal_handlers(self):
    """设置信号处理器"""
    self.interrupted = False

    def sigint_handler(signum, frame):
        if not self.interrupted:
            logger.info("\n=== Interrupt signal received (CTRL+C) ===")
            logger.info("Finishing current iteration before exit...")
            logger.info("(Press CTRL+C again to force quit)")
            self.interrupted = True
        else:
            logger.warning("\n=== Force quit ===")
            sys.exit(1)

    signal.signal(signal.SIGINT, sigint_handler)
```

#### 6.3.4 原子写入确保

```python
# 在 IterationHistory.save_record() 中 (Phase 1 已实现)
def save_record(self, record: IterationRecord) -> None:
    """原子写入迭代记录"""
    with self._lock:
        # 1. 写入临时文件
        temp_file = self.file_path + ".tmp"
        with open(temp_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(asdict(record)) + '\n')
            f.flush()
            os.fsync(f.fileno())  # 强制刷新到磁盘

        # 2. 原子重命名
        os.replace(temp_file, self.file_path)

    logger.debug(f"Saved iteration {record.iteration_num} to history")
```

#### 6.3.5 损坏文件处理

```python
def _validate_history_file(self) -> Tuple[bool, List[str]]:
    """验证历史文件完整性

    Returns:
        (is_valid, error_lines)
    """
    if not os.path.exists(self.config.history_file):
        return (True, [])

    error_lines = []
    try:
        with open(self.config.history_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    error_lines.append(f"Line {line_num}: {e}")

        if error_lines:
            logger.warning(f"Found {len(error_lines)} corrupted lines in history file")
            for error in error_lines[:5]:  # 只显示前 5 个
                logger.warning(f"  {error}")
            return (False, error_lines)

        return (True, [])

    except Exception as e:
        logger.error(f"Failed to validate history file: {e}")
        return (False, [str(e)])
```

---

### Task 6.4: 中断恢复测试

#### 6.4.1 测试场景清单

1. **正常中断测试**
   - 启动 10 次迭代
   - 在第 3 次迭代完成后发送 SIGINT
   - 验证：history 有 3 条记录，没有第 4 条
   - 重启：验证从第 4 次迭代开始

2. **中间迭代中断测试**
   - 在迭代执行过程中（未完成）发送 SIGINT
   - 验证：该迭代要么完成要么不在 history 中
   - 验证：没有部分记录

3. **空历史测试**
   - 删除 history 文件
   - 启动循环
   - 验证：从迭代 0 开始

4. **损坏历史测试**
   - 创建包含无效 JSON 的 history 文件
   - 启动循环
   - 验证：跳过无效行，从最后有效迭代继续

5. **原子写入测试**
   - 模拟写入过程中崩溃
   - 验证：history 文件要么有完整记录，要么没有新记录
   - 验证：没有部分 JSON

6. **快速双击 CTRL+C 测试**
   - 发送第一个 SIGINT
   - 在 1 秒内发送第二个 SIGINT
   - 验证：立即强制退出

7. **达到 max_iterations 测试**
   - history 已有 20 条记录，max_iterations=20
   - 启动循环
   - 验证：循环立即完成，显示已完成消息

8. **迭代号不连续测试**
   - 手动创建 history: [0, 1, 3, 5]
   - 启动循环
   - 验证：从 6 开始（max+1）

#### 6.4.2 测试实现策略

```python
# tests/learning/test_learning_loop_resumption.py

class TestLearningLoopResumption:

    @pytest.fixture
    def mock_executor(self):
        """模拟 IterationExecutor"""
        executor = Mock(spec=IterationExecutor)
        executor.execute_iteration.side_effect = self._mock_execute
        return executor

    def _mock_execute(self, iteration_num, config):
        """模拟迭代执行"""
        time.sleep(0.1)  # 模拟耗时
        return IterationRecord(
            iteration_num=iteration_num,
            generation_method="llm",
            strategy_code="# mock code",
            execution_result={"success": True},
            metrics={"sharpe_ratio": 1.5},
            classification_level="LEVEL_3",
            timestamp=datetime.now().isoformat()
        )

    def test_normal_interruption(self, tmp_path, mock_executor):
        """测试正常中断和恢复"""
        config = LearningConfig(
            max_iterations=10,
            history_file=str(tmp_path / "history.jsonl")
        )

        loop = LearningLoop(config, executor=mock_executor)

        # 启动循环，在第 3 次迭代后中断
        def interrupt_after_3():
            time.sleep(0.35)  # 等待 3 次迭代 (3 * 0.1s)
            os.kill(os.getpid(), signal.SIGINT)

        thread = threading.Thread(target=interrupt_after_3)
        thread.start()

        loop.run()
        thread.join()

        # 验证
        history = IterationHistory(config.history_file)
        records = history.get_all()
        assert len(records) == 3
        assert [r.iteration_num for r in records] == [0, 1, 2]

        # 恢复
        loop2 = LearningLoop(config, executor=mock_executor)
        # 模拟运行 2 次迭代
        mock_executor.execute_iteration.side_effect = None
        mock_executor.execute_iteration.return_value = self._mock_execute(3, config)

        loop2.run()

        records = history.get_all()
        assert len(records) == 5  # 3 + 2
        assert records[-1].iteration_num == 4
```

---

## 🔍 关键风险和缓解措施

### 风险 1: LearningLoop 职责膨胀
**风险**: 在实现过程中，LearningLoop 开始包含业务逻辑
**缓解**:
- 严格的代码审查，确保 <250 行
- 任何超过 10 行的逻辑必须提取到专门组件

### 风险 2: 配置参数遗漏
**风险**: 缺少重要配置参数，导致灵活性不足
**缓解**:
- 完整的参数列表已列出（21 个参数）
- 每个参数都有清晰的默认值和验证规则

### 风险 3: 中断恢复不可靠
**风险**: 中断后数据损坏或恢复失败
**缓解**:
- 原子写入确保数据完整性（Phase 1 已实现）
- 8 个全面的中断恢复测试
- 损坏文件检测和备份机制

### 风险 4: 错误处理不一致
**风险**: 不同类型的错误处理方式不一致
**缓解**:
- 明确的错误处理策略表
- 每种错误类型都有清晰的处理方式

---

## ✅ 实施检查清单

### Task 6.1: LearningLoop 编排器
- [ ] 定义 LearningLoop 类结构
- [ ] 实现 __init__() 组件初始化
- [ ] 实现 run() 主循环
- [ ] 实现 _setup_signal_handlers()
- [ ] 实现 _get_start_iteration()
- [ ] 实现 _show_startup_info()
- [ ] 实现 _show_progress()
- [ ] 实现 _generate_summary()
- [ ] 验证代码行数 <250 行

### Task 6.2: 配置管理
- [ ] 定义 LearningConfig dataclass (21 个参数)
- [ ] 实现 _validate() 配置验证
- [ ] 实现 from_yaml() 类方法
- [ ] 创建 config/learning_system.yaml 模板
- [ ] 测试配置加载（有效/无效/缺失文件）
- [ ] 测试所有验证规则

### Task 6.3: 循环恢复
- [ ] 实现 _get_start_iteration() 完整逻辑
- [ ] 实现 SIGINT 处理器
- [ ] 实现 _validate_history_file()
- [ ] 验证原子写入工作正常（Phase 1 遗留）
- [ ] 测试各种恢复场景

### Task 6.4: 测试
- [ ] 测试 1: 正常中断和恢复
- [ ] 测试 2: 中间迭代中断
- [ ] 测试 3: 空历史
- [ ] 测试 4: 损坏历史
- [ ] 测试 5: 原子写入
- [ ] 测试 6: 快速双击 CTRL+C
- [ ] 测试 7: 达到 max_iterations
- [ ] 测试 8: 迭代号不连续

---

## 📊 预估工作量

| 任务 | 预估时间 | 复杂度 |
|-----|---------|--------|
| 6.1 LearningLoop 编排器 | 4-6 小时 | 中 |
| 6.2 配置管理 | 2-3 小时 | 低-中 |
| 6.3 循环恢复逻辑 | 3-4 小时 | 中 |
| 6.4 中断恢复测试 | 4-5 小时 | 中-高 |
| **总计** | **13-18 小时** | **中** |

---

## 🎯 成功标准

### 功能性
- ✅ LearningLoop <250 行，职责清晰
- ✅ 所有 21 个配置参数正确加载和验证
- ✅ CTRL+C 中断后无数据损失
- ✅ 从任意迭代号恢复
- ✅ 所有 8 个测试场景通过

### 质量
- ✅ 代码覆盖率 ≥90%
- ✅ 类型提示完整
- ✅ 文档字符串完整
- ✅ 日志记录清晰且结构化

### 可维护性
- ✅ 组件边界清晰
- ✅ 依赖注入（便于测试）
- ✅ 配置与代码分离
- ✅ 错误消息清晰可操作

---

**规划完成**: 2025-11-05
**下一步**: 更新 tasks.md，开始实施 Task 6.1
