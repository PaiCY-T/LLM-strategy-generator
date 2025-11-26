"""
Integration module for P1 components.

Provides helper functions and utilities to integrate Spec B P1 components
with the existing LLM strategy generation workflow.
"""

from src.integration.p1_helpers import (
    ensure_dataframe,
    prepare_factor_data,
    extract_scoring_metrics,
    calculate_batch_slippage,
    apply_liquidity_filter_simple,
    score_strategy_simple,
    combine_factor_signals,
    calculate_strategy_volatility,
    validate_p1_inputs
)

__all__ = [
    'ensure_dataframe',
    'prepare_factor_data',
    'extract_scoring_metrics',
    'calculate_batch_slippage',
    'apply_liquidity_filter_simple',
    'score_strategy_simple',
    'combine_factor_signals',
    'calculate_strategy_volatility',
    'validate_p1_inputs'
]
