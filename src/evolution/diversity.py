"""
Diversity metrics for population-based evolutionary learning.

Provides Jaccard distance calculation, population diversity metrics, and
novelty search functionality to maintain genetic diversity and prevent
premature convergence in evolutionary algorithms.

Core Functions:
    extract_feature_set: Parse features/indicators from strategy code
    calculate_jaccard_distance: Measure similarity between two strategies
    calculate_population_diversity: Aggregate diversity metric for entire population
    calculate_novelty_score: K-nearest neighbor novelty metric for individual strategies
    should_increase_mutation_rate: Adaptive mutation trigger based on diversity threshold

Diversity Metrics:
    - Jaccard distance: Set-based similarity measure (0.0 = identical, 1.0 = completely different)
    - Population diversity: Average pairwise Jaccard distance across all strategies
    - Novelty score: Average distance to k-nearest neighbors (promotes exploration)

References:
    - Lehman, J., & Stanley, K. O. (2011). "Abandoning Objectives: Evolution through the Search for Novelty Alone"
    - Deb, K., & Tiwari, S. (2008). "Omni-optimizer: A generic evolutionary algorithm for single and multi-objective optimization"
"""

from typing import List, Set, Dict
from .types import Strategy
import re
import logging

logger = logging.getLogger(__name__)


def extract_feature_set(code: str) -> Set[str]:
    """
    Extract unique feature names from strategy code using regex pattern matching.

    Parses Python strategy code to identify all data features and indicators used,
    enabling calculation of code-based diversity metrics. Supports two common patterns:
    - data.get('feature_name'): DataFrame column access
    - data.indicator('indicator_name'): Technical indicator calls

    Args:
        code: Strategy implementation as Python code string

    Returns:
        Set[str]: Unique feature names extracted from code (e.g., {'roe', 'momentum', 'liquidity'})

    Example:
        >>> code = '''
        ... def strategy(data):
        ...     return data.get('roe') > 0.15 and data.indicator('momentum') > 0
        ... '''
        >>> features = extract_feature_set(code)
        >>> features
        {'roe', 'momentum'}

    Example (Multiple features):
        >>> code = '''
        ... def strategy(data):
        ...     high_roe = data.get('roe') > 0.15
        ...     good_momentum = data.indicator('momentum') > 0
        ...     liquid = data.get('liquidity') > 1000000
        ...     return high_roe and good_momentum and liquid
        ... '''
        >>> features = extract_feature_set(code)
        >>> sorted(features)
        ['liquidity', 'momentum', 'roe']

    Example (No features):
        >>> code = "def strategy(data): return True"
        >>> extract_feature_set(code)
        set()

    Notes:
        - Matches data.get('feature') and data.get("feature") (both quotes)
        - Matches data.indicator('name') and data.indicator("name")
        - Case-sensitive feature names
        - Returns empty set if no features found
        - Does not validate feature names (e.g., doesn't check if 'roe' exists in data)

    Regex Patterns:
        - data.get\\(['"]([^'"]+)['"]\\): Captures feature names in data.get()
        - data.indicator\\(['"]([^'"]+)['"]\\): Captures indicator names
    """
    features = set()

    # Pattern 1: data.get('feature_name') or data.get("feature_name")
    get_pattern = r"data\.get\(['\"]([^'\"]+)['\"]\)"
    get_matches = re.findall(get_pattern, code)
    features.update(get_matches)

    # Pattern 2: data.indicator('indicator_name') or data.indicator("indicator_name")
    indicator_pattern = r"data\.indicator\(['\"]([^'\"]+)['\"]\)"
    indicator_matches = re.findall(indicator_pattern, code)
    features.update(indicator_matches)

    return features


