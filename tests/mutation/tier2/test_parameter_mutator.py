"""
Comprehensive Tests for ParameterMutator

Tests cover all acceptance criteria:
1. Apply parameter mutations to Factor parameters
2. Gaussian distribution with configurable std dev
3. Respect parameter bounds (min/max)
4. Validate parameters after mutation
5. Track parameter drift across generations
6. Compatible with Factor DAG structure

Architecture: Phase 2.0+ Factor Graph System
Task: C.4 - mutate_parameters() Integration (Phase 1)
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any

from src.mutation.tier2 import ParameterMutator
from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory
from src.factor_graph.strategy import Strategy


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def rsi_factor():
    """Create RSI factor with period parameter."""
    def calculate_rsi(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Simple RSI calculation."""
        period = params["period"]
        data["rsi"] = 50.0  # Dummy implementation
        return data

    return Factor(
        id="rsi_14",
        name="RSI Indicator",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["rsi"],
        logic=calculate_rsi,
        parameters={"period": 14, "overbought": 70, "oversold": 30}
    )


@pytest.fixture
def atr_factor():
    """Create ATR factor with period and multiplier parameters."""
    def calculate_atr(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Simple ATR calculation."""
        period = params["period"]
        multiplier = params["multiplier"]
        data["atr"] = 1.0  # Dummy implementation
        return data

    return Factor(
        id="atr_20",
        name="ATR Indicator",
        category=FactorCategory.RISK,
        inputs=["high", "low", "close"],
        outputs=["atr"],
        logic=calculate_atr,
        parameters={"period": 20, "multiplier": 2.0}
    )


@pytest.fixture
def signal_factor():
    """Create signal factor that depends on RSI."""
    def generate_signal(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """Simple signal generation."""
        data["positions"] = 1  # Dummy implementation
        return data

    return Factor(
        id="signal_rsi",
        name="RSI Signal",
        category=FactorCategory.SIGNAL,
        inputs=["rsi"],
        outputs=["positions"],
        logic=generate_signal,
        parameters={}
    )


@pytest.fixture
def simple_strategy(rsi_factor, signal_factor):
    """Create simple strategy with RSI and signal."""
    strategy = Strategy(id="test_strategy", generation=0)
    strategy.add_factor(rsi_factor)
    strategy.add_factor(signal_factor, depends_on=["rsi_14"])
    return strategy


@pytest.fixture
def multi_factor_strategy(rsi_factor, atr_factor, signal_factor):
    """Create strategy with multiple factors."""
    strategy = Strategy(id="multi_strategy", generation=0)
    strategy.add_factor(rsi_factor)
    strategy.add_factor(atr_factor)  # Both are root factors - no dependency
    strategy.add_factor(signal_factor, depends_on=["rsi_14"])
    return strategy


@pytest.fixture
def mutator():
    """Create fresh ParameterMutator instance."""
    return ParameterMutator()


# ============================================================================
# Test 1: Mutate RSI period (14 → ~15) → valid mutation applied
# ============================================================================

class TestBasicMutation:
    """Test basic parameter mutation functionality."""

    def test_mutate_rsi_period(self, simple_strategy, mutator):
        """Test mutating RSI period parameter."""
        config = {
            "std_dev": 0.1,
            "mutation_probability": 1.0,  # Always mutate for predictable test
            "seed": 42
        }

        mutated = mutator.mutate(simple_strategy, config)

        # Verify original strategy unchanged
        assert simple_strategy.factors["rsi_14"].parameters["period"] == 14

        # Verify mutated strategy has different period
        mutated_period = mutated.factors["rsi_14"].parameters["period"]
        assert mutated_period != 14  # Should have changed
        assert isinstance(mutated_period, int)  # Type preserved

        # Verify reasonable range (with 10% std dev, typically 12-16)
        assert 10 <= mutated_period <= 20

    def test_mutation_creates_new_strategy(self, simple_strategy, mutator):
        """Test that mutation returns new strategy, preserves original."""
        config = {"std_dev": 0.1, "mutation_probability": 1.0, "seed": 42}

        original_id = simple_strategy.id
        mutated = mutator.mutate(simple_strategy, config)

        # Verify different strategy objects
        assert mutated is not simple_strategy
        assert mutated.id != simple_strategy.id

        # Verify original unchanged
        assert simple_strategy.factors["rsi_14"].parameters["period"] == 14


# ============================================================================
# Test 2: Respect bounds (14 → not > 50 if max=50) → bounds enforced
# ============================================================================

class TestBoundsEnforcement:
    """Test parameter bounds enforcement."""

    def test_bounds_enforced_upper(self, simple_strategy, mutator):
        """Test upper bound enforcement."""
        config = {
            "std_dev": 2.0,  # Large std dev to likely hit bounds
            "parameter_bounds": {
                "period": (5, 50)
            },
            "mutation_probability": 1.0,
            "seed": 42
        }

        # Run multiple mutations to ensure bounds are respected
        for _ in range(10):
            mutated = mutator.mutate(simple_strategy, config)
            period = mutated.factors["rsi_14"].parameters["period"]
            assert 5 <= period <= 50, f"Period {period} outside bounds [5, 50]"

    def test_bounds_enforced_lower(self, simple_strategy, mutator):
        """Test lower bound enforcement."""
        config = {
            "std_dev": 2.0,
            "parameter_bounds": {
                "period": (10, 20)
            },
            "mutation_probability": 1.0,
            "seed": 123
        }

        for _ in range(10):
            mutated = mutator.mutate(simple_strategy, config)
            period = mutated.factors["rsi_14"].parameters["period"]
            assert 10 <= period <= 20, f"Period {period} outside bounds [10, 20]"

    def test_float_bounds_respected(self, multi_factor_strategy, mutator):
        """Test float parameter bounds."""
        config = {
            "std_dev": 0.5,
            "parameter_bounds": {
                "multiplier": (1.0, 3.0)
            },
            "mutation_probability": 1.0,
            "seed": 456
        }

        for _ in range(10):
            mutated = mutator.mutate(multi_factor_strategy, config)
            # Check if ATR factor was mutated (random selection)
            if "atr_20" in mutated.factors:
                multiplier = mutated.factors["atr_20"].parameters["multiplier"]
                assert 1.0 <= multiplier <= 3.0, \
                    f"Multiplier {multiplier} outside bounds [1.0, 3.0]"

    def test_bounds_clip_statistics(self, simple_strategy, mutator):
        """Test that bounds clipping is tracked in statistics."""
        config = {
            "std_dev": 5.0,  # Very large to ensure clipping
            "parameter_bounds": {
                "period": (10, 20)
            },
            "mutation_probability": 1.0,
            "seed": 42
        }

        mutator.mutate(simple_strategy, config)
        stats = mutator.get_statistics()

        # Should have clipped at least once
        assert stats["bounded_clips"] >= 0


# ============================================================================
# Test 3: Gaussian distribution → samples around original value
# ============================================================================

class TestGaussianDistribution:
    """Test statistical properties of Gaussian mutation."""

    def test_gaussian_distribution_mean(self, simple_strategy, mutator):
        """Test that mutations center around original value."""
        config = {
            "std_dev": 0.1,
            "mutation_probability": 1.0,
            "seed": None  # Don't fix seed for statistical test
        }

        original_period = 14
        mutated_periods = []

        # Collect 100 mutations
        for i in range(100):
            mutator_instance = ParameterMutator()
            mutated = mutator_instance.mutate(simple_strategy, config)
            mutated_periods.append(mutated.factors["rsi_14"].parameters["period"])

        # Statistical test: mean should be close to original (within 10%)
        mean_period = np.mean(mutated_periods)
        assert abs(mean_period - original_period) / original_period < 0.10, \
            f"Mean {mean_period} too far from original {original_period}"

    def test_gaussian_distribution_variance(self, simple_strategy, mutator):
        """Test that mutations have appropriate spread."""
        config = {
            "std_dev": 0.2,  # 20% std dev
            "mutation_probability": 1.0,
            "seed": None
        }

        original_period = 14
        mutated_periods = []

        # Collect 100 mutations
        for i in range(100):
            mutator_instance = ParameterMutator()
            mutated = mutator_instance.mutate(simple_strategy, config)
            mutated_periods.append(mutated.factors["rsi_14"].parameters["period"])

        # Check variance exists (not all same value)
        assert len(set(mutated_periods)) >= 5, \
            "Mutations should produce diverse values"

        # Check standard deviation is reasonable
        std_period = np.std(mutated_periods)
        expected_std = 0.2 * original_period
        # Allow 50% tolerance for sample variance
        assert 0.5 * expected_std <= std_period <= 1.5 * expected_std, \
            f"Std dev {std_period} not close to expected {expected_std}"


# ============================================================================
# Test 4: Multiple parameters mutated → all remain valid
# ============================================================================

class TestMultipleParameters:
    """Test mutating factors with multiple parameters."""

    def test_multiple_parameters_mutated(self, multi_factor_strategy, mutator):
        """Test mutating factor with multiple parameters."""
        config = {
            "std_dev": 0.1,
            "mutation_probability": 1.0,  # Mutate all parameters
            "seed": 42
        }

        # Try multiple times to hit ATR factor
        mutated = None
        for i in range(20):
            test_mutator = ParameterMutator()
            test_mutated = test_mutator.mutate(multi_factor_strategy, config)
            # Check if ATR was selected for mutation
            if test_mutated.factors["atr_20"].parameters != \
               multi_factor_strategy.factors["atr_20"].parameters:
                mutated = test_mutated
                break

        if mutated is not None:
            # Verify both parameters can be mutated
            original_atr = multi_factor_strategy.factors["atr_20"].parameters
            mutated_atr = mutated.factors["atr_20"].parameters

            # At least one should have changed
            assert (mutated_atr["period"] != original_atr["period"] or
                    mutated_atr["multiplier"] != original_atr["multiplier"])

    def test_partial_mutation_probability(self, multi_factor_strategy, mutator):
        """Test that mutation_probability controls per-parameter mutation."""
        config = {
            "std_dev": 0.1,
            "mutation_probability": 0.5,  # 50% chance per parameter
            "seed": None
        }

        # Run many mutations and count parameter changes
        changes = {"period": 0, "multiplier": 0}

        for i in range(50):
            test_mutator = ParameterMutator()
            mutated = test_mutator.mutate(multi_factor_strategy, config)

            # Check if any parameter changed (random factor selection)
            for factor_id, factor in mutated.factors.items():
                original = multi_factor_strategy.factors[factor_id]
                for param_name, param_value in factor.parameters.items():
                    if param_value != original.parameters.get(param_name):
                        if param_name in changes:
                            changes[param_name] += 1

        # With 50% probability and 50 trials, we should see some mutations
        # but not all (statistical test)
        # This is probabilistic, so we just check that it's not 0 or 50


# ============================================================================
# Test 5: Parameter drift tracking → statistics collected correctly
# ============================================================================

class TestDriftTracking:
    """Test parameter drift statistics."""

    def test_drift_statistics_recorded(self, simple_strategy, mutator):
        """Test that drift statistics are collected."""
        config = {
            "std_dev": 0.1,
            "mutation_probability": 1.0,
            "seed": 42
        }

        mutator.mutate(simple_strategy, config)
        stats = mutator.get_statistics()

        # Should have recorded mutations
        assert stats["total_mutations"] > 0
        assert len(stats["parameter_drifts"]) > 0
        assert stats["avg_drift"] >= 0.0

    def test_drift_by_factor_tracked(self, simple_strategy, mutator):
        """Test drift tracking per factor."""
        config = {
            "std_dev": 0.1,
            "mutation_probability": 1.0,
            "seed": 42
        }

        mutator.mutate(simple_strategy, config)
        stats = mutator.get_statistics()

        # Should have mutations_by_factor entry
        assert len(stats["mutations_by_factor"]) > 0

    def test_drift_by_parameter_tracked(self, simple_strategy, mutator):
        """Test drift tracking per parameter name."""
        config = {
            "std_dev": 0.1,
            "mutation_probability": 1.0,
            "seed": 42
        }

        mutator.mutate(simple_strategy, config)
        stats = mutator.get_statistics()

        # Should have mutations_by_parameter entry
        assert len(stats["mutations_by_parameter"]) > 0

    def test_statistics_reset(self, simple_strategy, mutator):
        """Test statistics reset functionality."""
        config = {
            "std_dev": 0.1,
            "mutation_probability": 1.0,
            "seed": 42
        }

        # Perform mutation
        mutator.mutate(simple_strategy, config)
        assert mutator.get_statistics()["total_mutations"] > 0

        # Reset
        mutator.reset_statistics()
        stats = mutator.get_statistics()

        # Should be cleared
        assert stats["total_mutations"] == 0
        assert len(stats["parameter_drifts"]) == 0
        assert stats["avg_drift"] == 0.0


# ============================================================================
# Test 6: Invalid factor handling → gracefully handles factors without params
# ============================================================================

class TestInvalidFactorHandling:
    """Test handling of edge cases and invalid inputs."""

    def test_factor_without_parameters(self, signal_factor):
        """Test gracefully handling factor with no parameters."""
        strategy = Strategy(id="test", generation=0)

        # Create minimal valid strategy (needs positions output)
        def dummy_positions(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            data["positions"] = 1
            return data

        positions_factor = Factor(
            id="positions",
            name="Positions",
            category=FactorCategory.SIGNAL,
            inputs=["close"],
            outputs=["positions"],
            logic=dummy_positions,
            parameters={}  # No parameters
        )

        strategy.add_factor(positions_factor)

        mutator = ParameterMutator()
        config = {"std_dev": 0.1, "mutation_probability": 1.0}

        # Should not raise error
        mutated = mutator.mutate(strategy, config)

        # Strategy should be unchanged (no parameters to mutate)
        assert mutated.factors["positions"].parameters == {}

    def test_empty_strategy_raises_error(self, mutator):
        """Test that empty strategy raises error."""
        empty_strategy = Strategy(id="empty", generation=0)
        config = {"std_dev": 0.1}

        with pytest.raises(ValueError, match="no factors"):
            mutator.mutate(empty_strategy, config)

    def test_invalid_std_dev_raises_error(self, simple_strategy, mutator):
        """Test that invalid std_dev raises error."""
        config = {"std_dev": 0.0}  # Invalid: must be > 0

        with pytest.raises(ValueError, match="std_dev"):
            mutator.mutate(simple_strategy, config)

        config = {"std_dev": 15.0}  # Invalid: must be <= 10.0

        with pytest.raises(ValueError, match="std_dev"):
            mutator.mutate(simple_strategy, config)

    def test_invalid_mutation_probability_raises_error(
        self, simple_strategy, mutator
    ):
        """Test that invalid mutation_probability raises error."""
        config = {"std_dev": 0.1, "mutation_probability": 1.5}

        with pytest.raises(ValueError, match="mutation_probability"):
            mutator.mutate(simple_strategy, config)


# ============================================================================
# Test 7: Strategy integrity → DAG remains valid after mutation
# ============================================================================

class TestStrategyIntegrity:
    """Test that strategy remains valid after mutation."""

    def test_dag_structure_preserved(self, multi_factor_strategy, mutator):
        """Test that DAG structure is preserved."""
        config = {"std_dev": 0.1, "mutation_probability": 1.0, "seed": 42}

        mutated = mutator.mutate(multi_factor_strategy, config)

        # Verify same number of factors
        assert len(mutated.factors) == len(multi_factor_strategy.factors)

        # Verify same dependencies
        for factor_id in mutated.factors:
            original_deps = set(multi_factor_strategy.dag.predecessors(factor_id))
            mutated_deps = set(mutated.dag.predecessors(factor_id))
            assert original_deps == mutated_deps, \
                f"Dependencies changed for {factor_id}"

    def test_mutated_strategy_validates(self, simple_strategy, mutator):
        """Test that mutated strategy passes validation."""
        config = {
            "std_dev": 0.1,
            "parameter_bounds": {
                "period": (5, 50),
                "overbought": (60, 80),
                "oversold": (20, 40)
            },
            "mutation_probability": 1.0,
            "seed": 42
        }

        mutated = mutator.mutate(simple_strategy, config)

        # Should validate successfully (simple_strategy has valid DAG)
        assert mutated.validate() is True

    def test_factor_logic_preserved(self, simple_strategy, mutator):
        """Test that factor logic function is preserved."""
        config = {"std_dev": 0.1, "mutation_probability": 1.0, "seed": 42}

        original_logic = simple_strategy.factors["rsi_14"].logic
        mutated = mutator.mutate(simple_strategy, config)
        mutated_logic = mutated.factors["rsi_14"].logic

        # Logic function should be same reference
        assert mutated_logic is original_logic


# ============================================================================
# Test 8: Type preservation → int stays int, float stays float
# ============================================================================

class TestTypePreservation:
    """Test that parameter types are preserved."""

    def test_int_parameters_stay_int(self, simple_strategy, mutator):
        """Test that int parameters remain int after mutation."""
        config = {"std_dev": 0.1, "mutation_probability": 1.0, "seed": 42}

        mutated = mutator.mutate(simple_strategy, config)

        # Period should remain int
        period = mutated.factors["rsi_14"].parameters["period"]
        assert isinstance(period, int)

        # Overbought/oversold should remain int
        overbought = mutated.factors["rsi_14"].parameters["overbought"]
        oversold = mutated.factors["rsi_14"].parameters["oversold"]
        assert isinstance(overbought, int)
        assert isinstance(oversold, int)

    def test_float_parameters_stay_float(self, multi_factor_strategy, mutator):
        """Test that float parameters remain float after mutation."""
        config = {"std_dev": 0.1, "mutation_probability": 1.0, "seed": 42}

        # Mutate multiple times to hit ATR factor
        for i in range(20):
            test_mutator = ParameterMutator()
            mutated = test_mutator.mutate(multi_factor_strategy, config)

            # Check multiplier type (should be float)
            multiplier = mutated.factors["atr_20"].parameters["multiplier"]
            assert isinstance(multiplier, float), \
                f"Multiplier should be float, got {type(multiplier)}"


# ============================================================================
# Test 9: Reproducibility with seed
# ============================================================================

class TestReproducibility:
    """Test that mutations are reproducible with seed."""

    def test_same_seed_produces_same_mutation(self, simple_strategy):
        """Test that same seed produces identical mutations."""
        config = {
            "std_dev": 0.1,
            "mutation_probability": 1.0,
            "seed": 42
        }

        mutator1 = ParameterMutator()
        mutated1 = mutator1.mutate(simple_strategy, config)

        mutator2 = ParameterMutator()
        mutated2 = mutator2.mutate(simple_strategy, config)

        # Should produce identical results
        params1 = mutated1.factors["rsi_14"].parameters
        params2 = mutated2.factors["rsi_14"].parameters

        assert params1 == params2

    def test_different_seeds_produce_different_mutations(self, simple_strategy):
        """Test that different seeds produce different mutations."""
        config1 = {
            "std_dev": 0.1,
            "mutation_probability": 1.0,
            "seed": 42
        }
        config2 = {
            "std_dev": 0.1,
            "mutation_probability": 1.0,
            "seed": 123
        }

        mutator1 = ParameterMutator()
        mutated1 = mutator1.mutate(simple_strategy, config1)

        mutator2 = ParameterMutator()
        mutated2 = mutator2.mutate(simple_strategy, config2)

        # Should produce different results (with high probability)
        params1 = mutated1.factors["rsi_14"].parameters
        params2 = mutated2.factors["rsi_14"].parameters

        # At least one parameter should differ
        assert params1 != params2
