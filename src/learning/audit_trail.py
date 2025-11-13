"""
Phase 4 Audit Trail System: Generation Decision Tracking

This module provides the GenerationDecision dataclass for recording
individual generation decisions made during strategy evolution iterations.

Key Components:
- GenerationDecision: Immutable record of a single generation decision
- AuditLogger: Logger for recording decisions to memory and disk
- Captures configuration snapshot, decision rationale, and outcome
- Designed for JSON serialization to support audit logging

Design Reference: design.md lines 906-956
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class GenerationDecision:
    """
    Record of a single generation decision.

    This dataclass captures all relevant information about a strategy generation
    decision made during an iteration, including the configuration state, the
    decision logic, and the outcome.

    Attributes:
        timestamp: ISO 8601 formatted timestamp of the decision
        iteration_num: Iteration number (0-indexed)
        decision: Decision type ("llm", "factor_graph", or "unknown" on failure)
        reason: Human-readable explanation of why this decision was made
        config_snapshot: Complete copy of the config at decision time
        use_factor_graph: Value of use_factor_graph config (True/False/None)
        innovation_rate: Value of innovation_rate config (0-100)
        success: Whether the generation succeeded (True) or failed (False)
        error: Error message if generation failed, None otherwise

    Usage:
        >>> config = {"use_factor_graph": False, "innovation_rate": 100}
        >>> decision = GenerationDecision(
        ...     timestamp="2024-01-15T10:30:00.000000",
        ...     iteration_num=5,
        ...     decision="llm",
        ...     reason="Config: use_factor_graph=False, innovation_rate=100",
        ...     config_snapshot=config.copy(),
        ...     use_factor_graph=False,
        ...     innovation_rate=100,
        ...     success=True
        ... )
        >>> decision.to_dict()
        {...}  # Dictionary with all fields
    """

    timestamp: str
    iteration_num: int
    decision: str  # "llm", "factor_graph", or "unknown"
    reason: str
    config_snapshot: Dict[str, Any]
    use_factor_graph: Optional[bool]
    innovation_rate: int
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the dataclass to a dictionary for JSON serialization.

        This method uses dataclasses.asdict() to ensure all fields,
        including nested dictionaries in config_snapshot, are properly
        converted to dictionaries.

        Returns:
            dict: Dictionary representation of the decision with all fields

        Example:
            >>> decision.to_dict()
            {
                "timestamp": "2024-01-15T10:30:00.000000",
                "iteration_num": 5,
                "decision": "llm",
                "reason": "Config: use_factor_graph=False, innovation_rate=100",
                "config_snapshot": {"use_factor_graph": False, "innovation_rate": 100},
                "use_factor_graph": False,
                "innovation_rate": 100,
                "success": True,
                "error": None
            }
        """
        return asdict(self)


