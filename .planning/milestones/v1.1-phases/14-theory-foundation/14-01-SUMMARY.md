---
phase: 14-theory-foundation
plan: 01
subsystem: theory-library
tags: [music21, pitch, midi, theory, foundation]
dependency_graph:
  requires: []
  provides: [music21-dependency, theory-package, pitch-mapping]
  affects: [MCP_Server.theory, pyproject.toml]
tech_stack:
  added: [music21]
  patterns: [lazy-import, barrel-exports, key-aware-enharmonic]
key_files:
  created:
    - MCP_Server/theory/__init__.py
    - MCP_Server/theory/pitch.py
  modified:
    - pyproject.toml
decisions:
  - "Force sharps for black keys by checking accidental polarity rather than relying on simplifyEnharmonic, which prefers Eb/Bb"
  - "Use parenthesized negative octave format C(-1) to avoid music21 parsing ambiguity where C-1 is read as C-flat-1"
  - "Key-aware spelling via scale pitch lookup rather than simplifyEnharmonic(keyContext=) which is not available in music21 9.x"
requirements_completed: [THRY-01, THRY-02, THRY-03]
metrics:
  duration: 209s
  completed: "2026-03-24T11:12:44Z"
  tasks: 2
  files: 3
---

# Phase 14 Plan 01: Music21 Dependency and Pitch Mapping Summary

Bidirectional MIDI-to-note mapping with lazy music21 import, sharps-default enharmonic spelling, and key-aware respelling via scale lookup.

## What Was Built

### Task 1: Add music21 dependency and theory package to pyproject.toml
- **Commit:** `195be53`
- Added `"music21>=9.0"` to `[project.dependencies]`
- Added `"MCP_Server.theory"` to `[tool.setuptools]` packages
- music21 9.9.1 installed and importable

### Task 2: Create MCP_Server/theory/ package with pitch mapping utilities
- **Commit:** `e256e28`
- `MCP_Server/theory/pitch.py` — Core pitch mapping with lazy music21 import
  - `midi_to_note(midi_number, key_context=None)` — MIDI int to note info dict
  - `note_to_midi(note_name)` — note name string to MIDI info dict
  - `_force_sharp(p)` — ensures sharps default per D-12
  - `_format_note_name(p)` — safe formatting for negative octaves
  - `_parse_note_name(note_name)` — robust parsing including negative octaves
- `MCP_Server/theory/__init__.py` — Barrel exports for `midi_to_note`, `note_to_midi`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed roundtrip failure for MIDI 0-11 (negative octave)**
- **Found during:** Task 2
- **Issue:** music21's `nameWithOctave` produces ambiguous strings for octave -1 (e.g., "C-1" parses as C-flat in octave 1, not C in octave -1). MIDI 0 roundtripped to MIDI 23.
- **Fix:** Added `_format_note_name()` using parenthesized format `C(-1)` and `_parse_note_name()` regex parser that constructs Pitch from components to avoid ambiguity.
- **Files modified:** `MCP_Server/theory/pitch.py`
- **Commit:** `e256e28`

**2. [Rule 1 - Bug] Fixed sharps-default not working for Eb/Bb**
- **Found during:** Task 2
- **Issue:** music21 defaults to Eb (E-) and Bb (B-) instead of D# and A#, even with `simplifyEnharmonic()`. This violates D-12 (sharps default for black keys).
- **Fix:** Added `_force_sharp()` that checks accidental polarity and calls `getEnharmonic()` to convert flats to sharps when no key context.
- **Files modified:** `MCP_Server/theory/pitch.py`
- **Commit:** `e256e28`

**3. [Rule 1 - Bug] Fixed simplifyEnharmonic(keyContext=) not available in music21 9.x**
- **Found during:** Task 2
- **Issue:** The plan assumed `simplifyEnharmonic(keyContext=key.Key(...))` was available, but music21 9.9.1 does not support the `keyContext` parameter.
- **Fix:** Implemented key-aware spelling via scale pitch lookup — build a pitch-class-to-name map from the key's scale and use it for enharmonic selection.
- **Files modified:** `MCP_Server/theory/pitch.py`
- **Commit:** `e256e28`

## Verification Results

- music21 importable: 9.9.1
- `from MCP_Server.theory import midi_to_note, note_to_midi` succeeds
- `midi_to_note(60)` returns `{"midi": 60, "name": "C4", "octave": 4, "pitch_class": "C"}`
- All 128 MIDI values (0-127) roundtrip correctly
- Default enharmonic uses sharps (MIDI 61 -> "C#4")
- Key-aware spelling works (MIDI 61 in Ab major -> "D-4")

## Known Stubs

None -- all functions are fully implemented with no placeholder data.

## Self-Check: PASSED

- All created files exist on disk
- All commit hashes found in git log
- All verification tests pass
