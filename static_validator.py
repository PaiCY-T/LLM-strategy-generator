"""Static validation of generated strategy code before execution.

Pre-execution validator that checks for invalid dataset keys and unsupported
methods to prevent runtime failures. Part of Phase 2 fix to reach 60%+ success rate.
"""

import re
from typing import List, Tuple, Set


# Load available datasets from CSV extraction
def load_available_datasets() -> Set[str]:
    """Load the list of valid dataset keys from available_datasets.txt."""
    try:
        with open('available_datasets.txt', 'r', encoding='utf-8') as f:
            datasets = set()
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    datasets.add(line)
            return datasets
    except FileNotFoundError:
        # Fallback to hardcoded critical datasets
        return {
            'price:收盤價', 'price:開盤價', 'price:最高價', 'price:最低價',
            'price:成交股數', 'price:成交金額', 'price:漲跌價差', 'price:漲跌幅',
            'etl:market_value', 'monthly_revenue:當月營收', 'monthly_revenue:去年同月增減(%)',
            'financial_statement:每股盈餘', 'fundamental_features:ROE稅後',
            'price_earning_ratio:本益比',
            'institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)',
            'institutional_investors_trading_summary:投信買賣超股數',
        }


# Unsupported FinlabDataFrame methods
UNSUPPORTED_METHODS = {
    'between': 'Use .apply(lambda x: x.between(low, high)) instead',
    'isin': 'Use .apply(lambda x: x.isin(values)) for element-wise operation',
}


def validate_dataset_keys(code: str) -> Tuple[bool, List[str]]:
    """Validate that all dataset keys in code exist in available datasets.

    Args:
        code: Generated strategy code

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    available = load_available_datasets()

    # Pattern to match data.get('key') calls
    pattern = r"data\.get\(['\"]([^'\"]+)['\"]\)"

    for match in re.finditer(pattern, code):
        key = match.group(1)

        # Skip indicator calls (they use data.indicator() not data.get())
        if key.startswith('indicator:'):
            errors.append(f"Invalid: data.get('{key}') - use data.indicator('{key.replace('indicator:', '')}') instead")
            continue

        # Check if key exists
        if key not in available:
            errors.append(f"Unknown dataset key: '{key}' not in available datasets")

    return len(errors) == 0, errors


def validate_unsupported_methods(code: str) -> Tuple[bool, List[str]]:
    """Check for unsupported DataFrame methods.

    Args:
        code: Generated strategy code

    Returns:
        Tuple of (is_valid, list_of_warnings)
    """
    warnings = []

    for method, suggestion in UNSUPPORTED_METHODS.items():
        # Pattern to match .method( calls
        pattern = rf"\.{method}\s*\("

        if re.search(pattern, code):
            warnings.append(f"Unsupported method: .{method}() - {suggestion}")

    return len(warnings) == 0, warnings


def validate_code(code: str) -> Tuple[bool, List[str]]:
    """Comprehensive static validation of strategy code.

    Args:
        code: Generated strategy code

    Returns:
        Tuple of (is_valid, list_of_all_issues)
    """
    all_issues = []

    # Check dataset keys
    keys_valid, key_errors = validate_dataset_keys(code)
    all_issues.extend(key_errors)

    # Check unsupported methods
    methods_valid, method_warnings = validate_unsupported_methods(code)
    all_issues.extend(method_warnings)

    return len(all_issues) == 0, all_issues


def main():
    """Test the validator."""
    test_code = """
# Test code
close = data.get('price:收盤價')
volume = data.get('price:成交股數')
bad_key = data.get('price:漲跌百分比')  # This doesn't exist
rsi = data.get('indicator:RSI')  # Wrong - should use data.indicator()
market_cap = data.get('market_value')  # Wrong - should be etl:market_value

# Unsupported method
filtered = close.between(10, 100)  # This won't work
"""

    is_valid, issues = validate_code(test_code)

    print("Validation Result:", "PASS" if is_valid else "FAIL")
    print(f"\nIssues found: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")


if __name__ == '__main__':
    main()
