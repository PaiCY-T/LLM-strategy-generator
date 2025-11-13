"""
Test fixtures for YAML normalizer implementation.

Extracted from real LLM-generated YAML failures in:
- complete_validation_output.txt (20 iterations, 15 failures)
- QUICKWINS_VALIDATION_REPORT.md (10 iterations, 7 failures)

Error Distribution:
- 40% indicators array→object (6 cases)
- 30% field aliases (5 cases)
- 15% type case sensitivity (3 cases)
- 10% nested params (2 cases)
- 5% unfixable/Jinja (1 case)

Task 1 of yaml-normalizer-implementation spec.
Requirements: 4.1, 4.2, 4.3
"""

from typing import Dict, Any, List


# ============================================================================
# CATEGORY 1: INDICATORS ARRAY→OBJECT (40% - 6 cases)
# ============================================================================

CASE_01_INDICATORS_ARRAY = {
    "description": "indicators as flat array with params nested - iteration 2",
    "error": "indicators: [...] is not valid under any of the given schemas",
    "raw_yaml": {
        "indicators": [
            {"name": "SMA_Fast", "type": "SMA", "params": {"length": 20}},
            {"name": "SMA_Slow", "type": "SMA", "params": {"length": 50}},
            {"name": "RSI", "type": "RSI", "params": {"length": 14}}
        ]
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "sma_fast", "type": "SMA", "period": 20},
                {"name": "sma_slow", "type": "SMA", "period": 50},
                {"name": "rsi", "type": "RSI", "period": 14}
            ]
        }
    }
}

CASE_02_INDICATORS_ARRAY_WITH_SOURCE = {
    "description": "indicators array with source field - iteration 6",
    "error": "indicators: {...} is not valid under any of the given schemas",
    "raw_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "rsi_14", "type": "MACD_Histogram", "fast_period": 12, "slow_period": 26, "signal_period": 9, "source": "data.get('MACD_Hist_12_26_9')"},
                {"name": "sma_50", "type": "SMA", "period": 50, "source": "data.get('MA_50')"}
            ]
        }
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "rsi_14", "type": "MACD", "fast_period": 12, "slow_period": 26, "signal_period": 9, "source": "data.get('MACD_Hist_12_26_9')"},
                {"name": "sma_50", "type": "SMA", "period": 50, "source": "data.get('MA_50')"}
            ]
        }
    }
}

CASE_03_INDICATORS_ARRAY_SIMPLE = {
    "description": "indicators as simple array without params - iteration 12",
    "error": "indicators: [...] is not valid under any of the given schemas",
    "raw_yaml": {
        "indicators": [
            {"name": "SMA_Fast", "type": "SMA", "params": {"period": 20}},
            {"name": "SMA_Slow", "type": "SMA", "params": {"period": 50}},
            {"name": "RSI", "type": "RSI", "params": {"period": 14}}
        ]
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "sma_fast", "type": "SMA", "period": 20},
                {"name": "sma_slow", "type": "SMA", "period": 50},
                {"name": "rsi", "type": "RSI", "period": 14}
            ]
        }
    }
}

CASE_04_INDICATORS_MIXED = {
    "description": "indicators array with lowercase type - iteration 19",
    "error": "indicators: [...] is not valid under any of the given schemas",
    "raw_yaml": {
        "indicators": [
            {"name": "RSI", "type": "rsi", "params": {"period": 14}},
            {"name": "MACD", "type": "macd", "params": {"fast_period": 12, "slow_period": 26, "signal_period": 9}},
            {"name": "SMA_Fast", "type": "sma", "params": {"period": 20}}
        ]
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "rsi", "type": "RSI", "period": 14},
                {"name": "macd", "type": "MACD", "fast_period": 12, "slow_period": 26, "signal_period": 9},
                {"name": "sma_fast", "type": "SMA", "period": 20}
            ]
        }
    }
}

CASE_05_INDICATORS_LENGTH_ALIAS = {
    "description": "indicators array with 'length' instead of 'period' - iteration 20",
    "error": "indicators: [...] is not valid under any of the given schemas",
    "raw_yaml": {
        "indicators": [
            {"name": "SMA_Fast", "type": "sma", "params": {"length": 20}},
            {"name": "SMA_Slow", "type": "sma", "params": {"length": 50}},
            {"name": "RSI", "type": "rsi", "params": {"length": 14}},
            {"name": "ATR", "type": "atr", "params": {"length": 14}}
        ]
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "sma_fast", "type": "SMA", "period": 20},
                {"name": "sma_slow", "type": "SMA", "period": 50},
                {"name": "rsi", "type": "RSI", "period": 14},
                {"name": "atr", "type": "ATR", "period": 14}
            ]
        }
    }
}

