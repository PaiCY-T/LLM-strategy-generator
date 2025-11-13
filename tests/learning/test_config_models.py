# tests/learning/test_config_models.py
"""
Phase 2 TDD Test Suite: Pydantic Configuration Validation

Tests for config_models.py GenerationConfig Pydantic model:
- Field validation: innovation_rate range constraints (0-100)
- Configuration conflict detection (REQ-1.3)
- should_use_llm() priority logic (same as Phase 1)
- Type validation through Pydantic
- Default value handling

These tests are written against the DESIRED behavior for Phase 2 Pydantic implementation.
They define the contract for the GenerationConfig model before implementation.

Key Assertions:
1. Pydantic Field validation enforces innovation_rate range (0-100)
2. Model validator detects conflicts: use_factor_graph=True + innovation_rate=100
3. should_use_llm() method implements same priority logic as Phase 1
4. Type validation is automatic through Pydantic
5. Default values: innovation_rate=100, use_factor_graph=None
"""

import random
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.learning.config_models import GenerationConfig


class TestFieldValidation:
    """
    TDD Tests for Pydantic Field validation.

    These tests verify that Pydantic enforces the field constraints:
    - innovation_rate: Annotated[int, Field(ge=0, le=100)]
    - use_factor_graph: Optional[bool]
    """

    @pytest.mark.parametrize(
        "innovation_rate, use_factor_graph",
        [
            pytest.param(0, None, id="min_innovation_rate_boundary"),
            pytest.param(50, None, id="mid_innovation_rate"),
            pytest.param(100, False, id="max_innovation_rate_boundary_non_conflict"),
            pytest.param(50, True, id="innovation_rate_with_use_factor_graph_true"),
            pytest.param(50, False, id="innovation_rate_with_use_factor_graph_false"),
        ],
    )
    def test_valid_field_values(self, innovation_rate, use_factor_graph):
        """
        WHEN GenerationConfig is created with valid field values
        THEN the model should be instantiated successfully.
        """
        # Act
        config = GenerationConfig(
            innovation_rate=innovation_rate,
            use_factor_graph=use_factor_graph
        )

        # Assert
        assert config.innovation_rate == innovation_rate
        assert config.use_factor_graph == use_factor_graph

    @pytest.mark.parametrize(
        "innovation_rate, error_match",
        [
            pytest.param(-1, "greater than or equal to 0", id="below_minimum"),
            pytest.param(101, "less than or equal to 100", id="above_maximum"),
            pytest.param(-10, "greater than or equal to 0", id="far_below_minimum"),
            pytest.param(200, "less than or equal to 100", id="far_above_maximum"),
        ],
    )
    def test_invalid_innovation_rate_range(self, innovation_rate, error_match):
        """
        WHEN GenerationConfig is created with out-of-range innovation_rate
        THEN Pydantic ValidationError should be raised.
        """
        # Act & Assert
        with pytest.raises(ValidationError, match=error_match):
            GenerationConfig(innovation_rate=innovation_rate)

    @pytest.mark.parametrize(
        "innovation_rate_value, expected_error",
        [
            pytest.param("50", "Input should be a valid integer", id="string_type"),
            pytest.param(50.5, "Input should be a valid integer", id="float_type"),
            pytest.param(None, "Input should be a valid integer", id="none_value"),
        ],
    )
    def test_invalid_innovation_rate_type(self, innovation_rate_value, expected_error):
        """
        WHEN GenerationConfig is created with wrong type for innovation_rate
        THEN Pydantic ValidationError should be raised.
        """
        # Act & Assert
        with pytest.raises(ValidationError, match=expected_error):
            GenerationConfig(innovation_rate=innovation_rate_value)

    @pytest.mark.parametrize(
        "use_factor_graph_value, expected_error",
        [
            pytest.param("true", "Input should be a valid boolean", id="string_type"),
            pytest.param(1, "Input should be a valid boolean", id="integer_type"),
            pytest.param(0, "Input should be a valid boolean", id="zero_integer"),
        ],
    )
    def test_invalid_use_factor_graph_type(self, use_factor_graph_value, expected_error):
        """
        WHEN GenerationConfig is created with wrong type for use_factor_graph
        THEN Pydantic ValidationError should be raised.
        """
        # Act & Assert
        with pytest.raises(ValidationError, match=expected_error):
            GenerationConfig(use_factor_graph=use_factor_graph_value)


