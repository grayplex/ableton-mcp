---
phase: 15-chord-engine
plan: "02"
subsystem: theory/tools
tags: [chord-tools, mcp, fastmcp, integration-tests]
dependency_graph:
  requires: [15-01-chord-library]
  provides: [chord-mcp-tools]
  affects: [16-scale-engine]
tech_stack:
  added: []
  patterns: [tool-boundary-validation, format-error-responses, aliased-imports]
key_files:
  created: []
  modified:
    - MCP_Server/theory/__init__.py
    - MCP_Server/tools/theory.py
    - tests/test_theory.py
decisions:
  - "Aliased imports (_build_chord) to avoid name collision between tool function and library function"
  - "MIDI range validation at tool boundary for build_chord output and identify_chord input"
  - "Minimum 2 pitches validation for identify_chord at tool layer"
metrics:
  duration: "120s"
  completed: "2026-03-24"
  tasks_completed: 3
  tasks_total: 3
  test_count: 60
---

# Phase 15 Plan 02: Chord MCP Tools Summary

5 chord MCP tools wired to FastMCP with tool-boundary validation (MIDI range, minimum pitches), format_error responses, barrel exports updated, and 11 async integration tests verifying end-to-end tool execution through the server.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Update barrel exports in __init__.py | 77a87a5 | MCP_Server/theory/__init__.py |
| 2 | Wire 5 chord MCP tools with validation and error handling | a400cb7 | MCP_Server/tools/theory.py |
| 3 | Add integration tests for all 5 chord tools | eaa06d4 | tests/test_theory.py |

## What Was Built

### MCP_Server/theory/__init__.py (modified)

Added barrel exports for all 5 chord library functions: `build_chord`, `get_chord_inversions`, `get_chord_voicings`, `identify_chord`, `get_diatonic_chords`. Updated `__all__` to include all 7 theory exports (2 pitch + 5 chord).

### MCP_Server/tools/theory.py (modified)

Added 5 new `@mcp.tool()` decorated functions following the existing pattern established by `midi_to_note` and `note_to_midi`:

1. **build_chord** - Accepts root, quality, octave. Validates output MIDI range (0-127) at tool boundary. Returns JSON with chord info.
2. **get_chord_inversions** - Returns all inversions (root position through highest). JSON array output.
3. **get_chord_voicings** - Returns close/open/drop2/drop3 voicings. JSON dict output.
4. **identify_chord** - Accepts midi_pitches list. Validates minimum 2 pitches and MIDI range (0-127) at input. Returns ranked candidates.
5. **get_diatonic_chords** - Accepts key_name, scale_type. Returns triads and 7th chords with Roman numeral labels.

All tools use aliased imports (`_build_chord` etc.) to avoid name collision, wrap calls in try/except returning `format_error` on failure, and serialize results with `json.dumps(result, indent=2)`.

### tests/test_theory.py (modified)

Added `TestChordTools` class with 11 async integration tests:
- Tool registration check (all 5 tools discoverable)
- build_chord: C major MIDI values, A min7 octave 3, invalid quality error
- get_chord_inversions: C major triad returns 3 inversions
- get_chord_voicings: Cmaj7 returns all 4 voicing types
- identify_chord: C major identification, too few pitches error, out of range error
- get_diatonic_chords: C major (7 triads, 7 sevenths, Roman I), A minor (Roman i)

Total test suite: 60 tests passing (9 pitch unit + 34 chord unit + 7 pitch integration + 11 chord integration - 1 shared = 60).

## Deviations from Plan

None - plan executed exactly as written. All code was already committed from prior execution; Task 3 tests were staged but uncommitted.

## Decisions Made

1. **Aliased imports** - Library functions imported as `_build_chord` etc. to avoid name collision with the `@mcp.tool()` decorated functions that share the same public name.

2. **Tool-boundary validation** - MIDI range (0-127) checked at tool layer for both input (identify_chord) and output (build_chord), consistent with Phase 14 decision D-18.

3. **Minimum pitch count** - identify_chord validates at least 2 pitches before calling library, returning format_error for insufficient input.

## Verification Results

- `python -m pytest tests/test_theory.py -x -v` -- 60/60 passed
- `python -m pytest tests/test_theory.py::TestChordTools -x -v` -- 11/11 passed
- All 5 chord tools registered among 181 total tools
- Tool registration, happy paths, and error cases all verified

## Known Stubs

None - all tools fully wired to real library functions with complete validation.

## Self-Check: PASSED
