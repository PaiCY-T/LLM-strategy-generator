# tests/learning/test_generation_decision.py
"""
Phase 4 TDD Test Suite: GenerationDecision Dataclass

Tests for audit_trail.py GenerationDecision dataclass:
- Dataclass instantiation with all fields
- Field validation and types
- to_dict() method serialization
- Default values (error=None)
- Edge cases (empty strings, None values, special characters)
- JSON serialization compatibility
- Immutability considerations

These tests are written against the DESIRED behavior for Phase 4 Audit Trail implementation.
They define the contract for the GenerationDecision dataclass before implementation.

Key Assertions:
1. All required fields must be provided at instantiation
2. Optional error field defaults to None
3. to_dict() correctly serializes all fields including nested dicts
4. Dataclass handles edge cases (empty strings, special characters, None values)
5. JSON serialization works correctly for audit logging
6. Timestamp format is ISO 8601 compatible
7. Config snapshot is properly copied (not referenced)
"""

import json
from copy import deepcopy
from dataclasses import asdict

import pytest

from src.learning.audit_trail import GenerationDecision


class TestGenerationDecisionCreation:
    """
    TDD Tests for GenerationDecision dataclass instantiation.

    These tests verify that the dataclass can be created with all required
    and optional fields, following the specification from design.md.
    """

    def test_create_with_all_fields_success_case(self):
        """
        WHEN GenerationDecision is created with all fields (success=True)
        THEN all fields should be accessible with correct values.
        """
        # Arrange
        config_snapshot = {"use_factor_graph": False, "innovation_rate": 100}

        # Act
        decision = GenerationDecision(
            timestamp="2024-01-15T10:30:00.000000",
            iteration_num=5,
            decision="llm",
            reason="Config: use_factor_graph=False, innovation_rate=100",
            config_snapshot=config_snapshot,
            use_factor_graph=False,
            innovation_rate=100,
            success=True,
            error=None
        )

        # Assert
        assert decision.timestamp == "2024-01-15T10:30:00.000000"
        assert decision.iteration_num == 5
        assert decision.decision == "llm"
        assert decision.reason == "Config: use_factor_graph=False, innovation_rate=100"
        assert decision.config_snapshot == config_snapshot
        assert decision.use_factor_graph is False
        assert decision.innovation_rate == 100
        assert decision.success is True
        assert decision.error is None

    def test_create_with_all_fields_failure_case(self):
        """
        WHEN GenerationDecision is created with error (success=False)
        THEN error field should contain error message.
        """
        # Arrange
        config_snapshot = {"use_factor_graph": True, "innovation_rate": 50}

        # Act
        decision = GenerationDecision(
            timestamp="2024-01-15T10:35:00.000000",
            iteration_num=6,
            decision="unknown",
            reason="Generation failed",
            config_snapshot=config_snapshot,
            use_factor_graph=True,
            innovation_rate=50,
            success=False,
            error="LLMGenerationError: LLM engine not available"
        )

        # Assert
        assert decision.timestamp == "2024-01-15T10:35:00.000000"
        assert decision.iteration_num == 6
        assert decision.decision == "unknown"
        assert decision.reason == "Generation failed"
        assert decision.config_snapshot == config_snapshot
        assert decision.use_factor_graph is True
        assert decision.innovation_rate == 50
        assert decision.success is False
        assert decision.error == "LLMGenerationError: LLM engine not available"

    def test_create_with_factor_graph_decision(self):
        """
        WHEN GenerationDecision is created for factor graph strategy
        THEN decision field should be "factor_graph".
        """
        # Arrange & Act
        decision = GenerationDecision(
            timestamp="2024-01-15T11:00:00.000000",
            iteration_num=10,
            decision="factor_graph",
            reason="Config: use_factor_graph=True, innovation_rate=0",
            config_snapshot={"use_factor_graph": True, "innovation_rate": 0},
            use_factor_graph=True,
            innovation_rate=0,
            success=True
        )

        # Assert
        assert decision.decision == "factor_graph"
        assert decision.use_factor_graph is True
        assert decision.success is True
        assert decision.error is None

    @pytest.mark.parametrize(
        "use_factor_graph, decision_type",
        [
            pytest.param(True, "factor_graph", id="factor_graph_true"),
            pytest.param(False, "llm", id="factor_graph_false"),
            pytest.param(None, "llm", id="factor_graph_none_probabilistic"),
        ],
    )
    def test_create_with_different_use_factor_graph_values(self, use_factor_graph, decision_type):
        """
        WHEN GenerationDecision is created with different use_factor_graph values
        THEN the field should accept True, False, and None.
        """
        # Arrange & Act
        decision = GenerationDecision(
            timestamp="2024-01-15T12:00:00.000000",
            iteration_num=15,
            decision=decision_type,
            reason=f"use_factor_graph={use_factor_graph}",
            config_snapshot={"use_factor_graph": use_factor_graph},
            use_factor_graph=use_factor_graph,
            innovation_rate=50,
            success=True
        )

        # Assert
        assert decision.use_factor_graph == use_factor_graph
        assert decision.decision == decision_type


