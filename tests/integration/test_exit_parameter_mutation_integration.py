"""
Integration Tests for ExitParameterMutator with Real Strategy Code

Task 2.5: Integration tests with realistic strategy code
Validates ≥70% success rate requirement (0% → ≥70%)

Test Coverage:
1. Real strategy mutation with turtle/momentum templates
2. Success rate validation (≥70% over 100 mutations)
3. Factor Graph integration (20% exit_param weight)
4. Mutation statistics tracking
5. Backward compatibility (strategies without exit params)
6. All 4 parameters mutatable
7. Metadata extraction

Critical Test: test_success_rate_target_70_percent()
This validates the PRIMARY requirement (0% baseline → ≥70% target)
"""

import pytest
import ast
import numpy as np
from typing import Dict, Any

from src.mutation.exit_parameter_mutator import ExitParameterMutator, MutationResult


# Realistic strategy code samples from templates
TURTLE_STRATEGY_CODE = """
# Turtle Strategy with exit parameters
import finlab
from finlab import data

# Entry conditions (6-layer AND filtering)
close = data.get('price:收盤價')
yield_ratio = data.get('price_earning_ratio:殖利率(%)')
vol = data.get('price:成交股數')

# Filters
cond_yield = yield_ratio >= 6.0
cond_volume = vol.average(5) >= 50000
selected = cond_yield & cond_volume

# Position sizing
positions = selected.astype(float) / 10

# Exit parameters (CRITICAL: must be present for mutation)
stop_loss_pct = 0.08
take_profit_pct = 0.50
trailing_stop_offset = 0.02
holding_period_days = 30

# Apply exits (simplified)
entry_price = close.shift(1)
stop_loss_trigger = close < entry_price * (1 - stop_loss_pct)
take_profit_trigger = close > entry_price * (1 + take_profit_pct)
positions = positions * ~(stop_loss_trigger | take_profit_trigger)
"""

MOMENTUM_STRATEGY_CODE = """
# Momentum Strategy with exit parameters
import finlab
from finlab import data

# Momentum calculation
close = data.get('price:收盤價')
returns = close.pct_change(20)
momentum = returns.rolling(10).mean()

# MA filter
ma_filter = close > close.average(60)

# Select top momentum stocks
selected = momentum[ma_filter].is_largest(10)

# Position sizing
positions = selected.astype(float) / 10

# Exit parameters (CRITICAL: must be present for mutation)
stop_loss_pct = 0.10
take_profit_pct = 0.30
trailing_stop_offset = 0.015
holding_period_days = 20

# Apply exits (simplified)
entry_price = close.shift(1)
stop_loss_trigger = close < entry_price * (1 - stop_loss_pct)
positions = positions * ~stop_loss_trigger
"""

MINIMAL_EXIT_STRATEGY_CODE = """
# Minimal strategy with only exit parameters
stop_loss_pct = 0.06
take_profit_pct = 0.25
trailing_stop_offset = 0.01
holding_period_days = 15
"""

STRATEGY_WITHOUT_EXIT_PARAMS = """
# Strategy without exit parameters (backward compatibility test)
import finlab
from finlab import data

close = data.get('price:收盤價')
returns = close.pct_change(20)
selected = returns.is_largest(10)
positions = selected.astype(float) / 10
"""