class TestDefaultValues:
    """
    TDD Tests for default value initialization.

    These tests verify that GenerationConfig uses correct defaults:
    - innovation_rate: 100
    - use_factor_graph: None
    """

    def test_empty_config_defaults(self):
        """
        WHEN GenerationConfig is created with no parameters
        THEN it should use default values.
        """
        # Act
        config = GenerationConfig()

        # Assert
        assert config.innovation_rate == 100
        assert config.use_factor_graph is None

    def test_partial_config_use_factor_graph_only(self):
        """
        WHEN GenerationConfig is created with only use_factor_graph
        THEN innovation_rate should default to 100.
        """
        # Act
        config = GenerationConfig(use_factor_graph=False)

        # Assert
        assert config.innovation_rate == 100
        assert config.use_factor_graph is False

    def test_partial_config_innovation_rate_only(self):
        """
        WHEN GenerationConfig is created with only innovation_rate
        THEN use_factor_graph should default to None.
        """
        # Act
        config = GenerationConfig(innovation_rate=50)

        # Assert
        assert config.innovation_rate == 50
        assert config.use_factor_graph is None


class TestConfigurationConflicts:
    """
    TDD Tests for configuration conflict detection (REQ-1.3).

    These tests verify that the @model_validator detects logically incompatible
    settings and raises ValueError with descriptive messages.
    """

    def test_raises_on_primary_conflict(self):
        """
        WHEN use_factor_graph=True AND innovation_rate=100
        THEN ValueError should be raised (configuration conflict).

        This is the primary conflict: forcing factor graph while also
        forcing LLM (innovation_rate=100).
        """
        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Configuration conflict.*use_factor_graph=True.*innovation_rate=100"
        ):
            GenerationConfig(use_factor_graph=True, innovation_rate=100)

    def test_raises_on_default_innovation_rate_conflict(self):
        """
        WHEN use_factor_graph=True AND innovation_rate is defaulted (100)
        THEN ValueError should be raised.

        This tests that the validator catches conflicts even when
        innovation_rate uses its default value.
        """
        # Act & Assert
        with pytest.raises(
            ValueError,
            match="Configuration conflict.*use_factor_graph=True.*innovation_rate=100"
        ):
            GenerationConfig(use_factor_graph=True)

    @pytest.mark.parametrize(
        "use_factor_graph, innovation_rate",
        [
            pytest.param(True, 0, id="use_factor_graph_true_with_zero"),
            pytest.param(True, 50, id="use_factor_graph_true_with_fifty"),
            pytest.param(False, 100, id="use_factor_graph_false_with_hundred"),
            pytest.param(False, 0, id="use_factor_graph_false_with_zero"),
            pytest.param(None, 100, id="use_factor_graph_none_with_hundred"),
            pytest.param(None, 0, id="use_factor_graph_none_with_zero"),
        ],
    )
    def test_non_conflicting_configurations(self, use_factor_graph, innovation_rate):
        """
        WHEN configuration does not contain the specific conflict
        THEN GenerationConfig should be created successfully.

        Only use_factor_graph=True + innovation_rate=100 is a conflict.
        All other combinations are valid.
        """
        # Act
        config = GenerationConfig(
            use_factor_graph=use_factor_graph,
            innovation_rate=innovation_rate
        )

        # Assert
        assert config.use_factor_graph == use_factor_graph
        assert config.innovation_rate == innovation_rate