class TestDefaultValues:
    """
    TDD Tests for default value initialization.

    These tests verify that GenerationDecision uses correct default:
    - error: None (only optional field)
    """

    def test_error_defaults_to_none(self):
        """
        WHEN GenerationDecision is created without error parameter
        THEN error field should default to None.
        """
        # Arrange & Act
        decision = GenerationDecision(
            timestamp="2024-01-15T13:00:00.000000",
            iteration_num=20,
            decision="llm",
            reason="Successful generation",
            config_snapshot={"innovation_rate": 100},
            use_factor_graph=None,
            innovation_rate=100,
            success=True
        )

        # Assert
        assert decision.error is None

    def test_explicit_none_error(self):
        """
        WHEN GenerationDecision is created with error=None explicitly
        THEN error field should be None.
        """
        # Arrange & Act
        decision = GenerationDecision(
            timestamp="2024-01-15T13:30:00.000000",
            iteration_num=25,
            decision="factor_graph",
            reason="Factor graph generation",
            config_snapshot={"use_factor_graph": True},
            use_factor_graph=True,
            innovation_rate=0,
            success=True,
            error=None
        )

        # Assert
        assert decision.error is None


class TestToDictSerialization:
    """
    TDD Tests for to_dict() method serialization.

    These tests verify that to_dict() correctly converts the dataclass
    to a dictionary using asdict(), preserving all field values including
    nested dictionaries.
    """

    def test_to_dict_with_all_fields(self):
        """
        WHEN to_dict() is called on GenerationDecision with all fields
        THEN it should return a dictionary with all field values.
        """
        # Arrange
        config_snapshot = {
            "use_factor_graph": False,
            "innovation_rate": 100,
            "nested": {"key": "value"}
        }
        decision = GenerationDecision(
            timestamp="2024-01-15T14:00:00.000000",
            iteration_num=30,
            decision="llm",
            reason="Test reason",
            config_snapshot=config_snapshot,
            use_factor_graph=False,
            innovation_rate=100,
            success=True,
            error="Test error"
        )

        # Act
        result = decision.to_dict()

        # Assert
        assert result == {
            "timestamp": "2024-01-15T14:00:00.000000",
            "iteration_num": 30,
            "decision": "llm",
            "reason": "Test reason",
            "config_snapshot": {
                "use_factor_graph": False,
                "innovation_rate": 100,
                "nested": {"key": "value"}
            },
            "use_factor_graph": False,
            "innovation_rate": 100,
            "success": True,
            "error": "Test error"
        }

    def test_to_dict_with_none_error(self):
        """
        WHEN to_dict() is called with error=None
        THEN the dictionary should include error key with None value.
        """
        # Arrange
        decision = GenerationDecision(
            timestamp="2024-01-15T14:30:00.000000",
            iteration_num=35,
            decision="factor_graph",
            reason="Success",
            config_snapshot={"use_factor_graph": True},
            use_factor_graph=True,
            innovation_rate=0,
            success=True,
            error=None
        )

        # Act
        result = decision.to_dict()

        # Assert
        assert "error" in result
        assert result["error"] is None

    def test_to_dict_equals_asdict(self):
        """
        WHEN to_dict() is called
        THEN it should produce the same result as dataclasses.asdict().
        """
        # Arrange
        decision = GenerationDecision(
            timestamp="2024-01-15T15:00:00.000000",
            iteration_num=40,
            decision="llm",
            reason="Verify asdict equivalence",
            config_snapshot={"innovation_rate": 75},
            use_factor_graph=None,
            innovation_rate=75,
            success=True
        )

        # Act
        to_dict_result = decision.to_dict()
        asdict_result = asdict(decision)

        # Assert
        assert to_dict_result == asdict_result

    def test_to_dict_preserves_nested_dict_structure(self):
        """
        WHEN config_snapshot contains nested dictionaries
        THEN to_dict() should preserve the entire nested structure.
        """
        # Arrange
        config_snapshot = {
            "use_factor_graph": False,
            "innovation_rate": 100,
            "advanced_config": {
                "strategy_params": {
                    "lookback": 20,
                    "threshold": 0.05
                },
                "risk_settings": {
                    "max_loss": -0.10
                }
            }
        }
        decision = GenerationDecision(
            timestamp="2024-01-15T15:30:00.000000",
            iteration_num=45,
            decision="llm",
            reason="Complex config test",
            config_snapshot=config_snapshot,
            use_factor_graph=False,
            innovation_rate=100,
            success=True
        )

        # Act
        result = decision.to_dict()

        # Assert
        assert result["config_snapshot"] == config_snapshot
        assert result["config_snapshot"]["advanced_config"]["strategy_params"]["lookback"] == 20


