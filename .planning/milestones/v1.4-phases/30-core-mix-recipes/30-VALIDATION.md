---
phase: 30
slug: core-mix-recipes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 30 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_mixing.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_mixing.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 30-01-01 | 01 | 0 | RECIP-01 | unit | `pytest tests/test_mixing.py -x` | ❌ W0 | ⬜ pending |
| 30-02-01 | 02 | 1 | RECIP-01a/c/d | unit | `pytest tests/test_mixing.py::TestRecipeData tests/test_mixing.py::TestRecipeCompleteness tests/test_mixing.py::TestAutoDiscovery -x` | ❌ W0 | ⬜ pending |
| 30-03-01 | 03 | 1 | RECIP-01b | unit | `pytest tests/test_mixing.py::TestRecipeParameterNames -x` | ❌ W0 | ⬜ pending |
| 30-04-01 | 04 | 2 | RECIP-01e/f | unit | `pytest tests/test_mixing.py::TestGetRecipe tests/test_mixing.py::TestAliasResolution -x` | ❌ W0 | ⬜ pending |
| 30-05-01 | 05 | 3 | RECIP-01g/h | unit | `pytest tests/test_mixing.py::TestMixRecipeTool -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_mixing.py` — stubs for all RECIP-01 sub-requirements (a–h)
- [ ] MCP mock setup reusing pattern from `tests/test_catalog.py`

*Wave 0 creates the test file with all required test class stubs before recipe data is authored.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Recipe values sound musically reasonable | RECIP-01 | Subjective musical judgment | Review house/techno/ambient/DnB recipe values for kick, bass, lead — confirm EQ frequencies and compressor settings are genre-appropriate |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
