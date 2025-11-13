"""
Test Task 45: Template Analytics Implementation
================================================

Validates the TemplateAnalytics class implementation:
1. track_template_usage() method
2. calculate_template_success_rate() method
3. get_template_statistics() method
4. Atomic file operations
5. JSON persistence
"""

import json
import tempfile
from pathlib import Path
from src.feedback.template_analytics import TemplateAnalytics


def test_template_analytics_basic():
    """Test basic analytics functionality."""
    print("\n=== Test 1: Basic Template Analytics ===")

    # Create temporary storage
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_analytics.json"

        # Initialize analytics
        analytics = TemplateAnalytics(storage_path=str(storage_path))
        print(f"✓ Initialized TemplateAnalytics with storage: {storage_path}")

        # Track multiple template usages
        test_data = [
            ("TurtleTemplate", 1, 1.8, True),
            ("TurtleTemplate", 2, 2.1, True),
            ("TurtleTemplate", 3, 0.9, False),
            ("TurtleTemplate", 4, 1.6, True),
            ("MastiffTemplate", 5, 1.2, True),
            ("MastiffTemplate", 6, 0.8, False),
        ]

        for template_name, iteration, sharpe, validation in test_data:
            analytics.track_template_usage(
                template_name=template_name,
                iteration_num=iteration,
                sharpe_ratio=sharpe,
                validation_passed=validation
            )

        print(f"✓ Tracked {len(test_data)} template usages")

        # Verify storage file exists
        assert storage_path.exists(), "Storage file should exist"
        print(f"✓ Storage file created: {storage_path}")

        # Verify JSON content
        with open(storage_path, 'r') as f:
            stored_data = json.load(f)
        assert len(stored_data) == len(test_data), "All records should be stored"
        print(f"✓ JSON persistence verified: {len(stored_data)} records")


