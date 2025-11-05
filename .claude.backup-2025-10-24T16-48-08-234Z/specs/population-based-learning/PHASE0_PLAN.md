# Phase 0: Template Quick Test - Implementation Plan

**Duration**: 1 week (~20 hours)
**Goal**: Test if template-based generation can improve champion update rate from 0.5% → 5%+

---

## 🎯 Hypothesis (O3's Claim)

**Current Problem**:
- Champion update rate: 0.5% (1/200)
- 99.5% of generated strategies are worse than champion

**O3's Theory**:
- Root cause is **generation quality**, not search algorithm
- Template + improved prompt can solve the problem
- No need for complex population-based learning

**Test Hypothesis**:
```
IF template-guided generation + domain knowledge prompts
THEN champion update rate 0.5% → 5%+ (10x improvement)
SUCCESS: Proves O3 correct, skip population-based
FAILURE: Proves need for population-based learning
```

---

## 📋 Implementation Tasks

### Task 1: Create Template-Guided Parameter Generator (4 hours)

**File**: `src/generators/template_parameter_generator.py`

**Purpose**: Use LLM to intelligently select parameter combinations from MomentumTemplate.PARAM_GRID instead of generating free-form code.

**Design**:
```python
class TemplateParameterGenerator:
    """Generate parameters for MomentumTemplate using LLM guidance."""

    def __init__(self):
        self.template = MomentumTemplate()
        self.param_grid = self.template.PARAM_GRID

    def generate_parameters(
        self,
        iteration_num: int,
        champion_params: Optional[Dict] = None,
        feedback: Optional[str] = None
    ) -> Dict:
        """
        Use LLM to select smart parameter combination.

        Instead of generating Python code, LLM selects values from PARAM_GRID:
        - momentum_period: [5, 10, 20, 30]
        - ma_periods: [20, 60, 90, 120]
        - catalyst_type: ['revenue', 'earnings']
        - catalyst_lookback: [2, 3, 4, 6]
        - n_stocks: [5, 10, 15, 20]
        - stop_loss: [0.08, 0.10, 0.12, 0.15]
        - resample: ['W', 'M']
        - resample_offset: [0, 1, 2, 3, 4]

        LLM guided by:
        - Champion parameters (if exists)
        - Previous iteration feedback
        - Trading domain knowledge
        - Finlab-specific best practices
        """
        prompt = self._build_parameter_selection_prompt(
            iteration_num, champion_params, feedback
        )

        # Call LLM to get parameter selection
        response = call_llm(prompt)

        # Parse LLM response to extract parameter dict
        params = self._parse_parameter_response(response)

        # Validate params against PARAM_GRID
        validated_params = self._validate_params(params)

        return validated_params
```

**LLM Prompt Structure**:
```
You are a quantitative trading expert selecting parameters for a momentum strategy.

PARAMETER GRID (choose ONE value for each):
- momentum_period: [5, 10, 20, 30] days
  (5=very short-term, 10=short-term, 20=medium-term, 30=longer-term)
- ma_periods: [20, 60, 90, 120] days
  (20=1-month trend, 60=3-month, 90=4.5-month, 120=6-month)
- catalyst_type: ['revenue', 'earnings']
  (revenue=sales growth, earnings=ROE improvement)
...

CURRENT CHAMPION (if exists):
- Parameters: {champion_params}
- Sharpe: {champion_sharpe}
- Success patterns: {patterns}

FEEDBACK FROM PREVIOUS ITERATION:
{feedback}

TRADING DOMAIN KNOWLEDGE:
- Taiwan stock market characteristics
- Finlab data quality and limitations
- Risk management best practices
- Liquidity considerations

TASK: Select ONE value for each parameter that will likely OUTPERFORM champion.
Return as JSON: {"momentum_period": 10, "ma_periods": 60, ...}
```

**Expected Improvement**:
- LLM explores STRUCTURED parameter space (10,240 combinations)
- Instead of generating arbitrary code (infinite possibilities)
- Template enforces proven architecture (momentum + catalyst)
- Reduces "obviously bad" strategies from 99.5% to ~80%

---

### Task 2: Enhance Prompt with Trading Domain Knowledge (3 hours)

**File**: `artifacts/working/modules/prompt_template_v4_template_mode.txt`

