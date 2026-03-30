---
phase: 15-chord-engine
verified: 2026-03-24T00:00:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
---

# Phase 15: Chord Engine Verification Report

**Phase Goal:** Claude can build any chord by name, get inversions and voicings, identify chords from pitches, and enumerate all diatonic chords in a key.
**Verified:** 2026-03-24
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | build_chord returns correct MIDI pitches and rich note objects for any supported quality | VERIFIED | 9 unit tests pass; C maj=[60,64,67], Am7=[57,60,64,67], Gdom7=[67,71,74,77] confirmed |
| 2  | get_chord_inversions returns all inversions with notes rotated up by octave | VERIFIED | C maj: root=[60,64,67], 1st=[64,67,72], 2nd=[67,72,76]; triad=3, 7th=4 inversions |
| 3  | get_chord_voicings returns close/open/drop-2/drop-3 voicing variants | VERIFIED | Cmaj7 drop2=[55,60,64,71], drop3=[52,60,67,71]; triad drop3=null |
| 4  | identify_chord returns top 3 ranked candidates with root, quality, and inversion info | VERIFIED | [60,64,67]->C root pos; [64,67,72]->inversion=1; [57,60,64,67]->2+ candidates |
| 5  | get_diatonic_chords returns triads and 7th chords with Roman numerals for major and minor keys | VERIFIED | C major: 7 triads (I/ii/viio), 7 sevenths; A minor: 7 triads (i); degree/roman/quality/root/notes all present |
| 6  | build_chord MCP tool accepts root, quality, octave params and returns JSON with chord info | VERIFIED | integration test passes: C maj returns {root,quality,notes} with midi=[60,64,67] |
| 7  | get_chord_inversions MCP tool returns JSON array of all inversions | VERIFIED | C maj triad returns array len=3 with inversion=0/1/2 |
| 8  | get_chord_voicings MCP tool returns JSON dict with close/open/drop2/drop3 voicings | VERIFIED | Cmaj7 returns all 4 keys |
| 9  | identify_chord MCP tool accepts midi_pitches list and returns ranked candidates | VERIFIED | [60,64,67] -> top candidate root contains "C", inversion=0 |
| 10 | get_diatonic_chords MCP tool accepts key and scale_type and returns triads + sevenths | VERIFIED | C major: 7 triads roman[0]="I"; A minor: roman[0]="i" |
| 11 | All 5 tools are discoverable via mcp_server.list_tools() | VERIFIED | 5 chord tools confirmed among 181 total registered tools |
| 12 | Invalid inputs return format_error messages, not exceptions | VERIFIED | invalid quality returns "Error"; 1 pitch returns "Error"; MIDI >127 returns "Error" |

