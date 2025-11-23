# Hybrid 模式 Pilot 测试策略分析报告

**日期**: 2025-11-13
**测试配置**: config_pilot_hybrid_20.yaml
**创新率**: 30% LLM + 70% Factor Graph
**迭代次数**: 20

---

## 执行摘要

### 整体表现

| 指标 | 数值 | 说明 |
|------|------|------|
| 总迭代次数 | 20 | 完整执行 |
| 成功次数 | 1 (5%) | ❌ 远低于预期 |
| 失败次数 | 19 (95%) | ⚠️ 系统性错误 |
| LLM 生成 | 1 次 (5%) | ⚠️ 低于配置的 30% |
| Factor Graph 生成 | 19 次 (95%) | ⚠️ 全部失败 |

### 关键发现

1. **✅ Phase 3.3 Dict Interface Fix 验证成功**
   - 没有 `AttributeError: 'StrategyMetrics' object has no attribute 'get'`
   - 测试执行完整，E2E 流程通畅
   - Phase 7 已成功 UNBLOCK

2. **❌ Factor Graph 配置存在严重问题**
   - 所有 19 次 Factor Graph 生成的策略都失败
   - 错误原因：`trailing_stop_10pct` factor 依赖缺失
   - 实际创新率仅 5%，而非配置的 30%

3. **❌ 唯一成功策略表现极差**
   - Sharpe Ratio: -0.137（负值）
   - 总回报: -36.68%（严重亏损）
   - 最大回撤: -66.05%（极高风险）

---

## 详细分析

### 1. 失败原因分析

#### Factor Graph Pipeline Error (19 次全部失败)

**错误信息**:
```
RuntimeError: Pipeline execution failed at factor 'trailing_stop_10pct' (Trailing Stop (10%)):
"Factor 'trailing_stop_10pct' requires matrices ['close', 'positions', 'entry_price'],
but ['positions', 'entry_price'] are missing from container.
Available: ['close', 'momentum', 'high', 'low', 'breakout_signal']"
```

**根本原因**:
- Factor Graph 模板配置中包含 `trailing_stop_10pct` factor
- 该 factor 需要 `positions` 和 `entry_price` 作为输入矩阵
- 但在策略执行阶段，这些矩阵还未生成（需要先有持仓才能计算）
- 这是一个**模板设计缺陷**，不是策略生成问题

**影响**:
- 70% 的迭代（Factor Graph 部分）完全无法产生有效策略
- 系统无法验证 Factor Graph 的创新能力
- 测试结果不具备统计意义

---

### 2. 成功策略分析 (Iteration 9)

#### 策略概要

**生成方法**: LLM (OpenRouter - google/gemini-2.5-flash)
**执行时间**: 42.54 秒
**策略类型**: 多因子选股 + 动量策略

#### 策略逻辑

```
数据源 → 过滤条件 → 排名筛选 → 持仓输出
```

**1. 数据加载**
- 价格数据: 调整收盘价 (`etl:adj_close`)
- 流动性: 成交金额 (`price:成交金額`)
- 质量因子: ROE 税后 (`fundamental_features:ROE稅後`)
- 价值因子: PB Ratio (`price_earning_ratio:股價淨值比`)
- 效率因子: 营业利益率 (`fundamental_features:營業利益率`)

**2. 三重过滤系统**

| 过滤器 | 条件 | 目的 | Look-ahead Bias 防护 |
|--------|------|------|---------------------|
| 流动性过滤 | 20日平均成交金额 > 1.5亿 TWD | 确保可交易性 | ✅ shift(1) |
| 质量过滤 | ROE > 15% | 筛选高盈利能力公司 | ✅ shift(1) |
| 价值过滤 | 0.5 < PB Ratio < 5.0 | 避免极端高估/低估 | ✅ shift(1) |

**3. 双因子排名**

| 因子 | 权重 | 计算方法 |
|------|------|----------|
| 动量因子 | 60% | 5日价格动量百分位排名 |
| 营运效率 | 40% | 营业利益率百分位排名 |

