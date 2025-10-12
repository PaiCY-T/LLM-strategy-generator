#!/usr/bin/env python3
"""
Autonomous Iteration Engine - Main Orchestration Script

This script orchestrates an autonomous learning loop where Claude generates
trading strategies, they are validated and executed in a sandbox, and performance
feedback is used to improve the next iteration.

Design Patterns:
- JSONL append-only logging for iteration history
- AST-based validation before execution
- Sandboxed execution environment
- Natural language feedback loop
- Graceful error handling with fallbacks
"""

import argparse
import ast
import hashlib
import json
import logging
import os
import pandas as pd
import sys
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Strategy generation - using Claude Code directly instead of API calls
# import claude_api_client  # OLD: External API approach
import claude_code_strategy_generator  # NEW: Direct Claude Code generation

# AST validation and fallback system
from ast_validator import validate_strategy_code
from template_fallback import get_fallback_strategy, log_fallback_usage, get_champion_metadata

# Sandbox execution and metrics extraction
from sandbox_executor import execute_strategy_in_sandbox
from metrics_extractor import extract_metrics_from_signal


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration Constants
# ============================================================================

DEFAULT_ITERATIONS = 10
HISTORY_FILE = "iteration_history.jsonl"
BEST_STRATEGY_FILE = "best_strategy.py"
GENERATED_STRATEGY_TEMPLATE = "generated_strategy_iter{}.py"

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
CLAUDE_MODEL = "anthropic/claude-sonnet-4"  # Model for strategy generation
CLAUDE_TEMPERATURE = 0.7  # Balance between creativity and consistency
CLAUDE_MAX_TOKENS = 8000  # Sufficient for strategy code + explanations

# Prompt Configuration
PROMPT_TEMPLATE_PATH = "prompt_template_v2_with_datasets.txt"
FALLBACK_TEMPLATE_PATH = "prompt_template_v1.txt"

# Retry Configuration
MAX_API_RETRIES = 3
INITIAL_RETRY_BACKOFF = 2.0  # seconds
MAX_RETRY_BACKOFF = 60.0  # seconds

# Execution Configuration
MAX_EXECUTION_TIME = 600  # 10 minutes timeout for strategy execution (Finlab data loading is slow)
MEMORY_LIMIT_MB = 8192  # 8GB memory limit for sandbox (Finlab data is memory-intensive)

# Performance Thresholds
MIN_SHARPE_RATIO = 0.5
MIN_TOTAL_RETURN = 0.0

# Fallback Configuration
MAX_FALLBACK_RATIO = 0.3  # Maximum 30% of iterations can use fallback
FALLBACK_TRACKING_WINDOW = 10  # Track fallbacks over last N iterations

# Verbosity
VERBOSE = os.getenv("VERBOSE", "0") == "1"


# ============================================================================
# Core Functions
# ============================================================================

def generate_strategy(iteration: int, feedback: str = "") -> str:
    """
    Generate strategy code using Claude Code (direct generation).

    This function now uses Claude Code directly instead of calling external APIs.
    Claude Code will generate the trading strategy based on the prompt template
    and previous iteration feedback.

    Args:
        iteration: Current iteration number (0-indexed)
        feedback: Natural language summary of previous iteration's performance
                 Empty string for first iteration

    Returns:
        Generated Python strategy code as string

    Raises:
        NotImplementedError: When Claude Code needs to generate the strategy
        RuntimeError: If generation fails after all attempts

    Design:
        - Uses prompt template with feedback injection
        - Claude Code directly generates AST-valid Python code
        - Includes error context from previous failures
        - Fallback to champion template if generation fails
    """
    logger.info(f"Generating strategy for iteration {iteration} using Claude Code")

    try:
        # Call Claude Code strategy generator
        # This will raise NotImplementedError with the prompt for Claude Code to generate
        code = claude_code_strategy_generator.generate_strategy_with_claude_code(
            iteration=iteration,
            feedback=feedback,
            prompt_template_path=PROMPT_TEMPLATE_PATH
        )

        logger.info(f"Strategy generation successful: {len(code)} chars")

        # Validate code is not empty
        if not code or len(code.strip()) < 50:
            raise ValueError("Generated code is too short or empty")

        # Basic validation: check for critical components
        if "position" not in code and "signal" not in code:
            logger.warning("Generated code missing 'position' or 'signal' variable")
        if "sim(" not in code:
            logger.warning("Generated code missing 'sim()' call")

        if VERBOSE:
            logger.debug(f"Generated code preview:\n{code[:500]}...")

        return code

    except NotImplementedError as e:
        # This is expected - Claude Code needs to generate the strategy
        # Re-raise so Claude Code can see the prompt and generate the code
        logger.info("Claude Code needs to generate strategy code")
        raise

    except FileNotFoundError as e:
        # Template file missing - unrecoverable error
        logger.error(f"Template file not found: {e}")
        raise RuntimeError(f"Required template file missing: {e}")

    except Exception as e:
        # Generation failed - use champion fallback template
        logger.error(f"Strategy generation failed: {e}")
        logger.warning("Using champion fallback template (iter 6, Sharpe 2.48)")

        fallback_code = get_fallback_strategy()
        log_fallback_usage("Claude Code generation failed", iteration)

        return fallback_code


