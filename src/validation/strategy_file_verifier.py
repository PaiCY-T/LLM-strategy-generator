"""
Phase 2 Task 6.1: Strategy File Verification Module

Verifies the existence of generated strategy files from previous phases.
Scans multiple locations for strategy files and provides detailed reports.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class StrategyFileInfo:
    """Information about a discovered strategy file."""
    path: str
    filename: str
    size_bytes: int
    is_readable: bool
    category: str  # 'loop_iteration', 'fixed_iteration', 'innovations_jsonl'


@dataclass
class VerificationResult:
    """Complete verification results."""
    total_strategies_found: int
    total_accessible: int
    by_category: Dict[str, int]
    files: List[StrategyFileInfo]
    innovations_file: Dict[str, any]
    status: str  # 'success', 'partial', 'failed'
    summary: str


class StrategyFileVerifier:
    """Verifies generated strategy files exist and are accessible."""

    def __init__(self, project_root: str = None):
        """
        Initialize verifier with project root path.

        Args:
            project_root: Root directory of project. If None, uses current directory.
        """
        self.project_root = Path(project_root or os.getcwd())
        self.results = None

    def verify(self) -> VerificationResult:
        """
        Main verification method. Scans for strategy files in all locations.

        Returns:
            VerificationResult with complete findings
        """
        files = []
        by_category = {'loop_iteration': 0, 'fixed_iteration': 0, 'innovations_jsonl': 0}

        # Scan for loop iteration strategies
        loop_files = self._scan_loop_iterations()
        files.extend(loop_files)
        by_category['loop_iteration'] = len(loop_files)

        # Scan for fixed iteration strategies
        fixed_files = self._scan_fixed_iterations()
        files.extend(fixed_files)
        by_category['fixed_iteration'] = len(fixed_files)

        # Check innovations.jsonl
        innovations_info = self._check_innovations_file()

        total_accessible = sum(1 for f in files if f.is_readable)
        total_found = len(files)

        # Determine status
        if total_found == 0:
            status = 'failed'
            summary = 'No strategy files found. System may need initialization.'
        elif total_accessible < total_found:
            status = 'partial'
            summary = f'Found {total_found} strategies but {total_found - total_accessible} are inaccessible.'
        else:
            status = 'success'
            summary = f'Successfully verified {total_found} strategy files are accessible.'

        self.results = VerificationResult(
            total_strategies_found=total_found,
            total_accessible=total_accessible,
            by_category=by_category,
            files=files,
            innovations_file=innovations_info,
            status=status,
            summary=summary
        )

        return self.results

    def _scan_loop_iterations(self) -> List[StrategyFileInfo]:
        """Scan for generated_strategy_loop_iter*.py files."""
        files = []
        pattern = self.project_root / 'generated_strategy_loop_iter*.py'

        # Use glob to find matching files
        for filepath in sorted(self.project_root.glob('generated_strategy_loop_iter*.py')):
            file_info = self._get_file_info(filepath, 'loop_iteration')
            if file_info:
                files.append(file_info)

        return files

    def _scan_fixed_iterations(self) -> List[StrategyFileInfo]:
        """Scan for generated_strategy_fixed_iter*.py files."""
        files = []

        # Use glob to find matching files
        for filepath in sorted(self.project_root.glob('generated_strategy_fixed_iter*.py')):
            file_info = self._get_file_info(filepath, 'fixed_iteration')
            if file_info:
                files.append(file_info)

        return files

    def _check_innovations_file(self) -> Dict[str, any]:
        """Check for artifacts/data/innovations.jsonl file."""
        innovations_path = self.project_root / 'artifacts' / 'data' / 'innovations.jsonl'

        result = {
            'exists': False,
            'path': str(innovations_path),
            'size_bytes': 0,
            'is_readable': False,
            'line_count': 0,
            'sample': None
        }

        if not innovations_path.exists():
            return result

        result['exists'] = True

        try:
            size = innovations_path.stat().st_size
            result['size_bytes'] = size

            # Check if readable
            with open(innovations_path, 'r') as f:
                result['is_readable'] = True

                # Count lines and get sample
                lines = []
                for i, line in enumerate(f):
                    lines.append(line.rstrip())
                    if i >= 2:  # Get first 3 lines as sample
                        break

                result['line_count'] = i + 1
                result['sample'] = lines[0] if lines else None

        except Exception as e:
            logger.warning(f"Error reading innovations file: {e}")
            result['is_readable'] = False

        return result

    def _get_file_info(self, filepath: Path, category: str) -> StrategyFileInfo:
        """Get information about a strategy file."""
        try:
            size = filepath.stat().st_size

            # Check readability
            is_readable = False
            try:
                with open(filepath, 'r') as f:
                    f.read(100)  # Try reading first 100 chars
                    is_readable = True
            except Exception:
                pass

            return StrategyFileInfo(
                path=str(filepath),
                filename=filepath.name,
                size_bytes=size,
                is_readable=is_readable,
                category=category
            )

        except Exception as e:
            logger.warning(f"Error getting file info for {filepath}: {e}")
            return None

    def get_report(self) -> str:
        """Generate a human-readable report of verification results."""
        if not self.results:
            return "No verification results. Run verify() first."

        lines = [
            "=" * 70,
            "STRATEGY FILE VERIFICATION REPORT",
            "=" * 70,
            "",
            f"Status: {self.results.status.upper()}",
            f"Summary: {self.results.summary}",
            "",
            "COUNTS:",
            f"  Total strategies found: {self.results.total_strategies_found}",
            f"  Total accessible: {self.results.total_accessible}",
            "",
            "BREAKDOWN BY CATEGORY:",
            f"  Loop iterations (generated_strategy_loop_iter*.py): {self.results.by_category['loop_iteration']}",
            f"  Fixed iterations (generated_strategy_fixed_iter*.py): {self.results.by_category['fixed_iteration']}",
            "",
            "INNOVATIONS FILE:",
            f"  Path: {self.results.innovations_file['path']}",
            f"  Exists: {self.results.innovations_file['exists']}",
            f"  Readable: {self.results.innovations_file['is_readable']}",
            f"  Size: {self.results.innovations_file['size_bytes']} bytes",
            f"  Lines: {self.results.innovations_file['line_count']}",
        ]

        if self.results.innovations_file['sample']:
            lines.append(f"  Sample: {self.results.innovations_file['sample'][:100]}...")

        lines.extend([
            "",
            "FILES FOUND:",
        ])

        # Group files by category
        by_cat = {}
        for f in self.results.files:
            if f.category not in by_cat:
                by_cat[f.category] = []
            by_cat[f.category].append(f)

        for category in ['loop_iteration', 'fixed_iteration']:
            if category in by_cat:
                files = by_cat[category]
                lines.append(f"\n  {category.upper()}:")
                for f in files[:5]:  # Show first 5 of each category
                    status = "OK" if f.is_readable else "UNREADABLE"
                    lines.append(f"    {f.filename} ({f.size_bytes} bytes) [{status}]")

                if len(files) > 5:
                    lines.append(f"    ... and {len(files) - 5} more")

        lines.extend([
            "",
            "=" * 70,
        ])

        return "\n".join(lines)

    def to_json(self) -> str:
        """Export results as JSON."""
        if not self.results:
            return json.dumps({"error": "No verification results"})

        files_data = [asdict(f) for f in self.results.files]

        data = {
            'total_strategies_found': self.results.total_strategies_found,
            'total_accessible': self.results.total_accessible,
            'by_category': self.results.by_category,
            'status': self.results.status,
            'summary': self.results.summary,
            'innovations_file': self.results.innovations_file,
            'files': files_data
        }

        return json.dumps(data, indent=2)


def verify_strategies(project_root: str = None) -> VerificationResult:
    """
    Convenience function to verify strategies.

    Args:
        project_root: Root directory of project

    Returns:
        VerificationResult with findings
    """
    verifier = StrategyFileVerifier(project_root)
    return verifier.verify()


def main():
    """CLI entry point."""
    import sys

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Get project root from args or use current directory
    project_root = sys.argv[1] if len(sys.argv) > 1 else None

    verifier = StrategyFileVerifier(project_root)
    results = verifier.verify()

    # Print report
    print(verifier.get_report())

    # Print JSON if requested
    if '--json' in sys.argv:
        print("\nJSON OUTPUT:")
        print(verifier.to_json())

    # Exit with appropriate code
    if results.status == 'failed':
        sys.exit(1)
    elif results.status == 'partial':
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
