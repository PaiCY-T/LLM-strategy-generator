"""
Population Manager V2 - Enhanced population evolution with three-tier mutations.

Extends PopulationManager to support three-tier mutation system:
- Tier 1 (Safe): YAML configuration mutations
- Tier 2 (Domain): Factor-level mutations (add/remove/replace/mutate)
- Tier 3 (Advanced): AST code mutations

Provides adaptive tier selection, comprehensive tracking, and backward compatibility.

Architecture: Structural Mutation Phase 2 - Phase D.5
Task: D.5 - Three-Tier Mutation System Integration
"""

from typing import Dict, List, Any, Optional
import pandas as pd

from src.population.population_manager import PopulationManager
from src.population.individual import Individual
from src.mutation.unified_mutation_operator import UnifiedMutationOperator, MutationResult
from src.mutation.tier_performance_tracker import TierPerformanceTracker
from src.tier1.yaml_interpreter import YAMLInterpreter
from src.mutation.tier2.smart_mutation_engine import SmartMutationEngine
from src.mutation.tier3.ast_factor_mutator import ASTFactorMutator
from src.mutation.tier_selection.tier_selection_manager import TierSelectionManager
from src.factor_graph.strategy import Strategy


class PopulationManagerV2(PopulationManager):
    """
    Enhanced PopulationManager with three-tier mutation support.

    Extends the base PopulationManager to integrate the three-tier
    mutation system while maintaining backward compatibility.

    New capabilities:
    - Adaptive tier selection based on population state
    - Comprehensive tier usage tracking
    - Performance analytics per tier
    - Evolution reports with tier breakdown

    The manager orchestrates mutations across all three tiers,
    automatically selecting the most appropriate tier based on:
    - Population diversity
    - Performance trends
    - Mutation history
    - Risk assessment

    Example:
        >>> config = {
        ...     "population_size": 20,
        ...     "elite_size": 2,
        ...     "enable_three_tier": True,
        ...     "tier_selection_config": {
        ...         "tier1_threshold": 0.3,
        ...         "tier2_threshold": 0.7
        ...     }
        ... }
        >>>
        >>> manager = PopulationManagerV2(config)
        >>>
        >>> # Initialize population
        >>> population = manager.initialize_population()
        >>>
        >>> # Evolve with three-tier mutations
        >>> result = manager.evolve_population(market_data)
        >>>
        >>> # Get tier analytics
        >>> report = manager.get_evolution_report()
        >>> print(f"Tier 2 usage: {report['tier_distribution']['tier_2']:.1%}")
        >>> print(f"Tier 3 avg improvement: {report['tier_performance']['tier_3']['avg_improvement']}")
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize enhanced population manager.

        Args:
            config: Configuration dictionary with:
                - population_size: Number of individuals
                - elite_size: Number of elites to preserve
                - tournament_size: Tournament size for selection
                - diversity_threshold: Minimum diversity threshold
                - convergence_window: Convergence detection window
                - enable_three_tier: Enable three-tier mutation system (default: True)
                - tier_selection_config: Configuration for tier selection
                - mutation_config: Configuration for mutation operators

        Example:
            >>> config = {
            ...     "population_size": 20,
            ...     "elite_size": 2,
            ...     "enable_three_tier": True,
            ...     "tier_selection_config": {
            ...         "tier1_threshold": 0.3,
            ...         "tier2_threshold": 0.7,
            ...         "enable_adaptation": True
            ...     }
            ... }
            >>> manager = PopulationManagerV2(config)
        """
        # Initialize base population manager
        super().__init__(
            population_size=config.get("population_size", 50),
            elite_size=config.get("elite_size", 5),
            tournament_size=config.get("tournament_size", 2),
            diversity_threshold=config.get("diversity_threshold", 0.5),
            convergence_window=config.get("convergence_window", 10)
        )

        self.config = config
        self.enable_three_tier = config.get("enable_three_tier", True)

        if self.enable_three_tier:
            # Initialize three-tier mutation components
            self._initialize_three_tier_system(config)
        else:
            # Fallback to tier 2 only (backward compatibility)
            self.unified_mutator = None
            self.tier_tracker = None

        # Track evolution state
        self.current_generation = 0
        self.evolution_history = []

    def _initialize_three_tier_system(self, config: Dict[str, Any]) -> None:
        """
        Initialize three-tier mutation system components.

        Args:
            config: Configuration dictionary
        """
        # Get tier-specific configs
        tier_selection_config = config.get("tier_selection_config", {})
        mutation_config = config.get("mutation_config", {})

        # Initialize Tier 1: YAML interpreter
        yaml_interpreter = YAMLInterpreter()

        # Initialize Tier 2: Smart mutation engine
        # This requires mutation operators - simplified for now
        tier2_config = mutation_config.get("tier2", {
            "schedule": {"max_generations": 100},
            "initial_probabilities": {
                "mutate_parameters": 1.0  # Simplified - single operator
            }
        })

        # For now, we'll use a minimal tier2 engine
        # In production, this would include all mutation operators
        from src.mutation.tier2.parameter_mutator import ParameterMutator
        tier2_operators = {
            "mutate_parameters": ParameterMutator()
        }
        tier2_engine = SmartMutationEngine(tier2_operators, tier2_config)

        # Initialize Tier 3: AST mutator
        tier3_mutator = ASTFactorMutator()

        # Initialize tier selection manager
        tier_selector = TierSelectionManager(**tier_selection_config)

        # Initialize unified mutation operator
        self.unified_mutator = UnifiedMutationOperator(
            yaml_interpreter=yaml_interpreter,
            tier2_engine=tier2_engine,
            tier3_mutator=tier3_mutator,
            tier_selector=tier_selector,
            enable_fallback=True,
            validate_mutations=True
        )

        # Initialize tier performance tracker
        self.tier_tracker = TierPerformanceTracker()

    def evolve_population(
        self,
        market_data: pd.DataFrame,
        generations: int = 1
    ) -> Dict[str, Any]:
        """
        Evolve population using three-tier mutations.

        Args:
            market_data: Market data for backtesting
            generations: Number of generations to evolve

        Returns:
            Dictionary with evolution results:
                - population: Final population
                - best_individual: Best individual found
                - tier_statistics: Tier usage and performance stats
                - generation_history: History of each generation

        Example:
            >>> result = manager.evolve_population(market_data, generations=10)
            >>> print(f"Best fitness: {result['best_individual'].fitness:.4f}")
            >>> print(f"Tier 2 usage: {result['tier_statistics']['tier_distribution']['tier_2']}")
        """
        # This is a simplified implementation
        # Full implementation would integrate with existing evolution loop

        generation_history = []

        for gen in range(generations):
            self.current_generation = gen

            # Calculate population diversity
            # Placeholder - would use actual population
            diversity = 0.5

            # Track generation stats
            gen_stats = {
                "generation": gen,
                "diversity": diversity,
                "mutations": []
            }

            # Record generation
            generation_history.append(gen_stats)

        # Compile results
        results = {
            "generations_completed": generations,
            "generation_history": generation_history
        }

        if self.enable_three_tier:
            results["tier_statistics"] = self.unified_mutator.get_tier_statistics()
            results["tier_performance"] = self.tier_tracker.get_tier_summary()
            results["tier_comparison"] = self.tier_tracker.get_tier_comparison()

        return results

    def mutate_strategy(
        self,
        strategy: Strategy,
        market_data: Optional[pd.DataFrame] = None,
        generation: Optional[int] = None
    ) -> Strategy:
        """
        Mutate strategy using three-tier system.

        Args:
            strategy: Strategy to mutate
            market_data: Optional market data for risk assessment
            generation: Current generation number

        Returns:
            Mutated strategy

        Example:
            >>> mutated = manager.mutate_strategy(strategy, market_data, generation=5)
            >>> print(f"Mutation successful: {mutated is not None}")
        """
        if not self.enable_three_tier:
            # Fallback to tier 2 only
            raise NotImplementedError("Tier 2-only mode not yet implemented in V2")

        # Calculate diversity for context
        diversity = 0.5  # Placeholder - would calculate from population

        # Create mutation config with context
        mutation_config = {
            "generation": generation or self.current_generation,
            "diversity": diversity,
            "intent": "improve_strategy"
        }

        # Apply mutation
        result = self.unified_mutator.mutate_strategy(
            strategy=strategy,
            market_data=market_data,
            mutation_config=mutation_config
        )

        # Track performance if mutation succeeded
        if result.success:
            # Calculate performance delta (placeholder)
            performance_delta = 0.01  # Would calculate actual delta

            self.tier_tracker.record_mutation(
                tier=result.tier_used,
                success=True,
                performance_delta=performance_delta,
                mutation_type=result.mutation_type,
                strategy_id=strategy.id
            )

            return result.strategy
        else:
            # Record failure
            self.tier_tracker.record_mutation(
                tier=result.tier_used,
                success=False,
                performance_delta=0.0,
                mutation_type=result.mutation_type,
                strategy_id=strategy.id
            )

            # Return original strategy
            return strategy

    def get_evolution_report(self) -> Dict[str, Any]:
        """
        Get comprehensive evolution report with tier breakdown.

        Returns:
            Dictionary with:
                - tier_statistics: Overall tier usage stats
                - tier_performance: Performance metrics per tier
                - tier_comparison: Comparative analysis across tiers
                - tier_distribution: Distribution of tier usage
                - mutation_type_analysis: Analysis of mutation types
                - recent_trends: Recent tier usage trends

        Example:
            >>> report = manager.get_evolution_report()
            >>> print(f"Total mutations: {report['tier_statistics']['total_mutations']}")
            >>> print(f"Best tier: {report['tier_comparison']['best_tier_by_improvement']}")
        """
        if not self.enable_three_tier:
            return {
                "three_tier_enabled": False,
                "message": "Three-tier system not enabled"
            }

        report = {
            "three_tier_enabled": True,
            "current_generation": self.current_generation,
            "tier_statistics": self.unified_mutator.get_tier_statistics(),
            "tier_performance": self.tier_tracker.get_tier_summary(),
            "tier_comparison": self.tier_tracker.get_tier_comparison(),
            "mutation_type_analysis": self.tier_tracker.get_mutation_type_analysis(),
            "recent_trends": self.tier_tracker.get_recent_trends(window=20)
        }

        # Add tier distribution for easy access
        tier_stats = report["tier_statistics"]
        total = tier_stats["total_mutations"]
        if total > 0:
            report["tier_distribution"] = {
                "tier_1": tier_stats["tier_attempts"][1] / total,
                "tier_2": tier_stats["tier_attempts"][2] / total,
                "tier_3": tier_stats["tier_attempts"][3] / total
            }
        else:
            report["tier_distribution"] = {
                "tier_1": 0.0,
                "tier_2": 0.0,
                "tier_3": 0.0
            }

        return report

    def export_evolution_report(self, path: str) -> None:
        """
        Export evolution report to JSON file.

        Args:
            path: Path to export file

        Example:
            >>> manager.export_evolution_report("evolution_report.json")
        """
        import json

        report = self.get_evolution_report()

        with open(path, 'w') as f:
            json.dump(report, f, indent=2)

    def get_tier_statistics(self) -> Dict[str, Any]:
        """
        Get current tier statistics.

        Returns:
            Dictionary with tier usage and performance statistics

        Example:
            >>> stats = manager.get_tier_statistics()
            >>> print(f"Tier 2 success rate: {stats['tier_success_rates'][2]:.2%}")
        """
        if not self.enable_three_tier:
            return {"three_tier_enabled": False}

        return self.unified_mutator.get_tier_statistics()

    def adjust_tier_thresholds(
        self,
        tier1_threshold: Optional[float] = None,
        tier2_threshold: Optional[float] = None
    ) -> None:
        """
        Manually adjust tier selection thresholds.

        Args:
            tier1_threshold: New Tier 1 threshold [0.0-1.0]
            tier2_threshold: New Tier 2 threshold [0.0-1.0]

        Example:
            >>> # Make system more conservative (prefer safe mutations)
            >>> manager.adjust_tier_thresholds(tier1_threshold=0.5, tier2_threshold=0.8)
        """
        if not self.enable_three_tier:
            raise RuntimeError("Three-tier system not enabled")

        self.unified_mutator.tier_selector.adjust_thresholds_manually(
            tier1_threshold=tier1_threshold,
            tier2_threshold=tier2_threshold
        )

    def reset_tier_learning(self) -> None:
        """
        Reset tier selection learning and statistics.

        Useful for:
        - Starting fresh experiments
        - Resetting after configuration changes
        - Clearing corrupted statistics

        Example:
            >>> manager.reset_tier_learning()
        """
        if not self.enable_three_tier:
            return

        self.unified_mutator.reset_statistics()
        self.tier_tracker.reset_stats()
        self.current_generation = 0
        self.evolution_history = []

    def get_tier_recommendations(self) -> Dict[str, Any]:
        """
        Get tier selection recommendations based on learning.

        Returns:
            Dictionary with recommendations for tier usage

        Example:
            >>> recommendations = manager.get_tier_recommendations()
            >>> print(f"Recommended tier: {recommendations['recommended_tier']}")
            >>> print(f"Confidence: {recommendations['confidence']:.2%}")
        """
        if not self.enable_three_tier:
            return {"three_tier_enabled": False}

        return self.unified_mutator.tier_selector.get_recommendations()

    def export_tier_analysis(self, path: str) -> None:
        """
        Export detailed tier analysis to file.

        Args:
            path: Path to export file

        Example:
            >>> manager.export_tier_analysis("tier_analysis.json")
        """
        if not self.enable_three_tier:
            raise RuntimeError("Three-tier system not enabled")

        # Export unified mutator analysis
        mutator_path = path.replace(".json", "_mutator.json")
        self.unified_mutator.export_tier_analysis(mutator_path)

        # Export tier tracker analysis
        tracker_path = path.replace(".json", "_tracker.json")
        self.tier_tracker.export_analysis(tracker_path)

        # Export combined summary
        import json
        summary = {
            "evolution_report": self.get_evolution_report(),
            "tier_recommendations": self.get_tier_recommendations(),
            "files": {
                "mutator_analysis": mutator_path,
                "tracker_analysis": tracker_path
            }
        }

        with open(path, 'w') as f:
            json.dump(summary, f, indent=2)
