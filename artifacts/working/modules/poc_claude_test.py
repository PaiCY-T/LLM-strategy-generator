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

def _build_diversity_guidance(population_context):
    """
    Build diversity guidance text from population context.

    This function creates prompts that guide the LLM to generate diverse strategies
    by providing information about the existing population and explicitly asking
    for novelty.

    Args:
        population_context: Dict with 'top_factors', 'underused_factors', 'common_patterns'

    Returns:
        str: Diversity guidance text to prepend to main prompt
    """
    if not population_context:
        return ""

    top_factors = population_context.get('top_factors', [])
    underused_factors = population_context.get('underused_factors', [])
    common_patterns = population_context.get('common_patterns', [])

    guidance = """
═══════════════════════════════════════════════════════════════
DIVERSITY OPTIMIZATION REQUIREMENT
═══════════════════════════════════════════════════════════════

EXISTING POPULATION ANALYSIS:
"""

    if top_factors:
        guidance += f"\nMost frequently used factors (AVOID these if possible):\n"
        for i, factor in enumerate(top_factors[:5], 1):
            guidance += f"  {i}. {factor}\n"

    if underused_factors:
        guidance += f"\nUnderused/rare factors (PRIORITIZE these):\n"
        for i, factor in enumerate(underused_factors[:8], 1):
            guidance += f"  {i}. {factor}\n"

    if common_patterns:
        guidance += f"\nCommon patterns to DIFFERENTIATE from:\n"
        for i, pattern in enumerate(common_patterns[:3], 1):
            guidance += f"  {i}. {pattern}\n"

    guidance += """
YOUR TASK - GENERATE A NOVEL, DIVERSE STRATEGY:

1. FACTOR SELECTION DIVERSITY:
   - Prioritize factors from the "underused" list above
   - Avoid factors from the "most frequently used" list
   - Explore unusual factor combinations
   - Consider factors from different categories (entry, momentum, value, quality, risk)

2. STRUCTURAL DIVERSITY:
   - Use different exit parameter ranges from common patterns
   - Try different signal aggregation methods (weighted sum, multiplication, min/max)
   - Vary position sizing approaches
   - Explore different risk management techniques

3. INNOVATION REQUIREMENTS:
   - Your strategy must be STRUCTURALLY DIFFERENT from existing population
   - Aim for low correlation with existing strategies
   - Create a unique risk/return profile
   - Be creative while maintaining validity

CRITICAL: Generate a strategy that expands the diversity of the population.
Do NOT simply copy patterns from the most common strategies.

═══════════════════════════════════════════════════════════════

"""

    return guidance

def generate_strategy(iteration_num=0, history="", model="gemini-2.5-flash", population_context=None):
    """
    Generate a trading strategy using Google AI API first, with OpenRouter as fallback

    Priority: Google AI (primary) → OpenRouter (fallback)

    Args:
        iteration_num: Current iteration number (0-indexed)
        history: Natural language summary of previous iterations
        model: Model to use (default: gemini-2.5-flash)
               Google AI models: gemini-2.5-flash, gemini-2.0-flash-thinking-exp, gemini-pro
               OpenRouter models: google/gemini-2.5-flash, anthropic/claude-sonnet-4, openai/o3, etc.
        population_context: Optional dict with diversity information:
               {
                   'top_factors': list of most-used factors in population,
                   'underused_factors': list of rarely-used factors,
                   'common_patterns': list of common strategy patterns
               }

    Returns:
        str: Generated Python code
    """
    # Bug #2 fix: Validate model/provider routing before API calls
    # If model contains "/" prefix (like "anthropic/...", "openai/..."), it's for OpenRouter
    # Google AI only accepts gemini-* models without prefix
    if '/' in model:
        # Model has provider prefix (e.g., "anthropic/claude-3.5-sonnet")
        provider_prefix = model.split('/')[0].lower()

        # Only "google/" prefix should try Google AI first
        if provider_prefix != 'google':
            # Non-Google models (anthropic, openai, etc.) go directly to OpenRouter
            print(f"🔀 Model '{model}' routed to OpenRouter (provider: {provider_prefix})")
            try:
                return _generate_with_openrouter(iteration_num, history, model, population_context)
            except Exception as e:
                print(f"❌ OpenRouter failed: {e}")
                raise RuntimeError(f"OpenRouter API failed for {model}: {e}")

    # Try Google AI first (primary) - only for gemini-* models
    try:
        print("🎯 Attempting Google AI (primary)...")
        # If model has "google/" prefix, extract the model name
        google_model = model.split('/')[-1] if '/' in model else model

        # Bug #2 fix: Validate that Google AI only receives gemini-* models
        if not google_model.startswith('gemini'):
            raise ValueError(
                f"Invalid model '{google_model}' for Google AI provider. "
                f"Google AI only supports gemini-* models. "
                f"For other models, use OpenRouter with full model name (e.g., 'anthropic/claude-3.5-sonnet')"
            )

        return _generate_with_google_ai(iteration_num, history, google_model, population_context)
    except Exception as e:
        print(f"⚠️ Google AI failed: {e}")
        print("🔄 Falling back to OpenRouter...")

        # Fallback to OpenRouter
        try:
            # Convert to OpenRouter format if needed
            openrouter_model = f"google/{model}" if '/' not in model else model
            return _generate_with_openrouter(iteration_num, history, openrouter_model, population_context)
        except Exception as e2:
            print(f"❌ OpenRouter fallback also failed: {e2}")
            raise RuntimeError(f"Both APIs failed. Google AI: {e}, OpenRouter: {e2}")

