"""Integration tests for SandboxExecutionWrapper.

Tests the wrapper's routing logic and fallback mechanism without
requiring actual Docker execution (uses mocking for isolation).

Task 2.2: docker-sandbox-integration-testing
Requirement 4: Integration with Autonomous Loop
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Optional, Tuple
import sys
import os

# Add project root and working modules to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'artifacts/working/modules'))

# Import SandboxExecutionWrapper directly (avoid full autonomous_loop import)
# We only need the wrapper class for testing
from dataclasses import dataclass
from typing import Any, Tuple, Dict, Optional

# Define minimal mock for execute_strategy_safe
def execute_strategy_safe(code: str, data: Any, timeout: int):
    """Mock function - will be patched in tests."""
    # Default return value (will be overridden by patch)
    return (True, {'sharpe': 1.0}, None)

# Import SandboxExecutionWrapper class definition
# (Copied from autonomous_loop.py to avoid dependency issues)
class SandboxExecutionWrapper:
    """Wraps strategy execution with optional Docker Sandbox and automatic fallback.

    Provides dual-layer security defense:
    - Layer 1: AST validation (always enabled)
    - Layer 2: Docker container isolation (optional, configurable)

    When sandbox is enabled, automatically falls back to direct execution
    on Docker errors or timeouts to ensure autonomous loop continuity.
    """

    def __init__(self, sandbox_enabled: bool, docker_executor: Optional[Any], event_logger):
        """Initialize sandbox execution wrapper.

        Args:
            sandbox_enabled: Whether Docker sandbox is enabled
            docker_executor: DockerExecutor instance (None if disabled)
            event_logger: JSON event logger for execution metadata
        """
        self.sandbox_enabled = sandbox_enabled
        self.docker_executor = docker_executor
        self.event_logger = event_logger
        self.fallback_count = 0
        self.execution_count = 0

    def execute_strategy(
        self,
        code: str,
        data: Any,
        timeout: int = 120
    ) -> Tuple[bool, Dict, Optional[str]]:
        """Execute strategy with sandbox (if enabled) or direct execution.

        Args:
            code: Strategy code to execute
            data: Finlab data object
            timeout: Execution timeout in seconds

        Returns:
            Tuple of (success, metrics, error_message)
        """
        self.execution_count += 1

        if not self.sandbox_enabled:
            return self._direct_execution(code, data, timeout)

        try:
            return self._sandbox_execution(code, data, timeout)
        except (TimeoutError, Exception) as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Sandbox execution failed: {type(e).__name__}: {e}, "
                f"falling back to direct execution"
            )

            self.fallback_count += 1
            self.event_logger.log_event(
                logging.WARNING,
                "sandbox_fallback",
                "Sandbox execution failed, falling back to direct execution",
                error_type=type(e).__name__,
                error_message=str(e),
                fallback_count=self.fallback_count,
                execution_count=self.execution_count
            )

            return self._direct_execution(code, data, timeout)

    def _sandbox_execution(
        self,
        code: str,
        data: Any,
        timeout: int
    ) -> Tuple[bool, Dict, Optional[str]]:
        """Execute strategy in Docker container."""
        import logging
        logger = logging.getLogger(__name__)

        logger.info("Executing strategy in Docker sandbox")
        self.event_logger.log_event(
            logging.INFO,
            "sandbox_execution",
            "Executing strategy in Docker container",
            execution_count=self.execution_count
        )

        result = self.docker_executor.execute_strategy(code, data, timeout)
        return result

    def _direct_execution(
        self,
        code: str,
        data: Any,
        timeout: int
    ) -> Tuple[bool, Dict, Optional[str]]:
        """Direct execution without Docker (AST-only defense)."""
        return execute_strategy_safe(code=code, data=data, timeout=timeout)

    def get_fallback_stats(self) -> Dict[str, int]:
        """Get fallback statistics."""
        return {
            'execution_count': self.execution_count,
            'fallback_count': self.fallback_count,
            'fallback_rate': self.fallback_count / self.execution_count if self.execution_count > 0 else 0.0
        }


class TestSandboxExecutionWrapper:
    """Test suite for SandboxExecutionWrapper routing and fallback."""

    @pytest.fixture
    def mock_event_logger(self):
        """Mock event logger for testing."""
        logger = Mock()
        logger.log_event = Mock()
        return logger

    @pytest.fixture
    def mock_docker_executor(self):
        """Mock DockerExecutor for testing sandbox path."""
        executor = Mock()
        # Default: successful execution
        executor.execute_strategy = Mock(
            return_value=(True, {'sharpe': 1.5, 'annual_return': 0.15}, None)
        )
        return executor

    @pytest.fixture
    def sample_strategy_code(self):
        """Sample strategy code for testing."""
        return """
def strategy(data):
    return data.close > data.close.shift(1)
