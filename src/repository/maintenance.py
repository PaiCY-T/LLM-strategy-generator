"""
Hall of Fame Maintenance Manager
=================================

Automated maintenance for Hall of Fame repository including archival,
compression, integrity validation, and backup management.

Features:
    - Automatic archival of low-performing contenders
    - Compression of old strategies (6+ months)
    - YAML file integrity validation
    - Rolling backup management (7-day retention)
    - Cleanup of corrupted or orphaned files

Usage:
    from src.repository import HallOfFameRepository, MaintenanceManager

    repo = HallOfFameRepository()
    manager = MaintenanceManager(repo)

    # Archive low performers when contenders exceed 100
    archived = manager.archive_low_performers()

    # Compress strategies older than 6 months
    compressed = manager.compress_old_strategies()

    # Validate YAML integrity
    corrupt_files = manager.validate_integrity()

    # Cleanup old backups (keep last 7 days)
    removed = manager.cleanup_old_backups()

Requirements:
    - Requirement 2.8: Hall of Fame archival and compression
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
import gzip
import shutil
import yaml

# Configure logger
_logger = logging.getLogger(__name__)


def _load_maintenance_config(config_path: str = 'config/learning_system.yaml') -> Dict:
    """
    Load maintenance configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Dict with maintenance configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is malformed
    """
    config_file = Path(config_path)

    if not config_file.exists():
        _logger.warning(f"Config file not found: {config_path}, using defaults")
        return {}

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        return config_data.get('maintenance', {})

    except yaml.YAMLError as e:
        _logger.error(f"Failed to parse config file {config_path}: {e}")
        return {}
    except Exception as e:
        _logger.error(f"Failed to load config file {config_path}: {e}")
        return {}


class MaintenanceManager:
    """
    Maintenance manager for Hall of Fame repository.

    Provides automated maintenance operations including:
        - Low performer archival
        - Old strategy compression
        - YAML integrity validation
        - Rolling backup cleanup

    Attributes:
        repository: HallOfFameRepository instance
        logger: Python logger for operations

    Example:
        >>> from src.repository import HallOfFameRepository, MaintenanceManager
        >>> repo = HallOfFameRepository()
        >>> manager = MaintenanceManager(repo)
        >>> archived = manager.archive_low_performers()
        >>> print(f"Archived {archived} low performers")
    """

    # Default thresholds (used if config not available)
    _DEFAULT_CONTENDER_THRESHOLD = 100
    _DEFAULT_ARCHIVAL_PERCENTAGE = 0.20
    _DEFAULT_COMPRESSION_AGE_DAYS = 180
    _DEFAULT_BACKUP_RETENTION_DAYS = 7

    def __init__(
        self,
        repository,
        logger: Optional[logging.Logger] = None,
        config_path: str = 'config/learning_system.yaml'
    ):
        """
        Initialize maintenance manager.

        Args:
            repository: HallOfFameRepository instance
            logger: Optional logger for operations
            config_path: Path to configuration file (default: config/learning_system.yaml)
        """
        self.repository = repository
        self.logger = logger or _logger

        # Load configuration from YAML
        config = _load_maintenance_config(config_path)

        # Set thresholds from config or use defaults
        self.CONTENDER_SIZE_THRESHOLD = config.get(
            'contender_threshold', self._DEFAULT_CONTENDER_THRESHOLD
        )
        self.ARCHIVAL_PERCENTAGE = config.get(
            'archival_percentage', self._DEFAULT_ARCHIVAL_PERCENTAGE
        )
        self.COMPRESSION_AGE_DAYS = config.get(
            'compression_age_days', self._DEFAULT_COMPRESSION_AGE_DAYS
        )
        self.BACKUP_RETENTION_DAYS = config.get(
            'backup_retention_days', self._DEFAULT_BACKUP_RETENTION_DAYS
        )

        self.logger.info(
            f"MaintenanceManager initialized with config: "
            f"contender_threshold={self.CONTENDER_SIZE_THRESHOLD}, "
            f"archival_percentage={self.ARCHIVAL_PERCENTAGE}, "
            f"compression_age_days={self.COMPRESSION_AGE_DAYS}, "
            f"backup_retention_days={self.BACKUP_RETENTION_DAYS}"
        )

    def archive_low_performers(self) -> int:
        """
        Archive lowest 20% of contenders when size exceeds 100.

        Algorithm:
            1. Check if contenders count > CONTENDER_SIZE_THRESHOLD (100)
            2. Calculate number to archive (lowest 20%)
            3. Sort contenders by Sharpe ratio ascending
            4. Move lowest performers to archive tier
            5. Update repository cache and file locations

        Returns:
            Number of strategies archived

        Example:
            >>> manager = MaintenanceManager(repo)
            >>> archived = manager.archive_low_performers()
            >>> print(f"Archived {archived} contenders")

        Requirements:
            - Requirement 2.8: Archival logic
        """
        contenders = self.repository._cache.get('contenders', [])
        contender_count = len(contenders)

        # Check threshold
        if contender_count <= self.CONTENDER_SIZE_THRESHOLD:
            self.logger.info(
                f"Archival skipped: {contender_count} contenders "
                f"(threshold: {self.CONTENDER_SIZE_THRESHOLD})"
            )
            return 0

        # Calculate number to archive
        num_to_archive = int(contender_count * self.ARCHIVAL_PERCENTAGE)

        # Sort by Sharpe ratio ascending (worst performers first)
        sorted_contenders = sorted(
            contenders,
            key=lambda g: g.metrics.get('sharpe_ratio', 0.0)
        )

        # Get lowest performers
        to_archive = sorted_contenders[:num_to_archive]

        archived_count = 0

        for genome in to_archive:
            try:
                # Move file from contenders to archive
                old_path = self.repository.contenders_dir / f"{genome.genome_id}.yaml"
                new_path = self.repository.archive_dir / f"{genome.genome_id}.yaml"

                if old_path.exists():
                    shutil.move(str(old_path), str(new_path))

                    # Update cache
                    self.repository._cache['contenders'].remove(genome)
                    self.repository._cache['archive'].append(genome)

                    archived_count += 1

                    self.logger.debug(
                        f"Archived {genome.genome_id} "
                        f"(Sharpe: {genome.metrics.get('sharpe_ratio', 0.0):.2f})"
                    )
                else:
                    self.logger.warning(
                        f"File not found for archival: {old_path}"
                    )

            except Exception as e:
                self.logger.error(
                    f"Failed to archive {genome.genome_id}: {str(e)}"
                )

        self.logger.info(
            f"Archived {archived_count}/{num_to_archive} low-performing contenders "
            f"(contender count: {contender_count} → {contender_count - archived_count})"
        )

        return archived_count

    def compress_old_strategies(
        self,
        age_days: Optional[int] = None
    ) -> int:
        """
        Compress strategies older than specified days using gzip.

        Algorithm:
            1. Scan all tiers for YAML files
            2. Check timestamp of each strategy
            3. If age > threshold, compress with gzip
            4. Replace .yaml with .yaml.gz
            5. Update file references if needed

        Args:
            age_days: Age threshold in days (default: 180 = 6 months)

        Returns:
            Number of files compressed

        Example:
            >>> manager.compress_old_strategies(age_days=180)
            42  # Compressed 42 files

        Requirements:
            - Requirement 2.8: Compression logic
        """
        age_threshold_days = age_days or self.COMPRESSION_AGE_DAYS
        threshold_date = datetime.now() - timedelta(days=age_threshold_days)

        compressed_count = 0

        # Scan all tiers
        for tier in ['champions', 'contenders', 'archive']:
            tier_path = self.repository._get_tier_path(tier)
            yaml_files = list(tier_path.glob('*.yaml'))

            for yaml_file in yaml_files:
                try:
                    # Skip if already compressed
                    if yaml_file.suffix == '.gz':
                        continue

                    # Load genome to check timestamp
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)

                    timestamp_str = data.get('timestamp')
                    if not timestamp_str:
                        continue

                    # Parse timestamp (ISO 8601)
                    timestamp = datetime.fromisoformat(timestamp_str)

                    # Check age
                    if timestamp < threshold_date:
                        # Compress file
                        gz_path = yaml_file.with_suffix('.yaml.gz')

                        with open(yaml_file, 'rb') as f_in:
                            with gzip.open(gz_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)

                        # Remove original
                        yaml_file.unlink()

                        compressed_count += 1

                        self.logger.debug(
                            f"Compressed {yaml_file.name} "
                            f"(age: {(datetime.now() - timestamp).days} days)"
                        )

                except Exception as e:
                    self.logger.error(
                        f"Failed to compress {yaml_file}: {str(e)}"
                    )

        self.logger.info(
            f"Compressed {compressed_count} strategies older than {age_threshold_days} days"
        )

        return compressed_count

    def validate_integrity(self) -> List[Dict]:
        """
        Validate YAML file integrity across all tiers.

        Algorithm:
            1. Scan all YAML files in all tiers
            2. Attempt to parse each file
            3. Validate required fields
            4. Report corrupted files

        Returns:
            List of dictionaries containing:
                - file_path: Path to corrupted file
                - tier: Tier name
                - error: Error message
                - error_type: 'parse_error' | 'missing_field' | 'invalid_data'

        Example:
            >>> corrupt_files = manager.validate_integrity()
            >>> for corrupt in corrupt_files:
            ...     print(f"Corrupt: {corrupt['file_path']} - {corrupt['error']}")

        Requirements:
            - Requirement 2.8: Integrity validation
        """
        corrupt_files = []
        total_checked = 0

        # Scan all tiers
        for tier in ['champions', 'contenders', 'archive']:
            tier_path = self.repository._get_tier_path(tier)
            yaml_files = list(tier_path.glob('*.yaml')) + list(tier_path.glob('*.yml'))

            for yaml_file in yaml_files:
                total_checked += 1

                try:
                    # Attempt to parse YAML
                    with open(yaml_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)

                    # Validate required fields
                    required_fields = [
                        'iteration_num', 'code', 'parameters',
                        'metrics', 'timestamp'
                    ]

                    for field in required_fields:
                        if field not in data:
                            corrupt_files.append({
                                'file_path': str(yaml_file),
                                'tier': tier,
                                'error': f"Missing required field: {field}",
                                'error_type': 'missing_field'
                            })
                            break

                    # Validate metrics contain sharpe_ratio
                    if 'metrics' in data and isinstance(data['metrics'], dict):
                        if 'sharpe_ratio' not in data['metrics']:
                            corrupt_files.append({
                                'file_path': str(yaml_file),
                                'tier': tier,
                                'error': "Missing 'sharpe_ratio' in metrics",
                                'error_type': 'invalid_data'
                            })

                except yaml.YAMLError as e:
                    corrupt_files.append({
                        'file_path': str(yaml_file),
                        'tier': tier,
                        'error': f"YAML parse error: {str(e)}",
                        'error_type': 'parse_error'
                    })

                except Exception as e:
                    corrupt_files.append({
                        'file_path': str(yaml_file),
                        'tier': tier,
                        'error': f"Validation error: {str(e)}",
                        'error_type': 'parse_error'
                    })

        if corrupt_files:
            self.logger.warning(
                f"Found {len(corrupt_files)} corrupted files out of {total_checked} checked"
            )
            for corrupt in corrupt_files:
                self.logger.warning(
                    f"  {corrupt['file_path']}: {corrupt['error']}"
                )
        else:
            self.logger.info(
                f"Integrity validation passed: {total_checked} files checked"
            )

        return corrupt_files

    def cleanup_old_backups(
        self,
        retention_days: Optional[int] = None
    ) -> int:
        """
        Remove backup files older than retention period.

        Algorithm:
            1. Scan backup directory
            2. Check file modification time
            3. Remove files older than retention_days

        Args:
            retention_days: Number of days to retain (default: 7)

        Returns:
            Number of backup files removed

        Example:
            >>> removed = manager.cleanup_old_backups(retention_days=7)
            >>> print(f"Removed {removed} old backups")

        Requirements:
            - Requirement 2.8: Backup management
        """
        retention = retention_days or self.BACKUP_RETENTION_DAYS
        threshold_date = datetime.now() - timedelta(days=retention)

        removed_count = 0

        # Scan backup directory
        backup_files = list(self.repository.backup_dir.glob('*_failed.yaml'))

        for backup_file in backup_files:
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)

                # Remove if older than threshold
                if mtime < threshold_date:
                    backup_file.unlink()
                    removed_count += 1

                    self.logger.debug(
                        f"Removed old backup: {backup_file.name} "
                        f"(age: {(datetime.now() - mtime).days} days)"
                    )

            except Exception as e:
                self.logger.error(
                    f"Failed to remove backup {backup_file}: {str(e)}"
                )

        self.logger.info(
            f"Removed {removed_count} backup files older than {retention} days"
        )

        return removed_count

    def run_all_maintenance(self) -> Dict[str, int]:
        """
        Run all maintenance operations in sequence.

        Order:
            1. Archive low performers
            2. Compress old strategies
            3. Validate integrity
            4. Cleanup old backups

        Returns:
            Dictionary with operation results:
                - archived: Number of strategies archived
                - compressed: Number of files compressed
                - corrupted: Number of corrupted files found
                - backups_removed: Number of backups cleaned up

        Example:
            >>> results = manager.run_all_maintenance()
            >>> print(f"Archived: {results['archived']}, "
            ...       f"Compressed: {results['compressed']}")
        """
        self.logger.info("Starting comprehensive maintenance...")

        results = {}

        # 1. Archive low performers
        results['archived'] = self.archive_low_performers()

        # 2. Compress old strategies
        results['compressed'] = self.compress_old_strategies()

        # 3. Validate integrity
        corrupt_files = self.validate_integrity()
        results['corrupted'] = len(corrupt_files)

        # 4. Cleanup old backups
        results['backups_removed'] = self.cleanup_old_backups()

        self.logger.info(
            f"Maintenance complete: "
            f"archived={results['archived']}, "
            f"compressed={results['compressed']}, "
            f"corrupted={results['corrupted']}, "
            f"backups_removed={results['backups_removed']}"
        )

        return results
