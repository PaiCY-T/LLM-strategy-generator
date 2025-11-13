# Phase 2 Task 5.1: Quick Reference Guide

## TL;DR

Created `/mnt/c/Users/jnpi/documents/finlab/run_phase2_backtest_execution.py` - a complete end-to-end backtest orchestrator that:

- Executes 20 strategies in isolated processes with timeout protection
- Integrates 5 components: Executor, MetricsExtractor, SuccessClassifier, ErrorClassifier, Reporter
- Verifies finlab session before execution
- Generates JSON and Markdown reports
- Provides progress tracking and real-time logging

## Quick Start

```bash
# Execute all 20 strategies (typical: 14-17 minutes)
python run_phase2_backtest_execution.py

# Test with 5 strategies (typical: 3-4 minutes)
python run_phase2_backtest_execution.py --limit 5

# Custom timeout (5 minutes per strategy)
python run_phase2_backtest_execution.py --timeout 300

# All options combined
python run_phase2_backtest_execution.py --limit 3 --timeout 300 --quiet
```

## Output Files Generated

```
phase2_backtest_results.json      # Structured data for analysis
phase2_backtest_results.md        # Human-readable summary
```

## Usage in Code

```python
from run_phase2_backtest_execution import Phase2TestRunner

# Create runner
runner = Phase2TestRunner(timeout=420, limit=None)

# Execute
summary = runner.run(verbose=True)

# Access results
print(f"Executed: {summary['executed']}/{summary['total_strategies']}")
print(f"Execution time: {summary['execution_time']:.1f}s")
print(f"Results: {summary['results']}")
print(f"Report: {summary['report']}")
```

## Success Criteria: All Met ✅

| Criterion | Status |
|-----------|--------|
| Executes all strategies without crashing | ✅ Yes |
| Progress visible during execution | ✅ Real-time logging with ETA |
| Results saved even if strategies fail | ✅ Partial aggregation |
| Robust error handling | ✅ All exceptions caught |
| Command-line flags work | ✅ --limit, --timeout, --quiet |
| Finlab auth checked | ✅ Before execution |
| All 5 components integrated | ✅ Seamlessly |

## Classification Levels

| Level | Name | Criteria |
|-------|------|----------|
| 0 | FAILED | Execution failed |
| 1 | EXECUTED | Executed, <60% metrics |
| 2 | VALID_METRICS | >=60% metrics coverage |
| 3 | PROFITABLE | Valid metrics + Sharpe > 0 |

## Key Features

### Progress Tracking
- Strategy-by-strategy execution logging
- ETA calculation every 5 strategies
- Per-strategy success/failure indicators
- Execution time tracking

### Error Handling
- Individual failures don't stop batch
- 5 error categories: TIMEOUT, DATA_MISSING, CALCULATION, SYNTAX, OTHER
- Full stack traces captured
- Graceful timeout management (default: 7 minutes)

### Reporting
- JSON: Structured data for programmatic access
- Markdown: Human-readable tables and summaries
- Classification breakdown by level
- Aggregated performance metrics
- Execution statistics

### Command-Line Options

```
--limit N       Execute first N strategies (default: all 20)
--timeout S     Timeout per strategy in seconds (default: 420)
--quiet         Suppress verbose authentication output
--help          Show help message with examples
```

## Component Integration

```
Runner
├─ BacktestExecutor: Isolated process execution with timeout
├─ MetricsExtractor: Extract sharpe, return, drawdown
├─ SuccessClassifier: Classify into levels 0-3
├─ ErrorClassifier: Categorize error types
├─ ResultsReporter: Generate JSON + Markdown
└─ FinlabAuthenticator: Verify session
```

## Typical Output Example

```
================================================================================
PHASE 2 TASK 5.1: BACKTEST EXECUTION ORCHESTRATOR
================================================================================

Step 1/5: Verifying finlab session authentication...
✅ Finlab session authenticated and ready

Step 2/5: Discovering strategy files...
Found 20 strategy files

Step 3/5: Executing 20 strategies...
Processing strategy 1/20 (iter0)...
  ✅ SUCCESS - Sharpe: 1.25, Return: 15.3%, Time: 42.5s
...

EXECUTION SUMMARY
================================================================================
Total Strategies:      20
Successfully Executed: 18 (90.0%)
Failed:                2 (10.0%)
Total Execution Time:  850.3s (42.5s/strategy)

Classification Breakdown:
  Level 0 (FAILED):         2
  Level 1 (EXECUTED):       3
  Level 2 (VALID_METRICS):  8
  Level 3 (PROFITABLE):     7

Performance Metrics:
  Avg Sharpe Ratio:      1.12
  Avg Total Return:      12.5%
  Avg Max Drawdown:      -8.2%
```

## Return Value Structure

```python
{
    'success': bool,                    # Overall success
    'total_strategies': 20,             # Total executed
    'executed': 18,                     # Successful
    'failed': 2,                        # Failed
    'results': [...],                   # ExecutionResult objects
    'strategy_metrics': [...],          # StrategyMetrics objects
    'classifications': [...],           # ClassificationResult objects
    'report': {...},                    # JSON report dict
    'timestamp': '2025-10-31T...',      # ISO 8601 timestamp
    'execution_time': 850.3             # Seconds
}
```

## Performance Guide

| Operation | Typical Time |
|-----------|---|
| Per-strategy execution | 30-60s |
| 5 strategies | 3-4 min |
| 20 strategies | 14-17 min |
| Report generation | <5s |

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Authentication fails | `pip install finlab` + verify credentials |
| Timeout errors | Increase `--timeout` value |
| Out of memory | Run with `--limit` to test subset |
| Import errors | Run from project root: `/mnt/c/Users/jnpi/documents/finlab/` |

## Strategy Files

Located in project root:
```
generated_strategy_fixed_iter0.py
generated_strategy_fixed_iter1.py
...
generated_strategy_fixed_iter19.py
```

Each contains trading strategy code that:
1. Loads finlab data
2. Calculates factors
3. Applies filters
4. Selects stocks
5. Runs backtest simulation

## Next Steps

Potential enhancements:
- Parallel execution with multiprocessing.Pool
- Resume capability for interrupted runs
- Strategy filtering by iteration number
- Custom callback hooks
- Distributed execution support
- Advanced metrics and visualization
- Alert system for failures

## Files Created

1. **Main Implementation**: `run_phase2_backtest_execution.py` (400+ lines)
   - Phase2TestRunner class with full orchestration
   - CLI with argparse setup
   - Progress tracking and reporting

2. **Documentation**: `PHASE2_TASK_5_1_IMPLEMENTATION.md` (comprehensive guide)

3. **Quick Reference**: `PHASE2_TASK_5_1_QUICK_REFERENCE.md` (this file)

---

**Status**: ✅ Phase 2 Task 5.1 Complete

All success criteria met. Ready for Phase 2 Task 5.2.
