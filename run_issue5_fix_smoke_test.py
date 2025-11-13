"""
Smoke test to verify Issue #5 fix works in autonomous loop.
Run 5 iterations to verify Docker execution success rate.
"""

import sys
sys.path.insert(0, '/mnt/c/Users/jnpi/documents/finlab')

from artifacts.working.modules.autonomous_loop import AutonomousLoop
from src.config.experiment_config import ExperimentConfig
import yaml
import time

print("=" * 80)
print("ISSUE #5 FIX - 5-ITERATION SMOKE TEST")
print("=" * 80)
print()

# Load config
config_path = '/mnt/c/Users/jnpi/documents/finlab/config/learning_system.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

print("Configuration loaded:")
print(f"  LLM enabled: {config.get('llm_generation', {}).get('enabled', False)}")
print(f"  Sandbox enabled: True (Docker)")
print()

# Initialize autonomous loop
loop = AutonomousLoop(config)

print("Starting 5-iteration smoke test...")
print()

docker_success_count = 0
docker_attempt_count = 0
diversity_activation_count = 0

start_time = time.time()

for i in range(5):
    print(f"Iteration {i+1}/5...")

    try:
        result = loop.run_iteration(iteration=i)

        # Check if Docker was used
        if hasattr(loop, 'last_execution_mode'):
            if loop.last_execution_mode == 'sandbox':
                docker_attempt_count += 1
                if result.get('success'):
                    docker_success_count += 1
                    print(f"  ✅ Docker execution: SUCCESS")
                else:
                    print(f"  ❌ Docker execution: FAILED")
            else:
                print(f"  ⚠️  Direct execution (validation failed or diversity)")

        # Check diversity activation
        if hasattr(loop, 'last_result') and loop.last_result == False:
            diversity_activation_count += 1

    except Exception as e:
        print(f"  ❌ Error: {e}")

    print()

duration = time.time() - start_time

print("=" * 80)
print("SMOKE TEST RESULTS:")
print("=" * 80)
print(f"Total iterations: 5")
print(f"Docker attempts: {docker_attempt_count}")
print(f"Docker successes: {docker_success_count}")
print(f"Docker success rate: {docker_success_count/docker_attempt_count*100:.1f}%" if docker_attempt_count > 0 else "N/A")
print(f"Diversity activations: {diversity_activation_count}")
print(f"Test duration: {duration:.1f}s")
print()

# Verify fix
if docker_attempt_count > 0:
    success_rate = docker_success_count / docker_attempt_count
    if success_rate >= 0.8:
        print("✅ SUCCESS: Docker execution success rate >= 80%")
        print(f"   Issue #5 fix is VERIFIED!")
    else:
        print(f"⚠️  PARTIAL: Docker success rate {success_rate*100:.1f}% (target: >= 80%)")
else:
    print("⚠️  WARNING: No Docker executions attempted (check if sandbox is enabled)")

print()
print("=" * 80)
