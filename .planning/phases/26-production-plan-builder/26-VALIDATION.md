---
phase: 26
slug: production-plan-builder
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` or `pyproject.toml` (existing) |
| **Quick run command** | `pytest tests/test_plans.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_plans.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 26-01-01 | 01 | 0 | PLAN-01 | unit | `pytest tests/test_plans.py::test_generate_production_plan_basic -x -q` | ❌ W0 | ⬜ pending |
| 26-01-02 | 01 | 1 | PLAN-01 | unit | `pytest tests/test_plans.py::test_generate_production_plan_all_genres -x -q` | ❌ W0 | ⬜ pending |
| 26-01-03 | 01 | 1 | PLAN-01 | unit | `pytest tests/test_plans.py::test_token_budget_under_400 -x -q` | ❌ W0 | ⬜ pending |
| 26-02-01 | 02 | 1 | PLAN-02 | unit | `pytest tests/test_plans.py::test_generate_section_plan_basic -x -q` | ❌ W0 | ⬜ pending |
| 26-02-02 | 02 | 1 | PLAN-02 | unit | `pytest tests/test_plans.py::test_section_plan_bar_start_calculation -x -q` | ❌ W0 | ⬜ pending |
| 26-03-01 | 03 | 2 | PLAN-03 | unit | `pytest tests/test_plans.py::test_override_remove_section -x -q` | ❌ W0 | ⬜ pending |
| 26-03-02 | 03 | 2 | PLAN-03 | unit | `pytest tests/test_plans.py::test_override_insert_section -x -q` | ❌ W0 | ⬜ pending |
| 26-03-03 | 03 | 2 | PLAN-03 | unit | `pytest tests/test_plans.py::test_override_resize_section -x -q` | ❌ W0 | ⬜ pending |
| 26-04-01 | 01 | 1 | PLAN-01 | unit | `pytest tests/test_plans.py::test_beat_positions_time_signature -x -q` | ❌ W0 | ⬜ pending |
| 26-04-02 | 01 | 1 | PLAN-01 | integration | `pytest tests/test_mcp_tools.py::test_generate_production_plan_tool -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_plans.py` — stubs for PLAN-01, PLAN-02, PLAN-03 (generate_production_plan, generate_section_plan, overrides)
- [ ] `tests/conftest.py` — update with plan fixtures if needed

*Existing infrastructure covers framework; only test files need to be added.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Token count for largest genre (neo_soul_rnb) is ≤ 400 | PLAN-01 | Requires tiktoken/actual tokenizer | Run `python -c "import tiktoken; enc = tiktoken.get_encoding('cl100k_base'); plan = ...; print(len(enc.encode(plan)))"` against generated output |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
