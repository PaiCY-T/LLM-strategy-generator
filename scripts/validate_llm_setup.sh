#!/bin/bash
################################################################################
# LLM Setup Validation Script
#
# Purpose: Validate LLM configuration for FinLab trading system
# - Check environment variables for API keys
# - Validate config/learning_system.yaml structure
# - Test API connectivity for configured provider
# - Provide clear diagnostic output
#
# Usage: ./scripts/validate_llm_setup.sh [--provider openrouter|gemini|openai]
#
# Exit codes:
#   0 - All checks passed
#   1 - Configuration errors (fixable)
#   2 - API connectivity errors
#   3 - Fatal errors (missing files, etc.)
################################################################################

set -e  # Exit on error (except where explicitly handled)

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONFIG_FILE="${CONFIG_FILE:-config/learning_system.yaml}"
PROVIDER="${1}"
VERBOSE="${VERBOSE:-0}"

# Counters
ERRORS=0
WARNINGS=0
CHECKS_PASSED=0

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo ""
    echo "================================================================================"
    echo -e "${BLUE}$1${NC}"
    echo "================================================================================"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

################################################################################
# Check 1: Prerequisites
################################################################################

check_prerequisites() {
    print_header "Check 1: Prerequisites"

    # Check if config file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        print_info "Expected location: config/learning_system.yaml"
        return 3
    fi
    print_success "Configuration file found: $CONFIG_FILE"

    # Check for required tools
    if ! command -v python3 &> /dev/null; then
        print_error "python3 not found - required for configuration validation"
        return 3
    fi
    print_success "python3 found: $(python3 --version 2>&1)"

    if ! command -v curl &> /dev/null; then
        print_warning "curl not found - API connectivity tests will be skipped"
    else
        print_success "curl found: $(curl --version | head -1)"
    fi

    # Check if PyYAML is available
    if python3 -c "import yaml" 2>/dev/null; then
        print_success "PyYAML library available"
    else
        print_error "PyYAML not installed - required for YAML parsing"
        print_info "Install with: pip3 install pyyaml"
        return 1
    fi
}

################################################################################
# Check 2: Configuration File Structure
################################################################################

check_config_structure() {
    print_header "Check 2: Configuration Structure"

    # Check if llm section exists
    if ! grep -q "^llm:" "$CONFIG_FILE"; then
        print_error "No 'llm:' section found in $CONFIG_FILE"
        print_info "Add LLM configuration section to enable LLM integration"
        return 1
    fi
    print_success "LLM configuration section found"

    # Validate YAML syntax
    if python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>/dev/null; then
        print_success "YAML syntax is valid"
    else
        print_error "YAML syntax error in $CONFIG_FILE"
        python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>&1 | head -5
        return 1
    fi

    # Check for required fields
    local required_fields=("provider" "enabled")
    for field in "${required_fields[@]}"; do
        if grep -A 20 "^llm:" "$CONFIG_FILE" | grep -q "^\s*$field:"; then
            print_success "Required field found: $field"
        else
            print_warning "Optional field missing: $field (will use defaults)"
        fi
    done
}

################################################################################
# Check 3: Provider Configuration
################################################################################

check_provider_config() {
    print_header "Check 3: Provider Configuration"

    # Extract provider from config (if not specified via CLI)
    if [ -z "$PROVIDER" ]; then
        PROVIDER=$(python3 -c "import yaml; config = yaml.safe_load(open('$CONFIG_FILE')); print(config.get('llm', {}).get('provider', 'openrouter'))" 2>/dev/null)
    fi

    print_info "Configured provider: $PROVIDER"

    # Check provider-specific API key
    case "$PROVIDER" in
        openrouter)
            check_api_key "OPENROUTER_API_KEY" "sk-or-"
            ;;
        gemini)
            # Gemini supports both GOOGLE_API_KEY and GEMINI_API_KEY
            if [ -n "$GOOGLE_API_KEY" ] || [ -n "$GEMINI_API_KEY" ]; then
                print_success "Gemini API key found in environment"
                CHECKS_PASSED=$((CHECKS_PASSED + 1))
            else
                print_error "No Gemini API key found"
                print_info "Set GOOGLE_API_KEY or GEMINI_API_KEY environment variable"
                print_info "Example: export GOOGLE_API_KEY='AIza...'"
                return 1
            fi
            ;;
        openai)
            check_api_key "OPENAI_API_KEY" "sk-"
            ;;
        *)
            print_error "Unknown provider: $PROVIDER"
            print_info "Supported providers: openrouter, gemini, openai"
            return 1
            ;;
    esac
}

