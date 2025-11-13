"""
Tier Selection Demo - Usage examples for adaptive mutation tier selection.

Demonstrates:
- Basic tier selection workflow
- Risk-based tier routing
- Adaptive learning over time
- Manual threshold adjustment
- Integration with mutation system

Architecture: Phase 2.0+ Factor Graph System
Task: D.4 - Adaptive Mutation Tier Selection
"""

import pandas as pd
import networkx as nx
from typing import Dict, Any

# Import tier selection components
from src.mutation.tier_selection import (
    TierSelectionManager,
    MutationTier,
    RiskAssessor,
    TierRouter,
    AdaptiveLearner
)

# Mock Strategy class for demo (replace with actual Strategy from factor_graph)
class MockStrategy:
    """Mock strategy for demonstration."""
    def __init__(self, id: str, complexity: int = 2):
        self.id = id
        self.dag = nx.DiGraph()
        self.factors = {}

        # Create simple DAG based on complexity
        for i in range(complexity):
            factor_id = f"factor_{i}"
            self.factors[factor_id] = None
            if i > 0:
                self.dag.add_edge(f"factor_{i-1}", factor_id)


def example_1_basic_tier_selection():
    """
    Example 1: Basic Tier Selection

    Demonstrates simple tier selection based on strategy complexity.
    """
    print("\n" + "="*60)
    print("Example 1: Basic Tier Selection")
    print("="*60)

    # Create tier selection manager
    manager = TierSelectionManager()

    # Create test strategies with different complexities
    simple_strategy = MockStrategy("simple_momentum", complexity=3)
    complex_strategy = MockStrategy("complex_hybrid", complexity=10)

    # Select tier for simple strategy
    plan_simple = manager.select_mutation_tier(
        strategy=simple_strategy,
        mutation_intent="add_factor"
    )

    print(f"\nSimple Strategy:")
    print(f"  Selected Tier: {plan_simple.tier.value}")
    print(f"  Risk Score: {plan_simple.risk_score:.3f}")
    print(f"  Mutation Type: {plan_simple.mutation_type}")
    print(f"  Rationale: {plan_simple.rationale}")

    # Select tier for complex strategy
    plan_complex = manager.select_mutation_tier(
        strategy=complex_strategy,
        mutation_intent="add_factor"
    )

    print(f"\nComplex Strategy:")
    print(f"  Selected Tier: {plan_complex.tier.value}")
    print(f"  Risk Score: {plan_complex.risk_score:.3f}")
    print(f"  Mutation Type: {plan_complex.mutation_type}")
    print(f"  Rationale: {plan_complex.rationale}")


def example_2_market_based_selection():
    """
    Example 2: Market-Based Tier Selection

    Demonstrates how market volatility affects tier selection.
    """
    print("\n" + "="*60)
    print("Example 2: Market-Based Tier Selection")
    print("="*60)

    manager = TierSelectionManager()
    strategy = MockStrategy("momentum_v1", complexity=5)

    # Stable market data
    stable_market = pd.DataFrame({
        'close': [100.0 + i * 0.5 for i in range(20)]  # Smooth uptrend
    })

    plan_stable = manager.select_mutation_tier(
        strategy=strategy,
        market_data=stable_market,
        mutation_intent="add_factor"
    )

    print(f"\nStable Market Conditions:")
    print(f"  Market Risk: {plan_stable.config['risk_metrics']['market_risk']:.3f}")
    print(f"  Overall Risk: {plan_stable.risk_score:.3f}")
    print(f"  Selected Tier: {plan_stable.tier.value}")

    # Volatile market data
    volatile_market = pd.DataFrame({
        'close': [100, 110, 95, 120, 85, 130, 80, 125]  # High volatility
    })

    plan_volatile = manager.select_mutation_tier(
        strategy=strategy,
        market_data=volatile_market,
        mutation_intent="add_factor"
    )

    print(f"\nVolatile Market Conditions:")
    print(f"  Market Risk: {plan_volatile.config['risk_metrics']['market_risk']:.3f}")
    print(f"  Overall Risk: {plan_volatile.risk_score:.3f}")
    print(f"  Selected Tier: {plan_volatile.tier.value}")


