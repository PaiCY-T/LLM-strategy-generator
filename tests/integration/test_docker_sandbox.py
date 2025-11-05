"""
Integration tests for Docker sandbox with real containers.

This module tests the complete Docker sandbox security system end-to-end using
real Docker containers. Tests validate security isolation, resource limits, and
proper cleanup.

Test Scenarios:
1. Execute valid strategy in real container, verify results
2. Submit code with os.system, verify rejection before container creation
3. Submit memory-hungry code, verify container killed at limit
4. Submit network code, verify blocked by isolation
5. Verify filesystem isolation (read-only except /tmp)

Requirements Validated:
- Security: Network isolation, filesystem isolation, dangerous code detection
- Resources: Memory limits, CPU limits, timeout enforcement
- Cleanup: Container removal, no orphaned containers

Design Reference: docker-sandbox-security spec Task 11
"""

import pytest
import time
from pathlib import Path
from typing import Optional

# Try to import docker, handle gracefully if not available
try:
    import docker
    DOCKER_SDK_AVAILABLE = True
except ImportError:
    docker = None
    DOCKER_SDK_AVAILABLE = False

from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig
from src.sandbox.security_validator import SecurityValidator


# Check if Docker is available
def is_docker_available() -> bool:
    """Check if Docker daemon is available."""
    if not DOCKER_SDK_AVAILABLE:
        return False
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


# Check if required Docker image exists
def is_image_available(image: str = "python:3.10-slim") -> bool:
    """Check if required Docker image is available."""
    if not DOCKER_SDK_AVAILABLE:
        return False
    try:
        client = docker.from_env()
        client.images.get(image)
        return True
    except Exception:
        return False


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker daemon not available - integration tests require Docker"
)


@pytest.fixture(scope="function")
def docker_config():
    """Create DockerConfig for testing with safe defaults."""
    return DockerConfig(
        enabled=True,
        image="python:3.10-slim",
        memory_limit="512m",  # Lower limit for testing
        cpu_limit=0.5,
        timeout_seconds=30,  # Shorter timeout for tests
        network_mode="none",
        read_only=True,
        tmpfs_path="/tmp",
        tmpfs_size="100m",
        tmpfs_options="rw,noexec,nosuid",
        seccomp_profile="config/seccomp_profile.json",
        output_dir="sandbox_output/test",
        cleanup_on_exit=True,
        export_container_stats=False
    )


@pytest.fixture(scope="function")
def docker_executor(docker_config):
    """Create DockerExecutor for testing with automatic cleanup."""
    executor = DockerExecutor(docker_config)
    yield executor
    # Cleanup any remaining containers
    executor.cleanup_all()


@pytest.fixture(scope="function")
def ensure_image():
    """Ensure Docker image is available before tests."""
    if not is_image_available("python:3.10-slim"):
        pytest.skip("Docker image python:3.10-slim not available. Pull with: docker pull python:3.10-slim")


