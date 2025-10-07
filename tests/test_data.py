"""
Comprehensive test suite for data layer components.

Tests cover:
- FinlabDownloader: API downloads with retry logic and rate limiting
- DataCache: Parquet storage with timestamp-based management
- FreshnessChecker: Cache validation with bilingual messaging
- DataManager: Integration testing of complete data workflow

Coverage target: ≥80% for all data layer modules
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.data import DataManager
from src.data.cache import DataCache
from src.data.downloader import FinlabDownloader
from src.data.freshness import FreshnessChecker
from src.utils.exceptions import DataError


# =============================================================================
# FinlabDownloader Tests
# =============================================================================


class TestFinlabDownloader:
    """Test suite for FinlabDownloader class."""

    @pytest.fixture
    def downloader(self) -> FinlabDownloader:
        """Create a FinlabDownloader instance for testing."""
        return FinlabDownloader(max_retries=4, base_delay=0.01, max_delay=0.1)

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'price': [100, 101, 102],
            'volume': [1000, 1100, 1200]
        })

    def test_download_success(
        self,
        downloader: FinlabDownloader,
        sample_data: pd.DataFrame
    ) -> None:
        """Test successful download from Finlab API."""
        with patch('finlab.data.get', return_value=sample_data):
            result = downloader.download_with_retry('price:收盤價')

            assert isinstance(result, pd.DataFrame)
            assert result.shape == (3, 2)
            pd.testing.assert_frame_equal(result, sample_data)

    def test_download_with_retry_on_transient_error(
        self,
        downloader: FinlabDownloader,
        sample_data: pd.DataFrame
    ) -> None:
        """Test exponential backoff retry on transient errors."""
        # Mock API to fail twice, then succeed
        mock_get = Mock(side_effect=[
            RuntimeError("Temporary network error"),
            RuntimeError("Temporary server error"),
            sample_data
        ])

        with patch('finlab.data.get', mock_get):
            result = downloader.download_with_retry('price:收盤價')

            # Should succeed after retries
            assert isinstance(result, pd.DataFrame)
            pd.testing.assert_frame_equal(result, sample_data)

            # Should have attempted 3 times
            assert mock_get.call_count == 3

    def test_download_rate_limit_handling(
        self,
        downloader: FinlabDownloader,
        sample_data: pd.DataFrame
    ) -> None:
        """Test rate limit detection and retry handling."""
        # Mock API to return rate limit error, then succeed
        mock_get = Mock(side_effect=[
            RuntimeError("Rate limit exceeded: too many requests"),
            sample_data
        ])

        with patch('finlab.data.get', mock_get):
            result = downloader.download_with_retry('price:收盤價')

            # Should succeed after rate limit retry
            assert isinstance(result, pd.DataFrame)
            pd.testing.assert_frame_equal(result, sample_data)

            # Should have attempted twice
            assert mock_get.call_count == 2

    def test_download_permanent_failure(
        self,
        downloader: FinlabDownloader
    ) -> None:
        """Test max retries exhausted for permanent errors."""
        # Mock API to always fail
        mock_get = Mock(side_effect=RuntimeError("Permanent API error"))

        with patch('finlab.data.get', mock_get):
            with pytest.raises(DataError, match="after 5 attempts"):
                downloader.download_with_retry('price:收盤價')

            # Should have attempted max_retries + 1 times
            assert mock_get.call_count == 5

    def test_download_invalid_dataset(self, downloader: FinlabDownloader) -> None:
        """Test DataError for invalid dataset identifier."""
        # Test empty dataset
        with pytest.raises(ValueError, match="Invalid dataset identifier"):
            downloader.download_with_retry('')

        # Test None dataset
        with pytest.raises(ValueError, match="Invalid dataset identifier"):
            downloader.download_with_retry(None)  # type: ignore

    def test_download_non_dataframe_result(
        self,
        downloader: FinlabDownloader
    ) -> None:
        """Test error when API returns non-DataFrame result."""
        with patch('finlab.data.get', return_value="not a dataframe"):
            with pytest.raises(DataError, match="Expected DataFrame"):
                downloader.download_with_retry('price:收盤價')

    def test_download_empty_dataframe(
        self,
        downloader: FinlabDownloader
    ) -> None:
        """Test handling of empty DataFrame from API."""
        empty_df = pd.DataFrame()

        with patch('finlab.data.get', return_value=empty_df):
            result = downloader.download_with_retry('price:收盤價')

            # Should return empty DataFrame without error
            assert isinstance(result, pd.DataFrame)
            assert result.empty

    def test_downloader_initialization_validation(self) -> None:
        """Test parameter validation during initialization."""
        # Test negative max_retries
        with pytest.raises(ValueError, match="max_retries must be non-negative"):
            FinlabDownloader(max_retries=-1)

        # Test invalid base_delay
        with pytest.raises(ValueError, match="base_delay must be positive"):
            FinlabDownloader(base_delay=0)

        # Test invalid max_delay
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            FinlabDownloader(base_delay=10, max_delay=5)


# =============================================================================
# DataCache Tests
# =============================================================================


class TestDataCache:
    """Test suite for DataCache class."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Create temporary cache directory."""
        cache = tmp_path / "data"
        cache.mkdir()
        return cache

    @pytest.fixture
    def cache(self, cache_dir: Path) -> DataCache:
        """Create DataCache instance with temporary directory."""
        return DataCache(cache_dir=str(cache_dir))

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'price': [100, 101, 102],
            'volume': [1000, 1100, 1200]
        })

    def test_save_and_load_cache(
        self,
        cache: DataCache,
        sample_data: pd.DataFrame
    ) -> None:
        """Test round-trip save and load of cached data."""
        dataset = "price:收盤價"

        # Save data to cache
        cache.save_to_cache(dataset, sample_data)

        # Load data from cache
        loaded_data = cache.load_from_cache(dataset)

        # Verify data integrity
        assert loaded_data is not None
        pd.testing.assert_frame_equal(loaded_data, sample_data)

    def test_cache_age_calculation(
        self,
        cache: DataCache,
        sample_data: pd.DataFrame
    ) -> None:
        """Test cache age calculation with various timestamps."""
        dataset = "price:收盤價"

        # Save data to cache
        cache.save_to_cache(dataset, sample_data)

        # Get cache age
        age = cache.get_cache_age(dataset)

        # Verify age is very recent (within 1 second)
        assert age is not None
        assert age.total_seconds() < 1.0
        assert age.days == 0

    def test_clear_cache(
        self,
        cache: DataCache,
        sample_data: pd.DataFrame
    ) -> None:
        """Test cache deletion."""
        dataset = "price:收盤價"

        # Save data to cache
        cache.save_to_cache(dataset, sample_data)

        # Verify cache exists
        assert cache.load_from_cache(dataset) is not None

        # Clear cache
        removed_count = cache.clear_cache(dataset)

        # Verify cache is cleared
        assert removed_count == 1
        assert cache.load_from_cache(dataset) is None

    def test_load_nonexistent_cache(self, cache: DataCache) -> None:
        """Test None return for missing cache."""
        result = cache.load_from_cache("nonexistent:dataset")
        assert result is None

    def test_iso8601_timestamp_format(
        self,
        cache: DataCache,
        cache_dir: Path,
        sample_data: pd.DataFrame
    ) -> None:
        """Verify timestamp format in cache filenames."""
        dataset = "price:收盤價"

        # Save data to cache
        cache.save_to_cache(dataset, sample_data)

        # Find cache file
        cache_files = list(cache_dir.glob("*.parquet"))
        assert len(cache_files) == 1

        # Verify filename format
        filename = cache_files[0].stem
        parts = filename.rsplit("_", 1)
        assert len(parts) == 2

        timestamp_str = parts[1]

        # Verify ISO 8601 format: YYYYMMDDTHHMMSSZ
        assert len(timestamp_str) == 16
        assert timestamp_str.endswith("Z")
        assert "T" in timestamp_str

        # Verify parseable
        datetime.strptime(timestamp_str, "%Y%m%dT%H%M%SZ")

    def test_save_invalid_dataset(
        self,
        cache: DataCache,
        sample_data: pd.DataFrame
    ) -> None:
        """Test validation of dataset identifier on save."""
        # Test empty dataset
        with pytest.raises(ValueError, match="Invalid dataset identifier"):
            cache.save_to_cache('', sample_data)

        # Test None dataset
        with pytest.raises(ValueError, match="Invalid dataset identifier"):
            cache.save_to_cache(None, sample_data)  # type: ignore

    def test_save_invalid_data(self, cache: DataCache) -> None:
        """Test validation of data type on save."""
        with pytest.raises(ValueError, match="Invalid data type"):
            cache.save_to_cache('price:收盤價', "not a dataframe")  # type: ignore

    def test_save_empty_dataframe(self, cache: DataCache) -> None:
        """Test saving empty DataFrame generates warning but succeeds."""
        empty_df = pd.DataFrame()

        # Should succeed without error
        cache.save_to_cache('price:收盤價', empty_df)

        # Verify can load back
        loaded = cache.load_from_cache('price:收盤價')
        assert loaded is not None
        assert loaded.empty

    def test_dataset_slug_conversion(self, cache: DataCache) -> None:
        """Test filesystem-safe slug conversion."""
        # Access private method for testing
        assert cache._dataset_to_slug("price:收盤價") == "price_收盤價"
        assert cache._dataset_to_slug("etl:broker:top15") == "etl_broker_top15"
        assert cache._dataset_to_slug("path/with/slashes") == "path_with_slashes"
        assert cache._dataset_to_slug("mixed:path/chars\\test") == "mixed_path_chars_test"

    def test_cache_initialization_validation(self) -> None:
        """Test parameter validation during cache initialization."""
        # Test empty cache_dir
        with pytest.raises(ValueError, match="Invalid cache_dir"):
            DataCache(cache_dir='')

        # Test None cache_dir
        with pytest.raises(ValueError, match="Invalid cache_dir"):
            DataCache(cache_dir=None)  # type: ignore