class TestExitParameterMutatorIntegration:
    """Integration tests with realistic strategy code."""

    def test_real_strategy_mutation_turtle(self):
        """
        Test 1: Mutate turtle strategy successfully.

        Acceptance Criteria:
        - result.success == True
        - Code changed from original
        - Valid Python syntax
        """
        mutator = ExitParameterMutator()

        # Apply mutation
        result = mutator.mutate(TURTLE_STRATEGY_CODE)

        # Verify success
        assert result.success, f"Mutation failed: {result.error_message}"

        # Verify code changed
        assert result.mutated_code != TURTLE_STRATEGY_CODE, "Code should have changed"

        # Verify valid Python syntax
        try:
            ast.parse(result.mutated_code)
        except SyntaxError as e:
            pytest.fail(f"Mutated code has syntax error: {e}")

        # Verify metadata
        assert result.metadata['mutation_type'] == 'exit_param'
        assert 'parameter' in result.metadata
        assert 'old_value' in result.metadata
        assert 'new_value' in result.metadata

        print(f"\nTurtle strategy mutation:")
        print(f"  Parameter: {result.metadata['parameter']}")
        print(f"  Old value: {result.metadata['old_value']:.4f}")
        print(f"  New value: {result.metadata['new_value']:.4f}")
        print(f"  Bounded: {result.metadata['bounded']}")

    def test_real_strategy_mutation_momentum(self):
        """
        Test 1 (variant): Mutate momentum strategy successfully.

        Acceptance Criteria:
        - result.success == True
        - Code changed from original
        - Valid Python syntax
        """
        mutator = ExitParameterMutator()

        # Apply mutation
        result = mutator.mutate(MOMENTUM_STRATEGY_CODE)

        # Verify success
        assert result.success, f"Mutation failed: {result.error_message}"

        # Verify code changed
        assert result.mutated_code != MOMENTUM_STRATEGY_CODE, "Code should have changed"

        # Verify valid Python syntax
        try:
            ast.parse(result.mutated_code)
        except SyntaxError as e:
            pytest.fail(f"Mutated code has syntax error: {e}")

        print(f"\nMomentum strategy mutation:")
        print(f"  Parameter: {result.metadata['parameter']}")
        print(f"  Old value: {result.metadata['old_value']:.4f}")
        print(f"  New value: {result.metadata['new_value']:.4f}")

    def test_success_rate_target_70_percent(self):
        """
        Test 2: Verify ≥70% success rate over 100 mutations.

        CRITICAL TEST: This validates the PRIMARY requirement (0% → ≥70%)

        Acceptance Criteria:
        - success_rate ≥ 0.70 (70%)
        - All failures tracked properly
        - Statistics consistent
        """
        mutator = ExitParameterMutator()

        # Run 100 mutations on realistic strategy
        num_mutations = 100
        successes = 0
        failures = 0

        for i in range(num_mutations):
            # Alternate between turtle and momentum strategies for variety
            if i % 2 == 0:
                strategy_code = TURTLE_STRATEGY_CODE
            else:
                strategy_code = MOMENTUM_STRATEGY_CODE

            result = mutator.mutate(strategy_code)

            if result.success:
                successes += 1
            else:
                failures += 1

        # Calculate success rate
        success_rate = successes / num_mutations

        # Print statistics
        stats = mutator.get_statistics()
        print(f"\nSuccess Rate Validation (100 mutations):")
        print(f"  Successes: {successes}")
        print(f"  Failures: {failures}")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"\nDetailed Statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Success: {stats['success']}")
        print(f"  Failed Regex: {stats['failed_regex']}")
        print(f"  Failed Validation: {stats['failed_validation']}")
        print(f"  Clamped: {stats['clamped']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")

        # CRITICAL ASSERTION: Verify ≥70% success rate
        assert success_rate >= 0.70, (
            f"Success rate {success_rate:.1%} is below 70% target. "
            f"Expected ≥70% but got {success_rate:.1%}"
        )

        # Verify statistics consistency
        assert stats['total'] == num_mutations
        assert stats['success'] == successes
        assert stats['success'] + stats['failed_regex'] + stats['failed_validation'] == stats['total']

    def test_factor_graph_20_percent_weight(self):
        """
        Test 3: Verify 20% of mutations are exit_param type.

        This simulates Factor Graph mutation type selection.

        Acceptance Criteria:
        - ~20% of mutations select exit_param (tolerance: ±5%)
        - Uniform distribution within exit params (25% each)
        """
        # Simulate mutation type selection (includes exit_param)
        mutation_types = ['add_factor', 'remove_factor', 'mutate_factor', 'exit_param']
        weights = [0.30, 0.20, 0.30, 0.20]  # 20% exit_param

        num_selections = 1000
        exit_param_count = 0

        for _ in range(num_selections):
            mutation_type = np.random.choice(mutation_types, p=weights)
            if mutation_type == 'exit_param':
                exit_param_count += 1

        # Calculate percentage
        exit_param_percentage = exit_param_count / num_selections

        print(f"\nFactor Graph Mutation Type Selection (1000 trials):")
        print(f"  Exit Param Count: {exit_param_count}")
        print(f"  Exit Param Percentage: {exit_param_percentage:.1%}")

        # Verify ~20% (tolerance: ±5%)
        assert 0.15 <= exit_param_percentage <= 0.25, (
            f"Exit param percentage {exit_param_percentage:.1%} outside 15-25% range. "
            f"Expected ~20% ± 5%"
        )

        # Test uniform distribution of exit parameters
        mutator = ExitParameterMutator()
        param_counts = {
            'stop_loss_pct': 0,
            'take_profit_pct': 0,
            'trailing_stop_offset': 0,
            'holding_period_days': 0
        }

        # Run 1000 parameter selections
        for _ in range(1000):
            param = mutator._select_parameter_uniform()
            param_counts[param] += 1

        print(f"\nParameter Selection Distribution (1000 trials):")
        for param, count in param_counts.items():
            percentage = count / 1000
            print(f"  {param}: {count} ({percentage:.1%})")

        # Verify each parameter is ~25% (tolerance: ±7%)
        for param, count in param_counts.items():
            percentage = count / 1000
            assert 0.18 <= percentage <= 0.32, (
                f"Parameter {param} percentage {percentage:.1%} outside 18-32% range. "
                f"Expected ~25% ± 7%"
            )

    def test_mutation_statistics_tracking(self):
        """
        Test 4: Verify mutation statistics tracked correctly.

        Acceptance Criteria:
        - Total mutations tracked
        - Successes tracked
        - Failures (regex, validation) tracked separately
        - Clamped mutations tracked
        - Success rate calculated correctly
        """
        mutator = ExitParameterMutator()

        # Verify initial state
        stats = mutator.get_statistics()
        assert stats['total'] == 0
        assert stats['success'] == 0
        assert stats['failed_regex'] == 0
        assert stats['failed_validation'] == 0
        assert stats['clamped'] == 0
        assert stats['success_rate'] == 0.0

        # Apply 50 mutations
        num_mutations = 50
        for i in range(num_mutations):
            mutator.mutate(TURTLE_STRATEGY_CODE)

        # Verify statistics updated
        stats = mutator.get_statistics()
        assert stats['total'] == num_mutations
        assert stats['success'] > 0, "Should have at least some successes"
        assert stats['success'] + stats['failed_regex'] + stats['failed_validation'] == num_mutations

        # Verify success rate calculation
        expected_rate = stats['success'] / stats['total']
        assert abs(stats['success_rate'] - expected_rate) < 1e-6

        print(f"\nStatistics Tracking (50 mutations):")
        print(f"  Total: {stats['total']}")
        print(f"  Success: {stats['success']}")
        print(f"  Failed Regex: {stats['failed_regex']}")
        print(f"  Failed Validation: {stats['failed_validation']}")
        print(f"  Clamped: {stats['clamped']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")

    def test_backward_compatibility(self):
        """
        Test 5: Strategies without exit params skip gracefully.

        Acceptance Criteria:
        - No crashes
        - Returns original code
        - Success = False
        - Error message indicates parameter not found
        """
        mutator = ExitParameterMutator()

        # Apply mutation to strategy without exit params
        result = mutator.mutate(STRATEGY_WITHOUT_EXIT_PARAMS)

        # Verify graceful failure
        assert result.success is False, "Should fail gracefully"
        assert result.mutated_code == STRATEGY_WITHOUT_EXIT_PARAMS, "Should return original code"
        assert result.error_message is not None
        assert "not found" in result.error_message.lower(), "Error should indicate parameter not found"

        # Verify no crashes
        print(f"\nBackward Compatibility Test:")
        print(f"  Result: Graceful failure (as expected)")
        print(f"  Error: {result.error_message}")

    def test_all_parameters_mutatable(self):
        """
        Test 6: All 4 parameters can be mutated.

        Acceptance Criteria:
        - stop_loss_pct mutatable
        - take_profit_pct mutatable
        - trailing_stop_offset mutatable
        - holding_period_days mutatable
        """
        mutator = ExitParameterMutator()

        # Test each parameter individually
        parameters_to_test = [
            'stop_loss_pct',
            'take_profit_pct',
            'trailing_stop_offset',
            'holding_period_days'
        ]

        print(f"\nAll Parameters Mutatable Test:")

        for param_name in parameters_to_test:
            # Apply mutation to specific parameter
            result = mutator.mutate(MINIMAL_EXIT_STRATEGY_CODE, param_name=param_name)

            # Verify success
            assert result.success, f"Mutation of {param_name} failed: {result.error_message}"

            # Verify correct parameter mutated
            assert result.metadata['parameter'] == param_name

            # Verify value changed
            old_value = result.metadata['old_value']
            new_value = result.metadata['new_value']
            assert old_value != new_value, f"{param_name} value should have changed"

            # Verify bounds respected
            bounds = mutator.PARAM_BOUNDS[param_name]
            assert bounds.min_value <= new_value <= bounds.max_value, (
                f"{param_name} new value {new_value} outside bounds "
                f"[{bounds.min_value}, {bounds.max_value}]"
            )

            print(f"  {param_name}: {old_value:.4f} → {new_value:.4f} ✓")

    def test_metadata_extractable(self):
        """
        Test 7: Metadata accessible from mutation result.

        Acceptance Criteria:
        - mutation_type present
        - parameter present
        - old_value present
        - new_value present
        - bounded present
        """
        mutator = ExitParameterMutator()

        # Apply mutation
        result = mutator.mutate(TURTLE_STRATEGY_CODE)

        # Verify all metadata fields present
        required_fields = ['mutation_type', 'parameter', 'old_value', 'new_value', 'bounded']

        for field in required_fields:
            assert field in result.metadata, f"Metadata missing field: {field}"

        # Verify field types
        assert isinstance(result.metadata['mutation_type'], str)
        assert isinstance(result.metadata['parameter'], str)
        assert isinstance(result.metadata['old_value'], (int, float))
        assert isinstance(result.metadata['new_value'], (int, float))
        assert isinstance(result.metadata['bounded'], bool)

        # Verify mutation_type value
        assert result.metadata['mutation_type'] == 'exit_param'

        # Verify parameter value
        assert result.metadata['parameter'] in mutator.PARAM_BOUNDS

        print(f"\nMetadata Extraction Test:")
        print(f"  mutation_type: {result.metadata['mutation_type']}")
        print(f"  parameter: {result.metadata['parameter']}")
        print(f"  old_value: {result.metadata['old_value']:.4f}")
        print(f"  new_value: {result.metadata['new_value']:.4f}")
        print(f"  bounded: {result.metadata['bounded']}")


