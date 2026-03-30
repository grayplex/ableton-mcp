---
phase: 9
slug: automation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ with pytest-asyncio 0.25+ |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_automation.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_automation.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | AUTO-01, AUTO-02, AUTO-03 | unit | `pytest tests/test_automation.py -x` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | AUTO-01, AUTO-02, AUTO-03 | unit | `pytest tests/test_registry.py::TestFullRegistry -x` | ✅ (needs update) | ⬜ pending |
| 09-02-01 | 02 | 1 | AUTO-01 | smoke | `pytest tests/test_automation.py::test_get_clip_envelope_list_mode -x` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 1 | AUTO-02 | smoke | `pytest tests/test_automation.py::test_insert_envelope_breakpoints -x` | ❌ W0 | ⬜ pending |
| 09-02-03 | 02 | 1 | AUTO-03 | smoke | `pytest tests/test_automation.py::test_clear_clip_envelopes_all -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_automation.py` — smoke tests for all 3 MCP automation tools (AUTO-01, AUTO-02, AUTO-03)
- [ ] `tests/test_registry.py` — update expected count from 60 to 63 (3 new commands)
- [ ] `tests/conftest.py` — add `MCP_Server.tools.automation.get_ableton_connection` to `_GAC_PATCH_TARGETS`

*Existing infrastructure covers framework and fixture setup.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Automation line visible in Ableton UI after insert | AUTO-02 | Requires running Ableton Live | Insert breakpoints via MCP tool, open clip envelope view in Ableton, verify automation line matches expected shape |
| insert_step third parameter (step_length) behavior | AUTO-02 | Undocumented API parameter | Test with step_length=0.0 and step_length=0.25 in Ableton, verify visual difference in envelope shape |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
