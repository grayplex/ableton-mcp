---
phase: 17-progression-engine
plan: 01
subsystem: theory/progressions
tags: [progression, catalog, voice-leading, roman-numeral, suggestion]
dependency_graph:
  requires: [chords.py, scales.py, pitch.py]
  provides: [progressions.py, PROGRESSION_CATALOG, get_common_progressions, generate_progression, analyze_progression, suggest_next_chord]
  affects: [theory/__init__.py, tests/test_theory.py]
tech_stack:
  added: []
  patterns: [voice-leading, hybrid-suggestion, roman-numeral-resolution, chord-name-normalization]
key_files:
  created:
    - MCP_Server/theory/progressions.py
  modified:
    - MCP_Server/theory/__init__.py
    - tests/test_theory.py
decisions:
  - Voice leading uses permutation-based optimization for chords up to 5 notes
  - Chord name normalization converts user "b" flat notation to music21 "-" format
  - Modal progressions resolve via parent major key rotation from SCALE_CATALOG intervals
  - Catalog genre for R&B/Soul stored as "rnb" (lowercase, no special chars)
requirements_completed: [PROG-01, PROG-02, PROG-03, PROG-04]
metrics:
  duration: 315s
  completed: "2026-03-24T21:19:46Z"
  tasks: 1
  files: 3
  tests_added: 37
  tests_total_passing: 110
---

# Phase 17 Plan 01: Progression Library Summary

Progression engine library with PROGRESSION_CATALOG (25 progressions, 7 genres) and 4 public functions using music21 Roman numeral resolution, permutation-optimized voice leading, and hybrid theory+catalog suggestion ranking.

## Task Results

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create progressions.py with PROGRESSION_CATALOG and 4 library functions | 5c98bfb | progressions.py, __init__.py, test_theory.py |

## What Was Built

### PROGRESSION_CATALOG (25 entries, 7 genres)
- Pop (4): Axis of Awesome, Sensitive Female, 50s Progression, Pop-Punk
- Rock (4): Classic Rock, Rock Anthem, Grunge, Power Ballad
- Jazz (5): ii-V-I Major, ii-V-I Minor, Jazz Turnaround, Rhythm Changes A, Coltrane Changes
- Blues (3): 12-Bar Blues, Minor Blues, Jazz Blues
- R&B/Soul (3): Neo-Soul, Motown, R&B Ballad
- Classical (3): Authentic Cadence, Pachelbel Canon, Romanesca
- EDM (3): EDM Anthem, Trance, Future Bass

### Public Functions
1. **get_common_progressions(key, genre, octave)** - Returns catalog progressions resolved to MIDI in given key
2. **generate_progression(key, numerals, scale_type, octave)** - Voice-led chord sequence from Roman numerals
3. **analyze_progression(chord_names, key)** - Identifies Roman numerals including borrowed chords
4. **suggest_next_chord(key, preceding, genre)** - Hybrid theory-rules + catalog-frequency ranked suggestions

### Internal Helpers
- `_resolve_numeral_to_chord` - music21 RomanNumeral resolution with modal scale support
- `_voice_lead_pair` - Permutation-optimized nearest-voice voice leading
- `_normalize_chord_name` - Converts "Bb" -> "B-" for music21 compatibility
- `_get_base_numeral` - Strips quality suffixes for function lookup
- `_get_function` - Maps numeral to harmonic function label
- `_CHORD_FUNCTIONS` - Numeral-to-function mapping
- `_THEORY_RULES` - Function-to-likely-next-chord mapping with scores

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Voice leading algorithm produced ascending root-position chords**
- **Found during:** Task 1, test_generate_progression_voice_leading
- **Issue:** Original per-voice nearest-octave algorithm assigned pitch classes to voices in order, producing sequential ascending voicings (total movement 36 semitones for I-IV-V-I)
- **Fix:** Replaced with center-based placement + permutation optimization that tries all voice assignments for chords up to 5 notes
- **Result:** Total movement reduced from 36 to 12 semitones for C major I-IV-V-I
- **Files modified:** MCP_Server/theory/progressions.py
- **Commit:** 5c98bfb

**2. [Rule 1 - Bug] music21 ChordSymbol rejects "Bb" flat notation**
- **Found during:** Task 1, test_analyze_progression_borrowed_chord
- **Issue:** music21's ChordSymbol uses "-" for flats (e.g., "B-") but users write "Bb"
- **Fix:** Added `_normalize_chord_name` helper that converts "b" after note letter to "-" before passing to ChordSymbol
- **Files modified:** MCP_Server/theory/progressions.py
- **Commit:** 5c98bfb

## Decisions Made

1. **Permutation voice leading:** For chords up to 5 notes, try all permutations of voice assignments to find minimum total movement. O(n!) but n<=5 so max 120 permutations.
2. **Chord name normalization:** Pre-process chord names to convert "b" flat notation to music21's "-" format before ChordSymbol parsing.
3. **Modal resolution via parent major:** For modal progressions (dorian, mixolydian, etc.), find the parent major key by rotating SCALE_CATALOG intervals, then use music21's RomanNumeral with that key.
4. **R&B genre key:** Stored as "rnb" in catalog for simple matching; users can pass "rnb" as genre filter.

## Known Stubs

None - all functions fully implemented with real music21 integration.

## Verification

- 37 new tests in TestProgressionLibrary: all passing
- 73 existing tests (Pitch, Chord, Scale): all passing, no regressions
- All 4 functions importable via barrel exports
- All plan verification commands pass

## Self-Check: PASSED
