---
phase: 11-check-for-live-object-model-gaps
plan: 01
subsystem: api
tags: [lom, gap-analysis, midi, note-expression, requirements]

# Dependency graph
requires:
  - phase: 10-routing-audio-clips
    provides: Complete v1 implementation (65 tools) to audit against LOM spec
provides:
  - Structured gap report (78 gaps across 12 LOM classes)
  - Note expression fields (probability, velocity_deviation, release_velocity)
  - 58 new v2 requirements across 13 categories
affects: [future v2 planning, arrangement, simpler, groove, device-extended]

# Tech tracking
tech-stack:
  added: []
  patterns: [hasattr guard for optional Live 11+ note fields, conditional spec_kwargs building]

key-files:
  created:
    - .planning/phases/11-check-for-live-object-model-gaps/11-GAP-REPORT.md
  modified:
    - AbletonMCP_Remote_Script/handlers/notes.py
    - MCP_Server/tools/notes.py
    - MCP_Server/tools/clips.py
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Keep pitch_fine -500..500 range per STATE.md decision (needs live testing to confirm)"
  - "Keep manual quantize implementation (works correctly, native method is v2 enhancement)"
  - "Note expression fields are optional via conditional spec_kwargs (backward compatible)"
  - "hasattr guard for note_id/probability/velocity_deviation/release_velocity in get_notes (Live 11+ only)"

patterns-established:
  - "Conditional spec_kwargs building: collect optional fields then unpack with **kwargs"
  - "hasattr guard for Live version-dependent note fields"

requirements-completed: []

# Metrics
duration: 5min
completed: 2026-03-18
---

# Phase 11 Plan 01: LOM Gap Report, Correctness Fixes & Requirements Update Summary

**78 LOM gaps documented across 12 classes, note expression fields (probability/velocity_deviation/release_velocity) added to MIDI handlers, 58 v2 requirements created across 13 categories**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-18T23:37:36Z
- **Completed:** 2026-03-18T23:42:11Z
- **Tasks:** 3 (Task 4 was commit-only, folded into per-task commits)
- **Files modified:** 5

## Accomplishments
- Created structured gap report organized by LOM class with Add/Backlog tiers and AI production value ratings
- Added optional note expression fields (probability, velocity_deviation, release_velocity) to add_notes_to_clip and get_notes
- Expanded REQUIREMENTS.md from 5 v2 categories to 13 v2 categories with 58 total requirements

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Gap Report** - `d27f15b` (docs)
2. **Task 2: Fix Correctness Issues Inline** - `ffcbe55` (feat)
3. **Task 3: Update REQUIREMENTS.md** - `9185e2c` (docs)

## Files Created/Modified
- `.planning/phases/11-check-for-live-object-model-gaps/11-GAP-REPORT.md` - Structured gap report with 78 gaps across 12 LOM classes
- `AbletonMCP_Remote_Script/handlers/notes.py` - Added probability, velocity_deviation, release_velocity to add_notes_to_clip; exposed note_id + expression fields in get_notes
- `MCP_Server/tools/notes.py` - Updated get_notes docstring to document new expression fields
- `MCP_Server/tools/clips.py` - Updated add_notes_to_clip docstring to document optional expression fields
- `.planning/REQUIREMENTS.md` - Added 13 v2 categories with 58 requirements from gap analysis

## Decisions Made
- Keep pitch_fine -500..500 range per STATE.md decision [10-01] -- needs live testing to confirm actual API range vs LOM spec
- Keep manual quantize implementation -- works correctly, native Clip.quantize is a v2 enhancement
- Note expression fields added as optional parameters with validation (backward compatible with existing callers)
- Used hasattr guard for note expression fields in get_notes since they are Live 11+ only

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Gap report provides complete prioritized backlog for v2 planning
- REQUIREMENTS.md now has full v2 scope (58 requirements) for roadmap creation
- Note expression fields are backward compatible -- existing callers unaffected

---
*Phase: 11-check-for-live-object-model-gaps*
*Completed: 2026-03-18*
