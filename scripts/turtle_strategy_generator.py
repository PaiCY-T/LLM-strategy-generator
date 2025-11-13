"""
Parameterized 高殖利率烏龜 Strategy Generator
===========================================

Phase 1 Implementation: Systematic grid search testing of the successful
高殖利率烏龜 strategy with parameter variations.

Goal: Validate if the strategy's success is robust across parameter ranges
and identify optimal parameters for Sharpe >1.5 target.

Based on original strategy:
- 6-layer filtering: yield, technical, revenue, quality, insider, liquidity
- Monthly rebalancing with risk controls
- Achieved: Sharpe 2.09, 29.25% annual, MDD -15.41%
"""

import itertools
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from finlab import data, backtest

# ============================================================================
# Parameter Grid Definition
# ============================================================================

PARAM_GRID = {
    # Layer 1: Dividend Yield Filter (%)
    'yield_threshold': [4.0, 5.0, 6.0, 7.0, 8.0],

    # Layer 2: Technical Confirmation (MA periods)
    'ma_short': [10, 20, 30],
    'ma_long': [40, 60, 80],

    # Layer 3: Revenue Acceleration (periods)
    'rev_short': [3, 6],
    'rev_long': [12, 18],

    # Layer 4: Operating Margin Filter (%)
    'op_margin_threshold': [0, 3, 5],

    # Layer 5: Director Shareholding (%)
    'director_threshold': [5, 10, 15],

    # Layer 6: Liquidity (volume in thousands)
    'vol_min': [30, 50, 100],
    'vol_max': [5000, 10000, 15000],

    # Ranking & Selection
    'n_stocks': [5, 10, 15, 20],

    # Risk Controls
    'stop_loss': [0.06, 0.08, 0.10],
    'take_profit': [0.3, 0.5, 0.7],
    'position_limit': [0.10, 0.125, 0.15, 0.20],

    # Rebalancing
    'resample': ['M', 'W-FRI']
}

# Target Performance Criteria
TARGET_SHARPE = 1.5
TARGET_RETURN = 0.20
TARGET_MDD = -0.25

# Data Caching
_cached_data = {}

def get_cached_data(key: str):
    """Load and cache data to avoid repeated data.get() calls."""
    if key not in _cached_data:
        print(f"  Loading dataset: {key}...")
        _cached_data[key] = data.get(key)
    return _cached_data[key]


# ============================================================================
# Strategy Generator Function
# ============================================================================

def generate_turtle_strategy(params: Dict) -> Tuple[object, Dict]:
    """
    Generate parameterized 高殖利率烏龜 strategy.

    Returns:
        (report, metrics_dict) where metrics_dict contains:
        - annual_return, sharpe_ratio, max_drawdown
        - success (bool): whether meets all targets
    """

    # Load data (cached for performance)
    close = get_cached_data('price:收盤價')
    vol = get_cached_data('price:成交股數')
    rev = get_cached_data('monthly_revenue:當月營收')
    ope_earn = get_cached_data('fundamental_features:營業利益率')
    yield_ratio = get_cached_data('price_earning_ratio:殖利率(%)')
    boss_hold = get_cached_data('internal_equity_changes:董監持有股數占比')
    rev_growth_rate = get_cached_data('monthly_revenue:去年同月增減(%)')

    # Calculate technical indicators
    sma_short = close.average(params['ma_short'])
    sma_long = close.average(params['ma_long'])

    # Layer 1: Dividend Yield
    cond1 = yield_ratio >= params['yield_threshold']

    # Layer 2: Technical Confirmation
    cond2 = (close > sma_short) & (close > sma_long)

    # Layer 3: Revenue Acceleration
    cond3 = rev.average(params['rev_short']) > rev.average(params['rev_long'])

    # Layer 4: Operating Margin Quality
    cond4 = ope_earn >= params['op_margin_threshold']

    # Layer 5: Director Confidence
    cond5 = boss_hold >= params['director_threshold']

    # Layer 6: Liquidity
    cond6 = (
        (vol.average(5) >= params['vol_min'] * 1000) &
        (vol.average(5) <= params['vol_max'] * 1000)
    )

    # Combine all conditions
    cond_all = cond1 & cond2 & cond3 & cond4 & cond5 & cond6

    # Weight by revenue growth and select top N
    cond_all = cond_all * rev_growth_rate
    cond_all = cond_all[cond_all > 0].is_largest(params['n_stocks'])

    # Backtest
    strategy_name = f"Turtle_{params['yield_threshold']}y_{params['n_stocks']}n"

    report = backtest.sim(
        cond_all,
        resample=params['resample'],
        fee_ratio=1.425/1000/3,
        stop_loss=params['stop_loss'],
        take_profit=params['take_profit'],
        position_limit=params['position_limit'],
        name=strategy_name
    )

    # Extract metrics
    metrics = {
        'annual_return': report.metrics.annual_return(),
        'sharpe_ratio': report.metrics.sharpe_ratio(),
        'max_drawdown': report.metrics.max_drawdown(),
        'success': (
            report.metrics.sharpe_ratio() >= TARGET_SHARPE and
            report.metrics.annual_return() >= TARGET_RETURN and
            report.metrics.max_drawdown() >= TARGET_MDD
        )
    }

    return report, metrics


