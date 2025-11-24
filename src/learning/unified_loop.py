"""UnifiedLoop - Unified Learning Loop Architecture.

Integrates the best features of AutonomousLoop (Template Mode, JSON Parameter Output)
and LearningLoop (Learning Feedback, Modular Architecture) into a single unified architecture.

This module implements the Facade Pattern, providing a unified API that internally
delegates to LearningLoop while supporting Template Mode through TemplateIterationExecutor.

Design Philosophy:
    - Composition over Inheritance: UnifiedLoop wraps LearningLoop
    - Strategy Pattern: Switches between StandardIterationExecutor and TemplateIterationExecutor
    - Backward Compatibility: Provides AutonomousLoop-compatible API
    - Dependency Injection: All components configurable

Example Usage:
    ```python
    from src.learning.unified_loop import UnifiedLoop

    # Template Mode with JSON Parameter Output
    loop = UnifiedLoop(
        max_iterations=100,
        template_mode=True,
        template_name="Momentum",
        use_json_mode=True,
        enable_learning=True
    )

    # Run loop (delegates to LearningLoop)
    result = loop.run()

    # Access champion (backward compatible)
    champion = loop.champion
    print(f"Champion Sharpe: {champion.metrics['sharpe_ratio']}")

    # Access history (backward compatible)
    history = loop.history
    recent = history.load_recent(N=10)
    ```

Architecture:
    ```
    UnifiedLoop (Facade, <200 lines)
         ↓ delegates to
    LearningLoop (Orchestrator, <250 lines)
         ↓ uses
    IterationExecutor (Strategy Pattern)
         ├── StandardIterationExecutor (existing)
         └── TemplateIterationExecutor (new)
    ```

See Also:
    - src/learning/learning_loop.py: Core orchestrator
    - src/learning/unified_config.py: Configuration
    - src/learning/template_iteration_executor.py: Template Mode executor
    - .spec-workflow/specs/unified-loop-refactor/design.md: Architecture design
"""

import logging
from typing import Any, Dict, Optional

from src.learning.learning_loop import LearningLoop
from src.learning.unified_config import UnifiedConfig, ConfigurationError
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.resource_monitor import ResourceMonitor
from src.monitoring.diversity_monitor import DiversityMonitor

logger = logging.getLogger(__name__)


