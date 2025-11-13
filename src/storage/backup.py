"""
Automatic Database Backup Scheduler for Finlab Backtesting System.

Provides automated daily backups with configurable retention policy
and cleanup of old backups to manage disk space.

Features:
    - Daily backup scheduling with timestamp
    - Configurable retention period (default: 30 days)
    - Automatic cleanup of old backups
    - Thread-safe backup operations
    - Comprehensive error handling and logging

Example:
    >>> from src.storage.backup import BackupScheduler
    >>> from pathlib import Path
    >>>
    >>> db_path = Path("./storage/backtest.db")
    >>> backup_dir = Path("./storage/backups")
    >>>
    >>> scheduler = BackupScheduler(
    ...     db_path=db_path,
    ...     backup_dir=backup_dir,
    ...     retention_days=30
    ... )
    >>>
    >>> # Perform immediate backup
    >>> backup_path = scheduler.backup_now()
    >>> print(f"Backup created at: {backup_path}")
    >>>
    >>> # Start automatic daily backups (in separate thread)
    >>> scheduler.start_daily_backups()
    >>>
    >>> # Stop scheduler when done
    >>> scheduler.stop()
"""

import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.exceptions import StorageError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BackupScheduler:
    """
    Automated backup scheduler with retention management.

    Manages database backups with daily scheduling, automatic cleanup
    of old backups, and thread-safe operations.

    Attributes:
        db_path: Path to SQLite database file
        backup_dir: Directory to store backups
        retention_days: Number of days to retain backups (default: 30)
        _running: Flag indicating if scheduler is active
        _backup_thread: Background thread for scheduled backups
        _stop_event: Event to signal thread shutdown
    """

    def __init__(
        self,
        db_path: Path,
        backup_dir: Path,
        retention_days: int = 30,
    ) -> None:
        """
        Initialize backup scheduler.

        Args:
            db_path: Path to SQLite database file
            backup_dir: Directory to store backups
            retention_days: Number of days to retain backups

        Raises:
            ValueError: If retention_days is less than 1

        Example:
            >>> scheduler = BackupScheduler(
            ...     db_path=Path("./storage/backtest.db"),
            ...     backup_dir=Path("./storage/backups"),
            ...     retention_days=30
            ... )
        """
        if retention_days < 1:
            raise ValueError(
                f"retention_days must be >= 1, got {retention_days}"
            )

        self.db_path = db_path
        self.backup_dir = backup_dir
        self.retention_days = retention_days

        self._running = False
        self._backup_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Create backup directory if needed
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"BackupScheduler initialized: "
            f"db={db_path}, backup_dir={backup_dir}, "
            f"retention={retention_days} days"
        )

    def backup_now(self) -> Path:
        """
        Perform immediate backup of database.

        Creates a timestamped copy of the database file in the
        backup directory.

        Returns:
            Path to created backup file

        Raises:
            StorageError: If backup operation fails

        Example:
            >>> backup_path = scheduler.backup_now()
            >>> print(f"Backup created: {backup_path}")
        """
        if not self.db_path.exists():
            raise StorageError(
                f"Database file not found: {self.db_path}"
            )

        try:
            # Generate timestamped backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backtest_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename

            # Copy database file
            shutil.copy2(self.db_path, backup_path)

            logger.info(f"Database backed up to: {backup_path}")
            return backup_path

        except Exception as e:
            raise StorageError(
                f"Backup operation failed: {e}"
            ) from e

    def cleanup_old_backups(self) -> int:
        """
        Remove backups older than retention period.

        Scans backup directory and deletes files older than
        retention_days.

        Returns:
            Number of backups removed

        Raises:
            StorageError: If cleanup operation fails

        Example:
            >>> removed_count = scheduler.cleanup_old_backups()
            >>> print(f"Removed {removed_count} old backups")
        """
        try:
            cutoff_date = datetime.now() - timedelta(
                days=self.retention_days
            )
            removed_count = 0

            # Find all backup files
            backup_files = self._get_backup_files()

            for backup_file in backup_files:
                # Get file modification time
                file_time = datetime.fromtimestamp(
                    backup_file.stat().st_mtime
                )

                # Remove if older than cutoff
                if file_time < cutoff_date:
                    backup_file.unlink()
                    removed_count += 1
                    logger.debug(f"Removed old backup: {backup_file}")

            if removed_count > 0:
                logger.info(
                    f"Cleaned up {removed_count} backups older than "
                    f"{self.retention_days} days"
                )

            return removed_count

        except Exception as e:
            raise StorageError(
                f"Backup cleanup failed: {e}"
            ) from e

    def _get_backup_files(self) -> List[Path]:
        """
        Get list of all backup files in backup directory.

        Returns:
            List of backup file paths
        """
        if not self.backup_dir.exists():
            return []

        return sorted(
            self.backup_dir.glob("backtest_backup_*.db"),
            key=lambda p: p.stat().st_mtime,
        )

    def start_daily_backups(
        self, hour: int = 2, minute: int = 0
    ) -> None:
        """
        Start automatic daily backup scheduler in background thread.

        Creates backups daily at specified time and performs cleanup
        of old backups.

        Args:
            hour: Hour of day for backup (0-23, default: 2 AM)
            minute: Minute of hour for backup (0-59, default: 0)

        Raises:
            ValueError: If hour or minute are invalid
            RuntimeError: If scheduler is already running

        Example:
            >>> # Start daily backups at 2:00 AM
            >>> scheduler.start_daily_backups()
            >>>
            >>> # Start daily backups at 3:30 AM
            >>> scheduler.start_daily_backups(hour=3, minute=30)
        """
        if not (0 <= hour <= 23):
            raise ValueError(f"hour must be 0-23, got {hour}")
        if not (0 <= minute <= 59):
            raise ValueError(f"minute must be 0-59, got {minute}")

        if self._running:
            raise RuntimeError("Backup scheduler is already running")

        self._running = True
        self._stop_event.clear()

        # Start background thread
        self._backup_thread = threading.Thread(
            target=self._backup_loop,
            args=(hour, minute),
            daemon=True,
            name="BackupScheduler",
        )
        self._backup_thread.start()

        logger.info(
            f"Daily backup scheduler started (scheduled for "
            f"{hour:02d}:{minute:02d})"
        )

    def _backup_loop(self, hour: int, minute: int) -> None:
        """
        Background thread loop for daily backups.

        Args:
            hour: Hour of day for backup
            minute: Minute of hour for backup
        """
        logger.debug("Backup scheduler thread started")

        while not self._stop_event.is_set():
            try:
                # Calculate next backup time
                now = datetime.now()
                next_backup = now.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )

                # If scheduled time has passed today, schedule for tomorrow
                if next_backup <= now:
                    next_backup += timedelta(days=1)

                # Calculate wait time in seconds
                wait_seconds = (next_backup - now).total_seconds()

                logger.debug(
                    f"Next backup scheduled at {next_backup} "
                    f"(in {wait_seconds:.0f} seconds)"
                )

                # Wait until scheduled time (or stop signal)
                if self._stop_event.wait(timeout=wait_seconds):
                    # Stop signal received
                    break

                # Perform backup
                logger.info("Performing scheduled backup")
                self.backup_now()

                # Cleanup old backups
                self.cleanup_old_backups()

            except Exception as e:
                logger.error(
                    f"Error in backup scheduler loop: {e}",
                    exc_info=True
                )
                # Wait 1 hour before retrying
                if self._stop_event.wait(timeout=3600):
                    break

        logger.debug("Backup scheduler thread stopped")

    def stop(self) -> None:
        """
        Stop the backup scheduler and wait for thread to finish.

        Blocks until background thread completes. Safe to call
        multiple times.

        Example:
            >>> scheduler.start_daily_backups()
            >>> # ... later ...
            >>> scheduler.stop()
        """
        if not self._running:
            return

        logger.info("Stopping backup scheduler")
        self._running = False
        self._stop_event.set()

        # Wait for thread to finish (with timeout)
        if self._backup_thread and self._backup_thread.is_alive():
            self._backup_thread.join(timeout=5.0)

        logger.info("Backup scheduler stopped")

    def get_backup_info(self) -> Dict[str, Any]:
        """
        Get information about current backups.

        Returns:
            Dictionary containing:
                - total_backups: int
                - oldest_backup: datetime or None
                - newest_backup: datetime or None
                - total_size_mb: float

        Example:
            >>> info = scheduler.get_backup_info()
            >>> print(f"Total backups: {info['total_backups']}")
            >>> print(f"Total size: {info['total_size_mb']:.2f} MB")
        """
        backup_files = self._get_backup_files()

        oldest_backup: Optional[datetime] = None
        newest_backup: Optional[datetime] = None

        if backup_files:
            # Get oldest and newest
            oldest_backup = datetime.fromtimestamp(
                backup_files[0].stat().st_mtime
            )
            newest_backup = datetime.fromtimestamp(
                backup_files[-1].stat().st_mtime
            )

        info: Dict[str, Any] = {
            "total_backups": len(backup_files),
            "oldest_backup": oldest_backup,
            "newest_backup": newest_backup,
            "total_size_mb": 0.0,
        }

        if backup_files:

            # Calculate total size
            total_bytes = sum(f.stat().st_size for f in backup_files)
            info["total_size_mb"] = total_bytes / (1024 * 1024)

        return info
