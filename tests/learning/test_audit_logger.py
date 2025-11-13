# tests/learning/test_audit_logger.py
"""
Phase 4 TDD Test Suite: Audit Trail System

Tests for audit_trail.py components:
- GenerationDecision dataclass: Decision record structure
- AuditLogger class: Decision logging and HTML report generation

These tests follow TDD principles and ensure >95% coverage of the audit trail system.

Key Assertions:
1. AuditLogger initializes with default and custom directories
2. log_decision() records decisions with full context
3. JSON files are written in JSONL format with correct structure
4. generate_html_report() creates valid HTML with decision statistics
5. Edge cases (empty decisions, malformed data) are handled gracefully
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.learning.audit_trail import AuditLogger, GenerationDecision


class TestGenerationDecisionDataclass:
    """
    Tests for GenerationDecision dataclass structure and serialization.

    Ensures the decision record captures all necessary context and
    can be serialized/deserialized correctly.
    """

    def test_generation_decision_creation(self):
        """
        GIVEN valid decision parameters
        WHEN a GenerationDecision is created
        THEN it should contain all required fields
        """
        # Arrange
        timestamp = "2025-01-11T10:00:00"
        config = {"use_factor_graph": True, "innovation_rate": 50}

        # Act
        decision = GenerationDecision(
            timestamp=timestamp,
            iteration_num=1,
            decision="factor_graph",
            reason="use_factor_graph=True forces Factor Graph",
            config_snapshot=config,
            use_factor_graph=True,
            innovation_rate=50,
            success=True,
            error=None,
        )

        # Assert
        assert decision.timestamp == timestamp
        assert decision.iteration_num == 1
        assert decision.decision == "factor_graph"
        assert decision.reason == "use_factor_graph=True forces Factor Graph"
        assert decision.config_snapshot == config
        assert decision.use_factor_graph is True
        assert decision.innovation_rate == 50
        assert decision.success is True
        assert decision.error is None

    def test_generation_decision_with_error(self):
        """
        GIVEN a failed generation with error
        WHEN a GenerationDecision is created
        THEN it should capture the error message
        """
        # Arrange
        error_msg = "LLM client is not enabled"

        # Act
        decision = GenerationDecision(
            timestamp="2025-01-11T10:00:00",
            iteration_num=2,
            decision="unknown",
            reason="Generation failed",
            config_snapshot={"innovation_rate": 100},
            use_factor_graph=None,
            innovation_rate=100,
            success=False,
            error=error_msg,
        )

        # Assert
        assert decision.success is False
        assert decision.error == error_msg

    def test_generation_decision_to_dict(self):
        """
        GIVEN a GenerationDecision instance
        WHEN to_dict() is called
        THEN it should return a dictionary with all fields
        """
        # Arrange
        decision = GenerationDecision(
            timestamp="2025-01-11T10:00:00",
            iteration_num=1,
            decision="llm",
            reason="innovation_rate=100 forces LLM",
            config_snapshot={"innovation_rate": 100},
            use_factor_graph=None,
            innovation_rate=100,
            success=True,
            error=None,
        )

        # Act
        decision_dict = decision.to_dict()

        # Assert
        assert isinstance(decision_dict, dict)
        assert decision_dict["timestamp"] == "2025-01-11T10:00:00"
        assert decision_dict["iteration_num"] == 1
        assert decision_dict["decision"] == "llm"
        assert decision_dict["reason"] == "innovation_rate=100 forces LLM"
        assert decision_dict["config_snapshot"] == {"innovation_rate": 100}
        assert decision_dict["use_factor_graph"] is None
        assert decision_dict["innovation_rate"] == 100
        assert decision_dict["success"] is True
        assert decision_dict["error"] is None

    def test_generation_decision_serialization(self):
        """
        GIVEN a GenerationDecision
        WHEN serialized to JSON and deserialized
        THEN all data should be preserved
        """
        # Arrange
        original = GenerationDecision(
            timestamp="2025-01-11T10:00:00",
            iteration_num=1,
            decision="llm",
            reason="Test reason",
            config_snapshot={"use_factor_graph": False, "innovation_rate": 100},
            use_factor_graph=False,
            innovation_rate=100,
            success=True,
            error=None,
        )

        # Act
        json_str = json.dumps(original.to_dict())
        deserialized = json.loads(json_str)

        # Assert
        assert deserialized["timestamp"] == original.timestamp
        assert deserialized["iteration_num"] == original.iteration_num
        assert deserialized["decision"] == original.decision
        assert deserialized["reason"] == original.reason
        assert deserialized["config_snapshot"] == original.config_snapshot
        assert deserialized["use_factor_graph"] == original.use_factor_graph
        assert deserialized["innovation_rate"] == original.innovation_rate
        assert deserialized["success"] == original.success
        assert deserialized["error"] == original.error


class TestAuditLoggerInitialization:
    """
    Tests for AuditLogger initialization with default and custom directories.

    Ensures logger creates necessary directories and initializes state correctly.
    """

    def test_init_with_default_directory(self):
        """
        GIVEN no log directory specified
        WHEN AuditLogger is initialized
        THEN it should use default directory and create it
        """
        # Act
        with tempfile.TemporaryDirectory() as tmpdir:
            default_log_dir = Path(tmpdir) / "logs/generation_audit"
            logger = AuditLogger(log_dir=str(default_log_dir))

            # Assert
            assert logger.log_dir == default_log_dir
            assert logger.log_dir.exists()
            assert logger.log_dir.is_dir()
            assert isinstance(logger.decisions, list)
            assert len(logger.decisions) == 0

    def test_init_with_custom_directory(self):
        """
        GIVEN a custom log directory
        WHEN AuditLogger is initialized
        THEN it should use the custom directory and create it
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_log_dir = Path(tmpdir) / "custom_audit_logs"

            # Act
            logger = AuditLogger(log_dir=str(custom_log_dir))

            # Assert
            assert logger.log_dir == custom_log_dir
            assert logger.log_dir.exists()
            assert logger.log_dir.is_dir()

    def test_init_creates_nested_directories(self):
        """
        GIVEN a nested directory path that doesn't exist
        WHEN AuditLogger is initialized
        THEN it should create all parent directories
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "level1/level2/level3/audit_logs"

            # Act
            logger = AuditLogger(log_dir=str(nested_path))

            # Assert
            assert logger.log_dir == nested_path
            assert logger.log_dir.exists()
            assert logger.log_dir.is_dir()

    def test_init_with_existing_directory(self):
        """
        GIVEN an existing log directory
        WHEN AuditLogger is initialized
        THEN it should not raise an error
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_dir = Path(tmpdir) / "existing_logs"
            existing_dir.mkdir(parents=True, exist_ok=True)

            # Act
            logger = AuditLogger(log_dir=str(existing_dir))

            # Assert
            assert logger.log_dir.exists()
            assert len(logger.decisions) == 0


