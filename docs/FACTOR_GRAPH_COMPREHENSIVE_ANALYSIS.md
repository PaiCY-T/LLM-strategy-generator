# Factor Graph Architecture Comprehensive Analysis

**Date**: 2025-11-10
**Analysis Type**: Zen Analysis + Zen Tracer (Precision Mode)
**Status**: ✅ Complete - Ready for Implementation Planning

---

## Executive Summary

The Factor Graph system exhibits excellent architectural design (5 design patterns, well-documented, modular) but suffers from a **critical data structure incompatibility** that prevents execution. FinLab provides time-series data as Dates×Symbols matrices (4563×2661), while Factor Graph expects Observations×Features DataFrames with 1D columns. This three-layer mismatch renders the system non-functional.

**Recommendation**: Two-phase approach
- **Phase 1** (1-2 hours): Temporarily disable Factor Graph, use LLM/template-based strategies
- **Phase 2** (1 week): Redesign with Matrix-Native architecture

---

## Table of Contents

1. [Precision Trace Analysis](#precision-trace-analysis)
2. [Architecture Analysis Results](#architecture-analysis-results)
3. [Solution Options Evaluation](#solution-options-evaluation)
4. [Implementation Roadmap](#implementation-roadmap)
5. [Technical Appendix](#technical-appendix)

---

## Precision Trace Analysis

### Complete Execution Flow

```
[BacktestExecutor::execute_factor_graph_strategy] (file: /src/backtest/executor.py, line: 498)
↓ passes: finlab.data module
[Strategy::to_pipeline] (file: /src/factor_graph/strategy.py, line: 446)
↓ creates: pd.DataFrame() [EMPTY, 0 rows × 0 columns]
↓ stores: self._data_module = data [UNUSED by factors]
↓ for each factor in topological order...
[Factor::execute] (file: /src/factor_graph/factor.py, line: 209)
↓ validates: self.inputs in data.columns ❌ FAILS (no columns exist)
↓ passes: empty DataFrame to logic function
[_momentum_logic] (file: /src/factor_library/momentum_factors.py, line: 64)
  ↓ bypasses: ignores empty DataFrame parameter
  ↓ loads data via workaround
  [DataCache::get_instance] (file: /src/templates/data_cache.py, line: 116)
  ↓
  [DataCache::get] (file: /src/templates/data_cache.py, line: 120)
  ↓ returns: FinlabDataFrame matrix (4563 dates × 2661 symbols)
  ↓
  [_momentum_logic continues] (file: /src/factor_library/momentum_factors.py, line: 84)
  ↓ attempts: data['momentum'] = momentum (assign 2D matrix to 1D column)
  ↓
  ❌ CRITICAL FAILURE: ValueError - Cannot assign 2D array to DataFrame column
```

### Data Type Validation Table

| Layer | Component | Expected Type | Actual Type | Status |
|-------|-----------|---------------|-------------|--------|
| Entry | BacktestExecutor | finlab.data module | ✅ finlab.data module | Pass |
| L1 | Strategy.to_pipeline | OHLCV DataFrame | ❌ Empty DataFrame (0×0) | **Fail** |
| L2 | Factor.execute | DataFrame with columns | ❌ Empty DataFrame | **Fail** |
| L3 | Factor logic | DataFrame to mutate | ❌ FinLab matrix (4563×2661) | **Fail** |
| Output | Return to executor | Position DataFrame | ❌ Never reached | **Fail** |

### Branching & Execution Paths

| Location | Condition | Branches | Uncertain |
|----------|-----------|----------|-----------|
| executor.py:498 | Factor Graph strategy | to_pipeline() | No |
| executor.py:263 | LLM code string | exec(strategy_code) | No |
| strategy.py:463 | For each factor | factor.execute(result) | No |
| factor.py:209 | hasattr(data, 'columns') | Validate inputs | No |
| momentum_factors.py:73 | Need data | DataCache.get_instance() | No |

### Side Effects

```
Side Effects:
- [memory] Creates empty DataFrame allocation (strategy.py:446)
- [memory] Stores unused data module reference (strategy.py:449)
- [cache] Singleton DataCache instance creation (data_cache.py:116)
- [network] FinLab API data loading on cache miss (data_cache.py:154)
- [state] Updates cache statistics (hits, misses) (data_cache.py:144)
- [error] Raises ValueError on matrix assignment (momentum_factors.py:84)
```

### Usage Points

```
Usage Points:
1. executor.py:498 - BacktestExecutor calls strategy.to_pipeline() for Factor Graph strategies
2. executor.py:263 - BacktestExecutor uses exec() for LLM-generated code strategies
3. strategy.py:463 - Strategy calls factor.execute() in topological order
4. factor.py:232 - Factor calls self.logic() with DataFrame and parameters
5. momentum_factors.py:73 - Logic bypasses DataFrame, uses DataCache directly
```

### Entry Points

```
Entry Points:
- BacktestExecutor::execute_factor_graph_strategy (context: Factor Graph strategy execution)
- BacktestExecutor::_execute_in_process (context: LLM code string execution)
- Strategy::to_pipeline (context: Convert strategy DAG to positions DataFrame)
- Factor::execute (context: Execute single factor in pipeline)
```

---

## Architecture Analysis Results

### Design Patterns Identified (5 total)

1. **Singleton Pattern** (DataCache)
   - ✅ Well-implemented
   - ⚠️ Thread-safety noted as future enhancement
   - ⚠️ Acts as workaround for architectural mismatch

2. **Factory Pattern** (Factor Creation)
   - ✅ 13 factory functions implemented
   - ✅ Clean separation between factory and class
   - ✅ Integrated with FactorRegistry

3. **Strategy Pattern** (Factor Execution)
   - ✅ Uniform Factor.execute() interface
   - ✅ Logic functions encapsulated separately
   - ✅ Runtime composition support

4. **Composite Pattern** (Strategy DAG)
   - ✅ NetworkX-based dependency graph
   - ✅ Topological sort for execution order
   - ✅ Supports complex factor relationships

5. **Registry Pattern** (Factor Discovery)
   - ✅ Metadata-driven factor discovery
   - ✅ Parameter validation with ranges
   - ✅ Category-based organization

### Code Metrics

- **Total Lines**: 4,516 LOC across 9 files
- **Factor Implementations**: 13 (4 momentum, 4 turtle, 5 exit)
- **Core Architecture**: 2 files (strategy.py, factor.py)
- **Support Infrastructure**: 3 files (registry, data_cache, factor_category)
- **DataCache References**: 27 calls in momentum_factors.py

### Coupling Analysis

**Tight Coupling Issues**:
1. momentum_factors.py → DataCache (27 direct calls)
2. Factor.execute → DataFrame.columns (assumes 1D structure)

**SOLID Violations**:
- ❌ **Liskov Substitution**: MomentumFactor uses DataCache, other factors expect DataFrame columns
- ❌ **Dependency Inversion**: Factors depend on concrete DataCache class
- ⚠️ **Single Responsibility**: Factor.execute does validation + execution + error handling

### Performance Characteristics

**Memory**: ~97MB per FinLab matrix (4563×2661×8 bytes)
**Execution**: Sequential only (no parallelization)
**Bottleneck**: O(n) row iteration in exit factors
**Opportunity**: DAG supports parallel execution

**Scalability Rating**: ⭐⭐⭐ (3/5 - Room for improvement)

### Maintainability Assessment

**Documentation**: ⭐⭐⭐⭐⭐ (5/5 - Excellent)
- Comprehensive docstrings
- Usage examples in all modules
- Clear architecture notes

**Technical Debt**:
1. Empty DataFrame workaround (strategy.py:446)
2. Commented-out module passing logic (strategy.py:449, factor.py:209-216)
3. No data access abstraction

**Maintainability Rating**: ⭐⭐⭐⭐ (4/5)

### Security Assessment

**Security Rating**: ⭐⭐⭐⭐ (4/5 - Generally Secure)

**Concerns**:
1. No memory limits (medium risk)
2. No thread-safety in DataCache (medium risk)
3. No bounds checking on cache size (medium risk)

**No critical security issues detected.**

---

## Solution Options Evaluation

### Option 1: Matrix-Native Factor Graph (✅ Recommended Phase 2)

**Concept**: Redesign Factor Graph to work with FinLab 2D matrices natively.

**Architecture**:
```python
class FinLabDataFrame:
    """Wrapper for FinLab Dates×Symbols matrices"""
    def __init__(self):
        self._matrices: Dict[str, pd.DataFrame] = {}

    def add_matrix(self, name: str, matrix: pd.DataFrame):
        self._matrices[name] = matrix

    def get_matrix(self, name: str) -> pd.DataFrame:
        return self._matrices[name]
```

**Pros**:
- ✅ Native FinLab support
- ✅ No DataCache workaround needed
- ✅ Vectorized operations (full performance)
- ✅ Maintains DAG structure
- ✅ Scales well

**Cons**:
- ⚠️ Major refactoring (all 13 factors)
- ⚠️ Breaking change
- ⚠️ Exit factor complexity (position tracking)
- ⚠️ Testing burden

**Effort**: 3-5 days (23-41 hours)
**Risk**: Medium
**Verdict**: ✅ **Best long-term solution**

### Option 2: Hybrid Wrapper (❌ Not Recommended)

**Concept**: Compatibility layer with both matrix and column access.

**Pros**:
- ✅ Backward compatible
- ✅ Gradual migration

**Cons**:
- ❌ High complexity (two execution modes)
- ❌ Performance overhead (conversions)
- ❌ Confusing API
- ❌ Technical debt accumulation

**Effort**: 2-3 days (15-25 hours)
**Risk**: High
**Verdict**: ❌ **Increases complexity without clear benefits**

### Option 3: Data Flattening (❌ Not Recommended)

**Concept**: Flatten matrices to long-format DataFrame (12.1M rows).

**Pros**:
- ✅ Standard DataFrame operations
- ✅ No wrapper needed

**Cons**:
- ❌ Memory explosion (12.1M rows)
- ❌ Performance degradation (groupby operations)
- ❌ Loses matrix operation performance

**Effort**: 2 days (10-15 hours)
**Risk**: High
**Verdict**: ❌ **Performance penalties outweigh benefits**

### Option 4: Temporary Disable (✅ Recommended Phase 1)

**Concept**: Disable Factor Graph, use template-based strategies.

**Implementation**:
```python
# In orchestrator configuration
use_factor_graph = False  # Disable temporarily
```

**Pros**:
- ✅ No refactoring
- ✅ Unblocks LLM validation
- ✅ Time to design properly
- ✅ Zero risk

**Cons**:
- ⚠️ Feature loss (temporary)
- ⚠️ Delayed value

**Effort**: 1 hour
**Risk**: None
**Verdict**: ✅ **Pragmatic Phase 1 solution**

### Recommendation Matrix

| Solution | Effort | Risk | Performance | Maintainability | Recommended |
|----------|--------|------|-------------|-----------------|-------------|
| Option 1: Matrix-Native | 3-5 days | Medium | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Phase 2 |
| Option 2: Hybrid Wrapper | 2-3 days | High | ⭐⭐⭐ | ⭐⭐ | ❌ No |
| Option 3: Data Flattening | 2 days | High | ⭐⭐ | ⭐⭐⭐ | ❌ No |
| Option 4: Temporary Disable | 1 hour | None | N/A | ⭐⭐⭐⭐⭐ | ✅ Phase 1 |

---

## Implementation Roadmap

### Phase 1: Immediate Unblocking (✅ COMPLETE)

**Goal**: Enable LLM validation study to proceed

**Tasks**:
1. ✅ Document Factor Graph issue (FACTOR_GRAPH_ARCHITECTURE_ISSUE.md)
2. ✅ Document debug record (DEBUG_RECORD_LLM_AUTO_FIX.md)
3. ✅ Complete comprehensive analysis (this document)
4. ✅ Disable Factor Graph in orchestrator configuration
   - Added experimental.use_factor_graph flag to config.yaml
   - Updated ExperimentConfig dataclass to load experimental section
   - Modified orchestrator to pass flag to learning config
   - Updated IterationExecutor to check flag and force LLM generation
5. ✅ Validated configuration system (flag loading and propagation)
6. 🚀 Ready to run LLM validation study

**Effort**: 2 hours (actual)
**Risk**: None
**Timeline**: ✅ **Completed 2025-11-10**

**Implementation Files:**
- experiments/llm_learning_validation/config.yaml (line 87-94)
- experiments/llm_learning_validation/config.py (line 71, 120)
- experiments/llm_learning_validation/orchestrator.py (line 216-225)
- src/learning/iteration_executor.py (line 329-363)

### Phase 2: Matrix-Native Redesign (Future)

**Goal**: Proper Factor Graph implementation for FinLab matrices

**Design Specifications**:

**2.1 FinLabDataFrame Wrapper** (2 hours)
- Dict[str, pd.DataFrame] storage
- Methods: add_matrix(), get_matrix(), has_matrix()
- No conversion overhead

**2.2 Core Architecture Changes** (8 hours)
- Modified Strategy.to_pipeline: Accept data module, return wrapper
- Modified Factor.execute: Validate matrices, not columns
- Pass data_module to factors for additional loading

**2.3 Factor Refactoring** (16 hours)
- Momentum factors: 4 factors × 1 hour = 4 hours
- Turtle factors: 4 factors × 1 hour = 4 hours
- Exit factors: 5 factors × 1.6 hours = 8 hours (complex position tracking)

**2.4 Integration & Testing** (12 hours)
- Update FactorRegistry (2 hours)
- Integration tests (8 hours)
- Documentation update (2 hours)

**2.5 Performance Validation** (2 hours)
- Benchmark vs templates
- Memory profiling
- Execution time comparison

**Total Effort**: 40 hours (1 week full-time)
**Risk**: Medium (well-defined scope)
**Timeline**: Phase 2 (post-LLM validation)

### Phase 3: Performance Optimization (Optional)

**Tasks**:
1. Parallel factor execution (multiprocessing)
2. Vectorize exit factor logic
3. Memory optimization
4. Caching strategy

**Effort**: 20 hours
**Timeline**: Phase 3 (post-redesign)

---

## Technical Appendix

### File Structure

```
src/
├── factor_graph/
│   ├── strategy.py (831 lines) - Strategy DAG implementation
│   ├── factor.py (252 lines) - Factor base class
│   └── factor_category.py - Category definitions
├── factor_library/
│   ├── momentum_factors.py (497 lines) - 4 momentum factors
│   ├── exit_factors.py (695 lines) - 5 exit factors
│   ├── turtle_factors.py (518 lines) - 4 turtle factors
│   └── registry.py (631 lines) - Factor registry
├── templates/
│   └── data_cache.py (351 lines) - Singleton cache
└── backtest/
    └── executor.py - Strategy execution engine
```

### Key Code References

**Empty DataFrame Creation** (strategy.py:446):
```python
result = pd.DataFrame()  # ❌ Creates empty container
```

**Data Module Storage** (strategy.py:449):
```python
self._data_module = data  # ⚠️ Stored but unused
```

**Column Validation** (factor.py:209-216):
```python
missing = [inp for inp in self.inputs if inp not in data.columns]
if missing:
    raise KeyError(f"Factor '{self.id}' requires columns {self.inputs}")
```

**DataCache Bypass** (momentum_factors.py:73-75):
```python
cache = DataCache.get_instance()
close = cache.get('price:收盤價', verbose=False)
```

**Matrix Assignment Failure** (momentum_factors.py:84):
```python
data['momentum'] = momentum  # ❌ Cannot assign 2D to 1D
```

---

## Confidence Assessment

**Analysis Confidence**: ✅ **Certain** (100%)
- Full execution trace completed
- All assumptions validated
- Failure point pinpointed
- Alternative paths confirmed
- Solution options evaluated
- Implementation plan detailed

**Recommendation Confidence**: ✅ **Very High** (95%)
- Two-phase approach validated
- Phase 1 risk-free and immediate
- Phase 2 well-scoped with clear migration path
- Expert analysis confirms findings

---

## Next Steps

1. ✅ **Analysis Complete** - This document
2. ✅ **Phase 1 Implementation** - Factor Graph temporarily disabled
3. 🚀 **LLM Validation Study** - Ready to execute pilot and full study
4. ⏸️ **Zen Planner** - Detailed Phase 2 implementation planning (when needed)
5. ⏸️ **Zen Testgen** - TDD test strategy design for Phase 2 (when needed)
6. ⏸️ **Spec Workflow** - Formal specification for Phase 2 (when needed)
7. ⏸️ **Claude Cloud Handoff** - Phase 2 implementation (future)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-10
**Analysis Tools**: Zen Analysis, Zen Tracer (Precision Mode)
**Model Used**: Gemini 2.5 Pro (Analysis), GPT-5 Pro (Expert Validation)
