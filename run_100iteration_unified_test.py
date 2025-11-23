#!/usr/bin/env python3
"""
100-Iteration UnifiedLoop Test Script

Dedicated test script for UnifiedLoop with Template Mode and JSON Parameter Output.
Runs 100 iterations with Learning Feedback enabled and generates comprehensive
statistical analysis.

This script is optimized for UnifiedLoop testing and comparison with AutonomousLoop.

Usage:
    python3 run_100iteration_unified_test.py [options]

Options:
    --no-template-mode      Disable Template Mode (enabled by default)
    --no-json-mode          Disable JSON Parameter Output (enabled by default)
    --template TEMPLATE     Template to use (default: Momentum)
    --resume CHECKPOINT     Path to checkpoint file for resuming test
    --iterations N          Number of iterations to run (default: 100)
    --help                  Show this help message

Examples:
    # Run with default settings (Template Mode + JSON Mode enabled)
    python3 run_100iteration_unified_test.py

    # Run with Template Mode only (no JSON Mode)
    python3 run_100iteration_unified_test.py --no-json-mode

    # Run with different template
    python3 run_100iteration_unified_test.py --template Factor

    # Resume from checkpoint
    python3 run_100iteration_unified_test.py --resume checkpoints/unified_checkpoint_iter_50.json
"""

import os
import sys
import logging
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add modules to path
sys.path.insert(0, os.path.dirname(__file__))

from tests.integration.unified_test_harness import UnifiedTestHarness