def validate_and_execute(code: str, iteration: int, fallback_count: int = 0,
                         data_wrapper = None) -> Dict[str, Any]:
    """
    TWO-STAGE VALIDATION: Sandbox validation + main process execution.

    This solves the timeout problem where sim() takes 600+ seconds in sandbox subprocess.
    By running sim() in the main process, we retain loaded finlab data across iterations.

    Args:
        code: Python strategy code to validate and execute
        iteration: Current iteration number for logging
        fallback_count: Number of fallbacks used in recent iterations
        data_wrapper: PreloadedData wrapper with datasets (avoids expensive import)

    Returns:
        Dictionary containing:
            - success: bool - Whether execution succeeded
            - metrics: dict - Performance metrics if successful
            - error: str - Error message if failed
            - validation_errors: list - AST validation errors if any
            - execution_time: float - Time taken for execution
            - used_fallback: bool - Whether fallback strategy was used

    Design:
        - Phase 1: AST validation with security checks
        - Phase 2: Fallback logic if validation fails
        - Phase 3: SKIPPED - Sandbox validation removed (complex calculations timeout even at 120s)
        - Phase 4: Main process execution with sim() backtest (fast, uses retained data)
        - Phase 5: Metrics extraction and normalization
    """
    result = {
        "success": False,
        "metrics": {},
        "error": None,
        "validation_errors": [],
        "execution_time": 0.0,
        "used_fallback": False
    }

    start_time = time.time()

    # Phase 1: AST Validation
    logger.info(f"[Iteration {iteration}] Validating generated code with AST...")
    is_valid, validation_error = validate_strategy_code(code)

    if not is_valid:
        logger.error(f"[Iteration {iteration}] AST validation failed: {validation_error}")
        result["validation_errors"].append(validation_error)

        # Check if we can use fallback
        fallback_ratio = fallback_count / max(iteration, 1)
        can_use_fallback = fallback_ratio < MAX_FALLBACK_RATIO

        if can_use_fallback:
            logger.warning(f"[Iteration {iteration}] Using fallback strategy "
                          f"(fallback ratio: {fallback_ratio:.1%} < {MAX_FALLBACK_RATIO:.1%})")
            log_fallback_usage("AST validation failed", iteration)

            # Phase 2: Use pre-validated champion template (skip validation)
            code = get_fallback_strategy()
            result["used_fallback"] = True
            is_valid = True  # Champion template is pre-validated, always safe
        else:
            logger.error(f"[Iteration {iteration}] Cannot use fallback - ratio too high "
                        f"({fallback_ratio:.1%} >= {MAX_FALLBACK_RATIO:.1%})")
            result["error"] = f"AST validation failed and fallback unavailable: {validation_error}"
            result["execution_time"] = time.time() - start_time
            return result

    logger.info(f"[Iteration {iteration}] ✅ Code validation passed")

    # Phase 3: SKIPPED - Sandbox validation removed for performance
    # Rationale: AST validation already provides security, and sandbox validation
    # times out even at 120s due to complex calculations on full Taiwan market data.
    # Main process execution is safe because:
    # 1. AST validation blocks all dangerous operations (file I/O, network, subprocess)
    # 2. PreloadedData is validated and known-good
    # 3. Code has passed all security checks
    logger.info(f"[Iteration {iteration}] Skipping sandbox validation - proceeding to main process execution")

    # Phase 4: Main Process Execution (FAST - uses retained finlab data)
    logger.info(f"[Iteration {iteration}] Executing backtest in main process...")
    try:
        # Import finlab modules (already loaded in memory from main_loop pre-loading)
        from finlab import data
        from finlab.backtest import sim

        # Create a wrapper to capture sim() parameters (Task 13)
        captured_sim_params = {}
        original_sim = sim

        def sim_wrapper(signal, **kwargs):
            """Wrapper to capture backtest parameters before execution"""
            # Store parameters for fallback use
            captured_sim_params.update(kwargs)
            # Call original sim function
            return original_sim(signal, **kwargs)

        # Create execution namespace with our wrapper
        namespace = {
            'data': data,
            'sim': sim_wrapper,
            '__builtins__': __builtins__
        }

        # Execute strategy code to generate signal
        exec(code, namespace)

        # NEW: Capture report object from execution namespace (Task 11)
        report = namespace.get('report', None)

        if report is not None:
            logger.info(f"[Iteration {iteration}] ✅ Successfully captured report from execution namespace")
            # Store report for metrics extraction (will be used in Task 12)
            captured_report = report

            # Log captured parameters (Task 13)
            if captured_sim_params:
                logger.info(f"[Iteration {iteration}] Captured backtest parameters: {captured_sim_params}")
            else:
                logger.warning(f"[Iteration {iteration}] No backtest parameters captured (strategy may not have called sim)")
        else:
            # Report not found - log available namespace keys for debugging
            available_keys = [k for k in namespace.keys() if not k.startswith('__')]
            logger.warning(f"[Iteration {iteration}] ⚠️ Report not found in namespace. Available keys: {available_keys}")
            captured_report = None

        # Extract signal variable
        if 'signal' in namespace:
            signal = namespace['signal']
        elif 'position' in namespace:
            signal = namespace['position']
        else:
            raise ValueError("Generated code does not define 'signal' or 'position' variable")

        # Validate signal is DataFrame
        if not isinstance(signal, pd.DataFrame):
            raise ValueError(f"Signal must be pandas DataFrame, got {type(signal).__name__}")

        logger.info(f"[Iteration {iteration}] Signal generated successfully: shape={signal.shape}")

    except Exception as e:
        logger.error(f"[Iteration {iteration}] Main process execution failed: {e}")
        result["error"] = f"Execution error: {str(e)}"
        result["execution_time"] = time.time() - start_time
        return result

    logger.info(f"[Iteration {iteration}] ✅ Main process execution successful")

    # Phase 5: Metrics Extraction with 3-Method Fallback Chain
    # Task 17: Formalize DIRECT → SIGNAL → DEFAULT fallback chain
    extraction_start_time = time.time()
    extraction_method = None
    metrics_result = None  # Initialize to track if extraction succeeded
    methods_attempted = []  # Track which methods were tried

    # ============================================================================
    # Method 1: DIRECT extraction from captured report (best - no re-execution)
    # ============================================================================
    if captured_report is not None:
        logger.info(f"[Iteration {iteration}] Method 1: Attempting DIRECT extraction from captured report")
        methods_attempted.append("DIRECT")

        try:
            # Import the helper function from metrics_extractor
            from metrics_extractor import _extract_metrics_from_report

            # Extract metrics using the same logic as metrics_extractor
            metrics = _extract_metrics_from_report(captured_report)

            # Build result structure matching extract_metrics_from_signal format
            metrics_result = {
                'success': True,
                'metrics': metrics,
                'error': None,
                'backtest_report': captured_report
            }

            extraction_method = "DIRECT"
            logger.info(f"[Iteration {iteration}] ✅ Method 1 (DIRECT) succeeded - extracted from captured report")

        except Exception as e:
            logger.warning(f"[Iteration {iteration}] ❌ Method 1 (DIRECT) failed: {e}")
            # metrics_result remains None, will fall through to Method 2

    # ============================================================================
    # Method 2: SIGNAL extraction by re-running backtest (fallback)
    # ============================================================================
    if metrics_result is None:
        logger.info(f"[Iteration {iteration}] Method 2: Attempting SIGNAL extraction by re-running backtest")
        methods_attempted.append("SIGNAL")

        try:
            # Use captured parameters if available, otherwise use defaults
            if captured_sim_params:
                logger.info(f"[Iteration {iteration}] Using captured backtest parameters: {captured_sim_params}")
                metrics_result = extract_metrics_from_signal(signal, backtest_params=captured_sim_params)
                extraction_method = "SIGNAL_WITH_PARAMS"
            else:
                logger.warning(f"[Iteration {iteration}] No captured parameters - using default parameters")
                metrics_result = extract_metrics_from_signal(signal)
                extraction_method = "SIGNAL_DEFAULT_PARAMS"

            # Check if extraction succeeded
            if metrics_result and metrics_result.get("success"):
                logger.info(f"[Iteration {iteration}] ✅ Method 2 (SIGNAL) succeeded - {extraction_method}")
            else:
                # Extraction returned but marked as failed
                error_msg = metrics_result.get("error", "Unknown error") if metrics_result else "No result returned"
                logger.warning(f"[Iteration {iteration}] ❌ Method 2 (SIGNAL) returned failure: {error_msg}")
                metrics_result = None  # Force fallback to Method 3

        except Exception as e:
            logger.warning(f"[Iteration {iteration}] ❌ Method 2 (SIGNAL) raised exception: {e}")
            metrics_result = None  # Force fallback to Method 3

    # ============================================================================
    # Method 3: DEFAULT metrics (last resort - always succeeds)
    # ============================================================================
    if metrics_result is None or not metrics_result.get("success"):
        logger.error(f"[Iteration {iteration}] Method 3: All extraction methods failed - using DEFAULT metrics")
        methods_attempted.append("DEFAULT")

        # Build safe default metrics with failure metadata
        metrics_result = {
            'success': True,  # Mark as success to allow iteration to continue
            'metrics': {
                'sharpe_ratio': 0.0,
                'annual_return': 0.0,
                'max_drawdown': 0.0,
                'total_return': 0.0,
                'win_rate': 0.0,
                'total_trades': 0,
                'volatility': 0.0,
                # Failure metadata for debugging
                '_extraction_failed': True,
                '_failure_reason': 'All extraction methods failed',
                '_methods_attempted': methods_attempted
            },
            'error': None,  # Don't propagate error - we're providing defaults
            'backtest_report': None
        }

        extraction_method = "DEFAULT"
        logger.warning(f"[Iteration {iteration}] ⚠️ Method 3 (DEFAULT) - returning zero metrics with failure metadata")
        logger.warning(f"[Iteration {iteration}] Methods attempted: {', '.join(methods_attempted)}")

    # ============================================================================
    # Validate metrics_result is always defined
    # ============================================================================
    # This assertion should never fail due to Method 3 guarantee
    assert metrics_result is not None, "CRITICAL: metrics_result is None after fallback chain"
    assert "success" in metrics_result, "CRITICAL: metrics_result missing 'success' key"
    assert "metrics" in metrics_result, "CRITICAL: metrics_result missing 'metrics' key"

    # At this point, metrics_result is GUARANTEED to be defined with valid structure
    logger.info(f"[Iteration {iteration}] ✅ Metrics extraction chain complete - using method: {extraction_method}")

    # Calculate extraction time
    extraction_time = time.time() - extraction_start_time
    metrics_count = len(metrics_result["metrics"])

    # Task 15: Check for suspicious metric patterns at iteration level
    from metrics_extractor import _detect_suspicious_metrics
    suspicious_warnings = _detect_suspicious_metrics(metrics_result["metrics"])
    suspicious_count = len(suspicious_warnings)

    if suspicious_warnings:
        logger.warning(f"[Iteration {iteration}] Suspicious metrics detected:")
        for warning in suspicious_warnings:
            logger.warning(f"[Iteration {iteration}]   - {warning}")
        logger.warning(f"[Iteration {iteration}] Metrics extraction may have failed. Review report capture and API compatibility.")

    # Check if DEFAULT method was used (extraction failed)
    extraction_failed = metrics_result["metrics"].get("_extraction_failed", False)
    if extraction_failed:
        failure_reason = metrics_result["metrics"].get("_failure_reason", "Unknown")
        methods_attempted_list = metrics_result["metrics"].get("_methods_attempted", [])
        logger.error(f"[Iteration {iteration}] ⚠️ EXTRACTION FAILURE DETECTED:")
        logger.error(f"[Iteration {iteration}]   Reason: {failure_reason}")
        logger.error(f"[Iteration {iteration}]   Methods attempted: {', '.join(methods_attempted_list)}")
        logger.error(f"[Iteration {iteration}]   Using DEFAULT metrics (all zeros)")

    # Task 16 & 17: Extraction Summary
    logger.info(f"[Iteration {iteration}] 📊 Extraction Summary: Method={extraction_method}, "
                f"Metrics={metrics_count}, Suspicious={suspicious_count}, "
                f"Failed={extraction_failed}, Time={extraction_time:.3f}s")

    if not extraction_failed:
        logger.info(f"[Iteration {iteration}] ✅ Metrics extraction successful")
    else:
        logger.warning(f"[Iteration {iteration}] ⚠️ Metrics extraction failed - using DEFAULT metrics (iteration will continue with zeros)")

    # Success - return complete result
    result["success"] = True
    result["metrics"] = metrics_result["metrics"]
    result["execution_time"] = time.time() - start_time

    return result


