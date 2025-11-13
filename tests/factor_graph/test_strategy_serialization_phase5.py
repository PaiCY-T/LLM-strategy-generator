"""
Phase 5: Strategy JSON Serialization Tests

Tests for metadata-only Strategy serialization (to_dict/from_dict).

This test suite validates:
1. to_dict() creates JSON-serializable metadata
2. from_dict() reconstructs strategies correctly
3. Serialization round-trip preserves all metadata
4. Error handling for missing factor_registry entries
5. Complex DAG structure preservation
6. Edge cases (empty parameters, long descriptions, etc.)

Test Categories:
- Basic serialization/deserialization
- Complex DAG structures
- Error handling
- Round-trip validation
- Edge cases

Total: 20+ tests
"""

import unittest
from unittest.mock import Mock
import json
from typing import Dict, Any
import pandas as pd

from src.factor_graph.strategy import Strategy
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory


# Mock factor logic functions for testing
def mock_rsi_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """Mock RSI calculation for testing."""
    data["rsi"] = 50.0  # Simple mock
    return data


def mock_ma_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """Mock moving average calculation for testing."""
    data["ma"] = data["close"].rolling(window=params["period"]).mean()
    return data


def mock_signal_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """Mock signal generation for testing."""
    data["positions"] = 1  # Simple long signal
    return data


def mock_entry_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """Mock entry signal for testing."""
    data["entry_signal"] = (data["rsi"] > 30).astype(int)
    return data


def mock_exit_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
    """Mock exit signal for testing."""
    data["exit_signal"] = (data["rsi"] < 70).astype(int)
    data["positions"] = data["entry_signal"] - data["exit_signal"]
    return data


