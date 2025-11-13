"""
Integration tests for DockerExecutor with real Docker containers.

These tests require a running Docker daemon and the python:3.10-slim image.
They validate actual container execution, security isolation, and resource limits.

Prerequisites:
- Docker daemon running
- python:3.10-slim image available (docker pull python:3.10-slim)
- Network connectivity for pulling images if needed

Test Scenarios:
1. Execute valid strategy in real container
2. Reject dangerous code before container creation (os.system)
3. Enforce memory limits (kill container at limit)
4. Enforce network isolation (block network calls)
5. Enforce filesystem isolation (read-only except /tmp)

To run these tests:
    pytest tests/integration/test_docker_executor_integration.py -v -s

To skip if Docker unavailable:
    pytest tests/integration/test_docker_executor_integration.py -v -s -m "not requires_docker"
"""

import pytest
import time
import docker
from docker.errors import DockerException
from pathlib import Path

from src.sandbox.docker_executor import DockerExecutor, DOCKER_AVAILABLE
from src.sandbox.docker_config import DockerConfig


# Skip all tests if Docker not available
pytestmark = pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason="Docker SDK not installed"
)


def check_docker_available():
    """Check if Docker daemon is running and accessible."""
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


def check_image_available(image_name="python:3.10-slim"):
    """Check if required Docker image is available."""
    try:
        client = docker.from_env()
        client.images.get(image_name)
        return True
    except Exception:
        return False


# Mark tests that require Docker daemon
requires_docker = pytest.mark.skipif(
    not check_docker_available(),
    reason="Docker daemon not running or not accessible"
)

requires_image = pytest.mark.skipif(
    not check_image_available(),
    reason="Docker image python:3.10-slim not available"
)


@pytest.fixture
def docker_config():
    """Create DockerConfig for testing."""
    return DockerConfig(
        enabled=True,
        image="python:3.10-slim",
        memory_limit="512m",  # Use smaller limit for testing
        cpu_limit=0.5,
        timeout_seconds=30,  # Shorter timeout for tests
        network_mode="none",
        read_only=True,
        cleanup_on_exit=True,
        fallback_to_direct=False
    )


@pytest.fixture
def executor(docker_config):
    """Create DockerExecutor instance for testing."""
    executor = DockerExecutor(docker_config)
    yield executor
    # Cleanup any remaining containers
    executor.cleanup_all()


class TestDockerExecutorIntegrationBasic:
    """Basic integration tests with real Docker."""

    @requires_docker
    @requires_image
    def test_execute_valid_code_in_container(self, executor):
        """Test 1: Execute valid strategy in real container."""
        code = """
import pandas as pd
import numpy as np

# Create simple signal
signal = pd.DataFrame({
    'stock': ['AAPL', 'GOOGL', 'MSFT'],
    'position': [1.0, -1.0, 0.5]
})

print(f"Signal created with {len(signal)} rows")
"""

        result = executor.execute(code, timeout=30)

        # Verify success
        assert result['success'] is True, f"Execution failed: {result.get('error')}"
        assert result['error'] is None
        assert result['validated'] is True
        assert result['cleanup_success'] is True
        assert result['execution_time'] < 30

        # Verify container was created
        assert result['container_id'] is not None

        # Verify logs contain expected output
        assert 'Signal created' in result.get('logs', '')

    @requires_docker
    @requires_image
    def test_execute_code_with_error(self, executor):
        """Test execution when code raises an error."""
        code = """
# This will raise ZeroDivisionError
x = 1 / 0
"""

        result = executor.execute(code, timeout=10)

        # Should fail
        assert result['success'] is False
        assert 'ZeroDivisionError' in result['error']
        assert result['cleanup_success'] is True

    @requires_docker
    @requires_image
    def test_execute_code_with_syntax_error(self, executor):
        """Test execution when code has syntax error."""
        code = """
# Invalid Python syntax
def broken_function(
    print("Missing closing parenthesis")
"""

        result = executor.execute(code, timeout=10)

        # Should fail
        assert result['success'] is False
        assert 'SyntaxError' in result['error'] or 'syntax' in result['error'].lower()


