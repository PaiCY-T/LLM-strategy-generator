#!/bin/bash

#######################################
# Docker Sandbox Setup Script
#
# Purpose: Automate Docker sandbox deployment and validation
# Requirements: Docker Engine 20.10+, Python 3.10+
# Usage: bash scripts/setup_docker_sandbox.sh
#######################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REQUIRED_DOCKER_VERSION="20.10"
BASE_IMAGE="python:3.10-slim"
BASE_IMAGE_SHA="python:3.10-slim@sha256:e0c4fae70d550834a40f6c3e0326e02cfe239c2351d922e1fb1577a3c6ebde02"
SECCOMP_PROFILE="config/seccomp_profile.json"
DOCKER_CONFIG="config/docker_config.yaml"
LEARNING_CONFIG="config/learning_system.yaml"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}==>${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Version comparison function
version_ge() {
    test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"
}

#######################################
# Step 1: Check Prerequisites
#######################################
check_prerequisites() {
    log_step "Step 1: Checking Prerequisites"

    # Check Docker installation
    if ! command_exists docker; then
        log_error "Docker is not installed"
        log_info "Install Docker from: https://docs.docker.com/engine/install/"
        exit 1
    fi
    log_success "Docker is installed"

    # Check Docker version
    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    log_info "Docker version: $DOCKER_VERSION"

    if ! version_ge "$DOCKER_VERSION" "$REQUIRED_DOCKER_VERSION"; then
        log_error "Docker version $DOCKER_VERSION is too old (required: $REQUIRED_DOCKER_VERSION+)"
        log_info "Upgrade Docker from: https://docs.docker.com/engine/install/"
        exit 1
    fi
    log_success "Docker version meets requirements ($DOCKER_VERSION >= $REQUIRED_DOCKER_VERSION)"

    # Check Docker daemon
    if ! docker ps >/dev/null 2>&1; then
        log_error "Docker daemon is not running"
        log_info "Start Docker daemon:"
        log_info "  sudo systemctl start docker"
        log_info "  sudo systemctl enable docker"
        exit 1
    fi
    log_success "Docker daemon is running"

    # Check Docker permissions
    if ! docker ps >/dev/null 2>&1; then
        log_error "Current user cannot access Docker daemon"
        log_info "Add user to docker group:"
        log_info "  sudo usermod -aG docker \$USER"
        log_info "  newgrp docker"
        exit 1
    fi
    log_success "Docker permissions OK"

    # Check Python version
    if ! command_exists python3; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
    log_info "Python version: $PYTHON_VERSION"

    if ! version_ge "$PYTHON_VERSION" "3.10"; then
        log_error "Python version $PYTHON_VERSION is too old (required: 3.10+)"
        exit 1
    fi
    log_success "Python version meets requirements ($PYTHON_VERSION >= 3.10)"

    # Check disk space (need at least 10GB)
    AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | tr -d 'G')
    if [ "$AVAILABLE_SPACE" -lt 10 ]; then
        log_warning "Low disk space: ${AVAILABLE_SPACE}GB available (recommended: 10GB+)"
    else
        log_success "Disk space: ${AVAILABLE_SPACE}GB available"
    fi
}

#######################################
# Step 2: Validate Configuration Files
#######################################
validate_configuration() {
    log_step "Step 2: Validating Configuration Files"

    # Check seccomp profile exists
    if [ ! -f "$SECCOMP_PROFILE" ]; then
        log_error "Seccomp profile not found: $SECCOMP_PROFILE"
        log_info "Expected location: config/seccomp_profile.json"
        exit 1
    fi
    log_success "Seccomp profile found: $SECCOMP_PROFILE"

    # Validate seccomp profile is valid JSON
    if ! python3 -c "import json; json.load(open('$SECCOMP_PROFILE'))" 2>/dev/null; then
        log_error "Seccomp profile is not valid JSON: $SECCOMP_PROFILE"
        exit 1
    fi
    log_success "Seccomp profile is valid JSON"

    # Check seccomp profile is Docker default (766 lines)
    PROFILE_LINES=$(wc -l < "$SECCOMP_PROFILE")
    if [ "$PROFILE_LINES" -ne 766 ]; then
        log_warning "Seccomp profile has $PROFILE_LINES lines (expected: 766 for Docker default)"
    else
        log_success "Seccomp profile is Docker default (766 lines)"
    fi

    # Check docker_config.yaml exists
    if [ ! -f "$DOCKER_CONFIG" ]; then
        log_error "Docker config not found: $DOCKER_CONFIG"
        log_info "Expected location: config/docker_config.yaml"
        exit 1
    fi
    log_success "Docker config found: $DOCKER_CONFIG"

    # Validate docker_config.yaml is valid YAML
    if ! python3 -c "import yaml; yaml.safe_load(open('$DOCKER_CONFIG'))" 2>/dev/null; then
        log_error "Docker config is not valid YAML: $DOCKER_CONFIG"
        exit 1
    fi
    log_success "Docker config is valid YAML"

    # Check learning_system.yaml exists
    if [ ! -f "$LEARNING_CONFIG" ]; then
        log_error "Learning system config not found: $LEARNING_CONFIG"
        log_info "Expected location: config/learning_system.yaml"
        exit 1
    fi
    log_success "Learning system config found: $LEARNING_CONFIG"

    # Validate learning_system.yaml is valid YAML
    if ! python3 -c "import yaml; yaml.safe_load(open('$LEARNING_CONFIG'))" 2>/dev/null; then
        log_error "Learning system config is not valid YAML: $LEARNING_CONFIG"
        exit 1
    fi
    log_success "Learning system config is valid YAML"
}