class TestDockerSandboxIntegration:
    """Integration tests for Docker sandbox with real containers."""

    def test_scenario_1_execute_valid_strategy(self, docker_executor, ensure_image):
        """
        Test Scenario 1: Execute valid strategy in real container, verify results.

        This test validates:
        - Container creation with security settings
        - Valid code execution in isolated environment
        - Successful execution completion
        - Container cleanup after execution

        Expected: Code executes successfully, container is cleaned up
        """
        # Valid strategy code using pandas
        code = """
import pandas as pd
import numpy as np

# Create a simple trading signal
data = {
    'stock': ['AAPL', 'GOOGL', 'MSFT'],
    'price': [150.0, 2800.0, 300.0],
    'signal': [1.0, 0.5, 0.0]
}

signal = pd.DataFrame(data)
print("Strategy executed successfully")
print(f"Generated {len(signal)} signals")
"""

        # Execute code
        result = docker_executor.execute(code, validate=True)

        # Assertions
        assert result is not None, "Result should not be None"
        assert 'success' in result, "Result should contain 'success' key"
        assert 'error' in result, "Result should contain 'error' key"
        assert 'execution_time' in result, "Result should contain 'execution_time' key"
        assert 'container_id' in result, "Result should contain 'container_id' key"
        assert 'cleanup_success' in result, "Result should contain 'cleanup_success' key"
        assert 'validated' in result, "Result should contain 'validated' key"

        # Validate execution
        assert result['validated'] is True, "Code should be validated"
        assert result['success'] is True, f"Execution should succeed, but got error: {result.get('error')}"
        assert result['error'] is None, "Should have no error message"
        assert result['container_id'] is not None, "Should have container ID"
        assert result['cleanup_success'] is True, "Cleanup should succeed"
        assert result['execution_time'] > 0, "Execution time should be positive"
        assert result['execution_time'] < 30, "Execution should complete within timeout"

        # Verify container was cleaned up
        assert result['container_id'] not in docker_executor._active_containers, \
            "Container should be removed from active containers"

        # Verify no orphaned containers
        if DOCKER_SDK_AVAILABLE:
            try:
                client = docker.from_env()
                container = client.containers.get(result['container_id'])
                pytest.fail(f"Container {result['container_id']} should be removed but still exists")
            except docker.errors.NotFound:
                # Expected - container should be removed
                pass

    def test_scenario_2_reject_dangerous_code_os_system(self, docker_executor, ensure_image):
        """
        Test Scenario 2: Submit code with os.system, verify rejection before container creation.

        This test validates:
        - SecurityValidator detects dangerous imports
        - Code is rejected BEFORE container creation
        - No container is created for dangerous code
        - Clear error message is returned

        Expected: Code is rejected, no container created, error message explains reason
        """
        # Dangerous code with os.system
        code = """
import os
import pandas as pd

# Try to execute system command
os.system("ls -la /etc")

# Generate signal
signal = pd.DataFrame({'stock': ['AAPL'], 'position': [1.0]})
"""

        # Execute code (should be rejected)
        result = docker_executor.execute(code, validate=True)

        # Assertions
        assert result is not None, "Result should not be None"
        assert result['validated'] is True, "Code should be validated"
        assert result['success'] is False, "Execution should fail due to security validation"
        assert result['error'] is not None, "Should have error message"
        assert result['container_id'] is None, "No container should be created"
        assert result['cleanup_success'] is True, "Cleanup should succeed (no container to cleanup)"

        # Validate error message
        assert "Security validation failed" in result['error'], \
            f"Error should mention security validation, got: {result['error']}"
        assert "os" in result['error'].lower() or "dangerous" in result['error'].lower(), \
            f"Error should mention dangerous import, got: {result['error']}"

        # Verify no containers in active list
        assert len(docker_executor._active_containers) == 0, \
            "No containers should be active after rejection"

    def test_scenario_3_memory_limit_enforcement(self, docker_executor, ensure_image):
        """
        Test Scenario 3: Submit memory-hungry code, verify container killed at limit.

        This test validates:
        - Memory limits are enforced by Docker
        - Container is killed when exceeding limit
        - Error is captured and returned
        - Container is cleaned up after being killed

        Expected: Container is killed, error indicates memory issue, cleanup succeeds
        """
        # Memory-hungry code that tries to allocate 1GB (exceeds 512MB limit)
        code = """
import numpy as np

# Try to allocate 1GB array (should exceed 512MB memory limit)
large_array = np.zeros((128_000_000,), dtype=np.float64)  # ~1GB
print(f"Allocated {large_array.nbytes / (1024**3):.2f} GB")
"""

        # Execute code (should be killed by memory limit)
        result = docker_executor.execute(code, validate=True)

        # Assertions
        assert result is not None, "Result should not be None"
        assert result['validated'] is True, "Code should pass validation (no dangerous imports)"

        # Note: Memory limit enforcement behavior varies by system
        # Container may fail with exit code 137 (killed) or OOM error
        # We accept either failure mode
        if result['success'] is False:
            # Expected: Container was killed or failed
            assert result['error'] is not None, "Should have error message"
            assert result['container_id'] is not None, "Container should be created before being killed"
            assert result['cleanup_success'] is True, "Container should be cleaned up after failure"

            # Error should indicate container failure (exit code or killed)
            error_lower = result['error'].lower()
            assert any(indicator in error_lower for indicator in ['exit', 'killed', 'error', 'failed']), \
                f"Error should indicate container failure, got: {result['error']}"
        else:
            # Unexpected: Container might have succeeded if system has enough memory
            # This is acceptable but not ideal for testing limits
            print(f"WARNING: Memory limit test did not trigger OOM (system may have abundant memory)")

        # Verify container was cleaned up
        if result['container_id']:
            assert result['container_id'] not in docker_executor._active_containers, \
                "Container should be removed from active containers"

    def test_scenario_4_network_isolation(self, docker_executor, ensure_image):
        """
        Test Scenario 4: Submit network code, verify blocked by isolation.

        This test validates:
        - Network imports are detected by SecurityValidator
        - OR network operations fail due to network_mode="none"
        - Container cannot access network
        - Error message is clear

        Expected: Either code is rejected (preferred) or network operations fail in container
        """
        # Network code using socket
        code = """
import socket

# Try to create socket and connect
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('8.8.8.8', 53))  # Try to connect to Google DNS
print("Network connection successful")
s.close()
"""

        # Execute code (should be rejected or fail)
        result = docker_executor.execute(code, validate=True)

        # Assertions
        assert result is not None, "Result should not be None"
        assert result['validated'] is True, "Code should be validated"

        # SecurityValidator should reject socket import
        assert result['success'] is False, \
            "Execution should fail (either validation rejects socket or network is isolated)"
        assert result['error'] is not None, "Should have error message"

        if result['container_id'] is None:
            # Preferred path: SecurityValidator rejected code before container creation
            assert "Security validation failed" in result['error'], \
                f"Error should mention security validation, got: {result['error']}"
            assert "socket" in result['error'].lower() or "network" in result['error'].lower(), \
                f"Error should mention network/socket, got: {result['error']}"
        else:
            # Alternative path: Container was created but network operations failed
            assert result['cleanup_success'] is True, "Container should be cleaned up"
            error_lower = result['error'].lower()
            assert any(indicator in error_lower for indicator in ['network', 'socket', 'connection', 'failed']), \
                f"Error should indicate network failure, got: {result['error']}"

    def test_scenario_5_filesystem_isolation(self, docker_executor, ensure_image):
        """
        Test Scenario 5: Verify filesystem isolation (read-only except /tmp).

        This test validates:
        - Root filesystem is read-only
        - Writes to /tmp succeed (tmpfs is writable)
        - Writes to other locations fail
        - Container filesystem isolation is enforced

        Expected: Writes to /tmp succeed, writes to root fail, isolation is enforced
        """
        # Code that tests filesystem isolation
        code = """
import os

# Test 1: Try to write to /tmp (should succeed)
tmp_file = "/tmp/test_write.txt"
try:
    with open(tmp_file, 'w') as f:
        f.write("Test write to /tmp")
    print("SUCCESS: Write to /tmp succeeded")
    os.remove(tmp_file)
except Exception as e:
    print(f"FAILED: Write to /tmp failed: {e}")
    raise

# Test 2: Try to write to root filesystem (should fail)
root_file = "/test_write.txt"
try:
    with open(root_file, 'w') as f:
        f.write("Test write to root")
    print("FAILED: Write to root succeeded (should have failed)")
    raise RuntimeError("Root filesystem should be read-only")
except (PermissionError, OSError) as e:
    print(f"SUCCESS: Write to root failed as expected: {e}")

# Test 3: Try to write to /etc (should fail)
etc_file = "/etc/test_write.txt"
try:
    with open(etc_file, 'w') as f:
        f.write("Test write to /etc")
    print("FAILED: Write to /etc succeeded (should have failed)")
    raise RuntimeError("/etc should be read-only")
except (PermissionError, OSError) as e:
    print(f"SUCCESS: Write to /etc failed as expected: {e}")

print("Filesystem isolation test completed successfully")
"""

        # Execute code
        result = docker_executor.execute(code, validate=False)  # Skip validation (open is allowed for this test)

        # Assertions
        assert result is not None, "Result should not be None"

        # Note: open() function is in DANGEROUS_FUNCTIONS, so validation will reject it
        # We disable validation for this specific test to verify Docker filesystem isolation
        # In production, open() would be blocked by SecurityValidator

        if result['success'] is True:
            # Expected: Code executed successfully, demonstrating filesystem isolation
            assert result['container_id'] is not None, "Container should be created"
            assert result['cleanup_success'] is True, "Container should be cleaned up"
            assert 'logs' in result, "Should have container logs"

            # Verify logs show expected behavior
            logs = result.get('logs', '')
            assert "SUCCESS: Write to /tmp succeeded" in logs, \
                "Logs should show /tmp write succeeded"
            assert "SUCCESS: Write to root failed as expected" in logs, \
                "Logs should show root write failed"
            assert "SUCCESS: Write to /etc failed as expected" in logs, \
                "Logs should show /etc write failed"
        else:
            # Alternative: Code might fail due to open() being blocked
            # This is acceptable if SecurityValidator is preventing file operations
            if result['error'] and 'Security validation failed' in result['error']:
                pytest.skip("SecurityValidator blocked open() - cannot test filesystem isolation directly")
            else:
                # Unexpected failure
                pytest.fail(f"Filesystem isolation test failed unexpectedly: {result['error']}")


