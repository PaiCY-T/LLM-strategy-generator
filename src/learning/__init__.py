"""
Phase 3 Learning System Components.

This package provides the refactored learning iteration system, extracting
monolithic autonomous_loop.py into modular, testable components.

Components:
- ConfigManager: Singleton configuration manager for centralized config access (Task 1.1)
- IterationHistory: JSONL-based iteration record persistence
- FeedbackGenerator: LLM feedback generation from history
- LLMClient: Unified LLM API wrapper (Gemini + OpenRouter)
- ChampionTracker: Best strategy tracking with staleness detection
- IterationExecutor: Single iteration execution orchestrator
- LearningLoop: Main learning loop orchestrator

Usage:
    >>> from src.learning import ConfigManager, IterationHistory, ChampionTracker
    >>> config_manager = ConfigManager.get_instance()
    >>> config = config_manager.load_config()
    >>> history = IterationHistory("artifacts/data/innovations.jsonl")
    >>> champion = ChampionTracker("artifacts/data/champion_strategy.json")
"""

from .config_manager import ConfigManager
from .iteration_history import IterationHistory, IterationRecord
from .champion_tracker import ChampionTracker, ChampionStrategy

__all__ = [
    "ConfigManager",
    "IterationHistory",
    "IterationRecord",
    "ChampionTracker",
    "ChampionStrategy",
]
