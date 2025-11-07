"""Comprehensive tests for hybrid ChampionStrategy (Phase 2).

Tests coverage:
- LLM champion creation and validation
- Factor Graph champion creation and validation
- Serialization/deserialization (to_dict/from_dict)
- Backward compatibility with old LLM format
- Strategy metadata extraction (parameters and patterns)
- Edge cases and error handling
- Invalid input validation
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.learning.champion_tracker import ChampionStrategy
from src.learning.strategy_metadata import extract_dag_parameters, extract_dag_patterns


class TestLLMChampionCreation:
    """Test LLM champion creation and validation."""

    def test_llm_champion_creation_with_all_fields(self):
        """Test LLM champion creation with all fields populated."""
        champion = ChampionStrategy(
            iteration_num=10,
            generation_method="llm",
            code="# LLM strategy code",
            metrics={"sharpe_ratio": 1.5, "max_drawdown": -0.15},
            timestamp="2025-11-08T10:00:00",
            parameters={"dataset": "price:收盤價", "threshold": 0.02},
            success_patterns=["momentum", "volume_filter"]
        )

        assert champion.iteration_num == 10
        assert champion.generation_method == "llm"
        assert champion.code == "# LLM strategy code"
        assert champion.strategy_id is None
        assert champion.strategy_generation is None
        assert champion.metrics == {"sharpe_ratio": 1.5, "max_drawdown": -0.15}
        assert champion.parameters == {"dataset": "price:收盤價", "threshold": 0.02}
        assert champion.success_patterns == ["momentum", "volume_filter"]

    def test_llm_champion_creation_minimal_fields(self):
        """Test LLM champion creation with only required fields."""
        champion = ChampionStrategy(
            iteration_num=5,
            generation_method="llm",
            code="# minimal code",
            metrics={"sharpe_ratio": 1.0},
            timestamp="2025-11-08T10:00:00"
        )

        assert champion.code == "# minimal code"
        assert champion.parameters == {}  # Default empty dict
        assert champion.success_patterns == []  # Default empty list

    def test_llm_champion_validation_fails_without_code(self):
        """Test LLM champion validation fails if code is missing."""
        with pytest.raises(ValueError, match="LLM champion must have code"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="llm",
                code=None,  # Missing code!
                metrics={"sharpe_ratio": 1.5},
                timestamp="2025-11-08T10:00:00"
            )

    def test_llm_champion_validation_fails_with_empty_code(self):
        """Test LLM champion validation fails if code is empty string."""
        with pytest.raises(ValueError, match="LLM champion must have code"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="llm",
                code="",  # Empty code!
                metrics={"sharpe_ratio": 1.5},
                timestamp="2025-11-08T10:00:00"
            )

    def test_llm_champion_validation_fails_with_dag_fields(self):
        """Test LLM champion validation fails if it has Factor Graph fields."""
        with pytest.raises(ValueError, match="should not have strategy_id"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="llm",
                code="# code",
                strategy_id="momentum_v1",  # Should not have this!
                metrics={"sharpe_ratio": 1.5},
                timestamp="2025-11-08T10:00:00"
            )


class TestFactorGraphChampionCreation:
    """Test Factor Graph champion creation and validation."""

    def test_factor_graph_champion_creation_with_all_fields(self):
        """Test Factor Graph champion creation with all fields populated."""
        champion = ChampionStrategy(
            iteration_num=15,
            generation_method="factor_graph",
            strategy_id="momentum_v2",
            strategy_generation=2,
            metrics={"sharpe_ratio": 2.0, "max_drawdown": -0.12},
            timestamp="2025-11-08T11:00:00",
            parameters={"rsi_14": {"period": 14}, "ma_20": {"window": 20}},
            success_patterns=["RSI", "MA", "Signal"]
        )

        assert champion.iteration_num == 15
        assert champion.generation_method == "factor_graph"
        assert champion.code is None
        assert champion.strategy_id == "momentum_v2"
        assert champion.strategy_generation == 2
        assert champion.metrics == {"sharpe_ratio": 2.0, "max_drawdown": -0.12}
        assert champion.parameters == {"rsi_14": {"period": 14}, "ma_20": {"window": 20}}
        assert champion.success_patterns == ["RSI", "MA", "Signal"]

    def test_factor_graph_champion_creation_minimal_fields(self):
        """Test Factor Graph champion creation with only required fields."""
        champion = ChampionStrategy(
            iteration_num=20,
            generation_method="factor_graph",
            strategy_id="simple_v1",
            strategy_generation=1,
            metrics={"sharpe_ratio": 1.8},
            timestamp="2025-11-08T12:00:00"
        )

        assert champion.strategy_id == "simple_v1"
        assert champion.strategy_generation == 1
        assert champion.parameters == {}  # Default empty dict
        assert champion.success_patterns == []  # Default empty list

    def test_factor_graph_champion_validation_fails_without_strategy_id(self):
        """Test Factor Graph champion validation fails if strategy_id is missing."""
        with pytest.raises(ValueError, match="must have both strategy_id"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="factor_graph",
                strategy_id=None,  # Missing!
                strategy_generation=1,
                metrics={"sharpe_ratio": 2.0},
                timestamp="2025-11-08T11:00:00"
            )

    def test_factor_graph_champion_validation_fails_without_generation(self):
        """Test Factor Graph champion validation fails if strategy_generation is missing."""
        with pytest.raises(ValueError, match="must have both strategy_id"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="factor_graph",
                strategy_id="momentum_v1",
                strategy_generation=None,  # Missing!
                metrics={"sharpe_ratio": 2.0},
                timestamp="2025-11-08T11:00:00"
            )

    def test_factor_graph_champion_validation_fails_with_code(self):
        """Test Factor Graph champion validation fails if it has LLM code field."""
        with pytest.raises(ValueError, match="should not have code"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="factor_graph",
                strategy_id="momentum_v1",
                strategy_generation=1,
                code="# should not have this!",  # Should not have code!
                metrics={"sharpe_ratio": 2.0},
                timestamp="2025-11-08T11:00:00"
            )


class TestChampionStrategyValidation:
    """Test validation logic and error handling."""

    def test_invalid_generation_method(self):
        """Test validation fails with invalid generation_method."""
        with pytest.raises(ValueError, match="must be 'llm' or 'factor_graph'"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="invalid_method",  # Invalid!
                code="# code",
                metrics={"sharpe_ratio": 1.5},
                timestamp="2025-11-08T10:00:00"
            )

    def test_generation_method_case_sensitive(self):
        """Test generation_method is case-sensitive."""
        with pytest.raises(ValueError, match="must be 'llm' or 'factor_graph'"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="LLM",  # Wrong case!
                code="# code",
                metrics={"sharpe_ratio": 1.5},
                timestamp="2025-11-08T10:00:00"
            )

    def test_mixed_fields_llm_with_strategy_id(self):
        """Test validation fails if LLM champion has strategy_id."""
        with pytest.raises(ValueError, match="should not have strategy_id"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="llm",
                code="# code",
                strategy_id="momentum_v1",  # Mixed fields!
                metrics={"sharpe_ratio": 1.5},
                timestamp="2025-11-08T10:00:00"
            )

    def test_mixed_fields_factor_graph_with_code(self):
        """Test validation fails if Factor Graph champion has code."""
        with pytest.raises(ValueError, match="should not have code"):
            ChampionStrategy(
                iteration_num=1,
                generation_method="factor_graph",
                strategy_id="momentum_v1",
                strategy_generation=1,
                code="# code",  # Mixed fields!
                metrics={"sharpe_ratio": 2.0},
                timestamp="2025-11-08T11:00:00"
            )


class TestChampionStrategySerialization:
    """Test serialization and deserialization (to_dict/from_dict)."""

    def test_llm_champion_to_dict(self):
        """Test LLM champion serialization to dict."""
        champion = ChampionStrategy(
            iteration_num=10,
            generation_method="llm",
            code="# LLM code",
            metrics={"sharpe_ratio": 1.5},
            timestamp="2025-11-08T10:00:00",
            parameters={"param1": "value1"},
            success_patterns=["pattern1"]
        )

        data = champion.to_dict()

        assert data["iteration_num"] == 10
        assert data["generation_method"] == "llm"
        assert data["code"] == "# LLM code"
        assert data["strategy_id"] is None
        assert data["strategy_generation"] is None
        assert data["parameters"] == {"param1": "value1"}
        assert data["metrics"] == {"sharpe_ratio": 1.5}

    def test_factor_graph_champion_to_dict(self):
        """Test Factor Graph champion serialization to dict."""
        champion = ChampionStrategy(
            iteration_num=15,
            generation_method="factor_graph",
            strategy_id="momentum_v2",
            strategy_generation=2,
            metrics={"sharpe_ratio": 2.0},
            timestamp="2025-11-08T11:00:00",
            parameters={"rsi": {"period": 14}},
            success_patterns=["RSI", "Signal"]
        )

        data = champion.to_dict()

        assert data["generation_method"] == "factor_graph"
        assert data["code"] is None
        assert data["strategy_id"] == "momentum_v2"
        assert data["strategy_generation"] == 2
        assert data["parameters"] == {"rsi": {"period": 14}}

    def test_llm_champion_from_dict(self):
        """Test LLM champion deserialization from dict."""
        data = {
            "iteration_num": 10,
            "generation_method": "llm",
            "code": "# test code",
            "strategy_id": None,
            "strategy_generation": None,
            "parameters": {"param1": "value1"},
            "metrics": {"sharpe_ratio": 1.5},
            "success_patterns": ["pattern1"],
            "timestamp": "2025-11-08T10:00:00"
        }

        champion = ChampionStrategy.from_dict(data)

        assert champion.generation_method == "llm"
        assert champion.code == "# test code"
        assert champion.strategy_id is None
        assert champion.parameters == {"param1": "value1"}

    def test_factor_graph_champion_from_dict(self):
        """Test Factor Graph champion deserialization from dict."""
        data = {
            "iteration_num": 15,
            "generation_method": "factor_graph",
            "code": None,
            "strategy_id": "momentum_v2",
            "strategy_generation": 2,
            "parameters": {"rsi": {"period": 14}},
            "metrics": {"sharpe_ratio": 2.0},
            "success_patterns": ["RSI"],
            "timestamp": "2025-11-08T11:00:00"
        }

        champion = ChampionStrategy.from_dict(data)

        assert champion.generation_method == "factor_graph"
        assert champion.code is None
        assert champion.strategy_id == "momentum_v2"
        assert champion.strategy_generation == 2

    def test_serialization_roundtrip_llm(self):
        """Test LLM champion serialization roundtrip (to_dict → from_dict)."""
        original = ChampionStrategy(
            iteration_num=10,
            generation_method="llm",
            code="# original code",
            metrics={"sharpe_ratio": 1.5, "max_drawdown": -0.15},
            timestamp="2025-11-08T10:00:00",
            parameters={"param1": "value1"},
            success_patterns=["pattern1", "pattern2"]
        )

        # Roundtrip
        data = original.to_dict()
        restored = ChampionStrategy.from_dict(data)

        assert restored.generation_method == original.generation_method
        assert restored.code == original.code
        assert restored.metrics == original.metrics
        assert restored.parameters == original.parameters
        assert restored.success_patterns == original.success_patterns

    def test_serialization_roundtrip_factor_graph(self):
        """Test Factor Graph champion serialization roundtrip."""
        original = ChampionStrategy(
            iteration_num=15,
            generation_method="factor_graph",
            strategy_id="momentum_v2",
            strategy_generation=2,
            metrics={"sharpe_ratio": 2.0, "max_drawdown": -0.12},
            timestamp="2025-11-08T11:00:00",
            parameters={"rsi": {"period": 14}},
            success_patterns=["RSI", "Signal"]
        )

        # Roundtrip
        data = original.to_dict()
        restored = ChampionStrategy.from_dict(data)

        assert restored.generation_method == original.generation_method
        assert restored.strategy_id == original.strategy_id
        assert restored.strategy_generation == original.strategy_generation
        assert restored.metrics == original.metrics


class TestBackwardCompatibility:
    """Test backward compatibility with old LLM champion format."""

    def test_backward_compatibility_old_llm_format(self):
        """Test loading old format LLM champion (no generation_method field)."""
        old_data = {
            "iteration_num": 5,
            "code": "# old format code",
            "parameters": {"param1": "value1"},
            "metrics": {"sharpe_ratio": 1.5},
            "success_patterns": ["pattern1"],
            "timestamp": "2025-11-08T10:00:00"
        }

        champion = ChampionStrategy.from_dict(old_data)

        # Should infer generation_method="llm"
        assert champion.generation_method == "llm"
        assert champion.code == "# old format code"
        assert champion.strategy_id is None
        assert champion.strategy_generation is None

    def test_backward_compatibility_missing_optional_fields(self):
        """Test loading old format with missing optional fields."""
        old_data = {
            "iteration_num": 5,
            "code": "# code",
            "metrics": {"sharpe_ratio": 1.5},
            "timestamp": "2025-11-08T10:00:00"
            # Missing: parameters, success_patterns
        }

        champion = ChampionStrategy.from_dict(old_data)

        # Should default to empty dict/list
        assert champion.parameters == {}
        assert champion.success_patterns == []

    def test_backward_compatibility_success_patterns_none(self):
        """Test loading old format where success_patterns is None."""
        old_data = {
            "iteration_num": 5,
            "code": "# code",
            "parameters": {},
            "metrics": {"sharpe_ratio": 1.5},
            "success_patterns": None,  # Old format might have None
            "timestamp": "2025-11-08T10:00:00"
        }

        champion = ChampionStrategy.from_dict(old_data)

        # Should convert None to empty list
        assert champion.success_patterns == []

    def test_new_format_explicit_generation_method(self):
        """Test loading new format with explicit generation_method doesn't get modified."""
        new_data = {
            "iteration_num": 10,
            "generation_method": "factor_graph",
            "strategy_id": "momentum_v1",
            "strategy_generation": 1,
            "metrics": {"sharpe_ratio": 2.0},
            "timestamp": "2025-11-08T11:00:00"
        }

        champion = ChampionStrategy.from_dict(new_data)

        # Should preserve explicit generation_method
        assert champion.generation_method == "factor_graph"
        assert champion.strategy_id == "momentum_v1"


