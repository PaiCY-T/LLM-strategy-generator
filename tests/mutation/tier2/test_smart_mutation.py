"""
Tests for Smart Mutation Engine - Intelligent operator selection and scheduling.

Covers:
- OperatorStats tracking and success rate calculation
- MutationScheduler rate adaptation and operator probabilities
- SmartMutationEngine operator selection and statistics
- Integration tests for end-to-end workflows

Task: C.5 - Smart Mutation Operators and Scheduling
"""

import pytest
import numpy as np
from typing import Dict, Any

from src.mutation.tier2.smart_mutation_engine import (
    OperatorStats,
    MutationScheduler,
    SmartMutationEngine,
    MutationOperator
)


# ============================================================================
# Mock Mutation Operator for Testing
# ============================================================================


class MockMutationOperator:
    """
    Mock mutation operator for testing.

    Implements the MutationOperator protocol without requiring
    actual Strategy objects or complex mutation logic.
    """

    def __init__(self, name: str = "mock"):
        self.name = name
        self.call_count = 0

    def mutate(self, strategy: Any, config: Dict[str, Any]) -> Any:
        """Mock mutation that just increments call count."""
        self.call_count += 1
        return strategy  # Return unchanged


# ============================================================================
# OperatorStats Tests (8+ tests)
# ============================================================================


class TestOperatorStats:
    """Tests for OperatorStats class."""

    def test_record_success(self):
        """Test recording successful mutation."""
        stats = OperatorStats()
        stats.record("add_factor", success=True)

        assert stats.attempts["add_factor"] == 1
        assert stats.successes["add_factor"] == 1
        assert stats.failures["add_factor"] == 0

    def test_record_failure(self):
        """Test recording failed mutation."""
        stats = OperatorStats()
        stats.record("add_factor", success=False)

        assert stats.attempts["add_factor"] == 1
        assert stats.successes["add_factor"] == 0
        assert stats.failures["add_factor"] == 1

    def test_record_multiple_operators(self):
        """Test recording for multiple operators."""
        stats = OperatorStats()
        stats.record("add_factor", True)
        stats.record("remove_factor", False)
        stats.record("mutate_parameters", True)

        assert stats.attempts["add_factor"] == 1
        assert stats.attempts["remove_factor"] == 1
        assert stats.attempts["mutate_parameters"] == 1

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        stats = OperatorStats()
        stats.record("add_factor", True)
        stats.record("add_factor", True)
        stats.record("add_factor", False)

        rate = stats.get_success_rate("add_factor")
        assert abs(rate - 0.6667) < 0.01  # 2/3 ≈ 0.667

    def test_success_rate_zero_attempts(self):
        """Test success rate with no attempts."""
        stats = OperatorStats()
        rate = stats.get_success_rate("nonexistent")
        assert rate == 0.0

    def test_success_rate_all_failures(self):
        """Test success rate with all failures."""
        stats = OperatorStats()
        stats.record("add_factor", False)
        stats.record("add_factor", False)

        rate = stats.get_success_rate("add_factor")
        assert rate == 0.0

    def test_success_rate_all_successes(self):
        """Test success rate with all successes."""
        stats = OperatorStats()
        stats.record("add_factor", True)
        stats.record("add_factor", True)

        rate = stats.get_success_rate("add_factor")
        assert rate == 1.0

    def test_get_all_rates(self):
        """Test getting all success rates."""
        stats = OperatorStats()
        stats.record("add_factor", True)
        stats.record("add_factor", False)
        stats.record("remove_factor", True)
        stats.record("mutate_parameters", False)

        rates = stats.get_all_rates()

        assert abs(rates["add_factor"] - 0.5) < 0.01
        assert rates["remove_factor"] == 1.0
        assert rates["mutate_parameters"] == 0.0

    def test_multiple_records_same_operator(self):
        """Test multiple recordings for same operator."""
        stats = OperatorStats()

        # Record 10 attempts with 7 successes
        for i in range(10):
            stats.record("add_factor", success=(i < 7))

        assert stats.attempts["add_factor"] == 10
        assert stats.successes["add_factor"] == 7
        assert stats.failures["add_factor"] == 3
        assert abs(stats.get_success_rate("add_factor") - 0.7) < 0.01


# ============================================================================
# MutationScheduler Tests (10+ tests)
# ============================================================================


