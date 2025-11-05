#!/usr/bin/env python3
"""
Phase 1: Full Test (50 Generations)

Complete validation of population-based evolutionary learning with:
- Full population (50) per expert review
- 50 generations for comprehensive evolution
- Tournament selection with elitism
- Adaptive mutation rates
- IS/OOS data split validation
- Convergence detection with restarts

Target Metrics (from Expert Review):
- Champion update rate: ≥10% (5+ updates in 50 generations)
- Best In-Sample Sharpe: >2.5 (beat Phase 0 champion)
- Champion Out-of-Sample Sharpe: >1.0 (validate robustness)
- Parameter diversity: ≥50% unique at gen 1-3

Decision Matrix:
- SUCCESS (≥10% update rate AND IS Sharpe >2.5 AND OOS Sharpe >1.0): Phase 1 validated
- PARTIAL (≥5% update rate AND IS Sharpe >2.0 AND OOS Sharpe 0.6-1.0): Tune hyperparameters
- FAILURE (<5% update rate OR IS Sharpe <2.0 OR OOS Sharpe <0.6): Investigate root cause

Expected Duration: 2.5-3 hours

Usage:
    python3 run_phase1_full_test.py
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'tests', 'integration'))

from phase1_test_harness import Phase1TestHarness


def setup_logging():
    """Configure comprehensive logging for full test."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f"phase1_full_test_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: {log_file}")
    return logger, log_file


