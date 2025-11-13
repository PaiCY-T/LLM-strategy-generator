"""
YAML Normalizer Module

Transforms LLM-generated YAML specifications into schema-compliant format.
Applies 5 transformation patterns to improve validation success rate from 25% to 90%+.

Task 2 of yaml-normalizer-implementation spec.
Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7

IMPORTANT DESIGN PRINCIPLE:
This normalizer TRANSFORMS existing fields but does NOT ADD missing required fields.
Exit conditions are REQUIRED by schema (strategy_schema_v1.json line 8) and must be
provided by the LLM prompt. If exit_conditions are missing, schema validation will fail.

Three-Layer Defense for Strategy Completeness:
1. Schema Enforcement: exit_conditions in required fields array (strictest)
2. Prompt Guidance: LLM prompts explicitly request exit conditions
3. Normalizer Transformation: Normalizes existing exit_conditions to schema format

Rationale: Exit logic is fundamental to any viable trading strategy - a strategy without
exit conditions cannot determine when to close positions, making it incomplete and
potentially dangerous in production.
"""

import copy
import logging
import re
from typing import Dict, Any

from src.utils.exceptions import NormalizationError

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Field alias mappings (requirement 1.2)
FIELD_ALIASES = {
    # Indicator field aliases
    "length": "period",
    "window": "period",
    "lookback": "period",
    # Entry/exit condition aliases
    "rule": "field",
    "order": "method",
    "sort": "method",
    "direction": "method",
}

# Indicator type mappings (requirement 1.4)
INDICATOR_TYPE_MAP = {
    # Lowercase to uppercase
    "rsi": "RSI",
    "sma": "SMA",
    "ema": "EMA",
    "macd": "MACD",
    "bb": "BB",
    "atr": "ATR",
    "adx": "ADX",
    "cci": "CCI",
    "mfi": "MFI",
    "obv": "OBV",
    "vwap": "VWAP",
    "stochastic": "Stochastic",
    "williams_r": "Williams_R",
    "momentum": "Momentum",
    "roc": "ROC",
    "tsi": "TSI",
    # Invalid types to valid types
    "macd_histogram": "MACD",
    "macd_signal": "MACD",
    "macd_line": "MACD",
    "bollinger_bands": "BB",
    "moving_average": "SMA",
    "exponential_moving_average": "EMA",
}

# Jinja template pattern (requirement 1.5)
JINJA_PATTERN = re.compile(r'\{\{.*?\}\}|\{%.*?%\}')


# ============================================================================
# NAME NORMALIZATION (Phase 2)
# ============================================================================

def _normalize_indicator_name(name: str) -> str:
    """
    Normalize indicator name to match schema pattern ^[a-z_][a-z0-9_]*$.

    Transformations:
    1. Convert to lowercase
    2. Replace spaces with underscores
    3. Validate result matches pattern

    Args:
        name: Raw indicator name (e.g., "SMA_Fast", "RSI 14")

    Returns:
        Normalized name (e.g., "sma_fast", "rsi_14")

    Raises:
        NormalizationError: If normalized name is invalid (empty, starts with digit,
                           contains invalid characters)

    Examples:
        >>> _normalize_indicator_name("SMA_Fast")
        "sma_fast"
        >>> _normalize_indicator_name("RSI 14")
        "rsi_14"
        >>> _normalize_indicator_name("macd")
        "macd"
        >>> _normalize_indicator_name("14_day_rsi")
        NormalizationError: Indicator name '14_day_rsi' starts with digit
    """
    # Step 1: Convert to lowercase
    name_lower = name.lower()

    # Step 2: Replace spaces with underscores
    name_normalized = name_lower.replace(' ', '_')

    # Step 3: Validate pattern - empty name
    if not name_normalized:
        raise NormalizationError(
            f"Indicator name cannot be empty (original: '{name}')"
        )

    # Step 4: Validate pattern - starts with digit
    if name_normalized[0].isdigit():
        raise NormalizationError(
            f"Indicator name '{name_normalized}' starts with digit "
            f"(invalid Python identifier)"
        )

    # Step 5: Full pattern validation (defense-in-depth)
    pattern = re.compile(r"^[a-z_][a-z0-9_]*$")
    if not pattern.match(name_normalized):
        raise NormalizationError(
            f"Normalized name '{name_normalized}' contains invalid characters. "
            f"Pattern requires ^[a-z_][a-z0-9_]*$ (original: '{name}')"
        )

    # Log transformation if changed
    if name_normalized != name:
        logger.debug(f"Normalized indicator name: '{name}' → '{name_normalized}'")

    return name_normalized


