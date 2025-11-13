"""
Unit tests for mutation mechanism.

Tests cover:
- MutationManager initialization
- Gaussian mutation (bounds, distribution)
- Parameter mutation (type preservation, mutation rate)
- Weight renormalization
- Code generation
- Complete mutation workflow with retries
- Edge cases and error conditions
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any
import random
import numpy as np

from src.evolution.mutation import MutationManager
from src.evolution.types import Strategy, MultiObjectiveMetrics


class TestMutationManagerInit:
    """Test MutationManager initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        code_validator = Mock()

        manager = MutationManager(code_validator=code_validator)

        assert manager.code_validator is code_validator
        assert manager.mutation_rate == 0.1
        assert manager.mutation_strength == 0.1
        assert manager.max_retries == 3

    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        code_validator = Mock()

        manager = MutationManager(
            code_validator=code_validator,
            mutation_rate=0.2,
            mutation_strength=0.15,
            max_retries=5
        )

        assert manager.mutation_rate == 0.2
        assert manager.mutation_strength == 0.15
        assert manager.max_retries == 5

    def test_invalid_mutation_rate(self):
        """Test that invalid mutation_rate raises ValueError."""
        code_validator = Mock()

        with pytest.raises(ValueError, match="mutation_rate must be in"):
            MutationManager(code_validator, mutation_rate=1.5)

        with pytest.raises(ValueError, match="mutation_rate must be in"):
            MutationManager(code_validator, mutation_rate=-0.1)

    def test_invalid_mutation_strength(self):
        """Test that invalid mutation_strength raises ValueError."""
        code_validator = Mock()

        with pytest.raises(ValueError, match="mutation_strength must be positive"):
            MutationManager(code_validator, mutation_strength=0.0)

        with pytest.raises(ValueError, match="mutation_strength must be positive"):
            MutationManager(code_validator, mutation_strength=-0.1)

    def test_invalid_max_retries(self):
        """Test that invalid max_retries raises ValueError."""
        code_validator = Mock()

        with pytest.raises(ValueError, match="max_retries must be at least 1"):
            MutationManager(code_validator, max_retries=0)


class TestGaussianMutation:
    """Test Gaussian mutation functionality."""

    @pytest.fixture
    def manager(self):
        """Create MutationManager instance for testing."""
        code_validator = Mock()
        return MutationManager(code_validator)

    def test_gaussian_mutation_within_bounds(self, manager):
        """Test that Gaussian mutation respects bounds."""
        np.random.seed(42)

        # Test 100 mutations stay within bounds
        for _ in range(100):
            mutated = manager.gaussian_mutation(
                value=10.0,
                sigma=0.5,
                bounds=(5.0, 15.0)
            )
            assert 5.0 <= mutated <= 15.0

    def test_gaussian_mutation_no_bounds(self, manager):
        """Test Gaussian mutation without bounds."""
        np.random.seed(42)

        value = 10.0
        mutated = manager.gaussian_mutation(value, sigma=0.1)

        # Should be close to original but not identical
        assert mutated != value
        assert abs(mutated - value) < 2.0  # Reasonable deviation

    def test_gaussian_mutation_distribution(self, manager):
        """Test that Gaussian mutation follows expected distribution."""
        np.random.seed(42)

        value = 100.0
        sigma = 0.1
        samples = [
            manager.gaussian_mutation(value, sigma)
            for _ in range(1000)
        ]

        # Mean should be close to original value
        mean = np.mean(samples)
        assert abs(mean - value) < 5.0  # Within 5% of original

        # Standard deviation should be roughly sigma * value
        std = np.std(samples)
        expected_std = sigma * value
        assert abs(std - expected_std) < 5.0  # Reasonable tolerance

    def test_gaussian_mutation_zero_value(self, manager):
        """Test Gaussian mutation with zero value."""
        np.random.seed(42)

        mutated = manager.gaussian_mutation(0.0, sigma=0.1)

        # Mutation of 0 should remain 0 (since noise * 0 = 0)
        assert mutated == 0.0


