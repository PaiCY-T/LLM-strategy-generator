"""
Trailing Stop Factor Diagnostic Test - Task 1.5
================================================

Test rolling_trailing_stop_factor with dependencies to isolate timeout source.

Test Configuration:
- 3 factors: momentum_factor + breakout_factor + rolling_trailing_stop_factor
- Template parameters: trail_percent=0.10, lookback_periods=20
- Dependencies: rolling_trailing_stop depends on both momentum and breakout
- Timeout: 420s (same as main test)
- Timing: Per-factor instrumentation to isolate bottleneck

Expected Results:
- TIMEOUT (>420s): Confirms rolling_trailing_stop_factor is the culprit → Phase 2 fix
- SUCCESS (<30s): Unexpected - need to investigate factor interactions
- ERROR: Fix error and re-evaluate

Critical Timing Points:
1. After momentum_factor execution (expect ~2.75s based on Task 1.3)
2. After breakout_factor execution (expect ~10.84s based on Task 1.4)
3. BEFORE rolling_trailing_stop_factor execution ⚠️
4. AFTER rolling_trailing_stop_factor execution ⚠️ (if it completes)

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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_trailing_stop_test():
    """Execute diagnostic test with 3 factors and per-factor timing."""

    logger.info("=" * 80)
    logger.info("DIAGNOSTIC TRAILING STOP TEST - Task 1.5")
    logger.info("=" * 80)
    logger.info(f"Test Start: {datetime.now()}")
    logger.info(f"Configuration: 3 factors with dependencies")
    logger.info(f"Factors: momentum_factor, breakout_factor, rolling_trailing_stop_factor")
    logger.info(f"Timeout: 420s")
    logger.info("")

    test_start = time.time()
    timing_log = {}

    try:
        # ====================================================================
        # PHASE 1: Import Dependencies
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 1] Importing dependencies...")

        from finlab import data
        from src.factor_graph.strategy import Strategy
        from src.factor_graph.finlab_dataframe import FinLabDataFrame
        from src.factor_library.momentum_factors import create_momentum_factor
        from src.factor_library.turtle_factors import create_breakout_factor
        from src.factor_library.stateless_exit_factors import create_rolling_trailing_stop_factor

        phase_time = time.time() - phase_start
        timing_log['imports'] = phase_time
        logger.info(f"[PHASE 1] ✓ Imports complete in {phase_time:.2f}s")
        logger.info("")

        # ====================================================================
        # PHASE 2: Create Strategy with 3 Factors
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 2] Creating strategy with 3 factors...")

        # Create strategy
        strategy = Strategy(id="trailing_stop_test", generation=0)

        # Create factors (match template parameters)
        momentum_factor = create_momentum_factor(momentum_period=20)
        breakout_factor = create_breakout_factor(entry_window=20)
        trailing_stop_factor = create_rolling_trailing_stop_factor(
            trail_percent=0.10,
            lookback_periods=20
        )

        # Add factors with dependencies
        strategy.add_factor(momentum_factor, depends_on=[])
        strategy.add_factor(breakout_factor, depends_on=[])
        strategy.add_factor(
            trailing_stop_factor,
            depends_on=[momentum_factor.id, breakout_factor.id]
        )

        logger.info(f"Strategy ID: {strategy.id}")
        logger.info(f"Factors: {list(strategy.factors.keys())}")
        logger.info(f"Factor count: {len(strategy.factors)}")

        phase_time = time.time() - phase_start
        timing_log['strategy_creation'] = phase_time
        logger.info(f"[PHASE 2] ✓ Strategy created in {phase_time:.2f}s")
        logger.info("")

        # ====================================================================
        # PHASE 3: Load Market Data
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 3] Loading market data...")

        # Load data
        close = data.get('price:收盤價')
        logger.info(f"Close data shape: {close.shape}")
        logger.info(f"Close data memory: {close.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

        phase_time = time.time() - phase_start
        timing_log['data_loading'] = phase_time
        logger.info(f"[PHASE 3] ✓ Data loaded in {phase_time:.2f}s")
        logger.info("")

        # ====================================================================
        # PHASE 4: Execute Factors with Per-Factor Timing (CRITICAL)
        # ====================================================================
        logger.info("[PHASE 4] Executing factors with detailed timing...")
        logger.info("NOTE: This phase isolates the bottleneck location")
        logger.info("")

        # Initialize container
        container = FinLabDataFrame(data_module=data)
        container.add_matrix('close', close)

        # --------------------------------------------------------------------
        # Factor 1: momentum_factor (expect ~2.75s based on Task 1.3)
        # --------------------------------------------------------------------
        logger.info(f"[TIMING] Executing momentum_factor at {datetime.now()}")
        factor_start = time.time()

        container = momentum_factor.execute(container)

        factor_time = time.time() - factor_start
        timing_log['momentum_factor'] = factor_time
        logger.info(f"[TIMING] ✓ momentum_factor completed in {factor_time:.2f}s")
        logger.info(f"          Output: {momentum_factor.outputs}")
        logger.info("")

        # --------------------------------------------------------------------
        # Factor 2: breakout_factor (expect ~8s based on Task 1.4)
        # --------------------------------------------------------------------
        logger.info(f"[TIMING] Executing breakout_factor at {datetime.now()}")
        factor_start = time.time()

        container = breakout_factor.execute(container)

        factor_time = time.time() - factor_start
        timing_log['breakout_factor'] = factor_time
        logger.info(f"[TIMING] ✓ breakout_factor completed in {factor_time:.2f}s")
        logger.info(f"          Output: {breakout_factor.outputs}")
        logger.info("")

        # --------------------------------------------------------------------
        # Factor 3: rolling_trailing_stop_factor (SUSPECT - expect timeout)
        # --------------------------------------------------------------------
        logger.info("=" * 80)
        logger.info("🚨 CRITICAL POINT: About to execute rolling_trailing_stop_factor")
        logger.info("=" * 80)
        logger.info(f"[TIMING] Execution start: {datetime.now()}")
        logger.info(f"[TIMING] Expected: This should timeout if hypothesis is correct")
        logger.info(f"[TIMING] Dependencies available: {trailing_stop_factor.inputs}")
        logger.info("")

        factor_start = time.time()

        # THIS IS WHERE WE EXPECT THE HANG (if hypothesis is correct)
        container = trailing_stop_factor.execute(container)

        # If we reach this line, the factor completed successfully
        factor_time = time.time() - factor_start
        timing_log['trailing_stop_factor'] = factor_time
        logger.info("=" * 80)
        logger.info("⚠️  UNEXPECTED: rolling_trailing_stop_factor COMPLETED!")
        logger.info("=" * 80)
        logger.info(f"[TIMING] ✓ trailing_stop_factor completed in {factor_time:.2f}s")
        logger.info(f"          Output: {trailing_stop_factor.outputs}")
        logger.info("")

        # ====================================================================
        # PHASE 5: Validate Results
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 5] Validating results...")

        # Check outputs
        momentum_output = container.get_matrix(momentum_factor.outputs[0])
        breakout_output = container.get_matrix(breakout_factor.outputs[0])
        trailing_output = container.get_matrix(trailing_stop_factor.outputs[0])

        logger.info(f"Momentum output shape: {momentum_output.shape}")
        logger.info(f"Breakout output shape: {breakout_output.shape}")
        logger.info(f"Trailing stop output shape: {trailing_output.shape}")
        logger.info(f"Trailing stop signals: {trailing_output.sum().sum()} True values")

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
        logger.info(f"  Imports:           {timing_log['imports']:>8.2f}s")
        logger.info(f"  Strategy creation: {timing_log['strategy_creation']:>8.2f}s")
        logger.info(f"  Data loading:      {timing_log['data_loading']:>8.2f}s")
        logger.info(f"  momentum_factor:   {timing_log['momentum_factor']:>8.2f}s")
        logger.info(f"  breakout_factor:   {timing_log['breakout_factor']:>8.2f}s")
        logger.info(f"  trailing_stop:     {timing_log['trailing_stop_factor']:>8.2f}s  ⚠️")
        logger.info(f"  Validation:        {timing_log['validation']:>8.2f}s")
        logger.info("-" * 80)
        logger.info(f"  TOTAL:             {test_time:>8.2f}s")
        logger.info("")

        # Analysis
        logger.info("ANALYSIS:")
        logger.info("-" * 80)

        if test_time < 30:
            logger.info("⚠️  UNEXPECTED RESULT: All 3 factors completed in < 30s")
            logger.info("")
            logger.info("→ CONCLUSION: rolling_trailing_stop_factor is NOT the bottleneck!")
            logger.info("→ HYPOTHESIS REFUTED: The timeout must be elsewhere")
            logger.info("")
            logger.info("→ NEXT STEPS:")
            logger.info("  1. Re-examine to_pipeline() orchestration logic")
            logger.info("  2. Check for factor interaction bottlenecks")
            logger.info("  3. Investigate Strategy.execute() coordination overhead")
            logger.info("")
            logger.info("Per-factor timing:")
            if timing_log['momentum_factor'] > 5:
                logger.info(f"  - momentum_factor: {timing_log['momentum_factor']:.2f}s (SLOWER than Task 1.3)")
            if timing_log['breakout_factor'] > 15:
                logger.info(f"  - breakout_factor: {timing_log['breakout_factor']:.2f}s (SLOWER than Task 1.4)")
            if timing_log['trailing_stop_factor'] > 5:
                logger.info(f"  - trailing_stop_factor: {timing_log['trailing_stop_factor']:.2f}s (SLOW!)")

        elif test_time < 420:
            logger.info(f"⚠️  ANALYSIS: Execution time {test_time:.2f}s (30-420s range)")
            logger.info("")
            logger.info("→ CONCLUSION: System is slow but not timing out")
            logger.info("→ BOTTLENECK IDENTIFIED:")

            # Find slowest factor
            factor_times = {
                'momentum': timing_log['momentum_factor'],
                'breakout': timing_log['breakout_factor'],
                'trailing_stop': timing_log['trailing_stop_factor']
            }
            slowest_factor = max(factor_times.items(), key=lambda x: x[1])
            logger.info(f"     {slowest_factor[0]}: {slowest_factor[1]:.2f}s")
            logger.info("")
            logger.info("→ NEXT STEP: Optimize the slowest factor")

        else:
            logger.info("🚨 CRITICAL: Execution time > 420s (TIMEOUT)")
            logger.info("")
            logger.info("→ CONCLUSION: Timeout confirmed in this test")
            logger.info("→ BOTTLENECK: Unable to complete execution")
            logger.info("→ NEXT STEP: Review logs to see where timeout occurred")

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
        elif 'data_loading' not in timing_log:
            logger.error("→ FAILURE PHASE: Data loading")
        elif 'momentum_factor' not in timing_log:
            logger.error("→ FAILURE PHASE: momentum_factor execution")
        elif 'breakout_factor' not in timing_log:
            logger.error("→ FAILURE PHASE: breakout_factor execution")
        elif 'trailing_stop_factor' not in timing_log:
            logger.error("→ FAILURE PHASE: rolling_trailing_stop_factor execution")
            logger.error("")
            logger.error("🚨 CRITICAL: Error occurred in trailing_stop_factor!")
            logger.error("→ CONCLUSION: This confirms trailing_stop is problematic")
            logger.error("→ NEXT STEP: Analyze error and fix implementation")
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
    exit_code = run_trailing_stop_test()
    sys.exit(exit_code)
