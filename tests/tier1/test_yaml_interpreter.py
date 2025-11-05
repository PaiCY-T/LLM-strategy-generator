"""
Test Suite for YAML Interpreter
=================================

Comprehensive tests for YAMLInterpreter, FactorFactory, and InterpretationError.
Tests cover: config loading, factor creation, DAG construction, error handling,
integration with FactorRegistry, and end-to-end YAML → Strategy pipeline.

Architecture: Structural Mutation Phase 2 - Phase D.2
Task: D.2 - YAML → Factor Interpreter

Test Categories:
----------------
1. YAMLInterpreter Tests (15+ tests)
   - Load valid YAML files
   - Load example configs (momentum, turtle, multi-factor)
   - Invalid YAML/JSON syntax handling
   - Unknown factor types
   - Invalid parameters
   - Dependency cycles
   - Missing dependencies
   - Duplicate factor IDs
   - Empty factors list
   - Error context

2. FactorFactory Tests (10+ tests)
   - Create all factor types
   - Parameter validation
   - Default parameters
   - Invalid factor types
   - Parameter bounds checking

3. Integration Tests (8+ tests)
   - YAML → Strategy → validate
   - YAML → Strategy → to_pipeline
   - All example configs
   - Multi-generation strategies
   - Error recovery
   - Strategy execution
"""

import pytest
import yaml
import json
import tempfile
from pathlib import Path

from src.tier1.yaml_interpreter import YAMLInterpreter, InterpretationError
from src.tier1.factor_factory import FactorFactory, FactorFactoryError
from src.factor_library import FactorRegistry
from src.factor_graph import Strategy


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def registry():
    """Get FactorRegistry singleton."""
    return FactorRegistry.get_instance()


@pytest.fixture
def factory(registry):
    """Create FactorFactory with registry."""
    return FactorFactory(registry)


@pytest.fixture
def interpreter():
    """Create YAMLInterpreter."""
    return YAMLInterpreter()


@pytest.fixture
def minimal_config():
    """Minimal valid configuration."""
    return {
        "strategy_id": "test-strategy",
        "factors": [
            {
                "id": "momentum_20",
                "type": "momentum_factor",
                "parameters": {"momentum_period": 20},
                "depends_on": []
            }
        ]
    }


@pytest.fixture
def basic_config():
    """Basic configuration with multiple factors."""
    return {
        "strategy_id": "basic-strategy",
        "description": "Basic test strategy",
        "factors": [
            {
                "id": "momentum_20",
                "type": "momentum_factor",
                "parameters": {"momentum_period": 20},
                "depends_on": []
            },
            {
                "id": "ma_filter_60",
                "type": "ma_filter_factor",
                "parameters": {"ma_periods": 60},
                "depends_on": []
            },
            {
                "id": "trailing_stop",
                "type": "trailing_stop_factor",
                "parameters": {
                    "trail_percent": 0.10,
                    "activation_profit": 0.05
                },
                "depends_on": ["momentum_20", "ma_filter_60"]
            }
        ]
    }


