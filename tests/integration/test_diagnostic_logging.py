"""Integration test for diagnostic logging at boundaries.

Task 4.3: Verify diagnostic logs are generated at integration boundaries
Spec: docker-integration-test-framework
Requirement: R4 (Add diagnostic instrumentation)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys
import logging

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "artifacts" / "working" / "modules"))


class TestDiagnosticLogging:
    """
    Integration test: Verify diagnostic logs are generated at integration boundaries.

    Tests cover:
    1. F-string evaluation logging (Bug #1 fix validation)
    2. Docker execution result logging (integration boundary)
    3. LLM initialization logging (integration boundary)
    """

    def test_fstring_evaluation_logging(self, caplog):
        """Verify f-string evaluation generates diagnostic logs (Bug #1 detection)"""
        from artifacts.working.modules.autonomous_loop import SandboxExecutionWrapper

        mock_docker = Mock()
        mock_logger = Mock()
        mock_docker.execute.return_value = {'success': True, 'signal': {}, 'error': None}

        with caplog.at_level(logging.DEBUG):
            wrapper = SandboxExecutionWrapper(
                sandbox_enabled=True,
                docker_executor=mock_docker,
                event_logger=mock_logger
            )
            wrapper.execute_strategy(code="position = close.is_largest(10)", data=Mock(), timeout=120)

        # Verify logging occurred (Task 3.4 already implemented)
        assert any("Complete code" in record.message for record in caplog.records), \
            "Should log complete code assembly (first 500 chars)"

    def test_docker_result_logging(self, caplog):
        """Verify Docker result generates diagnostic logs (Task 4.3)"""
        from artifacts.working.modules.autonomous_loop import SandboxExecutionWrapper

        mock_docker = Mock()
        mock_logger = Mock()
        mock_docker.execute.return_value = {
            'success': True,
            'signal': {'sharpe_ratio': 1.5, 'annual_return': 0.3},
            'error': None
        }

        with caplog.at_level(logging.DEBUG):
            wrapper = SandboxExecutionWrapper(
                sandbox_enabled=True,
                docker_executor=mock_docker,
                event_logger=mock_logger
            )
            wrapper.execute_strategy(code="position = close.is_largest(10)", data=Mock(), timeout=120)

        # Verify Docker result logging
        docker_logs = [r.message for r in caplog.records if "Docker execution result" in r.message]
        assert len(docker_logs) > 0, "Should log Docker execution result"

        # Verify log contains key information
        docker_log = docker_logs[0]
        assert "success=True" in docker_log, "Should log success status"
        assert "signal_keys=" in docker_log, "Should log signal keys"

    def test_llm_initialization_logging(self, caplog):
        """Verify LLM initialization generates diagnostic logs (Task 4.3)"""
        from src.innovation.innovation_engine import InnovationEngine

        with caplog.at_level(logging.INFO):
            # Initialize with valid provider
            engine = InnovationEngine(
                provider_name='gemini',
                model='gemini-2.5-flash',
                max_retries=1
            )

        # Verify LLM initialization logging
        llm_logs = [r.message for r in caplog.records if "LLM initialized" in r.message]
        assert len(llm_logs) > 0, "Should log LLM initialization"

        # Verify log contains provider and model
        llm_log = llm_logs[0]
        assert "provider='gemini'" in llm_log, "Should log provider name"
        assert "model='gemini-2.5-flash'" in llm_log, "Should log model name"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
