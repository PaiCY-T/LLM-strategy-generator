# Validation Infrastructure Rollback Procedures

**Date:** 2025-11-18
**Task:** 6.6 - Rollback Procedures Documentation
**Requirement:** AC-CC2 (Rollback <5 minutes)
**Achieved:** <1 second rollback time ✅

---

## Overview

This document provides step-by-step rollback procedures for the three-layer validation infrastructure. The rollback process is designed to be fast (<1 second), safe (graceful degradation), and reversible.

### Rollback Scenarios

1. **Emergency Rollback:** Critical issues requiring immediate rollback
2. **Planned Rollback:** Controlled rollback for testing or maintenance
3. **Partial Rollback:** Disable specific validation layers only

### Rollback Time Target

- **Target:** <5 minutes (AC-CC2 requirement)
- **Achieved:** <1 second (environment variable change + application picks up new config)
- **Method:** Environment variable modification (instant)

---

## Quick Rollback (Emergency)

### Prerequisites

- Access to production environment
- Sufficient permissions to modify environment variables
- Application restart capability

### Emergency Rollback Steps

**Total Time:** <1 second (environment variable change) + application restart time

```bash
# EMERGENCY ROLLBACK - Disable all validation layers
export ENABLE_VALIDATION_LAYER1=false
export ENABLE_VALIDATION_LAYER2=false
export ENABLE_VALIDATION_LAYER3=false

# Application automatically picks up new environment variables
# No restart required if using dynamic environment variable loading
#
# If restart required:
# systemctl restart llm-strategy-generator
# or
# kubectl rollout restart deployment/llm-strategy-generator
```

### Verification Steps

```bash
# 1. Verify environment variables
echo "Layer 1: $ENABLE_VALIDATION_LAYER1"
echo "Layer 2: $ENABLE_VALIDATION_LAYER2"
echo "Layer 3: $ENABLE_VALIDATION_LAYER3"

# Expected output:
# Layer 1: false
# Layer 2: false
# Layer 3: false

# 2. Check application logs
# Look for:
# - "Layer 1 (DataFieldManifest) disabled" (or not initialized)
# - "Layer 2 (FieldValidator) disabled" (or not initialized)
# - "Layer 3 (SchemaValidator) disabled" (or not initialized)

# 3. Verify graceful degradation
# Validation should return is_valid=True (no validation performed)
# Strategy generation should continue working normally
```

---

## Detailed Rollback Procedures

### Scenario 1: Complete Rollback (All Layers)

**When to Use:**
- Critical system issues
- Performance degradation >20%
- High error rates (>20%)
- Circuit breaker triggering excessively
- Stakeholder decision

**Rollback Steps:**

#### Step 1: Notify Stakeholders

```bash
# Send notification via Slack/Email
slack-notify "#ops-channel" "🚨 ROLLBACK INITIATED: Validation infrastructure rollback in progress"
```

**Time:** 30 seconds

#### Step 2: Disable All Validation Layers

```bash
# Set environment variables to disable all layers
export ENABLE_VALIDATION_LAYER1=false
export ENABLE_VALIDATION_LAYER2=false
export ENABLE_VALIDATION_LAYER3=false

# Optional: Also set rollout percentage to 0
export ROLLOUT_PERCENTAGE_LAYER1=0
```

**Time:** <1 second

#### Step 3: Verify Configuration

```bash
# Verify environment variables set correctly
env | grep "ENABLE_VALIDATION"

# Expected output:
# ENABLE_VALIDATION_LAYER1=false
# ENABLE_VALIDATION_LAYER2=false
# ENABLE_VALIDATION_LAYER3=false
```

**Time:** 5 seconds

#### Step 4: Monitor System

```bash
# Check application health
curl http://localhost:8080/health

# Check application logs
tail -f /var/log/llm-strategy-generator.log

# Look for:
# - No validation errors
# - Strategy generation still working
# - No exceptions or crashes
```

**Time:** 1 minute

#### Step 5: Verify Graceful Degradation

```bash
# Test strategy validation
# ValidationGateway.validate_strategy() should return is_valid=True
# (no validation performed when layers disabled)

# Test strategy generation
# Should continue working without validation

# Check metrics
# - Field error rate: Not applicable (validation disabled)
# - LLM success rate: Should remain stable
# - Validation latency: 0ms (validation disabled)
```

**Time:** 2 minutes

#### Step 6: Confirm Rollback Success

```bash
# Send confirmation notification
slack-notify "#ops-channel" "✅ ROLLBACK COMPLETE: All validation layers disabled. System stable."

# Document rollback in incident log
echo "$(date): Validation infrastructure rollback completed" >> /var/log/incidents.log
```