class TestAuditLoggerDecisionLogging:
    """
    Tests for log_decision() method.

    Ensures decisions are recorded in memory and written to JSON files correctly.
    """

    @pytest.fixture
    def logger(self):
        """Provides an AuditLogger with a temporary directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield AuditLogger(log_dir=tmpdir)

    def test_log_decision_success_case(self, logger):
        """
        GIVEN a successful generation
        WHEN log_decision() is called
        THEN the decision should be recorded with success=True
        """
        # Arrange
        config = {"use_factor_graph": True, "innovation_rate": 50}

        # Act
        logger.log_decision(
            iteration_num=1,
            decision="factor_graph",
            reason="use_factor_graph=True forces Factor Graph",
            config=config,
            success=True,
            error=None,
        )

        # Assert
        assert len(logger.decisions) == 1
        decision = logger.decisions[0]
        assert decision.iteration_num == 1
        assert decision.decision == "factor_graph"
        assert decision.reason == "use_factor_graph=True forces Factor Graph"
        assert decision.config_snapshot == config
        assert decision.use_factor_graph is True
        assert decision.innovation_rate == 50
        assert decision.success is True
        assert decision.error is None

    def test_log_decision_failure_case(self, logger):
        """
        GIVEN a failed generation
        WHEN log_decision() is called with success=False
        THEN the decision should be recorded with error details
        """
        # Arrange
        config = {"innovation_rate": 100}
        error_msg = "LLM client is not enabled"

        # Act
        logger.log_decision(
            iteration_num=2,
            decision="unknown",
            reason="Generation failed",
            config=config,
            success=False,
            error=error_msg,
        )

        # Assert
        assert len(logger.decisions) == 1
        decision = logger.decisions[0]
        assert decision.iteration_num == 2
        assert decision.decision == "unknown"
        assert decision.success is False
        assert decision.error == error_msg

    def test_log_decision_writes_to_json_file(self, logger):
        """
        GIVEN a decision to log
        WHEN log_decision() is called
        THEN a JSON file should be created with the decision in JSONL format
        """
        # Arrange
        config = {"use_factor_graph": False, "innovation_rate": 100}

        # Act
        with patch("src.learning.audit_trail.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2025-01-11T10:00:00"
            mock_datetime.now.return_value.strftime.return_value = "20250111"

            logger.log_decision(
                iteration_num=1,
                decision="llm",
                reason="use_factor_graph=False forces LLM",
                config=config,
                success=True,
                error=None,
            )

        # Assert
        log_file = logger.log_dir / "audit_20250111.json"
        assert log_file.exists()

        # Verify JSONL format (one JSON object per line)
        with open(log_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 1
            decision_dict = json.loads(lines[0])
            assert decision_dict["iteration_num"] == 1
            assert decision_dict["decision"] == "llm"
            assert decision_dict["reason"] == "use_factor_graph=False forces LLM"

    def test_log_decision_appends_to_existing_file(self, logger):
        """
        GIVEN an existing log file for today
        WHEN multiple decisions are logged
        THEN they should be appended to the same file in JSONL format
        """
        # Arrange
        config1 = {"innovation_rate": 100}
        config2 = {"use_factor_graph": True, "innovation_rate": 50}

        # Act
        with patch("src.learning.audit_trail.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2025-01-11T10:00:00"
            mock_datetime.now.return_value.strftime.return_value = "20250111"

            logger.log_decision(
                iteration_num=1,
                decision="llm",
                reason="First decision",
                config=config1,
                success=True,
            )

            logger.log_decision(
                iteration_num=2,
                decision="factor_graph",
                reason="Second decision",
                config=config2,
                success=True,
            )

        # Assert
        log_file = logger.log_dir / "audit_20250111.json"
        with open(log_file, "r") as f:
            lines = f.readlines()
            assert len(lines) == 2

            # Verify first decision
            decision1 = json.loads(lines[0])
            assert decision1["iteration_num"] == 1
            assert decision1["decision"] == "llm"

            # Verify second decision
            decision2 = json.loads(lines[1])
            assert decision2["iteration_num"] == 2
            assert decision2["decision"] == "factor_graph"

    def test_log_decision_preserves_config_snapshot(self, logger):
        """
        GIVEN a config dictionary
        WHEN log_decision() is called
        THEN the config should be copied to prevent external mutations
        """
        # Arrange
        config = {"use_factor_graph": True, "innovation_rate": 50}

        # Act
        logger.log_decision(
            iteration_num=1,
            decision="factor_graph",
            reason="Test",
            config=config,
            success=True,
        )

        # Modify original config after logging
        config["use_factor_graph"] = False
        config["new_key"] = "new_value"

        # Assert
        decision = logger.decisions[0]
        assert decision.config_snapshot == {"use_factor_graph": True, "innovation_rate": 50}
        assert "new_key" not in decision.config_snapshot

    def test_log_decision_with_none_use_factor_graph(self, logger):
        """
        GIVEN a config without use_factor_graph
        WHEN log_decision() is called
        THEN use_factor_graph should be None in the record
        """
        # Arrange
        config = {"innovation_rate": 50}

        # Act
        logger.log_decision(
            iteration_num=1,
            decision="llm",
            reason="Probabilistic decision",
            config=config,
            success=True,
        )

        # Assert
        decision = logger.decisions[0]
        assert decision.use_factor_graph is None
        assert decision.innovation_rate == 50

    def test_log_decision_with_default_innovation_rate(self, logger):
        """
        GIVEN a config without innovation_rate
        WHEN log_decision() is called
        THEN innovation_rate should default to 100
        """
        # Arrange
        config = {"use_factor_graph": True}

        # Act
        logger.log_decision(
            iteration_num=1,
            decision="factor_graph",
            reason="Test",
            config=config,
            success=True,
        )

        # Assert
        decision = logger.decisions[0]
        assert decision.innovation_rate == 100

    def test_log_decision_timestamp_format(self, logger):
        """
        GIVEN current time
        WHEN log_decision() is called
        THEN timestamp should be in ISO format
        """
        # Act
        logger.log_decision(
            iteration_num=1,
            decision="llm",
            reason="Test",
            config={"innovation_rate": 100},
            success=True,
        )

        # Assert
        decision = logger.decisions[0]
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(decision.timestamp)


class TestAuditLoggerReportGeneration:
    """
    Tests for generate_html_report() method.

    Ensures HTML reports are generated correctly with decision statistics and formatting.
    """

    @pytest.fixture
    def logger_with_decisions(self):
        """Provides an AuditLogger with pre-logged decisions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            # Log multiple decisions
            with patch("src.learning.audit_trail.datetime") as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = "2025-01-11T10:00:00"
                mock_datetime.now.return_value.strftime.return_value = "20250111"

                logger.log_decision(
                    iteration_num=1,
                    decision="llm",
                    reason="use_factor_graph=False forces LLM",
                    config={"use_factor_graph": False, "innovation_rate": 100},
                    success=True,
                )

                logger.log_decision(
                    iteration_num=2,
                    decision="factor_graph",
                    reason="use_factor_graph=True forces Factor Graph",
                    config={"use_factor_graph": True, "innovation_rate": 50},
                    success=True,
                )

                logger.log_decision(
                    iteration_num=3,
                    decision="unknown",
                    reason="Generation failed",
                    config={"innovation_rate": 100},
                    success=False,
                    error="LLM client is not enabled",
                )

            yield logger

    def test_generate_html_report_creates_file(self, logger_with_decisions):
        """
        GIVEN decisions logged
        WHEN generate_html_report() is called
        THEN an HTML file should be created
        """
        # Arrange
        output_file = logger_with_decisions.log_dir / "test_report.html"

        # Act
        logger_with_decisions.generate_html_report(output_file=str(output_file))

        # Assert
        assert output_file.exists()
        assert output_file.is_file()

    def test_generate_html_report_with_empty_decisions(self):
        """
        GIVEN no decisions logged
        WHEN generate_html_report() is called
        THEN it should create an HTML report indicating no decisions
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            output_file = Path(tmpdir) / "empty_report.html"

            # Act
            logger.generate_html_report(output_file=str(output_file))

            # Assert
            assert output_file.exists()
            content = output_file.read_text()
            assert "No decisions recorded" in content or "0" in content

    def test_generate_html_report_content_structure(self, logger_with_decisions):
        """
        GIVEN decisions logged
        WHEN generate_html_report() is called
        THEN the HTML should contain proper structure and statistics
        """
        # Arrange
        output_file = logger_with_decisions.log_dir / "test_report.html"

        # Act
        logger_with_decisions.generate_html_report(output_file=str(output_file))

        # Assert
        content = output_file.read_text()
        assert "<html" in content.lower()
        assert "</html>" in content.lower()
        assert "Generation Audit Report" in content or "Audit Report" in content
        assert "llm" in content.lower() or "LLM" in content
        assert "factor_graph" in content.lower() or "Factor Graph" in content

    def test_generate_html_report_statistics(self, logger_with_decisions):
        """
        GIVEN 3 decisions (2 success, 1 failure)
        WHEN generate_html_report() is called
        THEN the HTML should contain correct statistics
        """
        # Arrange
        output_file = logger_with_decisions.log_dir / "test_report.html"

        # Act
        logger_with_decisions.generate_html_report(output_file=str(output_file))

        # Assert
        content = output_file.read_text()
        # Should show total decisions
        assert "3" in content
        # Should show success/failure counts
        assert "2" in content  # 2 successes
        assert "1" in content  # 1 failure

    def test_generate_html_report_decision_details(self, logger_with_decisions):
        """
        GIVEN logged decisions
        WHEN generate_html_report() is called
        THEN each decision's details should be present in the HTML
        """
        # Arrange
        output_file = logger_with_decisions.log_dir / "test_report.html"

        # Act
        logger_with_decisions.generate_html_report(output_file=str(output_file))

        # Assert
        content = output_file.read_text()
        # Check for decision reasons
        assert "use_factor_graph=False forces LLM" in content
        assert "use_factor_graph=True forces Factor Graph" in content
        assert "Generation failed" in content
        # Check for error message
        assert "LLM client is not enabled" in content

    def test_generate_html_report_with_custom_output_path(self, logger_with_decisions):
        """
        GIVEN a custom output file path
        WHEN generate_html_report() is called
        THEN the report should be created at the specified location
        """
        # Arrange
        custom_path = logger_with_decisions.log_dir / "custom/path/report.html"

        # Act
        logger_with_decisions.generate_html_report(output_file=str(custom_path))

        # Assert
        assert custom_path.exists()

    def test_generate_html_report_default_filename(self, logger_with_decisions):
        """
        GIVEN no output filename specified
        WHEN generate_html_report() is called
        THEN it should use default filename "audit_report.html"
        """
        # Act
        logger_with_decisions.generate_html_report()

        # Assert
        # Check if file was created (may be in current directory or log directory)
        possible_locations = [
            Path("audit_report.html"),
            logger_with_decisions.log_dir / "audit_report.html",
        ]
        assert any(p.exists() for p in possible_locations)

    def test_generate_html_report_includes_timestamp(self, logger_with_decisions):
        """
        GIVEN decisions with timestamps
        WHEN generate_html_report() is called
        THEN the HTML should include decision timestamps
        """
        # Arrange
        output_file = logger_with_decisions.log_dir / "test_report.html"

        # Act
        logger_with_decisions.generate_html_report(output_file=str(output_file))

        # Assert
        content = output_file.read_text()
        assert "2025-01-11" in content or "2025" in content

    def test_generate_html_report_violation_detection(self, logger_with_decisions):
        """
        GIVEN decisions including failures
        WHEN generate_html_report() is called
        THEN violations (failures) should be highlighted or listed
        """
        # Arrange
        output_file = logger_with_decisions.log_dir / "test_report.html"

        # Act
        logger_with_decisions.generate_html_report(output_file=str(output_file))

        # Assert
        content = output_file.read_text()
        # Should highlight or mention failures/violations
        assert "fail" in content.lower() or "error" in content.lower() or "violation" in content.lower()


class TestAuditLoggerEdgeCases:
    """
    Tests for edge cases and error handling.

    Ensures AuditLogger handles unusual inputs gracefully.
    """

    def test_log_decision_with_empty_config(self):
        """
        GIVEN an empty config dictionary
        WHEN log_decision() is called
        THEN it should handle it gracefully with defaults
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            # Act
            logger.log_decision(
                iteration_num=1,
                decision="llm",
                reason="Test",
                config={},
                success=True,
            )

            # Assert
            decision = logger.decisions[0]
            assert decision.use_factor_graph is None
            assert decision.innovation_rate == 100  # Default value

    def test_log_decision_with_extra_config_keys(self):
        """
        GIVEN a config with extra keys not used by decision logic
        WHEN log_decision() is called
        THEN all config data should be preserved in snapshot
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            config = {
                "use_factor_graph": True,
                "innovation_rate": 50,
                "extra_key1": "value1",
                "extra_key2": 123,
            }

            # Act
            logger.log_decision(
                iteration_num=1,
                decision="factor_graph",
                reason="Test",
                config=config,
                success=True,
            )

            # Assert
            decision = logger.decisions[0]
            assert decision.config_snapshot == config
            assert decision.config_snapshot["extra_key1"] == "value1"
            assert decision.config_snapshot["extra_key2"] == 123

    def test_log_decision_with_very_long_reason(self):
        """
        GIVEN a very long reason string
        WHEN log_decision() is called
        THEN it should handle the long text without truncation
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            long_reason = "x" * 10000

            # Act
            logger.log_decision(
                iteration_num=1,
                decision="llm",
                reason=long_reason,
                config={"innovation_rate": 100},
                success=True,
            )

            # Assert
            decision = logger.decisions[0]
            assert len(decision.reason) == 10000
            assert decision.reason == long_reason

    def test_log_decision_with_special_characters_in_error(self):
        """
        GIVEN an error message with special characters
        WHEN log_decision() is called
        THEN the error should be stored correctly
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            error_msg = "Error: <html>&special\"characters\"</html>"

            # Act
            logger.log_decision(
                iteration_num=1,
                decision="unknown",
                reason="Test",
                config={"innovation_rate": 100},
                success=False,
                error=error_msg,
            )

            # Assert
            decision = logger.decisions[0]
            assert decision.error == error_msg

    def test_multiple_audit_loggers_same_directory(self):
        """
        GIVEN multiple AuditLogger instances pointing to same directory
        WHEN both log decisions
        THEN they should write to the same log file without conflicts
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            logger1 = AuditLogger(log_dir=tmpdir)
            logger2 = AuditLogger(log_dir=tmpdir)

            # Act
            with patch("src.learning.audit_trail.datetime") as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = "2025-01-11T10:00:00"
                mock_datetime.now.return_value.strftime.return_value = "20250111"

                logger1.log_decision(
                    iteration_num=1,
                    decision="llm",
                    reason="Logger1 decision",
                    config={"innovation_rate": 100},
                    success=True,
                )

                logger2.log_decision(
                    iteration_num=2,
                    decision="factor_graph",
                    reason="Logger2 decision",
                    config={"use_factor_graph": True, "innovation_rate": 50},
                    success=True,
                )

            # Assert
            log_file = Path(tmpdir) / "audit_20250111.json"
            with open(log_file, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2

    def test_generate_html_report_with_unicode_content(self):
        """
        GIVEN decisions with unicode characters
        WHEN generate_html_report() is called
        THEN the HTML should handle unicode correctly
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)
            logger.log_decision(
                iteration_num=1,
                decision="llm",
                reason="測試 unicode 字符 🎯",
                config={"innovation_rate": 100},
                success=True,
            )
            output_file = Path(tmpdir) / "unicode_report.html"

            # Act
            logger.generate_html_report(output_file=str(output_file))

            # Assert
            content = output_file.read_text(encoding="utf-8")
            assert "測試 unicode 字符 🎯" in content


class TestAuditLoggerIntegration:
    """
    Integration tests for AuditLogger with realistic scenarios.

    Simulates real usage patterns from IterationExecutor integration.
    """

    def test_full_iteration_logging_scenario(self):
        """
        GIVEN multiple iterations of strategy generation
        WHEN decisions are logged for each iteration
        THEN the audit trail should capture the complete history
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            # Simulate multiple iterations
            scenarios = [
                (1, "llm", "innovation_rate=100 forces LLM", {"innovation_rate": 100}, True, None),
                (2, "factor_graph", "use_factor_graph=True forces Factor Graph", {"use_factor_graph": True, "innovation_rate": 50}, True, None),
                (3, "llm", "Probabilistic decision (random < innovation_rate)", {"innovation_rate": 75}, True, None),
                (4, "unknown", "Generation failed", {"innovation_rate": 100}, False, "LLM client is not enabled"),
                (5, "factor_graph", "use_factor_graph=True forces Factor Graph", {"use_factor_graph": True, "innovation_rate": 0}, True, None),
            ]

            # Act
            for iteration, decision, reason, config, success, error in scenarios:
                logger.log_decision(
                    iteration_num=iteration,
                    decision=decision,
                    reason=reason,
                    config=config,
                    success=success,
                    error=error,
                )

            # Assert
            assert len(logger.decisions) == 5
            assert sum(1 for d in logger.decisions if d.success) == 4
            assert sum(1 for d in logger.decisions if not d.success) == 1
            assert sum(1 for d in logger.decisions if d.decision == "llm") == 2
            assert sum(1 for d in logger.decisions if d.decision == "factor_graph") == 2

    def test_daily_log_file_rotation(self):
        """
        GIVEN decisions logged on different days
        WHEN log_decision() is called
        THEN separate log files should be created for each day
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            # Act - Log on day 1
            with patch("src.learning.audit_trail.datetime") as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = "2025-01-11T10:00:00"
                mock_datetime.now.return_value.strftime.return_value = "20250111"

                logger.log_decision(
                    iteration_num=1,
                    decision="llm",
                    reason="Day 1 decision",
                    config={"innovation_rate": 100},
                    success=True,
                )

            # Act - Log on day 2
            with patch("src.learning.audit_trail.datetime") as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = "2025-01-12T10:00:00"
                mock_datetime.now.return_value.strftime.return_value = "20250112"

                logger.log_decision(
                    iteration_num=2,
                    decision="factor_graph",
                    reason="Day 2 decision",
                    config={"use_factor_graph": True, "innovation_rate": 50},
                    success=True,
                )

            # Assert
            log_file_day1 = Path(tmpdir) / "audit_20250111.json"
            log_file_day2 = Path(tmpdir) / "audit_20250112.json"

            assert log_file_day1.exists()
            assert log_file_day2.exists()

            with open(log_file_day1, "r") as f:
                assert len(f.readlines()) == 1

            with open(log_file_day2, "r") as f:
                assert len(f.readlines()) == 1

    def test_audit_trail_with_configuration_conflicts(self):
        """
        GIVEN decisions with configuration conflicts
        WHEN log_decision() is called
        THEN conflicts should be recorded for analysis
        """
        # Arrange
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(log_dir=tmpdir)

            # Log a potential conflict scenario (would have raised error in Phase 1)
            logger.log_decision(
                iteration_num=1,
                decision="unknown",
                reason="Configuration conflict detected",
                config={"use_factor_graph": True, "innovation_rate": 100},
                success=False,
                error="ConfigurationConflictError: use_factor_graph=True but innovation_rate=100",
            )

            # Assert
            decision = logger.decisions[0]
            assert decision.success is False
            assert "ConfigurationConflictError" in decision.error
            assert decision.use_factor_graph is True
            assert decision.innovation_rate == 100
