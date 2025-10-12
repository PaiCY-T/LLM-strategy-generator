#!/usr/bin/env python3
"""Analyze learning cycle metrics from iteration history."""
import json
import ast
import re
import os
from datetime import datetime
from typing import Optional, Dict, Any, List


def extract_liquidity_threshold(strategy_code: str) -> Optional[int]:
    """
    Extract liquidity threshold from strategy code using AST parsing.

    Looks for patterns like:
    - trading_value.rolling(N).mean() > THRESHOLD
    - trading_value.rolling(N).mean().shift(M) > THRESHOLD

    Args:
        strategy_code: Python code as string

    Returns:
        Threshold value in TWD (e.g., 150_000_000) or None if not found
    """
    try:
        # First attempt: AST parsing
        tree = ast.parse(strategy_code)

        for node in ast.walk(tree):
            # Look for Compare nodes (e.g., x > y)
            if isinstance(node, ast.Compare):
                # Check if left side contains rolling/mean on trading_value
                left_str = ast.unparse(node.left) if hasattr(ast, 'unparse') else ''

                # Check if this is a trading value comparison
                if 'trading_value' in left_str and 'rolling' in left_str and 'mean' in left_str:
                    # Check for > operator
                    if any(isinstance(op, ast.Gt) for op in node.ops):
                        # Extract the threshold (right side of comparison)
                        for comparator in node.comparators:
                            if isinstance(comparator, ast.Constant):
                                return int(comparator.value)
                            elif isinstance(comparator, ast.Num):  # Python 3.7 compatibility
                                return int(comparator.n)

        # If AST parsing didn't find it, fall back to regex
        return _extract_threshold_regex(strategy_code)

    except SyntaxError:
        # Fall back to regex if AST parsing fails
        return _extract_threshold_regex(strategy_code)
    except Exception as e:
        print(f"  Warning: Error extracting threshold: {e}")
        return _extract_threshold_regex(strategy_code)


def _extract_threshold_regex(strategy_code: str) -> Optional[int]:
    """
    Fallback regex-based threshold extraction.

    Looks for patterns like:
    - trading_value.rolling(...).mean() > NUMBER
    - trading_value.rolling(...).mean().shift(...) > NUMBER
    """
    # Pattern to match liquidity threshold comparisons
    # Matches: trading_value.rolling(...).mean() > 100_000_000
    # or: trading_value.rolling(...).mean().shift(...) > 100_000_000
    patterns = [
        r'trading_value\.rolling\([^)]+\)\.mean\(\)(?:\.shift\([^)]+\))?\s*>\s*(\d[\d_]*)',
        r'avg_trading_value\s*>\s*(\d[\d_]*)',
        r'liquidity_filter\s*=\s*(?:avg_trading_value|trading_value\.rolling\([^)]+\)\.mean\(\)(?:\.shift\([^)]+\))?)\s*>\s*(\d[\d_]*)'
    ]

    for pattern in patterns:
        match = re.search(pattern, strategy_code)
        if match:
            # Remove underscores from number (e.g., 100_000_000 -> 100000000)
            threshold_str = match.group(1).replace('_', '')
            return int(threshold_str)

    return None


def check_liquidity_compliance(
    iteration_num: int,
    strategy_file: str,
    min_threshold: int = 150_000_000
) -> Dict[str, Any]:
    """
    Check if a strategy file meets liquidity compliance requirements.

    Args:
        iteration_num: Iteration number
        strategy_file: Path to strategy file
        min_threshold: Minimum required threshold (default: 150M TWD)

    Returns:
        Dict with compliance result:
        {
            'iteration': int,
            'threshold_found': int or None,
            'compliant': bool,
            'timestamp': str,
            'strategy_file': str,
            'min_threshold': int
        }
    """
    result = {
        'iteration': iteration_num,
        'threshold_found': None,
        'compliant': False,
        'timestamp': datetime.now().isoformat(),
        'strategy_file': strategy_file,
        'min_threshold': min_threshold
    }

    try:
        if not os.path.exists(strategy_file):
            result['error'] = 'File not found'
            return result

        with open(strategy_file, 'r', encoding='utf-8') as f:
            strategy_code = f.read()

        threshold = extract_liquidity_threshold(strategy_code)
        result['threshold_found'] = threshold

        if threshold is not None:
            result['compliant'] = threshold >= min_threshold

    except Exception as e:
        result['error'] = str(e)

    return result