class TestJSONSerialization:
    """
    TDD Tests for JSON serialization compatibility.

    These tests verify that GenerationDecision can be serialized to JSON
    for audit logging, as required by AuditLogger.log_decision().
    """

    def test_json_serialization_success(self):
        """
        WHEN GenerationDecision is converted to dict and then JSON
        THEN it should serialize successfully.
        """
        # Arrange
        decision = GenerationDecision(
            timestamp="2024-01-15T16:00:00.000000",
            iteration_num=50,
            decision="llm",
            reason="JSON serialization test",
            config_snapshot={"innovation_rate": 100},
            use_factor_graph=None,
            innovation_rate=100,
            success=True,
            error=None
        )

        # Act
        json_str = json.dumps(decision.to_dict())
        parsed = json.loads(json_str)

        # Assert
        assert parsed["timestamp"] == "2024-01-15T16:00:00.000000"
        assert parsed["iteration_num"] == 50
        assert parsed["decision"] == "llm"
        assert parsed["success"] is True
        assert parsed["error"] is None

    def test_json_serialization_with_error(self):
        """
        WHEN GenerationDecision with error is serialized to JSON
        THEN error message should be preserved.
        """
        # Arrange
        decision = GenerationDecision(
            timestamp="2024-01-15T16:30:00.000000",
            iteration_num=55,
            decision="unknown",
            reason="Generation failed",
            config_snapshot={"use_factor_graph": False},
            use_factor_graph=False,
            innovation_rate=100,
            success=False,
            error="LLMUnavailableError: LLM client is not enabled"
        )

        # Act
        json_str = json.dumps(decision.to_dict())
        parsed = json.loads(json_str)

        # Assert
        assert parsed["success"] is False
        assert parsed["error"] == "LLMUnavailableError: LLM client is not enabled"

    def test_json_serialization_preserves_types(self):
        """
        WHEN GenerationDecision is serialized to JSON and back
        THEN data types should be preserved correctly.
        """
        # Arrange
        decision = GenerationDecision(
            timestamp="2024-01-15T17:00:00.000000",
            iteration_num=60,
            decision="factor_graph",
            reason="Type preservation test",
            config_snapshot={
                "use_factor_graph": True,
                "innovation_rate": 25
            },
            use_factor_graph=True,
            innovation_rate=25,
            success=True
        )

        # Act
        json_str = json.dumps(decision.to_dict())
        parsed = json.loads(json_str)

        # Assert - verify types
        assert isinstance(parsed["timestamp"], str)
        assert isinstance(parsed["iteration_num"], int)
        assert isinstance(parsed["decision"], str)
        assert isinstance(parsed["reason"], str)
        assert isinstance(parsed["config_snapshot"], dict)
        assert isinstance(parsed["use_factor_graph"], bool)
        assert isinstance(parsed["innovation_rate"], int)
        assert isinstance(parsed["success"], bool)
        assert parsed["error"] is None


