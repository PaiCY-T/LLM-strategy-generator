"""
Local data caching with Parquet storage format.

Provides efficient storage and retrieval of financial data using Parquet
format with ISO 8601 timestamps for cache management.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

from src.utils.exceptions import DataError
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataCache:
    """
    Local cache manager for financial data using Parquet format.

    Implements efficient data storage with timestamp-based cache management.
    Organizes cache files by dataset type with ISO 8601 timestamps for
    easy age tracking and cleanup.

    Attributes:
        cache_dir: Base directory for cache storage
    """

    def __init__(self, cache_dir: str = "data") -> None:
        """
        Initialize DataCache with storage directory.

        Args:
            cache_dir: Base directory path for cache storage (default: "data")

        Raises:
            ValueError: If cache_dir is empty or invalid
        """
        if not cache_dir or not isinstance(cache_dir, str):
            raise ValueError(
                f"Invalid cache_dir: {cache_dir!r}. Must be a non-empty string."
            )

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initialized DataCache: cache_dir={self.cache_dir.absolute()}")

    def save_to_cache(self, dataset: str, data: pd.DataFrame) -> None:
        """
        Save DataFrame to cache with ISO 8601 timestamp.

        File naming: {dataset_slug}_{timestamp}.parquet
        Example: broker_transactions_top15_buy_20250105T143022Z.parquet

        Args:
            dataset: Dataset identifier (e.g., "etl:broker_transactions:top15_buy")
            data: DataFrame to cache

        Raises:
            DataError: If save operation fails
            ValueError: If dataset or data is invalid
        """
        if not dataset or not isinstance(dataset, str):
            raise ValueError(
                f"Invalid dataset identifier: {dataset!r}. "
                f"Must be a non-empty string."
            )

        if not isinstance(data, pd.DataFrame):
            raise ValueError(
                f"Invalid data type: {type(data).__name__}. "
                f"Expected pandas DataFrame."
            )

        if data.empty:
            logger.warning(
                f"Saving empty DataFrame to cache for dataset: {dataset}"
            )

        try:
            # Convert dataset identifier to filesystem-safe slug
            dataset_slug = self._dataset_to_slug(dataset)

            # Generate ISO 8601 timestamp (UTC)
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

            # Create cache file path
            cache_file = self.cache_dir / f"{dataset_slug}_{timestamp}.parquet"

            # Save to Parquet format
            logger.debug(f"Saving cache: {cache_file.name} (shape: {data.shape})")
            data.to_parquet(
                cache_file,
                engine="pyarrow",
                compression="snappy",
                index=True
            )

            logger.info(
                f"Successfully cached dataset: {dataset} → {cache_file.name}"
            )

        except Exception as e:
            error_msg = (
                f"Failed to save dataset '{dataset}' to cache: {e}"
            )
            logger.error(error_msg)
            raise DataError(error_msg) from e

    def load_from_cache(self, dataset: str) -> Optional[pd.DataFrame]:
        """
        Load most recent cached DataFrame for dataset.

        Searches for all cache files matching the dataset and returns
        the most recently created one based on timestamp.

        Args:
            dataset: Dataset identifier to load from cache

        Returns:
            DataFrame if cached data exists, None otherwise

        Raises:
            DataError: If cache file exists but is corrupted or unreadable
        """
        if not dataset or not isinstance(dataset, str):
            raise ValueError(
                f"Invalid dataset identifier: {dataset!r}. "
                f"Must be a non-empty string."
            )

        try:
            dataset_slug = self._dataset_to_slug(dataset)

            # Find all cache files for this dataset
            cache_files = list(
                self.cache_dir.glob(f"{dataset_slug}_*.parquet")
            )

            if not cache_files:
                logger.debug(f"No cache found for dataset: {dataset}")
                return None

            # Sort by timestamp (most recent first)
            cache_files.sort(reverse=True)
            latest_cache = cache_files[0]

            logger.debug(f"Loading cache: {latest_cache.name}")
            data = pd.read_parquet(latest_cache, engine="pyarrow")

            logger.info(
                f"Successfully loaded cached dataset: {dataset} "
                f"from {latest_cache.name} (shape: {data.shape})"
            )
            return data

        except Exception as e:
            error_msg = (
                f"Failed to load cached dataset '{dataset}': {e}"
            )
            logger.error(error_msg)
            raise DataError(error_msg) from e

    def get_cache_age(self, dataset: str) -> Optional[timedelta]:
        """
        Calculate age of most recent cache file for dataset.

        Args:
            dataset: Dataset identifier to check

        Returns:
            timedelta representing cache age, or None if no cache exists

        Raises:
            DataError: If cache metadata is corrupted or unreadable
        """
        if not dataset or not isinstance(dataset, str):
            raise ValueError(
                f"Invalid dataset identifier: {dataset!r}. "
                f"Must be a non-empty string."
            )

        try:
            dataset_slug = self._dataset_to_slug(dataset)

            # Find all cache files for this dataset
            cache_files = list(
                self.cache_dir.glob(f"{dataset_slug}_*.parquet")
            )

            if not cache_files:
                logger.debug(f"No cache found for dataset: {dataset}")
                return None

            # Sort by timestamp (most recent first)
            cache_files.sort(reverse=True)
            latest_cache = cache_files[0]

            # Extract timestamp from filename
            timestamp_str = latest_cache.stem.split("_")[-1]

            # Parse ISO 8601 timestamp
            cache_time = datetime.strptime(timestamp_str, "%Y%m%dT%H%M%SZ")

            # Calculate age
            age = datetime.utcnow() - cache_time

            logger.debug(
                f"Cache age for {dataset}: {age.total_seconds():.0f}s "
                f"({age.days} days)"
            )
            return age

        except ValueError as e:
            error_msg = (
                f"Failed to parse cache timestamp for dataset '{dataset}': {e}"
            )
            logger.error(error_msg)
            raise DataError(error_msg) from e
        except Exception as e:
            error_msg = (
                f"Failed to get cache age for dataset '{dataset}': {e}"
            )
            logger.error(error_msg)
            raise DataError(error_msg) from e

    def clear_cache(self, dataset: str) -> int:
        """
        Remove all cached files for specified dataset.

        Args:
            dataset: Dataset identifier to clear from cache

        Returns:
            Number of cache files removed

        Raises:
            DataError: If removal operation fails
        """
        if not dataset or not isinstance(dataset, str):
            raise ValueError(
                f"Invalid dataset identifier: {dataset!r}. "
                f"Must be a non-empty string."
            )

        try:
            dataset_slug = self._dataset_to_slug(dataset)

            # Find all cache files for this dataset
            cache_files = list(
                self.cache_dir.glob(f"{dataset_slug}_*.parquet")
            )

            removed_count = 0
            for cache_file in cache_files:
                logger.debug(f"Removing cache file: {cache_file.name}")
                cache_file.unlink()
                removed_count += 1

            if removed_count > 0:
                logger.info(
                    f"Cleared {removed_count} cache file(s) for dataset: {dataset}"
                )
            else:
                logger.debug(f"No cache files to clear for dataset: {dataset}")

            return removed_count

        except Exception as e:
            error_msg = (
                f"Failed to clear cache for dataset '{dataset}': {e}"
            )
            logger.error(error_msg)
            raise DataError(error_msg) from e

    def _dataset_to_slug(self, dataset: str) -> str:
        """
        Convert dataset identifier to filesystem-safe slug.

        Args:
            dataset: Dataset identifier (e.g., "etl:broker_transactions:top15_buy")

        Returns:
            Filesystem-safe slug (e.g., "etl_broker_transactions_top15_buy")
        """
        # Replace special characters with underscores
        slug = dataset.replace(":", "_").replace("/", "_").replace("\\", "_")

        # Remove any remaining non-alphanumeric characters except underscores
        slug = "".join(c if c.isalnum() or c == "_" else "_" for c in slug)

        # Collapse multiple underscores
        while "__" in slug:
            slug = slug.replace("__", "_")

        # Remove leading/trailing underscores
        slug = slug.strip("_")

        return slug.lower()


__all__ = ["DataCache"]