check_api_key() {
    local var_name="$1"
    local expected_prefix="$2"

    if [ -z "${!var_name}" ]; then
        print_error "$var_name not set"
        print_info "Set environment variable: export $var_name='your-key-here'"
        return 1
    fi

    # Check prefix (without revealing the key)
    if [[ "${!var_name}" == ${expected_prefix}* ]]; then
        print_success "$var_name is set (format looks correct)"
    else
        print_warning "$var_name is set but doesn't match expected format"
        print_info "Expected format: ${expected_prefix}..."
    fi

    # Check length (typical API keys are 40+ chars)
    local key_length=${#!var_name}
    if [ "$key_length" -lt 20 ]; then
        print_warning "$var_name seems too short (${key_length} chars)"
    else
        print_success "$var_name length OK (${key_length} chars)"
    fi
}

################################################################################
# Check 4: Configuration Parameters
################################################################################

check_config_parameters() {
    print_header "Check 4: Configuration Parameters"

    # Extract and validate parameters using Python
    python3 << 'PYTHON_SCRIPT'
import yaml
import sys

try:
    with open('config/learning_system.yaml') as f:
        config = yaml.safe_load(f)

    llm_config = config.get('llm', {})

    # Check if LLM is enabled
    enabled = llm_config.get('enabled', True)
    if not enabled:
        print("\033[1;33m⚠\033[0m LLM integration is DISABLED in configuration")
        print("\033[0;34mℹ\033[0m Set 'llm.enabled: true' to enable")
    else:
        print("\033[0;32m✓\033[0m LLM integration is enabled")

    # Check innovation_rate
    innovation_rate = llm_config.get('innovation_rate', 0.20)
    if 0.0 <= innovation_rate <= 1.0:
        print(f"\033[0;32m✓\033[0m innovation_rate: {innovation_rate} (valid range)")
    else:
        print(f"\033[0;31m✗\033[0m innovation_rate: {innovation_rate} (must be 0.0-1.0)")
        sys.exit(1)

    # Check timeout
    timeout = llm_config.get('timeout', 60)
    if timeout > 0:
        print(f"\033[0;32m✓\033[0m timeout: {timeout}s (valid)")
    else:
        print(f"\033[0;31m✗\033[0m timeout: {timeout} (must be > 0)")
        sys.exit(1)

    # Check max_tokens
    max_tokens = llm_config.get('max_tokens', 2000)
    if max_tokens > 0:
        print(f"\033[0;32m✓\033[0m max_tokens: {max_tokens} (valid)")
    else:
        print(f"\033[0;31m✗\033[0m max_tokens: {max_tokens} (must be > 0)")
        sys.exit(1)

    # Check temperature
    temperature = llm_config.get('temperature', 0.7)
    if 0.0 <= temperature <= 2.0:
        print(f"\033[0;32m✓\033[0m temperature: {temperature} (valid range)")
    else:
        print(f"\033[0;31m✗\033[0m temperature: {temperature} (should be 0.0-2.0)")
        sys.exit(1)

except Exception as e:
    print(f"\033[0;31m✗\033[0m Configuration validation failed: {e}")
    sys.exit(1)
PYTHON_SCRIPT

    if [ $? -eq 0 ]; then
        CHECKS_PASSED=$((CHECKS_PASSED + 5))
    else
        ERRORS=$((ERRORS + 5))
        return 1
    fi
}

################################################################################
# Check 5: API Connectivity (Optional)
################################################################################

test_api_connectivity() {
    print_header "Check 5: API Connectivity (Optional)"

    if ! command -v curl &> /dev/null; then
        print_warning "curl not available - skipping connectivity tests"
        return 0
    fi

    print_info "Testing API connectivity for $PROVIDER..."

    case "$PROVIDER" in
        openrouter)
            test_openrouter_api
            ;;
        gemini)
            test_gemini_api
            ;;
        openai)
            test_openai_api
            ;;
        *)
            print_warning "API connectivity test not implemented for $PROVIDER"
            ;;
    esac
}

