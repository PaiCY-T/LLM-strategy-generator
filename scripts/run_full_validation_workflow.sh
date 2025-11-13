#!/bin/bash
#
# Full Validation Workflow Script (Task 6.1)
# ==========================================
#
# Master workflow script that orchestrates all validation steps in one command.
#
# This script automates the complete validation workflow:
#   1. Re-validation (optional) - Execute Phase 2 with statistical validation
#   2. Duplicate Detection - Identify duplicate strategies
#   3. Diversity Analysis - Analyze strategy diversity
#   4. Decision Evaluation - Generate Phase 3 GO/NO-GO decision
#
# Usage:
#   ./scripts/run_full_validation_workflow.sh [options]
#
# Options:
#   --skip-revalidation        Skip re-validation step, use existing results
#   --validation-file <path>   Specify validation results file (required if skipping revalidation)
#   --help                     Show usage information
#
# Exit Codes:
#   0 - GO decision (all steps completed successfully)
#   1 - CONDITIONAL_GO decision (proceed with caution)
#   2 - NO-GO decision (blocking issues found)
#   3+ - Workflow error (step failure, missing files, etc.)
#
# Author: AI Assistant
# Date: 2025-11-03
# Version: 1.0

set -e  # Exit on error
set -o pipefail  # Catch errors in pipes

# ========================================
# Configuration
# ========================================

# Project root (absolute path)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Timestamp for workflow run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Log file for workflow
LOG_FILE="${PROJECT_ROOT}/validation_workflow_${TIMESTAMP}.log"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ========================================
# Functions
# ========================================

# Logging function
log() {
    local timestamp=$(date +"%H:%M:%S")
    echo -e "[${timestamp}] $*" | tee -a "$LOG_FILE"
}

# Error logging function
log_error() {
    local timestamp=$(date +"%H:%M:%S")
    echo -e "${RED}[${timestamp}] ERROR: $*${NC}" | tee -a "$LOG_FILE"
}

# Success logging function
log_success() {
    local timestamp=$(date +"%H:%M:%S")
    echo -e "${GREEN}[${timestamp}] ✓ $*${NC}" | tee -a "$LOG_FILE"
}

# Warning logging function
log_warning() {
    local timestamp=$(date +"%H:%M:%S")
    echo -e "${YELLOW}[${timestamp}] ⚠ $*${NC}" | tee -a "$LOG_FILE"
}

# Info logging function
log_info() {
    local timestamp=$(date +"%H:%M:%S")
    echo -e "${BLUE}[${timestamp}] ℹ $*${NC}" | tee -a "$LOG_FILE"
}

# Check if file exists
check_file() {
    local file_path="$1"
    local description="$2"

    if [ ! -f "$file_path" ]; then
        log_error "$description not found: $file_path"
        return 1
    fi

    log "Found $description: $(basename "$file_path")"
    return 0
}

# Check if command exists
check_command() {
    local cmd="$1"

    if ! command -v "$cmd" &> /dev/null; then
        log_error "Required command not found: $cmd"
        return 1
    fi

    return 0
}

# Run a workflow step
run_step() {
    local step_num="$1"
    local total_steps="$2"
    local step_name="$3"
    shift 3
    local cmd="$@"

    log ""
    log "========================================"
    log "Step $step_num/$total_steps: $step_name"
    log "========================================"
    log "Command: $cmd"
    log ""

    # Run command and capture exit code
    if eval "$cmd" 2>&1 | tee -a "$LOG_FILE"; then
        log_success "Step $step_num/$total_steps completed: $step_name"
        return 0
    else
        local exit_code=$?
        log_error "Step $step_num/$total_steps failed: $step_name (exit code: $exit_code)"
        return $exit_code
    fi
}

# Find latest validation results file
find_latest_validation_file() {
    local pattern="${PROJECT_ROOT}/phase2_validated_results_*.json"
    local latest_file=$(ls -t $pattern 2>/dev/null | head -1)

    if [ -z "$latest_file" ]; then
        log_error "No validation results files found matching pattern: phase2_validated_results_*.json"
        return 1
    fi

    echo "$latest_file"
    return 0
}

