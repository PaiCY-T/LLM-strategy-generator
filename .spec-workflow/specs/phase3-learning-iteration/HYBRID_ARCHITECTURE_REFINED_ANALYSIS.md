# Hybrid Architecture Refined Analysis

**Date**: 2025-11-08
**Status**: 🟡 **NEEDS REVISION** - Complexity Underestimated
**Reviewer**: zen thinkdeep analysis (Gemini 2.5 Pro)

---

## Executive Summary

After systematic investigation of the proposed Hybrid Architecture from `CRITICAL_FINDING_FACTOR_GRAPH_ARCHITECTURE.md`, I've identified **5 critical architectural gaps** that significantly impact implementation complexity and timeline.

**Original Estimate**: 1 day (4-6 hours)
**Revised Estimate**: 2-2.5 days (14-20 hours)
**Confidence**: HIGH (all major blockers identified with evidence)

---

## Critical Findings

### P0 Blocker 1: Metrics Extraction Path Undefined

**Issue**: The proposal assumes `strategy.to_pipeline()` can produce backtest metrics, but investigation reveals:

```python
# From src/factor_graph/strategy.py:384-433
def to_pipeline(self, data: pd.DataFrame) -> pd.DataFrame:
    """Returns DataFrame with all factor outputs computed in dependency order.
    Original data columns are preserved, factor outputs are added."""
```

**Evidence**: `to_pipeline()` returns a **signals DataFrame** (with columns like "rsi", "positions"), NOT backtest metrics (Sharpe ratio, returns, drawdown).

**Impact**:
- LLM path: `exec(code)` → finlab.backtest.sim() → report → extract metrics ✅
- Factor Graph path: `strategy.to_pipeline(data)` → signals DataFrame → **❌ UNDEFINED** → metrics

**Critical Questions**:
1. Does finlab.backtest.sim() accept signal DataFrames?
2. How to identify the final "positions" signal from multiple factor outputs?
3. What column naming convention does to_pipeline() use?

**Required Investigation**: Study finlab's backtest API to determine signal DataFrame → metrics path.

**Estimated Impact**: +4-6 hours

---

### P0 Blocker 2: Parameter Extraction Incompatibility

**Issue**: ChampionTracker calls `extract_strategy_params(code)` which parses Python code strings.

**Evidence** from `artifacts/working/modules/performance_attributor.py:14-100`:
```python
def extract_strategy_params(code: str) -> Dict[str, Any]:
    """Extract key strategy parameters using robust regex patterns."""
    datasets = re.findall(r"data\.get\(['\"]([^'\"]+)['\"]\)", code)
    liquidity_threshold = re.search(r'(?:trading_value|liquidity).*?>\s*([\d_e\.]+)', code)
    roe_smoothing_window = re.search(r'roe\s*\.\s*rolling\s*\(\s*window\s*=\s*(\d+)', code)
    # Extracts: datasets, liquidity_threshold, roe_smoothing_window, value_factor, etc.
```

**Impact**: These functions **cannot work** with Strategy DAG objects which have no code representation.

**From src/learning/champion_tracker.py:496-515**:
```python
def _create_champion(self, iteration_num: int, code: str, metrics: Dict[str, float]) -> None:
    parameters = extract_strategy_params(code)  # ❌ Expects CODE string
    success_patterns = extract_success_patterns(code, parameters)  # ❌ Expects CODE string

    self.champion = ChampionStrategy(
        iteration_num=iteration_num,
        code=code,
        parameters=parameters,  # ❌ Required field
        success_patterns=success_patterns,  # ❌ Required field
        metrics=metrics,
        timestamp=datetime.now().isoformat()  # ❌ Required field
    )
```

**Required Changes**:
1. ChampionTracker needs **dual extraction paths**:
   - LLM: Extract from code string (current)
   - Factor Graph: Extract from Strategy DAG structure (NEW)

2. Define Strategy DAG "parameters" concept:
   - Factor IDs used?
   - Factor type distribution?
   - DAG topology metrics (depth, breadth)?
   - Number of nodes/edges?

3. Define Strategy DAG "success_patterns":
   - Common factor combinations?
   - DAG structure patterns?
   - Or mark as Optional for factor_graph method?

**Estimated Impact**: +3-4 hours

---

### P0 Blocker 3: Missing ChampionStrategy Fields

**Issue**: Proposed dataclass is too simplistic.

**Proposed** (from CRITICAL_FINDING document):
```python
@dataclass
class ChampionStrategy:
    code: Optional[str] = None
    strategy: Optional[Strategy] = None
    generation_method: str = "unknown"
    metrics: Dict[str, float] = field(default_factory=dict)
```

