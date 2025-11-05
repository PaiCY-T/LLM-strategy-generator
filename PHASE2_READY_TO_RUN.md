# Phase 2 Ready to Run

**Date**: 2025-10-30
**Status**: ✅ **CONFIGURED AND READY**

---

## 准备工作完成 ✅

### 1. Champion 已备份
```
✅ artifacts/data/champion_strategy_backup_phase2_20251030_174753.json
```

### 2. LLM 配置已修复
```yaml
llm:
  enabled: true                    # ✅ LLM enabled
  provider: gemini                 # ✅ Using Gemini
  innovation_rate: 0.05            # ✅ 5% rate (float, not string)
```

**验证结果**:
```
✅ Innovation rate validation passed: 0.05
✅ Innovation rate type: <class 'float'>
```

### 3. 环境变量已设置
```bash
✅ GOOGLE_API_KEY is set (39 chars)
```

---

## 运行 Phase 2

### 方式 1: 在 finlab 环境中运行 (推荐)

如果你有完整的 finlab 环境（数据、finlab 库等）：

```bash
# 1. 确认环境
export GOOGLE_API_KEY=your_api_key
export PYTHONPATH=/path/to/finlab

# 2. 运行 Phase 2 (20 generations)
python3 artifacts/working/modules/autonomous_loop.py \
    --max-iterations 20 \
    --history-file artifacts/data/phase2_flashlite_history.jsonl

# 3. 监控进度 (另开 terminal)
tail -f artifacts/data/phase2_flashlite_history.jsonl | jq '.metrics.sharpe_ratio'
```

**预期时间**: 4-6 小时 (20 gen × 15 min/gen)
**预期成本**: $0 (Flash Lite 免费)

### 方式 2: 使用启动脚本

```bash
./run_phase2_flashlite.sh
```

脚本会自动：
- ✅ 检查 API key
- ✅ 备份 Champion
- ✅ 设置环境变量
- ✅ 运行 20 次迭代
- ✅ 保存结果

---

## 预期结果

### LLM Innovation
- **LLM 策略数**: ~1 (5% × 20 = 1)
- **Factor Graph**: ~19 (95%)
- **LLM 成功率**: 80%

### 性能指标 (真实回测)
- ✅ 真实 Sharpe ratio
- ✅ 真实 Annual Return, Max Drawdown
- ✅ 真实 Win Rate, Position Count
- ✅ vs Champion 自动比较

### Champion 更新
- 如果 LLM 策略 Sharpe >2.4751 → 自动更新
- Multi-objective validation
- Anti-churn protection

### Diversity 提升
- 预期: 35-45% (vs Stage 1 的 10.4%)
- Novel factors: RSI, EMA, MACD, ATR

---

## 成功标准

| 标准 | 目标 | 验证方式 |
|------|------|---------|
| **LLM 成功率** | ≥80% | API 统计 |
| **真实 Sharpe** | ≥1.0 | 实际回测 |
| **Champion 更新** | ≥1 次 | Champion 历史 |
| **Diversity** | ≥30% | Diversity 指标 |
| **Novel Factors** | ≥1 策略 | 代码分析 |

---

## 监控命令

### 实时监控进度
```bash
# Terminal 1: 查看迭代进度
tail -f artifacts/data/phase2_flashlite_history.jsonl | jq '.'

# Terminal 2: 监控 Champion 更新
watch -n 60 'cat artifacts/data/champion_strategy.json | jq ".metrics.sharpe_ratio"'

# Terminal 3: 查看 LLM 统计
watch -n 60 'cat artifacts/data/phase2_flashlite_history.jsonl | jq "select(.source == \"llm\") | .metrics.sharpe_ratio"'
```

### 快速检查
```bash
# 检查完成的迭代数
wc -l artifacts/data/phase2_flashlite_history.jsonl

# 检查 LLM 策略数
grep -c '"source": "llm"' artifacts/data/phase2_flashlite_history.jsonl

# 检查最新 Champion
cat artifacts/data/champion_strategy.json | jq '.metrics.sharpe_ratio'
```

---

## 结果分析

测试完成后运行：

```bash
python3 <<'EOF'
import json
from pathlib import Path

# Load history
history = []
with open('artifacts/data/phase2_flashlite_history.jsonl', 'r') as f:
    for line in f:
        history.append(json.loads(line))

# Analyze
llm_strategies = [h for h in history if h.get('source') == 'llm']
fg_strategies = [h for h in history if h.get('source') != 'llm']

print("=" * 60)
print("PHASE 2 RESULTS")
print("=" * 60)
print(f"\nTotal iterations: {len(history)}")
print(f"LLM strategies: {len(llm_strategies)}")
print(f"Factor Graph: {len(fg_strategies)}")

if llm_strategies:
    llm_sharpes = [s['metrics']['sharpe_ratio'] for s in llm_strategies]
    print(f"\n📊 LLM Quality:")
    print(f"  Avg Sharpe: {sum(llm_sharpes)/len(llm_sharpes):.4f}")
    print(f"  Best Sharpe: {max(llm_sharpes):.4f}")

# Champion updates
champion = json.load(open('artifacts/data/champion_strategy.json'))
print(f"\n🏆 Champion:")
print(f"  Current Sharpe: {champion['metrics']['sharpe_ratio']:.4f}")
print(f"  Last Updated: {champion['timestamp']}")

EOF
```

---

## 如果遇到问题

### 问题 1: LLM 配置加载失败
**症状**: `Failed to load LLM config`
**解决**:
```bash
# 还原配置
cp config/learning_system_backup_phase2.yaml config/learning_system.yaml

# 重新应用修复
python3 test_llm_config.py  # 验证配置
```

### 问题 2: 缺少 finlab 环境
**症状**: `Running without real finlab data`
**解决**: 在有 finlab 数据的环境中运行

### 问题 3: API 超时或失败
**症状**: LLM 调用失败
**解决**:
- 检查 GOOGLE_API_KEY
- 检查网络连接
- 查看 fallback 到 Factor Graph

---

## Phase 2 之后

### 如果成功 ✅
- LLM Sharpe ≥1.0
- Champion 有更新
- Diversity ≥30%

**下一步**: Phase 3 (20% rate, 50 gen)

### 如果需改进 ⚠️
- LLM Sharpe 0.5-1.0
- Champion 无更新

**下一步**:
- 延长测试到 50 代
- 或测试 Grok 模型

### 如果失败 ❌
- LLM Sharpe <0.5
- 多次失败

**下一步**: Debug + 模型比较

---

## 配置文件备份

所有原始配置已备份：
- ✅ `config/learning_system_backup_phase2.yaml`
- ✅ `artifacts/data/champion_strategy_backup_phase2_20251030_174753.json`

恢复命令：
```bash
cp config/learning_system_backup_phase2.yaml config/learning_system.yaml
```

---

**Status**: ✅ **READY TO RUN**
**Next Action**: 在 finlab 环境中执行 autonomous_loop.py
**Estimated Time**: 4-6 hours
**Cost**: $0
