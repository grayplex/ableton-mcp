---
phase: 31
slug: apply-recipe-and-batch-parameter-tools
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 31 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` or `pyproject.toml` (existing) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 31-01-01 | 01 | 1 | BATCH-01 | unit | `pytest tests/test_batch_params.py -x -q` | ❌ W0 | ⬜ pending |
| 31-01-02 | 01 | 1 | APPLY-03 | unit | `pytest tests/test_apply_recipe.py -x -q` | ❌ W0 | ⬜ pending |
| 31-01-03 | 01 | 2 | APPLY-01 | integration | `pytest tests/test_apply_recipe.py -x -q` | ❌ W0 | ⬜ pending |
| 31-01-04 | 01 | 2 | APPLY-02 | integration | `pytest tests/test_apply_recipe.py::test_master_recipe -x -q` | ❌ W0 | ⬜ pending |
| 31-02-01 | 02 | 1 | SIDE-01 | unit | `pytest tests/test_sidechain.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_batch_params.py` — stubs for BATCH-01 (set_device_parameters RS primitive)
- [ ] `tests/test_apply_recipe.py` — stubs for APPLY-01, APPLY-02, APPLY-03 (apply_mix_recipe, apply_master_recipe, atomicity)
- [ ] `tests/test_sidechain.py` — stubs for SIDE-01 (set_sidechain_source by track name)

*Existing test infrastructure (pytest) assumed — no new framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Device loading atomicity (no race condition) | APPLY-03 | Requires live Ableton session to verify device instantiation timing | Load recipe on track with no devices; verify devices appear before params are set in RS log |
| apply_master_recipe applies to master bus | APPLY-02 | Requires live Ableton session | Call apply_master_recipe("house"); verify GlueCompressor + MultibandDynamics + Limiter appear on master track |
| Sidechain source resolved by name | SIDE-01 | Requires live Ableton session with named tracks | Create track named "Kick", call set_sidechain_source with source_track_name="Kick", verify compressor input routing updates |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
