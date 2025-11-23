#!/usr/bin/env python3
"""200-Iteration Stability Test for UnifiedLoop - Week 3.3

Long-term stability test to verify:
1. Memory leak detection (resource monitoring over time)
2. Champion update consistency
3. Checkpoint/Resume mechanism
4. Monitoring system stability
5. Docker sandbox reliability (if enabled)

This test runs UnifiedLoop for 200 iterations with:
- Template Mode + JSON Parameter Output
- All monitoring systems enabled
- Docker sandbox (optional, controlled by --use-docker)
- Checkpoint every 50 iterations
- Resource usage tracking

Usage:
    # Fresh start
    python run_200iteration_stability_test.py

    # Resume from checkpoint
    python run_200iteration_stability_test.py --resume checkpoints_stability/checkpoint_iter_100.json

    # Enable Docker sandbox
    python run_200iteration_stability_test.py --use-docker

    # Custom template
    python run_200iteration_stability_test.py --template Factor

Prerequisites:
    - FINLAB_API_TOKEN environment variable
    - finlab-sandbox:latest Docker image (if --use-docker)
    - ~8-12 hours execution time
    - ~2GB disk space for checkpoints

Output:
    - checkpoints_stability/: Checkpoint files
    - results/stability_200iter_YYYYMMDD_HHMMSS.json: Final results
    - logs/stability_test.log: Detailed logs
"""

import os
import sys
import json
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.learning.unified_loop import UnifiedLoop
from tests.integration.unified_test_harness import UnifiedTestHarness


def setup_logging(log_file: str = "logs/stability_test.log") -> None:
    """Setup logging for stability test.

    Args:
        log_file: Path to log file
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="200-Iteration Stability Test for UnifiedLoop (Week 3.3)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fresh start with Momentum template
  python run_200iteration_stability_test.py

  # Resume from checkpoint
  python run_200iteration_stability_test.py --resume checkpoints_stability/checkpoint_iter_100.json

  # Enable Docker sandbox
  python run_200iteration_stability_test.py --use-docker

  # Custom template and model
  python run_200iteration_stability_test.py --template Factor --model gemini-2.5-flash
        """
    )

    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Resume from checkpoint file (default: start fresh)'
    )

    parser.add_argument(
        '--template',
        type=str,
        default='Momentum',
        choices=['Momentum', 'Factor', 'MeanReversion', 'Breakout'],
        help='Template name (default: Momentum)'
    )

    parser.add_argument(
        '--use-docker',
        action='store_true',
        help='Enable Docker sandbox execution (default: disabled)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='gemini-2.5-flash',
        help='LLM model name (default: gemini-2.5-flash)'
    )

    parser.add_argument(
        '--checkpoint-interval',
        type=int,
        default=50,
        help='Checkpoint interval in iterations (default: 50)'
    )

    parser.add_argument(
        '--checkpoint-dir',
        type=str,
        default='checkpoints_stability',
        help='Checkpoint directory (default: checkpoints_stability)'
    )

    return parser.parse_args()


def run_stability_test(args: argparse.Namespace) -> Dict[str, Any]:
    """Run 200-iteration stability test.

    Args:
        args: Command line arguments

    Returns:
        Test results dictionary
    """
    logger = logging.getLogger(__name__)

    # Print test configuration
    print("\n" + "=" * 80)
    print("200-ITERATION STABILITY TEST - Week 3.3")
    print("=" * 80)
    print(f"Template: {args.template}")
    print(f"Model: {args.model}")
    print(f"Docker: {'Enabled' if args.use_docker else 'Disabled'}")
    print(f"Checkpoint interval: {args.checkpoint_interval} iterations")
    print(f"Checkpoint dir: {args.checkpoint_dir}")
    if args.resume:
        print(f"Resuming from: {args.resume}")
    print("=" * 80)
    print()

    # Check environment
    if 'FINLAB_API_TOKEN' not in os.environ:
        logger.error("FINLAB_API_TOKEN environment variable not set")
        print("\n❌ ERROR: FINLAB_API_TOKEN not found in environment")
        print("   Please set it before running stability test:")
        print("   export FINLAB_API_TOKEN='your-api-token'")
        sys.exit(1)

    # Prepare checkpoint directory
    checkpoint_dir = Path(args.checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Prepare results directory
    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)

    # Initialize test harness
    try:
        harness = UnifiedTestHarness(
            model=args.model,
            template_name=args.template,
            use_json_mode=True,
            enable_learning=True,
            enable_monitoring=True,
            use_docker=args.use_docker,
            checkpoint_dir=str(checkpoint_dir),
            checkpoint_interval=args.checkpoint_interval
        )

        logger.info("UnifiedTestHarness initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize UnifiedTestHarness: {e}", exc_info=True)
        print(f"\n❌ Initialization failed: {e}")
        sys.exit(1)

    # Run test
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    try:
        if args.resume:
            # Resume from checkpoint
            logger.info(f"Resuming from checkpoint: {args.resume}")
            result = harness.run_test(
                target_iterations=200,
                resume_from_checkpoint=args.resume
            )
        else:
            # Fresh start
            logger.info("Starting fresh 200-iteration test")
            result = harness.run_test(target_iterations=200)

        # Calculate duration
        duration_seconds = time.time() - start_time
        duration_hours = duration_seconds / 3600

        # Add test metadata
        result['test_metadata'] = {
            'test_type': 'stability_200iter',
            'template': args.template,
            'model': args.model,
            'docker_enabled': args.use_docker,
            'checkpoint_interval': args.checkpoint_interval,
            'resumed': args.resume is not None,
            'resume_checkpoint': args.resume,
            'duration_seconds': duration_seconds,
            'duration_hours': duration_hours,
            'timestamp': timestamp
        }

        # Save results
        result_file = results_dir / f"stability_200iter_{args.template.lower()}_{timestamp}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        logger.info(f"Results saved to: {result_file}")

        # Print summary
        print("\n" + "=" * 80)
        print("STABILITY TEST COMPLETE")
        print("=" * 80)
        print(f"Total iterations: {result.get('total_iterations', 0)}")
        print(f"Duration: {duration_hours:.2f} hours ({duration_seconds/60:.1f} minutes)")
        print(f"Success rate: {result.get('success_rate', 0):.1f}%")
        print(f"Best Sharpe: {result.get('best_sharpe', 0):.4f}")
        print(f"Champion updates: {result.get('champion_update_count', 0)}")

        # Memory leak check
        if 'resource_trend' in result:
            memory_trend = result['resource_trend'].get('memory_slope', 0)
            if abs(memory_trend) > 0.01:  # >1% per iteration
                print(f"\n⚠️  WARNING: Memory leak detected (trend: {memory_trend:+.4f}/iter)")
            else:
                print(f"\n✓ No memory leak detected (trend: {memory_trend:+.4f}/iter)")

        print(f"\nResults: {result_file}")
        print("=" * 80)

        return result

    except KeyboardInterrupt:
        logger.warning("Test interrupted by user (Ctrl+C)")
        print("\n\n⚠️  Test interrupted by user. Progress has been saved to checkpoints.")
        print(f"   Resume with: python run_200iteration_stability_test.py --resume {checkpoint_dir}/checkpoint_iter_*.json")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Stability test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point for stability test."""
    # Parse arguments
    args = parse_args()

    # Setup logging
    setup_logging()

    # Run stability test
    result = run_stability_test(args)

    # Success
    print("\n✅ Stability test completed successfully!")
    sys.exit(0)


if __name__ == '__main__':
    main()
