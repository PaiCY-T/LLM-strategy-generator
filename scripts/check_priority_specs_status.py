#!/usr/bin/env python3
"""
Status Aggregation Script for Priority Specs Parallel Execution

Reads all 4 priority specs' tasks.md files and displays aggregated progress.
Part of Control Spec: priority-specs-parallel-execution

Usage:
    python scripts/check_priority_specs_status.py [--json]

Options:
    --json    Output in JSON format instead of table
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json


# Spec configuration
SPECS = [
    {
        "name": "Exit Mutation Redesign",
        "short": "exit-mutation",
        "path": ".spec-workflow/specs/exit-mutation-redesign/tasks.md"
    },
    {
        "name": "LLM Integration Activation",
        "short": "llm-integration",
        "path": ".spec-workflow/specs/llm-integration-activation/tasks.md"
    },
    {
        "name": "Structured Innovation MVP",
        "short": "structured-innovation",
        "path": ".spec-workflow/specs/structured-innovation-mvp/tasks.md"
    },
    {
        "name": "YAML Normalizer Phase2",
        "short": "yaml-normalizer-p2",
        "path": ".spec-workflow/specs/yaml-normalizer-phase2-complete-normalization/tasks.md"
    }
]


def find_project_root() -> Path:
    """Find project root by looking for .spec-workflow directory."""
    current = Path.cwd()

    # Check current directory and parents
    for path in [current] + list(current.parents):
        if (path / ".spec-workflow").exists():
            return path

    # Fallback: assume script is in scripts/ directory
    script_dir = Path(__file__).parent
    if (script_dir.parent / ".spec-workflow").exists():
        return script_dir.parent

    raise FileNotFoundError(
        "Could not find project root. "
        "Please run from project directory containing .spec-workflow/"
    )


def parse_task_status(tasks_md_path: Path) -> Tuple[int, int, int]:
    """
    Parse tasks.md file and count task statuses.

    Returns:
        Tuple of (completed, in_progress, pending) counts

    Task markers - supports THREE formats:
        1. Checklist: "- [x] 1. Task name" or "- [x] Task name"
        2. Status field: "**Status**: [x] Complete" or "**Status**: [ ] Pending"
        3. Numbered tasks with status field (YAML Normalizer Phase2 format)

    Detection logic:
        - If file contains "## Task N:" headers with "**Status**:" fields, count those
        - Otherwise, count checklist items
    """
    if not tasks_md_path.exists():
        raise FileNotFoundError(f"Tasks file not found: {tasks_md_path}")

    content = tasks_md_path.read_text(encoding='utf-8')

    # Detect format: Look for "## Task N:" headers with **Status**: fields
    task_header_pattern = re.compile(r'^##\s+Task\s+\d+:', re.MULTILINE)
    has_task_headers = bool(task_header_pattern.search(content))

    if has_task_headers:
        # Format 2: Status field format (e.g., YAML Normalizer Phase2)
        # Count "**Status**: [x] Complete" patterns
        completed_pattern = re.compile(r'^\*\*Status\*\*:\s*\[x\]', re.MULTILINE)
        in_progress_pattern = re.compile(r'^\*\*Status\*\*:\s*\[-\]', re.MULTILINE)
        pending_pattern = re.compile(r'^\*\*Status\*\*:\s*\[\s\]', re.MULTILINE)
    else:
        # Format 1: Checklist format (e.g., other specs)
        # Match task lines: "- [x] Task name" or "- [ ] Task name" or "- [-] Task name"
        # Must be at start of line (possibly indented)
        # Supports both numbered ("- [x] 1. Task") and unnumbered ("- [x] Task") formats
        completed_pattern = re.compile(r'^\s*-\s*\[x\]\s+(?:\d+\.)?\s*\S', re.MULTILINE)
        in_progress_pattern = re.compile(r'^\s*-\s*\[-\]\s+(?:\d+\.)?\s*\S', re.MULTILINE)
        pending_pattern = re.compile(r'^\s*-\s*\[\s\]\s+(?:\d+\.)?\s*\S', re.MULTILINE)

    completed = len(completed_pattern.findall(content))
    in_progress = len(in_progress_pattern.findall(content))
    pending = len(pending_pattern.findall(content))

    return completed, in_progress, pending


def calculate_percentage(completed: int, total: int) -> float:
    """Calculate completion percentage."""
    if total == 0:
        return 0.0
    return (completed / total) * 100


def format_table_output(results: List[Dict]) -> str:
    """Format results as ASCII table."""
    # Calculate column widths
    name_width = max(len(r['name']) for r in results) + 2

    # Header
    lines = []
    lines.append("=" * 80)
    lines.append("Priority Specs - Parallel Execution Status")
    lines.append("=" * 80)
    lines.append("")

    # Table header
    header = f"{'Spec Name':<{name_width}} | {'Done':>4} | {'In Progress':>11} | {'Pending':>7} | {'Total':>5} | {'%':>6}"
    lines.append(header)
    lines.append("-" * 80)

    # Table rows
    total_completed = 0
    total_in_progress = 0
    total_pending = 0
    total_tasks = 0

    for r in results:
        name = r['name']
        completed = r['completed']
        in_progress = r['in_progress']
        pending = r['pending']
        total = r['total']
        percentage = r['percentage']

        total_completed += completed
        total_in_progress += in_progress
        total_pending += pending
        total_tasks += total

        # Color coding for terminal (if supported)
        if percentage == 100:
            status_icon = "✓"
        elif in_progress > 0:
            status_icon = "→"
        else:
            status_icon = " "

        row = f"{name:<{name_width}} | {completed:>4} | {in_progress:>11} | {pending:>7} | {total:>5} | {percentage:>5.1f}% {status_icon}"
        lines.append(row)

    # Summary row
    lines.append("-" * 80)
    total_percentage = calculate_percentage(total_completed, total_tasks)
    summary = f"{'TOTAL':<{name_width}} | {total_completed:>4} | {total_in_progress:>11} | {total_pending:>7} | {total_tasks:>5} | {total_percentage:>5.1f}%"
    lines.append(summary)
    lines.append("=" * 80)
    lines.append("")

    # Additional insights
    if total_in_progress > 0:
        lines.append(f"⚡ {total_in_progress} task(s) currently in progress")

    if total_percentage == 100:
        lines.append("🎉 ALL SPECS COMPLETE!")
    elif total_percentage >= 75:
        lines.append("📈 Final sprint - over 75% complete!")
    elif total_percentage >= 50:
        lines.append("📊 Halfway there!")
    elif total_percentage >= 25:
        lines.append("🚀 Good progress - keep going!")
    else:
        lines.append("🏁 Just getting started...")

    lines.append("")

    return "\n".join(lines)


def format_json_output(results: List[Dict]) -> str:
    """Format results as JSON."""
    total_completed = sum(r['completed'] for r in results)
    total_in_progress = sum(r['in_progress'] for r in results)
    total_pending = sum(r['pending'] for r in results)
    total_tasks = sum(r['total'] for r in results)
    total_percentage = calculate_percentage(total_completed, total_tasks)

    output = {
        "specs": results,
        "summary": {
            "completed": total_completed,
            "in_progress": total_in_progress,
            "pending": total_pending,
            "total": total_tasks,
            "percentage": round(total_percentage, 2)
        }
    }

    return json.dumps(output, indent=2)


def main():
    """Main entry point."""
    # Parse arguments
    output_json = '--json' in sys.argv

    try:
        # Find project root
        project_root = find_project_root()

        # Parse each spec
        results = []
        errors = []

        for spec in SPECS:
            spec_path = project_root / spec['path']

            try:
                completed, in_progress, pending = parse_task_status(spec_path)
                total = completed + in_progress + pending
                percentage = calculate_percentage(completed, total)

                results.append({
                    "name": spec['name'],
                    "short": spec['short'],
                    "completed": completed,
                    "in_progress": in_progress,
                    "pending": pending,
                    "total": total,
                    "percentage": round(percentage, 2)
                })
            except FileNotFoundError as e:
                errors.append(f"ERROR: {spec['name']}: {e}")
            except Exception as e:
                errors.append(f"ERROR: {spec['name']}: Unexpected error: {e}")

        # Output results
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            if not results:
                sys.exit(1)

        if output_json:
            print(format_json_output(results))
        else:
            print(format_table_output(results))

        # Exit code: 0 if all complete, 1 if any errors, 2 if in progress
        total_completed = sum(r['completed'] for r in results)
        total_tasks = sum(r['total'] for r in results)

        if errors:
            sys.exit(1)
        elif total_completed == total_tasks and total_tasks > 0:
            sys.exit(0)
        else:
            sys.exit(2)  # In progress

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