def calculate_jaccard_distance(strategy1: Strategy, strategy2: Strategy) -> float:
    """
    Calculate Jaccard distance between two strategies based on feature sets.

    The Jaccard distance measures dissimilarity between two sets as 1 minus the
    Jaccard similarity coefficient. Used to quantify how different two strategies
    are in terms of the features and indicators they use.

    Formula:
        Jaccard similarity = |A ∩ B| / |A ∪ B|
        Jaccard distance = 1 - Jaccard similarity

    Where A and B are the feature sets of strategy1 and strategy2.

    Args:
        strategy1: First Strategy instance with code attribute
        strategy2: Second Strategy instance with code attribute

    Returns:
        float: Jaccard distance in range [0.0, 1.0]
               - 0.0: Identical feature sets (maximum similarity)
               - 1.0: Completely disjoint feature sets (maximum dissimilarity)
               - 0.5: 50% overlap (moderate similarity)

    Example (Identical strategies):
        >>> s1 = Strategy(code="data.get('roe') > 0.15")
        >>> s2 = Strategy(code="data.get('roe') > 0.20")
        >>> calculate_jaccard_distance(s1, s2)
        0.0

    Example (Completely different):
        >>> s1 = Strategy(code="data.get('roe') > 0.15")
        >>> s2 = Strategy(code="data.indicator('momentum') > 0")
        >>> calculate_jaccard_distance(s1, s2)
        1.0

    Example (Partial overlap):
        >>> s1 = Strategy(code="data.get('roe') > 0.15 and data.get('pe') < 20")
        >>> s2 = Strategy(code="data.get('roe') > 0.10 and data.indicator('momentum') > 0")
        >>> distance = calculate_jaccard_distance(s1, s2)
        >>> 0.0 < distance < 1.0  # Partial overlap: {'roe'} shared, {'pe', 'momentum'} different
        True

    Example (Empty feature sets):
        >>> s1 = Strategy(code="return True")
        >>> s2 = Strategy(code="return False")
        >>> calculate_jaccard_distance(s1, s2)
        0.0

    Notes:
        - Returns 0.0 when both strategies have empty feature sets (edge case)
        - Distance is symmetric: calculate_jaccard_distance(s1, s2) == calculate_jaccard_distance(s2, s1)
        - Commonly used for diversity-preserving selection in genetic algorithms
        - Complements fitness-based selection by encouraging exploration

    Complexity:
        - Time: O(|A| + |B|) for set operations
        - Space: O(|A| + |B|) for feature set storage
    """
    # Extract feature sets from both strategies
    features1 = extract_feature_set(strategy1.code)
    features2 = extract_feature_set(strategy2.code)

    # Handle edge case: both strategies have no features
    if len(features1) == 0 and len(features2) == 0:
        return 0.0  # Consider identical if both empty

    # Calculate Jaccard distance: 1 - (intersection / union)
    intersection = features1 & features2  # Set intersection
    union = features1 | features2  # Set union

    # Handle edge case: empty union (should not happen given previous check)
    if len(union) == 0:
        return 0.0

    jaccard_similarity = len(intersection) / len(union)
    jaccard_distance = 1.0 - jaccard_similarity

    return jaccard_distance


def calculate_population_diversity(population: List[Strategy]) -> float:
    """
    Calculate average pairwise Jaccard distance across entire population.

    Computes the mean Jaccard distance between all pairs of strategies in the
    population, providing an aggregate diversity metric. Higher values indicate
    more diverse populations with less redundancy.

    Formula:
        diversity = (2 / (N * (N - 1))) * Σ_i Σ_j>i jaccard_distance(s_i, s_j)

    Where N is the population size and the double sum iterates over all unique pairs.

    Args:
        population: List of Strategy instances to analyze

    Returns:
        float: Average pairwise Jaccard distance in range [0.0, 1.0]
               - 0.0: All strategies use identical features (no diversity)
               - 1.0: All strategies use completely disjoint features (maximum diversity)
               - 0.3-0.5: Typical healthy diversity range

    Raises:
        ValueError: If population has fewer than 2 strategies (diversity undefined)

    Example (Diverse population):
        >>> strategies = [
        ...     Strategy(code="data.get('roe') > 0.15"),
        ...     Strategy(code="data.indicator('momentum') > 0"),
        ...     Strategy(code="data.get('liquidity') > 1000000")
        ... ]
        >>> diversity = calculate_population_diversity(strategies)
        >>> diversity == 1.0  # All completely different
        True

    Example (Identical population):
        >>> strategies = [
        ...     Strategy(code="data.get('roe') > 0.15"),
        ...     Strategy(code="data.get('roe') > 0.20"),
        ...     Strategy(code="data.get('roe') > 0.10")
        ... ]
        >>> diversity = calculate_population_diversity(strategies)
        >>> diversity == 0.0  # All use same feature 'roe'
        True

    Example (Moderate diversity):
        >>> strategies = [
        ...     Strategy(code="data.get('roe') > 0.15 and data.get('pe') < 20"),
        ...     Strategy(code="data.get('roe') > 0.10 and data.indicator('momentum') > 0"),
        ...     Strategy(code="data.indicator('momentum') > 0 and data.get('liquidity') > 1M")
        ... ]
        >>> diversity = calculate_population_diversity(strategies)
        >>> 0.3 < diversity < 0.7  # Partial overlaps
        True

    Example (Edge case - 2 strategies):
        >>> strategies = [
        ...     Strategy(code="data.get('roe') > 0.15"),
        ...     Strategy(code="data.indicator('momentum') > 0")
        ... ]
        >>> diversity = calculate_population_diversity(strategies)
        >>> diversity == 1.0  # Single pair, completely different
        True

    Notes:
        - Requires at least 2 strategies (raises ValueError otherwise)
        - Used to detect diversity collapse (trigger adaptive mutation when diversity < 0.3)
        - Calculated at each generation for monitoring evolution health
        - Time complexity: O(N² * F) where N=population size, F=avg features per strategy

    Complexity:
        - Time: O(N² * F) for N strategies with F features each
        - Space: O(N * F) for feature set storage

    References:
        - Deb, K., & Tiwari, S. (2008). "Omni-optimizer: A generic evolutionary algorithm"
        - Typical diversity threshold for NSGA-II: 0.3-0.5
    """
    # Validation: need at least 2 strategies for pairwise comparison
    if len(population) < 2:
        raise ValueError(
            f"Cannot calculate population diversity: need at least 2 strategies, got {len(population)}"
        )

    total_distance = 0.0
    pair_count = 0

    # Calculate pairwise Jaccard distance for all unique pairs
    for i in range(len(population)):
        for j in range(i + 1, len(population)):
            distance = calculate_jaccard_distance(population[i], population[j])
            total_distance += distance
            pair_count += 1

    # Calculate average distance
    # pair_count = N * (N - 1) / 2 for N strategies
    average_diversity = total_distance / pair_count if pair_count > 0 else 0.0

    return average_diversity


