# Exit Strategy Mutation AST Framework Design

**Version**: 1.0
**Date**: 2025-10-20
**Phase**: Phase 1 - Exit Strategy Mutation MVP
**Task**: 1.0 - AST Framework Design for Exit Mutations

---

## Executive Summary

This document outlines the AST (Abstract Syntax Tree) manipulation framework for mutating exit strategies in trading algorithms. Based on Phase 0 validation (Sharpe improvement +0.5211), we design a framework to automatically generate and evolve exit logic through AST-based code mutations.

**Design Goals**:
1. Generate syntactically valid exit strategy code via AST manipulation
2. Support 3 core exit mechanisms validated in Phase 0
3. Enable parameter mutation for optimization
4. Ensure safety and validity of all mutations
5. Integrate seamlessly with existing template architecture

---

## Background: Phase 0 Validation Results

### Proven Exit Mechanisms

Phase 0 manual implementation validated these exit strategies:

**1. ATR Trailing Stop-Loss** (2× ATR below highest high)
```python
stop_level = highest_high - (atr * stop_atr_mult)
stop_exit = close < stop_level
```

**2. Fixed Profit Target** (3× ATR above entry)
```python
profit_target = entry_price + (atr * profit_atr_mult)
profit_exit = close >= profit_target
```

**3. Time-Based Exit** (30-day maximum hold)
```python
time_exit = holding_days >= max_hold_days
```

**Performance Impact**:
- Baseline Sharpe: -0.1215 (no exits)
- Enhanced Sharpe: 0.3996 (with exits)
- Improvement: +0.5211 (meets ≥0.3 threshold)

### Key Insights for AST Design

1. **Sequential State Tracking**: Exits require tracking entry_price, highest_high, holding_days across time
2. **Exit Priority**: Time → Stop-Loss → Profit Target (apply in order)
3. **Position Management**: Exits modify boolean position signals
4. **Parameter Sensitivity**: ATR multipliers and time periods are tunable

---

## AST Framework Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│         Exit Strategy Mutation Framework                │
└─────────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌─────────────┐  ┌──────────────┐  ┌────────────────┐
│ Exit        │  │ Exit         │  │ Exit           │
│ Detector    │  │ Mutator      │  │ Validator      │
│ (AST Read)  │  │ (AST Write)  │  │ (AST Check)    │
└─────────────┘  └──────────────┘  └────────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                 ┌───────────────┐
                 │ Code Generator│
                 │ (AST → Python)│
                 └───────────────┘
```

### Core Components

**1. ExitMechanismDetector**
- Purpose: Analyze existing strategy code to detect exit logic
- Input: Python source code (str)
- Output: ExitStrategyProfile (detected mechanisms + parameters)

**2. ExitStrategyMutator**
- Purpose: Modify/generate exit logic via AST manipulation
- Input: ExitStrategyProfile + MutationConfig
- Output: Modified AST tree

**3. ExitCodeValidator**
- Purpose: Validate mutated exit code for syntax + semantic correctness
- Input: AST tree
- Output: ValidationResult (success/failure + errors)

**4. PythonCodeGenerator**
- Purpose: Convert AST back to executable Python code
- Input: AST tree
- Output: Python source code (str)

---

## AST Schema for Exit Strategies

### Exit Strategy AST Pattern

Exit strategies follow this general AST structure:

```python
# High-level pattern
def _apply_exit_strategies(self, positions, data, params):
    # 1. Extract parameters
    param_assignments

    # 2. Calculate indicators (e.g., ATR)
    indicator_calculations

    # 3. Initialize tracking DataFrames
    state_initialization

    # 4. Sequential loop over dates
    for i, date in enumerate(dates):
        # 4a. State tracking logic
        state_updates

        # 4b. Exit condition checks
        exit_conditions

        # 4c. Apply exits to positions
        position_modifications

    # 5. Return modified positions
    return modified_positions
