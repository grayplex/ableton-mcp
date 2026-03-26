---
phase: 21
slug: blueprint-tools
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `python -m pytest tests/test_genre_tools.py -x -q` |
| **Full suite command** | `python -m pytest tests/test_genres.py tests/test_genre_tools.py -x -q` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_genre_tools.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/test_genres.py tests/test_genre_tools.py -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | TOOL-01 | unit | `python -m pytest tests/test_genre_tools.py -k "test_list" -x -q` | ❌ W0 | ⬜ pending |
| 21-01-02 | 01 | 1 | TOOL-02 | unit | `python -m pytest tests/test_genre_tools.py -k "test_get" -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_genre_tools.py` — stubs for TOOL-01, TOOL-02
- [ ] No new framework install needed (pytest already configured)

*Existing infrastructure covers test framework requirements.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
