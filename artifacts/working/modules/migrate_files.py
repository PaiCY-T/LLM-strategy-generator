#!/usr/bin/env python3
"""
Directory reorganization migration script
Moves files according to the reorganization plan
"""
import os
import shutil
import json
from pathlib import Path
from datetime import datetime

# Migration tracking
migration_report = {
    "timestamp": datetime.now().isoformat(),
    "phases": {},
    "errors": [],
    "summary": {}
}

def safe_move(src, dst, phase_name):
    """Safely move a file with error handling"""
    try:
        if not os.path.exists(src):
            migration_report["errors"].append(f"Source not found: {src}")
            return False

        # Create destination directory if needed
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        # Move the file
        shutil.move(src, dst)

        # Track in report
        if phase_name not in migration_report["phases"]:
            migration_report["phases"][phase_name] = {"moved": [], "failed": []}
        migration_report["phases"][phase_name]["moved"].append({"src": src, "dst": dst})

        print(f"✓ Moved: {src} → {dst}")
        return True
    except Exception as e:
        error_msg = f"Failed to move {src} to {dst}: {str(e)}"
        migration_report["errors"].append(error_msg)
        if phase_name not in migration_report["phases"]:
            migration_report["phases"][phase_name] = {"moved": [], "failed": []}
        migration_report["phases"][phase_name]["failed"].append({"src": src, "error": str(e)})
        print(f"✗ Error: {error_msg}")
        return False

def phase_a_strategy_files():
    """Phase A: Move strategy files"""
    print("\n=== Phase A: Moving Strategy Files ===\n")

    moved_count = 0

    # Move iter 0-99 files
    for i in range(150):
        filename = f"generated_strategy_iter{i}.py"
        if os.path.exists(filename):
            if i < 100:
                dst = f"artifacts/strategies/iter_000-099/{filename}"
            else:
                dst = f"artifacts/strategies/iter_100-149/{filename}"
            if safe_move(filename, dst, "Phase A - Iterations"):
                moved_count += 1

    # Move loop iteration files
    import glob
    for filename in glob.glob("generated_strategy_loop_iter*.py"):
        dst = f"artifacts/strategies/{filename}"
        if safe_move(filename, dst, "Phase A - Loop Iterations"):
            moved_count += 1

    # Move other strategy files
    strategy_files = [
        "best_strategy.py",
        "multi_factor_baseline_v1.py",
        "multi_factor_v2_aggressive.py",
        "multi_factor_v3_moonshot.py",
        "multi_factor_v4_final.py",
        "smart_money_momentum_v5.py",
        "smart_money_momentum_v5_simplified.py"
    ]

    for filename in strategy_files:
        if os.path.exists(filename):
            dst = f"artifacts/strategies/{filename}"
            if safe_move(filename, dst, "Phase A - Named Strategies"):
                moved_count += 1

    print(f"\nPhase A: Moved {moved_count} strategy files")
    return moved_count

def phase_b_data_files():
    """Phase B: Move JSON data and configuration files"""
    print("\n=== Phase B: Moving Data and Configuration Files ===\n")

    moved_count = 0

    # Move data files to artifacts/data
    data_files = [
        "champion_strategy.json",
        "iteration_history.json",
        "failure_patterns.json",
        "liquidity_compliance.json",
        "historical_analysis.json",
        "iteration_history_backup_20251009.json"
    ]

    for filename in data_files:
        if os.path.exists(filename):
            dst = f"artifacts/data/{filename}"
            if safe_move(filename, dst, "Phase B - Data Files"):
                moved_count += 1

    # Move configuration files to config/
    config_files = [
        "datasets_curated_50.json",
    ]

    for filename in config_files:
        if os.path.exists(filename):
            dst = f"config/{filename}"
            if safe_move(filename, dst, "Phase B - Config Files"):
                moved_count += 1

    # Move grid search results
    import glob
    for filename in glob.glob("turtle_grid_search_*.json"):
        dst = f"artifacts/reports/grid_search/{filename}"
        if safe_move(filename, dst, "Phase B - Grid Search"):
            moved_count += 1

    print(f"\nPhase B: Moved {moved_count} data/config files")
    return moved_count