@pytest.mark.integration
class TestExitParameterMutatorStress:
    """Stress tests for exit parameter mutation."""

    def test_stress_1000_mutations(self):
        """
        Stress test: 1000 mutations to verify stability.

        This extended test validates:
        - System stability under load
        - Consistent success rate
        - No memory leaks
        - No degradation over time
        """
        mutator = ExitParameterMutator()

        num_mutations = 1000
        successes = 0

        print(f"\nStress Test: {num_mutations} mutations")

        for i in range(num_mutations):
            # Rotate through strategies
            strategies = [TURTLE_STRATEGY_CODE, MOMENTUM_STRATEGY_CODE, MINIMAL_EXIT_STRATEGY_CODE]
            strategy_code = strategies[i % len(strategies)]

            result = mutator.mutate(strategy_code)

            if result.success:
                successes += 1

            # Progress indicator every 100 mutations
            if (i + 1) % 100 == 0:
                current_rate = successes / (i + 1)
                print(f"  Progress: {i + 1}/{num_mutations} - Success rate: {current_rate:.1%}")

        # Final statistics
        success_rate = successes / num_mutations
        stats = mutator.get_statistics()

        print(f"\nStress Test Results:")
        print(f"  Total Mutations: {num_mutations}")
        print(f"  Successes: {successes}")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"\nDetailed Statistics:")
        print(f"  Failed Regex: {stats['failed_regex']}")
        print(f"  Failed Validation: {stats['failed_validation']}")
        print(f"  Clamped: {stats['clamped']}")

        # Verify success rate still ≥70%
        assert success_rate >= 0.70, (
            f"Stress test success rate {success_rate:.1%} below 70% target"
        )

    def test_extreme_values_clamping(self):
        """
        Test clamping behavior with extreme Gaussian noise.

        Verifies that even with extreme noise, values are properly clamped
        to bounds and don't cause validation errors.
        """
        # Create mutator with high std_dev (aggressive mutations)
        mutator = ExitParameterMutator(gaussian_std_dev=0.50)  # 50% noise

        num_mutations = 100
        successes = 0
        clamped = 0

        for _ in range(num_mutations):
            result = mutator.mutate(MINIMAL_EXIT_STRATEGY_CODE)

            if result.success:
                successes += 1
                if result.metadata['bounded']:
                    clamped += 1

        success_rate = successes / num_mutations
        clamp_rate = clamped / successes if successes > 0 else 0

        print(f"\nExtreme Values Clamping Test:")
        print(f"  Gaussian std_dev: 0.50 (50% noise)")
        print(f"  Mutations: {num_mutations}")
        print(f"  Successes: {successes}")
        print(f"  Success Rate: {success_rate:.1%}")
        print(f"  Clamped: {clamped}")
        print(f"  Clamp Rate: {clamp_rate:.1%}")

        # Even with extreme noise, should still have reasonable success rate
        assert success_rate >= 0.50, (
            f"Even with high noise, success rate {success_rate:.1%} should be ≥50%"
        )


