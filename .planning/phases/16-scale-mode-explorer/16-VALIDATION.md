---
phase: 16
slug: scale-mode-explorer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` (pytest config section) |
| **Quick run command** | `python -m pytest tests/test_theory.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_theory.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 16-01-01 | 01 | 1 | SCLE-01 | unit | `python -m pytest tests/test_theory.py -k "list_scales" -x -q` | ❌ W0 | ⬜ pending |
| 16-01-02 | 01 | 1 | SCLE-02 | unit | `python -m pytest tests/test_theory.py -k "scale_pitches" -x -q` | ❌ W0 | ⬜ pending |
| 16-01-03 | 01 | 1 | SCLE-03 | unit | `python -m pytest tests/test_theory.py -k "check_notes" -x -q` | ❌ W0 | ⬜ pending |
| 16-01-04 | 01 | 1 | SCLE-04 | unit | `python -m pytest tests/test_theory.py -k "related_scales" -x -q` | ❌ W0 | ⬜ pending |
| 16-01-05 | 01 | 1 | SCLE-05 | unit | `python -m pytest tests/test_theory.py -k "detect_scales" -x -q` | ❌ W0 | ⬜ pending |
| 16-02-01 | 02 | 2 | SCLE-01..05 | integration | `python -m pytest tests/test_theory.py -k "scale" -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_theory.py` — add scale test stubs for SCLE-01..05
- [ ] Existing `conftest.py` and `mcp_server` fixture cover all needs

*Existing infrastructure covers phase requirements — only test cases need adding.*

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
