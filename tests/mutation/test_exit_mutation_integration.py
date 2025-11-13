"""
Integration Tests for Exit Mutation in UnifiedMutationOperator
================================================================

Tests the integration of ExitParameterMutator into the UnifiedMutationOperator,
validating:
- Exit mutation is selectable with 20% probability
- Metadata is correctly tracked
- Existing tier mutations remain unaffected (backward compatibility)
- Exit mutations work with real strategy code

Spec: exit-mutation-redesign
Task: 3 - Integrate ExitParameterMutator into Factor Graph
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any

from src.mutation.unified_mutation_operator import UnifiedMutationOperator, MutationResult
from src.mutation.exit_parameter_mutator import ExitParameterMutator
from src.tier1.yaml_interpreter import YAMLInterpreter
from src.mutation.tier2.smart_mutation_engine import SmartMutationEngine
from src.mutation.tier3.ast_factor_mutator import ASTFactorMutator
from src.mutation.tier_selection.tier_selection_manager import TierSelectionManager
from src.factor_graph.strategy import Strategy


# Test strategy code with exit parameters
STRATEGY_CODE_WITH_EXIT = """
def trading_strategy(data):
    # Entry logic
    signal = data['close'] > data['ma_20']

    # Exit parameters
    stop_loss_pct = 0.10
    take_profit_pct = 0.20
    trailing_stop_offset = 0.025
    holding_period_days = 10

    # Apply exits
    positions = apply_exits(signal, stop_loss_pct, take_profit_pct,
                           trailing_stop_offset, holding_period_days)
    return positions
"""

STRATEGY_CODE_WITHOUT_EXIT = """
def trading_strategy(data):
    # Simple strategy without exit parameters
    signal = data['close'] > data['ma_20']
    return signal
