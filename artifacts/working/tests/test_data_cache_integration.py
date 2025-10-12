"""
Integration Test for DataCache with BaseTemplate
=================================================

Tests:
1. BaseTemplate._get_cached_data() uses shared DataCache
2. Multiple template instances share the same cache
3. Cache statistics are properly tracked across templates
4. Preloading works correctly
"""

from src.templates import BaseTemplate, DataCache
from typing import Dict, List, Tuple, Any


class MockTemplate(BaseTemplate):
    """Mock template for testing DataCache integration."""

    @property
    def name(self) -> str:
        return "Mock Template"

    @property
    def pattern_type(self) -> str:
        return "test"

    @property
    def PARAM_GRID(self) -> Dict[str, List]:
        return {'test_param': [1, 2, 3]}

    @property
    def expected_performance(self) -> Dict[str, float]:
        return {
            'sharpe_ratio': 1.5,
            'annual_return': 0.20,
            'max_drawdown': -0.25
        }

    def generate_strategy(self, params: Dict) -> Tuple[object, Dict]:
        # Not used in this test
        pass


def test_shared_cache_integration():
    """Test that BaseTemplate uses shared DataCache."""
    print("=" * 80)
    print("INTEGRATION TEST: BaseTemplate + DataCache")
    print("=" * 80)

    # Clear cache and get singleton
    cache = DataCache.get_instance()
    cache.clear()

    print("\n1. Testing BaseTemplate._get_cached_data() uses shared cache:")
    print("-" * 80)

    # Create template instances
    template1 = MockTemplate()
    template2 = MockTemplate()

    # Load data through template1
    print("\nTemplate 1 loading 'price:收盤價':")
    data1 = template1._get_cached_data('price:收盤價')

    # Verify cache was used
    stats_after_first = cache.get_stats()
    print(f"  Cache stats: {stats_after_first['misses']} miss, {stats_after_first['hits']} hits")
    assert stats_after_first['misses'] == 1, "Should have 1 cache miss"
    assert stats_after_first['cache_size'] == 1, "Should have 1 dataset cached"

    # Load same data through template2 - should hit cache
    print("\nTemplate 2 loading 'price:收盤價' (should hit cache):")
    data2 = template2._get_cached_data('price:收盤價')

    # Verify cache hit
    stats_after_second = cache.get_stats()
    print(f"  Cache stats: {stats_after_second['misses']} misses, {stats_after_second['hits']} hit")
    assert stats_after_second['hits'] == 1, "Should have 1 cache hit"
    assert stats_after_second['cache_size'] == 1, "Should still have 1 dataset cached"
    assert data1 is data2, "Should return same cached object"

    print("\n✅ PASS: Templates share the same DataCache instance")
    print()


def test_cache_persistence_across_templates():
    """Test cache persists across multiple template instances."""
    print("=" * 80)
    print("TEST 2: Cache Persistence Across Templates")
    print("=" * 80)

    cache = DataCache.get_instance()
    cache.clear()

    # Reset statistics by creating a new cache instance
    # (since we're testing from scratch)
    initial_stats = cache.get_stats()
    print(f"\nInitial state: {initial_stats['cache_size']} cached, {initial_stats['total_requests']} requests")

    # Load data from different templates
    datasets = [
        'price:收盤價',
        'price:成交股數',
        'monthly_revenue:當月營收'
    ]

    print("\nLoading datasets from different template instances:")
    requests_before = initial_stats['total_requests']

    for i, dataset in enumerate(datasets, 1):
        template = MockTemplate()
        print(f"\nTemplate {i} loading '{dataset}':")
        template._get_cached_data(dataset)

    # Verify all data is in cache
    stats = cache.get_stats()
    new_requests = stats['total_requests'] - requests_before
    new_misses_expected = len([d for d in datasets if d not in initial_stats['cached_keys']])

    print(f"\nFinal cache state:")
    print(f"  Cache size: {stats['cache_size']} datasets")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  New requests: {new_requests}")
    print(f"  Cache misses (total): {stats['misses']}")
    print(f"  Cache hits (total): {stats['hits']}")

    assert stats['cache_size'] >= len(datasets), f"Should have at least {len(datasets)} datasets cached"
    assert new_requests == len(datasets), f"Should have {len(datasets)} new requests"

    print("\n✅ PASS: Cache persists across multiple template instances")
    print()