def test_calculate_success_rate():
    """Test calculate_template_success_rate() method."""
    print("\n=== Test 2: Calculate Success Rate ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_analytics.json"
        analytics = TemplateAnalytics(storage_path=str(storage_path))

        # Track TurtleTemplate usages
        # 4 total: 3 successful (Sharpe >= 1.5 AND validation passed), 1 failed
        analytics.track_template_usage("TurtleTemplate", 1, 1.8, True)  # Success
        analytics.track_template_usage("TurtleTemplate", 2, 2.1, True)  # Success
        analytics.track_template_usage("TurtleTemplate", 3, 0.9, False) # Failed
        analytics.track_template_usage("TurtleTemplate", 4, 1.6, True)  # Success

        # Calculate success rate with min_sharpe=1.5
        result = analytics.calculate_template_success_rate("TurtleTemplate", min_sharpe=1.5)

        print(f"Template: {result['template_name']}")
        print(f"Total usage: {result['total_usage']}")
        print(f"Successful strategies: {result['successful_strategies']}")
        print(f"Success rate: {result['success_rate']:.1%}")
        print(f"Average Sharpe (all): {result['avg_sharpe']:.2f}")
        print(f"Average Sharpe (successful): {result['avg_sharpe_successful']:.2f}")

        # Verify results
        assert result['total_usage'] == 4, "Should have 4 total usages"
        assert result['successful_strategies'] == 3, "Should have 3 successful strategies"
        assert result['success_rate'] == 0.75, "Success rate should be 75%"
        print("✓ Success rate calculation verified")


def test_get_template_statistics():
    """Test get_template_statistics() method."""
    print("\n=== Test 3: Get Template Statistics ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_analytics.json"
        analytics = TemplateAnalytics(storage_path=str(storage_path))

        # Track multiple templates
        analytics.track_template_usage("TurtleTemplate", 1, 1.8, True)
        analytics.track_template_usage("TurtleTemplate", 2, 2.1, True)
        analytics.track_template_usage("TurtleTemplate", 3, 1.2, True)
        analytics.track_template_usage("MastiffTemplate", 4, 0.9, False)
        analytics.track_template_usage("MastiffTemplate", 5, 1.5, True)

        # Get statistics for TurtleTemplate
        stats = analytics.get_template_statistics("TurtleTemplate")

        print(f"Template: TurtleTemplate")
        print(f"Total usage: {stats['total_usage']}")
        print(f"Success rate: {stats['success_rate']:.1%}")
        print(f"Average Sharpe: {stats['avg_sharpe']:.2f}")
        print(f"Best Sharpe: {stats['best_sharpe']:.2f}")
        print(f"Worst Sharpe: {stats['worst_sharpe']:.2f}")
        print(f"Validation pass rate: {stats['validation_pass_rate']:.1%}")

        # Verify statistics
        assert stats['total_usage'] == 3, "Should have 3 usages"
        assert stats['has_data'] == True, "Should have data"
        assert stats['best_sharpe'] == 2.1, "Best Sharpe should be 2.1"
        print("✓ Template statistics verified")


def test_atomic_file_operations():
    """Test atomic file operations (temp file + rename)."""
    print("\n=== Test 4: Atomic File Operations ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_analytics.json"
        analytics = TemplateAnalytics(storage_path=str(storage_path))

        # Track usage (triggers save)
        analytics.track_template_usage("TurtleTemplate", 1, 1.5, True)

        # Verify no temp files left behind
        temp_files = list(Path(tmpdir).glob('.tmp_analytics_*'))
        assert len(temp_files) == 0, "No temp files should remain after save"
        print("✓ No temporary files left behind")

        # Verify final file exists
        assert storage_path.exists(), "Final storage file should exist"
        print("✓ Atomic rename completed successfully")

        # Verify file is valid JSON
        with open(storage_path, 'r') as f:
            data = json.load(f)
        assert len(data) == 1, "Should have 1 record"
        print("✓ File content is valid JSON")


def test_persistence_and_reload():
    """Test data persistence across instances."""
    print("\n=== Test 5: Persistence and Reload ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / "test_analytics.json"

        # First instance: track data
        analytics1 = TemplateAnalytics(storage_path=str(storage_path))
        analytics1.track_template_usage("TurtleTemplate", 1, 1.8, True)
        analytics1.track_template_usage("TurtleTemplate", 2, 2.1, True)
        print("✓ First instance: tracked 2 records")

        # Second instance: load from storage
        analytics2 = TemplateAnalytics(storage_path=str(storage_path))
        stats = analytics2.get_template_statistics("TurtleTemplate")

        print(f"Loaded {stats['total_usage']} records from storage")
        assert stats['total_usage'] == 2, "Should reload 2 records"
        assert stats['avg_sharpe'] == 1.95, "Average Sharpe should be 1.95"
        print("✓ Data persisted and reloaded correctly")


def test_default_storage_path():
    """Test default storage path (artifacts/data/template_analytics.json)."""
    print("\n=== Test 6: Default Storage Path ===")

    # Test that default path is set correctly
    analytics = TemplateAnalytics()
    expected_path = Path("artifacts/data/template_analytics.json")

    print(f"Default storage path: {analytics.storage_path}")
    assert analytics.storage_path == expected_path, "Default path should be artifacts/data/template_analytics.json"
    print("✓ Default storage path verified")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Task 45: Template Analytics Tests")
    print("=" * 60)

    try:
        test_template_analytics_basic()
        test_calculate_success_rate()
        test_get_template_statistics()
        test_atomic_file_operations()
        test_persistence_and_reload()
        test_default_storage_path()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nTask 45 Implementation Summary:")
        print("- ✓ track_template_usage() method implemented")
        print("- ✓ calculate_template_success_rate() method implemented")
        print("- ✓ get_template_statistics() method implemented")
        print("- ✓ Atomic file operations (temp + rename) implemented")
        print("- ✓ JSON persistence verified")
        print("- ✓ Default storage path: artifacts/data/template_analytics.json")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
