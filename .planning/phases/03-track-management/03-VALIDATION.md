---
phase: 3
slug: track-management
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3 + pytest-asyncio 0.25 |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/test_tracks.py -x` |
| **Full suite command** | `uv run pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_tracks.py -x`
- **After every plan wave:** Run `uv run pytest tests/ -x && uv run ruff check .`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | TRCK-01 | smoke | `uv run pytest tests/test_tracks.py::test_create_midi_track_calls_send_command -x` | ✅ | ⬜ pending |
| 03-01-02 | 01 | 1 | TRCK-02 | smoke | `uv run pytest tests/test_tracks.py::test_create_audio_track -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | TRCK-03 | smoke | `uv run pytest tests/test_tracks.py::test_create_return_track -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 1 | TRCK-04 | smoke | `uv run pytest tests/test_tracks.py::test_create_group_track -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | TRCK-05 | smoke | `uv run pytest tests/test_tracks.py::test_delete_track -x` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | TRCK-06 | smoke | `uv run pytest tests/test_tracks.py::test_duplicate_track -x` | ❌ W0 | ⬜ pending |
| 03-02-03 | 02 | 1 | TRCK-07 | smoke | `uv run pytest tests/test_tracks.py::test_set_track_name -x` | ✅ | ⬜ pending |
| 03-02-04 | 02 | 1 | TRCK-08 | smoke | `uv run pytest tests/test_tracks.py::test_set_track_color -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 1 | TRCK-09 | smoke | `uv run pytest tests/test_tracks.py::test_get_track_info_returns_data -x` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_tracks.py::test_create_audio_track` — stub for TRCK-02
- [ ] `tests/test_tracks.py::test_create_return_track` — stub for TRCK-03
- [ ] `tests/test_tracks.py::test_create_group_track` — stub for TRCK-04
- [ ] `tests/test_tracks.py::test_delete_track` — stub for TRCK-05
- [ ] `tests/test_tracks.py::test_duplicate_track` — stub for TRCK-06
- [ ] `tests/test_tracks.py::test_set_track_color` — stub for TRCK-08
- [ ] `tests/test_tracks.py::test_get_track_info_all_types` — extend for return/master (TRCK-09)

*Existing infrastructure covers framework + fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Group track creation | TRCK-04 | No direct API method; needs runtime Ableton validation | 1. Call create_group_track, 2. Verify group appears in Ableton UI |
| Color visual accuracy | TRCK-08 | Color name-to-index mapping visual verification | 1. Set track color by name, 2. Verify correct color in Ableton UI |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