**Required** (from champion_tracker.py:502-509):
```python
@dataclass
class ChampionStrategy:
    # Hybrid fields
    code: Optional[str] = None
    strategy: Optional[Strategy] = None
    generation_method: str  # "llm" or "factor_graph"

    # Common fields
    metrics: Dict[str, float] = field(default_factory=dict)
    iteration_num: int
    timestamp: str  # ISO format

    # LLM-specific fields (Optional for factor_graph)
    parameters: Optional[Dict[str, Any]] = None
    success_patterns: Optional[List[str]] = None

    def __post_init__(self):
        """Validate mutual exclusivity and generation_method consistency."""
        if self.code is None and self.strategy is None:
            raise ValueError("Either code or strategy must be set")
        if self.code is not None and self.strategy is not None:
            raise ValueError("Cannot set both code and strategy")
        if self.generation_method not in ("llm", "factor_graph", "unknown"):
            raise ValueError(f"Invalid generation_method: {self.generation_method}")
```

**Estimated Impact**: +1 hour

---

### P1 Critical: Strategy Serialization Underspecified

**Issue**: Strategy objects use NetworkX DiGraph which is not JSON-serializable.

**Evidence** from src/factor_graph/strategy.py:
```python
self.dag = nx.DiGraph()  # NetworkX graph - requires special serialization
self.factors: Dict[str, Factor] = {}  # Factor objects - also not JSON-serializable
```

**Analysis of Proposed Options**:

#### Option 1: Strategy ID + Registry
```python
{"iteration_num": 5, "strategy_id": "momentum_v5", "metrics": {...}}
```
**Pros**: Compact JSONL records
**Cons**:
- Requires Strategy Registry (NEW component not in proposal)
- Lifecycle management complexity
- Reference integrity issues if Strategy mutates
**Estimated Effort**: +3-4 hours

#### Option 2: Pickle Strategy Objects
```python
# Save to: strategies/iteration_5_strategy.pkl
```
**Pros**: Simple implementation
**Cons**:
- Cannot version control binary files
- Cannot inspect/debug
- Cross-Python-version issues
- Security risk (pickle exploits)
- HIGH technical debt
**Estimated Effort**: +1 hour (but high cost later)

#### Option 3: JSON-like DAG Serialization ⭐ RECOMMENDED
```python
{
    "iteration_num": 5,
    "generation_method": "factor_graph",
    "strategy_metadata": {
        "strategy_id": "momentum_v5",
        "generation": 1,
        "parent_ids": ["momentum_v4"],
        "factors": [
            {"id": "rsi_14", "type": "RSI", "params": {"period": 14}},
            {"id": "entry", "type": "Signal", "params": {...}, "depends_on": ["rsi_14"]}
        ],
        "dag_edges": [["rsi_14", "entry"]]
    },
    "metrics": {"sharpe_ratio": 0.85, ...}
}
```
**Pros**:
- Human-readable, inspectable
- Version controllable
- Cross-platform compatible
- Debuggable
**Cons**:
- Requires custom Strategy encoder/decoder
- Factor objects must be serializable
**Estimated Effort**: +4-6 hours

**Recommendation**: Adopt Option 3 despite higher initial cost for long-term maintainability.

**Estimated Impact**: +4-6 hours

---

### P1 Critical: ChampionTracker Refactoring Scope

**Issue**: The proposal suggests "minimal changes" but evidence shows substantial refactoring required.

**Required Changes**:

1. **_create_champion() method** (champion_tracker.py:492-515):
```python
def _create_champion(
    self,
    iteration_num: int,
    code: Optional[str] = None,
    strategy: Optional[Strategy] = None,
    metrics: Dict[str, float] = None,
    generation_method: str = "unknown"
) -> None:
    """Create champion from either LLM code or Factor Graph Strategy."""

    if generation_method == "llm":
        # Extract from code
        parameters = extract_strategy_params(code)
        success_patterns = extract_success_patterns(code, parameters)
    elif generation_method == "factor_graph":
        # Extract from Strategy DAG
        parameters = extract_strategy_dag_metadata(strategy)
        success_patterns = extract_dag_patterns(strategy)
    else:
        parameters = {}
        success_patterns = []

    self.champion = ChampionStrategy(
        iteration_num=iteration_num,
        code=code,
        strategy=strategy,
        generation_method=generation_method,
        parameters=parameters,
        success_patterns=success_patterns,
        metrics=metrics,
        timestamp=datetime.now().isoformat()
    )

    self._save_champion()
```