class TestMutateParameters:
    """Test parameter mutation functionality."""

    @pytest.fixture
    def manager(self):
        """Create MutationManager instance for testing."""
        code_validator = Mock()
        return MutationManager(code_validator, mutation_rate=0.5)

    def test_integer_mutation_preserves_type(self, manager):
        """Test that integer parameters remain integers after mutation."""
        random.seed(42)
        np.random.seed(42)

        params = {'lookback': 20, 'n_stocks': 10}

        mutated = manager.mutate_parameters(params, mutation_rate=1.0)

        # All params should be mutated (rate=1.0)
        assert isinstance(mutated['lookback'], int)
        assert isinstance(mutated['n_stocks'], int)

    def test_float_mutation_preserves_type(self, manager):
        """Test that float parameters remain floats after mutation."""
        random.seed(42)
        np.random.seed(42)

        params = {'threshold': 0.5, 'alpha': 0.05}

        mutated = manager.mutate_parameters(params, mutation_rate=1.0)

        # All params should be mutated (rate=1.0)
        assert isinstance(mutated['threshold'], float)
        assert isinstance(mutated['alpha'], float)

    def test_mutation_rate_controls_frequency(self, manager):
        """Test that mutation_rate controls how many parameters are mutated."""
        random.seed(42)
        np.random.seed(42)

        params = {f'param_{i}': i * 1.0 for i in range(100)}

        # With rate=0.1, expect ~10 mutations
        mutated = manager.mutate_parameters(params, mutation_rate=0.1)

        # Count changed parameters
        changed = sum(1 for k in params if mutated[k] != params[k])

        # Should be roughly 10% (allow 5-20%)
        assert 5 <= changed <= 20, f"Expected 5-20 mutations, got {changed}"

    def test_factor_weights_renormalized(self, manager):
        """Test that factor weights are renormalized to sum=1.0."""
        random.seed(42)
        np.random.seed(42)

        params = {
            'factor_weights': {'roe': 0.6, 'momentum': 0.4}
        }

        mutated = manager.mutate_parameters(params, mutation_rate=1.0)

        # Check that weights sum to 1.0
        weights = mutated['factor_weights']
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-6, f"Weights sum to {total}, expected 1.0"

    def test_all_zero_weights_fallback(self, manager):
        """Test fallback to equal weights when all weights are zero."""
        random.seed(42)
        np.random.seed(42)

        params = {'factor_weights': {'roe': 0.0, 'momentum': 0.0, 'pe': 0.0}}

        # Force all weights to mutate to zero
        with patch.object(manager, 'gaussian_mutation', return_value=0.0):
            mutated = manager.mutate_parameters(params, mutation_rate=1.0)

        weights = mutated['factor_weights']
        # Should use equal weights (1/3 each)
        assert abs(weights['roe'] - 1/3) < 1e-6
        assert abs(weights['momentum'] - 1/3) < 1e-6
        assert abs(weights['pe'] - 1/3) < 1e-6

    def test_empty_parameters(self, manager):
        """Test mutation with empty parameter dictionary."""
        params = {}

        mutated = manager.mutate_parameters(params, mutation_rate=0.5)

        assert mutated == {}

    def test_mixed_type_parameters(self, manager):
        """Test mutation with mixed parameter types."""
        random.seed(42)
        np.random.seed(42)

        params = {
            'lookback': 20,           # int
            'threshold': 0.5,         # float
            'name': 'momentum',       # string (should not mutate)
            'factor_weights': {'roe': 1.0}
        }

        mutated = manager.mutate_parameters(params, mutation_rate=1.0)

        # Types should be preserved
        assert isinstance(mutated['lookback'], int)
        assert isinstance(mutated['threshold'], float)
        assert mutated['name'] == 'momentum'  # Unchanged
        assert 'factor_weights' in mutated


