"""
Test Docker lifecycle management: container start, execution, stop, cleanup.

This test module validates Requirement 1 (Basic Docker Sandbox Functionality):
- Container starts within 10 seconds
- Strategy executes successfully
- Container terminates within 5 seconds
- Concurrent execution without interference

Test Reference: docker-sandbox-integration-testing spec, Task 1.1
Coverage Target: DockerExecutor lifecycle methods
"""

import pytest
import time
import concurrent.futures
from pathlib import Path

from src.sandbox.docker_executor import DockerExecutor, DOCKER_AVAILABLE
from src.sandbox.docker_config import DockerConfig


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason="Docker SDK not available. Install with: pip install docker"
)


@pytest.fixture
def docker_config():
    """Create test Docker configuration with minimal timeouts."""
    config = DockerConfig.from_yaml()
    config.enabled = True
    config.timeout_seconds = 60  # 60s timeout for tests
    config.memory_limit = "2g"
    config.cpu_limit = 0.5
    return config


@pytest.fixture
def docker_executor(docker_config):
    """Create DockerExecutor instance for tests."""
    executor = DockerExecutor(docker_config)
    yield executor
    # Cleanup after tests
    executor.cleanup_all()


class TestContainerLifecycle:
    """Test basic container lifecycle: start, execute, stop."""

    def test_container_starts_within_10_seconds(self, docker_executor):
        """
        Test: Container starts within 10 seconds
        Requirement: 1.1 - WHEN a strategy code is submitted
                          THEN the Docker container SHALL start within 10 seconds
        """
        # Use pure Python code (no pandas dependency for basic lifecycle test)
        code = """
# Simple strategy simulation
stocks = [{'ticker': '2330.TW', 'position': 1.0}]
signal = stocks[0]
print(f"Signal generated: {signal}")
"""

        start_time = time.time()
        result = docker_executor.execute(code, validate=True)
        startup_time = time.time() - start_time

        # Assert container started and executed
        assert result['success'] is True, f"Execution failed: {result.get('error')}"
        assert result['container_id'] is not None, "Container ID not set"

        # Assert startup within 10 seconds
        assert startup_time < 10.0, (
            f"Container startup + execution took {startup_time:.2f}s, expected <10s. "
            f"This indicates slow container creation."
        )

    def test_strategy_executes_successfully(self, docker_executor):
        """
        Test: Strategy executes and returns results
        Requirement: 1.2 - WHEN a container is started
                          THEN the system SHALL execute the strategy and collect results successfully
        """
        code = """
# Simulate strategy execution with pure Python
stocks = [
    {'ticker': '2330.TW', 'price': 500.0, 'signal': 1.0},
    {'ticker': '2317.TW', 'price': 100.0, 'signal': -1.0},
    {'ticker': '2454.TW', 'price': 200.0, 'signal': 0.0}
]

# Filter signals
signals = [s for s in stocks if s['signal'] != 0]
print(f"Generated {len(signals)} signals")
"""

        result = docker_executor.execute(code, validate=True)

        # Assert successful execution
        assert result['success'] is True, f"Execution failed: {result.get('error')}"
        assert result['validated'] is True, "Code validation not performed"
        assert result['execution_time'] > 0, "Execution time not recorded"

    def test_container_terminates_within_5_seconds(self, docker_executor):
        """
        Test: Container terminates cleanly within 5 seconds
        Requirement: 1.3 - WHEN strategy execution completes
                          THEN the container SHALL terminate cleanly within 5 seconds
        """
        code = """
# Simple strategy
signal = {'ticker': '2330.TW', 'position': 1.0}
print(f"Signal: {signal}")
"""

        # Execute strategy
        result = docker_executor.execute(code, validate=True)
        assert result['success'] is True, f"Execution failed: {result.get('error')}"

        container_id = result['container_id']

        # Measure cleanup time
        cleanup_start = time.time()
        cleanup_success = docker_executor._cleanup_container(container_id)
        cleanup_time = time.time() - cleanup_start

        # Assert cleanup succeeded within 5 seconds
        assert cleanup_success is True, "Container cleanup failed"
        assert cleanup_time < 5.0, (
            f"Container cleanup took {cleanup_time:.2f}s, expected <5s"
        )

    def test_container_cleanup_on_failure(self, docker_executor):
        """
        Test: Container cleanup even on execution failure
        Requirement: 1.4 - WHEN a container fails
                          THEN the system SHALL log the error and return a meaningful failure message
        """
        # Code that will fail validation
        invalid_code = """
import os
os.system('echo hacked')  # Blocked by AST validator
"""

        result = docker_executor.execute(invalid_code, validate=True)

        # Assert execution failed
        assert result['success'] is False, "Validation should have failed"
        assert 'Security validation failed' in result['error'], (
            f"Expected security error, got: {result['error']}"
        )

        # Assert cleanup was performed (no container created, so cleanup_success=True)
        assert result['cleanup_success'] is True, "Cleanup flag not set correctly"