**Purpose**: Create new prompt template specifically for template-guided parameter generation with Finlab domain expertise.

**Key Additions**:

1. **Finlab Dataset Catalog** (specific dataset guidance):
```
AVAILABLE FINLAB DATASETS:
- price:收盤價 (Close price - ALWAYS use for price-based factors)
- price:成交金額 (Trading value - REQUIRED for liquidity filters)
- etl:market_value (Market cap - use for size filters)
- fundamental_features:ROE稅後 (ROE - quality factor, needs smoothing)
- monthly_revenue:去年同月增減(%) (YoY revenue growth - monthly updates)
- institutional_investors_trading_summary:外陸資買賣超股數 (Foreign flow)

CRITICAL REQUIREMENTS:
- ALWAYS include liquidity filter: trading_value > 50M-100M TWD
- ALWAYS smooth fundamentals: .rolling(4).mean() for ROE
- ALWAYS use .shift(1) to avoid look-ahead bias
```

2. **Proven Success Patterns** (from analysis of generated_strategy_loop_iter3.py):
```
PROVEN PATTERNS (from successful strategies):
1. Multi-factor combination:
   - Momentum (technical) + Quality (fundamental) + Value (fundamental)
   - Rank normalization: .rank(axis=1, pct=True)
   - Weighted combination: 0.4 × momentum + 0.35 × quality + 0.25 × value

2. Essential filters (DO NOT skip):
   - Liquidity: trading_value.rolling(20).mean() > 70M TWD
   - Price: close > 20 TWD (avoid penny stocks)
   - Market cap: market_value > 10B TWD (focus on liquid stocks)

3. Risk management:
   - Stop loss: 8-12% (balance protection vs whipsaw)
   - Position limit: ≤20 stocks (balance concentration vs diversification)
   - Rebalancing: Monthly or Quarterly (reduce turnover)
```

3. **Anti-Patterns to Avoid** (common failures):
```
AVOID THESE FAILURES:
❌ No liquidity filter → unstable strategies
❌ Un-smoothed fundamentals → noisy signals
❌ Negative .shift() values → look-ahead bias
❌ Too many factors (>5) → overfitting
❌ Daily rebalancing → high transaction costs
❌ Penny stocks (price < 20) → manipulation risk
```

---

### Task 3: Create Strategy Validation Gates (3 hours)

**File**: `src/validation/strategy_validator.py`

**Purpose**: Pre-backtest validation to reject obviously flawed strategies BEFORE expensive 3-minute backtest.

**Design**:
```python
class StrategyValidator:
    """Validate strategy parameters before backtesting."""

    def validate_parameters(self, params: Dict) -> Tuple[bool, List[str]]:
        """
        Validate parameters against best practices.

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # 1. Liquidity protection
        if not self._has_liquidity_filter(params):
            errors.append("Missing liquidity filter (trading_value > threshold)")

        # 2. Risk management
        if params.get('stop_loss', 0) < 0.05 or params.get('stop_loss', 1) > 0.20:
            errors.append(f"Stop loss {params['stop_loss']} outside safe range [0.05, 0.20]")

        # 3. Position sizing
        n_stocks = params.get('n_stocks', 0)
        if n_stocks < 5:
            errors.append(f"Portfolio too concentrated ({n_stocks} stocks), min 5 recommended")
        if n_stocks > 30:
            errors.append(f"Portfolio too diversified ({n_stocks} stocks), max 30 recommended")

        # 4. Rebalancing frequency
        if params.get('resample') == 'D':
            errors.append("Daily rebalancing causes excessive transaction costs")

        return (len(errors) == 0, errors)

    def _has_liquidity_filter(self, params: Dict) -> bool:
        """Check if strategy includes liquidity filtering."""
        # For template mode: check if catalyst includes liquidity consideration
        # For free-form mode: would need AST analysis
        return True  # Template enforces this structurally
```

**Validation Gates**:
1. ✅ **Liquidity Filter**: Ensures trading value > threshold
2. ✅ **Risk Management**: Stop loss in reasonable range (5-20%)
3. ✅ **Position Sizing**: 5-30 stocks (balanced concentration)
4. ✅ **Rebalancing**: Weekly or slower (avoid daily churn)
5. ✅ **Parameter Bounds**: All values within PARAM_GRID

**Expected Benefit**: Reject 10-20% of bad strategies before backtesting → save 30-60 minutes per 50-iteration test.

