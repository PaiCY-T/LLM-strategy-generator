#!/usr/bin/env python3
"""
Quick LLM Innovation Baseline Test

Tests the LLM innovation system with a quick 5-iteration run using MockLLM.
This validates the system architecture without consuming API quota.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from innovation.innovation_engine import InnovationEngine


def main():
    """Run quick 5-iteration smoke test."""
    print("=" * 70)
    print("LLM INNOVATION BASELINE TEST (5 iterations)")
    print("=" * 70)
    print()

    # Load baseline metrics
    baseline_path = Path(".claude/specs/llm-innovation-capability/baseline_metrics.json")
    with open(baseline_path, 'r') as f:
        baseline_data = json.load(f)
        baseline = baseline_data['metrics']

    print("📊 Baseline Metrics (Task 0.1):")
    print(f"   Mean Sharpe:   {baseline['mean_sharpe']:.4f}")
    print(f"   Mean Calmar:   {baseline['mean_calmar']:.4f}")
    print(f"   Target Sharpe: {baseline['adaptive_sharpe_threshold']:.4f}")
    print(f"   Target Calmar: {baseline['adaptive_calmar_threshold']:.4f}")
    print()

    # Initialize engine with MockLLM
    print("🔧 Initializing InnovationEngine (MockLLM)...")
    engine = InnovationEngine(
        baseline_sharpe=baseline['mean_sharpe'],
        baseline_calmar=baseline['mean_calmar'],
        innovation_frequency=0.20,  # 20% probability
        use_mock_llm=True,  # Use MockLLM for testing
        repository_path="artifacts/data/test_baseline_innovations.jsonl"
    )
    print("✅ Engine initialized")
    print()

    # Run 5 iterations
    print("=" * 70)
    print("RUNNING 5 ITERATIONS")
    print("=" * 70)
    print()

    categories = ['quality', 'value', 'growth', 'momentum', 'mixed']
    results = {
        'test_date': datetime.now().isoformat(),
        'baseline': baseline,
        'iterations': [],
        'summary': {
            'total_iterations': 5,
            'innovations_attempted': 0,
            'innovations_created': 0,
            'innovations_validated': 0
        }
    }

    for i in range(5):
        print(f"Iteration {i+1}/5:")

        # Check if innovation should be attempted
        should_innovate = engine._should_attempt_innovation()

        if should_innovate:
            results['summary']['innovations_attempted'] += 1
            category = categories[i % len(categories)]
            print(f"  🧪 Attempting innovation (category: {category})...")

            # Attempt innovation
            innovation = engine.attempt_innovation(category=category)

            if innovation:
                results['summary']['innovations_created'] += 1
                results['summary']['innovations_validated'] += 1
                print(f"  ✅ Innovation SUCCESS: {innovation['factor_name']}")
                print(f"     Mock Sharpe: {innovation['mock_sharpe']:.3f}")

                results['iterations'].append({
                    'iteration': i,
                    'innovation_attempted': True,
                    'innovation_success': True,
                    'factor_name': innovation['factor_name'],
                    'category': category,
                    'mock_sharpe': innovation['mock_sharpe']
                })
            else:
                print(f"  ❌ Innovation FAILED: Validation rejected")
                results['iterations'].append({
                    'iteration': i,
                    'innovation_attempted': True,
                    'innovation_success': False,
                    'category': category
                })
        else:
            print(f"  ⚪ Standard mutation (no innovation)")
            results['iterations'].append({
                'iteration': i,
                'innovation_attempted': False
            })

        print()

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    summary = results['summary']
    print(f"Total Iterations:       {summary['total_iterations']}")
    print(f"Innovations Attempted:  {summary['innovations_attempted']}")
    print(f"Innovations Created:    {summary['innovations_created']}")
    print(f"Innovations Validated:  {summary['innovations_validated']}")

    if summary['innovations_attempted'] > 0:
        success_rate = summary['innovations_created'] / summary['innovations_attempted']
        print(f"Success Rate:           {success_rate:.1%}")
    else:
        print(f"Success Rate:           N/A (no attempts)")
    print()

    # Check repository
    print("📚 Checking Innovation Repository...")
    repo_path = Path("artifacts/data/test_baseline_innovations.jsonl")
    if repo_path.exists():
        with open(repo_path, 'r') as f:
            lines = f.readlines()
            print(f"✅ Repository has {len(lines)} innovations")

            # Show first innovation
            if lines:
                first = json.loads(lines[0])
                print(f"\nExample Innovation:")
                print(f"  Factor: {first.get('factor_name', 'N/A')}")
                print(f"  Category: {first.get('category', 'N/A')}")
    else:
        print("⚠️  Repository file not found")

    print()

    # Save results
    output_path = Path("test_baseline_results.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Results saved to: {output_path}")
    print()

    # Status
    print("=" * 70)
    print("STATUS")
    print("=" * 70)

    if summary['innovations_created'] > 0:
        print("✅ TEST PASSED: Innovation system is operational")
        print(f"   Created {summary['innovations_created']} innovation(s)")
    else:
        if summary['innovations_attempted'] > 0:
            print("⚠️  TEST WARNING: No innovations created (validation too strict?)")
        else:
            print("⚠️  TEST WARNING: No innovation attempts (frequency too low?)")

    print()
    print("Next steps:")
    print("1. Review results in test_baseline_results.json")
    print("2. Check innovations in artifacts/data/test_baseline_innovations.jsonl")
    print("3. Run full 20-iteration test: python run_20iteration_innovation_test.py")
    print()


if __name__ == "__main__":
    main()