2. **New helper functions**:
```python
def extract_strategy_dag_metadata(strategy: Strategy) -> Dict[str, Any]:
    """Extract metadata from Strategy DAG structure."""
    return {
        "strategy_id": strategy.id,
        "generation": strategy.generation,
        "num_factors": len(strategy.factors),
        "factor_types": [f.type for f in strategy.get_factors()],
        "dag_depth": calculate_dag_depth(strategy.dag),
        "dag_breadth": calculate_dag_breadth(strategy.dag)
    }

def extract_dag_patterns(strategy: Strategy) -> List[str]:
    """Identify structural patterns in Strategy DAG."""
    patterns = []
    # Analyze DAG topology
    if has_parallel_branches(strategy.dag):
        patterns.append("parallel_execution")
    if has_deep_pipeline(strategy.dag):
        patterns.append("deep_pipeline")
    # Analyze factor combinations
    factor_types = [f.type for f in strategy.get_factors()]
    if "RSI" in factor_types and "Signal" in factor_types:
        patterns.append("momentum_strategy")
    return patterns
```

3. **promote_to_champion() method** (champion_tracker.py:945-953):
   - Update to accept Strategy objects
   - Handle hybrid champion promotion

4. **_save_champion() method**:
   - Implement Strategy serialization (Option 3 recommended)

**Estimated Impact**: +3-4 hours

---

## Revised Implementation Plan

### Phase 1: Investigation & Preparation (2-3 hours)
**Tasks**:
1. Investigate finlab.backtest.sim() API
   - Does it accept signal DataFrames?
   - How to convert to_pipeline() output → backtest metrics?
2. Research NetworkX graph serialization
   - Validate JSON-like approach feasibility
3. Define Strategy DAG metadata schema
   - What are meaningful "parameters" for DAG?
   - What "success_patterns" can be extracted from DAG structure?

**Deliverables**: API compatibility document, serialization schema

---

### Phase 2: Core Hybrid Dataclass (2-3 hours)
**Tasks**:
1. Implement ChampionStrategy hybrid dataclass
   - Add all required fields (code, strategy, parameters, success_patterns, timestamp)
   - Implement __post_init__ validation
   - Write 10 unit tests

2. Implement Strategy DAG metadata extraction
   - `extract_strategy_dag_metadata(strategy)` function
   - `extract_dag_patterns(strategy)` function
   - Write 5 unit tests

**Deliverables**: champion_strategy.py, test_champion_strategy.py

---

### Phase 3: ChampionTracker Refactoring (3-4 hours)
**Tasks**:
1. Refactor _create_champion() for dual paths
2. Update promote_to_champion() to handle Strategy objects
3. Implement conditional parameter/pattern extraction
4. Write 10 unit tests for hybrid paths

**Deliverables**: Updated champion_tracker.py, test_champion_tracker.py

---

### Phase 4: BacktestExecutor Strategy Support (4-6 hours)
**Tasks**:
1. Implement execute_strategy_dag() method
   ```python
   def execute_strategy_dag(
       self,
       strategy: Strategy,
       data: pd.DataFrame,
       timeout: Optional[float] = None
   ) -> ExecutionResult:
       """Execute Factor Graph Strategy DAG."""
       try:
           # Execute strategy
           signals_df = strategy.to_pipeline(data)

           # Convert signals → backtest metrics
           # (Implementation depends on finlab API investigation)
           metrics = self._extract_metrics_from_signals(signals_df, data)

           return ExecutionResult(
               success=True,
               execution_time=execution_time,
               sharpe_ratio=metrics.get('sharpe_ratio'),
               total_return=metrics.get('total_return'),
               max_drawdown=metrics.get('max_drawdown'),
               ...
           )
       except Exception as e:
           return ExecutionResult(
               success=False,
               error_type=type(e).__name__,
               error_message=str(e),
               ...
           )
   ```

2. Implement _extract_metrics_from_signals() helper
3. Update execute() method to route based on input type
4. Write 10 unit tests

**Deliverables**: Updated executor.py, test_executor.py

---

### Phase 5: Strategy Serialization (4-6 hours)
**Tasks**:
1. Implement JSON-like Strategy encoder
   ```python
   def serialize_strategy(strategy: Strategy) -> Dict[str, Any]:
       """Serialize Strategy DAG to JSON-serializable dict."""
       return {
           "strategy_id": strategy.id,
           "generation": strategy.generation,
           "parent_ids": strategy.parent_ids,
           "factors": [
               {
                   "id": f.id,
                   "type": f.type,
                   "params": f.params,
                   "depends_on": list(strategy.dag.predecessors(f.id))
               }
               for f in strategy.get_factors()
           ],
           "dag_edges": list(strategy.dag.edges())
       }
   ```

2. Implement Strategy decoder
   ```python
   def deserialize_strategy(data: Dict[str, Any]) -> Strategy:
       """Deserialize Strategy from JSON dict."""
       strategy = Strategy(
           id=data["strategy_id"],
           generation=data["generation"],
           parent_ids=data["parent_ids"]
       )

       # Reconstruct factors and DAG
       for factor_data in data["factors"]:
           factor = create_factor_from_dict(factor_data)
           strategy.add_factor(factor, depends_on=factor_data["depends_on"])

       return strategy
   ```

