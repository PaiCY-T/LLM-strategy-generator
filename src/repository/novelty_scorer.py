"""
Novelty Scorer for Strategy Genomes
====================================

Detects duplicate and similar strategies using factor vector analysis and cosine distance.

Novelty Scoring:
    - 1.0 = Completely novel strategy (different factor usage)
    - 0.0 = Duplicate strategy (identical factor vector)
    - <0.2 = Near duplicate (rejected from Hall of Fame)

Factor Vector:
    Captures strategy characteristics:
    - Dataset usage frequency (e.g., price:收盤價, monthly_revenue:當月營收)
    - Technical indicator patterns (e.g., moving averages, momentum)
    - Filter logic patterns (e.g., AND combinations, OR combinations)
"""

import re
from typing import Dict, List, Set, Optional, Tuple
from collections import Counter
import numpy as np
from pathlib import Path


# Duplicate rejection threshold
DUPLICATE_THRESHOLD = 0.2  # Novelty score < 0.2 → reject as duplicate


class NoveltyScorer:
    """
    Calculate novelty scores for strategy genomes using factor vector extraction.

    Features:
        - Dataset usage pattern extraction
        - Technical indicator fingerprinting
        - Cosine distance calculation
        - Duplicate detection and rejection

    Usage:
        >>> scorer = NoveltyScorer()
        >>> existing_vectors = [...]
        >>> novelty_score = scorer.calculate_novelty_score(new_code, existing_vectors)
        >>> if novelty_score < DUPLICATE_THRESHOLD:
        ...     print("Duplicate detected - rejected")
    """

    def __init__(self):
        """Initialize novelty scorer with pre-compiled regex patterns for performance."""
        self.known_datasets = self._build_dataset_registry()

        # Pre-compile regex patterns for performance (avoid repeated compilation)
        self._dataset_pattern = re.compile(r"data\.get\(['\"]([^'\"]+)['\"]\)")
        self._ma_pattern = re.compile(r'\.average\((\d+)\)')
        self._rolling_pattern = re.compile(r'\.rolling\((\d+)\)')
        self._shift_pattern = re.compile(r'\.shift\((\d+)\)')
        self._and_pattern = re.compile(r'&')
        self._or_pattern = re.compile(r'\|')
        self._weighting_pattern = re.compile(r'\*\s*[\w_]+\s*\[')
        self._resample_pattern = re.compile(r"resample=['\"]([^'\"]+)['\"]")

    def _build_dataset_registry(self) -> Set[str]:
        """
        Build registry of known Finlab datasets.

        Returns:
            Set of dataset keys (e.g., 'price:收盤價', 'monthly_revenue:當月營收')
        """
        return {
            # Price data
            'price:收盤價', 'price:開盤價', 'price:最高價', 'price:最低價',
            'price:成交股數', 'price:成交金額',

            # Revenue data
            'monthly_revenue:當月營收', 'monthly_revenue:去年同期營收',
            'monthly_revenue:上月營收', 'monthly_revenue:去年當月營收',

            # Fundamental data
            'fundamental_features:本益比', 'fundamental_features:股價淨值比',
            'fundamental_features:殖利率', 'fundamental_features:市值',

            # Financial statement data
            'price_earning_ratio:本益比', 'etl:股東權益報酬率',
            'etl:總資產報酬率', 'etl:營業毛利率',

            # Insider trading
            'tejdata_shareholding_director:持股增減'
        }

    def _extract_factor_vector(self, code: str) -> Dict[str, float]:
        """
        Extract factor vector from strategy code.

        Factor Vector Components:
            - dataset_usage: Frequency of each dataset used (normalized)
            - technical_indicators: Count of technical indicators (MA, momentum, etc.)
            - filter_patterns: AND/OR combination patterns
            - selection_method: is_largest, is_smallest, rank usage

        Args:
            code: Strategy Python code as string

        Returns:
            Dictionary mapping feature names to normalized frequency values

        Example:
            >>> code = "close = data.get('price:收盤價')\\nma = close.average(20)"
            >>> vector = scorer._extract_factor_vector(code)
            >>> vector['dataset:price:收盤價']
            1.0
        """
        vector = {}

        # 1. Extract dataset usage (using pre-compiled pattern)
        dataset_matches = self._dataset_pattern.findall(code)
        dataset_counts = Counter(dataset_matches)

        # Normalize dataset counts
        total_datasets = sum(dataset_counts.values()) or 1
        for dataset, count in dataset_counts.items():
            vector[f'dataset:{dataset}'] = count / total_datasets

        # 2. Extract technical indicators (using pre-compiled patterns)
        # Moving averages
        ma_periods = self._ma_pattern.findall(code)
        for period in set(ma_periods):
            vector[f'indicator:ma_{period}'] = ma_periods.count(period) / len(ma_periods) if ma_periods else 0

        # Rolling operations
        rolling_periods = self._rolling_pattern.findall(code)
        for period in set(rolling_periods):
            vector[f'indicator:rolling_{period}'] = rolling_periods.count(period) / len(rolling_periods) if rolling_periods else 0

        # Shift operations (lag)
        shift_periods = self._shift_pattern.findall(code)
        if shift_periods:
            vector['indicator:has_shift'] = 1.0

        # 3. Extract filter patterns (using pre-compiled patterns)
        # AND combinations (cond1 & cond2 & ...)
        and_count = len(self._and_pattern.findall(code))
        if and_count > 0:
            vector['filter:and_combinations'] = min(and_count / 10, 1.0)  # Normalize to max 10 ANDs

        # OR combinations (cond1 | cond2 | ...)
        or_count = len(self._or_pattern.findall(code))
        if or_count > 0:
            vector['filter:or_combinations'] = min(or_count / 5, 1.0)  # Normalize to max 5 ORs

        # 4. Extract selection method
        if 'is_largest' in code:
            vector['selection:is_largest'] = 1.0
        elif 'is_smallest' in code:
            vector['selection:is_smallest'] = 1.0

        # Ranking
        if '.rank(' in code:
            vector['selection:rank'] = 1.0

        # 5. Extract weighting patterns (using pre-compiled pattern)
        if self._weighting_pattern.search(code):
            vector['weighting:multiplicative'] = 1.0

        # 6. Extract backtest configuration (using pre-compiled pattern)
        resample_match = self._resample_pattern.search(code)
        if resample_match:
            resample_value = resample_match.group(1)
            vector[f'backtest:resample_{resample_value}'] = 1.0

        return vector

    def _calculate_cosine_distance(
        self,
        vector1: Dict[str, float],
        vector2: Dict[str, float]
    ) -> float:
        """
        Calculate cosine distance between two factor vectors.

        Cosine Distance = 1 - Cosine Similarity
        - 0.0 = Identical vectors (duplicate)
        - 1.0 = Orthogonal vectors (completely different)

        Args:
            vector1: First factor vector
            vector2: Second factor vector

        Returns:
            Cosine distance in range [0.0, 1.0]

        Example:
            >>> v1 = {'dataset:price:收盤價': 0.5, 'indicator:ma_20': 0.5}
            >>> v2 = {'dataset:price:收盤價': 0.5, 'indicator:ma_20': 0.5}
            >>> scorer._calculate_cosine_distance(v1, v2)
            0.0  # Identical
        """
        # Get union of all keys
        all_keys = set(vector1.keys()) | set(vector2.keys())

        if not all_keys:
            return 1.0  # Empty vectors are completely different

        # Create numpy arrays with aligned features
        arr1 = np.array([vector1.get(key, 0.0) for key in all_keys])
        arr2 = np.array([vector2.get(key, 0.0) for key in all_keys])

        # Calculate cosine similarity
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)

        if norm1 == 0 or norm2 == 0:
            return 1.0  # Zero vectors are completely different

        cosine_similarity = np.dot(arr1, arr2) / (norm1 * norm2)

        # Convert to distance (0 = identical, 1 = orthogonal)
        cosine_distance = 1.0 - cosine_similarity

        return float(cosine_distance)

    def extract_vectors_batch(self, codes: List[str]) -> List[Dict[str, float]]:
        """
        Extract factor vectors from multiple strategy codes in batch.

        This method is optimized for bulk vector extraction, useful for
        pre-computing and caching vectors for the Hall of Fame.

        Args:
            codes: List of strategy Python codes

        Returns:
            List of factor vectors (same order as input codes)

        Example:
            >>> codes = [code1, code2, code3]
            >>> vectors = scorer.extract_vectors_batch(codes)
            >>> # Cache vectors for later use
            >>> cached_vectors = {i: v for i, v in enumerate(vectors)}
        """
        return [self._extract_factor_vector(code) for code in codes]

    def calculate_novelty_score_with_cache(
        self,
        new_code: str,
        existing_vectors: List[Dict[str, float]]
    ) -> Tuple[float, Optional[Dict]]:
        """
        Calculate novelty score using pre-computed factor vectors.

        This method avoids O(n) repeated vector extraction by accepting
        pre-computed vectors. Use extract_vectors_batch() to prepare vectors.

        Novelty Score:
            - 1.0 = Completely novel (different from all existing strategies)
            - 0.0 = Duplicate (identical to at least one existing strategy)
            - <0.2 = Near duplicate (should be rejected)

        Args:
            new_code: Python code of new strategy
            existing_vectors: List of pre-computed factor vectors

        Returns:
            Tuple of (novelty_score, most_similar_info)
            - novelty_score: float in [0.0, 1.0]
            - most_similar_info: Dict with details of most similar strategy (if any)

        Example:
            >>> # Pre-compute and cache vectors once
            >>> existing_codes = [code1, code2, code3]
            >>> cached_vectors = scorer.extract_vectors_batch(existing_codes)
            >>>
            >>> # Reuse cached vectors for multiple comparisons
            >>> new_code = "close = data.get('price:收盤價')\\n..."
            >>> score, info = scorer.calculate_novelty_score_with_cache(new_code, cached_vectors)
            >>> if score < 0.2:
            ...     print(f"Duplicate detected: {info}")
        """
        # Extract factor vector from new code
        new_vector = self._extract_factor_vector(new_code)

        if not existing_vectors:
            # No existing strategies - completely novel
            return 1.0, None

        # Calculate distances to all existing strategies (using cached vectors)
        distances = []
        for idx, existing_vector in enumerate(existing_vectors):
            distance = self._calculate_cosine_distance(new_vector, existing_vector)
            distances.append((distance, idx, existing_vector))

        # Find minimum distance (most similar strategy)
        min_distance, most_similar_idx, most_similar_vector = min(distances, key=lambda x: x[0])

        # Build similarity info
        most_similar_info = {
            'index': most_similar_idx,
            'distance': min_distance,
            'similarity': 1.0 - min_distance,
            'shared_features': self._get_shared_features(new_vector, most_similar_vector)
        }

        return min_distance, most_similar_info

    def calculate_novelty_score(
        self,
        new_code: str,
        existing_codes: List[str]
    ) -> Tuple[float, Optional[Dict]]:
        """
        Calculate novelty score for a new strategy against existing strategies.

        Novelty Score:
            - 1.0 = Completely novel (different from all existing strategies)
            - 0.0 = Duplicate (identical to at least one existing strategy)
            - <0.2 = Near duplicate (should be rejected)

        Algorithm:
            1. Extract factor vector from new code
            2. Extract factor vectors from all existing codes
            3. Calculate cosine distance to each existing vector
            4. Return MINIMUM distance (most similar existing strategy)

        Args:
            new_code: Python code of new strategy
            existing_codes: List of Python codes for existing strategies

        Returns:
            Tuple of (novelty_score, most_similar_info)
            - novelty_score: float in [0.0, 1.0]
            - most_similar_info: Dict with details of most similar strategy (if any)

        Example (without caching):
            >>> new_code = "close = data.get('price:收盤價')\\n..."
            >>> existing = ["close = data.get('price:收盤價')\\n..."]
            >>> score, info = scorer.calculate_novelty_score(new_code, existing)
            >>> if score < 0.2:
            ...     print(f"Duplicate detected: {info}")

        Example (with caching for better performance):
            >>> # Pre-compute vectors once
            >>> existing_codes = [code1, code2, code3]
            >>> cached_vectors = scorer.extract_vectors_batch(existing_codes)
            >>>
            >>> # Use cached vectors for multiple comparisons
            >>> score, info = scorer.calculate_novelty_score_with_cache(new_code, cached_vectors)
        """
        # Extract factor vector from new code
        new_vector = self._extract_factor_vector(new_code)

        if not existing_codes:
            # No existing strategies - completely novel
            return 1.0, None

        # Calculate distances to all existing strategies
        distances = []
        for idx, existing_code in enumerate(existing_codes):
            existing_vector = self._extract_factor_vector(existing_code)
            distance = self._calculate_cosine_distance(new_vector, existing_vector)
            distances.append((distance, idx, existing_vector))

        # Find minimum distance (most similar strategy)
        min_distance, most_similar_idx, most_similar_vector = min(distances, key=lambda x: x[0])

        # Build similarity info
        most_similar_info = {
            'index': most_similar_idx,
            'distance': min_distance,
            'similarity': 1.0 - min_distance,
            'shared_features': self._get_shared_features(new_vector, most_similar_vector)
        }

        return min_distance, most_similar_info

    def _get_shared_features(
        self,
        vector1: Dict[str, float],
        vector2: Dict[str, float]
    ) -> List[str]:
        """
        Get list of shared features between two vectors.

        Args:
            vector1: First factor vector
            vector2: Second factor vector

        Returns:
            List of feature names present in both vectors

        Example:
            >>> v1 = {'dataset:price:收盤價': 0.5, 'indicator:ma_20': 0.3}
            >>> v2 = {'dataset:price:收盤價': 0.6, 'indicator:ma_50': 0.4}
            >>> scorer._get_shared_features(v1, v2)
            ['dataset:price:收盤價']
        """
        # Features present in both vectors (non-zero values)
        shared = []
        all_keys = set(vector1.keys()) | set(vector2.keys())

        for key in all_keys:
            val1 = vector1.get(key, 0.0)
            val2 = vector2.get(key, 0.0)

            # Both non-zero = shared feature
            if val1 > 0 and val2 > 0:
                shared.append(key)

        return sorted(shared)

    def is_duplicate(self, novelty_score: float) -> bool:
        """
        Check if novelty score indicates a duplicate strategy.

        Args:
            novelty_score: Calculated novelty score

        Returns:
            True if duplicate (score < threshold), False otherwise

        Example:
            >>> scorer.is_duplicate(0.15)
            True  # Below 0.2 threshold
            >>> scorer.is_duplicate(0.35)
            False  # Above threshold
        """
        return novelty_score < DUPLICATE_THRESHOLD

    def get_factor_vector(self, code: str) -> Dict[str, float]:
        """
        Public method to extract factor vector (for debugging/analysis).

        Args:
            code: Strategy Python code

        Returns:
            Factor vector dictionary

        Example:
            >>> vector = scorer.get_factor_vector(strategy_code)
            >>> print(vector.keys())
        """
        return self._extract_factor_vector(code)
