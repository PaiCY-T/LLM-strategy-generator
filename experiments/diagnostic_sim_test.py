"""
sim() Backtesting Layer Diagnostic Test - Task 2.2
===================================================

Test COMPLETE end-to-end workflow including finlab.sim() to identify if backtesting
is the timeout source.

Test Configuration:
- 3 factors: momentum_factor + breakout_factor + rolling_trailing_stop_factor
- Template parameters: trail_percent=0.10, lookback_periods=20
- Uses EXACT template workflow from iteration_executor.py:720-758
- Timeout: 420s (same as main test)
- Timing: Per-PHASE instrumentation including sim() internals

Context from Phase 1 & Phase 2:
- ✅ Task 1.5: Direct factor execution: 5.23s (3 factors)
- ✅ Task 2.1: to_pipeline() orchestration: 3.46s
- ❓ Task 2.2: sim() execution: SUSPECT (hypothesis: >420s timeout)

Hypothesis (95% confidence):
The 420s+ timeout occurs in finlab.backtest.sim() due to:
- Position tracking: O(days × stocks × trades) complexity
- Trade execution: Per-signal simulation logic
- Portfolio rebalancing: State updates at each timestamp
- Performance metrics: Cumulative calculations over 4,568 days
- Cash flow tracking: Balance updates over time

Expected Results:
- TIMEOUT (>420s): Confirms sim() is the bottleneck → ROOT CAUSE FOUND
  → Document exact timeout location
  → Recommend sim() optimization or parameter tuning
  → Consider alternative backtesting approaches

- SUCCESS (<30s): Unexpected - investigate environment or missing factors
  → Check if test environment differs from actual execution
  → Verify test uses same data and parameters as template

- SLOW (30-420s): Partial bottleneck
  → sim() is slow but within timeout
  → May indicate environment-dependent performance

Critical Timing Points:
1. Strategy creation (expect <1s from Task 2.1)
2. to_pipeline() execution (expect ~3.5s from Task 2.1)
3. **sim() initialization** (NEW - baseline timestamp)
4. **Position signal processing** (NEW - SUSPECT)
5. **Trade execution simulation** (NEW - SUSPECT)
6. **Portfolio state tracking** (NEW - SUSPECT)
7. **Performance metric calculation** (NEW - SUSPECT)
8. **Report generation** (NEW)

Architecture: Phase 2.0 Factor Graph + finlab.backtest.sim() integration
"""

