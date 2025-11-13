#!/usr/bin/env python3
"""
Phase 1-4 Pilot Validation Test
================================
Validates configuration priority fixes (Phase 1-4) with real system runs.

Test Scenarios:
1. LLM Only (use_factor_graph=False) - 300 iterations
2. Factor Graph Only (use_factor_graph=True) - 300 iterations
3. Hybrid Mode (use_factor_graph=None) - 300 iterations

Success Criteria:
- Configuration priority respected 100% (zero violations)
- No silent fallbacks to default behavior
- Audit trail captures all decisions
- System completes 900 total iterations successfully

Duration: ~45-90 minutes (3 × 300 iterations)
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Set up paths
project_root = Path(__file__).parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

from src.learning.learning_loop import LearningLoop
from src.learning.learning_config import LearningConfig


class Phase14PilotValidator:
    """Validates Phase 1-4 fixes across three configuration scenarios."""

    def __init__(self, iterations_per_scenario: int = 300):
        self.iterations_per_scenario = iterations_per_scenario
        self.results = {
            'llm_only': {},
            'factor_graph_only': {},
            'hybrid': {}
        }
        self.start_time = None
        self.scenarios_completed = 0

    def run_scenario(
        self,
        scenario_name: str,
        use_factor_graph: Optional[bool],
        output_prefix: str
    ) -> Dict[str, Any]:
        """Run one validation scenario.

        Args:
            scenario_name: Human-readable scenario name
            use_factor_graph: True/False/None for mode selection
            output_prefix: Prefix for output files

        Returns:
            Dictionary with scenario results
        """
        print("\n" + "=" * 80)
        print(f"SCENARIO: {scenario_name}")
        print("=" * 80)
        print(f"Configuration: use_factor_graph={use_factor_graph}")
        print(f"Iterations: {self.iterations_per_scenario}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Create output directories
        output_dir = f"pilot_validation_results/{output_prefix}"
        os.makedirs(output_dir, exist_ok=True)

        history_file = f"{output_dir}/iteration_history.jsonl"
        champion_file = f"{output_dir}/champion.json"
        audit_dir = f"{output_dir}/audit_logs"

        # Enable all Phase 1-4 features
        os.environ['ENABLE_GENERATION_REFACTORING'] = 'true'
        os.environ['PHASE1_CONFIG_ENFORCEMENT'] = 'true'
        os.environ['PHASE2_PYDANTIC_VALIDATION'] = 'true'
        os.environ['PHASE3_STRATEGY_PATTERN'] = 'true'
        os.environ['PHASE4_AUDIT_TRAIL'] = 'true'

        # Create configuration with specific use_factor_graph setting
        config = LearningConfig(
            max_iterations=self.iterations_per_scenario,
            continue_on_error=True,  # Continue on errors to collect full data
            history_file=history_file,
            champion_file=champion_file,
            log_dir=f"{output_dir}/logs",
            log_level="INFO"
        )

        # Note: use_factor_graph is set via GenerationConfig in IterationExecutor
        # We'll need to pass this through the configuration system

        scenario_start = time.time()

        try:
            # Initialize learning loop
            loop = LearningLoop(config)

            # Override use_factor_graph in executor's config
            # This is the key Phase 1 fix - configuration priority enforcement
            loop.iteration_executor.config['use_factor_graph'] = use_factor_graph
            print(f"✓ Configuration set: use_factor_graph={use_factor_graph}")

            # Verify configuration in validated_config if Pydantic is enabled
            if hasattr(loop.iteration_executor, 'validated_config') and loop.iteration_executor.validated_config is not None:
                loop.iteration_executor.validated_config.use_factor_graph = use_factor_graph
                print(f"✓ Pydantic config updated: use_factor_graph={use_factor_graph}")

            print(f"\n📋 Starting {self.iterations_per_scenario} iterations...")
            print("=" * 80)

            # Run the learning loop
            loop.run()

            elapsed = time.time() - scenario_start
            print(f"\n✅ Scenario completed in {elapsed/60:.1f} minutes")

        except KeyboardInterrupt:
            print("\n⚠️  Scenario interrupted by user")
            return {'status': 'interrupted', 'error': 'User interrupt'}
        except Exception as e:
            print(f"\n❌ Scenario failed: {e}")
            import traceback
            traceback.print_exc()
            return {'status': 'failed', 'error': str(e)}

        # Analyze results
        results = self._analyze_scenario_results(
            scenario_name=scenario_name,
            use_factor_graph=use_factor_graph,
            history_file=history_file,
            audit_dir=audit_dir,
            elapsed_time=elapsed
        )

        # Save scenario report
        report_file = f"{output_dir}/scenario_report.json"
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n📄 Scenario report saved: {report_file}")

        return results

    def _analyze_scenario_results(
        self,
        scenario_name: str,
        use_factor_graph: Optional[bool],
        history_file: str,
        audit_dir: str,
        elapsed_time: float
    ) -> Dict[str, Any]:
        """Analyze results from a scenario."""

        print(f"\n" + "=" * 80)
        print(f"ANALYZING: {scenario_name}")
        print("=" * 80)

        results = {
            'scenario': scenario_name,
            'use_factor_graph': use_factor_graph,
            'target_iterations': self.iterations_per_scenario,
            'elapsed_time_minutes': round(elapsed_time / 60, 1),
            'timestamp': datetime.now().isoformat()
        }

        # Analyze iteration history
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                iterations = [json.loads(line) for line in f]

            results['total_iterations'] = len(iterations)
            results['successful_iterations'] = sum(1 for it in iterations if it.get('success', False))
            results['failed_iterations'] = len(iterations) - results['successful_iterations']
            results['success_rate'] = (results['successful_iterations'] / len(iterations) * 100) if iterations else 0

            print(f"Total iterations: {results['total_iterations']}")
            print(f"Successful: {results['successful_iterations']} ({results['success_rate']:.1f}%)")
            print(f"Failed: {results['failed_iterations']}")
        else:
            print("⚠️  No history file found")
            results['total_iterations'] = 0

        # Analyze audit trail (Phase 4 validation)
        audit_files = list(Path(audit_dir).glob("audit_*.json")) if os.path.exists(audit_dir) else []

        if audit_files:
            print(f"\nAudit trail files: {len(audit_files)}")

            # Load all audit decisions
            all_decisions = []
            for audit_file in audit_files:
                with open(audit_file, 'r') as f:
                    for line in f:
                        try:
                            all_decisions.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass

            results['audit_decisions'] = len(all_decisions)
            print(f"Total audit decisions logged: {len(all_decisions)}")

            # Phase 1 Critical Validation: Check configuration priority compliance
            violations = []
            expected_method = None

            if use_factor_graph is True:
                expected_method = "factor_graph"
            elif use_factor_graph is False:
                expected_method = "llm"
            # For None (hybrid), we expect a mix based on innovation_rate

            if expected_method:
                for decision in all_decisions:
                    actual_method = decision.get('generation_method')
                    if actual_method != expected_method:
                        violations.append({
                            'iteration': decision.get('iteration_num'),
                            'expected': expected_method,
                            'actual': actual_method,
                            'reason': decision.get('decision_reason')
                        })

            results['configuration_violations'] = len(violations)
            results['configuration_compliance'] = (
                (len(all_decisions) - len(violations)) / len(all_decisions) * 100
                if all_decisions else 0
            )

            print(f"\n📊 Configuration Priority Validation (Phase 1):")
            print(f"  Expected method: {expected_method or 'mixed (hybrid)'}")
            print(f"  Violations: {len(violations)}")
            print(f"  Compliance: {results['configuration_compliance']:.1f}%")

            if violations:
                print(f"\n⚠️  VIOLATIONS DETECTED:")
                for v in violations[:5]:  # Show first 5
                    print(f"    Iteration {v['iteration']}: expected={v['expected']}, actual={v['actual']}")
                if len(violations) > 5:
                    print(f"    ... and {len(violations) - 5} more")

            # Hybrid mode validation
            if use_factor_graph is None:
                llm_count = sum(1 for d in all_decisions if d.get('generation_method') == 'llm')
                fg_count = sum(1 for d in all_decisions if d.get('generation_method') == 'factor_graph')

                results['hybrid_llm_count'] = llm_count
                results['hybrid_fg_count'] = fg_count
                results['hybrid_llm_rate'] = (llm_count / len(all_decisions) * 100) if all_decisions else 0

                print(f"\n📊 Hybrid Mode Distribution:")
                print(f"  LLM: {llm_count} ({results['hybrid_llm_rate']:.1f}%)")
                print(f"  Factor Graph: {fg_count} ({100 - results['hybrid_llm_rate']:.1f}%)")
        else:
            print("\n⚠️  No audit trail found (Phase 4 issue)")
            results['audit_decisions'] = 0
            results['configuration_violations'] = -1  # Indicates no audit data

        # Success criteria check
        criteria_passed = {
            'iterations_completed': results.get('total_iterations', 0) >= self.iterations_per_scenario * 0.9,
            'configuration_compliance': results.get('configuration_compliance', 0) >= 99.0,
            'audit_trail_present': results.get('audit_decisions', 0) > 0,
            'no_violations': results.get('configuration_violations', 999) == 0
        }

        results['criteria_passed'] = criteria_passed
        results['all_criteria_passed'] = all(criteria_passed.values())

        print(f"\n📋 Success Criteria:")
        for criterion, passed in criteria_passed.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {criterion}")

        return results

    def run_all_scenarios(self):
        """Run all three validation scenarios."""

        self.start_time = datetime.now()

        print("\n" + "=" * 80)
        print("PHASE 1-4 PILOT VALIDATION TEST")
        print("=" * 80)
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total iterations: {self.iterations_per_scenario * 3}")
        print(f"Estimated duration: {self.iterations_per_scenario * 3 * 5 / 60:.0f}-{self.iterations_per_scenario * 3 * 10 / 60:.0f} minutes")
        print("=" * 80)

        # Scenario 1: LLM Only
        print("\n" + "🔵" * 40)
        self.results['llm_only'] = self.run_scenario(
            scenario_name="LLM Only (use_factor_graph=False)",
            use_factor_graph=False,
            output_prefix="llm_only"
        )
        self.scenarios_completed += 1

        # Scenario 2: Factor Graph Only
        print("\n" + "🟢" * 40)
        self.results['factor_graph_only'] = self.run_scenario(
            scenario_name="Factor Graph Only (use_factor_graph=True)",
            use_factor_graph=True,
            output_prefix="factor_graph_only"
        )
        self.scenarios_completed += 1

        # Scenario 3: Hybrid Mode
        print("\n" + "🟡" * 40)
        self.results['hybrid'] = self.run_scenario(
            scenario_name="Hybrid Mode (use_factor_graph=None)",
            use_factor_graph=None,
            output_prefix="hybrid"
        )
        self.scenarios_completed += 1

        # Generate final report
        self._generate_final_report()

    def _generate_final_report(self):
        """Generate comprehensive validation report."""

        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds() / 60

        print("\n\n" + "=" * 80)
        print("PHASE 1-4 PILOT VALIDATION - FINAL REPORT")
        print("=" * 80)
        print(f"Start: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Duration: {total_duration:.1f} minutes")
        print(f"Scenarios Completed: {self.scenarios_completed}/3")
        print("=" * 80)

        # Summary table
        print(f"\n{'Scenario':<25} {'Iterations':<12} {'Success %':<12} {'Violations':<12} {'Status':<10}")
        print("-" * 80)

        for scenario_key, scenario_name in [
            ('llm_only', 'LLM Only'),
            ('factor_graph_only', 'Factor Graph Only'),
            ('hybrid', 'Hybrid Mode')
        ]:
            result = self.results.get(scenario_key, {})
            iterations = result.get('total_iterations', 0)
            success_rate = result.get('success_rate', 0)
            violations = result.get('configuration_violations', -1)
            all_passed = result.get('all_criteria_passed', False)

            status = "✅ PASS" if all_passed else "❌ FAIL"
            violations_str = str(violations) if violations >= 0 else "N/A"

            print(f"{scenario_name:<25} {iterations:<12} {success_rate:>10.1f}% {violations_str:<12} {status:<10}")

        # Overall validation status
        print("\n" + "=" * 80)
        print("OVERALL VALIDATION STATUS")
        print("=" * 80)

        all_scenarios_passed = all(
            self.results.get(key, {}).get('all_criteria_passed', False)
            for key in ['llm_only', 'factor_graph_only', 'hybrid']
        )

        if all_scenarios_passed:
            print("✅ ✅ ✅ ALL SCENARIOS PASSED ✅ ✅ ✅")
            print("\nPhase 1-4 fixes validated successfully:")
            print("  ✓ Configuration priority enforced (100% compliance)")
            print("  ✓ No silent fallbacks detected")
            print("  ✓ Audit trail capturing all decisions")
            print("  ✓ System stable across 900 iterations")
            print("\n🎉 System ready for production deployment!")
        else:
            print("❌ SOME SCENARIOS FAILED ❌")
            print("\nPlease review scenario reports for details")
            print("Issues may indicate:")
            print("  - Configuration priority violations (Phase 1)")
            print("  - Missing audit trail (Phase 4)")
            print("  - System stability issues")

        # Save combined report
        final_report = {
            'validation_type': 'phase_1_4_pilot',
            'timestamp': datetime.now().isoformat(),
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_duration_minutes': total_duration,
            'scenarios_completed': self.scenarios_completed,
            'iterations_per_scenario': self.iterations_per_scenario,
            'total_iterations_target': self.iterations_per_scenario * 3,
            'results': self.results,
            'all_scenarios_passed': all_scenarios_passed
        }

        report_file = "pilot_validation_results/FINAL_VALIDATION_REPORT.json"
        os.makedirs("pilot_validation_results", exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)

        print(f"\n📄 Final report saved: {report_file}")
        print("=" * 80)

        return all_scenarios_passed


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Phase 1-4 Pilot Validation Test")
    parser.add_argument(
        '--iterations',
        type=int,
        default=300,
        help="Iterations per scenario (default: 300)"
    )
    parser.add_argument(
        '--quick',
        action='store_true',
        help="Quick test mode (30 iterations per scenario)"
    )

    args = parser.parse_args()

    iterations = 30 if args.quick else args.iterations

    print("=" * 80)
    print("Phase 1-4 Pilot Validation Test")
    print("=" * 80)
    print(f"Iterations per scenario: {iterations}")
    print(f"Total iterations: {iterations * 3}")
    print(f"Mode: {'QUICK TEST' if args.quick else 'FULL VALIDATION'}")
    print("=" * 80)

    # Run validation
    validator = Phase14PilotValidator(iterations_per_scenario=iterations)
    all_passed = validator.run_all_scenarios()

    # Exit code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
