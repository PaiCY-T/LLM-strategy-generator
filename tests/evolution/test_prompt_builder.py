"""
Unit tests for prompt builder.

Tests cover:
- PromptBuilder initialization
- Crossover prompt generation
- Mutation prompt generation
- Initialization prompt generation
- Metric and parameter formatting
- Edge cases and error conditions
"""

import pytest
from src.evolution.prompt_builder import PromptBuilder
from src.evolution.types import Strategy, MultiObjectiveMetrics


class TestPromptBuilderInit:
    """Test PromptBuilder initialization."""

    def test_initialization(self):
        """Test that PromptBuilder initializes successfully."""
        builder = PromptBuilder()

        assert builder is not None
        assert hasattr(builder, 'base_constraints')
        assert hasattr(builder, 'template_guidelines')

    def test_base_constraints_exist(self):
        """Test that base constraints are defined."""
        builder = PromptBuilder()

        constraints = builder.base_constraints

        assert 'CODE REQUIREMENTS' in constraints
        assert 'NO import statements' in constraints
        assert 'NO exec()' in constraints
        assert 'data.get' in constraints

    def test_template_guidelines_exist(self):
        """Test that template guidelines are defined for all templates."""
        builder = PromptBuilder()

        templates = ['Momentum', 'Value', 'Quality', 'Mixed']

        for template in templates:
            assert template in builder.template_guidelines
            assert len(builder.template_guidelines[template]) > 0


class TestCrossoverPrompt:
    """Test crossover prompt generation."""

    @pytest.fixture
    def builder(self):
        """Create PromptBuilder instance."""
        return PromptBuilder()

    @pytest.fixture
    def parent1(self):
        """Create first parent strategy."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        return Strategy(
            id='parent1_abc123',
            generation=5,
            parent_ids=[],
            code='# Parent 1 momentum strategy\nclose = data.get("price:收盤價")\nmomentum = close.pct_change(20)',
            parameters={
                'lookback': 20,
                'n_stocks': 15,
                'factor_weights': {'momentum': 1.0}
            },
            template_type='Momentum',
            metrics=metrics
        )

    @pytest.fixture
    def parent2(self):
        """Create second parent strategy."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.3,
            calmar_ratio=1.1,
            max_drawdown=-0.18,
            total_return=0.22,
            win_rate=0.52,
            annual_return=0.18
        )

        return Strategy(
            id='parent2_def456',
            generation=5,
            parent_ids=[],
            code='# Parent 2 value strategy\npe = data.get("price_earning_ratio:本益比")\nvalue = 1 / pe',
            parameters={
                'lookback': 60,
                'n_stocks': 20,
                'factor_weights': {'value': 1.0}
            },
            template_type='Value',
            metrics=metrics
        )

    def test_crossover_prompt_structure(self, builder, parent1, parent2):
        """Test that crossover prompt has expected structure."""
        prompt = builder.build_crossover_prompt(parent1, parent2)

        assert 'GENETIC CROSSOVER' in prompt
        assert 'PARENT 1 INFORMATION' in prompt
        assert 'PARENT 2 INFORMATION' in prompt
        assert 'CROSSOVER INSTRUCTIONS' in prompt
        assert 'CODE REQUIREMENTS' in prompt
        assert 'EXPECTED OUTPUT' in prompt

    def test_crossover_includes_parent_info(self, builder, parent1, parent2):
        """Test that crossover prompt includes parent information."""
        prompt = builder.build_crossover_prompt(parent1, parent2)

        # Parent IDs
        assert parent1.id in prompt
        assert parent2.id in prompt

        # Parent templates
        assert 'Momentum' in prompt
        assert 'Value' in prompt

        # Parent code
        assert 'Parent 1 momentum strategy' in prompt
        assert 'Parent 2 value strategy' in prompt

    def test_crossover_includes_metrics(self, builder, parent1, parent2):
        """Test that crossover prompt includes parent metrics."""
        prompt = builder.build_crossover_prompt(parent1, parent2)

        # Sharpe ratios
        assert '1.5000' in prompt  # Parent 1 Sharpe
        assert '1.3000' in prompt  # Parent 2 Sharpe

    def test_crossover_includes_parameters(self, builder, parent1, parent2):
        """Test that crossover prompt includes parent parameters."""
        prompt = builder.build_crossover_prompt(parent1, parent2)

        # Lookback periods
        assert 'lookback' in prompt
        assert '20' in prompt
        assert '60' in prompt

        # Stock counts
        assert 'n_stocks' in prompt
        assert '15' in prompt
        assert '20' in prompt

    def test_crossover_includes_instructions(self, builder, parent1, parent2):
        """Test that crossover prompt includes blending instructions."""
        prompt = builder.build_crossover_prompt(parent1, parent2)

        assert 'Factor Combination' in prompt
        assert 'Parameter Blending' in prompt
        assert 'Logic Integration' in prompt
        assert 'Genetic Diversity' in prompt

    def test_crossover_with_unevaluated_parent(self, builder, parent1, parent2):
        """Test crossover prompt when a parent has no metrics."""
        parent1.metrics = None

        prompt = builder.build_crossover_prompt(parent1, parent2)

        assert 'Not yet evaluated' in prompt
        assert prompt is not None


