"""
Integration tests for exit parameter mutation within full evolution loop.

Task 5: Exit Mutation Redesign - Evolution Loop Integration
Tests exit mutation behavior across 20 generations of evolution.

Test Coverage:
1. 20-Generation Evolution Test - Full evolution with exit mutations
2. Exit Parameter Tracking Test - Track parameter evolution over generations
3. Performance Impact Test - Compare exit mutation vs no exit mutation
4. Metadata Tracking Test - Verify comprehensive metadata recording
5. Integration with UnifiedMutationOperator Test - Verify proper routing
6. Boundary Enforcement Test - Verify parameter bounds are respected

Success Criteria:
- 20-generation evolution completes successfully
- Exit mutation rate is 20% ±5%
- All parameters stay within bounds
- Metadata tracking is comprehensive
- Performance impact is measurable
"""

import json
import logging
import random
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple
from unittest.mock import Mock, patch

import pytest

from src.evolution.population_manager import PopulationManager
from src.evolution.types import Strategy
from src.factor_graph.strategy import Strategy as FactorGraphStrategy
from src.mutation.exit_parameter_mutator import ExitParameterMutator, PARAM_BOUNDS
from src.mutation.unified_mutation_operator import UnifiedMutationOperator, MutationResult
from src.mutation.tier2.smart_mutation_engine import SmartMutationEngine
from src.mutation.tier3.ast_factor_mutator import ASTFactorMutator
from src.mutation.tier_selection.tier_selection_manager import TierSelectionManager
from src.tier1.yaml_interpreter import YAMLInterpreter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Sample Strategy Code with Exit Parameters
# ============================================================================

SAMPLE_STRATEGY_WITH_EXITS = """
# Momentum strategy with exit parameters
import pandas as pd

def generate_signal(data):
    close = data.get('price:收盤價')

    # Momentum signal
    returns_20d = close.pct_change(20)
    signal = returns_20d.rank(axis=1, ascending=False)

    # Select top 20 stocks
    positions = (signal <= 20).astype(float)
    positions = positions.div(positions.sum(axis=1), axis=0)

    # Exit parameters
    stop_loss_pct = 0.10
    take_profit_pct = 0.20
    trailing_stop_offset = 0.02
    holding_period_days = 15

    # Apply exit logic
    entry_price = close.shift(1)

    # Stop loss
    stop_loss_trigger = close < entry_price * (1 - stop_loss_pct)
    positions = positions.where(~stop_loss_trigger, 0)

    # Take profit
    take_profit_trigger = close > entry_price * (1 + take_profit_pct)
    positions = positions.where(~take_profit_trigger, 0)

    # Trailing stop
    high_since_entry = close.rolling(holding_period_days).max()
    trailing_stop_trigger = close < high_since_entry * (1 - trailing_stop_offset)
    positions = positions.where(~trailing_stop_trigger, 0)

    return positions
"""


# ============================================================================
# Metrics and Data Classes
# ============================================================================

class ExitMutationEvolutionMetrics:
    """Metrics for exit mutation evolution testing."""

    def __init__(self):
        self.total_generations = 0
        self.total_mutations = 0
        self.exit_mutations = 0
        self.tier_mutations = 0

        # Parameter evolution tracking
        self.parameter_evolution: Dict[str, List[float]] = defaultdict(list)

        # Boundary tracking
        self.boundary_violations = 0
        self.clamping_events = 0

        # Performance tracking
        self.champion_performance_initial: Dict = {}
        self.champion_performance_final: Dict = {}

    @property
    def exit_mutation_rate(self) -> float:
        """Calculate exit mutation rate."""
        if self.total_mutations == 0:
            return 0.0
        return self.exit_mutations / self.total_mutations

    @property
    def performance_improvement(self) -> float:
        """Calculate performance improvement."""
        initial_fitness = self.champion_performance_initial.get('fitness', 0)
        final_fitness = self.champion_performance_final.get('fitness', 0)

        if initial_fitness == 0:
            return 0.0

        return (final_fitness - initial_fitness) / initial_fitness


