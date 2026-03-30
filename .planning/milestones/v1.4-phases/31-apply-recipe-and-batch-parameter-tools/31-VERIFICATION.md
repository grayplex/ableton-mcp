---
phase: 31-apply-recipe-and-batch-parameter-tools
verified: 2026-03-28T21:00:00Z
status: passed
score: 6/6 must-haves verified
gaps: []
human_verification:
  - test: "apply_mix_recipe with a real Ableton session"
    expected: "Required devices load on the track and all parameters are set atomically"
    why_human: "RS handler uses schedule_message + response_queue for device loading — can only be confirmed against a live Ableton session"
  - test: "set_sidechain_source with a real Ableton compressor"
    expected: "Sidechain input routing changes to the named source track"
    why_human: "available_input_routing_types is only populated by Ableton Live's LOM — cannot be exercised in unit tests"
---

# Phase 31: Apply Recipe and Batch Parameter Tools Verification Report

**Phase Goal:** Users can apply a track mix recipe or master bus recipe to an Ableton track in one MCP call with atomic device loading, and set multiple parameters in a single socket round-trip
**Verified:** 2026-03-28T21:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can call apply_mix_recipe with track_index, role, genre and see devices loaded + params set in one call | VERIFIED | `MCP_Server/tools/mixing.py` `apply_mix_recipe` calls `send_command("apply_recipe", ...)` once with full normalized payload; TestBatchParameterSetting confirms single call |
| 2 | User can call apply_master_recipe with genre and see GlueCompressor + MultibandDynamics + Limiter applied to master track | VERIFIED | `apply_master_recipe` calls `send_command("apply_recipe", {"track_type": "master", ...})`; TestApplyMasterRecipe verifies all 3 device class names present |
| 3 | apply_recipe RS handler loads missing devices atomically — params set only after device confirmed instantiated | VERIFIED | `@command("apply_recipe", write=True, self_scheduling=True)` in devices.py; recursive `_load_next_device` + `_verify_recipe_load` + `response_queue` pattern; params only set inside `_apply_all_params` called after all loads confirmed |
| 4 | set_device_parameters RS handler sets multiple params in a single socket round-trip | VERIFIED | `@command("set_device_parameters", write=True)` iterates `parameters` dict, sets each param; single command registered in `_WRITE_COMMANDS` |
| 5 | User can call set_sidechain_source MCP tool with track_index, device_index, source_track_name and see sidechain routed | VERIFIED | `set_sidechain_source` MCP tool and RS handler both implemented; substring match on `available_input_routing_types`; TestSidechainSource confirms payload |
| 6 | Existing devices are updated in-place, not reloaded | VERIFIED | `_apply_recipe` builds `existing = {d.class_name: d for d in track.devices}` and splits to_load vs to_update; existing devices only have params set, not reloaded |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `MCP_Server/devices/convert.py` | `natural_to_normalized` and `convert_recipe_to_payload` | VERIFIED | Both functions implemented (91 lines); imports `CATALOG`; handles log, linear, linear_db, passthrough, clamping, unknown passthrough |
| `MCP_Server/mixing/catalog.py` | `get_master_recipe` public API | VERIFIED | `get_master_recipe(genre)` implemented with `_master_registry` parallel registry; alias resolution via `_GENRE_ALIASES` |
| `MCP_Server/mixing/house.py` | `MASTER_RECIPE` constant for house | VERIFIED | `MASTER_RECIPE` at line 650 with GlueCompressor, MultibandDynamics, Limiter |
| `MCP_Server/mixing/techno.py` | `MASTER_RECIPE` constant for techno | VERIFIED | `MASTER_RECIPE` at line 600 |
| `MCP_Server/mixing/ambient.py` | `MASTER_RECIPE` constant for ambient | VERIFIED | `MASTER_RECIPE` at line 614 |
| `MCP_Server/mixing/drum_and_bass.py` | `MASTER_RECIPE` constant for DnB | VERIFIED | `MASTER_RECIPE` at line 645 |
| `AbletonMCP_Remote_Script/handlers/devices.py` | `apply_recipe`, `set_device_parameters`, `set_sidechain_source` RS handlers | VERIFIED | All 3 handlers present at lines 2401, 2454, 2518; `DEVICE_PATHS` dict (12 entries); `import queue` and `import traceback` |
| `MCP_Server/tools/mixing.py` | `apply_mix_recipe`, `apply_master_recipe`, `set_sidechain_source` MCP tools | VERIFIED | All 3 tools defined and registered via `@mcp.tool()` decorator |
| `MCP_Server/connection.py` | `apply_recipe` in `_BROWSER_COMMANDS`; `set_device_parameters`, `set_sidechain_source` in `_WRITE_COMMANDS` | VERIFIED | `apply_recipe` in `_BROWSER_COMMANDS` (line 34); `set_device_parameters` and `set_sidechain_source` in `_WRITE_COMMANDS` (lines 183-184) |
| `tests/test_convert.py` | Unit tests for conversion functions | VERIFIED | 161 lines; `TestNaturalToNormalized` (11 tests) and `TestConvertRecipeToPayload` (4 tests) |
| `tests/test_mixing.py` | `TestMasterRecipeData`, `TestApplyMixRecipe`, `TestApplyMasterRecipe`, `TestSidechainSource`, `TestBatchParameterSetting` | VERIFIED | All 5 test classes present |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `MCP_Server/tools/mixing.py` | `MCP_Server/devices/convert.py` | `from MCP_Server.devices.convert import convert_recipe_to_payload` | WIRED | Import confirmed at line 8; `convert_recipe_to_payload` called in `apply_mix_recipe` and `apply_master_recipe` |
| `MCP_Server/tools/mixing.py` | `MCP_Server/mixing/catalog.py` | `from MCP_Server.mixing.catalog import get_master_recipe, get_recipe` | WIRED | Import confirmed at line 9; both functions called in their respective tools |
| `MCP_Server/tools/mixing.py` | `MCP_Server/connection.py` | `send_command("apply_recipe", ...)` | WIRED | `get_ableton_connection()` imported from connection; `send_command("apply_recipe", ...)` called in `apply_mix_recipe` (line 55) and `apply_master_recipe` (line 81) |
| `MCP_Server/devices/convert.py` | `MCP_Server/devices/catalog.py` | `from MCP_Server.devices.catalog import CATALOG` | WIRED | Import confirmed at line 15; `CATALOG.get(device_class)` used in `natural_to_normalized` |
| `MCP_Server/mixing/catalog.py` | genre modules (house, techno, ambient, drum_and_bass) | auto-discovery of `MASTER_RECIPE` via `pkgutil.iter_modules` | WIRED | `_discover_recipes()` checks `getattr(mod, "MASTER_RECIPE", None)` and stores in `_master_registry`; confirmed working via `get_master_recipe("house")` returning `['GlueCompressor', 'Limiter', 'MultibandDynamics']` |
| `AbletonMCP_Remote_Script/handlers/devices.py` | browser loading pattern | `self_scheduling=True` + `schedule_message` + `response_queue` | WIRED | `self_scheduling=True` at line 2518; `response_queue = queue.Queue()` at line 2557; `schedule_message` called at lines 2570, 2634, 2664 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `MCP_Server/tools/mixing.py::apply_mix_recipe` | `recipe` (dict) | `get_recipe(role, genre)` from mixing catalog via pkgutil auto-discovery | Yes — auto-discovers from real genre files with populated RECIPE constants | FLOWING |
| `MCP_Server/tools/mixing.py::apply_mix_recipe` | `devices_payload` (list) | `convert_recipe_to_payload(recipe)` using CATALOG conversion metadata | Yes — CATALOG populated from bootstrapped live Ableton data | FLOWING |
| `MCP_Server/tools/mixing.py::apply_master_recipe` | `recipe` (dict) | `get_master_recipe(genre)` from `_master_registry` | Yes — genre files have real MASTER_RECIPE constants with 3 device chains each | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 3 MCP tools importable | `python -c "from MCP_Server.tools.mixing import apply_mix_recipe, apply_master_recipe, set_sidechain_source; print('3 tools imported OK')"` | `3 tools imported OK` | PASS |
| get_master_recipe returns correct device keys | `python -c "from MCP_Server.mixing import get_master_recipe; r = get_master_recipe('house'); print(sorted(r.keys()))"` | `['GlueCompressor', 'Limiter', 'MultibandDynamics']` | PASS |
| Phase test suite passes | `python -m pytest tests/test_convert.py tests/test_mixing.py -x -q` | `62 passed in 0.11s` | PASS |
| natural_to_normalized and convert_recipe_to_payload importable | `python -c "from MCP_Server.devices.convert import natural_to_normalized, convert_recipe_to_payload; print('OK')"` | `OK` | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| BATCH-01 | 31-01, 31-02 | User can set multiple device parameters in a single socket call | SATISFIED | `set_device_parameters` RS handler iterates `parameters` dict in one call; registered in `_WRITE_COMMANDS`; TestBatchParameterSetting verifies single `send_command` call |
| APPLY-01 | 31-02 | User can apply a role x genre mix recipe to an Ableton track in one MCP tool call | SATISFIED | `apply_mix_recipe` MCP tool exists; converts recipe to normalized payload; sends single `apply_recipe` command; tests verify payload structure and single call. NOTE: REQUIREMENTS.md traceability table shows "Pending" — this is a documentation staleness issue, not a code gap. |
| APPLY-02 | 31-01, 31-02 | User can apply a genre master bus recipe to the Ableton master track in one MCP tool call | SATISFIED | `apply_master_recipe` MCP tool sends `apply_recipe` with `track_type="master"`; MASTER_RECIPE data exists for all 4 genres; TestApplyMasterRecipe verifies |
| APPLY-03 | 31-02 | Recipe application is atomic — params set only after device confirmed instantiated | SATISFIED | `apply_recipe` RS handler uses `self_scheduling=True` + recursive `schedule_message` + `response_queue`; `_verify_recipe_load` checks device count before advancing; params only set in `_apply_all_params` after all loads confirmed |
| SIDE-01 | 31-02 | User can set a compressor's sidechain input source by track name | SATISFIED | `set_sidechain_source` RS handler and MCP tool both implemented; substring match on `available_input_routing_types`; error lists available names if no match. NOTE: REQUIREMENTS.md traceability table shows "Pending" — documentation staleness, not a code gap. |