def log_compliance_result(
    result: Dict[str, Any],
    log_file: str = 'liquidity_compliance.json'
) -> None:
    """
    Append compliance result to JSON log file.

    Creates file if it doesn't exist with proper structure.
    Uses atomic write to prevent corruption.

    Args:
        result: Compliance check result dictionary
        log_file: Path to log file (default: liquidity_compliance.json)
    """
    # Initialize log structure
    log_data = {
        'checks': [],
        'summary': {
            'total_checks': 0,
            'compliant_count': 0,
            'compliance_rate': 0.0,
            'last_updated': datetime.now().isoformat()
        }
    }

    # Read existing log if it exists
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            # If file is corrupted, start fresh
            pass

    # Append new result (only if not already logged to prevent duplicates)
    existing_iterations = {c['iteration'] for c in log_data['checks']}
    if result['iteration'] not in existing_iterations:
        log_data['checks'].append(result)

    # Update summary
    log_data['summary']['total_checks'] = len(log_data['checks'])
    log_data['summary']['compliant_count'] = sum(
        1 for c in log_data['checks'] if c.get('compliant', False)
    )
    log_data['summary']['compliance_rate'] = (
        log_data['summary']['compliant_count'] / log_data['summary']['total_checks']
        if log_data['summary']['total_checks'] > 0 else 0.0
    )
    log_data['summary']['last_updated'] = datetime.now().isoformat()

    # Atomic write: write to temp file then rename
    temp_file = log_file + '.tmp'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, log_file)
    except Exception as e:
        # Clean up temp file on error
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise e


def get_compliance_statistics(
    log_file: str = 'liquidity_compliance.json'
) -> Dict[str, Any]:
    """
    Calculate compliance statistics from log.

    Args:
        log_file: Path to log file (default: liquidity_compliance.json)

    Returns:
        Dict with statistics:
        {
            'total_checks': int,
            'compliant_count': int,
            'compliance_rate': float,
            'non_compliant_iterations': List[int],
            'average_threshold': float or None
        }
    """
    stats = {
        'total_checks': 0,
        'compliant_count': 0,
        'compliance_rate': 0.0,
        'non_compliant_iterations': [],
        'average_threshold': None
    }

    if not os.path.exists(log_file):
        return stats

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        checks = log_data.get('checks', [])
        stats['total_checks'] = len(checks)
        stats['compliant_count'] = sum(1 for c in checks if c.get('compliant', False))

        if stats['total_checks'] > 0:
            stats['compliance_rate'] = stats['compliant_count'] / stats['total_checks']

        # Find non-compliant iterations
        stats['non_compliant_iterations'] = [
            c['iteration'] for c in checks if not c.get('compliant', False)
        ]

        # Calculate average threshold (only for strategies where threshold was found)
        thresholds = [c['threshold_found'] for c in checks if c.get('threshold_found') is not None]
        if thresholds:
            stats['average_threshold'] = sum(thresholds) / len(thresholds)

    except (json.JSONDecodeError, IOError) as e:
        print(f"  Warning: Error reading compliance log: {e}")

    return stats


