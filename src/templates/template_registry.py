"""
Template Registry for Strategy Parameter Search Spaces

Maps template names to their parameter search space functions.
This registry is used by the TPE optimizer to select and configure templates.

Usage:
    >>> import optuna
    >>> study = optuna.create_study()
    >>> trial = study.ask()
    >>> template_name = 'Momentum'
    >>> params = TEMPLATE_SEARCH_SPACES[template_name](trial)
"""

from typing import Dict, Callable, Any
import optuna

from src.templates.parameter_spaces import (
    momentum_search_space,
    mean_reversion_search_space,
    breakout_trend_search_space,
    volatility_adaptive_search_space,
    dual_momentum_search_space,
    regime_adaptive_search_space
)


# Type alias for search space functions
SearchSpaceFunction = Callable[[optuna.Trial], Dict[str, Any]]


# Template Registry: Maps template names to search space functions
TEMPLATE_SEARCH_SPACES: Dict[str, SearchSpaceFunction] = {
    'Momentum': momentum_search_space,
    'MeanReversion': mean_reversion_search_space,
    'BreakoutTrend': breakout_trend_search_space,
    'VolatilityAdaptive': volatility_adaptive_search_space,
    'DualMomentum': dual_momentum_search_space,
    'RegimeAdaptive': regime_adaptive_search_space
}


def get_template_names() -> list[str]:
    """Get list of all available template names."""
    return list(TEMPLATE_SEARCH_SPACES.keys())


def get_search_space(template_name: str) -> SearchSpaceFunction:
    """
    Get search space function for a template.

    Args:
        template_name: Name of the template

    Returns:
        Search space function that takes an Optuna trial

    Raises:
        KeyError: If template name not found
    """
    if template_name not in TEMPLATE_SEARCH_SPACES:
        raise KeyError(
            f"Template '{template_name}' not found. "
            f"Available templates: {get_template_names()}"
        )
    return TEMPLATE_SEARCH_SPACES[template_name]
