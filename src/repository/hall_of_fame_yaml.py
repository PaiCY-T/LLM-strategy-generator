"""
Hall of Fame Repository with YAML Serialization
================================================

YAML-based strategy genome storage with tier-based classification and novelty scoring.

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

Key Differences from JSON-based System:
    - Human-readable YAML format for easy inspection
    - ISO 8601 timestamp formatting
    - Proper handling of nested structures
    - Enhanced readability for manual review
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import traceback

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    logging.warning("PyYAML not available. Install with: pip install pyyaml")

from .novelty_scorer import NoveltyScorer, DUPLICATE_THRESHOLD


# Configure logger for repository operations
_logger = logging.getLogger(__name__)


# Tier classification thresholds
CHAMPION_THRESHOLD = 2.0    # Sharpe ≥ 2.0
CONTENDER_THRESHOLD = 1.5   # Sharpe ≥ 1.5


@dataclass
class StrategyGenome:
    """
    Strategy genome data structure for YAML serialization.

    Attributes:
        iteration_num: Iteration number when strategy was generated
        code: Python code of the strategy
        parameters: Dictionary of parameter values
        metrics: Performance metrics dictionary (must include sharpe_ratio)
        success_patterns: Extracted success patterns from performance attribution
        timestamp: ISO 8601 formatted timestamp (auto-generated if not provided)
        genome_id: Unique identifier (auto-generated from timestamp and Sharpe)
    """
    iteration_num: int
    code: str
    parameters: Dict
    metrics: Dict
    success_patterns: Optional[Dict] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    genome_id: Optional[str] = None

    def __post_init__(self):
        """Generate genome_id if not provided using ISO 8601 timestamp."""
        if self.genome_id is None:
            # Format: iter{num}_{timestamp}_{sharpe}
            # Use ISO 8601 timestamp for consistency
            timestamp_str = self.timestamp.replace(':', '').replace('-', '').split('.')[0]
            sharpe = self.metrics.get('sharpe_ratio', 0.0)
            self.genome_id = f"iter{self.iteration_num}_{timestamp_str}_{sharpe:.2f}"

    def to_dict(self) -> Dict:
        """
        Convert genome to dictionary for YAML serialization.

        Returns:
            Dictionary representation with properly structured nested data

        Example:
            >>> genome = StrategyGenome(...)
            >>> genome_dict = genome.to_dict()
        """
        data = {
            'genome_id': self.genome_id,
            'iteration_num': self.iteration_num,
            'timestamp': self.timestamp,  # ISO 8601 format
            'code': self.code,
            'parameters': self.parameters,
            'metrics': self.metrics
        }

        # Include optional fields if present
        if self.success_patterns is not None:
            data['success_patterns'] = self.success_patterns

        return data

    def to_yaml(self) -> str:
        """
        Serialize genome to YAML string with human-readable formatting.

        Returns:
            YAML-formatted string

        Raises:
            RuntimeError: If PyYAML is not installed

        Example:
            >>> genome = StrategyGenome(...)
            >>> yaml_str = genome.to_yaml()
        """
        if not YAML_AVAILABLE:
            raise RuntimeError("PyYAML not installed. Install with: pip install pyyaml")

        data = self.to_dict()

        # Use human-readable YAML formatting
        # default_flow_style=False ensures block style for nested structures
        # sort_keys=False preserves logical ordering (genome_id first)
        # allow_unicode=True handles Chinese characters in dataset names
        return yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            indent=2
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> 'StrategyGenome':
        """
        Deserialize genome from YAML string.

        Args:
            yaml_str: YAML-formatted string

        Returns:
            StrategyGenome object

        Raises:
            RuntimeError: If PyYAML is not installed
            yaml.YAMLError: If YAML parsing fails
            ValueError: If required fields are missing or invalid

        Example:
            >>> yaml_str = '''
            ... genome_id: iter100_20251016_120000_2.30
            ... iteration_num: 100
            ... ...
            ... '''
            >>> genome = StrategyGenome.from_yaml(yaml_str)
        """
        if not YAML_AVAILABLE:
            raise RuntimeError("PyYAML not installed. Install with: pip install pyyaml")

        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML: {e}")

        # Validate required fields
        required_fields = ['iteration_num', 'code', 'parameters', 'metrics', 'timestamp']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(
                f"Malformed YAML: missing required field(s): {', '.join(missing_fields)}"
            )

        # Validate data types
        if not isinstance(data['iteration_num'], int):
            raise ValueError("Field 'iteration_num' must be an integer")
        if not isinstance(data['code'], str):
            raise ValueError("Field 'code' must be a string")
        if not isinstance(data['parameters'], dict):
            raise ValueError("Field 'parameters' must be a dictionary")
        if not isinstance(data['metrics'], dict):
            raise ValueError("Field 'metrics' must be a dictionary")
        if 'sharpe_ratio' not in data['metrics']:
            raise ValueError("Field 'metrics' must include 'sharpe_ratio'")

        return cls(
            iteration_num=data['iteration_num'],
            code=data['code'],
            parameters=data['parameters'],
            metrics=data['metrics'],
            success_patterns=data.get('success_patterns'),
            timestamp=data['timestamp'],
            genome_id=data.get('genome_id')
        )

    def save_to_file(self, file_path: Path) -> bool:
        """
        Save genome to YAML file.

        Args:
            file_path: Path to save the YAML file

        Returns:
            True if successful, False otherwise

        Example:
            >>> genome.save_to_file(Path('hall_of_fame/champions/genome_123.yaml'))
            True
        """
        if not YAML_AVAILABLE:
            _logger.error("PyYAML not installed. Cannot save YAML file.")
            return False

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.to_yaml())
            return True
        except (IOError, OSError) as e:
            _logger.error(f"Failed to save genome to {file_path}: {e}")
            return False

    @classmethod
    def load_from_file(cls, file_path: Path) -> Optional['StrategyGenome']:
        """
        Load genome from YAML file.

        Args:
            file_path: Path to the YAML file

        Returns:
            StrategyGenome object if successful, None otherwise

        Example:
            >>> genome = StrategyGenome.load_from_file(Path('champions/genome_123.yaml'))
        """
        if not YAML_AVAILABLE:
            _logger.error("PyYAML not installed. Cannot load YAML file.")
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml_str = f.read()
            return cls.from_yaml(yaml_str)
        except (IOError, OSError) as e:
            _logger.error(f"Failed to load genome from {file_path}: {e}")
            return None
        except yaml.YAMLError as e:
            _logger.error(f"Failed to parse YAML from {file_path}: {e}")
            return None
        except ValueError as e:
            _logger.error(f"Invalid genome data in {file_path}: {e}")
            return None


class HallOfFameRepository:
    """
    YAML-based repository for managing validated strategy genomes.

    Features:
        - Tier-based storage (Champions, Contenders, Archive)
        - YAML serialization with human-readable format
        - Novelty scoring and duplicate detection
        - Backup mechanisms for failed operations
        - Query and retrieval methods

    Usage:
        >>> repo = HallOfFameRepository()
        >>> success, msg = repo.add_strategy(genome)
        >>> champions = repo.get_champions()
    """

    def __init__(self, base_path: str = "hall_of_fame", test_mode: bool = False):
        """
        Initialize Hall of Fame repository with YAML storage.

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
            RuntimeError: If PyYAML is not installed
        """
        if not YAML_AVAILABLE:
            raise RuntimeError(
                "PyYAML not installed. Install with: pip install pyyaml"
            )

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
        Load all existing strategy genomes from YAML files into cache.

        Scans all tier directories and loads valid YAML files.
        Populates _cache for fast retrieval and novelty checking.
        Pre-computes and caches factor vectors for performance optimization.
        """
        for tier in ['champions', 'contenders', 'archive']:
            tier_path = self._get_tier_path(tier)
            yaml_files = list(tier_path.glob('*.yaml')) + list(tier_path.glob('*.yml'))

            for yaml_file in yaml_files:
                genome = StrategyGenome.load_from_file(yaml_file)
                if genome is not None:
                    self._cache[tier].append(genome)

                    # Pre-compute and cache factor vector for novelty scoring
                    if genome.code is not None and genome.genome_id is not None:
                        vector = self.novelty_scorer.get_factor_vector(genome.code)
                        self._vector_cache[genome.genome_id] = vector

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

    def add_strategy(self, genome: StrategyGenome) -> Tuple[bool, str]:
        """
        Add a strategy genome to the repository with novelty checking.

        Workflow:
            1. Validate metrics contain required fields
            2. Calculate novelty score using cached vectors
            3. Reject duplicates (novelty < 0.2)
            4. Classify tier based on Sharpe ratio
            5. Serialize to YAML and save to tier directory
            6. Update in-memory cache

        Args:
            genome: StrategyGenome object to add

        Returns:
            Tuple of (success: bool, message: str)

        Examples:
            >>> genome = StrategyGenome(
            ...     iteration_num=100,
            ...     code="close = data.get('price:收盤價')\\n...",
            ...     parameters={'n_stocks': 20},
            ...     metrics={'sharpe_ratio': 2.3}
            ... )
            >>> success, msg = repo.add_strategy(genome)
            >>> print(success, msg)
            True Strategy added to champions tier (novelty: 0.85)
        """
        # Validate required metrics
        if 'sharpe_ratio' not in genome.metrics:
            return False, "Metrics must include 'sharpe_ratio'"

        # Calculate novelty score if code provided
        novelty_score = None
        similarity_info = None

        if genome.code is not None:
            # Get all existing factor vectors from cache (performance optimized)
            existing_vectors = []
            genome_id_mapping = []  # Track which genome each vector corresponds to

            for tier in ['champions', 'contenders', 'archive']:
                for cached_genome in self._cache[tier]:
                    if cached_genome.code is not None and cached_genome.genome_id in self._vector_cache:
                        existing_vectors.append(self._vector_cache[cached_genome.genome_id])
                        genome_id_mapping.append(cached_genome.genome_id)

            # Calculate novelty using cached vectors (avoids O(n) repeated extraction)
            novelty_score, similarity_info = self.novelty_scorer.calculate_novelty_score_with_cache(
                genome.code,
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
        sharpe_ratio = genome.metrics['sharpe_ratio']
        tier = self._classify_tier(sharpe_ratio)

        # Save genome to tier directory
        success, message = self._save_genome(genome, tier)

        if not success:
            # Backup failed serialization
            self._backup_genome(genome, tier, message)
            return False, f"Failed to save genome: {message}"

        # Update in-memory cache
        self._cache[tier].append(genome)

        # Cache factor vector for future novelty scoring
        if genome.code is not None and genome.genome_id is not None:
            vector = self.novelty_scorer.get_factor_vector(genome.code)
            self._vector_cache[genome.genome_id] = vector

        # Build success message
        msg_parts = [f"Strategy added to {tier} tier (Sharpe: {sharpe_ratio:.2f}, ID: {genome.genome_id})"]
        if novelty_score is not None:
            msg_parts.append(f"novelty: {novelty_score:.3f}")

        return True, " | ".join(msg_parts)

    def _save_genome(self, genome: StrategyGenome, tier: str) -> Tuple[bool, str]:
        """
        Save genome to tier directory as YAML file.

        Args:
            genome: StrategyGenome object to save
            tier: Target tier ('champions', 'contenders', 'archive')

        Returns:
            Tuple of (success: bool, message: str)

        File Naming:
            {genome_id}.yaml (e.g., iter100_20251016_120000_2.30.yaml)
        """
        try:
            # Get tier directory
            tier_path = self._get_tier_path(tier)

            # Create file path
            filename = f"{genome.genome_id}.yaml"
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
        Backup genome when YAML serialization fails.

        Backup Mechanism:
            1. Convert genome to dictionary
            2. Add error metadata (tier, error, timestamp, stack trace)
            3. Save to backup/ directory as YAML
            4. Log failure for investigation

        Args:
            genome: StrategyGenome object that failed to save
            tier: Intended tier
            error_msg: Error message from failed save attempt

        Backup File:
            backup/{genome_id}_failed.yaml
        """
        try:
            # Create backup data
            backup_data = genome.to_dict()
            backup_data['_backup_metadata'] = {
                'intended_tier': tier,
                'error_message': error_msg,
                'backup_timestamp': datetime.now().isoformat(),
                'stack_trace': traceback.format_exc() if error_msg else None
            }

            # Save to backup directory
            filename = f"{genome.genome_id}_failed.yaml"
            file_path = self.backup_dir / filename

            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(backup_data, f, default_flow_style=False, allow_unicode=True, indent=2)

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
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Find similar strategies using cosine distance.

        Algorithm:
            1. Extract factor vector from input strategy code
            2. Calculate cosine distance to all existing strategies
            3. Filter strategies within max_distance threshold
            4. Sort by similarity (most similar first)
            5. Include similarity score and shared factors

        Args:
            strategy_code: Python code of strategy to compare
            max_distance: Maximum cosine distance threshold (default: 0.3)
                         Distance 0.0 = identical, 1.0 = completely different
            limit: Optional maximum number of results to return

        Returns:
            List of dictionaries containing:
                - genome: StrategyGenome object
                - distance: Cosine distance (0.0-1.0)
                - similarity: Similarity score (1.0-distance)
                - shared_factors: List of common factor names
                - tier: Tier classification

        Example:
            >>> code = "close = data.get('price:收盤價')\\n..."
            >>> similar = repo.query_similar(code, max_distance=0.3)
            >>> for result in similar[:5]:
            ...     print(f"{result['genome'].genome_id}: "
            ...           f"distance={result['distance']:.3f}, "
            ...           f"shared={len(result['shared_factors'])}")

        Performance:
            Target: <500ms for 100 strategies
            Uses pre-computed factor vector cache for O(n) complexity
        """
        # Extract factor vector from input code
        input_vector = self.novelty_scorer.get_factor_vector(strategy_code)
        input_factors = set(input_vector.keys())

        results = []

        # Compare with all cached strategies
        for tier in ['champions', 'contenders', 'archive']:
            for genome in self._cache[tier]:
                # Skip strategies without code
                if genome.code is None or genome.genome_id is None:
                    continue

                # Get cached vector (performance optimization)
                if genome.genome_id in self._vector_cache:
                    existing_vector = self._vector_cache[genome.genome_id]
                else:
                    # Compute and cache if missing
                    existing_vector = self.novelty_scorer.get_factor_vector(genome.code)
                    self._vector_cache[genome.genome_id] = existing_vector

                # Calculate cosine distance
                distance = self.novelty_scorer._calculate_cosine_distance(
                    input_vector,
                    existing_vector
                )

                # Filter by threshold
                if distance <= max_distance:
                    # Find shared factors
                    existing_factors = set(existing_vector.keys())
                    shared_factors = list(input_factors & existing_factors)

                    results.append({
                        'genome': genome,
                        'distance': distance,
                        'similarity': 1.0 - distance,
                        'shared_factors': shared_factors,
                        'tier': tier
                    })

        # Sort by distance (most similar first = lowest distance)
        results.sort(key=lambda x: x['distance'])

        # Apply limit if specified
        if limit is not None:
            results = results[:limit]

        _logger.info(
            f"Similarity query found {len(results)} strategies within "
            f"distance {max_distance} (searched {sum(len(self._cache[t]) for t in ['champions', 'contenders', 'archive'])} total)"
        )

        return results

    def get_statistics(self) -> Dict:
        """
        Get comprehensive repository statistics.

        Returns:
            Dictionary containing:
                - Tier counts (champions, contenders, archive, total)
                - Backup statistics (total_backups)
                - Storage format information

        Example:
            >>> repo.get_statistics()
            {
                'champions': 15,
                'contenders': 42,
                'archive': 128,
                'total': 185,
                'total_backups': 3,
                'storage_format': 'YAML'
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
        backup_files = list(self.backup_dir.glob('*_failed.yaml'))
        stats['total_backups'] = len(backup_files)

        # Storage format
        stats['storage_format'] = 'YAML'

        return stats