def test_preload_integration():
    """Test preload_all() works with template usage."""
    print("=" * 80)
    print("TEST 3: Preload Integration")
    print("=" * 80)

    cache = DataCache.get_instance()
    cache.clear()

    # Preload all common datasets
    print("\nPreloading all common datasets:")
    results = cache.preload_all(verbose=True)

    success_count = sum(1 for v in results.values() if v)
    print(f"\nPreloaded {success_count}/{len(results)} datasets")

    # Now access data through template - should all be cache hits
    template = MockTemplate()

    print("\nAccessing preloaded data through template:")
    for dataset in ['price:收盤價', 'price:成交股數']:
        print(f"  Loading '{dataset}' (should hit cache)")
        template._get_cached_data(dataset)

    # Check statistics
    stats = cache.get_stats()
    print(f"\nCache statistics after template access:")
    print(f"  Hit rate: {stats['hit_rate']:.2%}")
    print(f"  Total requests: {stats['total_requests']}")

    # Should have at least 2 hits (from template access)
    assert stats['hits'] >= 2, "Should have at least 2 cache hits from template access"

    print("\n✅ PASS: Preload integration working correctly")
    print()


def test_cache_statistics_tracking():
    """Test cache statistics are properly tracked."""
    print("=" * 80)
    print("TEST 4: Cache Statistics Tracking")
    print("=" * 80)

    cache = DataCache.get_instance()
    cache.clear()

    # Get baseline stats
    baseline_stats = cache.get_stats()
    print(f"\nBaseline: {baseline_stats['total_requests']} requests")

    template = MockTemplate()

    # Perform mixed operations
    print("\nPerforming mixed cache operations:")

    # Miss
    print("  1. First access to 'price:收盤價' (miss)")
    template._get_cached_data('price:收盤價')

    # Hit
    print("  2. Second access to 'price:收盤價' (hit)")
    template._get_cached_data('price:收盤價')

    # Miss
    print("  3. First access to 'price:成交股數' (miss)")
    template._get_cached_data('price:成交股數')

    # Hit
    print("  4. Second access to 'price:成交股數' (hit)")
    template._get_cached_data('price:成交股數')

    # Check statistics
    stats = cache.get_stats()

    # Calculate delta from baseline
    new_requests = stats['total_requests'] - baseline_stats['total_requests']
    new_hits = stats['hits'] - baseline_stats['hits']
    new_misses = stats['misses'] - baseline_stats['misses']

    print(f"\nFinal statistics (delta from baseline):")
    print(f"  New requests: {new_requests}")
    print(f"  New cache hits: {new_hits}")
    print(f"  New cache misses: {new_misses}")
    print(f"  Overall hit rate: {stats['hit_rate']:.2%}")
    print(f"  Cache size: {stats['cache_size']}")

    assert new_requests == 4, f"Should have 4 new requests (got {new_requests})"
    assert new_hits == 2, f"Should have 2 new cache hits (got {new_hits})"
    assert new_misses == 2, f"Should have 2 new cache misses (got {new_misses})"
    assert stats['cache_size'] == 2, "Should have 2 datasets cached"

    print("\n✅ PASS: Cache statistics tracking correctly")
    print()


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DataCache Integration Test Suite")
    print("=" * 80)
    print()

    try:
        test_shared_cache_integration()
        test_cache_persistence_across_templates()
        test_preload_integration()
        test_cache_statistics_tracking()

        print("=" * 80)
        print("ALL INTEGRATION TESTS PASSED")
        print("=" * 80)
        print()
        print("Summary:")
        print("  ✓ BaseTemplate uses shared DataCache")
        print("  ✓ Cache persists across template instances")
        print("  ✓ Preloading integrates correctly")
        print("  ✓ Statistics tracking works properly")
        print()
        print("Task 3 implementation complete and verified!")
        print("=" * 80)

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        raise
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        raise
