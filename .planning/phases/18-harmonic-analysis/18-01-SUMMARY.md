---
phase: 18-harmonic-analysis
plan: 01
subsystem: theory-engine
tags: [harmonic-analysis, key-detection, chord-segmentation, harmonic-rhythm, music21]
dependency_graph:
  requires: [chords.py/identify_chord, progressions.py/analyze_progression, pitch.py/_force_sharp]
  provides: [analysis.py/detect_key, analysis.py/analyze_clip_chords, analysis.py/analyze_harmonic_rhythm]
  affects: [tests/test_theory.py]
tech_stack:
  added: []
  patterns: [lazy-music21-imports, time-grid-segmentation, krumhansl-schmuckler-key-detection]
key_files:
  created: [MCP_Server/theory/analysis.py]
  modified: [tests/test_theory.py]
decisions:
  - "Use chord root name (not full name) for analyze_progression input in harmonic rhythm"
  - "Melodic patterns with tonic emphasis needed for unambiguous Krumhansl-Schmuckler results"
requirements_completed: [ANLY-01, ANLY-02, ANLY-03]
metrics:
  duration: 346s
  completed: "2026-03-25T13:13:31Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 14
  tests_total_after: 172
---

# Phase 18 Plan 01: Harmonic Analysis Library Summary

Three pure-computation analysis functions (detect_key, analyze_clip_chords, analyze_harmonic_rhythm) using music21 KS algorithm for key detection, time-grid chord segmentation via identify_chord, and merged chord timeline with optional Roman numeral analysis.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create analysis.py library with 3 functions | 65691bb | MCP_Server/theory/analysis.py |
| 2 | Add TestAnalysisLibrary unit tests | c79cf6c | tests/test_theory.py, MCP_Server/theory/analysis.py |

## Implementation Details

### detect_key(notes)
- Builds music21 Stream from note dicts, calls `s.analyze('key')` for Krumhansl-Schmuckler analysis
- Returns top 3 candidates with key, mode, confidence (0-1, normalized via `max(0, correlationCoefficient)`)
- Applies `_force_sharp()` to tonic for consistent sharp-default spelling
- Raises ValueError on empty input

### analyze_clip_chords(notes, resolution, beats_per_bar)
- Time-grid segmentation at beat (1.0), half_beat (0.5), or bar (N) resolution
- QUANTIZE_WINDOW = 0.1 beats catches off-grid notes via nearest-grid snapping
- 2+ unique pitches: calls `identify_chord()`, returns chord segment with beat, chord, quality, root, notes, confidence
- 1 pitch: returns single_note segment with chord=None
- 0 pitches: segment omitted

### analyze_harmonic_rhythm(notes, resolution, beats_per_bar, key)
- Calls analyze_clip_chords, merges consecutive same-chord segments into timeline spans
- Computes stats: total_chords, average_changes_per_bar, most_common_duration
- Optional key parameter triggers Roman numeral analysis via analyze_progression using root names

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Roman numeral analysis used wrong chord name format**
- **Found during:** Task 2
- **Issue:** `analyze_harmonic_rhythm` passed full chord names (e.g., "C-major triad") to `analyze_progression`, which expects simple root names (e.g., "C"). Roman numerals were silently failing and being skipped.
- **Fix:** Added `root` field to timeline entries from segment data; use `root` instead of `chord` for `analyze_progression` input.
- **Files modified:** MCP_Server/theory/analysis.py
- **Commit:** c79cf6c

**2. [Rule 1 - Bug] detect_key test data produced ambiguous results**
- **Found during:** Task 2
- **Issue:** C major scale notes (C-D-E-F-G-A-B) score nearly identically for C major and A minor in Krumhansl-Schmuckler (A minor scored 0.8424 vs C major 0.8401). Tests expecting C major as top result failed.
- **Fix:** Changed test data to use melodic patterns with tonic triad emphasis (C-E-G-C-F-G-B-C) which strongly implies C major (0.722 vs next candidate 0.566).
- **Files modified:** tests/test_theory.py
- **Commit:** c79cf6c

## Verification Results

- `python -c "from MCP_Server.theory.analysis import detect_key, analyze_clip_chords, analyze_harmonic_rhythm"` -- OK
- `python -m pytest tests/test_theory.py::TestAnalysisLibrary -x -q` -- 14 passed
- `python -m pytest tests/test_theory.py -x -q` -- 172 passed (no regressions)

## Known Stubs

None -- all three functions are fully implemented and tested.

## Self-Check: PASSED