test_openrouter_api() {
    if [ -z "$OPENROUTER_API_KEY" ]; then
        print_warning "Skipping API test - OPENROUTER_API_KEY not set"
        return 0
    fi

    # Test OpenRouter API with a minimal request
    local response=$(curl -s -w "\n%{http_code}" -X POST \
        https://openrouter.ai/api/v1/chat/completions \
        -H "Authorization: Bearer $OPENROUTER_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"model":"meta-llama/llama-3.2-1b-instruct:free","messages":[{"role":"user","content":"test"}],"max_tokens":1}' \
        --max-time 10 2>&1)

    local http_code=$(echo "$response" | tail -1)
    local body=$(echo "$response" | head -n -1)

    if [ "$http_code" = "200" ]; then
        print_success "OpenRouter API is accessible and authenticated"
    elif [ "$http_code" = "401" ]; then
        print_error "OpenRouter API authentication failed (401)"
        print_info "Check your OPENROUTER_API_KEY is valid"
    elif [ "$http_code" = "429" ]; then
        print_warning "OpenRouter API rate limit reached (429)"
        print_info "Your API key is valid but quota is exceeded"
    else
        print_warning "OpenRouter API returned status $http_code"
        [ "$VERBOSE" = "1" ] && echo "$body" | head -3
    fi
}

test_gemini_api() {
    local api_key="${GOOGLE_API_KEY:-$GEMINI_API_KEY}"
    if [ -z "$api_key" ]; then
        print_warning "Skipping API test - GOOGLE_API_KEY/GEMINI_API_KEY not set"
        return 0
    fi

    # Test Gemini API
    local response=$(curl -s -w "\n%{http_code}" \
        "https://generativelanguage.googleapis.com/v1/models?key=$api_key" \
        --max-time 10 2>&1)

    local http_code=$(echo "$response" | tail -1)

    if [ "$http_code" = "200" ]; then
        print_success "Gemini API is accessible and authenticated"
    elif [ "$http_code" = "400" ] || [ "$http_code" = "403" ]; then
        print_error "Gemini API authentication failed ($http_code)"
        print_info "Check your GOOGLE_API_KEY/GEMINI_API_KEY is valid"
    else
        print_warning "Gemini API returned status $http_code"
    fi
}

test_openai_api() {
    if [ -z "$OPENAI_API_KEY" ]; then
        print_warning "Skipping API test - OPENAI_API_KEY not set"
        return 0
    fi

    # Test OpenAI API with models endpoint
    local response=$(curl -s -w "\n%{http_code}" \
        https://api.openai.com/v1/models \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        --max-time 10 2>&1)

    local http_code=$(echo "$response" | tail -1)

    if [ "$http_code" = "200" ]; then
        print_success "OpenAI API is accessible and authenticated"
    elif [ "$http_code" = "401" ]; then
        print_error "OpenAI API authentication failed (401)"
        print_info "Check your OPENAI_API_KEY is valid"
    else
        print_warning "OpenAI API returned status $http_code"
    fi
}

################################################################################
# Check 6: Python Integration
################################################################################

check_python_integration() {
    print_header "Check 6: Python Integration"

    # Check if LLM modules can be imported
    if python3 -c "from src.innovation.llm_providers import LLMProviderInterface" 2>/dev/null; then
        print_success "LLM provider module can be imported"
    else
        print_error "Cannot import src.innovation.llm_providers"
        print_info "Ensure the project is properly installed"
        return 1
    fi

    if python3 -c "from src.innovation.llm_config import LLMConfig" 2>/dev/null; then
        print_success "LLM config module can be imported"
    else
        print_error "Cannot import src.innovation.llm_config"
        return 1
    fi

    # Try loading config
    if python3 -c "from src.innovation.llm_config import LLMConfig; LLMConfig.from_yaml('$CONFIG_FILE')" 2>/dev/null; then
        print_success "LLMConfig can load configuration successfully"
    else
        print_error "LLMConfig failed to load configuration"
        print_info "Run manually to see error details:"
        print_info "  python3 -c 'from src.innovation.llm_config import LLMConfig; LLMConfig.from_yaml(\"$CONFIG_FILE\")'"
        return 1
    fi
}

################################################################################
# Summary
################################################################################

print_summary() {
    print_header "Validation Summary"

    echo ""
    echo "Results:"
    echo -e "  ${GREEN}✓${NC} Checks passed: $CHECKS_PASSED"
    echo -e "  ${YELLOW}⚠${NC} Warnings: $WARNINGS"
    echo -e "  ${RED}✗${NC} Errors: $ERRORS"
    echo ""

    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}SUCCESS: LLM setup is valid and ready to use${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"

        if [ $WARNINGS -gt 0 ]; then
            echo ""
            echo -e "${YELLOW}Note: There are $WARNINGS warning(s) that should be reviewed.${NC}"
        fi

        return 0
    else
        echo -e "${RED}═══════════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}FAILED: LLM setup has $ERRORS error(s) that must be fixed${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════════════════════════${NC}"
        echo ""
        echo "Common solutions:"
        echo "  1. Set API key environment variable for your provider"
        echo "  2. Check config/learning_system.yaml syntax and structure"
        echo "  3. Ensure all required Python packages are installed"
        echo "  4. Verify provider name is one of: openrouter, gemini, openai"
        echo ""
        return 1
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                       LLM Setup Validation Script                             ║"
    echo "║                   FinLab Trading System - LLM Integration                     ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════════╝"

    # Run all checks
    check_prerequisites || true
    check_config_structure || true
    check_provider_config || true
    check_config_parameters || true
    test_api_connectivity || true
    check_python_integration || true

    # Print summary and exit with appropriate code
    print_summary
    local exit_code=$?

    echo ""
    exit $exit_code
}

# Run main function
main "$@"
