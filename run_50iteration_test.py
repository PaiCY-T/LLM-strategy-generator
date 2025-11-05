#!/usr/bin/env python3
"""
50-Iteration Production Test Run for Learning System Validation

Runs 50 iterations of the autonomous learning loop using ExtendedTestHarness
with automatic checkpointing, retry logic, and comprehensive statistical analysis.

This is a production-ready test script that validates learning system stability
and provides a production readiness assessment based on statistical criteria.
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
    log_file = os.path.join(log_dir, f"50iteration_test_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__), log_file


def validate_phase1_features(logger: logging.Logger) -> dict:
    """Validate that all Phase 1 stability features are available.

    Checks:
    - Story 6: MetricValidator available
    - Story 5: BehavioralValidator available (future)
    - Story 7: DataPipelineIntegrity available
    - Story 8: ExperimentConfigManager available

    Returns:
        dict: {
            'all_available': bool,
            'story6_available': bool,
            'story5_available': bool,
            'story7_available': bool,
            'story8_available': bool,
            'missing_features': list
        }
    """
    status = {
        'all_available': True,
        'story6_available': False,
        'story5_available': False,
        'story7_available': False,
        'story8_available': False,
        'missing_features': []
    }

    # Check Story 6: MetricValidator
    try:
        from src.validation.metric_validator import MetricValidator
        status['story6_available'] = True
        logger.info("  ✅ Story 6: MetricValidator available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('MetricValidator')
        logger.warning(f"  ❌ Story 6: MetricValidator not available - {e}")

    # Check Story 5: BehavioralValidator (future)
    try:
        from src.validation.behavioral_validator import BehavioralValidator
        status['story5_available'] = True
        logger.info("  ✅ Story 5: BehavioralValidator available")
    except ImportError:
        # Not critical - Story 5 is future work
        logger.info("  ⏳ Story 5: BehavioralValidator not yet implemented")

    # Check Story 7: DataPipelineIntegrity
    try:
        from src.data.pipeline_integrity import DataPipelineIntegrity
        status['story7_available'] = True
        logger.info("  ✅ Story 7: DataPipelineIntegrity available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('DataPipelineIntegrity')
        logger.warning(f"  ❌ Story 7: DataPipelineIntegrity not available - {e}")

    # Check Story 8: ExperimentConfigManager
    try:
        from src.config.experiment_config_manager import ExperimentConfigManager
        status['story8_available'] = True
        logger.info("  ✅ Story 8: ExperimentConfigManager available")
    except ImportError as e:
        status['all_available'] = False
        status['missing_features'].append('ExperimentConfigManager')
        logger.warning(f"  ❌ Story 8: ExperimentConfigManager not available - {e}")

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


def extract_phase1_metrics(results: dict) -> dict:
    """Extract Phase 1-specific metrics from test results.

    Extracts:
    - Data consistency checks performed
    - Data checksum changes detected
    - Configuration changes detected
    - Configuration diff severities

    Args:
        results: Test results dictionary from ExtendedTestHarness

    Returns:
        dict with Phase 1 metrics
    """
    phase1_metrics = {
        'data_checks': 0,
        'data_changes': 0,
        'config_snapshots': 0,
        'config_changes': 0,
        'critical_config_changes': 0,
        'moderate_config_changes': 0,
        'minor_config_changes': 0
    }

    # Check if iteration_history file exists
    history_file = Path('iteration_history.json')
    if not history_file.exists():
        return phase1_metrics

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)

        records = history_data.get('records', [])

        # Count data checksums present
        prev_checksum = None
        for record in records:
            if record.get('data_checksum'):
                phase1_metrics['data_checks'] += 1

                # Count changes
                if prev_checksum and prev_checksum != record['data_checksum']:
                    phase1_metrics['data_changes'] += 1

                prev_checksum = record['data_checksum']

        # Count config snapshots present
        prev_config = None
        for record in records:
            if record.get('config_snapshot'):
                phase1_metrics['config_snapshots'] += 1

                # Count changes between configs
                if prev_config:
                    # Compare model_config, prompt_config, system_thresholds
                    has_change = False

                    current_config = record['config_snapshot']

                    # Check model changes (critical)
                    if prev_config.get('model_config', {}).get('model_name') != current_config.get('model_config', {}).get('model_name'):
                        phase1_metrics['critical_config_changes'] += 1
                        has_change = True

                    # Check temperature changes (moderate)
                    if prev_config.get('model_config', {}).get('temperature') != current_config.get('model_config', {}).get('temperature'):
                        phase1_metrics['moderate_config_changes'] += 1
                        has_change = True

                    # Check prompt version changes (moderate)
                    if prev_config.get('prompt_config', {}).get('version') != current_config.get('prompt_config', {}).get('version'):
                        phase1_metrics['moderate_config_changes'] += 1
                        has_change = True

                    # Check threshold changes (moderate)
                    if prev_config.get('system_thresholds') != current_config.get('system_thresholds'):
                        phase1_metrics['moderate_config_changes'] += 1
                        has_change = True

                    if has_change:
                        phase1_metrics['config_changes'] += 1

                prev_config = record['config_snapshot']

    except Exception as e:
        logging.getLogger(__name__).warning(f"Error extracting Phase 1 metrics: {e}")

    return phase1_metrics


def print_colored_report(report: dict, logger: logging.Logger, phase1_metrics: dict = None):
    """Print production readiness report with colored formatting.

    Outputs comprehensive statistical report with color coding for
    production readiness status and key metrics.

    Args:
        report: Statistical report dictionary from ExtendedTestHarness
        logger: Logger instance for output
        phase1_metrics: Optional Phase 1 metrics dictionary
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("PRODUCTION READINESS REPORT")
    logger.info("=" * 70)

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
    logger.info(f"  Convergence achieved: {report.get('convergence_achieved', False)}")

    logger.info("")
    logger.info("ADDITIONAL METRICS:")
    logger.info(f"  Champion update frequency: {report.get('champion_update_frequency', 0.0):.1f}%")
    logger.info(f"  Avg duration per iteration: {report.get('avg_duration_per_iteration', 0.0):.2f}s")

    # Phase 1 stability features section
    if phase1_metrics:
        logger.info("")
        logger.info("PHASE 1 STABILITY FEATURES:")
        logger.info(f"  Data integrity checks: {phase1_metrics.get('data_checks', 0)}")
        logger.info(f"  Data changes detected: {phase1_metrics.get('data_changes', 0)}")
        logger.info(f"  Config snapshots captured: {phase1_metrics.get('config_snapshots', 0)}")
        logger.info(f"  Config changes detected: {phase1_metrics.get('config_changes', 0)}")

        # Show severity breakdown if there are changes
        if phase1_metrics.get('config_changes', 0) > 0:
            logger.info(f"    - Critical changes: {phase1_metrics.get('critical_config_changes', 0)}")
            logger.info(f"    - Moderate changes: {phase1_metrics.get('moderate_config_changes', 0)}")
            logger.info(f"    - Minor changes: {phase1_metrics.get('minor_config_changes', 0)}")

    logger.info("")
    logger.info("READINESS REASONING:")
    for reason in report.get('readiness_reasoning', []):
        logger.info(f"  {reason}")

    logger.info("=" * 70)


