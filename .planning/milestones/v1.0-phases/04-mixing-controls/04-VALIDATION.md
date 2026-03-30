---
phase: 4
slug: mixing-controls
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ / pytest-asyncio 0.25+ |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `python -m pytest tests/test_mixer.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_mixer.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | MIX-01 | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_volume -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | MIX-02 | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_pan -x` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | MIX-03 | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_mute -x` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | MIX-04 | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_solo -x` | ❌ W0 | ⬜ pending |
| 04-02-03 | 02 | 1 | MIX-05 | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_arm -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 1 | MIX-06 | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_send_level -x` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 1 | MIX-07 | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_volume_master -x` | ❌ W0 | ⬜ pending |
| 04-03-03 | 03 | 1 | MIX-08 | unit (smoke) | `python -m pytest tests/test_mixer.py::test_set_track_volume_return -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_mixer.py` — smoke tests for MIX-01 through MIX-08
- [ ] `tests/conftest.py` — add `MCP_Server.tools.mixer.get_ableton_connection` to `_GAC_PATCH_TARGETS`

*Existing infrastructure covers framework and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Volume change heard in Ableton | MIX-01 | Requires live audio playback | Set volume to 0.5, play a clip, verify level change is audible |
| Pan heard in correct speaker | MIX-02 | Requires stereo audio output | Pan fully left, verify sound in left speaker only |
| Solo isolates track audio | MIX-04 | Requires live audio context | Solo a track with multiple tracks playing, verify only that track is heard |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