class TestEdgeCases:
    """
    TDD Tests for edge cases and boundary conditions.

    These tests verify that GenerationDecision handles:
    - Empty strings
    - Special characters in reason/error
    - None values for optional fields
    - Large config snapshots
    - Extreme iteration numbers
    """

    def test_empty_string_reason(self):
        """
        WHEN reason is an empty string
        THEN GenerationDecision should accept it.
        """
        # Arrange & Act
        decision = GenerationDecision(
            timestamp="2024-01-15T18:00:00.000000",
            iteration_num=70,
            decision="llm",
            reason="",
            config_snapshot={},
            use_factor_graph=None,
            innovation_rate=100,
            success=True
        )

        # Assert
        assert decision.reason == ""

    def test_empty_string_error(self):
        """
        WHEN error is an empty string
        THEN GenerationDecision should accept it.
        """
        # Arrange & Act
        decision = GenerationDecision(
            timestamp="2024-01-15T18:30:00.000000",
            iteration_num=75,
            decision="unknown",
            reason="Failed",
            config_snapshot={},
            use_factor_graph=None,
            innovation_rate=100,
            success=False,
            error=""
        )

        # Assert
        assert decision.error == ""

    @pytest.mark.parametrize(
        "special_text, field_name",
        [
            pytest.param(
                "Config: use_factor_graph=False, innovation_rate=100 (forces LLM)",
                "reason",
                id="parentheses_in_reason"
            ),
            pytest.param(
                "LLMGenerationError: LLM generation failed: 'NoneType' object has no attribute 'generate'",
                "error",
                id="quotes_in_error"
            ),
            pytest.param(
                "使用 LLM 生成策略 (innovation_rate=100)",
                "reason",
                id="unicode_chinese_in_reason"
            ),
            pytest.param(
                "Error: Connection timeout [timeout=30s, retries=3]",
                "error",
                id="brackets_in_error"
            ),
            pytest.param(
                "Multi\nline\nreason",
                "reason",
                id="newlines_in_reason"
            ),
            pytest.param(
                'JSON parse error: {"invalid": json}',
                "error",
                id="json_like_in_error"
            ),
        ],
    )
    def test_special_characters_in_text_fields(self, special_text, field_name):
        """
        WHEN reason or error contains special characters
        THEN GenerationDecision should handle them correctly.
        """
        # Arrange
        kwargs = {
            "timestamp": "2024-01-15T19:00:00.000000",
            "iteration_num": 80,
            "decision": "llm",
            "reason": "Default reason",
            "config_snapshot": {},
            "use_factor_graph": None,
            "innovation_rate": 100,
            "success": True,
            "error": None
        }
        kwargs[field_name] = special_text

        # Act
        decision = GenerationDecision(**kwargs)

        # Assert
        assert getattr(decision, field_name) == special_text

        # Verify JSON serialization works
        json_str = json.dumps(decision.to_dict())
        parsed = json.loads(json_str)
        assert parsed[field_name] == special_text

    def test_large_config_snapshot(self):
        """
        WHEN config_snapshot is large with many nested fields
        THEN GenerationDecision should handle it correctly.
        """
        # Arrange
        large_config = {
            f"param_{i}": {
                "nested_1": {
                    "nested_2": {
                        "value": i * 10
                    }
                }
            }
            for i in range(100)
        }

        # Act
        decision = GenerationDecision(
            timestamp="2024-01-15T19:30:00.000000",
            iteration_num=85,
            decision="llm",
            reason="Large config test",
            config_snapshot=large_config,
            use_factor_graph=None,
            innovation_rate=100,
            success=True
        )

        # Assert
        assert len(decision.config_snapshot) == 100
        assert decision.config_snapshot["param_50"]["nested_1"]["nested_2"]["value"] == 500

    @pytest.mark.parametrize(
        "iteration_num",
        [
            pytest.param(0, id="iteration_zero"),
            pytest.param(1, id="iteration_one"),
            pytest.param(1000, id="iteration_thousand"),
            pytest.param(999999, id="iteration_large"),
        ],
    )
    def test_extreme_iteration_numbers(self, iteration_num):
        """
        WHEN iteration_num is at boundary values
        THEN GenerationDecision should accept it.
        """
        # Arrange & Act
        decision = GenerationDecision(
            timestamp="2024-01-15T20:00:00.000000",
            iteration_num=iteration_num,
            decision="llm",
            reason="Iteration boundary test",
            config_snapshot={},
            use_factor_graph=None,
            innovation_rate=100,
            success=True
        )

        # Assert
        assert decision.iteration_num == iteration_num

    def test_empty_config_snapshot(self):
        """
        WHEN config_snapshot is an empty dictionary
        THEN GenerationDecision should accept it.
        """
        # Arrange & Act
        decision = GenerationDecision(
            timestamp="2024-01-15T20:30:00.000000",
            iteration_num=90,
            decision="llm",
            reason="Empty config test",
            config_snapshot={},
            use_factor_graph=None,
            innovation_rate=100,
            success=True
        )

        # Assert
        assert decision.config_snapshot == {}

    def test_config_snapshot_independence(self):
        """
        WHEN config_snapshot is modified after creation
        THEN it should not affect the decision's config_snapshot
        if properly copied by AuditLogger.

        NOTE: This tests the expected behavior when AuditLogger
        uses config.copy() as shown in design.md line 420.
        """
        # Arrange
        original_config = {"use_factor_graph": False, "innovation_rate": 100}
        decision = GenerationDecision(
            timestamp="2024-01-15T21:00:00.000000",
            iteration_num=95,
            decision="llm",
            reason="Config independence test",
            config_snapshot=original_config.copy(),  # Simulating AuditLogger behavior
            use_factor_graph=False,
            innovation_rate=100,
            success=True
        )

        # Act - modify original config
        original_config["use_factor_graph"] = True
        original_config["innovation_rate"] = 50

        # Assert - decision's config should be unchanged
        assert decision.config_snapshot["use_factor_graph"] is False
        assert decision.config_snapshot["innovation_rate"] == 100


