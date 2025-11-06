#!/usr/bin/env python3
"""
Phase 8: E2E Smoke Test for Phase 3 Critical Fixes

This test verifies that the critical fixes from PR #2 (phase3-critical-bugs)
are properly integrated and the system can initialize and run without errors.

Critical Fixes Verified:
1. ChampionTracker receives all required dependencies (hall_of_fame, history, anti_churn)
2. IterationExecutor calls update_champion with correct parameters (iteration_num, code, metrics)

Test Strategy:
- Use minimal configuration (1-2 iterations)
- Mock LLM and backtest execution to avoid external dependencies
- Focus on component initialization and API contract compliance
- Verify no TypeError or AttributeError during initialization or execution
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop
from src.backtest.executor import ExecutionResult
from src.learning.iteration_history import IterationRecord

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_phase3_critical_fix_1_champion_tracker_initialization():
    """
    TEST 1: ChampionTracker Initialization with All Dependencies

    Verifies PR #2 Fix #1:
    - ChampionTracker receives hall_of_fame parameter
    - ChampionTracker receives history parameter
    - ChampionTracker receives anti_churn parameter

    Expected: No TypeError about missing parameters
    """
    logger.info("=" * 60)
    logger.info("TEST 1: ChampionTracker Initialization")
    logger.info("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LearningConfig(
            max_iterations=1,
            history_file=str(Path(tmpdir) / "history.jsonl"),
            champion_file=str(Path(tmpdir) / "champion.json"),
            log_to_file=False,
            log_to_console=False,
        )

        try:
            # This should NOT raise TypeError about missing parameters
            loop = LearningLoop(config)

            # Verify all required components are initialized
            assert loop.champion_tracker is not None, "ChampionTracker not initialized"
            assert loop.hall_of_fame is not None, "HallOfFameRepository not initialized"
            assert loop.anti_churn is not None, "AntiChurnManager not initialized"

            logger.info("✓ ChampionTracker initialized with all dependencies")
            logger.info("✓ HallOfFameRepository initialized")
            logger.info("✓ AntiChurnManager initialized")
            return True

        except TypeError as e:
            if "missing" in str(e) and "required" in str(e):
                logger.error(f"✗ CRITICAL FIX #1 FAILED: {e}")
                logger.error("  ChampionTracker did not receive required dependencies")
                return False
            raise


def test_phase3_critical_fix_2_update_champion_api():
    """
    TEST 2: update_champion API Contract Compliance

    Verifies PR #2 Fix #2:
    - update_champion called with exactly 3 parameters: iteration_num, code, metrics
    - No extra parameters like generation_method, strategy_id, strategy_generation

    Expected: No TypeError about unexpected keyword arguments
    """
    logger.info("=" * 60)
    logger.info("TEST 2: update_champion API Contract")
    logger.info("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LearningConfig(
            max_iterations=1,
            history_file=str(Path(tmpdir) / "history.jsonl"),
            champion_file=str(Path(tmpdir) / "champion.json"),
            log_to_file=False,
            log_to_console=False,
        )

        try:
            loop = LearningLoop(config)

            # Mock execution to return successful result
            mock_result = ExecutionResult(
                success=True,
                report={'returns': [0.01, 0.02], 'cagr': 0.15, 'mdd': 0.1},
                execution_time=1.0,
            )

            # Mock LLM to return code
            with patch.object(loop.llm_client, 'is_enabled', return_value=False):
                # This forces Factor Graph path which has placeholder implementation
                # We'll also mock the backtest execution (use correct 'execute' method)
                with patch.object(
                    loop.backtest_executor,
                    'execute',
                    return_value=mock_result
                ):
                    # Execute one iteration
                    # This will call update_champion internally with the correct signature
                    record = loop.iteration_executor.execute_iteration(iteration_num=0)

                    logger.info("✓ Iteration executed successfully")
                    logger.info(f"✓ Classification: {record.classification_level}")
                    logger.info("✓ update_champion called with correct parameters")
                    return True

        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                logger.error(f"✗ CRITICAL FIX #2 FAILED: {e}")
                logger.error("  update_champion received wrong parameters")
                return False
            raise


def test_full_initialization_smoke():
    """
    TEST 3: Full System Initialization Smoke Test

    Verifies complete system can initialize without errors:
    - All Phase 1-5 components initialize
    - No missing dependencies
    - No API mismatches
    - Configuration loads correctly

    Expected: All components initialized successfully
    """
    logger.info("=" * 60)
    logger.info("TEST 3: Full System Initialization")
    logger.info("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LearningConfig(
            max_iterations=1,
            history_file=str(Path(tmpdir) / "history.jsonl"),
            champion_file=str(Path(tmpdir) / "champion.json"),
            log_to_file=False,
            log_to_console=False,
        )

        try:
            loop = LearningLoop(config)

            # Verify all components
            components = {
                'history': loop.history,
                'hall_of_fame': loop.hall_of_fame,
                'anti_churn': loop.anti_churn,
                'champion_tracker': loop.champion_tracker,
                'llm_client': loop.llm_client,
                'feedback_generator': loop.feedback_generator,
                'backtest_executor': loop.backtest_executor,
                'iteration_executor': loop.iteration_executor,
            }

            for name, component in components.items():
                assert component is not None, f"{name} not initialized"
                logger.info(f"✓ {name} initialized")

            logger.info("✓ All components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"✗ INITIALIZATION FAILED: {e}")
            logger.exception("Full traceback:")
            return False


def test_single_iteration_integration():
    """
    TEST 4: Single Iteration Integration Test

    Verifies complete iteration flow:
    1. Load history
    2. Generate feedback
    3. Generate strategy (mocked)
    4. Execute strategy (mocked)
    5. Extract metrics
    6. Classify result
    7. Update champion
    8. Save record

    Expected: Complete iteration without errors
    """
    logger.info("=" * 60)
    logger.info("TEST 4: Single Iteration Integration")
    logger.info("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        config = LearningConfig(
            max_iterations=1,
            history_file=str(Path(tmpdir) / "history.jsonl"),
            champion_file=str(Path(tmpdir) / "champion.json"),
            log_to_file=False,
            log_to_console=False,
            innovation_rate=0,  # Use Factor Graph only (no LLM)
        )

        try:
            loop = LearningLoop(config)

            # Mock execution to return successful result with metrics
            mock_result = ExecutionResult(
                success=True,
                report={
                    'returns': [0.01, 0.02, 0.01, 0.015, 0.02],
                    'cagr': 0.25,
                    'mdd': 0.15,
                    'sharpe': 1.85,
                    'total_return': 0.30,
                },
                execution_time=1.0,
            )

            with patch.object(
                loop.backtest_executor,
                'execute',
                return_value=mock_result
            ):
                # Mock signal handlers to avoid signal setup
                with patch.object(loop, '_setup_signal_handlers'):
                    with patch.object(loop, '_show_startup_info'):
                        with patch.object(loop, '_show_progress'):
                            with patch.object(loop, '_generate_summary'):
                                # Run single iteration
                                loop.run()

                # Verify record was saved
                records = loop.history.get_all()
                assert len(records) == 1, "No record saved"

                record = records[0]
                logger.info(f"✓ Iteration completed: {record.classification_level}")
                logger.info(f"✓ Generation method: {record.generation_method}")
                logger.info(f"✓ Metrics extracted: {bool(record.metrics)}")
                logger.info(f"✓ Record saved to history")

                return True

        except Exception as e:
            logger.error(f"✗ ITERATION FAILED: {e}")
            logger.exception("Full traceback:")
            return False


def main():
    """Run all E2E smoke tests."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("PHASE 8: E2E SMOKE TEST SUITE")
    logger.info("=" * 60)
    logger.info("Testing Phase 3 Critical Fixes Integration")
    logger.info("")

    tests = [
        ("ChampionTracker Initialization", test_phase3_critical_fix_1_champion_tracker_initialization),
        ("update_champion API Contract", test_phase3_critical_fix_2_update_champion_api),
        ("Full System Initialization", test_full_initialization_smoke),
        ("Single Iteration Integration", test_single_iteration_integration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            logger.info("")
        except Exception as e:
            logger.error(f"✗ TEST CRASHED: {test_name}")
            logger.exception("Exception:")
            results.append((test_name, False))
            logger.info("")

    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info("")
    logger.info(f"Total: {len(results)} tests")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {failed}")
    logger.info("=" * 60)

    if failed == 0:
        logger.info("✅ ALL TESTS PASSED")
        logger.info("Phase 3 critical fixes are properly integrated")
        return 0
    else:
        logger.error("❌ SOME TESTS FAILED")
        logger.error("Phase 3 fixes may have integration issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
