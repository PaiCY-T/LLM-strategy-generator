"""Template Iteration Executor for UnifiedLoop.

Executes a single iteration using Template Mode with JSON Parameter Output support.
This executor replaces StandardIterationExecutor when template_mode=True, providing:

- Template-based parameter generation via TemplateParameterGenerator
- JSON Parameter Output mode with Pydantic validation
- Integration with FeedbackGenerator for learning feedback
- Template-based code generation via TemplateCodeGenerator

10-Step Iteration Flow (Template Mode):
    1. Load recent history
    2. Generate feedback (if enabled and not first iteration)
    3. Template mode decision (no LLM vs Factor Graph choice)
    4. Generate parameters (via TemplateParameterGenerator with feedback)
    5. Generate strategy code (via TemplateCodeGenerator)
    6. Execute strategy (via BacktestExecutor)
    7. Extract metrics (via MetricsExtractor)
    8. Classify success (via SuccessClassifier)
    9. Update Champion (if better)
    10. Create IterationRecord and return

Example Usage:
    ```python
    from src.learning.template_iteration_executor import TemplateIterationExecutor

    executor = TemplateIterationExecutor(
        llm_client=llm_client,
        feedback_generator=feedback_generator,
        backtest_executor=backtest_executor,
        champion_tracker=champion_tracker,
        history=history,
        template_name="Momentum",
        use_json_mode=True,
        config=config_dict
    )

    record = executor.execute_iteration(iteration_num=0)
    ```

See Also:
    - src/learning/iteration_executor.py: Base IterationExecutor
    - src/generators/template_parameter_generator.py: Parameter generation
    - src/templates/momentum_template.py: Template implementation
    - .spec-workflow/specs/unified-loop-refactor/design.md: Architecture design
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from src.backtest.executor import BacktestExecutor
from src.backtest.metrics import MetricsExtractor, StrategyMetrics
from src.backtest.classifier import SuccessClassifier
from src.learning.champion_tracker import ChampionTracker
from src.learning.feedback_generator import FeedbackGenerator
from src.learning.iteration_history import IterationHistory, IterationRecord
from src.learning.llm_client import LLMClient
from src.generators.template_parameter_generator import (
    TemplateParameterGenerator,
    ParameterGenerationContext
)
from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig

logger = logging.getLogger(__name__)


class TemplateIterationExecutor:
    """Iteration executor for Template Mode.

    Executes iterations using template-based parameter generation instead of
    freeform LLM or Factor Graph approaches. Integrates learning feedback to
    guide parameter selection over time.

    This executor implements the Strategy Pattern, replacing StandardIterationExecutor
    when template_mode=True in UnifiedLoop.

    Key Features:
        - Template parameter generation with LLM guidance
        - JSON Parameter Output mode (Pydantic validation)
        - Learning feedback integration
        - Template code generation

    Attributes:
        llm_client (LLMClient): LLM client for parameter generation
        feedback_generator (FeedbackGenerator): Generates learning feedback
        backtest_executor (BacktestExecutor): Executes strategy backtests
        champion_tracker (ChampionTracker): Tracks best strategy
        history (IterationHistory): Iteration history manager
        template_name (str): Template name (e.g., "Momentum")
        use_json_mode (bool): Whether to use JSON Parameter Output
        config (Dict): Configuration dictionary
        template_param_generator (TemplateParameterGenerator): Parameter generator
        metrics_extractor (MetricsExtractor): Metrics extraction
        success_classifier (SuccessClassifier): Success classification
        docker_executor (Optional[DockerExecutor]): Docker sandbox executor (Week 3.2)

    Example:
        >>> executor = TemplateIterationExecutor(
        ...     llm_client=llm,
        ...     feedback_generator=feedback_gen,
        ...     backtest_executor=backtest_exec,
        ...     champion_tracker=champion,
        ...     history=hist,
        ...     template_name="Momentum",
        ...     use_json_mode=True,
        ...     config={"history_window": 10}
        ... )
        >>> record = executor.execute_iteration(0)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        feedback_generator: FeedbackGenerator,
        backtest_executor: BacktestExecutor,
        champion_tracker: ChampionTracker,
        history: IterationHistory,
        template_name: str,
        use_json_mode: bool,
        config: Dict[str, Any],
        **kwargs
    ):
        """Initialize TemplateIterationExecutor.

        Args:
            llm_client: LLM client for parameter generation
            feedback_generator: Feedback generator from history
            backtest_executor: Backtest executor with timeout
            champion_tracker: Champion tracker for best strategy
            history: Iteration history
            template_name: Template name (e.g., "Momentum", "Factor")
            use_json_mode: Enable JSON Parameter Output mode
            config: Configuration dict with keys:
                - history_window: Number of recent iterations for feedback
                - timeout_seconds: Backtest timeout
                - ...
            **kwargs: Additional parameters

        Raises:
            ValueError: If template_name is invalid
            RuntimeError: If component initialization fails
        """
        self.llm_client = llm_client
        self.feedback_generator = feedback_generator
        self.backtest_executor = backtest_executor
        self.champion_tracker = champion_tracker
        self.history = history
        self.template_name = template_name
        self.use_json_mode = use_json_mode
        self.config = config

        # Initialize template parameter generator
        try:
            model = config.get("llm_model", "gemini-2.5-flash")
            self.template_param_generator = TemplateParameterGenerator(
                template_name=template_name,
                model=model
            )
            logger.info(
                f"TemplateParameterGenerator initialized: {template_name}, "
                f"JSON mode: {use_json_mode}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize TemplateParameterGenerator: {e}")
            raise RuntimeError(f"TemplateParameterGenerator init failed: {e}") from e

        # Initialize metrics extractor and success classifier
        self.metrics_extractor = MetricsExtractor()
        self.success_classifier = SuccessClassifier()

        # Initialize Docker sandbox executor (Week 3.2.1)
        self.docker_executor = None
        docker_enabled = config.get("use_docker", False)
        if docker_enabled:
            try:
                docker_config = DockerConfig.from_yaml()
                self.docker_executor = DockerExecutor(config=docker_config)
                logger.info(
                    f"✓ DockerExecutor initialized: "
                    f"image={docker_config.image[:30]}..., "
                    f"memory={docker_config.memory_limit}, "
                    f"cpu={docker_config.cpu_limit}, "
                    f"timeout={docker_config.timeout_seconds}s"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize DockerExecutor: {e}. "
                    f"Falling back to direct execution."
                )
                self.docker_executor = None
        else:
            logger.info("Docker sandbox disabled (use_docker=False)")

        logger.info(
            f"TemplateIterationExecutor initialized: {template_name}, "
            f"JSON mode: {use_json_mode}, "
            f"Docker: {self.docker_executor is not None}"
        )

    def execute_iteration(self, iteration_num: int, **kwargs) -> IterationRecord:
        """Execute single iteration using Template Mode.

        Implements 10-step iteration flow for template-based generation.

        Args:
            iteration_num: Current iteration number (0-indexed)
            **kwargs: Additional parameters

        Returns:
            IterationRecord: Complete iteration record

        Raises:
            Exception: Various exceptions (caught and recorded in IterationRecord)

        Example:
            >>> record = executor.execute_iteration(0)
            >>> print(f"Iteration {record.iteration_num}: {record.classification_level}")
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Template Iteration {iteration_num} (Template: {self.template_name})")
        logger.info(f"{'='*60}")

        # Step 1: Load recent history
        history_window = self.config.get("history_window", 10)
        recent_history = self.history.load_recent(N=history_window)
        logger.debug(f"Loaded {len(recent_history)} recent iterations")

        # Step 2: Generate feedback (if enabled and not first iteration)
        feedback = None
        if self.feedback_generator and iteration_num > 0 and recent_history:
            try:
                last_record = recent_history[0]  # Most recent (reversed order)
                feedback = self.feedback_generator.generate_feedback(
                    iteration_num=iteration_num,
                    metrics=last_record.metrics,
                    execution_result=last_record.execution_result,
                    classification_level=last_record.classification_level,
                    error_msg=last_record.error_msg if hasattr(last_record, 'error_msg') else None
                )
                logger.info(f"✓ Generated feedback ({len(feedback)} chars)")
                logger.debug(f"Feedback preview: {feedback[:200]}...")
            except Exception as e:
                logger.warning(f"Feedback generation failed, continuing without feedback: {e}")
                feedback = None

        # Step 3: Template mode (no LLM vs Factor Graph decision needed)
        logger.info(f"✓ Template Mode: {self.template_name}")

        # Step 4: Generate parameters
        try:
            params = self._generate_parameters(iteration_num, feedback)
            logger.info(f"✓ Generated parameters: {params}")
        except Exception as e:
            logger.error(f"Parameter generation failed: {e}")
            return self._create_error_record(
                iteration_num,
                f"Parameter generation error: {e}",
                params={}
            )

        # Step 5: Execute strategy directly via template (no code generation in template mode)
        try:
            logger.info(f"Executing template strategy with params: {params}")
            report, metrics_dict = self.template_param_generator.template.generate_strategy(params)

            # Metrics already extracted by template - convert to StrategyMetrics format
            from src.backtest.metrics import StrategyMetrics
            metrics = StrategyMetrics.from_dict(metrics_dict)

            # Build execution_result for compatibility with SuccessClassifier
            execution_result = {
                'success': metrics_dict.get('success', False),
                'sharpe_ratio': metrics_dict.get('sharpe_ratio'),
                'total_return': metrics_dict.get('annual_return'),
                'max_drawdown': metrics_dict.get('max_drawdown'),
                # Note: 'report' removed - finlab.Report object is not JSON serializable
                # and is never used downstream (Bug #7 fix)
                'template_executed': True
            }
            logger.info(f"✓ Template execution successful (Sharpe={metrics.sharpe_ratio:.3f})")

            # No strategy_code for template mode - store parameters as reference
            strategy_code = f"# Template: {self.template_name}\n# Parameters: {params}"

        except Exception as e:
            logger.error(f"Template execution failed: {e}")
            return self._create_error_record(
                iteration_num,
                f"Template execution error: {e}",
                params=params
            )

        # Step 8: Classify success
        try:
            # Bug #6 fix: Use classify_single() instead of classify()
            # SuccessClassifier API: classify_single(StrategyMetrics) -> ClassificationResult
            # ClassificationResult.level is int (0-3), convert to string format "LEVEL_N"
            classification_result = self.success_classifier.classify_single(metrics)
            classification_level = f"LEVEL_{classification_result.level}"
            logger.info(f"✓ Classification: {classification_level}")
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            classification_level = "LEVEL_0"

        # Step 9: Update Champion (if better)
        champion_updated = False
        try:
            if classification_level == "LEVEL_3" and metrics:
                was_updated = self.champion_tracker.update_if_better(
                    iteration_num=iteration_num,
                    strategy_code=strategy_code,
                    params=params,
                    metrics=metrics,
                    generation_method="template",
                    strategy_id=None,
                    strategy_generation=None
                )
                if was_updated:
                    champion_updated = True
                    logger.info(f"🏆 Champion UPDATED! Sharpe={metrics.sharpe_ratio:.3f}")
                else:
                    champion = self.champion_tracker.champion
                    if champion:
                        logger.info(
                            f"Champion unchanged (current: {champion.metrics.get('sharpe_ratio', 0):.3f})"
                        )
        except Exception as e:
            logger.error(f"Champion update failed: {e}")

        # Step 10: Create IterationRecord and return
        record = IterationRecord(
            iteration_num=iteration_num,
            generation_method="template",
            strategy_code=strategy_code,
            execution_result=execution_result if isinstance(execution_result, dict) else {},
            metrics=metrics,
            classification_level=classification_level,
            timestamp=datetime.now().isoformat(),
            champion_updated=champion_updated,
            feedback_used=feedback,
            template_name=self.template_name,
            json_mode=self.use_json_mode
        )

        logger.info(f"✓ Iteration {iteration_num} complete")
        return record

    def _generate_parameters(
        self,
        iteration_num: int,
        feedback: Optional[str]
    ) -> Dict[str, Any]:
        """Generate parameters using TemplateParameterGenerator.

        Args:
            iteration_num: Current iteration number
            feedback: Performance feedback from previous iterations

        Returns:
            Dict: Parameter dictionary for template

        Raises:
            Exception: If parameter generation fails
        """
        # Get champion context
        champion = self.champion_tracker.champion
        champion_params = champion.parameters if champion else None
        champion_sharpe = champion.metrics.get("sharpe_ratio") if champion and champion.metrics else None

        # Build context
        context = ParameterGenerationContext(
            iteration_num=iteration_num,
            champion_params=champion_params,
            champion_sharpe=champion_sharpe,
            feedback_history=feedback
        )

        # Generate parameters
        try:
            params = self.template_param_generator.generate_parameters(context)
            return params
        except Exception as e:
            logger.error(f"TemplateParameterGenerator.generate_parameters failed: {e}")
            raise

    def _create_error_record(
        self,
        iteration_num: int,
        error_msg: str,
        params: Dict[str, Any] = None,
        code: str = ""
    ) -> IterationRecord:
        """Create error iteration record.

        Args:
            iteration_num: Current iteration number
            error_msg: Error message
            params: Parameters (if generated)
            code: Strategy code (if generated)

        Returns:
            IterationRecord: Error record
        """
        return IterationRecord(
            iteration_num=iteration_num,
            generation_method="template",
            strategy_code=code,
            execution_result={"status": "error", "error": error_msg},
            metrics=None,
            classification_level="LEVEL_0",
            timestamp=datetime.now().isoformat(),
            champion_updated=False,
            feedback_used=None,
            template_name=self.template_name,
            json_mode=self.use_json_mode
        )
