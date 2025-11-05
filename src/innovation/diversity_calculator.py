"""
Diversity Calculator - Task 3.2

Calculates novelty scores and diversity rewards to prevent
population convergence and encourage exploration.

Responsibilities:
- Calculate novelty scores for innovations
- Combine fitness with diversity: 70% performance + 30% novelty
- Track diversity metrics
- Prevent convergence
"""

from typing import List, Dict, Any, Optional
from difflib import SequenceMatcher
import numpy as np


class DiversityCalculator:
    """
    Calculate diversity and novelty metrics.

    Uses code similarity and performance spread to measure
    population diversity and assign novelty bonuses.
    """

    def __init__(
        self,
        diversity_weight: float = 0.30,
        performance_weight: float = 0.70,
        novelty_threshold: float = 0.80
    ):
        """
        Initialize diversity calculator.

        Args:
            diversity_weight: Weight for novelty in combined fitness (default: 30%)
            performance_weight: Weight for performance in combined fitness (default: 70%)
            novelty_threshold: Similarity threshold above which considered duplicate
        """
        assert abs(diversity_weight + performance_weight - 1.0) < 1e-6, \
            "Weights must sum to 1.0"

        self.diversity_weight = diversity_weight
        self.performance_weight = performance_weight
        self.novelty_threshold = novelty_threshold

    def calculate_novelty_score(
        self,
        new_code: str,
        existing_codes: List[str]
    ) -> float:
        """
        Calculate novelty score for new code.

        Args:
            new_code: Code of new innovation
            existing_codes: List of existing innovation codes

        Returns:
            Novelty score (0.0 = duplicate, 1.0 = completely novel)
        """
        if not existing_codes:
            return 1.0  # First innovation is perfectly novel

        # Calculate similarity to all existing codes
        similarities = []
        for existing_code in existing_codes:
            similarity = SequenceMatcher(
                None,
                new_code.lower(),
                existing_code.lower()
            ).ratio()
            similarities.append(similarity)

        # Novelty is inverse of maximum similarity
        max_similarity = max(similarities)
        novelty = 1.0 - max_similarity

        return novelty

    def calculate_combined_fitness(
        self,
        performance: float,
        novelty: float
    ) -> float:
        """
        Calculate combined fitness: 70% performance + 30% novelty.

        Args:
            performance: Performance metric (e.g., Sharpe ratio normalized 0-1)
            novelty: Novelty score (0-1)

        Returns:
            Combined fitness score
        """
        return (
            self.performance_weight * performance +
            self.diversity_weight * novelty
        )

    def calculate_population_diversity(
        self,
        codes: List[str]
    ) -> float:
        """
        Calculate overall population diversity.

        Args:
            codes: List of all innovation codes in population

        Returns:
            Diversity metric (0.0 = all identical, 1.0 = all unique)
        """
        if len(codes) <= 1:
            return 1.0

        # Calculate average pairwise dissimilarity
        total_dissimilarity = 0.0
        pair_count = 0

        for i in range(len(codes)):
            for j in range(i + 1, len(codes)):
                similarity = SequenceMatcher(
                    None,
                    codes[i].lower(),
                    codes[j].lower()
                ).ratio()
                dissimilarity = 1.0 - similarity
                total_dissimilarity += dissimilarity
                pair_count += 1

        return total_dissimilarity / pair_count if pair_count > 0 else 0.0

    def assess_diversity_risk(
        self,
        diversity: float,
        min_diversity_threshold: float = 0.30
    ) -> Dict[str, Any]:
        """
        Assess convergence risk based on diversity.

        Args:
            diversity: Current population diversity (0-1)
            min_diversity_threshold: Minimum acceptable diversity

        Returns:
            Risk assessment dictionary
        """
        risk_level = "low"
        recommendation = "Continue current evolution"

        if diversity < min_diversity_threshold:
            risk_level = "high"
            recommendation = "ALERT: Increase innovation rate to prevent convergence"
        elif diversity < min_diversity_threshold * 1.5:
            risk_level = "medium"
            recommendation = "Monitor diversity closely, consider increasing exploration"

        return {
            'diversity': diversity,
            'risk_level': risk_level,
            'recommendation': recommendation,
            'threshold': min_diversity_threshold
        }

    def normalize_performance(
        self,
        performances: List[float],
        baseline_performance: float = 0.0
    ) -> List[float]:
        """
        Normalize performance metrics to 0-1 range.

        Args:
            performances: List of raw performance metrics
            baseline_performance: Baseline to subtract

        Returns:
            Normalized performance scores (0-1)
        """
        if not performances:
            return []

        # Subtract baseline
        adjusted = [p - baseline_performance for p in performances]

        # Handle all negative case
        if all(p <= 0 for p in adjusted):
            return [0.0] * len(adjusted)

        # Min-max normalization
        min_perf = min(adjusted)
        max_perf = max(adjusted)

        if abs(max_perf - min_perf) < 1e-6:
            return [0.5] * len(adjusted)  # All same

        return [
            (p - min_perf) / (max_perf - min_perf)
            for p in adjusted
        ]

    def get_diversity_report(
        self,
        innovations: List[Dict[str, Any]],
        baseline_sharpe: float = 0.68
    ) -> Dict[str, Any]:
        """
        Generate comprehensive diversity report.

        Args:
            innovations: List of innovations with 'code' and 'performance'
            baseline_sharpe: Baseline Sharpe for normalization

        Returns:
            Diversity report dictionary
        """
        if not innovations:
            return {
                'population_size': 0,
                'diversity': 0.0,
                'risk_assessment': {'risk_level': 'n/a'}
            }

        codes = [i['code'] for i in innovations]
        performances = [
            i.get('performance', {}).get('sharpe_ratio', 0)
            for i in innovations
        ]

        # Calculate metrics
        diversity = self.calculate_population_diversity(codes)
        risk = self.assess_diversity_risk(diversity)

        # Normalize performances
        norm_perfs = self.normalize_performance(performances, baseline_sharpe)

        # Calculate novelty for each innovation
        novelties = []
        for i, code in enumerate(codes):
            other_codes = codes[:i] + codes[i+1:]
            novelty = self.calculate_novelty_score(code, other_codes)
            novelties.append(novelty)

        # Calculate combined fitness
        combined_fitness = [
            self.calculate_combined_fitness(perf, nov)
            for perf, nov in zip(norm_perfs, novelties)
        ]

        return {
            'population_size': len(innovations),
            'diversity': diversity,
            'risk_assessment': risk,
            'avg_novelty': np.mean(novelties) if novelties else 0.0,
            'avg_performance_norm': np.mean(norm_perfs) if norm_perfs else 0.0,
            'avg_combined_fitness': np.mean(combined_fitness) if combined_fitness else 0.0,
            'min_novelty': min(novelties) if novelties else 0.0,
            'max_novelty': max(novelties) if novelties else 0.0
        }


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING DIVERSITY CALCULATOR")
    print("=" * 70)

    calculator = DiversityCalculator()

    # Test 1: Novelty score
    print("\nTest 1: Novelty Score")
    print("-" * 70)

    new_code = "factor = data.get('fundamental_features:ROE稅後') / data.get('fundamental_features:淨值比')"
    existing = [
        "factor = data.get('price:收盤價').rolling(20).mean()",
        "factor = data.get('fundamental_features:營收成長率') * 0.5"
    ]

    novelty = calculator.calculate_novelty_score(new_code, existing)
    print(f"✅ Novelty score: {novelty:.3f} (1.0 = completely novel)")

    # Test 2: Population diversity
    print("\nTest 2: Population Diversity")
    print("-" * 70)

    codes = [
        "factor = data.get('fundamental_features:ROE稅後')",
        "factor = data.get('price:收盤價').rolling(20).mean()",
        "factor = data.get('fundamental_features:營收成長率')"
    ]

    diversity = calculator.calculate_population_diversity(codes)
    print(f"✅ Population diversity: {diversity:.3f} (1.0 = all unique)")

    # Test 3: Combined fitness
    print("\nTest 3: Combined Fitness")
    print("-" * 70)

    performance = 0.8  # Normalized performance
    novelty = 0.9      # Novelty score

    combined = calculator.calculate_combined_fitness(performance, novelty)
    print(f"✅ Combined fitness: {combined:.3f}")
    print(f"   (70% perf {performance:.3f} + 30% novelty {novelty:.3f})")

    # Test 4: Diversity report
    print("\nTest 4: Diversity Report")
    print("-" * 70)

    mock_innovations = [
        {'code': codes[0], 'performance': {'sharpe_ratio': 0.75}},
        {'code': codes[1], 'performance': {'sharpe_ratio': 0.82}},
        {'code': codes[2], 'performance': {'sharpe_ratio': 0.69}}
    ]

    report = calculator.get_diversity_report(mock_innovations)
    print(f"✅ Diversity report:")
    print(f"   Population size: {report['population_size']}")
    print(f"   Diversity: {report['diversity']:.3f}")
    print(f"   Risk level: {report['risk_assessment']['risk_level']}")
    print(f"   Avg novelty: {report['avg_novelty']:.3f}")

    print("\n" + "=" * 70)
    print("DIVERSITY CALCULATOR TEST COMPLETE")
    print("=" * 70)
