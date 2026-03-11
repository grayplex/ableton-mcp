---
phase: 1
slug: foundation-repair
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + pytest-asyncio |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | FNDN-01 | unit | `pytest tests/test_py3_cleanup.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | FNDN-02 | unit | `pytest tests/test_py3_cleanup.py -x -q` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | FNDN-05 | unit | `pytest tests/test_error_handling.py -x -q` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 2 | FNDN-03 | unit | `pytest tests/test_socket_framing.py -x -q` | ❌ W0 | ⬜ pending |
| 1-03-02 | 03 | 2 | FNDN-04 | unit | `pytest tests/test_connection.py -x -q` | ❌ W0 | ⬜ pending |
| 1-04-01 | 04 | 2 | FNDN-06 | manual | N/A — requires Ableton Live running | ❌ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures (mock socket, mock Ableton connection)
- [ ] `tests/test_py3_cleanup.py` — stubs for FNDN-01, FNDN-02
- [ ] `tests/test_error_handling.py` — stubs for FNDN-05
- [ ] `tests/test_socket_framing.py` — stubs for FNDN-03
- [ ] `tests/test_connection.py` — stubs for FNDN-04
- [ ] `pip install pytest pytest-asyncio` — if no framework detected

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Instrument loads and plays sound | FNDN-06 (load fix) | Requires Ableton Live running with Remote Script | 1. Start Ableton, load Remote Script 2. Call load_instrument tool 3. Create MIDI clip with notes 4. Fire clip — verify audible sound |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
