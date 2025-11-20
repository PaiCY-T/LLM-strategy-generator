#!/usr/bin/env python3
"""
Tier1 Structural Validation Tool for Phase 1.1
==============================================

快速檢查LLM生成的策略程式碼結構，無需執行回測。

檢查項目:
1. has_strategy_def: 包含 def strategy()
2. has_report_assignment: 包含 report = sim()
3. has_return_statement: 包含 return position
4. compiles_successfully: Python編譯成功
5. no_lookahead_bias: 無前視偏差 (.shift(-))

閾值: >90% 合格率 (10次生成)
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class ValidationResult:
    """單次驗證結果"""
    has_strategy_def: bool
    has_report_assignment: bool
    has_return_statement: bool
    compiles_successfully: bool
    no_lookahead_bias: bool

    @property
    def score(self) -> float:
        """計算合格分數 (0.0-1.0)"""
        checks = [
            self.has_strategy_def,
            self.has_report_assignment,
            self.has_return_statement,
            self.compiles_successfully,
            self.no_lookahead_bias
        ]
        return sum(checks) / len(checks)

    @property
    def passed(self) -> bool:
        """是否全部通過"""
        return self.score == 1.0

    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            'has_strategy_def': self.has_strategy_def,
            'has_report_assignment': self.has_report_assignment,
            'has_return_statement': self.has_return_statement,
            'compiles_successfully': self.compiles_successfully,
            'no_lookahead_bias': self.no_lookahead_bias,
            'score': self.score,
            'passed': self.passed
        }


def validate_code_structure(code: str) -> ValidationResult:
    """
    驗證程式碼結構。

    Args:
        code: 策略程式碼字串

    Returns:
        ValidationResult: 驗證結果
    """
    # Check 1: Has strategy definition
    has_strategy_def = 'def strategy(' in code

    # Check 2: Has report assignment
    has_report_assignment = 'report = sim(' in code

    # Check 3: Has return statement
    has_return_statement = 'return position' in code

    # Check 4: Compiles successfully
    compiles_successfully = False
    try:
        compile(code, '<string>', 'exec')
        compiles_successfully = True
    except SyntaxError:
        pass

    # Check 5: No lookahead bias
    no_lookahead_bias = '.shift(-' not in code

    return ValidationResult(
        has_strategy_def=has_strategy_def,
        has_report_assignment=has_report_assignment,
        has_return_statement=has_return_statement,
        compiles_successfully=compiles_successfully,
        no_lookahead_bias=no_lookahead_bias
    )


def validate_from_file(file_path: Path) -> Tuple[List[ValidationResult], float]:
    """
    從innovations.jsonl檔案驗證所有生成的策略。

    Args:
        file_path: innovations.jsonl路徑

    Returns:
        (results, pass_rate): 驗證結果列表和通過率
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    results = []
    with open(file_path) as f:
        for line in f:
            data = json.loads(line)

            # Skip if not LLM generated
            if data.get('generation_method') != 'llm':
                continue

            # Get strategy code
            code = data.get('strategy_code', '')
            if not code:
                # Empty code - all checks fail
                results.append(ValidationResult(
                    has_strategy_def=False,
                    has_report_assignment=False,
                    has_return_statement=False,
                    compiles_successfully=False,
                    no_lookahead_bias=True  # Technically no lookahead in empty code
                ))
                continue

            # Validate structure
            result = validate_code_structure(code)
            results.append(result)

    # Calculate pass rate
    if not results:
        return results, 0.0

    passed_count = sum(1 for r in results if r.passed)
    pass_rate = passed_count / len(results)

    return results, pass_rate


def print_validation_report(results: List[ValidationResult], pass_rate: float):
    """
    列印驗證報告。

    Args:
        results: 驗證結果列表
        pass_rate: 通過率
    """
    print("="*80)
    print("TIER1 STRUCTURAL VALIDATION REPORT")
    print("="*80)

    # Summary
    total = len(results)
    passed = sum(1 for r in results if r.passed)

    print(f"\nTotal Generations: {total}")
    print(f"Fully Passed: {passed}/{total} ({pass_rate:.1%})")
    print(f"Threshold: >90%")

    if pass_rate >= 0.9:
        print(f"✅ TIER1 PASSED - Ready for Tier2 Canary Test")
    else:
        print(f"❌ TIER1 FAILED - Need Golden Template adjustment")

    # Detailed breakdown
    print(f"\n{'='*80}")
    print("DETAILED BREAKDOWN")
    print("="*80)

    check_names = [
        'has_strategy_def',
        'has_report_assignment',
        'has_return_statement',
        'compiles_successfully',
        'no_lookahead_bias'
    ]

    for check_name in check_names:
        count = sum(1 for r in results if getattr(r, check_name))
        rate = count / total if total > 0 else 0
        status = "✅" if rate >= 0.9 else "❌"
        print(f"{status} {check_name:25s}: {count:2d}/{total} ({rate:5.1%})")

    # Individual results
    print(f"\n{'='*80}")
    print("INDIVIDUAL RESULTS")
    print("="*80)

    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result.passed else f"❌ FAIL ({result.score:.0%})"
        print(f"Generation {i:2d}: {status}")

        if not result.passed:
            # Show which checks failed
            failures = []
            if not result.has_strategy_def:
                failures.append("no_strategy_def")
            if not result.has_report_assignment:
                failures.append("no_report")
            if not result.has_return_statement:
                failures.append("no_return")
            if not result.compiles_successfully:
                failures.append("syntax_error")
            if not result.no_lookahead_bias:
                failures.append("lookahead_bias")

            print(f"              Failures: {', '.join(failures)}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Tier1 structural validation for LLM-generated strategies"
    )
    parser.add_argument(
        'innovations_file',
        type=str,
        help='Path to innovations.jsonl file'
    )

    args = parser.parse_args()

    # Validate
    innovations_file = Path(args.innovations_file)
    results, pass_rate = validate_from_file(innovations_file)

    # Print report
    print_validation_report(results, pass_rate)

    # Exit code
    return 0 if pass_rate >= 0.9 else 1


if __name__ == '__main__':
    sys.exit(main())
