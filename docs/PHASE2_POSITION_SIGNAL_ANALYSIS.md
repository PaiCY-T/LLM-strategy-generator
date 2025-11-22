# Phase 2 Position Signal Analysis

**Date**: 2025-01-14
**Context**: Phase 2 Stateless EXIT Factors Implementation
**Issue**: 13/20 Factor Graph strategies fail with position signal validation error

## Executive Summary

Phase 2 successfully resolved the stateful EXIT factor architectural issue (stateful → stateless), but exposed a deeper architectural gap: **the Factor Graph system lacks a standard abstraction layer for converting intermediate signals into the final `position` matrix**.

### Impact
- **13/20 Factor Graph strategies fail** (65% failure rate)
- **Overall success rate**: 2/20 (10%)
- **Error type**: "Strategy must have at least one factor producing position signals"

---

## Problem Analysis

### 1. Core Issue: Missing Signal-to-Position Conversion Layer ⚠️ CRITICAL

**Current Template Strategy Outputs** (`iteration_executor.py:720-756`):
```python
# Factor 1: momentum_factor
outputs = ["momentum"]

# Factor 2: breakout_factor
outputs = ["breakout_signal"]

# Factor 3: rolling_trailing_stop_factor (Phase 2 fix)
outputs = ["rolling_trailing_stop_signal"]
```

**Validation Requirements** (`strategy.py:519-534`):
```python
position_signal_names = ["position", "positions", "signal", "signals"]

has_position_signal = any(
    output in position_signal_names
    for output in all_outputs
)

if not has_position_signal:
    raise ValueError(
        f"Strategy must have at least one factor producing position signals "
        f"(columns: {position_signal_names}). "
        f"Current outputs: {sorted(all_outputs)}."
    )
```

**Gap Identified**:
- Template produces 3 intermediate signals: `momentum`, `breakout_signal`, `rolling_trailing_stop_signal`
- Validation requires at least one of: `position`, `positions`, `signal`, `signals`
- **NO factor converts intermediate signals → final position matrix**

### 2. Architecture Assessment

**Factor Registry Analysis**:
- Total registered factors: 13
- Factors producing "position" output: **0** (grep confirmed)
- EXIT category factors: 6 (all produce exit signals, not positions)

**Existing Infrastructure**:
- `FactorCategory.SIGNAL` exists for "composite signals combining multiple factors"
- `SignalCombiner` exists but only combines signals, doesn't produce positions
- No standard "final stage" factor pattern established

**Technical Debt**:
- Hardcoded `position_signal_names` list (implicit contract)
- No type system enforcement for output requirements
- Each strategy must independently implement signal → position logic

---

## Solution: SignalToPositionFactor

### Design Specification

**New Factor: SignalToPositionFactor**