# ============================================================================
# Grid Search Execution
# ============================================================================

def create_param_combinations(strategy: str = 'full') -> List[Dict]:
    """
    Create parameter combinations for testing.

    Strategies:
    - 'full': Full grid search (500+ combinations)
    - 'focused': Focus on most promising ranges (30-50 combinations)
    - 'baseline': Test original parameters only
    """

    if strategy == 'baseline':
        # Original 高殖利率烏龜 parameters
        return [{
            'yield_threshold': 6.0,
            'ma_short': 20,
            'ma_long': 60,
            'rev_short': 3,
            'rev_long': 12,
            'op_margin_threshold': 3,
            'director_threshold': 10,
            'vol_min': 50,
            'vol_max': 10000,
            'n_stocks': 10,
            'stop_loss': 0.06,
            'take_profit': 0.5,
            'position_limit': 0.125,
            'resample': 'M'
        }]

    elif strategy == 'focused':
        # Focused grid: Test variations around successful parameters
        focused_grid = {
            'yield_threshold': [5.0, 6.0, 7.0],
            'ma_short': [20],
            'ma_long': [60],
            'rev_short': [3, 6],
            'rev_long': [12],
            'op_margin_threshold': [3, 5],
            'director_threshold': [10, 15],
            'vol_min': [50],
            'vol_max': [10000],
            'n_stocks': [5, 10, 15],
            'stop_loss': [0.06, 0.08],
            'take_profit': [0.5],
            'position_limit': [0.125, 0.15],
            'resample': ['M']
        }

        # Generate all combinations
        keys = focused_grid.keys()
        values = focused_grid.values()
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

        return combinations

    else:  # 'full'
        # Full grid search
        keys = PARAM_GRID.keys()
        values = PARAM_GRID.values()
        combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

        return combinations