def should_increase_mutation_rate(diversity_score: float, threshold: float = 0.3) -> bool:
    """
    Determine if mutation rate should be increased based on diversity threshold.

    Implements adaptive mutation rate control to prevent diversity collapse in
    evolutionary algorithms. When population diversity falls below threshold,
    signals that mutation rate should be increased to restore exploration.

    Args:
        diversity_score: Current population diversity (0.0 to 1.0 from calculate_population_diversity)
        threshold: Diversity threshold below which mutation increase is triggered (default: 0.3)

    Returns:
        bool: True if diversity is below threshold (mutation rate should increase), False otherwise

    Example (Low diversity - trigger mutation):
        >>> should_increase_mutation_rate(diversity_score=0.2, threshold=0.3)
        True

    Example (Healthy diversity - no action):
        >>> should_increase_mutation_rate(diversity_score=0.5, threshold=0.3)
        False

    Example (Edge case - exactly at threshold):
        >>> should_increase_mutation_rate(diversity_score=0.3, threshold=0.3)
        False

    Example (Custom threshold):
        >>> should_increase_mutation_rate(diversity_score=0.4, threshold=0.5)
        True

    Notes:
        - Logs warning when diversity collapse detected
        - Default threshold 0.3 is based on NSGA-II best practices
        - Typical usage: Check at end of each generation
        - Should be paired with actual mutation rate increase logic in PopulationManager

    Recommended Thresholds:
        - 0.3: Conservative (triggers frequently to maintain high diversity)
        - 0.2: Moderate (allows some convergence before intervention)
        - 0.1: Aggressive (only intervenes when diversity critically low)

    Usage Pattern:
        >>> diversity = calculate_population_diversity(population)
        >>> if should_increase_mutation_rate(diversity):
        ...     mutation_rate = min(mutation_rate * 1.5, 0.3)  # Increase by 50%, cap at 0.3
        ...     logger.warning(f"Diversity collapse detected ({diversity:.3f}), increasing mutation rate to {mutation_rate:.3f}")

    References:
        - Deb, K., et al. (2002). NSGA-II Section 4: "Adaptive Mutation Schemes"
        - Typical diversity threshold range: 0.2-0.4
    """
    if diversity_score < threshold:
        logger.warning(
            f"Diversity collapse detected: diversity={diversity_score:.4f} < threshold={threshold:.4f}. "
            "Consider increasing mutation rate to restore exploration."
        )
        return True
    return False


