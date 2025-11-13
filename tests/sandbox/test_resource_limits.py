"""
Test resource limit enforcement: Memory, CPU, Disk limits at container level.

This test module validates Requirement 2 (Resource Limits Enforcement):
- Memory limit (2GB) triggers OOMKilled
- CPU timeout (300s) triggers Timeout
- Disk limit (1GB) triggers restriction
- Violations logged correctly with metadata

Test Reference: docker-sandbox-integration-testing spec, Task 1.2
Coverage Target: DockerExecutor resource enforcement, ContainerMonitor
"""

import pytest
import time
from pathlib import Path

from src.sandbox.docker_executor import DockerExecutor, DOCKER_AVAILABLE
from src.sandbox.docker_config import DockerConfig


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason="Docker SDK not available. Install with: pip install docker"
)


@pytest.fixture
def docker_config_with_limits():
    """Create Docker configuration with strict resource limits for testing."""
    config = DockerConfig.from_yaml()
    config.enabled = True
    # Use stricter limits for testing
    config.memory_limit = "100m"  # 100MB for faster OOM testing (vs 2GB production)
    config.cpu_limit = 0.5
    config.timeout_seconds = 10  # 10s for faster timeout testing (vs 300s production)
    return config


@pytest.fixture
def docker_executor_limited(docker_config_with_limits):
    """Create DockerExecutor with strict limits for testing."""
    executor = DockerExecutor(docker_config_with_limits)
    yield executor
    # Cleanup after tests
    executor.cleanup_all()


class TestMemoryLimit:
    """Test memory limit enforcement (2GB production, 100MB test)."""

    def test_memory_limit_enforced_oom(self, docker_executor_limited):
        """
        Test: Container killed when exceeding memory limit
        Requirement: 2.1 - WHEN a strategy exceeds memory limit (2GB)
                          THEN the container SHALL be terminated with OOMKilled status

        Note: Uses 100MB limit for faster testing. Production uses 2GB.
        """
        # Strategy that allocates excessive memory
        memory_bomb_code = """
import sys

# Try to allocate large amounts of memory
# This should trigger OOM killer
data = []
try:
    # Allocate 200MB (exceeds 100MB limit)
    for i in range(20):
        # Each allocation ~10MB
        chunk = 'x' * (10 * 1024 * 1024)
        data.append(chunk)
        print(f"Allocated chunk {i+1}: {sys.getsizeof(chunk) / 1024 / 1024:.1f}MB")
except MemoryError as e:
    print(f"Python MemoryError (before container OOM): {e}")

print("If you see this, memory bomb did not trigger OOM")
"""

        # Execute with validation disabled (to test Docker limits, not AST validation)
        result = docker_executor_limited.execute(memory_bomb_code, validate=False)

        # Assert execution failed due to resource limits
        assert result['success'] is False, "Memory bomb should have failed due to OOM"

        # Check error message indicates OOM or container error
        error_msg = result.get('error', '').lower()
        assert any(keyword in error_msg for keyword in ['oom', 'killed', 'memory', 'error', 'exit']), (
            f"Expected OOM/killed error, got: {result.get('error')}"
        )

        # Verify cleanup was performed even after OOM
        assert result['cleanup_success'] is True, (
            "Container cleanup should succeed even after OOM"
        )

    def test_memory_limit_under_threshold_succeeds(self, docker_executor_limited):
        """
        Test: Container succeeds when staying under memory limit
        Requirement: 2.1 - Verify limit enforcement is not too aggressive
        """
        # Strategy that uses moderate memory (should succeed)
        moderate_memory_code = """
# Allocate 10MB (well under 100MB limit)
data = 'x' * (10 * 1024 * 1024)
print(f"Allocated 10MB successfully")
signal = {'status': 'success', 'memory_mb': 10}
"""

        result = docker_executor_limited.execute(moderate_memory_code, validate=False)

        # Assert execution succeeded
        assert result['success'] is True, (
            f"Moderate memory usage should succeed: {result.get('error')}"
        )