CASE_06_INDICATORS_OBJECT = {
    "description": "indicators object format with invalid type - iteration 14",
    "error": "indicators: {...} is not valid under any of the given schemas",
    "raw_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "rsi_14", "type": "RSI", "period": 14, "source": "data.get('RSI_14')"},
                {"name": "macd_histogram_12_26_9", "type": "MACD_Histogram", "fast_period": 12, "slow_period": 26, "signal_period": 9, "source": "data.get('MACD_Hist_12_26_9')"}
            ]
        }
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "rsi_14", "type": "RSI", "period": 14, "source": "data.get('RSI_14')"},
                {"name": "macd_histogram_12_26_9", "type": "MACD", "fast_period": 12, "slow_period": 26, "signal_period": 9, "source": "data.get('MACD_Hist_12_26_9')"}
            ]
        }
    }
}


# ============================================================================
# CATEGORY 2: FIELD ALIASES (30% - 5 cases)
# ============================================================================

CASE_07_ENTRY_FIELD_ALIAS_RULE = {
    "description": "entry_conditions with 'rule' instead of 'field' - iteration 10",
    "error": "entry_conditions: {...} is not valid under any of the given schemas",
    "raw_yaml": {
        "entry_conditions": {
            "ranking_rules": [
                {"rule": "momentum_score", "method": "top_percent", "value": 20, "description": "Top 20% by momentum"},
                {"rule": "relative_strength_rank", "method": "top_n", "value": 20, "description": "Top 20 by relative strength"}
            ],
            "logical_operator": "AND"
        }
    },
    "expected_yaml": {
        "entry_conditions": {
            "ranking_rules": [
                {"field": "momentum_score", "method": "top_percent", "value": 20, "description": "Top 20% by momentum"},
                {"field": "relative_strength_rank", "method": "top_n", "value": 20, "description": "Top 20 by relative strength"}
            ],
            "logical_operator": "AND"
        }
    }
}

CASE_08_ENTRY_FIELD_ALIAS_ORDER = {
    "description": "ranking_rules with 'order' instead of 'method'",
    "error": "entry_conditions: {...} is not valid under any of the given schemas",
    "raw_yaml": {
        "entry_conditions": {
            "ranking_rules": [
                {"field": "momentum_score", "order": "descending", "value": 20}
            ]
        }
    },
    "expected_yaml": {
        "entry_conditions": {
            "ranking_rules": [
                {"field": "momentum_score", "method": "top_percent", "value": 20}
            ]
        }
    }
}

CASE_09_INDICATOR_LENGTH_TO_PERIOD = {
    "description": "technical_indicators with 'length' instead of 'period'",
    "error": "Additional property 'length' not allowed",
    "raw_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "rsi", "type": "RSI", "length": 14}
            ]
        }
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "rsi", "type": "RSI", "period": 14}
            ]
        }
    }
}

CASE_10_ENTRY_CONDITIONS_ARRAY_STRING = {
    "description": "entry_conditions as array of plain strings - iteration 13",
    "error": "entry_conditions: [...] is not valid under any of the given schemas",
    "raw_yaml": {
        "entry_conditions": [
            "moving_average_short > moving_average_long",
            "rsi > 50"
        ]
    },
    "expected_yaml": {
        "entry_conditions": {
            "threshold_rules": [
                {"condition": "moving_average_short > moving_average_long"},
                {"condition": "rsi > 50"}
            ],
            "logical_operator": "AND"
        }
    }
}

CASE_11_PARAMS_NESTED = {
    "description": "indicators with nested params object containing 'length'",
    "error": "Additional properties not allowed",
    "raw_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "sma", "type": "SMA", "params": {"length": 50}}
            ]
        }
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "sma", "type": "SMA", "period": 50}
            ]
        }
    }
}


# ============================================================================
# CATEGORY 3: TYPE CASE SENSITIVITY (15% - 3 cases)
# ============================================================================

CASE_12_TYPE_LOWERCASE = {
    "description": "indicator type in lowercase - iteration 19",
    "error": "'rsi' is not one of ['RSI', 'MACD', 'BB', ...]",
    "raw_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "rsi", "type": "rsi", "period": 14},
                {"name": "sma", "type": "sma", "period": 50}
            ]
        }
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "rsi", "type": "RSI", "period": 14},
                {"name": "sma", "type": "SMA", "period": 50}
            ]
        }
    }
}

