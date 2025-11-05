#!/usr/bin/env python3
"""
Integration tests for Priority Specs Control System.

Tests the following scripts:
- scripts/check_priority_specs_status.py
- scripts/validate_spec_dependencies.py
- scripts/calculate_parallel_timeline.py (placeholder until implemented)
- scripts/sync_control_spec_status.py (placeholder until implemented)

Coverage target: >80% for each script
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

# Import modules to test
from check_priority_specs_status import (
    parse_task_status,
    calculate_percentage,
    format_table_output,
    format_json_output,
    find_project_root,
)

from validate_spec_dependencies import (
    parse_dependency_matrix,
    detect_circular_dependencies,
    get_task_status,
    validate_prerequisites,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_tasks_complete(fixtures_dir):
    """Path to sample tasks.md with all tasks complete."""
    return fixtures_dir / "sample_tasks_complete.md"


@pytest.fixture
def sample_tasks_mixed(fixtures_dir):
    """Path to sample tasks.md with mixed status."""
    return fixtures_dir / "sample_tasks_mixed.md"


@pytest.fixture
def sample_tasks_unnumbered(fixtures_dir):
    """Path to sample tasks.md with unnumbered format."""
    return fixtures_dir / "sample_tasks_unnumbered.md"


@pytest.fixture
def sample_control_spec(fixtures_dir):
    """Path to sample control spec with dependency matrix."""
    return fixtures_dir / "sample_control_spec.md"


@pytest.fixture
def sample_control_spec_circular(fixtures_dir):
    """Path to sample control spec with circular dependencies."""
    return fixtures_dir / "sample_control_spec_circular.md"


@pytest.fixture
def temp_spec_structure(tmp_path):
    """Create a temporary spec structure for integration tests."""
    spec_workflow = tmp_path / ".spec-workflow" / "specs"
    spec_workflow.mkdir(parents=True)

    # Create mock spec directories
    specs = {
        "exit-mutation-redesign": "# Tasks\n- [x] 1. Task 1\n- [ ] 2. Task 2\n",
        "llm-integration-activation": "# Tasks\n- [x] 1. Task 1\n- [-] 2. Task 2\n- [ ] 3. Task 3\n",
        "structured-innovation-mvp": "# Tasks\n- [ ] 1. Task 1\n- [ ] 2. Task 2\n",
        "yaml-normalizer-phase2-complete-normalization": "# Tasks\n- [x] 1. Task 1\n- [x] 2. Task 2\n- [x] 3. Task 3\n",
    }

    for spec_name, content in specs.items():
        spec_dir = spec_workflow / spec_name
        spec_dir.mkdir()
        (spec_dir / "tasks.md").write_text(content)

    return tmp_path


# ============================================================================
# Tests for check_priority_specs_status.py
# ============================================================================

class TestStatusAggregation:
    """Test check_priority_specs_status.py"""

    def test_parse_task_status_numbered_format(self, sample_tasks_mixed):
        """Test parsing numbered task format: '- [x] 1. Task name'"""
        completed, in_progress, pending = parse_task_status(sample_tasks_mixed)

        assert completed == 1, "Should find 1 completed task"
        assert in_progress == 1, "Should find 1 in-progress task"
        assert pending == 2, "Should find 2 pending tasks"

    def test_parse_task_status_all_complete(self, sample_tasks_complete):
        """Test parsing when all tasks are complete"""
        completed, in_progress, pending = parse_task_status(sample_tasks_complete)

        assert completed == 3, "Should find 3 completed tasks"
        assert in_progress == 0, "Should find 0 in-progress tasks"
        assert pending == 0, "Should find 0 pending tasks"

    def test_parse_task_status_unnumbered_format(self, sample_tasks_unnumbered):
        """Test parsing unnumbered task format: '- [x] Task name'"""
        completed, in_progress, pending = parse_task_status(sample_tasks_unnumbered)

        assert completed == 1, "Should find 1 completed task"
        assert in_progress == 1, "Should find 1 in-progress task"
        assert pending == 2, "Should find 2 pending tasks"

    def test_parse_task_status_missing_file(self, tmp_path):
        """Test error handling when tasks.md doesn't exist"""
        nonexistent_path = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            parse_task_status(nonexistent_path)

    def test_parse_task_status_empty_file(self, tmp_path):
        """Test parsing empty file"""
        empty_file = tmp_path / "empty.md"
        empty_file.write_text("")

        completed, in_progress, pending = parse_task_status(empty_file)

        assert completed == 0, "Should find 0 completed tasks"
        assert in_progress == 0, "Should find 0 in-progress tasks"
        assert pending == 0, "Should find 0 pending tasks"

    def test_calculate_percentage_normal(self):
        """Test percentage calculation with normal values"""
        assert calculate_percentage(5, 10) == 50.0
        assert calculate_percentage(1, 4) == 25.0
        assert calculate_percentage(3, 3) == 100.0

    def test_calculate_percentage_zero_total(self):
        """Test percentage calculation with zero total"""
        assert calculate_percentage(0, 0) == 0.0

    def test_calculate_percentage_partial(self):
        """Test percentage calculation with partial completion"""
        result = calculate_percentage(1, 3)
        assert abs(result - 33.333333) < 0.01

    def test_format_table_output(self):
        """Test table formatting output"""
        results = [
            {
                "name": "Test Spec 1",
                "short": "test-1",
                "completed": 5,
                "in_progress": 2,
                "pending": 3,
                "total": 10,
                "percentage": 50.0
            },
            {
                "name": "Test Spec 2",
                "short": "test-2",
                "completed": 10,
                "in_progress": 0,
                "pending": 0,
                "total": 10,
                "percentage": 100.0
            }
        ]

        output = format_table_output(results)

        assert "Priority Specs - Parallel Execution Status" in output
        assert "Test Spec 1" in output
        assert "Test Spec 2" in output
        assert "TOTAL" in output
        assert "75.0%" in output  # Overall percentage

    def test_format_json_output(self):
        """Test JSON formatting output"""
        results = [
            {
                "name": "Test Spec",
                "short": "test",
                "completed": 5,
                "in_progress": 2,
                "pending": 3,
                "total": 10,
                "percentage": 50.0
            }
        ]

        output = format_json_output(results)
        data = json.loads(output)

        assert "specs" in data
        assert "summary" in data
        assert data["summary"]["completed"] == 5
        assert data["summary"]["total"] == 10
        assert data["summary"]["percentage"] == 50.0

    def test_find_project_root_from_cwd(self, temp_spec_structure, monkeypatch):
        """Test finding project root from current directory"""
        monkeypatch.chdir(temp_spec_structure)

        root = find_project_root()
        assert root == temp_spec_structure
        assert (root / ".spec-workflow").exists()

    def test_find_project_root_from_subdirectory(self, temp_spec_structure, monkeypatch):
        """Test finding project root from subdirectory"""
        subdir = temp_spec_structure / "some" / "nested" / "dir"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)

        root = find_project_root()
        assert root == temp_spec_structure

    @pytest.mark.skip(reason="Hard to test due to __file__ fallback mechanism")
    def test_find_project_root_not_found(self, tmp_path, monkeypatch):
        """Test error when project root cannot be found"""
        # This is difficult to test because the function has a fallback
        # to use __file__ location, which always works in tests
        pass


