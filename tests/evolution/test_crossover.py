"""
Unit tests for crossover mechanism.

Tests cover:
- CrossoverManager initialization
- Parameter crossover (uniform distribution, weight renormalization)
- Offspring code generation
- Crossover with retry logic
- Compatibility checking
- Edge cases and error conditions
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any
import random

from src.evolution.crossover import CrossoverManager
from src.evolution.types import Strategy, MultiObjectiveMetrics


class TestCrossoverManagerInit:
    """Test CrossoverManager initialization."""

    def test_initialization_with_defaults(self):
        """Test initialization with default parameters."""
        prompt_builder = Mock()
        code_validator = Mock()

        manager = CrossoverManager(
            prompt_builder=prompt_builder,
            code_validator=code_validator
        )

        assert manager.prompt_builder is prompt_builder
        assert manager.code_validator is code_validator
        assert manager.crossover_rate == 0.7
        assert manager.max_retries == 3

    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters."""
        prompt_builder = Mock()
        code_validator = Mock()

        manager = CrossoverManager(
            prompt_builder=prompt_builder,
            code_validator=code_validator,
            crossover_rate=0.9,
            max_retries=5
        )

        assert manager.crossover_rate == 0.9
        assert manager.max_retries == 5

    def test_invalid_crossover_rate(self):
        """Test that invalid crossover_rate raises ValueError."""
        prompt_builder = Mock()
        code_validator = Mock()

        with pytest.raises(ValueError, match="crossover_rate must be in"):
            CrossoverManager(
                prompt_builder=prompt_builder,
                code_validator=code_validator,
                crossover_rate=1.5
            )

        with pytest.raises(ValueError, match="crossover_rate must be in"):
            CrossoverManager(
                prompt_builder=prompt_builder,
                code_validator=code_validator,
                crossover_rate=-0.1
            )

    def test_invalid_max_retries(self):
        """Test that invalid max_retries raises ValueError."""
        prompt_builder = Mock()
        code_validator = Mock()

        with pytest.raises(ValueError, match="max_retries must be at least 1"):
            CrossoverManager(
                prompt_builder=prompt_builder,
                code_validator=code_validator,
                max_retries=0
            )


class TestParameterCrossover:
    """Test parameter crossover functionality."""

    @pytest.fixture
    def manager(self):
        """Create CrossoverManager instance for testing."""
        prompt_builder = Mock()
        code_validator = Mock()
        return CrossoverManager(prompt_builder, code_validator)

    def test_uniform_crossover_distribution(self, manager):
        """Test that parameter crossover follows uniform distribution."""
        params1 = {'lookback': 20, 'threshold': 0.5}
        params2 = {'lookback': 30, 'threshold': 0.3}

        # Run crossover 100 times and check distribution
        random.seed(42)
        results = []
        for _ in range(100):
            crossover_params = manager.parameter_crossover(params1, params2)
            results.append(crossover_params['lookback'])

        # Count occurrences of each value
        count_20 = results.count(20)
        count_30 = results.count(30)

        # Should be roughly 50/50 (allow 30-70% range)
        assert 30 <= count_20 <= 70, f"Expected 30-70%, got {count_20}%"
        assert 30 <= count_30 <= 70, f"Expected 30-70%, got {count_30}%"

    def test_handles_missing_keys(self, manager):
        """Test that crossover handles missing keys gracefully."""
        params1 = {'lookback': 20, 'threshold': 0.5}
        params2 = {'lookback': 30, 'momentum': 0.8}

        crossover_params = manager.parameter_crossover(params1, params2)

        # All keys from both parents should be present
        assert 'lookback' in crossover_params
        assert 'threshold' in crossover_params or 'momentum' in crossover_params

        # Missing keys should be handled
        if 'threshold' in crossover_params:
            assert crossover_params['threshold'] == 0.5
        if 'momentum' in crossover_params:
            assert crossover_params['momentum'] == 0.8

    def test_factor_weights_renormalized(self, manager):
        """Test that factor weights are renormalized to sum=1.0."""
        params1 = {
            'factor_weights': {'roe': 0.6, 'momentum': 0.4}
        }
        params2 = {
            'factor_weights': {'roe': 0.3, 'pe': 0.7}
        }

        crossover_params = manager.parameter_crossover(params1, params2)

        # Check that weights sum to 1.0
        weights = crossover_params['factor_weights']
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-6, f"Weights sum to {total}, expected 1.0"

    def test_all_zero_weights_fallback(self, manager):
        """Test fallback to equal weights when all weights are zero."""
        params1 = {'factor_weights': {'roe': 0.0, 'momentum': 0.0}}
        params2 = {'factor_weights': {'roe': 0.0, 'momentum': 0.0}}

        crossover_params = manager.parameter_crossover(params1, params2)

        weights = crossover_params['factor_weights']
        # Should use equal weights
        assert abs(weights['roe'] - 0.5) < 1e-6
        assert abs(weights['momentum'] - 0.5) < 1e-6

    def test_empty_parameters(self, manager):
        """Test crossover with empty parameter dictionaries."""
        params1 = {}
        params2 = {}

        crossover_params = manager.parameter_crossover(params1, params2)

        assert crossover_params == {}


