"""
Data management module for Finlab backtesting system.

This module provides data retrieval, caching, and freshness checking
functionality for Finlab financial data.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

from src.data.cache import DataCache
from src.data.downloader import FinlabDownloader
from src.data.freshness import FreshnessChecker
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataManager:
    """
    Central data management interface for Finlab data operations.

    Provides unified interface for downloading, caching, and managing
    financial data from Finlab API with automatic freshness checking
    and cache management.

    Attributes:
        cache_dir: Directory path for storing cached data files
        max_retries: Maximum number of retry attempts for downloads
        freshness_days: Number of days before cached data is considered stale
    """

    def __init__(
        self,
        cache_dir: str = "data",
        max_retries: int = 4,
        freshness_days: int = 7
    ) -> None:
        """
        Initialize DataManager with configuration.

        Args:
            cache_dir: Directory path for cached data storage
            max_retries: Maximum retry attempts for failed downloads
            freshness_days: Days threshold for data freshness check
        """
        self.cache_dir = cache_dir
        self.max_retries = max_retries
        self.freshness_days = freshness_days

        # Initialize components
        self.downloader = FinlabDownloader(max_retries=max_retries)
        self.cache = DataCache(cache_dir=cache_dir)
        self.freshness_checker = FreshnessChecker(
            cache=self.cache,
            max_age_days=freshness_days
        )

        logger.info(
            f"Initialized DataManager: "
            f"cache_dir={cache_dir}, "
            f"max_retries={max_retries}, "
            f"freshness_days={freshness_days}"
        )

    def download_data(
        self,
        dataset: str,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Download dataset from Finlab API with caching support and graceful degradation.

        Implements cache-first strategy with stale-cache fallback:
        1. Check cache if force_refresh=False
        2. Validate freshness (7-day threshold)
        3. Download from Finlab API if needed or stale
        4. Save to cache after successful download
        5. If download fails and stale cache exists, use stale cache (graceful degradation)

        Args:
            dataset: Dataset identifier (e.g., "etl:broker_transactions:top15_buy")
            force_refresh: If True, bypass cache and force download

        Returns:
            DataFrame containing the requested dataset

        Raises:
            DataError: If download fails and no cached data available
            ValidationError: If dataset identifier is invalid
        """
        logger.info(
            f"Requesting dataset: {dataset} (force_refresh={force_refresh})"
        )

        # Step 1: Check cache if not forcing refresh
        cached_data = None
        if not force_refresh:
            cached_data = self.cache.load_from_cache(dataset)

            if cached_data is not None:
                # Step 2: Validate freshness
                is_fresh, last_updated, message = \
                    self.freshness_checker.check_freshness(dataset)

                if is_fresh:
                    logger.info(
                        f"Using fresh cached data for {dataset}. {message}"
                    )
                    return cached_data
                else:
                    logger.warning(
                        f"Cached data is stale for {dataset}. {message}. "
                        f"Attempting to download fresh data..."
                    )

        # Step 3: Attempt to download from Finlab API
        try:
            logger.info(f"Downloading dataset from Finlab API: {dataset}")
            data = self.downloader.download_with_retry(dataset)

            # Step 4: Save to cache
            logger.info(f"Saving downloaded data to cache: {dataset}")
            self.cache.save_to_cache(dataset, data)

            return data

        except Exception as e:
            from src.utils.exceptions import DataError

            # Step 5: Graceful degradation - use stale cache if available
            if cached_data is not None:
                logger.warning(
                    f"Download failed for {dataset}: {e}. "
                    f"Using stale cached data as fallback. "
                    f"Data may be outdated."
                )
                return cached_data
            else:
                # No cache available, re-raise error
                logger.error(
                    f"Download failed for {dataset} and no cached data available: {e}"
                )
                raise DataError(
                    f"Failed to download {dataset} and no cached data available"
                ) from e

    def get_cached_data(self, dataset: str) -> Optional[pd.DataFrame]:
        """
        Retrieve dataset from local cache if available.

        Args:
            dataset: Dataset identifier to retrieve from cache

        Returns:
            DataFrame if cached data exists and is valid, None otherwise

        Raises:
            DataError: If cache file is corrupted or unreadable
        """
        return self.cache.load_from_cache(dataset)

    def check_data_freshness(
        self,
        dataset: str
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Check if cached data meets freshness threshold.

        Args:
            dataset: Dataset identifier to check

        Returns:
            Tuple of (is_fresh, last_updated):
                - is_fresh: True if data age <= freshness_days
                - last_updated: Timestamp of cache file, None if not cached

        Raises:
            DataError: If cache metadata is corrupted
        """
        is_fresh, last_updated, message = \
            self.freshness_checker.check_freshness(dataset)
        return is_fresh, last_updated

    def list_available_datasets(self) -> List[str]:
        """
        List all datasets currently available in cache.

        Returns:
            List of dataset identifiers found in cache directory

        Raises:
            DataError: If cache directory is inaccessible
        """
        try:
            cache_path = Path(self.cache_dir)

            if not cache_path.exists():
                logger.warning(f"Cache directory does not exist: {cache_path}")
                return []

            # Find all .parquet files
            parquet_files = list(cache_path.glob("*.parquet"))

            # Extract unique dataset identifiers from filenames
            datasets = set()
            for file_path in parquet_files:
                # Filename format: dataset_slug_timestamp.parquet
                filename = file_path.stem  # Remove .parquet extension
                parts = filename.rsplit("_", 1)  # Split from right, max 1 split

                if len(parts) == 2:
                    dataset_slug = parts[0]
                    datasets.add(dataset_slug)

            dataset_list = sorted(list(datasets))

            logger.debug(
                f"Found {len(dataset_list)} unique datasets in cache"
            )
            return dataset_list

        except Exception as e:
            from src.utils.exceptions import DataError
            error_msg = f"Failed to list cached datasets: {e}"
            logger.error(error_msg)
            raise DataError(error_msg) from e

    def cleanup_old_cache(self, days_threshold: int = 30) -> int:
        """
        Remove cached data files older than specified threshold.

        Args:
            days_threshold: Age in days for cache cleanup (default: 30)

        Returns:
            Number of cache files removed

        Raises:
            DataError: If cleanup operation fails
        """
        try:
            cache_path = Path(self.cache_dir)

            if not cache_path.exists():
                logger.info("Cache directory does not exist, nothing to clean")
                return 0

            parquet_files = list(cache_path.glob("*.parquet"))
            removed_count = 0

            for file_path in parquet_files:
                # Extract timestamp from filename
                filename = file_path.stem
                parts = filename.rsplit("_", 1)

                if len(parts) == 2:
                    timestamp_str = parts[1]

                    try:
                        # Parse ISO 8601 timestamp
                        file_time = datetime.strptime(
                            timestamp_str,
                            "%Y%m%dT%H%M%SZ"
                        )

                        # Calculate age
                        age = datetime.utcnow() - file_time
                        age_days = age.days

                        if age_days > days_threshold:
                            logger.debug(
                                f"Removing old cache file: {file_path.name} "
                                f"({age_days} days old)"
                            )
                            file_path.unlink()
                            removed_count += 1

                    except ValueError as e:
                        logger.warning(
                            f"Skipping file with invalid timestamp: "
                            f"{file_path.name} ({e})"
                        )
                        continue

            if removed_count > 0:
                logger.info(
                    f"Cleaned up {removed_count} cache file(s) "
                    f"older than {days_threshold} days"
                )
            else:
                logger.debug(
                    f"No cache files older than {days_threshold} days found"
                )

            return removed_count

        except Exception as e:
            from src.utils.exceptions import DataError
            error_msg = f"Failed to cleanup old cache: {e}"
            logger.error(error_msg)
            raise DataError(error_msg) from e


__all__ = ["DataManager"]