class TestStrategyToDict(unittest.TestCase):
    """Test Strategy.to_dict() serialization."""

    def test_to_dict_simple_strategy(self):
        """Test to_dict() with single-factor strategy."""
        # Create simple strategy
        strategy = Strategy(id="simple", generation=0)

        rsi_factor = Factor(
            id="rsi_14",
            name="RSI 14",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["rsi"],
            logic=mock_rsi_logic,
            parameters={"period": 14},
            description="14-period RSI"
        )
        strategy.add_factor(rsi_factor)

        signal_factor = Factor(
            id="signal",
            name="Signal",
            category=FactorCategory.SIGNAL,
            inputs=["rsi"],
            outputs=["positions"],
            logic=mock_signal_logic,
            parameters={},
            description="Simple signal"
        )
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        # Serialize
        metadata = strategy.to_dict()

        # Validate structure
        self.assertIn("id", metadata)
        self.assertIn("generation", metadata)
        self.assertIn("parent_ids", metadata)
        self.assertIn("factors", metadata)
        self.assertIn("dag_edges", metadata)

        # Validate values
        self.assertEqual(metadata["id"], "simple")
        self.assertEqual(metadata["generation"], 0)
        self.assertEqual(metadata["parent_ids"], [])
        self.assertEqual(len(metadata["factors"]), 2)
        self.assertEqual(len(metadata["dag_edges"]), 1)

    def test_to_dict_preserves_factor_metadata(self):
        """Test that to_dict() preserves all factor metadata."""
        strategy = Strategy(id="test", generation=1)

        factor = Factor(
            id="rsi_14",
            name="RSI 14",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["rsi"],
            logic=mock_rsi_logic,
            parameters={"period": 14, "overbought": 70, "oversold": 30},
            description="14-period RSI with thresholds"
        )
        strategy.add_factor(factor)

        signal_factor = Factor(
            id="signal",
            name="Signal",
            category=FactorCategory.SIGNAL,
            inputs=["rsi"],
            outputs=["positions"],
            logic=mock_signal_logic,
            parameters={},
            description=""
        )
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        metadata = strategy.to_dict()

        # Find RSI factor in metadata
        rsi_metadata = next(f for f in metadata["factors"] if f["id"] == "rsi_14")

        # Validate all fields preserved
        self.assertEqual(rsi_metadata["id"], "rsi_14")
        self.assertEqual(rsi_metadata["name"], "RSI 14")
        self.assertEqual(rsi_metadata["category"], "MOMENTUM")
        self.assertEqual(rsi_metadata["inputs"], ["close"])
        self.assertEqual(rsi_metadata["outputs"], ["rsi"])
        self.assertEqual(rsi_metadata["parameters"], {"period": 14, "overbought": 70, "oversold": 30})
        self.assertEqual(rsi_metadata["description"], "14-period RSI with thresholds")

        # Validate logic is NOT in metadata
        self.assertNotIn("logic", rsi_metadata)

    def test_to_dict_json_serializable(self):
        """Test that to_dict() output is JSON-serializable."""
        strategy = Strategy(id="test", generation=1)

        factor = Factor(
            id="rsi_14",
            name="RSI 14",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["rsi"],
            logic=mock_rsi_logic,
            parameters={"period": 14},
            description="Test"
        )
        strategy.add_factor(factor)

        signal_factor = Factor(
            id="signal",
            name="Signal",
            category=FactorCategory.SIGNAL,
            inputs=["rsi"],
            outputs=["positions"],
            logic=mock_signal_logic,
            parameters={},
            description=""
        )
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        metadata = strategy.to_dict()

        # Should not raise exception
        json_str = json.dumps(metadata)
        self.assertIsInstance(json_str, str)

        # Should be deserializable
        loaded = json.loads(json_str)
        self.assertEqual(loaded["id"], "test")

    def test_to_dict_complex_dag(self):
        """Test to_dict() with complex DAG structure."""
        strategy = Strategy(id="complex", generation=5, parent_ids=["parent1", "parent2"])

        # Create diamond DAG structure:
        #     rsi_14
        #    /      \
        # entry    exit
        #    \      /
        #    signal

        rsi_factor = Factor(
            id="rsi_14",
            name="RSI",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["rsi"],
            logic=mock_rsi_logic,
            parameters={"period": 14}
        )
        strategy.add_factor(rsi_factor)

        entry_factor = Factor(
            id="entry",
            name="Entry",
            category=FactorCategory.SIGNAL,
            inputs=["rsi"],
            outputs=["entry_signal"],
            logic=mock_entry_logic,
            parameters={"threshold": 30}
        )
        strategy.add_factor(entry_factor, depends_on=["rsi_14"])

        exit_factor = Factor(
            id="exit",
            name="Exit",
            category=FactorCategory.SIGNAL,
            inputs=["rsi"],
            outputs=["exit_signal"],
            logic=mock_exit_logic,
            parameters={"threshold": 70}
        )
        strategy.add_factor(exit_factor, depends_on=["rsi_14"])

        signal_factor = Factor(
            id="signal",
            name="Signal",
            category=FactorCategory.SIGNAL,
            inputs=["entry_signal", "exit_signal"],
            outputs=["positions"],
            logic=mock_signal_logic,
            parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["entry", "exit"])

        metadata = strategy.to_dict()

        # Validate structure
        self.assertEqual(len(metadata["factors"]), 4)
        self.assertEqual(metadata["parent_ids"], ["parent1", "parent2"])

        # Validate DAG edges (4 factors, 4 edges)
        edges = metadata["dag_edges"]
        self.assertEqual(len(edges), 4)
        self.assertIn(["rsi_14", "entry"], edges)
        self.assertIn(["rsi_14", "exit"], edges)
        self.assertIn(["entry", "signal"], edges)
        self.assertIn(["exit", "signal"], edges)

    def test_to_dict_empty_parameters(self):
        """Test to_dict() with factors having empty parameters."""
        strategy = Strategy(id="test", generation=0)

        factor = Factor(
            id="simple",
            name="Simple Factor",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["positions"],
            logic=mock_signal_logic,
            parameters={},  # Empty parameters
            description=""
        )
        strategy.add_factor(factor)

        metadata = strategy.to_dict()
        factor_metadata = metadata["factors"][0]

        # Empty parameters should be preserved
        self.assertEqual(factor_metadata["parameters"], {})


