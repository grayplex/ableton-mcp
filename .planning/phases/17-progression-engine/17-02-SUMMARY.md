---
phase: 17-progression-engine
plan: 02
subsystem: tools/theory
tags: [mcp-tools, progression, integration-tests]
dependency_graph:
  requires: [progressions.py, theory/__init__.py]
  provides: [get_common_progressions tool, generate_progression tool, analyze_progression tool, suggest_next_chord tool]
  affects: [tools/theory.py, tests/test_theory.py]
tech_stack:
  added: []
  patterns: [aliased-import, json-dumps-format-error, midi-boundary-validation]
key_files:
  created: []
  modified:
    - MCP_Server/tools/theory.py
    - tests/test_theory.py
decisions:
  - All 4 tools follow established aliased-import + json.dumps + format_error pattern
  - MIDI range validation at tool boundary for tools returning chord notes
  - Empty input validation (numerals, chord_names, preceding) at tool layer before library call
metrics:
  duration: 120s
  completed: "2026-03-24T21:25:00Z"
  tasks: 2
  files: 2
  tests_added: 18
  tests_total_passing: 158
---

# Phase 17 Plan 02: Wire Progression MCP Tools Summary

4 MCP progression tools wired with aliased imports, MIDI boundary validation, json.dumps/format_error responses, and 18 integration tests covering registration, format, functionality, and error cases.

## Task Results

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Wire 4 progression MCP tools in theory.py | 5984f57 | MCP_Server/tools/theory.py |
| 2 | Add integration tests for all 4 progression tools | eed7b50 | tests/test_theory.py |

## What Was Built

### MCP Tools (4 new, total now 190)
1. **get_common_progressions** - Genre-filtered progression catalog with MIDI output, MIDI boundary validation
2. **generate_progression** - Voice-led chord sequences from Roman numerals, empty-input validation, MIDI boundary validation
3. **analyze_progression** - Roman numeral analysis of chord name sequences, empty-input validation
4. **suggest_next_chord** - Ranked next-chord suggestions with reasons, empty-input validation

### Integration Tests (18 new)
- TestProgressionTools class with full MCP protocol path coverage
- get_common_progressions: 5 tests (all, genre filter, chord format, key resolution, empty genre)
- generate_progression: 4 tests (basic, chord format, modal, empty numerals error)
- analyze_progression: 4 tests (basic, sevenths, chord format, empty error)
- suggest_next_chord: 4 tests (dominant resolution, format, genre filter, empty error)
- Registration test: 1 test (all 4 tools registered)

## Deviations from Plan

None - plan executed exactly as written. Task 1 (tool wiring) was already committed from a prior execution; Task 2 (integration tests) was staged but uncommitted and was committed in this session.

## Known Stubs

None - all tools fully functional with real library integration.

## Verification

- 18 new integration tests in TestProgressionTools: all passing
- 158 total theory tests: all passing, no regressions
- All 4 tools registered and callable end-to-end
- Total MCP tool count: 190
- All PROG-01 through PROG-04 requirements satisfied

## Self-Check: PASSED
