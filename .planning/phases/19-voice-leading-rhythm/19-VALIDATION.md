---
phase: 19
slug: voice-leading-rhythm
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/test_theory.py -x --tb=short -q` |
| **Full suite command** | `python -m pytest tests/test_theory.py --tb=short -q` |
| **Estimated runtime** | ~13 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_theory.py -x --tb=short -q`
- **After every plan wave:** Run `python -m pytest tests/test_theory.py --tb=short -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 13 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 01 | 1 | VOIC-01, VOIC-02 | unit | `python -m pytest tests/test_theory.py -k "voice_lead" -x` | ❌ W0 | ⬜ pending |
| 19-01-02 | 01 | 1 | RHYM-01, RHYM-02 | unit | `python -m pytest tests/test_theory.py -k "rhythm" -x` | ❌ W0 | ⬜ pending |
| 19-02-01 | 02 | 2 | VOIC-01, VOIC-02, RHYM-01, RHYM-02 | integration | `python -m pytest tests/test_theory.py -k "TestVoiceLeadingTools or TestRhythmTools" -x` | ❌ W0 | ⬜ pending |

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
- [ ] Feedback latency < 13s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
