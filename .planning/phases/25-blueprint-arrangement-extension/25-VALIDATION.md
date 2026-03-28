---
phase: 25
slug: blueprint-arrangement-extension
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` or `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/test_genres.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_genres.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 25-01-01 | 01 | 1 | ARNG-01/02/03 | unit | `python -m pytest tests/test_genres.py -x -q` | ✅ | ⬜ pending |
| 25-01-02 | 01 | 1 | ARNG-01/02/03 | unit | `python -m pytest tests/test_genres.py -x -q` | ✅ | ⬜ pending |
| 25-02-01 | 02 | 2 | ARNG-01/02/03 | unit | `python -m pytest tests/ -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_genres.py` — add new tests for ARNG-01, ARNG-02, ARNG-03 (new fields per section)

*Existing infrastructure covers core framework; Wave 0 only needs new test functions.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
