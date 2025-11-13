"""
Shared Data Caching Module
===========================

Singleton cache for finlab data.get() operations to avoid redundant data loading
across templates and strategy generation.

Features:
- Singleton pattern ensuring single cache instance
- Lazy loading with on-demand data retrieval
- Bulk preloading for common datasets
- Cache statistics tracking (hits, misses, load times)
- Cache invalidation support
- Thread-safe operations (future enhancement)

Performance:
- Pre-loading all common datasets: <10s target (NFR Performance.3)
- Cache hit: O(1) lookup with no data loading overhead
- Cache miss: First load + O(1) cache storage

Usage:
    from src.templates.data_cache import DataCache

    # Get singleton instance
    cache = DataCache.get_instance()

    # Load data with automatic caching
    close = cache.get('price:收盤價')

    # Preload all common datasets
    cache.preload_all()

    # Check cache performance
    stats = cache.get_stats()
    print(f"Hit rate: {stats['hit_rate']:.2%}")

    # Clear cache if needed
    cache.clear()
"""

import time
from typing import Any, Dict, Optional


class DataCache:
    """
    Singleton cache for finlab data.get() operations.

    This class implements a singleton pattern to ensure only one cache instance
    exists throughout the application lifecycle. All data loaded via data.get()
    is cached to avoid redundant loading operations.

    Attributes:
        _instance (Optional[DataCache]): Singleton instance
        _cache (Dict[str, Any]): Internal cache storage
        _stats (Dict[str, int]): Cache statistics (hits, misses, loads)
        _load_times (Dict[str, float]): Data loading time tracking
    """

    _instance: Optional['DataCache'] = None

    # Common datasets that should be preloaded for performance
    COMMON_DATASETS = [
        'etl:adj_close',                             # ✅ Adjusted close price (dividends/splits)
        'etl:adj_high',                              # ✅ Adjusted high price
        'etl:adj_low',                               # ✅ Adjusted low price
        'etl:adj_open',                              # ✅ Adjusted open price
        'price:成交金額',                            # Trading value (OK for liquidity filters)
        'monthly_revenue:當月營收',                  # Monthly revenue
        'fundamental_features:營業利益率',           # Operating margin
        'price_earning_ratio:殖利率(%)',             # Dividend yield
        'monthly_revenue:去年同月增減(%)',           # Revenue YoY growth
    ]

    def __init__(self):
        """
        Private constructor for singleton pattern.

        Do not call directly. Use DataCache.get_instance() instead.
        """
        if DataCache._instance is not None:
            raise RuntimeError(
                "DataCache is a singleton. Use DataCache.get_instance() instead."
            )

        # Initialize cache storage
        self._cache: Dict[str, Any] = {}

        # Initialize statistics tracking
        self._stats = {
            'hits': 0,      # Cache hits (data found in cache)
            'misses': 0,    # Cache misses (data loaded from source)
            'loads': 0      # Total data loading operations
        }

        # Track loading times for performance monitoring
        self._load_times: Dict[str, float] = {}

        DataCache._instance = self

    @classmethod
    def get_instance(cls) -> 'DataCache':
        """
        Get the singleton DataCache instance.

        Creates the instance on first call, returns existing instance on
        subsequent calls.

        Returns:
            DataCache: The singleton DataCache instance

        Example:
            cache = DataCache.get_instance()
            data = cache.get('price:收盤價')
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get(self, key: str, verbose: bool = True) -> Any:
        """
        Get data from cache with lazy loading.

        If data exists in cache, returns immediately (cache hit).
        If data not in cache, loads from finlab.data.get() and caches it (cache miss).

        Args:
            key (str): Data key to retrieve (e.g., 'price:收盤價', 'price:成交股數')
            verbose (bool): If True, prints loading messages. Default: True

        Returns:
            Any: Cached data object (typically DataFrame or Series)

        Raises:
            Exception: If data loading fails (propagated from finlab.data.get())

        Example:
            cache = DataCache.get_instance()
            close = cache.get('price:收盤價')
            volume = cache.get('price:成交股數', verbose=False)
        """
        # Cache hit - return immediately
        if key in self._cache:
            self._stats['hits'] += 1
            return self._cache[key]

        # Cache miss - load and cache data
        self._stats['misses'] += 1

        if verbose:
            print(f"  Loading dataset: {key}...")

        # Import here to avoid circular dependency
        from finlab import data

        # Track loading time
        start_time = time.time()

        try:
            # Load data from source
            data_obj = data.get(key)
            load_time = time.time() - start_time

            # Store in cache
            self._cache[key] = data_obj
            self._stats['loads'] += 1
            self._load_times[key] = load_time

            if verbose:
                print(f"  ✓ Loaded in {load_time:.2f}s")

            return data_obj

        except Exception as e:
            load_time = time.time() - start_time
            if verbose:
                print(f"  ✗ Failed after {load_time:.2f}s: {str(e)}")
            raise

    def preload_all(self, verbose: bool = True) -> Dict[str, bool]:
        """
        Preload all common datasets for optimal performance.

        Loads all datasets defined in COMMON_DATASETS in sequence.
        This is useful for bulk loading at application startup to avoid
        loading delays during strategy execution.

        Target: Complete in <10s (NFR Performance.3)

        Args:
            verbose (bool): If True, prints progress messages. Default: True

        Returns:
            Dict[str, bool]: Dictionary mapping dataset keys to success status
                True if loaded successfully, False if failed

        Example:
            cache = DataCache.get_instance()
            results = cache.preload_all()

            # Check if all datasets loaded successfully
            if all(results.values()):
                print("All datasets preloaded successfully")
        """
        results: Dict[str, bool] = {}
        start_time = time.time()

        if verbose:
            print(f"🔄 Pre-loading {len(self.COMMON_DATASETS)} datasets...")

        for dataset_key in self.COMMON_DATASETS:
            try:
                self.get(dataset_key, verbose=verbose)
                results[dataset_key] = True
            except Exception as e:
                results[dataset_key] = False
                if verbose:
                    print(f"  ⚠️ Failed to load '{dataset_key}': {str(e)}")

        total_time = time.time() - start_time
        success_count = sum(1 for v in results.values() if v)

        if verbose:
            print(f"✅ Pre-loaded {success_count}/{len(self.COMMON_DATASETS)} datasets in {total_time:.2f}s\n")

        return results

    def clear(self, keys: Optional[list] = None) -> None:
        """
        Clear cache entries.

        If keys is None, clears the entire cache. Otherwise, clears only
        the specified keys.

        Args:
            keys (Optional[list]): List of keys to clear. If None, clears all.

        Example:
            cache = DataCache.get_instance()

            # Clear specific datasets
            cache.clear(['price:收盤價', 'price:成交股數'])

            # Clear entire cache
            cache.clear()
        """
        if keys is None:
            # Clear entire cache
            cleared_count = len(self._cache)
            self._cache.clear()
            self._load_times.clear()
            print(f"Cache cleared: {cleared_count} entries removed")
        else:
            # Clear specific keys
            cleared_count = 0
            for key in keys:
                if key in self._cache:
                    del self._cache[key]
                    if key in self._load_times:
                        del self._load_times[key]
                    cleared_count += 1
            print(f"Cache cleared: {cleared_count}/{len(keys)} entries removed")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns detailed statistics about cache usage including hit rate,
        miss rate, cache size, and loading performance.

        Returns:
            Dict[str, Any]: Dictionary containing:
                - hits (int): Number of cache hits
                - misses (int): Number of cache misses
                - loads (int): Number of data loading operations
                - total_requests (int): Total get() calls
                - hit_rate (float): Cache hit rate (0.0-1.0)
                - miss_rate (float): Cache miss rate (0.0-1.0)
                - cache_size (int): Number of cached datasets
                - cached_keys (list): List of cached dataset keys
                - avg_load_time (float): Average data loading time in seconds
                - total_load_time (float): Total data loading time in seconds

        Example:
            cache = DataCache.get_instance()
            stats = cache.get_stats()

            print(f"Hit rate: {stats['hit_rate']:.2%}")
            print(f"Cache size: {stats['cache_size']} datasets")
            print(f"Avg load time: {stats['avg_load_time']:.2f}s")
        """
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0.0
        miss_rate = self._stats['misses'] / total_requests if total_requests > 0 else 0.0

        # Calculate loading time statistics
        load_times = list(self._load_times.values())
        avg_load_time = sum(load_times) / len(load_times) if load_times else 0.0
        total_load_time = sum(load_times)

        return {
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'loads': self._stats['loads'],
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'miss_rate': miss_rate,
            'cache_size': len(self._cache),
            'cached_keys': list(self._cache.keys()),
            'avg_load_time': avg_load_time,
            'total_load_time': total_load_time
        }

    def __repr__(self) -> str:
        """
        Return string representation of DataCache.

        Returns:
            str: String showing cache size and basic statistics
        """
        stats = self.get_stats()
        return (
            f"DataCache(size={stats['cache_size']}, "
            f"hit_rate={stats['hit_rate']:.2%}, "
            f"total_requests={stats['total_requests']})"
        )


def get_cached_data(key: str, verbose: bool = True) -> Any:
    """
    Convenience function for accessing cached data.

    This is a module-level convenience function that wraps DataCache.get_instance().get()
    for easier access. It maintains backward compatibility with existing code patterns.

    Args:
        key (str): Data key to retrieve
        verbose (bool): If True, prints loading messages. Default: True

    Returns:
        Any: Cached data object

    Example:
        from src.templates.data_cache import get_cached_data

        close = get_cached_data('price:收盤價')
        volume = get_cached_data('price:成交股數', verbose=False)
    """
    cache = DataCache.get_instance()
    return cache.get(key, verbose=verbose)
