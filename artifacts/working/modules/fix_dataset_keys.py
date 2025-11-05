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
    "price:本益比": "price_earning_ratio:本益比",  # Common LLM mistake
    "price:股價淨值比": "price_earning_ratio:股價淨值比",  # Common LLM mistake

    # ROE alternatives (use fundamental_features version if available)
    "fundamental_features:ROE": "fundamental_features:ROE稅後",

    # Institutional investor fixes - these etl:*:strength keys do NOT exist
    "etl:investment_trust_buy_sell_summary:strength": "institutional_investors_trading_summary:投信買賣超股數",
    "etl:foreign_main_force_buy_sell_summary:strength": "institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)",
    "etl:dealer_buy_sell_summary:strength": "institutional_investors_trading_summary:自營商買賣超股數(自行買賣)",

    # Common non-existent aggregated keys - map to proper institutional investors data
    "foreign_main_force_buy_sell_summary": "institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)",
    "investment_trust_buy_sell_summary": "institutional_investors_trading_summary:投信買賣超股數",
    "dealer_buy_sell_summary": "institutional_investors_trading_summary:自營商買賣超股數(自行買賣)",
    "three_main_forces_buy_sell_summary": "institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)",

    # Financial statement fixes (wrong category - use financial_statement not fundamental_features)
    "fundamental_features:EPS": "financial_statement:每股盈餘",
    "fundamental_features:每股盈餘": "financial_statement:每股盈餘",
    "fundamental_features:營業收入": "financial_statement:營業收入",

    # NOTE: Technical indicators are available via data.indicator() function, NOT data.get()
    # The LLM should use: data.indicator('RSI', timeperiod=14)
    # NOT: data.get('indicator:RSI')
    # We cannot auto-fix this as it requires changing the function call, not just the key

    # Market value variations
    "market_value": "etl:market_value",
    "etl:stock_market_value": "etl:market_value",

    # Common price key mistakes (LLM uses Chinese names with wrong prefix)
    "price:收盤價": "etl:adj_close",  # LLM mistake: should use adjusted close
    "price:開盤價": "etl:adj_open",   # LLM mistake: should use adjusted open
    "price:成交股數": "price:成交金額",  # LLM mistake: volume doesn't exist, use trading value
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

    # STEP 1: Fix indicator calls (data.get('indicator:XXX') → data.indicator('XXX'))
    indicator_pattern = r"data\.get\(['\"]indicator:([^'\"]+)['\"]\)"
    indicator_matches = list(re.finditer(indicator_pattern, code))

    for match in indicator_matches:
        indicator_name = match.group(1)
        old_call = match.group(0)
        new_call = f"data.indicator('{indicator_name}')"

        fixed_code = fixed_code.replace(old_call, new_call)
        fix_msg = f"Fixed: data.get('indicator:{indicator_name}') → data.indicator('{indicator_name}')"
        fixes_applied.append(fix_msg)

    # STEP 2: Fix incorrect dataset keys
    pattern = r"data\.get\(['\"]([^'\"]+)['\"]\)"

    for match in re.finditer(pattern, fixed_code):
        original_key = match.group(1)

        # Skip if already an indicator call
        if original_key.startswith('indicator:'):
            continue

        # Check if key needs fixing
        if original_key in KEY_FIXES:
            correct_key = KEY_FIXES[original_key]

            # Check if key is unfixable (mapped to None)
            if correct_key is None:
                continue

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
