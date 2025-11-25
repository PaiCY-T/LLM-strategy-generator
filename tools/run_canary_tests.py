#!/usr/bin/env python3
"""
Tier2 Canary Test Runner for Phase 1.1
======================================

Runs 3 test cases × 3 runs = 9 tests to validate Golden Template effectiveness
before running full 20-iteration test.

Test Cases:
- Simple: 5-20 MA crossover (>80% expected)
- Medium: ROE+Revenue+Momentum (>60% expected)
- Complex: Sector rotation (>40% expected)

Overall Threshold: >60% success rate
"""

import sys
import os
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.innovation.prompt_builder import PromptBuilder
from src.innovation.llm_client import LLMClient, LLMConfig
from src.backtest.executor import BacktestExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_canary_config() -> Dict:
    """Load canary test cases from YAML."""
    config_file = Path(__file__).parent / 'canary_test_cases.yaml'
    with open(config_file) as f:
        return yaml.safe_load(f)


def run_single_canary_test(
    case_name: str,
    case_config: Dict,
    run_number: int,
    output_dir: Path
) -> Dict:
    """
    Run a single canary test.

    Args:
        case_name: Test case name (simple/medium/complex)
        case_config: Test case configuration
        run_number: Run number (1-3)
        output_dir: Output directory for results

    Returns:
        Result dictionary with success status and metrics
    """
    logger.info(f"Running {case_name} - Run {run_number}/3")

    # Load finlab data and sim
    try:
        from finlab import data
        from finlab.backtest import sim
    except ImportError as e:
        logger.error(f"Failed to import finlab: {e}")
        return {
            'case': case_name,
            'run': run_number,
            'success': False,
            'error': 'FinlabImportError',
            'code_length': 0
        }

    # Initialize components
    prompt_builder = PromptBuilder()

    # Get API key from environment
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        return {
            'case': case_name,
            'run': run_number,
            'success': False,
            'error': 'MissingAPIKey',
            'code_length': 0
        }

    llm_config = LLMConfig(
        provider='openrouter',
        model='google/gemini-2.5-flash',
        api_key=api_key,
        temperature=0.7,
        max_tokens=8000
    )
    llm_client = LLMClient(llm_config)

    backtest_executor = BacktestExecutor(timeout=420)

    # Backtest parameters
    start_date = "2018-01-01"
    end_date = "2024-12-31"
    fee_ratio = 0.001425
    tax_ratio = 0.003

    # Generate strategy
    try:
        champion_approach = case_config['champion_approach']
        innovation_directive = case_config['innovation_directive']

        prompt = prompt_builder.build_creation_prompt(
            champion_approach=champion_approach,
            innovation_directive=innovation_directive
        )

        logger.info(f"Generating strategy (prompt size: {len(prompt)} chars)")
        strategy_code = llm_client.generate(prompt)

        if not strategy_code or strategy_code.strip() == '':
            logger.error("Empty strategy code")
            return {
                'case': case_name,
                'run': run_number,
                'success': False,
                'error': 'EmptyResponse',
                'code_length': 0
            }

        # Execute backtest
        logger.info("Executing backtest...")
        execution_result = backtest_executor.execute(
            strategy_code=strategy_code,
            data=data,
            sim=sim,
            start_date=start_date,
            end_date=end_date,
            fee_ratio=fee_ratio,
            tax_ratio=tax_ratio
        )

        # Extract metrics - ExecutionResult has direct attributes, not metrics dict
        success = execution_result.success
        sharpe_ratio = execution_result.sharpe_ratio if success else None
        error_type = execution_result.error_type if not success else None

        # Save result
        output_file = output_dir / f"{case_name}_run{run_number}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'case': case_name,
                'run': run_number,
                'complexity': case_config['complexity'],
                'strategy_code': strategy_code,
                'execution_result': {
                    'success': success,
                    'sharpe_ratio': sharpe_ratio,
                    'error_type': error_type,
                    'error_message': execution_result.error_message if not success else None,
                    'metrics': {
                        'sharpe_ratio': execution_result.sharpe_ratio,
                        'total_return': execution_result.total_return,
                        'max_drawdown': execution_result.max_drawdown
                    } if success else {}
                },
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)

        return {
            'case': case_name,
            'run': run_number,
            'success': success,
            'sharpe_ratio': sharpe_ratio,
            'error': error_type,
            'code_length': len(strategy_code)
        }

    except Exception as e:
        logger.error(f"Error in canary test: {e}", exc_info=True)
        return {
            'case': case_name,
            'run': run_number,
            'success': False,
            'error': str(e),
            'code_length': 0
        }


