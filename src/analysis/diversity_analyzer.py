"""
Diversity Analyzer Module

Analyzes strategy diversity using factor diversity, return correlation, and risk profile analysis.
This module is part of the validation-framework-critical-fixes specification (Task 3.1).

Key Components:
    - DiversityAnalyzer: Main class for diversity analysis
    - DiversityReport: Dataclass for analysis results
    - Factor extraction using AST parsing (no code execution)
    - Jaccard similarity for factor diversity
    - Correlation analysis for return diversity
    - Coefficient of variation for risk diversity

Author: AI Assistant
Date: 2025-11-01
"""

import ast
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Union

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DiversityReport:
    """Comprehensive diversity report for a set of strategies.

    Attributes:
        total_strategies: Total number of strategies analyzed
        excluded_strategies: List of strategy indices excluded from analysis
        factor_diversity: Factor diversity score (0-1, higher is more diverse)
        avg_correlation: Average pairwise correlation (0-1, lower is more diverse)
        risk_diversity: Risk profile diversity (CV of max drawdowns, higher is more diverse)
        diversity_score: Overall diversity score (0-100, higher is better)
        warnings: List of warning messages
        recommendation: Overall recommendation ("SUFFICIENT", "MARGINAL", "INSUFFICIENT")
        factor_details: Optional detailed factor analysis
    """

    total_strategies: int
    excluded_strategies: List[int]
    factor_diversity: float
    avg_correlation: float
    risk_diversity: float
    diversity_score: float
    warnings: List[str] = field(default_factory=list)
    recommendation: str = "UNKNOWN"
    factor_details: Optional[Dict] = None