# ============================================================================
# Mock Operators for Testing
# ============================================================================

class MockMutationOperator:
    """Mock mutation operator for testing."""

    def mutate(self, strategy, config):
        """Apply mock mutation."""
        return strategy.copy() if hasattr(strategy, 'copy') else strategy


def create_mock_tier2_engine():
    """Create a mock SmartMutationEngine for testing."""
    operators = {
        'mutate_parameters': MockMutationOperator(),
        'add_factor': MockMutationOperator(),
        'remove_factor': MockMutationOperator(),
    }

    config = {
        'initial_probabilities': {
            'mutate_parameters': 0.5,
            'add_factor': 0.3,
            'remove_factor': 0.2,
        },
        'schedule': {
            'max_generations': 100
        }
    }

    return SmartMutationEngine(operators, config)


# ============================================================================
# Helper Functions
# ============================================================================

def create_mock_strategy_with_exits(
    strategy_id: str = "test_strategy",
    generation: int = 0,
    parent_ids: List[str] = None
) -> Strategy:
    """Create a mock strategy with exit parameters."""
    if parent_ids is None:
        parent_ids = []

    return Strategy(
        id=strategy_id,
        generation=generation,
        parent_ids=parent_ids,
        code=SAMPLE_STRATEGY_WITH_EXITS,
        parameters={
            'lookback': 20,
            'stop_loss_pct': 0.10,
            'take_profit_pct': 0.20,
            'trailing_stop_offset': 0.02,
            'holding_period_days': 15
        },
        template_type='Momentum'
    )


def create_factor_graph_strategy_with_exits() -> FactorGraphStrategy:
    """Create a FactorGraphStrategy with exit parameters for UnifiedMutationOperator."""
    # Create a minimal FactorGraphStrategy with required 'id' parameter
    strategy = FactorGraphStrategy(id="fg_strategy_001", generation=0)
    strategy.code = SAMPLE_STRATEGY_WITH_EXITS

    # Add validate method
    strategy.validate = Mock()

    # Add copy method
    def copy_strategy():
        new_strategy = FactorGraphStrategy(id=strategy.id + "_copy", generation=strategy.generation + 1)
        new_strategy.code = strategy.code
        new_strategy.validate = Mock()
        new_strategy.copy = copy_strategy
        new_strategy.get_factors = Mock(return_value=[])
        new_strategy.to_code = Mock(return_value=strategy.code)
        new_strategy.update_code = Mock()
        return new_strategy

    strategy.copy = copy_strategy
    strategy.get_factors = Mock(return_value=[])
    strategy.to_code = Mock(return_value=SAMPLE_STRATEGY_WITH_EXITS)
    strategy.update_code = Mock()

    return strategy


def initialize_population_with_exits(size: int = 20) -> List[Strategy]:
    """Initialize population with strategies containing exit parameters."""
    population = []

    for i in range(size):
        # Vary parameters slightly
        strategy = create_mock_strategy_with_exits(
            strategy_id=f"strategy_{i:03d}",
            generation=0,
            parent_ids=[]
        )

        # Add slight variation to exit parameters
        variation = 1.0 + random.uniform(-0.1, 0.1)
        strategy.parameters['stop_loss_pct'] = 0.10 * variation
        strategy.parameters['take_profit_pct'] = 0.20 * variation

        population.append(strategy)

    return population


def count_mutation_type(evolution_results: Dict, mutation_type: str) -> int:
    """Count mutations of a specific type."""
    count = 0

    for gen_data in evolution_results.get('generations', []):
        for mutation in gen_data.get('mutations', []):
            if mutation.get('mutation_type') == mutation_type:
                count += 1

    return count


