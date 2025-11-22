# LLM vs Factor Graph: Comprehensive Architecture Comparison

**Date**: 2025-01-14
**Context**: Phase 2 Analysis - Understanding fundamental architectural differences

---

## Executive Summary

Your initial understanding captured **one dimension** of the difference (innovation approach), but the architectural divergence is much deeper and multi-dimensional. This document provides a complete comparison across **10 architectural dimensions**.

### TL;DR

| Dimension | LLM Strategy | Factor Graph |
|-----------|--------------|--------------|
| **Innovation** | 🆕 Creates new factors/logic | 🔧 Optimizes within factor space |
| **Structure** | 📄 Monolithic (single function) | 🧩 Compositional (DAG of factors) |
| **Execution** | ⚡ Direct (function call) | 🔄 Orchestrated (topological sort) |
| **State** | 🚫 Stateless (rebalance-based) | ⚠️ Mixed (can have stateful factors) |
| **Contract** | 💬 Implicit (variable name) | 📋 Explicit (validation rules) |
| **Interpretability** | 🌫️ Black box (hard to explain) | 💎 Transparent (factor composition) |
| **Maintainability** | ⚠️ Monolith evolution | ✅ Modular evolution |
| **Reusability** | ❌ Strategy-specific | ✅ Factor-level reuse |
| **Mutation** | 📝 Full code rewrite | 🎯 Surgical DAG edits |
| **Debugging** | 🔍 Hard (inline logic) | ✅ Easy (factor isolation) |

---

## Dimension 1: Innovation Approach (Your Original Understanding)

### LLM: Generative Innovation
```python
# LLM can create entirely NEW factors/logic
def strategy(data):
    # NEW: Combined momentum with ROE filter
    momentum = close.pct_change(20)
    roe_filter = (roe > 15).shift(1)  # ← Creative combination

    # NEW: Ranking with PB ratio
    pb_rank = pb_ratio.rank(axis=1, ascending=True)

    # NEW: Multi-factor synthesis
    position = (momentum_rank < 0.2) & roe_filter & (pb_rank < 0.3)
    return position
```

**Characteristics**:
- ✅ Unbounded creativity (can invent new combinations)
- ✅ Can discover novel patterns LLM learned from training data
- ✅ Not constrained by pre-defined factor library
- ❌ May generate syntactically valid but financially meaningless logic
- ❌ No guarantee of factor reusability

### Factor Graph: Combinatorial Optimization
```python
# Factor Graph optimizes WITHIN factor space
strategy = Strategy(id="optimized_strategy")

# Use EXISTING factors from registry
momentum_factor = registry.create_factor("momentum_factor", params={"period": 20})
breakout_factor = registry.create_factor("breakout_factor", params={"window": 55})

# Mutation: Change parameters, add/remove/replace factors
# NOT creating new factor logic
strategy.add_factor(momentum_factor, depends_on=[])
strategy.add_factor(breakout_factor, depends_on=[])
```

**Characteristics**:
- ✅ Systematic exploration of factor combinations
- ✅ Guaranteed factor validity (registered in library)
- ✅ Parameter optimization within defined ranges
- ❌ Cannot discover factors outside registry
- ❌ Innovation limited to composition, not creation

**Your Understanding**: ✅ **CORRECT** - This is a fundamental difference!

---

## Dimension 2: Code Structure

### LLM: Monolithic Architecture
```python
def strategy(data):
    # 100-120 lines of inline logic
    close = data.get('etl:adj_close')
    trading_value = data.get('price:成交金額')
    operating_margin = data.get('fundamental_features:營業利益率')

    # All logic in one function
    liquidity_filter = trading_value.rolling(20).mean() > 150_000_000
    momentum_60d = close.pct_change(60).shift(1)
    combined_momentum = 0.6 * momentum_20d + 0.4 * momentum_60d
    quality_filter = avg_operating_margin > quantile(0.7)

    # Final output
    position = (selection_candidates <= 50)
    return position
```

