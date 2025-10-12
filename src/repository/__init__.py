"""
Hall of Fame Repository System
==============================

This module provides the repository system for managing validated strategy genomes
with tier-based storage and novelty scoring.

Storage Tiers:
    - Champions: Sharpe Ratio ≥ 2.0
    - Contenders: Sharpe Ratio 1.5-2.0
    - Archive: Sharpe Ratio < 1.5

Novelty Scoring:
    - 1.0 = Completely novel
    - 0.0 = Duplicate
    - <0.2 = Rejected as near-duplicate

Usage:
    from src.repository import HallOfFameRepository, NoveltyScorer

    # Initialize repository
    repo = HallOfFameRepository()

    # Add strategy genome with novelty checking
    success, msg = repo.add_strategy(
        template_name='TurtleTemplate',
        parameters={...},
        metrics={'sharpe_ratio': 2.3, ...},
        strategy_code="close = data.get('price:收盤價')\\n..."
    )

    # Query by tier
    champions = repo.get_champions()
"""

from .hall_of_fame import HallOfFameRepository, StrategyGenome
from .novelty_scorer import NoveltyScorer, DUPLICATE_THRESHOLD

__all__ = [
    'HallOfFameRepository',
    'StrategyGenome',
    'NoveltyScorer',
    'DUPLICATE_THRESHOLD'
]
