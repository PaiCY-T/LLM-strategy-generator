"""
Tests for Experiment Tracker - Task 2.4.

Experiment tracking system that logs optimization runs, TTPT validations,
and strategy performance metrics for analysis and comparison.

Test Structure (TDD RED Phase):
1. TestExperimentTrackerConfig - Configuration and initialization
2. TestExperimentLogging - Log experiments, trials, TTPT results
3. TestQueryInterface - Query and retrieve experiment data
4. TestTPEIntegration - Integration with TPE optimizer
5. TestPerformanceTracking - Track improvements and comparisons
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from pathlib import Path
import json
import tempfile
import shutil
import sqlite3

# Import actual implementation (will be created in GREEN phase)
from src.tracking.experiment_tracker import ExperimentTracker
from src.tracking.schema import ExperimentSchema


class TestExperimentTrackerConfig:
    """Test configuration and initialization."""

    def test_default_sqlite_initialization(self):
        """Tracker should initialize with SQLite backend by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            assert tracker is not None
            assert tracker.backend == 'sqlite'
            assert Path(f"{tmpdir}/experiments.db").exists()

    def test_custom_db_path(self):
        """Tracker should accept custom database path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = f"{tmpdir}/custom/experiments.db"
            tracker = ExperimentTracker(db_path=custom_path)

            assert Path(custom_path).exists()
            assert tracker.db_path == custom_path

    def test_json_fallback_mode(self):
        """Tracker should support JSON file fallback."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(
                backend='json',
                db_path=f"{tmpdir}/experiments.json"
            )

            assert tracker.backend == 'json'
            assert Path(f"{tmpdir}/experiments.json").parent.exists()

    def test_schema_creation(self):
        """Tracker should create database schema on initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            # Check tables exist
            conn = sqlite3.connect(f"{tmpdir}/experiments.db")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            assert 'experiments' in tables
            assert 'trials' in tables
            assert 'ttpt_results' in tables

            conn.close()


class TestExperimentLogging:
    """Test experiment and trial logging."""

    def test_create_experiment(self):
        """Should create new experiment with metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            experiment_id = tracker.create_experiment(
                name="Test Optimization",
                template="Momentum",
                mode="tpe",
                config={
                    'n_trials': 50,
                    'checkpoint_interval': 10
                }
            )

            assert experiment_id is not None
            assert isinstance(experiment_id, (int, str))

    def test_log_trial(self):
        """Should log trial with parameters and performance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            exp_id = tracker.create_experiment(
                name="Test",
                template="Momentum",
                mode="tpe"
            )

            trial_id = tracker.log_trial(
                experiment_id=exp_id,
                trial_number=1,
                params={'lookback': 20, 'momentum_threshold': 0.05},
                performance={'sharpe': 1.23, 'returns': 0.15}
            )

            assert trial_id is not None

    def test_log_ttpt_result(self):
        """Should log TTPT validation result for trial."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            exp_id = tracker.create_experiment(
                name="Test",
                template="Momentum",
                mode="tpe"
            )

            trial_id = tracker.log_trial(
                experiment_id=exp_id,
                trial_number=10,
                params={'lookback': 20},
                performance={'sharpe': 1.5}
            )

            ttpt_id = tracker.log_ttpt_result(
                trial_id=trial_id,
                passed=True,
                num_violations=0,
                metrics={'correlation': 0.98, 'performance_change': 0.02}
            )

            assert ttpt_id is not None

    def test_log_strategy_metadata(self):
        """Should log strategy metadata (code, template, generation method)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            exp_id = tracker.create_experiment(
                name="Test",
                template="Momentum",
                mode="tpe"
            )

            trial_id = tracker.log_trial(
                experiment_id=exp_id,
                trial_number=1,
                params={'lookback': 20},
                performance={'sharpe': 1.2}
            )

            tracker.log_strategy_metadata(
                trial_id=trial_id,
                strategy_code="def strategy(data): pass",
                template="Momentum",
                generation_method="template"
            )

            # Should not raise error
            assert True

    def test_log_multiple_trials(self):
        """Should handle logging multiple trials for same experiment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            exp_id = tracker.create_experiment(
                name="Test",
                template="Momentum",
                mode="tpe"
            )

            trial_ids = []
            for i in range(5):
                trial_id = tracker.log_trial(
                    experiment_id=exp_id,
                    trial_number=i,
                    params={'lookback': 10 + i * 5},
                    performance={'sharpe': 1.0 + i * 0.1}
                )
                trial_ids.append(trial_id)

            assert len(trial_ids) == 5
            assert len(set(trial_ids)) == 5  # All unique


