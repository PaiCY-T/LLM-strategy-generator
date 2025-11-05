"""Integration test for f-string template evaluation before Docker execution.

This test verifies that f-string templates in data_setup are properly evaluated
before code is passed to Docker executor, ensuring no {{}} double braces remain
that would cause SyntaxError.

Integration boundary tested: Code assembly → Docker execution
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys

# Add paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "artifacts" / "working" / "modules"))


class TestFStringEvaluation:
    """
    Integration test: Verify f-string templates are evaluated before Docker execution.

    Tests the boundary between code assembly and Docker injection.
    Bug context: Bug #1 - f-string templates containing {{}} causing SyntaxError in Docker
    Fix verification: data_setup uses f-string which evaluates {{}} to {}
    """

    def test_data_setup_no_double_braces_in_assembled_code(self):
        """Verify assembled code contains single braces {}, not double braces {{}}

        This test captures the exact code sent to Docker executor and verifies
        that f-string evaluation has occurred, converting {{}} to {}.

        Failure mode: If {{}} appears in captured_code, f-string is not being evaluated
        """
        from artifacts.working.modules.autonomous_loop import SandboxExecutionWrapper

        # Create mocks
        mock_docker = Mock()
        mock_logger = Mock()

        # Capture what gets passed to Docker
        captured_code = None
        def capture_execute(code, timeout, validate):
            nonlocal captured_code
            captured_code = code
            return {'success': True, 'signal': {'sharpe_ratio': 1.0}, 'error': None}

        mock_docker.execute = capture_execute

        # Create wrapper and execute
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker,
            event_logger=mock_logger
        )

        sample_code = "position = close.is_largest(10)"
        mock_data = Mock()

        wrapper.execute_strategy(code=sample_code, data=mock_data, timeout=120)

        # INTEGRATION TEST: Verify no {{}} in assembled code
        assert captured_code is not None, "No code was passed to Docker"
        assert '{{' not in captured_code, "Found {{}} double braces - f-string not evaluated!"
        assert '}}' not in captured_code, "Found {{}} double braces - f-string not evaluated!"

        # Verify single braces ARE present (for .format() calls, dict literals, etc.)
        assert '{' in captured_code, "Should contain single braces for Python code"
        assert '}' in captured_code, "Should contain single braces for Python code"

    def test_data_setup_contains_expected_mock_structures(self):
        """Verify assembled code has proper mock data structures

        This test verifies that the assembled code contains the expected
        mock data structures and that formatting strings use single braces.

        Expected structures:
        - class Data: definition
        - def sim() function
        - data = Data() instantiation
        - signal = {} dictionary
        - STOCK_{:04d} formatting (not STOCK_{{:04d}})
        """
        from artifacts.working.modules.autonomous_loop import SandboxExecutionWrapper

        mock_docker = Mock()
        mock_logger = Mock()

        captured_code = None
        def capture_execute(code, timeout, validate):
            nonlocal captured_code
            captured_code = code
            return {'success': True, 'signal': {}, 'error': None}

        mock_docker.execute = capture_execute

        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker,
            event_logger=mock_logger
        )

        wrapper.execute_strategy(code="position = close.is_largest(10)", data=Mock(), timeout=120)

        # Verify expected structures in assembled code
        assert 'class Data:' in captured_code, "Missing Data class definition"
        assert 'def sim(' in captured_code, "Missing sim() function"
        assert 'data = Data()' in captured_code, "Missing Data instantiation"
        assert 'signal = {' in captured_code, "Missing signal dictionary"

        # Verify stock formatting is correct (single braces for .format())
        assert 'STOCK_{:04d}' in captured_code or 'STOCK_0000' in captured_code, \
            "Stock formatting should use single braces or be pre-formatted"
        assert 'STOCK_{{:04d}}' not in captured_code, "Double braces should be evaluated"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
