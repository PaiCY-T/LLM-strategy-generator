"""Pilot Test Execution Script - 20 Iterations Each

Runs three experimental groups:
1. LLM-Only (100% LLM innovation)
2. Factor Graph Only (0% LLM - baseline)
3. Hybrid (30% LLM + 70% Factor Graph)

After Phase 3.3 dict interface fix for Phase 7 E2E unblocking.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

def print_header(title: str, char: str = "="):
    """Print formatted section header."""
    print(f"\n{char * 72}")
    print(title)
    print(f"{char * 72}\n")

def run_pilot_test(config_file: Path, test_name: str, log_dir: Path) -> bool:
    """Run a single pilot test.

    Args:
        config_file: Path to config YAML file
        test_name: Name for this test run
        log_dir: Directory to save logs

    Returns:
        True if test passed, False otherwise
    """
    log_file = log_dir / f"{test_name}.log"

    print_header(f"Running: {test_name}", "-")
    print(f"Config: {config_file}")
    print(f"Log: {log_file}\n")

    # Prepare command
    cmd = [
        sys.executable,
        "experiments/llm_learning_validation/orchestrator.py",
        "--config", str(config_file),
        "--phase", "pilot"
    ]

    # Run test with output to both console and log file
    try:
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Stream output to both console and log file
            for line in process.stdout:
                print(line, end='')
                f.write(line)

            process.wait()

        if process.returncode == 0:
            print(f"\n✅ {test_name} COMPLETED SUCCESSFULLY")
            return True
        else:
            print(f"\n❌ {test_name} FAILED (exit code: {process.returncode})")
            return False

    except Exception as e:
        print(f"\n❌ {test_name} FAILED with exception: {e}")
        return False

def main():
    """Execute all three pilot tests."""
    print_header("Pilot Test Execution - 20 Iterations Per Group")

    print("Experimental Groups:")
    print("  1. LLM-Only (100% LLM innovation)")
    print("  2. Factor Graph Only (0% LLM - baseline)")
    print("  3. Hybrid (30% LLM + 70% Factor Graph)")
    print("\nTesting Phase 3.3 dict interface fix for Phase 7 E2E unblocking")

    # Setup paths
    project_root = Path(__file__).parent
    results_base = project_root / "experiments" / "llm_learning_validation" / "results"
    results_base.mkdir(parents=True, exist_ok=True)

    # Create timestamped log directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = results_base / f"pilot_run_{timestamp}"
    log_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nLog directory: {log_dir}")

    # Define test configurations
    tests = [
        {
            'name': 'LLM-Only Mode',
            'config': 'experiments/llm_learning_validation/config_pilot_llm_only_20.yaml',
            'test_id': 'pilot_llm_only_20'
        },
        {
            'name': 'Factor Graph Only Mode',
            'config': 'experiments/llm_learning_validation/config_pilot_fg_only_20.yaml',
            'test_id': 'pilot_fg_only_20'
        },
        {
            'name': 'Hybrid Mode',
            'config': 'experiments/llm_learning_validation/config_pilot_hybrid_20.yaml',
            'test_id': 'pilot_hybrid_20'
        }
    ]

    # Run all tests
    results = []
    for i, test in enumerate(tests, 1):
        print_header(f"TEST {i}/{len(tests)}: {test['name']}")

        config_path = project_root / test['config']
        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            results.append(False)
            continue

        passed = run_pilot_test(config_path, test['test_id'], log_dir)
        results.append(passed)

    # Print summary
    print_header("Pilot Test Execution Summary")

    total_tests = len(tests)
    passed_tests = sum(results)

    print(f"Tests Passed: {passed_tests} / {total_tests}")
    print(f"Logs saved to: {log_dir}\n")

    if passed_tests == total_tests:
        print("✅ ALL PILOT TESTS PASSED!\n")
        print("Next Steps:")
        print("  1. Review results in: experiments/llm_learning_validation/results/")
        print(f"  2. Check logs in: {log_dir}")
        print("  3. Update IMPLEMENTATION_STATUS.md - Mark Phase 7 as UNBLOCKED")
        print("  4. Run analysis:")
        print("     python3 experiments/llm_learning_validation/orchestrator.py --analyze pilot\n")
        sys.exit(0)
    else:
        failed = total_tests - passed_tests
        print(f"⚠️  Some tests failed: {failed} / {total_tests}\n")
        print(f"Check logs for details: {log_dir}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
