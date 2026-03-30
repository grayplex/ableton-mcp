---
phase: 20
slug: blueprint-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `python -m pytest tests/test_genres.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_genres.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | INFR-01 | unit | `python -m pytest tests/test_genres.py -k "test_schema" -x -q` | ❌ W0 | ⬜ pending |
| 20-01-02 | 01 | 1 | INFR-05 | unit | `python -m pytest tests/test_genres.py -k "test_validation" -x -q` | ❌ W0 | ⬜ pending |
| 20-02-01 | 02 | 1 | INFR-02 | unit | `python -m pytest tests/test_genres.py -k "test_catalog" -x -q` | ❌ W0 | ⬜ pending |
| 20-02-02 | 02 | 1 | INFR-03 | unit | `python -m pytest tests/test_genres.py -k "test_alias" -x -q` | ❌ W0 | ⬜ pending |
| 20-02-03 | 02 | 1 | INFR-04 | unit | `python -m pytest tests/test_genres.py -k "test_subgenre" -x -q` | ❌ W0 | ⬜ pending |
| 20-03-01 | 03 | 2 | GENR-01 | unit | `python -m pytest tests/test_genres.py -k "test_house" -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_genres.py` — stubs for INFR-01 through INFR-05, GENR-01
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
