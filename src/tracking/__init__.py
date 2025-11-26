"""
Experiment tracking for TPE optimization and TTPT validation.

Provides SQLite/JSON backend for logging trials, TTPT results,
and strategy performance metrics.
"""

from src.tracking.experiment_tracker import ExperimentTracker
from src.tracking.schema import ExperimentSchema

__all__ = ['ExperimentTracker', 'ExperimentSchema']