class TestMutationScheduler:
    """Tests for MutationScheduler class."""

    @pytest.fixture
    def default_config(self):
        """Default scheduler configuration."""
        return {
            "schedule": {
                "max_generations": 100,
                "early_rate": 0.7,
                "mid_rate": 0.4,
                "late_rate": 0.2,
                "diversity_threshold": 0.3,
                "diversity_boost": 0.2
            },
            "initial_probabilities": {
                "add_factor": 0.4,
                "remove_factor": 0.2,
                "replace_factor": 0.2,
                "mutate_parameters": 0.2
            },
            "adaptation": {
                "enable": True,
                "success_rate_weight": 0.3,
                "min_probability": 0.05,
                "update_interval": 5
            }
        }

    def test_early_generation_rate(self, default_config):
        """Test high mutation rate in early generations."""
        scheduler = MutationScheduler(default_config)

        # Generation 5 out of 100 (5% progress) -> Early phase
        rate = scheduler.get_mutation_rate(generation=5, diversity=0.5, stagnation_count=0)

        # Should be close to early_rate (0.7)
        assert 0.5 <= rate <= 0.8

    def test_mid_generation_rate(self, default_config):
        """Test medium mutation rate in mid generations."""
        scheduler = MutationScheduler(default_config)

        # Generation 50 out of 100 (50% progress) -> Mid phase
        rate = scheduler.get_mutation_rate(generation=50, diversity=0.5, stagnation_count=0)

        # Should be close to mid_rate (0.4)
        assert 0.3 <= rate <= 0.5

    def test_late_generation_rate(self, default_config):
        """Test low mutation rate in late generations."""
        scheduler = MutationScheduler(default_config)

        # Generation 90 out of 100 (90% progress) -> Late phase
        rate = scheduler.get_mutation_rate(generation=90, diversity=0.5, stagnation_count=0)

        # Should be close to late_rate (0.2)
        assert 0.1 <= rate <= 0.3

    def test_diversity_boost(self, default_config):
        """Test mutation rate increase with low diversity."""
        scheduler = MutationScheduler(default_config)

        # Mid generation, low diversity (< 0.3 threshold)
        rate_low_diversity = scheduler.get_mutation_rate(
            generation=50,
            diversity=0.2,  # Below threshold
            stagnation_count=0
        )

        # Mid generation, high diversity
        rate_high_diversity = scheduler.get_mutation_rate(
            generation=50,
            diversity=0.8,  # Above threshold
            stagnation_count=0
        )

        # Low diversity should have higher rate
        assert rate_low_diversity > rate_high_diversity
        # Difference should be approximately diversity_boost (0.2)
        assert abs((rate_low_diversity - rate_high_diversity) - 0.2) < 0.01

    def test_stagnation_boost(self, default_config):
        """Test mutation rate increase with stagnation."""
        scheduler = MutationScheduler(default_config)

        # No stagnation
        rate_no_stagnation = scheduler.get_mutation_rate(
            generation=50,
            diversity=0.5,
            stagnation_count=0
        )

        # 10 generations of stagnation (should add 0.1 * 2 = 0.2)
        rate_with_stagnation = scheduler.get_mutation_rate(
            generation=50,
            diversity=0.5,
            stagnation_count=10
        )

        # Stagnation should increase rate
        assert rate_with_stagnation > rate_no_stagnation
        # 10 generations / 5 = 2 boosts * 0.1 = 0.2
        assert abs((rate_with_stagnation - rate_no_stagnation) - 0.2) < 0.01

    def test_operator_probabilities_early(self, default_config):
        """Test operator probabilities favor add_factor early."""
        scheduler = MutationScheduler(default_config)

        success_rates = {
            "add_factor": 0.5,
            "remove_factor": 0.5,
            "replace_factor": 0.5,
            "mutate_parameters": 0.5
        }

        probs = scheduler.get_operator_probabilities(
            generation=5,  # Early
            max_generations=100,
            success_rates=success_rates
        )

        # add_factor should have highest probability early
        assert probs["add_factor"] > probs["mutate_parameters"]
        assert probs["add_factor"] > probs["remove_factor"]

    def test_operator_probabilities_mid(self, default_config):
        """Test operator probabilities balanced in mid generations."""
        scheduler = MutationScheduler(default_config)

        success_rates = {
            "add_factor": 0.5,
            "remove_factor": 0.5,
            "replace_factor": 0.5,
            "mutate_parameters": 0.5
        }

        probs = scheduler.get_operator_probabilities(
            generation=50,  # Mid
            max_generations=100,
            success_rates=success_rates
        )

        # All operators should have similar probabilities
        prob_values = list(probs.values())
        assert max(prob_values) - min(prob_values) < 0.2  # Within 20%

    def test_operator_probabilities_late(self, default_config):
        """Test operator probabilities favor mutate_parameters late."""
        scheduler = MutationScheduler(default_config)

        success_rates = {
            "add_factor": 0.5,
            "remove_factor": 0.5,
            "replace_factor": 0.5,
            "mutate_parameters": 0.5
        }

        probs = scheduler.get_operator_probabilities(
            generation=90,  # Late
            max_generations=100,
            success_rates=success_rates
        )

        # mutate_parameters should have highest probability late
        assert probs["mutate_parameters"] > probs["add_factor"]
        assert probs["mutate_parameters"] > probs["remove_factor"]

    def test_success_rate_adaptation(self, default_config):
        """Test probability adjustment based on success rates."""
        scheduler = MutationScheduler(default_config)

        # High success for add_factor, low for others
        success_rates = {
            "add_factor": 0.9,  # High success
            "remove_factor": 0.1,  # Low success
            "replace_factor": 0.5,  # Neutral
            "mutate_parameters": 0.5
        }

        probs = scheduler.get_operator_probabilities(
            generation=50,  # Mid
            max_generations=100,
            success_rates=success_rates
        )

        # High success operator should have boosted probability
        # Low success operator should have reduced probability
        assert probs["add_factor"] > probs["remove_factor"]

    def test_probabilities_sum_to_one(self, default_config):
        """Test that operator probabilities sum to 1.0."""
        scheduler = MutationScheduler(default_config)

        success_rates = {
            "add_factor": 0.8,
            "remove_factor": 0.3,
            "replace_factor": 0.6,
            "mutate_parameters": 0.4
        }

        for generation in [5, 50, 90]:
            probs = scheduler.get_operator_probabilities(
                generation=generation,
                max_generations=100,
                success_rates=success_rates
            )

            total = sum(probs.values())
            assert abs(total - 1.0) < 0.01  # Allow small floating point error

    def test_config_validation_invalid_rate(self):
        """Test config validation with invalid mutation rate."""
        config = {
            "schedule": {
                "early_rate": 1.5  # Invalid: > 1.0
            }
        }

        with pytest.raises(ValueError, match="early_rate must be in"):
            MutationScheduler(config)

    def test_config_validation_invalid_probabilities(self):
        """Test config validation with invalid initial probabilities."""
        config = {
            "initial_probabilities": {
                "add_factor": 0.5,
                "remove_factor": 0.5,
                "replace_factor": 0.5,
                "mutate_parameters": 0.5
                # Sum = 2.0, should be ~1.0
            }
        }

        with pytest.raises(ValueError, match="must sum to"):
            MutationScheduler(config)

    def test_adaptation_disabled(self, default_config):
        """Test that adaptation can be disabled."""
        # Disable adaptation
        config = default_config.copy()
        config["adaptation"]["enable"] = False

        scheduler = MutationScheduler(config)

        # Different success rates
        success_rates_high = {
            "add_factor": 0.9,
            "remove_factor": 0.9,
            "replace_factor": 0.9,
            "mutate_parameters": 0.9
        }

        success_rates_low = {
            "add_factor": 0.1,
            "remove_factor": 0.1,
            "replace_factor": 0.1,
            "mutate_parameters": 0.1
        }

        # Probabilities should be same regardless of success rates
        probs_high = scheduler.get_operator_probabilities(
            generation=50,
            max_generations=100,
            success_rates=success_rates_high
        )

        probs_low = scheduler.get_operator_probabilities(
            generation=50,
            max_generations=100,
            success_rates=success_rates_low
        )

        # Should be equal (no adaptation)
        for operator in probs_high.keys():
            assert abs(probs_high[operator] - probs_low[operator]) < 0.01


