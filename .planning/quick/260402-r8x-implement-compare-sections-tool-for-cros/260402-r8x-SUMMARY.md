---
phase: quick-260402-r8x
plan: 01
subsystem: refinement
tags: [mcp-tool, comparison, section-state, tdd]
dependency_graph:
  requires: [get_section_state]
  provides: [compare_sections]
  affects: [refinement-workflow]
tech_stack:
  added: []
  patterns: [structured-diff, track-matching-by-name]
key_files:
  created:
    - tests/test_compare_sections.py
  modified:
    - MCP_Server/tools/refinement.py
    - .planning/codebase/CONCERNS.md
decisions:
  - "Mock get_section_state directly in tests rather than mocking the full Ableton connection chain"
  - "Match tracks by exact track_name between sections; unmatched tracks go to only_in_a/only_in_b"
metrics:
  duration: "~4 minutes"
  completed: "2026-04-03"
  tasks: 2
  files: 3
---

# Quick Task 260402-r8x: Implement compare_sections Tool Summary

**compare_sections MCP tool for cross-section diffing: per-track comparison of clips, notes, pitch, mix, and devices**

## What Was Done

### Task 1: Implement compare_sections tool and unit tests (TDD)

Added `compare_sections` function in `MCP_Server/tools/refinement.py` registered as `@mcp.tool()`. The tool accepts two section names and an optional genre parameter, calls `get_section_state` for each, and returns a structured diff including:

- `only_in_a` / `only_in_b`: tracks exclusive to one section
- `track_diffs`: per-track comparison with clip counts, total notes, average rhythm density, pitch ranges, mix volume/pan, and device chain differences (a-only, b-only, both)
- `bar_ranges`: start/end bars for both sections
- Error handling: if either section is not found, returns early with error field and `diff: None`

6 unit tests cover: overlapping tracks, exclusive tracks, section-not-found (A and B), identical sections, and genre passthrough.

### Task 2: Update CONCERNS.md

Marked SNAP-03 (Cross-section comparison) as RESOLVED with reference to this task.

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 (RED) | f439634 | Failing tests for compare_sections |
| 1 (GREEN) | b5ed4a9 | Implement compare_sections MCP tool |
| 2 | 7bc2080 | Mark SNAP-03 resolved in CONCERNS.md |

## Known Stubs

None.

## Self-Check: PASSED

- [x] `MCP_Server/tools/refinement.py` contains `def compare_sections`
- [x] `tests/test_compare_sections.py` exists with 6 tests
- [x] CONCERNS.md has SNAP-03 RESOLVED
- [x] All 3 commits exist in git log
