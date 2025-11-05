"""
Unit tests for diversity metrics (Jaccard distance, novelty search, etc.).

Tests cover:
- Feature extraction from strategy code (extract_feature_set)
- Jaccard distance calculation between strategies
- Population diversity aggregation
- Adaptive mutation rate triggering
- Novelty score calculation with k-nearest neighbors
- Edge cases and error handling

References:
    - Lehman, J., & Stanley, K. O. (2011). "Abandoning Objectives: Evolution through the Search for Novelty Alone"
"""

import pytest
from src.evolution.types import Strategy
from src.evolution.diversity import (
    extract_feature_set,
    calculate_jaccard_distance,
    calculate_population_diversity,
    should_increase_mutation_rate,
    calculate_novelty_score
)


class TestExtractFeatureSet:
    """Test suite for extract_feature_set function (Task 16)."""

    def test_extract_single_get_feature(self):
        """Test extraction of single data.get() feature."""
        code = "data.get('roe') > 0.15"
        features = extract_feature_set(code)
        assert features == {'roe'}

    def test_extract_single_indicator(self):
        """Test extraction of single data.indicator() feature."""
        code = "data.indicator('momentum') > 0"
        features = extract_feature_set(code)
        assert features == {'momentum'}

    def test_extract_multiple_features(self):
        """Test extraction of multiple features with different patterns."""
        code = """
        def strategy(data):
            high_roe = data.get('roe') > 0.15
            good_momentum = data.indicator('momentum') > 0
            liquid = data.get('liquidity') > 1000000
            return high_roe and good_momentum and liquid
        """
        features = extract_feature_set(code)
        assert features == {'roe', 'momentum', 'liquidity'}

    def test_extract_duplicate_features(self):
        """Test that duplicate feature names are deduplicated."""
        code = """
        data.get('roe') > 0.15 and data.get('roe') < 0.30
        """
        features = extract_feature_set(code)
        assert features == {'roe'}

    def test_extract_no_features(self):
        """Test empty set when no features found."""
        code = "def strategy(data): return True"
        features = extract_feature_set(code)
        assert features == set()

    def test_extract_double_quotes(self):
        """Test extraction with double quotes instead of single quotes."""
        code = 'data.get("roe") > 0.15 and data.indicator("momentum") > 0'
        features = extract_feature_set(code)
        assert features == {'roe', 'momentum'}

    def test_extract_mixed_quotes(self):
        """Test extraction with mixed single and double quotes."""
        code = "data.get('roe') > 0.15 and data.indicator(\"momentum\") > 0"
        features = extract_feature_set(code)
        assert features == {'roe', 'momentum'}

    def test_extract_nested_expressions(self):
        """Test extraction from complex nested expressions."""
        code = """
        (data.get('roe') > 0.15 and data.get('pe') < 20) or
        (data.indicator('momentum') > 0 and data.get('liquidity') > 1M)
        """
        features = extract_feature_set(code)
        assert features == {'roe', 'pe', 'momentum', 'liquidity'}

    def test_extract_feature_names_with_underscores(self):
        """Test extraction of feature names containing underscores."""
        code = "data.get('net_income_growth') > 0.10"
        features = extract_feature_set(code)
        assert features == {'net_income_growth'}

    def test_extract_from_empty_string(self):
        """Test extraction from empty code string."""
        code = ""
        features = extract_feature_set(code)
        assert features == set()


