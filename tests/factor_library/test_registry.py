"""
Tests for Factor Registry
==========================

Tests for centralized factor discovery, lookup, and management.
Task: B.4 - Factor Registry Implementation

Test Coverage:
- Factor registration and lookup
- Category-based discovery
- Factor creation with parameters
- Parameter validation
- Singleton pattern
- Error handling
"""

import pytest
import pandas as pd

from src.factor_library.registry import FactorRegistry, FactorMetadata
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory


class TestFactorRegistry:
    """Test suite for FactorRegistry."""

    def setup_method(self):
        """Reset registry before each test."""
        FactorRegistry.reset()

    def test_singleton_pattern(self):
        """Test that registry follows singleton pattern."""
        registry1 = FactorRegistry.get_instance()
        registry2 = FactorRegistry.get_instance()

        assert registry1 is registry2, "Registry should be singleton"

    def test_auto_initialization(self):
        """Test that registry auto-registers all factors on first access."""
        registry = FactorRegistry.get_instance()

        # Should have all 13 factors registered
        all_factors = registry.list_factors()
        assert len(all_factors) == 13, f"Expected 13 factors, found {len(all_factors)}"

        # Check specific factors exist
        expected_factors = [
            "momentum_factor",
            "ma_filter_factor",
            "revenue_catalyst_factor",
            "earnings_catalyst_factor",
            "atr_factor",
            "breakout_factor",
            "dual_ma_filter_factor",
            "atr_stop_loss_factor",
            "trailing_stop_factor",
            "time_based_exit_factor",
            "volatility_stop_factor",
            "profit_target_factor",
            "composite_exit_factor",
        ]

        for factor_name in expected_factors:
            assert factor_name in all_factors, f"Factor '{factor_name}' not registered"

    def test_factor_registration(self):
        """Test manual factor registration."""
        registry = FactorRegistry.get_instance()

        # Create custom factory
        def custom_factory(param1: int = 10) -> Factor:
            from src.factor_graph.factor import Factor
            from src.factor_graph.factor_category import FactorCategory
            return Factor(
                id="custom",
                name="Custom",
                category=FactorCategory.MOMENTUM,
                inputs=["close"],
                outputs=["signal"],
                logic=lambda d, p: d,
                parameters={"param1": param1}
            )

        # Register custom factor
        registry.register_factor(
            name="custom_factor",
            factory=custom_factory,
            category=FactorCategory.MOMENTUM,
            description="Custom test factor",
            parameters={"param1": 10},
            parameter_ranges={"param1": (5, 50)}
        )

        # Verify registration
        assert "custom_factor" in registry.list_factors()
        assert "custom_factor" in registry.get_momentum_factors()

        # Test duplicate registration
        with pytest.raises(ValueError, match="already registered"):
            registry.register_factor(
                name="custom_factor",
                factory=custom_factory,
                category=FactorCategory.MOMENTUM,
                description="Duplicate",
            )

    def test_factor_lookup(self):
        """Test factor lookup by name."""
        registry = FactorRegistry.get_instance()

        # Lookup existing factor
        metadata = registry.get_factor("momentum_factor")
        assert metadata is not None
        assert isinstance(metadata, FactorMetadata)
        assert metadata.name == "momentum_factor"
        assert metadata.category == FactorCategory.MOMENTUM
        assert "momentum_period" in metadata.parameters

        # Lookup non-existent factor
        metadata = registry.get_factor("nonexistent_factor")
        assert metadata is None

    def test_get_metadata(self):
        """Test metadata retrieval as dictionary."""
        registry = FactorRegistry.get_instance()

        metadata = registry.get_metadata("momentum_factor")
        assert metadata is not None
        assert isinstance(metadata, dict)
        assert "name" in metadata
        assert "category" in metadata
        assert "description" in metadata
        assert "parameters" in metadata
        assert "parameter_ranges" in metadata

        # Non-existent factor
        metadata = registry.get_metadata("nonexistent")
        assert metadata is None

    def test_list_by_category(self):
        """Test category-based factor discovery."""
        registry = FactorRegistry.get_instance()

        # Test momentum factors
        momentum_factors = registry.list_by_category(FactorCategory.MOMENTUM)
        assert len(momentum_factors) >= 3  # At least 3 momentum factors
        assert "momentum_factor" in momentum_factors
        assert "ma_filter_factor" in momentum_factors
        assert "dual_ma_filter_factor" in momentum_factors

        # Test exit factors
        exit_factors = registry.list_by_category(FactorCategory.EXIT)
        assert len(exit_factors) == 6  # Exactly 6 exit factors (5 from exit_factors.py + 1 from turtle)
        assert "trailing_stop_factor" in exit_factors
        assert "time_based_exit_factor" in exit_factors
        assert "volatility_stop_factor" in exit_factors
        assert "profit_target_factor" in exit_factors
        assert "composite_exit_factor" in exit_factors
        assert "atr_stop_loss_factor" in exit_factors  # From turtle_factors.py

        # Test entry factors
        entry_factors = registry.list_by_category(FactorCategory.ENTRY)
        assert len(entry_factors) == 1  # 1 entry factor
        assert "breakout_factor" in entry_factors

        # Test risk factors
        risk_factors = registry.list_by_category(FactorCategory.RISK)
        assert len(risk_factors) == 1  # 1 risk factor
        assert "atr_factor" in risk_factors

        # Test value factors
        value_factors = registry.list_by_category(FactorCategory.VALUE)
        assert len(value_factors) == 1  # 1 value factor
        assert "revenue_catalyst_factor" in value_factors

        # Test quality factors
        quality_factors = registry.list_by_category(FactorCategory.QUALITY)
        assert len(quality_factors) == 1  # 1 quality factor
        assert "earnings_catalyst_factor" in quality_factors

    def test_category_convenience_methods(self):
        """Test category-specific convenience methods."""
        registry = FactorRegistry.get_instance()

        momentum = registry.get_momentum_factors()
        assert len(momentum) >= 3
        assert "momentum_factor" in momentum

        exit_factors = registry.get_exit_factors()
        assert len(exit_factors) == 6  # 5 from exit_factors.py + 1 from turtle

        entry_factors = registry.get_entry_factors()
        assert len(entry_factors) == 1

        risk_factors = registry.get_risk_factors()
        assert len(risk_factors) == 1

        value_factors = registry.get_value_factors()
        assert len(value_factors) == 1

        quality_factors = registry.get_quality_factors()
        assert len(quality_factors) == 1

        signal_factors = registry.get_signal_factors()
        assert len(signal_factors) == 0  # No signal factors yet

    def test_get_factory(self):
        """Test factory function retrieval."""
        registry = FactorRegistry.get_instance()

        # Get factory for momentum factor
        factory = registry.get_factory("momentum_factor")
        assert factory is not None
        assert callable(factory)

        # Create factor using factory
        factor = factory(momentum_period=30)
        assert isinstance(factor, Factor)
        assert factor.parameters["momentum_period"] == 30
        assert factor.category == FactorCategory.MOMENTUM

        # Non-existent factor
        factory = registry.get_factory("nonexistent")
        assert factory is None

    def test_create_factor_with_defaults(self):
        """Test factor creation using default parameters."""
        registry = FactorRegistry.get_instance()

        # Create with defaults
        factor = registry.create_factor("momentum_factor")
        assert isinstance(factor, Factor)
        assert factor.parameters["momentum_period"] == 20  # Default value
        assert factor.category == FactorCategory.MOMENTUM

    def test_create_factor_with_custom_parameters(self):
        """Test factor creation with custom parameters."""
        registry = FactorRegistry.get_instance()

        # Create with custom parameters
        factor = registry.create_factor(
            "momentum_factor",
            parameters={"momentum_period": 30}
        )
        assert factor.parameters["momentum_period"] == 30

        # Test dual parameter factor
        factor = registry.create_factor(
            "dual_ma_filter_factor",
            parameters={"short_ma": 10, "long_ma": 50}
        )
        assert factor.parameters["short_ma"] == 10
        assert factor.parameters["long_ma"] == 50

    def test_create_factor_invalid_name(self):
        """Test error handling for invalid factor name."""
        registry = FactorRegistry.get_instance()

        with pytest.raises(ValueError, match="not found in registry"):
            registry.create_factor("nonexistent_factor")

    def test_create_factor_invalid_parameters(self):
        """Test error handling for invalid parameters."""
        registry = FactorRegistry.get_instance()

        # Out of range parameter
        with pytest.raises(ValueError, match="out of range"):
            registry.create_factor(
                "momentum_factor",
                parameters={"momentum_period": 1}  # Below min of 5
            )

        with pytest.raises(ValueError, match="out of range"):
            registry.create_factor(
                "momentum_factor",
                parameters={"momentum_period": 200}  # Above max of 100
            )

    def test_validate_parameters_valid(self):
        """Test parameter validation with valid parameters."""
        registry = FactorRegistry.get_instance()

        # Valid single parameter
        is_valid, msg = registry.validate_parameters(
            "momentum_factor",
            {"momentum_period": 20}
        )
        assert is_valid
        assert msg == ""

        # Valid multiple parameters
        is_valid, msg = registry.validate_parameters(
            "dual_ma_filter_factor",
            {"short_ma": 20, "long_ma": 60}
        )
        assert is_valid
        assert msg == ""

        # Valid at boundary
        is_valid, msg = registry.validate_parameters(
            "momentum_factor",
            {"momentum_period": 5}  # Min boundary
        )
        assert is_valid

        is_valid, msg = registry.validate_parameters(
            "momentum_factor",
            {"momentum_period": 100}  # Max boundary
        )
        assert is_valid

    def test_validate_parameters_invalid(self):
        """Test parameter validation with invalid parameters."""
        registry = FactorRegistry.get_instance()

        # Factor not found
        is_valid, msg = registry.validate_parameters(
            "nonexistent",
            {"param": 10}
        )
        assert not is_valid
        assert "not found" in msg

        # Unknown parameter
        is_valid, msg = registry.validate_parameters(
            "momentum_factor",
            {"unknown_param": 10}
        )
        assert not is_valid
        assert "Unknown parameters" in msg

        # Out of range (below min)
        is_valid, msg = registry.validate_parameters(
            "momentum_factor",
            {"momentum_period": 1}
        )
        assert not is_valid
        assert "out of range" in msg

        # Out of range (above max)
        is_valid, msg = registry.validate_parameters(
            "momentum_factor",
            {"momentum_period": 200}
        )
        assert not is_valid
        assert "out of range" in msg

    def test_validate_parameters_float_ranges(self):
        """Test parameter validation for float parameters."""
        registry = FactorRegistry.get_instance()

        # Valid float parameter
        is_valid, msg = registry.validate_parameters(
            "atr_stop_loss_factor",
            {"atr_multiplier": 2.0}
        )
        assert is_valid

        # Valid at boundaries
        is_valid, msg = registry.validate_parameters(
            "atr_stop_loss_factor",
            {"atr_multiplier": 0.5}  # Min
        )
        assert is_valid

        is_valid, msg = registry.validate_parameters(
            "atr_stop_loss_factor",
            {"atr_multiplier": 5.0}  # Max
        )
        assert is_valid

        # Invalid (out of range)
        is_valid, msg = registry.validate_parameters(
            "atr_stop_loss_factor",
            {"atr_multiplier": 0.1}  # Below min
        )
        assert not is_valid

        is_valid, msg = registry.validate_parameters(
            "atr_stop_loss_factor",
            {"atr_multiplier": 10.0}  # Above max
        )
        assert not is_valid

    def test_factor_execution(self):
        """Test that created factors can execute successfully."""
        registry = FactorRegistry.get_instance()

        # Create momentum factor
        factor = registry.create_factor(
            "momentum_factor",
            parameters={"momentum_period": 5}
        )

        # Create test data
        data = pd.DataFrame({
            "close": [100, 102, 101, 103, 105, 107, 106, 108, 110]
        })

        # Execute factor
        result = factor.execute(data)

        # Verify output
        assert "momentum" in result.columns
        assert not result["momentum"].isna().all()  # Should have some non-NaN values

    def test_exit_factor_creation(self):
        """Test creation of exit factors with various parameters."""
        registry = FactorRegistry.get_instance()

        # Trailing stop
        trailing_stop = registry.create_factor(
            "trailing_stop_factor",
            parameters={"trail_percent": 0.15, "activation_profit": 0.10}
        )
        assert trailing_stop.parameters["trail_percent"] == 0.15
        assert trailing_stop.parameters["activation_profit"] == 0.10

        # Time-based exit
        time_exit = registry.create_factor(
            "time_based_exit_factor",
            parameters={"max_holding_periods": 30}
        )
        assert time_exit.parameters["max_holding_periods"] == 30

        # Profit target
        profit_target = registry.create_factor(
            "profit_target_factor",
            parameters={"target_percent": 0.50}
        )
        assert profit_target.parameters["target_percent"] == 0.50

    def test_composite_exit_factor_creation(self):
        """Test creation of composite exit factor."""
        registry = FactorRegistry.get_instance()

        # Create composite exit with multiple signals
        composite = registry.create_factor(
            "composite_exit_factor",
            parameters={
                "exit_signals": [
                    "trailing_stop_signal",
                    "time_exit_signal",
                    "profit_target_signal"
                ]
            }
        )

        assert isinstance(composite, Factor)
        assert composite.category == FactorCategory.EXIT
        assert len(composite.parameters["exit_signals"]) == 3

    def test_backward_compatibility(self):
        """Test that factory functions still work independently."""
        from src.factor_library.momentum_factors import create_momentum_factor
        from src.factor_library.turtle_factors import create_atr_factor
        from src.factor_library.exit_factors import create_trailing_stop_factor

        # Create factors directly via factory functions
        momentum = create_momentum_factor(momentum_period=25)
        atr = create_atr_factor(atr_period=15)
        trailing_stop = create_trailing_stop_factor(trail_percent=0.12)

        # Verify they work
        assert momentum.parameters["momentum_period"] == 25
        assert atr.parameters["atr_period"] == 15
        assert trailing_stop.parameters["trail_percent"] == 0.12

    def test_registry_comprehensive_coverage(self):
        """Test that all 13 factors are registered with correct categories."""
        registry = FactorRegistry.get_instance()

        # Count by category
        category_counts = {
            FactorCategory.MOMENTUM: 3,  # momentum, ma_filter, dual_ma_filter
            FactorCategory.VALUE: 1,      # revenue_catalyst
            FactorCategory.QUALITY: 1,    # earnings_catalyst
            FactorCategory.RISK: 1,       # atr
            FactorCategory.ENTRY: 1,      # breakout
            FactorCategory.EXIT: 6,       # trailing_stop, time_exit, volatility_stop, profit_target, composite_exit, atr_stop_loss
            FactorCategory.SIGNAL: 0,     # None yet
        }

        for category, expected_count in category_counts.items():
            factors = registry.list_by_category(category)
            assert len(factors) == expected_count, (
                f"Expected {expected_count} {category.value} factors, "
                f"found {len(factors)}: {factors}"
            )

    def test_parameter_ranges_completeness(self):
        """Test that all factors have parameter ranges defined."""
        registry = FactorRegistry.get_instance()

        # Factors that should have parameter ranges
        factors_with_ranges = [
            "momentum_factor",
            "ma_filter_factor",
            "revenue_catalyst_factor",
            "earnings_catalyst_factor",
            "atr_factor",
            "breakout_factor",
            "dual_ma_filter_factor",
            "atr_stop_loss_factor",
            "trailing_stop_factor",
            "time_based_exit_factor",
            "volatility_stop_factor",
            "profit_target_factor",
        ]

        for factor_name in factors_with_ranges:
            metadata = registry.get_metadata(factor_name)
            assert metadata is not None
            assert len(metadata["parameter_ranges"]) > 0, (
                f"Factor '{factor_name}' missing parameter ranges"
            )


