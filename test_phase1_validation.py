#!/usr/bin/env python3
"""
Quick test script to validate Phase 1 feature detection.

Demonstrates the validate_phase1_features() function from run_50iteration_test.py
without requiring a full 50-iteration test run.
"""

import os
import sys
import logging

# Add modules to path
sys.path.insert(0, os.path.dirname(__file__))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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


def main():
    """Test Phase 1 feature validation."""
    print("\n" + "=" * 70)
    print("PHASE 1 STABILITY FEATURES VALIDATION TEST")
    print("=" * 70)
    print()

    logger.info("Validating Phase 1 stability features...")
    print()

    phase1_status = validate_phase1_features(logger)

    print()
    print("=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    if phase1_status['all_available']:
        print("✅ SUCCESS: All Phase 1 features available")
    else:
        print("⚠️  WARNING: Some Phase 1 features missing")
        print(f"   Missing features: {phase1_status['missing_features']}")

    print()
    print("Feature Availability:")
    print(f"  Story 6 (MetricValidator): {'✅' if phase1_status['story6_available'] else '❌'}")
    print(f"  Story 5 (BehavioralValidator): {'✅' if phase1_status['story5_available'] else '⏳'}")
    print(f"  Story 7 (DataPipelineIntegrity): {'✅' if phase1_status['story7_available'] else '❌'}")
    print(f"  Story 8 (ExperimentConfigManager): {'✅' if phase1_status['story8_available'] else '❌'}")

    print()
    print("=" * 70)
    print()

    # Return exit code
    sys.exit(0 if phase1_status['all_available'] else 1)


if __name__ == '__main__':
    main()
