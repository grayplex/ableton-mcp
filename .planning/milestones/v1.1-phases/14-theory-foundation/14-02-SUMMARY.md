---
phase: 14-theory-foundation
plan: 02
subsystem: theory-tools
tags: [mcp-tools, theory, midi, pitch, testing]
dependency_graph:
  requires: [music21-dependency, theory-package, pitch-mapping]
  provides: [theory-mcp-tools, theory-tests]
  affects: [MCP_Server.tools, tests]
tech_stack:
  added: []
  patterns: [mcp-tool-wiring, boundary-validation, integration-testing]
key_files:
  created:
    - MCP_Server/tools/theory.py
    - tests/test_theory.py
  modified:
    - MCP_Server/tools/__init__.py
decisions:
  - "MIDI range validation at tool layer (0-127) returning format_error, not at library layer"
  - "Alias imports (_midi_to_note, _note_to_midi) to avoid name collision with tool function names"
requirements_completed: [THRY-01, THRY-02, THRY-03]
metrics:
  duration: 83s
  completed: "2026-03-24T11:18:12Z"
  tasks: 2
  files: 3
---

# Phase 14 Plan 02: Theory Tool Wiring and Tests Summary

Two MCP tools (midi_to_note, note_to_midi) wired from theory library with boundary validation, plus 15-test suite covering unit roundtrips and integration error handling.

## What Was Built

### Task 1: Create MCP tools and register in tools/__init__.py
- **Commit:** `9ea5ac9`
- `MCP_Server/tools/theory.py` -- Two `@mcp.tool()` functions following existing pattern
  - `midi_to_note(ctx, midi_number, key_context=None)` -- MIDI int to note JSON, with 0-127 range validation
  - `note_to_midi(ctx, note_name)` -- note name to MIDI JSON, with out-of-range result check
  - Both return `json.dumps(result, indent=2)` on success, `format_error(...)` on failure
- `MCP_Server/tools/__init__.py` -- Added `theory` to import line (alphabetical between session and tracks)
- Total registered tools: 176

### Task 2: Create comprehensive test suite for theory library and tools
- **Commit:** `e9d47ba`
- `tests/test_theory.py` -- 15 tests in two classes
  - **TestPitchLibrary** (8 unit tests): middle C, roundtrip all 128, sharps default, key-aware enharmonic, boundaries, note formats
  - **TestTheoryTools** (7 integration tests): tool registration, JSON output, key context, out-of-range errors, invalid input errors
- All 219 tests pass (204 existing + 15 new), zero regressions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed incorrect Eb3 expected MIDI value in test**
- **Found during:** Task 2
- **Issue:** Plan specified `note_to_midi("Eb3")["midi"] == 63` but Eb3 is MIDI 51 (D#4 is 63)
- **Fix:** Corrected expected value to 51
- **Files modified:** `tests/test_theory.py`
- **Commit:** `e9d47ba`

## Verification Results

- `midi_to_note` and `note_to_midi` registered in MCP tool list (176 total tools)
- `midi_to_note(60)` returns JSON `{"midi": 60, "name": "C4", "octave": 4, "pitch_class": "C"}`
- `note_to_midi("C4")` returns JSON `{"name": "C4", "midi": 60}`
- Invalid MIDI values (-1, 128) return format_error, not crash
- Invalid note names return format_error, not crash
- All 219 tests pass (15 theory + 204 existing)

## Known Stubs

None -- all tools are fully implemented with no placeholder data.

## Self-Check: PASSED

- All created files exist on disk
- All commit hashes found in git log
- All verification tests pass
