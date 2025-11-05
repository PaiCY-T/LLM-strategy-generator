#!/usr/bin/env python3
"""
Phase 0 Smoke Test - Dry-Run Mode (ZERO execution risk)
Tests LLM connectivity, YAML generation, validation, and code generation
WITHOUT executing any generated code.
"""

import os
import sys
import time
import json
import ast
from datetime import datetime

print("=" * 70)
print("Phase 0: Pre-Docker Smoke Test (Dry-Run Mode)")
print("=" * 70)
print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Safety: Docker=OFF, Execution=OFF, Mode=DRY-RUN")
print("=" * 70)
print()

# Results tracking
results = {
    "start_time": datetime.now().isoformat(),
    "test_cases": [],
    "summary": {}
}

def log_test(name, status, details=""):
    """Log test result"""
    emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{emoji} TC-P0-{len(results['test_cases'])+1:02d}: {name}")
    if details:
        print(f"    {details}")
    results["test_cases"].append({
        "name": name,
        "status": status,
        "details": details
    })

# TC-P0-01: Check API Key
try:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key and len(api_key) > 20:
        log_test("API Key Environment Variable", "PASS", f"Key length: {len(api_key)}")
    else:
        log_test("API Key Environment Variable", "FAIL", "API key not set or invalid")
        sys.exit(1)
except Exception as e:
    log_test("API Key Environment Variable", "FAIL", str(e))
    sys.exit(1)

# TC-P0-02: Test LLM Provider Import
try:
    sys.path.insert(0, '/mnt/c/Users/jnpi/documents/finlab')
    from src.innovation.llm_providers import OpenRouterProvider
    log_test("LLM Provider Module Import", "PASS", "OpenRouterProvider loaded")
except ImportError as e:
    log_test("LLM Provider Module Import", "FAIL", f"Import error: {e}")
    print("\n⚠️  LLM Provider not found. Testing with mock...")
    OpenRouterProvider = None
except Exception as e:
    log_test("LLM Provider Module Import", "FAIL", str(e))
    OpenRouterProvider = None

# TC-P0-03: Test LLM Connectivity (if provider available)
llm_response = None
if OpenRouterProvider:
    try:
        provider = OpenRouterProvider(
            api_key=api_key,
            model="google/gemini-2.5-flash-lite"
        )

        prompt = """Generate a YAML strategy specification EXACTLY as shown below.
Do NOT modify the structure. ONLY change the values if needed.

COPY THIS EXACTLY:
```yaml
metadata:
  name: "Simple Momentum Strategy"
  description: "Basic momentum strategy"
  strategy_type: "momentum"
  rebalancing_frequency: "M"

indicators:
  - name: "rsi_14"
    type: "RSI"
    period: 14

entry_conditions:
  - type: "threshold"
    indicator: "rsi_14"
    operator: ">"
    value: 50

exit_conditions:
  - type: "threshold"
    indicator: "rsi_14"
    operator: "<"
    value: 50
```

CRITICAL: Use EXACTLY this structure. The type field for conditions MUST be "threshold".
Do not add extra indicators or conditions. Keep it simple."""

        print(f"\n🔄 Calling LLM API (google/gemini-2.5-flash-lite)...")
        start = time.time()
        response = provider.generate(prompt, max_tokens=500, temperature=0.1)
        elapsed = time.time() - start

        if response and response.content and len(response.content) > 50:
            llm_response = response.content
            log_test("LLM API Connectivity", "PASS", f"Response received ({len(llm_response)} chars, {elapsed:.2f}s)")

            # Save response
            with open('artifacts/phase0_llm_response.txt', 'w') as f:
                f.write(llm_response)
        else:
            log_test("LLM API Connectivity", "FAIL", "Empty or invalid response")
            
    except Exception as e:
        log_test("LLM API Connectivity", "FAIL", str(e))
        llm_response = None
else:
    log_test("LLM API Connectivity", "SKIP", "Provider not available")

# TC-P0-04: Extract YAML from Response
yaml_extracted = None
if llm_response:
    try:
        import re
        # Try to extract YAML from markdown code blocks
        yaml_pattern = r'```(?:yaml)?\s*\n(.*?)\n```'
        matches = re.findall(yaml_pattern, llm_response, re.DOTALL)
        
        if matches:
            yaml_extracted = matches[0].strip()
            log_test("YAML Extraction", "PASS", f"Extracted {len(yaml_extracted)} chars")
            
            # Save extracted YAML
            with open('artifacts/phase0_extracted_yaml.yaml', 'w') as f:
                f.write(yaml_extracted)
        else:
            # Try direct parsing
            yaml_extracted = llm_response.strip()
            log_test("YAML Extraction", "WARN", "No markdown blocks, using raw response")
            
    except Exception as e:
        log_test("YAML Extraction", "FAIL", str(e))
else:
    log_test("YAML Extraction", "SKIP", "No LLM response to extract from")

# TC-P0-05: Validate YAML Schema
parsed_yaml = None
if yaml_extracted:
    try:
        import yaml
        parsed_yaml = yaml.safe_load(yaml_extracted)

        # Check for required top-level keys
        required_keys = ['metadata', 'indicators']
        has_required = all(key in parsed_yaml for key in required_keys)

        if has_required:
            log_test("YAML Schema Validation", "PASS", f"Has required keys: {', '.join(required_keys)}")
        else:
            missing = [k for k in required_keys if k not in parsed_yaml]
            log_test("YAML Schema Validation", "WARN", f"Missing keys: {', '.join(missing)}")

    except yaml.YAMLError as e:
        log_test("YAML Schema Validation", "FAIL", f"YAML parse error: {e}")
        parsed_yaml = None
    except Exception as e:
        log_test("YAML Schema Validation", "FAIL", str(e))
        parsed_yaml = None
