"""
Duplicate Strategy Detector (Task 2.1)
======================================

Detects duplicate strategies using two-stage analysis:
1. Sharpe ratio matching (tolerance 1e-8)
2. AST similarity analysis (threshold 95%)

This addresses REQ-2: Identify duplicate validated strategies that artificially
inflate diversity statistics.

Usage:
    from src.analysis.duplicate_detector import DuplicateDetector, DuplicateGroup

    detector = DuplicateDetector()
    duplicates = detector.find_duplicates(strategy_files, validation_results)

    for group in duplicates:
        print(f"Found {len(group.strategies)} duplicates with Sharpe {group.sharpe_ratio}")
"""

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import difflib

logger = logging.getLogger(__name__)


@dataclass
class StrategyInfo:
    """Information about a strategy for duplicate detection."""
    index: int
    file_path: str
    sharpe_ratio: float
    validation_passed: bool
    code: Optional[str] = None
    ast_tree: Optional[ast.AST] = None


@dataclass
class DuplicateGroup:
    """Group of duplicate strategies with identical Sharpe ratios and similar AST."""
    sharpe_ratio: float
    strategies: List[StrategyInfo]
    similarity_score: float
    diff: Optional[str] = None
    recommendation: str = "KEEP_FIRST"  # KEEP_FIRST, REMOVE_ALL, REVIEW

    def __post_init__(self):
        """Calculate recommendation based on validation status."""
        if len(self.strategies) < 2:
            self.recommendation = "NOT_DUPLICATE"
        elif any(s.validation_passed for s in self.strategies):
            self.recommendation = "KEEP_FIRST"
        else:
            self.recommendation = "REVIEW"


