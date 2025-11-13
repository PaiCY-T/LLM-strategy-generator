"""
Unit tests for DockerExecutor module.

This test suite validates the DockerExecutor using mocked Docker SDK.
All Docker API calls are mocked to enable testing without Docker daemon.

Test Coverage:
- Container creation with correct resource limits
- Security profile application (network, read-only FS, seccomp)
- Timeout enforcement
- Cleanup on success and failure paths
- Validation integration
- Error handling (image not found, API errors, etc.)

Coverage Target: >85%
"""

import pytest
import json
import time
import sys
from unittest.mock import Mock, MagicMock, patch, mock_open, call
from pathlib import Path

# Mock docker module at import time
mock_docker = MagicMock()
mock_docker.errors.DockerException = Exception
mock_docker.errors.APIError = Exception
mock_docker.errors.ContainerError = Exception
mock_docker.errors.ImageNotFound = Exception
sys.modules['docker'] = mock_docker
sys.modules['docker.errors'] = mock_docker.errors

from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig


class TestDockerExecutorInitialization:
    """Test DockerExecutor initialization and configuration."""

    @patch('src.sandbox.docker_executor.docker')
    def test_init_with_default_config(self, mock_docker):
        """Test initialization with default configuration."""
        # Mock Docker client
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        # Create executor
        executor = DockerExecutor()

        # Verify client initialization
        mock_docker.from_env.assert_called_once()
        mock_client.ping.assert_called_once()

        # Verify config defaults
        assert executor.config.enabled is True
        assert executor.config.memory_limit == "2g"
        assert executor.config.cpu_limit == 0.5
        assert executor.config.timeout_seconds == 600

    @patch('src.sandbox.docker_executor.docker')
    def test_init_with_custom_config(self, mock_docker):
        """Test initialization with custom configuration."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        # Custom config
        config = DockerConfig(
            memory_limit="4g",
            cpu_limit=1.0,
            timeout_seconds=300
        )

        executor = DockerExecutor(config)

        assert executor.config.memory_limit == "4g"
        assert executor.config.cpu_limit == 1.0
        assert executor.config.timeout_seconds == 300

    @patch('src.sandbox.docker_executor.docker')
    def test_init_docker_unavailable_raises_error(self, mock_docker):
        """Test initialization when Docker daemon unavailable raises RuntimeError."""
        # Mock Docker connection failure
        mock_docker.from_env.side_effect = Exception("Docker daemon not running")

        config = DockerConfig(enabled=True)

        with pytest.raises(RuntimeError) as exc_info:
            DockerExecutor(config)

        # Should raise error about Docker daemon
        assert "Docker daemon" in str(exc_info.value) or "Failed to connect" in str(exc_info.value)

    def test_init_docker_sdk_not_available(self):
        """Test initialization when Docker SDK not installed."""
        with patch('src.sandbox.docker_executor.DOCKER_AVAILABLE', False):
            config = DockerConfig(enabled=True)

            with pytest.raises(RuntimeError) as exc_info:
                DockerExecutor(config)

            assert "Docker SDK not available" in str(exc_info.value)


class TestDockerExecutorValidation:
    """Test code validation before execution."""

    @patch('src.sandbox.docker_executor.docker')
    def test_execute_with_invalid_code(self, mock_docker):
        """Test that invalid code is rejected by SecurityValidator."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        executor = DockerExecutor()

        # Dangerous code (subprocess import)
        code = "import subprocess\nsubprocess.call(['ls'])"

        result = executor.execute(code, validate=True)

        # Should fail validation
        assert result['success'] is False
        assert result['validated'] is True
        assert 'Security validation failed' in result['error']
        assert 'subprocess' in result['error']

        # Container should not be created
        mock_client.containers.create.assert_not_called()

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_execute_skip_validation(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker
    ):
        """Test execution with validation skipped."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        # Mock container
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Success"
        mock_client.containers.create.return_value = mock_container
        mock_client.containers.get.return_value = mock_container

        executor = DockerExecutor()

        # Even with dangerous code, should proceed if validation skipped
        code = "import subprocess"
        result = executor.execute(code, validate=False)

        # Validation should be skipped
        assert result['validated'] is False

        # Container should be created
        mock_client.containers.create.assert_called_once()


class TestDockerExecutorContainerCreation:
    """Test Docker container creation with correct settings."""

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_container_created_with_resource_limits(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker
    ):
        """Test container is created with correct resource limits."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False  # No seccomp profile

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        # Mock container
        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Success"
        mock_client.containers.create.return_value = mock_container

        config = DockerConfig(
            memory_limit="2g",
            cpu_limit=0.5,
            timeout_seconds=600
        )
        executor = DockerExecutor(config)

        code = "signal = None"
        result = executor.execute(code)

        # Verify container creation call
        mock_client.containers.create.assert_called_once()
        create_kwargs = mock_client.containers.create.call_args[1]

        # Check resource limits
        assert create_kwargs['mem_limit'] == "2g"
        assert create_kwargs['nano_cpus'] == int(0.5 * 1e9)
        assert create_kwargs['mem_swappiness'] == 0

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_container_created_with_security_settings(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker
    ):
        """Test container is created with security settings."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False  # No seccomp profile

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Success"
        mock_client.containers.create.return_value = mock_container

        executor = DockerExecutor()
        code = "signal = None"
        result = executor.execute(code)

        create_kwargs = mock_client.containers.create.call_args[1]

        # Check security settings
        assert create_kwargs['network_mode'] == "none"
        assert create_kwargs['read_only'] is True
        assert create_kwargs['privileged'] is False
        assert create_kwargs['cap_drop'] == ['ALL']
        assert '/tmp' in create_kwargs['tmpfs']

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('shutil.rmtree')
    def test_container_with_seccomp_profile(
        self, mock_rmtree, mock_mkdtemp, mock_docker
    ):
        """Test container uses seccomp profile when available."""
        mock_mkdtemp.return_value = '/tmp/test'

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Success"
        mock_client.containers.create.return_value = mock_container
        mock_client.containers.get.return_value = mock_container

        # Mock reading seccomp profile
        seccomp_profile = {"defaultAction": "SCMP_ACT_ERRNO"}
        seccomp_json = json.dumps(seccomp_profile)

        # Mock Path.exists to return True for seccomp file and builtins.open for reading files
        with patch('pathlib.Path.exists') as mock_exists:
            with patch('builtins.open', mock_open(read_data=seccomp_json)) as mock_file:
                mock_exists.return_value = True

                executor = DockerExecutor()
                code = "signal = None"
                result = executor.execute(code)

                create_kwargs = mock_client.containers.create.call_args[1]

                # Check seccomp in security options
                assert 'security_opt' in create_kwargs
                # Security opt should contain seccomp profile
                assert len(create_kwargs['security_opt']) > 0


class TestDockerExecutorExecution:
    """Test Docker container execution."""

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_successful_execution(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker
    ):
        """Test successful code execution."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Success"
        mock_client.containers.create.return_value = mock_container
        mock_client.containers.get.return_value = mock_container

        executor = DockerExecutor()
        code = "import pandas as pd\nsignal = pd.DataFrame()"

        result = executor.execute(code)

        # Verify success
        assert result['success'] is True
        assert result['error'] is None
        assert result['container_id'] == "abc123"
        assert result['cleanup_success'] is True

        # Verify container lifecycle
        mock_container.start.assert_called_once()
        mock_container.wait.assert_called_once()
        mock_container.remove.assert_called_once()

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_execution_with_error(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker
    ):
        """Test execution when container exits with error."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.wait.return_value = {'StatusCode': 1}
        mock_container.logs.return_value = b"ZeroDivisionError: division by zero"
        mock_client.containers.create.return_value = mock_container

        executor = DockerExecutor()
        code = "x = 1 / 0"

        result = executor.execute(code)

        # Verify failure
        assert result['success'] is False
        assert 'Container exited with code 1' in result['error']
        assert 'ZeroDivisionError' in result['error']
        assert result['cleanup_success'] is True

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_execution_timeout(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker
    ):
        """Test timeout enforcement."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "abc123"
        # Simulate timeout by raising exception
        mock_container.wait.side_effect = Exception("Timeout")
        mock_container.logs.return_value = b"Running..."
        mock_client.containers.create.return_value = mock_container

        executor = DockerExecutor()
        code = "import time\ntime.sleep(1000)"

        result = executor.execute(code, timeout=5)

        # Verify timeout handling
        assert result['success'] is False
        assert 'timeout' in result['error'].lower() or 'Timeout' in result['error']

        # Verify container stopped
        mock_container.stop.assert_called_once()

        # Verify cleanup
        assert result['cleanup_success'] is True


