#!/usr/bin/env python3
"""
Quick validation script to verify all Phase 1 features are integrated and working.

Validates:
- Story 6: Metric validation framework
- Story 7: Data pipeline integrity (checksums, provenance)
- Story 8: Experiment configuration tracking
"""

import os
import sys
import json
from pathlib import Path

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'artifacts', 'working', 'modules'))
sys.path.insert(0, os.path.dirname(__file__))

def validate_phase1_modules():
    """Validate all Phase 1 modules can be imported."""
    print("\n" + "=" * 70)
    print("PHASE 1 MODULE AVAILABILITY CHECK")
    print("=" * 70)

    results = {
        'all_available': True,
        'modules': {}
    }

    # Story 6: Metric Validator
    try:
        from src.validation.metric_validator import MetricValidator
        print("✅ Story 6: MetricValidator - Available")
        results['modules']['metric_validator'] = True
    except ImportError as e:
        print(f"❌ Story 6: MetricValidator - NOT Available ({e})")
        results['modules']['metric_validator'] = False
        results['all_available'] = False

    # Story 7: Data Pipeline Integrity
    try:
        from src.data.pipeline_integrity import DataPipelineIntegrity
        print("✅ Story 7: DataPipelineIntegrity - Available")
        results['modules']['data_integrity'] = True
    except ImportError as e:
        print(f"❌ Story 7: DataPipelineIntegrity - NOT Available ({e})")
        results['modules']['data_integrity'] = False
        results['all_available'] = False

    # Story 8: Experiment Config Manager
    try:
        from src.config.experiment_config_manager import ExperimentConfigManager
        print("✅ Story 8: ExperimentConfigManager - Available")
        results['modules']['config_manager'] = True
    except ImportError as e:
        print(f"❌ Story 8: ExperimentConfigManager - NOT Available ({e})")
        results['modules']['config_manager'] = False
        results['all_available'] = False

    print()
    return results

def validate_iteration_history():
    """Validate iteration history contains all Phase 1 fields."""
    print("=" * 70)
    print("ITERATION HISTORY VALIDATION")
    print("=" * 70)

    history_file = Path('iteration_history.json')

    if not history_file.exists():
        print("⚠️  No iteration_history.json found")
        print("   Run at least one iteration to generate history")
        return {
            'history_exists': False,
            'has_data_checksums': False,
            'has_config_snapshots': False
        }

    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        records = data.get('records', [])
        print(f"✅ History file loaded: {len(records)} iterations")

        # Check for Phase 1 fields
        has_data_checksums = False
        has_config_snapshots = False

        for record in records:
            if record.get('data_checksum'):
                has_data_checksums = True
            if record.get('config_snapshot'):
                has_config_snapshots = True

        print(f"\n   Phase 1 Field Status:")
        print(f"   - data_checksum: {'✅ Present' if has_data_checksums else '❌ Missing'}")
        print(f"   - data_version: {'✅ Present' if any(r.get('data_version') for r in records) else '❌ Missing'}")
        print(f"   - config_snapshot: {'✅ Present' if has_config_snapshots else '❌ Missing'}")

        # Sample first record to show structure
        if records:
            print(f"\n   Sample Record (Iteration {records[0].get('iteration_num', 'unknown')}):")
            print(f"   - Fields present: {list(records[0].keys())}")
            if records[0].get('data_checksum'):
                print(f"   - Data checksum: {records[0]['data_checksum'][:16]}...")
            if records[0].get('config_snapshot'):
                config = records[0]['config_snapshot']
                print(f"   - Config sections: {list(config.keys())}")

        print()
        return {
            'history_exists': True,
            'record_count': len(records),
            'has_data_checksums': has_data_checksums,
            'has_config_snapshots': has_config_snapshots
        }

    except Exception as e:
        print(f"❌ Error loading history: {e}")
        return {
            'history_exists': True,
            'error': str(e)
        }

def main():
    """Run Phase 1 validation checks."""
    print("\n🔍 Phase 1 Integration Validation")
    print("=" * 70)

    # Check module availability
    module_results = validate_phase1_modules()

    # Check iteration history
    history_results = validate_iteration_history()

    # Summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    all_passed = True

    # Module availability
    if module_results['all_available']:
        print("✅ All Phase 1 modules available")
    else:
        print("❌ Some Phase 1 modules missing")
        all_passed = False

    # History validation
    if history_results.get('history_exists'):
        if history_results.get('has_data_checksums') and history_results.get('has_config_snapshots'):
            print("✅ Iteration history has all Phase 1 fields")
        else:
            print("⚠️  Iteration history missing some Phase 1 fields")
            print("   (This is expected if no iterations have run since integration)")
    else:
        print("⚠️  No iteration history found")
        print("   (Run at least one iteration to validate integration)")

    print("=" * 70)

    if all_passed and history_results.get('has_data_checksums') and history_results.get('has_config_snapshots'):
        print("\n🎉 Phase 1 Integration: VALIDATED")
        return 0
    elif all_passed:
        print("\n✅ Phase 1 Modules: VALIDATED")
        print("⚠️  Run an iteration to fully validate integration")
        return 0
    else:
        print("\n❌ Phase 1 Integration: INCOMPLETE")
        return 1

if __name__ == '__main__':
    exit(main())
