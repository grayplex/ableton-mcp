---
phase: 8
slug: scene-transport
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ with pytest-asyncio 0.25+ |
| **Config file** | `pyproject.toml` [tool.pytest.ini_options] |
| **Quick run command** | `python -m pytest tests/test_scenes.py tests/test_transport.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_scenes.py tests/test_transport.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | SCNE-01 | unit | `python -m pytest tests/test_scenes.py::test_create_scene_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | SCNE-02 | unit | `python -m pytest tests/test_scenes.py::test_set_scene_name_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 1 | SCNE-03 | unit | `python -m pytest tests/test_scenes.py::test_fire_scene_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 08-01-04 | 01 | 1 | SCNE-04 | unit | `python -m pytest tests/test_scenes.py::test_delete_scene_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 1 | TRNS-03 | unit | `python -m pytest tests/test_transport.py::test_continue_playback_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 1 | TRNS-04 | unit | `python -m pytest tests/test_transport.py::test_stop_all_clips_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 1 | TRNS-05 | unit | `python -m pytest tests/test_transport.py::test_set_tempo_calls_send_command -x` | ✅ | ⬜ pending |
| 08-03-02 | 03 | 1 | TRNS-06 | unit | `python -m pytest tests/test_transport.py::test_set_time_signature_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 08-03-03 | 03 | 1 | TRNS-07 | unit | `python -m pytest tests/test_transport.py::test_set_loop_region_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 08-03-04 | 03 | 1 | TRNS-08 | unit | `python -m pytest tests/test_transport.py::test_get_playback_position_returns_json -x` | ❌ W0 | ⬜ pending |
| 08-04-01 | 04 | 1 | TRNS-09 | unit | `python -m pytest tests/test_transport.py::test_undo_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 08-04-02 | 04 | 1 | TRNS-10 | unit | `python -m pytest tests/test_transport.py::test_redo_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 08-05-01 | 05 | 2 | TRNS-01 | unit | `python -m pytest tests/test_transport.py::test_start_playback_returns_message -x` | ✅ | ⬜ pending |
| 08-05-02 | 05 | 2 | TRNS-02 | unit | `python -m pytest tests/test_transport.py::test_stop_playback_returns_message -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scenes.py` — stubs for SCNE-01 through SCNE-04
- [ ] `tests/test_transport.py` — extend with TRNS-03, TRNS-04, TRNS-06, TRNS-07, TRNS-08, TRNS-09, TRNS-10
- [ ] `tests/conftest.py` — add `MCP_Server.tools.scenes.get_ableton_connection` to `_GAC_PATCH_TARGETS`

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Scene fires in Session View | SCNE-03 | Requires Ableton Live running | Fire scene, verify clips launch visually |
| Transport start/stop/continue | TRNS-01/02/03 | Audio playback verification | Start/stop/continue playback, verify audio output |
| stop_all_clips leaves transport running | TRNS-04 | Requires Ableton Live running | Stop all clips, verify Song position continues advancing |
| Undo/Redo affect Live's state | TRNS-09/10 | Requires Ableton Live running | Perform action, undo, verify state reverted |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
