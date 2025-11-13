#!/usr/bin/env python3
"""
Verification script for DockerExecutor implementation (Task 3).

This script verifies that the DockerExecutor module is correctly implemented
and meets all requirements from the docker-sandbox-security spec.

Usage:
    python3 scripts/verify_docker_executor.py
"""

import sys
import importlib.util
from pathlib import Path


def check_file_exists(filepath: str) -> bool:
    """Check if file exists."""
    path = Path(filepath)
    if path.exists():
        print(f"✅ {filepath} exists ({path.stat().st_size} bytes)")
        return True
    else:
        print(f"❌ {filepath} missing")
        return False


def check_import(module_path: str, class_name: str) -> bool:
    """Check if module can be imported and class exists."""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, class_name):
            print(f"✅ {class_name} class found in {module_path}")
            return True
        else:
            print(f"❌ {class_name} class not found in {module_path}")
            return False
    except Exception as e:
        print(f"❌ Failed to import {module_path}: {e}")
        return False


def check_method_exists(module_path: str, class_name: str, method_name: str) -> bool:
    """Check if class has required method."""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        cls = getattr(module, class_name)
        if hasattr(cls, method_name):
            print(f"  ✅ {class_name}.{method_name}() exists")
            return True
        else:
            print(f"  ❌ {class_name}.{method_name}() missing")
            return False
    except Exception as e:
        print(f"  ❌ Error checking method {method_name}: {e}")
        return False


def check_task_status() -> bool:
    """Check if task is marked complete in tasks.md."""
    tasks_file = Path(".spec-workflow/specs/docker-sandbox-security/tasks.md")
    if not tasks_file.exists():
        print("❌ tasks.md not found")
        return False

    with open(tasks_file, 'r') as f:
        content = f.read()

    # Check if Task 3 is marked complete
    if "- [x] 3. Create DockerExecutor module" in content:
        print("✅ Task 3 marked complete in tasks.md")
        return True
    else:
        print("❌ Task 3 not marked complete in tasks.md")
        return False


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("DockerExecutor Implementation Verification (Task 3)")
    print("=" * 70)
    print()

    all_checks_passed = True

    # 1. Check implementation files
    print("1. Implementation Files")
    print("-" * 70)
    checks = [
        check_file_exists("src/sandbox/docker_executor.py"),
        check_file_exists("src/sandbox/security_validator.py"),
        check_file_exists("src/sandbox/docker_config.py"),
    ]
    all_checks_passed &= all(checks)
    print()

    # 2. Check test files
    print("2. Test Files")
    print("-" * 70)
    checks = [
        check_file_exists("tests/sandbox/test_docker_executor.py"),
        check_file_exists("tests/integration/test_docker_executor_integration.py"),
    ]
    all_checks_passed &= all(checks)
    print()

    # 3. Check class exists
    print("3. DockerExecutor Class")
    print("-" * 70)
    executor_path = "src/sandbox/docker_executor.py"
    checks = [
        check_import(executor_path, "DockerExecutor"),
    ]
    all_checks_passed &= all(checks)
    print()

    # 4. Check required methods
    print("4. Required Methods")
    print("-" * 70)
    checks = [
        check_method_exists(executor_path, "DockerExecutor", "__init__"),
        check_method_exists(executor_path, "DockerExecutor", "execute"),
        check_method_exists(executor_path, "DockerExecutor", "_run_container"),
        check_method_exists(executor_path, "DockerExecutor", "_cleanup_container"),
        check_method_exists(executor_path, "DockerExecutor", "cleanup_all"),
        check_method_exists(executor_path, "DockerExecutor", "get_orphaned_containers"),
        check_method_exists(executor_path, "DockerExecutor", "__enter__"),
        check_method_exists(executor_path, "DockerExecutor", "__exit__"),
    ]
    all_checks_passed &= all(checks)
    print()

    # 5. Check documentation
    print("5. Documentation")
    print("-" * 70)
    checks = [
        check_file_exists("TASK3_DOCKER_EXECUTOR_IMPLEMENTATION.md"),
        check_file_exists("src/sandbox/README.md"),
    ]
    all_checks_passed &= all(checks)
    print()

    # 6. Check task status
    print("6. Task Status")
    print("-" * 70)
    all_checks_passed &= check_task_status()
    print()

    # 7. Requirements checklist
    print("7. Requirements Checklist")
    print("-" * 70)
    print("Review the following requirements manually:")
    print()
    print("  Requirement 1.1 (Container Isolation):")
    print("    - Network isolation (network_mode: none)")
    print("    - Filesystem isolation (read_only: true)")
    print("    - SecurityValidator integration")
    print()
    print("  Requirement 1.2 (Resource Limits):")
    print("    - Memory limit (2GB default)")
    print("    - CPU limit (0.5 cores default)")
    print("    - Timeout (600s default)")
    print()
    print("  Requirement 1.3 (Network Isolation):")
    print("    - network_mode: none")
    print()
    print("  Requirement 1.4 (Filesystem Isolation):")
    print("    - read_only: true")
    print("    - tmpfs: /tmp with size limits")
    print()
    print("  Requirement 1.5 (Auto Cleanup):")
    print("    - Multi-strategy cleanup (normal → force → kill)")
    print("    - 100% success rate guaranteed")
    print("    - Context manager support")
    print()

    # Summary
    print("=" * 70)
    if all_checks_passed:
        print("✅ ALL AUTOMATED CHECKS PASSED")
        print()
        print("Next steps:")
        print("  1. Review code manually for quality and correctness")
        print("  2. Run unit tests: pytest tests/sandbox/test_docker_executor.py -v")
        print("  3. Run integration tests (requires Docker):")
        print("     pytest tests/integration/test_docker_executor_integration.py -v -s")
        print("  4. Proceed to Task 4 (ContainerMonitor)")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
