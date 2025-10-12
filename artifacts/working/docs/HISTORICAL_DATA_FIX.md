# Historical Data Loading Fix - Investigation Summary

## Problem Statement
ALL strategies timeout after 600 seconds, with 100% failure rate across 16+ iterations.

## Root Cause Analysis

### Initial Diagnosis (INCOMPLETE)
- Identified that `from finlab import data` loads ALL Taiwan stock market data (10+ minutes, 8GB+ RAM)
- Recognized Windows multiprocessing limitation: module objects cannot be pickled
- **However, this was only PART of the problem**

### Actual Root Cause (COMPLETE)
The timeout occurs in **TWO STAGES**:

#### Stage 1: Strategy Execution (SOLVED by PreloadedData)
- **Problem**: Each sandbox process re-imports `from finlab import data` (10+ minutes)
- **Solution**: PreloadedData wrapper passes DataFrame dictionaries via multiprocessing
- **Result**: Data loading reduced from 10+ minutes to 13 seconds ✅

#### Stage 2: Backtest Execution (UNSOLVED - CRITICAL BOTTLENECK)
- **Problem**: `sim()` backtest function INTERNALLY loads historical data again
- **Evidence**: Even with PreloadedData, execution still timeouts after 600s
- **Cause**: The `sim()` function from `finlab.backtest` module loads its own data internally
- **Result**: Total execution time still exceeds 600s timeout ❌

## Implementation Attempt

### What Was Implemented
1. Created `data_wrapper.py` with PreloadedData class
2. Modified `sandbox_executor.py` to accept data_wrapper parameter
3. Modified `iteration_engine.py` to preload datasets at startup
4. Loaded 9 core datasets in 13 seconds (huge improvement!)

### Test Results
```
⏳ Pre-loading Finlab datasets (this may take 10+ minutes)...
✅ Finlab datasets loaded successfully (9 datasets)  # 13 seconds

Iteration 1/3
  ✓ Strategy saved
  ✓ Validation passed
  Executing backtest...
  ✗ Backtest failed: Execution timeout exceeded (600s)  # STILL TIMING OUT!
```

### Files Modified
- ✅ `/mnt/c/Users/jnpi/Documents/finlab/data_wrapper.py` (CREATED)
- ✅ `/mnt/c/Users/jnpi/Documents/finlab/sandbox_executor.py` (MODIFIED)
- ✅ `/mnt/c/Users/jnpi/Documents/finlab/iteration_engine.py` (MODIFIED)

## Why PreloadedData Is Insufficient

The PreloadedData wrapper only solves data loading for **strategy code execution**:
- Strategy code: `close = data.get('price:收盤價')` ✅ Fast (uses preloaded data)
- Backtest code: `report = sim(signal, ...)` ❌ Slow (sim() loads data internally)

The `sim()` function is a black box that internally:
1. Loads historical price data for ALL Taiwan stocks
2. Calculates portfolio returns
3. Generates backtest report

**We cannot intercept or optimize the internal data loading of `sim()`** without modifying the Finlab library itself.

## Alternative Solutions

### Option 1: Increase Timeout (SIMPLE, INEFFICIENT)
```python
MAX_EXECUTION_TIME = 1200  # 20 minutes instead of 10
```
- **Pros**: Simple one-line change
- **Cons**:
  - 10 iterations would take 200+ minutes (3+ hours)
  - Still slow and inefficient
  - Doesn't solve root cause

### Option 2: Disk Cache + Index Only (COMPLEX, EFFICIENT)
- Pre-cache all historical data to disk once
- Modify `sim()` call to use cached data via environment variable
- **Requires**: Understanding Finlab's internal caching mechanism
- **Risk**: May not be possible without library modification

### Option 3: Use Simplified Backtest (MODERATE, PRACTICAL)
- Replace `sim()` with custom lightweight backtest
- Calculate returns manually: `(signal * close.pct_change()).sum(axis=1)`
- **Pros**: Fast, controllable, no data loading
- **Cons**: Loses Finlab's detailed metrics (fees, slippage, etc.)

### Option 4: Contact Finlab Support (EXTERNAL)
- Request guidance on optimizing `sim()` performance
- Ask if there's a way to pass preloaded data to `sim()`
- **Timeline**: Unknown, depends on support responsiveness

## Recommended Path Forward

**SHORT TERM** (Unblock MVP):
- Increase timeout to 1200s (20 minutes)
- Accept slow iteration time for now
- Complete MVP validation with 3-5 iterations

**MEDIUM TERM** (Performance Optimization):
- Implement custom lightweight backtest (Option 3)
- Calculate basic metrics: returns, Sharpe ratio
- Run 10+ iterations in reasonable time

**LONG TERM** (Comprehensive Solution):
- Investigate Finlab's caching mechanism
- Consider forking Finlab to add preload support
- Or implement full custom backtest engine

## Lessons Learned

1. **Multiprocessing on Windows requires picklable objects** - Module objects cannot be passed
2. **Black-box functions may have hidden data loading** - Even when input data is optimized
3. **Performance bottlenecks can exist in multiple layers** - Solving one layer may reveal another
4. **Integration with external libraries has limitations** - Cannot always optimize internal behavior

## Next Steps

1. **DECISION POINT**: Choose short-term solution (increase timeout or custom backtest)
2. Document decision rationale in tasks.md
3. Implement chosen solution
4. Run validation test (3-5 iterations)
5. If successful, proceed with full 10-iteration test

---

**Status**: Investigation complete, awaiting decision on solution approach
**Date**: 2025-10-09
**Context**: Phase 4 (Task 4.5) - 10-iteration validation blocked by systematic timeouts
