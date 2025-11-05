"""
Template Stats Tracker - Performance Tracking and LLM Recommendations
======================================================================

Tracks template performance metrics and provides intelligent recommendations for LLM prompts.
Complements the existing TemplateFeedbackIntegrator with persistence and analytics.

Features:
    - Per-template metric tracking (attempts, successes, Sharpe distribution)
    - JSON persistence for template statistics
    - LLM prompt recommendations based on success rates
    - Integration with existing feedback system

Storage Format (artifacts/data/template_stats.json):
    {
        "TurtleTemplate": {
            "total_attempts": 45,
            "successful_strategies": 36,
            "avg_sharpe": 1.85,
            "sharpe_distribution": [0.5, 1.2, 1.8, 2.1, 2.5, ...],
            "last_updated": "2025-10-16T10:30:00"
        }
    }

Usage:
    from src.feedback import TemplateStatsTracker

    tracker = TemplateStatsTracker()

    # Update template statistics after backtest
    tracker.update_template_stats(
        template_name='TurtleTemplate',
        sharpe_ratio=1.85,
        is_successful=True
    )

    # Get LLM prompt recommendations
    recommendations = tracker.get_template_recommendations(top_n=2)
    print(recommendations)
    # Output: "Focus on TurtleTemplate which has 80.0% success and avg Sharpe 1.85"

Requirements:
    - Task 36: Base class with storage infrastructure
    - Task 37: update_template_stats() implementation
    - Task 38: get_template_recommendations() implementation
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class TemplateStats:
    """
    Statistics for a single template.

    Attributes:
        total_attempts: Total number of strategies generated with this template
        successful_strategies: Number of strategies that passed validation
        avg_sharpe: Average Sharpe ratio across all strategies
        sharpe_distribution: List of all Sharpe ratios for distribution analysis
        last_updated: ISO timestamp of last update
    """
    total_attempts: int = 0
    successful_strategies: int = 0
    avg_sharpe: float = 0.0
    sharpe_distribution: List[float] = None
    last_updated: str = ""

    def __post_init__(self):
        """Initialize mutable default values."""
        if self.sharpe_distribution is None:
            self.sharpe_distribution = []
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_strategies / self.total_attempts) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TemplateStats':
        """Create from dictionary loaded from JSON."""
        return cls(**data)


class TemplateStatsTracker:
    """
    Template statistics tracker with performance tracking and LLM recommendations.

    Complements the existing feedback system with persistent storage and analytics.
    Tracks per-template metrics and provides intelligent LLM prompt suggestions.

    Storage:
        - File: artifacts/data/template_stats.json
        - Format: JSON dictionary keyed by template name
        - Auto-creates file if missing
        - Thread-safe file operations

    Attributes:
        storage_path: Path to template_stats.json file
        template_stats: In-memory cache of template statistics
        logger: Python logger for tracking operations

    Example:
        >>> tracker = TemplateStatsTracker()
        >>> tracker.update_template_stats('TurtleTemplate', 1.85, True)
        >>> recommendations = tracker.get_template_recommendations(top_n=2)
        >>> print(recommendations)
    """

    # Default storage path
    DEFAULT_STORAGE_PATH = Path('artifacts/data/template_stats.json')

    # Success threshold for LLM recommendations (minimum Sharpe)
    MIN_SHARPE_THRESHOLD = 0.5

    # Minimum attempts before including in recommendations
    MIN_ATTEMPTS_THRESHOLD = 3

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize template stats tracker.

        Args:
            storage_path: Optional custom path for template_stats.json
            logger: Optional logger for tracking operations
        """
        self.storage_path = storage_path or self.DEFAULT_STORAGE_PATH
        self.logger = logger or logging.getLogger(__name__)

        # In-memory cache of template statistics
        self.template_stats: Dict[str, TemplateStats] = {}

        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing statistics from disk
        self._load_template_stats()

        self.logger.info(
            f"TemplateStatsTracker initialized with storage: {self.storage_path}"
        )

    def _load_template_stats(self) -> None:
        """
        Load template statistics from JSON file.

        Creates empty file if it doesn't exist.
        Handles JSON parsing errors gracefully.
        """
        if not self.storage_path.exists():
            self.logger.info(
                f"No existing template stats found at {self.storage_path}. "
                "Starting with empty statistics."
            )
            self.template_stats = {}
            self._save_template_stats()  # Create empty file
            return

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert dictionary to TemplateStats objects
            self.template_stats = {
                template_name: TemplateStats.from_dict(stats_dict)
                for template_name, stats_dict in data.items()
            }

            self.logger.info(
                f"Loaded template stats for {len(self.template_stats)} templates"
            )

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse template stats JSON: {e}")
            self.logger.warning("Starting with empty template statistics")
            self.template_stats = {}

        except Exception as e:
            self.logger.error(f"Error loading template stats: {e}")
            self.template_stats = {}

    def _save_template_stats(self) -> None:
        """
        Save template statistics to JSON file.

        Writes atomically to prevent corruption.
        Pretty-prints JSON for human readability.
        """
        try:
            # Convert TemplateStats objects to dictionaries
            data = {
                template_name: stats.to_dict()
                for template_name, stats in self.template_stats.items()
            }

            # Write atomically using temporary file
            temp_path = self.storage_path.with_suffix('.tmp')

            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(self.storage_path)

            self.logger.debug(
                f"Saved template stats for {len(self.template_stats)} templates"
            )

        except Exception as e:
            self.logger.error(f"Error saving template stats: {e}")
            raise

    def update_template_stats(
        self,
        template_name: str,
        sharpe_ratio: float,
        is_successful: bool = True
    ) -> None:
        """
        Update template statistics after strategy generation.

        Tracks total attempts, successful strategies, and Sharpe distribution.
        Automatically recalculates average Sharpe and success rate.
        Persists changes to disk immediately.

        Args:
            template_name: Template name (e.g., 'TurtleTemplate')
            sharpe_ratio: Strategy Sharpe ratio from backtest
            is_successful: Whether strategy passed validation (default: True)

        Example:
            >>> integrator.update_template_stats('TurtleTemplate', 1.85, True)
            >>> integrator.update_template_stats('MastiffTemplate', 0.3, False)

        Requirements:
            - Task 37: Track success rates and Sharpe distribution
        """
        # Initialize template stats if first time
        if template_name not in self.template_stats:
            self.template_stats[template_name] = TemplateStats()
            self.logger.info(f"Initialized stats tracking for {template_name}")

        stats = self.template_stats[template_name]

        # Update counters
        stats.total_attempts += 1

        if is_successful:
            stats.successful_strategies += 1

        # Add to Sharpe distribution
        stats.sharpe_distribution.append(sharpe_ratio)

        # Recalculate average Sharpe
        stats.avg_sharpe = sum(stats.sharpe_distribution) / len(stats.sharpe_distribution)

        # Update timestamp
        stats.last_updated = datetime.now().isoformat()

        # Log the update
        self.logger.info(
            f"Updated {template_name} stats: "
            f"attempts={stats.total_attempts}, "
            f"success_rate={stats.success_rate:.1f}%, "
            f"avg_sharpe={stats.avg_sharpe:.2f}, "
            f"is_successful={is_successful}"
        )

        # Persist to disk
        self._save_template_stats()

    def get_template_recommendations(
        self,
        top_n: int = 3,
        min_attempts: Optional[int] = None,
        min_sharpe: Optional[float] = None
    ) -> str:
        """
        Generate LLM prompt recommendations based on template performance.

        Sorts templates by composite score: success_rate * avg_sharpe DESC
        Filters out templates with insufficient data or poor performance.
        Returns formatted string for direct inclusion in LLM prompts.

        Algorithm:
            1. Filter templates by min_attempts threshold (default: 3)
            2. Filter templates by min_sharpe threshold (default: 0.5)
            3. Calculate composite score: success_rate * avg_sharpe
            4. Sort by composite score descending
            5. Take top N templates
            6. Format as LLM-friendly recommendation string

        Args:
            top_n: Number of top templates to recommend (default: 3)
            min_attempts: Minimum attempts threshold (default: MIN_ATTEMPTS_THRESHOLD)
            min_sharpe: Minimum Sharpe threshold (default: MIN_SHARPE_THRESHOLD)

        Returns:
            Formatted recommendation string for LLM prompts

        Example:
            >>> recommendations = integrator.get_template_recommendations(top_n=2)
            >>> print(recommendations)
            Focus on TurtleTemplate which has 80.0% success and avg Sharpe 1.85.
            Consider MastiffTemplate which has 65.0% success and avg Sharpe 1.52.

        Requirements:
            - Task 38: LLM prompt enhancement with template recommendations
        """
        # Apply default thresholds
        min_attempts = min_attempts or self.MIN_ATTEMPTS_THRESHOLD
        min_sharpe = min_sharpe or self.MIN_SHARPE_THRESHOLD

        # Filter templates by thresholds
        eligible_templates = []

        for template_name, stats in self.template_stats.items():
            # Skip templates with insufficient data
            if stats.total_attempts < min_attempts:
                self.logger.debug(
                    f"Skipping {template_name}: insufficient attempts "
                    f"({stats.total_attempts} < {min_attempts})"
                )
                continue

            # Skip templates with poor performance
            if stats.avg_sharpe < min_sharpe:
                self.logger.debug(
                    f"Skipping {template_name}: low Sharpe "
                    f"({stats.avg_sharpe:.2f} < {min_sharpe})"
                )
                continue

            # Calculate composite score
            composite_score = (stats.success_rate / 100) * stats.avg_sharpe

            eligible_templates.append({
                'name': template_name,
                'stats': stats,
                'composite_score': composite_score
            })

        # Check if any templates are eligible
        if not eligible_templates:
            self.logger.warning(
                "No templates meet recommendation criteria. "
                f"min_attempts={min_attempts}, min_sharpe={min_sharpe}"
            )
            return (
                "No templates have sufficient data for recommendations yet. "
                "Continue exploring different templates."
            )

        # Sort by composite score descending
        eligible_templates.sort(key=lambda x: x['composite_score'], reverse=True)

        # Take top N
        top_templates = eligible_templates[:top_n]

        # Format recommendations for LLM
        recommendations = []

        for i, template_info in enumerate(top_templates):
            template_name = template_info['name']
            stats = template_info['stats']

            if i == 0:
                # Primary recommendation
                recommendation = (
                    f"Focus on {template_name} which has "
                    f"{stats.success_rate:.1f}% success and "
                    f"avg Sharpe {stats.avg_sharpe:.2f}"
                )
            else:
                # Secondary recommendations
                recommendation = (
                    f"Consider {template_name} which has "
                    f"{stats.success_rate:.1f}% success and "
                    f"avg Sharpe {stats.avg_sharpe:.2f}"
                )

            recommendations.append(recommendation)

        # Join with periods and newlines
        result = ". ".join(recommendations) + "."

        self.logger.info(
            f"Generated recommendations for top {len(top_templates)} templates"
        )

        return result

    def get_template_stats(self, template_name: str) -> Optional[TemplateStats]:
        """
        Get statistics for a specific template.

        Args:
            template_name: Template name to query

        Returns:
            TemplateStats object or None if template not found

        Example:
            >>> stats = integrator.get_template_stats('TurtleTemplate')
            >>> print(f"Success rate: {stats.success_rate:.1f}%")
        """
        return self.template_stats.get(template_name)

    def get_all_template_stats(self) -> Dict[str, TemplateStats]:
        """
        Get statistics for all templates.

        Returns:
            Dictionary mapping template names to TemplateStats objects

        Example:
            >>> all_stats = integrator.get_all_template_stats()
            >>> for name, stats in all_stats.items():
            ...     print(f"{name}: {stats.success_rate:.1f}%")
        """
        return self.template_stats.copy()

    def reset_template_stats(self, template_name: Optional[str] = None) -> None:
        """
        Reset statistics for a template or all templates.

        Args:
            template_name: Optional template name to reset. If None, resets all.

        Example:
            >>> integrator.reset_template_stats('TurtleTemplate')  # Reset one
            >>> integrator.reset_template_stats()  # Reset all
        """
        if template_name:
            if template_name in self.template_stats:
                del self.template_stats[template_name]
                self.logger.info(f"Reset stats for {template_name}")
            else:
                self.logger.warning(f"Template {template_name} not found in stats")
        else:
            self.template_stats = {}
            self.logger.info("Reset all template stats")

        self._save_template_stats()

    def get_stats_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics across all templates.

        Returns:
            Dictionary with summary statistics:
                - total_templates: Number of templates tracked
                - total_attempts: Total strategies generated
                - total_successful: Total successful strategies
                - overall_success_rate: Success rate across all templates
                - avg_sharpe_all: Average Sharpe across all templates
                - best_template: Template with highest composite score

        Example:
            >>> summary = integrator.get_stats_summary()
            >>> print(f"Best template: {summary['best_template']}")
        """
        if not self.template_stats:
            return {
                'total_templates': 0,
                'total_attempts': 0,
                'total_successful': 0,
                'overall_success_rate': 0.0,
                'avg_sharpe_all': 0.0,
                'best_template': None
            }

        total_attempts = sum(s.total_attempts for s in self.template_stats.values())
        total_successful = sum(s.successful_strategies for s in self.template_stats.values())

        # Calculate overall success rate
        overall_success_rate = (
            (total_successful / total_attempts * 100) if total_attempts > 0 else 0.0
        )

        # Calculate average Sharpe across all attempts
        all_sharpes = []
        for stats in self.template_stats.values():
            all_sharpes.extend(stats.sharpe_distribution)

        avg_sharpe_all = sum(all_sharpes) / len(all_sharpes) if all_sharpes else 0.0

        # Find best template by composite score
        best_template = None
        best_score = 0.0

        for template_name, stats in self.template_stats.items():
            if stats.total_attempts >= self.MIN_ATTEMPTS_THRESHOLD:
                composite_score = (stats.success_rate / 100) * stats.avg_sharpe
                if composite_score > best_score:
                    best_score = composite_score
                    best_template = template_name

        return {
            'total_templates': len(self.template_stats),
            'total_attempts': total_attempts,
            'total_successful': total_successful,
            'overall_success_rate': round(overall_success_rate, 2),
            'avg_sharpe_all': round(avg_sharpe_all, 2),
            'best_template': best_template
        }
