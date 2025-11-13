#!/usr/bin/env python3
"""
Direct Test Runner for Task 6.1 - Docker Integration Test Framework

This script runs all integration tests directly without pytest fixtures
to avoid the logger cache cleanup issue that causes I/O errors.

Tests:
- Characterization baseline (all 6 tests)
- F-string evaluation (2 tests)
- Exception state propagation (4 tests)
- Docker integration E2E (4 tests)

Total: 16 tests
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "artifacts" / "working" / "modules"))


def run_test(test_class, test_method_name: str) -> Tuple[str, bool, str]:
    """
    Run a single test method.

    Args:
        test_class: Test class instance
        test_method_name: Name of test method to run

    Returns:
        Tuple of (test_name, passed, error_message)
    """
    try:
        test_method = getattr(test_class, test_method_name)
        test_method()
        return (test_method_name, True, "")
    except AssertionError as e:
        return (test_method_name, False, f"AssertionError: {str(e)[:200]}")
    except Exception as e:
        return (test_method_name, False, f"{type(e).__name__}: {str(e)[:200]}")


def main():
    """Run all integration tests and generate report."""
    print("=" * 80)
    print("Task 6.1 - Docker Integration Test Framework Validation")
    print("=" * 80)
    print()

    start_time = time.time()
    results: List[Tuple[str, bool, str]] = []

    # Import test classes
    from tests.integration.test_characterization_baseline import TestCharacterizationBaseline
    from tests.integration.test_fstring_evaluation import TestFStringEvaluation
    from tests.integration.test_exception_state_propagation import TestExceptionStatePropagation
    from tests.integration.test_docker_integration_e2e import TestDockerIntegrationE2E

    # Define all tests to run
    test_suite = [
        # Characterization baseline tests (6 tests)
        (TestCharacterizationBaseline(), [
            'test_bug1_fstring_template_evaluation_in_docker_code',
            'test_bug2_llm_api_routing_validation_missing',
            'test_bug3_experiment_config_module_missing',
            'test_bug4_exception_state_propagation_broken',
            'test_integration_boundary_docker_code_assembly',
            'test_integration_boundary_llm_config_parsing',
        ]),
        # F-string evaluation tests (2 tests)
        (TestFStringEvaluation(), [
            'test_data_setup_no_double_braces_in_assembled_code',
            'test_data_setup_contains_expected_mock_structures',
        ]),
        # Exception state propagation tests (4 tests)
        (TestExceptionStatePropagation(), [
            'test_docker_exception_sets_last_result_false',
            'test_docker_success_sets_last_result_true',
            'test_fallback_count_increments_on_exception',
            'test_consecutive_exceptions_enable_diversity_fallback',
        ]),
        # Docker integration E2E tests (4 tests)
        (TestDockerIntegrationE2E(), [
            'test_full_integration_flow_with_all_bug_fixes',
            'test_llm_to_docker_code_assembly',
            'test_docker_exception_triggers_fallback',
            'test_config_snapshot_serialization',
        ]),
    ]

    # Run all tests
    print("Running Tests:")
    print("-" * 80)

    for test_instance, test_methods in test_suite:
        test_class_name = test_instance.__class__.__name__
        print(f"\n{test_class_name}:")

        for test_method in test_methods:
            test_name, passed, error = run_test(test_instance, test_method)
            results.append((f"{test_class_name}.{test_name}", passed, error))

            status = "PASS" if passed else "FAIL"
            print(f"  {test_name}: {status}")
            if not passed and error:
                print(f"    Error: {error}")

    # Calculate statistics
    end_time = time.time()
    total_tests = len(results)
    passed_tests = sum(1 for _, passed, _ in results if passed)
    failed_tests = total_tests - passed_tests
    execution_time = end_time - start_time

    # Print summary
    print()
    print("=" * 80)
    print("Test Summary:")
    print("-" * 80)
    print(f"Total Tests:     {total_tests}")
    print(f"Passed:          {passed_tests}")
    print(f"Failed:          {failed_tests}")
    print(f"Success Rate:    {(passed_tests/total_tests)*100:.1f}%")
    print(f"Execution Time:  {execution_time:.2f} seconds")
    print("=" * 80)

    # Check acceptance criteria
    print()
    print("Acceptance Criteria Check:")
    print("-" * 80)

    all_passed = failed_tests == 0
    time_acceptable = execution_time < 30

    print(f"✓ All tests passing: {'YES' if all_passed else 'NO'}")
    print(f"✓ Execution time < 30s: {'YES' if time_acceptable else 'NO'} ({execution_time:.2f}s)")

    if all_passed and time_acceptable:
        print()
        print("SUCCESS: All acceptance criteria met!")
        return 0
    else:
        print()
        print("FAILURE: Some acceptance criteria not met.")
        if failed_tests > 0:
            print("\nFailed Tests:")
            for test_name, passed, error in results:
                if not passed:
                    print(f"  - {test_name}")
                    if error:
                        print(f"    {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