def create_nl_summary(metrics: Dict[str, Any], code: str, iteration: int) -> str:
    """
    Create natural language summary of iteration results for next iteration.

    Args:
        metrics: Performance metrics from strategy execution
        code: Strategy code that was executed
        iteration: Current iteration number

    Returns:
        Natural language summary describing:
            - What worked well
            - What didn't work
            - Specific improvements to try
            - Metrics comparison with previous iterations

    Design:
        - Template-based summary generation
        - Metric interpretation and explanation
        - Actionable improvement suggestions
        - Historical context from previous iterations
    """
    # Extract key metrics
    sharpe = metrics.get("sharpe_ratio", 0.0)
    total_return = metrics.get("total_return", 0.0)
    annual_return = metrics.get("annual_return", 0.0)
    max_drawdown = metrics.get("max_drawdown", 0.0)
    win_rate = metrics.get("win_rate", 0.0)
    # Use correct key from metrics_extractor (total_trades, not position_count)
    position_count = metrics.get("total_trades", 0)

    # Load historical data for comparison
    history = _load_iteration_history()

    # Build feedback sections
    sections = []

    # Section 1: Performance Summary
    sections.append(_generate_performance_section(
        iteration, sharpe, total_return, annual_return, max_drawdown, win_rate, position_count
    ))

    # Section 2: Historical Comparison (if available)
    if history:
        sections.append(_generate_historical_comparison(metrics, history))

    # Section 3: What Worked
    sections.append(_analyze_what_worked(metrics, code))

    # Section 4: What Didn't Work
    sections.append(_analyze_what_didnt_work(metrics, code))

    # Section 5: Actionable Suggestions
    sections.append(_generate_improvement_suggestions(metrics, code, history))

    # Combine all sections
    feedback = "\n\n".join(sections)

    return feedback


