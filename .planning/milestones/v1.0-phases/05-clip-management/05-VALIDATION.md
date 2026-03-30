---
phase: 5
slug: clip-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ with pytest-asyncio 0.25+ |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/test_clips.py -x` |
| **Full suite command** | `python -m pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_clips.py -x`
- **After every plan wave:** Run `python -m pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | CLIP-01 | smoke | `python -m pytest tests/test_clips.py::test_create_clip_calls_send_command -x` | Exists | ⬜ pending |
| 05-01-02 | 01 | 1 | CLIP-02 | smoke | `python -m pytest tests/test_clips.py::test_delete_clip_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | CLIP-03 | smoke | `python -m pytest tests/test_clips.py::test_duplicate_clip_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 05-01-04 | 01 | 1 | CLIP-04 | smoke | `python -m pytest tests/test_clips.py::test_set_clip_name_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 1 | CLIP-05 | smoke | `python -m pytest tests/test_clips.py::test_set_clip_loop_calls_send_command -x` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 1 | CLIP-06 | smoke | (covered by CLIP-05 test) | ❌ W0 | ⬜ pending |
| 05-02-03 | 02 | 1 | CLIP-07 | smoke | (covered by CLIP-05 test) | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 1 | CLIP-08 | smoke | `python -m pytest tests/test_clips.py::test_fire_clip_returns_json -x` | Exists (needs update) | ⬜ pending |
| 05-03-02 | 03 | 1 | CLIP-09 | smoke | `python -m pytest tests/test_clips.py::test_stop_clip_returns_json -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_clips.py::test_clip_tools_registered` — update expected set with new tools (get_clip_info, delete_clip, duplicate_clip, set_clip_color, set_clip_loop)
- [ ] `tests/test_clips.py::test_delete_clip_calls_send_command` — covers CLIP-02
- [ ] `tests/test_clips.py::test_duplicate_clip_calls_send_command` — covers CLIP-03
- [ ] `tests/test_clips.py::test_get_clip_info_returns_json` — covers get_clip_info
- [ ] `tests/test_clips.py::test_get_clip_info_empty_slot` — covers empty slot behavior
- [ ] `tests/test_clips.py::test_set_clip_color_calls_send_command` — covers set_clip_color
- [ ] `tests/test_clips.py::test_set_clip_loop_calls_send_command` — covers CLIP-05/06/07
- [ ] `tests/test_clips.py::test_stop_clip_returns_json` — covers CLIP-09
- [ ] `tests/test_clips.py::test_fire_clip_returns_json` — update existing test for JSON response

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fire clip responds immediately | CLIP-08 | Requires live Ableton instance to verify launch quantization timing | Fire a clip in Session View, observe immediate trigger |
| Stop clip halts playback | CLIP-09 | Requires live Ableton instance to verify audio stops | Stop a playing clip, observe silence |
| Duplicate produces independent copy | CLIP-03 | Requires Ableton to verify clip independence post-duplicate | Duplicate clip, modify original, verify copy unchanged |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