class TestCalculateJaccardDistance:
    """Test suite for calculate_jaccard_distance function (Task 17)."""

    def test_identical_strategies(self):
        """Test that identical feature sets yield distance 0.0."""
        s1 = Strategy(code="data.get('roe') > 0.15")
        s2 = Strategy(code="data.get('roe') > 0.20")  # Different threshold, same feature
        distance = calculate_jaccard_distance(s1, s2)
        assert distance == 0.0

    def test_completely_different_strategies(self):
        """Test that disjoint feature sets yield distance 1.0."""
        s1 = Strategy(code="data.get('roe') > 0.15")
        s2 = Strategy(code="data.indicator('momentum') > 0")
        distance = calculate_jaccard_distance(s1, s2)
        assert distance == 1.0

    def test_partial_overlap(self):
        """Test strategies with partial feature overlap."""
        s1 = Strategy(code="data.get('roe') > 0.15 and data.get('pe') < 20")
        s2 = Strategy(code="data.get('roe') > 0.10 and data.indicator('momentum') > 0")
        distance = calculate_jaccard_distance(s1, s2)

        # Features: s1={'roe', 'pe'}, s2={'roe', 'momentum'}
        # Intersection: {'roe'} (1 element)
        # Union: {'roe', 'pe', 'momentum'} (3 elements)
        # Jaccard similarity: 1/3 ≈ 0.333
        # Jaccard distance: 1 - 1/3 ≈ 0.667
        assert abs(distance - (2/3)) < 0.001

    def test_both_empty_feature_sets(self):
        """Test edge case where both strategies have no features."""
        s1 = Strategy(code="return True")
        s2 = Strategy(code="return False")
        distance = calculate_jaccard_distance(s1, s2)
        assert distance == 0.0  # Both empty → considered identical

    def test_one_empty_feature_set(self):
        """Test edge case where one strategy has no features."""
        s1 = Strategy(code="data.get('roe') > 0.15")
        s2 = Strategy(code="return True")
        distance = calculate_jaccard_distance(s1, s2)
        assert distance == 1.0  # Disjoint (non-empty vs empty)

    def test_symmetry(self):
        """Test that Jaccard distance is symmetric."""
        s1 = Strategy(code="data.get('roe') > 0.15")
        s2 = Strategy(code="data.indicator('momentum') > 0")

        distance_12 = calculate_jaccard_distance(s1, s2)
        distance_21 = calculate_jaccard_distance(s2, s1)

        assert distance_12 == distance_21

    def test_complex_feature_sets(self):
        """Test with complex strategies using many features."""
        s1 = Strategy(code="""
            data.get('roe') > 0.15 and
            data.get('pe') < 20 and
            data.get('liquidity') > 1000000
        """)
        s2 = Strategy(code="""
            data.get('roe') > 0.10 and
            data.indicator('momentum') > 0 and
            data.get('dividend_yield') > 0.03
        """)
        distance = calculate_jaccard_distance(s1, s2)

        # s1: {'roe', 'pe', 'liquidity'}
        # s2: {'roe', 'momentum', 'dividend_yield'}
        # Intersection: {'roe'} (1)
        # Union: 5 features
        # Distance: 1 - 1/5 = 0.8
        assert abs(distance - 0.8) < 0.001


