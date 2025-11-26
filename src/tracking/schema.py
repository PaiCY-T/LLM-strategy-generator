"""
Database schema for experiment tracking.

Defines SQLite tables for experiments, trials, and TTPT validation results.
"""

from typing import Dict, Any
import sqlite3
from pathlib import Path


class ExperimentSchema:
    """
    Database schema manager for experiment tracking.

    Tables:
    - experiments: Top-level experiment metadata
    - trials: Individual optimization trials
    - ttpt_results: TTPT validation results per trial
    """

    # SQLite schema definitions
    EXPERIMENTS_TABLE = """
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            template TEXT NOT NULL,
            mode TEXT NOT NULL,
            config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary TEXT
        )
    """

    TRIALS_TABLE = """
        CREATE TABLE IF NOT EXISTS trials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id INTEGER NOT NULL,
            trial_number INTEGER NOT NULL,
            params TEXT NOT NULL,
            performance TEXT NOT NULL,
            strategy_code TEXT,
            strategy_template TEXT,
            generation_method TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (experiment_id) REFERENCES experiments(id)
        )
    """

    TTPT_RESULTS_TABLE = """
        CREATE TABLE IF NOT EXISTS ttpt_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trial_id INTEGER NOT NULL,
            passed BOOLEAN NOT NULL,
            num_violations INTEGER NOT NULL,
            metrics TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trial_id) REFERENCES trials(id)
        )
    """

    @staticmethod
    def create_tables(db_path: str) -> None:
        """
        Create database tables.

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure parent directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute(ExperimentSchema.EXPERIMENTS_TABLE)
        cursor.execute(ExperimentSchema.TRIALS_TABLE)
        cursor.execute(ExperimentSchema.TTPT_RESULTS_TABLE)

        conn.commit()
        conn.close()

    @staticmethod
    def get_schema_version() -> str:
        """Get current schema version."""
        return "1.0.0"