def setup_logging(template_mode: bool, use_json_mode: bool):
    """Configure comprehensive logging for UnifiedLoop test run.

    Creates logs directory and timestamp-based log file for test output.

    Args:
        template_mode: Whether Template Mode is enabled
        use_json_mode: Whether JSON Parameter Output mode is enabled

    Returns:
        tuple: (logger, log_file_path)
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    mode_suffix = "template" if template_mode else "standard"
    if template_mode and use_json_mode:
        mode_suffix = "template_json"
    log_file = os.path.join(log_dir, f"unified_100iteration_{mode_suffix}_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__), log_file


def save_results_json(results: dict, template_name: str):
    """Save test results to JSON file for analysis.

    Args:
        results: Test results dictionary from UnifiedTestHarness
        template_name: Name of template used
    """
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = results_dir / f"unified_100iter_{template_name.lower()}_{timestamp}.json"

    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger = logging.getLogger(__name__)
    logger.info(f"Results saved to: {results_file}")
    return str(results_file)


def print_unified_report(results: dict, logger: logging.Logger):
    """Print UnifiedLoop-specific test report.

    Args:
        results: Test results dictionary from UnifiedTestHarness
        logger: Logger instance for output
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("UNIFIEDLOOP 100-ITERATION TEST REPORT")
    logger.info("=" * 80)

    # Configuration summary
    logger.info("\nCONFIGURATION:")
    logger.info(f"  Loop type: UnifiedLoop")
    logger.info(f"  Template mode: {results.get('template_mode', False)}")
    logger.info(f"  JSON mode: {results.get('use_json_mode', False)}")
    logger.info(f"  Learning enabled: True")

    # Test summary
    logger.info("\nTEST SUMMARY:")
    logger.info(f"  Total iterations: {results.get('total_iterations', 0)}")
    logger.info(f"  Success rate: {results.get('success_rate', 0.0):.1f}%")
    logger.info(f"  Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
    logger.info(f"  Avg Sharpe: {results.get('avg_sharpe', 0.0):.4f}")
    logger.info(f"  Total duration: {results.get('total_duration_seconds', 0)/3600:.2f} hours")

    # Statistical report
    statistical_report = results.get('statistical_report', {})
    if statistical_report and not statistical_report.get('error'):
        logger.info("\nSTATISTICAL ANALYSIS:")
        logger.info(f"  Mean Sharpe: {statistical_report.get('mean_sharpe', 0.0):.4f}")
        logger.info(f"  Std Sharpe: {statistical_report.get('std_sharpe', 0.0):.4f}")
        logger.info(f"  Cohen's d: {statistical_report.get('cohens_d', 0.0):.3f} ({statistical_report.get('effect_size_interpretation', 'unknown')})")
        logger.info(f"  P-value: {statistical_report.get('p_value', 1.0):.4f} {'(significant)' if statistical_report.get('is_significant') else '(not significant)'}")
        logger.info(f"  Champion update frequency: {statistical_report.get('champion_update_frequency', 0.0):.1f}%")

        logger.info("\nPRODUCTION READINESS:")
        production_ready = statistical_report.get('production_ready', False)
        if production_ready:
            logger.info("  ✅ READY FOR PRODUCTION")
        else:
            logger.info("  ❌ NOT READY FOR PRODUCTION")

        for reason in statistical_report.get('readiness_reasoning', []):
            logger.info(f"    {reason}")
    else:
        logger.warning("  ⚠️  Statistical report not available")
        if statistical_report and 'error' in statistical_report:
            logger.warning(f"    Error: {statistical_report['error']}")

    logger.info("=" * 80)


def run_unified_test(
    template_mode: bool = True,
    use_json_mode: bool = True,
    template_name: str = "Momentum",
    target_iterations: int = 100,
    resume_from: str = None
):
    """Run UnifiedLoop 100-iteration test.

    Args:
        template_mode: Enable Template Mode
        use_json_mode: Enable JSON Parameter Output
        template_name: Template to use (e.g., "Momentum", "Factor")
        target_iterations: Number of iterations to run
        resume_from: Optional path to checkpoint file for resuming test

    Returns:
        dict: Test results with statistical report and metrics
    """
    logger, log_file = setup_logging(template_mode, use_json_mode)

    logger.info("=" * 80)
    logger.info("UNIFIEDLOOP 100-ITERATION TEST - START")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Model: gemini-2.5-flash")
    logger.info(f"Target iterations: {target_iterations}")
    logger.info(f"Template mode: {template_mode}")
    if template_mode:
        logger.info(f"  Template: {template_name}")
        logger.info(f"  JSON mode: {use_json_mode}")
    logger.info(f"Learning feedback: enabled")
    logger.info(f"Checkpoint interval: 10")
    logger.info(f"Log file: {log_file}")

    if resume_from:
        logger.info(f"Resume from checkpoint: {resume_from}")

    logger.info("")

    # Initialize UnifiedTestHarness
    logger.info("Initializing UnifiedTestHarness...")
    try:
        checkpoint_dir = f'checkpoints_unified_{template_name.lower()}'

        harness = UnifiedTestHarness(
            model='gemini-2.5-flash',
            target_iterations=target_iterations,
            checkpoint_interval=10,
            checkpoint_dir=checkpoint_dir,
            template_mode=template_mode,
            template_name=template_name,
            use_json_mode=use_json_mode,
            enable_learning=True
        )

        logger.info(f"✅ UnifiedTestHarness initialized (checkpoints: {checkpoint_dir})")
        if template_mode:
            logger.info(f"   Template Mode: enabled (template: {template_name})")
            logger.info(f"   JSON Mode: {'enabled' if use_json_mode else 'disabled'}")
            logger.info(f"   Learning Feedback: enabled")

    except Exception as e:
        logger.error(f"❌ Harness initialization failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file
        }

    # Run test
    logger.info("")
    logger.info("Starting UnifiedLoop test run...")
    logger.info("")

    start_time = datetime.now()

    try:
        results = harness.run_test(resume_from_checkpoint=resume_from)

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # Add metadata to results
        results['success'] = True
        results['log_file'] = log_file
        results['total_duration_seconds'] = total_duration
        results['template_mode'] = template_mode
        results['use_json_mode'] = use_json_mode
        results['template_name'] = template_name

        # Print UnifiedLoop-specific report
        print_unified_report(results, logger)

        # Save results to JSON
        results_file = save_results_json(results, template_name)
        results['results_file'] = results_file

        return results

    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file
        }