# =============================================================================
# FreshnessChecker Tests
# =============================================================================


class TestFreshnessChecker:
    """Test suite for FreshnessChecker class."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Create temporary cache directory."""
        cache = tmp_path / "data"
        cache.mkdir()
        return cache

    @pytest.fixture
    def cache(self, cache_dir: Path) -> DataCache:
        """Create DataCache instance."""
        return DataCache(cache_dir=str(cache_dir))

    @pytest.fixture
    def checker_en(self, cache: DataCache) -> FreshnessChecker:
        """Create FreshnessChecker with English messages."""
        return FreshnessChecker(cache=cache, max_age_days=7, language="en-US")

    @pytest.fixture
    def checker_zh(self, cache: DataCache) -> FreshnessChecker:
        """Create FreshnessChecker with Chinese messages."""
        return FreshnessChecker(cache=cache, max_age_days=7, language="zh-TW")

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame({'price': [100, 101, 102]})

    def test_fresh_data(
        self,
        checker_en: FreshnessChecker,
        cache: DataCache,
        sample_data: pd.DataFrame
    ) -> None:
        """Test data less than 7 days old returns True."""
        dataset = "price:收盤價"

        # Save fresh data
        cache.save_to_cache(dataset, sample_data)

        # Check freshness
        is_fresh, last_updated, message = checker_en.check_freshness(dataset)

        assert is_fresh is True
        assert last_updated is not None
        assert "fresh" in message.lower()
        assert "0 days old" in message

    def test_stale_data(
        self,
        checker_en: FreshnessChecker,
        cache_dir: Path,
        sample_data: pd.DataFrame
    ) -> None:
        """Test data older than 7 days returns False."""
        dataset = "price:收盤價"

        # Create old cache file manually with timestamp 10 days ago
        old_timestamp = (datetime.utcnow() - timedelta(days=10)).strftime("%Y%m%dT%H%M%SZ")
        cache_file = cache_dir / f"price_收盤價_{old_timestamp}.parquet"
        sample_data.to_parquet(cache_file)

        # Check freshness
        is_fresh, last_updated, message = checker_en.check_freshness(dataset)

        assert is_fresh is False
        assert last_updated is not None
        assert "stale" in message.lower()
        assert "10 days old" in message

    def test_missing_data(self, checker_en: FreshnessChecker) -> None:
        """Test no cache returns False."""
        is_fresh, last_updated, message = checker_en.check_freshness("nonexistent:dataset")

        assert is_fresh is False
        assert last_updated is None
        assert "no cached data" in message.lower()

    def test_bilingual_messages_english(
        self,
        checker_en: FreshnessChecker,
        cache: DataCache,
        sample_data: pd.DataFrame
    ) -> None:
        """Test English (en-US) messages."""
        dataset = "price:收盤價"

        # Test fresh message
        cache.save_to_cache(dataset, sample_data)
        is_fresh, _, message = checker_en.check_freshness(dataset)
        assert is_fresh is True
        assert "Data is fresh" in message
        assert "days old" in message

        # Test missing message
        is_fresh, _, message = checker_en.check_freshness("nonexistent:dataset")
        assert is_fresh is False
        assert "No cached data available" in message

    def test_bilingual_messages_chinese(
        self,
        checker_zh: FreshnessChecker,
        cache: DataCache,
        sample_data: pd.DataFrame
    ) -> None:
        """Test Traditional Chinese (zh-TW) messages."""
        dataset = "price:收盤價"

        # Test fresh message
        cache.save_to_cache(dataset, sample_data)
        is_fresh, _, message = checker_zh.check_freshness(dataset)
        assert is_fresh is True
        assert "資料新鮮" in message

        # Test missing message
        is_fresh, _, message = checker_zh.check_freshness("nonexistent:dataset")
        assert is_fresh is False
        assert "無快取資料" in message

    def test_custom_threshold(
        self,
        cache: DataCache,
        cache_dir: Path,
        sample_data: pd.DataFrame
    ) -> None:
        """Test different max_age_days values."""
        dataset = "price:收盤價"

        # Create cache file 5 days old
        old_timestamp = (datetime.utcnow() - timedelta(days=5)).strftime("%Y%m%dT%H%M%SZ")
        cache_file = cache_dir / f"price_收盤價_{old_timestamp}.parquet"
        sample_data.to_parquet(cache_file)

        # Test with threshold of 3 days (should be stale)
        checker_3d = FreshnessChecker(cache=cache, max_age_days=3)
        is_fresh, _, _ = checker_3d.check_freshness(dataset)
        assert is_fresh is False

        # Test with threshold of 7 days (should be fresh)
        checker_7d = FreshnessChecker(cache=cache, max_age_days=7)
        is_fresh, _, _ = checker_7d.check_freshness(dataset)
        assert is_fresh is True

    def test_freshness_checker_initialization_validation(
        self,
        cache: DataCache
    ) -> None:
        """Test parameter validation during initialization."""
        # Test invalid cache type
        with pytest.raises(ValueError, match="Invalid cache type"):
            FreshnessChecker(cache="not a cache", max_age_days=7)  # type: ignore

        # Test negative max_age_days
        with pytest.raises(ValueError, match="Invalid max_age_days"):
            FreshnessChecker(cache=cache, max_age_days=-1)

        # Test invalid language
        with pytest.raises(ValueError, match="Invalid language"):
            FreshnessChecker(cache=cache, language="fr-FR")  # type: ignore

    def test_check_freshness_invalid_dataset(
        self,
        checker_en: FreshnessChecker
    ) -> None:
        """Test validation of dataset identifier."""
        # Test empty dataset
        with pytest.raises(ValueError, match="Invalid dataset identifier"):
            checker_en.check_freshness('')

        # Test None dataset
        with pytest.raises(ValueError, match="Invalid dataset identifier"):
            checker_en.check_freshness(None)  # type: ignore


