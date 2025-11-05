"""
Factor Graph System - Phase 2.0+ (Unified Factor Graph Architecture)

This module implements the Factor Graph architecture for the finlab evolutionary strategy system.
Strategies are represented as Directed Acyclic Graphs (DAGs) of atomic Factors instead of parameter dictionaries.

Core Components:
- Factor: Atomic strategy component (inputs → logic → outputs)
- Strategy: DAG composition of Factors with dependency tracking
- Mutations: Tier 2 structural mutations (add_factor, remove_factor, replace_factor)
- Three-Tier Mutation System: Safe (YAML) → Domain-Specific (Factor Ops) → Advanced (AST)

Architecture Decision: Phase 2.0+ Fusion (2025-10-20)
- Integrates Phase 1 exit mutations as Factor library
- Integrates Phase 2a YAML config as Tier 1 safe entry point
- Implements Phase 2.0 structural mutations as Tier 3 advanced capabilities
"""

from .factor_category import FactorCategory
from .factor import Factor
from .strategy import Strategy
from .mutations import add_factor, remove_factor, replace_factor

__all__ = [
    "FactorCategory",
    "Factor",
    "Strategy",
    "add_factor",
    "remove_factor",
    "replace_factor",
]

__version__ = "2.0.0"
