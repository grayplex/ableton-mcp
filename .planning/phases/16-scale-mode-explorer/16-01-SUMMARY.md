---
phase: 16-scale-mode-explorer
plan: 01
subsystem: theory-engine
tags: [scales, music-theory, music21, catalog, detection]
dependency_graph:
  requires: [theory-foundation, chord-engine]
  provides: [scale-library, scale-catalog, scale-detection, harmonic-minor-chords, melodic-minor-chords]
  affects: [theory-tools, chord-tools]
tech_stack:
  added: []
  patterns: [interval-based-pitch-generation, pitch-class-set-comparison, mode-rotation]
key_files:
  created:
    - MCP_Server/theory/scales.py
  modified:
    - MCP_Server/theory/__init__.py
    - MCP_Server/theory/chords.py
    - tests/test_theory.py
decisions:
  - "Interval-based construction for all 38 scales (consistent, no music21 class dependency)"
  - "Pitch class set comparison for scale detection (456 comparisons, trivially fast)"
  - "Mode rotation derived from major scale intervals with root transposition"
  - "music21.scale.HarmonicMinorScale/MelodicMinorScale for diatonic chord pitch context"
metrics:
  duration: 8min
  completed: "2026-03-24T16:04:49Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 3
  tests_added: 31
  tests_total: 73
---

# Phase 16 Plan 01: Scale Library with SCALE_CATALOG and 5 Functions Summary

Scale library with 38-scale catalog, 5 public functions, and harmonic/melodic minor diatonic chord support via interval-based construction and pitch class set operations.

## What Was Built

### Task 1: scales.py Library with SCALE_CATALOG and 5 Functions

Created `MCP_Server/theory/scales.py` with:

- **SCALE_CATALOG**: 38 scales across 8 categories (diatonic, modal, minor_variant, pentatonic, blues, symmetric, bebop, world), each with interval patterns, category, music21_class mapping, and aliases
- **list_scales()**: Returns full catalog as list of dicts with name, intervals, category, note_count
- **get_scale_pitches()**: Generates MIDI note objects for any scale from root/octave using interval-based pitch construction
- **check_notes_in_scale()**: Classifies MIDI pitches as in-scale or out-of-scale using pitch class set comparison
- **get_related_scales()**: Computes parallel (same root), relative (same key sig), and modal relationships via interval rotation
- **detect_scales_from_notes()**: Ranks top 5 candidate scales by coverage percentage with simplicity tiebreak across all 38 scales x 12 roots

Updated `MCP_Server/theory/__init__.py` with barrel exports for all 5 scale functions.

### Task 2: Extended get_diatonic_chords for Harmonic/Melodic Minor

Extended `get_diatonic_chords()` in `MCP_Server/theory/chords.py` to accept:
- `"harmonic_minor"`: Roman numerals i, iio, III+, iv, V, VI, viio with augmented III and major V
- `"melodic_minor"`: Roman numerals i, ii, III+, IV, V, vio, viio with augmented III and major IV

Uses `music21.scale.HarmonicMinorScale`/`MelodicMinorScale` for pitch generation context while keeping minor key for Roman numeral resolution.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 (RED) | 52a2edc | Failing tests for scale library (21 tests) |
| 1 (GREEN) | dc94573 | Scale library implementation with 38-scale catalog and 5 functions |
| 2 (RED) | 3233c49 | Failing tests for harmonic/melodic minor diatonic chords (10 tests) |
| 2 (GREEN) | 6d978dd | Extended get_diatonic_chords for harmonic_minor and melodic_minor |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Theory module files missing from worktree**
- **Found during:** Task 1 setup
- **Issue:** This worktree branch did not contain `MCP_Server/theory/` or `tests/test_theory.py` from phases 14-15
- **Fix:** Copied files from main repo to establish the foundation for scale work
- **Files copied:** pitch.py, chords.py, __init__.py, test_theory.py, tools/theory.py

**2. [Rule 3 - Blocking] ROADMAP.md merge conflict**
- **Found during:** Task 1 RED phase commit
- **Issue:** Unresolved merge conflict in ROADMAP.md blocking all commits
- **Fix:** Resolved conflict keeping the incoming milestone content
- **Files modified:** .planning/ROADMAP.md

### Out of Scope

Integration tests (TestTheoryTools, TestChordTools) fail because server.py in this worktree doesn't import the theory tools module. This is a pre-existing issue from the worktree not having the full theory phase merged. All 73 unit tests pass.

## Decisions Made

1. **Interval-based construction for all scales**: Rather than using music21 scale classes where available, all 38 scales use consistent interval-based pitch generation. Simpler, more predictable, no dependency on music21 class coverage.
2. **Pitch class set comparison**: Scale detection and note validation both use pitch class sets (midi % 12) for efficient comparison across 456 root/scale combinations.
3. **Mode rotation from major intervals**: Modal relationships computed by rotating the major scale interval pattern and tracking root transposition, rather than using music21 mode APIs.

## Known Stubs

None - all functions are fully implemented with real logic.

## Verification Results

- 73 unit tests passing (8 pitch + 44 chord + 21 scale)
- All 5 scale functions importable from MCP_Server.theory
- SCALE_CATALOG contains exactly 38 scales
- get_diatonic_chords accepts harmonic_minor and melodic_minor
- No regressions in existing pitch or chord tests

## Self-Check: PASSED

All files exist, all 4 commits verified.