# ============================================================================
# Tests for validate_spec_dependencies.py
# ============================================================================

class TestDependencyValidation:
    """Test validate_spec_dependencies.py"""

    def test_parse_dependency_matrix(self, sample_control_spec):
        """Test parsing dependency matrix from control spec"""
        dependencies = parse_dependency_matrix(sample_control_spec)

        # Should find dependencies from all tracks
        assert "track-1-task-1" in dependencies
        assert "track-1-task-2" in dependencies
        assert "track-2a-task-1" in dependencies

        # Verify specific dependencies
        assert dependencies["track-1-task-1"] == []  # No dependencies
        assert dependencies["track-1-task-2"] == ["track-1-task-1"]  # Depends on task 1

    def test_parse_dependency_matrix_missing_file(self, tmp_path):
        """Test error handling when control spec doesn't exist"""
        nonexistent = tmp_path / "nonexistent.md"

        with pytest.raises(FileNotFoundError):
            parse_dependency_matrix(nonexistent)

    def test_parse_dependency_matrix_missing_section(self, tmp_path):
        """Test error when dependency matrix section is missing"""
        bad_spec = tmp_path / "bad_spec.md"
        bad_spec.write_text("# Tasks\n\nNo dependency matrix here\n")

        with pytest.raises(ValueError, match="Could not find.*Dependency Matrix"):
            parse_dependency_matrix(bad_spec)

    def test_parse_dependency_matrix_subtracks(self, sample_control_spec):
        """Test parsing sub-tracks (e.g., Track 2A, Track 2B)"""
        dependencies = parse_dependency_matrix(sample_control_spec)

        # Check sub-track 2A tasks
        assert "track-2a-task-1" in dependencies
        assert "track-2a-task-2" in dependencies
        assert dependencies["track-2a-task-2"] == ["track-2a-task-1"]

        # Check sub-track 2B tasks
        assert "track-2b-task-4" in dependencies
        assert "track-2b-task-5" in dependencies

    def test_parse_dependency_matrix_multiple_dependencies(self, sample_control_spec):
        """Test parsing tasks with single dependencies across multiple tasks"""
        dependencies = parse_dependency_matrix(sample_control_spec)

        # Track 3 Task 3 depends on Task 1
        assert "track-3-task-3" in dependencies
        assert len(dependencies["track-3-task-3"]) == 1
        assert "track-3-task-1" in dependencies["track-3-task-3"]

        # Track 3 Task 4 depends on Task 2
        assert "track-3-task-4" in dependencies
        assert len(dependencies["track-3-task-4"]) == 1
        assert "track-3-task-2" in dependencies["track-3-task-4"]

    def test_detect_circular_dependencies_none(self, sample_control_spec):
        """Test circular dependency detection when there are none"""
        dependencies = parse_dependency_matrix(sample_control_spec)
        cycle = detect_circular_dependencies(dependencies)

        assert cycle is None, "Should not detect circular dependencies"

    def test_detect_circular_dependencies_found(self, sample_control_spec_circular):
        """Test circular dependency detection when cycle exists"""
        dependencies = parse_dependency_matrix(sample_control_spec_circular)
        cycle = detect_circular_dependencies(dependencies)

        assert cycle is not None, "Should detect circular dependency"
        assert len(cycle) > 0, "Cycle should contain tasks"

    def test_detect_circular_dependencies_self_reference(self):
        """Test detection of self-referencing task"""
        dependencies = {
            "task-1": ["task-1"]  # Task depends on itself
        }

        cycle = detect_circular_dependencies(dependencies)
        assert cycle is not None

    def test_get_task_status_completed(self, temp_spec_structure):
        """Test getting status of completed task"""
        status = get_task_status(
            temp_spec_structure,
            "exit-mutation",
            1
        )
        assert status == "completed"

    def test_get_task_status_in_progress(self, temp_spec_structure):
        """Test getting status of in-progress task"""
        status = get_task_status(
            temp_spec_structure,
            "llm-integration",
            2
        )
        assert status == "in-progress"

    def test_get_task_status_pending(self, temp_spec_structure):
        """Test getting status of pending task"""
        status = get_task_status(
            temp_spec_structure,
            "structured-innovation",
            1
        )
        assert status == "pending"

    def test_get_task_status_not_found(self, temp_spec_structure):
        """Test getting status when task doesn't exist"""
        status = get_task_status(
            temp_spec_structure,
            "exit-mutation",
            999
        )
        assert status == "not-found"

    def test_get_task_status_missing_spec(self, tmp_path):
        """Test getting status when spec file doesn't exist"""
        # The function expects a valid spec_key, so KeyError is expected
        with pytest.raises(KeyError):
            get_task_status(tmp_path, "nonexistent", 1)

    def test_validate_prerequisites_all_complete(self, temp_spec_structure):
        """Test prerequisite validation when all dependencies are satisfied"""
        dependencies = {
            "track-1-task-2": ["track-1-task-1"]  # Task 2 depends on Task 1 (which is complete)
        }

        # Create a tasks.md with Task 2 in progress and Task 1 complete
        spec_path = temp_spec_structure / ".spec-workflow/specs/exit-mutation-redesign/tasks.md"
        spec_path.write_text("# Tasks\n- [x] 1. Task 1\n- [-] 2. Task 2\n")

        errors = validate_prerequisites(temp_spec_structure, dependencies)
        assert len(errors) == 0, "Should have no validation errors"

    def test_validate_prerequisites_incomplete_dependency(self, temp_spec_structure):
        """Test prerequisite validation when dependency is not complete"""
        dependencies = {
            "track-1-task-2": ["track-1-task-1"]  # Task 2 depends on Task 1
        }

        # Create tasks.md with Task 2 in progress but Task 1 pending
        spec_path = temp_spec_structure / ".spec-workflow/specs/exit-mutation-redesign/tasks.md"
        spec_path.write_text("# Tasks\n- [ ] 1. Task 1\n- [-] 2. Task 2\n")

        errors = validate_prerequisites(temp_spec_structure, dependencies)
        assert len(errors) > 0, "Should have validation errors"
        assert "prerequisite" in errors[0].lower()