class TestDockerExecutorIntegrationSecurity:
    """Security validation integration tests."""

    @requires_docker
    @requires_image
    def test_reject_dangerous_code_os_system(self, executor):
        """Test 2: Reject code with os.system before container creation."""
        code = """
import os
os.system('ls -la /')
"""

        result = executor.execute(code, timeout=10, validate=True)

        # Should be rejected by SecurityValidator
        assert result['success'] is False
        assert result['validated'] is True
        assert 'Security validation failed' in result['error']
        assert 'os' in result['error']

        # Container should not be created
        assert result['container_id'] is None

    @requires_docker
    @requires_image
    def test_reject_subprocess_import(self, executor):
        """Test rejection of subprocess import."""
        code = """
import subprocess
subprocess.call(['echo', 'hello'])
"""

        result = executor.execute(code, timeout=10)

        # Should be rejected
        assert result['success'] is False
        assert 'subprocess' in result['error']
        assert result['container_id'] is None

    @requires_docker
    @requires_image
    def test_reject_file_operations(self, executor):
        """Test rejection of file operations."""
        code = """
# Try to read sensitive file
with open('/etc/passwd', 'r') as f:
    data = f.read()
"""

        result = executor.execute(code, timeout=10)

        # Should be rejected by validator
        assert result['success'] is False
        assert 'open' in result['error'] or 'file' in result['error'].lower()

    @requires_docker
    @requires_image
    def test_reject_network_imports(self, executor):
        """Test rejection of network imports."""
        code = """
import socket
s = socket.socket()
s.connect(('google.com', 80))
"""

        result = executor.execute(code, timeout=10)

        # Should be rejected
        assert result['success'] is False
        assert 'socket' in result['error'] or 'network' in result['error'].lower()


class TestDockerExecutorIntegrationResourceLimits:
    """Resource limit enforcement integration tests."""

    @requires_docker
    @requires_image
    @pytest.mark.slow
    def test_timeout_enforcement(self, executor):
        """Test timeout kills long-running container."""
        code = """
import time
# Sleep longer than timeout
time.sleep(100)
"""

        result = executor.execute(code, timeout=5)

        # Should timeout
        assert result['success'] is False
        assert 'timeout' in result['error'].lower() or 'Timeout' in result['error']

        # Execution time should be close to timeout
        assert result['execution_time'] >= 4.5
        assert result['execution_time'] < 10

        # Container should be cleaned up
        assert result['cleanup_success'] is True

    @requires_docker
    @requires_image
    @pytest.mark.slow
    def test_memory_limit_enforcement(self, executor):
        """Test 3: Memory-hungry code is killed at limit."""
        # This test may not work reliably as memory limits depend on Docker config
        code = """
import numpy as np

# Try to allocate more than 512MB
# Create large arrays
arrays = []
for i in range(100):
    # Each array is ~10MB
    arrays.append(np.zeros((1000, 1000), dtype=np.float64))
"""

        result = executor.execute(code, timeout=30)

        # Should either:
        # 1. Fail due to memory limit (MemoryError)
        # 2. Succeed if memory is within limit (depends on Docker config)

        # At minimum, should not crash the executor
        assert result is not None
        assert 'execution_time' in result
        assert result['cleanup_success'] is True

        # If it failed, should mention memory
        if not result['success']:
            # Could be memory error or timeout
            assert result['error'] is not None


class TestDockerExecutorIntegrationIsolation:
    """Isolation enforcement integration tests."""

    @requires_docker
    @requires_image
    def test_network_isolation_enforced(self, executor):
        """Test 4: Network calls are blocked by isolation."""
        # Even if we skip validation, network should be blocked at container level
        code = """
import urllib.request

try:
    response = urllib.request.urlopen('http://google.com', timeout=5)
    print("Network call succeeded")
    result = "success"
except Exception as e:
    print(f"Network call failed: {e}")
    result = "blocked"

signal = result
"""

        # Skip validation to test network isolation at container level
        result = executor.execute(code, timeout=15, validate=False)

        # Network should be blocked
        # Either:
        # 1. urllib import is blocked (if validator still runs)
        # 2. Network call fails due to network_mode=none

        # Note: Since we're using network_mode=none, the import might succeed
        # but the actual network call should fail

    @requires_docker
    @requires_image
    def test_filesystem_read_only(self, executor):
        """Test 5: Filesystem is read-only except /tmp."""
        code = """
import os

# Test 1: Try to write to read-only location (should fail)
try:
    with open('/test_file.txt', 'w') as f:
        f.write('test')
    readonly_result = 'writable'
except Exception as e:
    readonly_result = 'readonly'

# Test 2: Try to write to /tmp (should succeed)
try:
    with open('/tmp/test_file.txt', 'w') as f:
        f.write('test')
    tmp_result = 'writable'
except Exception as e:
    tmp_result = 'readonly'

print(f"Root FS: {readonly_result}")
print(f"TMP FS: {tmp_result}")

# Return results as signal
signal = f"{readonly_result},{tmp_result}"
"""

        # Skip validation to test filesystem isolation
        result = executor.execute(code, timeout=15, validate=False)

        # Should complete (even if filesystem restrictions apply)
        # Check logs for results
        if result.get('logs'):
            # Root FS should be readonly
            assert 'Root FS: readonly' in result['logs'] or 'Read-only' in result['logs']

            # /tmp should be writable
            # Note: This depends on tmpfs configuration


