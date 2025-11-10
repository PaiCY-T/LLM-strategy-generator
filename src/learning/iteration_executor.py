"""Iteration Executor for Phase 5.

Executes a single iteration of the autonomous learning loop with 10-step process:
1. Load recent history
2. Generate feedback
3. Decide LLM or Factor Graph (based on innovation_rate)
4. Generate strategy (call LLM or Factor Graph)
5. Execute strategy (Phase 2 BacktestExecutor)
6. Extract metrics (Phase 2 MetricsExtractor)
7. Classify success (Phase 2 ErrorClassifier)
8. Update champion if better
9. Create IterationRecord
10. Return record

This refactored from autonomous_loop.py (~800 lines extracted).
"""

import logging
import random
from dataclasses import asdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.backtest.executor import BacktestExecutor, ExecutionResult
from src.backtest.metrics import MetricsExtractor, StrategyMetrics
from src.backtest.error_classifier import ErrorClassifier
from src.learning.champion_tracker import ChampionTracker
from src.learning.feedback_generator import FeedbackGenerator
from src.learning.iteration_history import IterationHistory, IterationRecord
from src.learning.llm_client import LLMClient

logger = logging.getLogger(__name__)


class IterationExecutor:
    """Executes single iteration with 10-step learning process.

    Integrates all Phase 2-4 components to run a complete iteration:
    - LLM-based or Factor Graph-based strategy generation
    - Sandboxed execution with timeout protection
    - Metrics extraction and success classification
    - Champion tracking and pattern learning

    Attributes:
        llm_client: LLM client for strategy generation
        feedback_generator: Generates feedback from history
        backtest_executor: Executes strategies with timeout
        champion_tracker: Tracks best-performing strategy
        history: Iteration history for loading recent iterations
        metrics_extractor: Extracts performance metrics
        error_classifier: Classifies execution results into levels
        config: Configuration dictionary
    """

    def __init__(
        self,
        llm_client: LLMClient,
        feedback_generator: FeedbackGenerator,
        backtest_executor: BacktestExecutor,
        champion_tracker: ChampionTracker,
        history: IterationHistory,
        config: Dict[str, Any],
        data: Any = None,
        sim: Any = None,
    ):
        """Initialize iteration executor with all required components.

        Args:
            llm_client: LLM client for strategy generation
            feedback_generator: Feedback generator from history
            backtest_executor: Backtest executor with timeout
            champion_tracker: Champion tracker for best strategy
            history: Iteration history
            config: Configuration dict with keys:
                - innovation_rate: 0-100, percentage of LLM vs Factor Graph
                - history_window: Number of recent iterations for feedback
                - timeout_seconds: Backtest timeout in seconds
                - start_date: Backtest start date
                - end_date: Backtest end date
                - fee_ratio: Transaction fee ratio
                - tax_ratio: Transaction tax ratio
                - resample: Rebalancing frequency (M/W/D)
            data: finlab data object (optional for Factor Graph)
            sim: finlab sim function (optional for Factor Graph)

        Raises:
            ValueError: If LLM is enabled but data/sim not provided
        """
        self.llm_client = llm_client
        self.feedback_generator = feedback_generator
        self.backtest_executor = backtest_executor
        self.champion_tracker = champion_tracker
        self.history = history
        self.config = config
        self.data = data
        self.sim = sim

        # Initialize Phase 2 components
        self.metrics_extractor = MetricsExtractor()
        self.error_classifier = ErrorClassifier()

        # Finlab initialization flag (lazy loading)
        self._finlab_initialized = False

        # === Factor Graph Support ===
        # Strategy DAG registry (maps strategy_id -> Strategy object)
        # Stores strategies created during iterations for execution
        self._strategy_registry: Dict[str, Any] = {}

        # Factor logic registry (maps factor_id -> logic Callable)
        # Used for Strategy serialization/deserialization (future feature)
        self._factor_logic_registry: Dict[str, Callable] = {}

        # ISSUE #4 FIX: Early validation - check data/sim if LLM is enabled
        if self.llm_client.is_enabled():
            if not self.data or not self.sim:
                raise ValueError(
                    "data and sim are required when LLM client is enabled. "
                    "Provide them to IterationExecutor.__init__(data=..., sim=...)"
                )

        logger.info("IterationExecutor initialized")

    def _initialize_finlab(self) -> bool:
        """Initialize finlab data and sim objects (lazy loading).

        Returns:
            True if initialization successful, False otherwise
        """
        if self._finlab_initialized:
            return True

        try:
            from finlab import data
            from finlab.backtest import sim

            self.data = data
            self.sim = sim
            self._finlab_initialized = True
            logger.info("✓ Finlab data and sim initialized")
            return True

        except ImportError as e:
            logger.error(f"Failed to import finlab: {e}")
            logger.error("Please ensure finlab is installed and authenticated")
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing finlab: {e}")
            return False

    def execute_iteration(
        self,
        iteration_num: int,
    ) -> IterationRecord:
        """Execute single iteration with 10-step process.

        10-Step Process:
        1. Load recent history (last N iterations)
        2. Generate feedback from history
        3. Decide LLM or Factor Graph (innovation_rate %)
        4. Generate strategy (LLM or Factor Graph)
        5. Execute strategy (BacktestExecutor)
        6. Extract metrics (MetricsExtractor)
        7. Classify success (ErrorClassifier: LEVEL_0-3)
        8. Update champion if better (ChampionTracker)
        9. Create IterationRecord
        10. Return record

        Args:
            iteration_num: Current iteration number (0-indexed, must be >= 0)

        Returns:
            IterationRecord with execution results

        Raises:
            ValueError: If iteration_num is negative

        Example:
            >>> executor = IterationExecutor(...)
            >>> record = executor.execute_iteration(iteration_num=5)
            >>> print(record.classification_level)  # "LEVEL_3"
            >>> print(record.metrics["sharpe_ratio"])  # 1.85
        """
        # Validate input
        if iteration_num < 0:
            raise ValueError(f"iteration_num must be >= 0, got {iteration_num}")

        start_time = datetime.now()
        logger.info(f"=== Starting iteration {iteration_num} ===")

        # Step 0: Initialize finlab (lazy loading)
        if not self._initialize_finlab():
            logger.error("Failed to initialize finlab - cannot execute iteration")
            return self._create_failure_record(
                iteration_num, "unknown", "Finlab initialization failed", start_time
            )

        # Step 1: Load recent history
        history_window = self.config.get("history_window", 5)
        recent_records = self._load_recent_history(history_window)
        logger.debug(f"Loaded {len(recent_records)} recent iterations")

        # Step 2: Generate feedback
        feedback = self._generate_feedback(recent_records, iteration_num)
        logger.debug(f"Generated feedback: {len(feedback)} chars")

        # Step 3: Decide LLM or Factor Graph
        use_llm = self._decide_generation_method()
        generation_method = "llm" if use_llm else "factor_graph"
        logger.info(f"Generation method: {generation_method}")

        # Step 4: Generate strategy
        if use_llm:
            strategy_code, strategy_id, strategy_generation = self._generate_with_llm(
                feedback, iteration_num
            )
            # If LLM fallback to Factor Graph, update generation_method
            if strategy_code is None and strategy_id is not None:
                generation_method = "factor_graph"
                logger.info("LLM fallback to Factor Graph detected, updated generation_method")
        else:
            strategy_code, strategy_id, strategy_generation = self._generate_with_factor_graph(
                iteration_num
            )

        if not strategy_code and not strategy_id:
            # Generation failed
            logger.error("Strategy generation failed")
            return self._create_failure_record(
                iteration_num, generation_method, "Generation failed", start_time
            )

        # Step 5: Execute strategy
        execution_result = self._execute_strategy(
            strategy_code, strategy_id, strategy_generation, generation_method
        )

        # Step 6: Extract metrics
        metrics = self._extract_metrics(execution_result)

        # Step 7: Classify success
        classification_level = self._classify_result(execution_result, metrics)
        logger.info(f"Classification: {classification_level}")

        # Step 8: Update champion if better
        champion_updated = self._update_champion_if_better(
            iteration_num, generation_method, strategy_code,
            strategy_id, strategy_generation, metrics, classification_level
        )

        # Step 9: Create IterationRecord
        record = IterationRecord(
            iteration_num=iteration_num,
            generation_method=generation_method,
            strategy_code=strategy_code if generation_method == "llm" else None,
            strategy_id=strategy_id if generation_method == "factor_graph" else None,
            strategy_generation=strategy_generation if generation_method == "factor_graph" else None,
            execution_result=execution_result.__dict__ if hasattr(execution_result, "__dict__") else execution_result,
            metrics=metrics,
            classification_level=classification_level,
            timestamp=datetime.now().isoformat(),
            champion_updated=champion_updated,
            feedback_used=feedback[:500] if feedback else None,  # Store first 500 chars
        )

        # Periodic cleanup of strategy registry (prevent memory bloat)
        if iteration_num > 0 and iteration_num % 100 == 0:
            self._cleanup_old_strategies(keep_last_n=100)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"=== Iteration {iteration_num} complete in {elapsed:.1f}s ===")

        # Step 10: Return record
        return record

    def _load_recent_history(self, window: int) -> list:
        """Load recent N iterations from history.

        Args:
            window: Number of recent iterations to load

        Returns:
            List of recent IterationRecords (newest first)
        """
        try:
            all_records = self.history.get_all()
            if not all_records:
                return []

            # Get last N records
            recent = all_records[-window:] if len(all_records) > window else all_records
            return recent
        except Exception as e:
            logger.warning(f"Failed to load history: {e}")
            return []

    def _generate_feedback(self, recent_records: list, iteration_num: int) -> str:
        """Generate feedback from recent history.

        Args:
            recent_records: Recent iteration records
            iteration_num: Current iteration number

        Returns:
            Feedback string for LLM
        """
        try:
            # For first iteration or no history, return default feedback
            if not recent_records:
                return "First iteration - no previous history. Generate a basic momentum strategy."

            # Get last record for context
            last_record = recent_records[-1]

            # Generate feedback based on last iteration's results
            feedback = self.feedback_generator.generate_feedback(
                iteration_num=iteration_num,
                metrics=last_record.metrics if hasattr(last_record, 'metrics') else None,
                execution_result={'status': 'success' if hasattr(last_record, 'classification_level') else 'error'},
                classification_level=last_record.classification_level if hasattr(last_record, 'classification_level') else None,
                error_msg=None
            )
            return feedback
        except Exception as e:
            logger.warning(f"Feedback generation failed: {e}")
            return "No feedback available (first iteration or error)."

    def _decide_generation_method(self) -> bool:
        """Decide whether to use LLM or Factor Graph.

        Uses innovation_rate from config (0-100):
        - 100 = always LLM
        - 0 = always Factor Graph
        - 50 = 50% chance each

        Returns:
            True for LLM, False for Factor Graph
        """
        innovation_rate = self.config.get("innovation_rate", 100)

        # Random decision based on innovation_rate
        use_llm = random.random() * 100 < innovation_rate

        return use_llm

    def _generate_with_llm(
        self, feedback: str, iteration_num: int
    ) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Generate strategy using LLM.

        Args:
            feedback: Feedback string for LLM
            iteration_num: Current iteration number

        Returns:
            (strategy_code, None, None) for LLM generation
        """
        try:
            # Check if LLM is enabled
            if not self.llm_client.is_enabled():
                logger.warning("LLM client not enabled, falling back to Factor Graph")
                return self._generate_with_factor_graph(iteration_num)

            # Get LLM engine
            engine = self.llm_client.get_engine()
            if not engine:
                logger.warning("LLM engine not available")
                return self._generate_with_factor_graph(iteration_num)

            # Get champion information for InnovationEngine
            champion = self.champion_tracker.get_champion()

            # Extract champion_code and champion_metrics
            if champion:
                # For LLM champions, use code directly
                if champion.generation_method == "llm":
                    champion_code = champion.code or ""
                    champion_metrics = champion.metrics
                # For Factor Graph champions, we don't have code
                # Use empty string and let InnovationEngine handle it
                else:
                    champion_code = ""
                    champion_metrics = champion.metrics
            else:
                # No champion yet, use defaults
                champion_code = ""
                champion_metrics = {"sharpe_ratio": 0.0}

            # Generate strategy using InnovationEngine API
            logger.info("Calling LLM for strategy generation...")
            strategy_code = engine.generate_innovation(
                champion_code=champion_code,
                champion_metrics=champion_metrics,
                failure_history=None,  # TODO: Extract from history in future iteration
                target_metric="sharpe_ratio"
            )

            if not strategy_code:
                logger.warning("LLM returned empty code")
                return self._generate_with_factor_graph(iteration_num)

            logger.info(f"LLM generated {len(strategy_code)} chars of code")

            return (strategy_code, None, None)

        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            # Fallback to Factor Graph
            return self._generate_with_factor_graph(iteration_num)

    def _generate_with_factor_graph(
        self, iteration_num: int
    ) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        """Generate strategy using Factor Graph mutation.

        Implementation:
        1. Check if Factor Graph champion exists
        2. If exists: Mutate champion using add_factor()
        3. If not: Create template strategy (momentum + breakout + exit)
        4. Register strategy to internal registry
        5. Return (None, strategy_id, strategy_generation)

        Args:
            iteration_num: Current iteration number

        Returns:
            (None, strategy_id, strategy_generation) for Factor Graph
            - code: Always None (Factor Graph doesn't use code strings)
            - strategy_id: Unique ID for Strategy DAG object
            - strategy_generation: Generation number (0 for templates, N+1 for mutated)
        """
        from src.factor_graph.strategy import Strategy
        from src.factor_graph.mutations import add_factor
        from src.factor_library.registry import FactorRegistry
        from src.factor_graph.factor_category import FactorCategory

        registry = FactorRegistry.get_instance()

        # Check if we have a Factor Graph champion
        champion = self.champion_tracker.get_champion()

        if champion and champion.generation_method == "factor_graph":
            # Mutate existing champion
            logger.info(f"Mutating Factor Graph champion: {champion.strategy_id}")

            # Get champion strategy from registry
            parent_strategy = self._strategy_registry.get(champion.strategy_id)

            if parent_strategy is None:
                # Champion not in registry (loaded from Hall of Fame or fresh session)
                # Create template and mutate from there
                logger.warning(f"Champion {champion.strategy_id} not in registry, creating template")
                parent_strategy = self._create_template_strategy(iteration_num)

            # Select random factor to add (mutation)
            available_categories = [
                FactorCategory.MOMENTUM,
                FactorCategory.EXIT,
                FactorCategory.ENTRY,
                FactorCategory.RISK
            ]

            # Randomly select category
            category = random.choice(available_categories)
            factors_in_category = registry.list_by_category(category)

            if not factors_in_category:
                # No factors in category, try MOMENTUM as fallback
                factors_in_category = registry.get_momentum_factors()

            # Randomly select factor from category
            factor_name = random.choice(factors_in_category)

            # Get default parameters from registry
            metadata = registry.get_metadata(factor_name)
            parameters = metadata['parameters'].copy() if metadata else {}

            # Mutate strategy (add factor)
            try:
                mutated_strategy = add_factor(
                    strategy=parent_strategy,
                    factor_name=factor_name,
                    parameters=parameters,
                    insert_point="smart"  # Smart insertion based on category
                )

                # Generate new ID and increment generation
                strategy_id = f"fg_{iteration_num}_{champion.strategy_generation + 1}"
                strategy_generation = champion.strategy_generation + 1
                mutated_strategy.id = strategy_id
                mutated_strategy.generation = strategy_generation
                mutated_strategy.parent_ids = [champion.strategy_id]

                logger.info(
                    f"Mutated strategy: added {factor_name} "
                    f"(gen {strategy_generation}, parent: {champion.strategy_id})"
                )

            except Exception as e:
                logger.error(f"Mutation failed: {e}, creating template instead")
                # Fallback: create template
                mutated_strategy = self._create_template_strategy(iteration_num)
                strategy_id = mutated_strategy.id
                strategy_generation = mutated_strategy.generation

        else:
            # No Factor Graph champion, create template strategy
            logger.info("No Factor Graph champion, creating template strategy")
            mutated_strategy = self._create_template_strategy(iteration_num)
            strategy_id = mutated_strategy.id
            strategy_generation = mutated_strategy.generation

        # Register strategy to internal registry
        self._strategy_registry[strategy_id] = mutated_strategy

        # Return None for code (Factor Graph doesn't use code strings)
        return (None, strategy_id, strategy_generation)

    def _create_template_strategy(self, iteration_num: int) -> Any:
        """Create template Factor Graph strategy (momentum + breakout + trailing stop).

        Template Strategy Composition:
        1. Momentum Factor (MOMENTUM): Price momentum using rolling mean
        2. Breakout Factor (ENTRY): N-day high/low breakout detection
        3. Trailing Stop Factor (EXIT): Trailing stop loss for risk management

        This provides a baseline strategy for Factor Graph evolution when no champion exists.

        Args:
            iteration_num: Current iteration number (used for unique ID)

        Returns:
            Strategy: Template strategy with 3 factors
        """
        from src.factor_graph.strategy import Strategy
        from src.factor_library.registry import FactorRegistry

        registry = FactorRegistry.get_instance()

        # Create strategy
        strategy_id = f"template_{iteration_num}"
        strategy = Strategy(id=strategy_id, generation=0)

        # Add momentum factor (root)
        momentum_factor = registry.create_factor(
            "momentum_factor",
            parameters={"momentum_period": 20}
        )
        strategy.add_factor(momentum_factor, depends_on=[])

        # Add breakout factor (entry signal)
        breakout_factor = registry.create_factor(
            "breakout_factor",
            parameters={"entry_window": 20}
        )
        strategy.add_factor(breakout_factor, depends_on=[])

        # Add trailing stop factor (exit)
        trailing_stop_factor = registry.create_factor(
            "trailing_stop_factor",
            parameters={"trail_percent": 0.10, "activation_profit": 0.05}
        )
        strategy.add_factor(
            trailing_stop_factor,
            depends_on=[momentum_factor.id, breakout_factor.id]
        )

        logger.info(f"Created template strategy: {strategy_id} with 3 factors")

        return strategy

    def _cleanup_old_strategies(self, keep_last_n: int = 100) -> None:
        """Clean up old strategies from registry to prevent memory bloat.

        Keeps only the most recent N strategies and the current champion.
        This prevents unbounded memory growth during long runs.

        Args:
            keep_last_n: Number of recent strategies to keep (default: 100)

        Note:
            - Champion strategy is always preserved (never deleted)
            - Strategies are identified by their numeric suffix (iteration number)
            - This is safe to call periodically (e.g., every 100 iterations)
        """
        if len(self._strategy_registry) <= keep_last_n:
            # Registry is small enough, no cleanup needed
            return

        # Get current champion ID (never delete champion)
        champion = self.champion_tracker.get_champion()
        champion_id = champion.strategy_id if (champion and champion.generation_method == "factor_graph") else None

        # Sort strategies by iteration number (extract from ID)
        # ID format: "fg_{iteration}_{generation}" or "template_{iteration}"
        strategy_items = list(self._strategy_registry.items())

        def extract_iteration(strategy_id: str) -> int:
            """Extract iteration number from strategy ID."""
            try:
                if strategy_id.startswith("fg_"):
                    # Format: "fg_123_1" -> extract 123
                    return int(strategy_id.split("_")[1])
                elif strategy_id.startswith("template_"):
                    # Format: "template_123" -> extract 123
                    return int(strategy_id.split("_")[1])
                else:
                    return 0  # Unknown format, keep at beginning
            except (IndexError, ValueError):
                return 0

        # Sort by iteration number (newest last)
        strategy_items.sort(key=lambda item: extract_iteration(item[0]))

        # Keep only last N strategies + champion
        strategies_to_keep = set()

        # Add champion
        if champion_id:
            strategies_to_keep.add(champion_id)

        # Add last N strategies
        for strategy_id, _ in strategy_items[-keep_last_n:]:
            strategies_to_keep.add(strategy_id)

        # Remove old strategies
        strategies_to_remove = [
            sid for sid in self._strategy_registry.keys()
            if sid not in strategies_to_keep
        ]

        for strategy_id in strategies_to_remove:
            del self._strategy_registry[strategy_id]

        if strategies_to_remove:
            logger.debug(
                f"Cleaned up {len(strategies_to_remove)} old strategies, "
                f"kept {len(self._strategy_registry)} (including champion)"
            )

    def _execute_strategy(
        self,
        strategy_code: Optional[str],
        strategy_id: Optional[str],
        strategy_generation: Optional[int],
        generation_method: str,
    ) -> ExecutionResult:
        """Execute strategy using BacktestExecutor.

        Args:
            strategy_code: Strategy code (for LLM)
            strategy_id: Strategy ID (for Factor Graph)
            strategy_generation: Strategy generation (for Factor Graph)
            generation_method: "llm" or "factor_graph"

        Returns:
            ExecutionResult from BacktestExecutor
        """
        try:
            if generation_method == "llm" and strategy_code:
                # Execute code string using BacktestExecutor.execute()
                # Note: BacktestExecutor requires data and sim to be passed in
                result = self.backtest_executor.execute(
                    strategy_code=strategy_code,
                    data=self.data,
                    sim=self.sim,
                    timeout=self.config.get("timeout_seconds", 420),
                    start_date=self.config.get("start_date"),
                    end_date=self.config.get("end_date"),
                    fee_ratio=self.config.get("fee_ratio"),
                    tax_ratio=self.config.get("tax_ratio"),
                )

            elif generation_method == "factor_graph" and strategy_id:
                # Execute Factor Graph Strategy object
                logger.info(f"Executing Factor Graph strategy: {strategy_id}")

                # Get strategy from registry
                strategy = self._strategy_registry.get(strategy_id)

                if strategy is None:
                    # Strategy not found in registry (shouldn't happen)
                    logger.error(f"Strategy {strategy_id} not found in registry")
                    result = ExecutionResult(
                        success=False,
                        error_type="ValueError",
                        error_message=f"Strategy {strategy_id} not found in internal registry",
                        execution_time=0.0,
                    )
                else:
                    # Execute Strategy DAG using BacktestExecutor.execute_strategy()
                    result = self.backtest_executor.execute_strategy(
                        strategy=strategy,
                        data=self.data,
                        sim=self.sim,
                        timeout=self.config.get("timeout_seconds", 420),
                        start_date=self.config.get("start_date"),
                        end_date=self.config.get("end_date"),
                        fee_ratio=self.config.get("fee_ratio"),
                        tax_ratio=self.config.get("tax_ratio"),
                        resample=self.config.get("resample", "M"),
                    )

                    logger.info(
                        f"Factor Graph execution complete: "
                        f"success={result.success}, time={result.execution_time:.1f}s"
                    )
            else:
                # Invalid state
                result = ExecutionResult(
                    success=False,
                    error_type="ValueError",
                    error_message=f"Invalid generation method: {generation_method}",
                    execution_time=0.0,
                )

            return result

        except Exception as e:
            logger.error(f"Strategy execution failed: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                error_type=type(e).__name__,
                error_message=str(e),
                execution_time=0.0,
            )

    def _extract_metrics(self, execution_result: ExecutionResult) -> Dict[str, float]:
        """Extract performance metrics from execution result.

        Args:
            execution_result: Execution result from BacktestExecutor

        Returns:
            Dictionary of metrics (sharpe_ratio, total_return, max_drawdown)
        """
        try:
            if not execution_result.success:
                # Return empty metrics for failures
                return {}

            # Use MetricsExtractor
            metrics = self.metrics_extractor.extract(execution_result.report)
            return metrics

        except Exception as e:
            logger.warning(f"Metrics extraction failed: {e}")
            return {}

    def _classify_result(
        self, execution_result: ExecutionResult, metrics: Dict[str, float]
    ) -> str:
        """Classify execution result into success level.

        Classification Levels:
        - LEVEL_0: Critical failure (syntax error, runtime crash)
        - LEVEL_1: Execution failure (FinLab API error, data issue)
        - LEVEL_2: Weak performance (low Sharpe, excessive drawdown)
        - LEVEL_3: Success (meets performance thresholds)

        Args:
            execution_result: Execution result
            metrics: Extracted metrics

        Returns:
            Classification level string
        """
        try:
            # Convert to StrategyMetrics for classification
            strategy_metrics = StrategyMetrics(
                sharpe_ratio=metrics.get("sharpe_ratio"),
                total_return=metrics.get("total_return"),
                max_drawdown=metrics.get("max_drawdown"),
                execution_success=execution_result.success
            )

            # Classify using ErrorClassifier
            classification_result = self.error_classifier.classify_single(strategy_metrics)

            # Convert level number to string format
            level_map = {
                0: "LEVEL_0",
                1: "LEVEL_1",
                2: "LEVEL_2",
                3: "LEVEL_3"
            }
            return level_map.get(classification_result.level, "LEVEL_0")

        except Exception as e:
            logger.warning(f"Classification failed: {e}")
            return "LEVEL_0"  # Default to worst level on error

    def _update_champion_if_better(
        self,
        iteration_num: int,
        generation_method: str,
        strategy_code: Optional[str],
        strategy_id: Optional[str],
        strategy_generation: Optional[int],
        metrics: Dict[str, float],
        classification_level: str,
    ) -> bool:
        """Update champion if current strategy is better.

        Args:
            iteration_num: Current iteration number
            generation_method: "llm" or "factor_graph"
            strategy_code: Strategy code (for LLM)
            strategy_id: Strategy ID (for Factor Graph)
            strategy_generation: Strategy generation (for Factor Graph)
            metrics: Performance metrics
            classification_level: Success level

        Returns:
            True if champion was updated, False otherwise
        """
        try:
            # Only consider LEVEL_3 (success) for champion
            if classification_level != "LEVEL_3":
                return False

            # Need valid metrics
            if not metrics or "sharpe_ratio" not in metrics:
                return False

            # Update champion using hybrid architecture
            # Pass ALL parameters for both LLM and Factor Graph support
            updated = self.champion_tracker.update_champion(
                iteration_num=iteration_num,
                metrics=metrics,
                generation_method=generation_method,  # "llm" or "factor_graph"
                code=strategy_code,                   # For LLM (None for Factor Graph)
                strategy_id=strategy_id,              # For Factor Graph (None for LLM)
                strategy_generation=strategy_generation  # For Factor Graph (None for LLM)
            )

            if updated:
                logger.info(f"🏆 New champion! Sharpe: {metrics['sharpe_ratio']:.2f}")

            return updated

        except Exception as e:
            logger.error(f"Champion update failed: {e}", exc_info=True)
            return False

    def _create_failure_record(
        self,
        iteration_num: int,
        generation_method: str,
        error_message: str,
        start_time: datetime,
    ) -> IterationRecord:
        """Create IterationRecord for generation failure.

        Args:
            iteration_num: Current iteration number
            generation_method: "llm" or "factor_graph"
            error_message: Error description
            start_time: Iteration start time

        Returns:
            IterationRecord marking failure
        """
        return IterationRecord(
            iteration_num=iteration_num,
            generation_method=generation_method,
            strategy_code=None,
            strategy_id=None,
            strategy_generation=None,
            execution_result={"success": False, "error": error_message},
            metrics={},
            classification_level="LEVEL_0",
            timestamp=datetime.now().isoformat(),
            champion_updated=False,
            feedback_used=None,
        )