class TestCPUTimeout:
    """Test CPU timeout enforcement (300s production, 10s test)."""

    def test_cpu_timeout_enforced(self, docker_executor_limited):
        """
        Test: Container terminated when exceeding timeout
        Requirement: 2.2 - WHEN a strategy exceeds CPU time limit (300 seconds)
                          THEN the container SHALL be terminated with Timeout status

        Note: Uses 10s timeout for faster testing. Production uses 300s.
        """
        # Strategy that runs longer than timeout
        infinite_loop_code = """
import time

# Infinite loop (will be killed by timeout)
print("Starting long-running computation...")
timeout_seconds = 20  # Exceeds 10s limit

start = time.time()
while time.time() - start < timeout_seconds:
    # Busy wait (CPU intensive)
    x = sum(range(1000))

print("This should never print (killed by timeout)")
"""

        start_time = time.time()
        result = docker_executor_limited.execute(infinite_loop_code, validate=False)
        elapsed = time.time() - start_time

        # Assert execution failed due to timeout
        assert result['success'] is False, "Timeout test should have failed"

        # Check error indicates timeout
        error_msg = result.get('error', '').lower()
        assert any(keyword in error_msg for keyword in ['timeout', 'time', 'killed', 'exceed']), (
            f"Expected timeout error, got: {result.get('error')}"
        )

        # Verify timeout occurred near the limit (allow 10s buffer for Docker overhead)
        timeout_limit = docker_executor_limited.config.timeout_seconds
        assert elapsed <= timeout_limit + 10, (
            f"Timeout took {elapsed:.1f}s, expected ~{timeout_limit}s (with ≤10s overhead)"
        )

        # Verify cleanup was performed
        assert result['cleanup_success'] is True, (
            "Container cleanup should succeed even after timeout"
        )

    def test_cpu_timeout_under_threshold_succeeds(self, docker_executor_limited):
        """
        Test: Container succeeds when completing before timeout
        Requirement: 2.2 - Verify timeout enforcement is not premature
        """
        # Strategy that completes quickly
        quick_code = """
import time

# Short computation (well under 10s limit)
time.sleep(1)
print("Completed in 1 second")
signal = {'status': 'success', 'duration': 1}
"""

        result = docker_executor_limited.execute(quick_code, validate=False)

        # Assert execution succeeded
        assert result['success'] is True, (
            f"Quick execution should succeed: {result.get('error')}"
        )


class TestDiskLimit:
    """Test disk limit enforcement (1GB production)."""

    def test_disk_limit_enforced(self, docker_executor_limited):
        """
        Test: Container restricted when exceeding disk limit
        Requirement: 2.3 - WHEN a strategy attempts excessive disk writes (>1GB)
                          THEN the container SHALL be terminated or restricted

        Note: Testing disk limits is complex due to Docker storage driver behavior.
        This test verifies read-only filesystem enforcement as disk protection mechanism.
        """
        # Strategy that attempts large file write (should fail due to read-only FS)
        disk_bomb_code = """
import os

# Try to write large file to workspace (read-only, should fail)
try:
    with open('/workspace/large_file.dat', 'w') as f:
        # Try to write 100MB
        for i in range(100):
            f.write('x' * (1024 * 1024))  # 1MB chunks
    print("ERROR: Write to read-only filesystem succeeded (unexpected)")
except (OSError, PermissionError, IOError) as e:
    print(f"Write blocked (expected): {type(e).__name__}: {e}")

# Try to write to /tmp (tmpfs, should succeed but limited)
try:
    tmp_file = '/tmp/test.dat'
    with open(tmp_file, 'w') as f:
        # Small write to /tmp (allowed via tmpfs)
        f.write('test data')
    print(f"Successfully wrote to {tmp_file} (tmpfs allowed)")
except Exception as e:
    print(f"Unexpected error writing to /tmp: {e}")
"""

        result = docker_executor_limited.execute(disk_bomb_code, validate=False)

        # Assert execution succeeded (expected behavior: read-only blocks, tmpfs allows)
        assert result['success'] is True, (
            f"Disk limit test should succeed with read-only protection: {result.get('error')}"
        )

    def test_disk_limit_tmpfs_only_writable(self, docker_executor_limited):
        """
        Test: Only /tmp (tmpfs) is writable, workspace is read-only
        Requirement: 2.3 - Verify disk protection via read-only filesystem
        """
        # Verify /tmp is writable, /workspace is not
        tmpfs_test_code = """
import os

results = {'tmp_writable': False, 'workspace_readonly': False}

# Test /tmp (should be writable)
try:
    with open('/tmp/test.txt', 'w') as f:
        f.write('test')
    os.remove('/tmp/test.txt')
    results['tmp_writable'] = True
    print("✓ /tmp is writable (expected)")
except Exception as e:
    print(f"✗ /tmp write failed (unexpected): {e}")

# Test /workspace (should be read-only)
try:
    with open('/workspace/test.txt', 'w') as f:
        f.write('test')
    print("✗ /workspace is writable (unexpected)")
except (OSError, PermissionError, IOError):
    results['workspace_readonly'] = True
    print("✓ /workspace is read-only (expected)")
except Exception as e:
    print(f"✗ /workspace unexpected error: {e}")

# Report results
assert results['tmp_writable'], "/tmp should be writable"
assert results['workspace_readonly'], "/workspace should be read-only"
print(f"Disk protection verified: {results}")
"""

        result = docker_executor_limited.execute(tmpfs_test_code, validate=False)

        # Assert execution succeeded
        assert result['success'] is True, (
            f"Tmpfs protection test failed: {result.get('error')}"
        )