```python
# src/factor_library/signal_factors.py

from typing import Dict, Any
import pandas as pd
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory


class SignalToPositionFactor(Factor):
    """
    Convert entry/exit signals to final position matrix.

    Logic:
    - Long (1): entry_signal = 1 AND exit_signal = 0
    - Flat (0): exit_signal = 1 OR entry_signal = 0
    - Maintain current state until signal changes

    Category: SIGNAL
    Inputs: ["breakout_signal", "rolling_trailing_stop_signal"]
    Outputs: ["position"]

    Parameters:
        entry_signal_col (str): Column name for entry signals (default: "breakout_signal")
        exit_signal_col (str): Column name for exit signals (default: "rolling_trailing_stop_signal")
    """

    def __init__(self,
                 entry_signal_col: str = "breakout_signal",
                 exit_signal_col: str = "rolling_trailing_stop_signal"):
        self.entry_signal_col = entry_signal_col
        self.exit_signal_col = exit_signal_col

        super().__init__(
            id="signal_to_position",
            name="Signal to Position Converter",
            category=FactorCategory.SIGNAL,
            inputs=[entry_signal_col, exit_signal_col],
            outputs=["position"],
            logic=self._convert_signals_to_position,
            parameters={
                "entry_signal_col": entry_signal_col,
                "exit_signal_col": exit_signal_col
            }
        )

    def _convert_signals_to_position(self,
                                     data: pd.DataFrame,
                                     params: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert entry/exit signals to position matrix.

        State machine:
        - Enter position when entry_signal = 1 (long) or -1 (short)
        - Exit position when exit_signal = 1
        - Hold position otherwise
        """
        entry_col = params["entry_signal_col"]
        exit_col = params["exit_signal_col"]

        entry_signal = data[entry_col]
        exit_signal = data[exit_col]

        # Initialize position matrix
        position = pd.DataFrame(0, index=data.index, columns=data.columns)

        # State-based position tracking
        for t in range(len(data)):
            if t == 0:
                # First period: enter if entry signal
                position.iloc[t] = (entry_signal.iloc[t] == 1).astype(int)
            else:
                # Exit condition: exit signal triggered
                if exit_signal.iloc[t].any():
                    position.iloc[t] = 0
                # Entry condition: entry signal triggered
                elif entry_signal.iloc[t].any():
                    position.iloc[t] = (entry_signal.iloc[t] == 1).astype(int)
                # Hold: maintain previous position
                else:
                    position.iloc[t] = position.iloc[t-1]

        # Add position matrix to data
        data["position"] = position

        return data


def create_signal_to_position_factor(
    entry_signal_col: str = "breakout_signal",
    exit_signal_col: str = "rolling_trailing_stop_signal"
) -> SignalToPositionFactor:
    """
    Factory function for creating SignalToPositionFactor instances.

    Args:
        entry_signal_col: Column name for entry signals
        exit_signal_col: Column name for exit signals

    Returns:
        SignalToPositionFactor instance
    """
    return SignalToPositionFactor(
        entry_signal_col=entry_signal_col,
        exit_signal_col=exit_signal_col
    )
```

### Implementation Plan

#### Step 1: Create signal_factors.py (1-2 hours)
```bash
# Create new module
touch src/factor_library/signal_factors.py

# Implement SignalToPositionFactor class
# Implement factory function
# Add unit tests
```

#### Step 2: Register in FactorRegistry (30 minutes)
```python
# src/factor_library/registry.py

from src.factor_library.signal_factors import create_signal_to_position_factor

class FactorRegistry:
    def __init__(self):
        # ... existing registrations ...

        # Register signal-to-position converter
        self.register(
            name="signal_to_position_factor",
            factory=create_signal_to_position_factor,
            category=FactorCategory.SIGNAL,
            description="Convert entry/exit signals to final position matrix",
            parameters={
                "entry_signal_col": "breakout_signal",
                "exit_signal_col": "rolling_trailing_stop_signal"
            },
            parameter_ranges={
                "entry_signal_col": ["breakout_signal", "momentum", "any_entry_signal"],
                "exit_signal_col": ["rolling_trailing_stop_signal", "rolling_profit_target_signal"]
            }
        )
```

#### Step 3: Update Template Strategy (30 minutes)
```python
# src/learning/iteration_executor.py:720-756

def _create_template_strategy(self, iteration_num: int) -> Strategy:
    """Create template strategy with stateless factors."""

    registry = FactorRegistry.get_instance()

    # Create strategy
    strategy_id = f"template_{iteration_num}"
    strategy = Strategy(id=strategy_id, generation=0)

    # Factor 1: Momentum (root)
    momentum_factor = registry.create_factor(
        "momentum_factor",
        parameters={"momentum_period": 20}
    )
    strategy.add_factor(momentum_factor, depends_on=[])

    # Factor 2: Breakout entry signal
    breakout_factor = registry.create_factor(
        "breakout_factor",
        parameters={"entry_window": 20}
    )
    strategy.add_factor(breakout_factor, depends_on=[])

    # Factor 3: Stateless trailing stop exit signal (Phase 2)
    trailing_stop_factor = registry.create_factor(
        "rolling_trailing_stop_factor",
        parameters={"trail_percent": 0.10, "lookback_periods": 20}
    )
    strategy.add_factor(
        trailing_stop_factor,
        depends_on=[momentum_factor.id, breakout_factor.id]
    )

    # Factor 4: Signal-to-Position converter (NEW - Phase 2 fix)
    position_factor = registry.create_factor(
        "signal_to_position_factor",
        parameters={
            "entry_signal_col": "breakout_signal",
            "exit_signal_col": "rolling_trailing_stop_signal"
        }
    )
    strategy.add_factor(
        position_factor,
        depends_on=[breakout_factor.id, trailing_stop_factor.id]
    )

    return strategy
```

