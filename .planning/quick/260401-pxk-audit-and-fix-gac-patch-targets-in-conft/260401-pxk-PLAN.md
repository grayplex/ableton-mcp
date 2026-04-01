# Quick Task 260401-pxk: audit and fix _GAC_PATCH_TARGETS in conftest.py

**Date:** 2026-04-01
**Mode:** quick

## Goal

Ensure all modules that import `get_ableton_connection` via `from ... import` are listed in `_GAC_PATCH_TARGETS` in `tests/conftest.py`, so that `mock_connection` fixture patches them correctly and no test attempts a real Ableton socket connection.

## Analysis

Grep of `from.*import.*get_ableton_connection` in `MCP_Server/` reveals these modules are missing from `_GAC_PATCH_TARGETS`:

| Module | File |
|---|---|
| `MCP_Server.orchestration.checkpoint` | `MCP_Server/orchestration/checkpoint.py` |
| `MCP_Server.orchestration.next_actions` | `MCP_Server/orchestration/next_actions.py` |
| `MCP_Server.tools.evaluation` | `MCP_Server/tools/evaluation.py` |
| `MCP_Server.tools.intelligence` | `MCP_Server/tools/intelligence.py` |
| `MCP_Server.tools.refinement` | `MCP_Server/tools/refinement.py` |

Excluded from patching (not direct `from ... import` or server init):
- `MCP_Server.server` — server init code, not a tool module called in tests
- `MCP_Server.__init__` — package init

## Tasks

### Task 1: Add missing modules to _GAC_PATCH_TARGETS

**Files:** `tests/conftest.py`

**Action:** Append 5 missing patch targets to `_GAC_PATCH_TARGETS` list:
- `"MCP_Server.orchestration.checkpoint.get_ableton_connection"`
- `"MCP_Server.orchestration.next_actions.get_ableton_connection"`
- `"MCP_Server.tools.evaluation.get_ableton_connection"`
- `"MCP_Server.tools.intelligence.get_ableton_connection"`
- `"MCP_Server.tools.refinement.get_ableton_connection"`

**Verify:** `_GAC_PATCH_TARGETS` contains all 24 entries (19 existing + 5 new)

**Done:** grep `_GAC_PATCH_TARGETS` in conftest.py shows all 5 new entries present