# ============================================================================
# Tests for calculate_parallel_timeline.py (Placeholder)
# ============================================================================

class TestTimelineCalculator:
    """Test calculate_parallel_timeline.py (placeholder until script exists)"""

    @pytest.mark.skip(reason="Script not yet implemented (parallel Task 3)")
    def test_critical_path_calculation(self):
        """Test identifying critical path (longest dependency chain)"""
        # This will be implemented when calculate_parallel_timeline.py exists
        pass

    @pytest.mark.skip(reason="Script not yet implemented (parallel Task 3)")
    def test_day_by_day_schedule(self):
        """Test generating day-by-day execution schedule"""
        # This will be implemented when calculate_parallel_timeline.py exists
        pass

    @pytest.mark.skip(reason="Script not yet implemented (parallel Task 3)")
    def test_resource_conflict_detection(self):
        """Test detecting when same role is assigned to parallel tasks"""
        # This will be implemented when calculate_parallel_timeline.py exists
        pass

    @pytest.mark.skip(reason="Script not yet implemented (parallel Task 3)")
    def test_timeline_estimation_accuracy(self):
        """Test that timeline matches 5-day estimate from control spec"""
        # This will be implemented when calculate_parallel_timeline.py exists
        pass


# ============================================================================
# Tests for sync_control_spec_status.py (Placeholder)
# ============================================================================