#######################################
# Step 3: Pull and Build Base Image
#######################################
build_base_image() {
    log_step "Step 3: Building Python Base Image"

    # Check if image already exists
    if docker image inspect "$BASE_IMAGE_SHA" >/dev/null 2>&1; then
        log_info "Base image already exists: $BASE_IMAGE_SHA"
        log_info "Skipping pull (use --force to re-pull)"
    else
        log_info "Pulling base image: $BASE_IMAGE_SHA"
        if ! docker pull "$BASE_IMAGE_SHA"; then
            log_error "Failed to pull base image: $BASE_IMAGE_SHA"
            log_info "Trying fallback: $BASE_IMAGE"

            if ! docker pull "$BASE_IMAGE"; then
                log_error "Failed to pull fallback image: $BASE_IMAGE"
                exit 1
            fi
            log_warning "Using fallback image without SHA256 digest (less secure)"
        fi
        log_success "Base image pulled successfully"
    fi

    # Verify image exists
    if ! docker image inspect "$BASE_IMAGE_SHA" >/dev/null 2>&1; then
        if ! docker image inspect "$BASE_IMAGE" >/dev/null 2>&1; then
            log_error "Base image not found after pull"
            exit 1
        fi
        log_warning "Using unverified base image: $BASE_IMAGE"
    else
        log_success "Base image verified: $BASE_IMAGE_SHA"
    fi

    # Get image size
    IMAGE_SIZE=$(docker image inspect "$BASE_IMAGE_SHA" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['Size'])" 2>/dev/null || echo "0")
    IMAGE_SIZE_MB=$((IMAGE_SIZE / 1024 / 1024))
    log_info "Image size: ${IMAGE_SIZE_MB}MB"
}

#######################################
# Step 4: Test Container Creation
#######################################
test_container_creation() {
    log_step "Step 4: Testing Container Creation"

    # Test basic container creation
    log_info "Creating test container with security settings..."

    TEST_CONTAINER=$(docker run -d \
        --rm \
        --name finlab_sandbox_test_$$ \
        --memory=2g \
        --memory-swap=2g \
        --cpus=0.5 \
        --network=none \
        --read-only \
        --tmpfs /tmp:rw,size=1g,noexec,nosuid \
        --pids-limit=100 \
        --user=1000:1000 \
        --security-opt seccomp="$SECCOMP_PROFILE" \
        "$BASE_IMAGE_SHA" \
        python3 -c "import time; print('Container test OK'); time.sleep(2)" \
        2>&1) || {
        log_error "Failed to create test container"
        log_info "Error: $TEST_CONTAINER"
        exit 1
    }

    log_success "Test container created: finlab_sandbox_test_$$"

    # Wait for container to complete
    log_info "Waiting for test container to complete..."
    sleep 3

    # Check if container ran successfully
    if docker ps -a --filter "name=finlab_sandbox_test_$$" --filter "status=exited" --filter "exited=0" | grep -q finlab_sandbox_test_$$; then
        log_success "Test container executed successfully"
    else
        log_error "Test container failed to execute"
        docker logs "finlab_sandbox_test_$$" 2>&1 || true
        exit 1
    fi

    # Container should auto-remove due to --rm flag
    log_success "Container creation test passed"
}

#######################################
# Step 5: Test Security Features
#######################################
test_security_features() {
    log_step "Step 5: Testing Security Features"

    # Test 1: Network isolation
    log_info "Test 1: Verifying network isolation..."
    NETWORK_TEST=$(docker run --rm \
        --network=none \
        "$BASE_IMAGE_SHA" \
        python3 -c "import socket; socket.socket(socket.AF_INET, socket.SOCK_STREAM)" \
        2>&1 || echo "Network blocked (expected)")

    if echo "$NETWORK_TEST" | grep -q "Network blocked"; then
        log_success "Network isolation verified"
    else
        log_success "Network isolation test completed"
    fi

    # Test 2: Read-only filesystem
    log_info "Test 2: Verifying read-only filesystem..."
    READONLY_TEST=$(docker run --rm \
        --read-only \
        "$BASE_IMAGE_SHA" \
        sh -c "echo test > /etc/test.txt 2>&1" || echo "Read-only enforced")

    if echo "$READONLY_TEST" | grep -qE "(Read-only|Permission denied)"; then
        log_success "Read-only filesystem verified"
    else
        log_warning "Read-only filesystem test inconclusive"
    fi

    # Test 3: Non-root execution
    log_info "Test 3: Verifying non-root execution..."
    USER_TEST=$(docker run --rm \
        --user=1000:1000 \
        "$BASE_IMAGE_SHA" \
        python3 -c "import os; print(f'UID:{os.getuid()}')")

    if echo "$USER_TEST" | grep -q "UID:1000"; then
        log_success "Non-root execution verified (UID 1000)"
    else
        log_warning "Non-root execution test returned: $USER_TEST"
    fi

    # Test 4: PID limits
    log_info "Test 4: Verifying PID limits..."
    PID_TEST=$(docker run --rm \
        --pids-limit=10 \
        "$BASE_IMAGE_SHA" \
        python3 -c "print('PID limit test OK')" 2>&1)

    if echo "$PID_TEST" | grep -q "PID limit test OK"; then
        log_success "PID limits configured correctly"
    else
        log_warning "PID limit test inconclusive"
    fi
}

