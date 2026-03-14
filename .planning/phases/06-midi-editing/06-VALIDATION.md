---
phase: 6
slug: midi-editing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ with pytest-asyncio 0.25+ |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/test_notes.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_notes.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | MIDI-01 | smoke | `pytest tests/test_notes.py::test_add_notes_returns_json -x` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | MIDI-02 | smoke | `pytest tests/test_notes.py::test_get_notes_returns_json -x` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 1 | MIDI-03 | smoke | `pytest tests/test_notes.py::test_remove_notes_returns_json -x` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 1 | MIDI-04 | smoke | `pytest tests/test_notes.py::test_quantize_notes_returns_json -x` | ❌ W0 | ⬜ pending |
| 06-03-02 | 03 | 1 | MIDI-05 | smoke | `pytest tests/test_notes.py::test_transpose_notes_returns_json -x` | ❌ W0 | ⬜ pending |
| 06-04-01 | 04 | 1 | MIDI-01 | smoke | `pytest tests/test_notes.py::test_note_tools_registered -x` | ❌ W0 | ⬜ pending |
| 06-04-02 | 04 | 1 | MIDI-01 | smoke | `pytest tests/test_notes.py::test_add_notes_json_format -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_notes.py` — stubs for MIDI-01 through MIDI-05 (smoke tests with mocked connection)
- [ ] Add `"MCP_Server.tools.notes.get_ableton_connection"` to `_GAC_PATCH_TARGETS` in conftest.py

*Existing pytest infrastructure covers framework install — no new dependencies needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Notes appear and play back in Live | MIDI-01 | Requires running Ableton Live | Add notes via MCP tool, verify in clip view |
| Removed notes disappear from clip | MIDI-03 | Requires running Ableton Live | Remove notes via MCP tool, verify in clip view |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
