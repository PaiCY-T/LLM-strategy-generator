"""
Tier Selection Package - Adaptive mutation tier routing.

Provides intelligent tier selection for three-tier mutation system:
- Tier 1 (Safe): YAML configuration mutations
- Tier 2 (Domain): Factor-level mutations
- Tier 3 (Advanced): AST code mutations

Main Components:
- TierSelectionManager: Main orchestrator
- RiskAssessor: Assess strategy/market/mutation risk
- TierRouter: Route mutations to appropriate tiers
- AdaptiveLearner: Learn from history and adapt thresholds

Architecture: Phase 2.0+ Factor Graph System
Task: D.4 - Adaptive Mutation Tier Selection
"""

from .risk_assessor import RiskAssessor, RiskMetrics
from .tier_router import TierRouter, MutationPlan, MutationTier
from .adaptive_learner import AdaptiveLearner, TierPerformance, MutationHistory
from .tier_selection_manager import TierSelectionManager

__all__ = [
    # Main interface
    'TierSelectionManager',

    # Core components
    'RiskAssessor',
    'TierRouter',
    'AdaptiveLearner',

    # Data classes
    'RiskMetrics',
    'MutationPlan',
    'MutationTier',
    'TierPerformance',
    'MutationHistory',
]

__version__ = '1.0.0'
