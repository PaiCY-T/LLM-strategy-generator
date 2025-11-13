#!/usr/bin/env python3
"""
Dependency Validation Script for Priority Specs Parallel Execution

Validates task dependencies and detects circular dependencies.
Part of Control Spec: priority-specs-parallel-execution

Usage:
    python scripts/validate_spec_dependencies.py [--check-prerequisites]

Options:
    --check-prerequisites    Validate that in-progress tasks have prerequisites complete
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from graphlib import TopologicalSorter
import json


# Spec paths for reading task status
SPEC_PATHS = {
    "exit-mutation": ".spec-workflow/specs/exit-mutation-redesign/tasks.md",
    "llm-integration": ".spec-workflow/specs/llm-integration-activation/tasks.md",
    "structured-innovation": ".spec-workflow/specs/structured-innovation-mvp/tasks.md",
    "yaml-normalizer-p2": ".spec-workflow/specs/yaml-normalizer-phase2-complete-normalization/tasks.md"
}


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


def detect_circular_dependencies(dependencies: Dict[str, List[str]]) -> Optional[List[str]]:
    """
    Detect circular dependencies using topological sort.

    Returns:
        None if no cycles, otherwise list of tasks in the cycle
    """
    try:
        # Create TopologicalSorter
        ts = TopologicalSorter(dependencies)
        # Prepare will raise CycleError if there's a cycle
        ts.prepare()
        return None
    except Exception as e:
        # Extract cycle information from exception
        error_str = str(e)
        # Try to parse cycle from error message
        # graphlib.CycleError format: "nodes are in a cycle: ['task1', 'task2', ...]"
        cycle_match = re.search(r'cycle:\s*\[([^\]]+)\]', error_str)
        if cycle_match:
            cycle_str = cycle_match.group(1)
            cycle_tasks = [t.strip().strip("'\"") for t in cycle_str.split(',')]
            return cycle_tasks
        else:
            return ["<cycle detection failed>", error_str]


def get_task_status(project_root: Path, spec_key: str, task_num: int) -> str:
    """
    Get task status from individual spec's tasks.md.

    Returns:
        "completed", "in-progress", "pending", or "not-found"
    """
    spec_path = project_root / SPEC_PATHS[spec_key]

    if not spec_path.exists():
        return "not-found"

    content = spec_path.read_text(encoding='utf-8')

    # Search for task markers
    completed_pattern = re.compile(rf'^\s*-\s*\[x\]\s+(?:\d+\.)?\s*{task_num}\.', re.MULTILINE)
    in_progress_pattern = re.compile(rf'^\s*-\s*\[-\]\s+(?:\d+\.)?\s*{task_num}\.', re.MULTILINE)
    pending_pattern = re.compile(rf'^\s*-\s*\[\s\]\s+(?:\d+\.)?\s*{task_num}\.', re.MULTILINE)

    if completed_pattern.search(content):
        return "completed"
    elif in_progress_pattern.search(content):
        return "in-progress"
    elif pending_pattern.search(content):
        return "pending"
    else:
        return "not-found"


def validate_prerequisites(
    project_root: Path,
    dependencies: Dict[str, List[str]]
) -> List[str]:
    """
    Validate that in-progress tasks have all prerequisites completed.

    Returns:
        List of error messages (empty if all valid)
    """
    errors = []

    for task_id, prereq_ids in dependencies.items():
        # Parse task_id: "track-2a-task-7" → spec_key="llm-integration", task_num=7
        # Map track names to spec keys
        track_to_spec = {
            "track-1": "exit-mutation",
            "track-2a": "llm-integration",
            "track-2b": "llm-integration",
            "track-3a": "structured-innovation",
            "track-3b": "structured-innovation",
            "track-3c": "structured-innovation",
            "track-4": "yaml-normalizer-p2"
        }

        # Extract track and task number
        match = re.match(r'(track-\d+[abc]?)-task-(\d+)', task_id)
        if not match:
            continue

        track_name = match.group(1)
        task_num = int(match.group(2))

        if track_name not in track_to_spec:
            continue

        spec_key = track_to_spec[track_name]
        task_status = get_task_status(project_root, spec_key, task_num)

        # Only check if task is in-progress
        if task_status != "in-progress":
            continue

        # Check all prerequisites
        for prereq_id in prereq_ids:
            prereq_match = re.match(r'(track-\d+[abc]?)-task-(\d+)', prereq_id)
            if not prereq_match:
                continue

            prereq_track = prereq_match.group(1)
            prereq_num = int(prereq_match.group(2))

            if prereq_track not in track_to_spec:
                continue

            prereq_spec = track_to_spec[prereq_track]
            prereq_status = get_task_status(project_root, prereq_spec, prereq_num)

            if prereq_status != "completed":
                errors.append(
                    f"ERROR: {task_id} is in-progress but prerequisite {prereq_id} "
                    f"is {prereq_status} (must be completed)"
                )

    return errors


def main():
    """Main entry point."""
    check_prereqs = '--check-prerequisites' in sys.argv

    try:
        # Find project root
        project_root = find_project_root()
        control_tasks_md = project_root / ".spec-workflow/specs/priority-specs-parallel-execution/tasks.md"

        # Parse dependency matrix
        print("Parsing dependency matrix from control spec...")
        dependencies = parse_dependency_matrix(control_tasks_md)
        print(f"Found {len(dependencies)} tasks with dependencies")

        # Detect circular dependencies
        print("\nChecking for circular dependencies...")
        cycle = detect_circular_dependencies(dependencies)

        if cycle:
            print("❌ CIRCULAR DEPENDENCY DETECTED!")
            print(f"Cycle: {' → '.join(cycle)}")
            sys.exit(1)
        else:
            print("✓ No circular dependencies found")

        # Validate prerequisites (if requested)
        if check_prereqs:
            print("\nValidating task prerequisites...")
            errors = validate_prerequisites(project_root, dependencies)

            if errors:
                print("❌ PREREQUISITE VALIDATION FAILED!")
                for error in errors:
                    print(f"  {error}")
                sys.exit(1)
            else:
                print("✓ All in-progress tasks have prerequisites completed")

        print("\n✅ Dependency validation PASSED")
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
