"""
Index Manager for Hall of Fame Repository
==========================================

Fast metadata indexing and search for strategy genomes.
Maintains comprehensive index for pattern-based and metrics-based queries.

Features:
    - JSON-based index storage for fast loading
    - Metadata tracking (genome_id, sharpe, template, patterns, timestamp)
    - Pattern-based search (find strategies with specific patterns)
    - Metrics-based search (find strategies by performance criteria)
    - Full index maintenance even after archival/compression
    - Automatic index updates on strategy add/remove

Index Structure (artifacts/data/hall_of_fame_index.json):
    {
        "genome_id_1": {
            "tier": "champions",
            "sharpe_ratio": 2.3,
            "template_name": "TurtleTemplate",
            "success_patterns": ["high_revenue_growth", "low_volatility"],
            "timestamp": "2025-10-16T10:30:00",
            "parameters": {"n_stocks": 10, "ma_short": 20},
            "file_path": "hall_of_fame/champions/genome_id_1.yaml"
        },
        ...
    }

Usage:
    from src.repository import IndexManager

    index_mgr = IndexManager(repository)

    # Update index after adding strategy
    index_mgr.update_index()

    # Search by pattern
    strategies = index_mgr.search_by_pattern("high_revenue_growth")

    # Search by metrics
    top_performers = index_mgr.search_by_metrics(min_sharpe=2.0, max_drawdown=0.15)

Requirements:
    - Requirement 2.8: Index management for fast lookup
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

# Configure logger
_logger = logging.getLogger(__name__)


class IndexManager:
    """
    Index manager for fast strategy lookup and search.

    Maintains a comprehensive JSON-based index of all strategies in the
    Hall of Fame repository for fast pattern-based and metrics-based queries.

    Features:
        - Automatic index generation from repository
        - Fast JSON-based storage and retrieval
        - Pattern-based search across all strategies
        - Metrics-based search with flexible filters
        - Maintains index even after archival/compression

    Attributes:
        repository: HallOfFameRepository instance
        index_path: Path to index JSON file
        index: In-memory index dictionary (genome_id → metadata)
        logger: Python logger for operations

    Example:
        >>> from src.repository import HallOfFameRepository, IndexManager
        >>> repo = HallOfFameRepository()
        >>> index_mgr = IndexManager(repo)
        >>> index_mgr.update_index()
        >>> results = index_mgr.search_by_metrics(min_sharpe=2.0)
    """

    # Default index storage path
    DEFAULT_INDEX_PATH = Path('artifacts/data/hall_of_fame_index.json')

    def __init__(
        self,
        repository: Any,  # HallOfFameRepository
        index_path: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize index manager.

        Args:
            repository: HallOfFameRepository instance to index
            index_path: Optional custom path for index JSON file
            logger: Optional logger for operations
        """
        self.repository = repository
        self.index_path = index_path or self.DEFAULT_INDEX_PATH
        self.logger = logger or _logger

        # In-memory index: genome_id → metadata
        self.index: Dict[str, Dict[str, Any]] = {}

        # Ensure index directory exists
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing index if available
        self._load_index()

        self.logger.info(f"IndexManager initialized with {len(self.index)} indexed strategies")

    def _load_index(self) -> None:
        """
        Load index from JSON file.

        If index file doesn't exist, initializes empty index.
        Handles JSON parsing errors gracefully.
        """
        if not self.index_path.exists():
            self.logger.info(f"No existing index at {self.index_path}. Starting with empty index.")
            self.index = {}
            return

        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                self.index = json.load(f)

            self.logger.info(f"Loaded index with {len(self.index)} strategies from {self.index_path}")

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse index JSON: {e}")
            self.logger.warning("Starting with empty index")
            self.index = {}

        except Exception as e:
            self.logger.error(f"Error loading index: {e}")
            self.index = {}

    def _save_index(self) -> None:
        """
        Save index to JSON file.

        Writes atomically using temporary file to prevent corruption.
        Pretty-prints JSON for human readability.
        """
        try:
            # Write atomically using temporary file
            temp_path = self.index_path.with_suffix('.tmp')

            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(self.index_path)

            self.logger.debug(f"Saved index with {len(self.index)} strategies")

        except Exception as e:
            self.logger.error(f"Error saving index: {e}")
            raise

    def update_index(self) -> int:
        """
        Update index from current repository state.

        Scans all tiers in the repository and builds comprehensive index
        with metadata for each strategy genome. Updates both new and existing
        entries.

        Algorithm:
            1. Get all strategies from repository (champions, contenders, archive)
            2. For each strategy, extract metadata
            3. Build index entry with genome_id as key
            4. Save updated index to JSON

        Returns:
            Number of strategies indexed

        Example:
            >>> index_mgr.update_index()
            185  # Indexed 185 strategies

        Requirements:
            - Requirement 2.8: Index management and updates
        """
        self.index = {}  # Reset index

        indexed_count = 0

        # Index all tiers
        for tier in ['champions', 'contenders', 'archive']:
            strategies = self.repository._cache.get(tier, [])

            for genome in strategies:
                # Extract metadata
                genome_id = genome.genome_id

                # Build index entry
                index_entry = {
                    'tier': tier,
                    'sharpe_ratio': genome.metrics.get('sharpe_ratio', 0.0),
                    'annual_return': genome.metrics.get('annual_return', 0.0),
                    'max_drawdown': genome.metrics.get('max_drawdown', 0.0),
                    'template_name': genome.parameters.get('template_name', 'unknown'),
                    'success_patterns': list(genome.success_patterns.keys()) if genome.success_patterns else [],
                    'timestamp': genome.timestamp,
                    'iteration_num': genome.iteration_num,
                    'parameters': genome.parameters.copy(),
                    'file_path': f"hall_of_fame/{tier}/{genome_id}.yaml"
                }

                # Add to index
                self.index[genome_id] = index_entry
                indexed_count += 1

        # Save updated index
        self._save_index()

        self.logger.info(f"Updated index: {indexed_count} strategies indexed")

        return indexed_count

    def search_by_pattern(
        self,
        pattern: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for strategies with specific success pattern.

        Searches the index for all strategies that have the specified
        success pattern. Returns metadata for matching strategies.

        Args:
            pattern: Success pattern to search for
                Examples: 'high_revenue_growth', 'low_volatility', 'strong_momentum'
            limit: Optional maximum number of results to return

        Returns:
            List of index entries (metadata dictionaries) for matching strategies

        Example:
            >>> results = index_mgr.search_by_pattern('high_revenue_growth')
            >>> for strategy in results:
            ...     print(f"{strategy['genome_id']}: Sharpe {strategy['sharpe_ratio']}")

        Requirements:
            - Requirement 2.8: Pattern-based queries
        """
        results = []

        for genome_id, metadata in self.index.items():
            # Check if pattern exists in success_patterns list
            success_patterns = metadata.get('success_patterns', [])

            if pattern in success_patterns:
                # Add genome_id to metadata for reference
                result_entry = metadata.copy()
                result_entry['genome_id'] = genome_id
                results.append(result_entry)

        # Sort by sharpe_ratio descending
        results.sort(key=lambda x: x.get('sharpe_ratio', 0.0), reverse=True)

        # Apply limit if specified
        if limit is not None:
            results = results[:limit]

        self.logger.info(
            f"Pattern search '{pattern}': found {len(results)} strategies"
        )

        return results

    def search_by_metrics(
        self,
        min_sharpe: Optional[float] = None,
        max_sharpe: Optional[float] = None,
        min_return: Optional[float] = None,
        max_return: Optional[float] = None,
        max_drawdown: Optional[float] = None,
        template_name: Optional[str] = None,
        tier: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for strategies by performance metrics.

        Flexible search with multiple filter criteria. All specified filters
        are applied with AND logic (strategy must match all criteria).

        Args:
            min_sharpe: Minimum Sharpe ratio threshold
            max_sharpe: Maximum Sharpe ratio threshold
            min_return: Minimum annual return threshold
            max_return: Maximum annual return threshold
            max_drawdown: Maximum drawdown threshold (absolute value, e.g., 0.15 for -15%)
            template_name: Filter by template name
            tier: Filter by tier ('champions', 'contenders', 'archive')
            limit: Optional maximum number of results to return

        Returns:
            List of index entries (metadata dictionaries) for matching strategies

        Example:
            >>> # Find all champions with Sharpe >= 2.0 and drawdown <= 15%
            >>> results = index_mgr.search_by_metrics(
            ...     min_sharpe=2.0,
            ...     max_drawdown=0.15,
            ...     tier='champions'
            ... )
            >>> print(f"Found {len(results)} matching strategies")

        Requirements:
            - Requirement 2.8: Metrics-based queries
        """
        results = []

        for genome_id, metadata in self.index.items():
            # Apply all filters with AND logic
            match = True

            # Sharpe ratio filters
            if min_sharpe is not None:
                if metadata.get('sharpe_ratio', 0.0) < min_sharpe:
                    match = False

            if max_sharpe is not None:
                if metadata.get('sharpe_ratio', 0.0) > max_sharpe:
                    match = False

            # Annual return filters
            if min_return is not None:
                if metadata.get('annual_return', 0.0) < min_return:
                    match = False

            if max_return is not None:
                if metadata.get('annual_return', 0.0) > max_return:
                    match = False

            # Max drawdown filter (absolute value comparison)
            if max_drawdown is not None:
                dd = abs(metadata.get('max_drawdown', 0.0))
                if dd > max_drawdown:
                    match = False

            # Template name filter
            if template_name is not None:
                if metadata.get('template_name') != template_name:
                    match = False

            # Tier filter
            if tier is not None:
                if metadata.get('tier') != tier:
                    match = False

            # Add to results if all filters passed
            if match:
                result_entry = metadata.copy()
                result_entry['genome_id'] = genome_id
                results.append(result_entry)

        # Sort by sharpe_ratio descending
        results.sort(key=lambda x: x.get('sharpe_ratio', 0.0), reverse=True)

        # Apply limit if specified
        if limit is not None:
            results = results[:limit]

        self.logger.info(
            f"Metrics search: found {len(results)} strategies "
            f"(filters: sharpe={min_sharpe}-{max_sharpe}, "
            f"return={min_return}-{max_return}, dd<={max_drawdown}, "
            f"template={template_name}, tier={tier})"
        )

        return results

    def get_index_statistics(self) -> Dict[str, Any]:
        """
        Get index statistics.

        Returns:
            Dictionary with index statistics:
                - total_strategies: Total number of indexed strategies
                - by_tier: Count by tier
                - by_template: Count by template
                - avg_sharpe_by_tier: Average Sharpe ratio by tier
                - index_file_size: Index file size in bytes

        Example:
            >>> stats = index_mgr.get_index_statistics()
            >>> print(f"Total strategies: {stats['total_strategies']}")
            >>> print(f"Champions: {stats['by_tier']['champions']}")
        """
        if not self.index:
            return {
                'total_strategies': 0,
                'by_tier': {},
                'by_template': {},
                'avg_sharpe_by_tier': {},
                'index_file_size': 0
            }

        # Count by tier
        by_tier = {}
        by_template = {}
        sharpe_by_tier = {}

        for genome_id, metadata in self.index.items():
            tier = metadata.get('tier', 'unknown')
            template = metadata.get('template_name', 'unknown')
            sharpe = metadata.get('sharpe_ratio', 0.0)

            # Count by tier
            by_tier[tier] = by_tier.get(tier, 0) + 1

            # Count by template
            by_template[template] = by_template.get(template, 0) + 1

            # Accumulate sharpe for tier average
            if tier not in sharpe_by_tier:
                sharpe_by_tier[tier] = []
            sharpe_by_tier[tier].append(sharpe)

        # Calculate average Sharpe by tier
        avg_sharpe_by_tier = {
            tier: round(sum(sharpes) / len(sharpes), 2) if sharpes else 0.0
            for tier, sharpes in sharpe_by_tier.items()
        }

        # Get index file size
        index_file_size = self.index_path.stat().st_size if self.index_path.exists() else 0

        return {
            'total_strategies': len(self.index),
            'by_tier': by_tier,
            'by_template': by_template,
            'avg_sharpe_by_tier': avg_sharpe_by_tier,
            'index_file_size': index_file_size
        }

    def rebuild_index(self) -> int:
        """
        Rebuild index from scratch.

        Alias for update_index() for clarity.
        Useful when index may be corrupted or out of sync.

        Returns:
            Number of strategies indexed

        Example:
            >>> index_mgr.rebuild_index()
            185
        """
        self.logger.info("Rebuilding index from repository...")
        return self.update_index()

    def get_strategy_metadata(self, genome_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific strategy by genome_id.

        Args:
            genome_id: Genome ID to lookup

        Returns:
            Metadata dictionary or None if not found

        Example:
            >>> metadata = index_mgr.get_strategy_metadata('iter100_...')
            >>> print(f"Sharpe: {metadata['sharpe_ratio']}")
        """
        metadata = self.index.get(genome_id)

        if metadata:
            result = metadata.copy()
            result['genome_id'] = genome_id
            return result

        self.logger.warning(f"Strategy {genome_id} not found in index")
        return None