```

### AST Node Types for Exit Logic

**Parameter Extraction** (ast.Assign):
```python
# AST Pattern:
# target: ast.Name(id='stop_atr_mult')
# value: ast.Call(
#   func=ast.Attribute(attr='get'),
#   args=[ast.Constant('stop_atr_mult'), ast.Constant(2.0)]
# )
stop_atr_mult = params.get('stop_atr_mult', 2.0)
```

**Indicator Calculation** (ast.Assign + ast.Call):
```python
# AST Pattern:
# target: ast.Name(id='atr')
# value: ast.Call(
#   func=ast.Attribute(attr='_calculate_atr'),
#   args=[ast.Name('data'), keyword(arg='period', value=...)]
# )
atr = self._calculate_atr(data, period=atr_period)
```

**Exit Condition** (ast.Compare):
```python
# AST Pattern (stop-loss):
# left: ast.Name('close')
# ops: [ast.Lt()]
# comparators: [ast.BinOp(
#   left=ast.Name('highest_high'),
#   op=ast.Sub(),
#   right=ast.BinOp(...)
# )]
stop_exit = close.loc[date] < (highest_high.loc[date] - atr.loc[date] * stop_atr_mult)
```

**Position Modification** (ast.Assign + ast.BoolOp):
```python
# AST Pattern:
# target: ast.Subscript(ast.Attribute(value=ast.Name('modified_positions'), attr='loc'))
# value: ast.BoolOp(
#   op=ast.And(),
#   values=[..., ast.UnaryOp(op=ast.Not(), operand=any_exit)]
# )
modified_positions.loc[date] = (continuing | new_entries) & ~any_exit
```

---

## Mutation Points and Operations

### Mutation Point 1: Exit Mechanism Selection

**Mutation Type**: Structural (add/remove/swap exit mechanisms)

**Operations**:
- `ADD_EXIT`: Insert new exit mechanism (stop-loss, profit target, time-based)
- `REMOVE_EXIT`: Delete existing exit mechanism
- `SWAP_EXIT`: Replace one mechanism with another

**AST Transformation**:
```python
# Original (no time exit)
any_exit = stop_exit | profit_exit

# Mutated (add time exit)
any_exit = time_exit | stop_exit | profit_exit
```

**Implementation**:
- Detect existing `ast.BoolOp` with `ast.Or()` operator
- Insert/remove operands from `values` list
- Regenerate variable assignments for new exit types

### Mutation Point 2: Parameter Values

**Mutation Type**: Parametric (modify numerical constants)

**Operations**:
- `MUTATE_MULTIPLIER`: Change ATR multipliers (e.g., 2.0 → 2.5)
- `MUTATE_PERIOD`: Change time periods (e.g., 30 → 40 days)
- `MUTATE_THRESHOLD`: Change percentage thresholds

**AST Transformation**:
```python
# Original
stop_atr_mult = params.get('stop_atr_mult', 2.0)

# Mutated
stop_atr_mult = params.get('stop_atr_mult', 2.5)
```

**Implementation**:
- Locate `ast.Constant` nodes in parameter assignments
- Replace `value` attribute with new numerical value
- Maintain type consistency (float/int)

**Parameter Ranges** (from Phase 0 validation):
- `atr_period`: [10, 14, 20, 30] days
- `stop_atr_mult`: [1.5, 2.0, 2.5, 3.0]
- `profit_atr_mult`: [2.0, 3.0, 4.0, 5.0]
- `max_hold_days`: [20, 30, 40, 60]

### Mutation Point 3: Exit Condition Logic

**Mutation Type**: Relational (change comparison operators)

**Operations**:
- `FLIP_OPERATOR`: Change < to <=, > to >=
- `INVERT_CONDITION`: Negate exit condition
- `COMBINE_CONDITIONS`: Add conjunctions/disjunctions

**AST Transformation**:
```python
# Original (strict inequality)
stop_exit = close < stop_level

# Mutated (inclusive inequality)
stop_exit = close <= stop_level
```

**Implementation**:
- Locate `ast.Compare` nodes for exit conditions
- Replace `ops` list elements (ast.Lt → ast.LtE)
- Validate semantic correctness

### Mutation Point 4: Indicator Selection

**Mutation Type**: Functional (swap indicator functions)

**Operations**:
- `SWAP_INDICATOR`: Replace ATR with other volatility measures (STD, Bollinger)
- `CHANGE_REFERENCE`: Use different price reference (close vs high vs low)

**AST Transformation**:
```python
# Original (ATR-based)
stop_level = highest_high - (atr * stop_atr_mult)