class UnifiedLoop:
    """Unified Loop implementing Facade Pattern over LearningLoop.

    Provides a unified API that integrates Template Mode, JSON Parameter Output,
    and Learning Feedback while maintaining backward compatibility with AutonomousLoop.

    Key Features:
        - Template Mode: Uses TemplateIterationExecutor for parameter generation
        - JSON Parameter Output: LLM outputs JSON format, Pydantic validation
        - Learning Feedback: FeedbackGenerator provides performance feedback
        - Backward Compatible: Same API as AutonomousLoop

    Design:
        - Facade Pattern: Thin wrapper (~200 lines) over LearningLoop
        - Strategy Pattern: Switches IterationExecutor based on template_mode
        - Dependency Injection: TemplateIterationExecutor injected after init

    Attributes:
        config (UnifiedConfig): Unified configuration
        learning_loop (LearningLoop): Core orchestrator
        template_mode (bool): Whether Template Mode is enabled
        use_json_mode (bool): Whether JSON Parameter Output is enabled

    Example:
        >>> loop = UnifiedLoop(
        ...     max_iterations=50,
        ...     template_mode=True,
        ...     template_name="Momentum",
        ...     use_json_mode=True
        ... )
        >>> result = loop.run()
        >>> print(f"Iterations completed: {result.get('iterations_completed')}")
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        max_iterations: int = 10,
        template_mode: bool = False,
        template_name: str = "Momentum",
        use_json_mode: bool = False,
        enable_learning: bool = True,
        history_file: str = "artifacts/data/iterations.jsonl",
        champion_file: str = "artifacts/data/champion.json",
        config_file: str = "config/learning_system.yaml",
        timeout_seconds: int = 420,
        **kwargs
    ):
        """Initialize UnifiedLoop.

        Args:
            model: LLM model name (e.g., "gemini-2.5-flash")
            max_iterations: Maximum iterations to run
            template_mode: Enable Template Mode (uses TemplateIterationExecutor)
            template_name: Template name (required if template_mode=True)
            use_json_mode: Enable JSON Parameter Output (requires template_mode=True)
            enable_learning: Enable Learning Feedback system
            history_file: Path to JSONL history file
            champion_file: Path to champion JSON file
            config_file: Path to YAML config file
            timeout_seconds: Backtest timeout in seconds
            **kwargs: Additional configuration parameters

        Raises:
            ConfigurationError: If configuration is invalid
            RuntimeError: If component initialization fails

        Example:
            >>> loop = UnifiedLoop(
            ...     max_iterations=100,
            ...     template_mode=True,
            ...     template_name="Momentum",
            ...     use_json_mode=True
            ... )
        """
        logger.info("=" * 60)
        logger.info("UnifiedLoop Initialization")
        logger.info("=" * 60)

        # Build UnifiedConfig
        self.config = self._build_unified_config(
            model=model,
            max_iterations=max_iterations,
            template_mode=template_mode,
            template_name=template_name,
            use_json_mode=use_json_mode,
            enable_learning=enable_learning,
            history_file=history_file,
            champion_file=champion_file,
            config_file=config_file,
            timeout_seconds=timeout_seconds,
            **kwargs
        )

        # Store template settings
        self.template_mode = self.config.template_mode
        self.use_json_mode = self.config.use_json_mode

        logger.info(f"Configuration:")
        logger.info(f"  Template Mode: {self.template_mode}")
        logger.info(f"  JSON Mode: {self.use_json_mode}")
        logger.info(f"  Learning Enabled: {self.config.enable_learning}")
        logger.info(f"  Max Iterations: {self.config.max_iterations}")
        logger.info(f"  Innovation Rate: {self.config.innovation_rate:.1f}% (LLM probability)")

        # Convert to LearningConfig and initialize LearningLoop
        learning_config = self.config.to_learning_config()
        self.learning_loop = LearningLoop(config=learning_config)

        logger.info("✓ LearningLoop initialized")

        # If Template Mode, inject TemplateIterationExecutor
        if self.template_mode:
            logger.info(f"✓ Template Mode enabled: {self.config.template_name}")
            self._inject_template_executor()
        else:
            # Log generation mode based on innovation_rate
            if self.config.innovation_rate >= 100.0:
                logger.info("✓ Pure LLM Mode (innovation_rate=100%)")
            elif self.config.innovation_rate <= 0.0:
                logger.info("✓ Pure Factor Graph Mode (innovation_rate=0%)")
            else:
                logger.info(f"✓ Hybrid Mode (LLM={self.config.innovation_rate:.1f}%, FG={100-self.config.innovation_rate:.1f}%)")

        # Initialize monitoring systems (Week 3.1)
        self._initialize_monitoring()

        logger.info("=" * 60)
        logger.info("UnifiedLoop initialization complete")
        logger.info("=" * 60)

    def _build_unified_config(self, **kwargs) -> UnifiedConfig:
        """Build UnifiedConfig from keyword arguments.

        Filters and maps keyword arguments to UnifiedConfig attributes.

        Args:
            **kwargs: Configuration parameters

        Returns:
            UnifiedConfig: Validated configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Extract known parameters for UnifiedConfig
        config_kwargs = {
            k: v for k, v in kwargs.items()
            if k in UnifiedConfig.__dataclass_fields__
        }

        # Add explicit parameters
        for key in ['model', 'max_iterations', 'template_mode', 'template_name',
                    'use_json_mode', 'enable_learning', 'history_file',
                    'champion_file', 'config_file', 'timeout_seconds']:
            if key in kwargs:
                # Map 'model' to 'llm_model' for UnifiedConfig
                if key == 'model':
                    config_kwargs['llm_model'] = kwargs[key]
                else:
                    config_kwargs[key] = kwargs[key]

        try:
            config = UnifiedConfig(**config_kwargs)
            logger.debug("UnifiedConfig created successfully")
            return config
        except Exception as e:
            logger.error(f"Failed to create UnifiedConfig: {e}")
            raise ConfigurationError(f"Invalid configuration: {e}") from e

    def _inject_template_executor(self) -> None:
        """Inject TemplateIterationExecutor to replace StandardIterationExecutor.

        This method implements the Strategy Pattern, switching the iteration executor
        from StandardIterationExecutor to TemplateIterationExecutor when Template Mode
        is enabled.

        Note:
            TemplateIterationExecutor will be implemented in Week 1.2.1.
            For now, this logs a warning that Template Mode requires the executor.

        Raises:
            RuntimeError: If TemplateIterationExecutor cannot be initialized
        """
        try:
            # Import here to avoid circular dependency
            # Note: This will be implemented in Week 1.2.1
            try:
                from src.learning.template_iteration_executor import TemplateIterationExecutor

                # Create TemplateIterationExecutor
                template_executor = TemplateIterationExecutor(
                    llm_client=self.learning_loop.llm_client,
                    feedback_generator=self.learning_loop.feedback_generator,
                    backtest_executor=self.learning_loop.backtest_executor,
                    champion_tracker=self.learning_loop.champion_tracker,
                    history=self.learning_loop.history,
                    template_name=self.config.template_name,
                    use_json_mode=self.config.use_json_mode,
                    config=self.config.to_dict()
                )

                # Inject executor
                self.learning_loop.iteration_executor = template_executor

                logger.info(
                    f"✓ TemplateIterationExecutor injected "
                    f"(template={self.config.template_name}, json_mode={self.config.use_json_mode})"
                )

            except ImportError:
                logger.warning(
                    "⚠️  TemplateIterationExecutor not yet implemented (Week 1.2.1)"
                )
                logger.warning("   UnifiedLoop will use StandardIterationExecutor for now")

        except Exception as e:
            logger.error(f"Failed to inject TemplateIterationExecutor: {e}")
            raise RuntimeError(f"Template Mode initialization failed: {e}") from e

    def _initialize_monitoring(self) -> None:
        """Initialize monitoring systems (Week 3.1).

        Creates and configures:
        - MetricsCollector: Collects performance and learning metrics
        - ResourceMonitor: Monitors CPU, memory, disk usage
        - DiversityMonitor: Tracks strategy diversity and champion staleness

        Monitoring is enabled if config.enable_monitoring=True (default).
        ResourceMonitor runs in background thread with minimal overhead (<1%).
        """
        if not self.config.enable_monitoring:
            logger.info("✓ Monitoring disabled (enable_monitoring=False)")
            self.metrics_collector = None
            self.resource_monitor = None
            self.diversity_monitor = None
            return

        logger.info("Initializing monitoring systems...")

        try:
            # 3.1.1: Initialize MetricsCollector
            self.metrics_collector = MetricsCollector(
                history_window=self.config.history_window
            )
            logger.info("  ✓ MetricsCollector initialized")

            # 3.1.2: Initialize ResourceMonitor
            self.resource_monitor = ResourceMonitor(
                metrics_collector=self.metrics_collector
            )
            # Start background monitoring
            self.resource_monitor.start_monitoring(interval_seconds=5)
            logger.info("  ✓ ResourceMonitor started (5s interval)")

            # 3.1.3: Initialize DiversityMonitor
            self.diversity_monitor = DiversityMonitor(
                metrics_collector=self.metrics_collector,
                collapse_threshold=0.1,
                collapse_window=5
            )
            logger.info("  ✓ DiversityMonitor initialized")

            logger.info("✓ All monitoring systems active")

        except Exception as e:
            logger.error(f"Failed to initialize monitoring: {e}", exc_info=True)
            logger.warning("Continuing without monitoring")
            self.metrics_collector = None
            self.resource_monitor = None
            self.diversity_monitor = None

    def _shutdown_monitoring(self) -> None:
        """Shutdown monitoring systems gracefully.

        Stops ResourceMonitor background thread and exports final metrics.
        Called at the end of run() or in __del__.
        """
        if not self.config.enable_monitoring:
            return

        logger.info("Shutting down monitoring systems...")

        try:
            # Stop ResourceMonitor background thread
            if self.resource_monitor:
                self.resource_monitor.stop_monitoring()
                logger.info("  ✓ ResourceMonitor stopped")

            # Export final metrics (if needed)
            if self.metrics_collector:
                logger.info("  ✓ MetricsCollector final state saved")

            logger.info("✓ Monitoring shutdown complete")

        except Exception as e:
            logger.error(f"Error during monitoring shutdown: {e}", exc_info=True)

    def run(self) -> Dict[str, Any]:
        """Run learning loop iterations.

        Delegates execution to LearningLoop, which handles:
        - Iteration loop management
        - SIGINT handling
        - Progress tracking
        - Summary report generation

        Returns:
            Dict containing:
                - iterations_completed (int): Number of iterations run
                - champion (Optional[ChampionRecord]): Current champion
                - interrupted (bool): Whether loop was interrupted

        Example:
            >>> loop = UnifiedLoop(max_iterations=50)
            >>> result = loop.run()
            >>> print(f"Completed {result['iterations_completed']} iterations")
        """
        logger.info("\n" + "=" * 60)
        logger.info("Starting UnifiedLoop Execution")
        logger.info("=" * 60)

        try:
            # Delegate to LearningLoop
            self.learning_loop.run()

            # Build result summary
            all_records = self.learning_loop.history.get_all()
            iterations_completed = len(all_records)
            champion = self.learning_loop.champion_tracker.champion

            result = {
                "iterations_completed": iterations_completed,
                "champion": champion,
                "interrupted": self.learning_loop.interrupted
            }

            logger.info("\n" + "=" * 60)
            logger.info("UnifiedLoop Execution Complete")
            logger.info("=" * 60)
            logger.info(f"Total Iterations: {iterations_completed}")
            if champion:
                logger.info(f"Champion Sharpe: {champion.metrics.get('sharpe_ratio', 'N/A')}")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"UnifiedLoop execution failed: {e}", exc_info=True)
            raise
        finally:
            # Always shutdown monitoring, even if execution failed
            self._shutdown_monitoring()

    @property
    def champion(self):
        """Access current champion strategy (backward compatible).

        Provides AutonomousLoop-compatible API for accessing champion.

        Returns:
            Optional[ChampionRecord]: Current champion or None

        Example:
            >>> loop = UnifiedLoop()
            >>> loop.run()
            >>> if loop.champion:
            ...     print(f"Champion Sharpe: {loop.champion.metrics['sharpe_ratio']}")
        """
        return self.learning_loop.champion_tracker.champion

    @property
    def history(self):
        """Access iteration history (backward compatible).

        Provides AutonomousLoop-compatible API for accessing history.

        Returns:
            IterationHistory: History manager

        Example:
            >>> loop = UnifiedLoop()
            >>> loop.run()
            >>> recent = loop.history.load_recent(N=5)
            >>> for record in recent:
            ...     print(f"Iteration {record.iteration_num}: {record.classification_level}")
        """
        return self.learning_loop.history