"""


@pytest.fixture
def mock_yaml_interpreter():
    """Create mock YAML interpreter."""
    return Mock(spec=YAMLInterpreter)


@pytest.fixture
def mock_tier2_engine():
    """Create mock tier 2 engine."""
    return Mock(spec=SmartMutationEngine)


@pytest.fixture
def mock_tier3_mutator():
    """Create mock tier 3 mutator."""
    return Mock(spec=ASTFactorMutator)


@pytest.fixture
def mock_tier_selector():
    """Create mock tier selector."""
    selector = Mock(spec=TierSelectionManager)

    # Create mock mutation plan
    mock_plan = Mock()
    mock_plan.tier = Mock()
    mock_plan.tier.value = 2  # Default to tier 2

    selector.select_mutation_tier.return_value = mock_plan
    selector.record_mutation_result = Mock()
    selector.reset_learning = Mock()

    return selector


@pytest.fixture
def mock_strategy():
    """Create mock strategy with exit parameters."""
    strategy = Mock(spec=Strategy)
    strategy.code = STRATEGY_CODE_WITH_EXIT
    strategy.to_code = Mock(return_value=STRATEGY_CODE_WITH_EXIT)
    strategy.copy = Mock(return_value=strategy)
    strategy.validate = Mock()
    strategy.update_code = Mock()
    return strategy


@pytest.fixture
def mock_strategy_without_exit():
    """Create mock strategy without exit parameters."""
    strategy = Mock(spec=Strategy)
    strategy.code = STRATEGY_CODE_WITHOUT_EXIT
    strategy.to_code = Mock(return_value=STRATEGY_CODE_WITHOUT_EXIT)
    strategy.copy = Mock(return_value=strategy)
    strategy.validate = Mock()
    return strategy


@pytest.fixture
def unified_operator(mock_yaml_interpreter, mock_tier2_engine,
                     mock_tier3_mutator, mock_tier_selector):
    """Create UnifiedMutationOperator with mocked components."""
    return UnifiedMutationOperator(
        yaml_interpreter=mock_yaml_interpreter,
        tier2_engine=mock_tier2_engine,
        tier3_mutator=mock_tier3_mutator,
        tier_selector=mock_tier_selector,
        exit_mutation_probability=0.20,
        validate_mutations=False  # Disable validation for unit tests
    )


class TestExitMutationIntegration:
    """Test suite for exit mutation integration."""

    def test_initialization_with_exit_mutator(
        self, mock_yaml_interpreter, mock_tier2_engine,
        mock_tier3_mutator, mock_tier_selector
    ):
        """Test that UnifiedMutationOperator initializes with exit mutator."""
        operator = UnifiedMutationOperator(
            yaml_interpreter=mock_yaml_interpreter,
            tier2_engine=mock_tier2_engine,
            tier3_mutator=mock_tier3_mutator,
            tier_selector=mock_tier_selector,
            exit_mutation_probability=0.20
        )

        # Verify exit mutator is initialized
        assert operator.exit_mutator is not None
        assert isinstance(operator.exit_mutator, ExitParameterMutator)
        assert operator.exit_mutation_probability == 0.20

        # Verify statistics tracking is initialized
        assert operator._exit_mutation_attempts == 0
        assert operator._exit_mutation_successes == 0
        assert operator._exit_mutation_failures == 0

    def test_custom_exit_mutator_initialization(
        self, mock_yaml_interpreter, mock_tier2_engine,
        mock_tier3_mutator, mock_tier_selector
    ):
        """Test initialization with custom exit mutator."""
        custom_mutator = ExitParameterMutator(gaussian_std=0.25)

        operator = UnifiedMutationOperator(
            yaml_interpreter=mock_yaml_interpreter,
            tier2_engine=mock_tier2_engine,
            tier3_mutator=mock_tier3_mutator,
            tier_selector=mock_tier_selector,
            exit_mutator=custom_mutator,
            exit_mutation_probability=0.30
        )

        # Verify custom mutator is used
        assert operator.exit_mutator is custom_mutator
        assert operator.exit_mutation_probability == 0.30

    def test_forced_exit_mutation(self, unified_operator, mock_strategy):
        """Test forcing exit mutation via config."""
        # Force exit mutation
        config = {
            "mutation_type": "exit_parameter_mutation",
            "exit_config": {"parameter_name": "stop_loss_pct"}
        }

        result = unified_operator.mutate_strategy(
            strategy=mock_strategy,
            mutation_config=config
        )

        # Verify exit mutation was applied
        assert result.mutation_type == "exit_parameter_mutation"
        assert result.tier_used == 0  # Exit mutation uses tier 0
        assert result.metadata.get('exit_mutation') is True
        assert 'parameter_name' in result.metadata

        # Verify statistics
        assert unified_operator._exit_mutation_attempts == 1

    def test_exit_mutation_probability(self, unified_operator, mock_strategy):
        """Test that exit mutations occur at ~20% probability."""
        # Run many mutations and count exit mutations
        num_iterations = 1000
        exit_mutation_count = 0

        for _ in range(num_iterations):
            result = unified_operator.mutate_strategy(
                strategy=mock_strategy,
                mutation_config={}
            )

            if result.mutation_type == "exit_parameter_mutation":
                exit_mutation_count += 1

        # Verify exit mutation probability is approximately 20%
        # Allow 5% tolerance (15%-25% range)
        exit_mutation_rate = exit_mutation_count / num_iterations
        assert 0.15 <= exit_mutation_rate <= 0.25, \
            f"Exit mutation rate {exit_mutation_rate:.2%} outside expected range [15%, 25%]"

    def test_exit_mutation_metadata_tracking(self, unified_operator, mock_strategy):
        """Test that exit mutation metadata is correctly tracked."""
        config = {
            "mutation_type": "exit_parameter_mutation",
            "exit_config": {"parameter_name": "stop_loss_pct"}
        }

        result = unified_operator.mutate_strategy(
            strategy=mock_strategy,
            mutation_config=config
        )

        # Verify metadata contains all required fields
        assert result.metadata['exit_mutation'] is True
        assert 'parameter_name' in result.metadata
        assert 'old_value' in result.metadata
        assert 'new_value' in result.metadata
        assert 'clamped' in result.metadata
        assert 'validation_passed' in result.metadata

        # Verify parameter was mutated
        if result.success:
            assert result.metadata['parameter_name'] == 'stop_loss_pct'
            assert isinstance(result.metadata['old_value'], float)
            assert isinstance(result.metadata['new_value'], float)

    def test_exit_mutation_success_tracking(self, unified_operator, mock_strategy):
        """Test that successful exit mutations are tracked."""
        config = {"mutation_type": "exit_parameter_mutation"}

        # Apply multiple exit mutations
        for _ in range(10):
            result = unified_operator.mutate_strategy(
                strategy=mock_strategy,
                mutation_config=config
            )

        # Verify statistics
        stats = unified_operator.get_tier_statistics()
        assert stats['exit_mutation_attempts'] == 10
        assert stats['exit_mutation_successes'] > 0
        assert stats['exit_mutation_success_rate'] > 0

    def test_exit_mutation_graceful_failure(
        self, unified_operator, mock_strategy_without_exit
    ):
        """Test that exit mutation fails gracefully when no exit parameters exist."""
        config = {"mutation_type": "exit_parameter_mutation"}

        result = unified_operator.mutate_strategy(
            strategy=mock_strategy_without_exit,
            mutation_config=config
        )

        # Verify mutation failed gracefully
        assert result.success is False
        assert result.mutation_type == "exit_parameter_mutation"
        assert result.error is not None
        assert unified_operator._exit_mutation_failures == 1

    def test_backward_compatibility_tier2_mutations(
        self, unified_operator, mock_strategy, mock_tier2_engine
    ):
        """Test that tier 2 mutations still work after exit mutation integration."""
        # Mock tier 2 mutation
        mock_tier2_engine.select_operator.return_value = (
            "add_factor",
            Mock(mutate=Mock(return_value=mock_strategy))
        )

        # Force tier 2 mutation (no exit mutation)
        with patch('random.random', return_value=0.99):  # Avoid exit mutation
            config = {"intent": "add_factor"}
            result = unified_operator.mutate_strategy(
                strategy=mock_strategy,
                mutation_config=config
            )

        # Verify tier 2 mutation was used
        assert result.tier_used == 2
        assert result.mutation_type == "add_factor"
        assert unified_operator._tier_attempts[2] >= 1

    def test_backward_compatibility_tier3_mutations(self, unified_operator):
        """Test that tier 3 mutations still work after exit mutation integration."""
        # This test verifies backward compatibility exists
        # The actual tier 3 implementation details are tested in tier 3 test suite
        # Here we just verify the integration doesn't break tier 3 access
        assert unified_operator.tier3_mutator is not None
        assert hasattr(unified_operator, '_apply_tier3_mutation')

        # Verify tier 3 statistics are tracked
        assert 3 in unified_operator._tier_attempts
        assert 3 in unified_operator._tier_successes
        assert 3 in unified_operator._tier_failures

    def test_statistics_include_exit_mutations(self, unified_operator, mock_strategy):
        """Test that get_tier_statistics includes exit mutation stats."""
        # Apply some mutations
        unified_operator.mutate_strategy(
            mock_strategy,
            {"mutation_type": "exit_parameter_mutation"}
        )

        stats = unified_operator.get_tier_statistics()

        # Verify exit mutation fields exist
        assert 'exit_mutation_attempts' in stats
        assert 'exit_mutation_successes' in stats
        assert 'exit_mutation_failures' in stats
        assert 'exit_mutation_success_rate' in stats

        # Verify totals include exit mutations
        assert stats['total_mutations'] >= stats['exit_mutation_attempts']

    def test_reset_statistics_clears_exit_mutations(
        self, unified_operator, mock_strategy
    ):
        """Test that reset_statistics clears exit mutation stats."""
        # Directly set statistics (bypassing mutation application)
        unified_operator._exit_mutation_attempts = 5
        unified_operator._exit_mutation_successes = 3
        unified_operator._exit_mutation_failures = 2

        # Verify stats are non-zero
        assert unified_operator._exit_mutation_attempts > 0

        # Reset statistics
        unified_operator.reset_statistics()

        # Verify exit mutation stats are cleared
        assert unified_operator._exit_mutation_attempts == 0
        assert unified_operator._exit_mutation_successes == 0
        assert unified_operator._exit_mutation_failures == 0

    def test_mutation_history_includes_exit_mutations(
        self, unified_operator, mock_strategy
    ):
        """Test that mutation history includes exit mutations."""
        config = {"mutation_type": "exit_parameter_mutation"}

        result = unified_operator.mutate_strategy(
            strategy=mock_strategy,
            mutation_config=config
        )

        # Verify mutation is in history
        assert len(unified_operator._mutation_history) == 1
        assert unified_operator._mutation_history[0] == result
        assert unified_operator._mutation_history[0].mutation_type == "exit_parameter_mutation"

    def test_multiple_parameter_mutations(self, unified_operator, mock_strategy):
        """Test mutating different exit parameters."""
        parameters = ["stop_loss_pct", "take_profit_pct", "trailing_stop_offset"]

        for param in parameters:
            config = {
                "mutation_type": "exit_parameter_mutation",
                "exit_config": {"parameter_name": param}
            }

            result = unified_operator.mutate_strategy(
                strategy=mock_strategy,
                mutation_config=config
            )

            # Verify correct parameter was mutated
            if result.success:
                assert result.metadata['parameter_name'] == param

    def test_exit_mutation_validation_enabled(
        self, mock_yaml_interpreter, mock_tier2_engine,
        mock_tier3_mutator, mock_tier_selector, mock_strategy
    ):
        """Test exit mutation with validation enabled."""
        operator = UnifiedMutationOperator(
            yaml_interpreter=mock_yaml_interpreter,
            tier2_engine=mock_tier2_engine,
            tier3_mutator=mock_tier3_mutator,
            tier_selector=mock_tier_selector,
            validate_mutations=True  # Enable validation
        )

        config = {"mutation_type": "exit_parameter_mutation"}
        result = operator.mutate_strategy(
            strategy=mock_strategy,
            mutation_config=config
        )

        # Verify validation was called
        if result.success:
            mock_strategy.validate.assert_called()

    def test_exit_mutation_with_invalid_strategy(
        self, unified_operator
    ):
        """Test exit mutation with strategy that doesn't support code access."""
        # Create strategy without code attribute
        invalid_strategy = Mock(spec=Strategy)
        invalid_strategy.copy = Mock(return_value=invalid_strategy)
        invalid_strategy.validate = Mock()
        # No code, to_code, or update_code methods

        config = {"mutation_type": "exit_parameter_mutation"}
        result = unified_operator.mutate_strategy(
            strategy=invalid_strategy,
            mutation_config=config
        )

        # Should still attempt mutation using str() fallback
        assert result.mutation_type == "exit_parameter_mutation"

    def test_concurrent_tier_and_exit_mutations(
        self, mock_yaml_interpreter, mock_tier2_engine,
        mock_tier3_mutator, mock_tier_selector, mock_strategy
    ):
        """Test that both tier and exit mutations can be applied in sequence."""
        # Create fresh operator to avoid interference from other tests
        operator = UnifiedMutationOperator(
            yaml_interpreter=mock_yaml_interpreter,
            tier2_engine=mock_tier2_engine,
            tier3_mutator=mock_tier3_mutator,
            tier_selector=mock_tier_selector,
            exit_mutation_probability=0.20,
            validate_mutations=False
        )

        # Setup tier 2 mock
        mock_tier2_engine.select_operator.return_value = (
            "add_factor",
            Mock(mutate=Mock(return_value=mock_strategy))
        )

        # Track initial history length
        initial_history_length = len(operator._mutation_history)

        # Apply exit mutation (explicitly forced via mutation_type)
        exit_config = {"mutation_type": "exit_parameter_mutation"}
        exit_result = operator.mutate_strategy(mock_strategy, mutation_config=exit_config)

        # Apply tier 2 mutation (explicitly forced via override_tier and mutation_type check)
        # We don't pass mutation_type, so it should check random() probability
        # But we override tier to force tier 2, and patch random to avoid exit mutation
        tier_config = {"override_tier": 2}
        with patch('src.mutation.unified_mutation_operator.random.random', return_value=0.99):
            tier_result = operator.mutate_strategy(mock_strategy, mutation_config=tier_config)

        # Verify exit mutation was applied
        assert exit_result.mutation_type == "exit_parameter_mutation"

        # Verify tier mutation was applied (tier 2 was used)
        assert tier_result.tier_used == 2

        # Verify both are in history
        final_history_length = len(operator._mutation_history)
        assert final_history_length >= initial_history_length + 2


