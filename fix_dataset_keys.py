"""Automatically fix incorrect dataset keys in generated code.

This is a workaround for LLM's tendency to use non-existent keys like
'etl:monthly_revenue:revenue_yoy' despite explicit instructions not to.
"""

import re
from typing import Tuple, List


# Mapping of incorrect keys to correct keys
KEY_FIXES = {
    # Monthly revenue fixes
    "etl:monthly_revenue:revenue_yoy": "monthly_revenue:去年同月增減(%)",
    "etl:monthly_revenue:revenue_mom": "monthly_revenue:上月比較增減(%)",
    "monthly_revenue:revenue_yoy": "monthly_revenue:去年同月增減(%)",
    "monthly_revenue:revenue_mom": "monthly_revenue:上月比較增減(%)",

    # Common incomplete keys
    "monthly_revenue": "monthly_revenue:當月營收",

    # Price-earnings ratio fixes (wrong category)
    "fundamental_features:本益比": "price_earning_ratio:本益比",
    "fundamental_features:股價淨值比": "price_earning_ratio:股價淨值比",

    # ROE alternatives (use fundamental_features version if available)
    "fundamental_features:ROE": "fundamental_features:ROE稅後",

    # Note: etl:investment_trust_buy_sell_summary:strength does NOT exist
    # Use institutional_investors_trading_summary:投信買賣超股數 instead
    "etl:investment_trust_buy_sell_summary:strength": "institutional_investors_trading_summary:投信買賣超股數",
}


def fix_dataset_keys(code: str) -> Tuple[str, List[str]]:
    """Automatically fix incorrect dataset keys in code.

    Args:
        code: Generated Python code with potentially incorrect keys

    Returns:
        Tuple of (fixed_code, list_of_fixes_applied)
    """
    fixes_applied = []
    fixed_code = code

    # Find all data.get() calls
    pattern = r"data\.get\(['\"]([^'\"]+)['\"]\)"

    for match in re.finditer(pattern, code):
        original_key = match.group(1)

        # Check if key needs fixing
        if original_key in KEY_FIXES:
            correct_key = KEY_FIXES[original_key]

            # Replace in code
            old_call = f"data.get('{original_key}')"
            new_call = f"data.get('{correct_key}')"
            fixed_code = fixed_code.replace(old_call, new_call)

            # Also try with double quotes
            old_call_dq = f'data.get("{original_key}")'
            new_call_dq = f'data.get("{correct_key}")'
            fixed_code = fixed_code.replace(old_call_dq, new_call_dq)

            fix_msg = f"Fixed: {original_key} → {correct_key}"
            fixes_applied.append(fix_msg)

    return fixed_code, fixes_applied


def test_fix_dataset_keys():
    """Test the key fixing function."""

    # Test case 1: Wrong monthly revenue key
    code1 = """
close = data.get('price:收盤價')
revenue_yoy = data.get('etl:monthly_revenue:revenue_yoy')
roe = data.get('fundamental_features:ROE稅後')
"""

    fixed1, fixes1 = fix_dataset_keys(code1)

    print("Test 1: Fix wrong monthly revenue key")
    print(f"Original: data.get('etl:monthly_revenue:revenue_yoy')")
    print(f"Fixed: {fixes1}")
    assert "monthly_revenue:去年同月增減(%)" in fixed1
    print("✅ Passed\n")

    # Test case 2: Multiple fixes
    code2 = """
revenue_yoy = data.get("etl:monthly_revenue:revenue_yoy")
revenue_mom = data.get('etl:monthly_revenue:revenue_mom')
"""

    fixed2, fixes2 = fix_dataset_keys(code2)

    print("Test 2: Multiple fixes")
    print(f"Fixes applied: {len(fixes2)}")
    for fix in fixes2:
        print(f"  - {fix}")
    assert len(fixes2) == 2
    print("✅ Passed\n")

    # Test case 3: No fixes needed
    code3 = """
close = data.get('price:收盤價')
roe = data.get('fundamental_features:ROE稅後')
"""

    fixed3, fixes3 = fix_dataset_keys(code3)

    print("Test 3: No fixes needed")
    print(f"Fixes applied: {len(fixes3)}")
    assert len(fixes3) == 0
    assert fixed3 == code3
    print("✅ Passed\n")

    print("All tests passed! ✅")


if __name__ == '__main__':
    test_fix_dataset_keys()