**Properties**:
- Single entry point: `strategy(data) → position`
- All dependencies implicit (variable scoping)
- No decomposition into reusable components
- Hard to test individual logic pieces

### Factor Graph: Compositional Architecture
```python
# DAG of independent, composable factors
class MomentumFactor(Factor):
    inputs = ["close"]
    outputs = ["momentum"]
    def execute(self, data, params):
        return close.pct_change(params["period"])

class BreakoutFactor(Factor):
    inputs = ["high", "low", "close"]
    outputs = ["breakout_signal"]
    def execute(self, data, params):
        # Independent, testable logic
        ...

# Strategy as composition
strategy.add_factor(momentum_factor)  # Node 1
strategy.add_factor(breakout_factor)   # Node 2
strategy.add_factor(exit_factor, depends_on=[breakout_factor.id])  # Node 3 (depends on Node 2)
```

**Properties**:
- Multiple entry points (each factor independently executable)
- Explicit dependencies (DAG edges)
- Each factor is independently testable/reusable
- Clear separation of concerns

**Impact**:
- **Testing**: LLM requires end-to-end tests, Factor Graph enables unit tests per factor
- **Debugging**: LLM failures are monolithic, Factor Graph can isolate failing factor
- **Reusability**: LLM strategies are one-off, Factor Graph factors are library assets

---

## Dimension 3: Execution Flow

### LLM: Direct Execution
```
┌─────────────────────────────────┐
│  1. Call strategy(data)         │
│  2. Execute all logic inline    │
│  3. Return position DataFrame   │
│  4. Pass to sim()               │
└─────────────────────────────────┘
```

**Execution Path**:
```python
position = strategy(data)  # All computation happens here
position = position.loc[start_date:end_date]
report = sim(position, fee_ratio, tax_ratio, resample="M")
```

**Characteristics**:
- Simple: Single function call
- Fast: No orchestration overhead
- Opaque: Can't inspect intermediate steps

### Factor Graph: Orchestrated Execution
```
┌─────────────────────────────────┐
│  1. Build DAG from factors      │
│  2. Topological sort            │
│  3. Execute factors in order    │
│  4. Store outputs in Container  │
│  5. Validate final 'position'   │
│  6. Return position matrix      │
└─────────────────────────────────┘
```

**Execution Path**:
```python
# Phase 1: Build execution plan
execution_order = strategy.get_execution_order()  # Topological sort

# Phase 2: Execute factors
container = FinLabDataFrame(data)
for factor in execution_order:
    outputs = factor.execute(container, factor.parameters)
    container.add_matrices(outputs)

# Phase 3: Extract final output
position = container.get_matrix('position')
report = sim(position, ...)
```

**Characteristics**:
- Complex: Multi-phase execution
- Inspectable: Can examine intermediate outputs
- Validated: Explicit checks at each stage
- Overhead: ~10-20% performance cost for orchestration

---

## Dimension 4: State Management

### LLM: Stateless (Rebalance-Based)
```python
def strategy(data):
    # Compute target positions at each rebalance point
    # NO state tracking across periods

    momentum = close.pct_change(20)
    position = (momentum > 0.1)  # Simple boolean

    # Rebalanced monthly - no intra-period state
    return position

# Execution
report = sim(position, resample="M")  # ← Rebalance monthly
```

**Properties**:
- Each rebalance period is independent
- No memory of previous positions/entry prices
- Cannot implement intra-period exits (trailing stop)
- Simpler mental model