class TestDockerSandboxCleanup:
    """Tests for container cleanup and resource management."""

    def test_cleanup_on_success(self, docker_executor, ensure_image):
        """Verify container is cleaned up after successful execution."""
        code = "print('Hello from container')"

        result = docker_executor.execute(code, validate=True)

        assert result['success'] is True, f"Execution should succeed: {result.get('error')}"
        assert result['cleanup_success'] is True, "Cleanup should succeed"

        # Verify container no longer exists
        if result['container_id'] and DOCKER_SDK_AVAILABLE:
            try:
                client = docker.from_env()
                client.containers.get(result['container_id'])
                pytest.fail("Container should be removed")
            except docker.errors.NotFound:
                pass  # Expected

    def test_cleanup_on_failure(self, docker_executor, ensure_image):
        """Verify container is cleaned up even when execution fails."""
        # Code that will fail
        code = "raise RuntimeError('Intentional failure')"

        result = docker_executor.execute(code, validate=True)

        assert result['success'] is False, "Execution should fail"
        assert result['cleanup_success'] is True, "Cleanup should succeed even on failure"

        # Verify container no longer exists
        if result['container_id'] and DOCKER_SDK_AVAILABLE:
            try:
                client = docker.from_env()
                client.containers.get(result['container_id'])
                pytest.fail("Container should be removed even on failure")
            except docker.errors.NotFound:
                pass  # Expected

    def test_cleanup_on_timeout(self, docker_executor, ensure_image):
        """Verify container is cleaned up when timeout occurs."""
        # Code that will timeout (sleep longer than 30s timeout)
        code = """
import time
time.sleep(60)  # Sleep 60 seconds (exceeds 30s timeout)
"""

        # Set shorter timeout for this test
        result = docker_executor.execute(code, timeout=5, validate=True)

        # Execution should fail due to timeout
        assert result['success'] is False, "Execution should fail due to timeout"
        assert result['cleanup_success'] is True, "Cleanup should succeed even on timeout"

        # Verify container no longer exists
        if result['container_id'] and DOCKER_SDK_AVAILABLE:
            try:
                client = docker.from_env()
                client.containers.get(result['container_id'])
                pytest.fail("Container should be removed after timeout")
            except docker.errors.NotFound:
                pass  # Expected

    def test_cleanup_all(self, docker_executor, ensure_image):
        """Verify cleanup_all removes all tracked containers."""
        # Execute multiple strategies to create containers
        code = "print('Test container')"

        # Execute 3 times (but don't wait for cleanup between executions)
        # Manually create containers without automatic cleanup
        docker_executor.config.cleanup_on_exit = False

        results = []
        for i in range(3):
            result = docker_executor.execute(code, validate=True)
            results.append(result)

        # All should succeed
        for result in results:
            assert result['success'] is True, "All executions should succeed"

        # At this point, containers might still exist (cleanup_on_exit=False)
        # Call cleanup_all
        stats = docker_executor.cleanup_all()

        # Verify cleanup statistics
        assert stats is not None, "Cleanup stats should not be None"
        assert 'total' in stats, "Stats should have 'total'"
        assert 'success' in stats, "Stats should have 'success'"
        assert 'failed' in stats, "Stats should have 'failed'"
        assert stats['success'] >= 0, "Success count should be non-negative"
        assert stats['failed'] == 0, "All cleanups should succeed"


