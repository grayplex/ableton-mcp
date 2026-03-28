---
phase: 27
slug: locator-and-scaffolding-commands
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 27 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | Standard (no pytest.ini) |
| **Quick run command** | `python -m pytest tests/test_scaffold.py -x` |
| **Full suite command** | `python -m pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_scaffold.py -x`
- **After every plan wave:** Run `python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 27-01-01 | 01 | 0 | SCAF-01 | unit | `python -m pytest tests/test_scaffold.py -x` | ❌ W0 | ⬜ pending |
| 27-01-02 | 01 | 1 | SCAF-01 | unit (mock socket) | `python -m pytest tests/test_scaffold.py::TestScaffoldArrangement -x` | ❌ W0 | ⬜ pending |
| 27-01-03 | 01 | 1 | SCAF-01 | unit (pure) | `python -m pytest tests/test_scaffold.py::TestRoleDeduplication -x` | ❌ W0 | ⬜ pending |
| 27-01-04 | 01 | 1 | SCAF-01 | unit (pure) | `python -m pytest tests/test_scaffold.py::TestBarToBeat -x` | ❌ W0 | ⬜ pending |
| 27-01-05 | 01 | 1 | SCAF-01 | unit | `python -m pytest tests/test_scaffold.py::test_scaffold_tools_registered -x` | ❌ W0 | ⬜ pending |
| 27-02-01 | 02 | 1 | SCAF-02 | unit (mock socket) | `python -m pytest tests/test_scaffold.py::TestArrangementOverview -x` | ❌ W0 | ⬜ pending |
| 27-02-02 | 02 | 1 | SCAF-02 | unit (pure) | `python -m pytest tests/test_scaffold.py::TestBarConversions -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scaffold.py` — stubs for SCAF-01, SCAF-02 (TestScaffoldArrangement, TestRoleDeduplication, TestBarToBeat, TestArrangementOverview, TestBarConversions, test_scaffold_tools_registered)
- [ ] `tests/conftest.py` — add `"MCP_Server.tools.scaffold.get_ableton_connection"` to `_GAC_PATCH_TARGETS`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Locators appear in Ableton Arrangement view at correct positions | SCAF-01 | Requires live Ableton session | Open Ableton, call scaffold_arrangement with a 4/4 plan, verify locators appear at correct bars in Arrangement view |
| Scaffold completes within 15-second write timeout | SCAF-01 | Requires live Ableton session | Call scaffold_arrangement with a 7-section plan and verify no timeout error |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
