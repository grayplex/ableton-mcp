---
phase: 28
slug: section-execution-and-quality-gate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 28 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `tests/conftest.py` |
| **Quick run command** | `python -m pytest tests/ -x -q 2>&1 | tail -20` |
| **Full suite command** | `python -m pytest tests/ -v 2>&1 | tail -40` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q 2>&1 | tail -20`
- **After every plan wave:** Run `python -m pytest tests/ -v 2>&1 | tail -40`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 28-01-01 | 01 | 0 | EXEC-01 | unit stub | `python -m pytest tests/test_execution.py -x -q` | ❌ W0 | ⬜ pending |
| 28-01-02 | 01 | 1 | EXEC-01 | unit | `python -m pytest tests/test_execution.py::test_get_section_checklist -v` | ✅ | ⬜ pending |
| 28-01-03 | 01 | 1 | EXEC-01 | unit | `python -m pytest tests/test_execution.py::test_section_checklist_dedup -v` | ✅ | ⬜ pending |
| 28-02-01 | 02 | 1 | EXEC-02 | unit | `python -m pytest tests/test_execution.py::test_get_arrangement_progress -v` | ✅ | ⬜ pending |
| 28-02-02 | 02 | 1 | EXEC-02 | unit | `python -m pytest tests/test_execution.py::test_progress_empty_tracks -v` | ✅ | ⬜ pending |
| 28-02-03 | 02 | 2 | EXEC-01, EXEC-02 | integration | `python -m pytest tests/test_execution.py -v` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_execution.py` — stubs for EXEC-01 and EXEC-02 (get_section_checklist and get_arrangement_progress)
- [ ] Update `tests/conftest.py` — add `MCP_Server.tools.execution` to `_GAC_PATCH_TARGETS`

*Wave 0 must create test file before any implementation tasks run.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| End-to-end workflow: blueprint → scaffold → section checklist in live Ableton | EXEC-01, EXEC-02 | Requires running Ableton Live with Remote Script | Run `scaffold_arrangement`, then call `get_section_checklist("intro")` and verify roles match scaffolded tracks |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