# ============================================================================
# SmartMutationEngine Tests (12+ tests)
# ============================================================================


class TestSmartMutationEngine:
    """Tests for SmartMutationEngine class."""

    @pytest.fixture
    def mock_operators(self):
        """Create mock mutation operators."""
        return {
            "add_factor": MockMutationOperator("add_factor"),
            "remove_factor": MockMutationOperator("remove_factor"),
            "replace_factor": MockMutationOperator("replace_factor"),
            "mutate_parameters": MockMutationOperator("mutate_parameters")
        }

    @pytest.fixture
    def default_config(self):
        """Default engine configuration."""
        return {
            "initial_probabilities": {
                "add_factor": 0.4,
                "remove_factor": 0.2,
                "replace_factor": 0.2,
                "mutate_parameters": 0.2
            },
            "schedule": {
                "max_generations": 100,
                "early_rate": 0.7,
                "mid_rate": 0.4,
                "late_rate": 0.2
            },
            "adaptation": {
                "enable": True,
                "success_rate_weight": 0.3
            }
        }

    def test_initialization(self, mock_operators, default_config):
        """Test engine initialization."""
        engine = SmartMutationEngine(mock_operators, default_config)

        assert engine.operators == mock_operators
        assert engine.config == default_config
        assert isinstance(engine.stats, OperatorStats)
        assert isinstance(engine.scheduler, MutationScheduler)

    def test_initialization_empty_operators(self, default_config):
        """Test initialization with empty operators dict."""
        with pytest.raises(ValueError, match="Must provide at least one"):
            SmartMutationEngine({}, default_config)

    def test_initialization_invalid_config_operator(self, mock_operators):
        """Test initialization with operator in config but not in operators dict."""
        config = {
            "initial_probabilities": {
                "add_factor": 0.5,
                "remove_factor": 0.3,
                "replace_factor": 0.2,
                "nonexistent_operator": 0.0  # Not in operators dict
            }
        }

        with pytest.raises(ValueError, match="not found in operators"):
            SmartMutationEngine(mock_operators, config)

    def test_select_operator_returns_valid(self, mock_operators, default_config):
        """Test that select_operator returns valid operator and instance."""
        engine = SmartMutationEngine(mock_operators, default_config)

        context = {"generation": 10, "diversity": 0.5}
        operator_name, operator = engine.select_operator(context)

        assert operator_name in mock_operators
        assert operator == mock_operators[operator_name]

    def test_select_operator_probability_distribution(self, mock_operators, default_config):
        """Test that operator selection follows probability distribution."""
        # Set seed for reproducibility
        np.random.seed(42)

        engine = SmartMutationEngine(mock_operators, default_config)

        # Select operators many times
        selections = []
        context = {"generation": 10, "diversity": 0.5}
        for _ in range(1000):
            operator_name, _ = engine.select_operator(context)
            selections.append(operator_name)

        # Count selections
        counts = {name: selections.count(name) for name in mock_operators.keys()}

        # Early generation should favor add_factor
        # Not exact due to randomness, but should be roughly proportional
        assert counts["add_factor"] > counts["mutate_parameters"]

    def test_update_success_rate(self, mock_operators, default_config):
        """Test updating success rate statistics."""
        engine = SmartMutationEngine(mock_operators, default_config)

        engine.update_success_rate("add_factor", success=True)
        engine.update_success_rate("add_factor", success=False)

        stats = engine.get_statistics()

        assert stats["operator_attempts"]["add_factor"] == 2
        assert stats["operator_successes"]["add_factor"] == 1
        assert stats["operator_failures"]["add_factor"] == 1

    def test_get_statistics_complete(self, mock_operators, default_config):
        """Test get_statistics returns complete data."""
        engine = SmartMutationEngine(mock_operators, default_config)

        # Record some statistics
        engine.update_success_rate("add_factor", True)
        engine.update_success_rate("remove_factor", False)
        engine.update_success_rate("mutate_parameters", True)

        stats = engine.get_statistics()

        # Check all expected keys are present
        assert "operator_attempts" in stats
        assert "operator_successes" in stats
        assert "operator_failures" in stats
        assert "operator_success_rates" in stats
        assert "total_attempts" in stats
        assert "total_successes" in stats

        # Check values
        assert stats["total_attempts"] == 3
        assert stats["total_successes"] == 2

    def test_select_operator_no_context(self, mock_operators, default_config):
        """Test select_operator with no context provided."""
        engine = SmartMutationEngine(mock_operators, default_config)

        # Should not raise error
        operator_name, operator = engine.select_operator()

        assert operator_name in mock_operators
        assert operator is not None

    def test_select_operator_empty_context(self, mock_operators, default_config):
        """Test select_operator with empty context dict."""
        engine = SmartMutationEngine(mock_operators, default_config)

        operator_name, operator = engine.select_operator(context={})

        assert operator_name in mock_operators
        assert operator is not None

    def test_multiple_operators_selected(self, mock_operators, default_config):
        """Test that all operators can be selected over time."""
        np.random.seed(42)

        engine = SmartMutationEngine(mock_operators, default_config)

        selected_operators = set()
        context = {"generation": 50, "diversity": 0.5}  # Mid-phase for balanced selection

        # Select many times to ensure all operators get selected
        for _ in range(500):
            operator_name, _ = engine.select_operator(context)
            selected_operators.add(operator_name)

        # All operators should have been selected at least once
        assert selected_operators == set(mock_operators.keys())

    def test_adaptive_probabilities_boost_successful(self, mock_operators, default_config):
        """Test that successful operators get boosted over time."""
        np.random.seed(42)

        engine = SmartMutationEngine(mock_operators, default_config)

        # Simulate add_factor being very successful
        for _ in range(20):
            engine.update_success_rate("add_factor", success=True)

        # Simulate remove_factor being unsuccessful
        for _ in range(20):
            engine.update_success_rate("remove_factor", success=False)

        # Select operators many times
        selections = []
        context = {"generation": 50, "diversity": 0.5}
        for _ in range(500):
            operator_name, _ = engine.select_operator(context)
            selections.append(operator_name)

        # Count selections
        counts = {name: selections.count(name) for name in mock_operators.keys()}

        # Successful operator should be selected more than unsuccessful
        assert counts["add_factor"] > counts["remove_factor"]

    def test_statistics_retrieval_immutability(self, mock_operators, default_config):
        """Test that get_statistics returns a copy (not reference)."""
        engine = SmartMutationEngine(mock_operators, default_config)

        engine.update_success_rate("add_factor", True)

        stats1 = engine.get_statistics()
        stats1["operator_attempts"]["add_factor"] = 999  # Modify returned dict

        stats2 = engine.get_statistics()

        # Original should not be affected
        assert stats2["operator_attempts"]["add_factor"] == 1

    def test_edge_case_single_operator(self):
        """Test engine with only a single operator."""
        operators = {"mutate_parameters": MockMutationOperator("mutate_parameters")}

        config = {
            "initial_probabilities": {"mutate_parameters": 1.0},
            "schedule": {
                "max_generations": 100,
                "early_rate": 0.7,
                "mid_rate": 0.4,
                "late_rate": 0.2
            },
            "adaptation": {
                "enable": True,
                "success_rate_weight": 0.3
            }
        }

        engine = SmartMutationEngine(operators, config)

        # Should always select the only operator
        for _ in range(10):
            operator_name, _ = engine.select_operator()
            assert operator_name == "mutate_parameters"


