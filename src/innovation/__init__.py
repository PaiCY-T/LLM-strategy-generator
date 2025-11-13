"""
LLM Innovation Capability Module

This module implements the innovation layer for the Factor Graph System,
enabling LLM to create novel trading strategy factors beyond the fixed pool
of 13 predefined factors.

Key Components:
- DataGuardian: Cryptographic protection for hold-out set
- InnovationValidator: 7-layer validation pipeline
- InnovationRepository: JSONL-based knowledge base
- BaselineMetrics: Immutable baseline metrics framework
- StatisticalValidator: Statistical significance testing

Executive Approval: 2025-10-23 (Opus 4.1)
Confidence: 8/10
"""

__version__ = "0.1.0"
__author__ = "User + Claude Code"
__status__ = "Pre-Implementation Audit"

from .data_guardian import DataGuardian, SecurityError
from .baseline_metrics import BaselineMetrics, StatisticalValidator
from .llm_config import LLMConfig

__all__ = [
    'DataGuardian',
    'SecurityError',
    'BaselineMetrics',
    'StatisticalValidator',
    'LLMConfig',
]
