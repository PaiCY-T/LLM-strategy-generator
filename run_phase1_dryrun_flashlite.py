#!/usr/bin/env python3
"""
Phase 1 Dry-Run Test: Gemini 2.5 Flash Lite Strategy Quality Evaluation

Purpose:
- Test LLM innovation with dry-run protection (Champion unchanged)
- Evaluate strategy quality across multiple dimensions
- Compare LLM strategies vs Factor Graph strategies
- Collect data for model comparison (Flash Lite vs Grok vs Pro)

Test Configuration:
- Model: Gemini 2.5 Flash Lite
- Iterations: 20
- Innovation Rate: 20% (4 LLM strategies expected)
- Dry-Run: Champion will NOT be updated

Success Criteria:
- ✅ 20 iterations complete
- ✅ 3-4 LLM strategies generated (75-100% of expected)
- ✅ LLM success rate ≥ 75%
- ✅ Average Sharpe ≥ 0.5
- ✅ Diversity ≥ 30%
- ✅ Champion unchanged (2.4751 Sharpe preserved)
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config.learning_system_config import LearningSystemConfig


class StrategyQualityEvaluator:
    """Evaluate strategy quality across multiple dimensions."""

    def __init__(self):
        self.metrics = []

    def evaluate_strategy(self, strategy_metrics: Dict) -> Dict:
        """
        Evaluate a single strategy's quality.

        Returns quality score and breakdown across dimensions.
        """
        quality_score = 0.0
        breakdown = {}

        # Performance metrics (40% weight)
        sharpe = strategy_metrics.get('sharpe_ratio', 0)
        annual_return = strategy_metrics.get('annual_return', 0)
        calmar = strategy_metrics.get('calmar_ratio', 0)

        performance_score = (
            self._normalize_sharpe(sharpe) * 0.20 +
            self._normalize_return(annual_return) * 0.10 +
            self._normalize_calmar(calmar) * 0.10
        )
        breakdown['performance'] = performance_score
        quality_score += performance_score

        # Risk metrics (30% weight)
        max_dd = abs(strategy_metrics.get('max_drawdown', 0))
        volatility = strategy_metrics.get('volatility', 0)

        risk_score = (
            self._normalize_drawdown(max_dd) * 0.15 +
            self._normalize_volatility(volatility) * 0.15
        )
        breakdown['risk'] = risk_score
        quality_score += risk_score

        # Practical metrics (30% weight)
        win_rate = strategy_metrics.get('win_rate', 0)
        position_count = strategy_metrics.get('position_count', 0)

        practical_score = (
            self._normalize_win_rate(win_rate) * 0.10 +
            self._normalize_position_count(position_count) * 0.20
        )
        breakdown['practical'] = practical_score
        quality_score += practical_score

        return {
            'quality_score': quality_score,
            'breakdown': breakdown,
            'metrics': strategy_metrics
        }

    def _normalize_sharpe(self, sharpe: float) -> float:
        """Normalize Sharpe ratio (0-1 scale, 0.20 weight)."""
        # 0.0 → 0.0, 1.0 → 0.10, 2.0 → 0.15, 3.0+ → 0.20
        if sharpe >= 3.0:
            return 0.20
        elif sharpe >= 2.0:
            return 0.15 + (sharpe - 2.0) * 0.05
        elif sharpe >= 1.0:
            return 0.10 + (sharpe - 1.0) * 0.05
        else:
            return max(0, sharpe * 0.10)

    def _normalize_return(self, annual_return: float) -> float:
        """Normalize annual return (0-1 scale, 0.10 weight)."""
        # 0% → 0.0, 15% → 0.05, 30%+ → 0.10
        if annual_return >= 0.30:
            return 0.10
        elif annual_return >= 0.15:
            return 0.05 + (annual_return - 0.15) / 0.15 * 0.05
        else:
            return max(0, annual_return / 0.15 * 0.05)

    def _normalize_calmar(self, calmar: float) -> float:
        """Normalize Calmar ratio (0-1 scale, 0.10 weight)."""
        # Similar to Sharpe
        if calmar >= 2.0:
            return 0.10
        elif calmar >= 1.0:
            return 0.05 + (calmar - 1.0) * 0.05
        else:
            return max(0, calmar * 0.05)

    def _normalize_drawdown(self, max_dd: float) -> float:
        """Normalize max drawdown (0-1 scale, 0.15 weight)."""
        # 0% → 0.15, 15% → 0.10, 30%+ → 0.0
        if max_dd >= 0.30:
            return 0.0
        elif max_dd >= 0.15:
            return 0.10 - (max_dd - 0.15) / 0.15 * 0.10
        else:
            return 0.10 + (0.15 - max_dd) / 0.15 * 0.05

    def _normalize_volatility(self, vol: float) -> float:
        """Normalize volatility (0-1 scale, 0.15 weight)."""
        # 0% → 0.15, 20% → 0.10, 40%+ → 0.0
        if vol >= 0.40:
            return 0.0
        elif vol >= 0.20:
            return 0.10 - (vol - 0.20) / 0.20 * 0.10
        else:
            return 0.10 + (0.20 - vol) / 0.20 * 0.05

    def _normalize_win_rate(self, win_rate: float) -> float:
        """Normalize win rate (0-1 scale, 0.10 weight)."""
        # 0% → 0.0, 50% → 0.05, 70%+ → 0.10
        if win_rate >= 0.70:
            return 0.10
        elif win_rate >= 0.50:
            return 0.05 + (win_rate - 0.50) / 0.20 * 0.05
        else:
            return max(0, win_rate / 0.50 * 0.05)

    def _normalize_position_count(self, count: int) -> float:
        """Normalize position count (0-1 scale, 0.20 weight)."""
        # <50 → penalty, 50-200 → good, >200 → excellent
        if count >= 200:
            return 0.20
        elif count >= 50:
            return 0.15 + (count - 50) / 150 * 0.05
        else:
            return max(0, count / 50 * 0.15)


def run_phase1_dryrun_test():
    """Run Phase 1 dry-run test with Flash Lite."""

    print("\n" + "="*80)
    print("Phase 1 Dry-Run Test: Gemini 2.5 Flash Lite")
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Model: Gemini 2.5 Flash Lite")
    print(f"Iterations: 20")
    print(f"Innovation Rate: 20% (4 LLM strategies expected)")
    print(f"Dry-Run: Champion will NOT be updated")
    print("="*80 + "\n")

    # Initialize quality evaluator
    evaluator = StrategyQualityEvaluator()

    # Results tracking
    results = {
        'test_start': datetime.now().isoformat(),
        'model': 'gemini-2.5-flash-lite',
        'config': 'config/phase1_dryrun_flashlite.yaml',
        'iterations_completed': 0,
        'llm_strategies': [],
        'factor_graph_strategies': [],
        'quality_comparison': {},
        'test_success': {},
    }

    print("\n⚠️  DRY-RUN TEST INSTRUCTIONS:")
    print("="*80)
    print("This is a DRY-RUN test script template.")
    print("To actually run the test, you need to:")
    print()
    print("1. Ensure autonomous loop supports config file loading:")
    print("   - Modify autonomous_loop.py to accept config_path parameter")
    print("   - Load config from phase1_dryrun_flashlite.yaml")
    print()
    print("2. Run the autonomous loop with dry-run config:")
    print("   ```bash")
    print("   export GOOGLE_API_KEY=your_api_key")
    print("   python3 -c \"")
    print("   from artifacts.working.modules.autonomous_loop import AutonomousLoop")
    print("   loop = AutonomousLoop(config_path='config/phase1_dryrun_flashlite.yaml')")
    print("   loop.run(max_iterations=20, dry_run=True)")
    print("   \"")
    print("   ```")
    print()
    print("3. After test completes, analyze results:")
    print("   - Check artifacts/data/phase1_dryrun_flashlite_history.jsonl")
    print("   - Check artifacts/data/phase1_dryrun_flashlite_innovations.jsonl")
    print("   - Review quality metrics")
    print()
    print("4. Compare with other models:")
    print("   - Run same test with Grok Code Fast 1")
    print("   - Run same test with Gemini 2.5 Pro")
    print("   - Compare quality scores across models")
    print("="*80)

    # Save test plan
    test_plan_path = project_root / "PHASE1_DRYRUN_TEST_PLAN.md"
    with open(test_plan_path, 'w', encoding='utf-8') as f:
        f.write(generate_test_plan())

    print(f"\n✅ Test plan saved to: {test_plan_path}")
    print("\n📋 Next Steps:")
    print("   1. Review test plan: PHASE1_DRYRUN_TEST_PLAN.md")
    print("   2. Set GOOGLE_API_KEY environment variable")
    print("   3. Modify autonomous loop to support config loading")
    print("   4. Execute test with dry-run protection")
    print("   5. Analyze strategy quality results")
    print("   6. Compare with Grok/Pro if needed")

    return results


def generate_test_plan() -> str:
    """Generate detailed test plan document."""
    return """# Phase 1 Dry-Run Test Plan: Strategy Quality Evaluation

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