class TestShouldUseLLMMethod:
    """
    TDD Tests for should_use_llm() business logic.

    These tests verify the priority-based decision logic:
    1. use_factor_graph takes absolute priority (deterministic)
    2. Fallback to probabilistic decision based on innovation_rate

    This is the same logic as Phase 1 _decide_generation_method(),
    but encapsulated in the Pydantic model.
    """

    @pytest.mark.parametrize(
        "use_factor_graph, innovation_rate, expected_result",
        [
            # Priority: use_factor_graph=True → LLM NOT used (False)
            pytest.param(True, 0, False, id="use_factor_graph_true_overrides_zero"),
            pytest.param(True, 50, False, id="use_factor_graph_true_overrides_fifty"),
            # Note: use_factor_graph=True + innovation_rate=100 would raise ValueError in __init__

            # Priority: use_factor_graph=False → LLM used (True)
            pytest.param(False, 0, True, id="use_factor_graph_false_overrides_zero"),
            pytest.param(False, 50, True, id="use_factor_graph_false_overrides_fifty"),
            pytest.param(False, 100, True, id="use_factor_graph_false_overrides_hundred"),
        ],
    )
    def test_use_factor_graph_has_priority(self, use_factor_graph, innovation_rate, expected_result):
        """
        WHEN use_factor_graph is explicitly set (True or False)
        THEN should_use_llm() must return the deterministic result
        regardless of innovation_rate value.
        """
        # Arrange
        config = GenerationConfig(
            use_factor_graph=use_factor_graph,
            innovation_rate=innovation_rate
        )

        # Act
        result = config.should_use_llm()

        # Assert
        assert result is expected_result

    @patch("random.random")
    @pytest.mark.parametrize(
        "random_value, innovation_rate, expected_result",
        [
            # Probabilistic decision when use_factor_graph=None
            pytest.param(0.00, 0, False, id="random_0.00_innovation_0_no_llm"),
            pytest.param(0.99, 100, True, id="random_0.99_innovation_100_use_llm"),
            pytest.param(0.49, 50, True, id="random_0.49_innovation_50_use_llm"),
            pytest.param(0.51, 50, False, id="random_0.51_innovation_50_no_llm"),
            pytest.param(0.50, 50, False, id="random_0.50_innovation_50_boundary_no_llm"),
        ],
    )
    def test_probabilistic_decision_when_use_factor_graph_none(
        self, mock_random, random_value, innovation_rate, expected_result
    ):
        """
        WHEN use_factor_graph is None
        THEN should_use_llm() must make probabilistic decision
        based on innovation_rate.

        Logic: random.random() * 100 < innovation_rate → use LLM
        """
        # Arrange
        mock_random.return_value = random_value
        config = GenerationConfig(
            use_factor_graph=None,
            innovation_rate=innovation_rate
        )

        # Act
        result = config.should_use_llm()

        # Assert
        assert result is expected_result
        mock_random.assert_called_once()

    def test_default_config_probabilistic_behavior(self):
        """
        WHEN GenerationConfig uses default values
        THEN should_use_llm() should use probabilistic logic
        with innovation_rate=100.

        Since innovation_rate defaults to 100, this should almost
        always return True (use LLM).
        """
        # Arrange
        config = GenerationConfig()

        # Act - call multiple times to verify probabilistic behavior
        results = [config.should_use_llm() for _ in range(10)]

        # Assert - with innovation_rate=100, should mostly be True
        # (We expect at least 8 out of 10 to be True)
        assert sum(results) >= 8


class TestModelIntegration:
    """
    Integration tests for GenerationConfig model.

    These tests verify end-to-end behavior and edge cases.
    """

    def test_model_immutability_after_creation(self):
        """
        WHEN GenerationConfig is created with values
        THEN the fields should be readable but the model
        should maintain Pydantic's validation on assignment.
        """
        # Arrange
        config = GenerationConfig(use_factor_graph=False, innovation_rate=50)

        # Act & Assert - fields are readable
        assert config.use_factor_graph is False
        assert config.innovation_rate == 50

        # Pydantic v2 allows assignment but validates
        config.innovation_rate = 75
        assert config.innovation_rate == 75

        # Invalid assignment should raise ValidationError
        with pytest.raises(ValidationError):
            config.innovation_rate = 150

    def test_model_dict_export(self):
        """
        WHEN GenerationConfig.model_dump() is called
        THEN it should export the configuration as a dictionary.
        """
        # Arrange
        config = GenerationConfig(use_factor_graph=True, innovation_rate=50)

        # Act
        config_dict = config.model_dump()

        # Assert
        assert config_dict == {
            "use_factor_graph": True,
            "innovation_rate": 50
        }

    def test_model_json_serialization(self):
        """
        WHEN GenerationConfig.model_dump_json() is called
        THEN it should serialize the model to JSON string.
        """
        # Arrange
        config = GenerationConfig(use_factor_graph=False, innovation_rate=75)

        # Act
        json_str = config.model_dump_json()

        # Assert
        import json
        parsed = json.loads(json_str)
        assert parsed["use_factor_graph"] is False
        assert parsed["innovation_rate"] == 75

    def test_model_from_dict(self):
        """
        WHEN GenerationConfig is created from a dictionary
        THEN it should validate and construct the model.
        """
        # Arrange
        config_dict = {
            "use_factor_graph": True,
            "innovation_rate": 25
        }

        # Act
        config = GenerationConfig(**config_dict)

        # Assert
        assert config.use_factor_graph is True
        assert config.innovation_rate == 25
