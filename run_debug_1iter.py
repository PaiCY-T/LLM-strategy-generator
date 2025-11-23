"""Debug test: Run 1 iteration to check classification logic"""
import sys
from pathlib import Path
from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop

# Load config
config_path = "experiments/llm_learning_validation/config_debug_1.yaml"
config = LearningConfig.from_yaml(config_path)

print("=== Running 1 iteration debug test ===")
print(f"Config: {config_path}")
print(f"Max Iterations: {config.max_iterations}")
print()

# Initialize and run
loop = LearningLoop(config)
loop.run()

print("\n=== Test completed ===")