# ============================================================================
# Integration Tests (6+ tests)
# ============================================================================


class TestIntegration:
    """Integration tests for SmartMutationEngine + Scheduler."""

    @pytest.fixture
    def full_setup(self):
        """Create full engine setup."""
        operators = {
            "add_factor": MockMutationOperator("add_factor"),
            "remove_factor": MockMutationOperator("remove_factor"),
            "replace_factor": MockMutationOperator("replace_factor"),
            "mutate_parameters": MockMutationOperator("mutate_parameters")
        }

        config = {
            "initial_probabilities": {
                "add_factor": 0.4,
                "remove_factor": 0.2,
                "replace_factor": 0.2,
                "mutate_parameters": 0.2
            },
            "schedule": {
                "max_generations": 100,
                "early_rate": 0.7,
                "mid_rate": 0.4,
                "late_rate": 0.2,
                "diversity_threshold": 0.3,
                "diversity_boost": 0.2
            },
            "adaptation": {
                "enable": True,
                "success_rate_weight": 0.3,
                "min_probability": 0.05,
                "update_interval": 5
            }
        }

        return SmartMutationEngine(operators, config), operators, config

    def test_end_to_end_selection(self, full_setup):
        """Test end-to-end operator selection workflow."""
        engine, operators, config = full_setup

        context = {
            "generation": 10,
            "diversity": 0.5,
            "population_size": 20
        }

        # Select operator
        operator_name, operator = engine.select_operator(context)

        # Should return valid operator
        assert operator_name in operators
        assert operator == operators[operator_name]

        # Update statistics
        engine.update_success_rate(operator_name, success=True)

        # Get statistics
        stats = engine.get_statistics()
        assert stats["total_attempts"] == 1
        assert stats["total_successes"] == 1

    def test_100_generation_simulation(self, full_setup):
        """Test mutation rates evolve correctly over 100 generations."""
        engine, _, _ = full_setup

        rates = []
        for generation in range(100):
            # Get mutation rate from scheduler
            rate = engine.scheduler.get_mutation_rate(
                generation=generation,
                diversity=0.5,
                stagnation_count=0
            )
            rates.append(rate)

        # Early rates should be higher than late rates
        early_avg = np.mean(rates[:20])
        late_avg = np.mean(rates[80:])

        assert early_avg > late_avg

    def test_operator_diversity_over_time(self, full_setup):
        """Test that all operators get selected over time."""
        np.random.seed(42)
        engine, operators, _ = full_setup

        selected_per_phase = {
            "early": set(),
            "mid": set(),
            "late": set()
        }

        # Early phase (0-20%)
        for generation in range(20):
            context = {"generation": generation, "diversity": 0.5}
            operator_name, _ = engine.select_operator(context)
            selected_per_phase["early"].add(operator_name)

        # Mid phase (40-60%)
        for generation in range(40, 60):
            context = {"generation": generation, "diversity": 0.5}
            operator_name, _ = engine.select_operator(context)
            selected_per_phase["mid"].add(operator_name)

        # Late phase (80-100%)
        for generation in range(80, 100):
            context = {"generation": generation, "diversity": 0.5}
            operator_name, _ = engine.select_operator(context)
            selected_per_phase["late"].add(operator_name)

        # All operators should appear in at least one phase
        all_selected = selected_per_phase["early"] | selected_per_phase["mid"] | selected_per_phase["late"]
        assert all_selected == set(operators.keys())

    def test_adaptive_learning(self, full_setup):
        """Test that probabilities shift toward successful operators."""
        np.random.seed(42)
        engine, _, _ = full_setup

        # Simulate evolution with add_factor being very successful
        for generation in range(50):
            context = {"generation": generation, "diversity": 0.5}
            operator_name, _ = engine.select_operator(context)

            # add_factor always succeeds, others fail
            success = (operator_name == "add_factor")
            engine.update_success_rate(operator_name, success)

        # Get statistics
        stats = engine.get_statistics()
        rates = stats["operator_success_rates"]

        # add_factor should have high success rate
        if "add_factor" in rates:
            assert rates["add_factor"] > 0.8

        # Now select operators and count - add_factor should dominate
        selections = []
        for _ in range(200):
            context = {"generation": 50, "diversity": 0.5}
            operator_name, _ = engine.select_operator(context)
            selections.append(operator_name)

        counts = {name: selections.count(name) for name in engine.operators.keys()}

        # add_factor should be selected most often
        assert counts["add_factor"] >= max(counts["remove_factor"], counts["replace_factor"])

    def test_configuration_variants(self):
        """Test different configuration variants work correctly."""
        operators = {
            "add_factor": MockMutationOperator("add_factor"),
            "mutate_parameters": MockMutationOperator("mutate_parameters")
        }

        # Minimal config
        config1 = {
            "initial_probabilities": {
                "add_factor": 0.5,
                "mutate_parameters": 0.5
            }
        }
        engine1 = SmartMutationEngine(operators, config1)
        assert engine1 is not None

        # Full config
        config2 = {
            "initial_probabilities": {
                "add_factor": 0.5,
                "mutate_parameters": 0.5
            },
            "schedule": {
                "max_generations": 50,
                "early_rate": 0.8,
                "mid_rate": 0.5,
                "late_rate": 0.1
            },
            "adaptation": {
                "enable": False
            }
        }
        engine2 = SmartMutationEngine(operators, config2)
        assert engine2.scheduler.max_generations == 50

    def test_reproducibility(self, full_setup):
        """Test that same seed produces same selections."""
        engine1, operators, config = full_setup

        # First run with seed
        np.random.seed(42)
        selections1 = []
        for generation in range(20):
            context = {"generation": generation, "diversity": 0.5}
            operator_name, _ = engine1.select_operator(context)
            selections1.append(operator_name)

        # Second run with same seed
        engine2 = SmartMutationEngine(operators, config)
        np.random.seed(42)
        selections2 = []
        for generation in range(20):
            context = {"generation": generation, "diversity": 0.5}
            operator_name, _ = engine2.select_operator(context)
            selections2.append(operator_name)

        # Should be identical
        assert selections1 == selections2


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
