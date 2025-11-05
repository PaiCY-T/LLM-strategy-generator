# Phase 2: Low Innovation Rate Test Plan

**Date**: 2025-10-30
**Model**: Gemini 2.5 Flash Lite
**Purpose**: Validate LLM integration in real autonomous loop with true backtest

---

## Phase 1 → Phase 2 升级

### Phase 1 (已完成) ✅
- **测试类型**: 独立测试脚本
- **Backtest**: Mock 数据 (Sharpe × 0.8)
- **Champion 更新**: ❌ Disabled (dry-run)
- **验证内容**: LLM API 成功率、代码生成质量
- **结果**: 80% 成功率，Mock Sharpe 1.98

### Phase 2 (本次测试) 🎯
- **测试类型**: 完整 autonomous_loop
- **Backtest**: ✅ **真实 finlab sim()**
- **Champion 更新**: ✅ **ENABLED** (真实测试)
- **验证内容**:
  1. ✅ **真实 Sharpe ratio** (实际回测)
  2. ✅ **真实 backtest 性能** (Drawdown, Win Rate, etc.)
  3. ✅ **vs Champion 比较** (自动比较并更新)
  4. ✅ **Diversity 提升** (vs Stage 1 的 10.4%)
  5. ✅ **创新持续性** (不再 19-day plateau)

---

## 测试配置

### LLM 配置
```yaml
llm:
  enabled: true                    # 启用 LLM innovation
  provider: gemini                 # 使用 Google Gemini
  model: gemini-2.5-flash-lite     # 免费模型
  innovation_rate: 0.05            # 5% (保守测试)
```

### Autonomous Loop 配置
```yaml
autonomous:
  max_iterations: 20               # 20 代
  history_file: phase2_flashlite_history.jsonl
```

### 预期 LLM 使用
- **总迭代**: 20
- **LLM 策略**: ~1 (5% × 20 = 1)
- **Factor Graph**: ~19 (95%)
- **LLM 成功率**: 80% (Phase 1 验证)

---

## 验证目标 🎯

### 1. 真实 Sharpe Ratio ✅

**Phase 1 问题**: Mock 数据 (Sharpe 1.98 = Champion × 0.8)

**Phase 2 验证**:
```python
# autonomous_loop.py 执行：
code = innovation_engine.generate_innovation(...)  # LLM 生成
position = exec(code)                              # 执行策略
report = sim(position, resample="Q", ...)          # 真实回测
metrics = extract_metrics(report)                  # 提取真实指标

# 得到真实值：
{
    'sharpe_ratio': 实际回测结果,     # 不再是 Mock
    'annual_return': 实际回测结果,
    'max_drawdown': 实际回测结果,
    'win_rate': 实际回测结果
}
```

**成功标准**:
- LLM 策略 Sharpe ≥ 0.5 (可接受)
- LLM 策略 Sharpe ≥ 1.0 (良好)
- LLM 策略 Sharpe ≥ Champion 2.4751 (优秀)

---

### 2. 真实 Backtest 性能 ✅

**完整指标验证**:

| 指标 | Phase 1 | Phase 2 | 验证方式 |
|------|---------|---------|---------|
| **Sharpe Ratio** | Mock (1.98) | ✅ 真实回测 | sim() 输出 |
| **Annual Return** | Mock (8.4%) | ✅ 真实回测 | sim() 输出 |
| **Max Drawdown** | Mock (-18%) | ✅ 真实回测 | sim() 输出 |
| **Win Rate** | Mock (28%) | ✅ 真实回测 | trade_records 计算 |
| **Position Count** | Mock (3277) | ✅ 真实回测 | position 统计 |
| **Calmar Ratio** | 未计算 | ✅ 真实计算 | Return / Drawdown |
| **Profit Factor** | 未计算 | ✅ 真实计算 | Wins / Losses |

**回测数据期间**:
- Train: 2020-01-01 to 2023-12-31
- Validation: 2024-01-01 to 2024-06-30
- Test: 2024-07-01 to 2024-10-08

---

### 3. vs Champion 比较 ✅

**自动比较逻辑** (autonomous_loop.py):

```python
# 每次策略评估后自动执行：
new_metrics = backtest(new_strategy)
champion_metrics = load_champion()

if new_metrics['sharpe_ratio'] > champion_metrics['sharpe_ratio']:
    # Multi-objective validation
    if validate_multi_objective(new_metrics):
        # Anti-churn check
        if anti_churn_manager.should_update(new_metrics, champion_metrics):
            # Update Champion
            update_champion(new_strategy, new_metrics)
            log_champion_update(
                old_sharpe=champion_metrics['sharpe_ratio'],
                new_sharpe=new_metrics['sharpe_ratio'],
                improvement=new_metrics['sharpe_ratio'] - champion_metrics['sharpe_ratio']
            )
```

