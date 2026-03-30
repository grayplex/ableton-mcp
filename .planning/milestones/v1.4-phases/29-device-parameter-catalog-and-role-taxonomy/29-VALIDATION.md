---
phase: 29
slug: device-parameter-catalog-and-role-taxonomy
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 29 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini or pyproject.toml |
| **Quick run command** | `pytest tests/test_device_catalog.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_device_catalog.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 29-01-01 | 01 | 1 | CATL-01 | unit | `pytest tests/test_device_catalog.py::test_catalog_structure -x -q` | ❌ W0 | ⬜ pending |
| 29-01-02 | 01 | 1 | CATL-01 | unit | `pytest tests/test_device_catalog.py::test_device_lookup -x -q` | ❌ W0 | ⬜ pending |
| 29-01-03 | 01 | 2 | CATL-01 | unit | `pytest tests/test_device_catalog.py::test_conversion_formulas -x -q` | ❌ W0 | ⬜ pending |
| 29-02-01 | 02 | 1 | ROLE-01 | unit | `pytest tests/test_role_taxonomy.py::test_role_list -x -q` | ❌ W0 | ⬜ pending |
| 29-02-02 | 02 | 1 | ROLE-01 | unit | `pytest tests/test_role_taxonomy.py::test_role_lookup -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_device_catalog.py` — stubs for CATL-01 (catalog structure, device lookup, conversion formulas)
- [ ] `tests/test_role_taxonomy.py` — stubs for ROLE-01 (role list, role lookup)
- [ ] `tests/conftest.py` — shared fixtures (if not already present)

*Existing pytest infrastructure assumed; Wave 0 adds test stubs only.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Bootstrap script captures correct parameter names from live Ableton session | CATL-01 | Requires running Ableton Live with 12 devices loaded | Load prepared Ableton project, run bootstrap tool, verify output matches expected parameter names |
| Catalog entries validated against live session | CATL-01 | Requires live Ableton session | Run `validate_catalog_against_live_session` tool, verify no mismatches |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