### Factor Graph: Mixed (Stateless + Potential for Stateful)
```python
# Stateless factors (current Phase 2 implementation)
class RollingTrailingStopFactor(Factor):
    inputs = ["close"]  # ← Only needs price, not positions
    outputs = ["rolling_trailing_stop_signal"]

    def execute(self, data, params):
        highest = close.rolling(params["lookback"]).max()
        signal = close < highest * (1 - params["trail_percent"])
        return signal

# Stateful factors (Phase 1 - failed due to architecture)
class TrailingStopFactor(Factor):
    inputs = ["close", "positions", "entry_price"]  # ← NEEDS STATE
    outputs = ["trailing_stop_signal"]

    def execute(self, data, params):
        # Requires knowing actual entry price
        # Can only work with custom backtest engine
        ...
```

**Current Reality** (Phase 2):
- Factor Graph uses **stateless approximations** (rolling windows)
- True stateful factors blocked by FinLab API limitations
- Both LLM and Factor Graph constrained to stateless patterns

---

## Dimension 5: Validation Contract

### LLM: Implicit Contract
```python
def strategy(data):
    # ... complex logic ...
    position = combined_signal.fillna(False)  # ← Must name it 'position'
    return position  # ← Must return DataFrame

# Validation happens in backtest executor
if 'position' not in locals():
    raise ValueError("Strategy must create 'position' variable")
```

**Contract Requirements** (implicit):
- Variable must be named `position` (or `positions`, `signal`, `signals`)
- Must return DataFrame with (Dates × Symbols) shape
- Must handle NaN values
- Must be boolean or numeric (0/1)

**Enforcement**: Runtime error if violated

### Factor Graph: Explicit Contract
```python
# Validation happens in Strategy class
def validate_data(self, container):
    position_signal_names = ["position", "positions", "signal", "signals"]
    all_outputs = []
    for factor in self.factors.values():
        all_outputs.extend(factor.outputs)

    has_position_signal = any(
        output in position_signal_names
        for output in all_outputs
    )

    if not has_position_signal:
        raise ValueError(
            f"Strategy must have at least one factor producing "
            f"position signals (columns: {position_signal_names}). "
            f"Current outputs: {sorted(all_outputs)}."
        )
```

**Contract Requirements** (explicit):
- At least one factor must output: "position", "positions", "signal", or "signals"
- Checked BEFORE execution
- Clear error messages with diagnostic info

**Enforcement**: Pre-execution validation

**Impact**:
- **LLM**: Failures discovered late (during/after execution)
- **Factor Graph**: Failures caught early (before execution)

---

## Dimension 6: Interpretability

### LLM: Black Box
```python
# What does this strategy actually do?
def strategy(data):
    close = data.get('etl:adj_close')
    trading_value = data.get('price:成交金額')
    roe = data.get('fundamental_features:ROE稅後')
    revenue_growth = data.get('fundamental_features:營收成長率')

    # 50 lines of complex logic...

    combined_signal = (
        (avg_trading_value > 150_000_000) &
        (roe > 15).shift(1) &
        (revenue_growth > 0.05).shift(1) &
        (momentum_rank <= momentum_rank.count(axis=1) * 0.20) &
        (pb_rank <= pb_rank.count(axis=1) * 0.30)
    )

    position = combined_signal.astype(float)
    return position
```

**Questions hard to answer**:
- Which factor contributes most to performance?
- Can we remove the ROE filter without hurting Sharpe?
- What's the correlation between momentum and PB rank?
- Which stocks are selected and why?

**Interpretability**: ⚠️ **Low** - Requires reading entire function

### Factor Graph: Transparent
```python
# Strategy composition is explicit
strategy = Strategy(id="transparent_strategy")

# Factor 1: Momentum filter
momentum_factor = registry.create_factor(
    "momentum_factor",
    parameters={"momentum_period": 20}
)

# Factor 2: Entry signal
breakout_factor = registry.create_factor(
    "breakout_factor",
    parameters={"entry_window": 20}
)

# Factor 3: Exit logic
exit_factor = registry.create_factor(
    "rolling_trailing_stop_factor",
    parameters={"trail_percent": 0.10, "lookback_periods": 20}
)

# Explicit dependencies
strategy.add_factor(momentum_factor, depends_on=[])
strategy.add_factor(breakout_factor, depends_on=[])
strategy.add_factor(exit_factor, depends_on=[momentum_factor.id, breakout_factor.id])
```