def example_3_adaptive_learning():
    """
    Example 3: Adaptive Learning Over Time

    Demonstrates how the system learns from mutation history
    and adapts tier selection thresholds.
    """
    print("\n" + "="*60)
    print("Example 3: Adaptive Learning Over Time")
    print("="*60)

    # Create manager with adaptation enabled
    manager = TierSelectionManager(
        enable_adaptation=True,
        min_samples=10,
        learning_rate=0.15
    )

    strategy = MockStrategy("evolving_strategy", complexity=5)

    print("\nInitial Thresholds:")
    print(f"  Tier 1 Threshold: {manager._current_tier1_threshold:.3f}")
    print(f"  Tier 2 Threshold: {manager._current_tier2_threshold:.3f}")

    # Simulate 30 mutation iterations
    print("\nRunning 30 mutation iterations...")
    tier_counts = {1: 0, 2: 0, 3: 0}

    for i in range(30):
        # Select tier
        plan = manager.select_mutation_tier(
            strategy=strategy,
            mutation_intent="add_factor"
        )

        tier_counts[plan.tier.value] += 1

        # Simulate mutation success
        # For demo: Tier 2 mutations succeed more often
        if plan.tier == MutationTier.TIER2_FACTOR:
            success = True
            fitness_delta = 0.05
        else:
            success = (i % 3 == 0)  # 33% success for other tiers
            fitness_delta = 0.02 if success else -0.01

        # Record result
        manager.record_mutation_result(
            plan=plan,
            success=success,
            metrics={'fitness_delta': fitness_delta}
        )

    print(f"\nTier Usage Distribution:")
    print(f"  Tier 1: {tier_counts[1]} mutations")
    print(f"  Tier 2: {tier_counts[2]} mutations")
    print(f"  Tier 3: {tier_counts[3]} mutations")

    print(f"\nAdapted Thresholds:")
    print(f"  Tier 1 Threshold: {manager._current_tier1_threshold:.3f}")
    print(f"  Tier 2 Threshold: {manager._current_tier2_threshold:.3f}")

    # Get recommendations
    recommendations = manager.get_recommendations()
    print(f"\nRecommendations:")
    print(f"  Best Performing Tier: {recommendations['recommended_tier']}")
    print(f"  Confidence: {recommendations['confidence']:.3f}")

    # Show tier performance
    print(f"\nTier Performance:")
    for tier_name, perf in recommendations['performance_summary'].items():
        print(f"  {tier_name.upper()}:")
        print(f"    Success Rate: {perf['success_rate']:.1%}")
        print(f"    Attempts: {perf['attempts']}")
        print(f"    Avg Fitness Delta: {perf['avg_fitness_delta']:.4f}")


def example_4_manual_override():
    """
    Example 4: Manual Tier Override

    Demonstrates manual tier selection for experimentation.
    """
    print("\n" + "="*60)
    print("Example 4: Manual Tier Override")
    print("="*60)

    manager = TierSelectionManager()
    strategy = MockStrategy("test_strategy", complexity=5)

    # Normal selection
    plan_normal = manager.select_mutation_tier(
        strategy=strategy,
        mutation_intent="modify_logic"
    )

    print(f"\nNormal Selection:")
    print(f"  Risk Score: {plan_normal.risk_score:.3f}")
    print(f"  Auto-Selected Tier: {plan_normal.tier.value}")

    # Force Tier 1 (safe)
    plan_tier1 = manager.select_mutation_tier(
        strategy=strategy,
        mutation_intent="modify_logic",
        override_tier=1
    )

    print(f"\nForced Tier 1 (Safe):")
    print(f"  Selected Tier: {plan_tier1.tier.value}")
    print(f"  Mutation Type: {plan_tier1.mutation_type}")
    print(f"  Rationale: {plan_tier1.rationale}")

    # Force Tier 3 (advanced)
    plan_tier3 = manager.select_mutation_tier(
        strategy=strategy,
        mutation_intent="modify_logic",
        override_tier=3
    )

    print(f"\nForced Tier 3 (Advanced):")
    print(f"  Selected Tier: {plan_tier3.tier.value}")
    print(f"  Mutation Type: {plan_tier3.mutation_type}")
    print(f"  Rationale: {plan_tier3.rationale}")