### Data Collection
- Iteration history: `artifacts/data/phase1_dryrun_flashlite_history.jsonl`
- LLM innovations: `artifacts/data/phase1_dryrun_flashlite_innovations.jsonl`
- Quality metrics: `artifacts/data/phase1_dryrun_flashlite_quality_metrics.jsonl`
- Comparisons: `artifacts/data/phase1_dryrun_flashlite_comparisons.json`

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

## Success Criteria

### Must Achieve ✅
1. **Iterations**: Complete all 20 iterations
2. **LLM Usage**: Generate 3-4 LLM strategies (75-100% of expected)
3. **LLM Success**: ≥75% of LLM attempts succeed
4. **Champion Preservation**: Current champion (2.4751 Sharpe) unchanged
5. **No Crashes**: System stability throughout test

### Should Achieve ⭐
1. **Average Quality**: Avg Sharpe ≥ 0.5 across LLM strategies
2. **Best Quality**: At least one LLM strategy with Sharpe ≥ 1.0
3. **Diversity**: Population diversity ≥ 30%
4. **Innovation**: At least one LLM strategy uses novel factors

### Stretch Goals 🚀
1. **Superior Quality**: LLM avg Sharpe > Factor Graph avg Sharpe
2. **Breakthrough**: LLM strategy beats current Champion (2.4751)
3. **High Innovation**: 50%+ of LLM strategies use novel factors
4. **Zero Failures**: 100% LLM success rate (4/4)