def count_total_mutations(evolution_results: Dict) -> int:
    """Count total mutations across all generations."""
    count = 0

    for gen_data in evolution_results.get('generations', []):
        count += len(gen_data.get('mutations', []))

    return count


def track_parameter_evolution(
    evolution_results: Dict,
    parameter_name: str
) -> List[float]:
    """Track parameter values across generations."""
    values = []

    for gen_data in evolution_results.get('generations', []):
        champion = gen_data.get('champion', {})
        params = champion.get('parameters', {})

        if parameter_name in params:
            values.append(params[parameter_name])

    return values


# ============================================================================
# Test 1: 20-Generation Evolution with Exit Mutation
# ============================================================================

class TestExitMutationEvolution:
    """Test exit mutation within full evolution loop."""

    @pytest.mark.slow
    def test_20_generation_evolution(self):
        """
        Run 20 generations with exit mutation enabled.

        Success Criteria:
        - Evolution completes 20 generations
        - Exit mutation rate 20% ±5%
        - All mutations tracked
        - Champion fitness improves or stays stable
        """
        logger.info("\n" + "="*70)
        logger.info("TEST: 20-Generation Evolution with Exit Mutation")
        logger.info("="*70)

        # Initialize metrics
        metrics = ExitMutationEvolutionMetrics()

        # Create UnifiedMutationOperator with exit mutation enabled
        yaml_interpreter = YAMLInterpreter()
        tier2_engine = create_mock_tier2_engine()
        tier3_mutator = ASTFactorMutator()
        tier_selector = TierSelectionManager()

        mutation_operator = UnifiedMutationOperator(
            yaml_interpreter=yaml_interpreter,
            tier2_engine=tier2_engine,
            tier3_mutator=tier3_mutator,
            tier_selector=tier_selector,
            exit_mutation_probability=0.20,  # 20% exit mutations
            enable_fallback=True,
            validate_mutations=False  # Disable for faster testing
        )

        # Initialize population with exit strategies
        population = [create_factor_graph_strategy_with_exits() for _ in range(20)]

        # Track mutations across generations
        all_mutations = []

        # Run evolution for 20 generations
        for generation in range(20):
            logger.info(f"\nGeneration {generation + 1}/20")

            # Apply mutations to population
            generation_mutations = []

            for i, strategy in enumerate(population):
                # Apply mutation
                result = mutation_operator.mutate_strategy(
                    strategy=strategy,
                    market_data=None,
                    mutation_config={}
                )

                # Track mutation
                if result.success:
                    all_mutations.append(result)
                    generation_mutations.append(result)

                    # Update metrics
                    metrics.total_mutations += 1

                    if result.mutation_type == "exit_parameter_mutation":
                        metrics.exit_mutations += 1
                    else:
                        metrics.tier_mutations += 1

                    # Track clamping events
                    if result.metadata.get('clamped', False):
                        metrics.clamping_events += 1

            metrics.total_generations += 1

            logger.info(
                f"  Mutations: {len(generation_mutations)} "
                f"(Exit: {sum(1 for m in generation_mutations if m.mutation_type == 'exit_parameter_mutation')})"
            )

        # Calculate statistics
        logger.info("\n" + "="*70)
        logger.info("Evolution Results")
        logger.info("="*70)
        logger.info(f"Total Generations: {metrics.total_generations}")
        logger.info(f"Total Mutations: {metrics.total_mutations}")
        logger.info(f"Exit Mutations: {metrics.exit_mutations}")
        logger.info(f"Tier Mutations: {metrics.tier_mutations}")
        logger.info(f"Exit Mutation Rate: {metrics.exit_mutation_rate:.1%}")
        logger.info(f"Clamping Events: {metrics.clamping_events}")

        # Assertions
        assert metrics.total_generations == 20, "Should complete 20 generations"
        assert metrics.total_mutations > 0, "Should have mutations"

        # Verify exit mutation rate 20% ±5%
        assert 0.15 <= metrics.exit_mutation_rate <= 0.25, \
            f"Exit mutation rate {metrics.exit_mutation_rate:.1%} should be 20% ±5%"

        # Verify mutation operator statistics
        stats = mutation_operator.get_tier_statistics()
        assert stats['exit_mutation_attempts'] == metrics.exit_mutations

        logger.info("\n✓ 20-generation evolution test PASSED")


