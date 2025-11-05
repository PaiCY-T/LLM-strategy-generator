"""
Task 45 - Template Analytics Usage Example
==========================================

Demonstrates the TemplateAnalytics class functionality:
- Template usage tracking
- Success rate calculation
- Statistics retrieval
- Temporal trends
- JSON persistence
"""

from src.feedback import TemplateAnalytics
import json


def main():
    print("=" * 70)
    print("Task 45: Template Analytics Usage Example")
    print("=" * 70)

    # Initialize analytics with default storage path
    analytics = TemplateAnalytics()
    print(f"\n1. Initialized TemplateAnalytics")
    print(f"   Storage: {analytics.storage_path}")
    print(f"   Existing records: {len(analytics.usage_records)}")

    # Track template usage for multiple iterations
    print("\n2. Tracking template usage:")
    print("-" * 70)

    test_scenarios = [
        # (iteration, template, sharpe, validation, exploration, champion_based)
        (101, "TurtleTemplate", 1.8, True, False, True),
        (102, "TurtleTemplate", 2.1, True, False, True),
        (103, "MastiffTemplate", 0.9, False, False, False),
        (104, "TurtleTemplate", 1.6, True, False, True),
        (105, "MastiffTemplate", 1.4, True, True, False),  # Exploration
        (106, "BreakoutTemplate", 1.9, True, False, False),
        (107, "TurtleTemplate", 0.8, False, False, True),
        (108, "BreakoutTemplate", 2.2, True, False, False),
    ]

    for iteration, template, sharpe, validation, exploration, champion in test_scenarios:
        analytics.track_template_usage(
            template_name=template,
            iteration_num=iteration,
            sharpe_ratio=sharpe,
            validation_passed=validation,
            exploration_mode=exploration,
            champion_based=champion,
            match_score=0.85
        )
        status = "✓" if validation else "✗"
        mode = " [EXPLORE]" if exploration else " [CHAMPION]" if champion else ""
        print(f"   {status} Iter {iteration}: {template:20s} Sharpe={sharpe:.1f}{mode}")

    # Calculate success rate for each template
    print("\n3. Success Rate Analysis (min_sharpe=1.5):")
    print("-" * 70)

    templates = ["TurtleTemplate", "MastiffTemplate", "BreakoutTemplate"]
    for template in templates:
        result = analytics.calculate_template_success_rate(template, min_sharpe=1.5)
        print(f"\n   {template}:")
        print(f"   - Total usage: {result['total_usage']}")
        print(f"   - Successful: {result['successful_strategies']}")
        print(f"   - Success rate: {result['success_rate']:.1%}")
        print(f"   - Avg Sharpe (all): {result['avg_sharpe']:.2f}")
        print(f"   - Avg Sharpe (successful): {result['avg_sharpe_successful']:.2f}")

    # Get detailed statistics for best performing template
    print("\n4. Detailed Statistics:")
    print("-" * 70)

    for template in templates:
        stats = analytics.get_template_statistics(template)
        if stats['has_data']:
            print(f"\n   {template}:")
            print(f"   - Total usage: {stats['total_usage']}")
            print(f"   - Success rate: {stats['success_rate']:.1%}")
            print(f"   - Avg Sharpe: {stats['avg_sharpe']:.2f}")
            print(f"   - Best Sharpe: {stats['best_sharpe']:.2f}")
            print(f"   - Worst Sharpe: {stats['worst_sharpe']:.2f}")
            print(f"   - Validation pass: {stats['validation_pass_rate']:.1%}")
            print(f"   - Exploration usage: {stats['exploration_usage']}")
            print(f"   - Champion-based: {stats['champion_usage']}")

    # Get usage trends
    print("\n5. Recent Usage Trend (Last 5 iterations):")
    print("-" * 70)

    recent = analytics.get_usage_trend(last_n_iterations=5)
    for record in recent:
        validation = "✓" if record['validation_passed'] else "✗"
        print(f"   {validation} Iter {record['iteration']}: {record['template_name']:20s} "
              f"Sharpe={record['sharpe_ratio']:.2f}")

    # Get best performing template
    print("\n6. Best Performing Template:")
    print("-" * 70)

    best_template = analytics.get_best_performing_template()
    if best_template:
        print(f"   Winner: {best_template}")
        best_stats = analytics.get_template_statistics(best_template)
        print(f"   Success rate: {best_stats['success_rate']:.1%}")
        print(f"   Average Sharpe: {best_stats['avg_sharpe']:.2f}")

    # Export comprehensive report
    report_path = "artifacts/data/template_analytics_report.json"
    analytics.export_report(report_path)
    print(f"\n7. Report exported to: {report_path}")

    # Display summary
    print("\n8. All Templates Summary:")
    print("-" * 70)

    summary = analytics.get_all_templates_summary()
    print(f"\n   {'Template':<25} {'Usage':>8} {'Success':>10} {'Avg Sharpe':>12}")
    print(f"   {'-'*25} {'-'*8} {'-'*10} {'-'*12}")
    for template_name, stats in sorted(summary.items()):
        print(f"   {template_name:<25} {stats['total_usage']:>8} "
              f"{stats['success_rate']:>9.1%} {stats['avg_sharpe']:>12.2f}")

    # Show JSON storage structure
    print("\n9. Storage File Structure:")
    print("-" * 70)

    with open(analytics.storage_path, 'r') as f:
        stored_data = json.load(f)

    print(f"   Total records: {len(stored_data)}")
    if stored_data:
        print(f"\n   Example record:")
        example = stored_data[0]
        for key, value in example.items():
            print(f"   - {key}: {value}")

    print("\n" + "=" * 70)
    print("✓ Template Analytics demonstration complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
