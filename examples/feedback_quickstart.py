"""
Template Feedback System - Quick Start Example
==============================================

Complete working example demonstrating the template feedback integration system.

This example shows:
1. Basic template recommendation
2. Champion-based parameter suggestions
3. Exploration mode activation
4. Validation-aware feedback
5. Analytics tracking and reporting

Run this example:
    python examples/feedback_quickstart.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from typing import Dict, Any
from src.feedback import (
    TemplateFeedbackIntegrator,
    FeedbackLoopIntegrator,
    TemplateAnalytics
)
from src.validation import ValidationResult, ValidationError, Severity, Category


def example_1_basic_recommendation():
    """Example 1: Basic template recommendation."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Template Recommendation")
    print("="*70)

    # Initialize integrator
    integrator = TemplateFeedbackIntegrator(repository=None)

    # Get recommendation for low Sharpe
    recommendation = integrator.recommend_template(
        current_metrics={'sharpe_ratio': 0.8},
        iteration=1
    )

    print(f"\nTemplate: {recommendation.template_name}")
    print(f"Match Score: {recommendation.match_score:.2f}")
    print(f"Exploration Mode: {recommendation.exploration_mode}")
    print(f"\nRationale:")
    print(f"  {recommendation.rationale}")
    print(f"\nSuggested Parameters:")
    for param, value in recommendation.suggested_params.items():
        print(f"  {param}: {value}")


def example_2_exploration_mode():
    """Example 2: Exploration mode activation."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Exploration Mode Activation")
    print("="*70)

    integrator = TemplateFeedbackIntegrator(repository=None)

    # Iterations 1-4: Normal recommendations
    for i in range(1, 5):
        rec = integrator.recommend_template(
            current_metrics={'sharpe_ratio': 0.8},
            iteration=i
        )
        print(f"\nIteration {i}: {rec.template_name} (Exploration: {rec.exploration_mode})")

    # Iteration 5: Exploration mode triggers
    rec = integrator.recommend_template(
        current_metrics={'sharpe_ratio': 0.8},
        iteration=5
    )
    print(f"\nIteration 5: {rec.template_name} (Exploration: {rec.exploration_mode})")
    print(f"Rationale: {rec.rationale[:100]}...")


def example_3_validation_feedback():
    """Example 3: Validation-aware parameter adjustment."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Validation-Aware Feedback")
    print("="*70)

    integrator = TemplateFeedbackIntegrator(repository=None)

    # Create validation result with parameter error
    validation_result = ValidationResult(
        status='FAIL',
        errors=[
            ValidationError(
                severity=Severity.CRITICAL,
                category=Category.PARAMETER,
                message='n_stocks out of range: 50 (must be 5-30)',
                context={'parameter': 'n_stocks', 'value': 50}
            )
        ],
        warnings=[],
        suggestions=[],
        metadata={}
    )

    # Get recommendation with validation feedback
    recommendation = integrator.recommend_template(
        current_metrics={'sharpe_ratio': 0.8},
        iteration=2,
        validation_result=validation_result
    )

    print(f"\nTemplate: {recommendation.template_name}")
    print(f"\nRationale with validation feedback:")
    print(f"  {recommendation.rationale}")
    print(f"\nAdjusted Parameters:")
    for param, value in recommendation.suggested_params.items():
        print(f"  {param}: {value}")