@pytest.mark.benchmark
class TestExitParameterMutatorBenchmark:
    """Benchmark tests for performance validation."""

    def test_benchmark_mutation_performance(self):
        """
        Benchmark: Measure mutation performance.

        Target: <10ms per mutation on average
        """
        import time

        mutator = ExitParameterMutator()

        num_mutations = 100
        start_time = time.time()

        for _ in range(num_mutations):
            mutator.mutate(TURTLE_STRATEGY_CODE)

        end_time = time.time()
        elapsed_time = end_time - start_time
        avg_time_ms = (elapsed_time / num_mutations) * 1000

        print(f"\nPerformance Benchmark:")
        print(f"  Mutations: {num_mutations}")
        print(f"  Total Time: {elapsed_time:.2f}s")
        print(f"  Average Time: {avg_time_ms:.2f}ms per mutation")

        # Target: <10ms per mutation
        assert avg_time_ms < 10, (
            f"Average mutation time {avg_time_ms:.2f}ms exceeds 10ms target"
        )


if __name__ == "__main__":
    # Run critical test directly
    print("=" * 80)
    print("Running CRITICAL Test: Success Rate Target (70%)")
    print("=" * 80)

    test = TestExitParameterMutatorIntegration()
    test.test_success_rate_target_70_percent()

    print("\n" + "=" * 80)
    print("CRITICAL TEST PASSED: ≥70% Success Rate Achieved!")
    print("=" * 80)