CASE_13_TYPE_MACD_HISTOGRAM = {
    "description": "MACD_Histogram should be MACD - iteration 6",
    "error": "'MACD_Histogram' is not one of ['RSI', 'MACD', 'BB', ...]",
    "raw_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "macd_hist", "type": "MACD_Histogram", "fast_period": 12, "slow_period": 26, "signal_period": 9}
            ]
        }
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "macd_hist", "type": "MACD", "fast_period": 12, "slow_period": 26, "signal_period": 9}
            ]
        }
    }
}

CASE_14_TYPE_MACD_SIGNAL = {
    "description": "MACD_Signal should be MACD - iteration 11",
    "error": "'MACD_Signal' is not one of ['RSI', 'MACD', 'BB', ...]",
    "raw_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "macd_signal", "type": "MACD_Signal", "fast_period": 12, "slow_period": 26, "signal_period": 9}
            ]
        }
    },
    "expected_yaml": {
        "indicators": {
            "technical_indicators": [
                {"name": "macd_signal", "type": "MACD", "fast_period": 12, "slow_period": 26, "signal_period": 9}
            ]
        }
    }
}


# ============================================================================
# CATEGORY 4: UNFIXABLE/JINJA TEMPLATES (5% - 1 case)
# ============================================================================

CASE_15_JINJA_TEMPLATES = {
    "description": "Jinja templates in params - iteration 9, 11 (unfixable)",
    "error": "Jinja templates detected - cannot normalize",
    "raw_yaml": {
        "indicators": [
            {"name": "MACD", "type": "MACD", "params": {"fast_period": "{{ parameters.fast_period }}", "slow_period": "{{ parameters.slow_period }}"}},
            {"name": "RSI", "type": "RSI", "params": {"period": "{{ parameters.rsi_period }}"}}
        ]
    },
    "expected_yaml": None,  # Should raise NormalizationError
    "should_fail": True
}


# ============================================================================
# ALL TEST CASES REGISTRY
# ============================================================================

ALL_CASES: List[Dict[str, Any]] = [
    CASE_01_INDICATORS_ARRAY,
    CASE_02_INDICATORS_ARRAY_WITH_SOURCE,
    CASE_03_INDICATORS_ARRAY_SIMPLE,
    CASE_04_INDICATORS_MIXED,
    CASE_05_INDICATORS_LENGTH_ALIAS,
    CASE_06_INDICATORS_OBJECT,
    CASE_07_ENTRY_FIELD_ALIAS_RULE,
    CASE_08_ENTRY_FIELD_ALIAS_ORDER,
    CASE_09_INDICATOR_LENGTH_TO_PERIOD,
    CASE_10_ENTRY_CONDITIONS_ARRAY_STRING,
    CASE_11_PARAMS_NESTED,
    CASE_12_TYPE_LOWERCASE,
    CASE_13_TYPE_MACD_HISTOGRAM,
    CASE_14_TYPE_MACD_SIGNAL,
    CASE_15_JINJA_TEMPLATES,
]

# Category-specific subsets for targeted testing
INDICATORS_ARRAY_CASES = [CASE_01_INDICATORS_ARRAY, CASE_02_INDICATORS_ARRAY_WITH_SOURCE, CASE_03_INDICATORS_ARRAY_SIMPLE, CASE_04_INDICATORS_MIXED, CASE_05_INDICATORS_LENGTH_ALIAS, CASE_06_INDICATORS_OBJECT]
FIELD_ALIAS_CASES = [CASE_07_ENTRY_FIELD_ALIAS_RULE, CASE_08_ENTRY_FIELD_ALIAS_ORDER, CASE_09_INDICATOR_LENGTH_TO_PERIOD, CASE_10_ENTRY_CONDITIONS_ARRAY_STRING, CASE_11_PARAMS_NESTED]
TYPE_CASE_CASES = [CASE_12_TYPE_LOWERCASE, CASE_13_TYPE_MACD_HISTOGRAM, CASE_14_TYPE_MACD_SIGNAL]
UNFIXABLE_CASES = [CASE_15_JINJA_TEMPLATES]


def get_all_cases() -> List[Dict[str, Any]]:
    """Get all 15 test cases."""
    return ALL_CASES


def get_cases_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Get test cases by category.

    Args:
        category: One of 'indicators_array', 'field_alias', 'type_case', 'unfixable'

    Returns:
        List of test cases for that category
    """
    categories = {
        "indicators_array": INDICATORS_ARRAY_CASES,
        "field_alias": FIELD_ALIAS_CASES,
        "type_case": TYPE_CASE_CASES,
        "unfixable": UNFIXABLE_CASES,
    }
    return categories.get(category, [])


def get_fixable_cases() -> List[Dict[str, Any]]:
    """Get all cases that should be fixable by the normalizer (14 cases)."""
    return [case for case in ALL_CASES if not case.get("should_fail", False)]