def example_4_analytics_tracking():
    """Example 4: Analytics tracking and statistics."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Analytics Tracking and Reporting")
    print("="*70)

    import tempfile
    import json

    # Create analytics with temporary storage
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        analytics_file = f.name

    analytics = TemplateAnalytics(storage_path=analytics_file)

    # Simulate 20 iterations with varying performance
    print("\nSimulating 20 iterations...")
    for i in range(1, 21):
        # Alternate between TurtleTemplate and MastiffTemplate
        template = 'TurtleTemplate' if i % 2 == 0 else 'MastiffTemplate'

        # Increasing Sharpe over time
        sharpe = 0.5 + (i * 0.05)

        # 70% validation pass rate
        validation_passed = (i % 3 != 0)

        analytics.record_template_usage(
            iteration=i,
            template_name=template,
            sharpe_ratio=sharpe,
            validation_passed=validation_passed,
            exploration_mode=(i % 5 == 0),
            match_score=0.75 + (i * 0.01)
        )

    print("Done!")

    # Get statistics
    print("\n" + "-"*70)
    print("TEMPLATE STATISTICS")
    print("-"*70)

    summary = analytics.get_all_templates_summary()
    for template, stats in summary.items():
        print(f"\n{template}:")
        print(f"  Total Usage: {stats['total_usage']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")
        print(f"  Avg Sharpe: {stats['avg_sharpe']:.2f}")
        print(f"  Best Sharpe: {stats['best_sharpe']:.2f}")
        print(f"  Validation Pass Rate: {stats['validation_pass_rate']:.1%}")
        print(f"  Exploration Usage: {stats['exploration_usage']}")
        print(f"  Champion Usage: {stats['champion_usage']}")

    # Get best performing template
    best = analytics.get_best_performing_template()
    print(f"\n{'='*70}")
    print(f"BEST PERFORMING TEMPLATE: {best}")
    print(f"{'='*70}")

    # Get usage trend
    print(f"\n{'='*70}")
    print("RECENT USAGE TREND (Last 5 Iterations)")
    print(f"{'='*70}")

    trend = analytics.get_usage_trend(last_n_iterations=5)
    for record in trend:
        print(f"\nIteration {record['iteration']}: {record['template_name']}")
        print(f"  Sharpe: {record['sharpe_ratio']:.2f}")
        print(f"  Validation: {'✓' if record['validation_passed'] else '✗'}")
        print(f"  Match Score: {record['match_score']:.2f}")

    # Export comprehensive report
    report_file = analytics_file.replace('.json', '_report.json')
    analytics.export_report(report_file)
    print(f"\n{'='*70}")
    print(f"Comprehensive report exported to: {report_file}")
    print(f"{'='*70}")

    # Show report contents
    with open(report_file, 'r') as f:
        report = json.load(f)

    print(f"\nReport Summary:")
    print(f"  Generated at: {report['generated_at']}")
    print(f"  Total Records: {report['total_records']}")
    print(f"  Best Template: {report['best_template']}")
    print(f"  Templates Tracked: {len(report['template_summary'])}")


def example_5_feedback_loop_integration():
    """Example 5: Full feedback loop integration."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Complete Feedback Loop Integration")
    print("="*70)

    # Initialize components
    template_integrator = TemplateFeedbackIntegrator(repository=None)
    loop_integrator = FeedbackLoopIntegrator(
        template_integrator=template_integrator,
        repository=None
    )

    # Simulate 5 iterations
    print("\nProcessing 5 iterations with feedback loop...")

    for iteration in range(1, 6):
        # Simulate backtest results (improving over time)
        backtest_result = {
            'sharpe_ratio': 0.5 + (iteration * 0.2),
            'max_drawdown': 0.20 - (iteration * 0.02),
            'total_return': 0.10 + (iteration * 0.05),
            'volatility': 0.18 - (iteration * 0.01)
        }

        # Process iteration
        feedback = loop_integrator.process_iteration(
            iteration=iteration,
            strategy_code=f"# Strategy code for iteration {iteration}",
            backtest_result=backtest_result,
            current_params={'n_stocks': 10}
        )

        print(f"\n{'='*70}")
        print(f"Iteration {iteration}")
        print(f"{'='*70}")
        print(f"Template: {feedback.template_recommendation.template_name}")
        print(f"Sharpe: {feedback.performance_metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {feedback.performance_metrics['max_drawdown']:.1%}")
        print(f"Exploration Mode: {feedback.template_recommendation.exploration_mode}")

        if feedback.suggested_improvements:
            print(f"\nSuggested Improvements:")
            for improvement in feedback.suggested_improvements[:3]:
                print(f"  • {improvement}")

    # Get learning trajectory
    trajectory = loop_integrator.get_learning_trajectory()

    print(f"\n{'='*70}")
    print("LEARNING TRAJECTORY ANALYSIS")
    print(f"{'='*70}")
    print(f"Total Iterations: {trajectory['total_iterations']}")
    print(f"Is Improving: {trajectory['is_improving']}")
    print(f"Best Sharpe: {trajectory['best_sharpe']:.2f}")
    print(f"Current Sharpe: {trajectory['current_sharpe']:.2f}")
    print(f"Improvement Trend: {trajectory['improvement_trend']:.2f}")

    print(f"\nSharpe Progression:")
    for i, sharpe in enumerate(trajectory['sharpe_trajectory'], 1):
        print(f"  Iteration {i}: {sharpe:.2f}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("TEMPLATE FEEDBACK SYSTEM - QUICK START EXAMPLES")
    print("="*70)

    try:
        example_1_basic_recommendation()
        example_2_exploration_mode()
        example_3_validation_feedback()
        example_4_analytics_tracking()
        example_5_feedback_loop_integration()

        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nNext Steps:")
        print("  1. Review the feedback system documentation: docs/FEEDBACK_SYSTEM.md")
        print("  2. Run the test suite: pytest tests/feedback/ -v")
        print("  3. Integrate with your learning loop using FeedbackLoopIntegrator")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