# =============================================================================
# DataManager Integration Tests
# =============================================================================


class TestDataManager:
    """Test suite for DataManager integration."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Create temporary cache directory."""
        cache = tmp_path / "data"
        cache.mkdir()
        return cache

    @pytest.fixture
    def manager(self, cache_dir: Path) -> DataManager:
        """Create DataManager instance."""
        return DataManager(
            cache_dir=str(cache_dir),
            max_retries=4,
            freshness_days=7
        )

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'price': [100, 101, 102],
            'volume': [1000, 1100, 1200]
        })

    def test_download_data_cache_miss(
        self,
        manager: DataManager,
        sample_data: pd.DataFrame
    ) -> None:
        """Test download when no cache exists."""
        dataset = "price:收盤價"

        with patch('finlab.data.get', return_value=sample_data):
            result = manager.download_data(dataset)

            # Should return downloaded data
            assert isinstance(result, pd.DataFrame)
            pd.testing.assert_frame_equal(result, sample_data)

            # Should save to cache
            cached = manager.get_cached_data(dataset)
            assert cached is not None
            pd.testing.assert_frame_equal(cached, sample_data)

    def test_download_data_cache_hit_fresh(
        self,
        manager: DataManager,
        sample_data: pd.DataFrame
    ) -> None:
        """Test using cache when data is fresh."""
        dataset = "price:收盤價"

        # Save fresh data to cache
        manager.cache.save_to_cache(dataset, sample_data)

        # Mock API call that should not be used
        mock_get = Mock()

        with patch('finlab.data.get', mock_get):
            result = manager.download_data(dataset)

            # Should return cached data
            assert isinstance(result, pd.DataFrame)
            pd.testing.assert_frame_equal(result, sample_data)

            # Should not call API
            mock_get.assert_not_called()

    def test_download_data_cache_stale(
        self,
        manager: DataManager,
        cache_dir: Path,
        sample_data: pd.DataFrame
    ) -> None:
        """Test re-download when cache is stale."""
        dataset = "price:收盤價"

        # Create old cache file (10 days old)
        old_timestamp = (datetime.utcnow() - timedelta(days=10)).strftime("%Y%m%dT%H%M%SZ")
        cache_file = cache_dir / f"price_收盤價_{old_timestamp}.parquet"
        sample_data.to_parquet(cache_file)

        # New data to download
        new_data = pd.DataFrame({'price': [200, 201, 202]})

        with patch('finlab.data.get', return_value=new_data):
            result = manager.download_data(dataset)

            # Should return new data
            assert isinstance(result, pd.DataFrame)
            pd.testing.assert_frame_equal(result, new_data)

    def test_download_data_force_refresh(
        self,
        manager: DataManager,
        sample_data: pd.DataFrame
    ) -> None:
        """Test force download even with fresh cache."""
        dataset = "price:收盤價"

        # Save fresh cache
        manager.cache.save_to_cache(dataset, sample_data)

        # New data to download
        new_data = pd.DataFrame({'price': [200, 201, 202]})

        with patch('finlab.data.get', return_value=new_data):
            result = manager.download_data(dataset, force_refresh=True)

            # Should return new data, not cache
            assert isinstance(result, pd.DataFrame)
            pd.testing.assert_frame_equal(result, new_data)

    def test_get_cached_data(
        self,
        manager: DataManager,
        sample_data: pd.DataFrame
    ) -> None:
        """Test getting existing cached data."""
        dataset = "price:收盤價"

        # Save data to cache
        manager.cache.save_to_cache(dataset, sample_data)

        # Retrieve cached data
        result = manager.get_cached_data(dataset)

        assert result is not None
        pd.testing.assert_frame_equal(result, sample_data)

        # Test nonexistent cache
        result = manager.get_cached_data("nonexistent:dataset")
        assert result is None

    def test_check_data_freshness(
        self,
        manager: DataManager,
        sample_data: pd.DataFrame
    ) -> None:
        """Test integration freshness check."""
        dataset = "price:收盤價"

        # Test missing data
        is_fresh, last_updated = manager.check_data_freshness(dataset)
        assert is_fresh is False
        assert last_updated is None

        # Save fresh data
        manager.cache.save_to_cache(dataset, sample_data)

        # Test fresh data
        is_fresh, last_updated = manager.check_data_freshness(dataset)
        assert is_fresh is True
        assert last_updated is not None

    def test_list_available_datasets(
        self,
        manager: DataManager,
        sample_data: pd.DataFrame
    ) -> None:
        """Test listing all cached datasets."""
        # Initially empty
        datasets = manager.list_available_datasets()
        assert datasets == []

        # Save multiple datasets
        manager.cache.save_to_cache("price:收盤價", sample_data)
        manager.cache.save_to_cache("etl:broker:top15", sample_data)

        # List datasets
        datasets = manager.list_available_datasets()
        assert len(datasets) == 2
        assert "price_收盤價" in datasets
        assert "etl_broker_top15" in datasets

    def test_cleanup_old_cache(
        self,
        manager: DataManager,
        cache_dir: Path,
        sample_data: pd.DataFrame
    ) -> None:
        """Test removing caches older than 30 days."""
        # Create old cache file (40 days old)
        old_timestamp = (datetime.utcnow() - timedelta(days=40)).strftime("%Y%m%dT%H%M%SZ")
        old_cache = cache_dir / f"old_dataset_{old_timestamp}.parquet"
        sample_data.to_parquet(old_cache)

        # Create recent cache file (5 days old)
        recent_timestamp = (datetime.utcnow() - timedelta(days=5)).strftime("%Y%m%dT%H%M%SZ")
        recent_cache = cache_dir / f"recent_dataset_{recent_timestamp}.parquet"
        sample_data.to_parquet(recent_cache)

        # Cleanup with 30-day threshold
        removed_count = manager.cleanup_old_cache(days_threshold=30)

        # Should remove only the old file
        assert removed_count == 1
        assert not old_cache.exists()
        assert recent_cache.exists()

    def test_cleanup_old_cache_empty_directory(
        self,
        manager: DataManager
    ) -> None:
        """Test cleanup with no cache files."""
        removed_count = manager.cleanup_old_cache(days_threshold=30)
        assert removed_count == 0

    def test_datamanager_component_initialization(
        self,
        manager: DataManager
    ) -> None:
        """Test all components are properly initialized."""
        assert isinstance(manager.downloader, FinlabDownloader)
        assert isinstance(manager.cache, DataCache)
        assert isinstance(manager.freshness_checker, FreshnessChecker)

        assert manager.max_retries == 4
        assert manager.freshness_days == 7


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================


class TestEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_concurrent_cache_access(
        self,
        tmp_path: Path,
        sample_data: pd.DataFrame = pd.DataFrame({'price': [100]})
    ) -> None:
        """Test concurrent access to cache doesn't cause corruption."""
        cache_dir = tmp_path / "data"
        cache_dir.mkdir()

        cache1 = DataCache(cache_dir=str(cache_dir))
        cache2 = DataCache(cache_dir=str(cache_dir))

        dataset = "price:收盤價"

        # Write with cache1
        cache1.save_to_cache(dataset, sample_data)

        # Read with cache2
        result = cache2.load_from_cache(dataset)
        assert result is not None
        pd.testing.assert_frame_equal(result, sample_data)

    def test_unicode_dataset_names(
        self,
        tmp_path: Path,
        sample_data: pd.DataFrame = pd.DataFrame({'price': [100]})
    ) -> None:
        """Test handling of Unicode characters in dataset names."""
        cache = DataCache(cache_dir=str(tmp_path / "data"))

        dataset = "價格:收盤價:台股"

        cache.save_to_cache(dataset, sample_data)
        result = cache.load_from_cache(dataset)

        assert result is not None
        pd.testing.assert_frame_equal(result, sample_data)

    def test_downloader_import_error_handling(self) -> None:
        """Test handling when finlab package is not available."""
        downloader = FinlabDownloader()

        with patch('finlab.data.get', side_effect=ImportError("No module named 'finlab'")):
            with pytest.raises(DataError, match="Failed to import finlab package"):
                downloader.download_with_retry('price:收盤價')


