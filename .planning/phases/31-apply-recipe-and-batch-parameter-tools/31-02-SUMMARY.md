---
phase: 31-apply-recipe-and-batch-parameter-tools
plan: "02"
subsystem: mixing-tools
tags: [mcp-tools, rs-handlers, recipe-application, batch-parameters, sidechain]
dependency_graph:
  requires: ["31-01"]
  provides: ["apply_mix_recipe", "apply_master_recipe", "set_sidechain_source", "apply_recipe_rs", "set_device_parameters_rs", "set_sidechain_source_rs"]
  affects: ["MCP_Server/tools/mixing.py", "AbletonMCP_Remote_Script/handlers/devices.py", "MCP_Server/connection.py"]
tech_stack:
  added: []
  patterns: ["self_scheduling RS handler", "response_queue atomic device loading", "natural-to-normalized conversion pipeline"]
key_files:
  created:
    - MCP_Server/tools/mixing.py
  modified:
    - AbletonMCP_Remote_Script/handlers/devices.py
    - MCP_Server/connection.py
    - tests/conftest.py
    - tests/test_mixing.py
decisions:
  - "D-01: apply_recipe RS handler uses recursive schedule_message pattern for sequential multi-device loading"
  - "D-02: DEVICE_PATHS dict maps 12 CATALOG class names to browser paths at module level"
  - "D-03: set_sidechain_source uses case-insensitive substring match on display_name for routing resolution"
metrics:
  duration: "4min"
  completed: "2026-03-28T20:03:00Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 15
  tests_total: 62
---

# Phase 31 Plan 02: RS Handlers and MCP Tools for Recipe Application Summary

Three RS handlers (apply_recipe with self_scheduling atomic load+set, set_device_parameters for batch param setting, set_sidechain_source for name-based routing) and three MCP tools (apply_mix_recipe, apply_master_recipe, set_sidechain_source) wired end-to-end with natural-to-normalized conversion pipeline.

## What Was Built

### RS Handlers (AbletonMCP_Remote_Script/handlers/devices.py)

1. **set_device_parameters** (BATCH-01): Sets multiple device parameters in a single call. Case-insensitive name lookup with min/max clamping.

2. **set_sidechain_source** (SIDE-01): Resolves source track name to routing type via case-insensitive substring match on `available_input_routing_types` display names. Sets first available channel automatically.

3. **apply_recipe** (APPLY-03): Self-scheduling handler that atomically loads missing devices and sets all parameters. Uses recursive `schedule_message` pattern: loads devices sequentially (one per tick with verification), then sets all params after all devices confirmed. Retry logic for failed loads. `DEVICE_PATHS` dict maps 12 CATALOG class names to browser paths.

### MCP Tools (MCP_Server/tools/mixing.py)

4. **apply_mix_recipe** (APPLY-01): Looks up role x genre recipe, converts natural-unit values to normalized via `convert_recipe_to_payload`, sends single `apply_recipe` command.

5. **apply_master_recipe** (APPLY-02): Looks up master recipe, converts and sends to master track. Expected devices: GlueCompressor, MultibandDynamics, Limiter.

6. **set_sidechain_source** (SIDE-01): Passes track name directly to RS handler for runtime routing resolution.

### Infrastructure

- `DEVICE_PATHS` dict at module level in devices.py (12 entries)
- `apply_recipe` added to `_BROWSER_COMMANDS` (30s timeout for multi-device loading)
- `set_device_parameters` and `set_sidechain_source` added to `_WRITE_COMMANDS` (15s timeout)
- `MCP_Server.tools.mixing.get_ableton_connection` added to conftest `_GAC_PATCH_TARGETS`

## Tests

- 15 new tests across 4 test classes (TestApplyMixRecipe, TestApplyMasterRecipe, TestSidechainSource, TestBatchParameterSetting)
- 62 total tests passing (47 mixing + 15 convert)
- Tests verify: payload structure, normalized params, single send_command call, master track type, error messages, sidechain routing params

## Requirements Fulfilled

| Requirement | Description | Implementation |
|-------------|-------------|----------------|
| BATCH-01 | set_device_parameters RS handler | Batch param setting in single call |
| APPLY-01 | apply_mix_recipe MCP tool | Single-call track recipe application |
| APPLY-02 | apply_master_recipe MCP tool | Single-call master chain application |
| APPLY-03 | apply_recipe RS handler atomicity | self_scheduling + schedule_message pattern |
| SIDE-01 | set_sidechain_source name resolution | Substring match on routing display names |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan 01 dependency files not on current branch**
- **Found during:** Task 1 (pre-execution)
- **Issue:** Plan 31-02 depends on 31-01 outputs (devices/catalog, mixing recipes, convert.py) which were on a parallel worktree branch
- **Fix:** Extracted files from 31-01 commit (2875519) via `git show` and committed as dependency inclusion
- **Files added:** MCP_Server/devices/, MCP_Server/mixing/, tests/test_convert.py
- **Commit:** e2d1643

## Known Stubs

None -- all tools are fully wired to real recipe data and RS handlers.

## Self-Check: PASSED

- All 5 key files verified present
- All 4 commits verified: 2679a68, 4611364, 65a1de3, e2d1643
- 62 tests passing (test_mixing.py + test_convert.py)