def analyze_iteration_history():
    """Analyze iteration history and generate metrics report."""
    try:
        with open('iteration_history.json', 'r', encoding='utf-8') as f:
            content = f.read().strip()

            # Check if file is empty or malformed
            if not content or content == '[]':
                print("⚠️  iteration_history.json is empty or invalid")
                return

            # Try to parse as JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                print(f"First 200 chars: {content[:200]}")
                return

            # Handle dict with 'records' key or list directly
            if isinstance(data, dict) and 'records' in data:
                history = data['records']
            elif isinstance(data, list):
                history = data
            else:
                print(f"❌ Expected list or dict with 'records', got {type(data)}")
                return

            if len(history) == 0:
                print("⚠️  No iterations recorded")
                return

            # Analyze iterations
            total = len(history)
            valid_iterations = [h for h in history if isinstance(h, dict) and 'metrics' in h]

            print(f"📊 Learning Cycle Metrics Analysis")
            print(f"=" * 60)
            print(f"Total iterations: {total}")
            print(f"Valid iterations: {len(valid_iterations)}")

            if not valid_iterations:
                print("⚠️  No valid iterations with metrics found")
                return

            # Find champion - handle None metrics
            def get_sharpe(x):
                if x is None or not isinstance(x, dict):
                    return float('-inf')
                metrics = x.get('metrics')
                if metrics is None or not isinstance(metrics, dict):
                    return float('-inf')
                return metrics.get('sharpe_ratio', float('-inf'))

            champion = max(valid_iterations, key=get_sharpe)

            print(f"\n🏆 Current Champion:")
            print(f"  Iteration: {champion.get('iteration_num', 'N/A')}")
            print(f"  Sharpe Ratio: {champion['metrics']['sharpe_ratio']:.4f}")
            print(f"  CAGR: {champion['metrics']['annual_return']:.2%}")
            print(f"  Max DD: {champion['metrics']['max_drawdown']:.2%}")
            print(f"  Win Rate: {champion['metrics'].get('win_rate', 0):.2%}")

            # Recent iterations
            recent = valid_iterations[-5:] if len(valid_iterations) >= 5 else valid_iterations
            print(f"\n📈 Recent 5 Iterations:")
            for entry in recent:
                iter_num = entry.get('iteration_num', 'N/A')
                m = entry['metrics']
                sharpe = m['sharpe_ratio']
                cagr = m['annual_return']
                max_dd = m['max_drawdown']
                valid = entry.get('validation_passed', False)
                status = "✅" if valid else "❌"
                print(f"  {status} Iter {iter_num:2d}: Sharpe={sharpe:7.4f}, CAGR={cagr:7.2%}, MaxDD={max_dd:7.2%}")

            # Learning effectiveness - filter out None metrics first
            if len(valid_iterations) >= 3:
                # Only use iterations with valid sharpe ratios
                iterations_with_sharpe = [
                    h for h in valid_iterations
                    if h and isinstance(h, dict) and
                    h.get('metrics') and isinstance(h.get('metrics'), dict) and
                    h['metrics'].get('sharpe_ratio') is not None
                ]

                if len(iterations_with_sharpe) < 3:
                    print(f"\n⚠️  Insufficient valid sharpe ratios for learning analysis")
                else:
                    first_third = iterations_with_sharpe[:len(iterations_with_sharpe)//3]
                    last_third = iterations_with_sharpe[-len(iterations_with_sharpe)//3:]

                    avg_sharpe_early = sum(h['metrics']['sharpe_ratio'] for h in first_third) / len(first_third)
                    avg_sharpe_late = sum(h['metrics']['sharpe_ratio'] for h in last_third) / len(last_third)

                    improvement = avg_sharpe_late - avg_sharpe_early
                    improvement_pct = (improvement / abs(avg_sharpe_early)) * 100 if avg_sharpe_early != 0 else 0

                    print(f"\n🎯 Learning Effectiveness:")
                    print(f"  Early avg Sharpe: {avg_sharpe_early:.4f}")
                    print(f"  Recent avg Sharpe: {avg_sharpe_late:.4f}")
                    print(f"  Improvement: {improvement:+.4f} ({improvement_pct:+.1f}%)")

                    if improvement > 0:
                        print(f"  ✅ Learning cycle is working (positive improvement)")
                    else:
                        print(f"  ⚠️  No improvement detected (may need more iterations)")

            # Liquidity compliance check
            print(f"\n💧 Liquidity Compliance Check:")
            print(f"=" * 60)

            # Check all iterations for liquidity compliance
            for entry in valid_iterations:
                iter_num = entry.get('iteration_num', None)
                if iter_num is None:
                    continue

                # Try both possible file patterns
                strategy_files = [
                    f'generated_strategy_loop_iter{iter_num}.py',
                    f'generated_strategy_iter{iter_num}.py'
                ]

                strategy_file = None
                for sf in strategy_files:
                    if os.path.exists(sf):
                        strategy_file = sf
                        break

                if strategy_file:
                    result = check_liquidity_compliance(iter_num, strategy_file)
                    log_compliance_result(result)

                    # Print compliance status
                    threshold = result.get('threshold_found')
                    compliant = result.get('compliant', False)
                    status = "✅" if compliant else "❌"

                    if threshold is not None:
                        threshold_str = f"{threshold:,} TWD"
                    else:
                        threshold_str = "Not found"

                    print(f"  {status} Iter {iter_num:2d}: Threshold = {threshold_str}")

            # Print compliance statistics
            stats = get_compliance_statistics()
            if stats['total_checks'] > 0:
                print(f"\n📊 Compliance Summary:")
                print(f"  Total checks: {stats['total_checks']}")
                print(f"  Compliant: {stats['compliant_count']}")
                print(f"  Compliance rate: {stats['compliance_rate']:.1%}")

                if stats['average_threshold'] is not None:
                    print(f"  Average threshold: {stats['average_threshold']:,.0f} TWD")

                if stats['non_compliant_iterations']:
                    print(f"  Non-compliant iterations: {stats['non_compliant_iterations']}")

    except FileNotFoundError:
        print("❌ iteration_history.json not found")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

def analyze_failure_patterns():
    """Analyze learned failure patterns."""
    try:
        with open('failure_patterns.json', 'r') as f:
            patterns = json.load(f)

        print(f"\n🚫 Learned Failure Patterns:")
        print(f"=" * 60)
        print(f"Total patterns: {len(patterns)}")

        if patterns:
            # Group by parameter
            by_param = {}
            for p in patterns:
                param = p.get('parameter', 'unknown')
                if param not in by_param:
                    by_param[param] = []
                by_param[param].append(p)

            for param, param_patterns in by_param.items():
                print(f"\n  Parameter: {param}")
                print(f"  Patterns learned: {len(param_patterns)}")

                # Find worst pattern
                worst = min(param_patterns, key=lambda x: x.get('performance_impact', 0))
                print(f"    Worst: {worst['description']}")
                print(f"           Impact: {worst['performance_impact']:.4f}")
                print(f"           Iter: {worst['iteration_discovered']}")

    except FileNotFoundError:
        print("⚠️  failure_patterns.json not found")
    except Exception as e:
        print(f"❌ Error analyzing failure patterns: {e}")

if __name__ == "__main__":
    analyze_iteration_history()
    analyze_failure_patterns()
