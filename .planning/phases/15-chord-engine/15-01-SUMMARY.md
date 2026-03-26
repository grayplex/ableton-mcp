---
phase: 15-chord-engine
plan: "01"
subsystem: theory/chords
tags: [chord-engine, music21, theory, library]
dependency_graph:
  requires: [14-theory-foundation]
  provides: [chord-library-functions]
  affects: [15-02-chord-tools, 16-scale-engine]
tech_stack:
  added: []
  patterns: [lazy-music21-imports, rich-note-objects, quality-mapping-dict, root-based-octave-transposition]
key_files:
  created:
    - MCP_Server/theory/chords.py
  modified:
    - tests/test_theory.py
decisions:
  - "Root-based octave transposition: octave param places chord root at that scientific pitch octave (C4=60, G4=67, A3=57)"
  - "26-entry quality map covering triads, 7ths, extended, sus, add, and altered chord types"
  - "Confidence scoring: root position=1.0, inversions penalized by 0.05 per inversion level, reinterpretations capped at 0.75"
requirements_completed: [CHRD-01, CHRD-02, CHRD-03, CHRD-04, CHRD-05]
metrics:
  duration: "296s"
  completed: "2026-03-24"
  tasks_completed: 1
  tasks_total: 1
  test_count: 34
---

# Phase 15 Plan 01: Chord Engine Library Summary

Chord engine library with 5 pure-logic functions (build, inversions, voicings, identify, diatonic) using music21 ChordSymbol/RomanNumeral APIs, 26-entry quality map, and ranked chord identification with confidence scoring.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create chord library with all 5 functions and unit tests | dd01977 | MCP_Server/theory/chords.py, tests/test_theory.py |

## What Was Built

### MCP_Server/theory/chords.py (new)

Five exported functions implementing the chord engine core:

1. **build_chord(root, quality, octave)** - Builds any chord from root + quality symbol using music21 ChordSymbol. 26-entry quality map translates user-facing symbols (maj, min7, dom7, etc.) to ChordSymbol notation. Root-based octave transposition places the chord root at the exact requested octave.

2. **get_chord_inversions(root, quality, octave)** - Returns all inversions by rotating bottom notes up an octave. Each inversion includes inversion number, bass note name, and rich note objects.

3. **get_chord_voicings(root, quality, octave)** - Returns close/open/drop-2/drop-3 voicing variants. Drop-2 moves 2nd-from-top down an octave, drop-3 moves 3rd-from-top. Drop-3 returns null for chords with fewer than 4 notes.

4. **identify_chord(midi_pitches)** - Identifies chords from MIDI pitch sets. Primary identification via music21's chord analysis, then generates alternative candidates by trying each pitch as potential root against the quality map. Returns up to 3 ranked candidates with confidence scores.

5. **get_diatonic_chords(key_name, scale_type, octave)** - Enumerates all 7 diatonic triads and 7th chords for major and natural minor keys using Roman numeral templates and music21's RomanNumeral API.

### tests/test_theory.py (modified)

Added TestChordLibrary class with 34 unit tests covering:
- 9 build_chord tests (major, minor7, dom7, aug, sus4, dim7, invalid root, invalid quality, rich note objects)
- 6 inversion tests (triad count, 7th count, root/1st/2nd position midis, bass note presence)
- 5 voicing tests (keys present, close values, drop2/drop3 values, triad drop3 null)
- 6 identify tests (root position, inversion, dyad, ambiguous, confidence, max 3 candidates)
- 8 diatonic tests (major triads count, I/ii/viio chords, minor triads, sevenths, degree fields, invalid scale)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected Am7 octave 3 test expectation**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Plan specified build_chord("A", "min7", 3) should return midi [45, 48, 52, 55] (A2=45), but root-based octave transposition correctly places A at octave 3 = A3 = MIDI 57, giving [57, 60, 64, 67]. The plan value was inconsistent with the octave semantics used by C maj (octave 4 = C4=60) and G dom7 (octave 4 = G4=67).
- **Fix:** Updated test expectation to [57, 60, 64, 67] for consistent root-based octave placement.
- **Files modified:** tests/test_theory.py
- **Commit:** dd01977

## Decisions Made

1. **Root-based octave transposition** - The octave parameter places the chord root at that exact scientific pitch octave (C4=60, G4=67, A3=57). This is consistent across all root notes and matches standard music notation expectations.

2. **Quality display from music21** - Uses music21's `.quality` attribute for display names rather than parsing from `pitchedCommonName`, giving clean values like "major", "minor", "dominant-seventh".

3. **Confidence scoring formula** - Root position gets 1.0, each inversion level subtracts 0.05, enharmonic reinterpretations capped at 0.75 to prefer the primary identification.

## Verification Results

- `python -m pytest tests/test_theory.py::TestChordLibrary -x -v` -- 34/34 passed
- `python -m pytest tests/test_theory.py -x -v` -- 49/49 passed (all theory tests including pitch and tools)
- All 5 functions importable from MCP_Server.theory.chords
- Quality map has 26 entries (exceeds 15 minimum)
- 34 test methods (exceeds 10 minimum)

## Known Stubs

None - all functions fully implemented with real music21 integration.

## Self-Check: PASSED