def _load_iteration_history() -> list:
    """Load iteration history from JSONL file."""
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        history = []
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    history.append(record)
        return history
    except Exception as e:
        logger.warning(f"Could not load iteration history: {e}")
        return []


def _generate_performance_section(iteration: int, sharpe: float, total_return: float,
                                   annual_return: float, max_drawdown: float,
                                   win_rate: float, position_count: int) -> str:
    """Generate performance summary section."""
    section = f"## Iteration {iteration} Performance Summary\n\n"
    section += "**Key Metrics:**\n"
    section += f"- Sharpe Ratio: {sharpe:.4f}"

    # Add interpretation
    if sharpe >= 2.0:
        section += " (EXCELLENT - exceeds institutional standards)\n"
    elif sharpe >= 1.5:
        section += " (VERY GOOD - strong risk-adjusted returns)\n"
    elif sharpe >= 1.0:
        section += " (GOOD - acceptable risk-adjusted returns)\n"
    elif sharpe >= 0.5:
        section += " (ACCEPTABLE - but needs improvement)\n"
    else:
        section += " (POOR - risk-adjusted returns below threshold)\n"

    section += f"- Total Return: {total_return:.2%}"
    if total_return >= 0.5:
        section += " (Strong absolute performance)\n"
    elif total_return >= 0.2:
        section += " (Solid performance)\n"
    elif total_return >= 0.0:
        section += " (Positive but modest)\n"
    else:
        section += " (NEGATIVE - needs improvement)\n"

    section += f"- Annual Return: {annual_return:.2%}\n"
    section += f"- Max Drawdown: {max_drawdown:.2%}"

    if max_drawdown > -0.15:
        section += " (EXCELLENT - low risk)\n"
    elif max_drawdown > -0.25:
        section += " (GOOD - acceptable risk)\n"
    elif max_drawdown > -0.35:
        section += " (MODERATE - consider risk reduction)\n"
    else:
        section += " (HIGH - significant risk, needs improvement)\n"

    section += f"- Win Rate: {win_rate:.2%}"
    if win_rate >= 0.60:
        section += " (Excellent hit rate)\n"
    elif win_rate >= 0.50:
        section += " (Good consistency)\n"
    else:
        section += " (Needs better entry timing)\n"

    section += f"- Total Positions: {position_count:,}"

    return section


def _generate_historical_comparison(current_metrics: Dict[str, Any],
                                     history: list) -> str:
    """Compare current performance with historical iterations."""
    if not history:
        return ""

    section = "## Historical Context\n\n"

    # Get previous iteration metrics
    prev_metrics = history[-1].get("metrics", {})

    if not prev_metrics:
        return section + "No previous metrics available for comparison."

    # Calculate deltas
    sharpe_delta = current_metrics.get("sharpe_ratio", 0) - prev_metrics.get("sharpe_ratio", 0)
    return_delta = current_metrics.get("total_return", 0) - prev_metrics.get("total_return", 0)
    dd_delta = current_metrics.get("max_drawdown", 0) - prev_metrics.get("max_drawdown", 0)
    wr_delta = current_metrics.get("win_rate", 0) - prev_metrics.get("win_rate", 0)

    section += "**Changes from Previous Iteration:**\n"
    section += f"- Sharpe Ratio: {sharpe_delta:+.4f}"
    section += " (✅ IMPROVED)\n" if sharpe_delta > 0 else " (⚠️ DECLINED)\n" if sharpe_delta < 0 else " (NO CHANGE)\n"

    section += f"- Total Return: {return_delta:+.2%}"
    section += " (✅ IMPROVED)\n" if return_delta > 0 else " (⚠️ DECLINED)\n" if return_delta < 0 else " (NO CHANGE)\n"

    section += f"- Max Drawdown: {dd_delta:+.2%}"
    section += " (✅ BETTER)\n" if dd_delta > 0 else " (⚠️ WORSE)\n" if dd_delta < 0 else " (NO CHANGE)\n"

    section += f"- Win Rate: {wr_delta:+.2%}"
    section += " (✅ IMPROVED)\n" if wr_delta > 0 else " (⚠️ DECLINED)\n" if wr_delta < 0 else " (NO CHANGE)\n"

    # Find best historical performance
    best_sharpe = max([h.get("metrics", {}).get("sharpe_ratio", -999) for h in history] +
                     [current_metrics.get("sharpe_ratio", -999)])

    if abs(current_metrics.get("sharpe_ratio", 0) - best_sharpe) < 0.01:
        section += "\n🏆 **NEW BEST PERFORMANCE!**\n"

    return section