def load_finlab_data():
    """Load real Finlab data for testing.

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
        logger.error(f"❌ Failed to load Finlab data: {e}")
        raise


def validate_phase1_components(logger: logging.Logger) -> dict:
    """Validate that all Phase 1 components are available.

    Returns:
        dict: Component availability status
    """
    logger.info("=" * 70)
    logger.info("VALIDATING PHASE 1 COMPONENTS")
    logger.info("=" * 70)

    status = {
        'all_available': True,
        'missing_components': []
    }

    # Check required components
    required = [
        ('Individual', 'src.population.individual'),
        ('PopulationManager', 'src.population.population_manager'),
        ('GeneticOperators', 'src.population.genetic_operators'),
        ('FitnessEvaluator', 'src.population.fitness_evaluator'),
        ('EvolutionMonitor', 'src.population.evolution_monitor'),
        ('MomentumTemplate', 'src.templates.momentum_template')
    ]

    for component_name, module_path in required:
        try:
            module = __import__(module_path, fromlist=[component_name])
            getattr(module, component_name)
            logger.info(f"  ✅ {component_name} available")
        except (ImportError, AttributeError) as e:
            status['all_available'] = False
            status['missing_components'].append(component_name)
            logger.error(f"  ❌ {component_name} not available - {e}")

    # Summary
    logger.info("")
    if status['all_available']:
        logger.info("✅ All Phase 1 components available")
    else:
        logger.error(f"❌ Missing {len(status['missing_components'])} components: {', '.join(status['missing_components'])}")
        logger.error("Cannot proceed without all components")

    logger.info("=" * 70)
    logger.info("")

    return status


def run_phase1_full_test():
    """Run 50-generation full test for Phase 1 population-based learning.

    Configuration (from Expert Review):
    - Population size: 50 (increased from 30)
    - Elite size: 5 (10%)
    - Generations: 50
    - Mutation rate: 0.15 (adaptive 0.05-0.30)
    - Tournament size: 2 (reduced from 3)
    - Max restarts: 3
    - IS period: 2015:2020
    - OOS period: 2021:2024
    - Checkpoint interval: 10

    Returns:
        Dictionary with test results and metrics
    """
    logger, log_file = setup_logging()

    logger.info("=" * 70)
    logger.info("PHASE 1: FULL TEST (50 GENERATIONS)")
    logger.info("=" * 70)
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info(f"Mode: Population-based evolutionary learning")
    logger.info(f"Target generations: 50")
    logger.info(f"Population size: 50 (per expert review)")
    logger.info(f"Expected duration: 2.5-3 hours")
    logger.info(f"Log file: {log_file}")
    logger.info("")

    # Validate Phase 1 components
    phase1_status = validate_phase1_components(logger)

    if not phase1_status['all_available']:
        logger.error("❌ Cannot proceed without all Phase 1 components")
        return {
            'success': False,
            'error': f"Missing components: {', '.join(phase1_status['missing_components'])}",
            'log_file': log_file,
            'phase1_status': phase1_status
        }

    # Load Finlab data
    try:
        data = load_finlab_data()
    except Exception as e:
        logger.error(f"❌ Data loading failed: {e}")
        logger.error("Cannot proceed without data")
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file,
            'phase1_status': phase1_status
        }

    # Initialize Phase1TestHarness for full test
    logger.info("Initializing Phase1TestHarness for full test...")
    harness = Phase1TestHarness(
        test_name='phase1_full',
        num_generations=50,
        population_size=50,
        elite_size=5,
        mutation_rate=0.15,
        tournament_size=2,
        max_restarts=3,
        is_period='2015:2020',
        oos_period='2021:2024',
        checkpoint_interval=10
    )

    # Run test
    try:
        logger.info("Starting 50-generation full test...")
        logger.info("")

        results = harness.run(data=data, resume_from_checkpoint=None)

        # Enhance results
        results['phase1_status'] = phase1_status
        results['log_file'] = log_file
        results['success'] = results.get('test_completed', False)

        # Save results to JSON
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = os.path.join(results_dir, f"phase1_full_test_{timestamp}.json")

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results saved to: {results_file}")

        # Print summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("PHASE 1 FULL TEST - COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Test completed: {results['success']}")
        logger.info(f"Total generations: {results.get('total_generations', 0)}")
        logger.info(f"Champion updates: {results.get('champion_update_count', 0)} ({results.get('champion_update_rate', 0.0):.1f}%)")
        logger.info(f"Best IS Sharpe: {results.get('best_is_sharpe', 0.0):.4f}")
        logger.info(f"Champion OOS Sharpe: {results.get('champion_oos_sharpe', 0.0):.4f}")
        logger.info(f"Avg IS Sharpe: {results.get('avg_is_sharpe', 0.0):.4f}")
        logger.info(f"Final diversity: {results.get('population_diversity_final', 0.0):.1%}")
        logger.info(f"Restarts: {results.get('restart_count', 0)}")
        logger.info(f"Cache hit rate: {results.get('cache_hit_rate', 0.0):.1%}")
        logger.info(f"Decision: {results.get('decision', 'N/A')}")
        logger.info("")
        logger.info(f"Results file: {results_file}")
        logger.info(f"Log file: {log_file}")
        logger.info("=" * 70)

        return results

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("=" * 70)
        logger.warning("TEST INTERRUPTED BY USER")
        logger.warning("=" * 70)
        logger.warning("Partial results may be available in checkpoint")
        return {
            'success': False,
            'error': 'User interrupted',
            'log_file': log_file,
            'phase1_status': phase1_status
        }

    except Exception as e:
        logger.error("")
        logger.error("=" * 70)
        logger.error("TEST FAILED WITH EXCEPTION")
        logger.error("=" * 70)
        logger.error(f"Error: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'log_file': log_file,
            'phase1_status': phase1_status
        }


def main():
    """Main entry point."""
    try:
        print("\n🚀 Starting Phase 1 full test (50 generations)...\n")
        print("⏱️  Estimated duration: 2.5-3 hours\n")

        results = run_phase1_full_test()

        if results.get('success'):
            print(f"\n✅ Full test completed successfully")
            print(f"   Total generations: {results.get('total_generations', 0)}")
            print(f"   Champion updates: {results.get('champion_update_count', 0)} ({results.get('champion_update_rate', 0.0):.1f}%)")
            print(f"   Best IS Sharpe: {results.get('best_is_sharpe', 0.0):.4f}")
            print(f"   Champion OOS Sharpe: {results.get('champion_oos_sharpe', 0.0):.4f}")
            print(f"   Avg IS Sharpe: {results.get('avg_is_sharpe', 0.0):.4f}")
            print(f"   Final diversity: {results.get('population_diversity_final', 0.0):.1%}")
            print(f"   Restarts: {results.get('restart_count', 0)}")
            print(f"   Cache hit rate: {results.get('cache_hit_rate', 0.0):.1%}")
            print(f"   Decision: {results.get('decision', 'N/A')}")

            # Phase 1 status
            phase1_status = results.get('phase1_status', {})
            if phase1_status.get('all_available'):
                print(f"   Phase 1 components: ✅ All available")

            print(f"   Log file: {results['log_file']}")

            # Decision analysis
            print("\n📊 Phase 1 Full Test Decision Analysis:")
            champion_update_rate = results.get('champion_update_rate', 0.0)
            best_is_sharpe = results.get('best_is_sharpe', 0.0)
            champion_oos_sharpe = results.get('champion_oos_sharpe', 0.0)

            if champion_update_rate >= 10.0 and best_is_sharpe > 2.5 and champion_oos_sharpe > 1.0:
                print("   ✅ SUCCESS: Phase 1 population-based learning validated")
                print("   📝 Recommendation: Deploy to production with confidence")
            elif champion_update_rate >= 5.0 and best_is_sharpe > 2.0 and champion_oos_sharpe > 0.6:
                print("   ⚠️  PARTIAL: Promising results, needs hyperparameter tuning")
                print("   📝 Recommendation: Re-test with adjusted parameters")
            else:
                print("   ❌ FAILURE: Did not meet Phase 1 targets")
                print("   📝 Recommendation: Investigate root cause and revise approach")

            print(f"\n   Metrics achieved:")
            print(f"   - Champion update rate: {champion_update_rate:.1f}% (target: ≥10%)")
            print(f"   - Best IS Sharpe: {best_is_sharpe:.4f} (target: >2.5)")
            print(f"   - Champion OOS Sharpe: {champion_oos_sharpe:.4f} (target: >1.0)")

            sys.exit(0)
        else:
            print(f"\n❌ Full test failed: {results.get('error', 'Unknown error')}")
            print(f"   Log file: {results.get('log_file', 'N/A')}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(2)

    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == '__main__':
    main()