---

### Task 4: Integrate Template Mode into Autonomous Loop (4 hours)

**File**: `artifacts/working/modules/autonomous_loop.py`

**Changes**:
```python
class AutonomousLoop:
    def __init__(
        self,
        ...,
        template_mode: bool = False,  # NEW PARAMETER
        template_name: str = "Momentum"  # NEW PARAMETER
    ):
        self.template_mode = template_mode
        if template_mode:
            self.param_generator = TemplateParameterGenerator()
            self.validator = StrategyValidator()
        ...

    def run_iteration(self, iteration_num: int):
        """Run single iteration with template mode support."""

        if self.template_mode:
            # TEMPLATE MODE: Generate parameters, not code
            params = self.param_generator.generate_parameters(
                iteration_num=iteration_num,
                champion_params=self.champion.parameters if self.champion else None,
                feedback=self.feedback_history
            )

            # Validate before backtesting
            is_valid, errors = self.validator.validate_parameters(params)
            if not is_valid:
                self.logger.warning(f"Parameter validation failed: {errors}")
                return None  # Skip this iteration

            # Generate strategy using template
            from src.templates.momentum_template import MomentumTemplate
            template = MomentumTemplate()
            report, metrics = template.generate_strategy(params)

            # Store generated parameters with results
            self.history.append({
                'iteration': iteration_num,
                'parameters': params,
                'metrics': metrics,
                'template': 'Momentum'
            })
        else:
            # ORIGINAL MODE: LLM generates free-form code
            code = self.llm_generator.generate_strategy(...)
            # ... existing code path
```

**Configuration**:
```python
# run_50iteration_template_test.py
loop = AutonomousLoop(
    template_mode=True,           # ← Enable template mode
    template_name="Momentum",     # ← Use MomentumTemplate
    model="gemini-2.5-flash",
    max_iterations=50
)
```

---

### Task 5: Create 50-Iteration Test Script (2 hours)

**File**: `run_50iteration_template_test.py`

**Purpose**: Test template mode with 50 iterations and compare to baseline.

**Design**:
```python
#!/usr/bin/env python3
"""Phase 0: Template Mode 50-iteration Test

Tests hypothesis: Template + improved prompts → 10x champion update improvement
"""

from artifacts.working.modules.autonomous_loop import AutonomousLoop
from tests.integration.extended_test_harness import ExtendedTestHarness
import json
from datetime import datetime

def main():
    """Run 50-iteration test with template mode."""

    print("=" * 70)
    print("PHASE 0: TEMPLATE MODE TEST (50 ITERATIONS)")
    print("=" * 70)
    print(f"Start time: {datetime.now()}")
    print()

    # Create test harness with template mode
    harness = ExtendedTestHarness(
        test_name="phase0_template_test",
        max_iterations=50,
        model="gemini-2.5-flash",
        save_checkpoints=True,
        template_mode=True,        # ← KEY DIFFERENCE
        template_name="Momentum"
    )

    # Run test
    print("Starting 50-iteration template test...")
    results = harness.run()

    # Analyze results
    print("\n" + "=" * 70)
    print("RESULTS ANALYSIS")
    print("=" * 70)

    champion_updates = results['champion_update_count']
    total_iterations = results['total_iterations']
    update_rate = champion_updates / total_iterations * 100

    print(f"Total iterations: {total_iterations}")
    print(f"Champion updates: {champion_updates}")
    print(f"Update rate: {update_rate:.2f}%")
    print()

    baseline_rate = 0.5
    print(f"Baseline (free-form LLM): {baseline_rate}%")
    print(f"Template mode: {update_rate:.2f}%")
    print(f"Improvement: {update_rate / baseline_rate:.1f}x")
    print()

    # Success criteria
    target_rate = 5.0
    if update_rate >= target_rate:
        print("✅ SUCCESS: Template mode achieves >5% update rate")
        print("   → O3's hypothesis CONFIRMED")
        print("   → Can skip population-based learning")
    else:
        print("❌ INSUFFICIENT: Template mode <5% update rate")
        print(f"   → Need {target_rate / update_rate:.1f}x more improvement")
        print("   → Proceed to Phase 1: Population-based learning")

    print()
    print(f"End time: {datetime.now()}")
    print("=" * 70)

    # Save detailed results
    results_file = f"phase0_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")

if __name__ == '__main__':
    main()
```