3. Update IterationHistory to handle Strategy objects
4. Write 10 serialization round-trip tests

**Deliverables**: strategy_serialization.py, updated iteration_history.py

---

### Phase 6: Integration & Testing (2-3 hours)
**Tasks**:
1. Write 15 integration tests:
   - LLM → Factor Graph champion transition
   - Factor Graph → LLM champion transition
   - Hybrid execution path end-to-end
   - Serialization/deserialization round-trip
   - Metrics extraction parity verification

2. Manual testing:
   - Run 10 iterations with FG-only mode
   - Verify champion promotion works
   - Verify history serialization works
   - Verify metrics match expectations

**Deliverables**: test_hybrid_integration.py, validation report

---

## Timeline Summary

| Phase | Tasks | Hours | Dependencies |
|-------|-------|-------|--------------|
| 1. Investigation | finlab API, serialization research | 2-3h | None |
| 2. Hybrid Dataclass | ChampionStrategy, metadata extraction | 2-3h | Phase 1 |
| 3. ChampionTracker | Dual extraction paths | 3-4h | Phase 2 |
| 4. BacktestExecutor | Strategy execution, metrics | 4-6h | Phase 1 |
| 5. Serialization | JSON encoder/decoder | 4-6h | Phase 2 |
| 6. Integration | End-to-end tests | 2-3h | Phase 2-5 |
| **Total** | | **17-25h** | **2-3 days** |

**Original Estimate**: 1 day (4-6 hours)
**Revised Estimate**: 2-3 days (17-25 hours)
**Variance**: +200% to +300%

---

## Risk Assessment

### High Risk (P0)
1. **finlab API Compatibility**: If finlab.backtest.sim() cannot accept signal DataFrames, may need alternative metrics calculation approach
2. **Factor Serialization**: If Factor objects cannot be serialized to JSON, may need to fall back to Pickle (Option 2)

### Medium Risk (P1)
1. **Metrics Extraction Parity**: Ensuring Strategy DAG execution produces identical metrics to code execution
2. **Test Coverage**: 40+ new tests required, may discover edge cases during implementation

### Low Risk (P2)
1. **Timeline Overrun**: Complex refactoring may extend beyond 3 days
2. **Technical Debt**: Serialization complexity may create maintenance burden

---

## Recommendations

### Immediate Actions
1. **Investigate finlab API** (CRITICAL): Determine signal DataFrame → metrics path before proceeding
2. **Define DAG metadata schema**: Establish what "parameters" and "success_patterns" mean for Strategy DAGs
3. **Prototype serialization**: Validate JSON-like approach works for Strategy + Factor objects

### Architecture Decisions
1. **Adopt Option 3 (JSON serialization)** for Strategy persistence
2. **Make parameters/success_patterns Optional** for factor_graph generation_method
3. **Add validation layer** to ensure metrics extraction parity between LLM and Factor Graph paths

### Implementation Strategy
1. **Start with Phase 1 investigation** - validate all assumptions before coding
2. **Implement Phase 2-3 in parallel** - dataclass and tracker changes are independent
3. **Phase 4-5 require Phase 1 completion** - cannot implement executor without API knowledge

---

## Comparison with Original Proposal

| Aspect | Original Proposal | Refined Analysis | Delta |
|--------|-------------------|------------------|-------|
| Timeline | 1 day (4-6h) | 2-3 days (17-25h) | +200-300% |
| ChampionStrategy fields | 4 fields | 8 fields | +100% |
| ChampionTracker changes | "~20 lines" | Substantial refactoring | N/A |
| New functions | 1 (execute_strategy_dag) | 6+ functions | +500% |
| Test count | "~40 tests" | 60+ tests | +50% |
| Serialization | "Option 1 or 2" | Option 3 (custom JSON) | Higher complexity |
| Metrics extraction | "Same logic" | Completely different path | N/A |

---

## Conclusion

The Hybrid Architecture proposal is **fundamentally sound** but significantly **underestimates implementation complexity**. The core insight - supporting both LLM code strings and Factor Graph Strategy objects - is correct and necessary.

However, the proposal assumes these two paths can share implementation ("same logic"), when evidence shows they require **parallel implementations** for:
1. Parameter/pattern extraction
2. Metrics extraction from execution results
3. Serialization/deserialization
4. Champion promotion logic

**Recommendation**: Proceed with Hybrid Architecture but allocate **2-3 days** instead of 1 day, and complete Phase 1 investigation before committing to implementation approach.

**Status**: Ready for expert review (zen chat with Gemini 2.5 Pro)

---

**Analysis Completed**: 2025-11-08
**Reviewer**: zen thinkdeep (Gemini 2.5 Pro)
**Confidence Level**: HIGH (all blockers identified with source evidence)
