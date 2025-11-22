"""
Pipeline Integration Diagnostic Test - Task 2.1
===============================================

Test Strategy.to_pipeline() orchestration to identify if this is the timeout bottleneck.

Test Configuration:
- 3 factors: momentum_factor + breakout_factor + rolling_trailing_stop_factor
- Template parameters: trail_percent=0.10, lookback_periods=20
- Uses EXACT template workflow from iteration_executor.py:720-758
- Timeout: 420s (same as main test)
- Timing: Per-PHASE instrumentation to isolate bottleneck

Context from Phase 1:
- ✅ Direct factor execution: 5.23s total (Task 1.5 SUCCESS)
- ✅ All 3 factors execute efficiently when called directly
- ❌ Template test timeouts at unknown location

Hypothesis (90% confidence):
Timeout occurs in to_pipeline() due to:
- N² dependency resolution complexity
- Redundant container operations
- Inefficient graph traversal
- Missing optimization in pipeline assembly

Expected Results:
- SUCCESS (<30s): to_pipeline() is healthy → Proceed to Task 2.2 (sim() testing)
- TIMEOUT (>420s): to_pipeline() is the culprit → Profile internal methods
- SLOW (30-420s): Partial bottleneck → Deeper profiling needed

Critical Timing Points:
1. Strategy creation (expect <1s)
2. to_pipeline() entry (baseline timestamp)
3. Phase 1: Validation (expect <1s)
4. Phase 2: Container creation (expect <1s)
5. Phase 3: Graph execution (expect ~5s based on Phase 1)
   - Factor 1: momentum_factor (expect ~2.75s)
   - Factor 2: breakout_factor (expect ~2s)
   - Factor 3: trailing_stop_factor (expect <1s)
6. Phase 4: Naming adapter + validation (expect <1s)
7. to_pipeline() exit (total time calculation)

Architecture: Phase 2.0 Factor Graph with FinLabDataFrame container
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


def run_pipeline_test():
    """Execute diagnostic test of Strategy.to_pipeline() orchestration."""

    logger.info("=" * 80)
    logger.info("DIAGNOSTIC PIPELINE TEST - Task 2.1")
    logger.info("=" * 80)
    logger.info(f"Test Start: {datetime.now()}")
    logger.info(f"Configuration: Full to_pipeline() workflow")
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
        strategy = Strategy(id="template_pipeline_test", generation=0)

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
        # PHASE 3: Execute to_pipeline() - CRITICAL TEST POINT
        # ====================================================================
        logger.info("=" * 80)
        logger.info("🚨 CRITICAL PHASE: Executing Strategy.to_pipeline()")
        logger.info("=" * 80)
        logger.info(f"[TIMING] to_pipeline() START at {datetime.now()}")
        logger.info(f"[TIMING] Expected phases:")
        logger.info(f"          1. Validation (~1s)")
        logger.info(f"          2. Container creation (~1s)")
        logger.info(f"          3. Graph execution (~5s based on Phase 1)")
        logger.info(f"          4. Naming adapter + validation (~1s)")
        logger.info(f"          Total expected: ~8s")
        logger.info("")

        pipeline_start = time.time()

        # THIS IS THE EXACT WORKFLOW USED BY TEMPLATES
        # If timeout occurs here, we've found the bottleneck
        position = strategy.to_pipeline(data, skip_validation=False)

        # If we reach this line, to_pipeline() completed successfully
        pipeline_time = time.time() - pipeline_start
        timing_log['to_pipeline'] = pipeline_time

        logger.info("=" * 80)
        logger.info(f"✓ to_pipeline() COMPLETED in {pipeline_time:.2f}s")
        logger.info("=" * 80)
        logger.info(f"[TIMING] to_pipeline() END at {datetime.now()}")
        logger.info("")

        # ====================================================================
        # PHASE 4: Validate Results
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 4] Validating results...")

        # Check position matrix
        logger.info(f"Position shape: {position.shape}")
        logger.info(f"Position signals: {position.sum().sum()} True values")
        logger.info(f"Position dtypes: {position.dtypes.value_counts().to_dict()}")
        logger.info(f"Position memory: {position.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

        # Sanity checks
        assert position.shape[0] > 0, "Position matrix has no rows"
        assert position.shape[1] > 0, "Position matrix has no columns"
        assert position.sum().sum() >= 0, "Position matrix has negative signals"

        phase_time = time.time() - phase_start
        timing_log['validation'] = phase_time
        logger.info(f"[PHASE 4] ✓ Validation complete in {phase_time:.2f}s")
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
        logger.info(f"  to_pipeline() TOTAL:  {timing_log['to_pipeline']:>8.2f}s  🎯")
        logger.info(f"  Validation:           {timing_log['validation']:>8.2f}s")
        logger.info("-" * 80)
        logger.info(f"  TOTAL:                {test_time:>8.2f}s")
        logger.info("")

        # ====================================================================
        # ANALYSIS & RECOMMENDATIONS
        # ====================================================================
        logger.info("ANALYSIS:")
        logger.info("-" * 80)

        if test_time < 30:
            logger.info("✅ EXCELLENT: to_pipeline() completed in < 30s")
            logger.info("")
            logger.info(f"→ CONCLUSION: to_pipeline() is NOT the bottleneck!")
            logger.info(f"   - Direct execution (Phase 1): 5.23s")
            logger.info(f"   - to_pipeline() execution:    {timing_log['to_pipeline']:.2f}s")
            logger.info(f"   - Overhead:                   {timing_log['to_pipeline'] - 5.23:.2f}s")
            logger.info("")

            if timing_log['to_pipeline'] - 5.23 > 5:
                logger.info(f"⚠️  WARNING: to_pipeline() overhead is {timing_log['to_pipeline'] - 5.23:.2f}s")
                logger.info("   This suggests some inefficiency in orchestration logic")
                logger.info("")
                logger.info("→ RECOMMENDATION:")
                logger.info("  1. Review strategy.py to_pipeline() implementation for optimization")
                logger.info("  2. Check if validation or naming adapter is slow")
                logger.info("  3. Proceed to Task 2.2 (sim() testing) as primary suspect")
            else:
                logger.info("✓ to_pipeline() overhead is acceptable (<5s)")
                logger.info("")
                logger.info("→ HYPOTHESIS REFUTED: Bottleneck is NOT in to_pipeline()")
                logger.info("")
                logger.info("→ NEXT STEP: Proceed to Task 2.2")
                logger.info("  Test sim() execution to identify the real bottleneck")
                logger.info("")
                logger.info("→ UPDATED HYPOTHESIS:")
                logger.info("  - Factor execution: ✅ Fast (~5s)")
                logger.info("  - to_pipeline():    ✅ Fast (< 30s)")
                logger.info("  - sim() execution:  ❓ SUSPECT (>420s timeout)")

        elif test_time < 420:
            logger.info(f"⚠️  ANALYSIS: to_pipeline() execution time {test_time:.2f}s (30-420s range)")
            logger.info("")
            logger.info("→ CONCLUSION: to_pipeline() has performance issues but doesn't timeout")
            logger.info(f"   - Direct execution (Phase 1): 5.23s")
            logger.info(f"   - to_pipeline() execution:    {timing_log['to_pipeline']:.2f}s")
            logger.info(f"   - Overhead:                   {timing_log['to_pipeline'] - 5.23:.2f}s")
            logger.info("")
            logger.info("→ BOTTLENECK IDENTIFIED: to_pipeline() orchestration")
            logger.info("")
            logger.info("→ RECOMMENDATION:")
            logger.info("  1. Profile to_pipeline() internal methods:")
            logger.info("     - validate_structure()")
            logger.info("     - Container creation")
            logger.info("     - Topological sort")
            logger.info("     - Factor execution loop")
            logger.info("     - Naming adapter logic")
            logger.info("     - validate_data()")
            logger.info("  2. Check strategy.py lines 607-790 for N² complexity")
            logger.info("  3. Optimize slow phase and re-test")

        else:
            logger.info("🚨 CRITICAL: to_pipeline() execution time > 420s (TIMEOUT)")
            logger.info("")
            logger.info("→ CONCLUSION: Timeout confirmed in to_pipeline()!")
            logger.info("→ HYPOTHESIS VALIDATED: to_pipeline() IS the bottleneck")
            logger.info("")
            logger.info("→ NEXT STEP: Deep profiling of to_pipeline() internals")
            logger.info("  The timeout logs in strategy.py should show which phase hung:")
            logger.info("  - Phase 1: Validation")
            logger.info("  - Phase 2: Container creation")
            logger.info("  - Phase 3: Graph execution (most likely suspect)")
            logger.info("  - Phase 4: Naming adapter + validation")

        logger.info("=" * 80)
        logger.info("")

        # Phase 1 comparison
        logger.info("COMPARISON WITH PHASE 1 (Direct Execution):")
        logger.info("-" * 80)
        logger.info(f"  Phase 1 (Task 1.5) - Direct execution:  5.23s")
        logger.info(f"  Task 2.1           - to_pipeline():     {timing_log['to_pipeline']:.2f}s")
        logger.info(f"  Overhead:                               {timing_log['to_pipeline'] - 5.23:+.2f}s")
        logger.info("")

        if timing_log['to_pipeline'] < 10:
            logger.info("✅ Overhead is minimal (<10s total)")
            logger.info("   to_pipeline() orchestration is efficient")
        elif timing_log['to_pipeline'] < 30:
            logger.info("⚠️  Overhead is moderate (10-30s)")
            logger.info("   Consider optimization but not critical")
        else:
            logger.info("🚨 Overhead is significant (>30s)")
            logger.info("   Deep profiling of to_pipeline() required")

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
            logger.error("")
            logger.error("🚨 CRITICAL: Error occurred in to_pipeline()!")
            logger.error("→ CONCLUSION: to_pipeline() has a bug or timeout")
            logger.error("")
            logger.error("→ NEXT STEP:")
            logger.error("  1. Review error traceback below")
            logger.error("  2. Check strategy.py to_pipeline() implementation")
            logger.error("  3. Look for timing logs in strategy.py Phase 1-4 markers")
            logger.error("  4. Fix error and re-run test")
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
    exit_code = run_pipeline_test()
    sys.exit(exit_code)