def phase_c_docs_and_scripts():
    """Phase C: Move documentation and script files"""
    print("\n=== Phase C: Moving Documentation and Scripts ===\n")

    moved_count = 0

    # Move summary docs
    import glob
    for filename in glob.glob("*_SUMMARY.md") + glob.glob("*_COMPLETE.md"):
        if os.path.exists(filename):
            dst = f"docs/summaries/{filename}"
            if safe_move(filename, dst, "Phase C - Summary Docs"):
                moved_count += 1

    # Move analysis docs
    analysis_patterns = ["LIQUIDITY*.md", "MULTIFACTOR*.md", "MARKET_LIQUIDITY*.md"]
    for pattern in analysis_patterns:
        for filename in glob.glob(pattern):
            if os.path.exists(filename):
                dst = f"docs/analysis/{filename}"
                if safe_move(filename, dst, "Phase C - Analysis Docs"):
                    moved_count += 1

    # Move architecture docs
    arch_docs = [
        "TWO_STAGE_VALIDATION.md",
        "STRATEGY_GENERATION_SYSTEM_SPEC.md",
        "SYSTEM_FIX_AND_VALIDATION_ENHANCEMENT_SPEC.md"
    ]

    for filename in arch_docs:
        if os.path.exists(filename):
            dst = f"docs/architecture/{filename}"
            if safe_move(filename, dst, "Phase C - Architecture Docs"):
                moved_count += 1

    # Check for FEEDBACK_SYSTEM.md in docs/
    if os.path.exists("docs/FEEDBACK_SYSTEM.md"):
        dst = "docs/architecture/FEEDBACK_SYSTEM.md"
        if safe_move("docs/FEEDBACK_SYSTEM.md", dst, "Phase C - Architecture Docs"):
            moved_count += 1

    # Move guide docs
    guide_patterns = ["*QUICK_REFERENCE.md"]
    for pattern in guide_patterns:
        for filename in glob.glob(pattern):
            if os.path.exists(filename):
                dst = f"docs/guides/{filename}"
                if safe_move(filename, dst, "Phase C - Guide Docs"):
                    moved_count += 1

    # Move script files
    script_patterns = [
        "analyze_*.py",
        "demo_*.py",
        "cleanup_*.py",
        "extract_*.py",
        "show_*.py",
        "run_*.py",
        "validate_*.py",
        "turtle_strategy_generator.py"
    ]

    for pattern in script_patterns:
        for filename in glob.glob(pattern):
            if os.path.exists(filename):
                dst = f"scripts/{filename}"
                if safe_move(filename, dst, "Phase C - Scripts"):
                    moved_count += 1

    print(f"\nPhase C: Moved {moved_count} docs/scripts")
    return moved_count

def create_symlinks():
    """Create symbolic links for backward compatibility"""
    print("\n=== Creating Symbolic Links ===\n")

    links = [
        ("artifacts/data/champion_strategy.json", "champion_strategy.json"),
        ("artifacts/data/iteration_history.json", "iteration_history.json"),
        ("artifacts/data/failure_patterns.json", "failure_patterns.json"),
    ]

    created = 0
    for target, link_name in links:
        try:
            if os.path.exists(link_name):
                print(f"⊘ Link already exists: {link_name}")
                continue

            os.symlink(target, link_name)
            print(f"✓ Created symlink: {link_name} → {target}")
            created += 1
        except Exception as e:
            error_msg = f"Failed to create symlink {link_name}: {str(e)}"
            migration_report["errors"].append(error_msg)
            print(f"✗ {error_msg}")

    print(f"\nCreated {created} symbolic links")
    return created

def generate_report():
    """Generate migration report"""
    # Calculate summary
    total_moved = sum(len(phase["moved"]) for phase in migration_report["phases"].values())
    total_failed = sum(len(phase["failed"]) for phase in migration_report["phases"].values())

    migration_report["summary"] = {
        "total_files_moved": total_moved,
        "total_files_failed": total_failed,
        "total_errors": len(migration_report["errors"])
    }

    # Save report
    with open("DIRECTORY_REORGANIZATION_REPORT.json", "w") as f:
        json.dump(migration_report, f, indent=2)

    # Generate markdown report
    md_report = f"""# Directory Reorganization Report

Generated: {migration_report['timestamp']}

## Summary

- **Total files moved**: {total_moved}
- **Total failures**: {total_failed}
- **Total errors**: {len(migration_report['errors'])}

## Phase Results

"""

    for phase_name, phase_data in migration_report["phases"].items():
        md_report += f"\n### {phase_name}\n\n"
        md_report += f"- Moved: {len(phase_data['moved'])} files\n"
        md_report += f"- Failed: {len(phase_data['failed'])} files\n\n"

        if phase_data['failed']:
            md_report += "**Failed files:**\n\n"
            for item in phase_data['failed']:
                md_report += f"- `{item['src']}`: {item['error']}\n"
            md_report += "\n"

    if migration_report["errors"]:
        md_report += "\n## Errors\n\n"
        for error in migration_report["errors"]:
            md_report += f"- {error}\n"

    md_report += "\n## Next Steps\n\n"
    md_report += "1. ✅ Review this report for any errors\n"
    md_report += "2. ✅ Update code path references in:\n"
    md_report += "   - `autonomous_loop.py`\n"
    md_report += "   - Any scripts that reference moved files\n"
    md_report += "3. ✅ Update `.gitignore` to exclude generated files\n"
    md_report += "4. ✅ Test basic functionality\n"
    md_report += "5. ✅ Commit changes to version control\n"

    with open("DIRECTORY_REORGANIZATION_REPORT.md", "w") as f:
        f.write(md_report)

    print("\n" + "="*60)
    print("Migration Report Generated")
    print("="*60)
    print(md_report)

def main():
    """Main migration execution"""
    print("="*60)
    print("Directory Reorganization Migration")
    print("="*60)

    # Execute phases
    phase_a_count = phase_a_strategy_files()
    phase_b_count = phase_b_data_files()
    phase_c_count = phase_c_docs_and_scripts()
    symlink_count = create_symlinks()

    # Generate report
    generate_report()

    print("\n" + "="*60)
    print(f"Migration Complete!")
    print(f"Total files moved: {phase_a_count + phase_b_count + phase_c_count}")
    print(f"Symlinks created: {symlink_count}")
    print("="*60)

if __name__ == "__main__":
    main()
