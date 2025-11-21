"""Strategy code validator to detect common DataFrame anti-patterns."""

import re
from typing import List


class StrategyCodeValidator:
    """Validates strategy code for common anti-patterns that cause runtime errors."""

    # Patterns that cause DataFrame comparison errors
    UNSAFE_PATTERNS = [
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
            code: Strategy code to validate

        Returns:
            List of issues found (empty if code is valid)
        """
        issues = []

        for pattern, message in self.UNSAFE_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                issues.append(message)

        return issues