**Questions easy to answer**:
- Which factors are used? `strategy.list_factors()`
- What are the parameters? `strategy.get_factor_params(factor_id)`
- What are the dependencies? `strategy.dag.edges()`
- Can we ablate factors? `strategy.remove_factor(factor_id)` and re-test

**Interpretability**: ✅ **High** - DAG structure is self-documenting

---

## Dimension 7: Maintainability & Evolution

### LLM: Monolithic Evolution
```python
# Iteration 1
def strategy_v1(data):
    # 100 lines of logic
    momentum = close.pct_change(20)
    position = momentum > 0
    return position

# Iteration 2: Modify to add liquidity filter
def strategy_v2(data):
    # 120 lines of logic (FULL REWRITE)
    momentum = close.pct_change(20)
    liquidity = trading_value.rolling(20).mean() > 150_000_000  # ← NEW
    position = (momentum > 0) & liquidity  # ← MODIFIED
    return position

# Iteration 3: Add value filter
def strategy_v3(data):
    # 140 lines of logic (ANOTHER FULL REWRITE)
    # ... copy all previous logic ...
    pb_filter = pb_ratio < quantile(0.25)  # ← NEW
    position = (momentum > 0) & liquidity & pb_filter  # ← MODIFIED
    return position
```

**Evolution Pattern**:
- ❌ No incremental changes (full function rewrites)
- ❌ Hard to track what changed between versions
- ❌ Risk of regression (might break existing logic)
- ❌ Difficult code review (compare entire functions)

### Factor Graph: Modular Evolution
```python
# Iteration 1: Base strategy
strategy_v1 = Strategy(id="v1")
strategy_v1.add_factor(momentum_factor)
# DAG: [momentum_factor]

# Iteration 2: Add liquidity filter (SURGICAL CHANGE)
strategy_v2 = strategy_v1.copy()
liquidity_factor = registry.create_factor("liquidity_filter_factor")
strategy_v2.add_factor(liquidity_factor)
# DAG: [momentum_factor, liquidity_factor]

# Iteration 3: Add value filter (SURGICAL CHANGE)
strategy_v3 = strategy_v2.copy()
value_factor = registry.create_factor("pb_value_filter_factor")
strategy_v3.add_factor(value_factor)
# DAG: [momentum_factor, liquidity_factor, value_factor]

# What changed? Diff the DAGs
added_factors = set(strategy_v3.factors) - set(strategy_v2.factors)
# Output: {'pb_value_filter_factor'}
```

**Evolution Pattern**:
- ✅ Incremental changes (add/remove/replace factors)
- ✅ Easy to track changes (DAG diff)
- ✅ Low regression risk (existing factors unchanged)
- ✅ Easy code review (review new factor only)

---

## Dimension 8: Reusability

### LLM: Strategy-Specific Logic
```python
# Iteration 5 strategy
def strategy_iter5(data):
    # ... 100 lines ...
    momentum_rank = combined_momentum.rank(axis=1, ascending=False)
    # This momentum logic is LOCKED in this strategy
    # Cannot reuse in other strategies without copy-paste

# Iteration 13 strategy
def strategy_iter13(data):
    # ... 100 lines ...
    momentum_rank = momentum_20d.rank(axis=1, ascending=False)
    # DUPLICATED momentum logic (slightly different)
    # No code sharing between strategies
```

**Reusability**: ❌ **None**
- Each strategy is independent monolith
- Common patterns duplicated across strategies
- No shared library of logic components

