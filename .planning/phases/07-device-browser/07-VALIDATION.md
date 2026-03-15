---
phase: 7
slug: device-browser
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | pyproject.toml (project-level) |
| **Quick run command** | `python -m pytest tests/test_devices.py tests/test_browser.py tests/test_session.py -x` |
| **Full suite command** | `python -m pytest tests/ -x` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_devices.py tests/test_browser.py tests/test_session.py -x`
- **After every plan wave:** Run `python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | DEV-01 | smoke | `pytest tests/test_devices.py::test_load_instrument_calls_send_command -x` | ✅ (update) | ⬜ pending |
| 07-01-02 | 01 | 1 | DEV-02 | smoke | `pytest tests/test_devices.py::test_load_effect_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 07-02-01 | 02 | 1 | DEV-03 | smoke | `pytest tests/test_devices.py::test_get_device_parameters -x` | ❌ W0 | ⬜ pending |
| 07-02-02 | 02 | 1 | DEV-04 | smoke | `pytest tests/test_devices.py::test_set_device_parameter -x` | ❌ W0 | ⬜ pending |
| 07-03-01 | 03 | 1 | DEV-05 | smoke | `pytest tests/test_browser.py::test_get_browser_tree_returns_data -x` | ✅ (update) | ⬜ pending |
| 07-03-02 | 03 | 1 | DEV-06 | smoke | `pytest tests/test_browser.py::test_get_browser_items_at_path -x` | ❌ W0 | ⬜ pending |
| 07-04-01 | 04 | 2 | DEV-07 | smoke | `pytest tests/test_devices.py::test_get_rack_chains -x` | ❌ W0 | ⬜ pending |
| 07-05-01 | 05 | 2 | DEV-08 | smoke | `pytest tests/test_session.py::test_get_session_state -x` | ❌ W0 | ⬜ pending |
| 07-06-01 | 06 | 3 | DEV-01..08 | integration | `pytest tests/test_devices.py tests/test_browser.py tests/test_session.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_devices.py` — add tests for load_effect, get_device_parameters, set_device_parameter (name + index), delete_device, get_rack_chains
- [ ] `tests/test_browser.py` — update: remove load_drum_kit test, add max_depth test, add path-based loading test
- [ ] `tests/test_session.py` — add test for get_session_state (lightweight + detailed modes)
- [ ] `tests/conftest.py` — no changes needed (mock_connection already patches all tool modules)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Instrument produces sound after load | DEV-01 | Requires live audio output | Load Analog on MIDI track, play C3, verify audio |
| Effect audible in chain | DEV-02 | Requires live audio | Load Reverb on audio track, play clip, verify wet signal |
| Device loading race condition | DEV-01/02 | Timing-dependent in Live | Load instrument, immediately check device count |
| Rack chain navigation | DEV-07 | Requires real rack structure | Load Instrument Rack, navigate chains in Live |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