@pytest.fixture
def temp_yaml_file(minimal_config):
    """Create temporary YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(minimal_config, f)
        temp_path = f.name
    yield temp_path
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


# ============================================================================
# FactorFactory Tests (10+ tests)
# ============================================================================

class TestFactorFactory:
    """Test FactorFactory functionality."""

    def test_create_momentum_factor(self, factory):
        """Test creating momentum factor."""
        factor = factory.create_factor(
            factor_id="momentum_20",
            factor_type="momentum_factor",
            parameters={"momentum_period": 20}
        )

        assert factor.id == "momentum_20"
        assert factor.parameters["momentum_period"] == 20
        assert "momentum" in factor.name.lower()

    def test_create_ma_filter_factor(self, factory):
        """Test creating MA filter factor."""
        factor = factory.create_factor(
            factor_id="ma_60",
            factor_type="ma_filter_factor",
            parameters={"ma_periods": 60}
        )

        assert factor.id == "ma_60"
        assert factor.parameters["ma_periods"] == 60

    def test_create_with_valid_parameters(self, factory):
        """Test creating factor with all valid parameters."""
        factor = factory.create_factor(
            factor_id="trailing_stop",
            factor_type="trailing_stop_factor",
            parameters={
                "trail_percent": 0.10,
                "activation_profit": 0.05
            }
        )

        assert factor.parameters["trail_percent"] == 0.10
        assert factor.parameters["activation_profit"] == 0.05

    def test_unknown_factor_type(self, factory):
        """Test error on unknown factor type."""
        with pytest.raises(FactorFactoryError) as exc_info:
            factory.create_factor(
                factor_id="unknown",
                factor_type="unknown_factor_type",
                parameters={}
            )

        error = exc_info.value
        assert "unknown_factor_type" in str(error).lower()
        assert "available types" in str(error).lower()

    def test_invalid_parameter_type(self, factory):
        """Test error on invalid parameter type."""
        with pytest.raises(FactorFactoryError) as exc_info:
            factory.create_factor(
                factor_id="momentum",
                factor_type="momentum_factor",
                parameters={"momentum_period": "invalid"}  # Should be int
            )

        assert "invalid" in str(exc_info.value).lower() or "parameter" in str(exc_info.value).lower()

    def test_parameter_out_of_range(self, factory):
        """Test error on parameter out of valid range."""
        with pytest.raises(FactorFactoryError) as exc_info:
            factory.create_factor(
                factor_id="momentum",
                factor_type="momentum_factor",
                parameters={"momentum_period": 1}  # Too small (min=5)
            )

        error_msg = str(exc_info.value).lower()
        assert "range" in error_msg or "out of" in error_msg

    def test_missing_required_parameter(self, factory):
        """Test error on missing required parameter."""
        with pytest.raises(FactorFactoryError) as exc_info:
            factory.create_factor(
                factor_id="momentum",
                factor_type="momentum_factor",
                parameters={}  # Missing momentum_period
            )

        # Note: FactorRegistry provides default parameters, so this may not fail
        # But we can test that defaults are used
        pass  # This test depends on registry behavior

    def test_default_parameters(self, factory):
        """Test using default parameters from registry."""
        factor = factory.create_factor(
            factor_id="momentum",
            factor_type="momentum_factor",
            parameters={}  # Use defaults
        )

        # Should use default momentum_period=20
        assert "momentum_period" in factor.parameters
        assert factor.parameters["momentum_period"] == 20

    def test_parameter_bounds_validation(self, factory):
        """Test parameter bounds are validated."""
        # Test lower bound
        with pytest.raises(FactorFactoryError):
            factory.create_factor(
                factor_id="atr",
                factor_type="atr_factor",
                parameters={"atr_period": 2}  # Too small (min=5)
            )

        # Test upper bound
        with pytest.raises(FactorFactoryError):
            factory.create_factor(
                factor_id="atr",
                factor_type="atr_factor",
                parameters={"atr_period": 150}  # Too large (max=100)
            )

    def test_create_all_registry_factors(self, factory, registry):
        """Test creating all 13 registered factor types."""
        factor_types = registry.list_factors()
        assert len(factor_types) >= 13

        # Try to create each factor type
        created_count = 0
        for factor_type in factor_types:
            try:
                metadata = registry.get_metadata(factor_type)
                if metadata:
                    factor = factory.create_factor(
                        factor_id=f"test_{factor_type}",
                        factor_type=factor_type,
                        parameters=metadata['parameters'].copy()
                    )
                    assert factor is not None
                    created_count += 1
            except Exception as e:
                pytest.fail(f"Failed to create {factor_type}: {str(e)}")

        assert created_count >= 13

    def test_get_available_types(self, factory):
        """Test getting available factor types."""
        types = factory.get_available_types()
        assert len(types) >= 13
        assert "momentum_factor" in types
        assert "atr_factor" in types
        assert "trailing_stop_factor" in types

    def test_get_metadata(self, factory):
        """Test getting factor metadata."""
        metadata = factory.get_metadata("momentum_factor")
        assert metadata is not None
        assert "parameters" in metadata
        assert "momentum_period" in metadata["parameters"]


# ============================================================================
# YAMLInterpreter Tests (15+ tests)
# ============================================================================

class TestYAMLInterpreter:
    """Test YAMLInterpreter functionality."""

    def test_from_dict_minimal(self, interpreter, minimal_config):
        """Test interpreting minimal valid config."""
        strategy = interpreter.from_dict(minimal_config)

        assert strategy.id == "test-strategy"
        assert len(strategy.factors) == 1
        assert "momentum_20" in strategy.factors

    def test_from_dict_basic(self, interpreter, basic_config):
        """Test interpreting basic config with dependencies."""
        strategy = interpreter.from_dict(basic_config)

        assert strategy.id == "basic-strategy"
        assert len(strategy.factors) == 3
        assert "momentum_20" in strategy.factors
        assert "ma_filter_60" in strategy.factors
        assert "trailing_stop" in strategy.factors

    def test_from_file_yaml(self, interpreter, temp_yaml_file):
        """Test loading YAML file."""
        strategy = interpreter.from_file(temp_yaml_file)

        assert strategy is not None
        assert len(strategy.factors) >= 1

    def test_load_momentum_basic_yaml(self, interpreter):
        """Test loading momentum_basic.yaml example."""
        yaml_path = "examples/yaml_strategies/momentum_basic.yaml"

        try:
            strategy = interpreter.from_file(yaml_path)

            assert strategy.id == "momentum-basic-v1"
            assert len(strategy.factors) == 3
            assert "momentum_20" in strategy.factors
            assert "ma_filter_60" in strategy.factors
            assert "trailing_stop" in strategy.factors

            # Validate strategy
            assert strategy.validate()
        except FileNotFoundError:
            pytest.skip(f"Example file not found: {yaml_path}")

    def test_load_turtle_exit_combo_yaml(self, interpreter):
        """Test loading turtle_exit_combo.yaml example."""
        yaml_path = "examples/yaml_strategies/turtle_exit_combo.yaml"

        try:
            strategy = interpreter.from_file(yaml_path)

            assert strategy.id == "turtle-exit-combo-v1"
            assert len(strategy.factors) == 6
            assert "atr_20" in strategy.factors
            assert "breakout_20" in strategy.factors
            assert "composite_exit" in strategy.factors

            # Validate strategy
            assert strategy.validate()
        except FileNotFoundError:
            pytest.skip(f"Example file not found: {yaml_path}")

    def test_load_multi_factor_complex_yaml(self, interpreter):
        """Test loading multi_factor_complex.yaml example."""
        yaml_path = "examples/yaml_strategies/multi_factor_complex.yaml"

        try:
            strategy = interpreter.from_file(yaml_path)

            assert strategy is not None
            assert len(strategy.factors) >= 5

            # Validate strategy
            assert strategy.validate()
        except FileNotFoundError:
            pytest.skip(f"Example file not found: {yaml_path}")

    def test_invalid_yaml_syntax(self, interpreter):
        """Test error on invalid YAML syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax:\n  - broken")
            temp_path = f.name

        try:
            with pytest.raises(InterpretationError) as exc_info:
                interpreter.from_file(temp_path)

            assert "invalid" in str(exc_info.value).lower() or "yaml" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_unknown_factor_type(self, interpreter):
        """Test error on unknown factor type."""
        config = {
            "strategy_id": "test",
            "factors": [
                {
                    "id": "unknown",
                    "type": "unknown_factor_type",
                    "parameters": {},
                    "depends_on": []
                }
            ]
        }

        with pytest.raises(InterpretationError) as exc_info:
            interpreter.from_dict(config)

        error_msg = str(exc_info.value)
        assert "unknown_factor_type" in error_msg.lower()
        assert "available" in error_msg.lower()

    def test_invalid_parameters(self, interpreter):
        """Test error on invalid parameters."""
        config = {
            "strategy_id": "test",
            "factors": [
                {
                    "id": "momentum",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 1},  # Too small
                    "depends_on": []
                }
            ]
        }

        with pytest.raises(InterpretationError) as exc_info:
            interpreter.from_dict(config)

        error_msg = str(exc_info.value).lower()
        assert "parameter" in error_msg or "range" in error_msg

    def test_dependency_cycle_detection(self, interpreter):
        """Test detection of circular dependencies."""
        config = {
            "strategy_id": "cycle-test",
            "factors": [
                {
                    "id": "factor_a",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20},
                    "depends_on": ["factor_b"]  # Circular: A→B→A
                },
                {
                    "id": "factor_b",
                    "type": "ma_filter_factor",
                    "parameters": {"ma_periods": 60},
                    "depends_on": ["factor_a"]  # Circular: B→A→B
                }
            ]
        }

        with pytest.raises(InterpretationError) as exc_info:
            interpreter.from_dict(config)

        error_msg = str(exc_info.value).lower()
        assert "cycle" in error_msg or "circular" in error_msg or "dependencies" in error_msg

    def test_missing_dependency(self, interpreter):
        """Test error on missing dependency."""
        config = {
            "strategy_id": "missing-dep",
            "factors": [
                {
                    "id": "factor_a",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20},
                    "depends_on": ["nonexistent_factor"]  # Missing
                }
            ]
        }

        with pytest.raises(InterpretationError) as exc_info:
            interpreter.from_dict(config)

        error_msg = str(exc_info.value).lower()
        assert "dependency" in error_msg or "nonexistent" in error_msg

    def test_empty_factors_list(self, interpreter):
        """Test error on empty factors list."""
        config = {
            "strategy_id": "empty",
            "factors": []
        }

        with pytest.raises(InterpretationError) as exc_info:
            interpreter.from_dict(config)

        assert "empty" in str(exc_info.value).lower()

    def test_duplicate_factor_ids(self, interpreter):
        """Test error on duplicate factor IDs."""
        config = {
            "strategy_id": "duplicate",
            "factors": [
                {
                    "id": "momentum_20",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20},
                    "depends_on": []
                },
                {
                    "id": "momentum_20",  # Duplicate ID
                    "type": "ma_filter_factor",
                    "parameters": {"ma_periods": 60},
                    "depends_on": []
                }
            ]
        }

        with pytest.raises(InterpretationError) as exc_info:
            interpreter.from_dict(config)

        error_msg = str(exc_info.value).lower()
        assert "duplicate" in error_msg or "already exists" in error_msg

    def test_strategy_validation_runs(self, interpreter, basic_config):
        """Test that strategy validation is executed."""
        strategy = interpreter.from_dict(basic_config)

        # Strategy should be automatically validated during interpretation
        # Additional validation should pass
        assert strategy.validate()

    def test_error_context_in_exceptions(self, interpreter):
        """Test that errors include helpful context."""
        config = {
            "strategy_id": "error-test",
            "factors": [
                {
                    "id": "bad_factor",
                    "type": "unknown_type",
                    "parameters": {},
                    "depends_on": []
                }
            ]
        }

        with pytest.raises(InterpretationError) as exc_info:
            interpreter.from_dict(config)

        error = exc_info.value
        # Check that context includes relevant information
        assert error.context is not None
        assert 'factor_id' in error.context or 'factor_type' in error.context