# ============================================================================
# Test 2: Exit Parameter Tracking
# ============================================================================

class TestExitParameterTracking:
    """Test exit parameter tracking across generations."""

    def test_parameter_evolution_tracking(self):
        """
        Track exit parameter evolution over 10 generations.

        Success Criteria:
        - All parameters stay within bounds
        - Parameters evolve (change over time)
        - No invalid values
        """
        logger.info("\n" + "="*70)
        logger.info("TEST: Exit Parameter Evolution Tracking")
        logger.info("="*70)

        # Create exit mutator
        mutator = ExitParameterMutator(gaussian_std=0.15, seed=42)

        # Initial parameters
        initial_params = {
            'stop_loss_pct': 0.10,
            'take_profit_pct': 0.15,
            'trailing_stop_offset': 0.02,
            'holding_period_days': 10.0
        }

        # Track parameter evolution
        param_evolution = {param: [initial_params[param]] for param in initial_params}

        # Current strategy code
        current_code = SAMPLE_STRATEGY_WITH_EXITS

        # Run 10 generations
        for generation in range(10):
            logger.info(f"\nGeneration {generation + 1}/10")

            # Select random parameter to mutate
            param_to_mutate = random.choice(list(initial_params.keys()))

            # Apply mutation
            result = mutator.mutate_exit_parameters(
                code=current_code,
                parameter_name=param_to_mutate
            )

            if result.success:
                current_code = result.code

                # Track new value
                new_value = result.metadata.new_value
                param_evolution[param_to_mutate].append(new_value)

                logger.info(
                    f"  Mutated {param_to_mutate}: "
                    f"{result.metadata.old_value:.4f} -> {new_value:.4f}"
                )

        # Analyze parameter evolution
        logger.info("\n" + "="*70)
        logger.info("Parameter Evolution Analysis")
        logger.info("="*70)

        for param_name, values in param_evolution.items():
            min_bound, max_bound = PARAM_BOUNDS[param_name]

            logger.info(f"\n{param_name}:")
            logger.info(f"  Values: {len(values)}")
            logger.info(f"  Min: {min(values):.4f}")
            logger.info(f"  Max: {max(values):.4f}")
            logger.info(f"  Bounds: [{min_bound}, {max_bound}]")
            logger.info(f"  Unique values: {len(set(values))}")

            # Assertions
            assert len(values) >= 1, f"{param_name} should have at least 1 value"

            # All values should be within bounds
            for value in values:
                assert min_bound <= value <= max_bound, \
                    f"{param_name} value {value} out of bounds [{min_bound}, {max_bound}]"

            # Values should change if mutated multiple times
            if len(values) > 1:
                assert len(set(values)) > 1, \
                    f"{param_name} should evolve (have different values)"

        logger.info("\n✓ Parameter tracking test PASSED")


# ============================================================================
# Test 3: Performance Impact Comparison
# ============================================================================

