"""
Pattern Search for Hall of Fame Repository
==========================================

Success pattern queries and analysis for strategy genomes.
Identifies common patterns among champions and provides pattern statistics.

Features:
    - Search strategies by success patterns
    - Identify common patterns among champions
    - Calculate pattern occurrence statistics
    - Pattern prioritization based on performance
    - Cross-tier pattern analysis

Usage:
    from src.repository import HallOfFameRepository, PatternSearch

    repo = HallOfFameRepository()
    searcher = PatternSearch(repo)

    # Find strategies with specific pattern
    strategies = searcher.search_by_pattern('high_revenue_growth')

    # Get common patterns among champions
    common = searcher.get_common_patterns(min_count=3)

    # Get pattern statistics
    stats = searcher.get_pattern_statistics()

Requirements:
    - Requirement 2.6: Success pattern tracking and analysis
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter
import logging

# Configure logger
_logger = logging.getLogger(__name__)


class PatternSearch:
    """
    Pattern search and analysis for Hall of Fame repository.

    Provides pattern-based queries and statistical analysis:
        - Find strategies with specific patterns
        - Identify common patterns among champions
        - Calculate pattern occurrence and success rates
        - Prioritize patterns by performance impact

    Attributes:
        repository: HallOfFameRepository instance
        logger: Python logger for operations

    Example:
        >>> from src.repository import HallOfFameRepository, PatternSearch
        >>> repo = HallOfFameRepository()
        >>> searcher = PatternSearch(repo)
        >>> strategies = searcher.search_by_pattern('high_revenue_growth')
        >>> print(f"Found {len(strategies)} strategies with pattern")
    """

    def __init__(
        self,
        repository,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize pattern search.

        Args:
            repository: HallOfFameRepository instance
            logger: Optional logger for operations
        """
        self.repository = repository
        self.logger = logger or _logger

        self.logger.info("PatternSearch initialized")

    def search_by_pattern(
        self,
        pattern: str,
        tier: Optional[str] = None,
        min_sharpe: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Find strategies with specific success pattern.

        Args:
            pattern: Success pattern to search for
                Examples: 'high_revenue_growth', 'low_volatility', 'strong_momentum'
            tier: Optional tier filter ('champions', 'contenders', 'archive')
            min_sharpe: Optional minimum Sharpe ratio threshold
            limit: Optional maximum number of results

        Returns:
            List of dictionaries containing:
                - genome: StrategyGenome object
                - tier: Tier classification
                - sharpe_ratio: Strategy Sharpe ratio
                - pattern_score: Score of the pattern (if available)
                - all_patterns: All success patterns for this strategy

        Example:
            >>> results = searcher.search_by_pattern(
            ...     'high_revenue_growth',
            ...     tier='champions',
            ...     min_sharpe=2.0
            ... )
            >>> for result in results:
            ...     print(f"{result['genome'].genome_id}: "
            ...           f"Sharpe {result['sharpe_ratio']:.2f}")

        Requirements:
            - Requirement 2.6: Pattern-based search
        """
        results = []

        # Determine tiers to search
        if tier is not None:
            tiers = [tier]
        else:
            tiers = ['champions', 'contenders', 'archive']

        # Search across tiers
        for tier_name in tiers:
            for genome in self.repository._cache.get(tier_name, []):
                # Check if genome has success_patterns
                if genome.success_patterns is None:
                    continue

                # Check if pattern exists in success_patterns
                if pattern in genome.success_patterns:
                    sharpe = genome.metrics.get('sharpe_ratio', 0.0)

                    # Apply Sharpe filter if specified
                    if min_sharpe is not None and sharpe < min_sharpe:
                        continue

                    # Get pattern score if available
                    pattern_score = genome.success_patterns.get(pattern, 0.0)

                    results.append({
                        'genome': genome,
                        'tier': tier_name,
                        'sharpe_ratio': sharpe,
                        'pattern_score': pattern_score,
                        'all_patterns': list(genome.success_patterns.keys())
                    })

        # Sort by Sharpe ratio descending
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)

        # Apply limit if specified
        if limit is not None:
            results = results[:limit]

        self.logger.info(
            f"Pattern search '{pattern}': found {len(results)} strategies "
            f"(tier={tier}, min_sharpe={min_sharpe})"
        )

        return results

    def get_common_patterns(
        self,
        tier: str = 'champions',
        min_count: int = 2,
        min_sharpe: Optional[float] = None
    ) -> List[Dict]:
        """
        Identify patterns commonly shared by strategies in a tier.

        Algorithm:
            1. Collect all patterns from strategies in tier
            2. Count pattern occurrences
            3. Filter by minimum occurrence count
            4. Calculate average Sharpe for each pattern
            5. Sort by frequency and performance

        Args:
            tier: Tier to analyze (default: 'champions')
            min_count: Minimum number of strategies that must share pattern
            min_sharpe: Optional minimum Sharpe filter for strategies

        Returns:
            List of dictionaries containing:
                - pattern: Pattern name
                - count: Number of strategies with this pattern
                - avg_sharpe: Average Sharpe ratio of strategies with pattern
                - max_sharpe: Highest Sharpe ratio with this pattern
                - strategy_ids: List of genome IDs with this pattern

        Example:
            >>> common = searcher.get_common_patterns(
            ...     tier='champions',
            ...     min_count=3
            ... )
            >>> for pattern_info in common:
            ...     print(f"{pattern_info['pattern']}: "
            ...           f"{pattern_info['count']} strategies, "
            ...           f"avg Sharpe {pattern_info['avg_sharpe']:.2f}")

        Requirements:
            - Requirement 2.6: Common pattern identification
        """
        # Collect patterns from tier
        pattern_data = {}  # pattern → {'sharpes': [], 'genome_ids': []}

        for genome in self.repository._cache.get(tier, []):
            # Skip if no patterns
            if genome.success_patterns is None:
                continue

            sharpe = genome.metrics.get('sharpe_ratio', 0.0)

            # Apply Sharpe filter if specified
            if min_sharpe is not None and sharpe < min_sharpe:
                continue

            # Record each pattern
            for pattern in genome.success_patterns.keys():
                if pattern not in pattern_data:
                    pattern_data[pattern] = {'sharpes': [], 'genome_ids': []}

                pattern_data[pattern]['sharpes'].append(sharpe)
                pattern_data[pattern]['genome_ids'].append(genome.genome_id)

        # Build results
        results = []

        for pattern, data in pattern_data.items():
            count = len(data['sharpes'])

            # Filter by minimum count
            if count >= min_count:
                avg_sharpe = sum(data['sharpes']) / count
                max_sharpe = max(data['sharpes'])

                results.append({
                    'pattern': pattern,
                    'count': count,
                    'avg_sharpe': avg_sharpe,
                    'max_sharpe': max_sharpe,
                    'strategy_ids': data['genome_ids']
                })

        # Sort by count descending, then by avg_sharpe descending
        results.sort(key=lambda x: (x['count'], x['avg_sharpe']), reverse=True)

        self.logger.info(
            f"Common patterns in {tier}: found {len(results)} patterns "
            f"(min_count={min_count}, min_sharpe={min_sharpe})"
        )

        return results

    def get_pattern_statistics(
        self,
        tier: Optional[str] = None
    ) -> Dict[str, Dict]:
        """
        Calculate comprehensive pattern statistics.

        Statistics calculated:
            - Total occurrence count across all strategies
            - Success rate (percentage in champions)
            - Average Sharpe ratio for strategies with pattern
            - Distribution across tiers

        Args:
            tier: Optional tier filter (None = all tiers)

        Returns:
            Dictionary mapping pattern name to statistics:
                {
                    'pattern_name': {
                        'total_count': Total occurrences,
                        'champions_count': Occurrences in champions,
                        'contenders_count': Occurrences in contenders,
                        'archive_count': Occurrences in archive,
                        'success_rate': champions_count / total_count,
                        'avg_sharpe': Average Sharpe ratio,
                        'max_sharpe': Highest Sharpe ratio
                    }
                }

        Example:
            >>> stats = searcher.get_pattern_statistics()
            >>> for pattern, data in stats.items():
            ...     print(f"{pattern}: {data['total_count']} occurrences, "
            ...           f"{data['success_rate']:.1%} in champions")

        Requirements:
            - Requirement 2.6: Pattern statistics
        """
        # Determine tiers to analyze
        if tier is not None:
            tiers = [tier]
        else:
            tiers = ['champions', 'contenders', 'archive']

        # Collect pattern data
        # pattern → {'total': 0, 'champions': 0, 'contenders': 0, 'archive': 0, 'sharpes': []}
        pattern_stats = {}

        for tier_name in tiers:
            for genome in self.repository._cache.get(tier_name, []):
                # Skip if no patterns
                if genome.success_patterns is None:
                    continue

                sharpe = genome.metrics.get('sharpe_ratio', 0.0)

                # Record each pattern
                for pattern in genome.success_patterns.keys():
                    if pattern not in pattern_stats:
                        pattern_stats[pattern] = {
                            'total': 0,
                            'champions': 0,
                            'contenders': 0,
                            'archive': 0,
                            'sharpes': []
                        }

                    pattern_stats[pattern]['total'] += 1
                    pattern_stats[pattern][tier_name] += 1
                    pattern_stats[pattern]['sharpes'].append(sharpe)

        # Build final statistics
        results = {}

        for pattern, data in pattern_stats.items():
            total = data['total']
            sharpes = data['sharpes']

            results[pattern] = {
                'total_count': total,
                'champions_count': data['champions'],
                'contenders_count': data['contenders'],
                'archive_count': data['archive'],
                'success_rate': data['champions'] / total if total > 0 else 0.0,
                'avg_sharpe': sum(sharpes) / len(sharpes) if sharpes else 0.0,
                'max_sharpe': max(sharpes) if sharpes else 0.0
            }

        self.logger.info(
            f"Pattern statistics: analyzed {len(results)} unique patterns "
            f"(tier={tier})"
        )

        return results

    def prioritize_patterns(
        self,
        tier: str = 'champions',
        min_count: int = 2
    ) -> List[Tuple[str, float]]:
        """
        Prioritize patterns by performance impact.

        Uses composite scoring:
            - Pattern frequency (occurrence count)
            - Average Sharpe ratio of strategies with pattern
            - Success rate (percentage in champions)

        Score = (avg_sharpe * success_rate) + (count * 0.1)

        Args:
            tier: Tier to analyze (default: 'champions')
            min_count: Minimum occurrence count to consider

        Returns:
            List of tuples (pattern_name, priority_score) sorted by score descending

        Example:
            >>> priorities = searcher.prioritize_patterns(
            ...     tier='champions',
            ...     min_count=3
            ... )
            >>> for pattern, score in priorities[:5]:
            ...     print(f"{pattern}: priority score {score:.2f}")

        Requirements:
            - Requirement 2.6: Pattern prioritization
            - Leverages performance_attributor pattern prioritization logic
        """
        # Get common patterns and statistics
        common = self.get_common_patterns(tier=tier, min_count=min_count)
        all_stats = self.get_pattern_statistics()

        # Calculate priority scores
        priorities = []

        for pattern_info in common:
            pattern = pattern_info['pattern']
            count = pattern_info['count']
            avg_sharpe = pattern_info['avg_sharpe']

            # Get success rate from all_stats
            stats = all_stats.get(pattern, {})
            success_rate = stats.get('success_rate', 0.0)

            # Composite score
            # Prioritize high Sharpe + high success rate + frequency
            score = (avg_sharpe * success_rate) + (count * 0.1)

            priorities.append((pattern, score))

        # Sort by score descending
        priorities.sort(key=lambda x: x[1], reverse=True)

        self.logger.info(
            f"Prioritized {len(priorities)} patterns "
            f"(tier={tier}, min_count={min_count})"
        )

        return priorities

    def analyze_pattern_combinations(
        self,
        tier: str = 'champions',
        max_combination_size: int = 3
    ) -> List[Dict]:
        """
        Analyze pattern combinations that appear together.

        Identifies frequently co-occurring patterns and their combined performance.

        Args:
            tier: Tier to analyze (default: 'champions')
            max_combination_size: Maximum patterns in combination (default: 3)

        Returns:
            List of dictionaries containing:
                - patterns: Tuple of pattern names
                - count: Number of strategies with this combination
                - avg_sharpe: Average Sharpe ratio
                - strategy_ids: List of genome IDs

        Example:
            >>> combinations = searcher.analyze_pattern_combinations(
            ...     tier='champions',
            ...     max_combination_size=2
            ... )
            >>> for combo in combinations[:5]:
            ...     print(f"{combo['patterns']}: "
            ...           f"{combo['count']} strategies, "
            ...           f"avg Sharpe {combo['avg_sharpe']:.2f}")
        """
        from itertools import combinations

        # Collect all pattern sets from strategies
        strategy_patterns = []  # [(genome_id, sharpe, frozenset(patterns))]

        for genome in self.repository._cache.get(tier, []):
            if genome.success_patterns is None or not genome.success_patterns:
                continue

            sharpe = genome.metrics.get('sharpe_ratio', 0.0)
            patterns = frozenset(genome.success_patterns.keys())

            strategy_patterns.append((genome.genome_id, sharpe, patterns))

        # Generate all pattern combinations
        combination_data = {}  # frozenset(patterns) → {'sharpes': [], 'genome_ids': []}

        for genome_id, sharpe, patterns in strategy_patterns:
            # Generate combinations of different sizes
            for size in range(2, min(len(patterns) + 1, max_combination_size + 1)):
                for combo in combinations(sorted(patterns), size):
                    combo_key = frozenset(combo)

                    if combo_key not in combination_data:
                        combination_data[combo_key] = {'sharpes': [], 'genome_ids': []}

                    combination_data[combo_key]['sharpes'].append(sharpe)
                    combination_data[combo_key]['genome_ids'].append(genome_id)

        # Build results
        results = []

        for combo, data in combination_data.items():
            count = len(data['sharpes'])
            avg_sharpe = sum(data['sharpes']) / count

            results.append({
                'patterns': tuple(sorted(combo)),
                'count': count,
                'avg_sharpe': avg_sharpe,
                'strategy_ids': data['genome_ids']
            })

        # Sort by count descending, then by avg_sharpe descending
        results.sort(key=lambda x: (x['count'], x['avg_sharpe']), reverse=True)

        self.logger.info(
            f"Pattern combinations in {tier}: found {len(results)} combinations "
            f"(max_size={max_combination_size})"
        )

        return results