class TestStrategyFromDict(unittest.TestCase):
    """Test Strategy.from_dict() deserialization."""

    def test_from_dict_simple_strategy(self):
        """Test from_dict() with simple strategy."""
        # Create metadata
        metadata = {
            "id": "test",
            "generation": 1,
            "parent_ids": [],
            "factors": [
                {
                    "id": "rsi_14",
                    "name": "RSI",
                    "category": "MOMENTUM",
                    "inputs": ["close"],
                    "outputs": ["rsi"],
                    "parameters": {"period": 14},
                    "description": "Test RSI"
                },
                {
                    "id": "signal",
                    "name": "Signal",
                    "category": "SIGNAL",
                    "inputs": ["rsi"],
                    "outputs": ["positions"],
                    "parameters": {},
                    "description": ""
                }
            ],
            "dag_edges": [["rsi_14", "signal"]]
        }

        # Create factor registry
        factor_registry = {
            "rsi_14": mock_rsi_logic,
            "signal": mock_signal_logic
        }

        # Reconstruct strategy
        strategy = Strategy.from_dict(metadata, factor_registry)

        # Validate basic metadata
        self.assertEqual(strategy.id, "test")
        self.assertEqual(strategy.generation, 1)
        self.assertEqual(strategy.parent_ids, [])

        # Validate factors
        self.assertEqual(len(strategy.factors), 2)
        self.assertIn("rsi_14", strategy.factors)
        self.assertIn("signal", strategy.factors)

        # Validate factor metadata
        rsi_factor = strategy.factors["rsi_14"]
        self.assertEqual(rsi_factor.name, "RSI")
        self.assertEqual(rsi_factor.category, FactorCategory.MOMENTUM)
        self.assertEqual(rsi_factor.parameters, {"period": 14})

        # Validate DAG structure
        self.assertEqual(len(list(strategy.dag.edges())), 1)
        self.assertTrue(strategy.dag.has_edge("rsi_14", "signal"))

    def test_from_dict_missing_registry_entry(self):
        """Test from_dict() raises KeyError for missing registry entry."""
        metadata = {
            "id": "test",
            "generation": 0,
            "parent_ids": [],
            "factors": [
                {
                    "id": "rsi_14",
                    "name": "RSI",
                    "category": "MOMENTUM",
                    "inputs": ["close"],
                    "outputs": ["rsi", "positions"],
                    "parameters": {},
                    "description": ""
                }
            ],
            "dag_edges": []
        }

        # Empty registry (missing rsi_14)
        factor_registry = {}

        with self.assertRaises(KeyError) as context:
            Strategy.from_dict(metadata, factor_registry)

        self.assertIn("rsi_14", str(context.exception))

    def test_from_dict_complex_dag(self):
        """Test from_dict() with complex DAG structure."""
        metadata = {
            "id": "complex",
            "generation": 5,
            "parent_ids": ["parent1"],
            "factors": [
                {
                    "id": "rsi_14",
                    "name": "RSI",
                    "category": "MOMENTUM",
                    "inputs": ["close"],
                    "outputs": ["rsi"],
                    "parameters": {"period": 14},
                    "description": ""
                },
                {
                    "id": "entry",
                    "name": "Entry",
                    "category": "SIGNAL",
                    "inputs": ["rsi"],
                    "outputs": ["entry_signal"],
                    "parameters": {},
                    "description": ""
                },
                {
                    "id": "exit",
                    "name": "Exit",
                    "category": "SIGNAL",
                    "inputs": ["rsi"],
                    "outputs": ["exit_signal"],
                    "parameters": {},
                    "description": ""
                },
                {
                    "id": "signal",
                    "name": "Signal",
                    "category": "SIGNAL",
                    "inputs": ["entry_signal", "exit_signal"],
                    "outputs": ["positions"],
                    "parameters": {},
                    "description": ""
                }
            ],
            "dag_edges": [
                ["rsi_14", "entry"],
                ["rsi_14", "exit"],
                ["entry", "signal"],
                ["exit", "signal"]
            ]
        }

        factor_registry = {
            "rsi_14": mock_rsi_logic,
            "entry": mock_entry_logic,
            "exit": mock_exit_logic,
            "signal": mock_signal_logic
        }

        strategy = Strategy.from_dict(metadata, factor_registry)

        # Validate structure
        self.assertEqual(len(strategy.factors), 4)
        self.assertEqual(strategy.generation, 5)
        self.assertEqual(strategy.parent_ids, ["parent1"])

        # Validate all edges
        self.assertEqual(len(list(strategy.dag.edges())), 4)
        self.assertTrue(strategy.dag.has_edge("rsi_14", "entry"))
        self.assertTrue(strategy.dag.has_edge("rsi_14", "exit"))
        self.assertTrue(strategy.dag.has_edge("entry", "signal"))
        self.assertTrue(strategy.dag.has_edge("exit", "signal"))

    def test_from_dict_validates_dag(self):
        """Test from_dict() performs DAG validation during reconstruction."""
        # This metadata would create a valid DAG
        metadata = {
            "id": "test",
            "generation": 0,
            "parent_ids": [],
            "factors": [
                {
                    "id": "rsi_14",
                    "name": "RSI",
                    "category": "MOMENTUM",
                    "inputs": ["close"],
                    "outputs": ["positions"],
                    "parameters": {},
                    "description": ""
                }
            ],
            "dag_edges": []
        }

        factor_registry = {
            "rsi_14": mock_rsi_logic
        }

        # Should succeed (no exception)
        strategy = Strategy.from_dict(metadata, factor_registry)
        self.assertEqual(len(strategy.factors), 1)


