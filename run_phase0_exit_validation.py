"""
Phase 0: Exit Strategy Hypothesis Validation

PHASE 0 VALIDATION TEST
======================
Task 0.1: Manual Exit Strategy Implementation ✅ COMPLETE
Task 0.2: Backtest Comparison (THIS SCRIPT)

**Objective**: Validate that sophisticated exit strategies improve Momentum template performance

**Success Criteria**: Sharpe improvement ≥0.3 vs baseline Momentum template

**Test Configuration**:
- Baseline: Momentum template (use_exits=False)
- Enhanced: MomentumExit template (use_exits=True)
- Parameters: Optimized Momentum parameters from Phase 1.5
- Backtest: Full historical data with real finlab backtest

**Decision Gate**:
- IF Sharpe improvement ≥0.3 → ✅ Proceed to Phase 1 (Exit Mutation MVP)
- IF Sharpe improvement <0.3 → ❌ Re-evaluate approach

**Requirements Traceability**:
- REQ-6: Exit Strategy Mutation (Phase 0 validation)
- User Insight: "止損、止盈的策略也都該加入演算法的範籌"
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.template_registry import TemplateRegistry


def test_baseline_momentum(params: Dict) -> Tuple[object, Dict]:
    """
    Test baseline Momentum template (no exit strategies).

    Args:
        params: Parameter dictionary with use_exits=False

    Returns:
        Tuple[object, Dict]: Backtest report and metrics
    """
    print("\n" + "="*80)
    print("BASELINE: Momentum Template (No Exit Strategies)")
    print("="*80)

    registry = TemplateRegistry.get_instance()
    momentum_template = registry.get_template('Momentum')

    # Remove exit-specific parameters for baseline (Momentum template doesn't have these)
    baseline_params = {k: v for k, v in params.items()
                      if k not in ['use_exits', 'atr_period', 'stop_atr_mult', 'profit_atr_mult', 'max_hold_days']}

    print(f"\nParameters: {baseline_params}")
    print("\nRunning backtest...")

    start_time = time.time()
    report, metrics = momentum_template.generate_strategy(baseline_params)
    elapsed = time.time() - start_time

    print(f"\n✅ Backtest completed in {elapsed:.1f}s")
    print(f"\nBaseline Metrics:")
    print(f"  Sharpe Ratio:   {metrics['sharpe_ratio']:.4f}")
    print(f"  Annual Return:  {metrics['annual_return']:.2%}")
    print(f"  Max Drawdown:   {metrics['max_drawdown']:.2%}")

    return report, metrics


def test_enhanced_momentum_with_exits(params: Dict) -> Tuple[object, Dict]:
    """
    Test enhanced Momentum template with exit strategies.

    Args:
        params: Parameter dictionary with use_exits=True

    Returns:
        Tuple[object, Dict]: Backtest report and metrics
    """
    print("\n" + "="*80)
    print("ENHANCED: Momentum + Exit Strategies")
    print("="*80)

    registry = TemplateRegistry.get_instance()
    momentum_exit_template = registry.get_template('MomentumExit')

    # Ensure exits are enabled
    enhanced_params = {**params, 'use_exits': True}

    print(f"\nParameters: {enhanced_params}")
    print("\nExit Strategies:")
    print(f"  1. ATR Trailing Stop-Loss: {enhanced_params.get('stop_atr_mult', 2.0)}× ATR")
    print(f"  2. Fixed Profit Target:    {enhanced_params.get('profit_atr_mult', 3.0)}× ATR")
    print(f"  3. Time-Based Exit:        {enhanced_params.get('max_hold_days', 30)} days max")
    print(f"  4. ATR Period:             {enhanced_params.get('atr_period', 14)} days")

    print("\nRunning backtest...")

    start_time = time.time()
    report, metrics = momentum_exit_template.generate_strategy(enhanced_params)
    elapsed = time.time() - start_time

    print(f"\n✅ Backtest completed in {elapsed:.1f}s")
    print(f"\nEnhanced Metrics:")
    print(f"  Sharpe Ratio:   {metrics['sharpe_ratio']:.4f}")
    print(f"  Annual Return:  {metrics['annual_return']:.2%}")
    print(f"  Max Drawdown:   {metrics['max_drawdown']:.2%}")

    return report, metrics


def analyze_comparison(baseline_metrics: Dict, enhanced_metrics: Dict) -> Dict:
    """
    Analyze performance comparison and validate success criteria.

    Args:
        baseline_metrics: Metrics from baseline Momentum template
        enhanced_metrics: Metrics from enhanced Momentum + Exit template

    Returns:
        Dict: Analysis results with decision gate verdict
    """
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON ANALYSIS")
    print("="*80)

    # Calculate improvements
    sharpe_improvement = enhanced_metrics['sharpe_ratio'] - baseline_metrics['sharpe_ratio']
    sharpe_pct_change = (sharpe_improvement / baseline_metrics['sharpe_ratio']) * 100 if baseline_metrics['sharpe_ratio'] != 0 else 0

    return_improvement = enhanced_metrics['annual_return'] - baseline_metrics['annual_return']
    return_pct_change = (return_improvement / baseline_metrics['annual_return']) * 100 if baseline_metrics['annual_return'] != 0 else 0

    mdd_improvement = enhanced_metrics['max_drawdown'] - baseline_metrics['max_drawdown']  # Negative is better (less drawdown)
    mdd_pct_change = (abs(mdd_improvement) / abs(baseline_metrics['max_drawdown'])) * 100 if baseline_metrics['max_drawdown'] != 0 else 0

    # Decision gate check
    success_criteria_met = sharpe_improvement >= 0.3

    print("\n📊 Absolute Changes:")
    print(f"  Sharpe Ratio:   {sharpe_improvement:+.4f}  ({sharpe_pct_change:+.1f}%)")
    print(f"  Annual Return:  {return_improvement:+.2%}  ({return_pct_change:+.1f}%)")
    print(f"  Max Drawdown:   {mdd_improvement:+.2%}  ({'improved' if mdd_improvement > 0 else 'worse'} by {mdd_pct_change:.1f}%)")

    print("\n🎯 Success Criteria Evaluation:")
    print(f"  Minimum Sharpe Improvement Required: 0.300")
    print(f"  Actual Sharpe Improvement:            {sharpe_improvement:.4f}")
    print(f"  Status: {'✅ CRITERIA MET' if success_criteria_met else '❌ CRITERIA NOT MET'}")

    print("\n📈 REQ-6 Expected Impact Validation:")
    print(f"  Expected Sharpe: +0.3 to +0.8 improvement (20-60% increase)")
    print(f"  Actual Sharpe:   {sharpe_improvement:+.4f} ({sharpe_pct_change:+.1f}%)")
    print(f"  Verdict: {'✅ Within expectations' if 0.3 <= sharpe_improvement <= 0.8 else '⚠️ Outside expectations'}")

    print("\n🚪 Decision Gate Verdict:")
    if success_criteria_met:
        print("  ✅ PROCEED TO PHASE 1 (Exit Strategy Mutation MVP)")
        print("  Hypothesis validated: Exit strategies significantly improve performance")
        print("  Next Steps: Implement ExitStrategyMutationOperator framework")
    else:
        print("  ❌ RE-EVALUATE APPROACH")
        print("  Hypothesis not validated: Exit strategies did not meet improvement threshold")
        print("  Next Steps: Analyze failure, adjust exit mechanisms, or reconsider structural mutation approach")

    return {
        'baseline_sharpe': baseline_metrics['sharpe_ratio'],
        'enhanced_sharpe': enhanced_metrics['sharpe_ratio'],
        'sharpe_improvement': sharpe_improvement,
        'sharpe_pct_change': sharpe_pct_change,
        'baseline_return': baseline_metrics['annual_return'],
        'enhanced_return': enhanced_metrics['annual_return'],
        'return_improvement': return_improvement,
        'return_pct_change': return_pct_change,
        'baseline_mdd': baseline_metrics['max_drawdown'],
        'enhanced_mdd': enhanced_metrics['max_drawdown'],
        'mdd_improvement': mdd_improvement,
        'mdd_pct_change': mdd_pct_change,
        'success_criteria_met': success_criteria_met,
        'decision_gate_verdict': 'PROCEED_TO_PHASE1' if success_criteria_met else 'RE_EVALUATE'
    }


def save_results(baseline_metrics: Dict, enhanced_metrics: Dict, analysis: Dict, output_file: str):
    """
    Save validation results to markdown file.

    Args:
        baseline_metrics: Baseline Momentum metrics
        enhanced_metrics: Enhanced Momentum + Exit metrics
        analysis: Comparison analysis results
        output_file: Output markdown file path
    """
    print(f"\n📄 Saving results to {output_file}...")

    with open(output_file, 'w') as f:
        f.write("# Phase 0: Exit Strategy Hypothesis Validation Results\n\n")
        f.write(f"**Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("**Test Configuration**:\n")
        f.write("- Baseline: Momentum template (no exit strategies)\n")
        f.write("- Enhanced: Momentum + Exit Strategies (ATR trailing, profit target, time exit)\n")
        f.write("- Success Criteria: Sharpe improvement ≥0.3\n\n")

        f.write("---\n\n")
        f.write("## Results Summary\n\n")

        f.write("### Baseline Momentum (No Exits)\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Sharpe Ratio | **{baseline_metrics['sharpe_ratio']:.4f}** |\n")
        f.write(f"| Annual Return | {baseline_metrics['annual_return']:.2%} |\n")
        f.write(f"| Max Drawdown | {baseline_metrics['max_drawdown']:.2%} |\n\n")

        f.write("### Enhanced Momentum + Exit Strategies\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| Sharpe Ratio | **{enhanced_metrics['sharpe_ratio']:.4f}** |\n")
        f.write(f"| Annual Return | {enhanced_metrics['annual_return']:.2%} |\n")
        f.write(f"| Max Drawdown | {enhanced_metrics['max_drawdown']:.2%} |\n\n")

        f.write("### Performance Improvement\n\n")
        f.write("| Metric | Absolute Change | Percentage Change |\n")
        f.write("|--------|----------------|-------------------|\n")
        f.write(f"| Sharpe Ratio | {analysis['sharpe_improvement']:+.4f} | {analysis['sharpe_pct_change']:+.1f}% |\n")
        f.write(f"| Annual Return | {analysis['return_improvement']:+.2%} | {analysis['return_pct_change']:+.1f}% |\n")
        f.write(f"| Max Drawdown | {analysis['mdd_improvement']:+.2%} | {analysis['mdd_pct_change']:+.1f}% |\n\n")

        f.write("---\n\n")
        f.write("## Decision Gate Evaluation\n\n")
        f.write(f"**Success Criteria**: Sharpe improvement ≥0.3\n\n")
        f.write(f"**Actual Sharpe Improvement**: {analysis['sharpe_improvement']:.4f}\n\n")
        f.write(f"**Status**: {'✅ **CRITERIA MET**' if analysis['success_criteria_met'] else '❌ **CRITERIA NOT MET**'}\n\n")

        f.write("### Verdict\n\n")
        if analysis['success_criteria_met']:
            f.write("✅ **PROCEED TO PHASE 1 (Exit Strategy Mutation MVP)**\n\n")
            f.write("**Rationale**:\n")
            f.write(f"- Exit strategies improved Sharpe ratio by {analysis['sharpe_improvement']:.4f} ({analysis['sharpe_pct_change']:+.1f}%)\n")
            f.write(f"- Improvement meets minimum threshold of 0.3\n")
            f.write(f"- Hypothesis validated: Sophisticated exits significantly improve performance\n\n")
            f.write("**Next Steps**:\n")
            f.write("1. Begin Phase 1: Implement ExitStrategyMutationOperator\n")
            f.write("2. Build AST-based exit logic mutation framework\n")
            f.write("3. Run 20-generation smoke test validation\n")
            f.write("4. Target: Sharpe >2.0 for full Phase 2 approval\n")
        else:
            f.write("❌ **RE-EVALUATE APPROACH**\n\n")
            f.write("**Rationale**:\n")
            f.write(f"- Exit strategies improved Sharpe ratio by only {analysis['sharpe_improvement']:.4f} ({analysis['sharpe_pct_change']:+.1f}%)\n")
            f.write(f"- Improvement falls short of minimum threshold (0.3)\n")
            f.write(f"- Hypothesis not validated: Exit strategies insufficient for breakthrough\n\n")
            f.write("**Next Steps**:\n")
            f.write("1. Analyze failure mode: Why did exits not improve performance?\n")
            f.write("2. Consider alternative exit mechanisms or parameter tuning\n")
            f.write("3. Re-evaluate structural mutation approach (explore other mutation operators)\n")
            f.write("4. Potentially proceed to Phase 3 fallback (ensemble methods)\n")

        f.write("\n---\n\n")
        f.write("## Detailed Analysis\n\n")
        f.write("### REQ-6 Expected Impact Validation\n\n")
        f.write("**Conservative Estimates** (from requirements.md):\n")
        f.write("- Sharpe Ratio: +0.3 to +0.8 improvement (20-60% increase)\n")
        f.write("- Max Drawdown: -15% to -40% reduction\n")
        f.write("- Win Rate: +5% to +15% increase\n\n")

        f.write("**Actual Results**:\n")
        f.write(f"- Sharpe Ratio: {analysis['sharpe_improvement']:+.4f} ({analysis['sharpe_pct_change']:+.1f}%) ")
        f.write("✅ Within expectations\n" if 0.3 <= analysis['sharpe_improvement'] <= 0.8 else "⚠️ Outside expectations\n")
        f.write(f"- Max Drawdown: {analysis['mdd_improvement']:+.2%} ({analysis['mdd_pct_change']:+.1f}%) ")
        f.write("✅ Within expectations\n" if 15 <= analysis['mdd_pct_change'] <= 40 else "⚠️ Outside expectations\n")

        f.write("\n### Exit Mechanism Performance\n\n")
        f.write("**Implemented Exit Strategies**:\n")
        f.write("1. **ATR Trailing Stop-Loss**: 2× ATR below highest high since entry\n")
        f.write("   - Risk management through volatility-adjusted stops\n")
        f.write("   - Cuts losing trades at ~10% typical loss on 5% ATR\n\n")

        f.write("2. **Fixed Profit Target**: 3× ATR above entry price\n")
        f.write("   - Systematic profit capture using risk-adjusted targets\n")
        f.write("   - Captures +15% typical profit on 5% ATR (3:1 risk:reward)\n\n")

        f.write("3. **Time-Based Exit**: Maximum 30 trading days\n")
        f.write("   - Prevents stale positions and capital lock-up\n")
        f.write("   - Forces reallocation of capital to fresh opportunities\n\n")

        f.write("---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**Generated by**: Phase 0 Exit Strategy Validation Test (`run_phase0_exit_validation.py`)\n")

    print(f"✅ Results saved to {output_file}")


def main():
    """
    Run Phase 0 exit strategy validation test.

    Compares baseline Momentum vs. Momentum + Exit Strategies to validate
    whether sophisticated exits improve performance sufficiently to proceed
    with Phase 1 mutation framework implementation.
    """
    print("="*80)
    print("PHASE 0: EXIT STRATEGY HYPOTHESIS VALIDATION")
    print("="*80)
    print("\nTask 0.2: Backtest Comparison (Baseline vs. Enhanced)")
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Optimized Momentum parameters (from Phase 1.5 validation)
    # These parameters were found to perform well in CombinationTemplate
    test_params = {
        'momentum_period': 20,  # Medium-term momentum (1 month)
        'ma_periods': 60,  # Medium-term trend (3 months)
        'catalyst_type': 'revenue',  # Revenue acceleration catalyst
        'catalyst_lookback': 3,  # 3-month catalyst detection
        'n_stocks': 10,  # Concentrated portfolio
        'stop_loss': 0.10,  # 10% stop-loss (will be overridden by exit strategies)
        'resample': 'M',  # Monthly rebalancing
        'resample_offset': 0,  # 1st of month rebalancing
        # Exit strategy parameters (for enhanced template)
        'use_exits': True,  # Will toggle for baseline
        'atr_period': 14,  # Standard ATR period
        'stop_atr_mult': 2.0,  # 2× ATR trailing stop
        'profit_atr_mult': 3.0,  # 3× ATR profit target (1.5:1 risk:reward)
        'max_hold_days': 30  # 30-day maximum hold
    }

    print("Test Configuration:")
    print(f"  Momentum Period:     {test_params['momentum_period']} days")
    print(f"  MA Period:           {test_params['ma_periods']} days")
    print(f"  Catalyst Type:       {test_params['catalyst_type']}")
    print(f"  Catalyst Lookback:   {test_params['catalyst_lookback']} months")
    print(f"  Portfolio Size:      {test_params['n_stocks']} stocks")
    print(f"  Rebalancing:         {test_params['resample']} (Monthly)")

    # Test 1: Baseline Momentum (no exits)
    baseline_report, baseline_metrics = test_baseline_momentum(test_params)

    # Test 2: Enhanced Momentum + Exit Strategies
    enhanced_report, enhanced_metrics = test_enhanced_momentum_with_exits(test_params)

    # Analyze comparison
    analysis = analyze_comparison(baseline_metrics, enhanced_metrics)

    # Save results
    output_file = "PHASE0_EXIT_VALIDATION_RESULTS.md"
    save_results(baseline_metrics, enhanced_metrics, analysis, output_file)

    # Final summary
    print("\n" + "="*80)
    print("VALIDATION TEST COMPLETE")
    print("="*80)
    print(f"\n📊 Results Summary:")
    print(f"  Baseline Sharpe:     {baseline_metrics['sharpe_ratio']:.4f}")
    print(f"  Enhanced Sharpe:     {enhanced_metrics['sharpe_ratio']:.4f}")
    print(f"  Improvement:         {analysis['sharpe_improvement']:+.4f} ({analysis['sharpe_pct_change']:+.1f}%)")
    print(f"\n🎯 Decision Gate:      {analysis['decision_gate_verdict']}")
    print(f"  Success Criteria:    {'✅ MET' if analysis['success_criteria_met'] else '❌ NOT MET'}")
    print(f"\n📄 Full report saved: {output_file}")

    return analysis


if __name__ == "__main__":
    try:
        analysis = main()
        sys.exit(0 if analysis['success_criteria_met'] else 1)
    except Exception as e:
        print(f"\n❌ Validation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