**Orphaned requirements check:** No requirements mapped to Phase 31 in REQUIREMENTS.md are unaccounted for.

**Documentation staleness note:** REQUIREMENTS.md traceability table marks APPLY-01 and SIDE-01 as "Pending" while the code fully implements both. The checkboxes in the requirement descriptions are also unchecked. This is a documentation update that was not made — the implementations are complete and tested.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | — |

No TODO/FIXME/placeholder comments, empty handlers, or hardcoded stubs were found in phase 31 files. All implementations are fully substantive.

**Pre-existing test failures (not introduced by phase 31):** Running the full test suite (`tests/`) shows 286 failures present on both `main` and the current branch. These are pre-existing failures in test files that use `await mcp_server.list_tools()` with a synchronous mock. The phase 31 test files (`test_convert.py`, `test_mixing.py`) pass cleanly (62/62). No regressions introduced.

### Human Verification Required

#### 1. apply_mix_recipe against live Ableton

**Test:** Open Ableton Live, connect the MCP server, call `apply_mix_recipe` with `track_index=0`, `role="kick"`, `genre="house"` on a track that has no devices.
**Expected:** EQ Eight, Compressor, and other kick/house recipe devices appear on the track with parameters set as specified in the recipe.
**Why human:** The RS `apply_recipe` handler uses `schedule_message` + `response_queue` for atomic device loading, which requires the Ableton main thread scheduler. Cannot exercise in unit tests.

#### 2. set_sidechain_source against live Ableton

**Test:** Add a Compressor to a track, call `set_sidechain_source` with `track_index` of that track, `device_index=0`, `source_track_name` matching another track's name.
**Expected:** The Compressor's sidechain source routing changes to the named track.
**Why human:** `available_input_routing_types` is only populated by Ableton's LOM at runtime — unit tests cannot verify routing resolution against real track names.

### Gaps Summary

No gaps found. All 5 phase requirements are satisfied with full implementation and passing tests.

The only notable discrepancy is documentation staleness: REQUIREMENTS.md traceability marks APPLY-01 and SIDE-01 as "Pending" and their requirement checkboxes are unchecked, despite complete implementation. This does not affect goal achievement — it is a documentation update task.

---

_Verified: 2026-03-28T21:00:00Z_
_Verifier: Claude (gsd-verifier)_
