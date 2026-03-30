---
phase: 2
slug: infrastructure-refactor
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ with pytest-asyncio 0.25+ |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v --timeout=10` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v --timeout=10 && uv run ruff check MCP_Server/ AbletonMCP_Remote_Script/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-* | 01 | 1 | FNDN-08 | unit | `uv run pytest tests/test_registry.py -x` | ❌ W0 | ⬜ pending |
| 02-02-* | 02 | 1 | FNDN-08 | unit | `uv run pytest tests/test_registry.py -x` | ❌ W0 | ⬜ pending |
| 02-03-* | 03 | 2 | FNDN-07 | smoke | `uv run pytest tests/test_session.py tests/test_tracks.py tests/test_clips.py -x` | ❌ W0 | ⬜ pending |
| 02-04-* | 04 | 2 | FNDN-09, FNDN-10 | lint+smoke | `uv run ruff check MCP_Server/ AbletonMCP_Remote_Script/ && uv run pytest tests/ -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_session.py` — smoke tests for session/connection tools (FNDN-07)
- [ ] `tests/test_tracks.py` — smoke tests for tracks tools (FNDN-07)
- [ ] `tests/test_clips.py` — smoke tests for clips tools (FNDN-07)
- [ ] `tests/test_transport.py` — smoke tests for transport tools (FNDN-07)
- [ ] `tests/test_devices.py` — smoke tests for devices tools (FNDN-07)
- [ ] `tests/test_browser.py` — smoke tests for browser tools (FNDN-07)
- [ ] `tests/test_registry.py` — command registry decorator tests (FNDN-08)
- [ ] Updated `tests/conftest.py` — mock_connection fixture, mcp_server fixture
- [ ] `pyproject.toml` ruff config (FNDN-09)
- [ ] `ruff` dev dependency — `uv add --dev ruff`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Remote Script loads in Ableton | FNDN-08 | Requires running Ableton Live instance | Install script, open Ableton, verify "AbletonMCP initialized" in log |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
