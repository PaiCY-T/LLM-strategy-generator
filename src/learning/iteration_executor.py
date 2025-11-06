"""Iteration Executor for Phase 5.

Executes a single iteration of the autonomous learning loop with 10-step process:
1. Load recent history
2. Generate feedback
3. Decide LLM or Factor Graph (based on innovation_rate)
4. Generate strategy (call LLM or Factor Graph)
5. Execute strategy (Phase 2 BacktestExecutor)
6. Extract metrics (Phase 2 MetricsExtractor)
7. Classify success (Phase 2 SuccessClassifier)
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
from src.backtest.metrics import MetricsExtractor
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
        data: Optional[Any] = None,  # ISSUE #3: Could use finlab.data.Data if available
        sim: Optional[Callable] = None,  # ISSUE #3 FIX: Use Callable instead of Any
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
            data: finlab.data object for backtesting (optional, required for LLM execution)
            sim: finlab.backtest.sim function (optional, required for LLM execution)

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

        # ISSUE #4 FIX: Early validation - check data/sim if LLM is enabled
        if self.llm_client.is_enabled():
            if not self.data or not self.sim:
                raise ValueError(
                    "data and sim are required when LLM client is enabled. "
                    "Provide them to IterationExecutor.__init__(data=..., sim=...)"
                )

        logger.info("IterationExecutor initialized")

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

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"=== Iteration {iteration_num} complete in {elapsed:.1f}s ===")

        # Step 10: Return record
        return record

    def _load_recent_history(self, window: int) -> List[IterationRecord]:
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
            feedback = self.feedback_generator.generate_feedback(
                history=recent_records,
                iteration_num=iteration_num
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

            # Generate strategy
            logger.info("Calling LLM for strategy generation...")
            response = engine.generate_innovation(feedback)

            if not response or not response.get("code"):
                logger.warning("LLM returned empty response")
                return self._generate_with_factor_graph(iteration_num)

            strategy_code = response["code"]
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

        Args:
            iteration_num: Current iteration number

        Returns:
            (None, strategy_id, strategy_generation) for Factor Graph
        """
        # TODO: Implement Factor Graph integration (Task 5.2.1)
        # For now, return a simple placeholder
        logger.warning("Factor Graph not yet integrated, returning placeholder")

        # Placeholder: Simple momentum strategy
        strategy_id = f"momentum_fallback_{iteration_num}"
        strategy_generation = 0

        # Return None for code (Factor Graph doesn't use code strings)
        return (None, strategy_id, strategy_generation)

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
                # Execute code string
                if not self.data or not self.sim:
                    logger.error("data and sim are required for LLM execution but not provided")
                    return ExecutionResult(
                        success=False,
                        error_type="ConfigurationError",
                        error_message="data and sim must be provided to IterationExecutor for LLM execution",
                        execution_time=0.0,
                    )

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
                # TODO: Execute Factor Graph Strategy object (Task 5.2.3)
                # For now, return failure
                logger.warning("Factor Graph execution not yet implemented")
                result = ExecutionResult(
                    success=False,
                    error_type="NotImplementedError",
                    error_message="Factor Graph execution not yet integrated",
                    execution_time=0.0,
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

            # Use MetricsExtractor (returns StrategyMetrics dataclass)
            metrics_obj = self.metrics_extractor.extract_metrics(execution_result.report)
            # Convert StrategyMetrics to dict for compatibility
            return asdict(metrics_obj)

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
            # Check if execution was successful
            if not execution_result.success:
                # Use ErrorClassifier for failure categorization
                if execution_result.error_type:
                    category = self.error_classifier.classify_error(
                        error_type=execution_result.error_type,
                        error_message=execution_result.error_message or ""
                    )
                    # Map ErrorCategory to LEVEL
                    return "LEVEL_0"  # All errors are LEVEL_0 (critical failure)
                else:
                    return "LEVEL_0"

            # Execution successful - classify by performance
            sharpe = metrics.get("sharpe_ratio", 0)

            # LEVEL_3: Good performance (Sharpe >= 1.0)
            if sharpe >= 1.0:
                return "LEVEL_3"
            # LEVEL_2: Weak performance (0 < Sharpe < 1.0)
            elif sharpe > 0:
                return "LEVEL_2"
            # LEVEL_1: Execution success but poor/negative performance
            else:
                return "LEVEL_1"

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

            # Champion tracker currently only supports LLM code strings
            # TODO: Add Factor Graph support to ChampionTracker (Task 5.2.4)
            if generation_method == "llm" and strategy_code:
                updated = self.champion_tracker.update_champion(
                    iteration_num=iteration_num,
                    code=strategy_code,
                    metrics=metrics,
                )

                if updated:
                    logger.info(f"🏆 New champion! Sharpe: {metrics['sharpe_ratio']:.2f}")

                return updated
            elif generation_method == "factor_graph":
                logger.warning("Factor Graph champion tracking not yet implemented")
                return False
            else:
                # ISSUE #5 FIX: More specific error messages
                if generation_method == "llm" and not strategy_code:
                    logger.warning("Cannot update champion: strategy_code is None for LLM generation method")
                else:
                    logger.warning(f"Cannot update champion: unknown generation_method '{generation_method}'")
                return False

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