class TestExitMutationProbability:
    """Test suite for exit mutation probability distribution."""

    def test_probability_distribution(self, unified_operator, mock_strategy):
        """Test that mutation type probabilities are correctly distributed."""
        num_iterations = 1000
        mutation_types = {
            'exit_parameter_mutation': 0,
            'tier_mutation': 0
        }

        for _ in range(num_iterations):
            result = unified_operator.mutate_strategy(
                strategy=mock_strategy,
                mutation_config={}
            )

            if result.mutation_type == "exit_parameter_mutation":
                mutation_types['exit_parameter_mutation'] += 1
            else:
                mutation_types['tier_mutation'] += 1

        # Verify exit mutations occur at ~20% (allow 5% tolerance)
        exit_rate = mutation_types['exit_parameter_mutation'] / num_iterations
        assert 0.15 <= exit_rate <= 0.25

        # Verify tier mutations occur at ~80%
        tier_rate = mutation_types['tier_mutation'] / num_iterations
        assert 0.75 <= tier_rate <= 0.85

    def test_custom_probability(
        self, mock_yaml_interpreter, mock_tier2_engine,
        mock_tier3_mutator, mock_tier_selector, mock_strategy
    ):
        """Test custom exit mutation probability."""
        operator = UnifiedMutationOperator(
            yaml_interpreter=mock_yaml_interpreter,
            tier2_engine=mock_tier2_engine,
            tier3_mutator=mock_tier3_mutator,
            tier_selector=mock_tier_selector,
            exit_mutation_probability=0.50  # 50% exit mutations
        )

        num_iterations = 1000
        exit_count = 0

        for _ in range(num_iterations):
            result = operator.mutate_strategy(
                strategy=mock_strategy,
                mutation_config={}
            )

            if result.mutation_type == "exit_parameter_mutation":
                exit_count += 1

        # Verify ~50% exit mutation rate (allow 5% tolerance)
        exit_rate = exit_count / num_iterations
        assert 0.45 <= exit_rate <= 0.55