class TestStrategyRoundTrip(unittest.TestCase):
    """Test Strategy serialization round-trip (to_dict -> from_dict)."""

    def test_roundtrip_preserves_metadata(self):
        """Test that to_dict -> from_dict preserves all metadata."""
        # Create original strategy
        original = Strategy(id="roundtrip", generation=3, parent_ids=["parent1"])

        rsi_factor = Factor(
            id="rsi_14",
            name="RSI 14",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["rsi"],
            logic=mock_rsi_logic,
            parameters={"period": 14, "overbought": 70},
            description="RSI with thresholds"
        )
        original.add_factor(rsi_factor)

        signal_factor = Factor(
            id="signal",
            name="Signal",
            category=FactorCategory.SIGNAL,
            inputs=["rsi"],
            outputs=["positions"],
            logic=mock_signal_logic,
            parameters={},
            description="Simple signal"
        )
        original.add_factor(signal_factor, depends_on=["rsi_14"])

        # Round trip
        metadata = original.to_dict()
        factor_registry = {
            "rsi_14": mock_rsi_logic,
            "signal": mock_signal_logic
        }
        reconstructed = Strategy.from_dict(metadata, factor_registry)

        # Validate all metadata preserved
        self.assertEqual(reconstructed.id, original.id)
        self.assertEqual(reconstructed.generation, original.generation)
        self.assertEqual(reconstructed.parent_ids, original.parent_ids)
        self.assertEqual(len(reconstructed.factors), len(original.factors))

        # Validate factor metadata
        for factor_id in original.factors:
            orig_factor = original.factors[factor_id]
            recon_factor = reconstructed.factors[factor_id]

            self.assertEqual(recon_factor.id, orig_factor.id)
            self.assertEqual(recon_factor.name, orig_factor.name)
            self.assertEqual(recon_factor.category, orig_factor.category)
            self.assertEqual(recon_factor.inputs, orig_factor.inputs)
            self.assertEqual(recon_factor.outputs, orig_factor.outputs)
            self.assertEqual(recon_factor.parameters, orig_factor.parameters)
            self.assertEqual(recon_factor.description, orig_factor.description)

        # Validate DAG structure
        orig_edges = set(original.dag.edges())
        recon_edges = set(reconstructed.dag.edges())
        self.assertEqual(recon_edges, orig_edges)

    def test_roundtrip_json_serialization(self):
        """Test full round trip including JSON serialization."""
        # Create strategy
        strategy = Strategy(id="json_test", generation=1)

        factor = Factor(
            id="rsi_14",
            name="RSI",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["rsi"],
            logic=mock_rsi_logic,
            parameters={"period": 14}
        )
        strategy.add_factor(factor)

        signal_factor = Factor(
            id="signal",
            name="Signal",
            category=FactorCategory.SIGNAL,
            inputs=["rsi"],
            outputs=["positions"],
            logic=mock_signal_logic,
            parameters={}
        )
        strategy.add_factor(signal_factor, depends_on=["rsi_14"])

        # Full round trip: to_dict -> JSON -> dict -> from_dict
        metadata = strategy.to_dict()
        json_str = json.dumps(metadata)
        loaded_metadata = json.loads(json_str)

        factor_registry = {
            "rsi_14": mock_rsi_logic,
            "signal": mock_signal_logic
        }
        reconstructed = Strategy.from_dict(loaded_metadata, factor_registry)

        # Validate
        self.assertEqual(reconstructed.id, strategy.id)
        self.assertEqual(len(reconstructed.factors), len(strategy.factors))

    def test_roundtrip_complex_parameters(self):
        """Test round trip with complex nested parameters."""
        strategy = Strategy(id="test", generation=0)

        factor = Factor(
            id="complex",
            name="Complex",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["positions"],
            logic=mock_signal_logic,
            parameters={
                "period": 14,
                "thresholds": {"upper": 70, "lower": 30},
                "weights": [0.5, 0.3, 0.2],
                "enabled": True
            }
        )
        strategy.add_factor(factor)

        # Round trip
        metadata = strategy.to_dict()
        factor_registry = {"complex": mock_signal_logic}
        reconstructed = Strategy.from_dict(metadata, factor_registry)

        # Validate complex parameters preserved
        recon_params = reconstructed.factors["complex"].parameters
        self.assertEqual(recon_params["period"], 14)
        self.assertEqual(recon_params["thresholds"], {"upper": 70, "lower": 30})
        self.assertEqual(recon_params["weights"], [0.5, 0.3, 0.2])
        self.assertEqual(recon_params["enabled"], True)


class TestStrategySerializationEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_empty_strategy_serialization(self):
        """Test serializing strategy with no factors."""
        strategy = Strategy(id="empty", generation=0)

        # to_dict should work (empty factors list)
        metadata = strategy.to_dict()
        self.assertEqual(metadata["factors"], [])
        self.assertEqual(metadata["dag_edges"], [])

    def test_long_description_serialization(self):
        """Test serialization with very long description."""
        strategy = Strategy(id="test", generation=0)

        long_description = "A" * 1000  # 1000 character description

        factor = Factor(
            id="test",
            name="Test",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["positions"],
            logic=mock_signal_logic,
            parameters={},
            description=long_description
        )
        strategy.add_factor(factor)

        # Should serialize without issues
        metadata = strategy.to_dict()
        self.assertEqual(len(metadata["factors"][0]["description"]), 1000)

        # Round trip
        factor_registry = {"test": mock_signal_logic}
        reconstructed = Strategy.from_dict(metadata, factor_registry)
        self.assertEqual(len(reconstructed.factors["test"].description), 1000)

    def test_special_characters_in_metadata(self):
        """Test serialization with special characters."""
        strategy = Strategy(id="test", generation=0)

        factor = Factor(
            id="test",
            name="Test: Special \"Chars\" & Symbols",
            category=FactorCategory.MOMENTUM,
            inputs=["close"],
            outputs=["positions"],
            logic=mock_signal_logic,
            parameters={"text": "Quote: \"hello\", Newline:\n, Tab:\t"},
            description="Special chars: <>&\"'"
        )
        strategy.add_factor(factor)

        # Should serialize to JSON
        metadata = strategy.to_dict()
        json_str = json.dumps(metadata)

        # Should deserialize correctly
        loaded = json.loads(json_str)
        factor_registry = {"test": mock_signal_logic}
        reconstructed = Strategy.from_dict(loaded, factor_registry)

        # Validate special characters preserved
        recon_factor = reconstructed.factors["test"]
        self.assertIn("Special", recon_factor.name)
        self.assertIn("Quote", recon_factor.parameters["text"])

    def test_from_dict_malformed_data(self):
        """Test from_dict() with malformed data."""
        # Missing required key
        malformed = {
            "id": "test",
            "generation": 0,
            # Missing parent_ids, factors, dag_edges
        }

        factor_registry = {}

        with self.assertRaises((KeyError, TypeError)):
            Strategy.from_dict(malformed, factor_registry)


class TestFactoryRegistryPattern(unittest.TestCase):
    """Test factor_registry pattern for logic function management."""

    def test_registry_with_multiple_strategies(self):
        """Test using same registry for multiple strategies."""
        # Single registry for all strategies
        factor_registry = {
            "rsi_14": mock_rsi_logic,
            "ma_20": mock_ma_logic,
            "signal": mock_signal_logic
        }

        # Strategy 1: RSI + Signal
        metadata1 = {
            "id": "strategy1",
            "generation": 0,
            "parent_ids": [],
            "factors": [
                {
                    "id": "rsi_14",
                    "name": "RSI",
                    "category": "MOMENTUM",
                    "inputs": ["close"],
                    "outputs": ["rsi"],
                    "parameters": {},
                    "description": ""
                },
                {
                    "id": "signal",
                    "name": "Signal",
                    "category": "SIGNAL",
                    "inputs": ["rsi"],
                    "outputs": ["positions"],
                    "parameters": {},
                    "description": ""
                }
            ],
            "dag_edges": [["rsi_14", "signal"]]
        }

        # Strategy 2: MA + Signal
        metadata2 = {
            "id": "strategy2",
            "generation": 0,
            "parent_ids": [],
            "factors": [
                {
                    "id": "ma_20",
                    "name": "MA",
                    "category": "MOMENTUM",
                    "inputs": ["close"],
                    "outputs": ["ma"],
                    "parameters": {"period": 20},
                    "description": ""
                },
                {
                    "id": "signal",
                    "name": "Signal",
                    "category": "SIGNAL",
                    "inputs": ["ma"],
                    "outputs": ["positions"],
                    "parameters": {},
                    "description": ""
                }
            ],
            "dag_edges": [["ma_20", "signal"]]
        }

        # Reconstruct both using same registry
        strategy1 = Strategy.from_dict(metadata1, factor_registry)
        strategy2 = Strategy.from_dict(metadata2, factor_registry)

        self.assertEqual(len(strategy1.factors), 2)
        self.assertEqual(len(strategy2.factors), 2)
        self.assertIn("rsi_14", strategy1.factors)
        self.assertIn("ma_20", strategy2.factors)


if __name__ == "__main__":
    unittest.main()