class TestQueryInterface:
    """Test querying and retrieving experiment data."""

    def test_get_experiment_by_id(self):
        """Should retrieve experiment by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            exp_id = tracker.create_experiment(
                name="Test Experiment",
                template="Momentum",
                mode="tpe",
                config={'n_trials': 50}
            )

            experiment = tracker.get_experiment(exp_id)

            assert experiment is not None
            assert experiment['name'] == "Test Experiment"
            assert experiment['template'] == "Momentum"
            assert experiment['mode'] == "tpe"

    def test_list_experiments(self):
        """Should list all experiments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            # Create multiple experiments
            for i in range(3):
                tracker.create_experiment(
                    name=f"Experiment {i}",
                    template="Momentum",
                    mode="tpe"
                )

            experiments = tracker.list_experiments()

            assert len(experiments) == 3

    def test_get_trials_for_experiment(self):
        """Should retrieve all trials for experiment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            exp_id = tracker.create_experiment(
                name="Test",
                template="Momentum",
                mode="tpe"
            )

            # Log 3 trials
            for i in range(3):
                tracker.log_trial(
                    experiment_id=exp_id,
                    trial_number=i,
                    params={'lookback': 20 + i},
                    performance={'sharpe': 1.0 + i * 0.1}
                )

            trials = tracker.get_trials(exp_id)

            assert len(trials) == 3
            assert trials[0]['trial_number'] == 0
            assert trials[2]['trial_number'] == 2

    def test_filter_by_violation_rate(self):
        """Should filter experiments by TTPT violation rate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            # Experiment with violations
            exp1 = tracker.create_experiment(
                name="High Violation",
                template="Momentum",
                mode="tpe"
            )

            for i in range(10):
                trial_id = tracker.log_trial(
                    experiment_id=exp1,
                    trial_number=i,
                    params={'lookback': 20},
                    performance={'sharpe': 1.0}
                )

                if i % 10 == 0:  # Checkpoint
                    tracker.log_ttpt_result(
                        trial_id=trial_id,
                        passed=(i % 2 == 0),  # 50% violation rate
                        num_violations=1 if i % 2 != 0 else 0,
                        metrics={}
                    )

            # Experiment without violations
            exp2 = tracker.create_experiment(
                name="Low Violation",
                template="Momentum",
                mode="tpe"
            )

            for i in range(10):
                trial_id = tracker.log_trial(
                    experiment_id=exp2,
                    trial_number=i,
                    params={'lookback': 20},
                    performance={'sharpe': 1.2}
                )

                if i % 10 == 0:  # Checkpoint
                    tracker.log_ttpt_result(
                        trial_id=trial_id,
                        passed=True,
                        num_violations=0,
                        metrics={}
                    )

            # Filter for low violation experiments
            low_violation_exps = tracker.filter_experiments(
                max_violation_rate=0.3
            )

            assert len(low_violation_exps) >= 1


