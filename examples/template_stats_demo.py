"""
Template Stats Tracker Demo
============================

Demonstrates the usage of TemplateStatsTracker for tracking template performance
and generating LLM recommendations.

Features Demonstrated:
    - Task 36: Base class initialization and storage
    - Task 37: update_template_stats() to track success rates and Sharpe distribution
    - Task 38: get_template_recommendations() for LLM prompt enhancement

Usage:
    python examples/template_stats_demo.py
"""

import tempfile
from pathlib import Path
from src.feedback import TemplateStatsTracker


def demo_basic_usage():
    """Demonstrate basic usage of TemplateStatsTracker."""
    print("=" * 70)
    print("DEMO 1: Basic Usage")
    print("=" * 70)

    # Create temporary storage for demo
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / 'template_stats.json'
        tracker = TemplateStatsTracker(storage_path=storage_path)

        print("\n1. Initialized TemplateStatsTracker")
        print(f"   Storage: {storage_path}")

        # Simulate some template usage
        print("\n2. Simulating template usage...")

        # TurtleTemplate: 8 attempts, 7 successful, avg Sharpe 1.8
        print("   - TurtleTemplate: Adding 8 attempts...")
        for i, sharpe in enumerate([1.5, 1.8, 2.0, 1.9, 1.7, 1.6, 2.1, 0.3], 1):
            is_success = sharpe > 0.5
            tracker.update_template_stats('TurtleTemplate', sharpe, is_success)
            print(f"     Attempt {i}: Sharpe={sharpe:.2f}, Success={is_success}")

        # Get stats
        stats = tracker.get_template_stats('TurtleTemplate')
        print(f"\n   TurtleTemplate Stats:")
        print(f"     - Total Attempts: {stats.total_attempts}")
        print(f"     - Successful: {stats.successful_strategies}")
        print(f"     - Success Rate: {stats.success_rate:.1f}%")
        print(f"     - Avg Sharpe: {stats.avg_sharpe:.2f}")

        print("\n3. ✓ Basic usage complete!")


def demo_multiple_templates():
    """Demonstrate tracking multiple templates."""
    print("\n" + "=" * 70)
    print("DEMO 2: Multiple Templates with Ranking")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / 'template_stats.json'
        tracker = TemplateStatsTracker(storage_path=storage_path)

        print("\n1. Adding performance data for multiple templates...")

        # TurtleTemplate: 80% success, avg Sharpe 1.85
        print("\n   TurtleTemplate (High Performance):")
        for sharpe in [1.5, 1.8, 2.0, 1.9, 2.1, 1.7, 2.0, 0.3, 1.8, 2.2]:
            is_success = sharpe > 0.5
            tracker.update_template_stats('TurtleTemplate', sharpe, is_success)

        stats = tracker.get_template_stats('TurtleTemplate')
        print(f"     Success Rate: {stats.success_rate:.1f}%")
        print(f"     Avg Sharpe: {stats.avg_sharpe:.2f}")

        # MastiffTemplate: 100% success, avg Sharpe 1.3
        print("\n   MastiffTemplate (Consistent):")
        for sharpe in [1.2, 1.3, 1.4, 1.3, 1.2]:
            tracker.update_template_stats('MastiffTemplate', sharpe, is_successful=True)

        stats = tracker.get_template_stats('MastiffTemplate')
        print(f"     Success Rate: {stats.success_rate:.1f}%")
        print(f"     Avg Sharpe: {stats.avg_sharpe:.2f}")

        # FactorTemplate: 60% success, avg Sharpe 0.9
        print("\n   FactorTemplate (Lower Performance):")
        for sharpe in [0.8, 0.9, 1.0, 0.3, 0.2]:
            is_success = sharpe > 0.5
            tracker.update_template_stats('FactorTemplate', sharpe, is_success)

        stats = tracker.get_template_stats('FactorTemplate')
        print(f"     Success Rate: {stats.success_rate:.1f}%")
        print(f"     Avg Sharpe: {stats.avg_sharpe:.2f}")

        # MomentumTemplate: Insufficient data (only 2 attempts)
        print("\n   MomentumTemplate (Insufficient Data):")
        tracker.update_template_stats('MomentumTemplate', 1.0, is_successful=True)
        tracker.update_template_stats('MomentumTemplate', 1.1, is_successful=True)
        print(f"     Only 2 attempts (below threshold of 3)")

        print("\n2. ✓ Multiple templates tracked!")


