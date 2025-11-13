#!/usr/bin/env python3
"""
Test Docker container can access finlab data
"""
import sys
sys.path.insert(0, '/mnt/c/Users/jnpi/documents/finlab')

from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig

# Test code that uses finlab data
test_code = """
from finlab import data

# Try to fetch data
close = data.get('price:收盤價')

print(f"✅ finlab data accessible!")
print(f"✅ Data shape: {close.shape}")
print(f"✅ Latest date: {close.index[-1]}")

# Set signal for return
signal = close.is_largest(10)
"""

print("Testing Docker container with finlab data access...")
print("=" * 60)

try:
    # Load config
    config = DockerConfig.from_yaml()
    print(f"✅ Config loaded")
    print(f"   Network mode: {config.network_mode}")
    print(f"   Sandbox enabled: {config.enabled}")

    # Create executor
    executor = DockerExecutor(config)
    print(f"✅ DockerExecutor created")

    # Execute test code
    print(f"\n🚀 Running test code in Docker...")
    result = executor.execute(test_code, timeout=120)

    print(f"\n📊 Results:")
    print(f"   Success: {result['success']}")
    print(f"   Execution time: {result['execution_time']:.2f}s")

    if result['success']:
        print(f"\n✅ TEST PASSED!")
        print(f"   finlab data IS accessible in Docker")
        if 'logs' in result:
            print(f"\n📝 Container logs:")
            print(result['logs'])
    else:
        print(f"\n❌ TEST FAILED!")
        print(f"   Error: {result['error']}")
        if 'logs' in result:
            print(f"\n📝 Container logs:")
            print(result['logs'])
        sys.exit(1)

except Exception as e:
    print(f"\n❌ TEST ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Docker finlab integration verified!")
