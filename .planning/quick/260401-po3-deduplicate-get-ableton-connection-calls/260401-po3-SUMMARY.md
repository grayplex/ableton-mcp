---
phase: quick
plan: 260401-po3
subsystem: orchestration
tags: [refactor, cleanup, connection-handling]
dependency_graph:
  requires: []
  provides: [single-connection-per-call-in-checkpoint, single-connection-per-call-in-next-actions]
  affects: [MCP_Server/orchestration/checkpoint.py, MCP_Server/orchestration/next_actions.py]
tech_stack:
  added: []
  patterns: [singleton-connection-reuse]
key_files:
  modified:
    - MCP_Server/orchestration/checkpoint.py
    - MCP_Server/orchestration/next_actions.py
decisions:
  - Use conn (already in scope from first get_ableton_connection call) throughout the clip loop
metrics:
  duration: ~5m
  completed: "2026-04-01T23:31:15Z"
  tasks: 2
  files: 2
---

# Quick Task 260401-po3: Remove Redundant get_ableton_connection Calls

**One-liner:** Eliminated duplicate `get_ableton_connection()` calls (conn2) in both orchestration functions — each now acquires the singleton connection exactly once per invocation.

## What Changed

Both `get_checkpoint` (checkpoint.py) and `get_transition_guidance` (next_actions.py) had the same pattern:

1. First `get_ableton_connection()` call assigned to `conn` for arrangement/mix state fetching
2. Second `get_ableton_connection()` call assigned to `conn2` for the per-track clip loop

Since `get_ableton_connection()` returns a global singleton, the second call was unnecessary and triggered an extra liveness ping under the mutex.

### Fix Applied

In both files:
- Deleted: `conn2 = get_ableton_connection()`
- Changed: `conn2.send_command(` → `conn.send_command(` in the clip loop

## Files Modified

- `MCP_Server/orchestration/checkpoint.py` — lines ~147-156 in `get_checkpoint`
- `MCP_Server/orchestration/next_actions.py` — lines ~213-222 in `get_transition_guidance`

## Commits

| Task | Description | Hash |
|------|-------------|------|
| 1    | Rebase onto misc-fixes | (rebase, no commit) |
| 2    | Remove conn2 from both orchestration files | 23a4ea8 |

## Verification

- `grep -n "conn2" checkpoint.py next_actions.py` returns no output (pass)
- `conn.send_command` appears in both initial block and clip loop in both files (pass)
- 29 passing tests still pass; pre-existing `test_arrangement_tools_registered` failure is unrelated to this change

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- `MCP_Server/orchestration/checkpoint.py` modified: FOUND
- `MCP_Server/orchestration/next_actions.py` modified: FOUND
- Commit `23a4ea8` exists: FOUND
