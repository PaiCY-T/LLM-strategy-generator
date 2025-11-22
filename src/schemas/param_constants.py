"""
Centralized Parameter Constants for Strategy Generation

This module provides a single source of truth for parameter constraints
used across the JSON Parameter Output system.

DRY Principle: This eliminates duplication in:
- src/schemas/strategy_params.py (Pydantic Literal types)
- src/generators/json_prompt_builder.py (PARAM_CONSTRAINTS)
- src/feedback/structured_error.py (PARAM_ALLOWED_VALUES)
"""

from typing import Dict, List, Any, Union

# Single source of truth for all parameter constraints
PARAM_ALLOWED_VALUES: Dict[str, List[Union[int, float, str]]] = {
    "momentum_period": [5, 10, 20, 30],
    "ma_periods": [20, 60, 90, 120],
    "catalyst_type": ["revenue", "earnings"],
    "catalyst_lookback": [2, 3, 4, 6],
    "n_stocks": [5, 10, 15, 20],
    "stop_loss": [0.08, 0.10, 0.12, 0.15],
    "resample": ["W", "M"],
    "resample_offset": [0, 1, 2, 3, 4]
}

# Parameter descriptions for prompt building
PARAM_DESCRIPTIONS: Dict[str, str] = {
    "momentum_period": "Momentum lookback period in days",
    "ma_periods": "Moving average period for trend confirmation",
    "catalyst_type": "Fundamental catalyst type",
    "catalyst_lookback": "Catalyst lookback window in months",
    "n_stocks": "Number of stocks in portfolio",
    "stop_loss": "Stop loss percentage",
    "resample": "Rebalancing frequency (W=Weekly, M=Monthly)",
    "resample_offset": "Rebalancing day offset"
}

# Parameter type mapping for prompt building
PARAM_TYPES: Dict[str, str] = {
    "momentum_period": "int",
    "ma_periods": "int",
    "catalyst_type": "string",
    "catalyst_lookback": "int",
    "n_stocks": "int",
    "stop_loss": "float",
    "resample": "string",
    "resample_offset": "int"
}


def get_param_constraints() -> Dict[str, Dict[str, Any]]:
    """
    Get parameter constraints in the format used by JsonPromptBuilder.

    Returns:
        Dict with type, allowed values, and description for each parameter
    """
    constraints = {}
    for param_name, allowed in PARAM_ALLOWED_VALUES.items():
        constraints[param_name] = {
            "type": PARAM_TYPES[param_name],
            "allowed": allowed,
            "description": PARAM_DESCRIPTIONS[param_name]
        }
    return constraints