class TestFactorRegistryIntegration:
    """Integration tests for factor registry."""

    def setup_method(self):
        """Reset registry before each test."""
        FactorRegistry.reset()

    def test_create_and_execute_pipeline(self):
        """Test creating and executing a multi-factor pipeline."""
        registry = FactorRegistry.get_instance()

        # Create a simple momentum + exit pipeline
        momentum = registry.create_factor("momentum_factor", {"momentum_period": 10})
        profit_target = registry.create_factor("profit_target_factor", {"target_percent": 0.20})

        # Create test data
        data = pd.DataFrame({
            "close": [100, 105, 110, 108, 115, 120, 118, 122, 125],
            "positions": [True] * 9,
            "entry_price": [100] * 9,
        })

        # Execute pipeline
        result = momentum.execute(data)
        result = profit_target.execute(result)

        # Verify outputs
        assert "momentum" in result.columns
        assert "profit_target_signal" in result.columns

    def test_discover_and_create_workflow(self):
        """Test typical workflow: discover -> validate -> create."""
        registry = FactorRegistry.get_instance()

        # 1. Discover available momentum factors
        momentum_factors = registry.get_momentum_factors()
        assert len(momentum_factors) >= 3

        # 2. Get metadata for a specific factor
        metadata = registry.get_metadata("momentum_factor")
        assert metadata is not None

        # 3. Validate custom parameters
        custom_params = {"momentum_period": 30}
        is_valid, msg = registry.validate_parameters("momentum_factor", custom_params)
        assert is_valid, f"Validation failed: {msg}"

        # 4. Create factor with validated parameters
        factor = registry.create_factor("momentum_factor", custom_params)
        assert factor.parameters["momentum_period"] == 30

    def test_mutation_scenario(self):
        """Test scenario: replace one factor with another from same category."""
        registry = FactorRegistry.get_instance()

        # Original factor
        original = registry.create_factor("momentum_factor")

        # Discover alternatives in same category
        momentum_alternatives = registry.get_momentum_factors()
        assert "ma_filter_factor" in momentum_alternatives

        # Replace with alternative
        replacement = registry.create_factor("ma_filter_factor")

        # Verify both are momentum factors but different
        assert original.category == replacement.category
        assert original.id != replacement.id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
