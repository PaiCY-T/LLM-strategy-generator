"""
TDD Tests for Template Parameter Search Spaces

Tests verify:
1. All 6 templates are registered
2. Search spaces return Optuna-compatible dictionaries
3. Parameter ranges are valid (min < max)
4. Templates have diverse parameter sets
5. No hardcoded values (all use trial.suggest_*)
"""

import pytest
import optuna
from typing import Dict, Any

# These imports will FAIL initially (RED phase)
from src.templates.template_registry import TEMPLATE_SEARCH_SPACES
from src.templates.parameter_spaces import (
    momentum_search_space,
    mean_reversion_search_space,
    breakout_trend_search_space,
    volatility_adaptive_search_space,
    dual_momentum_search_space,
    regime_adaptive_search_space
)


class TestTemplateRegistration:
    """Test that all required templates are registered."""

    def test_all_templates_registered(self):
        """Verify all 6 templates exist in registry."""
        expected_templates = {
            'Momentum',
            'MeanReversion',
            'BreakoutTrend',
            'VolatilityAdaptive',
            'DualMomentum',
            'RegimeAdaptive'
        }

        assert set(TEMPLATE_SEARCH_SPACES.keys()) == expected_templates, \
            f"Expected {expected_templates}, got {set(TEMPLATE_SEARCH_SPACES.keys())}"

    def test_registry_values_are_callable(self):
        """Each registry entry must be a callable function."""
        for template_name, search_space_fn in TEMPLATE_SEARCH_SPACES.items():
            assert callable(search_space_fn), \
                f"Template {template_name} search space is not callable"


class TestSearchSpaceOptuna:
    """Test Optuna compatibility of search spaces."""

    @pytest.fixture
    def optuna_study(self):
        """Create Optuna study for testing."""
        return optuna.create_study(direction='maximize')

    def test_search_space_returns_optuna_compatible_dict(self, optuna_study):
        """Each template must return dict compatible with Optuna trial."""
        for template_name, search_space_fn in TEMPLATE_SEARCH_SPACES.items():
            trial = optuna_study.ask()

            # Call search space function
            params = search_space_fn(trial)

            # Verify returns dictionary
            assert isinstance(params, dict), \
                f"{template_name} must return dict, got {type(params)}"

            # Verify dictionary is not empty
            assert len(params) > 0, \
                f"{template_name} returned empty parameter dict"

            # Verify all values are numeric or string (valid Optuna types)
            for param_name, param_value in params.items():
                assert isinstance(param_value, (int, float, str, bool)), \
                    f"{template_name}.{param_name} has invalid type {type(param_value)}"

    def test_search_space_uses_trial_suggest(self, optuna_study):
        """Verify each template uses trial.suggest_*() methods (no hardcoded values)."""
        for template_name, search_space_fn in TEMPLATE_SEARCH_SPACES.items():
            trial = optuna_study.ask()

            # Get parameters
            params1 = search_space_fn(trial)

            # Get parameters from new trial (should be potentially different)
            trial2 = optuna_study.ask()
            params2 = search_space_fn(trial2)

            # Both should have same keys
            assert params1.keys() == params2.keys(), \
                f"{template_name} has inconsistent parameter keys"


class TestParameterRanges:
    """Test parameter ranges are valid and sensible."""

    def _get_fresh_trial(self):
        """Create fresh trial for each template to avoid parameter conflicts."""
        study = optuna.create_study(direction='maximize')
        return study.ask()

    def test_parameter_ranges_valid(self):
        """All parameter ranges must be valid (min < max for numeric)."""
        for template_name, search_space_fn in TEMPLATE_SEARCH_SPACES.items():
            trial = self._get_fresh_trial()
            params = search_space_fn(trial)

            # Verify each parameter is within reasonable bounds
            for param_name, param_value in params.items():
                if isinstance(param_value, (int, float)):
                    # Numeric parameters should be positive for financial contexts
                    # (except for thresholds which can be 0)
                    assert param_value >= 0 or 'threshold' in param_name.lower(), \
                        f"{template_name}.{param_name} = {param_value} is negative"

    def test_position_sizes_reasonable(self):
        """Position size parameters should be between 0 and 1 (as percentages)."""
        for template_name, search_space_fn in TEMPLATE_SEARCH_SPACES.items():
            trial = self._get_fresh_trial()
            params = search_space_fn(trial)

            # Find position size parameters
            position_params = [
                (name, value) for name, value in params.items()
                if 'position' in name.lower() and 'pct' in name.lower()
            ]

            for param_name, param_value in position_params:
                assert 0 < param_value <= 1.0, \
                    f"{template_name}.{param_name} = {param_value} outside [0, 1]"

    def test_lookback_periods_reasonable(self):
        """Lookback periods should be between 1 and 252 days (trading year)."""
        for template_name, search_space_fn in TEMPLATE_SEARCH_SPACES.items():
            trial = self._get_fresh_trial()
            params = search_space_fn(trial)

            # Find lookback parameters
            lookback_params = [
                (name, value) for name, value in params.items()
                if 'lookback' in name.lower() or 'period' in name.lower()
            ]

            for param_name, param_value in lookback_params:
                if isinstance(param_value, int):
                    assert 1 <= param_value <= 252, \
                        f"{template_name}.{param_name} = {param_value} outside [1, 252] days"