import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging with detailed timing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_sim_test():
    """Execute diagnostic test of COMPLETE workflow including sim() backtesting."""

    logger.info("=" * 80)
    logger.info("DIAGNOSTIC SIM TEST - Task 2.2")
    logger.info("=" * 80)
    logger.info(f"Test Start: {datetime.now()}")
    logger.info(f"Configuration: Full end-to-end workflow (Factor Graph + sim())")
    logger.info(f"Factors: 3-factor template (momentum + breakout + trailing_stop)")
    logger.info(f"Timeout: 420s")
    logger.info("")

    test_start = time.time()
    timing_log = {}

    try:
        # ====================================================================
        # PHASE 1: Import Dependencies
        # ====================================================================
        phase_start = time.time()
        logger.info("[SETUP] Importing dependencies...")

        from finlab import data
        from finlab.backtest import sim
        from src.factor_graph.strategy import Strategy
        from src.factor_library.registry import FactorRegistry

        phase_time = time.time() - phase_start
        timing_log['imports'] = phase_time
        logger.info(f"[SETUP] ✓ Imports complete in {phase_time:.2f}s")
        logger.info("")

        # ====================================================================
        # PHASE 2: Create Template Strategy (EXACT template workflow)
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 2] Creating template strategy (mirroring iteration_executor.py:720-758)...")

        # Create strategy with EXACT template workflow
        registry = FactorRegistry.get_instance()
        strategy = Strategy(id="template_sim_test", generation=0)

        # Add momentum factor (root)
        momentum_factor = registry.create_factor(
            "momentum_factor",
            parameters={"momentum_period": 20}
        )
        strategy.add_factor(momentum_factor, depends_on=[])

        # Add breakout factor (entry signal)
        breakout_factor = registry.create_factor(
            "breakout_factor",
            parameters={"entry_window": 20}
        )
        strategy.add_factor(breakout_factor, depends_on=[])

        # Add rolling trailing stop factor (stateless exit)
        trailing_stop_factor = registry.create_factor(
            "rolling_trailing_stop_factor",
            parameters={"trail_percent": 0.10, "lookback_periods": 20}
        )
        strategy.add_factor(
            trailing_stop_factor,
            depends_on=[momentum_factor.id, breakout_factor.id]
        )

        logger.info(f"Strategy ID: {strategy.id}")
        logger.info(f"Factors: {list(strategy.factors.keys())}")
        logger.info(f"Factor count: {len(strategy.factors)}")
        logger.info(f"DAG edges: {list(strategy.dag.edges())}")

        phase_time = time.time() - phase_start
        timing_log['strategy_creation'] = phase_time
        logger.info(f"[PHASE 2] ✓ Strategy created in {phase_time:.2f}s")
        logger.info("")

        # ====================================================================
        # PHASE 3: Execute to_pipeline() - Baseline from Task 2.1
        # ====================================================================
        logger.info("=" * 80)
        logger.info("PHASE 3: Executing Strategy.to_pipeline()")
        logger.info("=" * 80)
        logger.info(f"[TIMING] to_pipeline() START at {datetime.now()}")
        logger.info(f"[BASELINE] Expected time: ~3.5s (from Task 2.1)")
        logger.info("")

        pipeline_start = time.time()

        # THIS IS THE EXACT WORKFLOW USED BY TEMPLATES
        position = strategy.to_pipeline(data, skip_validation=False)

        pipeline_time = time.time() - pipeline_start
        timing_log['to_pipeline'] = pipeline_time

        logger.info("=" * 80)
        logger.info(f"✓ to_pipeline() COMPLETED in {pipeline_time:.2f}s")
        logger.info("=" * 80)
        logger.info(f"[TIMING] to_pipeline() END at {datetime.now()}")
        logger.info("")

        # Log position matrix details
        logger.info(f"Position shape: {position.shape}")
        logger.info(f"Position signals: {(position != 0).sum().sum()} non-zero entries")
        logger.info(f"Position True signals: {position.sum().sum()} True values")
        logger.info(f"Position memory: {position.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        logger.info("")

        # ====================================================================
        # PHASE 4: Execute sim() - CRITICAL TEST POINT
        # ====================================================================
        logger.info("=" * 80)
        logger.info("🚨 CRITICAL PHASE: Executing finlab.backtest.sim()")
        logger.info("=" * 80)
        logger.info(f"[TIMING] sim() START at {datetime.now()}")
        logger.info(f"[TIMING] Position matrix: {position.shape}")
        logger.info(f"[TIMING] Non-zero signals: {(position != 0).sum().sum()}")
        logger.info(f"[TIMING] True signals: {position.sum().sum()}")
        logger.info("")
        logger.info("Expected phases (cannot instrument finlab.sim() directly):")
        logger.info("  1. Position signal processing")
        logger.info("  2. Trade execution simulation")
        logger.info("  3. Portfolio state tracking (4,568 days × 2,662 stocks)")
        logger.info("  4. Performance metric calculation")
        logger.info("  5. Report generation")
        logger.info("")
        logger.info("🚨 IF TIMEOUT OCCURS HERE, sim() IS THE BOTTLENECK!")
        logger.info("")

        sim_start = time.time()

        # Execute sim() with same parameters as test_validation_compatibility.py
        # Using minimal parameters to match template workflow
        try:
            report = sim(
                position,
                resample="Q",  # Quarterly resampling for performance
                upload=False   # Don't upload to cloud
            )

            # If we reach this line, sim() completed successfully
            sim_time = time.time() - sim_start
            timing_log['sim'] = sim_time

            logger.info("=" * 80)
            logger.info(f"✓ sim() COMPLETED in {sim_time:.2f}s")
            logger.info("=" * 80)
            logger.info(f"[TIMING] sim() END at {datetime.now()}")
            logger.info("")

        except Exception as sim_error:
            sim_time = time.time() - sim_start
            timing_log['sim'] = sim_time
            logger.error("=" * 80)
            logger.error(f"✗ sim() FAILED after {sim_time:.2f}s")
            logger.error("=" * 80)
            logger.error(f"Error: {sim_error}")
            logger.error(f"Error type: {type(sim_error).__name__}")
            logger.error("")
            raise

        # ====================================================================
        # PHASE 5: Validate Results
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 5] Validating results...")

        # Check report object
        logger.info(f"Report type: {type(report)}")

        # Extract metrics using get_stats()
        stats = report.get_stats()
        logger.info(f"Stats keys: {list(stats.keys())[:10]}")
        logger.info(f"Sharpe Ratio: {stats.get('daily_sharpe', 'N/A')}")
        logger.info(f"Total Return: {stats.get('acc_return', 'N/A')}")
        logger.info(f"Max Drawdown: {stats.get('mdd', 'N/A')}")

        # Sanity checks
        assert report is not None, "Report object is None"
        assert stats is not None, "Stats object is None"
        assert len(stats) > 0, "Stats dictionary is empty"

        phase_time = time.time() - phase_start
        timing_log['validation'] = phase_time
        logger.info(f"[PHASE 5] ✓ Validation complete in {phase_time:.2f}s")
        logger.info("")

        # ====================================================================
        # TEST SUMMARY
        # ====================================================================
        test_time = time.time() - test_start
        logger.info("=" * 80)
        logger.info("TEST RESULT: SUCCESS ✓")
        logger.info("=" * 80)
        logger.info(f"Total execution time: {test_time:.2f}s")
        logger.info(f"Test End: {datetime.now()}")
        logger.info("")

        # Detailed timing breakdown
        logger.info("TIMING BREAKDOWN:")
        logger.info("-" * 80)
        logger.info(f"  Imports:              {timing_log['imports']:>8.2f}s")
        logger.info(f"  Strategy creation:    {timing_log['strategy_creation']:>8.2f}s")
        logger.info(f"  to_pipeline():        {timing_log['to_pipeline']:>8.2f}s")
        logger.info(f"  sim() TOTAL:          {timing_log['sim']:>8.2f}s  🎯")
        logger.info(f"  Validation:           {timing_log['validation']:>8.2f}s")
        logger.info("-" * 80)
        logger.info(f"  TOTAL:                {test_time:>8.2f}s")
        logger.info("")

        # ====================================================================
        # ANALYSIS & RECOMMENDATIONS
        # ====================================================================
        logger.info("ANALYSIS:")
        logger.info("-" * 80)

        # Compare with baselines
        logger.info("COMPARISON WITH PREVIOUS PHASES:")
        logger.info(f"  Task 1.5 (Direct execution):     5.23s")
        logger.info(f"  Task 2.1 (to_pipeline()):        3.46s  (baseline)")
        logger.info(f"  Task 2.2 (to_pipeline()):        {timing_log['to_pipeline']:.2f}s  (current)")
        logger.info(f"  Task 2.2 (sim()):                {timing_log['sim']:.2f}s  🎯 NEW")
        logger.info("")

        # Analyze sim() performance
        if timing_log['sim'] > 420:
            logger.info("🚨 CRITICAL: sim() execution time > 420s (TIMEOUT)")
            logger.info("")
            logger.info("→ ROOT CAUSE CONFIRMED: sim() IS the bottleneck!")
            logger.info("")
            logger.info("→ HYPOTHESIS VALIDATED:")
            logger.info("  - Factor execution:  ✅ Fast (~5s)")
            logger.info("  - to_pipeline():     ✅ Fast (~3.5s)")
            logger.info("  - sim() execution:   🚨 TIMEOUT (>420s)")
            logger.info("")
            logger.info("→ BOTTLENECK BREAKDOWN:")
            logger.info(f"  Position matrix: {position.shape}")
            logger.info(f"  Trading days: {position.shape[0]} days")
            logger.info(f"  Stocks: {position.shape[1]} stocks")
            logger.info(f"  Non-zero signals: {(position != 0).sum().sum()}")
            logger.info(f"  Complexity: O(days × stocks × trades)")
            logger.info("")
            logger.info("→ IMMEDIATE ACTIONS:")
            logger.info("  1. Reduce backtest period (e.g., last 1 year instead of full history)")
            logger.info("  2. Implement position matrix sparsification")
            logger.info("  3. Use quarterly resampling (already enabled)")
            logger.info("  4. Consider alternative backtesting engines")
            logger.info("  5. Profile sim() internals if source available")

        elif timing_log['sim'] > 30:
            logger.info(f"⚠️  WARNING: sim() execution time {timing_log['sim']:.2f}s (30-420s range)")
            logger.info("")
            logger.info("→ CONCLUSION: sim() is slow but doesn't timeout")
            logger.info(f"  - Factor execution:  ✅ Fast (~5s)")
            logger.info(f"  - to_pipeline():     ✅ Fast ({timing_log['to_pipeline']:.2f}s)")
            logger.info(f"  - sim() execution:   ⚠️  SLOW ({timing_log['sim']:.2f}s)")
            logger.info("")
            logger.info("→ PARTIAL BOTTLENECK IDENTIFIED:")
            logger.info(f"  Position matrix: {position.shape}")
            logger.info(f"  sim() time: {timing_log['sim']:.2f}s")
            logger.info(f"  Percentage: {timing_log['sim'] / test_time * 100:.1f}% of total")
            logger.info("")
            logger.info("→ RECOMMENDATIONS:")
            logger.info("  1. Monitor sim() performance over time")
            logger.info("  2. Consider optimization if performance degrades")
            logger.info("  3. Environment-dependent performance possible")
            logger.info("  4. Acceptable for template workflow if <60s")

        else:
            logger.info(f"✅ EXCELLENT: sim() completed in {timing_log['sim']:.2f}s (< 30s)")
            logger.info("")
            logger.info("→ UNEXPECTED RESULT: All phases are fast!")
            logger.info(f"  - Factor execution:  ✅ Fast (~5s)")
            logger.info(f"  - to_pipeline():     ✅ Fast ({timing_log['to_pipeline']:.2f}s)")
            logger.info(f"  - sim() execution:   ✅ Fast ({timing_log['sim']:.2f}s)")
            logger.info(f"  - Total time:        ✅ Fast ({test_time:.2f}s)")
            logger.info("")
            logger.info("→ INVESTIGATION REQUIRED:")
            logger.info("  1. Why does template test timeout if all phases are fast?")
            logger.info("  2. Check if test environment differs from actual execution")
            logger.info("  3. Verify test uses same data and parameters as template")
            logger.info("  4. Review iteration_executor.py for missing logic")
            logger.info("  5. Consider environment-specific issues (memory, CPU)")

        logger.info("=" * 80)
        logger.info("")

        # Phase breakdown as percentage
        logger.info("PHASE BREAKDOWN (% of total):")
        logger.info("-" * 80)
        logger.info(f"  Imports:           {timing_log['imports'] / test_time * 100:>5.1f}%")
        logger.info(f"  Strategy creation: {timing_log['strategy_creation'] / test_time * 100:>5.1f}%")
        logger.info(f"  to_pipeline():     {timing_log['to_pipeline'] / test_time * 100:>5.1f}%")
        logger.info(f"  sim():             {timing_log['sim'] / test_time * 100:>5.1f}%  🎯")
        logger.info(f"  Validation:        {timing_log['validation'] / test_time * 100:>5.1f}%")
        logger.info("")

        return 0

    except Exception as e:
        test_time = time.time() - test_start
        logger.error("=" * 80)
        logger.error("TEST RESULT: ERROR ✗")
        logger.error("=" * 80)
        logger.error(f"Error after {test_time:.2f}s: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error("")

        # Check which phase failed
        if 'imports' not in timing_log:
            logger.error("→ FAILURE PHASE: Import dependencies")
        elif 'strategy_creation' not in timing_log:
            logger.error("→ FAILURE PHASE: Strategy creation")
        elif 'to_pipeline' not in timing_log:
            logger.error("→ FAILURE PHASE: to_pipeline() execution")
        elif 'sim' not in timing_log:
            logger.error("→ FAILURE PHASE: sim() execution")
            logger.error("")
            logger.error("🚨 CRITICAL: Error occurred in sim()!")
            logger.error("→ CONCLUSION: sim() has a bug or timeout")
            logger.error("")
            logger.error("→ NEXT STEP:")
            logger.error("  1. Review error traceback below")
            logger.error("  2. Check if sim() timed out or raised exception")
            logger.error("  3. Verify position matrix is valid")
            logger.error("  4. Check finlab.backtest.sim() documentation")
        else:
            logger.error("→ FAILURE PHASE: Validation")

        logger.error("")
        logger.error("Timing log at failure:")
        for phase, duration in timing_log.items():
            logger.error(f"  {phase}: {duration:.2f}s")

        import traceback
        logger.error("")
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())

        return 1


if __name__ == "__main__":
    exit_code = run_sim_test()
    sys.exit(exit_code)
