---
phase: 18-harmonic-analysis
verified: 2026-03-25T14:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 18: Harmonic Analysis Verification Report

**Phase Goal:** Claude can analyze existing clip content — detecting the key, identifying chords at each time position, and understanding the harmonic rhythm.
**Verified:** 2026-03-25T14:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

Combined must-haves from Plan 01 (library layer) and Plan 02 (tool layer):

| #  | Truth                                                                                              | Status     | Evidence                                                                                              |
|----|----------------------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------------------|
| 1  | detect_key returns top 3 ranked key candidates with key, mode, confidence from MIDI note data      | VERIFIED | `analysis.py` lines 32-83; spot-check confirmed `{"key":"C","mode":"major","confidence":0.722}` |
| 2  | analyze_clip_chords segments notes by time grid and identifies chords per segment                  | VERIFIED | `analysis.py` lines 86-162; QUANTIZE_WINDOW=0.1, beat/half_beat/bar grid; returns chord segments     |
| 3  | analyze_harmonic_rhythm merges consecutive same chords, computes stats, optionally adds Roman numerals | VERIFIED | `analysis.py` lines 165-251; timeline merge, stats dict, numeral injection confirmed by spot-check   |
| 4  | detect_key MCP tool accepts notes list, validates MIDI range, returns JSON string with key candidates | VERIFIED | `tools/theory.py` lines 492-523; `@mcp.tool()` decorator, MIDI 0-127 check, `json.dumps` return     |
| 5  | analyze_clip_chords MCP tool accepts notes + resolution + beats_per_bar, returns JSON string        | VERIFIED | `tools/theory.py` lines 526-565; resolution validated against ("beat","half_beat","bar")             |
| 6  | analyze_harmonic_rhythm MCP tool accepts notes + resolution + beats_per_bar + optional key, returns JSON | VERIFIED | `tools/theory.py` lines 568-609; full parameter set, json.dumps return, format_error paths           |
| 7  | All 3 tools are registered with FastMCP and discoverable                                           | VERIFIED | Lines 492, 526, 568 each have `@mcp.tool()` decorator; all 3 import without error                   |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact                          | Expected                                           | Status     | Details                                                                 |
|-----------------------------------|----------------------------------------------------|------------|-------------------------------------------------------------------------|
| `MCP_Server/theory/analysis.py`   | 3 library functions: detect_key, analyze_clip_chords, analyze_harmonic_rhythm | VERIFIED | 252 lines, fully implemented, no stubs, lazy music21 imports present |
| `MCP_Server/theory/__init__.py`   | Barrel exports for 3 analysis functions            | VERIFIED | Line 7: `from .analysis import detect_key, analyze_clip_chords, analyze_harmonic_rhythm`; all 3 in `__all__` |
| `MCP_Server/tools/theory.py`      | 3 new @mcp.tool() functions                        | VERIFIED | 3 decorated functions at lines 492, 526, 568 with full implementations  |
| `tests/test_theory.py`            | TestAnalysisLibrary (14 tests) + TestAnalysisTools (9 tests) | VERIFIED | Both classes present at lines 1498 and 1689; all 23 tests pass       |

---

### Key Link Verification

| From                              | To                                               | Via                        | Status     | Details                                                              |
|-----------------------------------|--------------------------------------------------|----------------------------|------------|----------------------------------------------------------------------|
| `MCP_Server/theory/analysis.py`   | `music21.stream.Stream.analyze`                  | lazy-imported stream module | VERIFIED  | Line 59: `k = s.analyze('key')` after lazy import on lines 12-19    |
| `MCP_Server/theory/analysis.py`   | `MCP_Server/theory/chords.py::identify_chord`    | direct import              | VERIFIED  | Line 4: `from MCP_Server.theory.chords import identify_chord, _make_note_obj, _midi_to_pitch` |
| `MCP_Server/theory/analysis.py`   | `MCP_Server/theory/progressions.py::analyze_progression` | direct import    | VERIFIED  | Line 5: `from MCP_Server.theory.progressions import analyze_progression` |
| `MCP_Server/tools/theory.py`      | `MCP_Server/theory/analysis.py`                  | aliased imports            | VERIFIED  | Lines 25-27: `detect_key as _detect_key`, `analyze_clip_chords as _analyze_clip_chords`, `analyze_harmonic_rhythm as _analyze_harmonic_rhythm` |
| `MCP_Server/theory/__init__.py`   | `MCP_Server/theory/analysis.py`                  | barrel re-export           | VERIFIED  | Line 7: `from .analysis import detect_key, analyze_clip_chords, analyze_harmonic_rhythm` |

---

### Data-Flow Trace (Level 4)

