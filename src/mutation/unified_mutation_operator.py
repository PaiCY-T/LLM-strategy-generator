"""
Unified Mutation Operator - Adaptive three-tier mutation interface.

Provides a unified interface for applying mutations across all three tiers:
- Tier 1 (Safe): YAML configuration mutations
- Tier 2 (Domain): Factor-level mutations (add/remove/replace/mutate)
- Tier 3 (Advanced): AST code mutations
- Exit Mutation: Parameter-based exit strategy mutations

The operator dispatches mutations to the appropriate tier based on
adaptive tier selection, with fallback support and comprehensive tracking.

Architecture: Structural Mutation Phase 2 - Phase D.5
Task: D.5 - Three-Tier Mutation System Integration
Exit Mutation Redesign: Phase 1 - Task 3 - Exit Parameter Mutation Integration
"""

import copy
import random
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import logging

from src.tier1.yaml_interpreter import YAMLInterpreter
from src.mutation.tier2.smart_mutation_engine import SmartMutationEngine
from src.mutation.tier3.ast_factor_mutator import ASTFactorMutator
from src.mutation.tier_selection.tier_selection_manager import TierSelectionManager, MutationTier
from src.mutation.exit_parameter_mutator import ExitParameterMutator
from src.mutation.exit_mutation_logger import ExitMutationLogger
from src.factor_graph.strategy import Strategy

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class MutationResult:
    """
    Result of a mutation operation.

    Attributes:
        success: Whether mutation succeeded
        strategy: Mutated strategy (None if failed)
        tier_used: Tier that was used (1, 2, or 3)
        mutation_type: Type of mutation applied
        error: Error message if failed
        fallback_chain: List of tiers attempted before success
        metadata: Additional metadata about mutation
    """
    success: bool
    strategy: Optional[Strategy]
    tier_used: int
    mutation_type: str
    error: Optional[str] = None
    fallback_chain: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class UnifiedMutationOperator:
    """
    Unified interface for all three mutation tiers.

    Orchestrates mutation operations across three tiers with:
    - Adaptive tier selection based on risk assessment
    - Automatic fallback between tiers on failure
    - Comprehensive mutation tracking and statistics
    - Validation of mutated strategies

    The operator provides a single entry point for mutations,
    abstracting away the complexity of tier selection and fallback logic.

    Example:
        >>> # Initialize with all tier components
        >>> operator = UnifiedMutationOperator(
        ...     yaml_interpreter=YAMLInterpreter(),
        ...     tier2_engine=SmartMutationEngine(...),
        ...     tier3_mutator=ASTFactorMutator(),
        ...     tier_selector=TierSelectionManager()
        ... )
        >>>
        >>> # Apply mutation with adaptive tier selection
        >>> result = operator.mutate_strategy(
        ...     strategy=my_strategy,
        ...     market_data=recent_data,
        ...     mutation_config={"intent": "add_factor"}
        ... )
        >>>
        >>> if result.success:
        ...     print(f"Mutation succeeded using Tier {result.tier_used}")
        ...     print(f"Type: {result.mutation_type}")
        ...     new_strategy = result.strategy
        ... else:
        ...     print(f"Mutation failed: {result.error}")
        ...     print(f"Attempted tiers: {result.fallback_chain}")
    """

    def __init__(
        self,
        yaml_interpreter: YAMLInterpreter,
        tier2_engine: SmartMutationEngine,
        tier3_mutator: ASTFactorMutator,
        tier_selector: TierSelectionManager,
        exit_mutator: Optional[ExitParameterMutator] = None,
        exit_mutation_logger: Optional[ExitMutationLogger] = None,
        metrics_collector: Optional[Any] = None,
        enable_fallback: bool = True,
        validate_mutations: bool = True,
        exit_mutation_probability: float = 0.20
    ):
        """
        Initialize unified mutation operator.

        Args:
            yaml_interpreter: Tier 1 YAML interpreter
            tier2_engine: Tier 2 smart mutation engine
            tier3_mutator: Tier 3 AST factor mutator
            tier_selector: Tier selection manager for adaptive routing
            exit_mutator: Exit parameter mutator (created if None)
            exit_mutation_logger: Exit mutation JSON logger (created if None)
            metrics_collector: Optional MetricsCollector for Prometheus integration
            enable_fallback: Enable automatic fallback between tiers
            validate_mutations: Validate mutated strategies before returning
            exit_mutation_probability: Probability of exit mutation (default 0.20 = 20%)
        """
        self.yaml_interpreter = yaml_interpreter
        self.tier2_engine = tier2_engine
        self.tier3_mutator = tier3_mutator
        self.tier_selector = tier_selector
        self.enable_fallback = enable_fallback
        self.validate_mutations = validate_mutations
        self.metrics_collector = metrics_collector

        # Initialize exit mutator
        self.exit_mutator = exit_mutator if exit_mutator is not None else ExitParameterMutator()
        self.exit_mutation_probability = exit_mutation_probability

        # Initialize exit mutation logger
        self.exit_mutation_logger = exit_mutation_logger if exit_mutation_logger is not None else ExitMutationLogger(
            metrics_collector=metrics_collector
        )

        # Mutation type probabilities (must sum to 1.0)
        # Adjust tier probabilities to make room for exit mutations
        tier_probability = 1.0 - exit_mutation_probability
        self.mutation_type_probabilities = {
            'tier2_factor_mutation': tier_probability * 0.40,  # 40% of tier mutations
            'tier2_add_mutation': tier_probability * 0.20,      # 20% of tier mutations
            'tier3_structural_mutation': tier_probability * 0.40, # 40% of tier mutations
            'exit_parameter_mutation': exit_mutation_probability  # 20% exit mutations
        }

        logger.info(
            f"Initialized UnifiedMutationOperator with exit mutation probability: "
            f"{exit_mutation_probability:.1%}"
        )

        # Track mutation statistics
        self._mutation_history: list[MutationResult] = []
        self._tier_attempts: Dict[int, int] = {1: 0, 2: 0, 3: 0}
        self._tier_successes: Dict[int, int] = {1: 0, 2: 0, 3: 0}
        self._tier_failures: Dict[int, int] = {1: 0, 2: 0, 3: 0}

        # Track exit mutation statistics
        self._exit_mutation_attempts: int = 0
        self._exit_mutation_successes: int = 0
        self._exit_mutation_failures: int = 0

    def mutate_strategy(
        self,
        strategy: Strategy,
        market_data: Optional[pd.DataFrame] = None,
        mutation_config: Optional[Dict[str, Any]] = None
    ) -> MutationResult:
        """
        Apply mutation using adaptive tier selection or exit mutation.

        Workflow:
        1. Determine mutation type (exit vs tier-based)
        2. If exit mutation: Apply exit parameter mutation
        3. If tier mutation: Select tier and apply tier-based mutation
        4. Validate mutated strategy (if enabled)
        5. Record mutation result for learning
        6. If failed and fallback enabled, try next tier/type
        7. Return mutation result

        Args:
            strategy: Strategy to mutate
            market_data: Optional market data for risk assessment
            mutation_config: Optional configuration dict with:
                - intent: Mutation intent (e.g., "add_factor", "adjust_parameters", "exit_mutation")
                - mutation_type: Force specific mutation type (overrides probability selection)
                - override_tier: Manual tier override (1, 2, or 3)
                - tier1_config: Tier 1-specific config
                - tier2_config: Tier 2-specific config
                - tier3_config: Tier 3-specific config
                - exit_config: Exit mutation-specific config
                - Additional parameters

        Returns:
            MutationResult with success status, mutated strategy, and metadata

        Example:
            >>> config = {
            ...     "intent": "add_factor",
            ...     "tier2_config": {"operator": "add_factor"}
            ... }
            >>> result = operator.mutate_strategy(strategy, data, config)
            >>> if result.success:
            ...     print(f"Added factor using Tier {result.tier_used}")
            >>>
            >>> # Force exit mutation
            >>> config = {"mutation_type": "exit_parameter_mutation"}
            >>> result = operator.mutate_strategy(strategy, data, config)
            >>> if result.success:
            ...     print(f"Exit mutation: {result.metadata}")
        """
        if mutation_config is None:
            mutation_config = {}

        # Extract config parameters
        intent = mutation_config.get("intent", "generic")
        override_tier = mutation_config.get("override_tier", None)
        force_mutation_type = mutation_config.get("mutation_type", None)

        # Determine mutation type (exit vs tier-based)
        if force_mutation_type == "exit_parameter_mutation" or \
           (force_mutation_type is None and random.random() < self.exit_mutation_probability):
            # Apply exit parameter mutation
            result = self._apply_exit_mutation(strategy, mutation_config)

            # Record mutation result
            self._mutation_history.append(result)

            return result

        # Otherwise, use tier-based mutation (existing logic)
        # Select tier using adaptive tier selection
        mutation_plan = self.tier_selector.select_mutation_tier(
            strategy=strategy,
            market_data=market_data,
            mutation_intent=intent,
            override_tier=override_tier,
            config=mutation_config
        )

        selected_tier = mutation_plan.tier.value
        fallback_chain = [selected_tier]

        # Attempt mutation with selected tier
        result = self._apply_mutation_with_tier(
            strategy=strategy,
            tier=selected_tier,
            mutation_plan=mutation_plan,
            mutation_config=mutation_config
        )

        # If failed and fallback enabled, try other tiers
        if not result.success and self.enable_fallback:
            result = self._apply_fallback(
                strategy=strategy,
                initial_tier=selected_tier,
                mutation_plan=mutation_plan,
                mutation_config=mutation_config,
                fallback_chain=fallback_chain
            )

        # Update fallback chain
        result.fallback_chain = fallback_chain

        # Record mutation result for learning
        self._record_mutation(result, mutation_plan)

        # Add to history
        self._mutation_history.append(result)

        return result

    def _apply_mutation_with_tier(
        self,
        strategy: Strategy,
        tier: int,
        mutation_plan: Any,
        mutation_config: Dict[str, Any]
    ) -> MutationResult:
        """
        Apply mutation using specified tier.

        Args:
            strategy: Strategy to mutate
            tier: Tier to use (1, 2, or 3)
            mutation_plan: Mutation plan from tier selector
            mutation_config: Mutation configuration

        Returns:
            MutationResult with success status and mutated strategy
        """
        self._tier_attempts[tier] += 1

        try:
            if tier == 1:
                mutated_strategy, mutation_type = self._apply_tier1_mutation(
                    strategy, mutation_config
                )
            elif tier == 2:
                mutated_strategy, mutation_type = self._apply_tier2_mutation(
                    strategy, mutation_config
                )
            elif tier == 3:
                mutated_strategy, mutation_type = self._apply_tier3_mutation(
                    strategy, mutation_config
                )
            else:
                raise ValueError(f"Invalid tier: {tier}")

            # Validate if enabled
            if self.validate_mutations:
                try:
                    mutated_strategy.validate()
                except Exception as e:
                    self._tier_failures[tier] += 1
                    return MutationResult(
                        success=False,
                        strategy=None,
                        tier_used=tier,
                        mutation_type=mutation_type,
                        error=f"Validation failed: {str(e)}"
                    )

            # Success
            self._tier_successes[tier] += 1
            return MutationResult(
                success=True,
                strategy=mutated_strategy,
                tier_used=tier,
                mutation_type=mutation_type
            )

        except Exception as e:
            self._tier_failures[tier] += 1
            return MutationResult(
                success=False,
                strategy=None,
                tier_used=tier,
                mutation_type="unknown",
                error=str(e)
            )

    def _apply_tier1_mutation(
        self,
        strategy: Strategy,
        config: Dict[str, Any]
    ) -> tuple[Strategy, str]:
        """
        Apply Tier 1 (YAML) mutation.

        This is a simplified implementation. In production, you would:
        1. Export strategy to YAML
        2. Modify YAML configuration
        3. Re-interpret YAML to create new strategy

        For now, we'll use tier 2 as fallback internally.
        """
        # Tier 1 mutation via YAML modification
        # This is a placeholder - full implementation would export to YAML,
        # modify it, and re-import
        raise NotImplementedError(
            "Tier 1 YAML mutation requires strategy export/import pipeline"
        )

    def _apply_tier2_mutation(
        self,
        strategy: Strategy,
        config: Dict[str, Any]
    ) -> tuple[Strategy, str]:
        """
        Apply Tier 2 (Factor-level) mutation.

        Args:
            strategy: Strategy to mutate
            config: Mutation configuration

        Returns:
            (mutated_strategy, mutation_type)
        """
        # Get tier2-specific config
        tier2_config = config.get("tier2_config", {})

        # Create context for operator selection
        context = {
            "generation": config.get("generation", 0),
            "diversity": config.get("diversity", 0.5),
            "strategy": strategy
        }

        # Select operator
        operator_name, operator = self.tier2_engine.select_operator(context)

        # Apply mutation
        mutated_strategy = operator.mutate(strategy, tier2_config)

        return mutated_strategy, operator_name

    def _apply_tier3_mutation(
        self,
        strategy: Strategy,
        config: Dict[str, Any]
    ) -> tuple[Strategy, str]:
        """
        Apply Tier 3 (AST) mutation.

        Args:
            strategy: Strategy to mutate
            config: Mutation configuration

        Returns:
            (mutated_strategy, mutation_type)
        """
        # Get tier3-specific config
        tier3_config = config.get("tier3_config", {})

        # Clone strategy
        mutated_strategy = strategy.copy()

        # Select random factor to mutate
        factors = mutated_strategy.get_factors()
        if not factors:
            raise ValueError("Strategy has no factors to mutate")

        factor_to_mutate = random.choice(factors)

        # Determine mutation type
        mutation_types = ["operator_mutation", "threshold_adjustment", "expression_modification"]
        mutation_type = tier3_config.get(
            "mutation_type",
            random.choice(mutation_types)
        )

        # Apply AST mutation
        mutation_config = {
            "mutation_type": mutation_type,
            "validate": True
        }
        mutation_config.update(tier3_config)

        mutated_factor = self.tier3_mutator.mutate(factor_to_mutate, mutation_config)

        # Replace factor in strategy
        mutated_strategy.remove_factor(factor_to_mutate.id)
        mutated_strategy.add_factor(mutated_factor, depends_on=[])

        return mutated_strategy, f"ast_{mutation_type}"

    def _apply_exit_mutation(
        self,
        strategy: Strategy,
        config: Dict[str, Any]
    ) -> MutationResult:
        """
        Apply exit parameter mutation to strategy code.

        This method applies parameter-based mutation to exit strategy parameters
        (stop_loss_pct, take_profit_pct, trailing_stop_offset, holding_period_days)
        using the ExitParameterMutator.

        Args:
            strategy: Strategy to mutate
            config: Mutation configuration with optional:
                - exit_config: Dict with exit mutation settings
                - parameter_name: Specific parameter to mutate (optional)

        Returns:
            MutationResult with success status, mutated strategy, and metadata

        Example:
            >>> config = {
            ...     "exit_config": {"parameter_name": "stop_loss_pct"}
            ... }
            >>> result = operator._apply_exit_mutation(strategy, config)
            >>> if result.success:
            ...     print(f"Mutated {result.metadata['parameter_name']}")
        """
        import time

        self._exit_mutation_attempts += 1
        start_time = time.time()

        try:
            # Get exit-specific config
            exit_config = config.get("exit_config", {})
            parameter_name = exit_config.get("parameter_name", None)

            # Get strategy source code
            # Note: This assumes strategy has a method to export to code
            # For now, we'll work with the strategy's code representation
            if hasattr(strategy, 'to_code'):
                strategy_code = strategy.to_code()
            elif hasattr(strategy, 'code'):
                strategy_code = strategy.code
            else:
                # Fallback: convert strategy to string representation
                strategy_code = str(strategy)

            # Apply exit parameter mutation
            mutation_result = self.exit_mutator.mutate_exit_parameters(
                code=strategy_code,
                parameter_name=parameter_name
            )

            if not mutation_result.success:
                # Mutation failed
                self._exit_mutation_failures += 1
                duration = time.time() - start_time

                logger.warning(
                    f"Exit mutation failed: {mutation_result.metadata.error if mutation_result.metadata else 'Unknown error'}"
                )

                # Log failure to JSON with duration
                if mutation_result.metadata:
                    self.exit_mutation_logger.log_mutation(
                        parameter=mutation_result.metadata.parameter_name,
                        old_value=mutation_result.metadata.old_value,
                        new_value=mutation_result.metadata.new_value,
                        clamped=mutation_result.metadata.clamped,
                        success=False,
                        validation_passed=mutation_result.validation_passed,
                        error=mutation_result.metadata.error,
                        duration=duration
                    )

                return MutationResult(
                    success=False,
                    strategy=None,
                    tier_used=0,  # 0 indicates exit mutation (not tier-based)
                    mutation_type="exit_parameter_mutation",
                    error=mutation_result.metadata.error if mutation_result.metadata else "Unknown error",
                    metadata={
                        'exit_mutation': True,
                        'parameter_name': parameter_name,
                        'validation_passed': mutation_result.validation_passed,
                        'duration_seconds': duration
                    }
                )

            # Mutation succeeded - create new strategy with mutated code
            mutated_strategy = strategy.copy()

            # Update strategy code with mutated version
            if hasattr(mutated_strategy, 'update_code'):
                mutated_strategy.update_code(mutation_result.code)
            elif hasattr(mutated_strategy, 'code'):
                mutated_strategy.code = mutation_result.code
            else:
                # If strategy doesn't support code updates, log warning
                logger.warning(
                    "Strategy does not support code updates. "
                    "Exit mutation applied but may not be reflected in strategy object."
                )

            # Validate mutated strategy if enabled
            if self.validate_mutations:
                try:
                    mutated_strategy.validate()
                except Exception as e:
                    self._exit_mutation_failures += 1
                    duration = time.time() - start_time

                    logger.error(f"Exit mutation validation failed: {str(e)}")

                    # Log validation failure to JSON with duration
                    self.exit_mutation_logger.log_mutation(
                        parameter=mutation_result.metadata.parameter_name,
                        old_value=mutation_result.metadata.old_value,
                        new_value=mutation_result.metadata.new_value,
                        clamped=mutation_result.metadata.clamped,
                        success=False,
                        validation_passed=False,
                        error=f"Validation failed: {str(e)}",
                        duration=duration
                    )

                    return MutationResult(
                        success=False,
                        strategy=None,
                        tier_used=0,
                        mutation_type="exit_parameter_mutation",
                        error=f"Validation failed: {str(e)}",
                        metadata={
                            'exit_mutation': True,
                            'parameter_name': mutation_result.metadata.parameter_name,
                            'old_value': mutation_result.metadata.old_value,
                            'new_value': mutation_result.metadata.new_value,
                            'clamped': mutation_result.metadata.clamped,
                            'duration_seconds': duration
                        }
                    )

            # Success!
            self._exit_mutation_successes += 1
            duration = time.time() - start_time

            logger.info(
                f"Exit mutation success: {mutation_result.metadata.parameter_name} "
                f"{mutation_result.metadata.old_value:.4f} -> {mutation_result.metadata.new_value:.4f} "
                f"(duration: {duration*1000:.2f}ms)"
            )

            # Log success to JSON with duration
            self.exit_mutation_logger.log_mutation(
                parameter=mutation_result.metadata.parameter_name,
                old_value=mutation_result.metadata.old_value,
                new_value=mutation_result.metadata.new_value,
                clamped=mutation_result.metadata.clamped,
                success=True,
                validation_passed=mutation_result.validation_passed,
                error=None,
                duration=duration
            )

            return MutationResult(
                success=True,
                strategy=mutated_strategy,
                tier_used=0,  # 0 indicates exit mutation
                mutation_type="exit_parameter_mutation",
                metadata={
                    'exit_mutation': True,
                    'parameter_name': mutation_result.metadata.parameter_name,
                    'old_value': mutation_result.metadata.old_value,
                    'new_value': mutation_result.metadata.new_value,
                    'clamped': mutation_result.metadata.clamped,
                    'validation_passed': mutation_result.validation_passed,
                    'duration_seconds': duration
                }
            )

        except Exception as e:
            self._exit_mutation_failures += 1
            duration = time.time() - start_time
            logger.error(f"Exit mutation error: {str(e)}", exc_info=True)

            # Log exception to JSON (with placeholder values and duration)
            self.exit_mutation_logger.log_mutation(
                parameter=parameter_name or "unknown",
                old_value=0.0,
                new_value=0.0,
                clamped=False,
                success=False,
                validation_passed=False,
                error=str(e),
                duration=duration
            )

            return MutationResult(
                success=False,
                strategy=None,
                tier_used=0,
                mutation_type="exit_parameter_mutation",
                error=str(e),
                metadata={
                    'exit_mutation': True,
                    'duration_seconds': duration
                }
            )

    def _apply_fallback(
        self,
        strategy: Strategy,
        initial_tier: int,
        mutation_plan: Any,
        mutation_config: Dict[str, Any],
        fallback_chain: list
    ) -> MutationResult:
        """
        Apply fallback mutation if initial tier failed.

        Fallback order: Tier 3 → Tier 2 → Tier 1

        Args:
            strategy: Strategy to mutate
            initial_tier: Initial tier that failed
            mutation_plan: Original mutation plan
            mutation_config: Mutation configuration
            fallback_chain: List to track attempted tiers

        Returns:
            MutationResult from fallback attempt
        """
        # Define fallback order
        fallback_order = {
            3: [2, 1],  # Tier 3 falls back to 2, then 1
            2: [1],     # Tier 2 falls back to 1
            1: []       # Tier 1 has no fallback
        }

        fallback_tiers = fallback_order.get(initial_tier, [])

        for tier in fallback_tiers:
            fallback_chain.append(tier)
            result = self._apply_mutation_with_tier(
                strategy=strategy,
                tier=tier,
                mutation_plan=mutation_plan,
                mutation_config=mutation_config
            )

            if result.success:
                return result

        # All fallbacks failed
        return MutationResult(
            success=False,
            strategy=None,
            tier_used=initial_tier,
            mutation_type="unknown",
            error=f"All fallback tiers failed. Attempted: {fallback_chain}"
        )

    def _record_mutation(
        self,
        result: MutationResult,
        mutation_plan: Any
    ) -> None:
        """
        Record mutation result for adaptive learning.

        Args:
            result: Mutation result
            mutation_plan: Original mutation plan
        """
        # Update tier selector with result
        metrics = {
            "success": result.success,
            "mutation_type": result.mutation_type,
            "tier_used": result.tier_used,
            "fallback_chain": result.fallback_chain
        }

        self.tier_selector.record_mutation_result(
            plan=mutation_plan,
            success=result.success,
            metrics=metrics
        )

    def get_tier_statistics(self) -> Dict[str, Any]:
        """
        Get tier usage and performance statistics, including exit mutations.

        Returns:
            Dictionary with:
                - tier_attempts: Attempts per tier
                - tier_successes: Successes per tier
                - tier_failures: Failures per tier
                - tier_success_rates: Success rates per tier
                - exit_mutation_attempts: Exit mutation attempts
                - exit_mutation_successes: Exit mutation successes
                - exit_mutation_failures: Exit mutation failures
                - exit_mutation_success_rate: Exit mutation success rate
                - total_mutations: Total mutations attempted (tiers + exit)
                - total_successes: Total successful mutations (tiers + exit)
                - success_rate: Overall success rate
        """
        total_tier_attempts = sum(self._tier_attempts.values())
        total_tier_successes = sum(self._tier_successes.values())

        # Include exit mutations in totals
        total_attempts = total_tier_attempts + self._exit_mutation_attempts
        total_successes = total_tier_successes + self._exit_mutation_successes

        tier_success_rates = {}
        for tier in [1, 2, 3]:
            attempts = self._tier_attempts[tier]
            if attempts > 0:
                tier_success_rates[tier] = self._tier_successes[tier] / attempts
            else:
                tier_success_rates[tier] = 0.0

        # Calculate exit mutation success rate
        exit_mutation_success_rate = 0.0
        if self._exit_mutation_attempts > 0:
            exit_mutation_success_rate = self._exit_mutation_successes / self._exit_mutation_attempts

        return {
            "tier_attempts": dict(self._tier_attempts),
            "tier_successes": dict(self._tier_successes),
            "tier_failures": dict(self._tier_failures),
            "tier_success_rates": tier_success_rates,
            "exit_mutation_attempts": self._exit_mutation_attempts,
            "exit_mutation_successes": self._exit_mutation_successes,
            "exit_mutation_failures": self._exit_mutation_failures,
            "exit_mutation_success_rate": exit_mutation_success_rate,
            "total_mutations": total_attempts,
            "total_successes": total_successes,
            "success_rate": total_successes / total_attempts if total_attempts > 0 else 0.0,
            "history_count": len(self._mutation_history)
        }

    def export_tier_analysis(self, path: str) -> None:
        """
        Export detailed tier analysis to JSON file.

        Args:
            path: Path to export file
        """
        import json

        analysis = {
            "statistics": self.get_tier_statistics(),
            "tier_selector_state": self.tier_selector.export_state(),
            "mutation_history": [
                {
                    "success": r.success,
                    "tier_used": r.tier_used,
                    "mutation_type": r.mutation_type,
                    "error": r.error,
                    "fallback_chain": r.fallback_chain,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self._mutation_history
            ]
        }

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)

    def reset_statistics(self) -> None:
        """Reset all mutation statistics, including exit mutations."""
        self._mutation_history = []
        self._tier_attempts = {1: 0, 2: 0, 3: 0}
        self._tier_successes = {1: 0, 2: 0, 3: 0}
        self._tier_failures = {1: 0, 2: 0, 3: 0}
        self._exit_mutation_attempts = 0
        self._exit_mutation_successes = 0
        self._exit_mutation_failures = 0
        self.tier_selector.reset_learning()