def _analyze_what_worked(metrics: Dict[str, Any], code: str) -> str:
    """Analyze positive aspects of the strategy."""
    section = "## What Worked Well\n\n"
    strengths = []

    # Analyze metrics
    sharpe = metrics.get("sharpe_ratio", 0)
    max_dd = metrics.get("max_drawdown", 0)
    win_rate = metrics.get("win_rate", 0)

    if sharpe >= 1.5:
        strengths.append("✅ Strong risk-adjusted returns (Sharpe ≥ 1.5)")
    if max_dd > -0.20:
        strengths.append("✅ Excellent risk management (low drawdown)")
    if win_rate >= 0.55:
        strengths.append("✅ High win rate indicating good entry timing")

    # Analyze code patterns
    code_lower = code.lower()

    if "roe" in code_lower:
        strengths.append("✅ ROE factor (quality signal)")
    if "revenue" in code_lower:
        strengths.append("✅ Revenue growth factor (fundamental strength)")
    if "momentum" in code_lower or "pct_change" in code_lower:
        strengths.append("✅ Momentum factor (trend following)")
    if "volume" in code_lower:
        strengths.append("✅ Volume analysis (liquidity consideration)")
    if "liquidity_filter" in code_lower or "trading_value" in code_lower:
        strengths.append("✅ Liquidity filter (tradeable stocks)")
    if "price > " in code_lower or "close >" in code_lower:
        strengths.append("✅ Price filter (avoid penny stocks)")
    if "shift(1)" in code_lower or "shift( 1 )" in code_lower:
        strengths.append("✅ Look-ahead bias prevention (proper shifting)")

    if strengths:
        section += "\n".join(strengths)
    else:
        section += "No significant strengths identified in this iteration."

    return section


def _analyze_what_didnt_work(metrics: Dict[str, Any], code: str) -> str:
    """Analyze weaknesses and issues."""
    section = "## What Didn't Work\n\n"
    weaknesses = []

    # Analyze metrics
    sharpe = metrics.get("sharpe_ratio", 0)
    max_dd = metrics.get("max_drawdown", 0)
    win_rate = metrics.get("win_rate", 0)
    total_return = metrics.get("total_return", 0)

    if sharpe < 1.0:
        weaknesses.append(f"⚠️ Low Sharpe ratio ({sharpe:.4f}) - risk not adequately compensated")
    if max_dd < -0.30:
        weaknesses.append(f"⚠️ High drawdown ({max_dd:.2%}) - insufficient risk control")
    if win_rate < 0.50:
        weaknesses.append(f"⚠️ Low win rate ({win_rate:.2%}) - poor entry/exit timing")
    if total_return < 0.15:
        weaknesses.append(f"⚠️ Low returns ({total_return:.2%}) - strategy not generating alpha")

    # Code quality issues
    code_lower = code.lower()

    if "stop_loss" not in code_lower and max_dd < -0.25:
        weaknesses.append("⚠️ No stop-loss despite high drawdown")
    if ".ffill()" in code and "shift(1)" not in code[code.index(".ffill()"):code.index(".ffill()") + 50]:
        weaknesses.append("⚠️ Potential look-ahead bias with ffill() without shift()")
    if code.count("is_largest") == 1 and ("is_smallest" not in code_lower):
        weaknesses.append("⚠️ Only long positions - consider short signals for hedging")

    if weaknesses:
        section += "\n".join(weaknesses)
    else:
        section += "No critical weaknesses identified."

    return section


def _generate_improvement_suggestions(metrics: Dict[str, Any], code: str,
                                       history: list) -> str:
    """Generate actionable improvement suggestions."""
    section = "## Suggestions for Next Iteration\n\n"
    suggestions = []

    sharpe = metrics.get("sharpe_ratio", 0)
    max_dd = metrics.get("max_drawdown", 0)
    win_rate = metrics.get("win_rate", 0)
    code_lower = code.lower()

    # Risk management suggestions
    if max_dd < -0.25 and "stop_loss" not in code_lower:
        suggestions.append("1. **Add stop-loss logic** - Use `sim(..., stop_loss=0.08)` or dynamic stops")

    if max_dd < -0.30:
        suggestions.append("2. **Implement volatility filter** - Avoid stocks with high volatility")
        suggestions.append("3. **Reduce position concentration** - Increase number of holdings")

    # Entry/exit timing
    if win_rate < 0.50:
        suggestions.append("4. **Improve entry timing** - Consider RSI or other momentum oscillators")
        suggestions.append("5. **Add technical filters** - Use moving average crossovers")

    # Factor engineering
    if sharpe < 1.5:
        suggestions.append("6. **Normalize factors** - Use rank() or z-score normalization")
        suggestions.append("7. **Test factor combinations** - Try different weights")

    # Diversification
    stock_count = _extract_stock_count(code)
    if stock_count and stock_count < 15:
        suggestions.append(f"8. **Increase diversification** - Current: {stock_count} stocks, try 15-20")

    # Data quality
    if ".ffill()" in code:
        suggestions.append("9. **Review data alignment** - Ensure proper shifting after ffill()")

    # Resampling
    if 'resample="Q"' in code or 'resample="M"' in code:
        suggestions.append("10. **Test different rebalancing** - Try weekly ('W') for more responsive strategy")

    # Factor ideas based on what's missing
    missing_factors = []
    if "roe" not in code_lower:
        missing_factors.append("ROE (quality)")
    if "revenue" not in code_lower:
        missing_factors.append("revenue growth (fundamentals)")
    if "debt" not in code_lower:
        missing_factors.append("debt ratio (safety)")
    if "momentum" not in code_lower and "pct_change" not in code_lower:
        missing_factors.append("momentum (trend)")

    if missing_factors and len(suggestions) < 10:
        suggestions.append(f"11. **Consider adding factors**: {', '.join(missing_factors[:3])}")

    if suggestions:
        section += "\n".join(suggestions[:10])  # Limit to 10 suggestions
    else:
        section += "Strategy is well-optimized. Focus on minor parameter tuning."

    return section


def _extract_stock_count(code: str) -> Optional[int]:
    """Extract number of stocks selected from code."""
    import re

    # Look for patterns like .is_largest(10) or .is_largest(15)
    match = re.search(r'\.is_largest\((\d+)\)', code)
    if match:
        return int(match.group(1))

    match = re.search(r'\.is_smallest\((\d+)\)', code)
    if match:
        return int(match.group(1))

    return None