class TestCalculatePopulationDiversity:
    """Test suite for calculate_population_diversity function (Task 18)."""

    def test_diverse_population(self):
        """Test population with completely different strategies."""
        strategies = [
            Strategy(code="data.get('roe') > 0.15"),
            Strategy(code="data.indicator('momentum') > 0"),
            Strategy(code="data.get('liquidity') > 1000000")
        ]
        diversity = calculate_population_diversity(strategies)
        assert diversity == 1.0  # All pairwise distances are 1.0

    def test_identical_population(self):
        """Test population where all strategies use same features."""
        strategies = [
            Strategy(code="data.get('roe') > 0.15"),
            Strategy(code="data.get('roe') > 0.20"),
            Strategy(code="data.get('roe') > 0.10")
        ]
        diversity = calculate_population_diversity(strategies)
        assert diversity == 0.0  # All pairwise distances are 0.0

    def test_moderate_diversity(self):
        """Test population with moderate diversity (partial overlaps)."""
        strategies = [
            Strategy(code="data.get('roe') > 0.15 and data.get('pe') < 20"),
            Strategy(code="data.get('roe') > 0.10 and data.indicator('momentum') > 0"),
            Strategy(code="data.indicator('momentum') > 0 and data.get('liquidity') > 1M")
        ]
        diversity = calculate_population_diversity(strategies)

        # Expected pairwise distances:
        # s1-s2: 1 - |{roe}| / |{roe, pe, momentum}| = 1 - 1/3 ≈ 0.667
        # s1-s3: 1 - |{}| / |{roe, pe, momentum, liquidity}| = 1.0
        # s2-s3: 1 - |{momentum}| / |{roe, momentum, liquidity}| = 1 - 1/3 ≈ 0.667
        # Average: (0.667 + 1.0 + 0.667) / 3 ≈ 0.778
        expected = (2/3 + 1.0 + 2/3) / 3
        assert abs(diversity - expected) < 0.001

    def test_two_strategies(self):
        """Test edge case with exactly 2 strategies."""
        strategies = [
            Strategy(code="data.get('roe') > 0.15"),
            Strategy(code="data.indicator('momentum') > 0")
        ]
        diversity = calculate_population_diversity(strategies)
        assert diversity == 1.0  # Single pair, completely different

    def test_raises_error_for_single_strategy(self):
        """Test that ValueError is raised for population size < 2."""
        strategies = [Strategy(code="data.get('roe') > 0.15")]

        with pytest.raises(ValueError, match="need at least 2 strategies"):
            calculate_population_diversity(strategies)

    def test_raises_error_for_empty_population(self):
        """Test that ValueError is raised for empty population."""
        strategies = []

        with pytest.raises(ValueError, match="need at least 2 strategies"):
            calculate_population_diversity(strategies)

    def test_large_population(self):
        """Test with larger population to verify pairwise calculation."""
        # Create 5 strategies with incrementally different features
        strategies = [
            Strategy(code="data.get('roe') > 0.15"),
            Strategy(code="data.get('roe') > 0.15 and data.get('pe') < 20"),
            Strategy(code="data.get('roe') > 0.15 and data.get('liquidity') > 1M"),
            Strategy(code="data.get('pe') < 20 and data.indicator('momentum') > 0"),
            Strategy(code="data.indicator('momentum') > 0")
        ]
        diversity = calculate_population_diversity(strategies)

        # Diversity should be between 0 and 1
        assert 0.0 <= diversity <= 1.0
        # Should be moderate diversity (not all identical, not all completely different)
        assert 0.3 < diversity < 0.9


class TestShouldIncreaseMutationRate:
    """Test suite for should_increase_mutation_rate function (Task 19)."""

    def test_triggers_when_below_threshold(self):
        """Test that mutation increase is triggered when diversity below threshold."""
        result = should_increase_mutation_rate(diversity_score=0.2, threshold=0.3)
        assert result is True

    def test_no_trigger_when_above_threshold(self):
        """Test that mutation increase is not triggered when diversity above threshold."""
        result = should_increase_mutation_rate(diversity_score=0.5, threshold=0.3)
        assert result is False

    def test_no_trigger_when_exactly_at_threshold(self):
        """Test behavior when diversity equals threshold (should not trigger)."""
        result = should_increase_mutation_rate(diversity_score=0.3, threshold=0.3)
        assert result is False

    def test_custom_threshold(self):
        """Test with custom threshold value."""
        result = should_increase_mutation_rate(diversity_score=0.4, threshold=0.5)
        assert result is True

    def test_very_low_diversity(self):
        """Test with critically low diversity."""
        result = should_increase_mutation_rate(diversity_score=0.05, threshold=0.3)
        assert result is True

    def test_very_high_diversity(self):
        """Test with very high diversity."""
        result = should_increase_mutation_rate(diversity_score=0.9, threshold=0.3)
        assert result is False

    def test_edge_case_zero_diversity(self):
        """Test edge case with zero diversity."""
        result = should_increase_mutation_rate(diversity_score=0.0, threshold=0.3)
        assert result is True

    def test_edge_case_maximum_diversity(self):
        """Test edge case with maximum diversity."""
        result = should_increase_mutation_rate(diversity_score=1.0, threshold=0.3)
        assert result is False


