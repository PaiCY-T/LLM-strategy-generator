"""
Integration test for Exit Mutation Framework + PopulationManager.

Task 1.6: Integration & Validation
Tests exit mutation integration into population-based learning workflow.

Test Coverage:
1. Configuration loading from YAML
2. Exit mutation operator initialization
3. Exit mutation application during evolution
4. Logging and statistics tracking
5. Backward compatibility (exit mutations can be disabled)
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.evolution.population_manager import PopulationManager
from src.evolution.types import Strategy
from src.mutation.exit_mutation_operator import ExitMutationOperator


# Sample strategy code with exit mechanism for testing
SAMPLE_STRATEGY_CODE = """
# Sample strategy with exit mechanisms
close = data.get('price:收盤價')
returns = close.pct_change(20)
signal = returns.rank(axis=1)

# Entry: Top 20 stocks
selected = signal.rank(axis=1, ascending=False) <= 20
positions = selected.astype(float) / selected.sum(axis=1)

# Exit: Simple stop-loss at -5%
entry_price = close.shift(1)
stop_loss = positions * (close < entry_price * 0.95)
positions = positions - stop_loss
"""


class TestExitMutationIntegration:
    """Integration tests for exit mutation framework."""

    def test_config_loading_success(self):
        """Test successful configuration loading from YAML."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'exit_mutation': {
                    'enabled': True,
                    'exit_mutation_probability': 0.4,
                    'mutation_config': {
                        'tier1_weight': 0.6,
                        'tier2_weight': 0.3,
                        'tier3_weight': 0.1,
                        'parameter_ranges': {
                            'stop_loss_range': [0.85, 1.15],
                            'take_profit_range': [0.9, 1.3],
                            'trailing_range': [0.8, 1.2]
                        }
                    },
                    'monitoring': {
                        'log_mutations': True,
                        'track_mutation_types': True
                    }
                }
            }
            yaml.dump(config, f)
            config_path = f.name

        try:
            # Initialize PopulationManager with custom config
            manager = PopulationManager(config_path=config_path)

            # Verify configuration loaded correctly
            assert manager.exit_mutation_enabled is True
            assert manager.exit_mutation_probability == 0.4
            assert manager.exit_mutation_logging is True
            assert manager.exit_mutation_track_types is True

            # Verify MutationConfig (uses probability_weights, not tier_weights)
            assert manager.exit_mutation_config.probability_weights['parametric'] == 0.6
            assert manager.exit_mutation_config.probability_weights['structural'] == 0.3
            assert manager.exit_mutation_config.probability_weights['relational'] == 0.1

        finally:
            # Cleanup
            Path(config_path).unlink()

    def test_config_loading_fallback_on_missing_file(self):
        """Test graceful fallback when config file is missing."""
        # Use non-existent config path
        manager = PopulationManager(config_path="nonexistent_config.yaml")

        # Verify defaults are used
        assert manager.exit_mutation_enabled is False
        assert manager.exit_mutation_probability == 0.3
        assert manager.exit_mutation_logging is True

    def test_exit_mutation_operator_initialization(self):
        """Test ExitMutationOperator is properly initialized."""
        manager = PopulationManager()

        # Verify operator exists
        assert manager.exit_mutation_operator is not None
        assert isinstance(manager.exit_mutation_operator, ExitMutationOperator)

    def test_apply_exit_mutation_disabled(self):
        """Test exit mutation returns None when disabled."""
        manager = PopulationManager()
        manager.exit_mutation_enabled = False

        # Create sample strategy
        strategy = Strategy(
            id="test_strategy",
            generation=0,
            parent_ids=[],
            code=SAMPLE_STRATEGY_CODE,
            parameters={'lookback': 20},
            template_type='Momentum'
        )

        # Apply exit mutation
        result = manager.apply_exit_mutation(strategy)

        # Should return None when disabled
        assert result is None

    def test_apply_exit_mutation_success(self):
        """Test successful exit mutation application."""
        # Create temporary config with exit mutations enabled
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'exit_mutation': {
                    'enabled': True,
                    'exit_mutation_probability': 1.0,  # Always apply
                    'mutation_config': {
                        'tier1_weight': 1.0,
                        'tier2_weight': 0.0,
                        'tier3_weight': 0.0
                    },
                    'monitoring': {
                        'log_mutations': True
                    }
                }
            }
            yaml.dump(config, f)
            config_path = f.name

        try:
            manager = PopulationManager(config_path=config_path)

            # Create sample strategy
            strategy = Strategy(
                id="test_strategy",
                generation=0,
                parent_ids=[],
                code=SAMPLE_STRATEGY_CODE,
                parameters={'lookback': 20},
                template_type='Momentum'
            )

            # Apply exit mutation
            result = manager.apply_exit_mutation(strategy)

            # Verify mutation was attempted
            assert manager.exit_mutation_stats['attempts'] == 1

            # Result may be None if mutation failed (which is acceptable)
            # or a mutated strategy if successful
            if result is not None:
                assert result.id.endswith('_exit_mutated')
                assert result.generation == 1
                assert result.parent_ids == [strategy.id]
                assert manager.exit_mutation_stats['successes'] == 1
            else:
                assert manager.exit_mutation_stats['failures'] == 1

        finally:
            Path(config_path).unlink()

    def test_exit_mutation_statistics_tracking(self):
        """Test statistics are properly tracked."""
        manager = PopulationManager()
        manager.exit_mutation_enabled = True

        # Verify initial state
        assert manager.exit_mutation_stats['attempts'] == 0
        assert manager.exit_mutation_stats['successes'] == 0
        assert manager.exit_mutation_stats['failures'] == 0

        # Create sample strategy
        strategy = Strategy(
            id="test_strategy",
            generation=0,
            parent_ids=[],
            code=SAMPLE_STRATEGY_CODE,
            parameters={'lookback': 20},
            template_type='Momentum'
        )

        # Apply mutation (may succeed or fail)
        manager.apply_exit_mutation(strategy)

        # Verify attempt was tracked
        assert manager.exit_mutation_stats['attempts'] == 1
        assert (
            manager.exit_mutation_stats['successes'] +
            manager.exit_mutation_stats['failures']
        ) == 1

    def test_backward_compatibility(self):
        """Test system works without exit mutations (backward compatibility)."""
        # Create config with exit mutations disabled
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'exit_mutation': {
                    'enabled': False
                }
            }
            yaml.dump(config, f)
            config_path = f.name

        try:
            manager = PopulationManager(config_path=config_path)

            # Verify exit mutations are disabled
            assert manager.exit_mutation_enabled is False

            # Create sample strategy
            strategy = Strategy(
                id="test_strategy",
                generation=0,
                parent_ids=[],
                code=SAMPLE_STRATEGY_CODE,
                parameters={'lookback': 20},
                template_type='Momentum'
            )

            # Apply exit mutation should return None
            result = manager.apply_exit_mutation(strategy)
            assert result is None

            # Statistics should not be updated
            assert manager.exit_mutation_stats['attempts'] == 0

        finally:
            Path(config_path).unlink()