# ============================================================================
# PUBLIC API
# ============================================================================

def normalize_yaml(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize LLM-generated YAML specification to schema-compliant format.

    Applies 5 transformation patterns:
    1. Convert indicators array → object with technical_indicators
    2. Flatten nested params (params.period → period)
    3. Map field aliases (length → period, rule → field)
    4. Uppercase indicator types (sma → SMA, macd_histogram → MACD)
    5. Detect Jinja templates and raise error (unfixable)

    Args:
        raw_data: Raw YAML specification as dictionary

    Returns:
        Normalized YAML specification

    Raises:
        NormalizationError: If YAML contains Jinja templates or missing required fields

    Example:
        >>> raw = {"indicators": [{"name": "rsi", "type": "rsi", "params": {"length": 14}}]}
        >>> normalized = normalize_yaml(raw)
        >>> normalized["indicators"]["technical_indicators"][0]
        {"name": "rsi", "type": "RSI", "period": 14}
    """
    # Deep copy to ensure immutability (requirement 1.7)
    data = copy.deepcopy(raw_data)

    # Step 1: Check for Jinja templates (requirement 1.5)
    _check_for_jinja(data)

    # Step 2: Validate required fields (requirement 1.6)
    _validate_required_fields(data)

    # Step 3: Normalize indicators section (requirement 1.1)
    if "indicators" in data:
        data["indicators"] = _normalize_indicators(data["indicators"])

    # Step 4: Normalize entry_conditions (requirement 1.2)
    if "entry_conditions" in data:
        data["entry_conditions"] = _normalize_conditions(data["entry_conditions"], "entry")

    # Step 5: Normalize exit_conditions (requirement 1.2)
    if "exit_conditions" in data:
        data["exit_conditions"] = _normalize_conditions(data["exit_conditions"], "exit")

    logger.info("YAML normalization successful")
    return data


# ============================================================================
# PRIVATE TRANSFORMATION FUNCTIONS
# ============================================================================

def _check_for_jinja(data: Dict[str, Any]) -> None:
    """
    Check for Jinja templates in YAML data.

    Raises:
        NormalizationError: If Jinja templates detected
    """
    data_str = str(data)
    match = JINJA_PATTERN.search(data_str)
    if match:
        raise NormalizationError(
            f"Cannot normalize YAML with Jinja templates: {match.group()}"
        )


def _validate_required_fields(data: Dict[str, Any]) -> None:
    """
    Validate that required fields exist.

    Raises:
        NormalizationError: If required fields missing
    """
    required = ["metadata", "indicators"]
    for field in required:
        if field not in data:
            raise NormalizationError(f"Missing required field: '{field}'")


def _normalize_indicators(indicators: Any) -> Dict[str, Any]:
    """
    Normalize indicators section to structured object format.

    Handles:
    - Array format → object with technical_indicators
    - Nested params flattening (params.period → period)
    - Field alias mapping (length → period)
    - Type uppercase conversion (rsi → RSI)

    Args:
        indicators: Raw indicators (array or object)

    Returns:
        Normalized indicators object
    """
    # Case 1: Already in object format
    if isinstance(indicators, dict):
        # Normalize each technical indicator
        if "technical_indicators" in indicators:
            indicators["technical_indicators"] = [
                _normalize_single_indicator(ind)
                for ind in indicators["technical_indicators"]
            ]
        # Normalize fundamental factors (Phase 2)
        if "fundamental_factors" in indicators:
            indicators["fundamental_factors"] = [
                _normalize_single_indicator(ind)
                for ind in indicators["fundamental_factors"]
            ]
        # Normalize custom calculations (Phase 2)
        if "custom_calculations" in indicators:
            indicators["custom_calculations"] = [
                _normalize_single_indicator(ind)
                for ind in indicators["custom_calculations"]
            ]
        # Normalize volume filters (Phase 2)
        if "volume_filters" in indicators:
            indicators["volume_filters"] = [
                _normalize_single_indicator(ind)
                for ind in indicators["volume_filters"]
            ]
        return indicators

    # Case 2: Array format → convert to object
    if isinstance(indicators, list):
        normalized_list = [_normalize_single_indicator(ind) for ind in indicators]
        logger.info(f"Transformed indicators array → object (count: {len(normalized_list)})")
        return {
            "technical_indicators": normalized_list
        }

    # Case 3: Invalid format
    return indicators


def _normalize_single_indicator(indicator: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a single indicator object.

    Applies:
    - Normalize name (uppercase → lowercase, spaces → underscores)
    - Flatten params (params.period → period)
    - Map field aliases (length → period)
    - Uppercase type (rsi → RSI, macd_histogram → MACD)

    Args:
        indicator: Raw indicator dict

    Returns:
        Normalized indicator dict
    """
    normalized = copy.deepcopy(indicator)

    # Step 0: Normalize name field (Phase 2 - requirement 2.1)
    if "name" in normalized:
        normalized["name"] = _normalize_indicator_name(normalized["name"])

    # Step 1: Flatten nested params (requirement 1.3)
    if "params" in normalized:
        params = normalized.pop("params")
        for key, value in params.items():
            # Map aliases before adding to indicator
            mapped_key = FIELD_ALIASES.get(key, key)
            if mapped_key not in normalized:
                normalized[mapped_key] = value

    # Step 2: Map field aliases (requirement 1.2)
    for old_field, new_field in FIELD_ALIASES.items():
        if old_field in normalized:
            value = normalized.pop(old_field)
            if new_field not in normalized:
                normalized[new_field] = value

    # Step 3: Normalize indicator type (requirement 1.4)
    if "type" in normalized:
        original_type = normalized["type"]
        normalized_type = _normalize_indicator_type(original_type)
        if normalized_type != original_type:
            logger.info(f"Normalized indicator type: {original_type} → {normalized_type}")
        normalized["type"] = normalized_type

    return normalized


def _normalize_indicator_type(indicator_type: str) -> str:
    """
    Normalize indicator type to uppercase and map variants.

    Args:
        indicator_type: Raw indicator type string

    Returns:
        Normalized indicator type (uppercase)
    """
    # Convert to lowercase for lookup
    type_lower = indicator_type.lower()

    # Check if it's a known alias
    if type_lower in INDICATOR_TYPE_MAP:
        return INDICATOR_TYPE_MAP[type_lower]

    # Otherwise, just uppercase it
    return indicator_type.upper()


def _normalize_conditions(conditions: Any, condition_type: str) -> Any:
    """
    Normalize entry_conditions or exit_conditions.

    Handles:
    - Array of strings → object with threshold_rules
    - Field alias mapping (rule → field, order → method)

    Args:
        conditions: Raw conditions (array, object, or list)
        condition_type: "entry" or "exit" for logging

    Returns:
        Normalized conditions
    """
    # Case 1: Already in object format
    if isinstance(conditions, dict):
        # Normalize ranking_rules if present
        if "ranking_rules" in conditions:
            conditions["ranking_rules"] = [
                _normalize_ranking_rule(rule)
                for rule in conditions["ranking_rules"]
            ]
        return conditions

    # Case 2: Array format → convert to object format with threshold_rules
    # Code generator templates expect object format for compatibility
    if isinstance(conditions, list):
        # Convert array to threshold_rules object format
        logger.info(f"Transformed {condition_type}_conditions array → object with threshold_rules")
        return {
            "threshold_rules": [
                {"condition": item} if isinstance(item, str) else item
                for item in conditions
            ],
            "logical_operator": "AND"
        }

    # Case 3: Invalid format
    return conditions


def _normalize_ranking_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a ranking rule.

    Applies field alias mapping:
    - rule → field
    - order → method (with value conversion)

    Args:
        rule: Raw ranking rule dict

    Returns:
        Normalized ranking rule dict
    """
    normalized = copy.deepcopy(rule)

    # Map 'rule' → 'field'
    if "rule" in normalized:
        normalized["field"] = normalized.pop("rule")

    # Map 'order' → 'method'
    if "order" in normalized:
        order_value = normalized.pop("order")
        # Convert order direction to method
        if order_value in ["descending", "desc"]:
            normalized["method"] = "top_percent"
        elif order_value in ["ascending", "asc"]:
            normalized["method"] = "bottom_percent"
        else:
            normalized["method"] = order_value

    return normalized


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_normalization_stats(raw_data: Dict[str, Any], normalized_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Get statistics about normalization transformations applied.

    Args:
        raw_data: Original YAML data
        normalized_data: Normalized YAML data

    Returns:
        Dictionary with transformation counts
    """
    stats = {
        "indicators_array_to_object": 0,
        "params_flattened": 0,
        "field_aliases_mapped": 0,
        "types_normalized": 0,
    }

    # Check if indicators was array
    if isinstance(raw_data.get("indicators"), list):
        stats["indicators_array_to_object"] = 1

    # Count params flattening and other transformations
    # (This is a simplified version - full implementation would traverse recursively)

    return stats