class TestCalculateNoveltyScore:
    """Test suite for calculate_novelty_score function (Task 21)."""

    def test_highly_novel_strategy(self):
        """Test strategy that is very different from its neighbors."""
        unique = Strategy(id='unique', code="data.get('unique_feature') > 0")
        similar_group = [
            Strategy(id='s1', code="data.get('roe') > 0.15"),
            Strategy(id='s2', code="data.get('roe') > 0.20"),
            Strategy(id='s3', code="data.get('roe') > 0.10"),
            Strategy(id='s4', code="data.get('pe') < 20"),
            unique
        ]
        novelty = calculate_novelty_score(unique, similar_group, k=4)

        # 'unique' uses completely different feature from all neighbors
        # All distances to neighbors should be 1.0
        assert novelty == 1.0

    def test_common_strategy(self):
        """Test strategy that is very similar to its neighbors."""
        common = Strategy(id='common', code="data.get('roe') > 0.15")
        roe_dominated = [
            common,
            Strategy(id='s1', code="data.get('roe') > 0.20"),
            Strategy(id='s2', code="data.get('roe') > 0.10"),
            Strategy(id='s3', code="data.get('roe') < 0.05"),
            Strategy(id='s4', code="data.get('roe') >= 0.12")
        ]
        novelty = calculate_novelty_score(common, roe_dominated, k=4)

        # All strategies use same feature 'roe'
        # All distances should be 0.0
        assert novelty == 0.0

    def test_moderate_novelty(self):
        """Test strategy with moderate novelty."""
        strategy = Strategy(id='target', code="data.get('roe') > 0.15 and data.get('pe') < 20")
        mixed_pop = [
            strategy,
            Strategy(id='s1', code="data.get('roe') > 0.10"),
            Strategy(id='s2', code="data.get('pe') < 15"),
            Strategy(id='s3', code="data.indicator('momentum') > 0"),
            Strategy(id='s4', code="data.get('liquidity') > 1M")
        ]
        novelty = calculate_novelty_score(strategy, mixed_pop, k=3)

        # Expected distances to 3 nearest neighbors:
        # s1: 1 - |{roe}| / |{roe, pe}| = 1 - 1/2 = 0.5
        # s2: 1 - |{pe}| / |{roe, pe}| = 1 - 1/2 = 0.5
        # s3: 1 - |{}| / |{roe, pe, momentum}| = 1.0
        # Novelty: (0.5 + 0.5 + 1.0) / 3 ≈ 0.667
        assert abs(novelty - (2/3)) < 0.001

    def test_raises_error_for_k_too_large(self):
        """Test that ValueError is raised when k >= population size."""
        strategies = [
            Strategy(id='s1', code="data.get('roe') > 0.15"),
            Strategy(id='s2', code="data.get('pe') < 20")
        ]

        with pytest.raises(ValueError, match="k must be less than population size"):
            calculate_novelty_score(strategies[0], strategies, k=2)

    def test_raises_error_for_k_zero(self):
        """Test that ValueError is raised for k=0."""
        strategies = [
            Strategy(id='s1', code="data.get('roe') > 0.15"),
            Strategy(id='s2', code="data.get('pe') < 20")
        ]

        with pytest.raises(ValueError, match="k must be at least 1"):
            calculate_novelty_score(strategies[0], strategies, k=0)

    def test_raises_error_for_negative_k(self):
        """Test that ValueError is raised for negative k."""
        strategies = [
            Strategy(id='s1', code="data.get('roe') > 0.15"),
            Strategy(id='s2', code="data.get('pe') < 20")
        ]

        with pytest.raises(ValueError, match="k must be at least 1"):
            calculate_novelty_score(strategies[0], strategies, k=-1)

    def test_k_equals_one(self):
        """Test with k=1 (only nearest neighbor)."""
        target = Strategy(id='target', code="data.get('roe') > 0.15")
        population = [
            target,
            Strategy(id='s1', code="data.get('roe') > 0.20"),  # Distance 0.0
            Strategy(id='s2', code="data.indicator('momentum') > 0")  # Distance 1.0
        ]
        novelty = calculate_novelty_score(target, population, k=1)

        # Nearest neighbor is s1 with distance 0.0
        assert novelty == 0.0

    def test_excludes_self_from_neighbors(self):
        """Test that strategy is excluded from its own k-nearest neighbors."""
        strategy = Strategy(id='target', code="data.get('roe') > 0.15")
        population = [
            strategy,
            Strategy(id='s1', code="data.get('roe') > 0.20"),
            Strategy(id='s2', code="data.get('roe') > 0.10")
        ]
        novelty = calculate_novelty_score(strategy, population, k=2)

        # Should calculate distance to s1 and s2, not to itself
        # Both distances should be 0.0 (same feature 'roe')
        assert novelty == 0.0

    def test_large_k(self):
        """Test with large k value (many neighbors)."""
        target = Strategy(id='target', code="data.get('roe') > 0.15")
        population = [target]

        # Add 10 strategies with varying similarity
        for i in range(10):
            if i < 5:
                # Similar strategies (use 'roe')
                population.append(Strategy(id=f's{i}', code=f"data.get('roe') > {0.10 + i*0.01}"))
            else:
                # Different strategies (use other features)
                population.append(Strategy(id=f's{i}', code=f"data.get('feature_{i}') > 0"))

        novelty = calculate_novelty_score(target, population, k=10)

        # k-nearest should include 5 similar (distance 0.0) and 5 different (distance 1.0)
        # Novelty: (5*0.0 + 5*1.0) / 10 = 0.5
        assert abs(novelty - 0.5) < 0.001