**Score:** 12/12 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `MCP_Server/theory/chords.py` | All 5 chord library functions | VERIFIED | 482 lines; all 5 functions defined; 26-entry _QUALITY_MAP; lazy music21 imports; _harmony_module=None pattern |
| `tests/test_theory.py` | Unit tests for chord library functions | VERIFIED | TestChordLibrary with 34 test methods; TestChordTools with 11 async integration tests |
| `MCP_Server/theory/__init__.py` | Barrel exports for chord functions | VERIFIED | `from .chords import build_chord, get_chord_inversions, get_chord_voicings, identify_chord, get_diatonic_chords`; all 7 symbols in __all__ |
| `MCP_Server/tools/theory.py` | 5 new @mcp.tool() chord tool functions | VERIFIED | 5 @mcp.tool() decorated functions with ctx:Context, docstrings, try/except, format_error, json.dumps |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `MCP_Server/theory/chords.py` | `music21.harmony.ChordSymbol` | lazy import `_get_harmony_module()` | WIRED | `_harmony_module = None`, `from music21 import harmony` inside getter |
| `MCP_Server/theory/chords.py` | `MCP_Server/theory/pitch.py` | `from MCP_Server.theory.pitch import _force_sharp, _format_note_name, _parse_note_name` | WIRED | Line 3 of chords.py; functions used throughout |
| `tests/test_theory.py` | `MCP_Server/theory/chords.py` | `from MCP_Server.theory.chords import` | WIRED | Per-test imports in TestChordLibrary; confirmed by 34 passing unit tests |
| `MCP_Server/tools/theory.py` | `MCP_Server/theory/__init__.py` | aliased imports `from MCP_Server.theory import build_chord as _build_chord` (and 4 others) | WIRED | Lines 11-15 of tools/theory.py |
| `MCP_Server/tools/theory.py` | `MCP_Server/connection.py` | `format_error` for error responses | WIRED | `from MCP_Server.connection import format_error` at line 7; used in all 5 tool except clauses |
| `tests/test_theory.py` | `MCP_Server/tools/theory.py` | `mcp_server.call_tool()` integration tests | WIRED | TestChordTools uses `await mcp_server.call_tool("build_chord", ...)` etc.; 11 passing integration tests |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `chords.py::build_chord` | `pitches` (music21 Pitch list) | `harmony.ChordSymbol(symbol).pitches` | Yes — music21 ChordSymbol computes real interval-based pitches | FLOWING |
| `chords.py::get_chord_inversions` | `base_midis` | `build_chord()` result | Yes — rotates real MIDI values from build_chord | FLOWING |
| `chords.py::get_chord_voicings` | `close_midis` | `build_chord()` result | Yes — derives drop-2/drop-3 from real close-position MIDI values | FLOWING |
| `chords.py::identify_chord` | `c` (music21.chord.Chord) | `chord_mod.Chord(sorted_pitches)` — music21 analysis | Yes — queries root(), quality, inversion() from music21 chord analysis | FLOWING |
| `chords.py::get_diatonic_chords` | `rn.pitches` | `roman.RomanNumeral(numeral, k).pitches` | Yes — music21 RomanNumeral resolves actual scale-degree pitches | FLOWING |
| `tools/theory.py` (all 5 tools) | result JSON | library functions via aliased imports | Yes — each tool calls real library function and serializes non-empty result | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 5 chord library functions importable | `python -c "from MCP_Server.theory.chords import build_chord, get_chord_inversions, get_chord_voicings, identify_chord, get_diatonic_chords; print('OK')"` | OK | PASS |
| All 5 chord tools registered in server | `asyncio.run(mcp.list_tools())` subset check | 5 tools in 181 total | PASS |
| TestChordLibrary: 34 unit tests | `pytest tests/test_theory.py::TestChordLibrary -x` | 34 passed | PASS |
| TestChordTools: 11 integration tests | `pytest tests/test_theory.py::TestChordTools -x` | 11 passed | PASS |
| Full theory test suite | `pytest tests/test_theory.py -x` | 60 passed, 0 failures | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CHRD-01 | 15-01-PLAN, 15-02-PLAN | User can build a chord from root note + quality | SATISFIED | build_chord() in chords.py + @mcp.tool() in tools/theory.py; midi=[60,64,67] confirmed |
| CHRD-02 | 15-01-PLAN, 15-02-PLAN | User can get chord inversions (root, 1st, 2nd, 3rd) | SATISFIED | get_chord_inversions() returns n inversions for n-note chord; all positions correct |
| CHRD-03 | 15-01-PLAN, 15-02-PLAN | User can get chord voicings (close, open, drop-2, drop-3) | SATISFIED | get_chord_voicings() returns all 4 types; drop-3=null for triads |
| CHRD-04 | 15-01-PLAN, 15-02-PLAN | User can identify a chord from a set of MIDI pitches | SATISFIED | identify_chord() returns up to 3 ranked candidates with confidence scores |
| CHRD-05 | 15-01-PLAN, 15-02-PLAN | User can get all diatonic chords for a given key/scale | SATISFIED | get_diatonic_chords() returns 7 triads + 7 sevenths with Roman numerals for major and minor |

All 5 CHRD requirements are marked `[x]` in REQUIREMENTS.md confirming phase-level tracking.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | No TODOs, FIXMEs, placeholders, or empty implementations found in chords.py or tools/theory.py | — | None |

---

### Notable Deviation (Non-blocking)

The plan specified major-key 7th numerals as `["Imaj7", "ii7", "iii7", "IVmaj7", "V7", "vi7", "viio7"]` but the implementation uses `["I7", "ii7", "iii7", "IV7", "V7", "vi7", "viio7"]`. In music21's RomanNumeral context, both `I7` and `Imaj7` resolve to C-E-G-B (major 7th) when key is C major — music21 interprets the diatonic context. Quality output is "major" for degree I, confirming correct behavior. This is functionally equivalent and tests pass.

---

### Human Verification Required

None — all behaviors are programmatically verifiable and confirmed via passing tests.

---

### Gaps Summary

No gaps. All 12 must-have truths are verified, all artifacts exist and are substantive, all key links are wired, data flows from real music21 computations through the full stack, and all 60 theory tests pass.

---

_Verified: 2026-03-24_
_Verifier: Claude (gsd-verifier)_