def run_50iteration_test(resume_from: str = None):
    """Run 50-iteration test with ExtendedTestHarness.

    Main test orchestration function that:
    - Sets up logging
    - Loads Finlab data
    - Initializes ExtendedTestHarness
    - Executes 50-iteration test run
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

    logger.info("=" * 70)
    logger.info("50-ITERATION PRODUCTION TEST - START")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Model: google/gemini-2.5-flash")
    logger.info(f"Target iterations: 50")
    logger.info(f"Checkpoint interval: 10")
    logger.info(f"Log file: {log_file}")

    if resume_from:
        logger.info(f"Resume from checkpoint: {resume_from}")

    logger.info("")

    # Validate Phase 1 stability features
    logger.info("Validating Phase 1 stability features...")
    phase1_status = validate_phase1_features(logger)

    if phase1_status['all_available']:
        logger.info("✅ All Phase 1 features available")
    else:
        logger.warning(f"⚠️  Missing features: {phase1_status['missing_features']}")

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
        harness = ExtendedTestHarness(
            model='google/gemini-2.5-flash',
            target_iterations=50,
            checkpoint_interval=10,
            checkpoint_dir='checkpoints'
        )
        logger.info("✅ ExtendedTestHarness initialized successfully")
    except Exception as e:
        logger.error(f"❌ Harness initialization failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file
        }

    # Run test with harness
    logger.info("")
    logger.info("Starting test run...")
    logger.info("")

    try:
        results = harness.run_test(
            data=data,
            resume_from_checkpoint=resume_from
        )

        # Extract key metrics
        test_completed = results.get('test_completed', False)
        total_iterations = results.get('total_iterations', 0)
        success_rate = results.get('success_rate', 0.0)
        best_sharpe = results.get('best_sharpe', 0.0)
        avg_sharpe = results.get('avg_sharpe', 0.0)
        statistical_report = results.get('statistical_report', {})
        final_checkpoint = results.get('final_checkpoint', '')

        # Extract Phase 1 metrics
        logger.info("")
        logger.info("Extracting Phase 1 stability metrics...")
        phase1_metrics = extract_phase1_metrics(results)
        logger.info(f"✅ Phase 1 metrics extracted:")
        logger.info(f"   Data integrity checks: {phase1_metrics.get('data_checks', 0)}")
        logger.info(f"   Config snapshots: {phase1_metrics.get('config_snapshots', 0)}")

        # Print summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("TEST EXECUTION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Test completed: {test_completed}")
        logger.info(f"Total iterations: {total_iterations}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        logger.info(f"Best Sharpe: {best_sharpe:.4f}")
        logger.info(f"Avg Sharpe: {avg_sharpe:.4f}")
        logger.info(f"Final checkpoint: {final_checkpoint}")
        logger.info("=" * 70)

        # Print production readiness report with Phase 1 metrics
        if statistical_report and not statistical_report.get('error'):
            print_colored_report(statistical_report, logger, phase1_metrics)
        else:
            logger.warning("❌ Statistical report not available")
            if statistical_report and 'error' in statistical_report:
                logger.warning(f"   Error: {statistical_report['error']}")

        # Add metadata to results
        results['success'] = True
        results['log_file'] = log_file

        return results

    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file
        }


def main():
    """Main entry point for 50-iteration production test.

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
        # Check for resume checkpoint argument
        resume_from = None
        if len(sys.argv) > 1:
            resume_from = sys.argv[1]
            if not os.path.exists(resume_from):
                print(f"\n❌ Checkpoint file not found: {resume_from}")
                print("Starting fresh test run instead")
                resume_from = None

        print("\n🚀 Starting 50-iteration production test...\n")

        results = run_50iteration_test(resume_from=resume_from)

        if results.get('success'):
            statistical_report = results.get('statistical_report', {})
            production_ready = statistical_report.get('production_ready', False)

            print(f"\n✅ Test completed successfully")
            print(f"   Total iterations: {results.get('total_iterations', 0)}")
            print(f"   Success rate: {results.get('success_rate', 0.0):.1f}%")
            print(f"   Best Sharpe: {results.get('best_sharpe', 0.0):.4f}")
            print(f"   Avg Sharpe: {results.get('avg_sharpe', 0.0):.4f}")

            if production_ready:
                print(f"\n🎉 PRODUCTION READY: All criteria met")
                print(f"   Log file: {results['log_file']}")
                print(f"   Final checkpoint: {results.get('final_checkpoint', 'N/A')}")
                sys.exit(0)
            else:
                print(f"\n⚠️  NOT PRODUCTION READY: Some criteria not met")
                print(f"   Review statistical report for details")
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
        print("  python run_50iteration_test.py checkpoints/checkpoint_iter_<N>.json")
        print("\nNote: Checkpoints are saved every 10 iterations")
        sys.exit(2)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main()