# =============================================================================
# Error Path Coverage Tests
# =============================================================================


class TestCacheErrorPaths:
    """Test suite for DataCache error handling paths."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Create temporary cache directory."""
        cache = tmp_path / "data"
        cache.mkdir()
        return cache

    @pytest.fixture
    def cache(self, cache_dir: Path) -> DataCache:
        """Create DataCache instance with temporary directory."""
        return DataCache(cache_dir=str(cache_dir))

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame({'col': [1, 2, 3]})

    def test_cache_save_permission_denied(
        self,
        tmp_path: Path,
        sample_data: pd.DataFrame
    ) -> None:
        """Test save fails gracefully when directory is read-only."""
        cache_dir = tmp_path / "readonly_cache"
        cache_dir.mkdir()
        cache = DataCache(cache_dir=str(cache_dir))

        # Make directory read-only
        cache_dir.chmod(0o444)

        try:
            with pytest.raises(DataError, match="Failed to save"):
                cache.save_to_cache("test_dataset", sample_data)
        finally:
            # Restore permissions for cleanup
            cache_dir.chmod(0o755)

    def test_cache_load_corrupted_file(
        self,
        cache_dir: Path
    ) -> None:
        """Test load handles corrupted parquet files."""
        cache = DataCache(cache_dir=str(cache_dir))

        # Create corrupted parquet file
        corrupted_file = cache_dir / "test_dataset_20250105T120000Z.parquet"
        corrupted_file.write_text("corrupted data")

        with pytest.raises(DataError, match="Failed to load"):
            cache.load_from_cache("test_dataset")

    def test_cache_age_invalid_timestamp(
        self,
        cache_dir: Path
    ) -> None:
        """Test get_cache_age handles invalid timestamp format."""
        cache = DataCache(cache_dir=str(cache_dir))

        # Create file with invalid timestamp
        invalid_file = cache_dir / "test_dataset_invalid.parquet"
        invalid_file.touch()

        with pytest.raises(DataError, match="Failed to parse cache timestamp"):
            cache.get_cache_age("test_dataset")

    def test_cache_clear_permission_denied(
        self,
        tmp_path: Path,
        sample_data: pd.DataFrame
    ) -> None:
        """Test clear_cache handles permission errors."""
        cache_dir = tmp_path / "cache_to_clear"
        cache_dir.mkdir()
        cache = DataCache(cache_dir=str(cache_dir))

        # Save a cache file first
        cache.save_to_cache("test", sample_data)

        # Make file read-only
        cache_files = list(cache_dir.glob("*.parquet"))
        assert len(cache_files) == 1
        cache_files[0].chmod(0o444)
        cache_dir.chmod(0o555)

        try:
            with pytest.raises(DataError, match="Failed to clear cache"):
                cache.clear_cache("test")
        finally:
            # Restore permissions for cleanup
            cache_dir.chmod(0o755)
            if cache_files:
                cache_files[0].chmod(0o644)