# ============================================================================
# Integration Tests (8+ tests)
# ============================================================================

class TestIntegration:
    """Test end-to-end integration."""

    def test_yaml_to_strategy_to_validate(self, interpreter, basic_config):
        """Test full pipeline: YAML → Strategy → validate."""
        # Interpret config
        strategy = interpreter.from_dict(basic_config)

        # Validate strategy
        assert strategy.validate()

        # Check structure
        assert len(strategy.factors) == 3
        assert strategy.id == "basic-strategy"

    def test_all_example_configs(self, interpreter):
        """Test loading all example YAML configs."""
        example_files = [
            "examples/yaml_strategies/momentum_basic.yaml",
            "examples/yaml_strategies/turtle_exit_combo.yaml",
            "examples/yaml_strategies/multi_factor_complex.yaml"
        ]

        loaded_count = 0
        for yaml_path in example_files:
            try:
                strategy = interpreter.from_file(yaml_path)
                assert strategy is not None
                assert strategy.validate()
                loaded_count += 1
            except FileNotFoundError:
                pass  # Skip missing example files

        # At least one example should load
        assert loaded_count >= 1, "No example configs loaded successfully"

    def test_integration_with_factor_registry(self, interpreter, registry):
        """Test integration with FactorRegistry."""
        # Get registry from interpreter
        interp_registry = interpreter.get_registry()
        assert interp_registry is registry

        # Create strategy using registry factors
        config = {
            "strategy_id": "registry-test",
            "factors": [
                {
                    "id": "mom",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20},
                    "depends_on": []
                }
            ]
        }

        strategy = interpreter.from_dict(config)
        assert strategy.validate()

    def test_integration_with_factor_graph(self, interpreter, basic_config):
        """Test integration with Factor Graph (Strategy/Factor)."""
        strategy = interpreter.from_dict(basic_config)

        # Check Strategy properties
        assert isinstance(strategy, Strategy)
        assert strategy.id == "basic-strategy"
        assert strategy.generation == 0

        # Check Factor properties
        factors = strategy.get_factors()
        assert len(factors) == 3

        # Check factor order (topological)
        factor_ids = [f.id for f in factors]
        # trailing_stop should come after its dependencies
        trailing_idx = factor_ids.index("trailing_stop")
        momentum_idx = factor_ids.index("momentum_20")
        ma_idx = factor_ids.index("ma_filter_60")
        assert trailing_idx > momentum_idx
        assert trailing_idx > ma_idx

    def test_error_recovery_and_messages(self, interpreter):
        """Test graceful error handling with helpful messages."""
        # Test various error conditions
        error_configs = [
            # Missing strategy_id
            {"factors": []},
            # Unknown factor type
            {"strategy_id": "test", "factors": [{"id": "a", "type": "unknown", "parameters": {}}]},
            # Invalid parameters
            {"strategy_id": "test", "factors": [{"id": "a", "type": "momentum_factor", "parameters": {"momentum_period": 1}}]},
        ]

        for config in error_configs:
            try:
                interpreter.from_dict(config)
                # Should raise error
                assert False, f"Expected error for config: {config}"
            except InterpretationError as e:
                # Check error has message and context
                assert str(e)
                assert e.context is not None

    def test_multi_generation_strategies(self, interpreter, basic_config):
        """Test creating multiple strategies from YAML."""
        # Create first strategy
        strategy1 = interpreter.from_dict(basic_config)
        assert strategy1.id == "basic-strategy"

        # Create second strategy with different ID
        config2 = basic_config.copy()
        config2["strategy_id"] = "basic-strategy-v2"
        strategy2 = interpreter.from_dict(config2)
        assert strategy2.id == "basic-strategy-v2"

        # Strategies should be independent
        assert strategy1.id != strategy2.id
        assert len(strategy1.factors) == len(strategy2.factors)

    def test_disabled_factors_are_skipped(self, interpreter):
        """Test that disabled factors are not added to strategy."""
        config = {
            "strategy_id": "disabled-test",
            "factors": [
                {
                    "id": "momentum_20",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20},
                    "depends_on": [],
                    "enabled": True
                },
                {
                    "id": "ma_filter_60",
                    "type": "ma_filter_factor",
                    "parameters": {"ma_periods": 60},
                    "depends_on": [],
                    "enabled": False  # Disabled
                }
            ]
        }

        strategy = interpreter.from_dict(config)

        # Only enabled factor should be in strategy
        assert len(strategy.factors) == 1
        assert "momentum_20" in strategy.factors
        assert "ma_filter_60" not in strategy.factors

    def test_get_validator_and_registry(self, interpreter):
        """Test accessing validator and registry from interpreter."""
        # Get validator
        validator = interpreter.get_validator()
        assert validator is not None

        # Get registry
        registry = interpreter.get_registry()
        assert registry is not None

        # Test validator works
        factor_types = validator.list_factor_types()
        assert len(factor_types) >= 13


