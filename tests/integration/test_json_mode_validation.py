"""JSON Parameter Output Mode Validation Test
==========================================

Extended validation test for JSON Parameter Output mode.
Runs 20 iterations to validate success rate at scale.

Baseline (without JSON mode): 20.6% success rate
Target: >= 60% success rate with JSON mode

Usage:
    python tests/integration/test_json_mode_validation.py
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from unittest.mock import MagicMock, patch

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "artifacts" / "working" / "modules"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TOTAL_ITERATIONS = 20
TIMEOUT_PER_ITERATION = 120  # seconds
BASELINE_SUCCESS_RATE = 20.6  # % (without JSON mode)
TARGET_SUCCESS_RATE = 60.0  # % (with JSON mode)


def create_mock_backtest_result():
    """Create mock backtest report and metrics."""
    import random

    mock_report = MagicMock()

    # Randomize metrics slightly for variety
    sharpe = random.uniform(0.5, 2.5)
    annual_return = random.uniform(-0.1, 0.4)
    max_drawdown = random.uniform(-0.5, -0.1)

    mock_report.sharpe_ratio = sharpe
    mock_report.annual_return = annual_return
    mock_report.max_drawdown = max_drawdown

    metrics = {
        'sharpe_ratio': sharpe,
        'annual_return': annual_return,
        'max_drawdown': max_drawdown
    }

    return mock_report, metrics


def run_single_iteration(loop, iteration_num: int) -> Dict[str, Any]:
    """Run a single iteration and capture result.

    Args:
        loop: AutonomousLoop instance
        iteration_num: Iteration number

    Returns:
        Dict with success status and details
    """
    result = {
        'iteration': iteration_num,
        'success': False,
        'error': None,
        'duration_seconds': 0,
        'parameters': None
    }

    start_time = time.time()

    try:
        # Run template mode iteration with JSON mode
        report, metrics, parameters, validation_success = loop._run_template_mode_iteration(
            iteration_num=iteration_num,
            data=None  # Using mock data
        )

        result['success'] = True
        result['parameters'] = parameters
        result['metrics'] = metrics
        result['validation_success'] = validation_success

    except Exception as e:
        result['success'] = False
        result['error'] = str(e)
        logger.warning(f"Iteration {iteration_num} failed: {e}")

    result['duration_seconds'] = time.time() - start_time
    return result


def run_validation_test():
    """Run the full 20-iteration validation test."""
    from autonomous_loop import AutonomousLoop

    print("=" * 70)
    print("JSON Parameter Output Mode - Extended Validation Test")
    print("=" * 70)
    print(f"Total iterations: {TOTAL_ITERATIONS}")
    print(f"Baseline success rate (without JSON mode): {BASELINE_SUCCESS_RATE}%")
    print(f"Target success rate: >= {TARGET_SUCCESS_RATE}%")
    print("=" * 70)
    print()

    results: List[Dict[str, Any]] = []
    successes = 0
    failures = 0

    # Create AutonomousLoop with JSON mode enabled
    print("[Setup] Creating AutonomousLoop with use_json_mode=True...")

    # Mock the template's generate_strategy to avoid real backtest
    with patch('src.templates.momentum_template.MomentumTemplate.generate_strategy') as mock_gen:
        # Configure mock to return realistic results
        def mock_generate_strategy(params):
            return create_mock_backtest_result()

        mock_gen.side_effect = mock_generate_strategy

        loop = AutonomousLoop(
            model="gemini-2.5-flash",
            max_iterations=TOTAL_ITERATIONS,
            template_mode=True,
            template_name="Momentum",
            use_json_mode=True  # Enable JSON Parameter Output mode
        )

        print("[Setup] AutonomousLoop created successfully")
        print(f"[Setup] JSON mode enabled: {loop.use_json_mode}")
        print()

        # Run iterations
        test_start_time = time.time()

        for i in range(TOTAL_ITERATIONS):
            print(f"\n{'='*50}")
            print(f"ITERATION {i + 1}/{TOTAL_ITERATIONS}")
            print(f"{'='*50}")

            result = run_single_iteration(loop, i)
            results.append(result)

            if result['success']:
                successes += 1
                print(f"[RESULT] SUCCESS (took {result['duration_seconds']:.1f}s)")
                if result.get('parameters'):
                    print(f"         Parameters: {list(result['parameters'].keys())}")
            else:
                failures += 1
                print(f"[RESULT] FAILURE - {result['error'][:100]}...")

            # Print running success rate
            current_rate = (successes / (i + 1)) * 100
            print(f"[PROGRESS] Success rate so far: {successes}/{i + 1} = {current_rate:.1f}%")

        test_duration = time.time() - test_start_time

    # Final report
    print()
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    success_rate = (successes / TOTAL_ITERATIONS) * 100

    print(f"Total iterations:     {TOTAL_ITERATIONS}")
    print(f"Successes:            {successes}")
    print(f"Failures:             {failures}")
    print(f"Success rate:         {success_rate:.1f}%")
    print(f"Total duration:       {test_duration:.1f}s")
    print(f"Avg time/iteration:   {test_duration/TOTAL_ITERATIONS:.1f}s")
    print()

    print("COMPARISON TO BASELINE:")
    print(f"  Baseline (no JSON mode):  {BASELINE_SUCCESS_RATE}%")
    print(f"  JSON mode:                {success_rate:.1f}%")

    if success_rate > BASELINE_SUCCESS_RATE:
        improvement = success_rate - BASELINE_SUCCESS_RATE
        improvement_ratio = success_rate / BASELINE_SUCCESS_RATE
        print(f"  Improvement:              +{improvement:.1f} percentage points ({improvement_ratio:.1f}x)")
    else:
        print(f"  WARNING: JSON mode did not improve success rate!")

    print()

    # Target evaluation
    if success_rate >= TARGET_SUCCESS_RATE:
        print(f"TARGET ACHIEVED: {success_rate:.1f}% >= {TARGET_SUCCESS_RATE}%")
    else:
        print(f"TARGET NOT MET: {success_rate:.1f}% < {TARGET_SUCCESS_RATE}%")

    print()
    print("=" * 70)

    # Error analysis
    if failures > 0:
        print("\nERROR ANALYSIS:")
        error_counts: Dict[str, int] = {}
        for r in results:
            if not r['success'] and r['error']:
                # Extract first line of error for grouping
                error_key = r['error'].split('\n')[0][:80]
                error_counts[error_key] = error_counts.get(error_key, 0) + 1

        for error, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            print(f"  ({count}x) {error}")

    return {
        'total_iterations': TOTAL_ITERATIONS,
        'successes': successes,
        'failures': failures,
        'success_rate': success_rate,
        'baseline_rate': BASELINE_SUCCESS_RATE,
        'target_rate': TARGET_SUCCESS_RATE,
        'target_achieved': success_rate >= TARGET_SUCCESS_RATE,
        'duration_seconds': test_duration,
        'results': results
    }


if __name__ == "__main__":
    try:
        summary = run_validation_test()

        # Exit code based on target achievement
        if summary['target_achieved']:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