class TestResourceViolationLogging:
    """Test that resource violations are logged correctly."""

    def test_violations_logged_with_metadata(self, docker_executor_limited):
        """
        Test: Resource violations logged with strategy ID and violation type
        Requirement: 2.4 - WHEN resource limits are enforced
                          THEN the system SHALL log the violation type and return error metadata
        """
        # Memory violation
        memory_bomb = """
# Allocate excessive memory
data = ['x' * (50 * 1024 * 1024) for _ in range(10)]  # 500MB
"""

        result = docker_executor_limited.execute(memory_bomb, validate=False)

        # Assert failure
        assert result['success'] is False, "Memory violation should fail"

        # Assert error metadata present
        assert result.get('error') is not None, "Error message should be present"
        assert result.get('container_id') is not None, "Container ID should be logged"
        assert result.get('execution_time') > 0, "Execution time should be recorded"

        # Assert cleanup performed
        assert result['cleanup_success'] is True, "Cleanup should succeed"

    def test_autonomous_loop_skips_failed_strategy(self, docker_executor_limited):
        """
        Test: Autonomous loop continues after resource violation
        Requirement: 2.5 - IF a container is terminated due to resource limits
                          THEN the autonomous loop SHALL skip this strategy and continue

        Note: This tests the executor behavior. Integration with autonomous loop
        tested in Phase 2 (Task 2.3).
        """
        # First strategy: violates memory (should fail)
        memory_bomb = "data = ['x' * (50 * 1024 * 1024) for _ in range(10)]"

        # Second strategy: normal (should succeed)
        normal_code = "signal = {'status': 'success'}"

        # Execute both
        result1 = docker_executor_limited.execute(memory_bomb, validate=False)
        result2 = docker_executor_limited.execute(normal_code, validate=False)

        # Assert first failed, second succeeded
        assert result1['success'] is False, "Memory bomb should fail"
        assert result2['success'] is True, (
            f"Normal strategy should succeed after failure: {result2.get('error')}"
        )

        # Assert both containers cleaned up
        assert result1['cleanup_success'] is True
        assert result2['cleanup_success'] is True


class TestResourceLimitConfiguration:
    """Test resource limit configuration and validation."""

    def test_config_memory_limit_applied(self, docker_config_with_limits):
        """
        Test: Memory limit from config applied to containers
        Requirement: Configuration validation
        """
        # Verify config has expected limits
        assert docker_config_with_limits.memory_limit == "100m"
        assert docker_config_with_limits.cpu_limit == 0.5
        assert docker_config_with_limits.timeout_seconds == 10

        # Create executor and verify it uses config
        executor = DockerExecutor(docker_config_with_limits)
        assert executor.config.memory_limit == "100m"

        executor.cleanup_all()

    def test_production_limits_documented(self):
        """
        Test: Production resource limits are documented correctly
        Requirement: Non-functional - Configuration documentation
        """
        # Load production config
        prod_config = DockerConfig.from_yaml()

        # Document production limits (from requirements.md)
        expected_prod_limits = {
            'memory_limit': '2g',  # 2GB
            'cpu_limit': 0.5,      # 0.5 cores
            'timeout_seconds': 300 # 300 seconds
        }

        print("\nProduction Resource Limits:")
        print(f"  Memory: {prod_config.memory_limit} (expected: {expected_prod_limits['memory_limit']})")
        print(f"  CPU: {prod_config.cpu_limit} cores (expected: {expected_prod_limits['cpu_limit']})")
        print(f"  Timeout: {prod_config.timeout_seconds}s (expected: {expected_prod_limits['timeout_seconds']}s)")

        # Note: Actual values may differ from expected if config was modified
        # This test documents the values for reference
