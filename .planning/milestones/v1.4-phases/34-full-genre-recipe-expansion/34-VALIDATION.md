---
phase: 34
slug: full-genre-recipe-expansion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 34 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini (existing) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 34-01-01 | 01 | 1 | RECIP-02 | unit | `pytest tests/ -k "synthwave" -x -q` | ❌ W0 | ⬜ pending |
| 34-01-02 | 01 | 1 | RECIP-02 | unit | `pytest tests/ -k "hip_hop" -x -q` | ❌ W0 | ⬜ pending |
| 34-01-03 | 01 | 1 | RECIP-02 | unit | `pytest tests/ -k "dubstep" -x -q` | ❌ W0 | ⬜ pending |
| 34-01-04 | 01 | 1 | RECIP-02 | unit | `pytest tests/ -k "trance" -x -q` | ❌ W0 | ⬜ pending |
| 34-01-05 | 01 | 1 | RECIP-02 | unit | `pytest tests/ -k "lo_fi" -x -q` | ❌ W0 | ⬜ pending |
| 34-01-06 | 01 | 1 | RECIP-02 | unit | `pytest tests/ -k "future_bass" -x -q` | ❌ W0 | ⬜ pending |
| 34-01-07 | 01 | 1 | RECIP-02 | unit | `pytest tests/ -k "disco" -x -q` | ❌ W0 | ⬜ pending |
| 34-01-08 | 01 | 1 | RECIP-02 | unit | `pytest tests/ -k "neo_soul" -x -q` | ❌ W0 | ⬜ pending |
| 34-02-01 | 02 | 2 | MSTR-01 | unit | `pytest tests/ -k "master" -x -q` | ❌ W0 | ⬜ pending |
| 34-03-01 | 03 | 3 | RECIP-02,MSTR-01 | integration | `pytest tests/ -v` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_genre_recipes.py` — expand `_MASTER_GENRES` to 12 genres, add stubs for 8 new genre files (RECIP-02)
- [ ] `tests/test_master_bus.py` — expand `_MASTER_GENRES` to 12 genres for master bus tests (MSTR-01)

*Existing infrastructure covers schema validation and catalog verification patterns.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Tool docstrings list all 12 genres | D-09 | String content check | Inspect `mixing.py` and `intelligence.py` docstrings for all 12 genre names |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
