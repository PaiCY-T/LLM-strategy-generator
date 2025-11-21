"""
Strategy code validator to detect common DataFrame anti-patterns.

This module provides validation for LLM-generated strategy code to catch
common errors before execution, particularly DataFrame comparison issues
that cause "Can only compare identically-labeled DataFrame" errors.
"""

import re
from typing import List, Tuple

# Type alias for pattern tuple (regex, message)
PatternTuple = Tuple[str, str]


class StrategyCodeValidator:
    """
    Validates strategy code for common anti-patterns that cause runtime errors.

    This validator checks for patterns that are syntactically valid but cause
    runtime errors when executed with pandas DataFrames, particularly:
    - DataFrame comparisons in .where() calls
    - Chained .where().fillna() patterns
    - rank() comparison mismatches

    Example:
        >>> validator = StrategyCodeValidator()
        >>> issues = validator.validate("position.where(rank == rank.max())")
        >>> len(issues) > 0
        True
    """

    # Patterns that cause DataFrame comparison errors
    UNSAFE_PATTERNS: List[PatternTuple] = [
        # .where(df == df.max()) pattern - causes label mismatch
        (r'\.where\s*\([^)]*==\s*[^)]*\.max\(\)',
         'CRITICAL: DataFrame comparison in .where() causes label mismatch error'),
        # .where(df).fillna() chain
        (r'\.where\s*\([^)]*\)\s*\.fillna',
         'WARNING: .where().fillna() chain may cause unexpected boolean conversion'),
        # rank comparison with scalar
        (r'\.rank\s*\([^)]*\)\s*==\s*\w+\.rank\s*\([^)]*\)\.max\(',
         'CRITICAL: Comparing rank() result with .max() causes label mismatch'),
    ]

    def validate(self, code: str) -> List[str]:
        """
        Validate strategy code for anti-patterns.

        Args:
            code: Strategy code string to validate

        Returns:
            List of issue messages found (empty list if code is valid)

        Example:
            >>> validator = StrategyCodeValidator()
            >>> validator.validate("position = (cond1 & cond2).is_largest(10)")
            []
        """
        issues: List[str] = []

        for pattern, message in self.UNSAFE_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                issues.append(message)

        return issues