### Factor Graph: Factor Library
```python
# Factor library (reusable components)
# src/factor_library/momentum_factors.py
class MomentumFactor(Factor):
    """Reusable momentum calculation."""
    category = FactorCategory.MOMENTUM
    inputs = ["close"]
    outputs = ["momentum"]

# Strategy 1 uses it
strategy_1.add_factor(
    registry.create_factor("momentum_factor", params={"period": 20})
)

# Strategy 2 also uses it (different parameters)
strategy_2.add_factor(
    registry.create_factor("momentum_factor", params={"period": 60})
)

# Strategy 3 uses same factor
strategy_3.add_factor(
    registry.create_factor("momentum_factor", params={"period": 20})
)
```

**Reusability**: ✅ **High**
- 13 factors in library, used across all strategies
- Common patterns centralized (momentum, breakout, filters)
- Changes to factor logic benefit all strategies using it
- Growing library becomes increasingly valuable

---

## Dimension 9: Mutation Mechanism

### LLM: Full Code Generation
```python
# Mutation: LLM rewrites entire strategy
prompt = f"""
Champion Strategy Code:
{champion_code}  # ← Provide full 100-line function

Champion Metrics:
Sharpe: {sharpe}, Max DD: {mdd}

Task: Improve Sharpe Ratio by modifying the strategy.
Generate COMPLETE strategy code.
"""

new_strategy_code = llm.generate(prompt)
# Output: Entirely new 120-line function
```

**Mutation Types**:
1. **Modification**: LLM edits parts of champion code
2. **Creation**: LLM generates novel strategy from scratch
3. **Hybrid**: LLM combines patterns from multiple champions

**Granularity**: ⚠️ **Coarse-grained**
- Smallest change unit: entire function
- Cannot target specific logic components
- Hard to predict what LLM will change

### Factor Graph: Surgical DAG Edits
```python
# Mutation Tier 1: Parameter tuning
mutator.mutate_parameters(
    strategy=current_strategy,
    factor_id="momentum_factor",
    new_params={"momentum_period": 30}  # ← Targeted change
)

# Mutation Tier 2: Structural changes
mutator.replace_factor(
    strategy=current_strategy,
    old_factor="momentum_factor",
    new_factor="ma_filter_factor"  # ← Same category, different factor
)

mutator.add_factor(
    strategy=current_strategy,
    new_factor="liquidity_filter_factor",
    depends_on=[]  # ← Add new node to DAG
)

mutator.remove_factor(
    strategy=current_strategy,
    factor_id="outdated_factor"  # ← Remove node from DAG
)

# Mutation Tier 3: Logic mutation (future)
mutator.mutate_factor_logic(
    factor_id="custom_factor",
    ast_transformation=...  # ← AST-level edits
)
```

**Mutation Types**:
1. **Tier 1 (Parameters)**: Adjust factor parameters within ranges
2. **Tier 2 (Structure)**: Add/remove/replace factors in DAG
3. **Tier 3 (Logic)**: AST-based factor code mutations

**Granularity**: ✅ **Fine-grained**
- Smallest change unit: single parameter or factor
- Precise targeting of components
- Predictable mutation effects

---

## Dimension 10: Debugging & Failure Analysis

### LLM: Monolithic Debugging
```python
# Strategy fails
def strategy(data):
    # ... 100 lines ...
    position = combined_signal.astype(float)
    return position

# Error: KeyError: 'return_20d'
# Where is the bug?
# → Must read entire function to find where 'return_20d' is used
# → Could be defined earlier and typo'd later
# → Or never defined at all
```

**Debugging Difficulty**: ⚠️ **High**
- Error location unclear (could be anywhere in 100 lines)
- Hard to isolate failing logic
- Difficult to reproduce in isolation
- Full function context needed

### Factor Graph: Isolated Debugging
```python
# Strategy fails
strategy.add_factor(momentum_factor)
strategy.add_factor(breakout_factor)
strategy.add_factor(exit_factor, depends_on=[breakout_factor.id])

# Error: ValueError: Strategy must have at least one factor producing position signals
# Where is the bug?
# → Check factor outputs: momentum_factor.outputs → ["momentum"]
# → Check factor outputs: breakout_factor.outputs → ["breakout_signal"]
# → Check factor outputs: exit_factor.outputs → ["rolling_trailing_stop_signal"]
# → FOUND: No factor produces "position"! Missing SignalToPositionFactor
```

