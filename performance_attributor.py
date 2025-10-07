"""Performance Attribution System for Strategy Learning Loop.

Analyzes generated strategies to identify success factors and failure patterns.
Uses regex-based extraction for rapid MVP implementation (80/20 solution).

Future: Migrate to AST parsing for robustness.
"""

import re
from typing import Dict, Any, List, Optional, Tuple


def extract_strategy_params(code: str) -> Dict[str, Any]:
    """Extract key strategy parameters using regex patterns.

    Args:
        code: Generated strategy Python code

    Returns:
        Dictionary of extracted parameters:
        - datasets: List of data.get() calls
        - liquidity_threshold: Trading value filter threshold
        - roe_smoothing_window: ROE rolling window (or 1 if simple shift)
        - factor_combination: Combined factor formula
        - price_filter: Minimum stock price threshold
        - volume_filter: Volume threshold (if present)
    """
    params = {}

    # 1. Extract datasets used
    datasets = re.findall(r"data\.get\(['\"]([^'\"]+)['\"]\)", code)
    params['datasets'] = sorted(list(set(datasets)))

    # 2. Liquidity filter threshold
    liquidity_match = re.search(
        r"trading_value\.rolling\(\d+\)\.mean\(\)\.shift\(\d+\)\s*>\s*([\d_]+)",
        code
    )
    if liquidity_match:
        threshold_str = liquidity_match.group(1).replace('_', '')
        params['liquidity_threshold'] = int(threshold_str)
    else:
        params['liquidity_threshold'] = None

    # 3. ROE smoothing detection
    roe_rolling_match = re.search(r"roe\.rolling\(window=(\d+)", code)
    if roe_rolling_match:
        params['roe_smoothing_window'] = int(roe_rolling_match.group(1))
        params['roe_type'] = 'smoothed'
    elif "roe.shift(" in code:
        params['roe_smoothing_window'] = 1
        params['roe_type'] = 'raw'
    else:
        params['roe_smoothing_window'] = None
        params['roe_type'] = 'not_used'

    # 4. Revenue data handling
    if "revenue_yoy.ffill()" in code:
        params['revenue_handling'] = 'forward_fill'
    elif "revenue_yoy.rolling(" in code:
        params['revenue_handling'] = 'smoothed'
    elif "revenue_yoy.shift(" in code:
        params['revenue_handling'] = 'simple_shift'
    else:
        params['revenue_handling'] = 'not_used'

    # 5. Value factor type (P/E vs P/B)
    if 'pe_ratio' in code:
        params['value_factor'] = 'pe_ratio'
    elif 'pb_ratio' in code:
        params['value_factor'] = 'pb_ratio'
    else:
        params['value_factor'] = None

    # 6. Price filter
    price_match = re.search(r"close\.shift\(\d+\)\s*>\s*(\d+)", code)
    if price_match:
        params['price_filter'] = int(price_match.group(1))
    else:
        params['price_filter'] = None

    # 7. Volume filter
    volume_match = re.search(r"volume.*?>\s*([\d_]+)", code)
    if volume_match:
        threshold_str = volume_match.group(1).replace('_', '')
        params['volume_filter'] = int(threshold_str)
    else:
        params['volume_filter'] = None

    # 8. Factor combination formula
    combined_match = re.search(
        r"combined_factor\s*=\s*\((.*?)\)",
        code,
        re.DOTALL
    )
    if combined_match:
        formula = combined_match.group(1).replace('\n', ' ').strip()
        params['factor_combination'] = formula
    else:
        # Handle simple sum case (iteration 0)
        combined_match = re.search(r"combined_factor\s*=\s*(.*)", code)
        if combined_match:
            params['factor_combination'] = combined_match.group(1).strip()
        else:
            params['factor_combination'] = 'unknown'

    return params


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
    params: Dict[str, Any],
    metrics: Dict[str, float]
) -> List[str]:
    """Extract key success patterns from a high-performing strategy.

    Args:
        params: Strategy parameters
        metrics: Performance metrics

    Returns:
        List of success pattern descriptions
    """
    patterns = []

    if metrics.get('sharpe_ratio', 0) < 0.8:
        return patterns  # Not a successful strategy

    # ROE smoothing
    if params['roe_type'] == 'smoothed':
        patterns.append(f"ROE {params['roe_smoothing_window']}-quarter rolling average (noise reduction)")

    # Strict liquidity
    if params['liquidity_threshold'] and params['liquidity_threshold'] >= 100_000_000:
        patterns.append(f"Strict liquidity filter (≥{params['liquidity_threshold']:,} TWD)")

    # Forward fill revenue
    if params['revenue_handling'] == 'forward_fill':
        patterns.append("Forward-filled revenue data (simple and effective)")

    # Value factor
    if params['value_factor']:
        patterns.append(f"Value factor: {params['value_factor']}")

    return patterns


# Example usage and testing
if __name__ == '__main__':
    # Test with iteration 1 code
    test_code = """
    roe_avg = roe.rolling(window=4, min_periods=1).mean().ffill().shift(1)
    revenue_yoy_daily = revenue_yoy.ffill().shift(1)
    liquidity_filter = trading_value.rolling(20).mean().shift(1) > 100_000_000
    combined_factor = (momentum * 0.4 + revenue_yoy_daily * 0.3)
    """

    params = extract_strategy_params(test_code)
    print("Extracted parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
