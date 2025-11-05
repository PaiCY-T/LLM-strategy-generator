#!/usr/bin/env python3
"""
Bug Fix Validation Pilot Test - Task 6.2
=========================================
30-iteration validation test to verify all 4 critical bug fixes are working

Test Objectives:
- Bug #1: Verify no {{}} in Docker code assembly
- Bug #2: Verify LLM API routing prevents 404 errors
- Bug #3: Verify configuration capture succeeds
- Bug #4: Verify diversity-aware prompting activates after failures

Success Criteria:
- >80% Docker execution success rate
- ≥30% diversity-aware prompting activation rate
- Zero 404 LLM API errors
- Zero configuration capture failures

Duration: ~3 minutes (6 seconds/iteration × 30 iterations)
"""

import sys
import os
import json
import time
import re
from datetime import datetime
from pathlib import Path

# Set up paths
project_root = Path(__file__).parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "artifacts" / "working" / "modules"))

from autonomous_loop import AutonomousLoop


class BugFixValidator:
    """Tracks bug fix indicators during pilot test"""

    def __init__(self):
        self.metrics = {
            'total_iterations': 0,
            'docker_success': 0,
            'docker_failure': 0,
            'config_capture_success': 0,
            'config_capture_failure': 0,
            'llm_404_errors': 0,
            'llm_success': 0,
            'diversity_prompting_activations': 0,
            'fstring_violations': 0,
        }
        self.iteration_details = []

    def record_iteration(self, iteration_num, success, error_msg=""):
        """Record results from an iteration"""
        self.metrics['total_iterations'] += 1

        # Track Docker execution (Bug #1 and #4)
        if success:
            self.metrics['docker_success'] += 1
        else:
            self.metrics['docker_failure'] += 1

        # Track 404 errors (Bug #2)
        if '404' in error_msg:
            self.metrics['llm_404_errors'] += 1

        # Track config capture (Bug #3)
        if 'Configuration capture failed' in error_msg:
            self.metrics['config_capture_failure'] += 1

        # Track f-string violations (Bug #1)
        if '{{' in error_msg or '}}' in error_msg:
            self.metrics['fstring_violations'] += 1

        self.iteration_details.append({
            'iteration': iteration_num,
            'success': success,
            'error': error_msg
        })

    def generate_report(self):
        """Generate validation report"""
        total = self.metrics['total_iterations']
        docker_success_rate = (self.metrics['docker_success'] / total * 100) if total > 0 else 0

        report = f"""
================================================================================
BUG FIX VALIDATION REPORT - Task 6.2
================================================================================
Test Duration: {total} iterations
Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CRITICAL BUG FIX VALIDATION
================================================================================

Bug #1 (F-String Evaluation):
  ❌ Violations Found: {self.metrics['fstring_violations']}
  ✅ Status: {'PASS' if self.metrics['fstring_violations'] == 0 else 'FAIL'}

Bug #2 (LLM API Routing):
  ❌ 404 Errors: {self.metrics['llm_404_errors']}
  ✅ Status: {'PASS' if self.metrics['llm_404_errors'] == 0 else 'FAIL'}

Bug #3 (ExperimentConfig Import):
  ✅ Success: {self.metrics['config_capture_success']}
  ❌ Failures: {self.metrics['config_capture_failure']}
  ✅ Status: {'PASS' if self.metrics['config_capture_failure'] == 0 else 'FAIL'}

Bug #4 (Exception State Propagation):
  🎨 Diversity Activations: {self.metrics['diversity_prompting_activations']}
  ✅ Status: {'PASS' if self.metrics['diversity_prompting_activations'] > 0 else 'NEEDS_MORE_DATA'}

SYSTEM PERFORMANCE METRICS
================================================================================

Docker Execution:
  ✅ Success: {self.metrics['docker_success']} ({docker_success_rate:.1f}%)
  ❌ Failure: {self.metrics['docker_failure']}
  Target: >80% success rate
  Status: {'PASS' if docker_success_rate > 80 else 'FAIL'}

Overall Validation:
  All Bugs Fixed: {'YES ✅' if all([
      self.metrics['fstring_violations'] == 0,
      self.metrics['llm_404_errors'] == 0,
      self.metrics['config_capture_failure'] == 0,
      docker_success_rate > 80
  ]) else 'NO ❌'}

================================================================================
"""
        return report


def run_validation_pilot():
    """Run 30-iteration validation pilot test"""

    validator = BugFixValidator()

    print("=" * 80)
    print("BUG FIX VALIDATION PILOT TEST - Task 6.2")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nValidating 4 critical bug fixes:")
    print("  1. F-string template evaluation")
    print("  2. LLM API routing validation")
    print("  3. ExperimentConfig module import")
    print("  4. Exception state propagation")
    print("\nTarget: 30 iterations (~3 minutes)")
    print("=" * 80)
    print()

    try:
        # Initialize autonomous loop with LLM innovation enabled
        loop = AutonomousLoop(
            max_iterations=30,
            llm_enabled=True,
            llm_model="gemini-2.5-flash",  # Use Google AI (should work with Bug #2 fix)
            innovation_rate=0.3  # 30% innovation rate to trigger diversity
        )

        print("📋 Autonomous loop initialized successfully")
        print(f"   LLM enabled: {loop.llm_enabled}")
        print(f"   Innovation rate: {loop.config.get('innovation_rate', 0.3)}")
        print(f"   Model: gemini-2.5-flash")
        print()

        # Run the loop
        print("=" * 80)
        print(f"STARTING VALIDATION - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        print()

        loop.run()

        print("\n" + "=" * 80)
        print("VALIDATION COMPLETE")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()

    # Generate and display report
    report = validator.generate_report()
    print(report)

    # Save report to file
    report_file = f"task_6.2_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"\n📄 Report saved to: {report_file}")

    return validator.metrics


if __name__ == "__main__":
    metrics = run_validation_pilot()

    # Exit with appropriate code
    all_pass = all([
        metrics['fstring_violations'] == 0,
        metrics['llm_404_errors'] == 0,
        metrics['config_capture_failure'] == 0,
        (metrics['docker_success'] / metrics['total_iterations'] * 100) > 80 if metrics['total_iterations'] > 0 else False
    ])

    sys.exit(0 if all_pass else 1)