**4. 选股规则**
- 通过三重过滤的股票中
- 选取综合得分前 20% 的股票
- 等权重持仓

#### 策略优点

1. **✅ 多维度风险控制**
   - 流动性过滤避免无法交易的小型股
   - 质量过滤确保基本面健康
   - 价值过滤避免泡沫股

2. **✅ Look-ahead Bias 防护**
   - 所有因子都使用 `shift(1)` 避免未来函数
   - 20日滚动平均确保使用历史数据

3. **✅ 逻辑清晰**
   - 因子选择合理（质量、价值、动量）
   - 权重分配有依据（动量更重要）

#### 策略缺陷

1. **❌ 缺乏风险管理**
   - 没有止损机制
   - 没有仓位管理
   - 没有动态调整机制

2. **❌ 因子选择可能不适合市场**
   - ROE > 15% 条件可能过于严格
   - PB Ratio 0.5-5.0 范围可能需要调整
   - 动量周期（5日）可能过短

3. **❌ 回测参数设定问题**
   - 回测期间可能包含不利市场环境
   - 再平衡频率（月度）可能不够灵活

#### 绩效指标详解

| 指标 | 数值 | 评级 | 说明 |
|------|------|------|------|
| **Sharpe Ratio** | -0.137 | ❌ 极差 | 负值表示风险调整后收益为负，低于无风险利率 |
| **Total Return** | -36.68% | ❌ 严重亏损 | 回测期间累计亏损超过三分之一 |
| **Max Drawdown** | -66.05% | ❌ 极高风险 | 最大回撤超过 60%，风险承受能力要求极高 |
| **Win Rate** | N/A | - | 未记录 |

**结论**: 该策略在回测期间表现极差，**不具备实用价值**，需要大幅改进。

---

## 根本问题诊断

### 问题 1: Factor Graph 模板配置错误

**症状**:
- 19/19 Factor Graph 策略全部失败
- 相同的错误信息重复出现

**根本原因**:
```yaml
# Factor Graph 模板中包含的问题配置
factors:
  - trailing_stop_10pct:  # ❌ 问题 factor
      requires: [close, positions, entry_price]  # positions 和 entry_price 不可用
```

**为什么会失败**:
1. `trailing_stop_10pct` 是一个**状态依赖型** factor
2. 它需要当前持仓 (`positions`) 和入场价格 (`entry_price`)
3. 但在策略生成阶段，这些状态还不存在
4. 这类 factor 应该在**回测执行层**实现，而非策略生成层

**修正方案**:
```python
# 选项 1: 移除 trailing_stop_10pct
# 在模板中完全移除该 factor

# 选项 2: 替换为无状态版本
# 使用基于价格的止损逻辑，不依赖持仓状态
factors:
  - price_based_stop:
      requires: [close, high, low]  # 只需要价格数据
```

---

### 问题 2: 创新率配置失效

**预期**: 30% LLM + 70% Factor Graph
**实际**: 5% LLM + 95% Factor Graph (全部失败)

**原因**:
- Factor Graph 占比过高（70%）
- 但由于配置错误，全部失败
- 导致实际只有 1/20 (5%) 的迭代产生有效策略

**影响**:
- 无法验证 Hybrid 模式的设计理念
- 无法评估 30/70 混合比例的有效性
- 测试结果不具统计意义

---

### 问题 3: LLM 策略质量不佳

**可能原因**:

1. **Prompt 设计不够优化**
   - 缺乏对市场环境的考虑
   - 缺乏对风险管理的强调
   - 缺乏对参数优化的指导

2. **回测设置问题**
   - 回测期间可能不合适（包含熊市/震荡市）
   - 交易成本设置可能过高
   - 再平衡频率可能不适合策略

3. **因子组合问题**
   - ROE > 15% 可能筛选出的股票数量过少
   - 动量周期（5日）可能过短
   - 缺乏对市场状态的适应性

---

## 建议改进措施

### 短期修正（紧急）

#### 1. 修正 Factor Graph 模板配置

**优先级**: 🔴 Critical
**预计工时**: 1-2 小时