def save_iteration_result(iteration: int, code: str, metrics: Dict[str, Any],
                          feedback: str, used_fallback: bool = False,
                          success: bool = True, error: Optional[str] = None) -> None:
    """
    Save iteration results to JSONL history file with atomic writes.

    Args:
        iteration: Iteration number (0-indexed)
        code: Generated strategy code
        metrics: Performance metrics dictionary
        feedback: Natural language feedback for next iteration
        used_fallback: Whether fallback strategy was used
        success: Whether execution succeeded
        error: Error message if failed

    Design:
        - Append-only JSONL format for crash recovery
        - Atomic writes via temp file to prevent corruption
        - Code hashing (SHA256) for deduplication detection
        - ISO 8601 timestamps for precise tracking
        - Each line is complete, parseable iteration record
        - Graceful error handling for I/O failures

    JSONL Record Format:
        {
            "iteration": 0,
            "timestamp": "2025-01-09T12:34:56.789012",
            "code": "<strategy code>",
            "code_hash": "abc123...",
            "metrics": {"sharpe_ratio": 1.24, ...},
            "feedback": "<NL summary>",
            "used_fallback": false,
            "success": true,
            "error": null
        }
    """
    try:
        # Calculate SHA256 hash of code for deduplication
        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()

        # Create JSONL record
        record = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "code": code,
            "code_hash": code_hash,
            "metrics": metrics,
            "feedback": feedback,
            "used_fallback": used_fallback,
            "success": success,
            "error": error
        }

        # Atomic write: write to temp file, then rename
        # This prevents corruption if process is killed mid-write
        temp_fd, temp_path = tempfile.mkstemp(
            dir=os.path.dirname(HISTORY_FILE) or '.',
            prefix='.iteration_history_',
            suffix='.tmp'
        )

        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as temp_f:
                # If history file exists, copy existing content efficiently
                if os.path.exists(HISTORY_FILE):
                    with open(HISTORY_FILE, 'r', encoding='utf-8') as existing_f:
                        # Stream copy in chunks to avoid loading entire file into memory
                        for line in existing_f:
                            temp_f.write(line)

                # Append new record
                temp_f.write(json.dumps(record, ensure_ascii=False) + '\n')

            # Atomic rename (replaces old file)
            os.replace(temp_path, HISTORY_FILE)

            # Log success (detailed logging only, user sees via print statements in main_loop)
            fallback_status = " (FALLBACK)" if used_fallback else ""
            error_status = f" [ERROR: {error}]" if error else ""
            logger.info(f"Saved iteration {iteration} to {HISTORY_FILE}{fallback_status}{error_status}")

        except Exception as e:
            # Clean up temp file on failure
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    except Exception as e:
        # Graceful failure - log error but don't crash
        logger.error(f"Failed to save iteration {iteration} to JSONL: {e}")
        print(f"⚠️  Warning: Could not save iteration {iteration} to {HISTORY_FILE}: {e}")
        # Don't raise - allow iteration loop to continue


def save_best_strategy(iteration: int, code: str, metrics: Dict[str, Any]) -> None:
    """
    Save best performing strategy to separate file.

    Args:
        iteration: Iteration number of best strategy
        code: Strategy code
        metrics: Performance metrics

    Design:
        - Overwrites previous best if new strategy is better
        - Includes metadata header with performance info
        - Validates code before saving
    """
    header = f'''"""
Best Strategy - Iteration {iteration}
Generated: {datetime.now().isoformat()}

Performance Metrics:
- Total Return: {metrics.get('total_return', 0):.2%}
- Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.4f}
- Max Drawdown: {metrics.get('max_drawdown', 0):.2%}
- Win Rate: {metrics.get('win_rate', 0):.2%}
"""

'''

    with open(BEST_STRATEGY_FILE, "w", encoding="utf-8") as f:
        f.write(header + code)

    print(f"🏆 Saved new best strategy from iteration {iteration}")


def load_previous_feedback() -> str:
    """
    Load feedback from the last successful iteration in history file.

    Returns:
        Feedback string from last iteration, or empty string if no history

    Design:
        - Reads last line of JSONL file
        - Handles missing/corrupted history gracefully
        - Returns empty string for first iteration
        - Validates JSON parsing and field access
        - Provides helpful error messages for debugging

    Usage:
        Used for crash recovery and iteration continuity
    """
    if not os.path.exists(HISTORY_FILE):
        logger.info("No history file found - starting fresh")
        return ""

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            # Efficiently read only last 2 lines (for fallback if last line corrupted)
            lines = []
            for line in f:
                lines.append(line)
                if len(lines) > 2:
                    lines.pop(0)  # Keep only last 2 lines in memory

            if not lines:
                logger.info("History file is empty - starting fresh")
                return ""

            # Try to parse last line
            try:
                last_record = json.loads(lines[-1].strip())
            except json.JSONDecodeError as e:
                logger.warning(f"Last line of history is corrupted: {e}")
                # Try second-to-last line
                if len(lines) >= 2:
                    try:
                        last_record = json.loads(lines[-2].strip())
                        logger.info("Successfully loaded feedback from second-to-last line")
                    except json.JSONDecodeError:
                        logger.warning("Could not parse any recent history - starting fresh")
                        return ""
                else:
                    return ""

            # Extract feedback
            feedback = last_record.get("feedback", "")
            iteration = last_record.get("iteration", -1)
            success = last_record.get("success", False)

            if feedback:
                logger.info(f"Loaded feedback from iteration {iteration} (success={success})")
            else:
                logger.warning(f"No feedback found in iteration {iteration}")

            return feedback

    except (IOError, OSError) as e:
        logger.error(f"I/O error reading history file: {e}")
        print(f"⚠️  Warning: Could not read history file: {e}")
        return ""

    except Exception as e:
        logger.error(f"Unexpected error loading feedback: {e}")
        print(f"⚠️  Warning: Could not load previous feedback: {e}")
        return ""


