#!/usr/bin/env python3
"""
Duplicate Detection Script (Task 2.2)
======================================

Standalone script to detect duplicate strategies in validation results.

This script:
1. Loads validation results JSON from file path argument
2. Scans strategy files (generated_strategy_loop_iter*.py)
3. Runs DuplicateDetector.find_duplicates()
4. Generates JSON report and Markdown summary
5. Outputs recommendations (KEEP/REMOVE) for each strategy

Usage:
    python3 scripts/detect_duplicates.py \
        --validation-results phase2_validated_results_20251101_060315.json \
        --strategy-dir . \
        --output duplicate_report.md

Requirements: REQ-2 (Acceptance Criteria 4, 5)
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.duplicate_detector import DuplicateDetector, DuplicateGroup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Detect duplicate strategies in validation results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--validation-results',
        type=str,
        required=True,
        help='Path to validation results JSON file'
    )

    parser.add_argument(
        '--strategy-dir',
        type=str,
        default='.',
        help='Directory containing strategy files (default: current directory)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='duplicate_report.md',
        help='Output path for Markdown report (default: duplicate_report.md)'
    )

    return parser.parse_args()


def load_validation_results(file_path: str) -> Dict[str, Any]:
    """
    Load validation results from JSON file.

    Args:
        file_path: Path to validation results JSON

    Returns:
        Validation results dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    path = Path(file_path)

    if not path.exists():
        logger.error(f"Validation results file not found: {file_path}")
        raise FileNotFoundError(f"Validation results file not found: {file_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Loaded validation results from {file_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise


def find_strategy_files(strategy_dir: str) -> List[str]:
    """
    Find all strategy files matching pattern generated_strategy_loop_iter*.py.

    Args:
        strategy_dir: Directory to search for strategy files

    Returns:
        List of strategy file paths (sorted by iteration number)

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    dir_path = Path(strategy_dir)

    if not dir_path.exists():
        logger.error(f"Strategy directory not found: {strategy_dir}")
        raise FileNotFoundError(f"Strategy directory not found: {strategy_dir}")

    if not dir_path.is_dir():
        logger.error(f"Strategy path is not a directory: {strategy_dir}")
        raise NotADirectoryError(f"Strategy path is not a directory: {strategy_dir}")

    # Find all matching strategy files
    pattern = "generated_strategy_loop_iter*.py"
    strategy_files = list(dir_path.glob(pattern))

    if not strategy_files:
        logger.warning(f"No strategy files found matching {pattern} in {strategy_dir}")
        return []

    # Sort by iteration number
    def get_iteration_num(path: Path) -> int:
        """Extract iteration number from filename."""
        try:
            name = path.stem
            if 'iter' in name:
                return int(name.split('iter')[1])
            return 0
        except (ValueError, IndexError):
            return 0

    strategy_files.sort(key=get_iteration_num)

    logger.info(f"Found {len(strategy_files)} strategy files in {strategy_dir}")
    return [str(f) for f in strategy_files]


def generate_json_report(
    duplicate_groups: List[DuplicateGroup],
    total_strategies: int
) -> Dict[str, Any]:
    """
    Generate JSON report from duplicate groups.

    Args:
        duplicate_groups: List of DuplicateGroup instances
        total_strategies: Total number of strategies analyzed

    Returns:
        JSON-serializable dictionary
    """
    report = {
        'total_strategies': total_strategies,
        'duplicate_groups': []
    }

    for group in duplicate_groups:
        # Get iteration numbers
        strategies = [s.index for s in group.strategies]

        # Determine keep/remove
        keep = strategies[0]  # Keep first strategy
        remove = strategies[1:]  # Remove others

        group_data = {
            'strategies': strategies,
            'sharpe_ratio': group.sharpe_ratio,
            'similarity': group.similarity_score,
            'keep': keep,
            'remove': remove
        }

        report['duplicate_groups'].append(group_data)

    return report


def generate_markdown_report(
    duplicate_groups: List[DuplicateGroup],
    total_strategies: int,
    validation_results: Dict[str, Any]
) -> str:
    """
    Generate Markdown report from duplicate groups.

    Args:
        duplicate_groups: List of DuplicateGroup instances
        total_strategies: Total number of strategies analyzed
        validation_results: Validation results for context

    Returns:
        Markdown-formatted report string
    """
    lines = []

    # Header
    lines.append("# Duplicate Strategy Detection Report")
    lines.append("")
    lines.append(f"**Generated**: {Path().absolute()}")
    lines.append(f"**Total Strategies Analyzed**: {total_strategies}")
    lines.append(f"**Duplicate Groups Found**: {len(duplicate_groups)}")
    lines.append("")

    # Summary section
    lines.append("## Summary")
    lines.append("")

    if not duplicate_groups:
        lines.append("No duplicate strategies detected.")
        lines.append("")
        return "\n".join(lines)

    total_duplicates = sum(len(g.strategies) for g in duplicate_groups)
    lines.append(f"- **Total strategies in duplicate groups**: {total_duplicates}")
    lines.append(f"- **Unique duplicate groups**: {len(duplicate_groups)}")
    lines.append("")

    # Detail section for each group
    lines.append("## Duplicate Groups")
    lines.append("")

    for i, group in enumerate(duplicate_groups, 1):
        strategies = [s.index for s in group.strategies]
        keep = strategies[0]
        remove = strategies[1:]

        lines.append(f"### Group {i}")
        lines.append("")
        lines.append(f"**Strategies Involved**: {', '.join(f'iter{s}' for s in strategies)}")
        lines.append(f"**Sharpe Ratio**: {group.sharpe_ratio:.16f} (identical)")
        lines.append(f"**Similarity Score**: {group.similarity_score:.2%}")
        lines.append("")

        # Recommendation
        lines.append("**Recommendation**:")
        lines.append(f"- **KEEP**: Strategy {keep} (first occurrence)")
        lines.append(f"- **REMOVE**: {', '.join(f'Strategy {s}' for s in remove)}")
        lines.append("")

        # Code diff
        if group.diff:
            lines.append("**Code Differences**:")
            lines.append("```diff")
            lines.append(group.diff)
            lines.append("```")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    """
    Main entry point for duplicate detection script.

    Returns:
        Exit code (0=success, 1=error)
    """
    try:
        # Parse arguments
        args = parse_arguments()

        logger.info("Starting duplicate detection...")
        logger.info(f"Validation results: {args.validation_results}")
        logger.info(f"Strategy directory: {args.strategy_dir}")
        logger.info(f"Output file: {args.output}")

        # Load validation results
        validation_results = load_validation_results(args.validation_results)

        # Find strategy files
        strategy_files = find_strategy_files(args.strategy_dir)

        if not strategy_files:
            logger.warning("No strategy files found. Exiting.")
            return 0

        # Run duplicate detection
        logger.info("Running duplicate detection...")
        detector = DuplicateDetector()
        duplicate_groups = detector.find_duplicates(strategy_files, validation_results)

        # Generate reports
        logger.info("Generating reports...")

        # JSON report
        json_report = generate_json_report(duplicate_groups, len(strategy_files))
        json_output = args.output.replace('.md', '.json')
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2)
        logger.info(f"JSON report saved to {json_output}")

        # Markdown report
        markdown_report = generate_markdown_report(
            duplicate_groups,
            len(strategy_files),
            validation_results
        )
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        logger.info(f"Markdown report saved to {args.output}")

        # Console summary
        print("\n" + "=" * 60)
        print("DUPLICATE DETECTION COMPLETE")
        print("=" * 60)
        print(f"Total strategies analyzed: {len(strategy_files)}")
        print(f"Duplicate groups found: {len(duplicate_groups)}")

        if duplicate_groups:
            print("\nDuplicate groups:")
            for i, group in enumerate(duplicate_groups, 1):
                strategies = [s.index for s in group.strategies]
                print(f"  Group {i}: Strategies {strategies} "
                      f"(Sharpe {group.sharpe_ratio:.4f}, "
                      f"Similarity {group.similarity_score:.2%})")
        else:
            print("\nNo duplicates detected.")

        print(f"\nReports saved:")
        print(f"  - Markdown: {args.output}")
        print(f"  - JSON: {json_output}")
        print("=" * 60)

        return 0

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