**行动清单**:
- [ ] 检查 Factor Graph 模板文件
- [ ] 移除或替换 `trailing_stop_10pct` factor
- [ ] 验证所有 factor 的输入依赖都在执行时可用
- [ ] 重新运行 Hybrid pilot 测试

**验证标准**:
- Factor Graph 生成的策略成功率 > 80%
- 实际创新率接近配置的 30%

---

#### 2. 重新执行 Pilot 测试

**优先级**: 🔴 Critical
**预计工时**: 30 分钟（执行时间）

**行动清单**:
- [ ] 修正 Factor Graph 配置后
- [ ] 重新运行 Hybrid pilot (20 iterations)
- [ ] 验证成功率提升
- [ ] 收集有效策略样本

**成功标准**:
- 执行成功率 > 80%
- 至少 6 个 LLM 策略成功（30% × 20）
- 至少 14 个 Factor Graph 策略成功（70% × 20）

---

### 中期优化（1-2周）

#### 3. 优化 LLM Prompt

**优先级**: 🟡 High
**预计工时**: 3-5 天

**改进方向**:

**3.1 增强风险管理指导**
```python
# 在 prompt 中明确要求
- 加入止损逻辑（固定止损或追踪止损）
- 加入仓位管理（避免过度集中）
- 加入市场状态判断（牛市/熊市/震荡）
```

**3.2 优化因子选择指导**
```python
# 提供因子组合建议
- 质量因子：ROE, ROA, 毛利率
- 价值因子：PB, PE, PEG
- 动量因子：不同周期（5日/20日/60日）
- 建议测试多个参数组合
```

**3.3 添加市场环境适应性**
```python
# 根据市场状态调整策略
if market_condition == '牛市':
    weight_momentum = 0.7
elif market_condition == '熊市':
    weight_quality = 0.7
```

---

#### 4. 改进回测设置

**优先级**: 🟡 High
**预计工时**: 2-3 天

**改进项目**:

**4.1 回测期间设置**
```python
# 建议使用多个时期验证
training_period = '2018-01-01' to '2021-12-31'  # 训练期
validation_period = '2022-01-01' to '2023-12-31'  # 验证期
```

**4.2 交易成本校准**
```python
# 确认台湾市场实际成本
fee_ratio = 0.001425  # 0.1425% 手续费
tax_ratio = 0.003     # 0.3% 证交税
slippage = 0.001      # 考虑滑点
```

**4.3 再平衡频率优化**
```python
# 测试不同频率
resample_options = ['D', 'W', 'M', 'Q']  # 日/周/月/季
# 根据策略特性选择（动量策略可能需要更高频率）
```

---

### 长期规划（1-2月）

#### 5. 建立策略评估框架

**目标**: 系统化评估策略质量

**评估维度**:
1. **收益指标**
   - 年化收益率
   - Sharpe Ratio (目标 > 1.0)
   - Calmar Ratio
   - Sortino Ratio

2. **风险指标**
   - 最大回撤 (目标 < 20%)
   - 波动率
   - Value at Risk (VaR)
   - 下行风险

3. **稳健性指标**
   - 胜率 (目标 > 50%)
   - 盈亏比
   - 连续亏损次数
   - 跨期稳定性

4. **实用性指标**
   - 换手率（交易成本）
   - 持仓集中度
   - 市场容量
   - 执行难度

---

#### 6. 扩大测试规模

**从 Pilot (20 iterations) → Full Study (200 iterations)**

**目标**:
- 收集足够样本量进行统计分析
- 验证 LLM vs Factor Graph 的创新能力差异
- 评估 Hybrid 模式的最优混合比例

**实验设计**:
```yaml
groups:
  llm_only:      100% LLM,   200 iterations
  fg_only:         0% LLM,   200 iterations
  hybrid_30_70:   30% LLM,   200 iterations
  hybrid_50_50:   50% LLM,   200 iterations
  hybrid_70_30:   70% LLM,   200 iterations
```

---

## 下一步行动

### 立即执行（今天）