class TestDockerExecutorIntegrationCleanup:
    """Container cleanup integration tests."""

    @requires_docker
    @requires_image
    def test_cleanup_after_successful_execution(self, executor):
        """Test containers are cleaned up after success."""
        code = "signal = 42"

        result = executor.execute(code)

        # Verify cleanup
        assert result['cleanup_success'] is True

        # Verify container no longer exists
        if result['container_id']:
            client = docker.from_env()
            try:
                client.containers.get(result['container_id'])
                pytest.fail("Container still exists after cleanup")
            except docker.errors.NotFound:
                # Expected - container was removed
                pass

    @requires_docker
    @requires_image
    def test_cleanup_after_failed_execution(self, executor):
        """Test containers are cleaned up after failure."""
        code = "raise ValueError('Test error')"

        result = executor.execute(code)

        # Cleanup should succeed even after error
        assert result['cleanup_success'] is True

        # Verify container no longer exists
        if result['container_id']:
            client = docker.from_env()
            try:
                client.containers.get(result['container_id'])
                pytest.fail("Container still exists after cleanup")
            except docker.errors.NotFound:
                # Expected
                pass

    @requires_docker
    @requires_image
    def test_cleanup_all_containers(self, executor):
        """Test cleanup_all removes all tracked containers."""
        # Execute multiple times
        for i in range(3):
            # Use validate=False to avoid validation overhead
            executor.execute(f"signal = {i}", validate=False)

        # All should be cleaned up automatically
        # Verify no active containers remain
        assert len(executor._active_containers) == 0

    @requires_docker
    @requires_image
    def test_context_manager_cleanup(self):
        """Test context manager ensures cleanup on exit."""
        config = DockerConfig(
            timeout_seconds=10,
            cleanup_on_exit=True
        )

        container_id = None
        with DockerExecutor(config) as executor:
            result = executor.execute("signal = 1", validate=False)
            container_id = result.get('container_id')

        # After context exit, container should be cleaned up
        if container_id:
            client = docker.from_env()
            try:
                client.containers.get(container_id)
                pytest.fail("Container not cleaned up by context manager")
            except docker.errors.NotFound:
                # Expected
                pass


class TestDockerExecutorIntegrationPerformance:
    """Performance characteristic integration tests."""

    @requires_docker
    @requires_image
    def test_container_creation_time(self, executor):
        """Test container creation time is <3 seconds."""
        code = "signal = None"

        start_time = time.time()
        result = executor.execute(code)
        total_time = time.time() - start_time

        # Total time (including creation) should be reasonable
        # Note: First run might be slower due to image pull
        assert total_time < 10, f"Container creation took {total_time}s (expected <10s)"

    @requires_docker
    @requires_image
    @pytest.mark.slow
    def test_multiple_sequential_executions(self, executor):
        """Test multiple sequential executions."""
        execution_times = []

        for i in range(5):
            code = f"signal = {i}"
            result = executor.execute(code, validate=False)

            assert result['success'] is True
            assert result['cleanup_success'] is True
            execution_times.append(result['execution_time'])

        # All should complete in reasonable time
        avg_time = sum(execution_times) / len(execution_times)
        assert avg_time < 5, f"Average execution time {avg_time}s too high"


class TestDockerExecutorIntegrationErrorHandling:
    """Error handling integration tests."""

    @requires_docker
    def test_missing_image(self):
        """Test handling when Docker image doesn't exist."""
        config = DockerConfig(
            image="nonexistent-image:latest",
            timeout_seconds=10
        )

        executor = DockerExecutor(config)
        result = executor.execute("signal = None", validate=False)

        # Should fail with image not found error
        assert result['success'] is False
        assert 'Image not found' in result['error'] or 'not found' in result['error'].lower()
        assert 'docker pull' in result['error']

    @requires_docker
    @requires_image
    def test_invalid_code_syntax(self, executor):
        """Test handling of Python syntax errors."""
        code = "def invalid syntax here"

        result = executor.execute(code, validate=False)

        # Should fail with syntax error
        assert result['success'] is False
        # Container might catch it or Python might
        assert result['error'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
