#!/usr/bin/env python3
"""
100-Iteration Production Validation Test Run

Runs 100 iterations of the autonomous learning loop using ExtendedTestHarness
with automatic checkpointing, retry logic, and comprehensive statistical analysis.

This is a balanced validation run to verify long-term stability of Phase 1 + Phase 2
implementations while avoiding memory constraints.

Usage:
    python3 run_100iteration_test.py [resume_checkpoint]

Arguments:
    resume_checkpoint: Optional path to checkpoint file for resuming test
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'artifacts', 'working', 'modules'))
sys.path.insert(0, os.path.dirname(__file__))

from tests.integration.extended_test_harness import ExtendedTestHarness


def setup_logging():
    """Configure comprehensive logging for test run.

    Creates logs directory and timestamp-based log file for test output.
    Configures both file and console logging handlers.

    Returns:
        tuple: (logger, log_file_path)
    """
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"100iteration_test_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__), log_file


def validate_phase2_features(logger: logging.Logger) -> dict:
    """Validate that all Phase 2 stability features are available.

    Checks:
    - Story 1: VarianceMonitor available
    - Story 2: PreservationValidator available
    - Story 4: AntiChurnManager available
    - Story 9: RollbackManager available

    Returns:
        dict: {
            'all_available': bool,
            'story1_available': bool,
            'story2_available': bool,
            'story4_available': bool,
            'story9_available': bool,
            'missing_features': list
        }
    """
    status = {
        'all_available': True,
        'story1_available': False,
        'story2_available': False,
        'story4_available': False,
        'story9_available': False,
        'missing_features': []
    }

    # Check Story 1: VarianceMonitor
    try:
        from src.monitoring.variance_monitor import VarianceMonitor
        status['story1_available'] = True
        logger.info("  ✅ Story 1: VarianceMonitor available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('VarianceMonitor')
        logger.warning(f"  ❌ Story 1: VarianceMonitor not available - {e}")

    # Check Story 2: PreservationValidator
    try:
        from src.validation.preservation_validator import PreservationValidator
        status['story2_available'] = True
        logger.info("  ✅ Story 2: PreservationValidator available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('PreservationValidator')
        logger.warning(f"  ❌ Story 2: PreservationValidator not available - {e}")

    # Check Story 4: AntiChurnManager
    try:
        from src.config.anti_churn_manager import AntiChurnManager
        status['story4_available'] = True
        logger.info("  ✅ Story 4: AntiChurnManager available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('AntiChurnManager')
        logger.warning(f"  ❌ Story 4: AntiChurnManager not available - {e}")

    # Check Story 9: RollbackManager
    try:
        from src.recovery.rollback_manager import RollbackManager
        status['story9_available'] = True
        logger.info("  ✅ Story 9: RollbackManager available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('RollbackManager')
        logger.warning(f"  ❌ Story 9: RollbackManager not available - {e}")

    return status


def load_finlab_data():
    """Load real Finlab data for testing.

    Authenticates with Finlab API using environment variable token
    and returns data object for strategy execution.

    Returns:
        Finlab data object with Taiwan stock market data

    Raises:
        ValueError: If FINLAB_API_TOKEN environment variable not set
        Exception: If Finlab data loading fails
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


def extract_phase1_phase2_metrics(results: dict) -> dict:
    """Extract Phase 1 + Phase 2 metrics from test results.

    Extracts:
    - Phase 1: Data consistency, config tracking
    - Phase 2: Variance monitoring, preservation, anti-churn, rollback

    Args:
        results: Test results dictionary from ExtendedTestHarness

    Returns:
        dict with Phase 1 + Phase 2 metrics
    """
    metrics = {
        # Phase 1 metrics
        'data_checks': 0,
        'data_changes': 0,
        'config_snapshots': 0,
        'config_changes': 0,
        # Phase 2 metrics
        'variance_alerts': 0,
        'preservation_checks': 0,
        'preservation_failures': 0,
        'champion_updates': 0,
        'anti_churn_activations': 0,
    }

    # Check if iteration_history file exists
    history_file = Path('iteration_history.json')
    if not history_file.exists():
        return metrics

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)

        records = history_data.get('records', [])

        # Count Phase 1 data checksums
        prev_checksum = None
        for record in records:
            if record.get('data_checksum'):
                metrics['data_checks'] += 1
                if prev_checksum and prev_checksum != record['data_checksum']:
                    metrics['data_changes'] += 1
                prev_checksum = record['data_checksum']

        # Count Phase 1 config snapshots
        for record in records:
            if record.get('config_snapshot'):
                metrics['config_snapshots'] += 1

        # Count Phase 2 variance alerts (would need to be tracked in iteration_history)
        # Count Phase 2 preservation checks
        # Count Phase 2 champion updates
        champion_history = history_data.get('champion_history', [])
        metrics['champion_updates'] = len(champion_history)

    except Exception as e:
        logging.getLogger(__name__).warning(f"Error extracting metrics: {e}")

    return metrics