def _generate_with_openrouter(iteration_num, history, model, population_context=None):
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

    # Add diversity guidance if population context provided
    if population_context:
        diversity_guidance = _build_diversity_guidance(population_context)
        full_prompt = diversity_guidance + "\n\n" + full_prompt
        print(f"🎨 Added diversity guidance to prompt (population-aware generation)")

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

def _generate_with_google_ai(iteration_num, history, model, population_context=None):
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

    # Add diversity guidance if population context provided
    if population_context:
        diversity_guidance = _build_diversity_guidance(population_context)
        full_prompt = diversity_guidance + "\n\n" + full_prompt
        print(f"🎨 Added diversity guidance to prompt (population-aware generation)")

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

            # Debug: Show response preview (first 500 chars)
            print(f"📝 Response preview: {generated_text[:500]}...")

            # Extract code from ```python blocks
            code = extract_code_from_response(generated_text)

            if code:
                print(f"✅ Successfully generated strategy ({len(code)} chars)")
                return code
            else:
                print(f"⚠️ No code block found in response")
                print(f"   Response length: {len(generated_text)} chars")
                print(f"   Response contains '```': {('```' in generated_text)}")
                print(f"   Response contains 'python': {('python' in generated_text.lower())}")
                print(f"⚠️ Retrying with enhanced prompt...")

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
    Extract Python code from response text with multiple fallback strategies

    Supports:
    - ```python ... ``` (standard markdown)
    - ``` ... ``` (generic code block)
    - Direct Python code (starts with import/def/class)

    Args:
        text: API response text

    Returns:
        str: Extracted Python code, or None if not found
    """
    # Strategy 1: Match ```python ... ``` blocks
    pattern = r'```python\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    if matches:
        print(f"   ✓ Found code in ```python block (Strategy 1)")
        return matches[0].strip()

    # Strategy 2: Match any ``` ... ``` blocks
    pattern = r'```\s*(.*?)\s*```'
    matches = re.findall(pattern, text, re.DOTALL)

    if matches:
        # Check if it looks like Python code
        for match in matches:
            if any(keyword in match for keyword in ['import ', 'def ', 'class ', 'from ']):
                print(f"   ✓ Found code in generic ``` block (Strategy 2)")
                return match.strip()

    # Strategy 3: Detect raw Python code without markdown wrapper
    # Check if the entire response looks like Python code
    lines = text.strip().split('\n')

    # Count lines that look like Python code
    python_line_count = 0
    total_non_empty_lines = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        total_non_empty_lines += 1

        # Check if line looks like Python code
        is_python_line = (
            stripped.startswith('#') or  # Comment
            stripped.startswith('import ') or
            stripped.startswith('from ') or
            stripped.startswith('def ') or
            stripped.startswith('class ') or
            '=' in stripped or  # Assignment
            stripped.startswith('return ') or
            stripped.startswith('if ') or
            stripped.startswith('for ') or
            stripped.startswith('while ') or
            any(keyword in stripped for keyword in ['data.get(', 'data.indicator(', '.shift(', '.pct_change('])
        )

        if is_python_line:
            python_line_count += 1

    # If >70% of non-empty lines look like Python, treat whole response as code
    if total_non_empty_lines > 0 and python_line_count / total_non_empty_lines > 0.7:
        # Remove any leading/trailing explanatory text
        code_lines = []
        for line in lines:
            # Skip obvious explanatory text at start
            if line.strip() and not any(phrase in line.lower() for phrase in [
                'here is', 'here\'s', 'this code', 'the code', 'strategy code:',
                'below is', 'following is'
            ]):
                code_lines.append(line)

        code = '\n'.join(code_lines).strip()
        if len(code) > 100:
            print(f"   ✓ Detected raw Python code (Strategy 3): {python_line_count}/{total_non_empty_lines} lines are Python")
            return code

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
    model = "gemini-2.5-flash"  # Default: Google AI (will fallback to OpenRouter if needed)
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