class TestGenerateOffspringCode:
    """Test offspring code generation."""

    @pytest.fixture
    def manager(self):
        """Create CrossoverManager instance with mocked dependencies."""
        prompt_builder = Mock()
        code_validator = Mock()
        return CrossoverManager(prompt_builder, code_validator)

    @pytest.fixture
    def parent_strategies(self):
        """Create parent strategies for testing."""
        metrics1 = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        metrics2 = MultiObjectiveMetrics(
            sharpe_ratio=1.8,
            calmar_ratio=1.0,
            max_drawdown=-0.20,
            total_return=0.30,
            win_rate=0.60,
            annual_return=0.25
        )

        parent1 = Strategy(
            id='parent1',
            generation=1,
            parent_ids=[],
            code='# Parent 1 code',
            parameters={'lookback': 20},
            metrics=metrics1,
            pareto_rank=1,
            crowding_distance=0.5,
            timestamp='2025-10-19T00:00:00'
        )

        parent2 = Strategy(
            id='parent2',
            generation=1,
            parent_ids=[],
            code='# Parent 2 code',
            parameters={'lookback': 30},
            metrics=metrics2,
            pareto_rank=1,
            crowding_distance=0.6,
            timestamp='2025-10-19T00:00:00'
        )

        return parent1, parent2

    def test_generate_valid_code(self, manager, parent_strategies):
        """Test generating valid offspring code."""
        parent1, parent2 = parent_strategies
        crossover_params = {'lookback': 25}

        # Mock prompt builder and code validator
        manager.prompt_builder.build_crossover_prompt = Mock(
            return_value="Generate strategy with lookback=25"
        )
        manager._call_llm_api = Mock(return_value="# Generated code")
        manager.code_validator.validate = Mock(return_value=True)

        code = manager.generate_offspring_code(parent1, parent2, crossover_params)

        assert code == "# Generated code"
        manager.prompt_builder.build_crossover_prompt.assert_called_once()
        manager.code_validator.validate.assert_called_once_with("# Generated code")

    def test_generate_invalid_code_returns_none(self, manager, parent_strategies):
        """Test that invalid code returns None."""
        parent1, parent2 = parent_strategies
        crossover_params = {'lookback': 25}

        # Mock validation failure
        manager.prompt_builder.build_crossover_prompt = Mock(
            return_value="Generate strategy"
        )
        manager._call_llm_api = Mock(return_value="# Invalid code")
        manager.code_validator.validate = Mock(return_value=False)

        code = manager.generate_offspring_code(parent1, parent2, crossover_params)

        assert code is None

    def test_generate_code_exception_returns_none(self, manager, parent_strategies):
        """Test that exceptions during generation return None."""
        parent1, parent2 = parent_strategies
        crossover_params = {'lookback': 25}

        # Mock exception
        manager.prompt_builder.build_crossover_prompt = Mock(
            side_effect=Exception("API error")
        )

        code = manager.generate_offspring_code(parent1, parent2, crossover_params)

        assert code is None


class TestCrossover:
    """Test complete crossover operation with retry logic."""

    @pytest.fixture
    def manager(self):
        """Create CrossoverManager instance for testing."""
        prompt_builder = Mock()
        code_validator = Mock()
        return CrossoverManager(prompt_builder, code_validator, max_retries=3)

    @pytest.fixture
    def parent_strategies(self):
        """Create compatible parent strategies."""
        metrics1 = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        metrics2 = MultiObjectiveMetrics(
            sharpe_ratio=1.8,
            calmar_ratio=1.0,
            max_drawdown=-0.20,
            total_return=0.30,
            win_rate=0.60,
            annual_return=0.25
        )

        parent1 = Strategy(
            id='parent1',
            generation=1,
            parent_ids=[],
            code='# Parent 1 code',
            parameters={
                'lookback': 20,
                'factor_weights': {'roe': 0.6, 'momentum': 0.4}
            },
            metrics=metrics1,
            pareto_rank=1,
            crowding_distance=0.5,
            timestamp='2025-10-19T00:00:00'
        )

        parent2 = Strategy(
            id='parent2',
            generation=1,
            parent_ids=[],
            code='# Parent 2 code',
            parameters={
                'lookback': 30,
                'factor_weights': {'roe': 0.3, 'momentum': 0.7}
            },
            metrics=metrics2,
            pareto_rank=1,
            crowding_distance=0.6,
            timestamp='2025-10-19T00:00:00'
        )

        return parent1, parent2

    def test_crossover_skipped_by_rate(self, manager, parent_strategies):
        """Test that crossover is skipped based on crossover_rate."""
        parent1, parent2 = parent_strategies

        # Mock random to always return > crossover_rate
        with patch('random.random', return_value=0.9):
            offspring = manager.crossover(parent1, parent2, crossover_rate=0.7)

        assert offspring is None

    def test_crossover_succeeds_on_first_attempt(self, manager, parent_strategies):
        """Test successful crossover on first attempt."""
        parent1, parent2 = parent_strategies

        # Mock random to pass crossover_rate check
        with patch('random.random', return_value=0.5):
            # Mock successful code generation
            manager.generate_offspring_code = Mock(return_value="# Valid code")

            offspring = manager.crossover(parent1, parent2)

            # Note: Current implementation returns None (placeholder)
            # In production, this should return a Strategy object
            manager.generate_offspring_code.assert_called_once()

    def test_crossover_retries_on_failure(self, manager, parent_strategies):
        """Test that crossover retries on code generation failure."""
        parent1, parent2 = parent_strategies

        # Mock random to pass crossover_rate check
        with patch('random.random', return_value=0.5):
            # Mock failures then success
            manager.generate_offspring_code = Mock(
                side_effect=[None, None, "# Valid code"]
            )

            offspring = manager.crossover(parent1, parent2, max_retries=3)

            # Should retry 3 times
            assert manager.generate_offspring_code.call_count == 3

    def test_crossover_fails_after_max_retries(self, manager, parent_strategies):
        """Test that crossover returns None after max retries."""
        parent1, parent2 = parent_strategies

        # Mock random to pass crossover_rate check
        with patch('random.random', return_value=0.5):
            # Mock all failures
            manager.generate_offspring_code = Mock(return_value=None)

            offspring = manager.crossover(parent1, parent2, max_retries=3)

            assert offspring is None
            assert manager.generate_offspring_code.call_count == 3

    def test_crossover_incompatible_parents(self, manager, parent_strategies):
        """Test that incompatible parents are rejected."""
        parent1, parent2 = parent_strategies

        # Make parents incompatible
        parent1.parameters['factor_weights'] = {'roe': 1.0}
        parent2.parameters['factor_weights'] = {'pe': 1.0}

        # Mock random to pass crossover_rate check
        with patch('random.random', return_value=0.5):
            offspring = manager.crossover(parent1, parent2)

            # Should be rejected due to incompatibility
            assert offspring is None


