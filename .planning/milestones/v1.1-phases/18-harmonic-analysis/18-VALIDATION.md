---
phase: 18
slug: harmonic-analysis
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/test_theory.py -x --tb=short -q` |
| **Full suite command** | `python -m pytest tests/test_theory.py --tb=short -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_theory.py -x --tb=short -q`
- **After every plan wave:** Run `python -m pytest tests/test_theory.py --tb=short -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | ANLY-01 | unit | `python -m pytest tests/test_theory.py -k "detect_key" -x` | ❌ W0 | ⬜ pending |
| 18-01-02 | 01 | 1 | ANLY-02 | unit | `python -m pytest tests/test_theory.py -k "analyze_clip_chords" -x` | ❌ W0 | ⬜ pending |
| 18-01-03 | 01 | 1 | ANLY-03 | unit | `python -m pytest tests/test_theory.py -k "analyze_harmonic_rhythm" -x` | ❌ W0 | ⬜ pending |
| 18-02-01 | 02 | 2 | ANLY-01 | integration | `python -m pytest tests/test_theory.py -k "TestAnalysisTools and detect_key" -x` | ❌ W0 | ⬜ pending |
| 18-02-02 | 02 | 2 | ANLY-02 | integration | `python -m pytest tests/test_theory.py -k "TestAnalysisTools and analyze_clip" -x` | ❌ W0 | ⬜ pending |
| 18-02-03 | 02 | 2 | ANLY-03 | integration | `python -m pytest tests/test_theory.py -k "TestAnalysisTools and harmonic_rhythm" -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. Tests will be added in-plan alongside implementation.*

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