**验证内容**:
- ✅ LLM 策略是否能更新 Champion (Sharpe >2.4751)
- ✅ Champion 更新频率 (预期 5-10%)
- ✅ 更新质量 (Multi-objective validation)
- ✅ Anti-churn 机制 (防止频繁更新)

**可能结果**:
1. **最佳**: LLM 策略更新 Champion (Sharpe >2.4751)
2. **良好**: LLM 策略接近 Champion (Sharpe 2.0-2.4)
3. **可接受**: LLM 策略 Sharpe 1.0-2.0 (为下一代提供基因)
4. **需改进**: LLM 策略 Sharpe <1.0 (回 Factor Graph)

---

### 4. Diversity 提升 ✅

**Stage 1 问题**: Diversity 崩溃到 10.4% (19-day plateau)

**Phase 2 验证**:
```python
# autonomous_loop 自动计算 diversity:
population = [strategy1, strategy2, ..., strategy20]
diversity_score = calculate_diversity(population)

# Diversity metrics:
- Parameter variance: σ(parameters)
- Factor composition: Unique factor combinations
- Strategy types: Template distribution
- Novel factors: Non-predefined factor usage
```

**成功标准**:
- Diversity ≥ 30% (vs Stage 1 的 10.4%)
- Novel factor usage: ≥1 LLM 策略使用新因子
- Strategy types: 不只是单一 template

**监控方式**:
- 每 5 代输出 diversity report
- 最终分析 20 代的 diversity 趋势
- 比较 LLM 策略 vs Factor Graph 策略的差异

---

### 5. 突破 19-Day Plateau ✅

**Stage 1 问题**:
- 19 天无改进 (Oct 8 - Oct 27)
- 原因: Template 限制，无法创造新因子

**Phase 2 验证**:
```python
# 分析 Champion 更新历史:
updates = []
for iteration in range(20):
    if champion_updated:
        updates.append({
            'iteration': iteration,
            'new_sharpe': champion_sharpe,
            'improvement': champion_sharpe - old_sharpe,
            'source': 'llm' or 'factor_graph'
        })

# 评估突破：
- Champion 是否有更新？
- 更新来源 (LLM vs Factor Graph)
- 更新频率 vs Stage 1 (0.5% → 目标 10%)
```

**成功标准**:
- Champion 更新率 ≥ 5% (1/20 迭代)
- 至少 1 次更新来自 LLM 策略
- Sharpe 提升 ≥ 0.1 (2.4751 → 2.5751+)

**失败情况**:
- 20 代无更新 (继续 plateau)
- 所有更新来自 Factor Graph (LLM 无贡献)
- Sharpe 下降 (回退风险)

---

## 执行计划

### 准备阶段 (5 分钟)

1. ✅ 检查 API Key
```bash
echo $GOOGLE_API_KEY
```

2. ✅ 备份 Champion
```bash
cp artifacts/data/champion_strategy.json \
   artifacts/data/champion_strategy_backup_phase2.json
```

3. ✅ 清理旧数据 (可选)
```bash
rm -f artifacts/data/phase2_flashlite_history.jsonl
```

### 执行阶段 (4-6 小时)

**运行测试**:
```bash
chmod +x run_phase2_flashlite.sh
./run_phase2_flashlite.sh
```

**实时监控**:
```bash
# Terminal 1: 运行测试
./run_phase2_flashlite.sh

# Terminal 2: 监控进度
tail -f artifacts/data/phase2_flashlite_history.jsonl | jq '.'

# Terminal 3: 检查 Champion 更新
watch -n 60 'cat artifacts/data/champion_strategy.json | jq ".metrics.sharpe_ratio"'
```

### 分析阶段 (30-60 分钟)

1. **提取关键指标**:
```bash
python3 scripts/analyze_phase2_results.py
```

2. **比较 LLM vs Factor Graph**:
```python
llm_strategies = [s for s in history if s['source'] == 'llm']
fg_strategies = [s for s in history if s['source'] == 'factor_graph']

print(f"LLM Avg Sharpe: {mean([s['sharpe'] for s in llm_strategies])}")
print(f"FG Avg Sharpe: {mean([s['sharpe'] for s in fg_strategies])}")
```

3. **Diversity 分析**:
```python
diversity_scores = [s['diversity'] for s in history]
print(f"Avg Diversity: {mean(diversity_scores)}")
print(f"Final Diversity: {diversity_scores[-1]}")
```

---

## 预期结果

### 乐观情况 🟢 (60% 概率)