class DuplicateDetector:
    """
    Detects duplicate strategies using Sharpe ratio matching and AST similarity.

    Two-stage detection:
    1. Group strategies by Sharpe ratio (tolerance 1e-8)
    2. Compare AST similarity within each group (threshold 95%)

    Attributes:
        sharpe_tolerance: Maximum difference for considering Sharpe ratios equal
        similarity_threshold: Minimum AST similarity (0-1) to consider duplicates
    """

    def __init__(
        self,
        sharpe_tolerance: float = 1e-8,
        similarity_threshold: float = 0.95
    ):
        """
        Initialize duplicate detector.

        Args:
            sharpe_tolerance: Maximum Sharpe ratio difference (default 1e-8)
            similarity_threshold: Minimum AST similarity 0-1 (default 0.95 = 95%)
        """
        self.sharpe_tolerance = sharpe_tolerance
        self.similarity_threshold = similarity_threshold
        logger.info(
            f"DuplicateDetector initialized: tolerance={sharpe_tolerance}, "
            f"threshold={similarity_threshold}"
        )

    def find_duplicates(
        self,
        strategy_files: List[str],
        validation_results: Dict[str, Any]
    ) -> List[DuplicateGroup]:
        """
        Find duplicate strategies using Sharpe matching + AST similarity.

        Args:
            strategy_files: List of strategy file paths
            validation_results: Validation results JSON (from run_phase2_with_validation.py)

        Returns:
            List of DuplicateGroup instances
        """
        logger.info(f"Finding duplicates in {len(strategy_files)} strategies")

        # Extract strategy information
        strategies = self._extract_strategy_info(strategy_files, validation_results)
        logger.info(f"Extracted info for {len(strategies)} strategies")

        # Group by Sharpe ratio
        sharpe_groups = self._group_by_sharpe(strategies)
        logger.info(f"Found {len(sharpe_groups)} Sharpe ratio groups")

        # Compare AST within each group
        duplicate_groups = []
        for sharpe, group_strategies in sharpe_groups.items():
            if len(group_strategies) < 2:
                continue

            logger.info(
                f"Analyzing group with Sharpe {sharpe:.16f} "
                f"({len(group_strategies)} strategies)"
            )

            # Compare all pairs in the group
            duplicates = self._find_duplicates_in_group(group_strategies)
            duplicate_groups.extend(duplicates)

        logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        return duplicate_groups

    def _extract_strategy_info(
        self,
        strategy_files: List[str],
        validation_results: Dict[str, Any]
    ) -> List[StrategyInfo]:
        """Extract strategy information from files and validation results."""
        strategies = []

        # Build lookup by strategy index
        strategies_validation = validation_results.get('strategies_validation', [])
        validation_lookup = {
            s['strategy_index']: s for s in strategies_validation
        }

        for file_path in strategy_files:
            # Extract strategy index from filename (e.g., "generated_strategy_loop_iter9.py" -> 9)
            try:
                filename = Path(file_path).name
                if 'iter' in filename:
                    index_str = filename.split('iter')[1].split('.')[0]
                    index = int(index_str)
                else:
                    logger.warning(f"Cannot extract index from {filename}, skipping")
                    continue
            except (IndexError, ValueError) as e:
                logger.warning(f"Cannot parse strategy index from {file_path}: {e}")
                continue

            # Get validation info
            val_info = validation_lookup.get(index)
            if not val_info:
                logger.warning(f"No validation info for strategy {index}")
                continue

            # Read strategy code
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            except Exception as e:
                logger.error(f"Cannot read {file_path}: {e}")
                continue

            # Parse AST
            try:
                tree = ast.parse(code)
            except SyntaxError as e:
                logger.error(f"Cannot parse {file_path}: {e}")
                continue

            strategy = StrategyInfo(
                index=index,
                file_path=file_path,
                sharpe_ratio=val_info['sharpe_ratio'],
                validation_passed=val_info.get('validation_passed', False),
                code=code,
                ast_tree=tree
            )
            strategies.append(strategy)

        return strategies

    def _group_by_sharpe(
        self,
        strategies: List[StrategyInfo]
    ) -> Dict[float, List[StrategyInfo]]:
        """
        Group strategies by Sharpe ratio (with tolerance).

        Args:
            strategies: List of StrategyInfo instances

        Returns:
            Dict mapping Sharpe ratio to list of strategies
        """
        groups = {}

        for strategy in strategies:
            sharpe = strategy.sharpe_ratio

            # Check if Sharpe matches any existing group
            matched_group = None
            for existing_sharpe in groups.keys():
                if abs(sharpe - existing_sharpe) <= self.sharpe_tolerance:
                    matched_group = existing_sharpe
                    break

            if matched_group is not None:
                groups[matched_group].append(strategy)
            else:
                groups[sharpe] = [strategy]

        return groups

    def _find_duplicates_in_group(
        self,
        strategies: List[StrategyInfo]
    ) -> List[DuplicateGroup]:
        """
        Find duplicates within a group of strategies with identical Sharpe ratios.

        Args:
            strategies: List of strategies with matching Sharpe ratios

        Returns:
            List of DuplicateGroup instances
        """
        duplicate_groups = []
        processed = set()

        for i, strategy_a in enumerate(strategies):
            if i in processed:
                continue

            duplicates = [strategy_a]

            for j, strategy_b in enumerate(strategies[i+1:], start=i+1):
                if j in processed:
                    continue

                # Compare AST similarity
                similarity = self.compare_strategies(
                    strategy_a.file_path,
                    strategy_b.file_path
                )

                if similarity >= self.similarity_threshold:
                    duplicates.append(strategy_b)
                    processed.add(j)
                    logger.info(
                        f"Found duplicate: strategies {strategy_a.index} and "
                        f"{strategy_b.index} (similarity {similarity:.2%})"
                    )

            if len(duplicates) > 1:
                # Generate diff for first pair
                diff = self._generate_diff(duplicates[0].code, duplicates[1].code)

                group = DuplicateGroup(
                    sharpe_ratio=strategy_a.sharpe_ratio,
                    strategies=duplicates,
                    similarity_score=1.0,  # TODO: Calculate average similarity
                    diff=diff
                )
                duplicate_groups.append(group)
                processed.add(i)

        return duplicate_groups

    def compare_strategies(
        self,
        strategy_a_path: str,
        strategy_b_path: str
    ) -> float:
        """
        Compare two strategies using normalized AST similarity.

        Args:
            strategy_a_path: Path to first strategy file
            strategy_b_path: Path to second strategy file

        Returns:
            Similarity score 0-1 (1 = identical after normalization)
        """
        try:
            # Read files
            with open(strategy_a_path, 'r', encoding='utf-8') as f:
                code_a = f.read()
            with open(strategy_b_path, 'r', encoding='utf-8') as f:
                code_b = f.read()

            # Parse AST
            tree_a = ast.parse(code_a)
            tree_b = ast.parse(code_b)

            # Normalize AST (variable names, etc.)
            norm_a = self.normalize_ast(tree_a)
            norm_b = self.normalize_ast(tree_b)

            # Compare normalized AST strings
            similarity = self._calculate_similarity(norm_a, norm_b)
            return similarity

        except Exception as e:
            logger.error(f"Error comparing strategies: {e}")
            return 0.0

    def normalize_ast(self, tree: ast.AST) -> str:
        """
        Normalize AST by replacing variable names with placeholders.

        This allows detecting duplicates that differ only in variable naming.

        Args:
            tree: AST tree to normalize

        Returns:
            Normalized AST as string
        """
        # Create a copy of the tree
        tree = ast.parse(ast.unparse(tree))

        # Variable name mapping
        var_mapping = {}
        counter = [0]  # Use list for mutable counter in closure

        class NameNormalizer(ast.NodeTransformer):
            """Replace variable names with VAR_0, VAR_1, etc."""

            def visit_Name(self, node):
                if node.id not in var_mapping:
                    var_mapping[node.id] = f"VAR_{counter[0]}"
                    counter[0] += 1
                node.id = var_mapping[node.id]
                return node

            def visit_arg(self, node):
                if node.arg not in var_mapping:
                    var_mapping[node.arg] = f"VAR_{counter[0]}"
                    counter[0] += 1
                node.arg = var_mapping[node.arg]
                return node

        normalizer = NameNormalizer()
        normalized_tree = normalizer.visit(tree)

        # Return unparsed normalized AST
        return ast.unparse(normalized_tree)

    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """
        Calculate similarity between two text strings using SequenceMatcher.

        Args:
            text_a: First text
            text_b: Second text

        Returns:
            Similarity ratio 0-1
        """
        matcher = difflib.SequenceMatcher(None, text_a, text_b)
        return matcher.ratio()

    def _generate_diff(
        self,
        code_a: Optional[str],
        code_b: Optional[str]
    ) -> Optional[str]:
        """
        Generate unified diff between two code strings.

        Args:
            code_a: First code string
            code_b: Second code string

        Returns:
            Unified diff as string, or None if inputs are None
        """
        if code_a is None or code_b is None:
            return None

        lines_a = code_a.splitlines(keepends=True)
        lines_b = code_b.splitlines(keepends=True)

        diff = difflib.unified_diff(
            lines_a,
            lines_b,
            fromfile='strategy_a',
            tofile='strategy_b',
            lineterm=''
        )

        return ''.join(diff)
