---
phase: 33
slug: mix-adjustment-intelligence
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 33 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` or `pyproject.toml` |
| **Quick run command** | `pytest tests/test_intelligence.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_intelligence.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 33-01-01 | 01 | 0 | INTEL-01 | unit stub | `pytest tests/test_intelligence.py -x -q` | ❌ W0 | ⬜ pending |
| 33-01-02 | 01 | 1 | INTEL-01 | unit | `pytest tests/test_intelligence.py -x -q` | ✅ | ⬜ pending |
| 33-01-03 | 01 | 1 | INTEL-01 | unit | `pytest tests/test_intelligence.py -x -q` | ✅ | ⬜ pending |
| 33-01-04 | 01 | 2 | INTEL-01 | unit | `pytest tests/test_intelligence.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_intelligence.py` — stubs for INTEL-01 (suggest_mix_adjustments, diff computation, threshold, display values)
- [ ] Test fixtures: mock `get_mix_state` response and recipe data

*Existing test infrastructure (pytest) covers the framework requirement.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| suggest_mix_adjustments returns correct diffs against live Ableton session | INTEL-01 | Requires live Ableton + loaded tracks with devices | Call tool via MCP client, verify JSON output matches expected diffs |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