| Artifact                        | Data Variable   | Source                                    | Produces Real Data | Status    |
|---------------------------------|-----------------|-------------------------------------------|--------------------|-----------|
| `tools/theory.py::detect_key`  | `result`        | `_detect_key(notes)` → `analysis.py::detect_key` → `music21 s.analyze('key')` | Yes — KS algorithm on real note stream | FLOWING |
| `tools/theory.py::analyze_clip_chords` | `result` | `_analyze_clip_chords(notes, ...)` → `identify_chord(unique_pitches)` | Yes — live chord identification per segment | FLOWING |
| `tools/theory.py::analyze_harmonic_rhythm` | `result` | `_analyze_harmonic_rhythm(notes, ...)` → `analyze_clip_chords` → `analyze_progression` | Yes — computed from note data, optional Roman numeral merge | FLOWING |

---

### Behavioral Spot-Checks

| Behavior                                         | Command/Check                                          | Result                                                 | Status |
|--------------------------------------------------|--------------------------------------------------------|--------------------------------------------------------|--------|
| detect_key returns C major for C-tonic MIDI data | In-process Python assertion on tonic-emphasized notes  | `{"key":"C","mode":"major","confidence":0.722}`        | PASS   |
| analyze_clip_chords identifies chord name         | C triad at beat 0.0                                   | `"chord": "C-major triad"`                             | PASS   |
| analyze_harmonic_rhythm produces timeline+stats  | C+G chord data, key="C"                               | `total_chords=2`, `average_changes_per_bar=4.0`, numeral present | PASS   |
| TestAnalysisLibrary — 14 unit tests              | `pytest tests/test_theory.py::TestAnalysisLibrary`    | 14 passed in 5.56s                                     | PASS   |
| TestAnalysisTools — 9 integration tests          | `pytest tests/test_theory.py::TestAnalysisTools`      | 9 passed in 2.96s                                      | PASS   |
| Full theory suite — no regressions               | `pytest tests/test_theory.py`                         | 181 passed in 12.03s                                   | PASS   |

---

### Requirements Coverage

All requirement IDs appear in both Plan 01 and Plan 02 frontmatter. Cross-referenced against `.planning/REQUIREMENTS.md`:

| Requirement | Source Plans | Description                                                                                      | Status     | Evidence                                                                     |
|-------------|-------------|--------------------------------------------------------------------------------------------------|------------|------------------------------------------------------------------------------|
| ANLY-01     | 18-01, 18-02 | User can detect the key and scale of a clip from its MIDI notes (using music21's key detection) | SATISFIED | `detect_key` library function + MCP tool; `s.analyze('key')` via music21 KS algorithm; 5 unit tests + 3 integration tests pass |
| ANLY-02     | 18-01, 18-02 | User can segment a clip's notes into chords by time position and identify each chord             | SATISFIED | `analyze_clip_chords` library function + MCP tool; beat/half_beat/bar grid with 0.1-beat quantize window; 5 unit tests + 3 integration tests pass |
| ANLY-03     | 18-01, 18-02 | User can analyze harmonic rhythm — chord change frequency, chord durations, and progression structure | SATISFIED | `analyze_harmonic_rhythm` library function + MCP tool; timeline merge, stats (total_chords, average_changes_per_bar, most_common_duration), optional Roman numerals; 4 unit tests + 3 integration tests pass |

No orphaned requirements. All 3 IDs claimed in plans and all 3 verified in codebase.

---

### Anti-Patterns Found

Scan of `MCP_Server/theory/analysis.py` and `MCP_Server/tools/theory.py`:

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

No TODO/FIXME/placeholder comments, no empty returns, no hardcoded stub values found in either file.

Note: `except (ValueError, Exception): pass` at `analysis.py` line 223 silently swallows Roman numeral failures. This is a deliberate degradation decision (Roman numerals are optional) and does not prevent goal achievement.

---

### Human Verification Required

None. All behaviors are mechanically verifiable:
- Key detection uses a deterministic algorithm (Krumhansl-Schmuckler).
- Chord segmentation produces structured JSON.
- All validation paths (empty input, out-of-range MIDI, invalid resolution) are covered by tests.

There is no visual output or real-time Ableton integration in this phase.

---

### Gaps Summary

No gaps. All three observable goals are fully achieved:

1. **Key detection** — `detect_key` uses music21's Krumhansl-Schmuckler algorithm, returns 3 candidates with normalized confidence, accessible as an MCP tool with MIDI validation at the boundary.

2. **Chord identification at each time position** — `analyze_clip_chords` segments MIDI notes onto a configurable time grid (beat/half-beat/bar), applies a 0.1-beat quantize window to catch off-grid notes, and delegates to the existing `identify_chord` library for per-segment identification.

3. **Harmonic rhythm understanding** — `analyze_harmonic_rhythm` builds on chord segmentation by merging consecutive identical chords into a timeline with durations, computes frequency statistics (changes per bar, most common duration), and optionally adds Roman numeral labels by delegating to `analyze_progression`.

All artifacts are substantive, wired, and data-flowing. 181 tests pass with zero regressions.

---

_Verified: 2026-03-25T14:00:00Z_
_Verifier: Claude (gsd-verifier)_