# Show usage information
show_usage() {
    cat << EOF
${BOLD}Full Validation Workflow Script (Task 6.1)${NC}

${BOLD}Usage:${NC}
  $0 [options]

${BOLD}Options:${NC}
  --skip-revalidation        Skip re-validation step, use existing results
  --validation-file <path>   Specify validation results file (required if skipping)
  --help                     Show this help message

${BOLD}Description:${NC}
  This script orchestrates the complete validation workflow:
    1. Re-validation (optional) - Execute Phase 2 with statistical validation
    2. Duplicate Detection - Identify duplicate strategies
    3. Diversity Analysis - Analyze strategy diversity
    4. Decision Evaluation - Generate Phase 3 GO/NO-GO decision

${BOLD}Exit Codes:${NC}
  0 - GO decision (system ready for Phase 3)
  1 - CONDITIONAL_GO decision (proceed with caution)
  2 - NO-GO decision (blocking issues found)
  3+ - Workflow error (step failure, missing files, etc.)

${BOLD}Examples:${NC}
  # Run full workflow including re-validation
  $0

  # Skip re-validation, use existing results
  $0 --skip-revalidation

  # Use specific validation results file
  $0 --skip-revalidation --validation-file phase2_validated_results_20251101_132244.json

${BOLD}Output Files:${NC}
  - validation_workflow_TIMESTAMP.log      Workflow execution log
  - phase2_validated_results_TIMESTAMP.json   Validation results (if re-validated)
  - duplicate_report.json                  Duplicate detection JSON report
  - duplicate_report.md                    Duplicate detection Markdown report
  - diversity_report.json                  Diversity analysis JSON report
  - diversity_report.md                    Diversity analysis Markdown report
  - diversity_report_correlation_heatmap.png   Correlation heatmap
  - diversity_report_factor_usage.png      Factor usage chart
  - phase3_decision_report.md              Final GO/NO-GO decision document

EOF
}

# ========================================
# Argument Parsing
# ========================================

SKIP_REVALIDATION=false
VALIDATION_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-revalidation)
            SKIP_REVALIDATION=true
            shift
            ;;
        --validation-file)
            VALIDATION_FILE="$2"
            shift 2
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 10
            ;;
    esac
done

# ========================================
# Pre-flight Checks
# ========================================

log "========================================="
log "Full Validation Workflow"
log "========================================="
log "Timestamp: $TIMESTAMP"
log "Project Root: $PROJECT_ROOT"
log "Log File: $LOG_FILE"
log ""

# Check required commands
log "Checking prerequisites..."

if ! check_command "python3"; then
    exit 11
fi

# Check Python packages (basic check)
if ! python3 -c "import numpy, pandas, finlab" 2>/dev/null; then
    log_warning "Some Python packages may be missing. Workflow may fail."
fi

# Verify project structure
if [ ! -d "${PROJECT_ROOT}/scripts" ]; then
    log_error "Scripts directory not found: ${PROJECT_ROOT}/scripts"
    exit 12
fi