def main():
    """Main entry point for UnifiedLoop 100-iteration test.

    Exit codes:
        0: Test completed successfully and passed production readiness criteria
        1: Test failed or did not meet production readiness criteria
        2: Test interrupted by user (KeyboardInterrupt)
        3: Test failed with exception
    """
    try:
        # Parse command-line arguments
        parser = argparse.ArgumentParser(
            description="100-iteration UnifiedLoop test with Template Mode and JSON Parameter Output",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Run with default settings (Template Mode + JSON Mode enabled)
  python3 run_100iteration_unified_test.py

  # Run with Template Mode only (no JSON Mode)
  python3 run_100iteration_unified_test.py --no-json-mode

  # Run with different template
  python3 run_100iteration_unified_test.py --template Factor

  # Resume from checkpoint
  python3 run_100iteration_unified_test.py --resume checkpoints/unified_checkpoint_iter_50.json
            """
        )

        parser.add_argument(
            '--no-template-mode',
            action='store_true',
            help='Disable Template Mode (enabled by default)'
        )

        parser.add_argument(
            '--no-json-mode',
            action='store_true',
            help='Disable JSON Parameter Output (enabled by default)'
        )

        parser.add_argument(
            '--template',
            type=str,
            default='Momentum',
            help='Template to use (default: Momentum)'
        )

        parser.add_argument(
            '--iterations',
            type=int,
            default=100,
            help='Number of iterations to run (default: 100)'
        )

        parser.add_argument(
            '--resume',
            type=str,
            default=None,
            metavar='CHECKPOINT',
            help='Path to checkpoint file for resuming test'
        )

        args = parser.parse_args()

        # Determine modes
        template_mode = not args.no_template_mode
        use_json_mode = not args.no_json_mode

        # Validate
        if use_json_mode and not template_mode:
            parser.error("JSON mode requires Template Mode (cannot use --no-template-mode with JSON mode)")

        # Check resume checkpoint exists
        resume_from = args.resume
        if resume_from and not os.path.exists(resume_from):
            print(f"\n❌ Checkpoint file not found: {resume_from}")
            print("Starting fresh test run instead")
            resume_from = None

        # Print start message
        mode_desc = "UnifiedLoop"
        if template_mode:
            mode_desc += f" with Template Mode (template: {args.template})"
            if use_json_mode:
                mode_desc += " + JSON Mode"

        print(f"\n🚀 Starting 100-iteration test ({mode_desc})...\n")

        results = run_unified_test(
            template_mode=template_mode,
            use_json_mode=use_json_mode,
            template_name=args.template,
            target_iterations=args.iterations,
            resume_from=resume_from
        )

        if results.get('success'):
            statistical_report = results.get('statistical_report', {})
            production_ready = statistical_report.get('production_ready', False) if statistical_report else False

            print("\n✅ Test completed successfully")
            print(f"   Total iterations: {results.get('total_iterations', 0)}")
            print(f"   Success rate: {results.get('success_rate', 0.0):.1f}%")
            print(f"   Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
            print(f"   Avg Sharpe: {results.get('avg_sharpe', 0.0):.4f}")
            print(f"   Total duration: {results.get('total_duration_seconds', 0)/3600:.2f} hours")
            print(f"   Results saved to: {results.get('results_file', 'N/A')}")

            if production_ready:
                print("\n🎉 PRODUCTION READY: All criteria met")
                print(f"   Log file: {results['log_file']}")
                print(f"   Final checkpoint: {results.get('final_checkpoint', 'N/A')}")
                sys.exit(0)
            else:
                print("\n⚠️  NOT PRODUCTION READY: Some criteria not met")
                print("   Review statistical report for details")
                print(f"   Log file: {results['log_file']}")
                print(f"   Final checkpoint: {results.get('final_checkpoint', 'N/A')}")
                sys.exit(1)
        else:
            print(f"\n❌ Test failed: {results.get('error', 'Unknown error')}")
            print(f"   Log file: {results['log_file']}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        print("\nTo resume from last checkpoint:")
        print("  python run_100iteration_unified_test.py --resume checkpoints_unified_<TEMPLATE>/unified_checkpoint_iter_<N>.json")
        print("\nExamples:")
        print("  python run_100iteration_unified_test.py --resume checkpoints_unified_momentum/unified_checkpoint_iter_50.json")
        print("\nNote: Checkpoints are saved every 10 iterations")
        sys.exit(2)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main()
