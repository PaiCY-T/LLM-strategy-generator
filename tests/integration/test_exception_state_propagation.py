"""Integration test for exception state propagation to enable diversity fallback.

This test verifies Bug #4 fix: Docker exceptions now set last_result = False
to enable diversity fallback activation.

Integration Boundary: Exception handling → State update
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "artifacts" / "working" / "modules"))


class TestExceptionStatePropagation:
    """
    Integration test: Verify exceptions update state for diversity fallback.

    Tests the boundary between exception handling and state propagation.
    Validates Bug #4 fix: Exception handler sets self.last_result = False
    """

    def test_docker_exception_sets_last_result_false(self):
        """Verify Docker exception sets last_result = False.

        This is the core Bug #4 fix validation:
        - Docker execution raises exception
        - Exception handler sets last_result = False
        - Diversity fallback can detect consecutive failures
        """
        from artifacts.working.modules.autonomous_loop import SandboxExecutionWrapper

        # Create mocks
        mock_docker = Mock()
        mock_logger = Mock()

        # Mock Docker to raise exception
        mock_docker.execute.side_effect = Exception("Docker execution failed")

        # Create wrapper
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker,
            event_logger=mock_logger
        )

        # Verify initial state
        assert wrapper.last_result is None, "Initial state should be None"

        # Execute strategy (should catch exception and fallback)
        mock_data = Mock()
        sample_code = "position = close.is_largest(10)"

        # This should NOT raise - should fallback to direct execution
        try:
            success, metrics, error = wrapper.execute_strategy(
                code=sample_code,
                data=mock_data,
                timeout=120
            )

            # INTEGRATION TEST: Verify last_result was set to False
            assert wrapper.last_result is False, \
                "Bug #4: last_result should be False after Docker exception (lines 157-158 of autonomous_loop.py)"

        except Exception as e:
            pytest.fail(f"Exception not caught properly: {e}")

    def test_docker_success_sets_last_result_true(self):
        """Verify Docker success sets last_result = True.

        Validates the positive case:
        - Docker execution succeeds
        - State updated to last_result = True
        - Next failure can be detected as transition
        """
        from artifacts.working.modules.autonomous_loop import SandboxExecutionWrapper

        mock_docker = Mock()
        mock_logger = Mock()

        # Mock Docker to succeed
        mock_docker.execute.return_value = {
            'success': True,
            'signal': {'sharpe_ratio': 1.5},
            'error': None
        }

        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker,
            event_logger=mock_logger
        )

        wrapper.execute_strategy(
            code="position = close.is_largest(10)",
            data=Mock(),
            timeout=120
        )

        # INTEGRATION TEST: Verify last_result = True after success
        assert wrapper.last_result is True, \
            "last_result should be True after Docker success"

    def test_fallback_count_increments_on_exception(self):
        """Verify fallback_count increments when exception occurs.

        Validates fallback tracking:
        - Docker raises TimeoutError
        - Wrapper catches and fallbacks to direct execution
        - fallback_count incremented for monitoring
        """
        from artifacts.working.modules.autonomous_loop import SandboxExecutionWrapper

        mock_docker = Mock()
        mock_logger = Mock()
        mock_docker.execute.side_effect = TimeoutError("Execution timeout")

        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker,
            event_logger=mock_logger
        )

        initial_count = wrapper.fallback_count
        wrapper.execute_strategy(
            code="position = close.is_largest(10)",
            data=Mock(),
            timeout=120
        )

        assert wrapper.fallback_count == initial_count + 1, \
            "Fallback count should increment on exception"

    def test_consecutive_exceptions_enable_diversity_fallback(self):
        """Verify consecutive Docker exceptions enable diversity fallback.

        This tests the complete integration chain:
        1. First Docker exception → last_result = False
        2. Second Docker exception → detects consecutive failures
        3. Diversity fallback condition satisfied
        """
        from artifacts.working.modules.autonomous_loop import SandboxExecutionWrapper

        mock_docker = Mock()
        mock_logger = Mock()
        mock_docker.execute.side_effect = Exception("Docker failed")

        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker,
            event_logger=mock_logger
        )

        # First exception
        wrapper.execute_strategy(
            code="position = close.is_largest(10)",
            data=Mock(),
            timeout=120
        )
        assert wrapper.last_result is False, "First exception should set last_result = False"

        # Second exception - should detect consecutive failures
        wrapper.execute_strategy(
            code="position = close.is_largest(5)",
            data=Mock(),
            timeout=120
        )
        assert wrapper.last_result is False, "Second exception should keep last_result = False"
        assert wrapper.fallback_count >= 2, "Should track multiple fallbacks"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
