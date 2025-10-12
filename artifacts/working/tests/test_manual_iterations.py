#!/usr/bin/env python3
"""Manual Test Script for Autonomous Iteration Engine - Task A4

Tests 5 complete iteration cycles to validate:
1. Claude API code generation
2. AST validation
3. Sandbox execution
4. Metrics extraction
5. Overall success rate >70%

This is the GO/NO-GO decision point for the project.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import our components
from claude_api_client import generate_strategy_with_claude
from ast_validator import validate_strategy_code
from sandbox_executor import execute_strategy_in_sandbox
from metrics_extractor import extract_metrics_from_signal


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ManualTestRunner:
    """Runs manual test iterations for system validation."""

    def __init__(self, num_iterations: int = 5):
        """Initialize test runner.

        Args:
            num_iterations: Number of test iterations to run (default: 5)
        """
        self.num_iterations = num_iterations
        self.results: List[Dict[str, Any]] = []

    def run_iteration(
        self,
        iteration_num: int,
        feedback: str = ""
    ) -> Dict[str, Any]:
        """Run a single test iteration.

        Args:
            iteration_num: Current iteration number (0-indexed)
            feedback: Feedback from previous iteration

        Returns:
            Dictionary with iteration results
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"ITERATION {iteration_num}")
        logger.info(f"{'='*70}")

        result = {
            'iteration': iteration_num,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'stages': {
                'generation': False,
                'validation': False,
                'execution': False,
                'metrics': False
            },
            'errors': [],
            'metrics': None,
            'code_length': 0
        }

        try:
            # Stage 1: Generate strategy code
            logger.info("\n[1/4] Generating strategy code...")
            try:
                code = generate_strategy_with_claude(
                    iteration=iteration_num,
                    feedback=feedback
                )
                result['code'] = code
                result['code_length'] = len(code)
                result['stages']['generation'] = True
                logger.info(f"✅ Generated {len(code)} chars of code")
            except Exception as e:
                error_msg = f"Generation failed: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
                return result

            # Stage 2: Validate with AST
            logger.info("\n[2/4] Validating code with AST...")
            try:
                is_valid, errors = validate_strategy_code(code)
                result['validation_errors'] = errors

                if is_valid:
                    result['stages']['validation'] = True
                    logger.info("✅ Code passed AST validation")
                else:
                    error_msg = f"Validation failed: {'; '.join(errors)}"
                    result['errors'].append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    return result

            except Exception as e:
                error_msg = f"Validation error: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
                return result

            # Stage 3: Execute in sandbox
            logger.info("\n[3/4] Executing in sandbox...")
            try:
                exec_result = execute_strategy_in_sandbox(code)

                if exec_result['success']:
                    result['signal'] = exec_result['signal']
                    result['stages']['execution'] = True
                    logger.info(f"✅ Execution successful (signal shape: {exec_result['signal'].shape})")
                else:
                    error_msg = f"Execution failed: {exec_result.get('error', 'Unknown error')}"
                    result['errors'].append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    return result

            except Exception as e:
                error_msg = f"Execution error: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
                return result

            # Stage 4: Extract metrics
            logger.info("\n[4/4] Extracting metrics...")
            try:
                metrics = extract_metrics_from_signal(
                    exec_result['signal'],
                    code=code
                )

                result['metrics'] = metrics
                result['stages']['metrics'] = True

                logger.info(f"✅ Metrics extracted:")
                logger.info(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
                logger.info(f"   Total Return: {metrics['total_return']*100:.2f}%")
                logger.info(f"   Max Drawdown: {metrics['max_drawdown']*100:.2f}%")

            except Exception as e:
                error_msg = f"Metrics extraction error: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
                return result

            # All stages successful
            result['success'] = True
            logger.info("\n✅ ITERATION SUCCESSFUL - All 4 stages passed")

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            result['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")

        return result

    def run_all_iterations(self) -> Dict[str, Any]:
        """Run all test iterations.

        Returns:
            Summary results dictionary
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"STARTING MANUAL TEST - {self.num_iterations} ITERATIONS")
        logger.info(f"{'='*70}\n")

        # Check environment
        self._check_environment()

        feedback = ""

        for i in range(self.num_iterations):
            result = self.run_iteration(i, feedback)
            self.results.append(result)

            # Save intermediate results
            self._save_results()

            # Save generated code
            if result.get('code'):
                code_path = Path(f"manual_test_iter{i}.py")
                code_path.write_text(result['code'], encoding='utf-8')
                logger.info(f"Saved code to {code_path}")

            # Prepare feedback for next iteration
            if result['success'] and result.get('metrics'):
                metrics = result['metrics']
                feedback = f"""
Previous iteration {i} results:
- Sharpe Ratio: {metrics['sharpe_ratio']:.3f}
- Total Return: {metrics['total_return']*100:.2f}%
- Max Drawdown: {metrics['max_drawdown']*100:.2f}%

Try to improve the Sharpe ratio and reduce drawdown.
"""
            elif result.get('errors'):
                feedback = f"""
Previous iteration {i} had errors:
{chr(10).join(result['errors'])}

Please fix these issues.
"""

        # Generate summary
        summary = self._generate_summary()

        # Save final report
        self._save_report(summary)

        return summary

    def _check_environment(self):
        """Check that required environment variables are set."""
        logger.info("Checking environment...")

        api_key = os.getenv("OPENROUTER_API_KEY")
        finlab_token = os.getenv("FINLAB_API_TOKEN")

        if not api_key:
            raise EnvironmentError(
                "OPENROUTER_API_KEY not set. "
                "Set with: export OPENROUTER_API_KEY='your-key-here'"
            )

        if not finlab_token:
            raise EnvironmentError(
                "FINLAB_API_TOKEN not set. "
                "Set with: export FINLAB_API_TOKEN='your-token-here'"
            )

        logger.info(f"✅ OPENROUTER_API_KEY: {api_key[:10]}...{api_key[-10:]}")
        logger.info(f"✅ FINLAB_API_TOKEN: {finlab_token[:10]}...{finlab_token[-10:]}")

    def _save_results(self):
        """Save intermediate results to JSON."""
        results_path = Path("manual_test_results.json")
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, default=str)

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics.

        Returns:
            Summary dictionary
        """
        total = len(self.results)
        successful = sum(1 for r in self.results if r['success'])
        success_rate = successful / total if total > 0 else 0

        # Stage-wise success
        stage_success = {
            'generation': sum(1 for r in self.results if r['stages']['generation']),
            'validation': sum(1 for r in self.results if r['stages']['validation']),
            'execution': sum(1 for r in self.results if r['stages']['execution']),
            'metrics': sum(1 for r in self.results if r['stages']['metrics'])
        }

        # Collect all errors
        all_errors = []
        for r in self.results:
            all_errors.extend(r.get('errors', []))

        # Metrics statistics (for successful iterations)
        metrics_stats = None
        successful_metrics = [r['metrics'] for r in self.results if r.get('metrics')]

        if successful_metrics:
            sharpe_ratios = [m['sharpe_ratio'] for m in successful_metrics]
            returns = [m['total_return'] * 100 for m in successful_metrics]
            drawdowns = [m['max_drawdown'] * 100 for m in successful_metrics]

            metrics_stats = {
                'sharpe': {
                    'min': min(sharpe_ratios),
                    'max': max(sharpe_ratios),
                    'avg': sum(sharpe_ratios) / len(sharpe_ratios)
                },
                'return': {
                    'min': min(returns),
                    'max': max(returns),
                    'avg': sum(returns) / len(returns)
                },
                'drawdown': {
                    'min': min(drawdowns),
                    'max': max(drawdowns),
                    'avg': sum(drawdowns) / len(drawdowns)
                }
            }

        # GO/NO-GO decision
        go_no_go = "GO" if success_rate >= 0.70 else "NO-GO"

        summary = {
            'total_iterations': total,
            'successful': successful,
            'success_rate': success_rate,
            'stage_success': stage_success,
            'errors': all_errors,
            'metrics_stats': metrics_stats,
            'go_no_go': go_no_go,
            'recommendation': self._get_recommendation(success_rate, stage_success)
        }

        return summary

    def _get_recommendation(
        self,
        success_rate: float,
        stage_success: Dict[str, int]
    ) -> str:
        """Generate recommendation based on results.

        Args:
            success_rate: Overall success rate
            stage_success: Success count by stage

        Returns:
            Recommendation text
        """
        if success_rate >= 0.70:
            return (
                f"✅ SUCCESS RATE {success_rate*100:.0f}% - PROCEED TO A5 (PROMPT REFINEMENT)\n"
                f"The system demonstrates acceptable reliability. "
                f"Focus next on improving prompt engineering to increase execution success rate."
            )
        else:
            # Identify bottleneck stage
            total = self.num_iterations
            bottleneck = min(stage_success.items(), key=lambda x: x[1])

            return (
                f"❌ SUCCESS RATE {success_rate*100:.0f}% - STOP AND REASSESS\n"
                f"The system does not meet the 70% success threshold.\n"
                f"Bottleneck: {bottleneck[0]} ({bottleneck[1]}/{total} = {bottleneck[1]/total*100:.0f}%)\n"
                f"Recommendation: Fix {bottleneck[0]} stage before proceeding."
            )

    def _save_report(self, summary: Dict[str, Any]):
        """Save final report to markdown file.

        Args:
            summary: Summary results dictionary
        """
        report_path = Path("MANUAL_TEST_RESULTS.md")

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Manual Test Results - Task A4\n\n")
            f.write(f"**Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Iterations**: {summary['total_iterations']}\n")
            f.write(f"- **Successful**: {summary['successful']}/{summary['total_iterations']}\n")
            f.write(f"- **Success Rate**: {summary['success_rate']*100:.1f}%\n")
            f.write(f"- **Decision**: **{summary['go_no_go']}**\n\n")

            # Stage-wise success
            f.write("## Stage-wise Success Rates\n\n")
            for stage, count in summary['stage_success'].items():
                rate = count / summary['total_iterations'] * 100
                f.write(f"- **{stage.capitalize()}**: {count}/{summary['total_iterations']} ({rate:.1f}%)\n")
            f.write("\n")

            # Metrics statistics
            if summary['metrics_stats']:
                f.write("## Metrics Statistics\n\n")
                stats = summary['metrics_stats']

                f.write("### Sharpe Ratio\n")
                f.write(f"- Min: {stats['sharpe']['min']:.3f}\n")
                f.write(f"- Max: {stats['sharpe']['max']:.3f}\n")
                f.write(f"- Avg: {stats['sharpe']['avg']:.3f}\n\n")

                f.write("### Total Return\n")
                f.write(f"- Min: {stats['return']['min']:.1f}%\n")
                f.write(f"- Max: {stats['return']['max']:.1f}%\n")
                f.write(f"- Avg: {stats['return']['avg']:.1f}%\n\n")

                f.write("### Max Drawdown\n")
                f.write(f"- Min: {stats['drawdown']['min']:.1f}%\n")
                f.write(f"- Max: {stats['drawdown']['max']:.1f}%\n")
                f.write(f"- Avg: {stats['drawdown']['avg']:.1f}%\n\n")

            # Error patterns
            if summary['errors']:
                f.write("## Common Failure Patterns\n\n")
                error_counts = {}
                for error in summary['errors']:
                    # Categorize errors
                    if 'Generation' in error:
                        category = 'API/Generation'
                    elif 'Validation' in error:
                        category = 'AST Validation'
                    elif 'Execution' in error:
                        category = 'Sandbox Execution'
                    elif 'Metrics' in error:
                        category = 'Metrics Extraction'
                    else:
                        category = 'Other'

                    error_counts[category] = error_counts.get(category, 0) + 1

                for category, count in sorted(error_counts.items(), key=lambda x: -x[1]):
                    f.write(f"- **{category}**: {count} occurrences\n")
                f.write("\n")

            # Individual iteration results
            f.write("## Iteration Details\n\n")
            for result in self.results:
                f.write(f"### Iteration {result['iteration']}\n\n")
                f.write(f"- **Status**: {'✅ Success' if result['success'] else '❌ Failed'}\n")
                f.write(f"- **Code Length**: {result['code_length']} chars\n")

                if result.get('metrics'):
                    m = result['metrics']
                    f.write(f"- **Sharpe Ratio**: {m['sharpe_ratio']:.3f}\n")
                    f.write(f"- **Total Return**: {m['total_return']*100:.2f}%\n")
                    f.write(f"- **Max Drawdown**: {m['max_drawdown']*100:.2f}%\n")

                if result.get('errors'):
                    f.write(f"- **Errors**:\n")
                    for error in result['errors']:
                        f.write(f"  - {error}\n")

                f.write("\n")

            # Recommendation
            f.write("## Recommendation\n\n")
            f.write(f"{summary['recommendation']}\n\n")

            # Next steps
            f.write("## Next Steps\n\n")
            if summary['go_no_go'] == "GO":
                f.write("1. Proceed to Task A5: Prompt refinement\n")
                f.write("2. Focus on improving execution success rate\n")
                f.write("3. Iterate on prompt engineering based on error patterns\n")
            else:
                f.write("1. Analyze and fix the bottleneck stage\n")
                f.write("2. Re-run manual test to validate fixes\n")
                f.write("3. Only proceed to A5 after achieving ≥70% success rate\n")

        logger.info(f"\n✅ Report saved to {report_path}")


def main():
    """Main entry point."""
    print("="*70)
    print("AUTONOMOUS ITERATION ENGINE - MANUAL TEST (TASK A4)")
    print("="*70)
    print()
    print("This test validates the core system with 5 manual iterations.")
    print("Success criteria: ≥70% success rate (4/5 iterations)")
    print()

    # Create and run test
    runner = ManualTestRunner(num_iterations=5)

    try:
        summary = runner.run_all_iterations()

        # Print summary
        print("\n" + "="*70)
        print("TEST COMPLETE - SUMMARY")
        print("="*70)
        print(f"\nSuccess Rate: {summary['success_rate']*100:.1f}% ({summary['successful']}/{summary['total_iterations']})")
        print(f"\nDecision: {summary['go_no_go']}")
        print(f"\n{summary['recommendation']}")
        print("\nSee MANUAL_TEST_RESULTS.md for detailed report.")
        print()

    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0 if summary['go_no_go'] == "GO" else 1


if __name__ == '__main__':
    exit(main())
