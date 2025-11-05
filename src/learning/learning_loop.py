"""Learning Loop Orchestrator for Phase 6.

Lightweight orchestrator (<250 lines) that coordinates all components:
- Initializes all Phase 1-5 components
- Runs iteration loop with progress tracking
- Handles CTRL+C interruption gracefully
- Supports resumption from last iteration
- Generates summary report

This refactored from autonomous_loop.py (2,981 lines → ~200 lines orchestration).
"""

import logging
import os
import signal
import sys
from datetime import datetime
from typing import Optional

from src.backtest.executor import BacktestExecutor
from src.learning.champion_tracker import ChampionTracker
from src.learning.feedback_generator import FeedbackGenerator
from src.learning.iteration_executor import IterationExecutor
from src.learning.iteration_history import IterationHistory
from src.learning.learning_config import LearningConfig
from src.learning.llm_client import LLMClient

logger = logging.getLogger(__name__)


class LearningLoop:
    """Lightweight learning loop orchestrator.

    Responsibilities (ONLY orchestration, ~200 lines):
    1. Load configuration
    2. Initialize all components
    3. Determine start iteration (new or resume)
    4. Loop: call IterationExecutor, save record, show progress
    5. Handle SIGINT interruption
    6. Generate summary report

    Does NOT contain:
    - Strategy generation logic → IterationExecutor
    - LLM calls → LLMClient
    - Backtest execution → BacktestExecutor
    - Metrics extraction → MetricsExtractor
    - Champion updates → ChampionTracker
    - Feedback generation → FeedbackGenerator
    """

    def __init__(self, config: LearningConfig):
        """Initialize learning loop with configuration.

        Args:
            config: LearningConfig with all parameters

        Raises:
            ValueError: If config validation fails
            RuntimeError: If component initialization fails
        """
        self.config = config
        self.interrupted = False

        # Setup logging
        self._setup_logging()

        logger.info("=" * 60)
        logger.info("Learning Loop Initialization")
        logger.info("=" * 60)

        # Initialize components in dependency order
        try:
            # 1. History (no dependencies)
            self.history = IterationHistory(file_path=config.history_file)
            logger.info(f"✓ IterationHistory: {config.history_file}")

            # 2. Champion Tracker (depends on history)
            self.champion_tracker = ChampionTracker(
                champion_file=config.champion_file,
                history=self.history
            )
            logger.info(f"✓ ChampionTracker: {config.champion_file}")

            # 3. LLM Client (no dependencies)
            self.llm_client = LLMClient(config_path=config.config_file)
            logger.info(f"✓ LLMClient: enabled={self.llm_client.is_enabled()}")

            # 4. Feedback Generator (depends on history, champion)
            self.feedback_generator = FeedbackGenerator(
                history=self.history,
                champion=self.champion_tracker
            )
            logger.info("✓ FeedbackGenerator initialized")

            # 5. Backtest Executor (no dependencies)
            self.backtest_executor = BacktestExecutor(timeout=config.timeout_seconds)
            logger.info(f"✓ BacktestExecutor: timeout={config.timeout_seconds}s")

            # 6. Iteration Executor (depends on all above)
            self.iteration_executor = IterationExecutor(
                llm_client=self.llm_client,
                feedback_generator=self.feedback_generator,
                backtest_executor=self.backtest_executor,
                champion_tracker=self.champion_tracker,
                history=self.history,
                config=config.to_dict(),
            )
            logger.info("✓ IterationExecutor initialized")

            logger.info("=" * 60)
            logger.info("All components initialized successfully")
            logger.info("=" * 60)

        except Exception as e:
            logger.critical(f"Component initialization failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize components: {e}")

    def run(self) -> None:
        """Run learning loop with interruption handling.

        Main orchestration flow:
        1. Setup SIGINT handler
        2. Determine start iteration (resume or 0)
        3. Show startup info
        4. Loop: execute iteration, save, show progress
        5. Handle interruption gracefully
        6. Generate summary report
        """
        # Setup signal handler
        self._setup_signal_handlers()

        # Determine start iteration
        start_iteration = self._get_start_iteration()

        # Show startup info
        self._show_startup_info(start_iteration)

        # Main loop
        for iteration_num in range(start_iteration, self.config.max_iterations):
            if self.interrupted:
                logger.info(f"\n⚠️  Interrupted at iteration {iteration_num}")
                break

            record = None
            try:
                # Execute iteration (delegates to IterationExecutor)
                logger.info(f"\n{'='*60}")
                logger.info(f"Iteration {iteration_num + 1}/{self.config.max_iterations}")
                logger.info(f"{'='*60}")

                record = self.iteration_executor.execute_iteration(iteration_num)

            except KeyboardInterrupt:
                logger.info("\n⚠️  KeyboardInterrupt received during iteration execution...")
                self.interrupted = True
                # Note: record will be None, so save will be skipped
                # This is intentional - partially executed iteration not saved

            except Exception as e:
                logger.error(f"❌ Iteration {iteration_num} failed: {e}", exc_info=True)

                if not self.config.continue_on_error:
                    logger.error("Stopping due to error (continue_on_error=False)")
                    raise

                logger.warning("Continuing to next iteration (continue_on_error=True)")

            finally:
                # Always try to save record if it was completed
                # Protects against race condition: if SIGINT arrives between
                # execute_iteration() and save_record(), we still save
                if record is not None:
                    try:
                        self.history.save_record(record)
                        logger.debug(f"Saved iteration {iteration_num} to history")

                        # Show progress
                        self._show_progress(iteration_num, record)

                    except Exception as e:
                        logger.error(f"Failed to save iteration {iteration_num}: {e}")

                # Break after save if interrupted
                if self.interrupted:
                    logger.info("Exiting loop due to interruption")
                    break

        # Generate summary
        self._generate_summary(start_iteration)

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.config.log_level, logging.INFO)

        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[]
        )

        # Console handler
        if self.config.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            logging.getLogger().addHandler(console_handler)

        # File handler
        if self.config.log_to_file:
            os.makedirs(self.config.log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(self.config.log_dir, f"learning_loop_{timestamp}.log")
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            logging.getLogger().addHandler(file_handler)
            logger.info(f"Logging to file: {log_file}")

    def _setup_signal_handlers(self) -> None:
        """Setup SIGINT (CTRL+C) handler."""
        def sigint_handler(signum, frame):
            if not self.interrupted:
                logger.info("\n" + "=" * 60)
                logger.info("⚠️  INTERRUPT SIGNAL RECEIVED (CTRL+C)")
                logger.info("=" * 60)
                logger.info("Finishing current iteration before exit...")
                logger.info("(Press CTRL+C again to force quit)")
                logger.info("=" * 60)
                self.interrupted = True
            else:
                logger.warning("\n⚠️  FORCE QUIT")
                sys.exit(1)

        signal.signal(signal.SIGINT, sigint_handler)
        logger.debug("SIGINT handler registered")

    def _get_start_iteration(self) -> int:
        """Determine starting iteration number.

        Handles:
        - New run: start from 0
        - Resume: start from last iteration + 1
        - Already complete: return max_iterations (loop exits immediately)

        Returns:
            Starting iteration number (0-indexed)
        """
        try:
            records = self.history.get_all()

            if not records:
                logger.info("📝 No previous iterations found, starting from 0")
                return 0

            # Find max iteration number
            max_iteration = max(r.iteration_num for r in records)
            next_iteration = max_iteration + 1

            # Check if already complete
            if next_iteration >= self.config.max_iterations:
                logger.warning(
                    f"⚠️  All {self.config.max_iterations} iterations already completed"
                )
                logger.warning("Increase max_iterations in config or start fresh")
                return self.config.max_iterations  # Loop will exit immediately

            # Resume
            logger.info(f"🔄 Resuming from iteration {next_iteration}")
            logger.info(f"   (Found {len(records)} previous iterations)")
            return next_iteration

        except Exception as e:
            logger.error(f"Failed to determine start iteration: {e}")
            logger.warning("Starting from iteration 0 as fallback")
            return 0

    def _show_startup_info(self, start_iteration: int) -> None:
        """Show startup information."""
        logger.info("\n" + "=" * 60)
        logger.info("🚀 LEARNING LOOP STARTING")
        logger.info("=" * 60)
        logger.info(f"Max Iterations:    {self.config.max_iterations}")
        logger.info(f"Starting From:     {start_iteration}")
        logger.info(f"Innovation Mode:   {self.config.innovation_mode}")
        logger.info(f"Innovation Rate:   {self.config.innovation_rate}%")
        logger.info(f"LLM Model:         {self.config.llm_model}")
        logger.info(f"Backtest Timeout:  {self.config.timeout_seconds}s")
        logger.info(f"History File:      {self.config.history_file}")
        logger.info("=" * 60)

    def _show_progress(self, iteration_num: int, record) -> None:
        """Show iteration progress.

        Args:
            iteration_num: Current iteration number
            record: IterationRecord from execution
        """
        # Calculate success rate
        all_records = self.history.get_all()
        total = len(all_records)
        level_1_plus = sum(1 for r in all_records if r.classification_level in ("LEVEL_1", "LEVEL_2", "LEVEL_3"))
        level_3 = sum(1 for r in all_records if r.classification_level == "LEVEL_3")

        success_rate_1 = (level_1_plus / total * 100) if total > 0 else 0
        success_rate_3 = (level_3 / total * 100) if total > 0 else 0

        # Get current champion
        champion = self.champion_tracker.get_champion()
        champion_sharpe = champion.metrics.get("sharpe_ratio", 0.0) if champion else 0.0

        # Show progress
        logger.info("\n" + "-" * 60)
        logger.info(f"📊 ITERATION {iteration_num + 1}/{self.config.max_iterations} COMPLETE")
        logger.info("-" * 60)
        logger.info(f"Method:         {record.generation_method}")
        logger.info(f"Classification: {record.classification_level}")

        if record.metrics:
            sharpe = record.metrics.get("sharpe_ratio", "N/A")
            logger.info(f"Sharpe Ratio:   {sharpe}")

        logger.info(f"Champion:       {'UPDATED ✨' if record.champion_updated else f'Unchanged (Sharpe={champion_sharpe:.2f})'}")
        logger.info(f"Success Rate:   Level 1+: {success_rate_1:.1f}%, Level 3: {success_rate_3:.1f}%")
        logger.info("-" * 60)

    def _generate_summary(self, start_iteration: int) -> None:
        """Generate final summary report.

        Args:
            start_iteration: Where loop started
        """
        all_records = self.history.get_all()
        total = len(all_records)

        # Filter to this run's records
        run_records = [r for r in all_records if r.iteration_num >= start_iteration]
        run_count = len(run_records)

        # Calculate statistics
        level_0 = sum(1 for r in run_records if r.classification_level == "LEVEL_0")
        level_1 = sum(1 for r in run_records if r.classification_level == "LEVEL_1")
        level_2 = sum(1 for r in run_records if r.classification_level == "LEVEL_2")
        level_3 = sum(1 for r in run_records if r.classification_level == "LEVEL_3")

        # Get champion
        champion = self.champion_tracker.get_champion()

        # Show summary
        logger.info("\n" + "=" * 60)
        logger.info("📋 LEARNING LOOP SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Iterations:     {total}")
        logger.info(f"This Run:             {run_count}")
        logger.info(f"")
        logger.info(f"Classification Breakdown:")
        logger.info(f"  LEVEL_0 (Failures):  {level_0} ({level_0/run_count*100:.1f}%)" if run_count > 0 else "  LEVEL_0: 0")
        logger.info(f"  LEVEL_1 (Executed):  {level_1} ({level_1/run_count*100:.1f}%)" if run_count > 0 else "  LEVEL_1: 0")
        logger.info(f"  LEVEL_2 (Weak):      {level_2} ({level_2/run_count*100:.1f}%)" if run_count > 0 else "  LEVEL_2: 0")
        logger.info(f"  LEVEL_3 (Success):   {level_3} ({level_3/run_count*100:.1f}%)" if run_count > 0 else "  LEVEL_3: 0")
        logger.info(f"")

        if champion:
            logger.info(f"🏆 Current Champion:")
            logger.info(f"  Iteration:     #{champion.iteration_num}")
            logger.info(f"  Method:        {champion.generation_method}")
            logger.info(f"  Sharpe Ratio:  {champion.metrics.get('sharpe_ratio', 'N/A')}")
            logger.info(f"  Total Return:  {champion.metrics.get('total_return', 'N/A')}")
        else:
            logger.info(f"🏆 No champion yet (no LEVEL_3 strategies)")

        logger.info("=" * 60)
        logger.info("✅ Learning Loop Complete")
        logger.info("=" * 60)