# Mutated (Percentage-based)
stop_level = highest_high * (1 - stop_pct)
```

**Implementation**:
- Identify indicator calculation `ast.Call` nodes
- Replace function name and arguments
- Update dependent variable references

---

## Mutation Strategy: Priority-Based Approach

### Mutation Priority Tiers

**Tier 1: High-Impact, Low-Risk** (80% mutation budget)
- Parameter value mutations (ATR multipliers, time periods)
- Exit mechanism combinations (add/remove exits)
- Rationale: Phase 0 showed parameter sensitivity, low syntax risk

**Tier 2: Medium-Impact, Medium-Risk** (15% mutation budget)
- Comparison operator modifications (< vs <=)
- Exit priority reordering (time → stop → profit vs other orders)
- Rationale: Can improve edge case handling, moderate syntax risk

**Tier 3: High-Impact, High-Risk** (5% mutation budget)
- Indicator function swapping (ATR → other indicators)
- Complex condition combinations
- Rationale: Potential for breakthroughs, but higher failure rate

### Mutation Workflow

```
1. SELECT mutation tier based on probability weights
   ├─ 80% → Tier 1 (parametric mutations)
   ├─ 15% → Tier 2 (relational mutations)
   └─  5% → Tier 3 (structural mutations)

2. CHOOSE specific mutation operation
   └─ Random selection within tier

3. LOCATE target AST node
   └─ Use ExitMechanismDetector to find mutation point

4. APPLY mutation transformation
   └─ Modify AST tree in-place

5. VALIDATE mutated code
   ├─ Syntax validation (ast.parse succeeds)
   ├─ Semantic validation (no impossible conditions)
   └─ Type validation (proper pandas operations)

6. GENERATE Python code
   └─ ast.unparse() → executable Python source

7. TEST execution
   └─ Run backtest with mutated strategy
