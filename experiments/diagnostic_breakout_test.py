"""
Breakout Factor Diagnostic Test - Task 1.4
===========================================

Test single breakout_factor in isolation to isolate timeout cause.

Test Configuration:
- Single factor: breakout_factor only (turtle entry signal)
- Data period: Same as main test (20 iterations config)
- Timeout: 420s (same as main test)
- Timing: Detailed logs at each phase

Expected Results:
- Success (<30s): breakout_factor is healthy → timeout is in rolling_trailing_stop_factor
- Timeout (>420s): breakout_factor is the culprit → investigate breakout implementation
- Error: Fix error and re-evaluate

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


def run_breakout_test():
    """Execute diagnostic test with single breakout factor."""

    logger.info("=" * 80)
    logger.info("DIAGNOSTIC BREAKOUT TEST - Task 1.4")
    logger.info("=" * 80)
    logger.info(f"Test Start: {datetime.now()}")
    logger.info(f"Configuration: Single breakout_factor (entry_window=20)")
    logger.info(f"Timeout: 420s")
    logger.info("")

    test_start = time.time()

    try:
        # ====================================================================
        # PHASE 1: Import Dependencies
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 1] Importing dependencies...")

        from finlab import data
        from src.factor_graph.strategy import Strategy
        from src.factor_library.turtle_factors import create_breakout_factor

        phase_time = time.time() - phase_start
        logger.info(f"[PHASE 1] ✓ Imports complete in {phase_time:.2f}s")
        logger.info("")

        # ====================================================================
        # PHASE 2: Create Strategy with Breakout Factor
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 2] Creating strategy with single breakout factor...")

        # Create strategy
        strategy = Strategy(id="breakout_test", generation=0)

        # Create and add only breakout factor (turtle entry signal)
        breakout_factor = create_breakout_factor(entry_window=20)
        strategy.add_factor(breakout_factor)

        logger.info(f"Strategy ID: {strategy.id}")
        logger.info(f"Factors: {list(strategy.factors.keys())}")
        logger.info(f"Factor count: {len(strategy.factors)}")
        logger.info(f"Factor details: {breakout_factor.name} (category: {breakout_factor.category})")

        phase_time = time.time() - phase_start
        logger.info(f"[PHASE 2] ✓ Strategy created in {phase_time:.2f}s")
        logger.info("")

        # ====================================================================
        # PHASE 3: Execute Strategy Pipeline (SUSPECT PHASE)
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 3] Executing strategy pipeline...")
        logger.info("NOTE: Testing if breakout_factor is the timeout culprit")
        logger.info("Expected: <30s if healthy, >420s if problematic")

        # Execute with skip_validation to isolate execution
        position = strategy.to_pipeline(data, skip_validation=True)

        phase_time = time.time() - phase_start
        logger.info(f"[PHASE 3] ✓ Pipeline executed in {phase_time:.2f}s")
        logger.info(f"Position matrix shape: {position.shape}")
        logger.info("")

        # ====================================================================
        # PHASE 4: Validate Results
        # ====================================================================
        phase_start = time.time()
        logger.info("[PHASE 4] Validating results...")

        logger.info(f"Position matrix type: {type(position)}")
        logger.info(f"Position matrix shape: {position.shape}")
        logger.info(f"Position matrix memory: {position.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        logger.info(f"Non-null positions: {position.notna().sum().sum()}")

        phase_time = time.time() - phase_start
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

        # Analysis
        if test_time < 30:
            logger.info("⚡ ANALYSIS: Execution time < 30s")
            logger.info("→ CONCLUSION: breakout_factor works normally")
            logger.info("→ NEXT STEP: Task 1.5 - Test rolling_trailing_stop_factor")
            logger.info("→ HYPOTHESIS: Timeout is in rolling_trailing_stop_factor (newest factor)")
        elif test_time < 420:
            logger.info("⚠️  ANALYSIS: Execution time 30-420s (slower than expected)")
            logger.info(f"→ CONCLUSION: breakout_factor execution took {test_time:.2f}s")
            logger.info("→ NEXT STEP: Investigate breakout_factor implementation")
            logger.info("→ HYPOTHESIS: Rolling max/min operations in breakout may be slow")
        else:
            logger.info("🚨 ANALYSIS: Execution time > 420s (TIMEOUT)")
            logger.info("→ CONCLUSION: breakout_factor is the timeout culprit")
            logger.info("→ NEXT STEP: Phase 2 Path B - Fix breakout_factor implementation")
            logger.info("→ HYPOTHESIS: Inefficient rolling window operations in _breakout_logic")

        return 0

    except Exception as e:
        test_time = time.time() - test_start
        logger.error("=" * 80)
        logger.error("TEST RESULT: ERROR ✗")
        logger.error("=" * 80)
        logger.error(f"Error after {test_time:.2f}s: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error("")
        logger.error("→ NEXT STEP: Fix error and re-run test")

        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())

        return 1


if __name__ == "__main__":
    exit_code = run_breakout_test()
    sys.exit(exit_code)