# ============================================================================
# InterpretationError Tests
# ============================================================================

class TestInterpretationError:
    """Test InterpretationError functionality."""

    def test_error_with_message(self):
        """Test creating error with message only."""
        error = InterpretationError("Test error message")
        assert str(error) == "Test error message"
        assert error.context == {}

    def test_error_with_context(self):
        """Test creating error with context."""
        context = {
            'file': 'test.yaml',
            'factor_id': 'momentum_20',
            'factor_type': 'momentum_factor'
        }
        error = InterpretationError("Test error", context=context)

        error_str = str(error)
        assert "Test error" in error_str
        assert "test.yaml" in error_str
        assert "momentum_20" in error_str

    def test_error_context_attribute(self):
        """Test that context is accessible as attribute."""
        context = {'factor_id': 'test'}
        error = InterpretationError("Test", context=context)
        assert error.context == context
        assert error.context['factor_id'] == 'test'


# ============================================================================
# FactorFactoryError Tests
# ============================================================================

class TestFactorFactoryError:
    """Test FactorFactoryError functionality."""

    def test_error_with_message(self):
        """Test creating error with message only."""
        error = FactorFactoryError("Test error")
        assert str(error) == "Test error"

    def test_error_with_context(self):
        """Test creating error with context."""
        error = FactorFactoryError(
            "Test error",
            factor_id="momentum_20",
            factor_type="momentum_factor",
            parameter="momentum_period"
        )

        error_str = str(error)
        assert "Test error" in error_str
        assert "momentum_20" in error_str
        assert "momentum_factor" in error_str
        assert "momentum_period" in error_str
