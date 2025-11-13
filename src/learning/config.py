"""
Feature flags and configuration for phased rollout of generation refactoring.

This module provides a master kill switch and phase-specific feature flags
to enable safe, gradual deployment of the strategy generation refactoring.

Environment Variables:
    ENABLE_GENERATION_REFACTORING: Master kill switch (default: false)
    PHASE1_CONFIG_ENFORCEMENT: Enable config validation (default: false)
    PHASE2_PYDANTIC_VALIDATION: Enable Pydantic models (default: false)
    PHASE3_STRATEGY_PATTERN: Enable strategy pattern (default: false)
    PHASE4_AUDIT_TRAIL: Enable audit trail (default: false)

Usage:
    from learning.config import ENABLE_GENERATION_REFACTORING

    if ENABLE_GENERATION_REFACTORING:
        # Use new implementation
        pass
    else:
        # Use legacy implementation
        pass
"""

import os
from typing import Dict, Any

# Master kill switch - controls entire refactoring rollout
ENABLE_GENERATION_REFACTORING = os.getenv(
    "ENABLE_GENERATION_REFACTORING", "false"
).lower() == "true"

# Phase 1: Configuration Validation & Enforcement
PHASE1_CONFIG_ENFORCEMENT = os.getenv(
    "PHASE1_CONFIG_ENFORCEMENT", "false"
).lower() == "true"

# Phase 2: Pydantic Validation Models
PHASE2_PYDANTIC_VALIDATION = os.getenv(
    "PHASE2_PYDANTIC_VALIDATION", "false"
).lower() == "true"

# Phase 3: Strategy Pattern Implementation
PHASE3_STRATEGY_PATTERN = os.getenv(
    "PHASE3_STRATEGY_PATTERN", "false"
).lower() == "true"

# Phase 4: Audit Trail & Observability
PHASE4_AUDIT_TRAIL = os.getenv(
    "PHASE4_AUDIT_TRAIL", "false"
).lower() == "true"


def get_feature_flags() -> Dict[str, bool]:
    """
    Get current state of all feature flags.

    Returns:
        Dictionary mapping feature flag names to their boolean values
    """
    return {
        "master_switch": ENABLE_GENERATION_REFACTORING,
        "phase1_config_enforcement": PHASE1_CONFIG_ENFORCEMENT,
        "phase2_pydantic_validation": PHASE2_PYDANTIC_VALIDATION,
        "phase3_strategy_pattern": PHASE3_STRATEGY_PATTERN,
        "phase4_audit_trail": PHASE4_AUDIT_TRAIL,
    }


def log_feature_flags(logger: Any) -> None:
    """
    Log current feature flag configuration.

    Args:
        logger: Logger instance to use for output
    """
    flags = get_feature_flags()
    logger.info("Feature flags configuration:")
    for flag_name, flag_value in flags.items():
        logger.info(f"  {flag_name}: {flag_value}")