def run_all_canary_tests() -> Tuple[List[Dict], float]:
    """
    Run all canary tests.

    Returns:
        (results, pass_rate): Test results and overall pass rate
    """
    # Load config
    config = load_canary_config()
    cases = config['canary_tests']
    test_config = config['test_config']

    # Setup output directory
    output_dir = Path('experiments/llm_learning_validation/results/canary_tier2')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run tests
    results = []
    for case_name, case_config in cases.items():
        for run_num in range(1, test_config['runs_per_case'] + 1):
            result = run_single_canary_test(
                case_name,
                case_config,
                run_num,
                output_dir
            )
            results.append(result)

    # Calculate pass rate
    successful = sum(1 for r in results if r['success'])
    pass_rate = successful / len(results) if results else 0.0

    return results, pass_rate


def print_canary_report(results: List[Dict], pass_rate: float):
    """Print canary test report."""
    print("="*80)
    print("TIER2 CANARY TEST REPORT")
    print("="*80)

    # Overall summary
    total = len(results)
    successful = sum(1 for r in results if r['success'])

    print(f"\nTotal Tests: {total}")
    print(f"Successful: {successful}/{total} ({pass_rate:.1%})")
    print(f"Threshold: >60%")

    if pass_rate >= 0.6:
        print(f"✅ TIER2 PASSED - Ready for Full Test (20 iterations)")
    else:
        print(f"❌ TIER2 FAILED - Need CoT/APPENDIX adjustment")

    # Breakdown by case
    print(f"\n{'='*80}")
    print("BREAKDOWN BY CASE")
    print("="*80)

    for case_name in ['simple', 'medium', 'complex']:
        case_results = [r for r in results if r['case'] == case_name]
        if not case_results:
            continue

        case_success = sum(1 for r in case_results if r['success'])
        case_total = len(case_results)
        case_rate = case_success / case_total if case_total > 0 else 0

        print(f"\n{case_name.upper()} ({case_success}/{case_total} = {case_rate:.1%})")
        for i, result in enumerate(case_results, 1):
            status = "✅" if result['success'] else f"❌ ({result['error']})"
            sharpe = result.get('sharpe_ratio')
            sharpe_str = f"Sharpe: {sharpe:.4f}" if sharpe is not None else "No Sharpe"
            print(f"  Run {i}: {status:30s} {sharpe_str}")

    # Error analysis
    print(f"\n{'='*80}")
    print("ERROR ANALYSIS")
    print("="*80)

    errors = {}
    for r in results:
        if not r['success']:
            error = r.get('error', 'Unknown')
            errors[error] = errors.get(error, 0) + 1

    if errors:
        for error, count in sorted(errors.items(), key=lambda x: -x[1]):
            print(f"{error:30s}: {count}/{total} ({count/total:.1%})")
    else:
        print("No errors - all tests passed!")


def main():
    """Main entry point."""
    logger.info("Starting Tier2 Canary Tests...")

    # Run tests
    results, pass_rate = run_all_canary_tests()

    # Print report
    print_canary_report(results, pass_rate)

    # Save summary
    summary_file = Path('experiments/llm_learning_validation/results/canary_tier2/summary.json')
    with open(summary_file, 'w') as f:
        json.dump({
            'total_tests': len(results),
            'successful': sum(1 for r in results if r['success']),
            'pass_rate': pass_rate,
            'threshold': 0.6,
            'passed_tier2': pass_rate >= 0.6,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)

    logger.info(f"Results saved to {summary_file}")

    # Exit code
    return 0 if pass_rate >= 0.6 else 1


if __name__ == '__main__':
    sys.exit(main())
