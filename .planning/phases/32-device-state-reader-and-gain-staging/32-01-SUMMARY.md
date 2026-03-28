---
phase: 32-device-state-reader-and-gain-staging
plan: 01
subsystem: api
tags: [ableton, remote-script, devices, gain-staging, meter-levels]

# Dependency graph
requires:
  - phase: 31-apply-recipe-and-batch-parameter-tools
    provides: devices.py RS handler infrastructure, recipe application patterns

provides:
  - get_mix_state RS command: single-call device parameter snapshot for all tracks
  - get_track_meters RS command: per-track output_meter_level readings with MIDI exclusion
  - GAIN_TARGETS constant: role-based dBFS target ranges for 9 mixing roles

affects:
  - 32-02 (MCP tools check_gain_staging and get_mix_state consume these RS handlers)
  - 33 (suggest_mix_adjustments will use get_mix_state output to diff against recipes)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Read-only RS handler with try/except and log_message on failure"
    - "Nested helper function (build_track_device_state) for per-track data assembly"
    - "MIDI scaffold track exclusion: has_midi_input and len(devices)==0"

key-files:
  created:
    - MCP_Server/devices/gain_targets.py
  modified:
    - AbletonMCP_Remote_Script/handlers/devices.py

key-decisions:
  - "get_mix_state includes all tracks even with zero devices (devices: []) — Phase 33 needs to know scaffold tracks exist"
  - "Parameters list is name+value only — no min/max/is_quantized to keep payload compact (D-02)"
  - "get_track_meters excludes MIDI tracks with len(devices)==0 to avoid false-positive gain flags (GAIN-02)"
  - "GAIN_TARGETS placed in MCP_Server/devices/gain_targets.py as pure data module (no imports needed)"

patterns-established:
  - "Phase 32 section block appended to devices.py after Phase 31 block"
  - "GAIN_TARGETS: dict[str, tuple[float, float]] uses Python 3.9+ inline type annotation"

requirements-completed: [STATE-01, GAIN-01, GAIN-02]

# Metrics
duration: 2min
completed: 2026-03-28
---

# Phase 32 Plan 01: Device State Reader and Gain Staging — RS Handlers Summary

**Two new RS command handlers for session-wide device state snapshot and per-track meter level reads, plus role-based dBFS gain targets data module**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-28T21:20:58Z
- **Completed:** 2026-03-28T21:22:00Z
- **Tasks:** 3
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- `get_mix_state` RS handler: returns device parameter snapshot for every device on every track (regular, return, master) in a single round-trip call
- `get_track_meters` RS handler: returns `output_meter_level` (0.0-1.0) per track with GAIN-02 exclusion for empty MIDI scaffold tracks
- `GAIN_TARGETS` data module: 9 mixing roles with `(low_dBFS, high_dBFS)` float tuples for gain staging analysis

## Task Commits

Each task was committed atomically:

1. **Task 1: Create MCP_Server/devices/gain_targets.py** - `85527c2` (feat)
2. **Task 2: Add get_mix_state RS command handler** - `e3f39d3` (feat)
3. **Task 3: Add get_track_meters RS command handler** - `e35d140` (feat)

## Files Created/Modified
- `MCP_Server/devices/gain_targets.py` - GAIN_TARGETS constant with 9 role dBFS target ranges
- `AbletonMCP_Remote_Script/handlers/devices.py` - Added Phase 32 section with get_mix_state and get_track_meters handlers

## Decisions Made
- `get_mix_state` includes tracks with zero devices (returns `devices: []`) — Phase 33 `suggest_mix_adjustments` needs to know these tracks exist when diffing against recipes
- Parameters trimmed to `{name, value}` only — no min/max to keep payload compact per D-02 scope decision
- `get_track_meters` MIDI exclusion: `has_midi_input and len(track.devices) == 0` targets empty scaffold tracks (v1.3 plan) specifically — not all MIDI tracks

## Deviations from Plan

None - plan executed exactly as written.

Note: The worktree required a `git checkout` of Phase 29-31 files from `gsd/v1.4-mix-master-intelligence` before executing, since this worktree branched from the v1.3 merge commit. This was necessary infrastructure bootstrapping, not a plan deviation.

## Issues Encountered
- Working tree was missing Phase 29-31 code (`MCP_Server/devices/`, `MCP_Server/mixing/`, etc.) — resolved by checking out the files from `gsd/v1.4-mix-master-intelligence` branch before execution began.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- RS handlers fully implemented and syntax-verified
- `GAIN_TARGETS` module importable and keys validated against ROLES
- Plan 32-02 can now implement `get_mix_state` and `check_gain_staging` MCP tools that call these handlers

---
*Phase: 32-device-state-reader-and-gain-staging*
*Completed: 2026-03-28*

## Self-Check: PASSED

- FOUND: MCP_Server/devices/gain_targets.py
- FOUND: AbletonMCP_Remote_Script/handlers/devices.py (with Phase 32 handlers)
- FOUND: .planning/phases/32-device-state-reader-and-gain-staging/32-01-SUMMARY.md
- FOUND commit 85527c2 (GAIN_TARGETS data module)
- FOUND commit e3f39d3 (get_mix_state handler)
- FOUND commit e35d140 (get_track_meters handler)