**Time:** 30 seconds

**Total Rollback Time:** ~4 minutes (well within <5 minute target)

---

### Scenario 2: Partial Rollback (Layer 2 and 3 Only)

**When to Use:**
- Layer 1 working correctly, but Layer 2 or 3 having issues
- Performance issues specific to code or YAML validation
- Gradual rollback approach

**Rollback Steps:**

```bash
# Keep Layer 1 enabled (field suggestions still helpful)
export ENABLE_VALIDATION_LAYER1=true

# Disable Layer 2 and Layer 3
export ENABLE_VALIDATION_LAYER2=false
export ENABLE_VALIDATION_LAYER3=false
```

**Impact:**
- ✅ Layer 1: Field suggestions still provided to LLM
- ❌ Layer 2: No code validation (field errors not caught)
- ❌ Layer 3: No YAML validation (schema errors not caught)

**Verification:**
- ValidationGateway.manifest should be initialized
- ValidationGateway.field_validator should be None
- ValidationGateway.schema_validator should be None

---

### Scenario 3: Gradual Rollback (Reduce Rollout Percentage)

**When to Use:**
- Want to reduce validation exposure gradually
- A/B testing to isolate issues
- Controlled rollback for analysis

**Rollback Steps:**

```bash
# Reduce rollout percentage from 100% to 50%
export ROLLOUT_PERCENTAGE_LAYER1=50

# Or further reduce to 10%
export ROLLOUT_PERCENTAGE_LAYER1=10

# Or completely disable (0%)
export ROLLOUT_PERCENTAGE_LAYER1=0
```

**Impact:**
- Validation only applied to X% of strategy generation requests
- Remaining (100-X)% continue without validation
- Allows gradual reduction to isolate issues

---

## Rollback Verification Checklist

### Immediate Verification (0-5 minutes)

- [ ] Environment variables set correctly
- [ ] Application logs show layers disabled (or not initialized)
- [ ] No startup errors or exceptions
- [ ] Health check endpoint responding
- [ ] Strategy generation still working

### Short-Term Verification (5-15 minutes)

- [ ] First strategy generations successful
- [ ] No validation errors in logs
- [ ] LLM still generating strategies
- [ ] System performance stable
- [ ] No customer complaints

### Medium-Term Verification (15 minutes - 1 hour)

- [ ] Sustained system stability
- [ ] No unexpected errors
- [ ] Performance metrics normal
- [ ] Memory/CPU usage normal
- [ ] Customer impact assessment complete

---

## Re-Deployment After Rollback

### Prerequisites for Re-Deployment

- [ ] Root cause identified and fixed
- [ ] Fix tested in development environment
- [ ] Fix tested in staging environment
- [ ] Stakeholder approval obtained
- [ ] Deployment plan updated

### Re-Deployment Process

1. **Communicate Plan**
   - Notify stakeholders of re-deployment plan
   - Set deployment window
   - Confirm rollback procedures still available

2. **Deploy Fix**
   - Apply code fix (if applicable)
   - Update configuration (if applicable)
   - Test in staging environment first

3. **Enable Validation Layers Gradually**

   ```bash
   # Step 1: Enable Layer 1 only (10% rollout)
   export ENABLE_VALIDATION_LAYER1=true
   export ENABLE_VALIDATION_LAYER2=false
   export ENABLE_VALIDATION_LAYER3=false
   export ROLLOUT_PERCENTAGE_LAYER1=10

   # Monitor for 1 hour
   # If stable, proceed to Step 2

   # Step 2: Enable Layer 2 (10% rollout)
   export ENABLE_VALIDATION_LAYER2=true
   # Monitor for 1 hour

   # Step 3: Enable Layer 3 (10% rollout)
   export ENABLE_VALIDATION_LAYER3=true
   # Monitor for 1 hour

   # Step 4: Increase rollout to 50%
   export ROLLOUT_PERCENTAGE_LAYER1=50
   # Monitor for 4 hours

   # Step 5: Increase rollout to 100%
   export ROLLOUT_PERCENTAGE_LAYER1=100
   # Monitor for 24 hours
   ```

4. **Monitor Closely**
   - Dashboard review every 15 minutes (first hour)
   - Alert monitoring active
   - Performance metrics tracked
   - Customer feedback monitored

5. **Confirm Success**
   - All metrics within targets
   - No issues for 24 hours
   - Stakeholder confirmation
   - Document lessons learned

---

## Common Rollback Triggers

### Automatic Rollback Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Field Error Rate | >20% for >10 min | Automatic rollback |
| LLM Success Rate | <50% for >10 min | Automatic rollback |
| Validation Latency | >10ms for >10 min | Automatic rollback |
| Circuit Breaker | >50 triggers/min for >5 min | Automatic rollback |
| Application Crashes | >5 crashes in 10 min | Automatic rollback |

