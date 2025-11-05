# Phase 1 Dry-Run Test Plan: Strategy Quality Evaluation

**Date**: 2025-10-30
**Model**: Gemini 2.5 Flash Lite
**Purpose**: Evaluate LLM-generated strategy quality with dry-run protection

---

## Test Configuration

### Model Settings
- **Provider**: Google Gemini
- **Model**: gemini-2.5-flash-lite
- **Cost**: ~$0 per generation
- **Success Rate**: 90% (validated 2025-10-30)

### Test Parameters
- **Iterations**: 20
- **Innovation Rate**: 20% (4 LLM strategies expected)
- **Dry-Run**: ✅ Champion unchanged
- **Fallback**: Factor Graph (80% of iterations)

---

## Strategy Quality Evaluation Framework

### Performance Metrics (40% weight)
| Metric | Weight | Excellent | Good | Acceptable | Poor |
|--------|--------|-----------|------|------------|------|
| Sharpe Ratio | 20% | ≥2.0 | 1.0-2.0 | 0.5-1.0 | <0.5 |
| Annual Return | 10% | ≥30% | 15-30% | 5-15% | <5% |
| Calmar Ratio | 10% | ≥2.0 | 1.0-2.0 | 0.5-1.0 | <0.5 |

### Risk Metrics (30% weight)
| Metric | Weight | Excellent | Good | Acceptable | Poor |
|--------|--------|-----------|------|------------|------|
| Max Drawdown | 15% | <10% | 10-15% | 15-25% | >25% |
| Volatility | 15% | <15% | 15-25% | 25-35% | >35% |

### Practical Metrics (30% weight)
| Metric | Weight | Excellent | Good | Acceptable | Poor |
|--------|--------|-----------|------|------------|------|
| Win Rate | 10% | ≥60% | 50-60% | 40-50% | <40% |
| Position Count | 20% | ≥200 | 100-200 | 50-100 | <50 |

### Innovation Bonus (up to 15%)
- **Novel Factor Combinations**: +10% if uses non-predefined factors
- **Structural Innovation**: +5% if includes custom calculations

---

## Model Comparison Plan

After Flash Lite test completes, run same test with other models:

| Model | Cost (20 iter) | Expected Benefit |
|-------|---------------|------------------|
| **Flash Lite** | ~$0 | ✅ Baseline (90% success, nearly free) |
| **Grok Fast** | ~$0.06 (6¢) | ⭐ Better code quality? |
| **Gemini Pro** | ~$0.34 (34¢) | ⭐ Superior strategy quality? |

### Decision Matrix

| Flash Lite Quality | Next Action |
|-------------------|-------------|
| **Excellent** (Sharpe ≥1.0) | ✅ Skip other models, proceed to Phase 2 |
| **Good** (Sharpe 0.5-1.0) | ⏳ Consider testing Grok for comparison |
| **Mediocre** (Sharpe <0.5) | ⚠️ Test Grok and Pro to find better option |

---

## Success Criteria

### Must Achieve ✅
1. Complete all 20 iterations
2. Generate 3-4 LLM strategies (75-100% of expected)
3. LLM success rate ≥75%
4. Champion unchanged (2.4751 Sharpe)
5. No system crashes

### Should Achieve ⭐
1. Avg Sharpe ≥0.5
2. At least one strategy with Sharpe ≥1.0
3. Diversity ≥30%
4. Novel factor usage in 1+ strategies

### Stretch Goals 🚀
1. LLM avg > Factor Graph avg
2. LLM strategy beats Champion (2.4751)
3. 100% LLM success rate (4/4)

---

## Next Steps

1. **Set API Key**:
   ```bash
   export GOOGLE_API_KEY=your_gemini_api_key
   ```

2. **Review Config**:
   ```bash
   cat config/phase1_dryrun_flashlite.yaml
   ```

3. **Run Test** (when autonomous loop supports config loading):
   ```bash
   python3 artifacts/working/modules/autonomous_loop.py        --config config/phase1_dryrun_flashlite.yaml        --iterations 20        --dry-run
   ```

4. **Monitor Progress**:
   ```bash
   tail -f artifacts/data/phase1_dryrun_flashlite_history.jsonl
   ```

5. **Analyze Results** and compare models if needed

---

**Test Plan Version**: 1.0
**Status**: Ready to Execute
