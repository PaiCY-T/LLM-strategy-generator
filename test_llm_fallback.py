#!/usr/bin/env python3
"""
Test LLM Fallback Mechanism

Simulates Gemini API quota exhaustion to verify automatic fallback to OpenRouter.
"""

import os
from src.innovation.llm_client import LLMClient, LLMConfig

def test_fallback_mechanism():
    """Test automatic fallback from Gemini to OpenRouter when quota exhausted."""
    print("=" * 70)
    print("TESTING LLM FALLBACK MECHANISM")
    print("=" * 70)

    # Setup primary (Gemini) and fallback (OpenRouter) configs
    google_key = os.getenv('GOOGLE_API_KEY')
    openrouter_key = os.getenv('OPENROUTER_API_KEY')

    if not google_key or not openrouter_key:
        print("⚠️  需要同時設置 GOOGLE_API_KEY 和 OPENROUTER_API_KEY 才能測試 fallback")
        return

    primary_config = LLMConfig(
        provider='gemini',
        model='gemini-2.5-flash',
        api_key=google_key,
        temperature=0.7,
        max_tokens=100
    )

    fallback_config = LLMConfig(
        provider='openrouter',
        model='google/gemini-2.5-flash',
        api_key=openrouter_key,
        temperature=0.7,
        max_tokens=100
    )

    client = LLMClient(primary_config, fallback_config=fallback_config)

    # Test 1: Normal operation (should use Gemini)
    print("\n測試 1: 正常操作 (應使用 Gemini)")
    print("-" * 70)
    response = client.generate("什麼是 Python?", max_retries=1)
    if response:
        print(f"✅ 成功獲取回應 (長度: {len(response)} 字)")
        print(f"預覽: {response[:100]}...")
    else:
        print("❌ 生成失敗")

    # Test 2: Manually trigger quota exhaustion
    print("\n測試 2: 模擬 Quota 耗盡")
    print("-" * 70)
    print("手動設置 _quota_exhausted = True...")
    client._quota_exhausted = True

    response = client.generate("什麼是機器學習?", max_retries=1)
    if response:
        print(f"✅ Fallback 成功! (長度: {len(response)} 字)")
        print(f"預覽: {response[:100]}...")
    else:
        print("❌ Fallback 失敗")

    print("\n" + "=" * 70)
    print("FALLBACK 測試完成")
    print("=" * 70)

if __name__ == "__main__":
    test_fallback_mechanism()