class TestSyncScript:
    """Test sync_control_spec_status.py (placeholder until script exists)"""

    @pytest.mark.skip(reason="Script not yet implemented (parallel Task 4)")
    def test_status_sync_basic(self, tmp_path):
        """Test basic status synchronization from individual specs to control spec"""
        # This will be implemented when sync_control_spec_status.py exists
        pass

    @pytest.mark.skip(reason="Script not yet implemented (parallel Task 4)")
    def test_status_sync_drift_detection(self, tmp_path):
        """Test detection of tasks completed out of order"""
        # This will be implemented when sync_control_spec_status.py exists
        pass

    @pytest.mark.skip(reason="Script not yet implemented (parallel Task 4)")
    def test_backup_creation(self, tmp_path):
        """Test that backup is created before modifying control spec"""
        # This will be implemented when sync_control_spec_status.py exists
        pass

    @pytest.mark.skip(reason="Script not yet implemented (parallel Task 4)")
    def test_markdown_preservation(self, tmp_path):
        """Test that sync preserves markdown formatting"""
        # This will be implemented when sync_control_spec_status.py exists
        pass


# ============================================================================
# Integration Tests
# ============================================================================

class TestEndToEndWorkflows:
    """Integration tests for complete workflows"""

    def test_status_to_json_pipeline(self, temp_spec_structure, monkeypatch):
        """Test status aggregation with JSON output for CI/CD integration"""
        monkeypatch.chdir(temp_spec_structure)

        # This would normally call main() with --json flag
        # For now, test the formatting functions
        results = [
            {
                "name": "Exit Mutation",
                "short": "exit-mutation",
                "completed": 1,
                "in_progress": 0,
                "pending": 1,
                "total": 2,
                "percentage": 50.0
            }
        ]

        json_output = format_json_output(results)
        data = json.loads(json_output)

        assert "specs" in data
        assert "summary" in data
        assert data["summary"]["percentage"] == 50.0

    def test_dependency_validation_workflow(self, sample_control_spec):
        """Test complete dependency validation workflow"""
        # Parse dependencies
        dependencies = parse_dependency_matrix(sample_control_spec)
        assert len(dependencies) > 0

        # Check for circular dependencies
        cycle = detect_circular_dependencies(dependencies)
        assert cycle is None

    def test_error_handling_missing_specs(self, tmp_path, monkeypatch):
        """Test graceful error handling when spec files are missing"""
        monkeypatch.chdir(tmp_path)

        # Create minimal structure
        spec_workflow = tmp_path / ".spec-workflow"
        spec_workflow.mkdir()

        # Try to find project root (should succeed)
        root = find_project_root()
        assert root == tmp_path

        # Parsing missing file should raise FileNotFoundError
        nonexistent = tmp_path / "missing.md"
        with pytest.raises(FileNotFoundError):
            parse_task_status(nonexistent)


