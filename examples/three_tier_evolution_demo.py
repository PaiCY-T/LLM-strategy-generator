"""
Three-Tier Evolution System Demo

Demonstrates the complete three-tier mutation system integration:
- Tier 1 (Safe): YAML configuration mutations
- Tier 2 (Domain): Factor-level mutations
- Tier 3 (Advanced): AST code mutations

Architecture: Structural Mutation Phase 2 - Phase D.5
Task: D.5 - Three-Tier Mutation System Integration

Usage:
    python examples/three_tier_evolution_demo.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.population.population_manager_v2 import PopulationManagerV2
from src.mutation.unified_mutation_operator import UnifiedMutationOperator
from src.mutation.tier_performance_tracker import TierPerformanceTracker
from src.tier1.yaml_interpreter import YAMLInterpreter
from src.mutation.tier2.smart_mutation_engine import SmartMutationEngine
from src.mutation.tier2.parameter_mutator import ParameterMutator
from src.mutation.tier3.ast_factor_mutator import ASTFactorMutator
from src.mutation.tier_selection.tier_selection_manager import TierSelectionManager
from src.factor_graph.strategy import Strategy
from src.factor_graph.factor import Factor, FactorCategory


def create_sample_strategy() -> Strategy:
    """Create a sample strategy for demonstration."""
    strategy = Strategy(id="demo_strategy", generation=0)

    # Create a simple momentum factor
    def momentum_logic(data, params):
        period = params.get("period", 20)
        data[f"momentum_{period}"] = data["close"].pct_change(period)
        return data

    momentum_factor = Factor(
        id="momentum_factor",
        name="Momentum Factor",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["momentum_20"],
        logic=momentum_logic,
        parameters={"period": 20}
    )

    strategy.add_factor(momentum_factor)
    return strategy


def demo_unified_mutation_operator():
    """Demonstrate unified mutation operator."""
    print("=" * 60)
    print("DEMO 1: Unified Mutation Operator")
    print("=" * 60)

    # Initialize components
    yaml_interpreter = YAMLInterpreter()

    # Tier 2 engine with parameter mutator
    tier2_operators = {
        "mutate_parameters": ParameterMutator()
    }
    tier2_config = {
        "schedule": {"max_generations": 100},
        "initial_probabilities": {"mutate_parameters": 1.0}
    }
    tier2_engine = SmartMutationEngine(tier2_operators, tier2_config)

    # Tier 3 AST mutator
    tier3_mutator = ASTFactorMutator()

    # Tier selection manager
    tier_selector = TierSelectionManager(
        tier1_threshold=0.3,
        tier2_threshold=0.7,
        enable_adaptation=True
    )

    # Create unified operator
    operator = UnifiedMutationOperator(
        yaml_interpreter=yaml_interpreter,
        tier2_engine=tier2_engine,
        tier3_mutator=tier3_mutator,
        tier_selector=tier_selector,
        enable_fallback=True,
        validate_mutations=False  # Disabled for demo
    )

    print("✓ Unified mutation operator initialized")
    print(f"  - Fallback enabled: {operator.enable_fallback}")
    print(f"  - Validation enabled: {operator.validate_mutations}")

    # Create sample strategy
    strategy = create_sample_strategy()
    print(f"\n✓ Sample strategy created: {strategy.id}")
    print(f"  - Factors: {len(strategy.get_factors())}")

    # Attempt mutations
    print("\n→ Attempting Tier 2 mutation...")
    result = operator.mutate_strategy(
        strategy=strategy,
        mutation_config={
            "intent": "mutate_parameters",
            "override_tier": 2,  # Force Tier 2
            "tier2_config": {"mutation_rate": 0.5}
        }
    )

    print(f"  - Success: {result.success}")
    print(f"  - Tier used: {result.tier_used}")
    print(f"  - Mutation type: {result.mutation_type}")
    if result.error:
        print(f"  - Error: {result.error}")

    # Get statistics
    print("\n→ Mutation statistics:")
    stats = operator.get_tier_statistics()
    print(f"  - Total mutations: {stats['total_mutations']}")
    print(f"  - Success rate: {stats['success_rate']:.1%}")
    for tier in [1, 2, 3]:
        attempts = stats['tier_attempts'][tier]
        if attempts > 0:
            rate = stats['tier_success_rates'][tier]
            print(f"  - Tier {tier}: {attempts} attempts, {rate:.1%} success")

    print("\n✓ Demo 1 complete\n")


def demo_tier_performance_tracker():
    """Demonstrate tier performance tracker."""
    print("=" * 60)
    print("DEMO 2: Tier Performance Tracker")
    print("=" * 60)

    tracker = TierPerformanceTracker()
    print("✓ Tracker initialized")

    # Simulate mutations
    print("\n→ Simulating mutations...")

    # Tier 2 mutations (mostly successful)
    for i in range(10):
        tracker.record_mutation(
            tier=2,
            success=(i < 8),  # 80% success rate
            performance_delta=0.05 if (i < 8) else 0.0,
            mutation_type="add_factor",
            strategy_id=f"strategy_{i}"
        )

    # Tier 3 mutations (less successful but higher improvement)
    for i in range(5):
        tracker.record_mutation(
            tier=3,
            success=(i < 2),  # 40% success rate
            performance_delta=0.15 if (i < 2) else 0.0,
            mutation_type="ast_mutation",
            strategy_id=f"strategy_{i+10}"
        )

    print(f"  - Recorded {15} mutations")

    # Get summary
    print("\n→ Tier summary:")
    summary = tracker.get_tier_summary()

    for tier in [1, 2, 3]:
        stats = summary[f"tier_{tier}"]
        if stats["count"] > 0:
            print(f"  Tier {tier}:")
            print(f"    - Attempts: {stats['count']}")
            print(f"    - Success rate: {stats['success_rate']:.1%}")
            print(f"    - Avg improvement: {stats['avg_improvement']:.4f}")
            print(f"    - Best improvement: {stats['best_improvement']:.4f}")

    # Get comparison
    print("\n→ Tier comparison:")
    comparison = tracker.get_tier_comparison()
    print(f"  - Most used tier: {comparison['most_used_tier']}")
    print(f"  - Best tier by success rate: {comparison['best_tier_by_success_rate']}")
    print(f"  - Best tier by improvement: {comparison['best_tier_by_improvement']}")

    # Distribution
    print("\n→ Tier distribution:")
    for tier, pct in comparison["tier_distribution_pct"].items():
        print(f"  - Tier {tier}: {pct:.1%}")

    print("\n✓ Demo 2 complete\n")


def demo_population_manager_v2():
    """Demonstrate PopulationManagerV2."""
    print("=" * 60)
    print("DEMO 3: PopulationManagerV2")
    print("=" * 60)

    config = {
        "population_size": 10,
        "elite_size": 2,
        "enable_three_tier": True,
        "tier_selection_config": {
            "tier1_threshold": 0.3,
            "tier2_threshold": 0.7,
            "enable_adaptation": True
        },
        "mutation_config": {
            "tier2": {
                "schedule": {"max_generations": 50},
                "initial_probabilities": {"mutate_parameters": 1.0}
            }
        }
    }

    manager = PopulationManagerV2(config)
    print("✓ PopulationManagerV2 initialized")
    print(f"  - Population size: {manager.population_size}")
    print(f"  - Elite size: {manager.elite_size}")
    print(f"  - Three-tier enabled: {manager.enable_three_tier}")

    # Get evolution report (empty at start)
    print("\n→ Initial evolution report:")
    report = manager.get_evolution_report()
    print(f"  - Three-tier enabled: {report['three_tier_enabled']}")
    print(f"  - Current generation: {report['current_generation']}")

    # Attempt strategy mutation
    strategy = create_sample_strategy()
    print(f"\n→ Mutating strategy: {strategy.id}")

    try:
        mutated = manager.mutate_strategy(strategy, generation=0)
        print(f"  - Mutated strategy: {mutated.id}")
        print(f"  - Generation: {mutated.generation}")
    except Exception as e:
        print(f"  - Mutation encountered expected limitation: {type(e).__name__}")
        print(f"    (This is expected in demo mode)")

    # Get tier recommendations
    print("\n→ Tier recommendations:")
    try:
        recommendations = manager.get_tier_recommendations()
        if "three_tier_enabled" in recommendations:
            print(f"  - Recommendations available: {recommendations['three_tier_enabled']}")
    except Exception as e:
        print(f"  - No recommendations yet (system warming up)")

    print("\n✓ Demo 3 complete\n")


def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("THREE-TIER EVOLUTION SYSTEM DEMO")
    print("=" * 60)
    print("\nDemonstrating the complete three-tier mutation system:")
    print("  - Tier 1: YAML configuration mutations (Safe)")
    print("  - Tier 2: Factor-level mutations (Domain-specific)")
    print("  - Tier 3: AST code mutations (Advanced)")
    print()

    try:
        demo_unified_mutation_operator()
        demo_tier_performance_tracker()
        demo_population_manager_v2()

        print("=" * 60)
        print("ALL DEMOS COMPLETE")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("  1. UnifiedMutationOperator provides a single interface for all tiers")
        print("  2. Tier selection is adaptive based on risk assessment")
        print("  3. Automatic fallback ensures robustness")
        print("  4. Comprehensive tracking enables analysis and optimization")
        print("  5. PopulationManagerV2 integrates seamlessly with evolution loop")
        print()

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