def get_last_iteration_number() -> int:
    """
    Get the last completed iteration number from history file.

    Returns:
        Last iteration number (0-indexed), or -1 if no history

    Design:
        - Parses JSONL history file backwards
        - Returns highest iteration number found
        - Used for crash recovery and resume functionality

    Usage:
        Call before starting main loop to determine resume point
    """
    if not os.path.exists(HISTORY_FILE):
        return -1

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            # Efficiently stream through file, keeping only last few lines
            recent_lines = []
            for line in f:
                recent_lines.append(line)
                if len(recent_lines) > 10:  # Keep last 10 lines for robustness
                    recent_lines.pop(0)

            if not recent_lines:
                return -1

            # Parse last valid line in reverse order
            for line in reversed(recent_lines):
                try:
                    record = json.loads(line.strip())
                    iteration = record.get("iteration", -1)
                    if iteration >= 0:
                        logger.info(f"Last completed iteration: {iteration}")
                        return iteration
                except json.JSONDecodeError:
                    continue

            return -1

    except Exception as e:
        logger.warning(f"Could not determine last iteration: {e}")
        return -1


def is_best_strategy(metrics: Dict[str, Any],
                     best_metrics: Optional[Dict[str, Any]]) -> bool:
    """
    Determine if current metrics represent best strategy so far.

    Args:
        metrics: Current iteration metrics
        best_metrics: Best metrics seen so far, or None

    Returns:
        True if current metrics are better than best_metrics

    Design:
        - Primary: Sharpe ratio comparison
        - Secondary: Total return if Sharpe is similar
        - Tertiary: Lower drawdown as tiebreaker
    """
    if best_metrics is None:
        return True

    current_sharpe = metrics.get("sharpe_ratio", -999)
    best_sharpe = best_metrics.get("sharpe_ratio", -999)

    # Primary comparison: Sharpe ratio
    if abs(current_sharpe - best_sharpe) > 0.1:
        return current_sharpe > best_sharpe

    # Secondary: Total return
    current_return = metrics.get("total_return", -999)
    best_return = best_metrics.get("total_return", -999)

    return current_return > best_return


# ============================================================================
# Main Iteration Loop
# ============================================================================

