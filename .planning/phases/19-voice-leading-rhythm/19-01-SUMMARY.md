---
phase: 19-voice-leading-rhythm
plan: 01
subsystem: theory
tags: [voice-leading, rhythm, midi, parallel-fifths, permutation, chord-tones, music21]

# Dependency graph
requires:
  - phase: 17-progression-engine
    provides: "_voice_lead_pair() nearest-voice algorithm, _resolve_numeral_to_chord(), generate_progression() pattern"
  - phase: 14-theory-foundation
    provides: "_make_note_obj(), _midi_to_pitch(), rich note object format, lazy import pattern"
provides:
  - "voice_lead_chords() - smooth chord connection with parallel 5ths/octaves avoidance"
  - "voice_lead_progression() - full voice-led Roman numeral progression"
  - "RHYTHM_CATALOG - 18 rhythm patterns across 4 categories"
  - "get_rhythm_patterns() - pattern metadata retrieval with category/style filtering"
  - "apply_rhythm_pattern() - chord-to-MIDI applicator matching add_notes_to_clip format"
affects: [19-02-PLAN, tools-registration, barrel-exports]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Permutation-based voice leading with interval filter (parallel 5ths/octaves)"
    - "Chord tone reference pattern (root/3rd/5th/7th/octave -> MIDI pitch mapping)"
    - "Rhythm pattern catalog with add_notes_to_clip-compatible output"

key-files:
  created:
    - MCP_Server/theory/voicing.py
    - MCP_Server/theory/rhythm.py
  modified:
    - tests/test_theory.py

key-decisions:
  - "Parallel detection uses modular interval comparison (% 12) with same-direction motion check"
  - "Fallback to minimum movement when all permutations have parallel 5ths/octaves"
  - "18 rhythm patterns across 4 categories (arpeggio, bass, comping, strumming) with 5 styles"
  - "Chord tone resolution uses index-based fallback for missing tones (7th -> last available)"

patterns-established:
  - "Parallel motion filter: _has_parallel_motion() checks pairwise intervals for P5/P8 with same-direction motion"
  - "Rhythm pattern format: {name, category, style, description, time_signature, steps: [{tone, beat, duration, velocity}]}"
  - "Pattern applicator output: {pitch, start_time, duration, velocity} matching add_notes_to_clip exactly"

requirements-completed: [VOIC-01, VOIC-02, RHYM-01, RHYM-02]

# Metrics
duration: 6min
completed: 2026-03-26
---

# Phase 19 Plan 01: Voice Leading & Rhythm Library Summary

**Nearest-voice voice leading with parallel 5ths/octaves avoidance plus 18-pattern rhythm catalog with chord-tone-to-MIDI applicator**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-26T01:29:30Z
- **Completed:** 2026-03-26T01:35:24Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Voice leading library with permutation optimization and parallel 5ths/octaves detection
- 18 rhythm patterns across 4 categories (arpeggio, bass, comping, strumming) in 5 styles
- apply_rhythm_pattern output matches add_notes_to_clip format exactly (zero transformation)
- 24 new unit tests passing, 205 total (zero regressions from 181 existing)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create voicing.py with voice leading functions** - `20fe7a0` (feat)
2. **Task 2: Create rhythm.py with pattern catalog and applicator** - `d143b29` (feat)
3. **Task 3: Add unit tests for voice leading and rhythm libraries** - `6fd657c` (test)

## Files Created/Modified
- `MCP_Server/theory/voicing.py` - Voice leading library: _has_parallel_motion, voice_lead_chords, voice_lead_progression
- `MCP_Server/theory/rhythm.py` - Rhythm pattern library: RHYTHM_CATALOG (18 patterns), _resolve_chord_tone, get_rhythm_patterns, apply_rhythm_pattern
- `tests/test_theory.py` - Added TestVoiceLeadingLibrary (12 tests) and TestRhythmLibrary (12 tests)

## Decisions Made
- Parallel detection uses `(interval) % 12` comparison for P5 (7) and P8/unison (0), checking same-direction motion only
- When all voice leading permutations have parallels, falls back to minimum total movement (best effort)
- 18 rhythm patterns with index-based chord tone fallback (7th -> last available for triads)
- Rhythm patterns use beat positions (0.0-3.75 for 4/4) not bar-relative fractions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing music21 dependency**
- **Found during:** Task 1 verification
- **Issue:** music21 not installed in current Python environment (needed by chords.py which voicing.py imports)
- **Fix:** Ran `pip install music21` to install v9.9.1
- **Files modified:** None (pip install, no source changes)
- **Verification:** All imports succeed, all 181 existing tests pass
- **Committed in:** Not committed separately (environment setup, no source file changes)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** music21 installation was required for any theory module to function. No scope creep.

## Issues Encountered
None beyond the music21 installation.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- voicing.py and rhythm.py are ready for tool registration in Plan 02
- Barrel exports in __init__.py still need to be updated (Plan 02 scope)
- 4 MCP tools to be added to MCP_Server/tools/theory.py (Plan 02 scope)

## Self-Check: PASSED

All 3 created/modified files verified on disk. All 3 task commits verified in git log.

---
*Phase: 19-voice-leading-rhythm*
*Completed: 2026-03-26*