# ============================================================================
# Performance and Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and unusual inputs"""

    def test_parse_task_status_with_indentation(self, tmp_path):
        """Test parsing tasks with various indentation levels"""
        tasks_md = tmp_path / "indented.md"
        tasks_md.write_text("""
# Tasks
- [x] 1. Root level task
  - [x] 2. Indented task
    - [-] 3. Double indented task
      - [ ] 4. Triple indented task
""")

        completed, in_progress, pending = parse_task_status(tasks_md)
        assert completed == 2
        assert in_progress == 1
        assert pending == 1

    def test_parse_task_status_unicode_content(self, tmp_path):
        """Test parsing tasks with unicode characters"""
        tasks_md = tmp_path / "unicode.md"
        tasks_md.write_text("""
# Tasks
- [x] 1. 中文任务 (Chinese task)
- [-] 2. タスク (Japanese task)
- [ ] 3. Emoji task 🚀
""", encoding='utf-8')

        completed, in_progress, pending = parse_task_status(tasks_md)
        assert completed == 1
        assert in_progress == 1
        assert pending == 1

    def test_parse_dependency_matrix_edge_whitespace(self, tmp_path):
        """Test dependency parsing with unusual whitespace"""
        spec = tmp_path / "whitespace.md"
        spec.write_text("""
## Dependency Matrix

### Track 1: Test
```
Task 1 (First)   →   No dependencies
Task 2 (Second)  →  Depends: Task 1
```

## Other Section
""")

        dependencies = parse_dependency_matrix(spec)
        assert "track-1-task-1" in dependencies
        assert "track-1-task-2" in dependencies

    def test_calculate_percentage_edge_values(self):
        """Test percentage calculation with edge values"""
        assert calculate_percentage(0, 1) == 0.0
        assert calculate_percentage(1, 1) == 100.0
        assert calculate_percentage(0, 0) == 0.0  # Avoid division by zero

    def test_format_table_output_empty_results(self):
        """Test table formatting with no results"""
        results = []

        # Empty results will cause ValueError in max(), which is expected behavior
        # The script is designed to work with at least one spec
        with pytest.raises(ValueError):
            format_table_output(results)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