class TestMutationPrompt:
    """Test mutation prompt generation."""

    @pytest.fixture
    def builder(self):
        """Create PromptBuilder instance."""
        return PromptBuilder()

    @pytest.fixture
    def strategy(self):
        """Create strategy for mutation."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        return Strategy(
            id='strategy_abc123',
            generation=3,
            parent_ids=['parent1', 'parent2'],
            code='# Original strategy\nclose = data.get("price:收盤價")\nmomentum = close.pct_change(20)',
            parameters={
                'lookback': 20,
                'threshold': 0.5,
                'n_stocks': 15,
                'factor_weights': {'momentum': 0.6, 'value': 0.4}
            },
            template_type='Mixed',
            metrics=metrics
        )

    def test_mutation_prompt_structure(self, builder, strategy):
        """Test that mutation prompt has expected structure."""
        mutated_params = {'lookback': 25, 'threshold': 0.52}

        prompt = builder.build_mutation_prompt(strategy, mutated_params)

        assert 'GENETIC MUTATION' in prompt
        assert 'ORIGINAL STRATEGY' in prompt
        assert 'PARAMETER MUTATIONS' in prompt
        assert 'MUTATION INSTRUCTIONS' in prompt
        assert 'CODE REQUIREMENTS' in prompt
        assert 'EXPECTED OUTPUT' in prompt

    def test_mutation_includes_original_strategy(self, builder, strategy):
        """Test that mutation prompt includes original strategy info."""
        mutated_params = {'lookback': 25}

        prompt = builder.build_mutation_prompt(strategy, mutated_params)

        assert strategy.id in prompt
        assert 'Original strategy' in prompt
        assert str(strategy.generation) in prompt

    def test_mutation_shows_parameter_changes(self, builder, strategy):
        """Test that mutation prompt shows before/after parameter values."""
        mutated_params = {
            'lookback': 25,
            'threshold': 0.52,
            'n_stocks': 18
        }

        prompt = builder.build_mutation_prompt(strategy, mutated_params)

        # Should show old → new for each parameter
        assert 'lookback: 20 → 25' in prompt
        assert 'threshold: 0.5 → 0.52' in prompt
        assert 'n_stocks: 15 → 18' in prompt

    def test_mutation_shows_weight_changes(self, builder, strategy):
        """Test that mutation prompt shows factor weight changes."""
        mutated_params = {
            'factor_weights': {'momentum': 0.65, 'value': 0.35}
        }

        prompt = builder.build_mutation_prompt(strategy, mutated_params)

        assert 'factor_weights' in prompt
        assert 'momentum' in prompt
        assert 'value' in prompt
        assert '0.6000 → 0.6500' in prompt  # Momentum weight change
        assert '0.4000 → 0.3500' in prompt  # Value weight change

    def test_mutation_includes_preservation_instructions(self, builder, strategy):
        """Test that mutation prompt emphasizes logic preservation."""
        mutated_params = {'lookback': 25}

        prompt = builder.build_mutation_prompt(strategy, mutated_params)

        assert 'Preserve Core Logic' in prompt
        assert 'Apply Parameter Changes' in prompt
        assert 'SAME strategy with UPDATED parameters' in prompt

    def test_mutation_with_empty_params(self, builder, strategy):
        """Test mutation prompt with no parameter changes."""
        mutated_params = {}

        prompt = builder.build_mutation_prompt(strategy, mutated_params)

        assert prompt is not None
        assert 'PARAMETER MUTATIONS' in prompt


class TestInitializationPrompt:
    """Test initialization prompt generation."""

    @pytest.fixture
    def builder(self):
        """Create PromptBuilder instance."""
        return PromptBuilder()

    def test_initialization_prompt_structure(self, builder):
        """Test that initialization prompt has expected structure."""
        prompt = builder.build_initialization_prompt('Momentum')

        assert 'STRATEGY INITIALIZATION' in prompt
        assert 'MOMENTUM TEMPLATE' in prompt
        assert 'INITIALIZATION INSTRUCTIONS' in prompt
        assert 'CODE REQUIREMENTS' in prompt
        assert 'EXPECTED OUTPUT' in prompt

    def test_initialization_for_each_template(self, builder):
        """Test initialization prompt for all template types."""
        templates = ['Momentum', 'Value', 'Quality', 'Mixed']

        for template in templates:
            prompt = builder.build_initialization_prompt(template)

            assert template.upper() in prompt
            assert 'Template Guidelines' in prompt
            assert len(prompt) > 1000  # Should be substantial

    def test_initialization_includes_template_guidelines(self, builder):
        """Test that initialization prompt includes template-specific guidelines."""
        prompt_momentum = builder.build_initialization_prompt('Momentum')
        prompt_value = builder.build_initialization_prompt('Value')

        # Momentum should mention momentum-specific concepts
        assert 'momentum' in prompt_momentum.lower()
        assert 'trend' in prompt_momentum.lower() or 'returns' in prompt_momentum.lower()

        # Value should mention value-specific concepts
        assert 'value' in prompt_value.lower() or 'valuation' in prompt_value.lower()
        assert 'P/E' in prompt_value or 'P/B' in prompt_value

    def test_initialization_generation_context(self, builder):
        """Test that initialization prompt adapts to generation number."""
        prompt_gen0 = builder.build_initialization_prompt('Mixed', generation=0)
        prompt_gen5 = builder.build_initialization_prompt('Mixed', generation=5)

        # Generation 0 should emphasize initial population diversity
        assert 'GENERATION 0' in prompt_gen0
        assert 'initial population' in prompt_gen0.lower()

        # Later generation should mention offspring creation
        assert 'GENERATION 5' in prompt_gen5
        assert 'offspring' in prompt_gen5.lower()

    def test_initialization_includes_diversity_guidance(self, builder):
        """Test that initialization prompt includes diversity considerations."""
        prompt = builder.build_initialization_prompt('Momentum', generation=0)

        assert 'DIVERSITY' in prompt
        assert 'HIGH DIVERSITY' in prompt
        assert 'different factor combinations' in prompt.lower()

    def test_initialization_includes_instructions(self, builder):
        """Test that initialization prompt includes step-by-step instructions."""
        prompt = builder.build_initialization_prompt('Quality')

        assert 'Data Selection' in prompt
        assert 'Factor Design' in prompt
        assert 'Signal Combination' in prompt
        assert 'Filtering & Selection' in prompt
        assert 'Position Sizing' in prompt


class TestHelperMethods:
    """Test helper methods for formatting."""

    @pytest.fixture
    def builder(self):
        """Create PromptBuilder instance."""
        return PromptBuilder()

    def test_format_metrics_with_valid_metrics(self, builder):
        """Test formatting of valid metrics."""
        metrics = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=1.2,
            max_drawdown=-0.15,
            total_return=0.25,
            win_rate=0.55,
            annual_return=0.20
        )

        formatted = builder._format_metrics(metrics)

        assert '1.5000' in formatted  # Sharpe
        assert '1.2000' in formatted  # Calmar
        assert '-0.1500' in formatted  # Max drawdown
        assert '0.2500' in formatted  # Total return
        assert '0.5500' in formatted  # Win rate
        assert '0.2000' in formatted  # Annual return

    def test_format_metrics_with_none(self, builder):
        """Test formatting when metrics are None."""
        formatted = builder._format_metrics(None)

        assert 'Not yet evaluated' in formatted

    def test_format_parameters_with_simple_params(self, builder):
        """Test formatting of simple parameters."""
        params = {
            'lookback': 20,
            'threshold': 0.5,
            'n_stocks': 15
        }

        formatted = builder._format_parameters(params)

        assert 'lookback: 20' in formatted
        assert 'threshold: 0.5' in formatted
        assert 'n_stocks: 15' in formatted

    def test_format_parameters_with_factor_weights(self, builder):
        """Test formatting of parameters with factor weights."""
        params = {
            'lookback': 20,
            'factor_weights': {'momentum': 0.6, 'value': 0.4}
        }

        formatted = builder._format_parameters(params)

        assert 'factor_weights' in formatted
        assert 'momentum: 0.6000' in formatted
        assert 'value: 0.4000' in formatted

    def test_format_parameters_with_empty_dict(self, builder):
        """Test formatting of empty parameter dictionary."""
        params = {}

        formatted = builder._format_parameters(params)

        assert 'No parameters' in formatted


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def builder(self):
        """Create PromptBuilder instance."""
        return PromptBuilder()

    def test_crossover_with_missing_template_type(self, builder):
        """Test crossover when parents have no template_type."""
        parent1 = Strategy(
            id='p1',
            generation=0,
            parent_ids=[],
            code='# code 1',
            parameters={},
            template_type=None
        )

        parent2 = Strategy(
            id='p2',
            generation=0,
            parent_ids=[],
            code='# code 2',
            parameters={},
            template_type=None
        )

        prompt = builder.build_crossover_prompt(parent1, parent2)

        assert 'Mixed' in prompt  # Should default to Mixed

    def test_mutation_with_empty_original_params(self, builder):
        """Test mutation when original strategy has no parameters."""
        strategy = Strategy(
            id='s1',
            generation=0,
            parent_ids=[],
            code='# code',
            parameters={}
        )

        mutated_params = {'new_param': 10}

        prompt = builder.build_mutation_prompt(strategy, mutated_params)

        assert 'new_param: N/A → 10' in prompt

    def test_initialization_with_invalid_template(self, builder):
        """Test initialization with unrecognized template type."""
        # Should not crash, just won't have specific guidelines
        prompt = builder.build_initialization_prompt('UnknownTemplate')

        assert 'UNKNOWNTEMPLATE TEMPLATE' in prompt
        assert 'CODE REQUIREMENTS' in prompt

    def test_prompts_are_non_empty(self, builder):
        """Test that all prompts generate non-empty strings."""
        parent1 = Strategy(id='p1', generation=0, parent_ids=[], code='#1', parameters={})
        parent2 = Strategy(id='p2', generation=0, parent_ids=[], code='#2', parameters={})

        crossover = builder.build_crossover_prompt(parent1, parent2)
        mutation = builder.build_mutation_prompt(parent1, {})
        initialization = builder.build_initialization_prompt('Momentum')

        assert len(crossover) > 100
        assert len(mutation) > 100
        assert len(initialization) > 100

    def test_prompts_contain_no_markdown(self, builder):
        """Test that prompts request code without markdown."""
        parent = Strategy(id='p', generation=0, parent_ids=[], code='#', parameters={})

        crossover = builder.build_crossover_prompt(parent, parent)
        mutation = builder.build_mutation_prompt(parent, {})
        initialization = builder.build_initialization_prompt('Value')

        for prompt in [crossover, mutation, initialization]:
            assert 'no markdown' in prompt.lower()
            assert 'executable Python code' in prompt or 'ONLY' in prompt


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
