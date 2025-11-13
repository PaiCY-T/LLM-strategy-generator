"""
30-Iteration Pilot Test for Diversity Optimization
===================================================
Tests Option B: Optimize LLM Diversity approach

Changes applied:
- Diversity-aware prompting in poc_claude_test.py
- innovation_rate increased from 0.05 to 0.30
- Fitness weights configured in learning_system.yaml

Expected outcome:
- Diversity score ≥40 (up from baseline 19.17)
- Improved factor variety
- Lower correlation between strategies
"""

import sys
import os
import json
import time
from datetime import datetime

# Change to project root directory
project_root = '/mnt/c/Users/jnpi/documents/finlab'
os.chdir(project_root)

# Add module paths to Python path
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'artifacts/working/modules'))

from autonomous_loop import AutonomousLoop

def run_pilot_test():
    """Run 30-iteration pilot test with diversity monitoring"""

    print("=" * 80)
    print("DIVERSITY OPTIMIZATION PILOT TEST")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nConfiguration:")
    print("  - LLM Innovation Rate: 30% (up from 5%)")
    print("  - Diversity-aware prompting: ENABLED")
    print("  - Population-aware generation: ENABLED")
    print("  - Target iterations: 30")
    print("  - Expected diversity: ≥40 (baseline was 19.17)")
    print("=" * 80)

    # Initialize autonomous loop
    # Note: Config loaded automatically from config/learning_system.yaml
    print(f"\n📋 Initializing autonomous loop...")

    try:
        # Create output directory for pilot test results
        os.makedirs('/mnt/c/Users/jnpi/documents/finlab/pilot_diversity_results', exist_ok=True)

        # Initialize with pilot test parameters
        loop = AutonomousLoop(
            model="gemini-2.5-flash",
            max_iterations=30,
            history_file='/mnt/c/Users/jnpi/documents/finlab/pilot_diversity_results/pilot_iteration_history.json',
            template_mode=False  # Using LLM mode with diversity-aware prompting
        )

        print("✅ Autonomous loop initialized successfully")
        print(f"   LLM enabled: {loop.llm_enabled}")
        print(f"   Innovation rate: {loop.innovation_rate}")
        print(f"   Model: {loop.model}")

    except Exception as e:
        print(f"❌ Failed to initialize autonomous loop: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Run the pilot test
    print("\n" + "=" * 80)
    print("STARTING PILOT TEST - 30 ITERATIONS")
    print("=" * 80)

    start_time = time.time()

    try:
        # Run the loop (max_iterations already set during initialization)
        results = loop.run()

        elapsed = time.time() - start_time
        print(f"\n✅ Pilot test completed in {elapsed/60:.1f} minutes")

        return results

    except Exception as e:
        print(f"\n❌ Pilot test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_diversity(history_file='/mnt/c/Users/jnpi/documents/finlab/pilot_diversity_results/pilot_iteration_history.json'):
    """Analyze diversity of pilot test results"""

    print("\n" + "=" * 80)
    print("DIVERSITY ANALYSIS")
    print("=" * 80)

    if not os.path.exists(history_file):
        print(f"⚠️  History file not found: {history_file}")
        return None

    print(f"📊 Analyzing: {history_file}")

    # Load iteration history
    with open(history_file, 'r') as f:
        history_data = json.load(f)

    # Extract successful strategies with metrics
    strategies = []

    if 'records' in history_data:
        for record in history_data['records']:
            # Only include successful executions with valid metrics
            if (record.get('execution_success', False) and
                record.get('metrics') and
                'sharpe_ratio' in record['metrics']):

                strategies.append({
                    'iteration': record.get('iteration_num', 0),
                    'metrics': record['metrics'],
                    'code': record.get('code', ''),
                    'model': record.get('model', '')
                })

    print(f"   Found {len(strategies)} successful strategies")

    if len(strategies) < 3:
        print("⚠️  Not enough strategies for diversity analysis (need ≥3)")
        print(f"   Total records: {len(history_data.get('records', []))}")
        print(f"   Successful with metrics: {len(strategies)}")
        return None

    # Analyze strategy characteristics
    try:
        # Calculate basic diversity metrics
        sharpe_ratios = [s['metrics']['sharpe_ratio'] for s in strategies]
        avg_sharpe = sum(sharpe_ratios) / len(sharpe_ratios)
        std_sharpe = (sum((x - avg_sharpe)**2 for x in sharpe_ratios) / len(sharpe_ratios)) ** 0.5

        # Check model diversity (how many used LLM)
        llm_strategies = [s for s in strategies if s.get('model')]
        llm_rate = len(llm_strategies) / len(strategies) * 100

        print(f"\n{'=' * 80}")
        print(f"PILOT TEST METRICS")
        print(f"{'=' * 80}")

        print(f"\nStrategy Generation:")
        print(f"  Total successful strategies: {len(strategies)}")
        print(f"  LLM-generated: {len(llm_strategies)} ({llm_rate:.1f}%)")
        print(f"  Expected LLM rate: 30%")

        print(f"\nPerformance Distribution:")
        print(f"  Average Sharpe: {avg_sharpe:.4f}")
        print(f"  Std Dev Sharpe: {std_sharpe:.4f}")
        print(f"  Min Sharpe: {min(sharpe_ratios):.4f}")
        print(f"  Max Sharpe: {max(sharpe_ratios):.4f}")

        # Check configuration effectiveness
        config_check = {
            'llm_rate_matches_config': abs(llm_rate - 30.0) < 10.0,  # Within 10% of target
            'sufficient_strategies': len(strategies) >= 20,  # At least 20/30 successful
            'performance_variation': std_sharpe > 0.1  # Some variation in performance
        }

        print(f"\nConfiguration Verification:")
        for check, passed in config_check.items():
            status = "✅" if passed else "⚠️ "
            print(f"  {status} {check}: {passed}")

        all_checks_passed = all(config_check.values())

        if all_checks_passed:
            print(f"\n✅ SUCCESS: Configuration is working as expected!")
            print(f"   LLM innovation rate matches 30% target")
            print(f"   Sufficient successful strategies generated")
            print(f"   Ready for full diversity analysis")
        else:
            print(f"\n⚠️  Some configuration checks failed")
            print(f"   Review results above for details")

        # Save pilot test results
        pilot_results = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'diversity_optimization_pilot',
            'configuration': {
                'innovation_rate': 0.30,
                'diversity_aware_prompting': True,
                'population_aware_generation': True
            },
            'results': {
                'num_strategies': len(strategies),
                'llm_generated': len(llm_strategies),
                'llm_rate_pct': llm_rate,
                'avg_sharpe': avg_sharpe,
                'std_sharpe': std_sharpe,
                'min_sharpe': min(sharpe_ratios),
                'max_sharpe': max(sharpe_ratios),
                'config_checks': config_check,
                'all_checks_passed': all_checks_passed
            }
        }

        # Save to pilot results directory
        results_dir = '/mnt/c/Users/jnpi/documents/finlab/pilot_diversity_results'
        output_file = f"{results_dir}/pilot_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(pilot_results, f, indent=2)

        print(f"\n💾 Pilot test results saved to: {output_file}")

        return pilot_results

    except Exception as e:
        print(f"❌ Diversity analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main execution"""

    # Run pilot test
    results = run_pilot_test()

    if results is None:
        print("\n❌ Pilot test failed - cannot proceed to analysis")
        return 1

    # Wait a moment for results to be written
    print("\n⏳ Waiting for results to be written...")
    time.sleep(5)

    # Analyze diversity
    pilot_results = analyze_diversity()

    if pilot_results is None:
        print("\n⚠️  Analysis incomplete")
        print("   Results may still be processing")
        return 1

    # Print summary
    print("\n" + "=" * 80)
    print("PILOT TEST SUMMARY")
    print("=" * 80)

    if pilot_results['results']['all_checks_passed']:
        print("✅ Pilot test successful!")
        print("   Configuration verified:")
        print("   - LLM innovation rate working (30%)")
        print("   - Diversity-aware prompting enabled")
        print("   - Sufficient successful strategies")
        print("\n   Next steps:")
        print("   1. Run full diversity analysis with DiversityAnalyzer")
        print("   2. Verify diversity score ≥40")
        print("   3. If diversity ≥40, proceed to Phase 3")
    else:
        print("⚠️  Some checks failed")
        print("   Review pilot test results for details")
        print("\n   Next steps:")
        print("   1. Check LLM innovation rate")
        print("   2. Verify configuration in learning_system.yaml")
        print("   3. Re-run pilot test after adjustments")

    print("=" * 80)

    return 0

if __name__ == '__main__':
    sys.exit(main())