class TestStrategyMetadataExtraction:
    """Test Strategy DAG metadata extraction functions."""

    def test_extract_dag_parameters_with_params(self):
        """Test extract_dag_parameters with factors having params."""
        # Mock Strategy with factors
        mock_strategy = Mock()
        mock_factor1 = Mock()
        mock_factor1.params = {"period": 14, "overbought": 70}
        mock_factor2 = Mock()
        mock_factor2.params = {"window": 20}

        mock_strategy.factors = {
            "rsi_14": mock_factor1,
            "ma_20": mock_factor2
        }

        params = extract_dag_parameters(mock_strategy)

        assert params == {
            "rsi_14": {"period": 14, "overbought": 70},
            "ma_20": {"window": 20}
        }

    def test_extract_dag_parameters_empty_params(self):
        """Test extract_dag_parameters with factors having empty params."""
        mock_strategy = Mock()
        mock_factor1 = Mock()
        mock_factor1.params = {}  # Empty params
        mock_factor2 = Mock()
        mock_factor2.params = None  # None params

        mock_strategy.factors = {
            "factor1": mock_factor1,
            "factor2": mock_factor2
        }

        params = extract_dag_parameters(mock_strategy)

        # Should skip factors with empty/None params
        assert params == {}

    def test_extract_dag_parameters_no_factors(self):
        """Test extract_dag_parameters with strategy having no factors."""
        mock_strategy = Mock()
        mock_strategy.factors = {}

        params = extract_dag_parameters(mock_strategy)

        assert params == {}

    def test_extract_dag_patterns_multiple_types(self):
        """Test extract_dag_patterns with multiple factor types."""
        # Mock Strategy with different factor types
        mock_strategy = Mock()

        mock_rsi = Mock()
        type(mock_rsi).__name__ = "RSI"

        mock_ma = Mock()
        type(mock_ma).__name__ = "MA"

        mock_signal = Mock()
        type(mock_signal).__name__ = "Signal"

        mock_strategy.factors = {
            "rsi_14": mock_rsi,
            "ma_20": mock_ma,
            "entry_signal": mock_signal
        }

        patterns = extract_dag_patterns(mock_strategy)

        # Should be sorted and unique
        assert patterns == ["MA", "RSI", "Signal"]

    def test_extract_dag_patterns_duplicate_types(self):
        """Test extract_dag_patterns with duplicate factor types."""
        mock_strategy = Mock()

        mock_rsi1 = Mock()
        type(mock_rsi1).__name__ = "RSI"

        mock_rsi2 = Mock()
        type(mock_rsi2).__name__ = "RSI"

        mock_strategy.factors = {
            "rsi_14": mock_rsi1,
            "rsi_21": mock_rsi2
        }

        patterns = extract_dag_patterns(mock_strategy)

        # Should deduplicate
        assert patterns == ["RSI"]

    def test_extract_dag_patterns_empty_strategy(self):
        """Test extract_dag_patterns with empty strategy."""
        mock_strategy = Mock()
        mock_strategy.factors = {}

        patterns = extract_dag_patterns(mock_strategy)

        assert patterns == []


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_metrics_dict(self):
        """Test champion creation with empty metrics dict."""
        champion = ChampionStrategy(
            iteration_num=1,
            generation_method="llm",
            code="# code",
            metrics={},  # Empty metrics
            timestamp="2025-11-08T10:00:00"
        )

        assert champion.metrics == {}

    def test_very_long_code_string(self):
        """Test LLM champion with very long code string."""
        long_code = "# " + "x" * 10000  # 10KB code string

        champion = ChampionStrategy(
            iteration_num=1,
            generation_method="llm",
            code=long_code,
            metrics={"sharpe_ratio": 1.5},
            timestamp="2025-11-08T10:00:00"
        )

        assert len(champion.code) > 10000

    def test_strategy_generation_zero(self):
        """Test Factor Graph champion with strategy_generation=0."""
        champion = ChampionStrategy(
            iteration_num=1,
            generation_method="factor_graph",
            strategy_id="initial",
            strategy_generation=0,  # Generation 0 is valid
            metrics={"sharpe_ratio": 1.5},
            timestamp="2025-11-08T10:00:00"
        )

        assert champion.strategy_generation == 0

    def test_negative_metrics_values(self):
        """Test champion with negative metric values (e.g., max_drawdown)."""
        champion = ChampionStrategy(
            iteration_num=1,
            generation_method="llm",
            code="# code",
            metrics={
                "sharpe_ratio": 1.5,
                "max_drawdown": -0.25,  # Negative is valid
                "calmar_ratio": -0.5    # Negative is valid
            },
            timestamp="2025-11-08T10:00:00"
        )

        assert champion.metrics["max_drawdown"] == -0.25
        assert champion.metrics["calmar_ratio"] == -0.5
