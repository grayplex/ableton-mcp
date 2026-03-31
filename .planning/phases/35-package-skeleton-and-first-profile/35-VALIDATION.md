---
phase: 35
slug: package-skeleton-and-first-profile
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 35 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/test_sounds.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_sounds.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 35-01-01 | 01 | 0 | PKG-01 | unit | `pytest tests/test_sounds.py -x` | ❌ W0 | ⬜ pending |
| 35-01-02 | 01 | 1 | PKG-01 | unit | `pytest tests/test_sounds.py::TestAutoDiscovery -x` | ❌ W0 | ⬜ pending |
| 35-01-03 | 01 | 1 | INST-01 | unit | `pytest tests/test_sounds.py::TestGetProfile -x` | ❌ W0 | ⬜ pending |
| 35-02-01 | 02 | 1 | INST-01 | unit | `pytest tests/test_sounds.py::TestProfileShape -x` | ❌ W0 | ⬜ pending |
| 35-02-02 | 02 | 1 | INST-01 | unit | `pytest tests/test_sounds.py::TestAliasResolution -x` | ❌ W0 | ⬜ pending |
| 35-02-03 | 02 | 1 | INST-01 | manual | Manual: `get_browser_items_at_path("Instruments/Wavetable")` via MCP | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_sounds.py` — stubs for PKG-01 and INST-01 (auto-discovery, profile shape, alias resolution, get_profile API)
- [ ] No new conftest fixtures needed — sounds/ catalog is pure data, no MCP mock required

*Existing pytest infrastructure covers all framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Browser root path `Instruments/Wavetable` loads in live Ableton | INST-01 | Requires live Ableton session; MCP tool talks to running DAW | Call `get_browser_items_at_path(path="Instruments/Wavetable")` via MCP in a live session. Success: returns list of items. Failure: log warning per D-06, note actual path from error's available_categories. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
