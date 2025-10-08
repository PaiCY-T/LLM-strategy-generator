#!/usr/bin/env python3
"""
10-Iteration Validation Run (Task 30)

Validates the learning system enhancement against success criteria:
1. Best Sharpe >1.2 (baseline: 0.97)
2. Success rate >60% (baseline: 33%)
3. Average Sharpe >0.5 (baseline: 0.33)
4. No regression >10% after establishing champion

Requires 3/4 criteria to pass for validation success.
"""

import os
import sys
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autonomous_loop import AutonomousLoop
from src.constants import METRIC_SHARPE


def setup_logging():
    """Configure logging for validation run."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


def load_finlab_data():
    """Load real Finlab data for validation.

    Returns:
        Finlab data object with Taiwan stock market data
    """
    try:
        import finlab
        from finlab import data

        # Login with API token
        api_token = os.getenv("FINLAB_API_TOKEN")
        if not api_token:
            raise ValueError("FINLAB_API_TOKEN environment variable not set")

        finlab.login(api_token)

        logger = logging.getLogger(__name__)
        logger.info("✅ Finlab data loaded successfully")

        return data

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to load Finlab data: {e}")
        raise


def run_validation_test(max_iterations: int = 10) -> bool:
    """Run 10-iteration validation against success criteria.

    Args:
        max_iterations: Number of iterations to run (default: 10)

    Returns:
        True if validation passes (3/4 criteria met), False otherwise
    """
    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("STARTING 10-ITERATION VALIDATION RUN (TASK 30)")
    logger.info("=" * 60)
    logger.info(f"Target: {max_iterations} iterations")
    logger.info(f"Model: google/gemini-2.5-flash")
    logger.info("")

    # Load Finlab data
    try:
        data = load_finlab_data()
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        logger.error("Validation cannot proceed without data")
        return False

    # Initialize autonomous loop
    loop = AutonomousLoop(
        model='google/gemini-2.5-flash',
        max_iterations=max_iterations
    )

    # Run iterations
    sharpes: List[float] = []
    success_count = 0

    for i in range(max_iterations):
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"ITERATION {i}/{max_iterations - 1}")
        logger.info("=" * 60)

        try:
            success, status = loop.run_iteration(i, data)

            if success:
                # Get metrics from history
                record = loop.history.get_record(i)
                if record and record.metrics:
                    sharpe = record.metrics.get(METRIC_SHARPE, 0.0)
                    sharpes.append(sharpe)

                    if sharpe > 0.5:
                        success_count += 1

                    logger.info(f"✅ Iteration {i} SUCCESS")
                    logger.info(f"   Sharpe: {sharpe:.4f}")

                    if loop.champion:
                        logger.info(f"   Champion: Iteration {loop.champion.iteration_num} (Sharpe {loop.champion.metrics[METRIC_SHARPE]:.4f})")
                else:
                    logger.warning(f"⚠️  Iteration {i} completed but no metrics recorded")
                    sharpes.append(0.0)
            else:
                logger.error(f"❌ Iteration {i} FAILED: {status}")
                sharpes.append(0.0)

        except Exception as e:
            logger.error(f"❌ Iteration {i} EXCEPTION: {e}", exc_info=True)
            sharpes.append(0.0)

    # Calculate validation metrics
    logger.info("")
    logger.info("=" * 60)
    logger.info("VALIDATION RESULTS")
    logger.info("=" * 60)

    best_sharpe = max(sharpes) if sharpes else 0.0
    success_rate = success_count / max_iterations if max_iterations > 0 else 0.0
    avg_sharpe = sum(sharpes) / len(sharpes) if sharpes else 0.0

    # Check regression
    regression_pct = 0.0
    if loop.champion and loop.champion.iteration_num < max_iterations - 1:
        champion_idx = loop.champion.iteration_num
        post_champion = sharpes[champion_idx + 1:]

        if post_champion:
            champion_sharpe = loop.champion.metrics[METRIC_SHARPE]
            worst_post_champion = min(post_champion)
            regression_pct = (worst_post_champion - champion_sharpe) / champion_sharpe if champion_sharpe != 0 else 0.0

    # Evaluate against success criteria
    criteria = {
        '1. Best Sharpe >1.2': {
            'actual': best_sharpe,
            'target': 1.2,
            'baseline': 0.97,
            'passed': best_sharpe > 1.2
        },
        '2. Success rate >60%': {
            'actual': success_rate,
            'target': 0.6,
            'baseline': 0.33,
            'passed': success_rate > 0.6
        },
        '3. Avg Sharpe >0.5': {
            'actual': avg_sharpe,
            'target': 0.5,
            'baseline': 0.33,
            'passed': avg_sharpe > 0.5
        },
        '4. No regression >10%': {
            'actual': regression_pct,
            'target': -0.10,
            'baseline': 'N/A',
            'passed': regression_pct > -0.10
        }
    }

    passed_count = sum(1 for c in criteria.values() if c['passed'])

    logger.info("")
    logger.info(f"Iterations completed: {max_iterations}")
    logger.info(f"Successful iterations (Sharpe >0.5): {success_count}")
    logger.info("")

    logger.info("SUCCESS CRITERIA (need 3/4 to pass):")
    logger.info("")

    for criterion, results in criteria.items():
        status = "✅ PASS" if results['passed'] else "❌ FAIL"
        actual = results['actual']
        target = results['target']
        baseline = results['baseline']

        if isinstance(actual, float):
            if criterion == '2. Success rate >60%':
                logger.info(f"{status} {criterion}")
                logger.info(f"     Actual: {actual:.1%} | Target: {target:.1%} | Baseline: {baseline:.1%}")
            else:
                logger.info(f"{status} {criterion}")
                logger.info(f"     Actual: {actual:.4f} | Target: {target} | Baseline: {baseline}")
        else:
            logger.info(f"{status} {criterion}")
            logger.info(f"     Actual: {actual} | Target: {target} | Baseline: {baseline}")

    logger.info("")
    logger.info(f"CRITERIA PASSED: {passed_count}/4")
    logger.info("")

    # Final verdict
    if passed_count >= 3:
        logger.info("=" * 60)
        logger.info("🎉 VALIDATION SUCCESSFUL")
        logger.info("=" * 60)
        logger.info("Learning system enhancement meets success criteria!")
        logger.info("System is ready for production deployment.")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Monitor system over 20+ iterations for stability")
        logger.info("2. Collect failure patterns for further analysis")
        logger.info("3. Plan Phase 3: Advanced Attribution (AST migration)")
        logger.info("4. Plan Phase 4: Knowledge Graph Integration (Graphiti)")
        return True
    elif passed_count >= 2:
        logger.warning("=" * 60)
        logger.warning("⚠️  VALIDATION PARTIALLY SUCCESSFUL")
        logger.warning("=" * 60)
        logger.warning(f"Passed {passed_count}/4 criteria (need 3/4)")
        logger.warning("")
        logger.warning("Recommended actions:")
        logger.warning("1. Analyze which criteria failed")
        logger.warning("2. Tune thresholds (champion update, probation period)")
        logger.warning("3. Review prompt effectiveness")
        logger.warning("4. Re-run validation")
        return False
    else:
        logger.error("=" * 60)
        logger.error("❌ VALIDATION FAILED")
        logger.error("=" * 60)
        logger.error(f"Passed only {passed_count}/4 criteria (need 3/4)")
        logger.error("")
        logger.error("Required actions:")
        logger.error("1. Review fundamental assumptions")
        logger.error("2. Analyze failure patterns")
        logger.error("3. Consider alternative approaches")
        logger.error("4. Consult design review")
        return False


def main():
    """Main entry point for validation script."""
    try:
        validation_passed = run_validation_test(max_iterations=10)
        sys.exit(0 if validation_passed else 1)

    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.warning("\n\nValidation interrupted by user")
        sys.exit(2)

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Validation failed with exception: {e}", exc_info=True)
        sys.exit(3)


if __name__ == '__main__':
    main()
