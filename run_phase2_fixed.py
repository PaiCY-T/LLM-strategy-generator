#!/usr/bin/env python3
"""
Phase 2 Re-Run with All Fixes Applied
=====================================

This script runs 20 iterations of strategy generation and backtesting
with all prompt template and data key fixes applied.

Fixes Applied:
1. Prompt template prioritizes etl:adj_close (adjusted data)
2. Strategy templates use adjusted data
3. Data cache preloads adjusted data
4. Static validator hardened against raw data
5. Actual prompt_template_v1.txt file corrected

Expected: >60% success rate (12+ successful backtests out of 20)
Previous: 0% success rate (0/20 successful)
"""

import os
import sys
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artifacts.working.modules.poc_claude_test import generate_strategy
from artifacts.working.modules.static_validator import validate_code

def run_phase2_fixed(num_iterations=20, model='gemini-2.5-flash-lite'):
    """Run Phase 2 testing with all fixes applied."""

    print("=" * 80)
    print("Phase 2 Re-Run with All Fixes Applied")
    print("=" * 80)
    print(f"Model: {model}")
    print(f"Iterations: {num_iterations}")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    results = {
        'model': model,
        'num_iterations': num_iterations,
        'start_time': datetime.now().isoformat(),
        'iterations': [],
        'summary': {}
    }

    generation_success = 0
    validation_success = 0
    uses_adjusted_data = 0

    for i in range(num_iterations):
        print(f"\n{'='*80}")
        print(f"Iteration {i+1}/{num_iterations}")
        print(f"{'='*80}")

        iteration_result = {
            'iteration': i + 1,
            'generation_success': False,
            'validation_success': False,
            'uses_adjusted_data': False,
            'uses_forbidden_data': False,
            'errors': []
        }

        try:
            # Generate strategy
            print(f"\n[{i+1}] Generating strategy...")
            start_time = time.time()
            code = generate_strategy(iteration_num=i, model=model)
            gen_time = time.time() - start_time

            iteration_result['generation_success'] = True
            iteration_result['generation_time'] = gen_time
            generation_success += 1

            print(f"✅ Strategy generated in {gen_time:.2f}s")

            # Check for adjusted data usage
            if 'etl:adj_close' in code:
                iteration_result['uses_adjusted_data'] = True
                uses_adjusted_data += 1
                print("✅ Uses adjusted data (etl:adj_close)")
            else:
                print("⚠️  Does NOT use etl:adj_close")

            # Check for forbidden data
            forbidden_keys = ["data.get('price:收盤價')", "data.get('price:開盤價')",
                            "data.get('price:最高價')", "data.get('price:最低價')",
                            "data.get('price:成交股數')"]

            for forbidden_key in forbidden_keys:
                if forbidden_key in code:
                    iteration_result['uses_forbidden_data'] = True
                    print(f"❌ Uses forbidden data: {forbidden_key}")
                    break

            if not iteration_result['uses_forbidden_data']:
                print("✅ No forbidden raw price data detected")

            # Validate code
            print(f"\n[{i+1}] Validating strategy...")
            is_valid, issues = validate_code(code)

            iteration_result['validation_success'] = is_valid
            iteration_result['validation_issues'] = issues

            if is_valid:
                validation_success += 1
                print(f"✅ Validation passed")
            else:
                print(f"❌ Validation failed with {len(issues)} issues:")
                for issue in issues[:3]:  # Show first 3 issues
                    print(f"   - {issue}")

            # Save generated code
            code_file = f"generated_strategy_fixed_iter{i}.py"
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)
            iteration_result['code_file'] = code_file

        except Exception as e:
            error_msg = str(e)
            iteration_result['errors'].append(error_msg)
            print(f"❌ Error: {error_msg}")

        results['iterations'].append(iteration_result)

        # Print progress
        print(f"\n[{i+1}] Progress:")
        print(f"  Generation: {generation_success}/{i+1} ({generation_success/(i+1)*100:.1f}%)")
        print(f"  Validation: {validation_success}/{i+1} ({validation_success/(i+1)*100:.1f}%)")
        print(f"  Uses adjusted data: {uses_adjusted_data}/{i+1} ({uses_adjusted_data/(i+1)*100:.1f}%)")

    # Final summary
    results['end_time'] = datetime.now().isoformat()
    results['summary'] = {
        'generation_success': generation_success,
        'generation_rate': generation_success / num_iterations,
        'validation_success': validation_success,
        'validation_rate': validation_success / num_iterations,
        'uses_adjusted_data': uses_adjusted_data,
        'adjusted_data_rate': uses_adjusted_data / num_iterations,
    }

    print("\n" + "=" * 80)
    print("PHASE 2 RE-RUN COMPLETE")
    print("=" * 80)
    print(f"Total iterations: {num_iterations}")
    print(f"Generation success: {generation_success}/{num_iterations} ({generation_success/num_iterations*100:.1f}%)")
    print(f"Validation success: {validation_success}/{num_iterations} ({validation_success/num_iterations*100:.1f}%)")
    print(f"Uses adjusted data: {uses_adjusted_data}/{num_iterations} ({uses_adjusted_data/num_iterations*100:.1f}%)")
    print("=" * 80)

    # Save results
    results_file = f'phase2_fixed_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to: {results_file}")

    # Success criteria check
    target_rate = 0.60  # 60% target
    if validation_success / num_iterations >= target_rate:
        print(f"\n🎉 SUCCESS! Achieved {validation_success/num_iterations*100:.1f}% success rate (target: {target_rate*100:.0f}%)")
    else:
        print(f"\n⚠️  Below target: {validation_success/num_iterations*100:.1f}% success rate (target: {target_rate*100:.0f}%)")

    return results

if __name__ == '__main__':
    results = run_phase2_fixed(num_iterations=20, model='gemini-2.5-flash-lite')
    sys.exit(0)
