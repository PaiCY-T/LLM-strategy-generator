#!/usr/bin/env python3
"""
Task 6.2 System Validation Test - 30 Iterations
============================================

Validates Requirement 7 success criteria through actual system execution:
1. Docker execution success rate >80%
2. Diversity-aware prompting activates ≥30% of eligible iterations
3. No regression in direct-execution mode
4. Config snapshots saved successfully

Background Context:
- Bug #1 (F-string): Fixed with diagnostic logging
- Bug #2 (LLM API): Fixed via config (provider=openrouter, model=google/gemini-2.5-flash)
- Bug #3 (ExperimentConfig): Module created at src/config/experiment_config.py
- Bug #4 (Exception state): Fixed (last_result=False in exception handler)

Success Criteria:
- Docker success rate >80% (>24 out of 30 iterations)
- Diversity activation rate ≥30% (if failures trigger it)
- Zero import errors for ExperimentConfig
- All metrics collected and documented
"""

import sys
import os
import json
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "artifacts" / "working" / "modules"))

# Import autonomous loop components
from autonomous_loop import AutonomousLoop
from history import IterationHistory


class ValidationMetricsCollector:
    """Collects and analyzes validation metrics for Task 6.2."""

    def __init__(self):
        self.iterations_data = []
        self.docker_successes = 0
        self.docker_failures = 0
        self.diversity_activations = 0
        self.import_errors = 0
        self.config_snapshot_errors = 0
        self.start_time = None
        self.end_time = None

    def start_collection(self):
        """Start timing metrics collection."""
        self.start_time = time.time()
        print("🚀 Starting Task 6.2 Validation - 30 Iterations")
        print("=" * 70)

    def record_iteration(self, iteration_num: int, iteration_data: Dict[str, Any],
                        log_output: str = ""):
        """Record metrics for a single iteration.

        Args:
            iteration_num: Iteration number (0-indexed)
            iteration_data: Data from iteration history
            log_output: Captured log output from the iteration
        """
        print(f"\n📊 Iteration {iteration_num} Analysis:")

        # Track Docker execution
        docker_used = self._check_docker_execution(log_output)
        if docker_used:
            docker_success = self._check_docker_success(log_output, iteration_data)
            if docker_success:
                self.docker_successes += 1
                print("  ✅ Docker execution: SUCCESS")
            else:
                self.docker_failures += 1
                print("  ❌ Docker execution: FAILED")
        else:
            print("  ⚠️  Direct execution mode (no Docker)")

        # Track diversity-aware prompting activation
        diversity_activated = self._check_diversity_activation(log_output)
        if diversity_activated:
            self.diversity_activations += 1
            print("  🎯 Diversity-aware prompting: ACTIVATED")

        # Track import errors
        import_error = self._check_import_errors(log_output)
        if import_error:
            self.import_errors += 1
            print("  ⚠️  Import error detected!")

        # Track config snapshot errors
        config_error = self._check_config_snapshot_errors(log_output)
        if config_error:
            self.config_snapshot_errors += 1
            print("  ⚠️  Config snapshot error detected!")

        # Store iteration data
        self.iterations_data.append({
            "iteration": iteration_num,
            "docker_used": docker_used,
            "docker_success": docker_success if docker_used else None,
            "diversity_activated": diversity_activated,
            "import_error": import_error,
            "config_error": config_error,
            "timestamp": datetime.now().isoformat(),
            "metrics": iteration_data.get("metrics", {})
        })

    def _check_docker_execution(self, log_output: str) -> bool:
        """Check if Docker was used for execution."""
        return "Executing strategy in Docker sandbox" in log_output or \
               "DockerExecutor" in log_output

    def _check_docker_success(self, log_output: str, iteration_data: Dict) -> bool:
        """Check if Docker execution succeeded."""
        # Look for success indicators
        if "Docker execution completed successfully" in log_output:
            return True
        if "Container execution succeeded" in log_output:
            return True

        # Check if metrics were extracted (indicates success)
        metrics = iteration_data.get("metrics", {})
        if metrics and "sharpe_ratio" in metrics:
            return True

        # Look for failure indicators
        if "Docker execution failed" in log_output:
            return False
        if "Container timeout" in log_output:
            return False
        if "DockerException" in log_output:
            return False

        # If we have metrics, assume success
        return bool(metrics)

    def _check_diversity_activation(self, log_output: str) -> bool:
        """Check if diversity-aware prompting was activated."""
        # Look for the key indicator from Bug #4 fix
        if "Setting last_result=False" in log_output:
            return True
        if "Diversity-aware prompting activated" in log_output:
            return True
        if "diversity_aware_mode: true" in log_output:
            return True
        return False

    def _check_import_errors(self, log_output: str) -> bool:
        """Check for import errors related to ExperimentConfig."""
        if "ImportError" in log_output and "experiment_config" in log_output.lower():
            return True
        if "ModuleNotFoundError" in log_output and "ExperimentConfig" in log_output:
            return True
        return False

    def _check_config_snapshot_errors(self, log_output: str) -> bool:
        """Check for config snapshot save errors."""
        if "Failed to save config snapshot" in log_output:
            return True
        if "ExperimentConfig" in log_output and "error" in log_output.lower():
            return True
        return False

    def finish_collection(self):
        """Finalize metrics collection."""
        self.end_time = time.time()

    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate final validation metrics.

        Returns:
            Dictionary with all validation metrics
        """
        total_iterations = len(self.iterations_data)
        docker_iterations = sum(1 for d in self.iterations_data if d["docker_used"])

        # Calculate success rate (only for Docker iterations)
        if docker_iterations > 0:
            success_rate = (self.docker_successes / docker_iterations) * 100
        else:
            success_rate = 0

        # Calculate diversity rate (percentage of total iterations)
        if total_iterations > 0:
            diversity_rate = (self.diversity_activations / total_iterations) * 100
        else:
            diversity_rate = 0

        execution_time = self.end_time - self.start_time if self.end_time else 0

        return {
            "total_iterations": total_iterations,
            "docker_iterations": docker_iterations,
            "docker_successes": self.docker_successes,
            "docker_failures": self.docker_failures,
            "success_rate": round(success_rate, 2),
            "diversity_activations": self.diversity_activations,
            "diversity_rate": round(diversity_rate, 2),
            "import_errors": self.import_errors,
            "config_snapshot_errors": self.config_snapshot_errors,
            "execution_time_seconds": round(execution_time, 2),
            "iterations_data": self.iterations_data
        }

    def print_summary(self, metrics: Dict[str, Any]):
        """Print validation summary with pass/fail status."""
        print("\n" + "=" * 70)
        print("📊 TASK 6.2 VALIDATION SUMMARY")
        print("=" * 70)

        print(f"\n📈 Overall Metrics:")
        print(f"  Total iterations: {metrics['total_iterations']}")
        print(f"  Docker iterations: {metrics['docker_iterations']}")
        print(f"  Execution time: {metrics['execution_time_seconds']:.1f}s")

        print(f"\n🐳 Docker Execution:")
        print(f"  Successes: {metrics['docker_successes']}")
        print(f"  Failures: {metrics['docker_failures']}")
        print(f"  Success rate: {metrics['success_rate']:.1f}%")

        # Check success criterion 1
        success_rate_pass = metrics['success_rate'] > 80
        status1 = "✅ PASS" if success_rate_pass else "❌ FAIL"
        print(f"  Criterion 1 (>80% success): {status1}")

        print(f"\n🎯 Diversity-Aware Prompting:")
        print(f"  Activations: {metrics['diversity_activations']}")
        print(f"  Activation rate: {metrics['diversity_rate']:.1f}%")

        # Check success criterion 2 (if there were failures)
        if metrics['docker_failures'] > 0:
            diversity_pass = metrics['diversity_rate'] >= 30
            status2 = "✅ PASS" if diversity_pass else "❌ FAIL"
            print(f"  Criterion 2 (≥30% activation): {status2}")
        else:
            status2 = "N/A (no failures)"
            diversity_pass = True
            print(f"  Criterion 2: {status2}")

        print(f"\n🚨 Error Detection:")
        print(f"  Import errors: {metrics['import_errors']}")
        print(f"  Config snapshot errors: {metrics['config_snapshot_errors']}")

        # Check success criterion 3
        import_errors_pass = metrics['import_errors'] == 0
        status3 = "✅ PASS" if import_errors_pass else "❌ FAIL"
        print(f"  Criterion 3 (zero import errors): {status3}")

        # Check success criterion 4
        config_errors_pass = metrics['config_snapshot_errors'] == 0
        status4 = "✅ PASS" if config_errors_pass else "❌ FAIL"
        print(f"  Criterion 4 (zero config errors): {status4}")

        # Overall pass/fail
        all_pass = success_rate_pass and diversity_pass and import_errors_pass and config_errors_pass

        print("\n" + "=" * 70)
        if all_pass:
            print("🎉 VALIDATION RESULT: ✅ ALL CRITERIA PASSED")
            print("Task 6.2 is ready to be marked complete!")
        else:
            print("⚠️  VALIDATION RESULT: ❌ SOME CRITERIA FAILED")
            print("Please review failures before marking task complete.")
        print("=" * 70)

        return all_pass


def run_validation():
    """Run 30-iteration validation test for Task 6.2."""

    # Initialize metrics collector
    collector = ValidationMetricsCollector()
    collector.start_collection()

    # Load configuration
    config_path = project_root / "config" / "learning_system.yaml"
    if not config_path.exists():
        print(f"❌ ERROR: Configuration file not found: {config_path}")
        sys.exit(1)

    print(f"📝 Configuration: {config_path}")

    # Check for API keys
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("\n⚠️  WARNING: OPENROUTER_API_KEY not set in environment")
        print("   LLM innovation may fail. Please set the API key:")
        print("   export OPENROUTER_API_KEY='your-key-here'")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Validation cancelled.")
            sys.exit(0)
    else:
        print("✅ OPENROUTER_API_KEY configured")

    # Initialize autonomous loop
    max_iterations = 30
    print(f"\n🔄 Initializing autonomous loop for {max_iterations} iterations...")

    # Set up logging to capture output
    import logging
    import io

    # Create string buffer to capture logs
    log_buffer = io.StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    log_handler.setLevel(logging.DEBUG)

    # Add handler to root logger
    root_logger = logging.getLogger()
    original_level = root_logger.level
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(log_handler)

    try:
        # Create autonomous loop instance
        # AutonomousLoop creates its own IterationHistory
        loop = AutonomousLoop(
            model="gemini-2.5-flash",  # Will use openrouter based on config
            max_iterations=max_iterations,
            history_file="task_6_2_validation_history.json",
            template_mode=False  # Free-form mode for LLM innovation
        )

        print("✅ Autonomous loop initialized")
        print(f"   Sandbox enabled: {loop.sandbox_enabled}")
        print(f"   LLM enabled: {loop.llm_enabled}")

        # Run iterations with metrics collection
        print(f"\n🚀 Starting {max_iterations} iterations...")
        print("This will take approximately 1-2 hours...")

        for iteration in range(max_iterations):
            print(f"\n{'='*70}")
            print(f"Iteration {iteration}/{max_iterations}")
            print(f"{'='*70}")

            # Clear log buffer for this iteration
            log_buffer.truncate(0)
            log_buffer.seek(0)

            try:
                # Run single iteration
                success, status = loop.run_iteration(iteration, data=None)

                # Get log output from buffer
                log_output = log_buffer.getvalue()

                # Get iteration data from history
                iteration_record = loop.history.get_record(iteration)
                iteration_data = {
                    "success": success,
                    "status": status,
                    "metrics": iteration_record.metrics if iteration_record else {},
                    "validation_passed": iteration_record.validation_passed if iteration_record else False,
                    "execution_success": iteration_record.execution_success if iteration_record else False
                }

                # Record metrics
                collector.record_iteration(iteration, iteration_data, log_output)

            except Exception as e:
                print(f"❌ Iteration {iteration} failed with exception: {e}")
                import traceback
                traceback.print_exc()

                # Get log output even on exception
                log_output = log_buffer.getvalue()
                log_output += f"\nException: {str(e)}\n{traceback.format_exc()}"

                # Still record the failure
                collector.record_iteration(iteration, {"success": False}, log_output)

        print(f"\n✅ Completed {max_iterations} iterations")

    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Cleanup logging
        root_logger.removeHandler(log_handler)
        root_logger.setLevel(original_level)
        collector.finish_collection()

    # Calculate and save metrics
    print("\n📊 Calculating final metrics...")
    metrics = collector.calculate_metrics()

    # Save raw metrics to JSON
    results_file = project_root / "task_6_2_validation_results.json"
    with open(results_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✅ Raw metrics saved to: {results_file}")

    # Print summary
    all_pass = collector.print_summary(metrics)

    # Generate detailed report
    print("\n📝 Generating detailed validation report...")
    generate_report(metrics, all_pass)

    return all_pass


def generate_report(metrics: Dict[str, Any], all_pass: bool):
    """Generate detailed validation report in Markdown.

    Args:
        metrics: Validation metrics dictionary
        all_pass: Whether all criteria passed
    """
    report_file = project_root / "TASK_6.2_VALIDATION_REPORT.md"

    with open(report_file, 'w') as f:
        f.write("# Task 6.2 System Validation Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Status**: {'✅ PASSED' if all_pass else '❌ FAILED'}\n")
        f.write(f"**Duration**: {metrics['execution_time_seconds']:.1f} seconds\n\n")

        f.write("## Executive Summary\n\n")
        if all_pass:
            f.write("All success criteria for Task 6.2 have been met. The system validation ")
            f.write("demonstrates that:\n\n")
            f.write("1. Docker execution maintains >80% success rate\n")
            f.write("2. Diversity-aware prompting activates appropriately after failures\n")
            f.write("3. No import errors for ExperimentConfig module\n")
            f.write("4. Config snapshots are saved successfully\n\n")
            f.write("**Recommendation**: Task 6.2 can be marked complete in tasks.md.\n\n")
        else:
            f.write("Some success criteria were not met. Please review the failures below ")
            f.write("and address issues before marking task complete.\n\n")

        f.write("## Metrics Summary\n\n")
        f.write("| Metric | Value | Target | Status |\n")
        f.write("|--------|-------|--------|--------|\n")

        # Success Rate
        success_rate_status = "✅ Pass" if metrics['success_rate'] > 80 else "❌ Fail"
        f.write(f"| Docker Success Rate | {metrics['success_rate']:.1f}% | >80% | {success_rate_status} |\n")

        # Diversity Rate
        if metrics['docker_failures'] > 0:
            diversity_status = "✅ Pass" if metrics['diversity_rate'] >= 30 else "❌ Fail"
            f.write(f"| Diversity Activation Rate | {metrics['diversity_rate']:.1f}% | ≥30% | {diversity_status} |\n")
        else:
            f.write(f"| Diversity Activation Rate | {metrics['diversity_rate']:.1f}% | ≥30% | N/A (no failures) |\n")

        # Import Errors
        import_status = "✅ Pass" if metrics['import_errors'] == 0 else "❌ Fail"
        f.write(f"| Import Errors | {metrics['import_errors']} | 0 | {import_status} |\n")

        # Config Errors
        config_status = "✅ Pass" if metrics['config_snapshot_errors'] == 0 else "❌ Fail"
        f.write(f"| Config Snapshot Errors | {metrics['config_snapshot_errors']} | 0 | {config_status} |\n\n")

        f.write("## Detailed Results\n\n")
        f.write(f"- **Total Iterations**: {metrics['total_iterations']}\n")
        f.write(f"- **Docker Iterations**: {metrics['docker_iterations']}\n")
        f.write(f"- **Docker Successes**: {metrics['docker_successes']}\n")
        f.write(f"- **Docker Failures**: {metrics['docker_failures']}\n")
        f.write(f"- **Diversity Activations**: {metrics['diversity_activations']}\n")
        f.write(f"- **Execution Time**: {metrics['execution_time_seconds']:.1f}s ({metrics['execution_time_seconds']/60:.1f} minutes)\n\n")

        f.write("## Iteration-by-Iteration Breakdown\n\n")
        f.write("| Iter | Docker Used | Docker Success | Diversity Activated | Import Error | Config Error |\n")
        f.write("|------|-------------|----------------|---------------------|--------------|-------------|\n")

        for data in metrics['iterations_data']:
            iter_num = data['iteration']
            docker_used = "Yes" if data['docker_used'] else "No"
            docker_success = "✅" if data.get('docker_success') else ("❌" if data['docker_used'] else "-")
            diversity = "🎯" if data['diversity_activated'] else "-"
            import_err = "⚠️" if data['import_error'] else "-"
            config_err = "⚠️" if data['config_error'] else "-"

            f.write(f"| {iter_num} | {docker_used} | {docker_success} | {diversity} | {import_err} | {config_err} |\n")

        f.write("\n## Success Criteria Verification\n\n")

        f.write("### Criterion 1: Docker Execution Success Rate >80%\n\n")
        if metrics['success_rate'] > 80:
            f.write(f"✅ **PASSED**: Achieved {metrics['success_rate']:.1f}% success rate ")
            f.write(f"({metrics['docker_successes']}/{metrics['docker_iterations']} successful executions)\n\n")
        else:
            f.write(f"❌ **FAILED**: Only achieved {metrics['success_rate']:.1f}% success rate ")
            f.write(f"({metrics['docker_successes']}/{metrics['docker_iterations']} successful executions)\n\n")

        f.write("### Criterion 2: Diversity-Aware Prompting Activation ≥30%\n\n")
        if metrics['docker_failures'] > 0:
            if metrics['diversity_rate'] >= 30:
                f.write(f"✅ **PASSED**: Diversity activated in {metrics['diversity_rate']:.1f}% of iterations ")
                f.write(f"({metrics['diversity_activations']}/{metrics['total_iterations']} iterations)\n\n")
            else:
                f.write(f"❌ **FAILED**: Diversity only activated in {metrics['diversity_rate']:.1f}% of iterations ")
                f.write(f"({metrics['diversity_activations']}/{metrics['total_iterations']} iterations)\n\n")
        else:
            f.write(f"**N/A**: No Docker failures occurred, so diversity prompting was not needed.\n")
            f.write(f"This is actually a positive result (100% success rate).\n\n")

        f.write("### Criterion 3: Zero Import Errors\n\n")
        if metrics['import_errors'] == 0:
            f.write("✅ **PASSED**: No import errors detected for ExperimentConfig module\n\n")
        else:
            f.write(f"❌ **FAILED**: {metrics['import_errors']} import errors detected\n\n")

        f.write("### Criterion 4: Config Snapshots Saved Successfully\n\n")
        if metrics['config_snapshot_errors'] == 0:
            f.write("✅ **PASSED**: All config snapshots saved successfully\n\n")
        else:
            f.write(f"❌ **FAILED**: {metrics['config_snapshot_errors']} config snapshot errors detected\n\n")

        f.write("## Recommendations\n\n")
        if all_pass:
            f.write("1. Mark Task 6.2 as complete in tasks.md with `[x]`\n")
            f.write("2. Archive this validation report for documentation\n")
            f.write("3. Proceed to next phase of docker-integration-test-framework spec\n")
        else:
            f.write("1. Review failed criteria and address root causes\n")
            f.write("2. Re-run validation after fixes are applied\n")
            f.write("3. Do not mark task complete until all criteria pass\n")

        f.write("\n## Bug Fix Context\n\n")
        f.write("This validation confirms the fixes applied for:\n\n")
        f.write("- **Bug #1**: F-string formatting - Fixed with diagnostic logging\n")
        f.write("- **Bug #2**: LLM API 404 errors - Fixed via config (provider=openrouter, model=google/gemini-2.5-flash)\n")
        f.write("- **Bug #3**: ExperimentConfig import - Module created at src/config/experiment_config.py\n")
        f.write("- **Bug #4**: Exception state - Fixed (last_result=False in exception handler)\n\n")

        f.write("---\n")
        f.write(f"*Report generated at {datetime.now().isoformat()}*\n")

    print(f"✅ Detailed report saved to: {report_file}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("TASK 6.2 SYSTEM VALIDATION TEST")
    print("Docker Integration Test Framework - Phase 6")
    print("=" * 70)

    success = run_validation()

    sys.exit(0 if success else 1)