- ✅ LLM 策略 Sharpe 1.5-2.5 (接近或超越 Champion)
- ✅ Champion 更新 1-2 次 (5-10% 更新率)
- ✅ Diversity 提升到 35-45%
- ✅ Novel factors 使用 (RSI, MACD, ATR)
- ✅ 无 plateau (持续改进)

**决策**: ✅ 进入 Phase 3 (20% rate, 50 gen)

### 中等情况 🟡 (30% 概率)

- ✅ LLM 策略 Sharpe 1.0-1.5 (良好但未超越)
- ⚠️ Champion 无更新 (但 LLM 策略质量可接受)
- ✅ Diversity 提升到 25-35%
- ✅ Novel factors 使用

**决策**: ⏳ 延长测试到 50 代 (5% rate)，或提高到 10% rate

### 悲观情况 🔴 (10% 概率)

- ❌ LLM 策略 Sharpe <0.5 (质量差)
- ❌ Champion 无更新
- ❌ Diversity 无提升 (仍 ~10%)
- ❌ 多次 LLM 失败

**决策**:
- Debug prompt template
- 测试 Grok/Pro 模型
- 调整 innovation_rate 或 temperature

---

## 风险控制

### Champion 保护 ✅

- **自动备份**: 测试前备份 Champion
- **Anti-churn**: 防止劣质更新
- **Multi-objective**: 多目标验证
- **Rollback**: 可回滚到备份

### 成本控制 ✅

- **Innovation Rate**: 仅 5% 使用 LLM
- **Model**: Flash Lite (~$0)
- **Fallback**: LLM 失败自动降级
- **预期成本**: $0

### 系统稳定性 ✅

- **Docker Sandbox**: 防止恶意代码
- **Timeout**: 60s per generation
- **Max Retries**: 3 次重试
- **Error Handling**: 完整错误处理

---

## 成功标准总结

| 标准 | 目标 | 评估方式 |
|------|------|---------|
| **LLM 成功率** | ≥80% | API 调用统计 |
| **真实 Sharpe** | ≥1.0 | 实际回测结果 |
| **Champion 更新** | ≥1 次 | Champion 历史 |
| **Diversity 提升** | ≥30% | Diversity 指标 |
| **Novel Factors** | ≥1 策略 | 代码分析 |
| **无 Plateau** | 持续改进 | 20 代趋势 |
| **成本** | $0 | 无成本 ✅ |

**Phase 2 通过标准**: 6/7 指标达标

---

## Next Steps

### 如果 Phase 2 成功 ✅
1. 创建 Phase 3 配置 (20% rate, 50 gen)
2. 运行完整 Stage 2 breakthrough test
3. 评估是否达到 >80% success, >40% diversity, Sharpe >2.5

### 如果 Phase 2 需改进 ⚠️
1. 分析失败原因 (API, prompt, validation)
2. 测试 Grok 模型 (vs Flash Lite)
3. 调整 temperature 或 innovation_rate
4. 重新运行 Phase 2

### 如果 Phase 2 失败 ❌
1. 深度 debug (LLM response, YAML validation)
2. 比较 Grok + Pro 模型
3. 重新评估 prompt template
4. 考虑降级到 template-based 优化

---

## 问题与回答

### Q1: Phase 2 会改变 Champion 吗？

**A**: ✅ **会**。Phase 2 是真实测试，Champion 可能被更新。

- 如果 LLM 策略 Sharpe >2.4751，Champion 会更新
- 更新前会经过 Multi-objective 和 Anti-churn 验证
- 已备份原始 Champion，可随时回滚

### Q2: 5% innovation rate 太低吗？

**A**: ✅ **合理**。Phase 2 是保守测试。

- 20 代 × 5% = 1 个 LLM 策略 (足够验证)
- 降低风险 (如果 LLM 质量差，影响小)
- Phase 3 会提高到 20% (4/20 迭代)

### Q3: 如何确认是真实回测而非 Mock？

**A**: ✅ 可以从日志验证。

```bash
# 查看回测日志
grep "sim(position" phase2_flashlite_history.jsonl

# 真实回测会有：
# - 回测执行时间 (通常 10-30 秒)
# - 完整 trade_records
# - Position 历史数据
# - Equity curve

# Mock 数据会：
# - 瞬间完成 (<1 秒)
# - 没有 trade_records
# - Metrics 是计算值 (Champion × 0.8)
```

### Q4: Phase 2 能验证全部 3 项吗？

**A**: ✅ **能**。

1. ✅ 真实 Sharpe ratio - `sim()` 输出
2. ✅ 真实 backtest 性能 - 完整 metrics
3. ✅ vs Champion 比较 - 自动比较并更新

---

**Document Version**: 1.0
**Status**: Ready for Execution
**Estimated Time**: 4-6 hours
**Risk Level**: 🟢 LOW