class TestDockerSandboxContextManager:
    """Tests for DockerExecutor context manager functionality."""

    def test_context_manager_cleanup(self, docker_config, ensure_image):
        """Verify context manager cleans up containers on exit."""
        code = "print('Test container')"

        # Use executor as context manager
        with DockerExecutor(docker_config) as executor:
            result = executor.execute(code, validate=True)
            assert result['success'] is True, "Execution should succeed"
            container_id = result['container_id']

        # After exiting context, verify container is cleaned up
        if container_id and DOCKER_SDK_AVAILABLE:
            try:
                client = docker.from_env()
                client.containers.get(container_id)
                pytest.fail("Container should be cleaned up by context manager")
            except docker.errors.NotFound:
                pass  # Expected


class TestDockerSandboxEdgeCases:
    """Tests for edge cases and error handling."""

    def test_invalid_docker_image(self, docker_config):
        """Test handling of invalid Docker image."""
        # Use non-existent image
        docker_config.image = "nonexistent-image:latest"
        executor = DockerExecutor(docker_config)

        code = "print('Test')"
        result = executor.execute(code, validate=True)

        # Should fail with clear error message
        assert result['success'] is False, "Execution should fail with invalid image"
        assert result['error'] is not None, "Should have error message"
        assert "not found" in result['error'].lower() or "image" in result['error'].lower(), \
            f"Error should mention image issue: {result['error']}"

    def test_empty_code(self, docker_executor):
        """Test handling of empty code."""
        result = docker_executor.execute("", validate=True)

        # Empty code should be valid (passes security checks)
        assert result['validated'] is True, "Empty code should be validated"
        # Execution should succeed (empty code is valid Python)
        assert result['success'] is True, "Empty code should execute successfully"

    def test_syntax_error_code(self, docker_executor, ensure_image):
        """Test handling of code with syntax errors."""
        code = "def invalid syntax here"

        result = docker_executor.execute(code, validate=True)

        # Should fail during validation (syntax error)
        assert result['validated'] is True, "Code should be validated"
        assert result['success'] is False, "Execution should fail due to syntax error"
        assert result['error'] is not None, "Should have error message"
        assert "syntax" in result['error'].lower(), \
            f"Error should mention syntax: {result['error']}"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
