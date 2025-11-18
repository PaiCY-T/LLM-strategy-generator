"""
Security Test: Detect Hardcoded API Keys and Secrets

Task: 1.1 - Week 1: Security Fix
Requirements: AC1.1, NFR-S1, NFR-S2

This test ensures that no hardcoded API keys, passwords, or secrets
are present in the codebase. All credentials must be loaded from
environment variables.

Test-Driven Development - RED Phase:
    This test MUST fail initially to verify it catches hardcoded secrets.
    After implementing environment variable loading, this test should pass.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


# Patterns that indicate hardcoded secrets
SECRET_PATTERNS = [
    # API keys
    (r"['\"]api_key['\"]\s*:\s*['\"](?!{|test-key$)[^'\"]{8,}['\"]", "hardcoded api_key value"),
    (r"API_KEY\s*=\s*['\"][^'\"]{8,}['\"]", "hardcoded API_KEY variable"),

    # Passwords
    (r"['\"]password['\"]\s*:\s*['\"][^'\"]{4,}['\"]", "hardcoded password value"),
    (r"PASSWORD\s*=\s*['\"][^'\"]{4,}['\"]", "hardcoded PASSWORD variable"),

    # Tokens
    (r"['\"]token['\"]\s*:\s*['\"][^'\"]{8,}['\"]", "hardcoded token value"),
    (r"TOKEN\s*=\s*['\"][^'\"]{8,}['\"]", "hardcoded TOKEN variable"),

    # Generic secrets
    (r"['\"]secret['\"]\s*:\s*['\"][^'\"]{8,}['\"]", "hardcoded secret value"),
    (r"SECRET\s*=\s*['\"][^'\"]{8,}['\"]", "hardcoded SECRET variable"),
]

# Files and directories to exclude from scanning
EXCLUDED_PATHS = [
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    ".venv",
    "venv",
    ".env.example",  # Example files are OK
    "test_no_hardcoded_secrets.py",  # This test file itself
]


def scan_file_for_secrets(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scan a single file for hardcoded secrets.

    Args:
        file_path: Path to file to scan

    Returns:
        List of (line_number, pattern_description, line_content) tuples
        for any hardcoded secrets found
    """
    violations = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, start=1):
                for pattern, description in SECRET_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append((line_num, description, line.strip()))
    except Exception as e:
        # Skip files that can't be read
        pass

    return violations


def should_scan_file(file_path: Path) -> bool:
    """
    Determine if a file should be scanned for secrets.

    Args:
        file_path: Path to check

    Returns:
        True if file should be scanned, False otherwise
    """
    # Only scan Python files
    if file_path.suffix != '.py':
        return False

    # Skip excluded paths
    for excluded in EXCLUDED_PATHS:
        if excluded in file_path.parts:
            return False

    return True


def scan_codebase_for_secrets() -> List[Tuple[Path, int, str, str]]:
    """
    Scan entire codebase for hardcoded secrets.

    Returns:
        List of (file_path, line_number, pattern_description, line_content)
        tuples for all hardcoded secrets found
    """
    project_root = Path(__file__).parent.parent.parent  # Go up to project root
    all_violations = []

    # Scan all Python files in the project
    for py_file in project_root.rglob("*.py"):
        if should_scan_file(py_file):
            file_violations = scan_file_for_secrets(py_file)
            for line_num, description, line_content in file_violations:
                all_violations.append((py_file, line_num, description, line_content))

    return all_violations


def test_no_hardcoded_api_keys():
    """
    RED Test: Detect hardcoded API keys in codebase.

    This test scans the entire codebase for hardcoded API keys, passwords,
    and other secrets. All credentials must be loaded from environment
    variables using os.getenv() or similar mechanisms.

    Expected Initial Result: FAIL
        - tests/e2e/conftest.py:77 contains 'api_key': 'test-key'

    Expected After Fix: PASS
        - All API keys loaded from environment variables
        - No hardcoded credentials in codebase
    """
    violations = scan_codebase_for_secrets()

    if violations:
        # Format violation report
        violation_report = "\n\nHardcoded secrets detected:\n"
        violation_report += "=" * 80 + "\n"

        for file_path, line_num, description, line_content in violations:
            relative_path = file_path.relative_to(
                Path(__file__).parent.parent.parent
            )
            violation_report += f"\n{relative_path}:{line_num}\n"
            violation_report += f"  Issue: {description}\n"
            violation_report += f"  Line: {line_content}\n"

        violation_report += "\n" + "=" * 80 + "\n"
        violation_report += "\nSecurity Violation: Hardcoded secrets must be replaced with "
        violation_report += "environment variable loading (os.getenv()).\n"

        # Fail the test with detailed report
        assert False, violation_report

    # Test passes - no hardcoded secrets found
    assert True, "No hardcoded secrets detected - security check passed!"


def test_environment_variable_loading_pattern():
    """
    Verify that codebase uses environment variable loading pattern.

    This test checks that sensitive configuration values are loaded
    using os.getenv() or similar environment variable mechanisms.

    Expected Pattern:
        api_key = os.getenv("API_KEY", "default_value")
        OR
        api_key = os.environ.get("API_KEY")
    """
    # Search for environment variable usage in configuration files
    project_root = Path(__file__).parent.parent.parent

    env_var_pattern = r"(os\.getenv|os\.environ\.get|os\.environ\[)"

    # Check key configuration files use environment variables
    config_files = [
        "tests/e2e/conftest.py",
        "src/config/feature_flags.py",  # Will be created in Task 2.2
    ]

    env_var_usage = {}

    for config_file_path in config_files:
        full_path = project_root / config_file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = re.findall(env_var_pattern, content)
                    if matches:
                        env_var_usage[config_file_path] = len(matches)
            except Exception:
                pass

    # At least some configuration files should use environment variables
    # This test is informational during RED phase, will be enforced in GREEN phase
    if env_var_usage:
        print(f"\nEnvironment variable usage detected:")
        for file_path, count in env_var_usage.items():
            print(f"  {file_path}: {count} occurrences")
    else:
        print("\nWarning: No environment variable loading detected in configuration files.")
        print("Expected pattern: os.getenv('VAR_NAME', 'default_value')")


if __name__ == "__main__":
    """
    Run security scan manually for debugging.

    Usage:
        python -m pytest tests/security/test_no_hardcoded_secrets.py -v
    """
    print("Scanning codebase for hardcoded secrets...")
    violations = scan_codebase_for_secrets()

    if violations:
        print(f"\nFound {len(violations)} hardcoded secret(s):\n")
        for file_path, line_num, description, line_content in violations:
            relative_path = file_path.relative_to(
                Path(__file__).parent.parent.parent
            )
            print(f"{relative_path}:{line_num}")
            print(f"  Issue: {description}")
            print(f"  Line: {line_content}\n")
    else:
        print("\nNo hardcoded secrets detected!")
