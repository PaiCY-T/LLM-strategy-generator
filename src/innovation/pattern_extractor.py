"""
Pattern Extraction - Task 3.1

Analyzes top-performing innovations to extract winning patterns
and guide future LLM generation.

Responsibilities:
- Extract factor combinations from successful innovations
- Identify parameter ranges that work well
- Detect common patterns across top performers
- Build pattern library for LLM context
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from collections import Counter, defaultdict
import re
import json
from datetime import datetime


class PatternExtractor:
    """
    Extract patterns from successful innovations.

    Analyzes top-performing innovations to identify:
    - Common data fields used (e.g., ROE, revenue growth)
    - Mathematical operations (multiply, divide, ratios)
    - Factor combinations that work well together
    - Parameter ranges (rolling windows, thresholds)
    """

    def __init__(self, min_pattern_frequency: int = 2):
        """
        Initialize pattern extractor.

        Args:
            min_pattern_frequency: Minimum times a pattern must appear
                                  to be considered significant
        """
        self.min_pattern_frequency = min_pattern_frequency
        self.pattern_library: Dict[str, Any] = {
            'field_patterns': {},
            'operation_patterns': {},
            'combination_patterns': {},
            'parameter_ranges': {},
            'extraction_timestamp': None
        }

    def extract_patterns(
        self,
        innovations: List[Dict[str, Any]],
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Extract patterns from top N innovations.

        Args:
            innovations: List of innovation dictionaries
            top_n: Number of top innovations to analyze

        Returns:
            Pattern library with extracted patterns
        """
        # Sort by performance (Sharpe ratio)
        sorted_innovations = sorted(
            innovations,
            key=lambda x: x.get('performance', {}).get('sharpe_ratio', 0),
            reverse=True
        )

        top_innovations = sorted_innovations[:top_n]

        # Extract different pattern types
        self.pattern_library['field_patterns'] = self._extract_field_patterns(top_innovations)
        self.pattern_library['operation_patterns'] = self._extract_operation_patterns(top_innovations)
        self.pattern_library['combination_patterns'] = self._extract_combination_patterns(top_innovations)
        self.pattern_library['parameter_ranges'] = self._extract_parameter_ranges(top_innovations)
        self.pattern_library['extraction_timestamp'] = datetime.now().isoformat()
        self.pattern_library['analyzed_innovations'] = len(top_innovations)

        return self.pattern_library

    def _extract_field_patterns(self, innovations: List[Dict]) -> Dict[str, int]:
        """
        Extract which data fields are used most frequently.

        Example: {'fundamental_features:ROE稅後': 5, 'price:收盤價': 3}
        """
        field_counter = Counter()

        for innovation in innovations:
            code = innovation.get('code', '')

            # Find all data.get() calls
            pattern = r"data\.get\(['\"]([^'\"]+)['\"]\)"
            matches = re.findall(pattern, code)

            field_counter.update(matches)

        # Filter by minimum frequency
        return {
            field: count
            for field, count in field_counter.items()
            if count >= self.min_pattern_frequency
        }

    def _extract_operation_patterns(self, innovations: List[Dict]) -> Dict[str, int]:
        """
        Extract mathematical operations used.

        Example: {'division': 4, 'multiplication': 3, 'rolling': 2}
        """
        operation_counter = Counter()

        for innovation in innovations:
            code = innovation.get('code', '')

            # Detect operations
            if '/' in code:
                operation_counter['division'] += 1
            if '*' in code:
                operation_counter['multiplication'] += 1
            if '+' in code:
                operation_counter['addition'] += 1
            if '-' in code:
                operation_counter['subtraction'] += 1
            if '.rolling(' in code:
                operation_counter['rolling_window'] += 1
            if '.rank(' in code:
                operation_counter['rank'] += 1
            if '.replace(' in code:
                operation_counter['replace'] += 1
            if 'np.log' in code or 'log' in code:
                operation_counter['logarithm'] += 1

        return dict(operation_counter)

    def _extract_combination_patterns(self, innovations: List[Dict]) -> List[Dict[str, Any]]:
        """
        Extract field combinations that appear together.

        Example: [{'fields': ['ROE', 'P/E'], 'frequency': 3, 'avg_sharpe': 0.85}]
        """
        combinations = defaultdict(lambda: {'count': 0, 'sharpe_sum': 0})

        for innovation in innovations:
            code = innovation.get('code', '')
            sharpe = innovation.get('performance', {}).get('sharpe_ratio', 0)

            # Find all fields in this innovation
            pattern = r"data\.get\(['\"]([^'\"]+)['\"]\)"
            fields = set(re.findall(pattern, code))

            # For each pair of fields
            if len(fields) >= 2:
                fields_list = sorted(fields)  # Sort for consistency
                key = tuple(fields_list)

                combinations[key]['count'] += 1
                combinations[key]['sharpe_sum'] += sharpe

        # Convert to list format
        result = []
        for fields_tuple, stats in combinations.items():
            if stats['count'] >= self.min_pattern_frequency:
                result.append({
                    'fields': list(fields_tuple),
                    'frequency': stats['count'],
                    'avg_sharpe': stats['sharpe_sum'] / stats['count']
                })

        # Sort by average Sharpe
        return sorted(result, key=lambda x: x['avg_sharpe'], reverse=True)

    def _extract_parameter_ranges(self, innovations: List[Dict]) -> Dict[str, Dict[str, float]]:
        """
        Extract parameter ranges (e.g., rolling window sizes).

        Example: {'rolling_window': {'min': 10, 'max': 50, 'median': 20}}
        """
        params = defaultdict(list)

        for innovation in innovations:
            code = innovation.get('code', '')

            # Extract rolling window sizes
            rolling_pattern = r'\.rolling\((\d+)\)'
            rolling_matches = re.findall(rolling_pattern, code)
            params['rolling_window'].extend([int(x) for x in rolling_matches])

        # Calculate statistics for each parameter
        result = {}
        for param_name, values in params.items():
            if values:
                result[param_name] = {
                    'min': min(values),
                    'max': max(values),
                    'median': sorted(values)[len(values) // 2],
                    'values': values
                }

        return result

    def get_pattern_summary(self) -> str:
        """
        Get human-readable pattern summary for LLM prompt.

        Returns:
            Formatted string describing patterns
        """
        if not self.pattern_library.get('field_patterns'):
            return "No patterns extracted yet."

        summary_parts = []

        # Top fields
        top_fields = sorted(
            self.pattern_library['field_patterns'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        if top_fields:
            summary_parts.append("**Top Fields Used**:")
            for field, count in top_fields:
                summary_parts.append(f"  - {field}: {count} times")

        # Top operations
        ops = self.pattern_library.get('operation_patterns', {})
        if ops:
            summary_parts.append("\n**Common Operations**:")
            for op, count in sorted(ops.items(), key=lambda x: x[1], reverse=True)[:3]:
                summary_parts.append(f"  - {op}: {count} times")

        # Top combinations
        combos = self.pattern_library.get('combination_patterns', [])[:3]
        if combos:
            summary_parts.append("\n**Winning Combinations**:")
            for combo in combos:
                fields_str = ' + '.join([f.split(':')[-1] for f in combo['fields']])
                summary_parts.append(
                    f"  - {fields_str} "
                    f"(freq: {combo['frequency']}, avg Sharpe: {combo['avg_sharpe']:.3f})"
                )

        # Parameter ranges
        params = self.pattern_library.get('parameter_ranges', {})
        if params:
            summary_parts.append("\n**Parameter Ranges**:")
            for param, stats in params.items():
                summary_parts.append(
                    f"  - {param}: {stats['min']}-{stats['max']} "
                    f"(median: {stats['median']})"
                )

        return "\n".join(summary_parts)

    def save_patterns(self, filepath: str):
        """Save pattern library to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.pattern_library, f, indent=2, ensure_ascii=False)

    def load_patterns(self, filepath: str):
        """Load pattern library from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            self.pattern_library = json.load(f)


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING PATTERN EXTRACTOR")
    print("=" * 70)

    # Mock innovations for testing
    mock_innovations = [
        {
            'code': "factor = data.get('fundamental_features:ROE稅後') / data.get('fundamental_features:淨值比')",
            'performance': {'sharpe_ratio': 0.85}
        },
        {
            'code': "factor = data.get('price:收盤價').rolling(20).mean() / data.get('price:收盤價').rolling(50).mean()",
            'performance': {'sharpe_ratio': 0.72}
        },
        {
            'code': "factor = (data.get('fundamental_features:營收成長率') * data.get('fundamental_features:營業毛利率')) / data.get('fundamental_features:本益比')",
            'performance': {'sharpe_ratio': 0.91}
        }
    ]

    # Extract patterns
    extractor = PatternExtractor(min_pattern_frequency=1)
    patterns = extractor.extract_patterns(mock_innovations, top_n=3)

    print("\nExtracted Patterns:")
    print(extractor.get_pattern_summary())

    print("\n" + "=" * 70)
    print("PATTERN EXTRACTOR TEST COMPLETE")
    print("=" * 70)
