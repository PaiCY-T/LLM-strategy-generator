#!/usr/bin/env python3
"""
Factor Graph 10轮测试 - 详细计时版本
验证timeout fix后的执行时间
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.learning.learning_loop import LearningLoop


def main():
    print("=" * 80)
    print("Factor Graph 10轮测试 - 详细计时")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 配置文件路径
    config_path = "experiments/llm_learning_validation/config_fg_only_10.yaml"

    # 确保输出目录存在
    os.makedirs("experiments/llm_learning_validation/results/fg_only_10", exist_ok=True)
    os.makedirs("experiments/llm_learning_validation/results/fg_only_10/logs", exist_ok=True)

    # 初始化LearningLoop
    print("正在初始化 LearningLoop...")
    loop = LearningLoop(config_path)
    print("✓ 初始化完成")
    print()

    # 记录每轮时间
    iteration_times = []
    total_start = time.time()

    print("开始执行10轮迭代...")
    print("-" * 80)

    try:
        # 手动运行每一轮，以便记录时间
        for i in range(10):
            iter_start = time.time()
            print(f"\n第 {i+1}/10 轮 开始 - {datetime.now().strftime('%H:%M:%S')}")

            try:
                # 执行单轮迭代
                loop.executor.execute_iteration(
                    iteration=i,
                    history=loop.history,
                    champion_tracker=loop.champion_tracker,
                    feedback_generator=loop.feedback_generator,
                    innovation_mode=loop.config.get("llm", {}).get("enabled", False),
                    llm_client=loop.llm_client,
                )

                iter_time = time.time() - iter_start
                iteration_times.append({
                    "iteration": i + 1,
                    "duration_seconds": round(iter_time, 2),
                    "status": "success"
                })

                print(f"第 {i+1}/10 轮 完成 - 耗时: {iter_time:.2f}秒")

            except Exception as e:
                iter_time = time.time() - iter_start
                iteration_times.append({
                    "iteration": i + 1,
                    "duration_seconds": round(iter_time, 2),
                    "status": "failed",
                    "error": str(e)
                })
                print(f"第 {i+1}/10 轮 失败 - 耗时: {iter_time:.2f}秒")
                print(f"错误: {e}")

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")

    total_time = time.time() - total_start

    # 打印汇总统计
    print("\n" + "=" * 80)
    print("测试完成 - 时间统计")
    print("=" * 80)

    success_count = sum(1 for t in iteration_times if t["status"] == "success")
    failed_count = len(iteration_times) - success_count

    print(f"\n总体统计:")
    print(f"  完成轮数: {len(iteration_times)}/10")
    print(f"  成功: {success_count}")
    print(f"  失败: {failed_count}")
    print(f"  成功率: {success_count/len(iteration_times)*100:.1f}%")
    print(f"  总耗时: {total_time:.2f}秒 ({total_time/60:.1f}分钟)")

    if success_count > 0:
        success_times = [t["duration_seconds"] for t in iteration_times if t["status"] == "success"]
        print(f"\n成功轮次时间统计:")
        print(f"  平均: {sum(success_times)/len(success_times):.2f}秒")
        print(f"  最快: {min(success_times):.2f}秒")
        print(f"  最慢: {max(success_times):.2f}秒")

    print(f"\n详细轮次时间:")
    print(f"{'轮次':<6} {'耗时(秒)':<12} {'状态':<10}")
    print("-" * 80)
    for t in iteration_times:
        status_str = "✓ 成功" if t["status"] == "success" else "✗ 失败"
        print(f"{t['iteration']:<6} {t['duration_seconds']:<12} {status_str}")
        if t["status"] == "failed" and "error" in t:
            print(f"       错误: {t['error'][:60]}")

    # 保存详细结果到JSON
    result_file = f"experiments/llm_learning_validation/results/fg_only_10/timing_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result_data = {
        "test_config": {
            "mode": "Factor Graph Only",
            "iterations": 10,
            "timeout_seconds": 900,
            "resample": "M"
        },
        "summary": {
            "total_iterations": len(iteration_times),
            "success_count": success_count,
            "failed_count": failed_count,
            "success_rate": round(success_count/len(iteration_times)*100, 2) if iteration_times else 0,
            "total_duration_seconds": round(total_time, 2),
            "total_duration_minutes": round(total_time/60, 2)
        },
        "iterations": iteration_times,
        "timestamp": datetime.now().isoformat()
    }

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    print(f"\n详细结果已保存至: {result_file}")
    print("=" * 80)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