class TestExitMutationMetadata:
    """Test suite for exit mutation metadata tracking."""

    def test_metadata_structure(self, unified_operator, mock_strategy):
        """Test that metadata has correct structure."""
        config = {"mutation_type": "exit_parameter_mutation"}
        result = unified_operator.mutate_strategy(
            strategy=mock_strategy,
            mutation_config=config
        )

        # Verify metadata structure
        assert isinstance(result.metadata, dict)
        assert result.metadata['exit_mutation'] is True

        if result.success:
            # Successful mutation metadata
            assert isinstance(result.metadata['parameter_name'], str)
            assert isinstance(result.metadata['old_value'], float)
            assert isinstance(result.metadata['new_value'], float)
            assert isinstance(result.metadata['clamped'], bool)
            assert isinstance(result.metadata['validation_passed'], bool)

    def test_metadata_parameter_values(self, unified_operator, mock_strategy):
        """Test that metadata contains correct parameter values."""
        config = {
            "mutation_type": "exit_parameter_mutation",
            "exit_config": {"parameter_name": "stop_loss_pct"}
        }

        result = unified_operator.mutate_strategy(
            strategy=mock_strategy,
            mutation_config=config
        )

        if result.success:
            # Verify parameter name matches
            assert result.metadata['parameter_name'] == 'stop_loss_pct'

            # Verify old and new values are different (mutation occurred)
            assert result.metadata['old_value'] != result.metadata['new_value']

            # Verify values are within bounds
            assert 0.01 <= result.metadata['new_value'] <= 0.20  # stop_loss bounds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
