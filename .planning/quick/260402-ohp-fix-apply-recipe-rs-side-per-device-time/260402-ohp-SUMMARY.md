---
phase: quick
plan: 260402-ohp
title: "Fix apply_recipe RS-side per-device timeout"
completed: "2026-04-02T22:41:12Z"
duration: "~1m"
tasks_completed: 2
tasks_total: 2
key-files:
  modified:
    - MCP_Server/tools/mixing.py
    - AbletonMCP_Remote_Script/handlers/devices.py
    - tests/test_mixing.py
decisions:
  - "Compute timeout as max(30.0, len(devices) * 15.0) giving 15s per device with 30s floor"
---

# Quick 260402-ohp: Fix apply_recipe RS-side per-device timeout

MCP-side computes dynamic timeout based on device count and passes it to RS via command payload; RS uses that budget instead of hardcoded 30s.

## Commits

| Hash | Message |
|------|---------|
| 4c4a732 | fix(quick-260402-ohp): pass timeout in apply_recipe payload and use it on RS side |
| 416a4f9 | test(quick-260402-ohp): add timeout passthrough assertions to recipe tests |

## Changes

### Task 1: Pass timeout in command payload and use it on RS side

- `MCP_Server/tools/mixing.py`: Both `apply_mix_recipe` and `apply_master_recipe` now compute `timeout = max(30.0, len(devices_payload) * 15.0)` and include it in the command payload dict alongside passing it as the `send_command` kwarg.
- `AbletonMCP_Remote_Script/handlers/devices.py`: `_apply_recipe` reads `total_timeout = params.get("timeout", 30.0)` and uses it for `response_queue.get(timeout=total_timeout)` instead of the hardcoded 30s.

### Task 2: Add test coverage for timeout passthrough

- `tests/test_mixing.py`: Added assertions to `test_valid_recipe_calls_send_command` and `test_valid_genre_calls_with_master_track_type` verifying that the payload `timeout` field exists and matches the `send_command` timeout kwarg.

## Deviations from Plan

**1. [Rule 2 - Missing functionality] Added timeout computation to MCP side**
- Plan assumed `timeout` was already computed in mixing.py. It was not -- neither function computed a timeout or passed `timeout=` kwarg to `send_command`.
- Added `timeout = max(30.0, len(devices_payload) * 15.0)` computation and `timeout=timeout` kwarg to both functions.

## Verification

All 47 tests in `tests/test_mixing.py` pass.

## Known Stubs

None.

## Self-Check: PASSED
