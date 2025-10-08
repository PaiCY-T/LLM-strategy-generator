#!/usr/bin/env python3
"""
Extended Validation Run - 30 Iterations

Runs extended validation to:
1. Verify long-term system stability
2. Collect more failure pattern data (8-12 patterns expected)
3. Validate P0 preservation fix under extended usage
4. Monitor champion progression over longer timeframe

This extends the Task 30 validation from 10 to 30 iterations to meet
the post-MVP monitoring requirement stated in STATUS.md.
"""

import os
import sys
import logging
from typing import List
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autonomous_loop import AutonomousLoop
from src.constants import METRIC_SHARPE
from run_10iteration_validation import setup_logging, load_finlab_data


def run_extended_validation(max_iterations: int = 30, model: str = 'gemini-2.5-flash') -> bool:
    """Run extended validation with custom model.

    Args:
        max_iterations: Number of iterations to run (default: 30)
        model: Model to use for generation (default: gemini-2.5-flash)

    Returns:
        True if validation passes (3/4 criteria), False otherwise
    """
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info(f"STARTING EXTENDED VALIDATION - {max_iterations} ITERATIONS")
    logger.info("=" * 60)
    logger.info(f"Model: {model}")
    logger.info("")

    # Load Finlab data
    try:
        data = load_finlab_data()
    except Exception as e:
        logger.error(f"Data loading failed: {e}")
        return False

    # Initialize autonomous loop with custom model
    loop = AutonomousLoop(
        model=model,
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

    # Calculate metrics
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

    # Report results
    logger.info("")
    logger.info("=" * 60)
    logger.info("EXTENDED VALIDATION RESULTS")
    logger.info("=" * 60)
    logger.info(f"Iterations completed: {max_iterations}")
    logger.info(f"Successful iterations: {success_count} ({success_rate:.1%})")
    logger.info(f"Best Sharpe: {best_sharpe:.4f}")
    logger.info(f"Avg Sharpe: {avg_sharpe:.4f}")
    logger.info(f"Worst regression: {regression_pct:.1%}")

    # Check criteria
    criteria_passed = 0
    if best_sharpe > 1.2:
        criteria_passed += 1
        logger.info("✅ Best Sharpe >1.2: PASS")
    else:
        logger.info(f"❌ Best Sharpe >1.2: FAIL ({best_sharpe:.4f})")

    if success_rate > 0.6:
        criteria_passed += 1
        logger.info("✅ Success rate >60%: PASS")
    else:
        logger.info(f"❌ Success rate >60%: FAIL ({success_rate:.1%})")

    if avg_sharpe > 0.5:
        criteria_passed += 1
        logger.info("✅ Avg Sharpe >0.5: PASS")
    else:
        logger.info(f"❌ Avg Sharpe >0.5: FAIL ({avg_sharpe:.4f})")

    if regression_pct > -0.10:
        criteria_passed += 1
        logger.info("✅ No regression >10%: PASS")
    else:
        logger.info(f"❌ No regression >10%: FAIL ({regression_pct:.1%})")

    logger.info("")
    logger.info(f"CRITERIA PASSED: {criteria_passed}/4")

    return criteria_passed >= 3


def main():
    """Run extended 30-iteration validation."""
    # Set Gemini API key
    os.environ['GOOGLE_API_KEY'] = 'AIzaSyDohXMsnWRJXwiZqUo7xkw4So1vYQCcmu8'

    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("EXTENDED VALIDATION - 30 ITERATIONS")
    logger.info("=" * 60)
    logger.info("Model: gemini-2.5-flash (via Google AI)")
    logger.info("Purpose: Long-term stability monitoring + failure pattern collection")
    logger.info("Expected duration: ~6 minutes (30 iterations × ~12 seconds)")
    logger.info("")

    try:
        # Run 30-iteration validation with Gemini
        validation_passed = run_extended_validation(
            max_iterations=30,
            model='gemini-2.5-flash'
        )

        # Additional analysis for extended run
        logger.info("")
        logger.info("=" * 60)
        logger.info("EXTENDED VALIDATION ANALYSIS")
        logger.info("=" * 60)

        # Check failure_patterns.json for collected patterns
        import json
        if os.path.exists("failure_patterns.json"):
            with open("failure_patterns.json", 'r') as f:
                patterns = json.load(f)
                logger.info(f"Total failure patterns collected: {len(patterns)}")
                logger.info("")
                logger.info("Pattern breakdown:")

                # Group by parameter
                param_counts = {}
                for p in patterns:
                    param = p.get('parameter', 'unknown')
                    param_counts[param] = param_counts.get(param, 0) + 1

                for param, count in sorted(param_counts.items(), key=lambda x: -x[1]):
                    logger.info(f"  {param}: {count} patterns")

        sys.exit(0 if validation_passed else 1)

    except KeyboardInterrupt:
        logger.warning("\n\nExtended validation interrupted by user")
        sys.exit(2)

    except Exception as e:
        logger.error(f"Extended validation failed: {e}", exc_info=True)
        sys.exit(3)


if __name__ == '__main__':
    main()
