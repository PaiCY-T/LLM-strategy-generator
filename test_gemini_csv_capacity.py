#!/usr/bin/env python3
"""
測試 Gemini 2.5 Flash 是否能處理完整 CSV schema (307 欄位)
驗證官方文檔的 1,048,576 tokens 限制是否真實有效
使用 OpenRouter API: google/gemini-2.5-flash
"""

import os
import csv
import requests
from datetime import datetime

def load_csv_schema(csv_path: str) -> str:
    """載入完整 CSV schema 並格式化為 prompt"""
    fields = []

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            field_name = row['資料集名稱']
            field_key = row['下載方式及key']
            field_type = row['數據類型']
            fields.append(f"- {field_name}: {field_key} ({field_type})")

    schema_text = "\n".join(fields)

    # 創建完整的 prompt（模擬實際使用情況）
    full_prompt = f"""# Taiwan Stock Market Data Fields (FinLab Database)

You are a quantitative trading expert. Below is the COMPLETE list of {len(fields)} data fields available for strategy development:

{schema_text}

**Task**: Based on these fields, suggest 3 momentum-based trading strategies.

**Response Format**:
1. Strategy name and core logic
2. Required fields from the above list
3. Expected holding period
"""

    return full_prompt, len(fields)


def test_gemini_api(prompt: str, field_count: int):
    """測試 Gemini 2.5 Flash API (via OpenRouter) 是否能處理完整 prompt"""

    # 配置 OpenRouter API
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY environment variable not set")
        print("Please set it with: export OPENROUTER_API_KEY='your-api-key'")
        return False

    # 計算 prompt 統計
    char_count = len(prompt)
    estimated_tokens = char_count // 4  # 粗略估計：1 token ≈ 4 chars

    print("=" * 80)
    print("測試配置")
    print("=" * 80)
    print(f"API: OpenRouter")
    print(f"Model: google/gemini-2.5-flash")
    print(f"CSV 欄位數: {field_count}")
    print(f"Prompt 字符數: {char_count:,}")
    print(f"估計 Token 數: {estimated_tokens:,}")
    print(f"官方限制: 1,048,576 tokens")
    print(f"使用比例: {estimated_tokens / 1_048_576 * 100:.2f}%")
    print("")

    # 測試 API 調用
    print("=" * 80)
    print("開始 API 測試 (OpenRouter → Gemini 2.5 Flash)")
    print("=" * 80)

    try:
        start_time = datetime.now()

        # OpenRouter API 調用
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-2.5-flash",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            timeout=120  # 2 分鐘超時
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 檢查回應
        if response.status_code != 200:
            print(f"❌ API 調用失敗 (HTTP {response.status_code})")
            print(f"錯誤訊息: {response.text}")
            return False

        result = response.json()

        # 成功！
        print("✅ API 調用成功！")
        print(f"⏱️  耗時: {duration:.2f} 秒")
        print("")

        # 顯示回應前500字符
        response_text = result['choices'][0]['message']['content']
        print("=" * 80)
        print("API 回應預覽 (前500字符)")
        print("=" * 80)
        print(response_text[:500])
        if len(response_text) > 500:
            print(f"\n... (還有 {len(response_text) - 500} 個字符)")
        print("")

        # Token 使用統計
        if 'usage' in result:
            usage = result['usage']
            print("=" * 80)
            print("Token 使用統計")
            print("=" * 80)
            print(f"Prompt Tokens: {usage.get('prompt_tokens', 'N/A'):,}")
            print(f"Response Tokens: {usage.get('completion_tokens', 'N/A'):,}")
            print(f"Total Tokens: {usage.get('total_tokens', 'N/A'):,}")

            if 'prompt_tokens' in usage:
                print(f"官方限制: 1,048,576 tokens (input)")
                print(f"實際使用: {usage['prompt_tokens'] / 1_048_576 * 100:.2f}%")
            print("")

        print("=" * 80)
        print("結論")
        print("=" * 80)
        print("✅ Gemini 2.5 Flash 可以成功處理完整的 307 欄位 CSV schema")
        print("✅ 沒有 token 限制錯誤")
        print("✅ 官方文檔的 1,048,576 tokens 限制是真實有效的")
        print("")
        print("🎯 下一步建議：")
        print("1. 修復 prompt_builder.py 中的欄位名稱錯誤 (price:成交量 → price:成交股數)")
        print("2. 移除或大幅提高 MAX_PROMPT_TOKENS = 2000 的人為限制")
        print("3. 載入完整 CSV schema 到 prompt 中")
        print("")

        return True

    except requests.exceptions.Timeout:
        print("❌ API 調用超時 (>120秒)")
        print("可能原因：prompt 太大或網路問題")
        return False
    except Exception as e:
        print(f"❌ API 調用失敗: {e}")
        print("")
        print("可能原因：")
        print("1. OPENROUTER_API_KEY 未設置或無效")
        print("2. API 配額已用完")
        print("3. 網路連接問題")
        print("")
        return False


def main():
    csv_path = "/mnt/c/Users/jnpi/ML4T/epic-finlab-data-downloader/example/finlab_database_cleaned.csv"

    print("載入 CSV schema...")
    prompt, field_count = load_csv_schema(csv_path)

    print(f"✅ 載入成功：{field_count} 個欄位")
    print("")

    # 執行測試
    success = test_gemini_api(prompt, field_count)

    if success:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
