---
phase: 13
slug: remaining-lom-gaps
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` |
| **Quick run command** | `python -m pytest tests/ -x -q --tb=short` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | SCNX-01..06 | unit | `python -m pytest tests/test_scenes.py -v` | ✅ | ⬜ pending |
| 13-01-02 | 01 | 1 | MIXX-01..03 | unit | `python -m pytest tests/test_mixer.py -v` | ❌ W0 | ⬜ pending |
| 13-02-01 | 02 | 1 | SMPL-01..05 | unit | `python -m pytest tests/test_simpler.py -v` | ❌ W0 | ⬜ pending |
| 13-02-02 | 02 | 1 | DRPD-01..02 | unit | `python -m pytest tests/test_devices.py -v` | ✅ | ⬜ pending |
| 13-02-03 | 02 | 1 | DEVX-03..04 | unit | `python -m pytest tests/test_devices.py -v` | ✅ | ⬜ pending |
| 13-03-01 | 03 | 2 | GRVX-01..03 | unit | `python -m pytest tests/test_grooves.py -v` | ❌ W0 | ⬜ pending |
| 13-03-02 | 03 | 2 | ACRT-01 | unit | `python -m pytest tests/test_clips.py -v` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_mixer.py` — stubs for MIXX-01..03 (crossfader, crossfade_assign, panning_mode)
- [ ] `tests/test_simpler.py` — stubs for SMPL-01..05 (Simpler device operations + slicing)
- [ ] `tests/test_grooves.py` — stubs for GRVX-01..03 (groove pool operations)
- [ ] `tests/conftest.py` — add `_GAC_PATCH_TARGETS` entries for new tool modules

*Existing test infrastructure (pytest, conftest.py) covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Scene tempo overrides global tempo | SCNX-03 | Requires live playback | Set scene tempo, fire scene, verify global tempo changes |
| Simpler slice playback | SMPL-05 | Requires audio playback | Load sample, create slices, verify slicing mode activates |
| A/B preset compare | DEVX-04 | Requires loaded plugin with preset history | Store preset, modify, restore, verify |
| Create audio clip from file | ACRT-01 | Requires audio file on disk | Call create_audio_clip with valid file path, verify clip appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