class AuditLogger:
    """
    Logger for recording generation decisions to memory and disk.

    This class maintains an in-memory list of GenerationDecision records
    and writes them to daily JSONL log files for audit trail persistence.

    Attributes:
        log_dir: Path to the directory for storing log files
        decisions: In-memory list of all logged decisions

    Usage:
        >>> logger = AuditLogger(log_dir="logs/generation_audit")
        >>> config = {"use_factor_graph": False, "innovation_rate": 100}
        >>> logger.log_decision(
        ...     iteration_num=5,
        ...     decision="llm",
        ...     reason="Config: use_factor_graph=False, innovation_rate=100",
        ...     config=config,
        ...     success=True
        ... )
        >>> logger.generate_html_report()

    Design Reference: design.md lines 922-956
    """

    def __init__(self, log_dir: str = "logs/generation_audit"):
        """
        Initialize the AuditLogger with a log directory.

        Args:
            log_dir: Path to the directory for storing log files.
                     Defaults to "logs/generation_audit".
                     Will be created if it doesn't exist.

        Example:
            >>> logger = AuditLogger()  # Uses default directory
            >>> logger = AuditLogger(log_dir="custom/audit/path")
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.decisions: List[GenerationDecision] = []

    def log_decision(
        self,
        iteration_num: int,
        decision: str,
        reason: str,
        config: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None,
    ) -> None:
        """
        Log a generation decision to memory and disk.

        Creates a GenerationDecision record with the provided information,
        appends it to the in-memory list, and writes it to a daily JSONL file.

        Args:
            iteration_num: Iteration number (0-indexed)
            decision: Decision type ("llm", "factor_graph", or "unknown")
            reason: Human-readable explanation of the decision
            config: Configuration dictionary at decision time (will be copied)
            success: Whether the generation succeeded (default: True)
            error: Error message if generation failed (default: None)

        File Format:
            Log files are named "audit_YYYYMMDD.json" and use JSONL format
            (newline-delimited JSON) where each line is a complete JSON object.

        Example:
            >>> logger.log_decision(
            ...     iteration_num=5,
            ...     decision="llm",
            ...     reason="innovation_rate=100 forces LLM",
            ...     config={"innovation_rate": 100},
            ...     success=True
            ... )

        Design Reference: design.md lines 922-956
        """
        # Create timestamp in ISO format
        timestamp = datetime.now().isoformat()

        # Create GenerationDecision record
        record = GenerationDecision(
            timestamp=timestamp,
            iteration_num=iteration_num,
            decision=decision,
            reason=reason,
            config_snapshot=config.copy(),
            use_factor_graph=config.get("use_factor_graph"),
            innovation_rate=config.get("innovation_rate", 100),
            success=success,
            error=error,
        )

        # Append to in-memory list
        self.decisions.append(record)

        # Write to JSONL file (one JSON object per line)
        log_filename = f"audit_{datetime.now().strftime('%Y%m%d')}.json"
        log_file = self.log_dir / log_filename

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def generate_html_report(self, output_file: Optional[str] = None) -> None:
        """
        Generate an HTML report of all logged decisions.

        Creates a comprehensive HTML file with:
        - Summary statistics (total decisions, success rate, violations)
        - Detailed decision table with all fields
        - Violation detection and highlighting
        - Responsive design with proper CSS styling

        Args:
            output_file: Path for the output HTML file.
                        Defaults to "audit_report.html" in the log directory.

        Example:
            >>> logger.generate_html_report()  # Uses default filename
            >>> logger.generate_html_report(output_file="custom_report.html")

        Design Reference: design.md lines 958-961, requirements.md lines 339-343
        """
        # Determine output file path
        if output_file is None:
            output_file = str(self.log_dir / "audit_report.html")

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate statistics
        total_decisions = len(self.decisions)
        successful_decisions = sum(1 for d in self.decisions if d.success)
        failed_decisions = sum(1 for d in self.decisions if not d.success)
        success_rate = (
            (successful_decisions / total_decisions * 100) if total_decisions > 0 else 0
        )

        # Count violations (failures)
        violations = [d for d in self.decisions if not d.success]

        # Generate HTML content
        html_content = self._generate_html_template(
            total_decisions=total_decisions,
            successful_decisions=successful_decisions,
            failed_decisions=failed_decisions,
            success_rate=success_rate,
            violations=violations,
        )

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _generate_html_template(
        self,
        total_decisions: int,
        successful_decisions: int,
        failed_decisions: int,
        success_rate: float,
        violations: List[GenerationDecision],
    ) -> str:
        """
        Generate the HTML template for the audit report.

        Args:
            total_decisions: Total number of decisions
            successful_decisions: Number of successful decisions
            failed_decisions: Number of failed decisions
            success_rate: Success rate percentage
            violations: List of violation (failed) decisions

        Returns:
            str: Complete HTML content
        """
        # Escape HTML special characters in strings
        def escape_html(text: str) -> str:
            """Escape HTML special characters."""
            if text is None:
                return ""
            return (
                str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;")
            )

        # Generate decision table rows
        decision_rows = ""
        for decision in self.decisions:
            # Determine row class based on success/failure
            row_class = "success-row" if decision.success else "failure-row"

            # Format decision method
            decision_method = escape_html(decision.decision.upper().replace("_", " "))

            # Format config snapshot
            config_str = escape_html(json.dumps(decision.config_snapshot, indent=2))

            # Format error (if any)
            error_cell = (
                f'<td class="error-cell">{escape_html(decision.error)}</td>'
                if decision.error
                else "<td>-</td>"
            )

            # Format success/failure with visual indicator
            status_cell = (
                '<td class="success-cell">✓ Success</td>'
                if decision.success
                else '<td class="failure-cell">✗ Failed</td>'
            )

            decision_rows += f"""
                <tr class="{row_class}">
                    <td>{decision.iteration_num}</td>
                    <td>{escape_html(decision.timestamp)}</td>
                    <td class="decision-method">{decision_method}</td>
                    <td>{escape_html(decision.reason)}</td>
                    <td><pre class="config-snapshot">{config_str}</pre></td>
                    {status_cell}
                    {error_cell}
                </tr>
            """

        # Generate violation summary if any exist
        violation_section = ""
        if violations:
            violation_section = f"""
            <div class="violation-section">
                <h2>⚠️ Violations Detected</h2>
                <p class="violation-summary">
                    Found {len(violations)} failed generation attempt(s). These require attention.
                </p>
                <table class="violations-table">
                    <thead>
                        <tr>
                            <th>Iteration</th>
                            <th>Timestamp</th>
                            <th>Intended Method</th>
                            <th>Error Message</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for violation in violations:
                violation_section += f"""
                        <tr>
                            <td>{violation.iteration_num}</td>
                            <td>{escape_html(violation.timestamp)}</td>
                            <td class="decision-method">{escape_html(violation.decision.upper().replace("_", " "))}</td>
                            <td class="error-cell">{escape_html(violation.error or "Unknown error")}</td>
                        </tr>
                """
            violation_section += """
                    </tbody>
                </table>
            </div>
            """

        # Generate complete HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generation Audit Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .statistics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-card h3 {{
            font-size: 1em;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: 700;
            color: #333;
        }}

        .stat-card.success {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: white;
        }}

        .stat-card.success h3 {{
            color: rgba(255, 255, 255, 0.9);
        }}

        .stat-card.success .value {{
            color: white;
        }}

        .stat-card.failure {{
            background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
            color: white;
        }}

        .stat-card.failure h3 {{
            color: rgba(255, 255, 255, 0.9);
        }}

        .stat-card.failure .value {{
            color: white;
        }}

        h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 40px;
            background: white;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 1px;
        }}

        td {{
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        .success-row {{
            background: #f0fdf4;
        }}

        .success-row:hover {{
            background: #dcfce7;
        }}

        .failure-row {{
            background: #fef2f2;
        }}

        .failure-row:hover {{
            background: #fee2e2;
        }}

        .decision-method {{
            font-weight: 600;
            color: #667eea;
            text-transform: uppercase;
            font-size: 0.9em;
        }}

        .config-snapshot {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            font-size: 0.85em;
            overflow-x: auto;
            max-width: 300px;
        }}

        .success-cell {{
            color: #059669;
            font-weight: 600;
        }}

        .failure-cell {{
            color: #dc2626;
            font-weight: 600;
        }}

        .error-cell {{
            color: #dc2626;
            font-size: 0.9em;
            max-width: 300px;
            word-wrap: break-word;
        }}

        .violation-section {{
            background: #fef2f2;
            border: 2px solid #fecaca;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 40px;
        }}

        .violation-section h2 {{
            color: #dc2626;
            border-bottom-color: #dc2626;
        }}

        .violation-summary {{
            font-size: 1.1em;
            color: #991b1b;
            margin-bottom: 20px;
            font-weight: 500;
        }}

        .violations-table {{
            background: white;
        }}

        .no-decisions {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }}

        .no-decisions h2 {{
            font-size: 2em;
            margin-bottom: 20px;
            border: none;
        }}

        @media (max-width: 768px) {{
            .container {{
                border-radius: 0;
            }}

            .statistics {{
                grid-template-columns: 1fr;
            }}

            table {{
                font-size: 0.85em;
            }}

            th, td {{
                padding: 10px;
            }}

            .config-snapshot {{
                max-width: 200px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Generation Audit Report</h1>
            <p>Strategy Evolution Decision Tracking</p>
        </div>

        <div class="content">
            {"" if total_decisions > 0 else '<div class="no-decisions"><h2>No decisions recorded</h2><p>No generation decisions have been logged yet.</p></div>'}

            {f'''
            <div class="statistics">
                <div class="stat-card">
                    <h3>Total Decisions</h3>
                    <div class="value">{total_decisions}</div>
                </div>
                <div class="stat-card success">
                    <h3>Successful</h3>
                    <div class="value">{successful_decisions}</div>
                </div>
                <div class="stat-card failure">
                    <h3>Failed</h3>
                    <div class="value">{failed_decisions}</div>
                </div>
                <div class="stat-card">
                    <h3>Success Rate</h3>
                    <div class="value">{success_rate:.1f}%</div>
                </div>
            </div>

            {violation_section}

            <h2>📋 Decision History</h2>
            <table>
                <thead>
                    <tr>
                        <th>Iteration</th>
                        <th>Timestamp</th>
                        <th>Decision Method</th>
                        <th>Reason</th>
                        <th>Config Snapshot</th>
                        <th>Status</th>
                        <th>Error</th>
                    </tr>
                </thead>
                <tbody>
                    {decision_rows}
                </tbody>
            </table>
            ''' if total_decisions > 0 else ''}
        </div>
    </div>
</body>
</html>
"""
        return html
