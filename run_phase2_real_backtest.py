#!/usr/bin/env python3
"""
Phase 2 Test: 20 generations with Flash Lite and real backtest
- 5% LLM innovation rate
- Docker sandbox enabled
- Real finlab data access
- Champion updates enabled
"""
import sys
import os

# Add artifacts/working/modules to sys.path for autonomous_loop imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'artifacts/working/modules'))

import json
from pathlib import Path
from autonomous_loop import AutonomousLoop

def main():
    print("=" * 60)
    print("PHASE 2: 20 GENERATIONS WITH REAL BACKTEST")
    print("=" * 60)
    print()
    print("Configuration:")
    print("  Model: gemini-2.5-flash-lite")
    print("  Max iterations: 20")
    print("  Innovation rate: 5% (from config/learning_system.yaml)")
    print("  Sandbox: ENABLED")
    print("  Champion updates: ENABLED")
    print()

    # Create autonomous loop
    # Config is loaded automatically from config/learning_system.yaml
    # Sandbox, LLM, and Champion updates are configured in the YAML
    loop = AutonomousLoop(
        model="gemini-2.5-flash-lite",  # Fast model for Phase 2
        max_iterations=20,
        history_file="iteration_history.json"
    )

    print(f"✅ Loop created")
    print(f"   Model: {loop.model}")
    print(f"   Max iterations: {loop.max_iterations}")
    print(f"   LLM enabled: {loop.llm_enabled}")
    print(f"   Innovation rate: {loop.innovation_rate:.1%}")
    print(f"   Sandbox enabled: {loop.sandbox_executor.sandbox_enabled if hasattr(loop, 'sandbox_executor') else 'Unknown'}")
    print()

    # Run loop
    print("🚀 Starting Phase 2 test...")
    print()
    results = loop.run()

    # Print results
    print()
    print("=" * 60)
    print("PHASE 2 RESULTS")
    print("=" * 60)
    print(f"Total iterations: {results['total_iterations']}")
    print(f"Successful: {results['successful_iterations']}")
    print(f"Failed: {results['failed_iterations']}")
    print(f"Success rate: {results['success_rate']:.1%}")
    print(f"Total time: {results['elapsed_time']:.1f}s")
    print(f"Time per iteration: {results['elapsed_time']/results['total_iterations']:.1f}s")
    print()

    # LLM statistics
    llm_stats = results.get('llm_statistics', {})
    print("LLM INNOVATION STATISTICS")
    print("-" * 60)
    print(f"LLM enabled: {llm_stats.get('llm_enabled', False)}")
    print(f"Innovation rate: {llm_stats.get('innovation_rate', 0):.1%}")
    print(f"LLM innovations: {llm_stats.get('llm_innovations', 0)}")
    print(f"LLM fallbacks: {llm_stats.get('llm_fallbacks', 0)}")
    print(f"Factor Graph mutations: {llm_stats.get('factor_mutations', 0)}")
    print(f"LLM success rate: {llm_stats.get('llm_success_rate', 0):.1%}")

    if llm_stats.get('llm_costs'):
        cost_report = llm_stats['llm_costs']
        print(f"\nLLM Costs:")
        print(f"  Total cost: ${cost_report['total_cost_usd']:.6f}")
        print(f"  Total tokens: {cost_report['total_tokens']}")
        print(f"  Successful generations: {cost_report['successful_generations']}")
    print()

    # Save results
    results_file = Path("phase2_20gen_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Results saved to {results_file}")

    # Summary
    print()
    print("=" * 60)
    print("PHASE 2 VALIDATION TARGETS")
    print("=" * 60)
    print("✓ Real Sharpe ratio (not Mock data)")
    print("✓ Real backtest performance metrics")
    print("✓ vs Champion comparison")
    print()

    if results['successful_iterations'] > 0:
        print("✅ PHASE 2 COMPLETED SUCCESSFULLY")
        print(f"   Check generated_strategy_loop_iter*.py for strategies")
        print(f"   Check iteration_history.json for metrics")
        return 0
    else:
        print("❌ PHASE 2 FAILED")
        print(f"   All {results['total_iterations']} iterations failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