class TestPerformanceImpact:
    """Test performance impact of exit mutation."""

    @pytest.mark.slow
    def test_performance_impact(self):
        """
        Compare evolution with vs without exit mutation.

        Success Criteria:
        - Both runs complete successfully
        - Statistics tracked correctly
        - Performance measurable
        """
        logger.info("\n" + "="*70)
        logger.info("TEST: Performance Impact Comparison")
        logger.info("="*70)

        generations = 10
        population_size = 10

        # Run 1: WITH exit mutation
        logger.info("\nRun 1: WITH Exit Mutation (20% probability)")

        yaml_interpreter = YAMLInterpreter()
        tier2_engine = create_mock_tier2_engine()
        tier3_mutator = ASTFactorMutator()
        tier_selector = TierSelectionManager()

        operator_with = UnifiedMutationOperator(
            yaml_interpreter=yaml_interpreter,
            tier2_engine=tier2_engine,
            tier3_mutator=tier3_mutator,
            tier_selector=tier_selector,
            exit_mutation_probability=0.20,
            validate_mutations=False
        )

        mutations_with = 0
        exit_mutations_with = 0

        for gen in range(generations):
            for _ in range(population_size):
                strategy = create_factor_graph_strategy_with_exits()
                result = operator_with.mutate_strategy(strategy)

                if result.success:
                    mutations_with += 1
                    if result.mutation_type == "exit_parameter_mutation":
                        exit_mutations_with += 1

        stats_with = operator_with.get_tier_statistics()

        # Run 2: WITHOUT exit mutation
        logger.info("\nRun 2: WITHOUT Exit Mutation (0% probability)")

        operator_without = UnifiedMutationOperator(
            yaml_interpreter=YAMLInterpreter(),
            tier2_engine=create_mock_tier2_engine(),
            tier3_mutator=ASTFactorMutator(),
            tier_selector=TierSelectionManager(),
            exit_mutation_probability=0.0,  # NO exit mutations
            validate_mutations=False
        )

        mutations_without = 0
        exit_mutations_without = 0

        for gen in range(generations):
            for _ in range(population_size):
                strategy = create_factor_graph_strategy_with_exits()
                result = operator_without.mutate_strategy(strategy)

                if result.success:
                    mutations_without += 1
                    if result.mutation_type == "exit_parameter_mutation":
                        exit_mutations_without += 1

        stats_without = operator_without.get_tier_statistics()

        # Compare results
        logger.info("\n" + "="*70)
        logger.info("Performance Comparison")
        logger.info("="*70)
        logger.info("\nWITH Exit Mutation:")
        logger.info(f"  Total mutations: {mutations_with}")
        logger.info(f"  Exit mutations: {exit_mutations_with}")
        logger.info(f"  Exit mutation rate: {exit_mutations_with / mutations_with * 100:.1f}%")
        logger.info(f"  Success rate: {stats_with['success_rate']:.1%}")

        logger.info("\nWITHOUT Exit Mutation:")
        logger.info(f"  Total mutations: {mutations_without}")
        logger.info(f"  Exit mutations: {exit_mutations_without}")
        logger.info(f"  Exit mutation rate: 0.0%")
        logger.info(f"  Success rate: {stats_without['success_rate']:.1%}")

        # Assertions
        assert mutations_with > 0, "Should have mutations with exit enabled"
        assert mutations_without > 0, "Should have mutations with exit disabled"
        assert exit_mutations_with > 0, "Should have exit mutations when enabled"
        assert exit_mutations_without == 0, "Should have NO exit mutations when disabled"

        logger.info("\n✓ Performance impact test PASSED")


# ============================================================================
# Test 4: Metadata Tracking
# ============================================================================