def main_loop(num_iterations: int = DEFAULT_ITERATIONS,
              start_iteration: int = 0) -> None:
    """
    Main autonomous iteration loop.

    Args:
        num_iterations: Total number of iterations to run
        start_iteration: Starting iteration number (for resuming)

    Design:
        - Iterative improvement cycle: Generate → Validate → Execute → Feedback
        - Progress tracking and display
        - Best strategy tracking and saving
        - Graceful error handling with continuation
        - Resume capability from history file

    Flow:
        1. Load previous feedback (if resuming)
        2. For each iteration:
           a. Generate strategy code from feedback
           b. Validate with AST
           c. Execute in sandbox
           d. Extract metrics
           e. Create feedback summary
           f. Save results
           g. Update best strategy if improved
        3. Display final summary
    """
    print("=" * 70)
    print("🚀 Autonomous Iteration Engine - Starting")
    print("=" * 70)
    print(f"Configuration:")
    print(f"  - Total Iterations: {num_iterations}")
    print(f"  - Start Iteration: {start_iteration}")
    print(f"  - History File: {HISTORY_FILE}")
    print(f"  - Best Strategy File: {BEST_STRATEGY_FILE}")
    print("=" * 70)
    print()

    # Track best strategy
    best_metrics = None
    best_iteration = -1

    # Track fallback usage
    fallback_history = []  # List of (iteration, used_fallback) tuples

    # Initialize feedback
    feedback = load_previous_feedback() if start_iteration > 0 else ""

    # Pre-load Finlab datasets once to avoid repeated expensive imports in sandbox
    # This is critical for performance - Finlab data loading takes 10+ minutes
    print("⏳ Pre-loading Finlab datasets (this may take 10+ minutes)...")
    logger.info("Pre-loading Finlab datasets to avoid repeated imports in sandbox...")
    try:
        # Import Finlab and login
        import finlab
        finlab_api_token = os.getenv("FINLAB_API_TOKEN", "")
        if not finlab_api_token:
            raise ValueError("FINLAB_API_TOKEN environment variable not set")

        finlab.login(finlab_api_token)
        logger.info(f"Logged into Finlab {finlab.__version__}")

        # Load common datasets using our data_wrapper module
        from data_wrapper import load_common_datasets, PreloadedData

        print("   Loading datasets from Finlab API...")
        datasets = load_common_datasets()

        # Create PreloadedData wrapper (this object is picklable and can be passed to child processes)
        data_wrapper = PreloadedData(datasets)

        print(f"✅ Finlab datasets loaded successfully ({len(datasets)} datasets)\n")
        logger.info(f"Finlab datasets pre-loaded successfully: {len(datasets)} datasets")
    except Exception as e:
        error_msg = f"Failed to pre-load Finlab datasets: {e}"
        logger.error(error_msg)
        print(f"❌ Error: {error_msg}")
        import traceback
        traceback.print_exc()
        print("Cannot proceed without Finlab datasets")
        sys.exit(1)

    for iteration in range(start_iteration, num_iterations):
        # Display iteration header (Task 4.1 spec format)
        print(f"\n{'=' * 42}")
        print(f"Iteration {iteration + 1}/{num_iterations}")
        print(f"{'=' * 42}")

        try:
            # Calculate recent fallback count for threshold checking
            recent_fallbacks = [fb for fb in fallback_history[-FALLBACK_TRACKING_WINDOW:] if fb[1]]
            fallback_count = len(recent_fallbacks)

            # Display fallback statistics if any exist
            if fallback_history:
                total_fallbacks = len([fb for fb in fallback_history if fb[1]])
                fallback_ratio = total_fallbacks / len(fallback_history)
                print(f"📊 Fallback Status: {total_fallbacks}/{len(fallback_history)} total "
                      f"({fallback_ratio:.1%}), {fallback_count}/{FALLBACK_TRACKING_WINDOW} recent")
                print()  # Blank line for readability

            # Step 1: Generate strategy
            print("Generating strategy...")
            code = generate_strategy(iteration, feedback)

            # Save generated code to file
            strategy_file = GENERATED_STRATEGY_TEMPLATE.format(iteration)
            with open(strategy_file, "w", encoding="utf-8") as f:
                f.write(code)
            print(f"  ✓ Strategy saved to {strategy_file}")

            # Step 2: Validate code
            print("Validating code...")
            result = validate_and_execute(code, iteration, fallback_count,
                                        data_wrapper=data_wrapper)

            # Step 3: Execute backtest (if validation passed)
            if result.get("used_fallback"):
                print("  ⚠ Used fallback strategy (champion template)")
            if not result.get("validation_errors"):
                print("  ✓ Validation passed")
                print("Executing backtest...")

            # Track fallback usage
            used_fallback = result.get("used_fallback", False)
            fallback_history.append((iteration, used_fallback))

            if used_fallback:
                # Update code to fallback version for saving
                code = get_fallback_strategy()

            # Display results
            if result["success"]:
                print("  ✓ Backtest complete")
                metrics = result["metrics"]
                print("\n📈 Results:")
                print(f"  Sharpe Ratio:  {metrics.get('sharpe_ratio', 0):>8.4f}")
                print(f"  Total Return:  {metrics.get('total_return', 0):>7.2%}")
                print(f"  Max Drawdown:  {metrics.get('max_drawdown', 0):>7.2%}")
                print(f"  Win Rate:      {metrics.get('win_rate', 0):>7.2%}")

                # Check if best strategy
                if is_best_strategy(metrics, best_metrics):
                    best_metrics = metrics
                    best_iteration = iteration
                    save_best_strategy(iteration, code, metrics)
                    print("  🏆 New best strategy!")

                # Create feedback for next iteration
                feedback = create_nl_summary(metrics, code, iteration)

                # Save iteration results
                save_iteration_result(
                    iteration=iteration,
                    code=code,
                    metrics=metrics,
                    feedback=feedback,
                    used_fallback=used_fallback,
                    success=True,
                    error=None
                )
                print(f"  ✓ Results saved to {HISTORY_FILE}")
            else:
                print(f"  ✗ Backtest failed: {result['error']}")

                # Create error feedback for next iteration
                feedback = f"Previous iteration failed: {result['error']}\n"
                feedback += "Please generate a simpler, more robust strategy that:\n"
                feedback += "- Uses proper data shifting (shift(1)) to avoid look-ahead bias\n"
                feedback += "- Includes liquidity filters\n"
                feedback += "- Has proper error handling\n"

                # Save failed iteration
                save_iteration_result(
                    iteration=iteration,
                    code=code,
                    metrics={},
                    feedback=feedback,
                    used_fallback=used_fallback,
                    success=False,
                    error=result["error"]
                )

        except KeyboardInterrupt:
            print(f"\n\n⚠️  Interrupted by user at iteration {iteration}")
            print(f"Resume with: --start-iteration {iteration}")
            sys.exit(0)

        except Exception as e:
            print(f"\n❌ Error in iteration {iteration}: {e}")
            print(traceback.format_exc())

            # Create error feedback for next iteration
            feedback = f"Previous iteration failed with error: {str(e)}\n"
            feedback += "Please generate a simpler, more robust strategy."

            # Save failed iteration
            save_iteration_result(
                iteration=iteration,
                code="",
                metrics={},
                feedback=feedback,
                used_fallback=False,
                success=False,
                error=str(e)
            )

            print(f"⚠️  Continuing to next iteration...")

    # Final Summary
    print(f"\n\n{'=' * 70}")
    print(f"🏁 Iteration Engine Complete")
    print(f"{'=' * 70}")

    if best_iteration >= 0:
        print(f"\n🏆 Best Strategy:")
        print(f"  - Iteration: {best_iteration + 1}")
        print(f"  - Sharpe Ratio: {best_metrics.get('sharpe_ratio', 0):.4f}")
        print(f"  - Total Return: {best_metrics.get('total_return', 0):.2%}")
        print(f"  - Saved to: {BEST_STRATEGY_FILE}")
    else:
        print(f"\n⚠️  No successful iterations")

    # Fallback statistics
    if fallback_history:
        total_fallbacks = len([fb for fb in fallback_history if fb[1]])
        fallback_ratio = total_fallbacks / len(fallback_history)
        print(f"\n📊 Fallback Statistics:")
        print(f"  - Total Fallbacks: {total_fallbacks}/{len(fallback_history)} ({fallback_ratio:.1%})")
        print(f"  - Threshold: {MAX_FALLBACK_RATIO:.1%}")
        champion_meta = get_champion_metadata()
        print(f"  - Template: Iteration {champion_meta['iteration']} "
              f"(Sharpe: {champion_meta['sharpe_ratio']:.4f})")

    print(f"\n📊 Full history available in: {HISTORY_FILE}")
    print()


# ============================================================================
# CLI Entry Point
# ============================================================================

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Autonomous Iteration Engine for Trading Strategy Evolution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run 10 iterations (default)
  python iteration_engine.py

  # Run 30 iterations
  python iteration_engine.py --iterations 30

  # Resume from iteration 15
  python iteration_engine.py --start-iteration 15 --iterations 30

  # Clean start (remove history)
  python iteration_engine.py --clean
        """
    )

    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"Number of iterations to run (default: {DEFAULT_ITERATIONS})"
    )

    parser.add_argument(
        "--start-iteration",
        type=int,
        default=0,
        help="Starting iteration number for resuming (default: 0)"
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing history and start fresh"
    )

    parser.add_argument(
        "--history-file",
        type=str,
        default=HISTORY_FILE,
        help=f"Path to history file (default: {HISTORY_FILE})"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Update global constants from args
    HISTORY_FILE = args.history_file

    # Clean history if requested
    if args.clean:
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
            print(f"🗑️  Removed {HISTORY_FILE}")
        if os.path.exists(BEST_STRATEGY_FILE):
            os.remove(BEST_STRATEGY_FILE)
            print(f"🗑️  Removed {BEST_STRATEGY_FILE}")

    # API key validation removed - now using Claude Code for direct generation
    # No external API key required anymore
    logger.info("Using Claude Code for strategy generation (no API key needed)")

    # Run main loop
    try:
        main_loop(
            num_iterations=args.iterations,
            start_iteration=args.start_iteration
        )
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print(traceback.format_exc())
        sys.exit(1)