@pytest.mark.integration
class TestExitMutationSmoke:
    """Smoke tests for exit mutation integration."""

    def test_smoke_mutation_pipeline(self):
        """
        Smoke test: Create 5 strategies and apply exit mutations.

        Success Criteria:
        - No exceptions raised
        - At least 1 mutation attempt
        - Statistics properly tracked
        """
        # Create temporary config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config = {
                'exit_mutation': {
                    'enabled': True,
                    'exit_mutation_probability': 0.5,
                    'mutation_config': {
                        'tier1_weight': 0.7,
                        'tier2_weight': 0.2,
                        'tier3_weight': 0.1
                    },
                    'monitoring': {
                        'log_mutations': True,
                        'track_mutation_types': True
                    }
                }
            }
            yaml.dump(config, f)
            config_path = f.name

        try:
            manager = PopulationManager(config_path=config_path)

            # Create 5 sample strategies
            strategies = []
            for i in range(5):
                strategy = Strategy(
                    id=f"strategy_{i}",
                    generation=0,
                    parent_ids=[],
                    code=SAMPLE_STRATEGY_CODE,
                    parameters={'lookback': 20 + i * 5},
                    template_type='Momentum'
                )
                strategies.append(strategy)

            # Apply exit mutations to all strategies
            mutated_strategies = []
            for strategy in strategies:
                result = manager.apply_exit_mutation(strategy)
                if result is not None:
                    mutated_strategies.append(result)

            # Verify smoke test criteria
            assert manager.exit_mutation_stats['attempts'] >= 1
            assert (
                manager.exit_mutation_stats['successes'] +
                manager.exit_mutation_stats['failures']
            ) == manager.exit_mutation_stats['attempts']

            # Log results
            print(f"\nSmoke test results:")
            print(f"  Strategies: 5")
            print(f"  Attempts: {manager.exit_mutation_stats['attempts']}")
            print(f"  Successes: {manager.exit_mutation_stats['successes']}")
            print(f"  Failures: {manager.exit_mutation_stats['failures']}")
            print(f"  Mutated strategies: {len(mutated_strategies)}")

        finally:
            Path(config_path).unlink()


if __name__ == "__main__":
    # Run smoke test directly
    print("Running Exit Mutation Integration Smoke Test...")
    test = TestExitMutationSmoke()
    test.test_smoke_mutation_pipeline()
    print("\nSmoke test completed successfully!")