def print_colored_report(report: dict, logger: logging.Logger, metrics: dict = None):
    """Print production readiness report with colored formatting.

    Outputs comprehensive statistical report with color coding for
    production readiness status and key metrics.

    Args:
        report: Statistical report dictionary from ExtendedTestHarness
        logger: Logger instance for output
        metrics: Optional Phase 1+2 metrics dictionary
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("100-ITERATION TEST - PRODUCTION READINESS REPORT")
    logger.info("=" * 80)

    # Production readiness status
    production_ready = report.get('production_ready', False)
    if production_ready:
        logger.info("✅ STATUS: READY FOR PRODUCTION")
    else:
        logger.info("❌ STATUS: NOT READY FOR PRODUCTION")

    logger.info("")
    logger.info("STATISTICAL METRICS:")
    logger.info(f"  Sample size: {report.get('sample_size', 0)}")
    logger.info(f"  Mean Sharpe: {report.get('mean_sharpe', 0.0):.4f}")
    logger.info(f"  Std Sharpe: {report.get('std_sharpe', 0.0):.4f}")
    logger.info(f"  Range: [{report.get('min_sharpe', 0.0):.4f}, {report.get('max_sharpe', 0.0):.4f}]")

    logger.info("")
    logger.info("LEARNING EFFECT ANALYSIS:")
    logger.info(f"  Cohen's d: {report.get('cohens_d', 0.0):.3f} ({report.get('effect_size_interpretation', 'unknown')})")
    logger.info(f"  P-value: {report.get('p_value', 1.0):.4f} {'(significant)' if report.get('is_significant') else '(not significant)'}")

    ci_lower, ci_upper = report.get('confidence_interval_95', (0.0, 0.0))
    logger.info(f"  95% CI: [{ci_lower:.3f}, {ci_upper:.3f}]")

    logger.info("")
    logger.info("CONVERGENCE ANALYSIS:")
    logger.info(f"  Rolling variance: {report.get('rolling_variance', 0.0):.3f}")
    logger.info(f"  Convergence achieved (σ<0.5): {report.get('convergence_achieved', False)}")

    logger.info("")
    logger.info("ADDITIONAL METRICS:")
    logger.info(f"  Champion update frequency: {report.get('champion_update_frequency', 0.0):.1f}%")
    logger.info(f"  Avg duration per iteration: {report.get('avg_duration_per_iteration', 0.0):.2f}s")
    logger.info(f"  Total test duration: {report.get('total_duration', 0.0)/3600:.2f} hours")

    # Phase 1 + Phase 2 stability features
    if metrics:
        logger.info("")
        logger.info("PHASE 1 + PHASE 2 STABILITY FEATURES:")
        logger.info(f"  Data integrity checks: {metrics.get('data_checks', 0)}")
        logger.info(f"  Config snapshots: {metrics.get('config_snapshots', 0)}")
        logger.info(f"  Champion updates: {metrics.get('champion_updates', 0)}")
        if metrics.get('champion_updates', 0) > 0:
            update_freq = (metrics['champion_updates'] / report.get('sample_size', 1)) * 100
            logger.info(f"  Update frequency: {update_freq:.1f}% (target: 10-20%)")

    logger.info("")
    logger.info("READINESS REASONING:")
    for reason in report.get('readiness_reasoning', []):
        logger.info(f"  {reason}")

    logger.info("=" * 80)


def run_100iteration_test(resume_from: str = None):
    """Run 100-iteration test with ExtendedTestHarness.

    Main test orchestration function that:
    - Sets up logging
    - Loads Finlab data
    - Initializes ExtendedTestHarness
    - Executes 100-iteration test run
    - Generates statistical report
    - Prints production readiness assessment

    Args:
        resume_from: Optional path to checkpoint file for resuming test

    Returns:
        dict: Test results with statistical report and metrics

    Raises:
        Exception: If critical test failure occurs
    """
    logger, log_file = setup_logging()

    logger.info("=" * 80)
    logger.info("100-ITERATION PRODUCTION TEST - START")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Model: google/gemini-2.5-flash")
    logger.info(f"Target iterations: 100")
    logger.info(f"Checkpoint interval: 10")
    logger.info(f"Generation mode: TEMPLATE (Momentum golden template)")
    logger.info(f"JSON mode: ENABLED (Phase 1.1 JSON Parameter Output)")
    logger.info(f"Log file: {log_file}")

    if resume_from:
        logger.info(f"Resume from checkpoint: {resume_from}")

    logger.info("")

    # Validate Phase 2 stability features
    logger.info("Validating Phase 2 stability features...")
    phase2_status = validate_phase2_features(logger)

    if phase2_status['all_available']:
        logger.info("✅ All Phase 2 features available")
    else:
        logger.warning(f"⚠️  Missing features: {phase2_status['missing_features']}")

    logger.info("")

    # Load Finlab data
    try:
        data = load_finlab_data()
    except Exception as e:
        logger.error(f"❌ Data loading failed: {e}")
        logger.error("Cannot proceed without data")
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file
        }

    # Initialize ExtendedTestHarness
    logger.info("Initializing ExtendedTestHarness...")
    try:
        checkpoint_dir = 'checkpoints_100iteration'
        harness = ExtendedTestHarness(
            model='google/gemini-2.5-flash',
            target_iterations=100,
            checkpoint_interval=10,
            checkpoint_dir=checkpoint_dir,
            template_mode=True,  # Use template mode for consistent param preservation
            template_name="Momentum",  # Golden template from example/ analysis
            use_json_mode=True  # Phase 1.1: JSON Parameter Output for 100% success rate
        )
        logger.info(f"✅ ExtendedTestHarness initialized (checkpoints: {checkpoint_dir})")
        logger.info(f"   Template mode: ENABLED (Momentum template)")
        logger.info(f"   JSON mode: ENABLED (Phase 1.1)")
    except Exception as e:
        logger.error(f"❌ Harness initialization failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file
        }

    # Run test with harness
    logger.info("")
    logger.info("Starting 100-iteration test run...")
    logger.info("")

    start_time = datetime.now()

    try:
        results = harness.run_test(
            data=data,
            resume_from_checkpoint=resume_from
        )

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        # Extract key metrics
        test_completed = results.get('test_completed', False)
        total_iterations = results.get('total_iterations', 0)
        success_rate = results.get('success_rate', 0.0)
        best_sharpe = results.get('best_sharpe', 0.0)
        avg_sharpe = results.get('avg_sharpe', 0.0)
        statistical_report = results.get('statistical_report', {})
        final_checkpoint = results.get('final_checkpoint', '')

        # Extract Phase 1 + Phase 2 metrics
        logger.info("")
        logger.info("Extracting Phase 1 + Phase 2 metrics...")
        metrics = extract_phase1_phase2_metrics(results)
        logger.info(f"✅ Metrics extracted:")
        logger.info(f"   Data integrity checks: {metrics.get('data_checks', 0)}")
        logger.info(f"   Config snapshots: {metrics.get('config_snapshots', 0)}")
        logger.info(f"   Champion updates: {metrics.get('champion_updates', 0)}")

        # Add total duration to report
        if statistical_report:
            statistical_report['total_duration'] = total_duration

        # Print summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("TEST EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Test completed: {test_completed}")
        logger.info(f"Total iterations: {total_iterations}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Best Sharpe: {best_sharpe:.4f}")
        logger.info(f"Avg Sharpe: {avg_sharpe:.4f}")
        logger.info(f"Total duration: {total_duration/3600:.2f} hours")
        logger.info(f"Final checkpoint: {final_checkpoint}")
        logger.info("=" * 80)

        # Print production readiness report
        if statistical_report and not statistical_report.get('error'):
            print_colored_report(statistical_report, logger, metrics)
        else:
            logger.warning("❌ Statistical report not available")
            if statistical_report and 'error' in statistical_report:
                logger.warning(f"   Error: {statistical_report['error']}")

        # Add metadata to results
        results['success'] = True
        results['log_file'] = log_file
        results['total_duration'] = total_duration

        return results

    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file
        }


def main():
    """Main entry point for 100-iteration production test.

    Handles:
    - Command-line argument parsing for checkpoint resume
    - Test execution coordination
    - KeyboardInterrupt graceful handling
    - Exit codes for CI/CD integration

    Exit codes:
        0: Test completed successfully and passed production readiness criteria
        1: Test failed or did not meet production readiness criteria
        2: Test interrupted by user (KeyboardInterrupt)
        3: Test failed with exception
    """
    try:
        # Parse command-line arguments
        resume_from = None

        if len(sys.argv) > 1:
            resume_from = sys.argv[1]
            if not os.path.exists(resume_from):
                print(f"\n❌ Checkpoint file not found: {resume_from}")
                print("Starting fresh test run instead")
                resume_from = None

        print("\n🚀 Starting 100-iteration production test...\n")

        results = run_100iteration_test(resume_from=resume_from)

        if results.get('success'):
            statistical_report = results.get('statistical_report', {})
            production_ready = statistical_report.get('production_ready', False)

            print("\n✅ Test completed successfully")
            print(f"   Total iterations: {results.get('total_iterations', 0)}")
            print(f"   Success rate: {results.get('success_rate', 0.0):.1f}%")
            print(f"   Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
            print(f"   Avg Sharpe: {results.get('avg_sharpe', 0.0):.4f}")
            print(f"   Total duration: {results.get('total_duration', 0)/3600:.2f} hours")

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
        print("  python run_100iteration_test.py checkpoints_100iteration/checkpoint_iter_<N>.json")
        print("\nNote: Checkpoints are saved every 10 iterations")
        sys.exit(2)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main()