class TestConcurrentExecution:
    """Test concurrent container execution without interference."""

    def test_concurrent_5_containers(self, docker_executor):
        """
        Test: 5 concurrent containers execute without interference
        Requirement: 1.5 - IF multiple strategies are submitted concurrently
                          THEN each SHALL execute in isolated containers without interference
        """
        # Create 5 different strategies with pure Python
        strategies = [
            f"""
import time
# Strategy {i}
signal = {{'ticker': 'TST{i}.TW', 'position': {i * 0.1}}}
print(f"Strategy {i}: {{signal}}")
"""
            for i in range(1, 6)
        ]

        # Execute concurrently using ThreadPoolExecutor
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(docker_executor.execute, code, None, True)
                for code in strategies
            ]

            # Collect results
            results = [future.result() for future in futures]

        total_time = time.time() - start_time

        # Assert all executions succeeded
        for i, result in enumerate(results, 1):
            assert result['success'] is True, (
                f"Strategy {i} failed: {result.get('error')}"
            )
            assert result['container_id'] is not None, (
                f"Strategy {i} missing container ID"
            )

        # Assert all container IDs are unique (no interference)
        container_ids = [r['container_id'] for r in results]
        assert len(set(container_ids)) == 5, (
            "Container IDs not unique - possible interference"
        )

        # Assert reasonable parallel execution time
        # 5 containers in parallel should not take 5x serial time
        # Allow 3x overhead as upper bound (expect better on multicore)
        avg_serial_time = sum(r['execution_time'] for r in results) / len(results)
        assert total_time < avg_serial_time * 3, (
            f"Parallel execution took {total_time:.2f}s, "
            f"expected < {avg_serial_time * 3:.2f}s (3x average serial time)"
        )

    def test_concurrent_execution_isolation(self, docker_executor):
        """
        Test: Concurrent containers do not share state
        Requirement: Container isolation guarantee

        Note: This test disables AST validation to test Docker-level isolation features.
        In production, AST validation would block file operations, but we want to verify
        that containers have isolated filesystems at the Docker level.
        """
        # Strategy that modifies /tmp (only tmpfs should be writable)
        code_template = """
import os

# Try to write to /tmp (should succeed, but isolated)
tmp_file = '/tmp/test_{}.txt'
with open(tmp_file, 'w') as f:
    f.write('container_{}')

# Verify file exists in this container
assert os.path.exists(tmp_file), "Failed to write to /tmp"

signal = {{'ticker': 'TST{}.TW', 'position': 1.0}}
print(f"Container {} wrote to {{tmp_file}}")
"""

        strategies = [code_template.format(i, i, i, i) for i in range(1, 4)]

        # Execute concurrently with validation disabled to test Docker isolation
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(docker_executor.execute, code, None, False)  # validate=False
                for code in strategies
            ]
            results = [future.result() for future in futures]

        # Assert all succeeded (each wrote to their own /tmp)
        for i, result in enumerate(results, 1):
            assert result['success'] is True, (
                f"Strategy {i} failed: {result.get('error')}. "
                f"Containers should have isolated /tmp via tmpfs."
            )


class TestCleanupGuarantee:
    """Test guaranteed container cleanup under various failure modes."""

    def test_cleanup_all_containers(self, docker_executor):
        """
        Test: execute() automatically cleans up containers
        Requirement: 100% cleanup success rate

        Note: DockerExecutor automatically cleans up containers in execute() finally block.
        This test verifies that after execution, no containers remain tracked.
        """
        # Execute multiple strategies with pure Python
        codes = [
            f"signal = {{'value': {i}}}; print(f'Signal: {{signal}}')"
            for i in range(3)
        ]

        results = [docker_executor.execute(code, validate=True) for code in codes]

        # Verify all containers were created successfully
        container_ids = [r['container_id'] for r in results if r['success']]
        assert len(container_ids) == 3, f"Expected 3 containers, got {len(container_ids)}"

        # Verify all containers were cleaned up during execution
        for i, result in enumerate(results):
            assert result['cleanup_success'] is True, (
                f"Container {i} cleanup failed. "
                f"DockerExecutor should automatically cleanup in execute() finally block."
            )

        # Verify no containers remain tracked
        assert len(docker_executor._active_containers) == 0, (
            f"Found {len(docker_executor._active_containers)} tracked containers, expected 0. "
            f"All containers should be cleaned up after execute()."
        )

    def test_cleanup_on_timeout(self, docker_executor):
        """
        Test: Container cleanup even on timeout
        Requirement: Zero data loss via fallback
        """
        # Code that will timeout (sleep longer than timeout)
        timeout_code = """
import time
time.sleep(120)  # Will exceed 60s timeout
"""

        result = docker_executor.execute(timeout_code, timeout=5, validate=True)

        # Assert timeout occurred
        assert result['success'] is False, "Expected timeout failure"
        assert 'timeout' in result['error'].lower() or 'time' in result['error'].lower(), (
            f"Expected timeout error, got: {result['error']}"
        )

        # Assert cleanup was performed
        assert result['cleanup_success'] is True, (
            "Container cleanup failed after timeout"
        )


class TestPerformanceBaseline:
    """Establish performance baseline for container lifecycle."""

    def test_measure_container_startup_time(self, docker_executor):
        """
        Benchmark: Measure container startup time for baseline
        Target: <10 seconds per container
        """
        measurements = []

        for i in range(3):
            code = f"""
# Iteration {i}
signal = {{'iteration': {i}}}
print(f"Completed iteration {{signal['iteration']}}")
"""
            start = time.time()
            result = docker_executor.execute(code, validate=True)
            elapsed = time.time() - start

            assert result['success'] is True, f"Iteration {i} failed"
            measurements.append(elapsed)

        avg_time = sum(measurements) / len(measurements)
        max_time = max(measurements)

        print(f"\nContainer Lifecycle Baseline:")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Maximum: {max_time:.2f}s")
        print(f"  Measurements: {[f'{t:.2f}s' for t in measurements]}")

        # Assert performance target met
        assert avg_time < 10.0, (
            f"Average container lifecycle {avg_time:.2f}s exceeds 10s target"
        )
        assert max_time < 15.0, (
            f"Maximum container lifecycle {max_time:.2f}s significantly exceeds target"
        )