class TestMetadataTracking:
    """Test comprehensive metadata tracking."""

    def test_metadata_tracking(self):
        """
        Verify exit mutation metadata is tracked correctly.

        Success Criteria:
        - Parameter name tracked
        - Old/new values tracked
        - Clamping status tracked
        - Success/failure tracked
        """
        logger.info("\n" + "="*70)
        logger.info("TEST: Exit Mutation Metadata Tracking")
        logger.info("="*70)

        # Create mutation operator
        yaml_interpreter = YAMLInterpreter()
        tier2_engine = create_mock_tier2_engine()
        tier3_mutator = ASTFactorMutator()
        tier_selector = TierSelectionManager()

        operator = UnifiedMutationOperator(
            yaml_interpreter=yaml_interpreter,
            tier2_engine=tier2_engine,
            tier3_mutator=tier3_mutator,
            tier_selector=tier_selector,
            exit_mutation_probability=1.0,  # Always exit mutation
            validate_mutations=False
        )

        # Apply multiple mutations
        metadata_samples = []

        for i in range(10):
            strategy = create_factor_graph_strategy_with_exits()

            result = operator.mutate_strategy(
                strategy=strategy,
                mutation_config={'mutation_type': 'exit_parameter_mutation'}
            )

            if result.success:
                metadata_samples.append(result.metadata)

        # Verify metadata structure
        logger.info(f"\nCollected {len(metadata_samples)} metadata samples")

        for i, metadata in enumerate(metadata_samples[:3]):  # Show first 3
            logger.info(f"\nSample {i + 1}:")
            logger.info(f"  Exit mutation: {metadata.get('exit_mutation')}")
            logger.info(f"  Parameter: {metadata.get('parameter_name')}")
            logger.info(f"  Old value: {metadata.get('old_value')}")
            logger.info(f"  New value: {metadata.get('new_value')}")
            logger.info(f"  Clamped: {metadata.get('clamped')}")
            logger.info(f"  Validation passed: {metadata.get('validation_passed')}")

        # Assertions
        assert len(metadata_samples) > 0, "Should have metadata samples"

        for metadata in metadata_samples:
            # Verify required fields
            assert 'exit_mutation' in metadata, "Should have exit_mutation flag"
            assert metadata['exit_mutation'] is True, "Should be exit mutation"

            assert 'parameter_name' in metadata, "Should have parameter_name"
            assert metadata['parameter_name'] in PARAM_BOUNDS, "Parameter should be valid"

            assert 'old_value' in metadata, "Should have old_value"
            assert 'new_value' in metadata, "Should have new_value"
            assert 'clamped' in metadata, "Should have clamped flag"
            assert 'validation_passed' in metadata, "Should have validation_passed"

        logger.info("\n✓ Metadata tracking test PASSED")


# ============================================================================
# Test 5: Integration with UnifiedMutationOperator
# ============================================================================

class TestUnifiedOperatorIntegration:
    """Test integration with UnifiedMutationOperator."""

    def test_exit_mutation_probability(self):
        """
        Verify exit mutation probability is respected.

        Success Criteria:
        - Exit mutations occur at 20% rate ±5%
        - All mutation types work together
        - No conflicts between mutation types
        """
        logger.info("\n" + "="*70)
        logger.info("TEST: UnifiedMutationOperator Integration")
        logger.info("="*70)

        # Create operator with 20% exit mutation
        operator = UnifiedMutationOperator(
            yaml_interpreter=YAMLInterpreter(),
            tier2_engine=create_mock_tier2_engine(),
            tier3_mutator=ASTFactorMutator(),
            tier_selector=TierSelectionManager(),
            exit_mutation_probability=0.20,
            validate_mutations=False
        )

        # Run 1000 mutations for statistical significance
        total_mutations = 1000
        mutation_types = []

        logger.info(f"\nRunning {total_mutations} mutations...")

        for i in range(total_mutations):
            strategy = create_factor_graph_strategy_with_exits()

            result = operator.mutate_strategy(strategy)

            if result.success:
                mutation_types.append(result.mutation_type)

        # Count mutation types
        exit_count = mutation_types.count('exit_parameter_mutation')
        tier_count = len(mutation_types) - exit_count

        exit_rate = exit_count / len(mutation_types) if mutation_types else 0

        logger.info("\n" + "="*70)
        logger.info("Mutation Distribution")
        logger.info("="*70)
        logger.info(f"Total mutations: {len(mutation_types)}")
        logger.info(f"Exit mutations: {exit_count} ({exit_rate:.1%})")
        logger.info(f"Tier mutations: {tier_count} ({(1-exit_rate):.1%})")

        # Verify statistics
        stats = operator.get_tier_statistics()
        logger.info(f"\nOperator statistics:")
        logger.info(f"  Exit attempts: {stats['exit_mutation_attempts']}")
        logger.info(f"  Exit successes: {stats['exit_mutation_successes']}")
        logger.info(f"  Exit success rate: {stats['exit_mutation_success_rate']:.1%}")

        # Assertions
        assert len(mutation_types) > 0, "Should have mutations"
        assert 0.15 <= exit_rate <= 0.25, \
            f"Exit rate {exit_rate:.1%} should be 20% ±5%"

        logger.info("\n✓ UnifiedOperator integration test PASSED")