# Check validation file logic
if [ "$SKIP_REVALIDATION" = true ]; then
    log "Re-validation will be skipped"

    # If validation file specified, check it exists
    if [ -n "$VALIDATION_FILE" ]; then
        # Convert to absolute path if relative
        if [[ "$VALIDATION_FILE" != /* ]]; then
            VALIDATION_FILE="${PROJECT_ROOT}/${VALIDATION_FILE}"
        fi

        if ! check_file "$VALIDATION_FILE" "Specified validation results"; then
            exit 13
        fi
    else
        # Try to find latest validation file
        log "No validation file specified, searching for latest..."
        VALIDATION_FILE=$(find_latest_validation_file)
        if [ $? -ne 0 ]; then
            log_error "No validation file found. Please specify with --validation-file or run without --skip-revalidation"
            exit 14
        fi
        log_info "Using latest validation file: $(basename "$VALIDATION_FILE")"
    fi
else
    log "Re-validation will be performed"
fi

# Check that required scripts exist
if ! check_file "${PROJECT_ROOT}/scripts/detect_duplicates.py" "Duplicate detection script"; then
    exit 15
fi

if ! check_file "${PROJECT_ROOT}/scripts/analyze_diversity.py" "Diversity analysis script"; then
    exit 16
fi

if ! check_file "${PROJECT_ROOT}/scripts/evaluate_phase3_decision.py" "Decision evaluation script"; then
    exit 17
fi

if [ "$SKIP_REVALIDATION" = false ]; then
    if ! check_file "${PROJECT_ROOT}/run_phase2_with_validation.py" "Phase 2 validation script"; then
        exit 18
    fi
fi

log_success "Prerequisites check passed"
log ""

# ========================================
# Main Workflow
# ========================================

TOTAL_STEPS=4
CURRENT_STEP=0

# Change to project root
cd "$PROJECT_ROOT"

# ========================================
# Step 1: Re-validation (optional)
# ========================================

if [ "$SKIP_REVALIDATION" = false ]; then
    CURRENT_STEP=$((CURRENT_STEP + 1))

    if ! run_step "$CURRENT_STEP" "$TOTAL_STEPS" "Re-validation" \
        "python3 run_phase2_with_validation.py --save-results"; then
        log_error "Re-validation failed. Aborting workflow."
        exit 20
    fi

    # Find the newly created validation results file
    VALIDATION_FILE=$(find_latest_validation_file)
    if [ $? -ne 0 ]; then
        log_error "Could not find newly created validation results file"
        exit 21
    fi

    log_info "Using validation results: $(basename "$VALIDATION_FILE")"
else
    log_info "Skipping re-validation step (using existing results)"
fi

# ========================================
# Step 2: Duplicate Detection
# ========================================

CURRENT_STEP=$((CURRENT_STEP + 1))

DUPLICATE_REPORT_JSON="${PROJECT_ROOT}/duplicate_report.json"
DUPLICATE_REPORT_MD="${PROJECT_ROOT}/duplicate_report.md"

if ! run_step "$CURRENT_STEP" "$TOTAL_STEPS" "Duplicate Detection" \
    "python3 scripts/detect_duplicates.py \
        --validation-results \"$VALIDATION_FILE\" \
        --strategy-dir . \
        --output \"$DUPLICATE_REPORT_MD\""; then
    log_error "Duplicate detection failed. Aborting workflow."
    exit 30
fi

# Verify outputs were created
if ! check_file "$DUPLICATE_REPORT_JSON" "Duplicate report JSON"; then
    log_error "Duplicate report JSON was not generated"
    exit 31
fi

if ! check_file "$DUPLICATE_REPORT_MD" "Duplicate report Markdown"; then
    log_error "Duplicate report Markdown was not generated"
    exit 32
fi

# ========================================
# Step 3: Diversity Analysis
# ========================================

CURRENT_STEP=$((CURRENT_STEP + 1))

DIVERSITY_REPORT_JSON="${PROJECT_ROOT}/diversity_report.json"
DIVERSITY_REPORT_MD="${PROJECT_ROOT}/diversity_report.md"

if ! run_step "$CURRENT_STEP" "$TOTAL_STEPS" "Diversity Analysis" \
    "python3 scripts/analyze_diversity.py \
        --validation-results \"$VALIDATION_FILE\" \
        --duplicate-report \"$DUPLICATE_REPORT_JSON\" \
        --strategy-dir . \
        --output \"$DIVERSITY_REPORT_MD\""; then
    log_error "Diversity analysis failed. Aborting workflow."
    exit 40
fi

# Verify outputs were created
if ! check_file "$DIVERSITY_REPORT_JSON" "Diversity report JSON"; then
    log_error "Diversity report JSON was not generated"
    exit 41
fi

if ! check_file "$DIVERSITY_REPORT_MD" "Diversity report Markdown"; then
    log_error "Diversity report Markdown was not generated"
    exit 42
fi

# ========================================
# Step 4: Decision Evaluation
# ========================================

CURRENT_STEP=$((CURRENT_STEP + 1))

DECISION_REPORT_MD="${PROJECT_ROOT}/phase3_decision_report.md"

if ! run_step "$CURRENT_STEP" "$TOTAL_STEPS" "Decision Evaluation" \
    "python3 scripts/evaluate_phase3_decision.py \
        --validation-results \"$VALIDATION_FILE\" \
        --duplicate-report \"$DUPLICATE_REPORT_JSON\" \
        --diversity-report \"$DIVERSITY_REPORT_JSON\" \
        --output \"$DECISION_REPORT_MD\""; then

    # Capture exit code from decision script
    DECISION_EXIT_CODE=$?

    log_warning "Decision evaluation completed with exit code: $DECISION_EXIT_CODE"

    # Verify decision report was created
    if ! check_file "$DECISION_REPORT_MD" "Decision report"; then
        log_error "Decision report was not generated"
        exit 50
    fi

    # Parse decision from report
    DECISION=$(grep -m 1 "^\*\*Decision\*\*:" "$DECISION_REPORT_MD" | sed 's/.*\*\*\(.*\)\*\*.*/\1/' | xargs)

    log ""
    log "========================================="
    log "Workflow Summary"
    log "========================================="
    log ""
    log "Final Decision: $DECISION"
    log ""
    log "Generated Reports:"
    log "  - Validation Results: $(basename "$VALIDATION_FILE")"
    log "  - Duplicate Report (JSON): duplicate_report.json"
    log "  - Duplicate Report (MD): duplicate_report.md"
    log "  - Diversity Report (JSON): diversity_report.json"
    log "  - Diversity Report (MD): diversity_report.md"
    log "  - Decision Report: phase3_decision_report.md"
    log ""
    log "Workflow Log: $LOG_FILE"
    log ""
    log "========================================="

    # Return appropriate exit code based on decision
    case "$DECISION" in
        "GO")
            log_success "Workflow complete: GO decision"
            exit 0
            ;;
        "CONDITIONAL_GO"|"CONDITIONAL GO")
            log_warning "Workflow complete: CONDITIONAL_GO decision"
            exit 1
            ;;
        "NO-GO"|"NO GO")
            log_error "Workflow complete: NO-GO decision"
            exit 2
            ;;
        *)
            log_warning "Workflow complete: Unknown decision ($DECISION)"
            exit $DECISION_EXIT_CODE
            ;;
    esac
