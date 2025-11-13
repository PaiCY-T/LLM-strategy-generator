#!/bin/bash
# create_critical_path_specs.sh
# Created: 2025-10-24
# Purpose: Create 5 new specs for LLM Innovation Critical Path (5-week roadmap)

set -e  # Exit on error

echo "======================================================================"
echo "Creating 5 Specs for LLM Innovation Critical Path"
echo "======================================================================"
echo ""
echo "Based on findings from:"
echo "  - EXECUTIVE_SUMMARY_DEEP_ANALYSIS.md"
echo "  - CRITICAL_BASELINE_REVIEW_O3.md"
echo "  - LLM_INNOVATION_COMPREHENSIVE_REVIEW.md"
echo ""
echo "Timeline: 5 weeks to Task 3.5 readiness"
echo "======================================================================"
echo ""

# Spec 1: Docker Sandbox Security (CRITICAL - Week 1)
echo "1/5: Creating docker-sandbox-security spec (CRITICAL, 8-12 days)..."
npx -y claude-code-spec-workflow create \
  docker-sandbox-security \
  "Implement Docker-based isolated execution environment for LLM-generated code with resource limits (2GB memory, 0.5 CPU), network isolation, read-only filesystem, and security controls (seccomp profiles) to prevent code injection, resource exhaustion, and sandbox escape attacks"

echo "    ✅ docker-sandbox-security created"
echo ""

# Spec 2: Resource Monitoring System (HIGH - Week 1)
echo "2/5: Creating resource-monitoring-system spec (HIGH, 2-3 days)..."
npx -y claude-code-spec-workflow create \
  resource-monitoring-system \
  "Implement comprehensive resource monitoring with Prometheus metrics (memory, CPU, container-level stats), Grafana dashboards, alerting system (memory >80%, diversity <0.1), orphaned process cleanup, and production stability monitoring"

echo "    ✅ resource-monitoring-system created"
echo ""

# Spec 3: LLM Integration Activation (HIGH - Week 2)
echo "3/5: Creating llm-integration-activation spec (HIGH, 1-2 days)..."
npx -y claude-code-spec-workflow create \
  llm-integration-activation \
  "Connect InnovationEngine to iteration loop with 20% innovation rate, API key configuration (OpenRouter/Gemini/OpenAI), feedback loop implementation, prompt engineering for strategy modification vs creation, and fallback to Factor Graph on LLM failure"

echo "    ✅ llm-integration-activation created"
echo ""

# Spec 4: Exit Mutation Redesign (MEDIUM - Week 2-3)
echo "4/5: Creating exit-mutation-redesign spec (MEDIUM, 3-5 days)..."
npx -y claude-code-spec-workflow create \
  exit-mutation-redesign \
  "Redesign exit mutation from AST-based code modification to parameter-based genetic operators that mutate numerical parameters (stop_loss_pct, take_profit_pct, trailing_stop_offset) using Gaussian noise within bounded ranges to fix 0/41 success rate design flaw"

echo "    ✅ exit-mutation-redesign created"
echo ""

# Spec 5: Structured Innovation MVP (MEDIUM - Week 3-4)
echo "5/5: Creating structured-innovation-mvp spec (MEDIUM, 2-3 weeks)..."
npx -y claude-code-spec-workflow create \
  structured-innovation-mvp \
  "Implement YAML/JSON-based structured innovation as Phase 2a, enabling LLM to create novel factor combinations through declarative specifications (schema: indicators, entry_conditions, exit_conditions, position_sizing, risk_management) instead of full code generation, covering 85% of innovation needs with reduced hallucination risk"

echo "    ✅ structured-innovation-mvp created"
echo ""

echo "======================================================================"
echo "✅ All 5 specs created successfully!"
echo "======================================================================"
echo ""
echo "Created specs in .spec-workflow/specs/:"
echo "  1. docker-sandbox-security/          (CRITICAL, Week 1)"
echo "  2. resource-monitoring-system/       (HIGH, Week 1)"
echo "  3. llm-integration-activation/       (HIGH, Week 2)"
echo "  4. exit-mutation-redesign/           (MEDIUM, Week 2-3)"
echo "  5. structured-innovation-mvp/        (MEDIUM, Week 3-4)"
echo ""
echo "Dependencies:"
echo "  - docker-sandbox-security → llm-integration-activation"
echo "  - llm-integration-activation → structured-innovation-mvp"
echo "  - All → Task 3.5 (100-gen LLM test)"
echo ""
echo "Next steps:"
echo "  1. Review each spec's requirements.md and tasks.md"
echo "  2. Update .spec-workflow/specs/llm-innovation-capability/STATUS.md"
echo "  3. Start implementation with docker-sandbox-security (HIGHEST PRIORITY)"
echo "  4. Use CRITICAL_PATH_SPECS_SUMMARY.md for overview"
echo ""
echo "Timeline to Task 3.5 readiness: 5 weeks"
echo "======================================================================"
