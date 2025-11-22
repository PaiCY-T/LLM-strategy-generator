"""Unified Test Harness for UnifiedLoop testing with statistical analysis.

Provides infrastructure for long-running tests with checkpoint/resume capability,
comprehensive metrics tracking, and statistical validation of learning effects.

This test harness is compatible with ExtendedTestHarness API but uses UnifiedLoop
instead of AutonomousLoop, enabling Template Mode and JSON Parameter Output testing.
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sys
import os
import numpy as np
from scipy import stats
import time

# Add src to path for UnifiedLoop import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from src.learning.unified_loop import UnifiedLoop


class UnifiedTestHarness:
    """Test harness for UnifiedLoop with 50-200 iteration runs.

    Provides same API as ExtendedTestHarness but uses UnifiedLoop, enabling:
    - Template Mode testing
    - JSON Parameter Output mode testing
    - Learning Feedback integration testing
    - Automatic checkpointing for resume capability
    - Comprehensive metrics tracking (Sharpe ratios, durations, champion updates)
    - Statistical analysis (Cohen's d, significance tests, confidence intervals)
    - Production readiness assessment

    Attributes:
        model: LLM model identifier (e.g., 'gemini-2.5-flash')
        target_iterations: Total number of iterations to run (50-200)
        checkpoint_interval: Save checkpoint every N iterations (default: 10)
        checkpoint_dir: Directory for checkpoint files (default: 'checkpoints')
        template_mode: Whether to use Template Mode (default: False)
        template_name: Template to use (e.g., 'Momentum', 'Factor')
        use_json_mode: Whether to use JSON Parameter Output mode
        enable_learning: Whether to enable Learning Feedback (default: True)
        loop: UnifiedLoop instance for strategy generation and execution
        sharpes: List of Sharpe ratios per iteration
        durations: List of iteration execution durations in seconds
        champion_updates: List of boolean flags indicating champion updates per iteration
        iteration_records: List of complete iteration records for detailed analysis
        logger: Logger instance for test harness output
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        target_iterations: int = 50,
        checkpoint_interval: int = 10,
        checkpoint_dir: str = "checkpoints",
        template_mode: bool = False,
        template_name: str = "Momentum",
        use_json_mode: bool = False,
        enable_learning: bool = True,
        history_file: str = 'unified_iteration_history.jsonl',
        champion_file: str = 'unified_champion.json',
        **kwargs
    ):
        """Initialize Unified Test Harness.

        Args:
            model: LLM model to use for strategy generation
            target_iterations: Number of iterations to run (50-200)
            checkpoint_interval: Save checkpoint every N iterations
            checkpoint_dir: Directory path for checkpoint files
            template_mode: Enable Template Mode for parameter-based generation
            template_name: Name of template to use (e.g., 'Momentum', 'Factor')
            use_json_mode: Enable JSON Parameter Output mode
            enable_learning: Enable Learning Feedback integration
            history_file: Path to iteration history file
            champion_file: Path to champion file
            **kwargs: Additional parameters passed to UnifiedLoop
        """
        self.model = model
        self.target_iterations = target_iterations
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_dir = Path(checkpoint_dir)
        self.template_mode = template_mode
        self.template_name = template_name
        self.use_json_mode = use_json_mode
        self.enable_learning = enable_learning

        # Initialize UnifiedLoop instance
        self.loop = UnifiedLoop(
            model=self.model,
            max_iterations=target_iterations,
            template_mode=template_mode,
            template_name=template_name,
            use_json_mode=use_json_mode,
            enable_learning=enable_learning,
            history_file=history_file,
            champion_file=champion_file,
            **kwargs
        )

        # Initialize result tracking lists
        self.sharpes: List[float] = []
        self.durations: List[float] = []
        self.champion_updates: List[bool] = []
        self.iteration_records: List[Dict[str, Any]] = []

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

        # Create checkpoint directory if it doesn't exist
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"UnifiedTestHarness initialized:")
        self.logger.info(f"  Model: {self.model}")
        self.logger.info(f"  Target iterations: {self.target_iterations}")
        self.logger.info(f"  Template mode: {self.template_mode}")
        if self.template_mode:
            self.logger.info(f"  Template name: {self.template_name}")
            self.logger.info(f"  JSON mode: {self.use_json_mode}")
        self.logger.info(f"  Learning enabled: {self.enable_learning}")
        self.logger.info(f"  Checkpoint interval: {self.checkpoint_interval}")
        self.logger.info(f"  Checkpoint dir: {self.checkpoint_dir}")

    def _setup_logging(self) -> None:
        """Configure logging for test harness output.

        Sets up console and file logging with INFO level and timestamps.
        Creates logs directory if it doesn't exist.
        """
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        mode_suffix = "template" if self.template_mode else "standard"
        log_file = log_dir / f"unified_test_{mode_suffix}_{timestamp}.log"

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger.info(f"Logging initialized: {log_file}")

    def save_checkpoint(self, iteration: int) -> str:
        """Save checkpoint for current test state.

        Creates a JSON checkpoint file containing:
        - Current iteration number
        - Timestamp
        - All tracking metrics (Sharpe ratios, durations, champion updates)
        - Complete iteration records
        - Champion state (if available)
        - UnifiedLoop configuration (template_mode, use_json_mode, etc.)

        Args:
            iteration: Current iteration number

        Returns:
            str: Path to saved checkpoint file

        Raises:
            Exception: If checkpoint save fails (logged but not raised)
        """
        try:
            # Build checkpoint data structure
            checkpoint_data = {
                "iteration_number": iteration,
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "model": self.model,
                    "template_mode": self.template_mode,
                    "template_name": self.template_name,
                    "use_json_mode": self.use_json_mode,
                    "enable_learning": self.enable_learning
                },
                "sharpes": self.sharpes,
                "durations": self.durations,
                "champion_updates": self.champion_updates,
                "iteration_records": self.iteration_records,
                "champion_state": None
            }

            # Add champion state if available
            if self.loop.champion:
                checkpoint_data["champion_state"] = {
                    "sharpe": self.loop.champion.metrics.get("sharpe_ratio") if hasattr(self.loop.champion.metrics, 'get') else None,
                    "iteration": self.loop.champion.iteration_num,
                    "metrics": self.loop.champion.metrics if hasattr(self.loop.champion, 'metrics') else {}
                }

            # Create checkpoint filename
            checkpoint_file = self.checkpoint_dir / f"unified_checkpoint_iter_{iteration}.json"

            # Save to JSON file with formatting
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            self.logger.info(f"Checkpoint saved: {checkpoint_file}")
            self.logger.info(f"  Iteration: {iteration}")
            self.logger.info(f"  Metrics tracked: {len(self.sharpes)} Sharpe ratios, "
                           f"{len(self.durations)} durations")

            return str(checkpoint_file)

        except Exception as e:
            self.logger.error(f"Failed to save checkpoint at iteration {iteration}: {e}")
            # Don't raise - allow test to continue even if checkpoint fails
            return ""

    def load_checkpoint(self, filepath: str) -> int:
        """Load checkpoint and restore test state.

        Restores all tracking metrics and iteration records from a checkpoint file.
        Allows resuming a test from the saved iteration number.

        Args:
            filepath: Path to checkpoint JSON file

        Returns:
            int: Iteration number to resume from (next iteration after checkpoint)

        Raises:
            FileNotFoundError: If checkpoint file doesn't exist
            json.JSONDecodeError: If checkpoint file is corrupted
            KeyError: If checkpoint file is missing required fields
        """
        try:
            # Load checkpoint file
            with open(filepath, 'r') as f:
                checkpoint_data = json.load(f)

            # Validate required fields
            required_fields = ["iteration_number", "sharpes", "durations",
                             "champion_updates", "iteration_records"]
            missing_fields = [field for field in required_fields
                            if field not in checkpoint_data]
            if missing_fields:
                raise KeyError(f"Checkpoint missing required fields: {missing_fields}")

            # Restore tracking lists
            self.sharpes = checkpoint_data["sharpes"]
            self.durations = checkpoint_data["durations"]
            self.champion_updates = checkpoint_data["champion_updates"]
            self.iteration_records = checkpoint_data["iteration_records"]

            # Get iteration number to resume from
            iteration_number = checkpoint_data["iteration_number"]
            resume_from = iteration_number + 1

            # Log restoration details
            self.logger.info(f"Checkpoint loaded: {filepath}")
            self.logger.info(f"  Saved at iteration: {iteration_number}")
            self.logger.info(f"  Resuming from iteration: {resume_from}")
            self.logger.info(f"  Restored metrics: {len(self.sharpes)} Sharpe ratios, "
                           f"{len(self.durations)} durations")

            # Restore champion state if available
            if checkpoint_data.get("champion_state"):
                champion_state = checkpoint_data["champion_state"]
                if champion_state:
                    self.logger.info(f"  Champion Sharpe: {champion_state.get('sharpe')}")
                    self.logger.info(f"  Champion iteration: {champion_state.get('iteration')}")

            # Log config if available
            if checkpoint_data.get("config"):
                config = checkpoint_data["config"]
                self.logger.info(f"  Template mode: {config.get('template_mode')}")
                if config.get('template_mode'):
                    self.logger.info(f"  Template name: {config.get('template_name')}")
                    self.logger.info(f"  JSON mode: {config.get('use_json_mode')}")

            return resume_from

        except FileNotFoundError:
            self.logger.error(f"Checkpoint file not found: {filepath}")
            raise

        except json.JSONDecodeError as e:
            self.logger.error(f"Corrupted checkpoint file: {filepath} - {e}")
            raise

        except KeyError as e:
            self.logger.error(f"Invalid checkpoint format: {e}")
            raise

        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
            raise

    def calculate_cohens_d(self, sharpes: List[float]) -> Tuple[float, str]:
        """Calculate Cohen's d effect size for learning improvement.

        Compares first 10 and last 10 iterations to measure learning effect magnitude.
        Cohen's d measures standardized difference between two groups.

        Formula: d = (mean_last_10 - mean_first_10) / pooled_std
        where pooled_std = sqrt((std1² + std2²) / 2)

        Effect size interpretation:
        - |d| < 0.2: negligible
        - 0.2 <= |d| < 0.5: small
        - 0.5 <= |d| < 0.8: medium
        - |d| >= 0.8: large

        Args:
            sharpes: List of Sharpe ratios (minimum 20 required for 10+10 comparison)

        Returns:
            Tuple[float, str]: (cohen_d_value, interpretation)
                - cohen_d_value: Standardized effect size
                - interpretation: "negligible", "small", "medium", or "large"

        Raises:
            ValueError: If sharpes list has fewer than 20 values
        """
        if len(sharpes) < 20:
            raise ValueError(f"Need at least 20 Sharpe ratios for Cohen's d, got {len(sharpes)}")

        # Split into first 10 and last 10 iterations
        first_10 = sharpes[:10]
        last_10 = sharpes[-10:]

        # Calculate means
        mean1 = np.mean(first_10)
        mean2 = np.mean(last_10)

        # Calculate standard deviations
        std1 = np.std(first_10, ddof=1)  # ddof=1 for sample std
        std2 = np.std(last_10, ddof=1)

        # Calculate pooled standard deviation
        pooled_std = np.sqrt((std1**2 + std2**2) / 2)

        # Handle case where pooled_std is zero (no variance)
        if pooled_std == 0:
            self.logger.warning("Zero pooled standard deviation, returning d=0 (negligible)")
            return (0.0, "negligible")

        # Calculate Cohen's d
        cohens_d = (mean2 - mean1) / pooled_std

        # Interpret effect size
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            interpretation = "negligible"
        elif abs_d < 0.5:
            interpretation = "small"
        elif abs_d < 0.8:
            interpretation = "medium"
        else:
            interpretation = "large"

        self.logger.info(f"Cohen's d: {cohens_d:.3f} ({interpretation})")
        self.logger.info(f"  First 10 mean: {mean1:.3f}, Last 10 mean: {mean2:.3f}")
        self.logger.info(f"  Improvement: {mean2 - mean1:.3f}")

        return (cohens_d, interpretation)

    def calculate_significance(self, sharpes: List[float]) -> Tuple[float, bool, str]:
        """Calculate statistical significance of learning improvement using paired t-test.

        Compares first half vs second half of iterations to test if improvement
        is statistically significant. Uses paired t-test since iterations are
        sequential and dependent.

        Null hypothesis: No difference in mean Sharpe ratio between first and second half
        Alternative hypothesis: Mean Sharpe ratio improved in second half

        Args:
            sharpes: List of Sharpe ratios (minimum 4 required for meaningful test)

        Returns:
            Tuple[float, bool, str]: (p_value, is_significant, interpretation)
                - p_value: Probability of observing results under null hypothesis
                - is_significant: True if p < 0.05 (reject null hypothesis)
                - interpretation: Description of statistical significance

        Raises:
            ValueError: If sharpes list has fewer than 4 values
        """
        if len(sharpes) < 4:
            raise ValueError(f"Need at least 4 Sharpe ratios for significance test, got {len(sharpes)}")

        # Split into first half and second half
        midpoint = len(sharpes) // 2
        first_half = sharpes[:midpoint]
        second_half = sharpes[midpoint:]

        # Ensure equal length for paired t-test (trim longer half if needed)
        min_length = min(len(first_half), len(second_half))
        first_half = first_half[:min_length]
        second_half = second_half[:min_length]

        # Perform paired t-test (two-tailed)
        t_statistic, p_value = stats.ttest_rel(first_half, second_half)

        # Determine significance (alpha = 0.05)
        is_significant = p_value < 0.05

        # Interpret result
        if is_significant:
            if np.mean(second_half) > np.mean(first_half):
                interpretation = "Significant improvement detected (p < 0.05)"
            else:
                interpretation = "Significant decline detected (p < 0.05)"
        else:
            interpretation = "No significant change detected (p >= 0.05)"

        self.logger.info(f"Paired t-test: p-value={p_value:.4f}, significant={is_significant}")
        self.logger.info(f"  First half mean: {np.mean(first_half):.3f}")
        self.logger.info(f"  Second half mean: {np.mean(second_half):.3f}")
        self.logger.info(f"  {interpretation}")

        return (p_value, is_significant, interpretation)

    def calculate_confidence_intervals(self, sharpes: List[float]) -> Tuple[float, float]:
        """Calculate 95% confidence interval for mean Sharpe ratio.

        Uses t-distribution to estimate range containing true mean with 95% confidence.
        Accounts for sample size uncertainty using degrees of freedom.

        Formula: CI = mean ± t_critical * (std / sqrt(n))
        where t_critical is from t-distribution with df=n-1

        Args:
            sharpes: List of Sharpe ratios (minimum 2 required for CI calculation)

        Returns:
            Tuple[float, float]: (lower_bound, upper_bound)
                - lower_bound: Lower 95% confidence limit
                - upper_bound: Upper 95% confidence limit

        Raises:
            ValueError: If sharpes list has fewer than 2 values
        """
        if len(sharpes) < 2:
            raise ValueError(f"Need at least 2 Sharpe ratios for confidence intervals, got {len(sharpes)}")

        # Calculate mean and standard error
        mean = np.mean(sharpes)
        std = np.std(sharpes, ddof=1)  # Sample standard deviation
        n = len(sharpes)
        se = std / np.sqrt(n)

        # Calculate 95% confidence interval using t-distribution
        confidence = 0.95
        df = n - 1  # degrees of freedom

        # Get confidence interval from t-distribution
        lower_bound, upper_bound = stats.t.interval(
            confidence=confidence,
            df=df,
            loc=mean,
            scale=se
        )

        self.logger.info(f"95% Confidence Interval: [{lower_bound:.3f}, {upper_bound:.3f}]")
        self.logger.info(f"  Mean: {mean:.3f}, SE: {se:.3f}")
        self.logger.info(f"  Interval width: {upper_bound - lower_bound:.3f}")

        return (lower_bound, upper_bound)

    def generate_statistical_report(self) -> Dict[str, Any]:
        """Generate comprehensive statistical report with production readiness assessment.

        Aggregates all statistical metrics and determines if the system is ready for
        production based on three criteria:
        1. Statistical significance: p-value < 0.05
        2. Meaningful effect size: Cohen's d >= 0.4
        3. Convergence: rolling variance (last 10 iterations) < 0.5

        Production readiness requires ALL criteria to be met.

        Returns:
            Dict[str, Any]: Comprehensive report containing:
                - sample_size: Number of iterations
                - mean_sharpe: Average Sharpe ratio
                - std_sharpe: Standard deviation of Sharpe ratios
                - min_sharpe: Minimum Sharpe ratio
                - max_sharpe: Maximum Sharpe ratio
                - cohens_d: Effect size value
                - effect_size_interpretation: "negligible", "small", "medium", or "large"
                - p_value: Statistical significance probability
                - is_significant: True if p < 0.05
                - confidence_interval_95: (lower_bound, upper_bound)
                - rolling_variance: Std of last 10 iterations
                - convergence_achieved: True if rolling_variance < 0.5
                - production_ready: True if all criteria met
                - readiness_reasoning: List of reasons for readiness decision
                - champion_update_frequency: Percentage of iterations with champion updates
                - avg_duration_per_iteration: Average time per iteration in seconds

        Raises:
            ValueError: If insufficient data for statistical analysis
        """
        if len(self.sharpes) < 20:
            raise ValueError(f"Need at least 20 iterations for comprehensive report, got {len(self.sharpes)}")

        self.logger.info("=" * 70)
        self.logger.info("GENERATING STATISTICAL REPORT")
        self.logger.info("=" * 70)

        # Calculate basic statistics
        mean_sharpe = np.mean(self.sharpes)
        std_sharpe = np.std(self.sharpes, ddof=1)
        min_sharpe = np.min(self.sharpes)
        max_sharpe = np.max(self.sharpes)

        self.logger.info(f"Basic Statistics:")
        self.logger.info(f"  Sample size: {len(self.sharpes)}")
        self.logger.info(f"  Mean Sharpe: {mean_sharpe:.3f}")
        self.logger.info(f"  Std Sharpe: {std_sharpe:.3f}")
        self.logger.info(f"  Range: [{min_sharpe:.3f}, {max_sharpe:.3f}]")

        # Calculate statistical metrics
        self.logger.info("\nStatistical Analysis:")
        cohens_d, effect_size_interpretation = self.calculate_cohens_d(self.sharpes)
        p_value, is_significant, sig_interpretation = self.calculate_significance(self.sharpes)
        ci_lower, ci_upper = self.calculate_confidence_intervals(self.sharpes)

        # Calculate rolling variance (standard deviation of last 10 iterations)
        rolling_variance = np.std(self.sharpes[-10:], ddof=1)
        convergence_achieved = rolling_variance < 0.5

        self.logger.info(f"\nConvergence Analysis:")
        self.logger.info(f"  Rolling variance (last 10): {rolling_variance:.3f}")
        self.logger.info(f"  Convergence threshold: 0.5")
        self.logger.info(f"  Convergence achieved: {convergence_achieved}")

        # Determine production readiness based on three criteria
        criteria_met = []
        criteria_failed = []

        # Criterion 1: Statistical significance (p < 0.05)
        if is_significant and p_value < 0.05:
            criteria_met.append("Statistical significance: p-value < 0.05")
        else:
            criteria_failed.append(f"Statistical significance NOT met: p-value = {p_value:.4f} >= 0.05")

        # Criterion 2: Meaningful effect size (Cohen's d >= 0.4)
        if cohens_d >= 0.4:
            criteria_met.append(f"Meaningful effect size: Cohen's d = {cohens_d:.3f} >= 0.4")
        else:
            criteria_failed.append(f"Effect size too small: Cohen's d = {cohens_d:.3f} < 0.4")

        # Criterion 3: Convergence (rolling variance < 0.5)
        if convergence_achieved:
            criteria_met.append(f"Convergence achieved: rolling variance = {rolling_variance:.3f} < 0.5")
        else:
            criteria_failed.append(f"Convergence NOT achieved: rolling variance = {rolling_variance:.3f} >= 0.5")

        # Production ready if ALL criteria are met
        production_ready = len(criteria_failed) == 0

        # Build readiness reasoning
        readiness_reasoning = []
        if production_ready:
            readiness_reasoning.append("READY FOR PRODUCTION: All criteria met")
            readiness_reasoning.extend(criteria_met)
        else:
            readiness_reasoning.append("NOT READY FOR PRODUCTION: Some criteria failed")
            readiness_reasoning.extend(criteria_failed)
            if criteria_met:
                readiness_reasoning.append("Criteria met:")
                readiness_reasoning.extend(criteria_met)

        # Log production readiness assessment
        self.logger.info("\n" + "=" * 70)
        self.logger.info("PRODUCTION READINESS ASSESSMENT")
        self.logger.info("=" * 70)
        for reason in readiness_reasoning:
            self.logger.info(f"  {reason}")

        # Calculate additional metrics
        champion_update_frequency = (sum(self.champion_updates) / len(self.champion_updates) * 100
                                     if self.champion_updates else 0.0)
        avg_duration = np.mean(self.durations) if self.durations else 0.0

        self.logger.info(f"\nAdditional Metrics:")
        self.logger.info(f"  Champion update frequency: {champion_update_frequency:.1f}%")
        self.logger.info(f"  Avg duration per iteration: {avg_duration:.2f}s")

        # Build comprehensive report
        report = {
            'sample_size': len(self.sharpes),
            'mean_sharpe': float(mean_sharpe),
            'std_sharpe': float(std_sharpe),
            'min_sharpe': float(min_sharpe),
            'max_sharpe': float(max_sharpe),
            'cohens_d': float(cohens_d),
            'effect_size_interpretation': effect_size_interpretation,
            'p_value': float(p_value),
            'is_significant': bool(is_significant),
            'confidence_interval_95': (float(ci_lower), float(ci_upper)),
            'rolling_variance': float(rolling_variance),
            'convergence_achieved': bool(convergence_achieved),
            'production_ready': bool(production_ready),
            'readiness_reasoning': readiness_reasoning,
            'champion_update_frequency': float(champion_update_frequency),
            'avg_duration_per_iteration': float(avg_duration)
        }

        self.logger.info("\n" + "=" * 70)
        self.logger.info("STATISTICAL REPORT COMPLETE")
        self.logger.info("=" * 70)

        return report

    def run_test(
        self,
        resume_from_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute long test run with automatic checkpointing.

        Main test execution method that orchestrates:
        - Multi-iteration test runs (50-200 iterations)
        - Automatic checkpointing every N iterations
        - Comprehensive metrics tracking (Sharpe ratios, durations, champion updates)
        - Statistical analysis and production readiness assessment

        Note: UnifiedLoop handles the iteration execution internally via run() method,
        unlike AutonomousLoop which requires calling run_iteration() per iteration.

        Args:
            resume_from_checkpoint: Optional path to checkpoint file for resuming test

        Returns:
            Dict[str, Any]: Comprehensive results containing:
                - test_completed: True if test finished successfully
                - total_iterations: Number of iterations executed
                - sharpes: List of Sharpe ratios per iteration
                - durations: List of execution durations per iteration
                - champion_updates: List of boolean flags for champion updates
                - statistical_report: Complete statistical analysis report
                - final_checkpoint: Path to final checkpoint file
                - success_rate: Percentage of successful iterations
                - best_sharpe: Highest Sharpe ratio achieved
                - avg_sharpe: Average Sharpe ratio

        Raises:
            Exception: Critical failures that prevent test completion
        """
        # Initialize test state
        start_iteration = 0

        # Resume from checkpoint if provided
        if resume_from_checkpoint:
            self.logger.info("=" * 70)
            self.logger.info("RESUMING TEST FROM CHECKPOINT")
            self.logger.info("=" * 70)
            try:
                start_iteration = self.load_checkpoint(resume_from_checkpoint)
                self.logger.info(f"✅ Checkpoint restored successfully")
                self.logger.info(f"   Resuming from iteration: {start_iteration}")
            except Exception as e:
                self.logger.error(f"❌ Failed to load checkpoint: {e}")
                self.logger.error("Starting fresh test run instead")
                start_iteration = 0
                # Clear any partial state
                self.sharpes = []
                self.durations = []
                self.champion_updates = []
                self.iteration_records = []
        else:
            self.logger.info("=" * 70)
            self.logger.info("STARTING UNIFIED TEST RUN")
            self.logger.info("=" * 70)

        # Log test configuration
        self.logger.info(f"Configuration:")
        self.logger.info(f"  Model: {self.model}")
        self.logger.info(f"  Target iterations: {self.target_iterations}")
        self.logger.info(f"  Template mode: {self.template_mode}")
        if self.template_mode:
            self.logger.info(f"  Template name: {self.template_name}")
            self.logger.info(f"  JSON mode: {self.use_json_mode}")
        self.logger.info(f"  Learning enabled: {self.enable_learning}")
        self.logger.info(f"  Start iteration: {start_iteration}")
        self.logger.info(f"  Checkpoint interval: {self.checkpoint_interval}")
        self.logger.info("")

        # Execute UnifiedLoop
        test_start_time = time.time()

        try:
            # Run UnifiedLoop (handles all iterations internally)
            self.logger.info("Starting UnifiedLoop.run()...")
            result = self.loop.run()

            # Extract iteration history
            history_records = self.loop.history.get_all()

            # Process each iteration record
            for record in history_records:
                # Extract Sharpe ratio
                sharpe = 0.0
                if hasattr(record, 'metrics'):
                    if hasattr(record.metrics, 'sharpe_ratio'):
                        sharpe = record.metrics.sharpe_ratio
                    elif isinstance(record.metrics, dict):
                        sharpe = record.metrics.get('sharpe_ratio', 0.0)

                # Track metrics
                self.sharpes.append(sharpe)
                self.durations.append(0.0)  # UnifiedLoop doesn't track per-iteration duration yet

                # Check if this iteration updated champion
                champion_updated = (
                    hasattr(record, 'champion_updated') and record.champion_updated
                ) or False
                self.champion_updates.append(champion_updated)

                # Store iteration record
                self.iteration_records.append({
                    'iteration': record.iteration_num,
                    'sharpe': sharpe,
                    'champion_updated': champion_updated,
                    'classification_level': record.classification_level if hasattr(record, 'classification_level') else None
                })

                # Save checkpoint at intervals
                if (record.iteration_num + 1) % self.checkpoint_interval == 0:
                    self.logger.info(f"\n📁 Saving checkpoint at iteration {record.iteration_num}...")
                    checkpoint_path = self.save_checkpoint(record.iteration_num)
                    if checkpoint_path:
                        self.logger.info(f"✅ Checkpoint saved: {checkpoint_path}")

        except Exception as e:
            self.logger.error(f"❌ Test run failed: {e}", exc_info=True)
            raise

        # Test completed
        test_duration = time.time() - test_start_time

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("UNIFIED TEST RUN - COMPLETE")
        self.logger.info("=" * 70)
        self.logger.info(f"Total duration: {test_duration:.1f}s ({test_duration/60:.1f}m)")
        self.logger.info(f"Total iterations: {len(self.sharpes)}")

        # Calculate statistics
        successful_sharpes = [s for s in self.sharpes if s > 0]
        success_rate = (len(successful_sharpes) / len(self.sharpes) * 100) if self.sharpes else 0.0
        best_sharpe = max(successful_sharpes) if successful_sharpes else 0.0
        avg_sharpe = (sum(successful_sharpes) / len(successful_sharpes)) if successful_sharpes else 0.0

        self.logger.info(f"Success rate: {success_rate:.1f}%")
        self.logger.info(f"Best Sharpe: {best_sharpe:.4f}")
        self.logger.info(f"Avg Sharpe: {avg_sharpe:.4f}")

        # Champion summary
        if self.loop.champion:
            champion_sharpe = (
                self.loop.champion.metrics.sharpe_ratio
                if hasattr(self.loop.champion.metrics, 'sharpe_ratio')
                else self.loop.champion.metrics.get('sharpe_ratio', 0.0)
            )
            self.logger.info("")
            self.logger.info(f"🏆 FINAL CHAMPION: Iteration {self.loop.champion.iteration_num}")
            self.logger.info(f"   Sharpe: {champion_sharpe:.4f}")
            self.logger.info(f"   Champion updates: {sum(self.champion_updates)}")

        # Generate statistical report (if enough data)
        statistical_report = None
        if len(self.sharpes) >= 20:
            try:
                self.logger.info("")
                statistical_report = self.generate_statistical_report()
                self.logger.info("✅ Statistical report generated")
            except Exception as e:
                self.logger.error(f"❌ Statistical report generation failed: {e}", exc_info=True)
                statistical_report = {'error': str(e)}
        else:
            self.logger.warning(f"Insufficient data for statistical report (need ≥20, got {len(self.sharpes)})")
            statistical_report = {
                'error': f'Insufficient data: need at least 20 iterations, got {len(self.sharpes)}'
            }

        # Save final checkpoint
        self.logger.info("")
        self.logger.info("📁 Saving final checkpoint...")
        final_checkpoint = self.save_checkpoint(len(self.sharpes) - 1)
        if final_checkpoint:
            self.logger.info(f"✅ Final checkpoint saved: {final_checkpoint}")

        # Build comprehensive results
        results = {
            'test_completed': True,
            'total_iterations': len(self.sharpes),
            'sharpes': self.sharpes,
            'durations': self.durations,
            'champion_updates': self.champion_updates,
            'statistical_report': statistical_report,
            'final_checkpoint': final_checkpoint,
            'success_rate': success_rate,
            'best_sharpe': best_sharpe,
            'avg_sharpe': avg_sharpe,
            'total_duration_seconds': test_duration,
            'template_mode': self.template_mode,
            'use_json_mode': self.use_json_mode
        }

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("TEST COMPLETE - RESULTS SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Test completed: {results['test_completed']}")
        self.logger.info(f"Total iterations: {results['total_iterations']}")
        self.logger.info(f"Success rate: {results['success_rate']:.1f}%")
        self.logger.info(f"Best Sharpe: {results['best_sharpe']:.4f}")
        self.logger.info(f"Avg Sharpe: {results['avg_sharpe']:.4f}")
        if statistical_report and not statistical_report.get('error'):
            self.logger.info(f"Production ready: {statistical_report.get('production_ready', False)}")
        self.logger.info("=" * 70)

        return results
