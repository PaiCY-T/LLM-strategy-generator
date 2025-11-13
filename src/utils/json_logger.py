"""
JSON Structured Logging Module for Finlab Trading System.

This module provides structured logging in JSON format for machine-parseable logs
that can be ingested by log aggregation systems (ELK, Splunk, CloudWatch, etc.).

Features:
    - JSON-formatted log output with consistent schema
    - Standard event types for iteration, champion updates, metrics, validation
    - Automatic context enrichment (hostname, process_id, thread_id)
    - Log rotation support
    - Performance metrics tracking
    - Error event standardization

Architecture:
    - JSONFormatter: Converts log records to JSON format
    - EventLogger: High-level API for structured events
    - Standard log schemas for consistent querying

Design Reference: Task 98 from system-fix-validation-enhancement/tasks.md
"""

import json
import logging
import socket
import os
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
from logging.handlers import RotatingFileHandler


# ==============================================================================
# JSON Formatter - Converts log records to JSON format
# ==============================================================================

class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs structured JSON logs.

    Each log record is converted to a JSON object with:
    - Standard fields: timestamp, level, logger, message
    - Context fields: hostname, process_id, thread_id, thread_name
    - Custom fields: Any extra fields passed to log calls

    Example output:
        {
            "timestamp": "2025-10-16T14:30:45.123456",
            "level": "INFO",
            "logger": "autonomous_loop",
            "message": "Iteration started",
            "hostname": "trading-server-1",
            "process_id": 12345,
            "thread_id": 67890,
            "thread_name": "MainThread",
            "event_type": "iteration_start",
            "iteration_num": 42,
            "model": "google/gemini-2.5-flash"
        }
    """

    def __init__(self, include_context: bool = True):
        """
        Initialize JSON formatter.

        Args:
            include_context: Whether to include system context (hostname, PID, etc.)
        """
        super().__init__()
        self.include_context = include_context
        self.hostname = socket.gethostname()
        self.process_id = os.getpid()

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON string.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Build base log entry
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add system context if enabled
        if self.include_context:
            log_data.update({
                "hostname": self.hostname,
                "process_id": self.process_id,
                "thread_id": threading.get_ident(),
                "thread_name": threading.current_thread().name,
            })

        # Add source location
        log_data.update({
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        })

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from log call (e.g., logger.info("msg", extra={...}))
        # Filter out standard LogRecord attributes
        standard_attrs = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName', 'levelname',
            'levelno', 'lineno', 'module', 'msecs', 'message', 'pathname', 'process',
            'processName', 'relativeCreated', 'thread', 'threadName', 'exc_info',
            'exc_text', 'stack_info', 'getMessage', 'taskName'
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith('_'):
                # Serialize complex types
                try:
                    # Test if value is JSON serializable
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    # Convert to string if not serializable
                    log_data[key] = str(value)

        # Return JSON string
        return json.dumps(log_data, ensure_ascii=False, default=str)


# ==============================================================================
# Event Logger - High-level API for structured logging
# ==============================================================================

class EventLogger:
    """
    High-level API for logging structured events with standard schemas.

    Provides convenience methods for common event types in the trading system:
    - Iteration events (start, end, failure)
    - Champion updates (new champion, demotion)
    - Metric extraction (success, failure, method used)
    - Validation results (pass, fail, warnings)
    - Template integration (recommendation, instantiation)

    Usage:
        >>> event_logger = EventLogger("autonomous_loop", log_file="iterations.json.log")
        >>> event_logger.log_iteration_start(iteration_num=42, model="gemini-2.5-flash")
        >>> event_logger.log_champion_update(
        ...     iteration_num=42,
        ...     old_sharpe=2.5,
        ...     new_sharpe=2.8,
        ...     improvement_pct=12.0
        ... )
    """

    def __init__(
        self,
        logger_name: str,
        log_file: Optional[str] = None,
        log_level: int = logging.INFO,
        log_dir: Optional[Path] = None,
        max_bytes: int = 50 * 1024 * 1024,  # 50MB
        backup_count: int = 10
    ):
        """
        Initialize event logger with JSON formatting.

        Args:
            logger_name: Name for the logger (e.g., "autonomous_loop")
            log_file: Log file name (e.g., "iterations.json.log")
            log_level: Minimum log level (default: INFO)
            log_dir: Directory for log files (default: ./logs)
            max_bytes: Max log file size before rotation (default: 50MB)
            backup_count: Number of backup files to keep (default: 10)
        """
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Setup file handler with JSON formatting
        if log_file:
            log_dir = log_dir or Path("./logs")
            log_dir.mkdir(parents=True, exist_ok=True)

            log_path = log_dir / log_file
            handler = RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            handler.setFormatter(JSONFormatter(include_context=True))
            self.logger.addHandler(handler)

    def log_event(self, level: int, event_type: str, message: str, **kwargs):
        """
        Log a structured event with custom fields.

        Args:
            level: Log level (logging.INFO, logging.ERROR, etc.)
            event_type: Event type identifier (e.g., "iteration_start")
            message: Human-readable message
            **kwargs: Additional fields to include in the log
        """
        extra = {"event_type": event_type}
        extra.update(kwargs)
        self.logger.log(level, message, extra=extra)

    # =========================================================================
    # Iteration Events
    # =========================================================================

    def log_iteration_start(
        self,
        iteration_num: int,
        model: str,
        max_iterations: int,
        has_champion: bool
    ):
        """
        Log iteration start event.

        Schema:
            - event_type: "iteration_start"
            - iteration_num: Current iteration number
            - model: LLM model being used
            - max_iterations: Total iterations planned
            - has_champion: Whether a champion exists
        """
        self.log_event(
            logging.INFO,
            "iteration_start",
            f"Starting iteration {iteration_num}/{max_iterations}",
            iteration_num=iteration_num,
            model=model,
            max_iterations=max_iterations,
            has_champion=has_champion
        )

    def log_iteration_end(
        self,
        iteration_num: int,
        success: bool,
        validation_passed: bool,
        execution_success: bool,
        duration_seconds: float,
        metrics: Optional[Dict[str, float]] = None
    ):
        """
        Log iteration end event.

        Schema:
            - event_type: "iteration_end"
            - iteration_num: Completed iteration number
            - success: Overall success (validation AND execution)
            - validation_passed: Whether code validation passed
            - execution_success: Whether strategy execution succeeded
            - duration_seconds: Total iteration time
            - metrics: Performance metrics (optional)
        """
        self.log_event(
            logging.INFO,
            "iteration_end",
            f"Iteration {iteration_num} completed: {'SUCCESS' if success else 'FAILED'}",
            iteration_num=iteration_num,
            success=success,
            validation_passed=validation_passed,
            execution_success=execution_success,
            duration_seconds=duration_seconds,
            metrics=metrics
        )

    def log_iteration_failure(
        self,
        iteration_num: int,
        failure_stage: str,
        error_message: str,
        error_type: Optional[str] = None
    ):
        """
        Log iteration failure event.

        Schema:
            - event_type: "iteration_failure"
            - iteration_num: Failed iteration number
            - failure_stage: Where failure occurred (generation, validation, execution)
            - error_message: Error description
            - error_type: Error class name (optional)
        """
        self.log_event(
            logging.ERROR,
            "iteration_failure",
            f"Iteration {iteration_num} failed at {failure_stage}: {error_message}",
            iteration_num=iteration_num,
            failure_stage=failure_stage,
            error_message=error_message,
            error_type=error_type
        )

    # =========================================================================
    # Champion Events
    # =========================================================================

    def log_champion_update(
        self,
        iteration_num: int,
        old_sharpe: Optional[float],
        new_sharpe: float,
        improvement_pct: float,
        threshold_type: str,
        multi_objective_passed: bool = True
    ):
        """
        Log champion update event.

        Schema:
            - event_type: "champion_update"
            - iteration_num: Iteration that produced new champion
            - old_sharpe: Previous champion Sharpe ratio (null if first)
            - new_sharpe: New champion Sharpe ratio
            - improvement_pct: Percentage improvement
            - threshold_type: "relative" or "absolute"
            - multi_objective_passed: Whether multi-objective validation passed
        """
        self.log_event(
            logging.INFO,
            "champion_update",
            f"Champion updated: Sharpe {old_sharpe or 0:.4f} → {new_sharpe:.4f} (+{improvement_pct:.1f}%)",
            iteration_num=iteration_num,
            old_sharpe=old_sharpe,
            new_sharpe=new_sharpe,
            improvement_pct=improvement_pct,
            threshold_type=threshold_type,
            multi_objective_passed=multi_objective_passed
        )

    def log_champion_rejected(
        self,
        iteration_num: int,
        candidate_sharpe: float,
        champion_sharpe: float,
        rejection_reason: str
    ):
        """
        Log champion update rejection.

        Schema:
            - event_type: "champion_rejected"
            - iteration_num: Iteration number
            - candidate_sharpe: Candidate strategy Sharpe
            - champion_sharpe: Current champion Sharpe
            - rejection_reason: Why update was rejected
        """
        self.log_event(
            logging.INFO,
            "champion_rejected",
            f"Champion update rejected: {rejection_reason}",
            iteration_num=iteration_num,
            candidate_sharpe=candidate_sharpe,
            champion_sharpe=champion_sharpe,
            rejection_reason=rejection_reason
        )

    def log_champion_demotion(
        self,
        old_iteration: int,
        new_iteration: int,
        old_sharpe: float,
        new_sharpe: float,
        demotion_reason: str
    ):
        """
        Log champion demotion due to staleness.

        Schema:
            - event_type: "champion_demotion"
            - old_iteration: Demoted champion iteration
            - new_iteration: New champion iteration
            - old_sharpe: Demoted champion Sharpe
            - new_sharpe: New champion Sharpe
            - demotion_reason: Reason for demotion
        """
        self.log_event(
            logging.INFO,
            "champion_demotion",
            f"Champion demoted: Iteration {old_iteration} → {new_iteration}",
            old_iteration=old_iteration,
            new_iteration=new_iteration,
            old_sharpe=old_sharpe,
            new_sharpe=new_sharpe,
            demotion_reason=demotion_reason
        )

    # =========================================================================
    # Metric Extraction Events
    # =========================================================================

    def log_metric_extraction(
        self,
        iteration_num: int,
        method_used: str,
        success: bool,
        duration_ms: float,
        metrics: Optional[Dict[str, float]] = None,
        fallback_attempts: int = 0
    ):
        """
        Log metric extraction event.

        Schema:
            - event_type: "metric_extraction"
            - iteration_num: Iteration number
            - method_used: "DIRECT", "SIGNAL", or "DEFAULT"
            - success: Whether extraction succeeded
            - duration_ms: Extraction time in milliseconds
            - metrics: Extracted metrics
            - fallback_attempts: Number of fallback attempts
        """
        self.log_event(
            logging.INFO if success else logging.WARNING,
            "metric_extraction",
            f"Metrics extracted via {method_used} in {duration_ms:.1f}ms",
            iteration_num=iteration_num,
            method_used=method_used,
            success=success,
            duration_ms=duration_ms,
            metrics=metrics,
            fallback_attempts=fallback_attempts
        )

    # =========================================================================
    # Validation Events
    # =========================================================================

    def log_validation_result(
        self,
        iteration_num: int,
        validator_name: str,
        passed: bool,
        checks_performed: List[str],
        failures: List[str],
        warnings: List[str],
        duration_ms: float
    ):
        """
        Log validation result event.

        Schema:
            - event_type: "validation_result"
            - iteration_num: Iteration number
            - validator_name: Name of validator (e.g., "MetricValidator")
            - passed: Whether validation passed
            - checks_performed: List of checks executed
            - failures: List of failure messages
            - warnings: List of warning messages
            - duration_ms: Validation time in milliseconds
        """
        self.log_event(
            logging.INFO if passed else logging.WARNING,
            "validation_result",
            f"Validation {validator_name}: {'PASSED' if passed else 'FAILED'}",
            iteration_num=iteration_num,
            validator_name=validator_name,
            passed=passed,
            checks_performed=checks_performed,
            failures=failures,
            warnings=warnings,
            duration_ms=duration_ms
        )

    # =========================================================================
    # Template Integration Events
    # =========================================================================

    def log_template_recommendation(
        self,
        iteration_num: int,
        template_name: str,
        exploration_mode: bool,
        confidence_score: Optional[float] = None
    ):
        """
        Log template recommendation event.

        Schema:
            - event_type: "template_recommendation"
            - iteration_num: Iteration number
            - template_name: Recommended template
            - exploration_mode: Whether in exploration mode
            - confidence_score: Recommendation confidence (optional)
        """
        self.log_event(
            logging.INFO,
            "template_recommendation",
            f"Template recommended: {template_name} (exploration={exploration_mode})",
            iteration_num=iteration_num,
            template_name=template_name,
            exploration_mode=exploration_mode,
            confidence_score=confidence_score
        )

    def log_template_instantiation(
        self,
        iteration_num: int,
        template_name: str,
        success: bool,
        retry_count: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Log template instantiation event.

        Schema:
            - event_type: "template_instantiation"
            - iteration_num: Iteration number
            - template_name: Template being instantiated
            - success: Whether instantiation succeeded
            - retry_count: Number of retries attempted
            - error_message: Error if failed
        """
        self.log_event(
            logging.INFO if success else logging.WARNING,
            "template_instantiation",
            f"Template {template_name}: {'SUCCESS' if success else 'FAILED'}",
            iteration_num=iteration_num,
            template_name=template_name,
            success=success,
            retry_count=retry_count,
            error_message=error_message
        )

    # =========================================================================
    # Performance Events
    # =========================================================================

    def log_performance_metric(
        self,
        operation: str,
        duration_ms: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log performance metric.

        Schema:
            - event_type: "performance_metric"
            - operation: Operation name
            - duration_ms: Duration in milliseconds
            - details: Additional details
        """
        self.log_event(
            logging.DEBUG,
            "performance_metric",
            f"Performance: {operation} took {duration_ms:.1f}ms",
            operation=operation,
            duration_ms=duration_ms,
            details=details or {}
        )


# ==============================================================================
# Convenience Functions
# ==============================================================================

def get_event_logger(
    logger_name: str,
    log_file: Optional[str] = None,
    log_level: int = logging.INFO
) -> EventLogger:
    """
    Get or create an EventLogger instance.

    Args:
        logger_name: Name for the logger
        log_file: Optional log file name
        log_level: Minimum log level

    Returns:
        EventLogger instance

    Example:
        >>> logger = get_event_logger("autonomous_loop", "iterations.json.log")
        >>> logger.log_iteration_start(iteration_num=1, model="gemini-2.5-flash",
        ...                            max_iterations=100, has_champion=False)
    """
    return EventLogger(logger_name, log_file=log_file, log_level=log_level)


def setup_json_logging(
    log_dir: Path = Path("./logs"),
    default_level: int = logging.INFO
) -> None:
    """
    Setup JSON logging for the entire application.

    Creates log directory and configures default JSON formatters.

    Args:
        log_dir: Directory for log files
        default_level: Default log level
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger with JSON formatter
    root_logger = logging.getLogger()
    root_logger.setLevel(default_level)

    # Add JSON file handler to root
    handler = RotatingFileHandler(
        log_dir / "application.json.log",
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding="utf-8"
    )
    handler.setFormatter(JSONFormatter(include_context=True))
    root_logger.addHandler(handler)


# ==============================================================================
# Example Usage
# ==============================================================================

if __name__ == "__main__":
    # Example: Setup and test JSON logging
    print("Testing JSON structured logging...\n")

    # Create event logger
    logger = get_event_logger("test_logger", "test.json.log")

    # Test iteration events
    logger.log_iteration_start(
        iteration_num=1,
        model="google/gemini-2.5-flash",
        max_iterations=10,
        has_champion=False
    )

    logger.log_metric_extraction(
        iteration_num=1,
        method_used="DIRECT",
        success=True,
        duration_ms=45.3,
        metrics={"sharpe_ratio": 2.5, "annual_return": 0.35}
    )

    logger.log_champion_update(
        iteration_num=1,
        old_sharpe=None,
        new_sharpe=2.5,
        improvement_pct=0.0,
        threshold_type="initial"
    )

    logger.log_iteration_end(
        iteration_num=1,
        success=True,
        validation_passed=True,
        execution_success=True,
        duration_seconds=125.7,
        metrics={"sharpe_ratio": 2.5}
    )

    # Test validation event
    logger.log_validation_result(
        iteration_num=1,
        validator_name="MetricValidator",
        passed=True,
        checks_performed=["sharpe_cross_validation", "impossible_combinations"],
        failures=[],
        warnings=[],
        duration_ms=12.4
    )

    print("✓ Test logs written to logs/test.json.log")
    print("\nExample log entry:")
    print(json.dumps({
        "timestamp": "2025-10-16T14:30:45.123456",
        "level": "INFO",
        "logger": "test_logger",
        "message": "Starting iteration 1/10",
        "event_type": "iteration_start",
        "iteration_num": 1,
        "model": "google/gemini-2.5-flash",
        "max_iterations": 10,
        "has_champion": False
    }, indent=2))