class TestIntegrationScenarios:
    """Integration tests combining multiple diversity functions."""

    def test_diversity_workflow(self):
        """Test complete diversity analysis workflow."""
        # Create population
        population = [
            Strategy(id='s1', code="data.get('roe') > 0.15"),
            Strategy(id='s2', code="data.get('roe') > 0.15 and data.get('pe') < 20"),
            Strategy(id='s3', code="data.indicator('momentum') > 0"),
            Strategy(id='s4', code="data.get('liquidity') > 1000000")
        ]

        # Calculate population diversity
        diversity = calculate_population_diversity(population)
        assert 0.0 <= diversity <= 1.0

        # Check if mutation rate should increase
        should_increase = should_increase_mutation_rate(diversity, threshold=0.5)

        # Calculate novelty scores for all strategies
        novelty_scores = []
        for strategy in population:
            novelty = calculate_novelty_score(strategy, population, k=2)
            novelty_scores.append(novelty)

        # All novelty scores should be valid
        assert all(0.0 <= score <= 1.0 for score in novelty_scores)

    def test_feature_extraction_consistency(self):
        """Test that feature extraction is consistent across diversity calculations."""
        code1 = "data.get('roe') > 0.15 and data.get('pe') < 20"
        code2 = "data.get('roe') > 0.10 and data.indicator('momentum') > 0"

        # Extract features
        features1 = extract_feature_set(code1)
        features2 = extract_feature_set(code2)

        # Create strategies
        s1 = Strategy(code=code1)
        s2 = Strategy(code=code2)

        # Calculate Jaccard distance manually
        intersection = features1 & features2
        union = features1 | features2
        expected_distance = 1.0 - (len(intersection) / len(union))

        # Compare with function result
        calculated_distance = calculate_jaccard_distance(s1, s2)

        assert abs(calculated_distance - expected_distance) < 0.001
