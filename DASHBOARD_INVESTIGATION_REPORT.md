# Dashboard Investigation Report

**Date**: 2025-10-28
**Issue**: Dashboard localhost refusing connection
**Status**: ⚠️ **ISSUE IDENTIFIED**

---

## Problem Summary

User reports: "dashboard local host拒絕連線" (dashboard localhost refuses connection)

### Investigation Results

**Spec Workflow MCP Server**: ✅ RUNNING
```
Process: node spec-workflow-mcp --AutoStartDashboard --port 3456
PID: 21263
Status: Running since Oct 27
```

**Dashboard Port (3456)**: ❌ NOT LISTENING
```
Port scan result: Port 3456 not listening
HTTP test: Connection refused
```

---

## Root Cause Analysis

### Issue 1: Dashboard Failed to Start

**Evidence**:
- MCP server process is running
- `--AutoStartDashboard` flag is present
- Port 3456 is specified but not bound
- No HTTP response from localhost:3456

**Likely Causes**:
1. Dashboard initialization failed silently
2. Port conflict (unlikely - port is free)
3. Dashboard dependencies missing
4. Configuration error in spec-workflow package

### Issue 2: Dashboard Type Unclear

**Current State**:
- Only found: `config/grafana_dashboard.json` (Grafana config)
- Test file: `tests/integration/test_grafana_dashboard.py`
- No spec-workflow dashboard files in project

**Clarification Needed**:
- Is user expecting spec-workflow dashboard?
- Is user expecting Grafana dashboard?
- Different dashboards serve different purposes

---

## Dashboard Types in System

### 1. Spec Workflow Dashboard (MCP)

**Purpose**: View spec requirements, design, tasks progress
**Location**: Provided by @pimzino/spec-workflow-mcp package
**Port**: 3456 (configured)
**Status**: ❌ FAILED TO START

**Expected Features**:
- Spec list and status
- Task completion tracking
- Requirements/design viewing
- Approval workflow

### 2. Grafana Dashboard (Monitoring)

**Purpose**: Monitor learning system metrics
**Configuration**: `config/grafana_dashboard.json`
**Status**: ⚠️ NOT CONFIGURED

**Expected Features**:
- Sharpe ratio trends
- Champion update tracking
- Iteration success rates
- Template usage analytics

---

## Recommendations

### Immediate Actions

#### Option 1: Restart MCP Server (Recommended)

If user needs spec-workflow dashboard:

```bash
# Stop current MCP server (find PID)
kill 21263

# Restart Claude Code session
# MCP server will auto-restart with dashboard
```

**Expected Outcome**: Dashboard should start on port 3456

#### Option 2: Access Dashboard Directly

If dashboard is actually running on different port:

```bash
# Check all listening ports
ss -tuln | grep LISTEN

# Try common ports
curl http://localhost:3000
curl http://localhost:8000
curl http://localhost:5000
```

#### Option 3: Manual Dashboard Launch

If MCP dashboard can be launched separately:

```bash
# Navigate to dashboard directory (if exists)
cd .spec-workflow/dashboard/

# Launch dashboard manually
npm run dev  # or similar command
```

### Long-Term Solutions

#### 1. Setup Grafana Dashboard (For Metrics)

**Purpose**: Monitor learning system performance

**Steps**:
```bash
# Install Grafana (Docker)
docker run -d -p 3000:3000 grafana/grafana

# Import dashboard config
# Upload config/grafana_dashboard.json to Grafana UI

# Configure Prometheus data source
# Point to metrics endpoint
```

**Metrics Available**:
- Iteration history (iteration_history.jsonl)
- Champion tracking (hall_of_fame/)
- Template analytics (template_analytics.json)

#### 2. Verify Spec Workflow Dashboard

**Check MCP Server Logs**:

```bash
# Find MCP server process
ps aux | grep spec-workflow-mcp

# Check if dashboard started
# (Need to access MCP server logs - location TBD)
```

**Verify Package Version**:
```bash
npm list @pimzino/spec-workflow-mcp
```

#### 3. Alternative: CLI-Based Monitoring

**Current Working Solution**:

```bash
# View spec status via MCP tool
# (Already working - spec status shows in Claude Code)

# View metrics via CLI
python scripts/analyze_metrics.py

# View iteration history
tail -f iteration_history.jsonl | jq .

# View champion
cat hall_of_fame/champion.json | jq .
```

---

## Current Workarounds

### View Spec Progress (Working ✅)

Use MCP tool in Claude Code:

```
User: "Check spec status for exit-mutation-redesign"
Claude: Uses mcp__spec-workflow__spec-status tool
```

**Output**:
- Requirements completion
- Design status
- Tasks progress (total/completed/pending)

### View Metrics (Working ✅)

```bash
# Check latest champion
cat hall_of_fame/champion.json

# View iteration history
tail -20 iteration_history.jsonl | jq '.iteration_num, .metrics.sharpe_ratio'

# Template analytics
cat artifacts/data/template_analytics.json | jq .
```

### Monitor Real-Time (Working ✅)

```bash
# During iteration loop
tail -f logs/autonomous_loop.log

# Watch metrics file
watch -n 2 'tail -5 iteration_history.jsonl | jq .'
```

---

## Dashboard Comparison

| Dashboard Type | Purpose | Status | Access Method |
|---------------|---------|--------|---------------|
| **Spec Workflow** | View spec tasks | ❌ Not Starting | localhost:3456 (FAILED) |
| **Grafana** | Monitor metrics | ⚠️ Not Configured | localhost:3000 (need setup) |
| **MCP Status** | Spec progress | ✅ Working | Claude Code tool |
| **CLI Tools** | View metrics | ✅ Working | Terminal commands |

---

## Decision Matrix

### If User Needs: Spec Task Tracking

**Use**: MCP Status Tool (Already working)
- ✅ No setup required
- ✅ Works in Claude Code
- ❌ Not visual dashboard

**Alternative**: Fix spec-workflow dashboard
- ⏰ Requires debugging MCP server
- ⏰ May need package update
- ✅ Visual interface

### If User Needs: Performance Monitoring

**Use**: CLI tools (Already working)
- ✅ `scripts/analyze_metrics.py`
- ✅ Direct JSON file reading
- ❌ Not real-time visual

**Alternative**: Setup Grafana
- ⏰ Requires Docker install
- ⏰ Requires dashboard import
- ✅ Real-time visual charts

---

## Next Steps

**Pending User Clarification**:
1. Which dashboard is expected? (Spec workflow vs Grafana vs other)
2. What information do you need to view? (Tasks vs Metrics vs both)
3. Preference: Fix dashboard vs use CLI tools?

**Recommended Path**:
1. Use MCP status tool for spec tracking (already working)
2. Use CLI tools for metrics (already working)
3. Setup Grafana later if visual monitoring needed
4. Debug spec-workflow dashboard if critical

---

**Report Status**: ⚠️ NEEDS USER INPUT
**Priority**: Medium (workarounds available)
**Blocking**: No (system functionality unaffected)

**End of Report**