class TestDockerExecutorCleanup:
    """Test container cleanup mechanisms."""

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_cleanup_on_success(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker
    ):
        """Test container cleanup after successful execution."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Success"
        mock_client.containers.create.return_value = mock_container
        mock_client.containers.get.return_value = mock_container

        executor = DockerExecutor()
        result = executor.execute("signal = None")

        # Verify cleanup
        assert result['cleanup_success'] is True
        mock_container.remove.assert_called_once()

        # Verify temp directory cleanup
        mock_rmtree.assert_called_once()

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_cleanup_on_failure(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker
    ):
        """Test container cleanup after failed execution."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "abc123"
        mock_container.wait.return_value = {'StatusCode': 1}
        mock_container.logs.return_value = b"Error"
        mock_client.containers.create.return_value = mock_container
        mock_client.containers.get.return_value = mock_container

        executor = DockerExecutor()
        result = executor.execute("raise Exception('Test error')")

        # Cleanup should still succeed
        assert result['cleanup_success'] is True
        mock_container.remove.assert_called_once()

    @patch('src.sandbox.docker_executor.docker')
    def test_cleanup_with_force_remove(self, mock_docker):
        """Test cleanup falls back to force remove when normal remove fails."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "abc123"
        # Normal remove fails, force remove succeeds
        mock_container.remove.side_effect = [Exception("Container running"), None]
        mock_client.containers.get.return_value = mock_container

        executor = DockerExecutor()
        executor._active_containers = ["abc123"]

        success = executor._cleanup_container("abc123")

        # Should succeed with force remove
        assert success is True
        assert mock_container.remove.call_count == 2
        # Second call should have force=True
        assert mock_container.remove.call_args_list[1][1]['force'] is True

    @patch('src.sandbox.docker_executor.docker')
    def test_cleanup_with_kill_then_remove(self, mock_docker):
        """Test cleanup falls back to kill then remove when force remove fails."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "abc123"
        # Both remove attempts fail, kill succeeds
        mock_container.remove.side_effect = Exception("Failed")
        mock_client.containers.get.return_value = mock_container

        executor = DockerExecutor()
        executor._active_containers = ["abc123"]

        success = executor._cleanup_container("abc123")

        # Should attempt kill
        mock_container.kill.assert_called_once()

        # Final remove should be attempted
        assert mock_container.remove.call_count >= 2

    @patch('src.sandbox.docker_executor.docker')
    def test_cleanup_all_containers(self, mock_docker):
        """Test cleanup_all removes all active containers."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        # Mock multiple containers
        containers = []
        for i in range(3):
            container = MagicMock()
            container.id = f"abc{i}"
            containers.append(container)

        def get_container(container_id):
            idx = int(container_id[-1])
            return containers[idx]

        mock_client.containers.get.side_effect = get_container

        executor = DockerExecutor()
        executor._active_containers = ["abc0", "abc1", "abc2"]

        stats = executor.cleanup_all()

        # Verify all cleaned up
        assert stats['total'] == 3
        assert stats['success'] == 3
        assert stats['failed'] == 0


class TestDockerExecutorErrorHandling:
    """Test error handling for various failure scenarios."""

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_image_not_found(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker_patch
    ):
        """Test handling when Docker image not found."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False

        mock_client = MagicMock()
        mock_docker_patch.from_env.return_value = mock_client

        # Create a custom exception class that inherits from Exception
        class ImageNotFoundError(Exception):
            pass

        # Patch the ImageNotFound at the module level
        with patch('src.sandbox.docker_executor.ImageNotFound', ImageNotFoundError):
            mock_client.containers.create.side_effect = ImageNotFoundError("Image not found")

            executor = DockerExecutor()
            result = executor.execute("signal = None")

            # Should return error
            assert result['success'] is False
            assert 'image not found' in result['error'].lower()
            assert 'docker pull' in result['error']

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_general_exception_handling(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker_patch
    ):
        """Test handling of general exceptions during container creation."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False

        mock_client = MagicMock()
        mock_docker_patch.from_env.return_value = mock_client

        # Create custom exception classes that don't inherit from each other
        class ImageNotFoundError(Exception):
            pass

        class APIErrorException(Exception):
            def __init__(self, msg):
                super().__init__(msg)
                self.explanation = msg

        # Patch exceptions and raise a generic exception
        with patch('src.sandbox.docker_executor.ImageNotFound', ImageNotFoundError):
            with patch('src.sandbox.docker_executor.APIError', APIErrorException):
                mock_client.containers.create.side_effect = RuntimeError("Unexpected error")

                executor = DockerExecutor()
                result = executor.execute("signal = None")

                # Should return error via general exception handler
                assert result['success'] is False
                assert 'Container error' in result['error']
                assert 'RuntimeError' in result['error']

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_api_error(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker_patch
    ):
        """Test handling Docker API errors."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False

        mock_client = MagicMock()
        mock_docker_patch.from_env.return_value = mock_client

        # Create custom exception classes that don't inherit from each other
        class ImageNotFoundError(Exception):
            pass

        class APIErrorException(Exception):
            def __init__(self, msg):
                super().__init__(msg)
                self.explanation = msg

        # Patch both exceptions
        with patch('src.sandbox.docker_executor.ImageNotFound', ImageNotFoundError):
            with patch('src.sandbox.docker_executor.APIError', APIErrorException):
                api_error = APIErrorException("Insufficient resources")
                mock_client.containers.create.side_effect = api_error

                executor = DockerExecutor()
                result = executor.execute("signal = None")

                # Should return error
                assert result['success'] is False
                assert 'api error' in result['error'].lower()