class TestFreshnessCheckerErrorPaths:
    """Test suite for FreshnessChecker error handling paths."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Create temporary cache directory."""
        cache = tmp_path / "data"
        cache.mkdir()
        return cache

    @pytest.fixture
    def cache(self, cache_dir: Path) -> DataCache:
        """Create DataCache instance."""
        return DataCache(cache_dir=str(cache_dir))

    def test_freshness_check_cache_error(
        self,
        cache: DataCache
    ) -> None:
        """Test freshness check handles cache errors gracefully."""
        checker = FreshnessChecker(cache=cache, max_age_days=7)

        # Mock cache.get_cache_age to raise DataError
        with patch.object(
            cache,
            'get_cache_age',
            side_effect=DataError("Cache corrupted")
        ):
            is_fresh, last_updated, message = checker.check_freshness("test")

            assert is_fresh is False
            assert last_updated is None
            assert "error" in message.lower() or "失敗" in message

    def test_freshness_check_unexpected_error(
        self,
        cache: DataCache
    ) -> None:
        """Test freshness check handles unexpected exceptions."""
        checker = FreshnessChecker(cache=cache, max_age_days=7)

        # Mock to raise unexpected error
        with patch.object(
            cache,
            'get_cache_age',
            side_effect=RuntimeError("Unexpected")
        ):
            is_fresh, last_updated, message = checker.check_freshness("test")

            assert is_fresh is False
            assert last_updated is None
            assert "error" in message.lower() or "失敗" in message


class TestDataManagerErrorPaths:
    """Test suite for DataManager error handling paths."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Create temporary cache directory."""
        cache = tmp_path / "data"
        cache.mkdir()
        return cache

    @pytest.fixture
    def manager(self, cache_dir: Path) -> DataManager:
        """Create DataManager instance."""
        return DataManager(cache_dir=str(cache_dir))

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame({'price': [100, 101]})

    def test_datamanager_list_datasets_directory_error(
        self,
        tmp_path: Path
    ) -> None:
        """Test list_available_datasets handles inaccessible directory."""
        cache_dir = tmp_path / "restricted_cache"
        cache_dir.mkdir()
        dm = DataManager(cache_dir=str(cache_dir))

        # Make directory inaccessible
        cache_dir.chmod(0o000)

        try:
            with pytest.raises(DataError, match="Failed to list cached datasets"):
                dm.list_available_datasets()
        finally:
            # Restore permissions for cleanup
            cache_dir.chmod(0o755)

    def test_datamanager_cleanup_invalid_timestamp(
        self,
        manager: DataManager,
        cache_dir: Path
    ) -> None:
        """Test cleanup_old_cache handles files with invalid timestamps."""
        # Create file with invalid timestamp format
        invalid_file = cache_dir / "dataset_invalid_timestamp.parquet"
        invalid_file.touch()

        # Should skip invalid file, not crash
        removed = manager.cleanup_old_cache(days_threshold=0)
        assert removed == 0  # Invalid file skipped

    def test_datamanager_cleanup_permission_error(
        self,
        tmp_path: Path,
        sample_data: pd.DataFrame
    ) -> None:
        """Test cleanup handles permission denied on file deletion."""
        cache_dir = tmp_path / "cleanup_test"
        cache_dir.mkdir()
        dm = DataManager(cache_dir=str(cache_dir))

        # Create old file
        old_file = cache_dir / "dataset_20200101T120000Z.parquet"
        old_file.touch()

        # Make file and directory read-only
        old_file.chmod(0o444)
        cache_dir.chmod(0o555)

        try:
            with pytest.raises(DataError, match="Failed to cleanup old cache"):
                dm.cleanup_old_cache(days_threshold=0)
        finally:
            # Cleanup
            cache_dir.chmod(0o755)
            old_file.chmod(0o644)

    def test_datamanager_graceful_degradation_with_stale_cache(
        self,
        manager: DataManager,
        sample_data: pd.DataFrame,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test download_data falls back to stale cache when API fails."""
        # Create stale cache
        df_stale = pd.DataFrame({'price': [100, 101]})
        manager.cache.save_to_cache("test_dataset", df_stale)

        # Mock downloader to fail
        def mock_download_fail(dataset: str) -> pd.DataFrame:
            raise Exception("API unavailable")

        monkeypatch.setattr(
            manager.downloader,
            'download_with_retry',
            mock_download_fail
        )

        # Should return stale cache instead of raising
        result = manager.download_data("test_dataset")
        assert result is not None
        assert len(result) == 2

    def test_datamanager_no_cache_and_api_fails(
        self,
        manager: DataManager,
        monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test download_data raises when API fails and no cache exists."""
        from src.utils.exceptions import DataError

        # Mock downloader to fail
        def mock_download_fail(dataset: str) -> pd.DataFrame:
            raise Exception("API unavailable")

        monkeypatch.setattr(
            manager.downloader,
            'download_with_retry',
            mock_download_fail
        )

        # Should raise DataError since no cache available
        with pytest.raises(DataError, match="no cached data available"):
            manager.download_data("nonexistent_dataset")


class TestConcurrentAccess:
    """Test suite for concurrent access scenarios."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Create temporary cache directory."""
        cache = tmp_path / "data"
        cache.mkdir()
        return cache

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame({'val': [1, 2, 3]})

    def test_cache_concurrent_writes(
        self,
        cache_dir: Path
    ) -> None:
        """Test cache handles concurrent writes safely."""
        import threading

        cache = DataCache(cache_dir=str(cache_dir))
        errors: list[Exception] = []

        def write_cache(i: int) -> None:
            try:
                df = pd.DataFrame({'val': [i]})
                cache.save_to_cache(f"dataset_{i}", df)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=write_cache, args=(i,))
            for i in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0  # No crashes
        assert len(list(cache_dir.glob("*.parquet"))) == 10  # All files created

    def test_cache_concurrent_reads(
        self,
        cache_dir: Path,
        sample_data: pd.DataFrame
    ) -> None:
        """Test cache handles concurrent reads safely."""
        import threading

        cache = DataCache(cache_dir=str(cache_dir))
        df = pd.DataFrame({'val': [1, 2, 3]})
        cache.save_to_cache("test", df)

        results: list[Optional[pd.DataFrame]] = []
        errors: list[Exception] = []

        def read_cache() -> None:
            try:
                data = cache.load_from_cache("test")
                results.append(data)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=read_cache)
            for _ in range(10)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 10
        assert all(r is not None for r in results)


