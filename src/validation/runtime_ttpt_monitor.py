"""
Runtime TTPT Monitor - Real-time Look-ahead Bias Detection.

Integrates Time-Travel Perturbation Testing into optimization workflows,
providing checkpoint-based validation, automated violation logging, and
real-time alerts during TPE parameter optimization.

Example:
    >>> monitor = RuntimeTTPTMonitor(checkpoint_interval=10)
    >>> result = monitor.validate_checkpoint(
    ...     trial_number=20,
    ...     strategy_fn=my_strategy,
    ...     data=market_data,
    ...     params={'lookback': 25}
    ... )
    >>> if not result['passed']:
    ...     print(f"⚠️ Look-ahead bias detected at trial 20!")
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Callable, Optional
from pathlib import Path
import json
import logging
from datetime import datetime

from src.validation.ttpt_framework import TTPTFramework, TTPTViolation

logger = logging.getLogger(__name__)


class RuntimeTTPTMonitor:
    """
    Runtime monitor for TTPT validation during optimization.

    Integrates with TPE optimizer to validate strategies at checkpoints,
    log violations, and alert when look-ahead bias is detected.

    Attributes:
        ttpt_framework: Underlying TTPT framework instance
        checkpoint_interval: Validate every N trials
        log_dir: Directory for violation logs
        alert_on_violation: Print alert when violation detected
        validation_history: List of all validation results
    """

    def __init__(
        self,
        ttpt_config: Optional[Dict[str, Any]] = None,
        checkpoint_interval: int = 10,
        log_dir: Optional[str] = None,
        alert_on_violation: bool = True
    ):
        """
        Initialize runtime TTPT monitor.

        Args:
            ttpt_config: Configuration for TTPTFramework (shift_days, tolerance, etc.)
            checkpoint_interval: Validate every N trials (default: 10)
            log_dir: Directory for violation logs (default: logs/ttpt_violations)
            alert_on_violation: Print alert when violation detected
        """
        # Initialize TTPT framework
        if ttpt_config is None:
            ttpt_config = {}

        self.ttpt_framework = TTPTFramework(**ttpt_config)
        self.checkpoint_interval = checkpoint_interval
        self.alert_on_violation = alert_on_violation

        # Set up logging directory
        if log_dir is None:
            log_dir = "logs/ttpt_violations"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Tracking
        self.validation_history: List[Dict[str, Any]] = []

        logger.info(
            f"Initialized Runtime TTPT Monitor: "
            f"checkpoint_interval={checkpoint_interval}, "
            f"log_dir={self.log_dir}, "
            f"alert_on_violation={alert_on_violation}"
        )

    def validate_checkpoint(
        self,
        trial_number: int,
        strategy_fn: Callable,
        data: Dict[str, pd.DataFrame],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate strategy at optimization checkpoint.

        Args:
            trial_number: Current trial number in optimization
            strategy_fn: Strategy function to validate
            data: Market data dictionary
            params: Strategy parameters for this trial

        Returns:
            {
                'passed': bool,  # Validation result
                'should_continue': bool,  # Whether to continue optimization
                'violations': List[TTPTViolation],  # Detected violations
                'logged': bool,  # Whether violation was logged
                'skipped': bool  # Whether validation was skipped (not at checkpoint)
            }
        """
        # Check if this is a checkpoint trial
        if trial_number % self.checkpoint_interval != 0:
            return {
                'skipped': True,
                'should_continue': True,
                'passed': None,
                'violations': [],
                'logged': False
            }

        logger.info(f"Validating trial {trial_number} at checkpoint (interval={self.checkpoint_interval})")

        # Run TTPT validation
        try:
            ttpt_result = self.ttpt_framework.validate_strategy(
                strategy_fn=strategy_fn,
                original_data=data,
                params=params
            )
        except Exception as e:
            logger.error(f"TTPT validation failed at trial {trial_number}: {e}")
            return {
                'passed': False,
                'should_continue': True,  # Continue despite error
                'violations': [],
                'logged': False,
                'skipped': False,
                'error': str(e)
            }

        # Extract results
        passed = ttpt_result['passed']
        violations = ttpt_result.get('violations', [])

        # Log violation if detected
        logged = False
        if not passed and violations:
            try:
                self.log_violation(
                    trial_number=trial_number,
                    params=params,
                    ttpt_result=ttpt_result
                )
                logged = True
            except Exception as e:
                logger.error(f"Failed to log violation: {e}")

            # Print alert if enabled
            if self.alert_on_violation:
                self._print_violation_alert(trial_number, violations)

        # Record in history
        history_entry = {
            'trial_number': trial_number,
            'passed': passed,
            'num_violations': len(violations),
            'params': params.copy(),
            'timestamp': datetime.now().isoformat()
        }
        self.validation_history.append(history_entry)

        return {
            'passed': passed,
            'should_continue': True,  # Always continue (monitoring only)
            'violations': violations,
            'logged': logged,
            'skipped': False
        }

    def log_violation(
        self,
        trial_number: int,
        params: Dict[str, Any],
        ttpt_result: Dict[str, Any]
    ) -> str:
        """
        Log TTPT violation to file.

        Args:
            trial_number: Trial number where violation occurred
            params: Strategy parameters
            ttpt_result: Full TTPT validation result

        Returns:
            Path to log file
        """
        # Helper to convert numpy types to native Python types
        def convert_value(val):
            if isinstance(val, (np.integer, np.floating)):
                return float(val)
            elif isinstance(val, np.ndarray):
                return val.tolist()
            return val

        # Create log entry
        log_entry = {
            'trial_number': trial_number,
            'timestamp': datetime.now().isoformat(),
            'params': params,
            'passed': ttpt_result['passed'],
            'violations': [],
            'metrics': {k: convert_value(v) for k, v in ttpt_result.get('metrics', {}).items()}
        }

        # Convert TTPTViolation objects to dicts
        for violation in ttpt_result.get('violations', []):
            if isinstance(violation, TTPTViolation):
                log_entry['violations'].append({
                    'shift_days': int(violation.shift_days),
                    'violation_type': str(violation.violation_type),
                    'metric_name': str(violation.metric_name),
                    'original_value': convert_value(violation.original_value),
                    'shifted_value': convert_value(violation.shifted_value),
                    'change': convert_value(violation.change),
                    'severity': str(violation.severity)
                })
            else:
                # Already a dict - still need to convert numpy types
                log_entry['violations'].append({
                    k: convert_value(v) for k, v in violation.items()
                })

        # Write to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"violation_trial_{trial_number}_{timestamp}.json"
        log_path = self.log_dir / log_filename

        with open(log_path, 'w') as f:
            json.dump(log_entry, f, indent=2)

        logger.info(f"Violation logged to: {log_path}")

        return str(log_path)

    def _print_violation_alert(
        self,
        trial_number: int,
        violations: List[TTPTViolation]
    ):
        """Print violation alert to console."""
        print(f"\n{'='*70}")
        print(f"⚠️  TTPT VIOLATION DETECTED - Trial {trial_number}")
        print(f"{'='*70}")
        print(f"Number of violations: {len(violations)}")

        for i, v in enumerate(violations[:3], 1):  # Show first 3
            if isinstance(v, TTPTViolation):
                print(f"\nViolation #{i}:")
                print(f"  Type: {v.violation_type}")
                print(f"  Shift: {v.shift_days} days")
                print(f"  Metric: {v.metric_name}")
                print(f"  Change: {v.change:.4f} ({v.change:.2%})")
                print(f"  Severity: {v.severity}")

        if len(violations) > 3:
            print(f"\n... and {len(violations) - 3} more violations")

        print(f"{'='*70}\n")

    def get_violation_summary(self) -> Dict[str, Any]:
        """
        Get summary of violations detected during optimization.

        Returns:
            {
                'total_validations': int,
                'total_violations': int,
                'violation_rate': float,
                'violations': List[Dict]
            }
        """
        total_validations = len(self.validation_history)
        total_violations = sum(
            1 for entry in self.validation_history
            if not entry['passed']
        )

        violation_rate = (
            total_violations / total_validations
            if total_validations > 0
            else 0.0
        )

        return {
            'total_validations': total_validations,
            'total_violations': total_violations,
            'violation_rate': violation_rate,
            'violations': [
                entry for entry in self.validation_history
                if not entry['passed']
            ]
        }

    def reset(self):
        """Reset validation history."""
        self.validation_history = []
        logger.info("Validation history reset")