def demo_llm_recommendations():
    """Demonstrate LLM recommendation generation."""
    print("\n" + "=" * 70)
    print("DEMO 3: LLM Recommendations (Task 38)")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / 'template_stats.json'
        tracker = TemplateStatsTracker(storage_path=storage_path)

        # Add template data
        print("\n1. Building template performance history...")

        # TurtleTemplate: Excellent performer
        for sharpe in [1.8, 2.0, 1.9, 2.1, 1.7]:
            tracker.update_template_stats('TurtleTemplate', sharpe, is_successful=True)

        # MastiffTemplate: Good performer
        for sharpe in [1.3, 1.4, 1.5, 1.2]:
            tracker.update_template_stats('MastiffTemplate', sharpe, is_successful=True)

        # FactorTemplate: Moderate performer
        for sharpe in [0.9, 1.0, 0.8, 0.7]:
            tracker.update_template_stats('FactorTemplate', sharpe, is_successful=True)

        print("   ✓ Performance history built")

        # Get recommendations
        print("\n2. Generating LLM recommendations...")

        print("\n   Top 3 Templates:")
        recommendations = tracker.get_template_recommendations(top_n=3)
        print(f"\n{recommendations}\n")

        print("   Top 2 Templates:")
        recommendations = tracker.get_template_recommendations(top_n=2)
        print(f"\n{recommendations}\n")

        print("   Top 1 Template:")
        recommendations = tracker.get_template_recommendations(top_n=1)
        print(f"\n{recommendations}\n")

        print("3. ✓ LLM recommendations generated!")


def demo_stats_summary():
    """Demonstrate overall statistics summary."""
    print("\n" + "=" * 70)
    print("DEMO 4: Statistics Summary")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / 'template_stats.json'
        tracker = TemplateStatsTracker(storage_path=storage_path)

        # Add diverse template data
        print("\n1. Adding diverse template performance data...")

        # TurtleTemplate: 5 attempts, 4 successful
        for sharpe in [1.5, 1.8, 2.0, 0.3, 1.9]:
            is_success = sharpe > 0.5
            tracker.update_template_stats('TurtleTemplate', sharpe, is_success)

        # MastiffTemplate: 3 attempts, 3 successful
        for sharpe in [1.2, 1.3, 1.1]:
            tracker.update_template_stats('MastiffTemplate', sharpe, is_successful=True)

        # FactorTemplate: 4 attempts, 2 successful
        for sharpe in [0.8, 0.3, 0.9, 0.2]:
            is_success = sharpe > 0.5
            tracker.update_template_stats('FactorTemplate', sharpe, is_success)

        print("   ✓ Data added for 3 templates")

        # Get summary
        print("\n2. Overall Statistics Summary:")
        summary = tracker.get_stats_summary()

        print(f"\n   Total Templates Tracked: {summary['total_templates']}")
        print(f"   Total Attempts: {summary['total_attempts']}")
        print(f"   Total Successful: {summary['total_successful']}")
        print(f"   Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        print(f"   Average Sharpe (All): {summary['avg_sharpe_all']:.2f}")
        print(f"   Best Template: {summary['best_template']}")

        print("\n3. ✓ Summary statistics retrieved!")


def demo_persistence():
    """Demonstrate data persistence across sessions."""
    print("\n" + "=" * 70)
    print("DEMO 5: Data Persistence")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir) / 'template_stats.json'

        print("\n1. Session 1: Adding data...")
        tracker1 = TemplateStatsTracker(storage_path=storage_path)

        tracker1.update_template_stats('TurtleTemplate', 1.5, is_successful=True)
        tracker1.update_template_stats('TurtleTemplate', 1.8, is_successful=True)
        tracker1.update_template_stats('TurtleTemplate', 2.0, is_successful=True)

        stats1 = tracker1.get_template_stats('TurtleTemplate')
        print(f"   Session 1 Stats: {stats1.total_attempts} attempts, avg Sharpe {stats1.avg_sharpe:.2f}")

        print("\n2. Session 2: Loading persisted data...")
        tracker2 = TemplateStatsTracker(storage_path=storage_path)

        stats2 = tracker2.get_template_stats('TurtleTemplate')
        print(f"   Session 2 Stats: {stats2.total_attempts} attempts, avg Sharpe {stats2.avg_sharpe:.2f}")

        print("\n3. Adding more data in Session 2...")
        tracker2.update_template_stats('TurtleTemplate', 1.9, is_successful=True)

        stats2_updated = tracker2.get_template_stats('TurtleTemplate')
        print(f"   Session 2 Updated: {stats2_updated.total_attempts} attempts, avg Sharpe {stats2_updated.avg_sharpe:.2f}")

        print("\n4. ✓ Data persisted successfully across sessions!")

        # Verify file contents
        print(f"\n5. Storage file contents:")
        with open(storage_path, 'r') as f:
            import json
            data = json.load(f)
            print(f"   {json.dumps(data, indent=2)}")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("TEMPLATE STATS TRACKER DEMONSTRATION")
    print("Tasks 36-38: Feedback Integration System")
    print("=" * 70)

    try:
        # Run demos
        demo_basic_usage()
        demo_multiple_templates()
        demo_llm_recommendations()
        demo_stats_summary()
        demo_persistence()

        print("\n" + "=" * 70)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nKey Features Demonstrated:")
        print("  ✓ Task 36: TemplateStatsTracker base class with storage")
        print("  ✓ Task 37: update_template_stats() tracking success rates and Sharpe")
        print("  ✓ Task 38: get_template_recommendations() for LLM prompts")
        print("\nIntegration Points:")
        print("  - Storage: artifacts/data/template_stats.json")
        print("  - Import: from src.feedback import TemplateStatsTracker")
        print("  - Recommendation format: 'Focus on {template} which has {rate}% success'")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