**Debugging Difficulty**: ✅ **Low**
- Error message points to specific validation check
- Can test each factor independently
- DAG structure makes dependencies explicit
- Isolated factor testing possible

---

## Summary Table: 10 Dimensions

| # | Dimension | LLM | Factor Graph | Advantage |
|---|-----------|-----|--------------|-----------|
| 1 | **Innovation** | Generative (creates new factors) | Combinatorial (optimizes within space) | **LLM** (creativity) |
| 2 | **Structure** | Monolithic (single function) | Compositional (DAG) | **Factor Graph** (modularity) |
| 3 | **Execution** | Direct (one function call) | Orchestrated (topological sort) | **LLM** (simplicity) |
| 4 | **State** | Stateless (rebalance-based) | Mixed (stateless + potential stateful) | **Tie** (both limited by FinLab API) |
| 5 | **Contract** | Implicit (variable name) | Explicit (validation rules) | **Factor Graph** (early failure detection) |
| 6 | **Interpretability** | Black box (hard to explain) | Transparent (DAG visualization) | **Factor Graph** (explainability) |
| 7 | **Maintainability** | Monolith evolution | Modular evolution | **Factor Graph** (incremental changes) |
| 8 | **Reusability** | Strategy-specific | Factor library | **Factor Graph** (shared components) |
| 9 | **Mutation** | Coarse-grained (full rewrite) | Fine-grained (surgical edits) | **Factor Graph** (precision) |
| 10 | **Debugging** | Monolithic (whole function) | Isolated (per factor) | **Factor Graph** (testability) |

---

## Strategic Implications

### When to Use LLM
1. **Exploration Phase**: Discover novel factor combinations
2. **Rapid Prototyping**: Quickly test new ideas
3. **Unconstrained Search**: When factor space is unknown
4. **Creative Innovation**: Generate unexpected patterns

### When to Use Factor Graph
1. **Exploitation Phase**: Optimize known factor combinations
2. **Production Deployment**: Maintainable, debuggable strategies
3. **Systematic Search**: Exhaustive parameter optimization
4. **Knowledge Building**: Accumulate reusable factor library

### Hybrid Approach (Current System)
**30% LLM + 70% Factor Graph**:
- LLM discovers novel patterns → Extract successful factors → Add to Factor Graph library
- Factor Graph systematically optimizes → Plateaus → LLM explores new directions
- Continuous cycle of exploration (LLM) and exploitation (Factor Graph)

---

## Phase 2 Impact on Architecture

### Problem Discovered
**Both LLM and Factor Graph lack "signal-to-position" conversion layer**:
- LLM implements it **inline** (implicit)
- Factor Graph **missing** it (explicit architecture gap)

### Current Situation
```
LLM:     [inline logic] → position ✅
Factor Graph: [factors] → signals → [MISSING] → position ❌
```

### After SignalToPositionFactor Implementation
```
LLM:     [inline logic] → position ✅
Factor Graph: [factors] → signals → [SignalToPositionFactor] → position ✅
```

**This closes a critical architectural gap while preserving all other differences.**

---

## Conclusion

Your initial understanding (innovation approach) was **correct but incomplete**. The LLM vs Factor Graph comparison spans **10 architectural dimensions**, each with different trade-offs:

**LLM Strengths**:
- Unbounded creativity
- Simple execution
- Rapid experimentation

**Factor Graph Strengths**:
- Modularity & reusability
- Interpretability & explainability
- Maintainability & debuggability
- Systematic optimization

**The Hybrid System leverages both**, using LLM for exploration and Factor Graph for exploitation. Phase 2's discovery of the missing conversion layer affects **both** architectures, though it manifests differently in each.
