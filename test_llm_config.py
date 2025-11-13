import sys
sys.path.insert(0, '/mnt/c/Users/jnpi/documents/finlab')

import yaml

with open('config/learning_system.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
llm = config.get('llm', {})

print("LLM Configuration:")
print(f"  enabled: {llm.get('enabled')}")
print(f"  provider: {llm.get('provider')}")
print(f"  innovation_rate: {llm.get('innovation_rate')}")
print(f"  innovation_rate type: {type(llm.get('innovation_rate'))}")

# Test validation
rate = llm.get('innovation_rate', 0.20)
try:
    if 0.0 <= rate <= 1.0:
        print(f"✅ Innovation rate validation passed: {rate}")
    else:
        print(f"❌ Innovation rate out of range: {rate}")
except TypeError as e:
    print(f"❌ Innovation rate validation failed: {e}")