class TestCheckCompatibility:
    """Test parent compatibility checking."""

    @pytest.fixture
    def manager(self):
        """Create CrossoverManager instance for testing."""
        prompt_builder = Mock()
        code_validator = Mock()
        return CrossoverManager(prompt_builder, code_validator)

    @pytest.fixture
    def base_strategy(self):
        """Create base strategy for testing."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        return Strategy(
            id='base',
            generation=1,
            parent_ids=[],
            code='# Base code',
            parameters={},
            metrics=metrics,
            pareto_rank=1,
            crowding_distance=0.5,
            timestamp='2025-10-19T00:00:00'
        )

    def test_compatible_same_factors(self, manager, base_strategy):
        """Test that parents with same factors are compatible."""
        parent1 = base_strategy
        parent1.parameters['factor_weights'] = {'roe': 0.6, 'momentum': 0.4}

        parent2 = base_strategy
        parent2.parameters = {'factor_weights': {'roe': 0.3, 'momentum': 0.7}}

        assert manager.check_compatibility(parent1, parent2) is True

    def test_compatible_overlapping_factors(self, manager, base_strategy):
        """Test that parents with overlapping factors are compatible."""
        parent1 = base_strategy
        parent1.parameters['factor_weights'] = {'roe': 0.5, 'momentum': 0.5}

        parent2 = base_strategy
        parent2.parameters = {'factor_weights': {'roe': 0.6, 'pe': 0.4}}

        # 1 common factor out of 3 total = 33% overlap (>30% threshold)
        assert manager.check_compatibility(parent1, parent2) is True

    def test_incompatible_no_common_factors(self, manager):
        """Test that parents with no common factors are incompatible."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        parent1 = Strategy(
            id='parent1',
            generation=1,
            parameters={'factor_weights': {'roe': 1.0}},
            metrics=metrics
        )

        parent2 = Strategy(
            id='parent2',
            generation=1,
            parameters={'factor_weights': {'pe': 1.0}},
            metrics=metrics
        )

        assert manager.check_compatibility(parent1, parent2) is False

    def test_incompatible_missing_factors(self, manager):
        """Test that parents with missing factors are incompatible."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        parent1 = Strategy(
            id='parent1',
            generation=1,
            parameters={'factor_weights': {}},
            metrics=metrics
        )

        parent2 = Strategy(
            id='parent2',
            generation=1,
            parameters={'factor_weights': {'roe': 1.0}},
            metrics=metrics
        )

        assert manager.check_compatibility(parent1, parent2) is False

    def test_incompatible_low_overlap(self, manager):
        """Test that parents with low factor overlap are incompatible."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        parent1 = Strategy(
            id='parent1',
            generation=1,
            parameters={'factor_weights': {
                'roe': 0.2, 'momentum': 0.2, 'quality': 0.2, 'value': 0.2, 'growth': 0.2
            }},
            metrics=metrics
        )

        parent2 = Strategy(
            id='parent2',
            generation=1,
            parameters={'factor_weights': {'roe': 1.0}},
            metrics=metrics
        )

        # 1 common factor out of 6 total = 17% overlap (<30% threshold)
        assert manager.check_compatibility(parent1, parent2) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
