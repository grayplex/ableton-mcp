---
phase: 12
slug: fill-in-missing-gaps
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x + pytest-asyncio |
| **Config file** | tests/conftest.py |
| **Quick run command** | `python -m pytest tests/ -x -q --timeout=10` |
| **Full suite command** | `python -m pytest tests/ -v --timeout=30` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q --timeout=10`
- **After every plan wave:** Run `python -m pytest tests/ -v --timeout=30`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | Song: scale/key | unit | `pytest tests/test_song_gaps.py -k scale` | ❌ W0 | ⬜ pending |
| 12-01-02 | 01 | 1 | Song: cue points | unit | `pytest tests/test_song_gaps.py -k cue` | ❌ W0 | ⬜ pending |
| 12-01-03 | 01 | 1 | Song: capture | unit | `pytest tests/test_song_gaps.py -k capture` | ❌ W0 | ⬜ pending |
| 12-01-04 | 01 | 1 | Song: session controls | unit | `pytest tests/test_song_gaps.py -k session` | ❌ W0 | ⬜ pending |
| 12-01-05 | 01 | 1 | Song: navigation | unit | `pytest tests/test_song_gaps.py -k navigation` | ❌ W0 | ⬜ pending |
| 12-01-06 | 01 | 1 | Song: device mgmt | unit | `pytest tests/test_song_gaps.py -k device` | ❌ W0 | ⬜ pending |
| 12-02-01 | 02 | 1 | Track: arrangement | unit | `pytest tests/test_arrangement.py` | ❌ W0 | ⬜ pending |
| 12-02-02 | 02 | 1 | Track: insert_device | unit | `pytest tests/test_arrangement.py -k insert` | ❌ W0 | ⬜ pending |
| 12-02-03 | 02 | 1 | Track: ops | unit | `pytest tests/test_arrangement.py -k ops` | ❌ W0 | ⬜ pending |
| 12-03-01 | 03 | 2 | Clip: launch settings | unit | `pytest tests/test_clip_gaps.py -k launch` | ❌ W0 | ⬜ pending |
| 12-03-02 | 03 | 2 | Clip: warp markers | unit | `pytest tests/test_clip_gaps.py -k warp` | ❌ W0 | ⬜ pending |
| 12-03-03 | 03 | 2 | Clip: note ops | unit | `pytest tests/test_clip_gaps.py -k note` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_transport.py` — extended with scale/key, cue points, capture, session controls, navigation smoke tests
- [ ] `tests/test_scenes.py` — extended with duplicate_scene smoke tests
- [ ] `tests/test_arrangement.py` — new file for arrangement clips, session-to-arrangement bridge smoke tests
- [ ] `tests/test_devices.py` — extended with insert_device, move_device smoke tests
- [ ] `tests/test_tracks.py` — extended with stop_all_clips, freeze state smoke tests
- [ ] `tests/test_routing.py` — extended with sub-routing channels smoke tests
- [ ] `tests/test_clips.py` — extended with launch settings, clip state, clip editing smoke tests
- [ ] `tests/test_notes.py` — extended with note ID ops, note modifications, native quantize smoke tests
- [ ] `tests/test_audio_clips.py` — extended with warp marker smoke tests

*Existing conftest.py and pytest infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Arrangement clip appears in Ableton timeline | Track arrangement | Requires live Ableton connection | Create arrangement clip via tool, verify in Ableton arrangement view |
| insert_device loads correct instrument | Track insert_device | Requires live Ableton connection | Call insert_device("Wavetable"), verify device appears on track |
| Warp markers affect audio timing | Clip warp markers | Requires audio playback | Insert warp marker, play clip, verify timing change |
| Scale/key info matches Ableton UI | Song scale | Requires live Ableton | Set scale, verify in Ableton status bar |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