```

---

## Safety and Validation Rules

### Syntactic Validation Rules

**Rule S1**: All mutations must produce parseable Python (ast.parse succeeds)
```python
def validate_syntax(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False
```

**Rule S2**: Required components must exist
- `_apply_exit_strategies` method
- Parameter extraction from `params` dict
- Return statement with `modified_positions`

**Rule S3**: DataFrame operations must use proper pandas syntax
- `.loc[date]` for row access, not `.iloc[i]`
- Boolean indexing for position masking
- Proper Series/DataFrame type handling

### Semantic Validation Rules

**Rule M1**: Exit conditions must be logically sound
```python
# INVALID: Stop above entry (impossible)
stop_level = entry_price + (atr * stop_atr_mult)  # ❌

# VALID: Stop below entry
stop_level = entry_price - (atr * stop_atr_mult)  # ✅
```

**Rule M2**: Parameter ranges must be sensible
```python
# ATR multipliers must be positive
assert stop_atr_mult > 0  # ✅
assert profit_atr_mult > 0  # ✅

# Time periods must be reasonable (1-252 trading days)
assert 1 <= max_hold_days <= 252  # ✅
```

**Rule M3**: Exit priority must avoid conflicts
```python
# VALID: Apply exits independently
any_exit = time_exit | stop_exit | profit_exit  # ✅

# INVALID: Contradictory conditions
any_exit = (price > target) & (price < target)  # ❌
```

**Rule M4**: State tracking must be continuous
```python
# VALID: Sequential state updates
for i, date in enumerate(dates):
    if i > 0:
        entry_price.loc[date] = entry_price.loc[prev_date].where(continuing, ...)  # ✅

# INVALID: Skipping state
entry_price.loc[date] = ...  # No reference to previous state ❌
```

### Type Validation Rules

**Rule T1**: Price data must be DataFrames with matching columns
```python
# Ensure column alignment
close = close.reindex(columns=positions.columns)
high = high.reindex(columns=positions.columns)
```

**Rule T2**: Exit signals must be boolean Series/DataFrames
```python
# Exit conditions produce boolean types
stop_exit: pd.Series[bool] = close < stop_level  # ✅
```

**Rule T3**: Position modifications must preserve DataFrame structure
```python
# Maintain same index and columns
assert modified_positions.index.equals(positions.index)
assert modified_positions.columns.equals(positions.columns)
```

---

## Implementation Plan

### Phase 1.1: Core AST Components (Days 1-3)

**Deliverables**:
1. `src/mutation/exit_detector.py` - ExitMechanismDetector class
2. `src/mutation/exit_mutator.py` - ExitStrategyMutator class
3. `src/mutation/exit_validator.py` - ExitCodeValidator class

**Key Classes**:

```python
class ExitStrategyProfile:
    """Detected exit strategy characteristics."""
    mechanisms: List[str]  # ['stop_loss', 'profit_target', 'time_based']
    parameters: Dict[str, float]  # {'stop_atr_mult': 2.0, ...}
    ast_nodes: Dict[str, ast.AST]  # Mapping of mechanism names to AST nodes

class ExitMechanismDetector:
    """Detect exit logic in strategy code via AST analysis."""

    def detect(self, code: str) -> ExitStrategyProfile:
        """Analyze code and extract exit strategy profile."""
        tree = ast.parse(code)
        mechanisms = self._find_exit_mechanisms(tree)
        parameters = self._extract_parameters(tree)
        ast_nodes = self._map_ast_nodes(tree, mechanisms)
        return ExitStrategyProfile(mechanisms, parameters, ast_nodes)

    def _find_exit_mechanisms(self, tree: ast.AST) -> List[str]:
        """Identify which exit types are present."""
        # Look for variable names: stop_exit, profit_exit, time_exit

    def _extract_parameters(self, tree: ast.AST) -> Dict[str, float]:
        """Extract parameter values from params.get() calls."""

    def _map_ast_nodes(self, tree: ast.AST, mechanisms: List[str]) -> Dict[str, ast.AST]:
        """Map mechanism names to their AST node locations."""

class ExitStrategyMutator:
    """Mutate exit strategies via AST manipulation."""

    def mutate(self, profile: ExitStrategyProfile, config: MutationConfig) -> ast.AST:
        """Apply mutation operations to exit strategy AST."""
        mutation_type = self._select_mutation_tier(config)

        if mutation_type == 'parametric':
            return self._mutate_parameters(profile)
        elif mutation_type == 'structural':
            return self._mutate_mechanisms(profile)
        elif mutation_type == 'relational':
            return self._mutate_conditions(profile)

    def _mutate_parameters(self, profile: ExitStrategyProfile) -> ast.AST:
        """Modify parameter values in AST."""
        # Locate ast.Constant nodes for parameters
        # Replace with new values from valid ranges

    def _mutate_mechanisms(self, profile: ExitStrategyProfile) -> ast.AST:
        """Add/remove/swap exit mechanisms."""
        # Modify ast.BoolOp operands for exit combinations

    def _mutate_conditions(self, profile: ExitStrategyProfile) -> ast.AST:
        """Change comparison operators in exit conditions."""
        # Replace ast.Compare ops (Lt → LtE, etc.)

class ExitCodeValidator:
    """Validate mutated exit strategy code."""

    def validate(self, code: str) -> ValidationResult:
        """Run all validation checks."""
        results = []
        results.append(self._validate_syntax(code))
        results.append(self._validate_semantics(code))
        results.append(self._validate_types(code))
        return ValidationResult.aggregate(results)

    def _validate_syntax(self, code: str) -> bool:
        """Check if code parses without errors."""

    def _validate_semantics(self, code: str) -> bool:
        """Check logical soundness of exit conditions."""

    def _validate_types(self, code: str) -> bool:
        """Verify pandas DataFrame operations are correct."""
```

### Phase 1.2: Integration and Testing (Days 4-5)

**Deliverables**:
1. `src/mutation/exit_mutation_operator.py` - Unified operator
2. `tests/mutation/test_exit_mutations.py` - Comprehensive tests
3. `examples/exit_mutation_demo.py` - Usage demonstration

**Integration Points**:
- Connect to existing mutation pipeline
- Integrate with template registry for exit templates
- Hook into fitness evaluation for mutation effectiveness

### Phase 1.3: Smoke Test Validation (Days 6-7)

**Test Configuration**:
- Population: 50 strategies
- Generations: 20
- Mutation rate: 0.3 (30% of offspring mutated)
- Selection: Tournament (size=3)

**Success Criteria**:
- Target Sharpe: >2.0 (5× Phase 0 manual baseline)
- Syntax valid: 100% of generated strategies
- Backtest complete: ≥90% of strategies
- Performance improvement: ≥50% strategies better than baseline

---

## Risk Mitigation

### Technical Risks

**Risk T1**: AST mutations produce invalid Python
- **Mitigation**: Strict validation pipeline (S1-S3 rules)
- **Fallback**: Reject invalid mutations, retry with different operation

**Risk T2**: Mutated code has runtime errors
- **Mitigation**: Try-except wrapper around backtest execution
- **Fallback**: Assign fitness=-∞ to failing strategies

**Risk T3**: State tracking logic breaks with mutations
- **Mitigation**: Preserve sequential loop structure (M4 rule)
- **Fallback**: Template-based state initialization

### Performance Risks

**Risk P1**: Mutation doesn't improve over manual Phase 0 implementation
- **Mitigation**: Start with Phase 0 parameters as baseline, mutate from there
- **Fallback**: Increase mutation budget to explore more variations

**Risk P2**: 20-generation test fails to reach Sharpe >2.0
- **Mitigation**: Analyze failure modes, adjust mutation probabilities
- **Fallback**: Extend to 50 generations or optimize selection pressure

**Risk P3**: Computational cost too high for mutation testing
- **Mitigation**: Parallelize backtest execution across strategies
- **Fallback**: Reduce population size or use faster backtest approximation

---

## Appendix: AST Manipulation Examples

### Example 1: Adding Time-Based Exit

**Original Code** (stop + profit only):
```python
any_exit = stop_exit | profit_exit
```

**AST Representation**:
```python
ast.Assign(
    targets=[ast.Name(id='any_exit')],
    value=ast.BoolOp(
        op=ast.Or(),
        values=[
            ast.Name(id='stop_exit'),
            ast.Name(id='profit_exit')
        ]
    )
)
```

**Mutation Operation**:
```python
# Insert time_exit into BoolOp values
node.value.values.insert(0, ast.Name(id='time_exit'))
```

**Mutated Code**:
```python
any_exit = time_exit | stop_exit | profit_exit
```

### Example 2: Changing ATR Multiplier

**Original Code**:
```python
stop_atr_mult = params.get('stop_atr_mult', 2.0)
```

**AST Representation**:
```python
ast.Assign(
    targets=[ast.Name(id='stop_atr_mult')],
    value=ast.Call(
        func=ast.Attribute(attr='get'),
        args=[
            ast.Constant('stop_atr_mult'),
            ast.Constant(2.0)  # ← Target for mutation
        ]
    )
)
```

**Mutation Operation**:
```python
# Locate default value constant
default_const = node.value.args[1]
# Replace with new value
default_const.value = 2.5
```

**Mutated Code**:
```python
stop_atr_mult = params.get('stop_atr_mult', 2.5)
```

### Example 3: Flipping Comparison Operator

**Original Code**:
```python
stop_exit = close < stop_level
```

**AST Representation**:
```python
ast.Assign(
    targets=[ast.Name(id='stop_exit')],
    value=ast.Compare(
        left=ast.Name(id='close'),
        ops=[ast.Lt()],  # ← Target for mutation
        comparators=[ast.Name(id='stop_level')]
    )
)
```

**Mutation Operation**:
```python
# Replace comparison operator
node.value.ops[0] = ast.LtE()  # Lt → LtE
```

**Mutated Code**:
```python
stop_exit = close <= stop_level
```

---

## Conclusion

This AST framework design provides a systematic approach to mutating exit strategies based on Phase 0 validation. Key design principles:

1. **Evidence-Based**: Builds on proven exit mechanisms from Phase 0
2. **Safety-First**: Comprehensive validation rules prevent invalid mutations
3. **Flexible**: Supports parametric, structural, and relational mutations
4. **Testable**: Clear validation criteria and smoke test plan

**Next Steps**:
- Task 1.1: Implement ExitMechanismDetector
- Task 1.2: Implement ExitStrategyMutator
- Task 1.3: Implement ExitCodeValidator
- Task 1.4: Run 20-generation smoke test

**Success Metric**: Achieve Sharpe >2.0 in 20-generation test (vs. Phase 0 manual 0.3996)

---

**Document Status**: ✅ COMPLETE
**Approval**: Ready for Phase 1 implementation
**References**: Phase 0 validation results, `src/templates/momentum_exit_template.py`