1. **✅ Phase 3.3 验证完成**
   - Dict interface fix 工作正常
   - E2E 流程已通畅
   - Phase 7 成功 UNBLOCK

2. **🔴 修正 Factor Graph 配置**
   ```bash
   # 定位问题文件
   find factor_graph/templates -name "*.yaml" -o -name "*.json"

   # 检查 trailing_stop_10pct 使用
   grep -r "trailing_stop" factor_graph/

   # 修正或移除问题配置
   ```

3. **🔴 重新运行 Pilot 测试**
   ```bash
   # 修正后重新执行
   python3 experiments/llm_learning_validation/orchestrator.py \
       --config experiments/llm_learning_validation/config_pilot_hybrid_20.yaml \
       --phase pilot
   ```

### 本周完成

4. **🟡 优化 LLM Prompt**
   - 添加风险管理要求
   - 优化因子选择指导
   - 增强市场适应性

5. **🟡 校准回测参数**
   - 验证交易成本设置
   - 测试不同再平衡频率
   - 选择合适的回测期间

### 下周开始

6. **🟢 执行完整测试**
   - 运行 LLM-Only pilot
   - 运行 FG-Only pilot
   - 比较三种模式的表现

7. **🟢 分析统计结果**
   - Mann-Whitney U 检验
   - Mann-Kendall 趋势分析
   - 生成对比报告

---

## 附录

### A. 测试配置详情

```yaml
# config_pilot_hybrid_20.yaml
experiment:
  name: "pilot-hybrid-20"
  version: "1.0.0"
  description: "Pilot run: 30% LLM + 70% Factor Graph, 20 iterations"

groups:
  hybrid:
    name: "Hybrid"
    innovation_rate: 0.30
    description: "Current production configuration"

phases:
  pilot:
    iterations_per_run: 20
    num_runs: 1
    total_iterations: 20

novelty:
  weights:
    factor_diversity: 0.30
    combination_patterns: 0.40
    logic_complexity: 0.30

statistics:
  significance_level: 0.05
  tests:
    - mann_whitney_u
    - mann_kendall
    - sliding_window

execution:
  timeout_seconds: 420
  continue_on_error: false
  max_parallel_groups: 1
```

### B. 成功策略完整代码

见测试结果文件：
- `experiments/llm_learning_validation/results/pilot_hybrid_20/hybrid_run1_history.jsonl` (line 9)
- `experiments/llm_learning_validation/results/pilot_hybrid_20/pilot_results.json` (iteration 9)

### C. 错误日志样本

```
RuntimeError: Pipeline execution failed at factor 'trailing_stop_10pct' (Trailing Stop (10%)):
"Factor 'trailing_stop_10pct' requires matrices ['close', 'positions', 'entry_price'],
but ['positions', 'entry_price'] are missing from container.
Available: ['close', 'momentum', 'high', 'low', 'breakout_signal']"
```

---

## 总结

### ✅ 成功点

1. **Phase 3.3 Dict Interface Fix 验证成功**
   - E2E 流程完整执行
   - 没有兼容性错误
   - Phase 7 成功 UNBLOCK

2. **LLM 策略生成能力验证**
   - 能够生成完整、可执行的策略代码
   - 逻辑清晰，包含多重过滤和排名机制
   - Look-ahead bias 防护到位

### ❌ 问题点

1. **Factor Graph 模板配置严重错误**
   - 100% 失败率（19/19）
   - 阻碍了 Hybrid 模式的验证
   - 需要紧急修正

2. **策略绩效极差**
   - Sharpe: -0.137
   - Return: -36.68%
   - Drawdown: -66.05%
   - 需要大幅优化

3. **测试有效性不足**
   - 只有 1/20 成功
   - 无法进行统计分析
   - 无法验证创新假设

### 🎯 核心建议

**立即行动**: 修正 Factor Graph 配置，重新执行测试
**短期目标**: 提高策略成功率 > 80%，优化 LLM prompt
**长期规划**: 建立完整评估框架，扩大测试规模到 200 iterations