class TestTimestampFormat:
    """
    TDD Tests for timestamp format compatibility.

    These tests verify that timestamp field accepts ISO 8601 format
    as used by datetime.now().isoformat() in design.md line 416.
    """

    @pytest.mark.parametrize(
        "timestamp_str",
        [
            pytest.param("2024-01-15T10:30:00.000000", id="microseconds"),
            pytest.param("2024-01-15T10:30:00", id="no_microseconds"),
            pytest.param("2024-01-15T10:30:00.123456", id="full_microseconds"),
            pytest.param("2024-01-15T10:30:00+00:00", id="with_timezone"),
            pytest.param("2024-01-15T10:30:00.123456+08:00", id="with_timezone_microseconds"),
        ],
    )
    def test_iso8601_timestamp_formats(self, timestamp_str):
        """
        WHEN timestamp is in various ISO 8601 formats
        THEN GenerationDecision should accept them.
        """
        # Arrange & Act
        decision = GenerationDecision(
            timestamp=timestamp_str,
            iteration_num=100,
            decision="llm",
            reason="Timestamp format test",
            config_snapshot={},
            use_factor_graph=None,
            innovation_rate=100,
            success=True
        )

        # Assert
        assert decision.timestamp == timestamp_str

    def test_timestamp_is_stored_as_string(self):
        """
        WHEN timestamp is provided as string
        THEN it should be stored as string (not converted to datetime object).
        """
        # Arrange
        timestamp_str = "2024-01-15T10:30:00.000000"

        # Act
        decision = GenerationDecision(
            timestamp=timestamp_str,
            iteration_num=105,
            decision="llm",
            reason="String type test",
            config_snapshot={},
            use_factor_graph=None,
            innovation_rate=100,
            success=True
        )

        # Assert
        assert isinstance(decision.timestamp, str)
        assert decision.timestamp == timestamp_str