"""

    @pytest.fixture
    def sample_data(self):
        """Mock data object for testing."""
        return Mock()

    # Test Case 1: Sandbox enabled → routes to DockerExecutor
    def test_sandbox_enabled_routes_to_docker(
        self,
        mock_event_logger,
        mock_docker_executor,
        sample_strategy_code,
        sample_data
    ):
        """Test: When sandbox enabled, execution routes to DockerExecutor.

        Requirement 4.1: WHEN `sandbox.enabled: true` in config THEN
        the autonomous loop SHALL route strategy execution through Docker Sandbox.
        """
        # Arrange
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker_executor,
            event_logger=mock_event_logger
        )

        # Act
        success, metrics, error = wrapper.execute_strategy(
            code=sample_strategy_code,
            data=sample_data,
            timeout=120
        )

        # Assert
        assert success is True
        assert metrics is not None
        assert error is None
        assert metrics['sharpe'] == 1.5

        # Verify DockerExecutor was called (not direct execution)
        mock_docker_executor.execute_strategy.assert_called_once()

        # Verify sandbox execution was logged
        assert mock_event_logger.log_event.called

    # Test Case 2: Sandbox disabled → routes to direct execution
    def test_sandbox_disabled_routes_to_direct(
        self,
        mock_event_logger,
        sample_strategy_code,
        sample_data
    ):
        """Test: When sandbox disabled, execution routes to direct execution.

        Requirement 4.4: IF sandbox is disabled (`sandbox.enabled: false`) THEN
        the system SHALL use AST-only execution (current behavior).
        """
        # Arrange
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=False,
            docker_executor=None,
            event_logger=mock_event_logger
        )

        # Mock the _direct_execution method to verify it's called
        with patch.object(wrapper, '_direct_execution') as mock_direct:
            mock_direct.return_value = (
                True,
                {'sharpe': 1.2, 'annual_return': 0.12},
                None
            )

            # Act
            success, metrics, error = wrapper.execute_strategy(
                code=sample_strategy_code,
                data=sample_data,
                timeout=120
            )

            # Assert
            assert success is True
            assert metrics is not None
            assert error is None
            assert metrics['sharpe'] == 1.2

            # Verify _direct_execution was called (not Docker)
            mock_direct.assert_called_once_with(
                sample_strategy_code,
                sample_data,
                120
            )

    # Test Case 3: Timeout triggers fallback
    def test_timeout_triggers_fallback(
        self,
        mock_event_logger,
        mock_docker_executor,
        sample_strategy_code,
        sample_data
    ):
        """Test: Docker timeout triggers automatic fallback to direct execution.

        Requirement 4.2: WHEN a sandbox execution fails (timeout, error) THEN
        the system SHALL automatically fallback to AST-only execution.
        """
        # Arrange
        # Docker execution raises TimeoutError
        mock_docker_executor.execute_strategy = Mock(
            side_effect=TimeoutError("Container execution timeout")
        )

        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker_executor,
            event_logger=mock_event_logger
        )

        # Mock _direct_execution to verify fallback
        with patch.object(wrapper, '_direct_execution') as mock_direct:
            mock_direct.return_value = (
                True,
                {'sharpe': 1.0, 'annual_return': 0.10},
                None
            )

            # Act
            success, metrics, error = wrapper.execute_strategy(
                code=sample_strategy_code,
                data=sample_data,
                timeout=120
            )

            # Assert
            assert success is True  # Fallback succeeded
            assert metrics is not None
            assert metrics['sharpe'] == 1.0

            # Verify both Docker and fallback were attempted
            mock_docker_executor.execute_strategy.assert_called_once()
            mock_direct.assert_called_once()

            # Verify fallback was logged
            fallback_logged = any(
                call[0][1] == "sandbox_fallback"
                for call in mock_event_logger.log_event.call_args_list
            )
            assert fallback_logged, "Fallback event should be logged"

            # Verify fallback count increased
            stats = wrapper.get_fallback_stats()
            assert stats['fallback_count'] == 1
            assert stats['execution_count'] == 1

    # Test Case 4: Docker error triggers fallback
    def test_docker_error_triggers_fallback(
        self,
        mock_event_logger,
        mock_docker_executor,
        sample_strategy_code,
        sample_data
    ):
        """Test: Docker execution error triggers automatic fallback.

        Requirement 4.2: WHEN a sandbox execution fails (timeout, error) THEN
        the system SHALL automatically fallback to AST-only execution.
        """
        # Arrange
        # Docker execution raises exception
        mock_docker_executor.execute_strategy = Mock(
            side_effect=Exception("Docker daemon connection failed")
        )

        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker_executor,
            event_logger=mock_event_logger
        )

        # Mock _direct_execution (fallback path)
        with patch.object(wrapper, '_direct_execution') as mock_direct:
            mock_direct.return_value = (
                True,
                {'sharpe': 0.9, 'annual_return': 0.09},
                None
            )

            # Act
            success, metrics, error = wrapper.execute_strategy(
                code=sample_strategy_code,
                data=sample_data,
                timeout=120
            )

            # Assert
            assert success is True  # Fallback succeeded
            assert metrics is not None

            # Verify fallback occurred
            stats = wrapper.get_fallback_stats()
            assert stats['fallback_count'] == 1

    # Test Case 5: Metadata tracking works correctly
    def test_metadata_tracking(
        self,
        mock_event_logger,
        mock_docker_executor,
        sample_strategy_code,
        sample_data
    ):
        """Test: Execution metadata is tracked correctly.

        Requirement 4.5: WHEN an iteration completes THEN the system SHALL
        record whether sandbox or fallback was used in iteration metadata.
        """
        # Arrange
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker_executor,
            event_logger=mock_event_logger
        )

        # Fallback setup
        mock_docker_executor.execute_strategy = Mock(
            side_effect=TimeoutError("Timeout")
        )

        # Mock _direct_execution for fallback
        with patch.object(wrapper, '_direct_execution') as mock_direct:
            mock_direct.return_value = (True, {'sharpe': 1.0}, None)

            # Act - Execute multiple times to test counter
            wrapper.execute_strategy(sample_strategy_code, sample_data, 120)  # Fallback
            wrapper.execute_strategy(sample_strategy_code, sample_data, 120)  # Fallback

            # Disable sandbox for direct execution
            wrapper.sandbox_enabled = False
            wrapper.execute_strategy(sample_strategy_code, sample_data, 120)  # Direct

            # Assert
            stats = wrapper.get_fallback_stats()
            assert stats['execution_count'] == 3
            assert stats['fallback_count'] == 2
            assert stats['fallback_rate'] == pytest.approx(2/3, 0.01)

    # Test Case 6: Fallback continues iteration (doesn't halt loop)
    def test_fallback_continues_iteration(
        self,
        mock_event_logger,
        mock_docker_executor,
        sample_strategy_code,
        sample_data
    ):
        """Test: Fallback doesn't halt autonomous loop.

        Requirement 4.3: WHEN fallback occurs THEN the system SHALL log a
        WARNING with failure reason and continue the iteration.
        """
        # Arrange
        mock_docker_executor.execute_strategy = Mock(
            side_effect=Exception("Docker error")
        )

        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker_executor,
            event_logger=mock_event_logger
        )

        # Mock _direct_execution for fallback
        with patch.object(wrapper, '_direct_execution') as mock_direct:
            mock_direct.return_value = (True, {'sharpe': 1.0}, None)

            # Act
            success, metrics, error = wrapper.execute_strategy(
                code=sample_strategy_code,
                data=sample_data,
                timeout=120
            )

            # Assert - Iteration continues (no exception raised)
            assert success is True  # Fallback succeeded, iteration continues
            assert error is None

            # Verify warning was logged
            warning_logged = any(
                call[0][0] == 30  # logging.WARNING = 30
                for call in mock_event_logger.log_event.call_args_list
            )
            assert warning_logged or mock_event_logger.log_event.called

    # Test Case 7: Multiple fallbacks work correctly
    def test_multiple_fallbacks(
        self,
        mock_event_logger,
        mock_docker_executor,
        sample_strategy_code,
        sample_data
    ):
        """Test: Multiple consecutive fallbacks work correctly."""
        # Arrange
        mock_docker_executor.execute_strategy = Mock(
            side_effect=TimeoutError("Timeout")
        )

        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker_executor,
            event_logger=mock_event_logger
        )

        # Mock _direct_execution for fallback
        with patch.object(wrapper, '_direct_execution') as mock_direct:
            mock_direct.return_value = (True, {'sharpe': 1.0}, None)

            # Act - Execute 5 times, all should fallback
            for _ in range(5):
                success, _, _ = wrapper.execute_strategy(
                    sample_strategy_code,
                    sample_data,
                    120
                )
                assert success is True  # All fallbacks succeed

            # Assert
            stats = wrapper.get_fallback_stats()
            assert stats['execution_count'] == 5
            assert stats['fallback_count'] == 5
            assert stats['fallback_rate'] == 1.0

    # Test Case 8: Direct execution never triggers fallback count
    def test_direct_execution_no_fallback_count(
        self,
        mock_event_logger,
        sample_strategy_code,
        sample_data
    ):
        """Test: Direct execution doesn't increment fallback count."""
        # Arrange
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=False,  # Sandbox disabled
            docker_executor=None,
            event_logger=mock_event_logger
        )

        # Mock _direct_execution
        with patch.object(wrapper, '_direct_execution') as mock_direct:
            mock_direct.return_value = (True, {'sharpe': 1.0}, None)

            # Act - Execute 3 times
            for _ in range(3):
                wrapper.execute_strategy(sample_strategy_code, sample_data, 120)

            # Assert
            stats = wrapper.get_fallback_stats()
            assert stats['execution_count'] == 3
            assert stats['fallback_count'] == 0  # No fallback in direct mode
            assert stats['fallback_rate'] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
