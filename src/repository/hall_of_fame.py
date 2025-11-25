"""
Hall of Fame Repository
=======================

Manages validated strategy genomes with tier-based storage and novelty scoring.

Storage Tiers (based on Sharpe Ratio):
    - Champions: Sharpe ≥ 2.0 (Top performers)
    - Contenders: Sharpe 1.5-2.0 (Strong performers)
    - Archive: Sharpe < 1.5 (Below threshold)

Directory Structure:
    hall_of_fame/
    ├── champions/    # Sharpe ≥ 2.0
    ├── contenders/   # Sharpe 1.5-2.0
    ├── archive/      # Sharpe < 1.5
    └── backup/       # Serialization failure recovery
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import logging
import gzip
import shutil
import traceback
from datetime import datetime, timedelta

from .novelty_scorer import NoveltyScorer, DUPLICATE_THRESHOLD

# Configure logger for repository operations
_logger = logging.getLogger(__name__)


# Tier classification thresholds
CHAMPION_THRESHOLD = 2.0    # Sharpe ≥ 2.0
CONTENDER_THRESHOLD = 1.5   # Sharpe ≥ 1.5


@dataclass
class StrategyGenome:
    """
    Strategy genome data structure.

    Attributes:
        template_name: Name of the template (e.g., 'TurtleTemplate')
        parameters: Dictionary of parameter values
        metrics: Performance metrics dictionary
        created_at: Timestamp of creation
        strategy_code: Python code of the strategy (optional, for novelty scoring)
        success_patterns: Extracted success patterns (optional)
        genome_id: Unique identifier (auto-generated)
    """
    template_name: str
    parameters: Dict
    metrics: Dict
    created_at: str
    strategy_code: Optional[str] = None
    success_patterns: Optional[Dict] = None
    genome_id: Optional[str] = None

    def __post_init__(self):
        """Generate genome_id if not provided."""
        if self.genome_id is None:
            # Format: template_timestamp_sharpe
            timestamp = self.created_at.replace(':', '').replace('-', '').replace(' ', '_')
            sharpe = self.metrics.get('sharpe_ratio', 0.0)
            self.genome_id = f"{self.template_name}_{timestamp}_{sharpe:.2f}"

    def to_dict(self) -> Dict:
        """
        Convert genome to dictionary.

        Returns:
            Dictionary representation of the genome

        Example:
            >>> genome = StrategyGenome(...)
            >>> genome_dict = genome.to_dict()
        """
        data = {
            'genome_id': self.genome_id,
            'template_name': self.template_name,
            'parameters': self.parameters,
            'metrics': self.metrics,
            'created_at': self.created_at
        }

        # Include optional fields if present
        if self.strategy_code is not None:
            data['strategy_code'] = self.strategy_code
        if self.success_patterns is not None:
            data['success_patterns'] = self.success_patterns

        return data

    def to_json(self) -> str:
        """
        Serialize genome to JSON string.

        Returns:
            JSON-formatted string

        Example:
            >>> genome = StrategyGenome(...)
            >>> json_str = genome.to_json()
        """
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'StrategyGenome':
        """
        Deserialize genome from JSON string.

        Args:
            json_str: JSON-formatted string

        Returns:
            StrategyGenome object

        Raises:
            json.JSONDecodeError: If JSON parsing fails
            ValueError: If required fields are missing or invalid

        Example:
            >>> json_str = '{"genome_id": "TurtleTemplate_20250110_120000_2.30", ...}'
            >>> genome = StrategyGenome.from_json(json_str)
        """
        data = json.loads(json_str)

        # Validate required fields
        required_fields = ['template_name', 'parameters', 'metrics', 'created_at']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(
                f"Malformed JSON: missing required field(s): {', '.join(missing_fields)}"
            )

        # Validate data types
        if not isinstance(data['parameters'], dict):
            raise ValueError("Field 'parameters' must be a dictionary")
        if not isinstance(data['metrics'], dict):
            raise ValueError("Field 'metrics' must be a dictionary")

        return cls(
            template_name=data['template_name'],
            parameters=data['parameters'],
            metrics=data['metrics'],
            created_at=data['created_at'],
            strategy_code=data.get('strategy_code'),
            success_patterns=data.get('success_patterns'),
            genome_id=data.get('genome_id')
        )

    def save_to_file(self, file_path: Path) -> bool:
        """
        Save genome to JSON file.

        Args:
            file_path: Path to save the JSON file

        Returns:
            True if successful, False otherwise

        Example:
            >>> genome.save_to_file(Path('hall_of_fame/champions/genome_123.json'))
            True
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            return True
        except (IOError, OSError) as e:
            _logger.error(f"Failed to save genome to {file_path}: {e}")
            return False

    @classmethod
    def load_from_file(cls, file_path: Path) -> Optional['StrategyGenome']:
        """
        Load genome from JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            StrategyGenome object if successful, None otherwise

        Example:
            >>> genome = StrategyGenome.load_from_file(Path('champions/genome_123.json'))
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                json_str = f.read()
            return cls.from_json(json_str)
        except (IOError, OSError) as e:
            _logger.error(f"Failed to load genome from {file_path}: {e}")
            return None
        except json.JSONDecodeError as e:
            _logger.error(f"Failed to parse JSON from {file_path}: {e}")
            return None
        except ValueError as e:
            _logger.error(f"Invalid genome data in {file_path}: {e}")
            return None


class HallOfFameRepository:
    """
    Repository for managing validated strategy genomes.

    Features:
        - Tier-based storage (Champions, Contenders, Archive)
        - JSON serialization with backup
        - Novelty scoring (upcoming)
        - Query and retrieval methods (upcoming)

    Usage:
        >>> repo = HallOfFameRepository()
        >>> repo.add_strategy(genome, metrics)
        >>> champions = repo.get_champions()
    """

    def __init__(self, base_path: str = "hall_of_fame", test_mode: bool = False):
        """
        Initialize Hall of Fame repository.

        Args:
            base_path: Base directory for strategy storage (default: 'hall_of_fame')
            test_mode: If True, disable path security validation for testing (default: False)

        Storage Structure:
            {base_path}/
            ├── champions/    # Sharpe ≥ 2.0
            ├── contenders/   # Sharpe 1.5-2.0
            ├── archive/      # Sharpe < 1.5
            └── backup/       # Serialization failure recovery

        Raises:
            ValueError: If base_path attempts path traversal outside current directory
                       (only when test_mode=False)
        """
        # Validate path to prevent directory traversal attacks (skip in test mode)
        resolved_path = Path(base_path).resolve()

        if not test_mode:
            try:
                # Check if resolved path is relative to current working directory
                resolved_path.relative_to(Path.cwd())
            except ValueError:
                raise ValueError(
                    f"Security violation: base_path '{base_path}' resolves to '{resolved_path}' "
                    f"which is outside the allowed directory '{Path.cwd()}'"
                )

        self.base_path = resolved_path
        self._ensure_directories()

        # Tier subdirectories
        self.champions_dir = self.base_path / "champions"
        self.contenders_dir = self.base_path / "contenders"
        self.archive_dir = self.base_path / "archive"
        self.backup_dir = self.base_path / "backup"

        # Novelty scorer for duplicate detection
        self.novelty_scorer = NoveltyScorer()

        # In-memory cache for fast retrieval
        self._cache: Dict[str, List[StrategyGenome]] = {
            'champions': [],
            'contenders': [],
            'archive': []
        }

        # Indices for fast lookup
        self._template_index: Dict[str, List[StrategyGenome]] = {}  # template_name → genomes
        self._id_index: Dict[str, StrategyGenome] = {}  # genome_id → genome
        self._sharpe_index: Dict[str, List[StrategyGenome]] = {  # Sharpe range → genomes
            '2.5+': [],    # Sharpe ≥ 2.5 (exceptional)
            '2.0-2.5': [], # Sharpe 2.0-2.5 (champions)
            '1.5-2.0': [], # Sharpe 1.5-2.0 (contenders)
            '1.0-1.5': [], # Sharpe 1.0-1.5 (archive)
            '<1.0': []     # Sharpe < 1.0 (weak)
        }

        # Factor vector cache for performance optimization
        # genome_id → factor_vector (pre-computed for novelty scoring)
        self._vector_cache: Dict[str, Dict[str, float]] = {}

        # Load existing strategies into cache on initialization
        self._load_existing_strategies()

    def _ensure_directories(self) -> None:
        """
        Ensure all required directories exist.

        Creates:
            - champions/
            - contenders/
            - archive/
            - backup/
        """
        required_dirs = ['champions', 'contenders', 'archive', 'backup']
        for dir_name in required_dirs:
            dir_path = self.base_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)

    def _load_existing_strategies(self) -> None:
        """
        Load all existing strategy genomes from JSON files into cache.

        Scans all tier directories and loads valid JSON files.
        Populates _cache for fast retrieval and novelty checking.
        Pre-computes and caches factor vectors for performance optimization.
        """
        for tier in ['champions', 'contenders', 'archive']:
            tier_path = self._get_tier_path(tier)
            json_files = list(tier_path.glob('*.json'))

            for json_file in json_files:
                genome = StrategyGenome.load_from_file(json_file)
                if genome is not None:
                    self._cache[tier].append(genome)
                    self._update_indices(genome)  # Update indices

                    # Pre-compute and cache factor vector for novelty scoring
                    if genome.strategy_code is not None and genome.genome_id is not None:
                        vector = self.novelty_scorer.get_factor_vector(genome.strategy_code)
                        self._vector_cache[genome.genome_id] = vector

    def _update_indices(self, genome: StrategyGenome) -> None:
        """
        Update all indices when a new genome is added.

        Args:
            genome: StrategyGenome object to index

        Indices Updated:
            - template_index: By template name
            - id_index: By genome ID
            - sharpe_index: By Sharpe ratio range
        """
        # Update template index
        if genome.template_name not in self._template_index:
            self._template_index[genome.template_name] = []
        self._template_index[genome.template_name].append(genome)

        # Update ID index
        if genome.genome_id is not None:
            self._id_index[genome.genome_id] = genome

        # Update Sharpe index
        sharpe = genome.metrics.get('sharpe_ratio', 0.0)
        if sharpe >= 2.5:
            self._sharpe_index['2.5+'].append(genome)
        elif sharpe >= 2.0:
            self._sharpe_index['2.0-2.5'].append(genome)
        elif sharpe >= 1.5:
            self._sharpe_index['1.5-2.0'].append(genome)
        elif sharpe >= 1.0:
            self._sharpe_index['1.0-1.5'].append(genome)
        else:
            self._sharpe_index['<1.0'].append(genome)

    def _classify_tier(self, sharpe_ratio: float) -> str:
        """
        Classify strategy into tier based on Sharpe ratio.

        Classification Rules:
            - Sharpe ≥ 2.0  → 'champions'
            - Sharpe ≥ 1.5  → 'contenders'
            - Sharpe < 1.5  → 'archive'

        Args:
            sharpe_ratio: Sharpe ratio from backtest metrics

        Returns:
            Tier name: 'champions', 'contenders', or 'archive'

        Examples:
            >>> repo = HallOfFameRepository()
            >>> repo._classify_tier(2.5)
            'champions'
            >>> repo._classify_tier(1.8)
            'contenders'
            >>> repo._classify_tier(1.2)
            'archive'
        """
        if sharpe_ratio >= CHAMPION_THRESHOLD:
            return 'champions'
        elif sharpe_ratio >= CONTENDER_THRESHOLD:
            return 'contenders'
        else:
            return 'archive'

    def _get_tier_path(self, tier: str) -> Path:
        """
        Get directory path for a tier.

        Args:
            tier: Tier name ('champions', 'contenders', 'archive')

        Returns:
            Path object for the tier directory

        Raises:
            ValueError: If tier name is invalid
        """
        tier_map = {
            'champions': self.champions_dir,
            'contenders': self.contenders_dir,
            'archive': self.archive_dir
        }

        if tier not in tier_map:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {list(tier_map.keys())}")

        return tier_map[tier]

    def add_strategy(
        self,
        template_name: str,
        parameters: Dict,
        metrics: Dict,
        strategy_code: Optional[str] = None,
        success_patterns: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Add a strategy genome to the repository with novelty checking.

        Workflow:
            1. Validate metrics contain required fields
            2. Calculate novelty score (if strategy_code provided)
            3. Reject duplicates (novelty < 0.2)
            4. Classify tier based on Sharpe ratio
            5. Create StrategyGenome object
            6. Serialize to JSON and save to tier directory
            7. Update in-memory cache

        Args:
            template_name: Name of the template (e.g., 'TurtleTemplate')
            parameters: Parameter dictionary
            metrics: Performance metrics (must include 'sharpe_ratio')
            strategy_code: Python code of strategy (optional, for novelty scoring)
            success_patterns: Extracted success patterns (optional)

        Returns:
            Tuple of (success: bool, message: str)

        Examples:
            >>> repo = HallOfFameRepository()
            >>> success, msg = repo.add_strategy(
            ...     'TurtleTemplate',
            ...     {'n_stocks': 20, 'revenue_threshold': 1.05},
            ...     {'sharpe_ratio': 2.3, 'annual_return': 0.25},
            ...     strategy_code="close = data.get('price:收盤價')\\n..."
            ... )
            >>> print(success, msg)
            True Strategy added to champions tier (novelty: 0.85)
        """
        # Validate required metrics
        if 'sharpe_ratio' not in metrics:
            return False, "Metrics must include 'sharpe_ratio'"

        # Calculate novelty score if strategy code provided
        novelty_score = None
        similarity_info = None

        if strategy_code is not None:
            # Get all existing factor vectors from cache (performance optimized)
            existing_vectors = []
            genome_id_mapping = []  # Track which genome each vector corresponds to

            for tier in ['champions', 'contenders', 'archive']:
                for genome in self._cache[tier]:
                    if genome.strategy_code is not None and genome.genome_id in self._vector_cache:
                        existing_vectors.append(self._vector_cache[genome.genome_id])
                        genome_id_mapping.append(genome.genome_id)

            # Calculate novelty using cached vectors (avoids O(n) repeated extraction)
            novelty_score, similarity_info = self.novelty_scorer.calculate_novelty_score_with_cache(
                strategy_code,
                existing_vectors
            )

            # Reject duplicates
            if self.novelty_scorer.is_duplicate(novelty_score):
                # Map index back to genome_id for better error message
                similar_genome_id = genome_id_mapping[similarity_info['index']] if similarity_info['index'] < len(genome_id_mapping) else "unknown"
                return False, (
                    f"Duplicate strategy rejected (novelty: {novelty_score:.3f}, "
                    f"threshold: {DUPLICATE_THRESHOLD}). "
                    f"Similar to strategy {similar_genome_id} "
                    f"(similarity: {similarity_info['similarity']:.3f})"
                )

        # Classify tier
        sharpe_ratio = metrics['sharpe_ratio']
        tier = self._classify_tier(sharpe_ratio)

        # Create genome object
        genome = StrategyGenome(
            template_name=template_name,
            parameters=parameters,
            metrics=metrics,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            strategy_code=strategy_code,
            success_patterns=success_patterns
        )

        # Save genome to tier directory
        success, message = self._save_genome(genome, tier)

        if not success:
            # Backup failed serialization
            self._backup_genome(genome, tier, message)
            return False, f"Failed to save genome: {message}"

        # Update in-memory cache and indices
        self._cache[tier].append(genome)
        self._update_indices(genome)

        # Cache factor vector for future novelty scoring
        if genome.strategy_code is not None and genome.genome_id is not None:
            vector = self.novelty_scorer.get_factor_vector(genome.strategy_code)
            self._vector_cache[genome.genome_id] = vector

        # Build success message
        msg_parts = [f"Strategy added to {tier} tier (Sharpe: {sharpe_ratio:.2f}, ID: {genome.genome_id})"]
        if novelty_score is not None:
            msg_parts.append(f"novelty: {novelty_score:.3f}")

        return True, " | ".join(msg_parts)

    def _save_genome(self, genome: StrategyGenome, tier: str) -> Tuple[bool, str]:
        """
        Save genome to tier directory as JSON file.

        Args:
            genome: StrategyGenome object to save
            tier: Target tier ('champions', 'contenders', 'archive')

        Returns:
            Tuple of (success: bool, message: str)

        File Naming:
            {genome_id}.json (e.g., TurtleTemplate_20250110_120000_2.30.json)
        """
        try:
            # Get tier directory
            tier_path = self._get_tier_path(tier)

            # Create file path
            filename = f"{genome.genome_id}.json"
            file_path = tier_path / filename

            # Save to file
            success = genome.save_to_file(file_path)

            if success:
                return True, f"Saved to {tier}/{filename}"
            else:
                return False, "File write operation failed"

        except Exception as e:
            return False, f"Serialization error: {str(e)}"

    def _backup_genome(self, genome: StrategyGenome, tier: str, error_msg: str) -> None:
        """
        Backup genome as JSON when JSON serialization fails.

        Backup Mechanism:
            1. Convert genome to dictionary
            2. Add error metadata (tier, error, timestamp, stack trace)
            3. Save to backup/ directory as JSON
            4. Log failure for investigation

        Args:
            genome: StrategyGenome object that failed to save
            tier: Intended tier
            error_msg: Error message from failed save attempt

        Backup File:
            backup/{genome_id}_failed.json
        """
        try:
            # Create backup data
            backup_data = genome.to_dict()
            backup_data['_backup_metadata'] = {
                'intended_tier': tier,
                'error_message': error_msg,
                'backup_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'stack_trace': traceback.format_exc() if error_msg else None
            }

            # Save to backup directory
            filename = f"{genome.genome_id}_failed.json"
            file_path = self.backup_dir / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            _logger.warning(
                f"Genome {genome.genome_id} backed up to {filename} after save failure: {error_msg}"
            )

        except Exception as e:
            # If backup also fails, log critical error with full details
            _logger.critical(
                f"Failed to backup genome {genome.genome_id}: {str(e)}\n"
                f"Original error: {error_msg}\n"
                f"Backup error traceback: {traceback.format_exc()}"
            )

    def get_champions(self, limit: int = 10, sort_by: str = 'sharpe_ratio') -> List[StrategyGenome]:
        """
        Retrieve top N champion strategies (Sharpe ≥ 2.0) sorted by performance.

        Args:
            limit: Maximum number of champions to return (default: 10)
            sort_by: Metric to sort by (default: 'sharpe_ratio')

        Returns:
            List of StrategyGenome objects sorted by specified metric (descending)

        Example:
            >>> repo = HallOfFameRepository()
            >>> top_champions = repo.get_champions(limit=5)
            >>> for champ in top_champions:
            ...     print(f"{champ.genome_id}: {champ.metrics['sharpe_ratio']}")
        """
        champions = self._cache.get('champions', [])

        # Sort by metric (descending)
        sorted_champions = sorted(
            champions,
            key=lambda g: g.metrics.get(sort_by, 0.0),
            reverse=True
        )

        # Return top N
        return sorted_champions[:limit]

    def get_current_champion(self) -> Optional[StrategyGenome]:
        """
        Get the current champion strategy (highest Sharpe among champions tier).

        This method provides backward compatibility with the Learning System's
        single-champion model by returning the top-performing strategy from
        the champions tier (Sharpe ≥ 2.0).

        Returns:
            StrategyGenome object of the current champion, or None if no champions exist

        Example:
            >>> repo = HallOfFameRepository()
            >>> champion = repo.get_current_champion()
            >>> if champion:
            ...     print(f"Current champion: {champion.genome_id}")
            ...     print(f"Sharpe: {champion.metrics['sharpe_ratio']:.2f}")
            ... else:
            ...     print("No champion yet")

        Note:
            This is a convenience wrapper around get_champions(limit=1) for
            Learning System integration. The Hall of Fame can store multiple
            champions, but this method returns only the top one for backward
            compatibility.
        """
        champions = self.get_champions(limit=1, sort_by='sharpe_ratio')
        return champions[0] if champions else None

    def get_contenders(self, limit: int = 20, sort_by: str = 'sharpe_ratio') -> List[StrategyGenome]:
        """
        Retrieve top N contender strategies (Sharpe 1.5-2.0) sorted by performance.

        Args:
            limit: Maximum number of contenders to return (default: 20)
            sort_by: Metric to sort by (default: 'sharpe_ratio')

        Returns:
            List of StrategyGenome objects sorted by specified metric (descending)

        Example:
            >>> repo = HallOfFameRepository()
            >>> top_contenders = repo.get_contenders(limit=10)
            >>> for cont in top_contenders:
            ...     print(f"{cont.genome_id}: {cont.metrics['sharpe_ratio']}")
        """
        contenders = self._cache.get('contenders', [])

        # Sort by metric (descending)
        sorted_contenders = sorted(
            contenders,
            key=lambda g: g.metrics.get(sort_by, 0.0),
            reverse=True
        )

        # Return top N
        return sorted_contenders[:limit]

    def get_archive(self, limit: Optional[int] = None, sort_by: str = 'sharpe_ratio') -> List[StrategyGenome]:
        """
        Retrieve archived strategies (Sharpe < 1.5) sorted by performance.

        Args:
            limit: Maximum number of archived strategies to return (default: None = all)
            sort_by: Metric to sort by (default: 'sharpe_ratio')

        Returns:
            List of StrategyGenome objects sorted by specified metric (descending)

        Example:
            >>> repo = HallOfFameRepository()
            >>> archive = repo.get_archive(limit=50)
            >>> for strat in archive:
            ...     print(f"{strat.genome_id}: {strat.metrics['sharpe_ratio']}")
        """
        archive = self._cache.get('archive', [])

        # Sort by metric (descending)
        sorted_archive = sorted(
            archive,
            key=lambda g: g.metrics.get(sort_by, 0.0),
            reverse=True
        )

        # Return top N or all
        if limit is not None:
            return sorted_archive[:limit]
        return sorted_archive

    def query_similar(
        self,
        strategy_code: str,
        max_distance: float = 0.3,
        include_tiers: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Find similar strategies based on factor vector cosine distance.

        Args:
            strategy_code: Python code of the query strategy
            max_distance: Maximum cosine distance threshold (default: 0.3)
                         - 0.0 = Identical
                         - 0.3 = Similar
                         - 1.0 = Completely different
            include_tiers: Tiers to search (default: None = all tiers)

        Returns:
            List of dictionaries containing:
                - genome: StrategyGenome object
                - distance: Cosine distance score
                - similarity: Similarity score (1 - distance)
                - shared_features: List of common features
                - tier: Tier name

            Sorted by similarity (most similar first)

        Example:
            >>> code = "close = data.get('price:收盤價')\\nma = close.average(20)\\n..."
            >>> similar = repo.query_similar(code, max_distance=0.3)
            >>> for result in similar[:5]:
            ...     print(f"{result['genome'].genome_id}: similarity={result['similarity']:.3f}")

        Performance Target:
            <500ms for 100 strategies
        """
        # Default to all tiers
        if include_tiers is None:
            include_tiers = ['champions', 'contenders', 'archive']

        # Extract query vector
        query_vector = self.novelty_scorer.get_factor_vector(strategy_code)

        # Calculate distances to all strategies in specified tiers
        results = []

        for tier in include_tiers:
            for genome in self._cache.get(tier, []):
                # Skip strategies without code
                if genome.strategy_code is None:
                    continue

                # Use cached factor vector if available, otherwise extract
                if genome.genome_id in self._vector_cache:
                    genome_vector = self._vector_cache[genome.genome_id]
                else:
                    genome_vector = self.novelty_scorer.get_factor_vector(genome.strategy_code)
                    # Cache for future use
                    if genome.genome_id is not None:
                        self._vector_cache[genome.genome_id] = genome_vector

                # Calculate distance
                distance = self.novelty_scorer._calculate_cosine_distance(query_vector, genome_vector)

                # Include only strategies within threshold
                if distance <= max_distance:
                    # Get shared features
                    shared_features = self.novelty_scorer._get_shared_features(query_vector, genome_vector)

                    results.append({
                        'genome': genome,
                        'distance': distance,
                        'similarity': 1.0 - distance,
                        'shared_features': shared_features,
                        'tier': tier
                    })

        # Sort by similarity (most similar first = lowest distance)
        results.sort(key=lambda x: x['distance'])

        return results

    def get_statistics(self) -> Dict:
        """
        Get comprehensive repository statistics.

        Returns:
            Dictionary containing:
                - Tier counts (champions, contenders, archive, total)
                - Backup statistics (total_backups, oldest_backup_age_days)
                - Compression statistics (compressed_archives)
                - Template distribution

        Example:
            >>> repo.get_statistics()
            {
                'champions': 15,
                'contenders': 42,
                'archive': 128,
                'total': 185,
                'total_backups': 3,
                'oldest_backup_age_days': 12,
                'compressed_archives': 45,
                'templates': {'TurtleTemplate': 85, 'MastiffTemplate': 50, ...}
            }
        """
        # Tier counts
        stats = {
            'champions': len(self._cache.get('champions', [])),
            'contenders': len(self._cache.get('contenders', [])),
            'archive': len(self._cache.get('archive', []))
        }
        stats['total'] = sum(stats.values())

        # Backup statistics
        backup_files = list(self.backup_dir.glob('*_failed.json'))
        stats['total_backups'] = len(backup_files)

        if backup_files:
            # Find oldest backup
            oldest_mtime = min(f.stat().st_mtime for f in backup_files)
            oldest_age = (datetime.now() - datetime.fromtimestamp(oldest_mtime)).days
            stats['oldest_backup_age_days'] = oldest_age
        else:
            stats['oldest_backup_age_days'] = 0

        # Compression statistics
        compressed_files = list(self.archive_dir.glob('*.json.gz'))
        stats['compressed_archives'] = len(compressed_files)

        # Template distribution
        template_counts = {}
        for template_name, genomes in self._template_index.items():
            template_counts[template_name] = len(genomes)

        stats['templates'] = template_counts

        return stats

    def get_by_id(self, genome_id: str) -> Optional[StrategyGenome]:
        """
        Get strategy genome by ID using O(1) index lookup.

        Args:
            genome_id: Unique genome identifier

        Returns:
            StrategyGenome object if found, None otherwise

        Performance:
            O(1) lookup using ID index

        Example:
            >>> repo = HallOfFameRepository()
            >>> genome = repo.get_by_id('TurtleTemplate_20250110_120000_2.30')
            >>> if genome:
            ...     print(f"Found: {genome.template_name}, Sharpe: {genome.metrics['sharpe_ratio']}")
        """
        return self._id_index.get(genome_id)

    def get_by_template(
        self,
        template_name: str,
        limit: Optional[int] = None,
        sort_by: str = 'sharpe_ratio'
    ) -> List[StrategyGenome]:
        """
        Get all strategies for a specific template using index lookup.

        Args:
            template_name: Template name (e.g., 'TurtleTemplate', 'MastiffTemplate')
            limit: Maximum number to return (default: None = all)
            sort_by: Metric to sort by (default: 'sharpe_ratio')

        Returns:
            List of StrategyGenome objects sorted by specified metric (descending)

        Performance:
            O(1) index lookup + O(n log n) sort (n = strategies for this template)

        Example:
            >>> repo = HallOfFameRepository()
            >>> turtle_strategies = repo.get_by_template('TurtleTemplate', limit=10)
            >>> for strat in turtle_strategies:
            ...     print(f"{strat.genome_id}: Sharpe {strat.metrics['sharpe_ratio']:.2f}")
        """
        strategies = self._template_index.get(template_name, [])

        # Sort by metric (descending)
        sorted_strategies = sorted(
            strategies,
            key=lambda g: g.metrics.get(sort_by, 0.0),
            reverse=True
        )

        if limit is not None:
            return sorted_strategies[:limit]
        return sorted_strategies

    def get_by_sharpe_range(
        self,
        sharpe_range: str,
        limit: Optional[int] = None,
        sort_by: str = 'sharpe_ratio'
    ) -> List[StrategyGenome]:
        """
        Get strategies in a specific Sharpe ratio range using index lookup.

        Args:
            sharpe_range: One of '2.5+', '2.0-2.5', '1.5-2.0', '1.0-1.5', '<1.0'
            limit: Maximum number to return (default: None = all)
            sort_by: Metric to sort by (default: 'sharpe_ratio')

        Returns:
            List of StrategyGenome objects sorted by specified metric (descending)

        Raises:
            ValueError: If sharpe_range is invalid

        Performance:
            O(1) index lookup + O(n log n) sort (n = strategies in range)

        Example:
            >>> repo = HallOfFameRepository()
            >>> exceptional = repo.get_by_sharpe_range('2.5+', limit=5)
            >>> for strat in exceptional:
            ...     print(f"{strat.genome_id}: Sharpe {strat.metrics['sharpe_ratio']:.2f}")
        """
        valid_ranges = {'2.5+', '2.0-2.5', '1.5-2.0', '1.0-1.5', '<1.0'}
        if sharpe_range not in valid_ranges:
            raise ValueError(f"Invalid sharpe_range: {sharpe_range}. Must be one of {valid_ranges}")

        strategies = self._sharpe_index.get(sharpe_range, [])

        # Sort by metric (descending)
        sorted_strategies = sorted(
            strategies,
            key=lambda g: g.metrics.get(sort_by, 0.0),
            reverse=True
        )

        if limit is not None:
            return sorted_strategies[:limit]
        return sorted_strategies

    def query_by_metric_range(
        self,
        metric_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        include_tiers: Optional[List[str]] = None,
        limit: Optional[int] = None,
        sort_by: str = 'sharpe_ratio'
    ) -> List[StrategyGenome]:
        """
        Query strategies by metric value range.

        Args:
            metric_name: Name of the metric to filter (e.g., 'sharpe_ratio', 'annual_return')
            min_value: Minimum value (inclusive, default: None = no minimum)
            max_value: Maximum value (inclusive, default: None = no maximum)
            include_tiers: Tiers to search (default: None = all tiers)
            limit: Maximum number to return (default: None = all)
            sort_by: Metric to sort by (default: 'sharpe_ratio')

        Returns:
            List of StrategyGenome objects matching the range, sorted by sort_by metric

        Example:
            >>> repo = HallOfFameRepository()
            >>> # Find strategies with Sharpe > 2.5 and annual return > 0.3
            >>> high_sharpe = repo.query_by_metric_range('sharpe_ratio', min_value=2.5)
            >>> high_return = repo.query_by_metric_range('annual_return', min_value=0.3)
        """
        if include_tiers is None:
            include_tiers = ['champions', 'contenders', 'archive']

        results = []

        for tier in include_tiers:
            for genome in self._cache.get(tier, []):
                metric_value = genome.metrics.get(metric_name)

                if metric_value is None:
                    continue

                # Check range
                if min_value is not None and metric_value < min_value:
                    continue
                if max_value is not None and metric_value > max_value:
                    continue

                results.append(genome)

        # Sort by specified metric
        results.sort(key=lambda g: g.metrics.get(sort_by, 0.0), reverse=True)

        if limit is not None:
            return results[:limit]
        return results

    def query_by_parameters(
        self,
        parameter_filters: Dict[str, any],
        match_mode: str = 'exact',
        include_tiers: Optional[List[str]] = None,
        limit: Optional[int] = None,
        sort_by: str = 'sharpe_ratio'
    ) -> List[StrategyGenome]:
        """
        Query strategies by parameter values.

        Args:
            parameter_filters: Dictionary of parameter name → value/range
                For exact mode: {'n_stocks': 20, 'revenue_threshold': 1.05}
                For range mode: {'n_stocks': (10, 30), 'revenue_threshold': (1.0, 1.2)}
            match_mode: 'exact' or 'range' matching (default: 'exact')
            include_tiers: Tiers to search (default: None = all tiers)
            limit: Maximum number to return (default: None = all)
            sort_by: Metric to sort by (default: 'sharpe_ratio')

        Returns:
            List of StrategyGenome objects matching the parameter criteria

        Example:
            >>> repo = HallOfFameRepository()
            >>> # Find strategies with exact parameters
            >>> exact = repo.query_by_parameters({'n_stocks': 20, 'revenue_threshold': 1.05})
            >>> # Find strategies with parameter ranges
            >>> ranged = repo.query_by_parameters(
            ...     {'n_stocks': (10, 30), 'revenue_threshold': (1.0, 1.2)},
            ...     match_mode='range'
            ... )
        """
        if include_tiers is None:
            include_tiers = ['champions', 'contenders', 'archive']

        results = []

        for tier in include_tiers:
            for genome in self._cache.get(tier, []):
                match = True

                for param_name, param_value in parameter_filters.items():
                    genome_value = genome.parameters.get(param_name)

                    if genome_value is None:
                        match = False
                        break

                    if match_mode == 'exact':
                        if genome_value != param_value:
                            match = False
                            break
                    elif match_mode == 'range':
                        if not isinstance(param_value, (tuple, list)) or len(param_value) != 2:
                            raise ValueError(f"Range mode requires tuple/list of (min, max) for {param_name}")
                        min_val, max_val = param_value
                        if not (min_val <= genome_value <= max_val):
                            match = False
                            break
                    else:
                        raise ValueError(f"Invalid match_mode: {match_mode}. Must be 'exact' or 'range'")

                if match:
                    results.append(genome)

        # Sort by specified metric
        results.sort(key=lambda g: g.metrics.get(sort_by, 0.0), reverse=True)

        if limit is not None:
            return results[:limit]
        return results

    def query_by_factor_pattern(
        self,
        factor_type: str,
        factor_value: Optional[str] = None,
        include_tiers: Optional[List[str]] = None,
        limit: Optional[int] = None,
        sort_by: str = 'sharpe_ratio'
    ) -> List[StrategyGenome]:
        """
        Query strategies by factor vector patterns.

        Args:
            factor_type: Factor category ('dataset', 'indicator', 'filter', 'selection', 'weighting')
            factor_value: Specific factor value (e.g., 'price:收盤價', 'ma_20')
                         If None, returns all strategies with any factor of this type
            include_tiers: Tiers to search (default: None = all tiers)
            limit: Maximum number to return (default: None = all)
            sort_by: Metric to sort by (default: 'sharpe_ratio')

        Returns:
            List of StrategyGenome objects using the specified factor pattern

        Example:
            >>> repo = HallOfFameRepository()
            >>> # Find all strategies using moving averages
            >>> ma_strategies = repo.query_by_factor_pattern('indicator', 'ma_20')
            >>> # Find all strategies using price data
            >>> price_strategies = repo.query_by_factor_pattern('dataset', 'price:收盤價')
            >>> # Find all strategies using any filtering
            >>> filtered = repo.query_by_factor_pattern('filter')
        """
        if include_tiers is None:
            include_tiers = ['champions', 'contenders', 'archive']

        results = []

        for tier in include_tiers:
            for genome in self._cache.get(tier, []):
                # Skip if no strategy code
                if genome.strategy_code is None:
                    continue

                # Extract factor vector
                factor_vector = self.novelty_scorer.get_factor_vector(genome.strategy_code)

                # Check if genome has matching factor
                match = False

                if factor_value is None:
                    # Match any factor of this type
                    for factor_key in factor_vector.keys():
                        if factor_key.startswith(f'{factor_type}:'):
                            match = True
                            break
                else:
                    # Match specific factor
                    factor_key = f'{factor_type}:{factor_value}'
                    if factor_key in factor_vector and factor_vector[factor_key] > 0:
                        match = True

                if match:
                    results.append(genome)

        # Sort by specified metric
        results.sort(key=lambda g: g.metrics.get(sort_by, 0.0), reverse=True)

        if limit is not None:
            return results[:limit]
        return results

    def query_by_code_pattern(
        self,
        code_pattern: str,
        case_sensitive: bool = False,
        include_tiers: Optional[List[str]] = None,
        limit: Optional[int] = None,
        sort_by: str = 'sharpe_ratio'
    ) -> List[StrategyGenome]:
        """
        Query strategies by code pattern (full-text search).

        Args:
            code_pattern: String pattern to search for in strategy code
            case_sensitive: Whether search is case-sensitive (default: False)
            include_tiers: Tiers to search (default: None = all tiers)
            limit: Maximum number to return (default: None = all)
            sort_by: Metric to sort by (default: 'sharpe_ratio')

        Returns:
            List of StrategyGenome objects containing the code pattern

        Example:
            >>> repo = HallOfFameRepository()
            >>> # Find strategies using .average() method
            >>> avg_strategies = repo.query_by_code_pattern('.average(')
            >>> # Find strategies using resample
            >>> resample_strategies = repo.query_by_code_pattern('resample=')
        """
        if include_tiers is None:
            include_tiers = ['champions', 'contenders', 'archive']

        # Convert pattern to lowercase if case-insensitive
        search_pattern = code_pattern if case_sensitive else code_pattern.lower()

        results = []

        for tier in include_tiers:
            for genome in self._cache.get(tier, []):
                # Skip if no strategy code
                if genome.strategy_code is None:
                    continue

                # Check if pattern exists in code
                code_to_search = genome.strategy_code if case_sensitive else genome.strategy_code.lower()

                if search_pattern in code_to_search:
                    results.append(genome)

        # Sort by specified metric
        results.sort(key=lambda g: g.metrics.get(sort_by, 0.0), reverse=True)

        if limit is not None:
            return results[:limit]
        return results

    def query_advanced(
        self,
        metric_filters: Optional[Dict[str, Tuple[Optional[float], Optional[float]]]] = None,
        parameter_filters: Optional[Dict[str, any]] = None,
        parameter_match_mode: str = 'exact',
        factor_patterns: Optional[List[Tuple[str, Optional[str]]]] = None,
        code_pattern: Optional[str] = None,
        include_tiers: Optional[List[str]] = None,
        limit: Optional[int] = None,
        sort_by: str = 'sharpe_ratio'
    ) -> List[StrategyGenome]:
        """
        Advanced query with multiple filter criteria (AND logic).

        Combines metric ranges, parameter filters, factor patterns, and code search.

        Args:
            metric_filters: Dict of metric_name → (min_value, max_value)
                Example: {'sharpe_ratio': (2.5, None), 'annual_return': (0.3, None)}
            parameter_filters: Dict of parameter_name → value/range
                Example: {'n_stocks': (10, 30), 'revenue_threshold': 1.05}
            parameter_match_mode: 'exact' or 'range' for parameter matching
            factor_patterns: List of (factor_type, factor_value) tuples
                Example: [('indicator', 'ma_20'), ('dataset', 'price:收盤價')]
            code_pattern: String pattern to search in code
            include_tiers: Tiers to search (default: None = all tiers)
            limit: Maximum number to return (default: None = all)
            sort_by: Metric to sort by (default: 'sharpe_ratio')

        Returns:
            List of StrategyGenome objects matching ALL filter criteria

        Example:
            >>> repo = HallOfFameRepository()
            >>> # Find high-performing strategies with specific patterns
            >>> results = repo.query_advanced(
            ...     metric_filters={'sharpe_ratio': (2.5, None), 'annual_return': (0.3, None)},
            ...     parameter_filters={'n_stocks': (15, 25)},
            ...     parameter_match_mode='range',
            ...     factor_patterns=[('indicator', 'ma_20')],
            ...     code_pattern='.average('
            ... )
        """
        if include_tiers is None:
            include_tiers = ['champions', 'contenders', 'archive']

        # Start with all strategies from specified tiers
        candidates = []
        for tier in include_tiers:
            candidates.extend(self._cache.get(tier, []))

        # Apply metric filters
        if metric_filters:
            filtered = []
            for genome in candidates:
                match = True
                for metric_name, (min_val, max_val) in metric_filters.items():
                    metric_value = genome.metrics.get(metric_name)
                    if metric_value is None:
                        match = False
                        break
                    if min_val is not None and metric_value < min_val:
                        match = False
                        break
                    if max_val is not None and metric_value > max_val:
                        match = False
                        break
                if match:
                    filtered.append(genome)
            candidates = filtered

        # Apply parameter filters
        if parameter_filters:
            filtered = []
            for genome in candidates:
                match = True
                for param_name, param_value in parameter_filters.items():
                    genome_value = genome.parameters.get(param_name)
                    if genome_value is None:
                        match = False
                        break

                    if parameter_match_mode == 'exact':
                        if genome_value != param_value:
                            match = False
                            break
                    elif parameter_match_mode == 'range':
                        if not isinstance(param_value, (tuple, list)) or len(param_value) != 2:
                            match = False
                            break
                        min_val, max_val = param_value
                        if not (min_val <= genome_value <= max_val):
                            match = False
                            break

                if match:
                    filtered.append(genome)
            candidates = filtered

        # Apply factor pattern filters
        if factor_patterns:
            filtered = []
            for genome in candidates:
                if genome.strategy_code is None:
                    continue

                factor_vector = self.novelty_scorer.get_factor_vector(genome.strategy_code)
                match = True

                for factor_type, factor_value in factor_patterns:
                    factor_match = False

                    if factor_value is None:
                        # Match any factor of this type
                        for factor_key in factor_vector.keys():
                            if factor_key.startswith(f'{factor_type}:'):
                                factor_match = True
                                break
                    else:
                        # Match specific factor
                        factor_key = f'{factor_type}:{factor_value}'
                        if factor_key in factor_vector and factor_vector[factor_key] > 0:
                            factor_match = True

                    if not factor_match:
                        match = False
                        break

                if match:
                    filtered.append(genome)
            candidates = filtered

        # Apply code pattern filter
        if code_pattern:
            filtered = []
            search_pattern = code_pattern.lower()

            for genome in candidates:
                if genome.strategy_code is None:
                    continue

                if search_pattern in genome.strategy_code.lower():
                    filtered.append(genome)

            candidates = filtered

        # Sort by specified metric
        candidates.sort(key=lambda g: g.metrics.get(sort_by, 0.0), reverse=True)

        if limit is not None:
            return candidates[:limit]
        return candidates

    def cleanup_old_archive(self, days_threshold: int = 90, keep_top_n: int = 50) -> Tuple[int, int]:
        """
        Clean up old archive strategies while keeping top performers.

        Cleanup Strategy:
            1. Identify archive strategies older than threshold
            2. Keep top N by Sharpe ratio regardless of age
            3. Compress remaining old strategies to .json.gz
            4. Remove original JSON files after compression

        Args:
            days_threshold: Archive strategies older than this many days (default: 90)
            keep_top_n: Always keep this many top performers (default: 50)

        Returns:
            Tuple of (compressed_count, deleted_count)

        Example:
            >>> repo = HallOfFameRepository()
            >>> compressed, deleted = repo.cleanup_old_archive(days_threshold=90)
            >>> print(f"Compressed: {compressed}, Deleted: {deleted}")
        """
        archive_path = self.archive_dir
        cutoff_date = datetime.now() - timedelta(days=days_threshold)

        # Get all archive strategies
        archive_strategies = self._cache.get('archive', [])

        # Sort by Sharpe ratio to identify top performers
        sorted_archive = sorted(
            archive_strategies,
            key=lambda g: g.metrics.get('sharpe_ratio', 0.0),
            reverse=True
        )

        # Top performers to keep (never compress)
        top_performers = set(g.genome_id for g in sorted_archive[:keep_top_n])

        compressed_count = 0
        deleted_count = 0

        # Scan archive directory
        for json_file in archive_path.glob('*.json'):
            # Load genome to check age
            genome = StrategyGenome.load_from_file(json_file)
            if genome is None:
                continue

            # Skip top performers
            if genome.genome_id in top_performers:
                continue

            # Parse creation date
            try:
                created = datetime.strptime(genome.created_at, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                _logger.warning(f"Invalid date format for {genome.genome_id}, skipping")
                continue

            # Compress if older than threshold
            if created < cutoff_date:
                compressed_path = Path(str(json_file) + '.gz')

                try:
                    # Compress JSON to .gz
                    with open(json_file, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)

                    # Remove original after successful compression
                    json_file.unlink()
                    compressed_count += 1
                    _logger.info(f"Compressed old archive: {genome.genome_id}")

                except Exception as e:
                    _logger.error(f"Failed to compress {genome.genome_id}: {e}")

        return compressed_count, deleted_count

    def restore_compressed_genome(self, genome_id: str) -> Optional[StrategyGenome]:
        """
        Restore a compressed genome from archive.

        Args:
            genome_id: Genome ID to restore

        Returns:
            StrategyGenome object if found and restored, None otherwise

        Example:
            >>> repo = HallOfFameRepository()
            >>> genome = repo.restore_compressed_genome('TurtleTemplate_20240101_120000_1.25')
            >>> if genome:
            ...     print(f"Restored: {genome.template_name}")
        """
        # Search for compressed file in archive
        archive_path = self.archive_dir

        for gz_file in archive_path.glob(f'{genome_id}.json.gz'):
            try:
                # Decompress and load
                with gzip.open(gz_file, 'rt', encoding='utf-8') as f:
                    json_str = f.read()

                genome = StrategyGenome.from_json(json_str)
                _logger.info(f"Restored compressed genome: {genome_id}")
                return genome

            except Exception as e:
                _logger.error(f"Failed to restore {genome_id}: {e}")
                return None

        return None

    def archive_low_performers(self, min_sharpe: float = 1.0) -> int:
        """
        Move low-performing strategies from archive to compressed storage.

        Args:
            min_sharpe: Minimum Sharpe ratio to keep uncompressed (default: 1.0)

        Returns:
            Number of strategies compressed

        Example:
            >>> repo = HallOfFameRepository()
            >>> compressed = repo.archive_low_performers(min_sharpe=1.0)
            >>> print(f"Compressed {compressed} low performers")
        """
        archive_strategies = self._cache.get('archive', [])
        compressed_count = 0

        for genome in archive_strategies:
            sharpe = genome.metrics.get('sharpe_ratio', 0.0)

            # Compress if below threshold
            if sharpe < min_sharpe:
                json_file = self.archive_dir / f'{genome.genome_id}.json'

                if json_file.exists():
                    compressed_path = Path(str(json_file) + '.gz')

                    try:
                        with open(json_file, 'rb') as f_in:
                            with gzip.open(compressed_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)

                        json_file.unlink()
                        compressed_count += 1
                        _logger.info(f"Compressed low performer: {genome.genome_id}")

                    except Exception as e:
                        _logger.error(f"Failed to compress {genome.genome_id}: {e}")

        return compressed_count

    def recover_from_backup(
        self,
        genome_id: str,
        retry_save: bool = True
    ) -> Tuple[bool, Optional[StrategyGenome], str]:
        """
        Recover a strategy genome from backup directory.

        Recovery Workflow:
            1. Find backup file by genome_id
            2. Load JSON backup data
            3. Extract genome and metadata
            4. Optionally retry saving to original tier
            5. Return recovery status

        Args:
            genome_id: Genome ID to recover
            retry_save: If True, attempt to save to original tier (default: True)

        Returns:
            Tuple of (success, genome, message)
            - success: Whether recovery succeeded
            - genome: Recovered StrategyGenome object (None if failed)
            - message: Status message

        Example:
            >>> repo = HallOfFameRepository()
            >>> success, genome, msg = repo.recover_from_backup('TurtleTemplate_20250110_120000_2.30')
            >>> if success:
            ...     print(f"Recovered: {genome.genome_id}")
        """
        backup_file = self.backup_dir / f"{genome_id}_failed.json"

        if not backup_file.exists():
            return False, None, f"Backup file not found: {genome_id}"

        try:
            # Load backup data
            with open(backup_file, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # Extract metadata
            metadata = backup_data.pop('_backup_metadata', {})
            intended_tier = metadata.get('intended_tier', 'archive')

            # Recreate genome
            genome = StrategyGenome(
                template_name=backup_data['template_name'],
                parameters=backup_data['parameters'],
                metrics=backup_data['metrics'],
                created_at=backup_data['created_at'],
                strategy_code=backup_data.get('strategy_code'),
                success_patterns=backup_data.get('success_patterns'),
                genome_id=backup_data.get('genome_id')
            )

            # Optionally retry saving to original tier
            if retry_save:
                success, save_msg = self._save_genome(genome, intended_tier)

                if success:
                    # Remove backup file after successful save
                    backup_file.unlink()
                    _logger.info(f"Recovered and saved {genome_id} to {intended_tier}")
                    return True, genome, f"Recovered and saved to {intended_tier}: {save_msg}"
                else:
                    _logger.warning(f"Recovered {genome_id} but save failed: {save_msg}")
                    return True, genome, f"Recovered but save failed: {save_msg}"
            else:
                _logger.info(f"Recovered {genome_id} (not saved)")
                return True, genome, "Recovered successfully (not saved)"

        except Exception as e:
            _logger.error(f"Failed to recover {genome_id}: {e}\n{traceback.format_exc()}")
            return False, None, f"Recovery failed: {str(e)}"

    def list_backup_failures(self) -> List[Dict]:
        """
        List all failed genome backups with metadata.

        Returns:
            List of dictionaries containing:
                - genome_id: Genome identifier
                - intended_tier: Original target tier
                - error_message: Error that caused backup
                - backup_timestamp: When backup was created
                - file_path: Path to backup file

            Sorted by backup timestamp (newest first)

        Example:
            >>> repo = HallOfFameRepository()
            >>> failures = repo.list_backup_failures()
            >>> for failure in failures:
            ...     print(f"{failure['genome_id']}: {failure['error_message']}")
        """
        failures = []

        for backup_file in self.backup_dir.glob('*_failed.json'):
            try:
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)

                metadata = backup_data.get('_backup_metadata', {})

                failures.append({
                    'genome_id': backup_data.get('genome_id', 'unknown'),
                    'intended_tier': metadata.get('intended_tier', 'unknown'),
                    'error_message': metadata.get('error_message', 'unknown'),
                    'backup_timestamp': metadata.get('backup_timestamp', 'unknown'),
                    'file_path': str(backup_file)
                })

            except Exception as e:
                _logger.error(f"Failed to read backup file {backup_file}: {e}")

        # Sort by timestamp (newest first)
        failures.sort(key=lambda x: x['backup_timestamp'], reverse=True)

        return failures

    def cleanup_old_backups(self, keep_last_n: int = 100, days_threshold: int = 30) -> int:
        """
        Clean up old backup files to prevent directory growth.

        Cleanup Strategy:
            1. Keep last N most recent backups
            2. Delete backups older than threshold
            3. Protect backups from last 7 days

        Args:
            keep_last_n: Always keep this many most recent backups (default: 100)
            days_threshold: Delete backups older than this (default: 30 days)

        Returns:
            Number of backup files deleted

        Example:
            >>> repo = HallOfFameRepository()
            >>> deleted = repo.cleanup_old_backups(keep_last_n=100, days_threshold=30)
            >>> print(f"Deleted {deleted} old backups")
        """
        backup_files = list(self.backup_dir.glob('*_failed.json'))

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Always keep last N
        protected_files = set(backup_files[:keep_last_n])

        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        protection_date = datetime.now() - timedelta(days=7)  # Protect last 7 days

        deleted_count = 0

        for backup_file in backup_files:
            # Skip protected files
            if backup_file in protected_files:
                continue

            # Get file modification time
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

            # Protect recent backups (last 7 days)
            if mtime >= protection_date:
                continue

            # Delete if older than threshold
            if mtime < cutoff_date:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                    _logger.info(f"Deleted old backup: {backup_file.name}")
                except Exception as e:
                    _logger.error(f"Failed to delete backup {backup_file.name}: {e}")

        return deleted_count

    def verify_backup_recovery(self) -> Dict[str, any]:
        """
        Verify that backup files can be loaded and restored.

        Test Process:
            1. Scan all backup files
            2. Attempt to load JSON data
            3. Validate genome structure
            4. Report success/failure statistics

        Returns:
            Dictionary containing:
                - total_backups: Total backup files found
                - valid_backups: Number of valid, recoverable backups
                - invalid_backups: Number of corrupted/invalid backups
                - validation_errors: List of error messages
                - success_rate: Percentage of valid backups

        Example:
            >>> repo = HallOfFameRepository()
            >>> report = repo.verify_backup_recovery()
            >>> print(f"Success rate: {report['success_rate']:.1f}%")
        """
        backup_files = list(self.backup_dir.glob('*_failed.json'))

        total_backups = len(backup_files)
        valid_backups = 0
        invalid_backups = 0
        validation_errors = []

        for backup_file in backup_files:
            try:
                # Attempt to load JSON
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)

                # Validate required fields
                required_fields = ['template_name', 'parameters', 'metrics', 'created_at']
                missing_fields = [field for field in required_fields if field not in backup_data]

                if missing_fields:
                    raise ValueError(f"Missing fields: {', '.join(missing_fields)}")

                # Validate data types
                if not isinstance(backup_data['parameters'], dict):
                    raise ValueError("Field 'parameters' must be a dictionary")
                if not isinstance(backup_data['metrics'], dict):
                    raise ValueError("Field 'metrics' must be a dictionary")

                # Backup is valid
                valid_backups += 1

            except Exception as e:
                invalid_backups += 1
                validation_errors.append({
                    'file': backup_file.name,
                    'error': str(e)
                })
                _logger.warning(f"Invalid backup file {backup_file.name}: {e}")

        # Calculate success rate
        success_rate = (valid_backups / total_backups * 100) if total_backups > 0 else 100.0

        return {
            'total_backups': total_backups,
            'valid_backups': valid_backups,
            'invalid_backups': invalid_backups,
            'validation_errors': validation_errors,
            'success_rate': success_rate
        }

    def save_strategy(self, strategy, tier: str) -> None:
        """
        Save Factor Graph Strategy to tier-based storage.

        Uses Strategy.to_dict() for serialization and saves to tier-based
        JSON file (champion_strategy.json, contender_strategy.json, etc.).

        Args:
            strategy: Strategy object to persist (from src.evolution.types)
            tier: Storage tier ('champions', 'contenders', 'archive')

        Raises:
            ValueError: If tier is invalid

        Example:
            >>> from src.evolution.types import Strategy
            >>> repo = HallOfFameRepository()
            >>> repo.save_strategy(strategy, tier='champions')
        """
        # Validate tier
        tier_path = self._get_tier_path(tier)

        # Serialize strategy using to_dict()
        try:
            strategy_dict = strategy.to_dict()
        except Exception as e:
            _logger.error(f"Failed to serialize strategy {strategy.id}: {e}")
            raise

        # Save to tier-based file (e.g., champion_strategy.json)
        filename = f"{tier[:-1]}_strategy.json"  # Remove 's' from plural tier name
        file_path = tier_path / filename

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(strategy_dict, f, indent=2, ensure_ascii=False)
            _logger.info(f"Saved strategy {strategy.id} to {tier}/{filename}")
        except (IOError, OSError) as e:
            _logger.error(f"Failed to save strategy to {file_path}: {e}")
            raise

    def load_strategy(self, tier: str):
        """
        Load Factor Graph Strategy from tier-based storage.

        Uses Strategy.from_dict() for deserialization and loads from tier-based
        JSON file (champion_strategy.json, contender_strategy.json, etc.).

        Args:
            tier: Storage tier to load from ('champions', 'contenders', 'archive')

        Returns:
            Strategy object if found and valid, None otherwise

        Example:
            >>> repo = HallOfFameRepository()
            >>> strategy = repo.load_strategy(tier='champions')
            >>> if strategy:
            ...     print(f"Loaded: {strategy.id}")
        """
        # Import Strategy here to avoid circular dependency
        from src.evolution.types import Strategy

        # Validate tier
        tier_path = self._get_tier_path(tier)

        # Load from tier-based file
        filename = f"{tier[:-1]}_strategy.json"  # Remove 's' from plural tier name
        file_path = tier_path / filename

        if not file_path.exists():
            _logger.debug(f"No strategy file found at {file_path}")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                strategy_dict = json.load(f)

            # Deserialize using Strategy.from_dict()
            strategy = Strategy.from_dict(strategy_dict)
            _logger.info(f"Loaded strategy {strategy.id} from {tier}/{filename}")
            return strategy

        except json.JSONDecodeError as e:
            _logger.error(f"Failed to parse JSON from {file_path}: {e}")
            return None
        except (IOError, OSError) as e:
            _logger.error(f"Failed to load strategy from {file_path}: {e}")
            return None
        except Exception as e:
            _logger.error(f"Failed to deserialize strategy from {file_path}: {e}")
            return None