class TestDockerExecutorContextManager:
    """Test context manager functionality."""

    @patch('src.sandbox.docker_executor.docker')
    def test_context_manager_cleanup(self, mock_docker):
        """Test context manager cleans up containers on exit."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        container = MagicMock()
        container.id = "abc123"
        mock_client.containers.get.return_value = container

        with DockerExecutor() as executor:
            executor._active_containers = ["abc123"]

        # Should cleanup on exit
        container.remove.assert_called_once()


class TestDockerExecutorOrphanedContainers:
    """Test orphaned container detection."""

    @patch('src.sandbox.docker_executor.docker')
    def test_get_orphaned_containers(self, mock_docker):
        """Test finding orphaned containers."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        # Mock containers
        orphan1 = MagicMock()
        orphan1.id = "orphan1"
        orphan1.short_id = "orp1"
        orphan1.name = "finlab_sandbox_old"
        orphan1.status = "exited"
        orphan1.attrs = {'Created': '2024-01-01'}

        active = MagicMock()
        active.id = "active1"

        mock_client.containers.list.return_value = [orphan1, active]

        executor = DockerExecutor()
        executor._active_containers = ["active1"]

        orphaned = executor.get_orphaned_containers()

        # Should find orphan1 but not active1
        assert len(orphaned) == 1
        assert orphaned[0]['id'] == "orphan1"
        assert orphaned[0]['status'] == "exited"