def run_grid_search(
    strategy: str = 'focused',
    max_tests: int = 50,
    save_results: bool = True
) -> Dict:
    """
    Execute grid search with progress tracking.

    Args:
        strategy: 'baseline', 'focused', or 'full'
        max_tests: Maximum number of parameter combinations to test
        save_results: Whether to save results to JSON file

    Returns:
        results_dict with:
        - tested_combinations: number of tests run
        - success_count: number achieving targets
        - best_sharpe: best Sharpe result
        - best_return: best return result
        - all_results: list of all test results
    """

    print("=" * 80)
    print("高殖利率烏龜 Parameterized Grid Search")
    print("=" * 80)
    print(f"\nStrategy: {strategy}")
    print(f"Max Tests: {max_tests}")
    print(f"Targets: Sharpe ≥{TARGET_SHARPE}, Return ≥{TARGET_RETURN:.0%}, MDD ≥{TARGET_MDD:.0%}")
    print()

    # Generate parameter combinations
    param_combinations = create_param_combinations(strategy)
    total_combinations = len(param_combinations)

    print(f"Total Possible Combinations: {total_combinations}")

    if total_combinations > max_tests:
        print(f"⚠️ Limiting to first {max_tests} combinations")
        param_combinations = param_combinations[:max_tests]

    print(f"Testing {len(param_combinations)} combinations...\n")

    # Track results
    all_results = []
    success_count = 0
    best_sharpe = None
    best_return = None
    best_mdd = None

    # Pre-load all data
    print("🔄 Pre-loading data...")
    get_cached_data('price:收盤價')
    get_cached_data('price:成交股數')
    get_cached_data('monthly_revenue:當月營收')
    get_cached_data('fundamental_features:營業利益率')
    get_cached_data('price_earning_ratio:殖利率(%)')
    get_cached_data('internal_equity_changes:董監持有股數占比')
    get_cached_data('monthly_revenue:去年同月增減(%)')
    print("✅ Data cached\n")

    # Run tests
    for i, params in enumerate(param_combinations, 1):
        print(f"[{i}/{len(param_combinations)}] Testing: yield={params['yield_threshold']}%, n={params['n_stocks']}, stop={params['stop_loss']:.2f}")

        try:
            report, metrics = generate_turtle_strategy(params)

            # Track result
            result = {
                'test_id': i,
                'params': params,
                'metrics': metrics,
                'timestamp': datetime.now().isoformat()
            }
            all_results.append(result)

            # Display result
            print(f"  → Sharpe: {metrics['sharpe_ratio']:.2f} | Return: {metrics['annual_return']:.2%} | MDD: {metrics['max_drawdown']:.2%}")

            if metrics['success']:
                success_count += 1
                print(f"  ✅ SUCCESS! ({success_count} total successes)")

            # Track best results
            if best_sharpe is None or metrics['sharpe_ratio'] > best_sharpe['metrics']['sharpe_ratio']:
                best_sharpe = result

            if best_return is None or metrics['annual_return'] > best_return['metrics']['annual_return']:
                best_return = result

            if best_mdd is None or metrics['max_drawdown'] > best_mdd['metrics']['max_drawdown']:
                best_mdd = result

            print()

        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}\n")
            continue

    # Prepare summary
    results_summary = {
        'strategy': strategy,
        'tested_combinations': len(all_results),
        'success_count': success_count,
        'success_rate': success_count / len(all_results) if all_results else 0,
        'best_sharpe': best_sharpe,
        'best_return': best_return,
        'best_mdd': best_mdd,
        'all_results': all_results,
        'timestamp': datetime.now().isoformat()
    }

    # Save results
    if save_results:
        output_file = f"turtle_grid_search_{strategy}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_summary, f, indent=2, ensure_ascii=False)
        print(f"📁 Results saved: {output_file}\n")

    # Display summary
    print("=" * 80)
    print("GRID SEARCH SUMMARY")
    print("=" * 80)
    print(f"\n📊 Tests Completed: {len(all_results)}/{len(param_combinations)}")
    print(f"✅ Success Count: {success_count} ({results_summary['success_rate']:.1%})")
    print()

    if best_sharpe:
        print("🏆 Best Sharpe Ratio:")
        print(f"  Sharpe: {best_sharpe['metrics']['sharpe_ratio']:.2f}")
        print(f"  Return: {best_sharpe['metrics']['annual_return']:.2%}")
        print(f"  MDD: {best_sharpe['metrics']['max_drawdown']:.2%}")
        print(f"  Params: yield={best_sharpe['params']['yield_threshold']}%, "
              f"n={best_sharpe['params']['n_stocks']}, "
              f"stop={best_sharpe['params']['stop_loss']:.2f}")
        print()

    if best_return:
        print("💰 Best Annual Return:")
        print(f"  Return: {best_return['metrics']['annual_return']:.2%}")
        print(f"  Sharpe: {best_return['metrics']['sharpe_ratio']:.2f}")
        print(f"  MDD: {best_return['metrics']['max_drawdown']:.2%}")
        print(f"  Params: yield={best_return['params']['yield_threshold']}%, "
              f"n={best_return['params']['n_stocks']}, "
              f"stop={best_return['params']['stop_loss']:.2f}")
        print()

    if best_mdd:
        print("🛡️ Best Max Drawdown (Lowest):")
        print(f"  MDD: {best_mdd['metrics']['max_drawdown']:.2%}")
        print(f"  Sharpe: {best_mdd['metrics']['sharpe_ratio']:.2f}")
        print(f"  Return: {best_mdd['metrics']['annual_return']:.2%}")
        print(f"  Params: yield={best_mdd['params']['yield_threshold']}%, "
              f"n={best_mdd['params']['n_stocks']}, "
              f"stop={best_mdd['params']['stop_loss']:.2f}")

    print("=" * 80)

    return results_summary


# ============================================================================
# Main Execution
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Turtle Strategy Grid Search')
    parser.add_argument(
        '--strategy',
        choices=['baseline', 'focused', 'full'],
        default='focused',
        help='Grid search strategy (default: focused)'
    )
    parser.add_argument(
        '--max-tests',
        type=int,
        default=50,
        help='Maximum number of parameter combinations to test (default: 50)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save results to file'
    )

    args = parser.parse_args()

    # Run grid search
    results = run_grid_search(
        strategy=args.strategy,
        max_tests=args.max_tests,
        save_results=not args.no_save
    )

    # Display final recommendation
    print("\n📋 RECOMMENDATION:")
    if results['success_count'] > 0:
        success_rate = results['success_rate']
        if success_rate >= 0.3:
            print(f"✅ EXCELLENT: {success_rate:.1%} success rate proves strategy robustness!")
            print("   → Ready to proceed with Phase 2: Improve feedback mechanism")
        elif success_rate >= 0.1:
            print(f"⚠️ MODERATE: {success_rate:.1%} success rate shows potential")
            print("   → Consider expanding parameter search or adjusting targets")
        else:
            print(f"❌ LOW: {success_rate:.1%} success rate indicates sensitivity to parameters")
            print("   → Need to investigate why original strategy succeeded")
    else:
        print("❌ FAILURE: No combinations achieved targets")
        print("   → Verify original strategy still works with current data")
        print("   → Consider if market conditions have changed")