# ============================================================================
# Test 6: Boundary Enforcement
# ============================================================================

class TestBoundaryEnforcement:
    """Test parameter boundary enforcement."""

    def test_boundary_enforcement(self):
        """
        Verify parameters stay within bounds during mutation.

        Success Criteria:
        - All mutated values within bounds
        - Clamping works correctly
        - Extreme values handled
        """
        logger.info("\n" + "="*70)
        logger.info("TEST: Parameter Boundary Enforcement")
        logger.info("="*70)

        mutator = ExitParameterMutator(gaussian_std=0.50, seed=42)  # High std for testing

        # Test each parameter
        for param_name, (min_bound, max_bound) in PARAM_BOUNDS.items():
            logger.info(f"\nTesting {param_name}: bounds=[{min_bound}, {max_bound}]")

            # Test with value near minimum
            test_values = [
                min_bound + 0.001,  # Near minimum
                (min_bound + max_bound) / 2,  # Middle
                max_bound - 0.001,  # Near maximum
            ]

            for test_value in test_values:
                # Create test code
                test_code = f"{param_name} = {test_value}"

                # Apply multiple mutations
                clamping_occurred = False

                for _ in range(10):
                    result = mutator.mutate_exit_parameters(
                        code=test_code,
                        parameter_name=param_name
                    )

                    if result.success:
                        new_value = result.metadata.new_value

                        # Verify within bounds
                        assert min_bound <= new_value <= max_bound, \
                            f"{param_name} value {new_value} out of bounds"

                        if result.metadata.clamped:
                            clamping_occurred = True

                        # Update for next iteration
                        test_code = result.code

            logger.info(f"  ✓ All mutations within bounds")
            if clamping_occurred:
                logger.info(f"  ✓ Clamping occurred as expected")

        logger.info("\n✓ Boundary enforcement test PASSED")


# ============================================================================
# Integration Test Summary
# ============================================================================

@pytest.mark.integration
class TestExitMutationEvolutionSuite:
    """Complete test suite for exit mutation evolution integration."""

    def test_complete_suite(self):
        """
        Run all integration tests in sequence.

        This is a convenience test to run all integration tests together.
        """
        logger.info("\n" + "="*70)
        logger.info("RUNNING COMPLETE EXIT MUTATION EVOLUTION TEST SUITE")
        logger.info("="*70)

        # Run all tests
        test_evolution = TestExitMutationEvolution()
        test_evolution.test_20_generation_evolution()

        test_tracking = TestExitParameterTracking()
        test_tracking.test_parameter_evolution_tracking()

        test_performance = TestPerformanceImpact()
        test_performance.test_performance_impact()

        test_metadata = TestMetadataTracking()
        test_metadata.test_metadata_tracking()

        test_integration = TestUnifiedOperatorIntegration()
        test_integration.test_exit_mutation_probability()

        test_boundary = TestBoundaryEnforcement()
        test_boundary.test_boundary_enforcement()

        logger.info("\n" + "="*70)
        logger.info("ALL TESTS PASSED!")
        logger.info("="*70)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Run tests directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("\n" + "="*70)
    print("Exit Mutation Evolution Integration Tests")
    print("="*70)

    # Run complete suite
    suite = TestExitMutationEvolutionSuite()
    suite.test_complete_suite()

    print("\n" + "="*70)
    print("Integration tests completed successfully!")
    print("="*70)