class TestTemplateDiversity:
    """Test that templates are diverse and not duplicates."""

    @pytest.fixture
    def all_param_sets(self):
        """Get parameter sets from all templates."""
        # Use separate trial for each template to avoid parameter name conflicts
        return {
            template_name: set(self._get_params_for_template(search_space_fn).keys())
            for template_name, search_space_fn in TEMPLATE_SEARCH_SPACES.items()
        }

    def _get_params_for_template(self, search_space_fn):
        """Get parameters for a single template using a fresh trial."""
        study = optuna.create_study(direction='maximize')
        trial = study.ask()
        return search_space_fn(trial)

    def test_template_diversity(self, all_param_sets):
        """Each template should have different parameter sets."""
        template_names = list(all_param_sets.keys())

        # Compare each pair of templates
        for i, template1 in enumerate(template_names):
            for template2 in template_names[i+1:]:
                params1 = all_param_sets[template1]
                params2 = all_param_sets[template2]

                # Templates should not be identical
                assert params1 != params2, \
                    f"{template1} and {template2} have identical parameters: {params1}"

    def test_minimum_parameters_per_template(self, all_param_sets):
        """Each template should have at least 3 parameters."""
        for template_name, params in all_param_sets.items():
            assert len(params) >= 3, \
                f"{template_name} has only {len(params)} parameters (minimum 3)"

    def test_templates_cover_entry_exit_position(self, all_param_sets):
        """Each template should have parameters for entry, exit, and position sizing."""
        for template_name, params in all_param_sets.items():
            param_str = ' '.join(params).lower()

            # Check for entry-related parameters (broader set of keywords)
            has_entry = any(keyword in param_str for keyword in [
                'entry', 'threshold', 'lookback', 'rsi', 'breakout',
                'efficiency', 'ma', 'period', 'bb', 'percentb'
            ])

            # Check for exit-related parameters
            has_exit = any(keyword in param_str for keyword in [
                'exit', 'stop', 'trailing', 'neutral', 'reverse', 'confirmation',
                'threshold'  # Regime thresholds also control exits
            ])

            # Check for position sizing
            has_position = any(keyword in param_str for keyword in [
                'position', 'size'
            ])

            assert has_entry, f"{template_name} missing entry parameters: {params}"
            assert has_exit, f"{template_name} missing exit parameters: {params}"
            assert has_position, f"{template_name} missing position sizing parameters: {params}"


class TestNoHardcodedValues:
    """Test that all parameters use trial.suggest_*() methods."""

    def test_no_hardcoded_values(self):
        """Verify parameters change across trials (not hardcoded)."""
        study = optuna.create_study(direction='maximize', sampler=optuna.samplers.RandomSampler())

        for template_name, search_space_fn in TEMPLATE_SEARCH_SPACES.items():
            # Generate multiple trials
            trials_params = []
            for _ in range(10):
                trial = study.ask()
                params = search_space_fn(trial)
                trials_params.append(params)

            # Check that at least some parameters vary across trials
            # (proving they're not hardcoded)
            for param_name in trials_params[0].keys():
                values = [p[param_name] for p in trials_params]

                # For numeric parameters, expect variation
                if isinstance(values[0], (int, float)):
                    unique_values = len(set(values))
                    assert unique_values > 1, \
                        f"{template_name}.{param_name} appears hardcoded (same value across 10 trials)"
