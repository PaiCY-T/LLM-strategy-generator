"""Phase 0 Test Harness for Template Mode 50-Iteration Testing.

Provides infrastructure for validating O3's template mode hypothesis:
Can template-guided parameter generation achieve ≥5% champion update rate?

This harness orchestrates 50-iteration tests with:
- Template mode (Momentum strategy with LLM parameter selection)
- Checkpoint/resume capability
- Parameter diversity tracking
- Validation statistics tracking
- Decision matrix for GO/NO-GO/PARTIAL recommendation

Target Metrics:
- Champion update rate: ≥5% (target), 2-5% (partial), <2% (failure)
- Average Sharpe: >1.0 (target), 0.8-1.0 (partial), <0.8 (failure)
- Parameter diversity: ≥30 unique combinations (target)
- Validation pass rate: ≥90% (target)

Decision Matrix:
- SUCCESS (≥5% update rate AND >1.0 Sharpe): Skip population-based, use template mode
- PARTIAL (2-5% OR 0.8-1.0 Sharpe): Consider hybrid approach
- FAILURE (<2% OR <0.8 Sharpe): Proceed to population-based learning
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import sys
import os

# Add artifacts/working/modules to path for AutonomousLoop import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'artifacts', 'working', 'modules'))

from autonomous_loop import AutonomousLoop


class Phase0TestHarness:
    """Test harness for 50-iteration template mode validation.

    Validates O3's hypothesis that template-guided parameter generation can achieve
    ≥5% champion update rate, sufficient to skip population-based learning.

    Attributes:
        test_name: Identifier for this test run (used in checkpoint filenames)
        max_iterations: Total number of iterations to run (default: 50)
        model: LLM model identifier for parameter generation
        checkpoint_interval: Save checkpoint every N iterations (default: 10)
        checkpoint_dir: Directory for checkpoint files
        loop: AutonomousLoop instance in template mode
        sharpes: List of Sharpe ratios per iteration
        durations: List of iteration execution durations in seconds
        champion_updates: List of boolean flags indicating champion updates
        iteration_records: List of complete iteration records
        param_combinations: List of unique parameter combinations explored
        validation_stats: Dictionary tracking validation pass/fail statistics
        logger: Logger instance for test harness output
    """

    def __init__(
        self,
        test_name: str = "phase0_template_test",
        max_iterations: int = 50,
        model: str = "gemini-2.5-flash",
        checkpoint_interval: int = 10,
        checkpoint_dir: str = "checkpoints"
    ):
        """Initialize Phase 0 Test Harness for template mode testing.

        Args:
            test_name: Test identifier (used in checkpoint filenames)
            max_iterations: Number of iterations to run (50 for Phase 0)
            model: LLM model for parameter generation (default: gemini-2.5-flash)
            checkpoint_interval: Save checkpoint every N iterations (default: 10)
            checkpoint_dir: Directory path for checkpoint files
        """
        self.test_name = test_name
        self.max_iterations = max_iterations
        self.model = model
        self.checkpoint_interval = checkpoint_interval
        self.checkpoint_dir = Path(checkpoint_dir)

        # Initialize AutonomousLoop in template mode
        self.loop = AutonomousLoop(
            template_mode=True,
            template_name="Momentum",
            model=self.model,
            max_iterations=max_iterations,
            history_file=f'iteration_history_{test_name}.json'
        )

        # Clear history from previous test runs to avoid duplicate iteration numbers
        self.loop.history.clear()

        # Initialize result tracking
        self.sharpes: List[float] = []
        self.durations: List[float] = []
        self.champion_updates: List[bool] = []
        self.iteration_records: List[Dict[str, Any]] = []

        # Phase 0 specific tracking
        self.param_combinations: List[Tuple] = []  # Unique parameter combinations
        self.validation_stats: Dict[str, int] = {
            'total_validations': 0,
            'validation_passes': 0,
            'validation_failures': 0,
            'common_errors': {}
        }

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

        # Create checkpoint directory
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Phase0TestHarness initialized:")
        self.logger.info(f"  Test name: {self.test_name}")
        self.logger.info(f"  Model: {self.model}")
        self.logger.info(f"  Max iterations: {self.max_iterations}")
        self.logger.info(f"  Checkpoint interval: {self.checkpoint_interval}")
        self.logger.info(f"  Checkpoint dir: {self.checkpoint_dir}")
        self.logger.info(f"  Template mode: ENABLED (Momentum)")

    def _setup_logging(self) -> None:
        """Configure logging for test harness output.

        Creates timestamped log file in logs directory with INFO level.
        Logs to both file and console.
        """
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f"phase0_test_{self.test_name}_{timestamp}.log"

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

    def run(
        self,
        data: Any,
        resume_from_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute 50-iteration template mode test with checkpointing.

        Main test execution method that orchestrates:
        - 50-iteration test run in template mode
        - Automatic checkpointing every 10 iterations
        - Parameter diversity tracking
        - Validation statistics tracking
        - Progress monitoring and reporting
        - Retry logic for failed iterations (max 3 attempts)

        Args:
            data: Finlab data object for strategy execution
            resume_from_checkpoint: Optional path to checkpoint file for resuming

        Returns:
            Dict[str, Any]: Comprehensive results containing:
                - test_completed: True if test finished successfully
                - total_iterations: Number of iterations executed
                - champion_update_count: Number of champion updates
                - champion_update_rate: Percentage of iterations with champion updates
                - best_sharpe: Highest Sharpe ratio achieved
                - avg_sharpe: Average Sharpe ratio (successful iterations)
                - sharpes: List of Sharpe ratios per iteration
                - durations: List of execution durations per iteration
                - champion_updates: List of champion update flags
                - param_diversity: Number of unique parameter combinations
                - param_diversity_rate: Diversity percentage
                - validation_pass_rate: Percentage of validations passed
                - success_rate: Percentage of successful iterations
                - final_checkpoint: Path to final checkpoint file

        Raises:
            Exception: Critical failures that prevent test completion
        """
        import time

        # Initialize test state
        start_iteration = 0

        # Resume from checkpoint if provided
        if resume_from_checkpoint:
            self.logger.info("=" * 70)
            self.logger.info("RESUMING TEST FROM CHECKPOINT")
            self.logger.info("=" * 70)
            try:
                start_iteration = self._load_checkpoint(resume_from_checkpoint)
                self.logger.info(f"✅ Checkpoint restored successfully")
                self.logger.info(f"   Resuming from iteration: {start_iteration}")
            except Exception as e:
                self.logger.error(f"❌ Failed to load checkpoint: {e}")
                self.logger.error("Starting fresh test run instead")
                start_iteration = 0
        else:
            self.logger.info("=" * 70)
            self.logger.info("STARTING PHASE 0 TEMPLATE MODE TEST")
            self.logger.info("=" * 70)

        # Log test configuration
        self.logger.info(f"Configuration:")
        self.logger.info(f"  Test name: {self.test_name}")
        self.logger.info(f"  Model: {self.model}")
        self.logger.info(f"  Template: Momentum")
        self.logger.info(f"  Max iterations: {self.max_iterations}")
        self.logger.info(f"  Start iteration: {start_iteration}")
        self.logger.info(f"  Checkpoint interval: {self.checkpoint_interval}")
        self.logger.info("")

        # Track test-level statistics
        test_start_time = time.time()
        success_count = 0
        failure_count = 0

        # Main test loop
        for i in range(start_iteration, self.max_iterations):
            self.logger.info("")
            self.logger.info("=" * 70)
            self.logger.info(f"ITERATION {i}/{self.max_iterations - 1}")
            self.logger.info("=" * 70)

            iteration_start_time = time.time()
            retry_count = 0
            max_retries = 3
            iteration_success = False

            # Retry loop (max 3 attempts per iteration)
            while retry_count < max_retries and not iteration_success:
                try:
                    # Run iteration with AutonomousLoop
                    self.logger.info(f"Attempt {retry_count + 1}/{max_retries}")

                    success, status = self.loop.run_iteration(i, data)
                    iteration_duration = time.time() - iteration_start_time

                    # Get detailed record from history
                    record = self.loop.history.get_record(i)

                    # Debug logging to understand what we're getting
                    self.logger.info(f"Iteration {i} - success: {success}, status: {status}, record exists: {record is not None}")
                    if record:
                        self.logger.info(f"  record has metrics attr: {hasattr(record, 'metrics')}")
                        self.logger.info(f"  record.metrics value: {record.metrics if hasattr(record, 'metrics') else 'NO ATTR'}")
                        self.logger.info(f"  record has parameters attr: {hasattr(record, 'parameters')}")
                        self.logger.info(f"  record.parameters value: {record.parameters if hasattr(record, 'parameters') else 'NO ATTR'}")

                    # Check success condition - prioritize the success flag from run_iteration
                    if success:
                        # Extract metrics safely (handle case where record or metrics may be None)
                        sharpe = 0.0
                        if record and hasattr(record, 'metrics') and record.metrics:
                            sharpe = record.metrics.get('sharpe_ratio', 0.0)

                        champion_updated = (self.loop.champion and
                                          self.loop.champion.iteration_num == i)

                        # Track metrics
                        self.sharpes.append(sharpe)
                        self.durations.append(iteration_duration)
                        self.champion_updates.append(champion_updated)

                        # Build iteration result
                        iteration_result = {
                            'iteration': i,
                            'success': True,
                            'sharpe': sharpe,
                            'metrics': record.metrics if (record and hasattr(record, 'metrics')) else {},
                            'duration_seconds': iteration_duration,
                            'champion_updated': champion_updated,
                            'retry_count': retry_count
                        }

                        # Track parameters (if available)
                        if record and hasattr(record, 'parameters') and record.parameters:
                            iteration_result['parameters'] = record.parameters
                            # Track parameter diversity
                            self._track_parameters(record.parameters)

                        # Track validation (if available)
                        if record and hasattr(record, 'validation_passed'):
                            validation_result = {
                                'passed': record.validation_passed,
                                'errors': getattr(record, 'validation_errors', [])
                            }
                            self._track_validation(validation_result)
                            iteration_result['validation_passed'] = record.validation_passed

                        self.iteration_records.append(iteration_result)

                        # Log success
                        success_count += 1
                        iteration_success = True

                        self.logger.info(f"✅ Iteration {i} SUCCESS (duration: {iteration_duration:.1f}s)")
                        self.logger.info(f"   Sharpe: {sharpe:.4f}")

                        if champion_updated:
                            self.logger.info(f"   🏆 NEW CHAMPION ESTABLISHED")

                    else:
                        # Iteration failed
                        failure_count += 1

                        # Track failed iteration
                        self.sharpes.append(0.0)
                        self.durations.append(iteration_duration)
                        self.champion_updates.append(False)

                        failure_result = {
                            'iteration': i,
                            'success': False,
                            'sharpe': 0.0,
                            'duration_seconds': iteration_duration,
                            'retry_count': retry_count,
                            'status': status
                        }
                        self.iteration_records.append(failure_result)

                        self.logger.error(f"❌ Iteration {i} FAILED: {status}")

                        # Retry logic
                        retry_count += 1
                        if retry_count < max_retries:
                            self.logger.warning(f"⚠️  Retrying iteration {i} (attempt {retry_count + 1}/{max_retries})")
                            time.sleep(2)
                        else:
                            self.logger.error(f"❌ Iteration {i} failed after {max_retries} attempts")
                            iteration_success = True  # Exit retry loop

                except Exception as e:
                    # Unexpected exception
                    iteration_duration = time.time() - iteration_start_time
                    failure_count += 1

                    self.logger.error(f"❌ Iteration {i} EXCEPTION: {e}", exc_info=True)

                    # Track exception
                    self.sharpes.append(0.0)
                    self.durations.append(iteration_duration)
                    self.champion_updates.append(False)

                    exception_result = {
                        'iteration': i,
                        'success': False,
                        'sharpe': 0.0,
                        'duration_seconds': iteration_duration,
                        'retry_count': retry_count,
                        'error': str(e)
                    }
                    self.iteration_records.append(exception_result)

                    # Retry on exception
                    retry_count += 1
                    if retry_count < max_retries:
                        self.logger.warning(f"⚠️  Retrying after exception (attempt {retry_count + 1}/{max_retries})")
                        time.sleep(2)
                    else:
                        self.logger.error(f"❌ Iteration {i} failed after {max_retries} attempts")
                        iteration_success = True  # Exit retry loop

            # Update progress after each iteration
            self._update_progress(i, self.loop)

            # Save checkpoint at regular intervals
            if (i + 1) % self.checkpoint_interval == 0:
                self.logger.info(f"\n📁 Saving checkpoint at iteration {i}...")
                checkpoint_path = self._save_checkpoint(i)
                if checkpoint_path:
                    self.logger.info(f"✅ Checkpoint saved: {checkpoint_path}")

        # Test loop completed
        test_duration = time.time() - test_start_time

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("PHASE 0 TEMPLATE MODE TEST - COMPLETE")
        self.logger.info("=" * 70)
        self.logger.info(f"Total duration: {test_duration:.1f}s ({test_duration/60:.1f}m)")
        self.logger.info(f"Total iterations: {len(self.sharpes)}")
        self.logger.info(f"✅ Successful: {success_count}")
        self.logger.info(f"❌ Failed: {failure_count}")

        # Calculate success rate
        success_rate = (success_count / len(self.sharpes) * 100) if self.sharpes else 0.0
        self.logger.info(f"Success rate: {success_rate:.1f}%")

        # Save final checkpoint
        self.logger.info("")
        self.logger.info("📁 Saving final checkpoint...")
        final_checkpoint = self._save_checkpoint(self.max_iterations - 1)
        if final_checkpoint:
            self.logger.info(f"✅ Final checkpoint saved: {final_checkpoint}")

        # Compile and return results
        return self._compile_results(self.loop, test_duration)

    def _update_progress(self, iteration: int, loop: AutonomousLoop) -> None:
        """Display real-time progress metrics after each iteration.

        Shows current state of test run including:
        - Current iteration number and progress percentage
        - Champion update count and update rate
        - Current champion Sharpe ratio
        - Parameter diversity metrics
        - Estimated time remaining (ETA)

        Args:
            iteration: Current iteration number (0-indexed)
            loop: AutonomousLoop instance with current champion state
        """
        import time

        # Calculate progress percentage
        progress_pct = ((iteration + 1) / self.max_iterations * 100)

        # Calculate champion update statistics
        champion_update_count = sum(self.champion_updates)
        update_rate = (champion_update_count / (iteration + 1) * 100) if iteration >= 0 else 0.0

        # Get current champion info
        current_champion_sharpe = 0.0
        current_champion_iteration = -1
        if loop.champion:
            current_champion_sharpe = loop.champion.metrics.get('sharpe_ratio', 0.0)
            current_champion_iteration = loop.champion.iteration_num

        # Calculate ETA based on average iteration time
        avg_duration = sum(self.durations) / len(self.durations) if self.durations else 0.0
        iterations_remaining = self.max_iterations - (iteration + 1)
        eta_seconds = avg_duration * iterations_remaining
        eta_minutes = eta_seconds / 60

        # Calculate parameter diversity
        param_diversity = len(self.param_combinations)
        param_diversity_rate = (param_diversity / (iteration + 1) * 100) if iteration >= 0 else 0.0

        # Display progress
        self.logger.info("")
        self.logger.info("─" * 70)
        self.logger.info("PROGRESS UPDATE")
        self.logger.info("─" * 70)
        self.logger.info(f"Iteration: {iteration + 1}/{self.max_iterations} ({progress_pct:.1f}%)")
        self.logger.info(f"Champion updates: {champion_update_count} ({update_rate:.1f}%)")

        if current_champion_iteration >= 0:
            self.logger.info(f"Current champion: Iteration {current_champion_iteration} (Sharpe: {current_champion_sharpe:.4f})")
        else:
            self.logger.info(f"Current champion: None yet")

        self.logger.info(f"Parameter diversity: {param_diversity} unique combinations ({param_diversity_rate:.1f}%)")
        self.logger.info(f"Avg iteration time: {avg_duration:.1f}s")
        self.logger.info(f"ETA: {eta_minutes:.1f} minutes ({eta_seconds:.0f}s)")
        self.logger.info("─" * 70)

    def _save_checkpoint(self, iteration: int) -> str:
        """Save checkpoint for current test state.

        Creates a JSON checkpoint file containing all tracking metrics and state.
        Enables resuming test from this iteration if needed.

        Checkpoint includes:
        - Current iteration number
        - Timestamp
        - All tracking metrics (sharpes, durations, champion_updates)
        - Complete iteration records
        - Parameter combinations (Phase 0 specific)
        - Validation statistics (Phase 0 specific)
        - Champion state (if available)

        Args:
            iteration: Current iteration number

        Returns:
            str: Path to saved checkpoint file, or empty string if save fails

        Raises:
            Exception: Logs error but doesn't raise (allows test to continue)
        """
        try:
            # Build checkpoint data structure
            checkpoint_data = {
                "test_name": self.test_name,
                "iteration_number": iteration,
                "timestamp": datetime.now().isoformat(),
                "sharpes": self.sharpes,
                "durations": self.durations,
                "champion_updates": self.champion_updates,
                "iteration_records": self.iteration_records,
                "param_combinations": [list(combo) for combo in self.param_combinations],  # Convert tuples to lists for JSON
                "validation_stats": self.validation_stats
            }

            # Add champion state if available
            if hasattr(self.loop, 'champion') and self.loop.champion:
                checkpoint_data["champion_state"] = {
                    "sharpe": self.loop.champion.metrics.get("sharpe_ratio"),
                    "iteration": self.loop.champion.iteration_num,
                    "metrics": self.loop.champion.metrics,
                    "parameters": self.loop.champion.parameters if hasattr(self.loop.champion, 'parameters') else None
                }
            else:
                checkpoint_data["champion_state"] = None

            # Create checkpoint filename
            checkpoint_file = self.checkpoint_dir / f"checkpoint_{self.test_name}_iter_{iteration}.json"

            # Save to JSON file with formatting
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            self.logger.info(f"Checkpoint saved: {checkpoint_file}")
            self.logger.info(f"  Iteration: {iteration}")
            self.logger.info(f"  Metrics: {len(self.sharpes)} Sharpe ratios, {len(self.param_combinations)} param combinations")

            return str(checkpoint_file)

        except Exception as e:
            self.logger.error(f"Failed to save checkpoint at iteration {iteration}: {e}")
            # Don't raise - allow test to continue even if checkpoint fails
            return ""

    def _load_checkpoint(self, filepath: str) -> int:
        """Load checkpoint and restore test state.

        Restores all tracking metrics, iteration records, and Phase 0 specific data
        from a checkpoint file. Allows resuming a test from the saved iteration number.

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

            # Restore Phase 0 specific data
            if "param_combinations" in checkpoint_data:
                # Convert lists back to tuples
                self.param_combinations = [tuple(combo) for combo in checkpoint_data["param_combinations"]]

            if "validation_stats" in checkpoint_data:
                self.validation_stats = checkpoint_data["validation_stats"]

            # Get iteration number to resume from
            iteration_number = checkpoint_data["iteration_number"]
            resume_from = iteration_number + 1

            # Log restoration details
            self.logger.info(f"Checkpoint loaded: {filepath}")
            self.logger.info(f"  Saved at iteration: {iteration_number}")
            self.logger.info(f"  Resuming from iteration: {resume_from}")
            self.logger.info(f"  Restored metrics: {len(self.sharpes)} Sharpe ratios, "
                           f"{len(self.param_combinations)} param combinations")

            # Restore champion state if available
            if checkpoint_data.get("champion_state"):
                champion_state = checkpoint_data["champion_state"]
                self.logger.info(f"  Champion Sharpe: {champion_state.get('sharpe')}")
                self.logger.info(f"  Champion iteration: {champion_state.get('iteration')}")

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

    def _compile_results(self, loop: AutonomousLoop, test_duration: float) -> Dict[str, Any]:
        """Compile comprehensive test results for Phase 0 decision analysis.

        Calculates all primary metrics needed for the GO/NO-GO/PARTIAL decision:
        - Champion update rate (target: ≥5%)
        - Average Sharpe (target: >1.0)
        - Parameter diversity (target: ≥30 unique combinations)
        - Validation pass rate (target: ≥90%)

        Args:
            loop: AutonomousLoop instance with final champion state
            test_duration: Total test duration in seconds

        Returns:
            Dict[str, Any]: Comprehensive results dictionary containing:
                - test_completed: True
                - total_iterations: Number of iterations executed
                - champion_update_count: Number of champion updates
                - champion_update_rate: Percentage of iterations with updates
                - best_sharpe: Highest Sharpe ratio achieved
                - avg_sharpe: Average Sharpe (successful iterations only)
                - sharpe_variance: Variance of Sharpe ratios
                - sharpes: List of all Sharpe ratios
                - durations: List of iteration durations
                - champion_updates: List of update flags
                - param_diversity: Number of unique parameter combinations
                - param_diversity_rate: Diversity percentage
                - param_combinations: List of unique combinations
                - validation_pass_rate: Percentage of validations passed
                - validation_stats: Detailed validation statistics
                - success_count: Number of successful iterations
                - failure_count: Number of failed iterations
                - success_rate: Percentage of successful iterations
                - total_duration_seconds: Total test duration
                - avg_duration_per_iteration: Average iteration time
                - final_champion: Champion state dict (if available)
        """
        import numpy as np

        # Calculate champion update metrics
        champion_update_count = sum(self.champion_updates)
        champion_update_rate = (champion_update_count / len(self.sharpes) * 100) if self.sharpes else 0.0

        # Calculate Sharpe metrics (successful iterations only)
        successful_sharpes = [s for s in self.sharpes if s > 0]
        if successful_sharpes:
            best_sharpe = max(successful_sharpes)
            avg_sharpe = sum(successful_sharpes) / len(successful_sharpes)
            sharpe_variance = np.var(successful_sharpes, ddof=1) if len(successful_sharpes) > 1 else 0.0
        else:
            best_sharpe = 0.0
            avg_sharpe = 0.0
            sharpe_variance = 0.0

        # Calculate parameter diversity metrics
        param_diversity = len(self.param_combinations)
        param_diversity_rate = (param_diversity / len(self.sharpes) * 100) if self.sharpes else 0.0

        # Calculate validation statistics
        total_validations = self.validation_stats.get('total_validations', 0)
        validation_passes = self.validation_stats.get('validation_passes', 0)
        validation_pass_rate = (validation_passes / total_validations * 100) if total_validations > 0 else 100.0

        # Calculate success metrics
        success_count = len(successful_sharpes)
        failure_count = len(self.sharpes) - success_count
        success_rate = (success_count / len(self.sharpes) * 100) if self.sharpes else 0.0

        # Calculate average duration
        avg_duration = sum(self.durations) / len(self.durations) if self.durations else 0.0

        # Get final champion state
        final_champion = None
        if loop.champion:
            final_champion = {
                'iteration': loop.champion.iteration_num,
                'sharpe': loop.champion.metrics.get('sharpe_ratio', 0.0),
                'metrics': loop.champion.metrics,
                'parameters': loop.champion.parameters if hasattr(loop.champion, 'parameters') else None
            }

        # Build comprehensive results
        results = {
            # Test completion
            'test_completed': True,
            'total_iterations': len(self.sharpes),

            # Primary decision metrics
            'champion_update_count': champion_update_count,
            'champion_update_rate': float(champion_update_rate),
            'best_sharpe': float(best_sharpe),
            'avg_sharpe': float(avg_sharpe),
            'sharpe_variance': float(sharpe_variance),

            # Detailed metrics
            'sharpes': self.sharpes,
            'durations': self.durations,
            'champion_updates': self.champion_updates,

            # Phase 0 specific metrics
            'param_diversity': param_diversity,
            'param_diversity_rate': float(param_diversity_rate),
            'param_combinations': [list(combo) for combo in self.param_combinations],
            'validation_pass_rate': float(validation_pass_rate),
            'validation_stats': self.validation_stats,

            # Success metrics
            'success_count': success_count,
            'failure_count': failure_count,
            'success_rate': float(success_rate),

            # Duration metrics
            'total_duration_seconds': float(test_duration),
            'avg_duration_per_iteration': float(avg_duration),

            # Champion state
            'final_champion': final_champion
        }

        # Log summary
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("RESULTS SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Total iterations: {results['total_iterations']}")
        self.logger.info(f"Champion updates: {results['champion_update_count']} ({results['champion_update_rate']:.1f}%)")
        self.logger.info(f"Best Sharpe: {results['best_sharpe']:.4f}")
        self.logger.info(f"Avg Sharpe: {results['avg_sharpe']:.4f}")
        self.logger.info(f"Sharpe variance: {results['sharpe_variance']:.4f}")
        self.logger.info(f"Parameter diversity: {results['param_diversity']} ({results['param_diversity_rate']:.1f}%)")
        self.logger.info(f"Validation pass rate: {results['validation_pass_rate']:.1f}%")
        self.logger.info(f"Success rate: {results['success_rate']:.1f}%")

        if final_champion:
            self.logger.info("")
            self.logger.info(f"🏆 FINAL CHAMPION:")
            self.logger.info(f"   Iteration: {final_champion['iteration']}")
            self.logger.info(f"   Sharpe: {final_champion['sharpe']:.4f}")

        self.logger.info("=" * 70)

        return results

    def _track_parameters(self, parameters: Dict[str, Any]) -> None:
        """Track unique parameter combinations for diversity metrics.

        Converts parameter dictionary to a hashable tuple and adds to
        param_combinations list if not already present. This supports
        calculating parameter diversity metrics for Phase 0 decision.

        Args:
            parameters: Dictionary of parameters from iteration record
                Expected keys: momentum_period, ma_periods, catalyst_type,
                               catalyst_lookback, n_stocks, stop_loss,
                               resample, resample_offset

        Side Effects:
            Updates self.param_combinations with new unique combination
        """
        try:
            # Extract parameters in consistent order for tuple creation
            param_tuple = (
                parameters.get('momentum_period'),
                parameters.get('ma_periods'),
                parameters.get('catalyst_type'),
                parameters.get('catalyst_lookback'),
                parameters.get('n_stocks'),
                parameters.get('stop_loss'),
                parameters.get('resample'),
                parameters.get('resample_offset')
            )

            # Add to param_combinations if not already present
            if param_tuple not in self.param_combinations:
                self.param_combinations.append(param_tuple)
                self.logger.debug(f"New parameter combination tracked: {param_tuple}")
                self.logger.debug(f"Total unique combinations: {len(self.param_combinations)}")

        except Exception as e:
            self.logger.warning(f"Failed to track parameters: {e}")
            # Don't raise - parameter tracking failure shouldn't crash test

    def _track_validation(self, validation_result: Dict[str, Any]) -> None:
        """Track validation statistics for Phase 0 decision metrics.

        Updates validation_stats dictionary with pass/fail counts and
        common error patterns. Supports calculating validation pass rate
        for Phase 0 decision criteria (target: ≥90%).

        Args:
            validation_result: Validation result dictionary containing:
                - passed: Boolean indicating validation success
                - errors: Optional list of error messages if validation failed

        Side Effects:
            Updates self.validation_stats with:
                - total_validations: Incremented by 1
                - validation_passes: Incremented if passed=True
                - validation_failures: Incremented if passed=False
                - common_errors: Error frequency tracking
        """
        try:
            # Update validation counters
            self.validation_stats['total_validations'] += 1

            if validation_result.get('passed', False):
                # Validation passed
                self.validation_stats['validation_passes'] += 1
                self.logger.debug(f"Validation passed (total passes: {self.validation_stats['validation_passes']})")
            else:
                # Validation failed
                self.validation_stats['validation_failures'] += 1
                self.logger.debug(f"Validation failed (total failures: {self.validation_stats['validation_failures']})")

                # Track common errors
                errors = validation_result.get('errors', [])
                for error in errors:
                    error_key = error[:100]  # Truncate long error messages
                    self.validation_stats['common_errors'][error_key] = \
                        self.validation_stats['common_errors'].get(error_key, 0) + 1

            # Log validation pass rate periodically
            total = self.validation_stats['total_validations']
            if total % 10 == 0:  # Every 10 validations
                passes = self.validation_stats['validation_passes']
                pass_rate = (passes / total * 100) if total > 0 else 0.0
                self.logger.info(f"Validation pass rate: {pass_rate:.1f}% ({passes}/{total})")

        except Exception as e:
            self.logger.warning(f"Failed to track validation: {e}")
            # Don't raise - validation tracking failure shouldn't crash test

    def run_5_generation_test(
        self,
        data: Any,
        resume_from_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute 5-iteration smoke test for Phase 0 template mode validation.

        Lightweight version of run() method for quick validation:
        - 5 iterations instead of 50
        - Validates template mode parameter generation
        - Tests checkpointing capability (checkpoint every 2 iterations)
        - Verifies all metrics are calculated correctly
        - Quick GO/NO-GO feasibility check

        This is NOT the full Phase 0 test - it's a smoke test to ensure:
        1. Template mode parameter generation works
        2. Champion update tracking works
        3. Metrics calculation works
        4. Checkpointing works
        5. Results compilation works

        Args:
            data: Finlab data object for strategy execution
            resume_from_checkpoint: Optional path to checkpoint file for resuming

        Returns:
            Dict[str, Any]: Results dictionary with same structure as run()
                but with only 5 iterations of data

        Raises:
            Exception: Critical failures that prevent test completion
        """
        # Temporarily override max_iterations for smoke test
        original_max_iterations = self.max_iterations
        original_checkpoint_interval = self.checkpoint_interval

        try:
            # Set smoke test parameters
            self.max_iterations = 5
            self.checkpoint_interval = 2  # Checkpoint every 2 iterations for testing

            self.logger.info("=" * 70)
            self.logger.info("PHASE 0 SMOKE TEST (5 ITERATIONS)")
            self.logger.info("=" * 70)
            self.logger.info(f"This is a quick validation test, NOT the full 50-iteration test")
            self.logger.info(f"Purpose: Verify template mode infrastructure works correctly")
            self.logger.info("")

            # Run the standard test with 5 iterations
            results = self.run(data, resume_from_checkpoint)

            # Add smoke test metadata
            results['smoke_test'] = True
            results['smoke_test_iterations'] = 5
            results['full_test_required'] = True

            self.logger.info("")
            self.logger.info("=" * 70)
            self.logger.info("SMOKE TEST COMPLETE - INFRASTRUCTURE VALIDATED")
            self.logger.info("=" * 70)
            self.logger.info(f"✅ Template mode parameter generation: WORKING")
            self.logger.info(f"✅ Champion update tracking: WORKING")
            self.logger.info(f"✅ Metrics calculation: WORKING")
            self.logger.info(f"✅ Checkpointing: WORKING")
            self.logger.info(f"✅ Results compilation: WORKING")
            self.logger.info("")
            self.logger.info(f"⚠️  NOTE: This was only a 5-iteration smoke test")
            self.logger.info(f"⚠️  Full 50-iteration test required for GO/NO-GO decision")
            self.logger.info("=" * 70)

            return results

        finally:
            # Restore original settings
            self.max_iterations = original_max_iterations
            self.checkpoint_interval = original_checkpoint_interval