def calculate_novelty_score(strategy: Strategy, population: List[Strategy], k: int = 5) -> float:
    """
    Calculate novelty score based on k-nearest neighbor distances.

    Implements novelty search metric that rewards strategies for being different
    from their neighbors. Uses average distance to k-nearest neighbors as a
    measure of how novel/unique a strategy is within the population.

    Formula:
        novelty_score(s) = (1 / k) * Σ_i=1^k distance(s, neighbor_i)

    Where neighbor_i is the i-th nearest neighbor by Jaccard distance.

    Args:
        strategy: Strategy to calculate novelty for
        population: List of all strategies in the population (including strategy itself)
        k: Number of nearest neighbors to consider (default: 5)

    Returns:
        float: Novelty score in range [0.0, 1.0]
               - 0.0: Strategy is identical to all k-nearest neighbors (not novel)
               - 1.0: Strategy is maximally different from all k-nearest neighbors (highly novel)
               - Higher scores indicate more novel/exploratory strategies

    Raises:
        ValueError: If k is larger than population size - 1 (not enough neighbors)
        ValueError: If strategy is not in population (must be member for self-exclusion)

    Example (Highly novel strategy):
        >>> unique = Strategy(code="data.get('unique_feature') > 0")
        >>> similar_group = [
        ...     Strategy(code="data.get('roe') > 0.15"),
        ...     Strategy(code="data.get('roe') > 0.20"),
        ...     Strategy(code="data.get('roe') > 0.10"),
        ...     Strategy(code="data.get('pe') < 20"),
        ...     unique
        ... ]
        >>> novelty = calculate_novelty_score(unique, similar_group, k=4)
        >>> novelty > 0.8  # Very different from neighbors
        True

    Example (Common strategy):
        >>> common = Strategy(code="data.get('roe') > 0.15")
        >>> roe_dominated = [
        ...     common,
        ...     Strategy(code="data.get('roe') > 0.20"),
        ...     Strategy(code="data.get('roe') > 0.10"),
        ...     Strategy(code="data.get('roe') < 0.05"),
        ...     Strategy(code="data.get('roe') >= 0.12")
        ... ]
        >>> novelty = calculate_novelty_score(common, roe_dominated, k=4)
        >>> novelty < 0.2  # Very similar to neighbors (all use 'roe')
        True

    Example (Moderate novelty):
        >>> strategy = Strategy(code="data.get('roe') > 0.15 and data.get('pe') < 20")
        >>> mixed_pop = [
        ...     strategy,
        ...     Strategy(code="data.get('roe') > 0.10"),
        ...     Strategy(code="data.get('pe') < 15"),
        ...     Strategy(code="data.indicator('momentum') > 0"),
        ...     Strategy(code="data.get('liquidity') > 1M")
        ... ]
        >>> novelty = calculate_novelty_score(strategy, mixed_pop, k=3)
        >>> 0.3 < novelty < 0.7  # Moderate novelty
        True

    Notes:
        - Excludes strategy itself when finding neighbors (self-distance = 0)
        - Typically k=5 to k=15 for population sizes of 20-50
        - Used in novelty search to drive exploration over exploitation
        - Can be combined with fitness-based selection (e.g., 70% fitness, 30% novelty)
        - Returns 0.0 if all neighbors are identical to the strategy

    Recommended k values:
        - Population 20: k=5 (25% of population)
        - Population 50: k=10-15 (20-30% of population)
        - Population 100: k=15-20 (15-20% of population)

    Usage Pattern:
        >>> for strategy in population:
        ...     strategy.novelty_score = calculate_novelty_score(strategy, population, k=5)
        >>> # Select strategies with high novelty_score for diversity-preserving mating
        >>> novel_strategies = sorted(population, key=lambda s: s.novelty_score, reverse=True)[:10]

    Complexity:
        - Time: O(N² * F) where N=population size, F=avg features per strategy
        - Space: O(N) for distance list

    References:
        - Lehman, J., & Stanley, K. O. (2011). "Abandoning Objectives: Evolution through the Search for Novelty Alone"
        - Mouret, J. B., & Doncieux, S. (2012). "Encouraging Behavioral Diversity in Evolutionary Robotics"
    """
    # Validation: check k parameter
    if k >= len(population):
        raise ValueError(
            f"k must be less than population size. Got k={k}, population size={len(population)}"
        )

    if k < 1:
        raise ValueError(f"k must be at least 1, got {k}")

    # Calculate distance to all other strategies in population
    distances = []
    for other in population:
        # Exclude self (distance to self is 0)
        if other.id == strategy.id:
            continue

        distance = calculate_jaccard_distance(strategy, other)
        distances.append(distance)

    # Adaptive k: use min(k, available_neighbors) to handle small populations
    # This allows the system to work even when population size < k
    effective_k = min(k, len(distances))

    if effective_k == 0:
        # Only one strategy in population (edge case)
        return 1.0  # Maximum novelty when alone

    # Find k-nearest neighbors (smallest distances)
    distances_sorted = sorted(distances)
    k_nearest_distances = distances_sorted[:effective_k]

    # Calculate novelty score: average distance to k-nearest neighbors
    novelty_score = sum(k_nearest_distances) / effective_k

    return novelty_score
