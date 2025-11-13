"""
Template Usage Analytics
=========================

Template selection tracking and success rate analytics.
Persistent storage in JSON format for historical analysis.

Features:
    - Template usage tracking
    - Success rate calculation
    - Performance statistics
    - Trend analysis
    - JSON persistence
    - Historical reporting

Usage:
    from src.feedback.template_analytics import TemplateAnalytics

    analytics = TemplateAnalytics(storage_path='template_analytics.json')

    # Track template usage
    analytics.record_template_usage(
        iteration=5,
        template_name='TurtleTemplate',
        sharpe_ratio=0.8,
        validation_passed=True
    )

    # Get statistics
    stats = analytics.get_template_statistics('TurtleTemplate')
    print(f"Success rate: {stats['success_rate']:.1%}")

Requirements:
    - Analytics requirement: Track template selections and success rates
    - Persistent storage requirement: JSON historical tracking
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import logging
import os
import tempfile
from pathlib import Path


@dataclass
class TemplateUsageRecord:
    """
    Single template usage record.

    Attributes:
        iteration: Iteration number
        timestamp: ISO timestamp string
        template_name: Template used
        sharpe_ratio: Resulting Sharpe ratio
        validation_passed: True if validation passed
        exploration_mode: True if exploration iteration
        champion_based: True if champion-based parameters
        match_score: Template match score
    """
    iteration: int
    timestamp: str
    template_name: str
    sharpe_ratio: float = 0.0
    validation_passed: bool = False
    exploration_mode: bool = False
    champion_based: bool = False
    match_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class TemplateAnalytics:
    """
    Template usage analytics and tracking system.

    Tracks template selections, calculates success rates, analyzes trends,
    and provides persistent JSON storage for historical analysis.

    Success Criteria:
        - Validation passed: True/False
        - Sharpe >= 1.0: Considered successful
        - Combination: Both validation and performance

    Metrics Tracked:
        - Total usage count per template
        - Success rate (validation + performance)
        - Average Sharpe ratio
        - Best/worst performance
        - Exploration vs. exploitation ratio
        - Champion-based success rate

    Example:
        >>> analytics = TemplateAnalytics('analytics.json')
        >>> analytics.record_template_usage(
        ...     iteration=5,
        ...     template_name='TurtleTemplate',
        ...     sharpe_ratio=1.8,
        ...     validation_passed=True
        ... )
        >>> stats = analytics.get_template_statistics('TurtleTemplate')
        >>> print(stats['success_rate'])
        0.85  # 85% success rate

    Attributes:
        storage_path: Path to JSON storage file
        usage_records: List of TemplateUsageRecord objects
        logger: Python logger
    """

    # Success thresholds
    MIN_SHARPE_SUCCESS = 1.0  # Minimum Sharpe for success
    MIN_RECORDS_FOR_STATS = 3  # Minimum records for reliable statistics

    def __init__(
        self,
        storage_path: str = 'artifacts/data/template_analytics.json',
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize template analytics.

        Args:
            storage_path: Path to JSON storage file (default: artifacts/data/template_analytics.json)
            logger: Optional logger
        """
        self.storage_path = Path(storage_path)
        self.logger = logger or logging.getLogger(__name__)

        # Ensure parent directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing records
        self.usage_records: List[TemplateUsageRecord] = []
        self._load_from_storage()

        self.logger.info(
            f"TemplateAnalytics initialized: "
            f"{len(self.usage_records)} records loaded from {storage_path}"
        )

    def record_template_usage(
        self,
        iteration: int,
        template_name: str,
        sharpe_ratio: float = 0.0,
        validation_passed: bool = False,
        exploration_mode: bool = False,
        champion_based: bool = False,
        match_score: float = 0.0
    ) -> None:
        """
        Record a template usage event.

        Args:
            iteration: Iteration number
            template_name: Template used
            sharpe_ratio: Resulting Sharpe ratio
            validation_passed: True if validation passed
            exploration_mode: True if exploration mode
            champion_based: True if champion-based parameters
            match_score: Template match score

        Example:
            >>> analytics.record_template_usage(
            ...     iteration=10,
            ...     template_name='MastiffTemplate',
            ...     sharpe_ratio=1.5,
            ...     validation_passed=True,
            ...     exploration_mode=True
            ... )
        """
        record = TemplateUsageRecord(
            iteration=iteration,
            timestamp=datetime.now().isoformat(),
            template_name=template_name,
            sharpe_ratio=sharpe_ratio,
            validation_passed=validation_passed,
            exploration_mode=exploration_mode,
            champion_based=champion_based,
            match_score=match_score
        )

        self.usage_records.append(record)

        self.logger.info(
            f"Recorded usage: iteration={iteration}, template={template_name}, "
            f"sharpe={sharpe_ratio:.2f}, validation={validation_passed}"
        )

        # Save to storage
        self._save_to_storage()

    def track_template_usage(
        self,
        template_name: str,
        iteration_num: int,
        sharpe_ratio: float,
        validation_passed: bool = False,
        exploration_mode: bool = False,
        champion_based: bool = False,
        match_score: float = 0.0
    ) -> None:
        """
        Track template usage (alias for record_template_usage with task-specific signature).

        Args:
            template_name: Template used
            iteration_num: Iteration number
            sharpe_ratio: Resulting Sharpe ratio
            validation_passed: True if validation passed
            exploration_mode: True if exploration mode
            champion_based: True if champion-based parameters
            match_score: Template match score

        Example:
            >>> analytics.track_template_usage(
            ...     template_name='TurtleTemplate',
            ...     iteration_num=10,
            ...     sharpe_ratio=1.5
            ... )
        """
        self.record_template_usage(
            iteration=iteration_num,
            template_name=template_name,
            sharpe_ratio=sharpe_ratio,
            validation_passed=validation_passed,
            exploration_mode=exploration_mode,
            champion_based=champion_based,
            match_score=match_score
        )

    def calculate_template_success_rate(
        self,
        template_name: str,
        min_sharpe: float = 1.5
    ) -> Dict[str, Any]:
        """
        Calculate success rate for a specific template.

        Success is defined as strategies that pass validation AND meet minimum Sharpe threshold.

        Args:
            template_name: Template name to analyze
            min_sharpe: Minimum Sharpe ratio for success (default: 1.5)

        Returns:
            Dictionary with:
                - total_usage: Total times template was used
                - successful_strategies: Count of successful strategies
                - success_rate: Percentage (0.0-1.0)
                - avg_sharpe: Average Sharpe ratio
                - avg_sharpe_successful: Average Sharpe of successful strategies only

        Example:
            >>> result = analytics.calculate_template_success_rate('TurtleTemplate', min_sharpe=1.5)
            >>> print(f"Success rate: {result['success_rate']:.1%}")
            Success rate: 80.0%
        """
        # Filter records for this template
        template_records = [
            r for r in self.usage_records
            if r.template_name == template_name
        ]

        total_usage = len(template_records)

        if total_usage == 0:
            return {
                'template_name': template_name,
                'total_usage': 0,
                'successful_strategies': 0,
                'success_rate': 0.0,
                'avg_sharpe': 0.0,
                'avg_sharpe_successful': 0.0,
                'min_sharpe_threshold': min_sharpe
            }

        # Success: validation passed AND Sharpe >= threshold
        successful_records = [
            r for r in template_records
            if r.validation_passed and r.sharpe_ratio >= min_sharpe
        ]
        successful_strategies = len(successful_records)
        success_rate = successful_strategies / total_usage if total_usage > 0 else 0.0

        # Calculate average Sharpe ratios
        all_sharpe = [r.sharpe_ratio for r in template_records]
        avg_sharpe = sum(all_sharpe) / len(all_sharpe) if all_sharpe else 0.0

        successful_sharpe = [r.sharpe_ratio for r in successful_records]
        avg_sharpe_successful = sum(successful_sharpe) / len(successful_sharpe) if successful_sharpe else 0.0

        return {
            'template_name': template_name,
            'total_usage': total_usage,
            'successful_strategies': successful_strategies,
            'success_rate': round(success_rate, 3),
            'avg_sharpe': round(avg_sharpe, 3),
            'avg_sharpe_successful': round(avg_sharpe_successful, 3),
            'min_sharpe_threshold': min_sharpe
        }

    def get_template_statistics(
        self,
        template_name: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a template.

        Args:
            template_name: Template name

        Returns:
            Dictionary with template statistics

        Example:
            >>> stats = analytics.get_template_statistics('TurtleTemplate')
            >>> print(stats)
            {
                'total_usage': 15,
                'success_rate': 0.80,
                'avg_sharpe': 1.35,
                'best_sharpe': 2.1,
                'worst_sharpe': 0.6,
                'validation_pass_rate': 0.73,
                'exploration_usage': 3,
                'champion_usage': 8
            }
        """
        # Filter records for this template
        template_records = [
            r for r in self.usage_records
            if r.template_name == template_name
        ]

        if not template_records:
            return {
                'total_usage': 0,
                'success_rate': 0.0,
                'avg_sharpe': 0.0,
                'has_data': False
            }

        # Calculate statistics
        total_usage = len(template_records)

        # Success rate (validation passed AND Sharpe >= 1.0)
        successful_records = [
            r for r in template_records
            if r.validation_passed and r.sharpe_ratio >= self.MIN_SHARPE_SUCCESS
        ]
        success_rate = len(successful_records) / total_usage if total_usage > 0 else 0.0

        # Sharpe statistics
        sharpe_ratios = [r.sharpe_ratio for r in template_records]
        avg_sharpe = sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else 0.0
        best_sharpe = max(sharpe_ratios) if sharpe_ratios else 0.0
        worst_sharpe = min(sharpe_ratios) if sharpe_ratios else 0.0

        # Validation pass rate
        validation_passed_count = sum(1 for r in template_records if r.validation_passed)
        validation_pass_rate = validation_passed_count / total_usage if total_usage > 0 else 0.0

        # Exploration vs exploitation
        exploration_usage = sum(1 for r in template_records if r.exploration_mode)
        champion_usage = sum(1 for r in template_records if r.champion_based)

        return {
            'total_usage': total_usage,
            'success_rate': round(success_rate, 3),
            'avg_sharpe': round(avg_sharpe, 3),
            'best_sharpe': round(best_sharpe, 3),
            'worst_sharpe': round(worst_sharpe, 3),
            'validation_pass_rate': round(validation_pass_rate, 3),
            'exploration_usage': exploration_usage,
            'champion_usage': champion_usage,
            'has_data': True,
            'reliable_stats': total_usage >= self.MIN_RECORDS_FOR_STATS
        }

    def get_all_templates_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary statistics for all templates.

        Returns:
            Dictionary mapping template names to statistics

        Example:
            >>> summary = analytics.get_all_templates_summary()
            >>> for template, stats in summary.items():
            ...     print(f"{template}: {stats['success_rate']:.1%}")
        """
        # Get unique template names
        template_names = set(r.template_name for r in self.usage_records)

        # Calculate stats for each template
        summary = {}
        for template_name in template_names:
            summary[template_name] = self.get_template_statistics(template_name)

        return summary

    def get_usage_trend(
        self,
        template_name: Optional[str] = None,
        last_n_iterations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get usage trend for template or all templates.

        Args:
            template_name: Optional template name filter
            last_n_iterations: Number of recent iterations to include

        Returns:
            List of usage records (most recent first)

        Example:
            >>> trend = analytics.get_usage_trend('TurtleTemplate', last_n_iterations=5)
            >>> for record in trend:
            ...     print(f"Iteration {record['iteration']}: Sharpe {record['sharpe_ratio']:.2f}")
        """
        # Filter by template if specified
        if template_name:
            filtered_records = [
                r for r in self.usage_records
                if r.template_name == template_name
            ]
        else:
            filtered_records = self.usage_records

        # Sort by iteration (most recent first)
        sorted_records = sorted(
            filtered_records,
            key=lambda r: r.iteration,
            reverse=True
        )

        # Take last N iterations
        recent_records = sorted_records[:last_n_iterations]

        # Convert to dictionaries
        return [r.to_dict() for r in recent_records]

    def get_best_performing_template(self) -> Optional[str]:
        """
        Get the template with highest success rate.

        Returns:
            Template name with highest success rate, or None

        Example:
            >>> best = analytics.get_best_performing_template()
            >>> print(best)
            'TurtleTemplate'
        """
        summary = self.get_all_templates_summary()

        if not summary:
            return None

        # Filter templates with reliable statistics
        reliable_templates = {
            name: stats for name, stats in summary.items()
            if stats['reliable_stats']
        }

        if not reliable_templates:
            return None

        # Find template with highest success rate
        best_template = max(
            reliable_templates.items(),
            key=lambda x: (x[1]['success_rate'], x[1]['avg_sharpe'])
        )

        return best_template[0]

    def export_report(self, output_path: str = 'template_analytics_report.json') -> None:
        """
        Export comprehensive analytics report to JSON.

        Args:
            output_path: Output file path

        Example:
            >>> analytics.export_report('report.json')
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_records': len(self.usage_records),
            'template_summary': self.get_all_templates_summary(),
            'best_template': self.get_best_performing_template(),
            'recent_usage': self.get_usage_trend(last_n_iterations=20)
        }

        output_file = Path(output_path)
        with output_file.open('w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Analytics report exported to {output_path}")

    def _load_from_storage(self) -> None:
        """Load usage records from JSON storage."""
        if not self.storage_path.exists():
            self.logger.info(f"No existing storage file at {self.storage_path}")
            return

        try:
            with self.storage_path.open('r', encoding='utf-8') as f:
                data = json.load(f)

            # Convert dictionaries to TemplateUsageRecord objects
            self.usage_records = [
                TemplateUsageRecord(**record) for record in data
            ]

            self.logger.info(f"Loaded {len(self.usage_records)} records from storage")

        except Exception as e:
            self.logger.error(f"Failed to load from storage: {e}")
            self.usage_records = []

    def _save_to_storage(self) -> None:
        """
        Save usage records to JSON storage using atomic file operations.

        Uses temp file + rename pattern to ensure data integrity:
        1. Write to temporary file
        2. Atomic rename to actual storage path

        This prevents corruption from partial writes or crashes during save.
        """
        try:
            # Convert records to dictionaries
            data = [r.to_dict() for r in self.usage_records]

            # Write to temporary file first (atomic operation)
            temp_fd, temp_path = tempfile.mkstemp(
                dir=self.storage_path.parent,
                prefix='.tmp_analytics_',
                suffix='.json',
                text=True
            )

            try:
                with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                # Atomic rename to final location
                # On POSIX systems, this is atomic even if target exists
                os.replace(temp_path, str(self.storage_path))

                self.logger.debug(f"Saved {len(self.usage_records)} records to storage (atomic)")

            except Exception as e:
                # Clean up temp file on error
                try:
                    os.unlink(temp_path)
                except:
                    pass
                raise

        except Exception as e:
            self.logger.error(f"Failed to save to storage: {e}")