#### Step 4: Validation (1 hour)
```bash
# Test new factor creation
python test_stateless_factors.py

# Re-run Phase 2 validation
python3 experiments/llm_learning_validation/orchestrator.py \
  --config experiments/llm_learning_validation/config_pilot_hybrid_20.yaml \
  --phase pilot
```

---

## Expected Impact

| Metric | Current | After Fix |
|--------|---------|-----------|
| Factor Graph success rate | 0/13 (0%) | ~9/13 (70%) |
| Overall success rate | 2/20 (10%) | ~14/20 (70%) |
| Position signal errors | 13/20 | 0/20 |
| Development time | - | 3-4 hours |
| Risk level | - | **LOW** (additive change) |

### Success Criteria
- ✅ 0/20 position signal validation errors
- ✅ Factor Graph success rate improves from 0% → 70%+
- ✅ Template strategy executes successfully in all iterations
- ✅ New factor is discoverable by mutation system

---

## Alternative Solutions (Rejected)

### Option 2: Modify Validation Logic (NOT RECOMMENDED)
Accept `breakout_signal` as valid position signal.

**Rejected because**:
- ❌ Breaks abstraction (signals ≠ positions)
- ❌ Requires backtest engine changes
- ❌ Doesn't address architectural gap

### Option 3: Enhance SignalCombiner (ALTERNATIVE)
Extend existing SignalCombiner to support position output mode.

**Rejected because**:
- Conflates signal combination with position generation
- Medium implementation complexity
- Less clear separation of concerns

---

## Long-Term Improvements (Optional)

### 1. Formalize Strategy Output Contract (Medium Priority)
**Current Issue**: Implicit contract based on hardcoded string names

**Proposed Solution**:
```python
class Strategy:
    def set_output_node(self, factor_id: str, output_name: str):
        """Explicitly declare which factor produces final output."""
        self._output_node = (factor_id, output_name)

    def to_pipeline(self, data):
        # Use declared output node instead of searching
        factor_id, output_name = self._output_node
        return self.container.get_matrix(output_name)
```

**Benefits**:
- Explicit contract (no implicit string matching)
- Better error messages
- Self-documenting strategies

### 2. Expand SIGNAL Category Factors (Low Priority)
**Future Enhancements**:
- Position sizing factors (based on volatility, portfolio heat)
- Multi-signal voting combiners (majority vote, weighted ensemble)
- Portfolio-level risk overlays (correlation-based position limits)

---

## Investigation: LLM Strategy Position Logic

**Open Question**: How do LLM-generated strategies (2/7 success) implement the signal-to-position conversion?

**Hypothesis**: LLM strategies may:
1. Generate position logic directly in factor code
2. Use different output naming conventions
3. Implement custom signal combination logic

**Action Required**:
- Analyze successful LLM-generated strategy code
- Extract common patterns
- Validate hypothesis about implicit conversion logic

---

## References

### Related Files
- `src/factor_graph/strategy.py:515-536` - Position signal validation
- `src/learning/iteration_executor.py:720-756` - Template strategy creation
- `src/factor_library/stateless_exit_factors.py` - Phase 2 stateless factors
- `src/factor_library/registry.py` - Factor registry
- `src/factor_graph/factor_category.py` - Factor categories

### Related Documents
- Phase 2 Implementation Plan
- Factor Graph User Guide
- Troubleshooting Guide

---

## Next Actions

1. ✅ **Implement SignalToPositionFactor** (3-4 hours)
   - Create `signal_factors.py`
   - Register in FactorRegistry
   - Update template strategy
   - Add unit tests

2. ✅ **Validate Solution** (1 hour)
   - Run `test_stateless_factors.py`
   - Execute Phase 2 validation test
   - Verify 0/20 position signal errors

3. 🔍 **Investigate LLM Strategy Logic** (research)
   - Analyze 2 successful LLM strategies
   - Document position conversion patterns
   - Compare with proposed solution

4. 📝 **Document Results** (30 minutes)
   - Update implementation status
   - Record actual vs expected impact
   - Create completion report
