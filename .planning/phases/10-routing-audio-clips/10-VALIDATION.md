---
phase: 10
slug: routing-audio-clips
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio (existing) |
| **Config file** | `pyproject.toml` / `conftest.py` |
| **Quick run command** | `python -m pytest tests/test_routing.py tests/test_audio_clips.py -x` |
| **Full suite command** | `python -m pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_routing.py tests/test_audio_clips.py -x`
- **After every plan wave:** Run `python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | ROUT-01 | smoke | `python -m pytest tests/test_routing.py::test_get_input_routing_types -x` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | ROUT-02 | smoke | `python -m pytest tests/test_routing.py::test_set_input_routing -x` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 1 | ROUT-03 | smoke | `python -m pytest tests/test_routing.py::test_get_output_routing_types -x` | ❌ W0 | ⬜ pending |
| 10-01-04 | 01 | 1 | ROUT-04 | smoke | `python -m pytest tests/test_routing.py::test_set_output_routing -x` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 1 | ACLP-01 | smoke | `python -m pytest tests/test_audio_clips.py::test_set_audio_clip_properties_pitch -x` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 1 | ACLP-02 | smoke | `python -m pytest tests/test_audio_clips.py::test_set_audio_clip_properties_gain -x` | ❌ W0 | ⬜ pending |
| 10-02-03 | 02 | 1 | ACLP-03 | smoke | `python -m pytest tests/test_audio_clips.py::test_set_audio_clip_properties_warping -x` | ❌ W0 | ⬜ pending |
| 10-03-01 | 03 | 2 | ROUT-01..04 | smoke | `python -m pytest tests/test_routing.py -x` | ❌ W0 | ⬜ pending |
| 10-03-02 | 03 | 2 | ACLP-01..03 | smoke | `python -m pytest tests/test_audio_clips.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_routing.py` — stubs for ROUT-01 through ROUT-04
- [ ] `tests/test_audio_clips.py` — stubs for ACLP-01 through ACLP-03
- [ ] `tests/conftest.py` — add `MCP_Server.tools.routing.get_ableton_connection` and `MCP_Server.tools.audio_clips.get_ableton_connection` to `_GAC_PATCH_TARGETS`

*Existing infrastructure covers framework install — pytest already configured.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Routing change audible in Ableton | ROUT-02, ROUT-04 | Requires live Ableton session with audio hardware | Set input/output routing via MCP, verify signal flow changes in Ableton mixer |
| Pitch transposition audible | ACLP-01 | Requires audio playback | Set pitch_coarse/fine via MCP, play clip, verify pitch change heard |
| Gain change audible | ACLP-02 | Requires audio playback | Set gain via MCP, play clip, verify volume change heard |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