class TestDataclassIntegration:
    """
    Integration tests for GenerationDecision dataclass.

    These tests verify end-to-end behavior and compatibility
    with the audit logging workflow described in design.md.
    """

    def test_create_serialize_deserialize_cycle(self):
        """
        WHEN GenerationDecision is created, serialized to JSON, and parsed back
        THEN the data should be preserved correctly.
        """
        # Arrange
        original = GenerationDecision(
            timestamp="2024-01-15T22:00:00.000000",
            iteration_num=110,
            decision="factor_graph",
            reason="Round-trip test",
            config_snapshot={"use_factor_graph": True, "innovation_rate": 25},
            use_factor_graph=True,
            innovation_rate=25,
            success=True,
            error=None
        )

        # Act - serialize and deserialize
        json_str = json.dumps(original.to_dict())
        parsed_dict = json.loads(json_str)
        reconstructed = GenerationDecision(**parsed_dict)

        # Assert
        assert reconstructed.timestamp == original.timestamp
        assert reconstructed.iteration_num == original.iteration_num
        assert reconstructed.decision == original.decision
        assert reconstructed.reason == original.reason
        assert reconstructed.config_snapshot == original.config_snapshot
        assert reconstructed.use_factor_graph == original.use_factor_graph
        assert reconstructed.innovation_rate == original.innovation_rate
        assert reconstructed.success == original.success
        assert reconstructed.error == original.error

    def test_multiple_decisions_in_sequence(self):
        """
        WHEN multiple GenerationDecision objects are created in sequence
        THEN each should maintain independent state.
        """
        # Arrange & Act
        decisions = [
            GenerationDecision(
                timestamp=f"2024-01-15T23:00:{i:02d}.000000",
                iteration_num=i,
                decision="llm" if i % 2 == 0 else "factor_graph",
                reason=f"Iteration {i}",
                config_snapshot={"iteration": i},
                use_factor_graph=i % 2 == 1,
                innovation_rate=100 - i,
                success=True
            )
            for i in range(10)
        ]

        # Assert
        for i, decision in enumerate(decisions):
            assert decision.iteration_num == i
            assert decision.config_snapshot["iteration"] == i
            assert decision.innovation_rate == 100 - i

    def test_audit_logging_workflow_simulation(self):
        """
        WHEN simulating the audit logging workflow from design.md
        THEN GenerationDecision should work correctly with AuditLogger pattern.

        This simulates the workflow shown in design.md lines 413-431.
        """
        # Arrange - simulate config and decision data
        config = {"use_factor_graph": False, "innovation_rate": 100}

        # Act - simulate log_decision() call
        decision = GenerationDecision(
            timestamp="2024-01-15T23:30:00.000000",
            iteration_num=120,
            decision="llm",
            reason=f"Config: use_factor_graph={config.get('use_factor_graph')}, "
                   f"innovation_rate={config.get('innovation_rate')}",
            config_snapshot=config.copy(),  # AuditLogger does config.copy()
            use_factor_graph=config.get("use_factor_graph"),
            innovation_rate=config.get("innovation_rate", 100),
            success=True,
            error=None
        )

        # Act - simulate writing to JSON log
        json_line = json.dumps(decision.to_dict()) + "\n"

        # Assert
        parsed = json.loads(json_line.strip())
        assert parsed["iteration_num"] == 120
        assert parsed["decision"] == "llm"
        assert parsed["success"] is True
        assert "Config: use_factor_graph=False" in parsed["reason"]