---

## Execution Steps

### 1. Pre-Test Preparation
```bash
# Set API key
export GOOGLE_API_KEY=your_gemini_api_key

# Verify config file
cat config/phase1_dryrun_flashlite.yaml

# Check current champion
python3 -c "
from src.repository.hall_of_fame import HallOfFame
hof = HallOfFame()
champion = hof.get_current_champion()
print(f'Current Champion: {champion.metrics.sharpe_ratio:.4f} Sharpe')
"
```

### 2. Run Test
```bash
# Option A: If autonomous loop supports config loading
python3 artifacts/working/modules/autonomous_loop.py \
    --config config/phase1_dryrun_flashlite.yaml \
    --iterations 20 \
    --dry-run

# Option B: Manual integration (modify autonomous_loop.py)
# See implementation notes below
```

### 3. Monitor Progress
```bash
# Watch iteration history
tail -f artifacts/data/phase1_dryrun_flashlite_history.jsonl

# Check LLM innovations
cat artifacts/data/phase1_dryrun_flashlite_innovations.jsonl | jq .

# View quality metrics
cat artifacts/data/phase1_dryrun_flashlite_quality_metrics.jsonl | jq .
```

### 4. Post-Test Analysis
```bash
# Generate quality report
python3 analyze_phase1_results.py \
    --history artifacts/data/phase1_dryrun_flashlite_history.jsonl \
    --innovations artifacts/data/phase1_dryrun_flashlite_innovations.jsonl \
    --output PHASE1_QUALITY_REPORT.md
```

---

## Model Comparison Plan

After Flash Lite test completes, run same test with other models:

