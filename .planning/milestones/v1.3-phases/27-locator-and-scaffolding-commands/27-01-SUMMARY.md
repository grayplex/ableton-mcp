---
phase: 27-locator-and-scaffolding-commands
plan: 01
subsystem: arrangement
tags: [scaffold, locators, tracks, cue-points, mcp-tool, remote-script]

requires:
  - phase: 26-production-plan-builder
    provides: generate_production_plan output format with sections, bar_start, roles

provides:
  - scaffold_arrangement MCP tool converting production plans to Ableton locators + tracks
  - create_locator_at Remote Script handler for atomic cue point creation
  - scaffold_tracks Remote Script handler for batch MIDI track creation
  - _deduplicate_roles helper for role-count-based track naming
  - _bar_to_beat helper for time-signature-aware bar-to-beat conversion

affects: [27-02, 28-section-execution]

tech-stack:
  added: []
  patterns: [role-dedup-suffix-naming, bar-to-beat-conversion, toggle-safe-locator-creation]

key-files:
  created:
    - AbletonMCP_Remote_Script/handlers/scaffold.py
    - MCP_Server/tools/scaffold.py
    - tests/test_scaffold.py
  modified:
    - AbletonMCP_Remote_Script/handlers/__init__.py
    - MCP_Server/tools/__init__.py
    - MCP_Server/connection.py
    - tests/conftest.py

key-decisions:
  - "Role dedup counts sections containing each role: lead in 3 sections = lead, lead 2, lead 3"
  - "Toggle safety: existing cue at target position renamed instead of toggled off"
  - "Playhead saved/restored around locator creation to avoid disrupting user position"

patterns-established:
  - "Scaffold handler mixin: ScaffoldHandler with @command(..., write=True) pattern"
  - "Side-effect factory in tests: _mock_send_command_factory dispatches by command name"

requirements-completed: [SCAF-01]

duration: 7min
completed: 2026-03-28
---

# Phase 27 Plan 01: Scaffold Arrangement Summary

**scaffold_arrangement MCP tool writes production plans into Ableton as named locators at time-sig-aware beat positions and deduplicated MIDI tracks in one operation**

## What Was Built

### Remote Script Handlers (AbletonMCP_Remote_Script/handlers/scaffold.py)

- `create_locator_at`: Creates a named cue point at a specific beat position with toggle safety (renames existing cue instead of deleting). Saves/restores playhead position.
- `scaffold_tracks`: Batch-creates named MIDI tracks from a list of track names.

### MCP Tool (MCP_Server/tools/scaffold.py)

- `scaffold_arrangement(plan)`: Accepts a production plan dict, reads session time signature from Ableton, creates locators for each section at the correct beat position, deduplicates roles into track names, and batch-creates MIDI tracks. Returns JSON with locators_created, tracks_created, track_names, and any locator_errors.

### Pure Helper Functions

- `_deduplicate_roles(sections)`: Counts how many sections contain each role, generates track names with numbered suffixes (e.g., "lead", "lead 2", "lead 3"), preserving first-seen order.
- `_bar_to_beat(bar_start, beats_per_bar)`: Converts 1-based bar number to 0-based beat position using time-signature-derived beats_per_bar.

### Registration

- Handler registered in `AbletonMCP_Remote_Script/handlers/__init__.py`
- Tool registered in `MCP_Server/tools/__init__.py`
- `create_locator_at` and `scaffold_tracks` added to `_WRITE_COMMANDS` in `MCP_Server/connection.py`
- Patch target added to `tests/conftest.py`

## Tests

13 tests in tests/test_scaffold.py:
- TestRoleDeduplication (4 tests): single occurrence, multiple occurrences with suffixes, empty sections, first-seen ordering
- TestBarToBeat (3 tests): 4/4, 3/4, 6/8 time signatures
- TestScaffoldArrangement (5 tests): full flow with locators+tracks, 4/4 beat positions, 3/4 beat positions, missing sections error, partial failure with error reporting
- test_scaffold_tools_registered: tool registration check

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test_single_occurrence_per_role test data**
- **Found during:** Task 1
- **Issue:** Plan spec listed roles [["kick","bass"],["kick","lead"]] expecting ["kick","bass","lead"], but kick appearing in 2 sections would produce ["kick","kick 2","bass","lead"] per the dedup algorithm. Test name "single_occurrence_per_role" implied each role should appear in only one section.
- **Fix:** Changed test data so each role appears in exactly one section: [["kick","bass"],["lead","pad"]] -> ["kick","bass","lead","pad"]
- **Files modified:** tests/test_scaffold.py
- **Commit:** a79c771

**2. [Rule 1 - Bug] Fixed test_creates_locators_and_tracks expected track count**
- **Found during:** Task 2
- **Issue:** Test expected tracks_created=3 but kick in 2 sections produces 4 tracks (kick, kick 2, bass, lead)
- **Fix:** Changed assertion to tracks_created=4
- **Files modified:** tests/test_scaffold.py
- **Commit:** 8144374

## Known Stubs

None -- all data flows are wired and functional.

## Pre-existing Issues Noted

test_plan_tools.py module-level sys.modules mocking poisons mcp_server fixture for all test files when collected together. This affects test_arrangement.py, test_audio_clips.py, and other files using the async mcp_server fixture. Not introduced by this plan.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | a79c771 | Pure helper functions + Remote Script handler + tests (7 passing) |
| 2 | 8144374 | scaffold_arrangement MCP tool + registration + integration tests (13 passing) |
