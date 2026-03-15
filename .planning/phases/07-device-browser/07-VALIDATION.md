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
| 07-01-01 | 01 | 1 | DEV-03, DEV-04 | import | `python -c "from AbletonMCP_Remote_Script.handlers.devices import DeviceHandlers; print('OK')"` | N/A | pending |
| 07-01-02 | 01 | 1 | DEV-07 | import | `python -c "from AbletonMCP_Remote_Script.handlers.devices import DeviceHandlers; methods = [m for m in dir(DeviceHandlers) if not m.startswith('__')]; assert '_delete_device' in methods; print('OK')"` | N/A | pending |
| 07-02-01 | 02 | 2 | DEV-05, DEV-06, DEV-01, DEV-02 | import | `python -c "from AbletonMCP_Remote_Script.handlers.browser import BrowserHandlers; print('OK')"` | N/A | pending |
| 07-02-02 | 02 | 2 | DEV-08 | import | `python -c "from AbletonMCP_Remote_Script.handlers.devices import DeviceHandlers; assert hasattr(DeviceHandlers, '_get_session_state'); print('OK')"` | N/A | pending |
| 07-03-01 | 03 | 3 | DEV-01..08 | import | `python -c "from MCP_Server.tools.devices import get_device_parameters, set_device_parameter, delete_device, get_rack_chains; from MCP_Server.tools.session import get_session_state; print('OK')"` | N/A | pending |
| 07-03-02 | 03 | 3 | DEV-01..08 | smoke | `pytest tests/test_devices.py tests/test_browser.py tests/test_session.py -v` | W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_devices.py` — add tests for get_device_parameters, set_device_parameter (name + index), delete_device, get_rack_chains, load_instrument path support
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
| Instrument-on-audio-track error | DEV-01 | Requires Live track types | Attempt to load instrument on audio track, verify error message |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
