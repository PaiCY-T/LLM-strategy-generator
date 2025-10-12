"""
Template System for Strategy Generation
========================================

This module provides a template-based system for generating trading strategies
with parameterized patterns, data caching, and validation.

Available Templates:
    - TurtleTemplate: 6-layer AND filtering with revenue weighting
    - MastiffTemplate: Contrarian reversal with low-volume selection
    - FactorTemplate: Single-factor cross-sectional ranking
    - MomentumTemplate: Momentum + revenue catalyst strategy

Usage:
    from src.templates import BaseTemplate, DataCache, TurtleTemplate

    # Create template instance
    template = TurtleTemplate()

    # Get default parameters
    params = template.get_default_params()

    # Generate strategy
    report, metrics = template.generate_strategy(params)

    # Access shared cache
    cache = DataCache.get_instance()
    cache.preload_all()
"""

from .base_template import BaseTemplate
from .data_cache import DataCache, get_cached_data
from .turtle_template import TurtleTemplate
from .mastiff_template import MastiffTemplate
from .factor_template import FactorTemplate
from .momentum_template import MomentumTemplate

__all__ = [
    'BaseTemplate',
    'DataCache',
    'get_cached_data',
    'TurtleTemplate',
    'MastiffTemplate',
    'FactorTemplate',
    'MomentumTemplate'
]