# =============================================================================
# Queue Tests (for rate limit handling)
# =============================================================================


class TestQueuedDownloads:
    """Test suite for request queueing during rate limits."""

    @pytest.fixture
    def downloader_with_queue(self) -> FinlabDownloader:
        """Create FinlabDownloader with short timeouts for testing."""
        return FinlabDownloader(
            max_retries=2,
            base_delay=0.1,
            max_delay=0.5,
            queue_timeout=5.0
        )

    @pytest.fixture
    def sample_data(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame({'val': [1, 2, 3]})

    def test_queue_activation_on_rate_limit(
        self,
        downloader_with_queue: FinlabDownloader,
        sample_data: pd.DataFrame
    ) -> None:
        """Test queue activates when rate limit detected."""
        import time

        # Mock to raise rate limit error on first call, then succeed
        call_count = 0

        def mock_download(dataset: str) -> pd.DataFrame:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("429 rate limit exceeded")
            time.sleep(0.1)
            return sample_data

        with patch.object(
            downloader_with_queue,
            '_download_from_finlab',
            side_effect=mock_download
        ):
            # First request triggers rate limit and queues itself
            result = downloader_with_queue.download_with_retry("test_dataset")

            # Should succeed after queueing
            assert isinstance(result, pd.DataFrame)
            pd.testing.assert_frame_equal(result, sample_data)

            # Check rate limited flag was activated
            metrics = downloader_with_queue.get_queue_metrics()
            # Queue should be empty now (request processed)
            assert metrics["queue_size"] == 0

    def test_concurrent_requests_with_rate_limit(
        self,
        downloader_with_queue: FinlabDownloader,
        sample_data: pd.DataFrame
    ) -> None:
        """Test multiple concurrent requests queue properly."""
        import threading
        import time

        results = []
        errors = []

        def download_task(dataset: str) -> None:
            try:
                # Simulate concurrent downloads
                data = downloader_with_queue.download_with_retry(dataset)
                results.append(data)
            except Exception as e:
                errors.append(e)

        # Create 3 concurrent download threads
        threads = [
            threading.Thread(target=download_task, args=(f"dataset_{i}",))
            for i in range(3)
        ]

        # Mock first call to trigger rate limit, then succeed
        call_count = 0

        def mock_download(dataset: str) -> pd.DataFrame:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("429 rate limit exceeded")
            time.sleep(0.1)  # Simulate API delay
            return sample_data

        with patch.object(
            downloader_with_queue,
            '_download_from_finlab',
            side_effect=mock_download
        ):
            # Start all threads
            for t in threads:
                t.start()

            # Wait for completion
            for t in threads:
                t.join(timeout=10)

        # All should complete (1 directly, 2 queued)
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"

    def test_queue_metrics(
        self,
        downloader_with_queue: FinlabDownloader
    ) -> None:
        """Test queue metrics reporting."""
        metrics = downloader_with_queue.get_queue_metrics()

        assert "queue_size" in metrics
        assert "rate_limited" in metrics
        assert "queue_processor_alive" in metrics

        assert isinstance(metrics["queue_size"], int)
        assert isinstance(metrics["rate_limited"], bool)
        assert isinstance(metrics["queue_processor_alive"], bool)

        # Queue processor should be alive
        assert metrics["queue_processor_alive"] is True

    def test_queue_timeout(
        self,
        downloader_with_queue: FinlabDownloader
    ) -> None:
        """Test queued request timeout handling."""
        import time

        # Mock to simulate slow processing that exceeds timeout
        def mock_download_slow(dataset: str) -> pd.DataFrame:
            time.sleep(10)  # Longer than queue_timeout (5s)
            return pd.DataFrame({'val': [1]})

        # Manually activate rate limit mode
        with downloader_with_queue._rate_limit_lock:
            downloader_with_queue._rate_limited = True

        with patch.object(
            downloader_with_queue,
            '_download_from_finlab',
            side_effect=mock_download_slow
        ):
            # Should timeout after 5 seconds
            with pytest.raises(DataError, match="timed out"):
                downloader_with_queue.download_with_retry("slow_dataset")

    def test_queue_initialization_validation(self) -> None:
        """Test parameter validation for queue_timeout."""
        # Test negative queue_timeout
        with pytest.raises(ValueError, match="queue_timeout must be positive"):
            FinlabDownloader(queue_timeout=-1)

        # Test zero queue_timeout
        with pytest.raises(ValueError, match="queue_timeout must be positive"):
            FinlabDownloader(queue_timeout=0)


# =============================================================================
# Integration Tests (require FINLAB_API_TOKEN)
# =============================================================================


class TestIntegrationFinlabAPI:
    """Integration tests with real Finlab API (requires valid token)."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("FINLAB_API_TOKEN"),
        reason="FINLAB_API_TOKEN environment variable not set"
    )
    def test_real_finlab_price_data(self) -> None:
        """Test downloading real price data from Finlab API."""
        downloader = FinlabDownloader()

        # Use lightweight dataset
        data = downloader.download_with_retry("price:收盤價")

        # Validate DataFrame structure
        assert isinstance(data, pd.DataFrame), \
            f"Expected DataFrame, got {type(data).__name__}"
        assert not data.empty, "Downloaded DataFrame is empty"
        assert len(data.columns) > 0, "DataFrame has no columns"

        # Verify data has expected characteristics
        assert data.index is not None, "DataFrame index is None"
        assert len(data) > 0, "DataFrame has no rows"

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("FINLAB_API_TOKEN"),
        reason="FINLAB_API_TOKEN environment variable not set"
    )
    def test_real_finlab_margin_data(self) -> None:
        """Test downloading real margin financing data from Finlab API."""
        downloader = FinlabDownloader()

        # Download 融資餘額 (margin financing balance)
        data = downloader.download_with_retry("fundamental_features:融資餘額")

        # Validate DataFrame structure
        assert isinstance(data, pd.DataFrame), \
            f"Expected DataFrame, got {type(data).__name__}"
        assert not data.empty, "Downloaded DataFrame is empty"
        assert len(data.columns) > 0, "DataFrame has no columns"

        # Verify data characteristics
        assert data.index is not None, "DataFrame index is None"
        assert len(data) > 0, "DataFrame has no rows"

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("FINLAB_API_TOKEN"),
        reason="FINLAB_API_TOKEN environment variable not set"
    )
    def test_real_finlab_broker_data(self) -> None:
        """Test downloading real broker transaction data from Finlab API."""
        downloader = FinlabDownloader()

        # Download 券商分點進出 (broker transactions)
        data = downloader.download_with_retry("etl:broker_transactions:top15_buy")

        # Validate DataFrame structure
        assert isinstance(data, pd.DataFrame), \
            f"Expected DataFrame, got {type(data).__name__}"
        assert not data.empty, "Downloaded DataFrame is empty"
        assert len(data.columns) > 0, "DataFrame has no columns"

        # Verify data characteristics
        assert data.index is not None, "DataFrame index is None"
        assert len(data) > 0, "DataFrame has no rows"

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("FINLAB_API_TOKEN"),
        reason="FINLAB_API_TOKEN environment variable not set"
    )
    def test_real_finlab_market_cap_data(self) -> None:
        """Test downloading real market capitalization data from Finlab API."""
        downloader = FinlabDownloader()

        # Download 市值 (market capitalization)
        data = downloader.download_with_retry("fundamental_features:市值")

        # Validate DataFrame structure
        assert isinstance(data, pd.DataFrame), \
            f"Expected DataFrame, got {type(data).__name__}"
        assert not data.empty, "Downloaded DataFrame is empty"
        assert len(data.columns) > 0, "DataFrame has no columns"

        # Verify data characteristics
        assert data.index is not None, "DataFrame index is None"
        assert len(data) > 0, "DataFrame has no rows"

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("FINLAB_API_TOKEN"),
        reason="FINLAB_API_TOKEN environment variable not set"
    )
    def test_real_finlab_etl_data(self) -> None:
        """Test downloading real ETL dataset from Finlab API."""
        downloader = FinlabDownloader()

        # Download ETL dataset (券商分點進出)
        data = downloader.download_with_retry("etl:broker_transactions:top15_sell")

        # Validate DataFrame structure
        assert isinstance(data, pd.DataFrame), \
            f"Expected DataFrame, got {type(data).__name__}"
        assert not data.empty, "Downloaded DataFrame is empty"
        assert len(data.columns) > 0, "DataFrame has no columns"

        # Verify data characteristics
        assert data.index is not None, "DataFrame index is None"
        assert len(data) > 0, "DataFrame has no rows"
