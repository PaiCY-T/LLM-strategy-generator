"""
PoC: OpenRouter API Strategy Generation Test
Generates trading strategies using OpenRouter API with curated datasets and prompt template.
Supports multiple models via OpenRouter.
"""
import os
import re
import json
import requests

def load_prompt_template():
    """Load the baseline prompt template"""
    with open('prompt_template_v1.txt', 'r', encoding='utf-8') as f:
        return f.read()

def generate_strategy(iteration_num=0, history="", model="google/gemini-2.5-flash"):
    """
    Generate a trading strategy using OpenRouter API or Google AI API

    Args:
        iteration_num: Current iteration number (0-indexed)
        history: Natural language summary of previous iterations
        model: Model to use (default: google/gemini-2.5-flash)
               OpenRouter models: google/gemini-2.5-flash, anthropic/claude-sonnet-4, openai/o3, etc.
               Google AI models: gemini-2.5-flash, gemini-2.0-flash-thinking-exp, gemini-pro

    Returns:
        str: Generated Python code
    """
    # Determine API based on model name format
    # OpenRouter models have "/" in name (e.g., "google/gemini-2.5-flash")
    # Google AI models don't have "/" (e.g., "gemini-2.5-flash")
    use_google_ai = '/' not in model

    if use_google_ai:
        return _generate_with_google_ai(iteration_num, history, model)
    else:
        return _generate_with_openrouter(iteration_num, history, model)

def _generate_with_openrouter(iteration_num, history, model):
    """Generate strategy using OpenRouter API"""
    # Load API key from environment
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")

    # Load prompt template
    template = load_prompt_template()

    # Build full prompt
    if iteration_num == 0:
        # First iteration: no history
        full_prompt = template.replace('{history}', 'None - this is the first iteration.')
    else:
        # Subsequent iterations: include history
        full_prompt = template.replace('{history}', history)

    # Call OpenRouter API with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Calling OpenRouter API with {model} (attempt {attempt + 1}/{max_retries})...")

            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                timeout=60,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": full_prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4096
                }
            )

            response.raise_for_status()
            result = response.json()

            # Extract generated text
            generated_text = result['choices'][0]['message']['content']

            # Extract code from ```python blocks
            code = extract_code_from_response(generated_text)

            if code:
                print(f"✅ Successfully generated strategy ({len(code)} chars)")
                return code
            else:
                print(f"⚠️ No code block found in response, retrying...")

        except Exception as e:
            print(f"❌ API call failed: {e}")
            if attempt < max_retries - 1:
                import time
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise

    raise RuntimeError("Failed to generate strategy after all retries")

def _generate_with_google_ai(iteration_num, history, model):
    """Generate strategy using Google AI Gemini API"""
    import google.generativeai as genai

    # Load API key from environment
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set")

    # Configure Google AI
    genai.configure(api_key=api_key)

    # Load prompt template
    template = load_prompt_template()

    # Build full prompt
    if iteration_num == 0:
        # First iteration: no history
        full_prompt = template.replace('{history}', 'None - this is the first iteration.')
    else:
        # Subsequent iterations: include history
        full_prompt = template.replace('{history}', history)

    # Call Google AI API with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Calling Google AI with {model} (attempt {attempt + 1}/{max_retries})...")

            # Create model instance
            gemini_model = genai.GenerativeModel(model)

            # Generate response
            response = gemini_model.generate_content(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=4096
                )
            )

            # Extract generated text
            generated_text = response.text

            # Extract code from ```python blocks
            code = extract_code_from_response(generated_text)

            if code:
                print(f"✅ Successfully generated strategy ({len(code)} chars)")
                return code
            else:
                print(f"⚠️ No code block found in response, retrying...")

        except Exception as e:
            print(f"❌ API call failed: {e}")
            if attempt < max_retries - 1:
                import time
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise

    raise RuntimeError("Failed to generate strategy after all retries")

def extract_code_from_response(text):
    """
    Extract Python code from ```python code blocks

    Args:
        text: Claude API response text

    Returns:
        str: Extracted Python code, or None if not found
    """
    # Pattern to match ```python ... ``` blocks
    pattern = r'```python\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        # Return the first code block
        return matches[0].strip()

    # Fallback: try to find any ``` blocks
    pattern = r'```\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        return matches[0].strip()

    return None

def save_strategy(code, iteration_num):
    """Save generated strategy to file"""
    filename = f'generated_strategy_iter{iteration_num}.py'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"💾 Saved to {filename}")
    return filename

if __name__ == '__main__':
    import sys

    # Parse command line arguments for model selection
    model = "google/gemini-2.5-flash"
    if len(sys.argv) > 1:
        model = sys.argv[1]

    # Test: Generate a single strategy
    print("=" * 60)
    print("Testing OpenRouter API Strategy Generation")
    print(f"Model: {model}")
    print("=" * 60)

    try:
        code = generate_strategy(iteration_num=0, model=model)
        print("\n" + "=" * 60)
        print("Generated Code:")
        print("=" * 60)
        print(code)
        print("=" * 60)

        # Save to file
        filename = save_strategy(code, 0)
        print(f"\n✅ Test completed successfully!")
        print(f"Next step: Manually test {filename} in Python REPL")
        print(f"\nUsage: python poc_claude_test.py [model]")
        print(f"Available models: anthropic/claude-sonnet-4, openai/o3-mini, google/gemini-2.5-pro")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