# Performance benchmarking helpers
class TestDockerExecutorPerformance:
    """Test performance characteristics."""

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    @patch('builtins.open', new_callable=mock_open)
    @patch('shutil.rmtree')
    @patch('pathlib.Path.exists')
    def test_execution_time_tracking(
        self, mock_exists, mock_rmtree, mock_file, mock_mkdtemp, mock_docker
    ):
        """Test execution time is accurately tracked."""
        mock_mkdtemp.return_value = '/tmp/test'
        mock_exists.return_value = False

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        mock_container = MagicMock()
        mock_container.id = "abc123"

        # Simulate 0.5 second execution
        def wait_with_delay(*args, **kwargs):
            time.sleep(0.1)
            return {'StatusCode': 0}

        mock_container.wait.side_effect = wait_with_delay
        mock_container.logs.return_value = b"Success"
        mock_client.containers.create.return_value = mock_container
        mock_client.containers.get.return_value = mock_container

        executor = DockerExecutor()
        result = executor.execute("signal = None")

        # Execution time should be > 0.1 seconds
        assert result['execution_time'] >= 0.1
        assert result['execution_time'] < 1.0  # Should not take too long

    @patch('src.sandbox.docker_executor.docker')
    @patch('tempfile.mkdtemp')
    def test_execution_exception_in_main_flow(self, mock_mkdtemp, mock_docker):
        """Test exception handling in main execute flow."""
        # Raise exception when creating temp directory
        mock_mkdtemp.side_effect = OSError("Disk full")

        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client

        executor = DockerExecutor()
        result = executor.execute("signal = None")

        # Should capture exception
        assert result['success'] is False
        assert 'Docker execution error' in result['error']
        assert 'OSError' in result['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=src.sandbox.docker_executor'])