### Test 2: Grok Code Fast 1
```bash
# Update config
cp config/phase1_dryrun_flashlite.yaml config/phase1_dryrun_grok.yaml
# Change provider to xai, model to grok-code-fast-1

# Run test
python3 run_phase1_dryrun_test.py --model grok-code-fast-1
```

### Test 3: Gemini 2.5 Pro
```bash
# Update config
cp config/phase1_dryrun_flashlite.yaml config/phase1_dryrun_gemini_pro.yaml
# Change model to gemini-2.5-pro

# Run test
python3 run_phase1_dryrun_test.py --model gemini-2.5-pro
```

### Comparison Metrics
| Dimension | Flash Lite | Grok Fast | Gemini Pro |
|-----------|-----------|-----------|------------|
| Cost (20 iter) | ~$0 | ~$0.06 | ~$0.34 |
| Success Rate | ? | ? | ? |
| Avg Quality Score | ? | ? | ? |
| Best Sharpe | ? | ? | ? |
| Innovation Level | ? | ? | ? |
| Speed (avg) | ? | ? | ? |

---

## Implementation Notes

### Modifying Autonomous Loop for Config Loading

Add config_path parameter to AutonomousLoop.__init__():
- Load config from specified YAML file
- Override default config/learning_system.yaml

Add dry_run parameter to AutonomousLoop.run():
- When True, evaluate but don't update Champion
- Log comparisons for quality analysis

---

## Expected Outcomes

### Best Case 🎯
- LLM success rate: 100% (4/4)
- Avg Sharpe: >1.0
- Best Sharpe: >2.0
- Innovation: Novel factor combinations in 3+ strategies
- **Decision**: Proceed directly to Phase 3 (full activation)

### Good Case ✅
- LLM success rate: 75-100% (3-4/4)
- Avg Sharpe: 0.5-1.0
- Best Sharpe: 1.0-2.0
- Innovation: Novel factors in 1-2 strategies
- **Decision**: Proceed to Phase 2 (low rate test)

### Acceptable Case ⚠️
- LLM success rate: 50-75% (2-3/4)
- Avg Sharpe: 0.3-0.5
- Best Sharpe: 0.5-1.0
- Innovation: Minimal novel factors
- **Decision**: Test Grok or Pro for comparison

### Poor Case ❌
- LLM success rate: <50% (<2/4)
- Avg Sharpe: <0.3
- Best Sharpe: <0.5
- Innovation: No novel factors
- **Decision**: Debug issues before proceeding

---

## Risk Mitigation

### Dry-Run Protection
- ✅ Champion cannot be updated during test
- ✅ All LLM strategies evaluated but not promoted
- ✅ Safe to test without production impact

### Fallback Mechanisms
- ✅ Automatic Factor Graph fallback on LLM failure
- ✅ Retry logic (3 attempts) for transient errors
- ✅ Timeout protection (60s per generation)

### Data Preservation
- ✅ All strategies saved to disk
- ✅ Full iteration history recorded
- ✅ Quality metrics logged for analysis
- ✅ Can replay/analyze test results later

---

## Next Steps After Test

### If Flash Lite Quality is Good (Sharpe ≥ 0.5)
1. ✅ Skip Grok/Pro testing (cost savings)
2. ✅ Proceed to Phase 2 (5% innovation rate, 20 generations)
3. ✅ Enable Champion updates (dry_run=false)

### If Flash Lite Quality is Mediocre (Sharpe 0.3-0.5)
1. ⏳ Test Grok Code Fast 1 (6¢ for 20 iterations)
2. ⏳ Compare quality scores
3. ⏳ Select best model for Phase 2

### If All Models Poor (Sharpe <0.3)
1. ❌ Debug prompt template further
2. ❌ Review strategy validation criteria
3. ❌ Consider hybrid mode (mix YAML + code generation)

---

**Test Plan Version**: 1.0
**Last Updated**: 2025-10-30
**Status**: Ready to Execute
"""


if __name__ == '__main__':
    results = run_phase1_dryrun_test()

    # Save results
    results_path = Path('PHASE1_DRYRUN_RESULTS.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Test preparation complete")
    print(f"📄 Results will be saved to: {results_path}")