def example_5_custom_configuration():
    """
    Example 5: Custom Configuration

    Demonstrates configuring the tier selection system
    for different use cases.
    """
    print("\n" + "="*60)
    print("Example 5: Custom Configuration")
    print("="*60)

    # Conservative configuration (prefer safe mutations)
    conservative_manager = TierSelectionManager(
        tier1_threshold=0.5,  # Expand Tier 1 range
        tier2_threshold=0.8,  # Reduce Tier 3 range
        strategy_complexity_weight=0.5,
        market_risk_weight=0.3,
        mutation_risk_weight=0.2
    )

    # Aggressive configuration (prefer advanced mutations)
    aggressive_manager = TierSelectionManager(
        tier1_threshold=0.2,  # Reduce Tier 1 range
        tier2_threshold=0.5,  # Expand Tier 3 range
        strategy_complexity_weight=0.3,
        market_risk_weight=0.3,
        mutation_risk_weight=0.4
    )

    strategy = MockStrategy("test_strategy", complexity=5)

    # Test with medium risk score
    risk_score = 0.6

    # Conservative selection
    plan_conservative = conservative_manager.select_mutation_tier(
        strategy=strategy,
        mutation_intent="add_factor"
    )

    # Aggressive selection
    plan_aggressive = aggressive_manager.select_mutation_tier(
        strategy=strategy,
        mutation_intent="add_factor"
    )

    print(f"\nConservative Configuration:")
    print(f"  Tier 1 Threshold: 0.5, Tier 2 Threshold: 0.8")
    print(f"  Selected Tier: {plan_conservative.tier.value}")

    print(f"\nAggressive Configuration:")
    print(f"  Tier 1 Threshold: 0.2, Tier 2 Threshold: 0.5")
    print(f"  Selected Tier: {plan_aggressive.tier.value}")

    # Show expected distributions
    print(f"\nExpected Tier Distributions:")

    dist_conservative = conservative_manager.tier_router.get_tier_distribution()
    print(f"  Conservative: Tier1={dist_conservative['tier1']:.1%}, "
          f"Tier2={dist_conservative['tier2']:.1%}, "
          f"Tier3={dist_conservative['tier3']:.1%}")

    dist_aggressive = aggressive_manager.tier_router.get_tier_distribution()
    print(f"  Aggressive:   Tier1={dist_aggressive['tier1']:.1%}, "
          f"Tier2={dist_aggressive['tier2']:.1%}, "
          f"Tier3={dist_aggressive['tier3']:.1%}")


def example_6_state_export():
    """
    Example 6: State Export and Analysis

    Demonstrates exporting manager state for analysis and persistence.
    """
    print("\n" + "="*60)
    print("Example 6: State Export and Analysis")
    print("="*60)

    manager = TierSelectionManager()
    strategy = MockStrategy("test_strategy", complexity=5)

    # Run some mutations
    for i in range(15):
        plan = manager.select_mutation_tier(strategy, mutation_intent="add_factor")
        manager.record_mutation_result(plan, success=(i % 3 != 0))

    # Export state
    state = manager.export_state()

    print(f"\nExported State:")
    print(f"\nThresholds:")
    print(f"  Tier 1: {state['thresholds']['tier1_threshold']:.3f}")
    print(f"  Tier 2: {state['thresholds']['tier2_threshold']:.3f}")

    print(f"\nTier Statistics:")
    for tier_name, stats in state['tier_stats'].items():
        if stats['attempts'] > 0:
            print(f"  {tier_name.upper()}:")
            print(f"    Attempts: {stats['attempts']}")
            print(f"    Success Rate: {stats['success_rate']:.1%}")

    print(f"\nConfiguration:")
    for key, value in state['configuration'].items():
        print(f"  {key}: {value}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print(" Tier Selection System - Usage Examples")
    print("="*70)

    try:
        example_1_basic_tier_selection()
        example_2_market_based_selection()
        example_3_adaptive_learning()
        example_4_manual_override()
        example_5_custom_configuration()
        example_6_state_export()

        print("\n" + "="*70)
        print(" All examples completed successfully!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
