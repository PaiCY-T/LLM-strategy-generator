#!/usr/bin/env python3
"""Docker Execution Test for Week 3.2.2

Tests Docker sandbox execution to verify:
1. Docker image build succeeds
2. Strategy execution works in Docker
3. Result parsing from container logs
4. Error handling and cleanup

Usage:
    python tests/docker/test_docker_execution.py
"""

import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_simple_execution():
    """Test simple Python code execution in Docker."""
    print("\n" + "=" * 70)
    print("TEST 1: Simple Python Execution")
    print("=" * 70)

    config = DockerConfig.from_yaml()
    executor = DockerExecutor(config=config)

    # Simple test code
    code = """
import json
print("__SIGNAL_JSON_START__")
print(json.dumps({"test": "success", "value": 42}))
print("__SIGNAL_JSON_END__")
"""

    result = executor.execute(code=code, timeout=30, validate=True)

    print(f"✓ Execution completed")
    print(f"  - Success: {result['success']}")
    print(f"  - Signal: {result.get('signal')}")
    print(f"  - Execution time: {result.get('execution_time', 0):.2f}s")
    print(f"  - Validated: {result.get('validated', False)}")
    print(f"  - Cleanup: {result.get('cleanup_success', False)}")

    assert result['success'], f"Execution failed: {result.get('error')}"
    assert result['signal'] == {"test": "success", "value": 42}, "Signal mismatch"
    assert result['validated'], "Code was not validated"
    assert result['cleanup_success'], "Container cleanup failed"

    print("✓ TEST 1 PASSED")
    return True


def test_pandas_execution():
    """Test pandas/numpy execution in Docker."""
    print("\n" + "=" * 70)
    print("TEST 2: Pandas/Numpy Execution")
    print("=" * 70)

    config = DockerConfig.from_yaml()
    executor = DockerExecutor(config=config)

    # Test code with pandas and numpy
    code = """
import pandas as pd
import numpy as np
import json

# Create DataFrame
df = pd.DataFrame({
    'A': [1, 2, 3],
    'B': [4, 5, 6]
})

# Calculate mean
mean_a = float(df['A'].mean())

# Output signal
signal = {
    "rows": len(df),
    "mean_a": mean_a,
    "sum_b": int(df['B'].sum())
}

print("__SIGNAL_JSON_START__")
print(json.dumps(signal))
print("__SIGNAL_JSON_END__")
"""

    result = executor.execute(code=code, timeout=60, validate=True)

    print(f"✓ Execution completed")
    print(f"  - Success: {result['success']}")
    print(f"  - Signal: {result.get('signal')}")
    print(f"  - Execution time: {result.get('execution_time', 0):.2f}s")

    assert result['success'], f"Execution failed: {result.get('error')}"
    assert result['signal']['rows'] == 3, "Incorrect row count"
    assert result['signal']['mean_a'] == 2.0, "Incorrect mean"
    assert result['signal']['sum_b'] == 15, "Incorrect sum"

    print("✓ TEST 2 PASSED")
    return True


def test_error_handling():
    """Test error handling for invalid code."""
    print("\n" + "=" * 70)
    print("TEST 3: Error Handling")
    print("=" * 70)

    config = DockerConfig.from_yaml()
    executor = DockerExecutor(config=config)

    # Code with syntax error
    code = """
import json
# Intentional syntax error
print("This will fail"
"""

    result = executor.execute(code=code, timeout=30, validate=True)

    print(f"✓ Execution completed")
    print(f"  - Success: {result['success']}")
    print(f"  - Error: {result.get('error', 'N/A')[:100]}")
    print(f"  - Cleanup: {result.get('cleanup_success', False)}")

    assert not result['success'], "Should have failed with syntax error"
    assert result.get('error'), "Should have error message"
    assert result['cleanup_success'], "Container cleanup should still succeed"

    print("✓ TEST 3 PASSED")
    return True


def test_security_validation():
    """Test security validator blocks dangerous code."""
    print("\n" + "=" * 70)
    print("TEST 4: Security Validation")
    print("=" * 70)

    config = DockerConfig.from_yaml()
    executor = DockerExecutor(config=config)

    # Dangerous code (file system access)
    code = """
import os
os.system("rm -rf /")
"""

    result = executor.execute(code=code, timeout=30, validate=True)

    print(f"✓ Validation completed")
    print(f"  - Success: {result['success']}")
    print(f"  - Error: {result.get('error', 'N/A')[:100]}")
    print(f"  - Validated: {result.get('validated', False)}")

    assert not result['success'], "Should have failed security validation"
    assert "Security validation failed" in result.get('error', ''), "Should mention validation failure"
    assert result['validated'], "Validation should have run"

    print("✓ TEST 4 PASSED")
    return True


def main():
    """Run all Docker tests."""
    print("\n" + "=" * 70)
    print("DOCKER EXECUTION TEST SUITE - Week 3.2.2")
    print("=" * 70)
    print("Testing Docker sandbox execution infrastructure...")
    print()

    try:
        # Check Docker availability
        config = DockerConfig.from_yaml()
        if not config.enabled:
            print("❌ Docker sandbox is disabled in config")
            print("   Set docker.enabled=true in config/docker_config.yaml")
            return False

        # Run tests
        tests = [
            ("Simple Execution", test_simple_execution),
            ("Pandas Execution", test_pandas_execution),
            ("Error Handling", test_error_handling),
            ("Security Validation", test_security_validation),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
            except AssertionError as e:
                print(f"\n❌ {test_name} FAILED: {e}")
                failed += 1
            except Exception as e:
                print(f"\n❌ {test_name} ERROR: {e}")
                failed += 1

        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total: {len(tests)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print()

        if failed == 0:
            print("✅ ALL TESTS PASSED - Docker sandbox is working correctly!")
            return True
        else:
            print(f"❌ {failed} TEST(S) FAILED - Please review errors above")
            return False

    except Exception as e:
        print(f"\n❌ SETUP ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