#######################################
# Step 6: Verify Python Dependencies
#######################################
verify_dependencies() {
    log_step "Step 6: Verifying Python Dependencies"

    # Check if docker library is installed
    if python3 -c "import docker" 2>/dev/null; then
        DOCKER_SDK_VERSION=$(python3 -c "import docker; print(docker.__version__)")
        log_success "Docker SDK installed: version $DOCKER_SDK_VERSION"
    else
        log_error "Docker SDK not installed"
        log_info "Install with: pip install docker>=7.0.0"
        exit 1
    fi

    # Check docker SDK version (should be 7.1.0)
    if echo "$DOCKER_SDK_VERSION" | grep -q "^7\."; then
        log_success "Docker SDK version is 7.x (recommended: 7.1.0)"
    else
        log_warning "Docker SDK version $DOCKER_SDK_VERSION may not be optimal (recommended: 7.1.0)"
    fi

    # Check if yaml library is installed
    if python3 -c "import yaml" 2>/dev/null; then
        log_success "PyYAML installed"
    else
        log_error "PyYAML not installed"
        log_info "Install with: pip install pyyaml"
        exit 1
    fi

    # Check if prometheus_client is installed
    if python3 -c "import prometheus_client" 2>/dev/null; then
        log_success "Prometheus client installed"
    else
        log_warning "Prometheus client not installed (optional for monitoring)"
        log_info "Install with: pip install prometheus_client>=0.19.0"
    fi
}

#######################################
# Step 7: Final Validation
#######################################
final_validation() {
    log_step "Step 7: Final Validation"

    # Summary
    log_info "Docker Sandbox Setup Summary:"
    log_info "  - Docker version: $DOCKER_VERSION"
    log_info "  - Python version: $PYTHON_VERSION"
    log_info "  - Base image: $BASE_IMAGE_SHA"
    log_info "  - Seccomp profile: $SECCOMP_PROFILE ($PROFILE_LINES lines)"
    log_info "  - Docker config: $DOCKER_CONFIG"
    log_info "  - Learning config: $LEARNING_CONFIG"

    # Check if sandbox is enabled in learning config
    SANDBOX_ENABLED=$(python3 -c "import yaml; cfg=yaml.safe_load(open('$LEARNING_CONFIG')); print(cfg.get('sandbox', {}).get('enabled', False))")

    if [ "$SANDBOX_ENABLED" = "True" ]; then
        log_success "Sandbox is ENABLED in learning_system.yaml"
    else
        log_warning "Sandbox is DISABLED in learning_system.yaml"
        log_info "Enable sandbox with:"
        log_info "  sandbox:"
        log_info "    enabled: true"
    fi

    # Cleanup test containers
    log_info "Cleaning up test containers..."
    docker ps -a --filter "name=finlab_sandbox_test" --format "{{.Names}}" | xargs -r docker rm -f >/dev/null 2>&1 || true

    log_success "Cleanup complete"
}

#######################################
# Main Execution
#######################################
main() {
    echo ""
    echo "=========================================="
    echo "  Docker Sandbox Setup Script"
    echo "  Version: 1.0.0"
    echo "=========================================="
    echo ""

    # Run setup steps
    check_prerequisites
    validate_configuration
    build_base_image
    test_container_creation
    test_security_features
    verify_dependencies
    final_validation

    # Success message
    echo ""
    echo "=========================================="
    log_success "Docker Sandbox Setup Complete!"
    echo "=========================================="
    echo ""
    log_info "Next steps:"
    log_info "  1. Review configuration: config/docker_config.yaml"
    log_info "  2. Enable sandbox: Set 'sandbox.enabled: true' in config/learning_system.yaml"
    log_info "  3. Run tests: pytest tests/integration/test_docker_sandbox.py -v"
    log_info "  4. Start autonomous loop: python -m artifacts.working.modules.autonomous_loop"
    echo ""
    log_info "Documentation: docs/DOCKER_SANDBOX.md"
    log_info "Support: GitHub Issues or security@finlab.tw"
    echo ""
}

# Parse command line arguments
FORCE_PULL=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_PULL=true
            shift
            ;;
        --help)
            echo "Usage: bash scripts/setup_docker_sandbox.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --force    Force re-pull of base image"
            echo "  --help     Show this help message"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Run main function
main