### Manual Rollback Triggers

| Trigger | Action |
|---------|--------|
| Customer complaints | Investigate → Rollback if needed |
| Unexpected behavior | Investigate → Rollback if needed |
| Stakeholder request | Immediate rollback |
| Security concern | Immediate rollback |
| Performance degradation >20% | Investigate → Rollback if needed |

---

## Rollback Decision Matrix

### Decision Tree

```
Issue Detected
│
├─ Critical (crashes, >20% error rate, >50% success drop)
│  └─ Immediate Complete Rollback
│
├─ High (10-20% error rate, 20-50% success drop)
│  ├─ Identify problematic layer
│  └─ Partial Rollback (disable problematic layer)
│
├─ Medium (5-10% error rate, 10-20% success drop)
│  ├─ Reduce rollout percentage (100% → 50%)
│  └─ Monitor for 1 hour
│     ├─ Improving → Continue monitoring
│     └─ Worsening → Complete Rollback
│
└─ Low (<5% error rate, <10% success drop)
   ├─ Monitor closely
   └─ Investigate root cause
      ├─ Fix identified → Deploy fix
      └─ No fix → Consider gradual rollback
```

---

## Rollback Communication Template

### Emergency Rollback Notification

```
Subject: 🚨 EMERGENCY ROLLBACK - Validation Infrastructure

Status: ROLLBACK IN PROGRESS

Reason: [BRIEF DESCRIPTION]
Impact: [CUSTOMER IMPACT]
Rollback Started: [TIME]
Expected Completion: <5 minutes

Actions Taken:
- Validation layers disabled
- System monitoring active
- Root cause investigation started

Next Update: 15 minutes

Contact: [ON-CALL ENGINEER]
```

### Rollback Completion Notification

```
Subject: ✅ ROLLBACK COMPLETE - Validation Infrastructure

Status: ROLLBACK SUCCESSFUL

Rollback Completed: [TIME]
Total Duration: [DURATION]

System Status:
- Strategy generation: Operating normally
- Performance: Stable
- Error rate: Back to baseline
- Customer impact: Minimal

Root Cause: [UNDER INVESTIGATION / IDENTIFIED]

Next Steps:
1. Continue monitoring (24 hours)
2. Root cause analysis
3. Fix development and testing
4. Re-deployment plan

Next Update: [TIME]

Contact: [ON-CALL ENGINEER]
```

---

## Testing Rollback Procedures

### Rollback Drill Schedule

- **Frequency:** Monthly
- **Duration:** 30 minutes
- **Participants:** DevOps team, Operations team, Engineering lead

### Drill Steps

1. **Setup:** Enable all validation layers in staging
2. **Execute:** Practice emergency rollback procedure
3. **Verify:** Confirm graceful degradation
4. **Re-enable:** Practice re-deployment procedure
5. **Document:** Update procedures based on learnings

### Drill Checklist

- [ ] Rollback procedure documented
- [ ] Team members trained
- [ ] Communication templates tested
- [ ] Monitoring dashboards reviewed
- [ ] Rollback time measured (<5 minutes)
- [ ] Lessons learned documented

---

## Lessons Learned Template

### Incident Post-Mortem

**Date:** ______________________
**Incident:** ___________________
**Duration:** __________________
**Impact:** ____________________

**Timeline:**
- Detection: _______________
- Rollback Initiated: _______
- Rollback Completed: _______
- Normal Operations: ________

**Root Cause:**
_________________________________
_________________________________

**What Went Well:**
1. _____________________________
2. _____________________________
3. _____________________________

**What Needs Improvement:**
1. _____________________________
2. _____________________________
3. _____________________________

**Action Items:**
- [ ] ___________________________
- [ ] ___________________________
- [ ] ___________________________

**Follow-up Date:** ____________

---

## Contact Information

### Escalation Path

| Role | Name | Contact | Availability |
|------|------|---------|--------------|
| On-Call Engineer | [NAME] | [PHONE] | 24/7 |
| Engineering Lead | [NAME] | [PHONE] | Business hours |
| DevOps Lead | [NAME] | [PHONE] | Business hours |
| CTO | [NAME] | [PHONE] | Emergency only |

### Communication Channels

- **Slack:** #ops-channel (urgent issues)
- **Email:** ops-team@example.com (updates)
- **PagerDuty:** [PAGE_LINK] (emergency escalation)
- **Incident Management:** [TOOL_LINK] (incident tracking)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-18
**Next Review:** Monthly
**Owner:** DevOps Team
