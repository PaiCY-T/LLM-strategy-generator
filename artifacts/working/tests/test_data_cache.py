"""
Test script for DataCache implementation
=========================================

Tests:
1. Singleton pattern - only one instance exists
2. get() with lazy loading - cache miss then cache hit
3. preload_all() - bulk loading performance
4. get_stats() - cache statistics tracking
5. clear() - cache invalidation
6. Convenience function - get_cached_data()
"""

import time
from src.templates.data_cache import DataCache, get_cached_data


def test_singleton_pattern():
    """Test that only one DataCache instance exists."""
    print("=" * 80)
    print("TEST 1: Singleton Pattern")
    print("=" * 80)

    cache1 = DataCache.get_instance()
    cache2 = DataCache.get_instance()

    assert cache1 is cache2, "Multiple instances created - singleton pattern broken"
    print("✅ PASS: Singleton pattern working - same instance returned")
    print(f"   Instance: {cache1}")
    print()


def test_lazy_loading():
    """Test lazy loading with cache hits and misses."""
    print("=" * 80)
    print("TEST 2: Lazy Loading (Cache Miss → Cache Hit)")
    print("=" * 80)

    cache = DataCache.get_instance()
    cache.clear()  # Start fresh

    # First access - should be cache miss
    print("First access (cache miss expected):")
    start = time.time()
    data1 = cache.get('price:收盤價', verbose=True)
    time1 = time.time() - start

    # Second access - should be cache hit
    print("\nSecond access (cache hit expected):")
    start = time.time()
    data2 = cache.get('price:收盤價', verbose=True)
    time2 = time.time() - start

    assert data1 is data2, "Same data should be returned from cache"
    assert time2 < time1 * 0.1, f"Cache hit should be much faster ({time2:.4f}s vs {time1:.2f}s)"

    stats = cache.get_stats()
    assert stats['hits'] >= 1, "Should have at least 1 cache hit"
    assert stats['misses'] >= 1, "Should have at least 1 cache miss"

    print(f"\n✅ PASS: Lazy loading working")
    print(f"   Cache miss time: {time1:.2f}s")
    print(f"   Cache hit time: {time2:.4f}s (speedup: {time1/time2:.0f}x)")
    print()


def test_preload_all():
    """Test bulk preloading of common datasets."""
    print("=" * 80)
    print("TEST 3: Preload All Common Datasets")
    print("=" * 80)

    cache = DataCache.get_instance()
    cache.clear()  # Start fresh

    # Preload all datasets
    start = time.time()
    results = cache.preload_all(verbose=True)
    total_time = time.time() - start

    # Check results
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    assert success_count > 0, "At least some datasets should load successfully"
    assert total_time < 10.0, f"Preloading took {total_time:.2f}s (target: <10s)"

    print(f"✅ PASS: Preloaded {success_count}/{total_count} datasets in {total_time:.2f}s")
    print(f"   Target: <10s (NFR Performance.3)")
    print()

    return total_time


def test_cache_statistics():
    """Test cache statistics tracking."""
    print("=" * 80)
    print("TEST 4: Cache Statistics")
    print("=" * 80)

    cache = DataCache.get_instance()
    stats = cache.get_stats()

    print(f"Cache Statistics:")
    print(f"  Cache size: {stats['cache_size']} datasets")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Cache hits: {stats['hits']}")
    print(f"  Cache misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.2%}")
    print(f"  Miss rate: {stats['miss_rate']:.2%}")
    print(f"  Total data loads: {stats['loads']}")
    print(f"  Avg load time: {stats['avg_load_time']:.2f}s")
    print(f"  Total load time: {stats['total_load_time']:.2f}s")
    print(f"\nCached datasets:")
    for key in stats['cached_keys']:
        print(f"  - {key}")

    assert stats['cache_size'] > 0, "Cache should contain data"
    assert stats['total_requests'] > 0, "Should have processed requests"
    assert 0.0 <= stats['hit_rate'] <= 1.0, "Hit rate should be between 0 and 1"

    print(f"\n✅ PASS: Statistics tracking working")
    print()


def test_cache_clear():
    """Test cache invalidation."""
    print("=" * 80)
    print("TEST 5: Cache Clear")
    print("=" * 80)

    cache = DataCache.get_instance()
    initial_size = cache.get_stats()['cache_size']

    # Test selective clear
    print("Testing selective clear:")
    cache.clear(['price:收盤價'])

    # Test full clear
    print("\nTesting full clear:")
    cache.clear()

    final_size = cache.get_stats()['cache_size']
    assert final_size == 0, "Cache should be empty after clear()"

    print(f"\n✅ PASS: Cache cleared successfully (was {initial_size}, now {final_size})")
    print()


def test_convenience_function():
    """Test module-level convenience function."""
    print("=" * 80)
    print("TEST 6: Convenience Function")
    print("=" * 80)

    cache = DataCache.get_instance()
    cache.clear()

    # Test convenience function
    print("Testing get_cached_data() convenience function:")
    data1 = get_cached_data('price:收盤價', verbose=True)
    data2 = get_cached_data('price:收盤價', verbose=False)

    assert data1 is data2, "Should return same cached data"

    stats = cache.get_stats()
    print(f"\n✅ PASS: Convenience function working")
    print(f"   Total requests: {stats['total_requests']}")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DataCache Implementation Test Suite")
    print("=" * 80)
    print()

    try:
        # Run all tests
        test_singleton_pattern()
        test_lazy_loading()
        preload_time = test_preload_all()
        test_cache_statistics()
        test_cache_clear()
        test_convenience_function()

        # Final summary
        print("=" * 80)
        print("TEST SUITE SUMMARY")
        print("=" * 80)
        print("✅ All tests passed!")
        print()
        print("Performance:")
        print(f"  - Preload time: {preload_time:.2f}s (target: <10s)")
        print()
        print("Features verified:")
        print("  ✓ Singleton pattern")
        print("  ✓ Lazy loading with cache hits/misses")
        print("  ✓ Bulk preloading")
        print("  ✓ Statistics tracking")
        print("  ✓ Cache invalidation")
        print("  ✓ Convenience function")
        print("=" * 80)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        raise