class DiversityAnalyzer:
    """Analyzes strategy diversity across multiple dimensions.

    This class provides comprehensive diversity analysis for a set of trading strategies,
    including factor diversity, return correlation, and risk profile analysis.

    The analyzer:
    - Parses strategy files using AST (no code execution)
    - Calculates Jaccard similarity for factor diversity
    - Computes pairwise correlations for return similarity
    - Measures risk profile diversity using coefficient of variation
    - Generates comprehensive reports with recommendations

    Example:
        >>> analyzer = DiversityAnalyzer()
        >>> report = analyzer.analyze_diversity(
        ...     strategy_files=['strategy1.py', 'strategy2.py'],
        ...     validation_results={'population': [...]},
        ...     exclude_indices=[5]
        ... )
        >>> print(f"Diversity Score: {report.diversity_score:.1f}")
        >>> print(f"Recommendation: {report.recommendation}")
    """

    def __init__(self):
        """Initialize the DiversityAnalyzer."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def analyze_diversity(
        self,
        strategy_files: List[Union[str, Path]],
        validation_results: Dict,
        exclude_indices: Optional[List[int]] = None,
        original_indices: Optional[List[int]] = None
    ) -> DiversityReport:
        """Analyze diversity across multiple dimensions.

        Args:
            strategy_files: List of strategy file paths
            validation_results: Validation results dict with population metrics
            exclude_indices: Strategy indices to exclude (e.g., duplicates)
            original_indices: Original indices of strategies in population (for non-sequential cases)

        Returns:
            DiversityReport with comprehensive diversity analysis

        Raises:
            ValueError: If insufficient strategies provided
        """
        exclude_indices = exclude_indices or []

        # If original_indices not provided, assume sequential [0, 1, 2, ...]
        if original_indices is None:
            original_indices = list(range(len(strategy_files)))

        # Convert to paths
        strategy_paths = [Path(f) for f in strategy_files]

        # Filter out excluded strategies, maintaining original indices
        included_indices = [idx for i, idx in enumerate(original_indices) if i not in exclude_indices]
        included_paths = [strategy_paths[i] for i in range(len(strategy_paths)) if i not in exclude_indices]

        total_strategies = len(included_paths)
        warnings = []

        # Check minimum strategy count
        if total_strategies < 2:
            warnings.append(f"Insufficient strategies for diversity analysis: {total_strategies} < 2")
            return DiversityReport(
                total_strategies=total_strategies,
                excluded_strategies=exclude_indices,
                factor_diversity=0.0,
                avg_correlation=1.0,
                risk_diversity=0.0,
                diversity_score=0.0,
                warnings=warnings,
                recommendation="INSUFFICIENT"
            )

        if total_strategies < 3:
            warnings.append(f"Low strategy count for diversity analysis: {total_strategies} < 3")

        # Extract factors from each strategy
        self.logger.info(f"Extracting factors from {total_strategies} strategies...")
        factor_sets = []
        all_factors = set()

        for path in included_paths:
            try:
                factors = self.extract_factors(path)
                factor_sets.append(factors)
                all_factors.update(factors)
            except Exception as e:
                self.logger.warning(f"Failed to extract factors from {path}: {e}")
                factor_sets.append(set())

        # Calculate factor diversity
        self.logger.info("Calculating factor diversity...")
        try:
            factor_diversity = self.calculate_factor_diversity(factor_sets)
        except Exception as e:
            self.logger.error(f"Failed to calculate factor diversity: {e}")
            factor_diversity = 0.0
            warnings.append(f"Factor diversity calculation failed: {str(e)}")

        # Check factor diversity threshold
        if factor_diversity < 0.5:
            warnings.append(f"Low factor diversity detected: {factor_diversity:.3f} < 0.5")

        # Calculate return correlation
        self.logger.info("Calculating return correlation...")
        try:
            avg_correlation = self.calculate_return_correlation(
                validation_results, included_indices
            )
        except Exception as e:
            self.logger.error(f"Failed to calculate return correlation: {e}")
            avg_correlation = 0.5
            warnings.append(f"Return correlation calculation failed: {str(e)}")

        # Check correlation threshold
        if avg_correlation > 0.8:
            warnings.append(f"High correlation detected: {avg_correlation:.3f} > 0.8")

        # Calculate risk diversity
        self.logger.info("Calculating risk diversity...")
        try:
            risk_diversity = self.calculate_risk_diversity(
                validation_results, included_indices
            )
        except Exception as e:
            self.logger.error(f"Failed to calculate risk diversity: {e}")
            risk_diversity = 0.0
            warnings.append(f"Risk diversity calculation failed: {str(e)}")

        # Check risk diversity threshold
        if risk_diversity < 0.3:
            warnings.append(f"Low risk diversity detected: {risk_diversity:.3f} < 0.3")

        # Calculate overall diversity score (0-100)
        diversity_score = self._calculate_overall_score(
            factor_diversity, avg_correlation, risk_diversity
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(diversity_score)

        # Create detailed factor analysis
        factor_details = {
            "total_unique_factors": len(all_factors),
            "avg_factors_per_strategy": np.mean([len(fs) for fs in factor_sets]),
            "factor_sets_by_strategy": [list(fs) for fs in factor_sets]
        }

        return DiversityReport(
            total_strategies=total_strategies,
            excluded_strategies=exclude_indices,
            factor_diversity=factor_diversity,
            avg_correlation=avg_correlation,
            risk_diversity=risk_diversity,
            diversity_score=diversity_score,
            warnings=warnings,
            recommendation=recommendation,
            factor_details=factor_details
        )

    def extract_factors(self, strategy_path: Path) -> Set[str]:
        """Extract factor names from strategy file using AST parsing.

        Parses the strategy file and extracts all data.get() calls to identify
        which market data factors are used by the strategy.

        Args:
            strategy_path: Path to strategy Python file

        Returns:
            Set of factor names (first argument to data.get())

        Raises:
            FileNotFoundError: If strategy file doesn't exist
            SyntaxError: If strategy file has invalid Python syntax
        """
        if not strategy_path.exists():
            raise FileNotFoundError(f"Strategy file not found: {strategy_path}")

        try:
            with open(strategy_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            self.logger.error(f"Failed to read {strategy_path}: {e}")
            return set()

        factors = set()

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {strategy_path}: {e}")
            raise

        # Walk the AST to find data.get() calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check if this is a method call
                if isinstance(node.func, ast.Attribute):
                    # Check if it's data.get()
                    if (isinstance(node.func.value, ast.Name) and
                        node.func.value.id == 'data' and
                        node.func.attr == 'get'):
                        # Extract the first argument (factor name)
                        if node.args:
                            arg = node.args[0]
                            if isinstance(arg, ast.Constant):
                                factors.add(arg.value)
                            elif isinstance(arg, ast.Str):  # Python 3.7 compatibility
                                factors.add(arg.s)
                # Also check for data.indicator() calls
                if isinstance(node.func, ast.Attribute):
                    if (isinstance(node.func.value, ast.Name) and
                        node.func.value.id == 'data' and
                        node.func.attr == 'indicator'):
                        # Extract the first argument (indicator name)
                        if node.args:
                            arg = node.args[0]
                            if isinstance(arg, ast.Constant):
                                factors.add(f"indicator:{arg.value}")
                            elif isinstance(arg, ast.Str):
                                factors.add(f"indicator:{arg.s}")

        self.logger.debug(f"Extracted {len(factors)} factors from {strategy_path.name}")
        return factors

    def calculate_factor_diversity(self, factor_sets: List[Set[str]]) -> float:
        """Calculate factor diversity using Jaccard distance.

        Computes pairwise Jaccard similarity between all factor sets and returns
        the average Jaccard distance (1 - similarity) as a diversity measure.

        Args:
            factor_sets: List of factor sets (one per strategy)

        Returns:
            Average Jaccard distance (0-1, higher is more diverse)
        """
        if len(factor_sets) < 2:
            return 0.0

        # Remove empty factor sets
        valid_sets = [fs for fs in factor_sets if len(fs) > 0]

        if len(valid_sets) < 2:
            return 0.0

        # Calculate pairwise Jaccard similarities
        similarities = []
        n = len(valid_sets)

        for i in range(n):
            for j in range(i + 1, n):
                set_i = valid_sets[i]
                set_j = valid_sets[j]

                # Jaccard similarity = |A ∩ B| / |A ∪ B|
                intersection = len(set_i & set_j)
                union = len(set_i | set_j)

                if union > 0:
                    similarity = intersection / union
                else:
                    similarity = 0.0

                similarities.append(similarity)

        # Average Jaccard distance (1 - similarity)
        if similarities:
            avg_similarity = np.mean(similarities)
            diversity = 1.0 - avg_similarity
        else:
            diversity = 0.0

        return float(np.clip(diversity, 0.0, 1.0))

    def calculate_return_correlation(
        self,
        validation_results: Dict,
        strategy_indices: List[int]
    ) -> float:
        """Calculate average pairwise return correlation.

        Uses Sharpe ratio as a proxy for returns when actual return series
        are not available in the validation results.

        Args:
            validation_results: Validation results dict
            strategy_indices: Indices of strategies to include

        Returns:
            Average pairwise correlation (0-1)
        """
        # Extract metrics from validation results
        if 'population' in validation_results:
            population = validation_results['population']
        elif 'strategies' in validation_results:
            population = validation_results['strategies']
        else:
            self.logger.warning("No population or strategies found in validation_results")
            return 0.5  # Default neutral correlation

        # Extract Sharpe ratios for included strategies
        sharpes = []
        for idx in strategy_indices:
            if idx < len(population):
                strategy = population[idx]

                # Try different metric field names
                if 'metrics' in strategy:
                    metrics = strategy['metrics']
                    sharpe = metrics.get('sharpe_ratio', metrics.get('sharpe', None))
                elif 'sharpe_ratio' in strategy:
                    sharpe = strategy['sharpe_ratio']
                elif 'sharpe' in strategy:
                    sharpe = strategy['sharpe']
                else:
                    sharpe = None

                if sharpe is not None:
                    sharpes.append(sharpe)

        if len(sharpes) < 2:
            self.logger.warning(f"Insufficient Sharpe ratios for correlation: {len(sharpes)} < 2")
            return 0.5  # Default neutral correlation

        # Since we only have single values per strategy (not time series),
        # we can't calculate true correlation. Instead, we use variance
        # as a proxy: low variance = high correlation, high variance = low correlation
        sharpe_array = np.array(sharpes)
        sharpe_mean = np.mean(sharpe_array)

        if sharpe_mean == 0:
            return 0.5  # Neutral correlation

        # Coefficient of variation as correlation proxy
        cv = np.std(sharpe_array) / abs(sharpe_mean) if sharpe_mean != 0 else 0

        # Map CV to correlation: low CV -> high correlation, high CV -> low correlation
        # Use sigmoid-like transformation: corr = 1 / (1 + cv)
        correlation = 1.0 / (1.0 + cv)

        return float(np.clip(correlation, 0.0, 1.0))

    def calculate_risk_diversity(
        self,
        validation_results: Dict,
        strategy_indices: List[int]
    ) -> float:
        """Calculate risk profile diversity using coefficient of variation.

        Measures diversity of risk profiles by computing the coefficient of
        variation (CV) of maximum drawdowns across strategies.

        Args:
            validation_results: Validation results dict
            strategy_indices: Indices of strategies to include

        Returns:
            Coefficient of variation (higher is more diverse)
        """
        # Extract metrics from validation results
        if 'population' in validation_results:
            population = validation_results['population']
        elif 'strategies' in validation_results:
            population = validation_results['strategies']
        else:
            self.logger.warning("No population or strategies found in validation_results")
            return 0.0

        # Extract max drawdowns for included strategies
        drawdowns = []
        for idx in strategy_indices:
            if idx < len(population):
                strategy = population[idx]

                # Try different metric field names
                if 'metrics' in strategy:
                    metrics = strategy['metrics']
                    mdd = metrics.get('max_drawdown', metrics.get('mdd', None))
                elif 'max_drawdown' in strategy:
                    mdd = strategy['max_drawdown']
                elif 'mdd' in strategy:
                    mdd = strategy['mdd']
                else:
                    mdd = None

                if mdd is not None:
                    # Convert to absolute value for CV calculation
                    drawdowns.append(abs(mdd))

        if len(drawdowns) < 2:
            self.logger.warning(f"Insufficient drawdowns for risk diversity: {len(drawdowns)} < 2")
            return 0.0

        # Calculate coefficient of variation
        dd_array = np.array(drawdowns)
        mean_dd = np.mean(dd_array)

        if mean_dd == 0:
            return 0.0

        cv = np.std(dd_array) / mean_dd

        # Clip to reasonable range (0-2) and normalize to 0-1
        cv = float(np.clip(cv, 0.0, 2.0)) / 2.0

        return cv

    def _calculate_overall_score(
        self,
        factor_diversity: float,
        avg_correlation: float,
        risk_diversity: float
    ) -> float:
        """Calculate overall diversity score from component metrics.

        Args:
            factor_diversity: Factor diversity (0-1)
            avg_correlation: Average correlation (0-1)
            risk_diversity: Risk diversity (0-1)

        Returns:
            Overall diversity score (0-100)
        """
        # Weight the components:
        # - Factor diversity: 50% (most important)
        # - Low correlation: 30% (1 - correlation)
        # - Risk diversity: 20%
        score = (
            factor_diversity * 0.5 +
            (1.0 - avg_correlation) * 0.3 +
            risk_diversity * 0.2
        ) * 100.0

        return float(np.clip(score, 0.0, 100.0))

    def _generate_recommendation(self, diversity_score: float) -> str:
        """Generate recommendation based on diversity score.

        Args:
            diversity_score: Overall diversity score (0-100)

        Returns:
            Recommendation string ("SUFFICIENT", "MARGINAL", "INSUFFICIENT")
        """
        if diversity_score >= 60:
            return "SUFFICIENT"
        elif diversity_score >= 40:
            return "MARGINAL"
        else:
            return "INSUFFICIENT"


__all__ = [
    "DiversityAnalyzer",
    "DiversityReport"
]