fi

# If we reach here, decision evaluation succeeded with exit code 0
if ! check_file "$DECISION_REPORT_MD" "Decision report"; then
    log_error "Decision report was not generated"
    exit 51
fi

# ========================================
# Final Summary
# ========================================

log ""
log "========================================="
log "Workflow Complete!"
log "========================================="
log ""

# Extract key metrics from reports
if [ -f "$DIVERSITY_REPORT_JSON" ]; then
    DIVERSITY_SCORE=$(python3 -c "import json; print(json.load(open('$DIVERSITY_REPORT_JSON'))['diversity_score'])" 2>/dev/null || echo "N/A")
    TOTAL_STRATEGIES=$(python3 -c "import json; print(json.load(open('$DIVERSITY_REPORT_JSON'))['total_strategies'])" 2>/dev/null || echo "N/A")
fi

if [ -f "$DUPLICATE_REPORT_JSON" ]; then
    DUPLICATE_GROUPS=$(python3 -c "import json; print(len(json.load(open('$DUPLICATE_REPORT_JSON'))['duplicate_groups']))" 2>/dev/null || echo "N/A")
fi

DECISION=$(grep -m 1 "^\*\*Decision\*\*:" "$DECISION_REPORT_MD" | sed 's/.*\*\*\(.*\)\*\*.*/\1/' | xargs 2>/dev/null || echo "UNKNOWN")

log "Key Metrics:"
log "  - Total Strategies: $TOTAL_STRATEGIES"
log "  - Duplicate Groups: $DUPLICATE_GROUPS"
log "  - Diversity Score: $DIVERSITY_SCORE"
log "  - Final Decision: $DECISION"
log ""
log "Generated Reports:"
log "  - Validation Results: $(basename "$VALIDATION_FILE")"
log "  - Duplicate Report (JSON): duplicate_report.json"
log "  - Duplicate Report (MD): duplicate_report.md"
log "  - Diversity Report (JSON): diversity_report.json"
log "  - Diversity Report (MD): diversity_report.md"
if [ -f "${PROJECT_ROOT}/diversity_report_correlation_heatmap.png" ]; then
    log "  - Correlation Heatmap: diversity_report_correlation_heatmap.png"
fi
if [ -f "${PROJECT_ROOT}/diversity_report_factor_usage.png" ]; then
    log "  - Factor Usage Chart: diversity_report_factor_usage.png"
fi
log "  - Decision Report: phase3_decision_report.md"
log ""
log "Workflow Log: $LOG_FILE"
log ""

# Determine final exit code based on decision
case "$DECISION" in
    "GO")
        log_success "System ready for Phase 3!"
        log ""
        log "========================================="
        exit 0
        ;;
    "CONDITIONAL_GO"|"CONDITIONAL GO")
        log_warning "System meets minimal criteria for Phase 3 (with mitigation)"
        log "Review decision report for mitigation strategies"
        log ""
        log "========================================="
        exit 1
        ;;
    "NO-GO"|"NO GO")
        log_error "System not ready for Phase 3"
        log "Review decision report for blocking issues"
        log ""
        log "========================================="
        exit 2
        ;;
    *)
        log_warning "Unknown decision: $DECISION"
        log ""
        log "========================================="
        exit 60
        ;;
esac
