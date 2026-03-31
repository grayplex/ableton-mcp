---
phase: 38-recommendation-tools-and-registration
plan: "01"
subsystem: sounds
tags: [mcp-tools, get_sound_recommendation, get_instrument_profile, pyproject, sound-selection]
dependency_graph:
  requires: [MCP_Server/sounds/catalog.py, MCP_Server/sounds/__init__.py]
  provides: [get_sound_recommendation MCP tool, get_instrument_profile MCP tool, MCP_Server.sounds in packages]
  affects: [MCP_Server/tools/sounds.py, pyproject.toml, tests/test_sounds.py]
tech_stack:
  added: []
  patterns: [mcp.tool decorator, format_error helper, json.dumps return pattern]
key_files:
  created: []
  modified:
    - MCP_Server/tools/sounds.py
    - pyproject.toml
    - tests/test_sounds.py
decisions:
  - "Tools delegate to catalog functions: recommend(), get_profile(), list_profiles() -- thin wrappers with error handling"
  - "None result from recommend() returns format_error, not an exception -- expected workflow for zero-score queries"
  - "None result from get_profile() enumerates available instruments in detail field -- aids recovery"
  - "MCP_Server.sounds, MCP_Server.genres, MCP_Server.mixing all added to pyproject.toml for completeness"
metrics:
  duration: "~3m"
  completed: "2026-03-31"
  tasks: 4
  files: 3
---

# Phase 38 Plan 01: Recommendation Tools and Registration Summary

**One-liner:** `get_sound_recommendation` and `get_instrument_profile` MCP tools wired to catalog scoring engine with error recovery, plus `MCP_Server.sounds` registered in `pyproject.toml`; completes v1.5 Sound Selection Intelligence milestone.

## What Was Built

### get_sound_recommendation MCP tool

Added to `MCP_Server/tools/sounds.py` with `@mcp.tool()` decorator. Delegates to `catalog.recommend(descriptor)` — tokenizes the descriptor, scores all 6 native instruments, and returns the top match as JSON. Handles the zero-score `None` return with a user-facing `format_error` pointing to `list_sound_descriptors()`.

Return shape (on success):
```python
{
    "id": "wavetable",
    "name": "Wavetable",
    "score": 1.65,
    "browser_path": "Instruments/Wavetable",
    "category_hint": "Pads",
    "reasoning": "Best match for 'warm pad': Wavetable scores 1.65 ..."
}
```

### get_instrument_profile MCP tool

Added to `MCP_Server/tools/sounds.py` with `@mcp.tool()` decorator. Delegates to `catalog.get_profile(instrument)` with alias normalization. On `None` result, enumerates all available instrument ids via `list_profiles()` in the error detail field to guide recovery.

### pyproject.toml packages registration

Added `"MCP_Server.sounds"`, `"MCP_Server.genres"`, and `"MCP_Server.mixing"` to the `packages` list in `[tool.setuptools]`. All three sub-packages were previously missing from the list.

### TestMCPTools test class

Appended `class TestMCPTools` to `tests/test_sounds.py` with 3 tests:
- `test_get_sound_recommendation_importable` — import + callable check
- `test_get_instrument_profile_importable` — import + callable check
- `test_all_three_tools_in_sounds_module` — all 3 tool names in `dir(sounds_module)`

## Test Results

All 65 tests in `tests/test_sounds.py` pass (3 new: TestMCPTools, 62 pre-existing).

```
python -m pytest tests/test_sounds.py -v
65 passed, 2 warnings in 1.20s
```

Import verification:
```
python -c "from MCP_Server.tools.sounds import get_sound_recommendation, get_instrument_profile, list_sound_descriptors; print('all 3 tools registered')"
all 3 tools registered
```

pyproject.toml verification:
```
grep "MCP_Server.sounds" pyproject.toml
packages = ["MCP_Server", "MCP_Server.tools", "MCP_Server.theory", "MCP_Server.sounds", "MCP_Server.genres", "MCP_Server.mixing"]
```

## Commits

- `3703388` test(38-01): add failing TestMCPTools class for get_sound_recommendation and get_instrument_profile
- `cd6fbb6` feat(38-01): add get_sound_recommendation and get_instrument_profile MCP tools
- `8062b67` feat(38): add MCP_Server.sounds to pyproject.toml packages list

## Deviations from Plan

None - plan executed exactly as written. All implementation was already in place as the prior session had completed these tasks. Verified all tests pass and all acceptance criteria met.

[Rule 3 - Blocking] Pre-existing `ModuleNotFoundError: No module named 'tiktoken'` in `test_genre_quality.py` prevented the full test suite from running with `-x`. Installed `tiktoken` via pip. The `test_arrangement.py::test_arrangement_tools_registered` failure is a pre-existing async framework issue (pytest-asyncio not recognized) unrelated to this plan's scope — out of scope per deviation boundary rules, logged here as deferred.

## Known Stubs

None. All three tools are fully wired to live catalog data.

## Self-Check: PASSED

- `/home/user/ableton-mcp/MCP_Server/tools/sounds.py` - FOUND (all 3 tools: list_sound_descriptors, get_sound_recommendation, get_instrument_profile)
- `/home/user/ableton-mcp/pyproject.toml` - FOUND (MCP_Server.sounds in packages list)
- `/home/user/ableton-mcp/tests/test_sounds.py` - FOUND (TestMCPTools class present)
- All 65 tests pass: `python -m pytest tests/test_sounds.py -v` exits 0
- Import check: all 3 tools importable from MCP_Server.tools.sounds
