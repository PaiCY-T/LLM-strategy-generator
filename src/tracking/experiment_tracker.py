"""
Experiment Tracker - Task 2.4.

Logs optimization runs, TTPT validations, and strategy performance
metrics for analysis and comparison.

Features:
- SQLite backend (default) with JSON fallback
- Log experiments, trials, TTPT results, strategy metadata
- Query interface for retrieving and analyzing data
- Integration with TPE optimizer
- Performance tracking and comparison
"""

import sqlite3
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import pandas as pd
import logging

from src.tracking.schema import ExperimentSchema

logger = logging.getLogger(__name__)


class ExperimentTracker:
    """
    Experiment tracking system for TPE optimization.

    Attributes:
        backend: 'sqlite' or 'json'
        db_path: Path to database file
    """

    def __init__(
        self,
        backend: str = 'sqlite',
        db_path: Optional[str] = None
    ):
        """
        Initialize experiment tracker.

        Args:
            backend: Storage backend ('sqlite' or 'json')
            db_path: Path to database file (default: experiments.db)
        """
        self.backend = backend
        self.db_path = db_path or 'experiments.db'

        # Create database and tables
        if backend == 'sqlite':
            ExperimentSchema.create_tables(self.db_path)
            logger.info(f"Initialized SQLite experiment tracker: {self.db_path}")
        elif backend == 'json':
            # Ensure parent directory exists for JSON
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Initialized JSON experiment tracker: {self.db_path}")
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self.backend != 'sqlite':
            raise RuntimeError("Connection only available for SQLite backend")
        return sqlite3.connect(self.db_path)

    def create_experiment(
        self,
        name: str,
        template: str,
        mode: str,
        config: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Create new experiment.

        Args:
            name: Experiment name
            template: Strategy template used
            mode: Optimization mode ('tpe', 'tpe_runtime_ttpt', etc.)
            config: Configuration dictionary

        Returns:
            Experiment ID
        """
        if self.backend == 'sqlite':
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO experiments (name, template, mode, config)
                VALUES (?, ?, ?, ?)
                """,
                (name, template, mode, json.dumps(config or {}))
            )

            experiment_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"Created experiment {experiment_id}: {name}")
            return experiment_id

        elif self.backend == 'json':
            # JSON fallback - simple implementation
            # Read existing data
            data = self._read_json()

            # Generate ID
            experiment_id = len(data.get('experiments', [])) + 1

            # Add experiment
            experiment = {
                'id': experiment_id,
                'name': name,
                'template': template,
                'mode': mode,
                'config': config or {},
                'created_at': datetime.now().isoformat(),
                'trials': []
            }

            if 'experiments' not in data:
                data['experiments'] = []

            data['experiments'].append(experiment)

            # Write back
            self._write_json(data)

            logger.info(f"Created experiment {experiment_id}: {name}")
            return experiment_id

    def log_trial(
        self,
        experiment_id: int,
        trial_number: int,
        params: Dict[str, Any],
        performance: Dict[str, float]
    ) -> int:
        """
        Log trial result.

        Args:
            experiment_id: Parent experiment ID
            trial_number: Trial number
            params: Strategy parameters
            performance: Performance metrics (e.g., {'sharpe': 1.23})

        Returns:
            Trial ID
        """
        if self.backend == 'sqlite':
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO trials (
                    experiment_id, trial_number, params, performance
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    experiment_id,
                    trial_number,
                    json.dumps(params),
                    json.dumps(performance)
                )
            )

            trial_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return trial_id

        elif self.backend == 'json':
            data = self._read_json()

            # Find experiment
            exp = self._find_experiment_json(data, experiment_id)
            if not exp:
                raise ValueError(f"Experiment {experiment_id} not found")

            # Generate trial ID
            trial_id = len(exp.get('trials', [])) + 1

            # Add trial
            trial = {
                'id': trial_id,
                'trial_number': trial_number,
                'params': params,
                'performance': performance,
                'created_at': datetime.now().isoformat()
            }

            if 'trials' not in exp:
                exp['trials'] = []

            exp['trials'].append(trial)

            self._write_json(data)

            return trial_id

    def log_ttpt_result(
        self,
        trial_id: int,
        passed: bool,
        num_violations: int,
        metrics: Dict[str, float]
    ) -> int:
        """
        Log TTPT validation result.

        Args:
            trial_id: Parent trial ID
            passed: Whether validation passed
            num_violations: Number of violations detected
            metrics: TTPT metrics (correlation, performance_change, etc.)

        Returns:
            TTPT result ID
        """
        if self.backend == 'sqlite':
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO ttpt_results (
                    trial_id, passed, num_violations, metrics
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    trial_id,
                    int(passed),
                    num_violations,
                    json.dumps(metrics)
                )
            )

            ttpt_id = cursor.lastrowid
            conn.commit()
            conn.close()

            return ttpt_id

        elif self.backend == 'json':
            data = self._read_json()

            # Find trial in any experiment
            trial = None
            for exp in data.get('experiments', []):
                for t in exp.get('trials', []):
                    if t['id'] == trial_id:
                        trial = t
                        break
                if trial:
                    break

            if not trial:
                raise ValueError(f"Trial {trial_id} not found")

            # Add TTPT result
            ttpt_result = {
                'passed': passed,
                'num_violations': num_violations,
                'metrics': metrics,
                'created_at': datetime.now().isoformat()
            }

            trial['ttpt_result'] = ttpt_result

            self._write_json(data)

            return trial_id  # Use trial_id as TTPT ID for JSON

    def log_strategy_metadata(
        self,
        trial_id: int,
        strategy_code: str,
        template: str,
        generation_method: str
    ) -> None:
        """
        Log strategy metadata.

        Args:
            trial_id: Trial ID
            strategy_code: Generated strategy code
            template: Template name
            generation_method: Generation method ('template', 'llm', etc.)
        """
        if self.backend == 'sqlite':
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE trials
                SET strategy_code = ?,
                    strategy_template = ?,
                    generation_method = ?
                WHERE id = ?
                """,
                (strategy_code, template, generation_method, trial_id)
            )

            conn.commit()
            conn.close()

        elif self.backend == 'json':
            data = self._read_json()

            # Find trial
            for exp in data.get('experiments', []):
                for trial in exp.get('trials', []):
                    if trial['id'] == trial_id:
                        trial['strategy_code'] = strategy_code
                        trial['strategy_template'] = template
                        trial['generation_method'] = generation_method
                        break

            self._write_json(data)

    def get_experiment(self, experiment_id: int) -> Dict[str, Any]:
        """
        Get experiment by ID.

        Args:
            experiment_id: Experiment ID

        Returns:
            Experiment dictionary
        """
        if self.backend == 'sqlite':
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, name, template, mode, config, created_at, summary
                FROM experiments
                WHERE id = ?
                """,
                (experiment_id,)
            )

            row = cursor.fetchone()
            conn.close()

            if not row:
                raise ValueError(f"Experiment {experiment_id} not found")

            return {
                'id': row[0],
                'name': row[1],
                'template': row[2],
                'mode': row[3],
                'config': json.loads(row[4]) if row[4] else {},
                'created_at': row[5],
                'summary': json.loads(row[6]) if row[6] else {}
            }

        elif self.backend == 'json':
            data = self._read_json()
            exp = self._find_experiment_json(data, experiment_id)

            if not exp:
                raise ValueError(f"Experiment {experiment_id} not found")

            return exp

    def list_experiments(self) -> List[Dict[str, Any]]:
        """
        List all experiments.

        Returns:
            List of experiment dictionaries
        """
        if self.backend == 'sqlite':
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, name, template, mode, config, created_at
                FROM experiments
                ORDER BY created_at DESC
                """
            )

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'id': row[0],
                    'name': row[1],
                    'template': row[2],
                    'mode': row[3],
                    'config': json.loads(row[4]) if row[4] else {},
                    'created_at': row[5]
                }
                for row in rows
            ]

        elif self.backend == 'json':
            data = self._read_json()
            return data.get('experiments', [])

    def get_trials(self, experiment_id: int) -> List[Dict[str, Any]]:
        """
        Get all trials for experiment.

        Args:
            experiment_id: Experiment ID

        Returns:
            List of trial dictionaries
        """
        if self.backend == 'sqlite':
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, trial_number, params, performance, created_at
                FROM trials
                WHERE experiment_id = ?
                ORDER BY trial_number
                """,
                (experiment_id,)
            )

            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    'id': row[0],
                    'trial_number': row[1],
                    'params': json.loads(row[2]),
                    'performance': json.loads(row[3]),
                    'created_at': row[4]
                }
                for row in rows
            ]

        elif self.backend == 'json':
            data = self._read_json()
            exp = self._find_experiment_json(data, experiment_id)

            if not exp:
                raise ValueError(f"Experiment {experiment_id} not found")

            return exp.get('trials', [])

    def filter_experiments(
        self,
        max_violation_rate: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter experiments by criteria.

        Args:
            max_violation_rate: Maximum TTPT violation rate (0.0-1.0)

        Returns:
            Filtered experiments
        """
        experiments = self.list_experiments()

        if max_violation_rate is not None:
            filtered = []
            for exp in experiments:
                # Get TTPT results for this experiment
                trials = self.get_trials(exp['id'])
                ttpt_results = []

                if self.backend == 'sqlite':
                    conn = self._get_connection()
                    cursor = conn.cursor()

                    for trial in trials:
                        cursor.execute(
                            """
                            SELECT passed
                            FROM ttpt_results
                            WHERE trial_id = ?
                            """,
                            (trial['id'],)
                        )
                        result = cursor.fetchone()
                        if result:
                            ttpt_results.append(result[0])

                    conn.close()

                elif self.backend == 'json':
                    for trial in trials:
                        if 'ttpt_result' in trial:
                            ttpt_results.append(trial['ttpt_result']['passed'])

                # Calculate violation rate
                if ttpt_results:
                    violation_rate = 1.0 - (sum(ttpt_results) / len(ttpt_results))
                    if violation_rate <= max_violation_rate:
                        filtered.append(exp)

            return filtered

        return experiments

    def get_performance_improvement(self, experiment_id: int) -> float:
        """
        Calculate performance improvement over trials.

        Args:
            experiment_id: Experiment ID

        Returns:
            Improvement (final best - initial best)
        """
        trials = self.get_trials(experiment_id)

        if not trials:
            return 0.0

        # Extract Sharpe ratios
        sharpes = []
        for trial in trials:
            perf = trial.get('performance', {})
            if 'sharpe' in perf:
                sharpes.append(perf['sharpe'])

        if not sharpes:
            return 0.0

        # Calculate improvement
        initial_best = max(sharpes[:len(sharpes)//2]) if len(sharpes) > 1 else sharpes[0]
        final_best = max(sharpes)

        return final_best - initial_best

    def compare_experiments(
        self,
        experiment_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Compare multiple experiments.

        Args:
            experiment_ids: List of experiment IDs

        Returns:
            Comparison results
        """
        results = []

        for exp_id in experiment_ids:
            experiment = self.get_experiment(exp_id)
            trials = self.get_trials(exp_id)

            # Calculate best Sharpe
            sharpes = [
                t['performance'].get('sharpe', 0.0)
                for t in trials
            ]

            best_sharpe = max(sharpes) if sharpes else 0.0

            results.append({
                'id': exp_id,
                'name': experiment['name'],
                'best_sharpe': best_sharpe,
                'n_trials': len(trials)
            })

        return results

    def export_to_dataframe(self, experiment_id: int) -> pd.DataFrame:
        """
        Export experiment trials to DataFrame.

        Args:
            experiment_id: Experiment ID

        Returns:
            pandas DataFrame
        """
        trials = self.get_trials(experiment_id)

        # Flatten trial data
        records = []
        for trial in trials:
            record = {
                'trial_number': trial['trial_number'],
                **trial['params'],
                **trial['performance']
            }
            records.append(record)

        return pd.DataFrame(records)

    def log_experiment_summary(
        self,
        experiment_id: int,
        summary: Dict[str, Any]
    ) -> None:
        """
        Log experiment summary.

        Args:
            experiment_id: Experiment ID
            summary: Summary dictionary
        """
        if self.backend == 'sqlite':
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE experiments
                SET summary = ?
                WHERE id = ?
                """,
                (json.dumps(summary), experiment_id)
            )

            conn.commit()
            conn.close()

        elif self.backend == 'json':
            data = self._read_json()
            exp = self._find_experiment_json(data, experiment_id)

            if exp:
                exp['summary'] = summary
                self._write_json(data)

    # JSON backend helpers
    def _read_json(self) -> Dict[str, Any]:
        """Read JSON file."""
        if not Path(self.db_path).exists():
            return {}

        with open(self.db_path, 'r') as f:
            return json.load(f)

    def _write_json(self, data: Dict[str, Any]) -> None:
        """Write JSON file."""
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _find_experiment_json(
        self,
        data: Dict[str, Any],
        experiment_id: int
    ) -> Optional[Dict[str, Any]]:
        """Find experiment in JSON data."""
        for exp in data.get('experiments', []):
            if exp['id'] == experiment_id:
                return exp
        return None