class TestTPEIntegration:
    """Test integration with TPE optimizer."""

    def test_integrates_with_optimize_with_runtime_ttpt(self):
        """Should integrate with TPE optimizer's optimize_with_runtime_ttpt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from src.learning.optimizer import TPEOptimizer

            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")
            optimizer = TPEOptimizer()

            # Create experiment
            exp_id = tracker.create_experiment(
                name="TPE Integration Test",
                template="Momentum",
                mode="tpe_runtime_ttpt"
            )

            # Simple test data
            dates = pd.date_range('2023-01-01', periods=100, freq='D')
            data = {
                'close': pd.DataFrame({
                    '2330.TW': np.random.randn(100) + 100
                }, index=dates)
            }

            def objective(params):
                return np.random.uniform(0.5, 2.0)

            def strategy(data_dict, params):
                close = data_dict['close']
                ma = close.rolling(window=params['lookback']).mean()
                return (close > ma).astype(float)

            param_space = {
                'lookback': ('int', 10, 50)
            }

            # Run optimization with tracking
            result = optimizer.optimize_with_runtime_ttpt(
                objective_fn=objective,
                strategy_fn=strategy,
                data=data,
                n_trials=5,
                param_space=param_space,
                checkpoint_interval=5
            )

            # Manually log trials (integration will be automatic in final)
            for i in range(5):
                tracker.log_trial(
                    experiment_id=exp_id,
                    trial_number=i,
                    params={'lookback': 20 + i},
                    performance={'sharpe': 1.0 + i * 0.1}
                )

            trials = tracker.get_trials(exp_id)
            assert len(trials) == 5

    def test_logs_trials_automatically(self):
        """Should automatically log trials during optimization."""
        # This will be implemented in integration phase
        # For now, test manual logging works
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            exp_id = tracker.create_experiment(
                name="Auto Logging Test",
                template="Momentum",
                mode="tpe"
            )

            # Simulate automatic trial logging
            for trial_num in range(10):
                tracker.log_trial(
                    experiment_id=exp_id,
                    trial_number=trial_num,
                    params={'lookback': 20 + trial_num},
                    performance={'sharpe': 1.0 + trial_num * 0.05}
                )

            trials = tracker.get_trials(exp_id)
            assert len(trials) == 10

    def test_stores_ttpt_summary(self):
        """Should store TTPT summary from optimize_with_runtime_ttpt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            exp_id = tracker.create_experiment(
                name="TTPT Summary Test",
                template="Momentum",
                mode="tpe_runtime_ttpt"
            )

            # Simulate TTPT summary logging
            ttpt_summary = {
                'total_validations': 5,
                'total_violations': 1,
                'violation_rate': 0.2
            }

            tracker.log_experiment_summary(
                experiment_id=exp_id,
                summary={
                    'ttpt_summary': ttpt_summary,
                    'best_sharpe': 1.5,
                    'n_trials_completed': 50
                }
            )

            # Retrieve and verify
            experiment = tracker.get_experiment(exp_id)
            assert 'summary' in experiment or 'ttpt_summary' in experiment


class TestPerformanceTracking:
    """Test performance tracking and comparison."""

    def test_track_improvement_over_time(self):
        """Should track performance improvement across trials."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            exp_id = tracker.create_experiment(
                name="Improvement Tracking",
                template="Momentum",
                mode="tpe"
            )

            # Log trials with improving performance
            for i in range(10):
                tracker.log_trial(
                    experiment_id=exp_id,
                    trial_number=i,
                    params={'lookback': 20 + i},
                    performance={'sharpe': 1.0 + i * 0.1}
                )

            # Get performance trend
            improvement = tracker.get_performance_improvement(exp_id)

            assert improvement is not None
            assert improvement > 0  # Should show improvement

    def test_compare_experiments(self):
        """Should compare performance across experiments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            # Create two experiments
            exp1 = tracker.create_experiment(
                name="Experiment A",
                template="Momentum",
                mode="tpe"
            )

            exp2 = tracker.create_experiment(
                name="Experiment B",
                template="Momentum",
                mode="tpe"
            )

            # Log different performance levels
            for i in range(5):
                tracker.log_trial(
                    experiment_id=exp1,
                    trial_number=i,
                    params={'lookback': 20},
                    performance={'sharpe': 1.0 + i * 0.1}
                )

                tracker.log_trial(
                    experiment_id=exp2,
                    trial_number=i,
                    params={'lookback': 30},
                    performance={'sharpe': 1.5 + i * 0.1}
                )

            # Compare
            comparison = tracker.compare_experiments([exp1, exp2])

            assert len(comparison) == 2
            assert comparison[1]['best_sharpe'] > comparison[0]['best_sharpe']

    def test_export_to_dataframe(self):
        """Should export experiment results to pandas DataFrame."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = ExperimentTracker(db_path=f"{tmpdir}/experiments.db")

            exp_id = tracker.create_experiment(
                name="Export Test",
                template="Momentum",
                mode="tpe"
            )

            for i in range(5):
                tracker.log_trial(
                    experiment_id=exp_id,
                    trial_number=i,
                    params={'lookback': 20 + i},
                    performance={'sharpe': 1.0 + i * 0.1}
                )

            # Export to DataFrame
            df = tracker.export_to_dataframe(exp_id)

            assert isinstance(df, pd.DataFrame)
            assert len(df) == 5
            assert 'trial_number' in df.columns
            assert 'sharpe' in df.columns or 'performance' in df.columns