**Expected Runtime**: 50 iterations × 3-6 min = 2.5-5 hours

---

### Task 6: Results Analysis & Decision (4 hours)

**Analysis Script**: `scripts/analyze_phase0_results.py`

**Metrics to Track**:
1. **Champion Update Rate**: Primary metric (target: ≥5%)
2. **Average Sharpe**: Quality of generated strategies
3. **Variance**: Strategy diversity
4. **Parameter Diversity**: Are different parameter combinations explored?
5. **Validation Pass Rate**: % strategies passing pre-backtest validation

**Decision Matrix**:

| Champion Update Rate | Avg Sharpe | Decision |
|---------------------|------------|----------|
| ≥10% | >1.2 | ✅ SUCCESS - Use template mode, skip population-based |
| 5-10% | >1.0 | ⚠️ PARTIAL - Consider hybrid approach |
| <5% | Any | ❌ FAILURE - Proceed to Phase 1 (population-based) |

**Report Template**:
```markdown
# Phase 0 Results Report

## Test Configuration
- Iterations: 50
- Mode: Template-guided parameter generation
- Template: MomentumTemplate
- Model: gemini-2.5-flash

## Primary Metrics
- Champion update rate: X.X% (baseline: 0.5%)
- Improvement factor: XXx
- Average Sharpe: X.XX
- Best Sharpe: X.XX
- Variance: X.XXX

## Parameter Exploration
- Unique parameter combinations: XX/50
- Most explored parameters: {analysis}
- Least explored parameters: {analysis}

## Validation Results
- Validation pass rate: XX%
- Common validation failures: {list}

## Decision
[✅/❌] Template mode meets 5% threshold
[Proceed to / Skip] Phase 1: Population-based learning

## Insights
{Key learnings from test}
```

---

## 📊 Expected Outcomes

### Scenario A: Success (Update Rate ≥5%)
```
Champion update rate: 0.5% → 7.5% (15x improvement)
Conclusion: O3 was correct - generation quality was the problem
Action: Continue with template mode, optimize prompts further
Savings: 80-100 hours (skip population-based implementation)
```

### Scenario B: Partial Success (Update Rate 2-5%)
```
Champion update rate: 0.5% → 3.2% (6x improvement)
Conclusion: Template helps but not enough
Action: Hybrid - template as baseline + population-based variation
Benefit: Reduced population-based search space
```

### Scenario C: Failure (Update Rate <2%)
```
Champion update rate: 0.5% → 1.8% (3x improvement)
Conclusion: Search algorithm IS the problem (Gemini was right)
Action: Proceed with full population-based learning (Phase 1)
Investment: 50-80 hours for complete implementation
```

---

## 🎯 Success Criteria

**Primary** (Must Meet):
- Champion update rate ≥5% (10x baseline)

**Secondary** (Nice to Have):
- Average Sharpe >1.0
- Validation pass rate >90%
- Parameter diversity >30 unique combinations

**Failure Triggers**:
- Update rate <2% after 50 iterations
- All strategies converge to same parameters
- Validation failures >20%

---

## ⏱️ Timeline

| Task | Duration | Dependencies |
|------|----------|--------------|
| 1. Template Parameter Generator | 4h | None |
| 2. Enhanced Prompt Template | 3h | None |
| 3. Strategy Validator | 3h | None |
| 4. Autonomous Loop Integration | 4h | Tasks 1, 2, 3 |
| 5. 50-Iteration Test Script | 2h | Task 4 |
| 6. Results Analysis | 4h | Task 5 completion |
| **TOTAL** | **20h** | **~1 week** |

---

## 🔄 Next Steps After Phase 0

**If Success (≥5% update rate)**:
1. Document template mode as standard approach
2. Optimize prompt further for 10%+ update rate
3. Skip population-based learning (save 80-100h)
4. Focus on out-of-sample validation and robustness

**If Failure (<5% update rate)**:
1. Document findings in Phase 0 report
2. Proceed to Phase 1: Population-based Learning
3. Use template as one of the evolution operators
4. Implement all critical fixes from Gemini/O3 reviews

---

**Status**: 📋 READY TO START
**Estimated Start**: 2025-10-17
**Estimated Completion**: 2025-10-24
