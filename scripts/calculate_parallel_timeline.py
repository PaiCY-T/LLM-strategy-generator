#!/usr/bin/env python3
"""
Timeline Calculator Script for Priority Specs Parallel Execution

Calculates critical path and generates day-by-day schedule for 4 priority specs.
Part of Control Spec: priority-specs-parallel-execution

Usage:
    python scripts/calculate_parallel_timeline.py [--verbose] [--json]

Options:
    --verbose    Show detailed calculation steps
    --json       Output in JSON format instead of formatted text
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque
import json


# Import dependency parsing from validate_spec_dependencies.py
# (We'll import the function directly or copy the logic)


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


def parse_dependency_matrix(control_tasks_md: Path) -> Dict[str, List[str]]:
    """
    Parse dependency matrix from control spec's tasks.md.

    Returns:
        Dict mapping task_id to list of prerequisite task_ids

    Example dependency format in Markdown (inside code blocks):
        Task 7 (Dynamic prompt selection) → Depends: Task 6
        Task 8 (Modification prompts) → Depends: Task 7
        Task 9 (Creation prompts) → Can overlap with Task 8
    """
    if not control_tasks_md.exists():
        raise FileNotFoundError(f"Control spec tasks.md not found: {control_tasks_md}")

    content = control_tasks_md.read_text(encoding='utf-8')

    # Find the Dependency Matrix section
    matrix_section_pattern = re.compile(
        r'## Dependency Matrix\n(.*?)\n## ',
        re.DOTALL
    )
    match = matrix_section_pattern.search(content)
    if not match:
        raise ValueError("Could not find '## Dependency Matrix' section in tasks.md")

    matrix_text = match.group(1)

    # Parse dependencies
    dependencies = {}

    # Pattern: "Task X (...) → Depends: Task Y" or "Task X (...) → Depends: Task Y, Task Z"
    dep_pattern = re.compile(
        r'Task\s+(\d+)\s+\([^)]+\)\s+→\s+Depends:\s+Task\s+([\d,\s]+)',
        re.IGNORECASE
    )

    # Pattern: "Task X (...) → Can overlap with Task Y"
    overlap_pattern = re.compile(
        r'Task\s+(\d+)\s+\([^)]+\)\s+→\s+Can overlap',
        re.IGNORECASE
    )

    # Pattern: "Task X (...) → No dependencies"
    no_dep_pattern = re.compile(
        r'Task\s+(\d+)\s+\([^)]+\)\s+→\s+No dependencies',
        re.IGNORECASE
    )

    # Extract track names (Track 1, Track 2, etc.)
    track_pattern = re.compile(r'###\s+Track\s+(\d+):')

    # Sub-track pattern (Sub-track 2A, etc.)
    subtrack_pattern = re.compile(r'Sub-track\s+(\d+)([A-Z])')

    current_track = None
    current_subtrack = None

    for line in matrix_text.split('\n'):
        # Update current track
        track_match = track_pattern.search(line)
        if track_match:
            track_num = track_match.group(1)
            current_track = f"track-{track_num}"
            current_subtrack = None
            continue

        # Update current sub-track
        subtrack_match = subtrack_pattern.search(line)
        if subtrack_match:
            track_num = subtrack_match.group(1)
            subtrack_letter = subtrack_match.group(2).lower()
            current_track = f"track-{track_num}"
            current_subtrack = f"track-{track_num}{subtrack_letter}"
            continue

        if not current_track:
            continue

        # Use sub-track if available, otherwise use track
        effective_track = current_subtrack if current_subtrack else current_track

        # Check for dependencies
        dep_match = dep_pattern.search(line)
        if dep_match:
            task_num = dep_match.group(1)
            prereq_nums = [n.strip() for n in dep_match.group(2).split(',')]

            task_id = f"{effective_track}-task-{task_num}"
            prereq_ids = [f"{effective_track}-task-{n}" for n in prereq_nums]

            dependencies[task_id] = prereq_ids
            continue

        # Check for no dependencies
        no_dep_match = no_dep_pattern.search(line)
        if no_dep_match:
            task_num = no_dep_match.group(1)
            task_id = f"{effective_track}-task-{task_num}"
            dependencies[task_id] = []
            continue

        # Check for overlap (no dependency, independent task)
        overlap_match = overlap_pattern.search(line)
        if overlap_match:
            task_num = overlap_match.group(1)
            task_id = f"{effective_track}-task-{task_num}"
            if task_id not in dependencies:
                dependencies[task_id] = []

    return dependencies


def parse_task_estimates(control_tasks_md: Path) -> Dict[str, float]:
    """
    Parse task time estimates from control spec's timeline section.

    Returns:
        Dict mapping task_id to estimated hours
    """
    if not control_tasks_md.exists():
        raise FileNotFoundError(f"Control spec tasks.md not found: {control_tasks_md}")

    content = control_tasks_md.read_text(encoding='utf-8')

    # Find the 5-Day Timeline section
    timeline_section_pattern = re.compile(
        r'## 5-Day Timeline\n(.*?)(?:\n## |\Z)',
        re.DOTALL
    )
    match = timeline_section_pattern.search(content)
    if not match:
        raise ValueError("Could not find '## 5-Day Timeline' section in tasks.md")

    timeline_text = match.group(1)

    # Parse task estimates from timeline
    # Format: "Task 7 (2h)" or "Task 5 (start 3h)" or "Task 8 (1h left)"
    estimates = {}

    # Pattern to match task estimates in timeline
    # Examples:
    #   - "Task 7 (2h)"
    #   - "Task 5 (start 3h)" -> 3h remaining
    #   - "Task 8 (1h left)" -> 1h remaining
    #   - "Task 12 (4h complete)" -> 4h total
    # Match both simple "(2h)" and complex "(start 3h)" or "(1h left)"
    task_estimate_pattern = re.compile(
        r'Task\s+(\d+)\s+\((?:start\s+)?(\d+(?:\.\d+)?)\s*h(?:\s+(?:left|complete))?\)',
        re.IGNORECASE
    )

    # Extract track context
    track_pattern = re.compile(r'\*\*Track\s+(\d+[A-Z]?)\*\*:')
    current_track = None
    task_start_hours = {}  # Track "start Xh" for combining with "Xh left"

    for line in timeline_text.split('\n'):
        # Update current track
        track_match = track_pattern.search(line)
        if track_match:
            track_id = track_match.group(1)
            # Normalize track ID (e.g., "2A" -> "track-2a")
            if track_id[-1].isalpha():
                current_track = f"track-{track_id[:-1]}{track_id[-1].lower()}"
            else:
                current_track = f"track-{track_id}"
            # Don't continue - process task estimates on the same line

        if not current_track:
            continue

        # Find all task estimates in this line
        for match in task_estimate_pattern.finditer(line):
            task_num = match.group(1)
            hours = float(match.group(2))

            task_id = f"{current_track}-task-{task_num}"

            # Check if this is a "start Xh" pattern
            full_match_text = match.group(0)
            is_start = "start" in full_match_text.lower()
            is_left = "left" in full_match_text.lower()

            if is_start:
                # Record the start hours for potential combining
                task_start_hours[task_id] = hours
                # Also set the estimate (in case there's no "left" later)
                if task_id not in estimates:
                    estimates[task_id] = hours
            elif is_left:
                # This is hours left - combine with start hours if available
                if task_id in task_start_hours:
                    total_hours = task_start_hours[task_id] + hours
                    estimates[task_id] = total_hours
                else:
                    estimates[task_id] = hours
            else:
                # Regular estimate - only set if not already set
                if task_id not in estimates:
                    estimates[task_id] = hours

    return estimates


def calculate_critical_path(
    dependencies: Dict[str, List[str]],
    estimates: Dict[str, float]
) -> Tuple[List[str], float]:
    """
    Calculate the critical path (longest sequence of dependent tasks).

    Returns:
        Tuple of (critical_path_tasks, total_time)
    """
    # Build reverse dependencies (which tasks depend on this task)
    dependents = defaultdict(list)
    for task, prereqs in dependencies.items():
        for prereq in prereqs:
            dependents[prereq].append(task)

    # Find all tasks (including those not in dependencies dict)
    all_tasks = set(dependencies.keys())
    for prereqs in dependencies.values():
        all_tasks.update(prereqs)

    # Calculate earliest start time for each task using topological sort
    earliest_start = {}
    earliest_finish = {}
    in_degree = defaultdict(int)

    # Initialize in-degrees
    for task in all_tasks:
        in_degree[task] = len(dependencies.get(task, []))

    # Queue of tasks with no prerequisites
    ready_queue = deque([task for task in all_tasks if in_degree[task] == 0])

    # Process tasks in topological order
    while ready_queue:
        task = ready_queue.popleft()

        # Calculate earliest start time (max of all prerequisite finish times)
        prereqs = dependencies.get(task, [])
        if prereqs:
            earliest_start[task] = max(earliest_finish.get(p, 0) for p in prereqs)
        else:
            earliest_start[task] = 0

        # Calculate earliest finish time
        task_duration = estimates.get(task, 1.0)  # Default 1h if not found
        earliest_finish[task] = earliest_start[task] + task_duration

        # Add dependent tasks to queue when their prerequisites are done
        for dependent in dependents[task]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                ready_queue.append(dependent)

    # Find the critical path by backtracking from the task with latest finish time
    if not earliest_finish:
        return [], 0.0

    # Find task with latest finish time
    critical_end = max(earliest_finish.items(), key=lambda x: x[1])
    critical_path = [critical_end[0]]
    current_task = critical_end[0]
    total_time = critical_end[1]

    # Backtrack to find the critical path
    while True:
        prereqs = dependencies.get(current_task, [])
        if not prereqs:
            break

        # Find the prerequisite on the critical path (one with latest finish time)
        critical_prereq = max(prereqs, key=lambda p: earliest_finish.get(p, 0))
        critical_path.insert(0, critical_prereq)
        current_task = critical_prereq

    return critical_path, total_time


def generate_day_schedule(
    dependencies: Dict[str, List[str]],
    estimates: Dict[str, float],
    critical_path: List[str],
    hours_per_day: float = 8.0
) -> List[Dict]:
    """
    Generate day-by-day schedule with parallel tracks.

    Returns:
        List of dictionaries, one per day, with task schedules
    """
    # Track which tasks are completed
    completed = set()
    in_progress = {}  # task_id -> hours_remaining

    # Track for each task
    task_to_track = {}
    for task in dependencies.keys():
        # Extract track from task_id (e.g., "track-2a-task-7" -> "track-2a")
        match = re.match(r'(track-\d+[abc]?)-task-\d+', task)
        if match:
            task_to_track[task] = match.group(1)

    schedule = []
    day_num = 1
    max_days = 10  # Safety limit

    while day_num <= max_days:
        day_schedule = {
            "day": day_num,
            "hours_used": 0.0,
            "tasks": [],
            "completed_tasks": [],
            "tracks": defaultdict(list)
        }

        # Find tasks that can start (all prerequisites complete)
        ready_tasks = []
        for task, prereqs in dependencies.items():
            if task in completed:
                continue
            if task in in_progress:
                continue
            if all(prereq in completed for prereq in prereqs):
                ready_tasks.append(task)

        # Add in-progress tasks to ready list
        for task in in_progress:
            if task not in ready_tasks:
                ready_tasks.append(task)

        if not ready_tasks and not in_progress:
            break  # All tasks complete

        # Allocate time to tasks (simple greedy: process all ready tasks up to 8h)
        hours_used = 0.0

        for task in ready_tasks:
            task_duration = estimates.get(task, 1.0)
            hours_remaining = in_progress.get(task, task_duration)

            # Determine how much time to allocate
            hours_available = hours_per_day - hours_used
            hours_allocated = min(hours_remaining, hours_available)

            if hours_allocated > 0:
                track = task_to_track.get(task, "unknown")

                # Record task work
                task_info = {
                    "task_id": task,
                    "track": track,
                    "hours_allocated": hours_allocated,
                    "hours_remaining": hours_remaining,
                    "on_critical_path": task in critical_path
                }
                day_schedule["tasks"].append(task_info)
                day_schedule["tracks"][track].append(task_info)

                hours_used += hours_allocated
                hours_remaining -= hours_allocated

                # Update task status
                if hours_remaining <= 0.001:  # Floating point tolerance
                    completed.add(task)
                    day_schedule["completed_tasks"].append(task)
                    if task in in_progress:
                        del in_progress[task]
                else:
                    in_progress[task] = hours_remaining

                # Stop if day is full
                if hours_used >= hours_per_day - 0.001:
                    break

        day_schedule["hours_used"] = hours_used
        schedule.append(day_schedule)

        day_num += 1

    return schedule


def format_timeline_output(
    schedule: List[Dict],
    critical_path: List[str],
    critical_path_time: float,
    estimates: Dict[str, float]
) -> str:
    """Format timeline as human-readable text."""
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append("Critical Path Analysis for Priority Specs Parallel Execution")
    lines.append("=" * 80)
    lines.append("")

    # Critical path summary
    lines.append("Critical Path Summary")
    lines.append("-" * 80)
    lines.append(f"Total Time (Critical Path): {critical_path_time:.1f} hours ({critical_path_time/8:.1f} days)")
    lines.append(f"Number of Tasks in Critical Path: {len(critical_path)}")
    lines.append("")

    # Show critical path sequence
    if critical_path:
        # Extract track from first task in critical path
        first_task = critical_path[0]
        match = re.match(r'(track-\d+[abc]?)-task-\d+', first_task)
        critical_track = match.group(1) if match else "unknown"

        lines.append(f"Critical Track: {critical_track.upper()}")
        lines.append("Critical Path Sequence:")

        for i, task in enumerate(critical_path):
            duration = estimates.get(task, 1.0)
            # Extract task number for display
            task_match = re.match(r'.*-task-(\d+)', task)
            task_num = task_match.group(1) if task_match else "?"

            if i == 0:
                lines.append(f"  Task {task_num} ({duration}h)")
            else:
                lines.append(f"    ↓")
                lines.append(f"  Task {task_num} ({duration}h)")

    lines.append("")
    lines.append("=" * 80)
    lines.append("")

    # Day-by-day schedule
    lines.append("Day-by-Day Schedule")
    lines.append("=" * 80)
    lines.append("")

    for day in schedule:
        day_num = day["day"]
        hours_used = day["hours_used"]

        lines.append(f"Day {day_num} ({hours_used:.1f}h used)")
        lines.append("-" * 80)

        if not day["tasks"]:
            lines.append("  No tasks scheduled")
        else:
            # Group by track
            for track in sorted(day["tracks"].keys()):
                track_tasks = day["tracks"][track]

                # Format track line
                track_display = track.upper().replace("TRACK-", "Track ")
                task_details = []

                for task_info in track_tasks:
                    task_id = task_info["task_id"]
                    task_match = re.match(r'.*-task-(\d+)', task_id)
                    task_num = task_match.group(1) if task_match else "?"

                    hours_alloc = task_info["hours_allocated"]
                    hours_remain = task_info["hours_remaining"]

                    critical_marker = " *CRITICAL*" if task_info["on_critical_path"] else ""

                    if task_id in day["completed_tasks"]:
                        task_details.append(f"Task {task_num} ({hours_alloc}h) ✓{critical_marker}")
                    elif hours_remain > hours_alloc:
                        task_details.append(f"Task {task_num} (start {hours_alloc}h){critical_marker}")
                    else:
                        task_details.append(f"Task {task_num} ({hours_alloc}h left){critical_marker}")

                line = f"  {track_display}: " + " → ".join(task_details)
                lines.append(line)

        # Show completions
        if day["completed_tasks"]:
            completed_count = len(day["completed_tasks"])
            lines.append(f"\n  Tasks Completed: {completed_count}")

        lines.append("")

    lines.append("=" * 80)
    lines.append("Legend:")
    lines.append("  ✓ = Task completed this day")
    lines.append("  *CRITICAL* = Task on critical path")
    lines.append("  start Xh = Task started but not finished")
    lines.append("  Xh left = Continuing task from previous day")
    lines.append("=" * 80)

    return "\n".join(lines)


def format_json_output(
    schedule: List[Dict],
    critical_path: List[str],
    critical_path_time: float,
    estimates: Dict[str, float]
) -> str:
    """Format timeline as JSON."""
    output = {
        "critical_path": {
            "tasks": critical_path,
            "total_time_hours": critical_path_time,
            "total_time_days": critical_path_time / 8.0
        },
        "schedule": []
    }

    for day in schedule:
        day_output = {
            "day": day["day"],
            "hours_used": day["hours_used"],
            "tasks": [],
            "completed_tasks": [t for t in day["completed_tasks"]]
        }

        for task_info in day["tasks"]:
            day_output["tasks"].append({
                "task_id": task_info["task_id"],
                "track": task_info["track"],
                "hours_allocated": task_info["hours_allocated"],
                "hours_remaining_after": task_info["hours_remaining"] - task_info["hours_allocated"],
                "on_critical_path": task_info["on_critical_path"],
                "completed": task_info["task_id"] in day["completed_tasks"]
            })

        output["schedule"].append(day_output)

    return json.dumps(output, indent=2)


def main():
    """Main entry point."""
    verbose = '--verbose' in sys.argv
    output_json = '--json' in sys.argv

    try:
        # Find project root
        project_root = find_project_root()
        control_tasks_md = project_root / ".spec-workflow/specs/priority-specs-parallel-execution/tasks.md"

        if verbose:
            print("Parsing dependency matrix from control spec...", file=sys.stderr)

        # Parse dependency matrix
        dependencies = parse_dependency_matrix(control_tasks_md)

        if verbose:
            print(f"Found {len(dependencies)} tasks with dependencies", file=sys.stderr)

        # Parse task estimates
        if verbose:
            print("Parsing task time estimates...", file=sys.stderr)

        estimates = parse_task_estimates(control_tasks_md)

        if verbose:
            print(f"Found time estimates for {len(estimates)} tasks", file=sys.stderr)

        # Calculate critical path
        if verbose:
            print("Calculating critical path...", file=sys.stderr)

        critical_path, critical_path_time = calculate_critical_path(dependencies, estimates)

        if verbose:
            print(f"Critical path: {len(critical_path)} tasks, {critical_path_time:.1f} hours", file=sys.stderr)

        # Generate day-by-day schedule
        if verbose:
            print("Generating day-by-day schedule...", file=sys.stderr)

        schedule = generate_day_schedule(dependencies, estimates, critical_path)

        if verbose:
            print(f"Generated {len(schedule)} day schedule", file=sys.stderr)
            print("", file=sys.stderr)

        # Output results
        if output_json:
            print(format_json_output(schedule, critical_path, critical_path_time, estimates))
        else:
            print(format_timeline_output(schedule, critical_path, critical_path_time, estimates))

        sys.exit(0)

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
