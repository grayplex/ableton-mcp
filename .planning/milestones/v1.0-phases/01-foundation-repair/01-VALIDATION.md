---
phase: 1
slug: foundation-repair
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-10
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ with pytest-asyncio 0.25+ |
| **Config file** | none — Wave 0 adds `[tool.pytest.ini_options]` to `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/ -x --timeout=10` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x --timeout=10`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | FNDN-01 | unit (grep-based) | `uv run pytest tests/test_python3_cleanup.py -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | FNDN-02 | unit (AST/grep) | `uv run pytest tests/test_python3_cleanup.py -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | FNDN-05 | unit (grep-based) | `uv run pytest tests/test_python3_cleanup.py::test_no_bare_excepts -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | FNDN-03 | unit | `uv run pytest tests/test_protocol.py -x` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | FNDN-04 | unit (threading) | `uv run pytest tests/test_connection.py -x` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 2 | FNDN-06 | unit | `uv run pytest tests/test_dispatch.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pyproject.toml` — add `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`
- [ ] `tests/__init__.py` — empty init for test package
- [ ] `tests/conftest.py` — shared fixtures (mock socket, mock Ableton connection)
- [ ] `tests/test_python3_cleanup.py` — grep-based tests for FNDN-01, FNDN-02, FNDN-05
- [ ] `tests/test_protocol.py` — length-prefix framing roundtrip tests for FNDN-03
- [ ] `tests/test_connection.py` — threading.Lock concurrent access tests for FNDN-04
- [ ] `tests/test_dispatch.py` — dict router tests for FNDN-06
- [ ] Framework install: `uv add --dev pytest>=8.3 pytest-asyncio>=0.25`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Instrument loading produces audible sound | FNDN-01, FNDN-02 | Requires live Ableton session with audio output | 1. Open Ableton with Remote Script loaded 2. Create MIDI track 3. Call load_instrument tool 4. Play notes — verify audio output |
| Concurrent MCP calls don't crash connection | FNDN-04 | Requires real MCP client sending parallel requests | 1. Start MCP server 2. Send 2+ tool calls simultaneously 3. Verify both return results without crash |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