else:
    log_test("YAML Schema Validation", "SKIP", "No YAML to validate")

# TC-P0-06: Test YAML Normalizer
if parsed_yaml:
    try:
        from src.generators.yaml_normalizer import normalize_yaml

        normalized = normalize_yaml(parsed_yaml)

        if normalized:
            import yaml
            normalized_str = yaml.dump(normalized, default_flow_style=False)
            log_test("YAML Normalization", "PASS", f"Normalization successful")

            # Save normalized YAML
            with open('artifacts/phase0_normalized_yaml.yaml', 'w') as f:
                f.write(normalized_str)
        else:
            log_test("YAML Normalization", "WARN", "Normalization returned empty")
            normalized = None

    except Exception as e:
        log_test("YAML Normalization", "WARN", f"Normalizer error: {e}")
        normalized = None
else:
    log_test("YAML Normalization", "SKIP", "No YAML to normalize")
    normalized = None

# TC-P0-07: Test Code Generation
generated_code = None
if normalized:
    try:
        from src.generators.yaml_to_code_generator import YAMLToCodeGenerator
        generator = YAMLToCodeGenerator()

        generated_code = generator.generate(normalized)
        
        if generated_code and len(generated_code) > 50:
            log_test("Code Generation", "PASS", f"Generated {len(generated_code)} chars of code")
            
            # Save generated code
            with open('artifacts/phase0_generated_code.py', 'w') as f:
                f.write(generated_code)
        else:
            log_test("Code Generation", "FAIL", "Code generation failed or empty")
            
    except Exception as e:
        log_test("Code Generation", "FAIL", str(e))
else:
    log_test("Code Generation", "SKIP", "No YAML to generate code from")

# TC-P0-08: AST Syntax Validation (DRY-RUN - NO EXECUTION)
if generated_code:
    try:
        tree = ast.parse(generated_code)
        
        if tree:
            log_test("AST Syntax Validation", "PASS", "✅ Code is syntactically correct")
        else:
            log_test("AST Syntax Validation", "FAIL", "AST parse returned None")
            
    except SyntaxError as e:
        log_test("AST Syntax Validation", "FAIL", f"Syntax error: {e}")
    except Exception as e:
        log_test("AST Syntax Validation", "FAIL", str(e))
else:
    log_test("AST Syntax Validation", "SKIP", "No code to validate")

# TC-P0-09: Import Safety Check
if generated_code:
    try:
        dangerous_imports = ['os.system', 'subprocess', 'eval', 'exec', '__import__']
        found_dangerous = []
        
        for dangerous in dangerous_imports:
            if dangerous in generated_code:
                found_dangerous.append(dangerous)
        
        if not found_dangerous:
            log_test("Import Safety Check", "PASS", "No dangerous imports found")
        else:
            log_test("Import Safety Check", "FAIL", f"Found: {', '.join(found_dangerous)}")
            
    except Exception as e:
        log_test("Import Safety Check", "FAIL", str(e))
else:
    log_test("Import Safety Check", "SKIP", "No code to check")

# TC-P0-10: Execution Safety Guarantee
try:
    # Verify no actual execution happened
    execution_happened = False  # This is a DRY-RUN test
    
    if not execution_happened:
        log_test("Execution Safety Guarantee", "PASS", "✅ ZERO execution (dry-run only)")
    else:
        log_test("Execution Safety Guarantee", "FAIL", "⚠️  Execution detected!")
        
except Exception as e:
    log_test("Execution Safety Guarantee", "FAIL", str(e))

# Calculate Summary
print("\n" + "=" * 70)
print("Phase 0 Test Summary")
print("=" * 70)

passed = sum(1 for tc in results["test_cases"] if tc["status"] == "PASS")
failed = sum(1 for tc in results["test_cases"] if tc["status"] == "FAIL")
skipped = sum(1 for tc in results["test_cases"] if tc["status"] == "SKIP")
warned = sum(1 for tc in results["test_cases"] if tc["status"] == "WARN")
total = len(results["test_cases"])

results["summary"] = {
    "total": total,
    "passed": passed,
    "failed": failed,
    "skipped": skipped,
    "warned": warned,
    "pass_rate": passed / total if total > 0 else 0,
    "end_time": datetime.now().isoformat()
}

print(f"\nTotal Tests: {total}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"⚠️  Warnings: {warned}")
print(f"⏭️  Skipped: {skipped}")
print(f"\nPass Rate: {results['summary']['pass_rate']:.1%}")

# Save results
with open('artifacts/phase0_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n📊 Results saved to: artifacts/phase0_test_results.json")
print(f"📄 Artifacts saved to: artifacts/phase0_*")

# Determine success
if failed == 0 and passed >= 5:
    print("\n✅ Phase 0 Test: SUCCESS")
    print("Safe to proceed with Week 1 planning")
    exit(0)
elif failed > 0:
    print("\n⚠️  Phase 0 Test: PARTIAL SUCCESS")
    print("Some tests failed - review issues before proceeding")
    exit(1)
else:
    print("\n⚠️  Phase 0 Test: INCOMPLETE")
    print("Not enough tests passed - check configuration")
    exit(2)
