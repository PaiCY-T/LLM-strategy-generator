#!/usr/bin/env python3
"""分析 Hybrid 模式策略产出结果"""

import json

# Load results
with open('experiments/llm_learning_validation/results/pilot_hybrid_20/pilot_results.json', 'r') as f:
    data = json.load(f)

iterations = data['hybrid']['runs'][0]['iterations']

print('=' * 80)
print('Hybrid 模式策略产出分析报告 (20 Iterations)')
print('=' * 80)
print()

# 统计成功/失败
success_count = sum(1 for it in iterations if it['execution_result']['success'])
failure_count = len(iterations) - success_count

print(f'执行统计:')
print(f'  总迭代次数: {len(iterations)}')
print(f'  成功次数: {success_count} ({success_count/len(iterations)*100:.1f}%)')
print(f'  失败次数: {failure_count} ({failure_count/len(iterations)*100:.1f}%)')
print()

# 按生成方法统计
llm_count = sum(1 for it in iterations if it['generation_method'] == 'llm')
fg_count = sum(1 for it in iterations if it['generation_method'] == 'factor_graph')

print(f'生成方法分布:')
print(f'  LLM生成: {llm_count} 次 ({llm_count/len(iterations)*100:.1f}%)')
print(f'  Factor Graph生成: {fg_count} 次 ({fg_count/len(iterations)*100:.1f}%)')
print(f'  配置的创新率: 30% LLM + 70% Factor Graph')
print()

# 失败原因分析
print('失败原因分析:')
error_types = {}
for it in iterations:
    if not it['execution_result']['success']:
        error = it['execution_result']['error_message']
        if 'trailing_stop_10pct' in error:
            key = 'Factor Graph Pipeline Error (trailing_stop_10pct 缺少依赖)'
        else:
            key = it['execution_result']['error_type']
        error_types[key] = error_types.get(key, 0) + 1

for error, count in sorted(error_types.items(), key=lambda x: -x[1]):
    print(f'  {error}: {count} 次')
print()

# 成功策略分析
print('=' * 80)
print('成功策略详细分析')
print('=' * 80)
print()

for it in iterations:
    if it['execution_result']['success']:
        print(f'Iteration {it["iteration_num"]}:')
        print(f'  生成方法: {it["generation_method"].upper()}')
        print(f'  执行时间: {it["execution_result"]["execution_time"]:.2f} 秒')
        print(f'  绩效指标:')
        print(f'    - Sharpe Ratio: {it["metrics"]["sharpe_ratio"]:.4f}')
        print(f'    - Total Return: {it["metrics"]["total_return"]:.2%}')
        print(f'    - Max Drawdown: {it["metrics"]["max_drawdown"]:.2%}')
        champion_status = "是" if it['champion_updated'] else "否"
        print(f'  Champion更新: {champion_status}')
        print()

        # 策略代码分析
        if it['strategy_code']:
            code = it['strategy_code']
            print('  策略特征:')
            if 'ROE' in code or 'roe' in code:
                print('    ✓ 使用 ROE 质量过滤')
            if 'momentum' in code or '动量' in code:
                print('    ✓ 使用动量因子')
            if 'trading_value' in code or '成交金额' in code:
                print('    ✓ 使用流动性过滤')
            if 'pb_ratio' in code or '股价净值比' in code:
                print('    ✓ 使用价值因子 (PB Ratio)')
            if 'operating_margin' in code or '营业利益率' in code:
                print('    ✓ 使用营运效率因子')

            # 分析选股逻辑
            print('  选股逻辑:')
            if 'top' in code.lower() and '20' in code:
                print('    - 选取综合得分前 20% 的股票')
            if 'filter' in code.lower():
                print('    - 应用多重过滤条件（流动性、质量、价值）')
            if 'rank' in code.lower():
                print('    - 使用排名系统进行股票筛选')
            print()

print('=' * 80)
print('问题诊断')
print('=' * 80)
print()
print('核心问题:')
print('  Factor Graph 模板配置错误')
print('    - 所有 Factor Graph 生成的策略都使用了 trailing_stop_10pct')
print('    - 该 factor 需要 positions 和 entry_price 作为输入')
print('    - 但这些矩阵在执行阶段不可用（只有 close, momentum, high, low, breakout_signal）')
print('    - 这是模板配置问题，不是策略生成问题')
print()
print('影响:')
print('  - 70% 的迭代（Factor Graph部分）无法产生有效策略')
print('  - 只有 30% 的 LLM 生成部分能够执行')
print('  - 实际创新率降低到了 5% (1/20)')
print()
print('策略质量评估:')
print('  唯一成功的 LLM 策略表现:')
print('    - Sharpe Ratio: -0.137 (非常差，低于0表示风险调整后收益为负)')
print('    - 总回报: -36.68% (严重亏损)')
print('    - 最大回撤: -66.05% (极高风险)')
print('    - 结论: 该策略在回测期间表现极差，不具备实用价值')
print()
print('建议修正措施:')
print('  1. 修正 Factor Graph 模板配置')
print('     - 移除或修正 trailing_stop_10pct 的依赖')
print('     - 确保所有 factor 的输入矩阵在执行时可用')
print('  2. 重新运行测试')
print('     - 修正后再次执行 20 次迭代')
print('     - 验证 70% Factor Graph 部分能正常工作')
print('  3. 策略改进')
print('     - 当前 LLM 生成的策略表现不佳')
print('     - 需要优化 prompt 或调整因子组合')
print('     - 考虑加入止损、仓位管理等风险控制')