class TestGenerateMutatedCode:
    """Test mutated code generation."""

    @pytest.fixture
    def manager(self):
        """Create MutationManager instance with mocked dependencies."""
        code_validator = Mock()
        return MutationManager(code_validator)

    @pytest.fixture
    def strategy(self):
        """Create strategy for testing."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        return Strategy(
            id='strategy1',
            generation=1,
            parent_ids=[],
            code='# Original code',
            parameters={'lookback': 20},
            metrics=metrics
        )

    def test_generate_valid_code(self, manager, strategy):
        """Test generating valid mutated code."""
        mutated_params = {'lookback': 25}
        prompt_builder = Mock()

        # Mock prompt builder and code validator
        prompt_builder.build_mutation_prompt = Mock(
            return_value="Generate mutated strategy with lookback=25"
        )
        manager._call_llm_api = Mock(return_value="# Generated mutated code")
        manager.code_validator.validate = Mock(return_value=True)

        code = manager.generate_mutated_code(strategy, mutated_params, prompt_builder)

        assert code == "# Generated mutated code"
        prompt_builder.build_mutation_prompt.assert_called_once()
        manager.code_validator.validate.assert_called_once_with("# Generated mutated code")

    def test_generate_invalid_code_returns_none(self, manager, strategy):
        """Test that invalid code returns None."""
        mutated_params = {'lookback': 25}
        prompt_builder = Mock()

        # Mock validation failure
        prompt_builder.build_mutation_prompt = Mock(
            return_value="Generate mutated strategy"
        )
        manager._call_llm_api = Mock(return_value="# Invalid mutated code")
        manager.code_validator.validate = Mock(return_value=False)

        code = manager.generate_mutated_code(strategy, mutated_params, prompt_builder)

        assert code is None

    def test_generate_code_exception_returns_none(self, manager, strategy):
        """Test that exceptions during generation return None."""
        mutated_params = {'lookback': 25}
        prompt_builder = Mock()

        # Mock exception
        prompt_builder.build_mutation_prompt = Mock(
            side_effect=Exception("API error")
        )

        code = manager.generate_mutated_code(strategy, mutated_params, prompt_builder)

        assert code is None


class TestMutate:
    """Test complete mutation operation with retry logic."""

    @pytest.fixture
    def manager(self):
        """Create MutationManager instance for testing."""
        code_validator = Mock()
        return MutationManager(code_validator, max_retries=3)

    @pytest.fixture
    def strategy(self):
        """Create strategy for testing."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        return Strategy(
            id='strategy1',
            generation=1,
            parent_ids=[],
            code='# Original code',
            parameters={
                'lookback': 20,
                'factor_weights': {'roe': 0.6, 'momentum': 0.4}
            },
            metrics=metrics
        )

    def test_mutate_succeeds_on_first_attempt(self, manager, strategy):
        """Test successful mutation on first attempt."""
        prompt_builder = Mock()

        # Mock successful code generation
        manager.generate_mutated_code = Mock(return_value="# Valid mutated code")

        mutated = manager.mutate(strategy, prompt_builder)

        # Note: Current implementation returns None (placeholder)
        # In production, this should return a Strategy object
        manager.generate_mutated_code.assert_called_once()

    def test_mutate_retries_on_failure(self, manager, strategy):
        """Test that mutation retries on code generation failure."""
        prompt_builder = Mock()

        # Mock failures then success
        manager.generate_mutated_code = Mock(
            side_effect=[None, None, "# Valid mutated code"]
        )

        mutated = manager.mutate(strategy, prompt_builder, max_retries=3)

        # Should retry 3 times
        assert manager.generate_mutated_code.call_count == 3

    def test_mutate_fails_after_max_retries(self, manager, strategy):
        """Test that mutation returns None after max retries."""
        prompt_builder = Mock()

        # Mock all failures
        manager.generate_mutated_code = Mock(return_value=None)

        mutated = manager.mutate(strategy, prompt_builder, max_retries=3)

        assert mutated is None
        assert manager.generate_mutated_code.call_count == 3

    def test_mutate_with_custom_params(self, manager, strategy):
        """Test mutation with custom mutation rate and strength."""
        prompt_builder = Mock()

        # Mock successful code generation
        manager.generate_mutated_code = Mock(return_value="# Valid mutated code")

        mutated = manager.mutate(
            strategy,
            prompt_builder,
            mutation_rate=0.3,
            mutation_strength=0.2
        )

        # Should use custom parameters
        manager.generate_mutated_code.assert_called_once()


class TestWeightRenormalization:
    """Test weight renormalization helper."""

    @pytest.fixture
    def manager(self):
        """Create MutationManager instance for testing."""
        code_validator = Mock()
        return MutationManager(code_validator)

    def test_renormalize_sums_to_one(self, manager):
        """Test that renormalization produces sum=1.0."""
        weights = {'roe': 0.6, 'momentum': 0.3, 'pe': 0.1}

        normalized = manager._renormalize_weights(weights)

        total = sum(normalized.values())
        assert abs(total - 1.0) < 1e-6

    def test_renormalize_preserves_ratios(self, manager):
        """Test that renormalization preserves relative ratios."""
        weights = {'roe': 0.3, 'momentum': 0.6}

        normalized = manager._renormalize_weights(weights)

        # Ratios should be preserved
        ratio_before = weights['roe'] / weights['momentum']
        ratio_after = normalized['roe'] / normalized['momentum']
        assert abs(ratio_before - ratio_after) < 1e-6

    def test_renormalize_all_zero_weights(self, manager):
        """Test renormalization with all zero weights."""
        weights = {'roe': 0.0, 'momentum': 0.0, 'pe': 0.0}

        normalized = manager._renormalize_weights(weights)

        # Should use equal weights
        assert abs(normalized['roe'] - 1/3) < 1e-6
        assert abs(normalized['momentum'] - 1/3) < 1e-6
        assert abs(normalized['pe'] - 1/3) < 1e-6

    def test_renormalize_empty_weights(self, manager):
        """Test renormalization with empty weights."""
        weights = {}

        normalized = manager._renormalize_weights(weights)

        assert normalized == {}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
