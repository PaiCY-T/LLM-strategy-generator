"""Performance Attribution System for Strategy Learning Loop.

Analyzes generated strategies to identify success factors and failure patterns.
Uses regex-based extraction for rapid MVP implementation (80/20 solution).

Future: Migrate to AST parsing for robustness.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from src.constants import CRITICAL_PARAMS, MODERATE_PARAMS, LOW_PARAMS


def extract_strategy_params(code: str) -> Dict[str, Any]:
    """Extract key strategy parameters using robust regex patterns.

    Enhanced with:
    - Scientific notation support (e.g., 1e8)
    - Underscore number support (e.g., 100_000_000)
    - Flexible whitespace handling
    - Comprehensive error handling
    - Extraction failure tracking

    Args:
        code: Generated strategy Python code

    Returns:
        Dictionary of extracted parameters:
        - datasets: List of data.get() calls
        - liquidity_threshold: Trading value filter threshold
        - roe_smoothing_window: ROE rolling window (or 1 if simple shift)
        - roe_type: 'smoothed', 'raw', or 'not_used'
        - revenue_handling: Processing method for revenue data
        - value_factor: 'pe_ratio', 'pb_ratio', or None
        - price_filter: Minimum stock price threshold
        - volume_filter: Volume threshold (if present)
        - factor_combination: Combined factor formula
        - extraction_failures: List of failed parameter extractions (if any)
    """
    params = {}
    extraction_failures = []

    # 1. Extract datasets used
    try:
        datasets = re.findall(r"data\.get\(['\"]([^'\"]+)['\"]\)", code)
        params['datasets'] = sorted(list(set(datasets)))
    except Exception as e:
        extraction_failures.append({
            'parameter': 'datasets',
            'error': str(e),
            'context': code[:200] if len(code) > 200 else code
        })
        params['datasets'] = []

    # 2. Liquidity filter threshold (CRITICAL parameter)
    # Enhanced regex: Handles scientific notation, underscores, flexible whitespace
    try:
        # Pattern 1: Simple comparison (liquidity > VALUE or trading_value > VALUE)
        liquidity_match = re.search(
            r'(?:trading_value|liquidity).*?>\s*([\d_e\.]+)',
            code,
            re.IGNORECASE
        )
        if liquidity_match:
            threshold_str = liquidity_match.group(1).replace('_', '')
            # Convert scientific notation: 1e8 -> 100000000
            params['liquidity_threshold'] = int(float(threshold_str))
        else:
            params['liquidity_threshold'] = None
    except Exception as e:
        extraction_failures.append({
            'parameter': 'liquidity_threshold',
            'error': str(e),
            'context': _extract_code_context(code, 'liquidity')
        })
        params['liquidity_threshold'] = None

    # 3. ROE smoothing detection (CRITICAL parameter)
    # Enhanced regex: Flexible whitespace, handles window= parameter
    try:
        roe_rolling_match = re.search(
            r'roe\s*\.\s*rolling\s*\(\s*window\s*=\s*(\d+)',
            code,
            re.IGNORECASE
        )
        if roe_rolling_match:
            params['roe_smoothing_window'] = int(roe_rolling_match.group(1))
            params['roe_type'] = 'smoothed'
        elif re.search(r'roe\s*\.\s*shift\s*\(', code, re.IGNORECASE):
            params['roe_smoothing_window'] = 1
            params['roe_type'] = 'raw'
        else:
            params['roe_smoothing_window'] = None
            params['roe_type'] = 'not_used'
    except Exception as e:
        extraction_failures.append({
            'parameter': 'roe_smoothing_window',
            'error': str(e),
            'context': _extract_code_context(code, 'roe')
        })
        params['roe_smoothing_window'] = None
        params['roe_type'] = 'not_used'

    # 4. Revenue data handling (MODERATE parameter)
    try:
        if re.search(r'revenue_yoy\s*\.\s*ffill\s*\(', code, re.IGNORECASE):
            params['revenue_handling'] = 'forward_fill'
        elif re.search(r'revenue_yoy\s*\.\s*rolling\s*\(', code, re.IGNORECASE):
            params['revenue_handling'] = 'smoothed'
        elif re.search(r'revenue_yoy\s*\.\s*shift\s*\(', code, re.IGNORECASE):
            params['revenue_handling'] = 'simple_shift'
        else:
            params['revenue_handling'] = 'not_used'
    except Exception as e:
        extraction_failures.append({
            'parameter': 'revenue_handling',
            'error': str(e),
            'context': _extract_code_context(code, 'revenue')
        })
        params['revenue_handling'] = 'not_used'

    # 5. Value factor type (MODERATE parameter)
    try:
        if re.search(r'pe_ratio', code, re.IGNORECASE):
            params['value_factor'] = 'pe_ratio'
        elif re.search(r'pb_ratio', code, re.IGNORECASE):
            params['value_factor'] = 'pb_ratio'
        else:
            params['value_factor'] = None
    except Exception as e:
        extraction_failures.append({
            'parameter': 'value_factor',
            'error': str(e),
            'context': code[:200] if len(code) > 200 else code
        })
        params['value_factor'] = None

    # 6. Price filter (LOW parameter)
    # Enhanced regex: Supports scientific notation and underscores
    try:
        price_match = re.search(
            r'close\s*\.\s*shift\s*\(\s*\d+\s*\)\s*>\s*([\d_e\.]+)',
            code,
            re.IGNORECASE
        )
        if price_match:
            price_str = price_match.group(1).replace('_', '')
            params['price_filter'] = int(float(price_str))
        else:
            params['price_filter'] = None
    except Exception as e:
        extraction_failures.append({
            'parameter': 'price_filter',
            'error': str(e),
            'context': _extract_code_context(code, 'close')
        })
        params['price_filter'] = None

    # 7. Volume filter (LOW parameter)
    # Enhanced regex: Supports scientific notation and underscores
    try:
        volume_match = re.search(
            r'volume.*?>\s*([\d_e\.]+)',
            code,
            re.IGNORECASE
        )
        if volume_match:
            threshold_str = volume_match.group(1).replace('_', '')
            params['volume_filter'] = int(float(threshold_str))
        else:
            params['volume_filter'] = None
    except Exception as e:
        extraction_failures.append({
            'parameter': 'volume_filter',
            'error': str(e),
            'context': _extract_code_context(code, 'volume')
        })
        params['volume_filter'] = None

    # 8. Factor combination formula
    try:
        combined_match = re.search(
            r'combined_factor\s*=\s*\((.*?)\)',
            code,
            re.DOTALL | re.IGNORECASE
        )
        if combined_match:
            formula = combined_match.group(1).replace('\n', ' ').strip()
            params['factor_combination'] = formula
        else:
            # Handle simple sum case (iteration 0)
            combined_match = re.search(
                r'combined_factor\s*=\s*(.*)',
                code,
                re.IGNORECASE
            )
            if combined_match:
                params['factor_combination'] = combined_match.group(1).strip()
            else:
                params['factor_combination'] = 'unknown'
    except Exception as e:
        extraction_failures.append({
            'parameter': 'factor_combination',
            'error': str(e),
            'context': _extract_code_context(code, 'combined_factor')
        })
        params['factor_combination'] = 'unknown'

    # Log extraction failures if any
    if extraction_failures:
        params['extraction_failures'] = extraction_failures
        _log_extraction_failures(extraction_failures)

    return params


def _extract_code_context(code: str, keyword: str, context_lines: int = 3) -> str:
    """Extract code context around a keyword for error logging.

    Args:
        code: Full code string
        keyword: Keyword to find context around
        context_lines: Number of lines of context to include

    Returns:
        Code snippet around the keyword
    """
    lines = code.split('\n')
    keyword_lines = [i for i, line in enumerate(lines) if keyword.lower() in line.lower()]

    if not keyword_lines:
        return code[:200] if len(code) > 200 else code

    # Get first occurrence with context
    idx = keyword_lines[0]
    start = max(0, idx - context_lines)
    end = min(len(lines), idx + context_lines + 1)

    return '\n'.join(lines[start:end])


def _log_extraction_failures(failures: List[Dict[str, str]]) -> None:
    """Log extraction failures with context for debugging.

    Args:
        failures: List of extraction failure dictionaries
    """
    print("\n" + "=" * 60)
    print("⚠️  PARAMETER EXTRACTION FAILURES")
    print("=" * 60)

    for failure in failures:
        param = failure['parameter']
        error = failure['error']
        context = failure['context']

        print(f"\n❌ Parameter: {param}")
        print(f"   Error: {error}")
        print(f"   Context:")
        for line in context.split('\n'):
            print(f"      {line}")

    print("\n" + "=" * 60)
    print("ℹ️  Fallback values used for failed extractions")
    print("=" * 60 + "\n")


def compare_strategies(
    prev_params: Dict[str, Any],
    curr_params: Dict[str, Any],
    prev_metrics: Dict[str, float],
    curr_metrics: Dict[str, float]
) -> Dict[str, Any]:
    """Compare two strategies and identify key differences.

    Args:
        prev_params: Previous strategy parameters
        curr_params: Current strategy parameters
        prev_metrics: Previous performance metrics
        curr_metrics: Current performance metrics

    Returns:
        Dictionary with:
        - changes: List of detected changes
        - performance_delta: Change in Sharpe ratio
        - assessment: 'improved', 'degraded', or 'similar'
        - critical_changes: List of changes to ROE/liquidity (high impact)
    """
    changes = []
    critical_changes = []

    prev_sharpe = prev_metrics.get('sharpe_ratio', 0)
    curr_sharpe = curr_metrics.get('sharpe_ratio', 0)
    sharpe_delta = curr_sharpe - prev_sharpe

    # Compare liquidity threshold
    if prev_params['liquidity_threshold'] != curr_params['liquidity_threshold']:
        change = {
            'parameter': 'liquidity_threshold',
            'from': prev_params['liquidity_threshold'],
            'to': curr_params['liquidity_threshold'],
            'impact': 'critical'
        }
        changes.append(change)
        critical_changes.append(change)

    # Compare ROE smoothing (CRITICAL)
    if prev_params['roe_smoothing_window'] != curr_params['roe_smoothing_window']:
        change = {
            'parameter': 'roe_smoothing',
            'from': f"{prev_params['roe_type']} (window={prev_params['roe_smoothing_window']})",
            'to': f"{curr_params['roe_type']} (window={curr_params['roe_smoothing_window']})",
            'impact': 'critical'
        }
        changes.append(change)
        critical_changes.append(change)

    # Compare revenue handling
    if prev_params['revenue_handling'] != curr_params['revenue_handling']:
        changes.append({
            'parameter': 'revenue_handling',
            'from': prev_params['revenue_handling'],
            'to': curr_params['revenue_handling'],
            'impact': 'moderate'
        })

    # Compare value factor
    if prev_params['value_factor'] != curr_params['value_factor']:
        changes.append({
            'parameter': 'value_factor',
            'from': prev_params['value_factor'],
            'to': curr_params['value_factor'],
            'impact': 'moderate'
        })

    # Compare filters
    if prev_params['price_filter'] != curr_params['price_filter']:
        changes.append({
            'parameter': 'price_filter',
            'from': prev_params['price_filter'],
            'to': curr_params['price_filter'],
            'impact': 'low'
        })

    if prev_params['volume_filter'] != curr_params['volume_filter']:
        changes.append({
            'parameter': 'volume_filter',
            'from': prev_params['volume_filter'],
            'to': curr_params['volume_filter'],
            'impact': 'low'
        })

    # Assess performance change
    if sharpe_delta > 0.1:
        assessment = 'improved'
    elif sharpe_delta < -0.1:
        assessment = 'degraded'
    else:
        assessment = 'similar'

    return {
        'changes': changes,
        'critical_changes': critical_changes,
        'performance_delta': sharpe_delta,
        'prev_sharpe': prev_sharpe,
        'curr_sharpe': curr_sharpe,
        'assessment': assessment
    }


def generate_attribution_feedback(
    comparison: Dict[str, Any],
    iteration_num: int,
    champion_iteration: Optional[int] = None
) -> str:
    """Generate human-readable feedback with performance attribution.

    Args:
        comparison: Result from compare_strategies()
        iteration_num: Current iteration number
        champion_iteration: Iteration number of best strategy (if any)

    Returns:
        Structured feedback string for LLM learning
    """
    curr_sharpe = comparison['curr_sharpe']
    prev_sharpe = comparison['prev_sharpe']
    delta = comparison['performance_delta']
    assessment = comparison['assessment']
    changes = comparison['changes']
    critical_changes = comparison['critical_changes']

    feedback_lines = []

    # Header
    feedback_lines.append("=" * 60)
    feedback_lines.append(f"PERFORMANCE ATTRIBUTION - Iteration {iteration_num}")
    feedback_lines.append("=" * 60)
    feedback_lines.append("")

    # Performance summary
    if assessment == 'improved':
        emoji = "✅ IMPROVEMENT"
        direction = "improved"
    elif assessment == 'degraded':
        emoji = "❌ REGRESSION"
        direction = "degraded"
    else:
        emoji = "➡️ SIMILAR"
        direction = "remained similar"

    feedback_lines.append(f"{emoji}: Sharpe ratio {direction}")
    feedback_lines.append(f"  Previous: {prev_sharpe:.4f}")
    feedback_lines.append(f"  Current:  {curr_sharpe:.4f}")
    feedback_lines.append(f"  Delta:    {delta:+.4f}")
    feedback_lines.append("")

    # Changes analysis
    if not changes:
        feedback_lines.append("ℹ️  No significant parameter changes detected.")
    else:
        feedback_lines.append(f"📊 DETECTED CHANGES ({len(changes)} total):")
        feedback_lines.append("")

        # Critical changes first
        if critical_changes:
            feedback_lines.append("🔥 CRITICAL CHANGES (High Impact):")
            for change in critical_changes:
                feedback_lines.append(f"  • {change['parameter']}:")
                feedback_lines.append(f"      From: {change['from']}")
                feedback_lines.append(f"      To:   {change['to']}")
            feedback_lines.append("")

        # Other changes
        other_changes = [c for c in changes if c['impact'] != 'critical']
        if other_changes:
            feedback_lines.append("📝 Other Changes:")
            for change in other_changes:
                feedback_lines.append(f"  • {change['parameter']}: {change['from']} → {change['to']}")
            feedback_lines.append("")

    # Attribution insights
    feedback_lines.append("💡 ATTRIBUTION INSIGHTS:")

    if assessment == 'degraded' and critical_changes:
        feedback_lines.append("")
        feedback_lines.append("⚠️  Performance degraded after critical changes:")
        for change in critical_changes:
            if change['parameter'] == 'roe_smoothing':
                if 'raw' in str(change['to']) and 'smoothed' in str(change['from']):
                    feedback_lines.append("  • Removing ROE smoothing likely increased noise")
                    feedback_lines.append("    → 4-quarter rolling average provides stable signal")
            elif change['parameter'] == 'liquidity_threshold':
                if change['to'] and change['from'] and change['to'] < change['from']:
                    feedback_lines.append("  • Relaxing liquidity filter likely reduced quality")
                    feedback_lines.append(f"    → Higher threshold ({change['from']}) selects more stable stocks")

    elif assessment == 'improved' and critical_changes:
        feedback_lines.append("")
        feedback_lines.append("✅ Performance improved after critical changes:")
        for change in critical_changes:
            if change['parameter'] == 'roe_smoothing':
                if 'smoothed' in str(change['to']):
                    feedback_lines.append("  • Adding ROE smoothing reduced noise")
            elif change['parameter'] == 'liquidity_threshold':
                if change['to'] and change['from'] and change['to'] > change['from']:
                    feedback_lines.append("  • Stricter liquidity filter improved quality")

    else:
        feedback_lines.append("  • No critical changes detected in this iteration")

    feedback_lines.append("")

    # Learning directives
    if champion_iteration is not None and assessment == 'degraded':
        feedback_lines.append("🎯 LEARNING DIRECTIVE:")
        feedback_lines.append(f"  → Review iteration {champion_iteration}'s successful patterns")
        feedback_lines.append("  → Preserve proven elements: ROE smoothing, strict filters")
        feedback_lines.append("  → Make INCREMENTAL improvements, not revolutionary changes")

    feedback_lines.append("=" * 60)

    return "\n".join(feedback_lines)


def extract_success_patterns(
    code: str,
    parameters: Dict[str, Any]
) -> List[str]:
    """Extract preservation directives from successful strategy.

    Analyzes strategy code and parameters to identify key success patterns
    that should be preserved in future iterations. Patterns are categorized
    by criticality level and returned with actionable descriptions.

    Args:
        code: Strategy code string
        parameters: Extracted parameter dict from extract_strategy_params()

    Returns:
        List of human-readable success pattern strings, sorted by criticality
    """
    from src.constants import CRITICAL_PARAMS, MODERATE_PARAMS

    patterns = []

    # Critical Pattern 1: ROE Smoothing
    if parameters.get('roe_type') == 'smoothed':
        window = parameters.get('roe_smoothing_window', 1)
        patterns.append(
            f"roe.rolling(window={window}).mean() - "
            f"{window}-quarter smoothing reduces quarterly noise"
        )

    # Critical Pattern 2: Strict Liquidity Filter
    threshold = parameters.get('liquidity_threshold')
    if threshold and threshold >= 100_000_000:
        patterns.append(
            f"liquidity_filter > {threshold:,} TWD - "
            f"Selects stable, high-volume stocks"
        )

    # Moderate Pattern 3: Revenue Handling
    if parameters.get('revenue_handling') == 'forward_filled':
        patterns.append(
            "revenue_yoy.ffill() - "
            "Forward-filled revenue data handles missing values"
        )

    # Moderate Pattern 4: Value Factor
    if parameters.get('value_factor') == 'inverse_pe':
        patterns.append(
            "1 / pe_ratio - "
            "Value factor using inverse P/E ratio"
        )

    # Low Pattern 5: Price Filter
    price_filter = parameters.get('price_filter')
    if price_filter and price_filter > 0:
        patterns.append(
            f"price > {price_filter} TWD - "
            f"Filters penny stocks"
        )

    # Low Pattern 6: Volume Filter
    volume_filter = parameters.get('volume_filter')
    if volume_filter and volume_filter > 0:
        patterns.append(
            f"volume > {volume_filter:,} shares - "
            f"Ensures adequate trading volume"
        )

    # Additional patterns extracted from code analysis
    # Pattern 7: Market cap filter (if present in code)
    if 'market_cap' in code.lower() and 'filter' in code.lower():
        patterns.append(
            "market_cap filter - "
            "Size-based stock selection"
        )

    # Pattern 8: Sector filtering (if present)
    if 'sector' in code.lower() or 'industry' in code.lower():
        patterns.append(
            "sector/industry filter - "
            "Industry-specific selection"
        )

    # Prioritize patterns by criticality
    return _prioritize_patterns(patterns)


def _prioritize_patterns(patterns: List[str]) -> List[str]:
    """Sort patterns by criticality (critical first, then moderate, then low).

    Identifies patterns by keywords and reorders them to present
    critical success factors first, followed by moderate and low impact patterns.

    Args:
        patterns: List of pattern description strings

    Returns:
        Sorted list with critical patterns first, moderate second, low last
    """
    # Critical keywords indicate high-impact patterns
    critical_keywords = ['rolling', 'liquidity', 'smoothing', 'filter >']

    # Moderate keywords indicate medium-impact patterns
    moderate_keywords = ['ffill', 'forward', 'inverse', 'value']

    # Categorize patterns
    critical = []
    moderate = []
    low = []

    for pattern in patterns:
        pattern_lower = pattern.lower()
        if any(keyword in pattern_lower for keyword in critical_keywords):
            critical.append(pattern)
        elif any(keyword in pattern_lower for keyword in moderate_keywords):
            moderate.append(pattern)
        else:
            low.append(pattern)

    # Return in priority order: critical → moderate → low
    return critical + moderate + low


# Example usage and testing
if __name__ == '__main__':
    print("=" * 60)
    print("Testing Enhanced Regex Extraction")
    print("=" * 60)

    # Test 1: Standard notation with underscores
    print("\n1. Test: Standard notation with underscores")
    test_code_1 = """
    roe_avg = roe.rolling(window=4, min_periods=1).mean().ffill().shift(1)
    revenue_yoy_daily = revenue_yoy.ffill().shift(1)
    liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000
    combined_factor = (momentum * 0.4 + revenue_yoy_daily * 0.3)
    """
    params_1 = extract_strategy_params(test_code_1)
    print(f"  Liquidity threshold: {params_1.get('liquidity_threshold')}")
    print(f"  ROE smoothing window: {params_1.get('roe_smoothing_window')}")
    print(f"  ROE type: {params_1.get('roe_type')}")

    # Test 2: Scientific notation
    print("\n2. Test: Scientific notation")
    test_code_2 = """
    roe_avg = roe  .  rolling  (  window  =  4  )  .  mean()
    liquidity_filter = liquidity > 1e8
    combined_factor = (momentum * 0.5 + roe_avg * 0.5)
    """
    params_2 = extract_strategy_params(test_code_2)
    print(f"  Liquidity threshold: {params_2.get('liquidity_threshold')}")
    print(f"  ROE smoothing window: {params_2.get('roe_smoothing_window')}")

    # Test 3: Flexible whitespace
    print("\n3. Test: Flexible whitespace")
    test_code_3 = """
    roe_avg=roe.rolling(window=8).mean()
    liquidity>1.5e8
    close  .  shift  (  1  )  >  10
    volume>5000000
    """
    params_3 = extract_strategy_params(test_code_3)
    print(f"  Liquidity threshold: {params_3.get('liquidity_threshold')}")
    print(f"  ROE smoothing window: {params_3.get('roe_smoothing_window')}")
    print(f"  Price filter: {params_3.get('price_filter')}")
    print(f"  Volume filter: {params_3.get('volume_filter')}")

    # Test 4: Combined edge cases
    print("\n4. Test: Combined edge cases (underscores + scientific notation)")
    test_code_4 = """
    data.get('price:收盤價')
    data.get('financial_statement:綜合損益表')
    ROE.rolling(window=12).mean()
    LIQUIDITY > 2_500_000_000
    Close.shift(1) > 1.5e1
    VOLUME > 1e6
    """
    params_4 = extract_strategy_params(test_code_4)
    print(f"  Datasets: {params_4.get('datasets')}")
    print(f"  Liquidity threshold: {params_4.get('liquidity_threshold')}")
    print(f"  ROE smoothing window: {params_4.get('roe_smoothing_window')}")
    print(f"  Price filter: {params_4.get('price_filter')}")
    print(f"  Volume filter: {params_4.get('volume_filter')}")

    # Test 5: Extraction failures (intentionally malformed)
    print("\n5. Test: Extraction failures (malformed code)")
    test_code_5 = """
    liquidity > abc123
    roe.rolling(window=invalid)
    """
    params_5 = extract_strategy_params(test_code_5)
    if 'extraction_failures' in params_5:
        print(f"  Failures detected: {len(params_5['extraction_failures'])} parameters")
    else:
        print("  No failures (graceful fallback succeeded)")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
