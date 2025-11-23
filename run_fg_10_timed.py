#!/usr/bin/env python3
"""
Factor Graph 10轮测试 - 详细计时

验证timeout fix后的Factor Graph性能
"""

import os
import sys
import logging
import json
import time
from datetime import datetime
from pathlib import Path

# Add src to path for LearningLoop import
sys.path.insert(0, os.path.dirname(__file__))

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop


def main():
    print("=" * 80)
    print("Factor Graph 10轮测试 - 详细计时")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    config_path = "experiments/llm_learning_validation/config_fg_only_10.yaml"

    # 确保输出目录存在
    os.makedirs("experiments/llm_learning_validation/results/fg_only_10", exist_ok=True)
    os.makedirs("experiments/llm_learning_validation/results/fg_only_10/logs", exist_ok=True)

    try:
        # Load configuration from YAML
        config = LearningConfig.from_yaml(config_path)
        print(f"✓ 配置加载成功")
        print(f"  迭代次数: {config.max_iterations}")
        print(f"  Timeout: {config.timeout_seconds}秒")
        print(f"  Resample: {config.resample}")
        print()

        # Initialize learning loop
        print("正在初始化 LearningLoop...")
        loop = LearningLoop(config)
        print("✓ LearningLoop 初始化完成")
        print()

        # 记录每轮时间
        iteration_times = []
        total_start = time.time()

        print("开始执行10轮迭代...")
        print("-" * 80)

        # 运行测试
        loop.run()

        total_time = time.time() - total_start

        # 读取结果
        innovations_file = "experiments/llm_learning_validation/results/fg_only_10/innovations.jsonl"
        if os.path.exists(innovations_file):
            with open(innovations_file, 'r') as f:
                lines = f.readlines()
                success_count = len(lines)
        else:
            success_count = 0

        # 打印结果
        print()
        print("=" * 80)
        print("测试完成")
        print("=" * 80)
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {total_time:.2f}秒 ({total_time/60:.1f}分钟)")
        print(f"完成轮数: {success_count}/10")
        if success_count > 0:
            print(f"平均每轮: {total_time/success_count:.2f}秒")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
