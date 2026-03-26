---
phase: 17-progression-engine
verified: 2026-03-25T22:00:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 17: Progression Engine Verification Report

**Phase Goal:** Claude can retrieve genre-specific progressions, generate voice-led chord sequences, analyze existing progressions as Roman numerals, and get next-chord suggestions.
**Verified:** 2026-03-25T22:00:00Z
**Status:** passed
**Re-verification:** No — initial verification (gap closure from milestone audit)

---

## Goal Achievement

### Observable Truths

Combined must-haves from Plan 01 (library layer) and Plan 02 (tool layer):

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | get_common_progressions returns catalog entries filtered by genre with MIDI-resolved chords | VERIFIED | `progressions.py` PROGRESSION_CATALOG (25 entries, 7 genres); spot-check: `get_common_progressions('C','pop')` returns 4 pop progressions with chords containing MIDI pitches and note names |
| 2  | generate_progression produces voice-led chord sequence from Roman numerals in any key/scale | VERIFIED | `progressions.py` `generate_progression`; permutation-based voice leading; spot-check: C major I-IV-V-I returns 4 chords with minimal voice movement |
| 3  | analyze_progression identifies Roman numerals including borrowed chords from chord name input | VERIFIED | `progressions.py` `analyze_progression`; spot-check: `['C','Am','F','G']` in key C returns `[I, vi, IV, V]` with functions (tonic, submediant, subdominant, dominant) |
| 4  | suggest_next_chord returns ranked suggestions with reasons using hybrid theory+catalog ranking | VERIFIED | `progressions.py` `suggest_next_chord`; spot-check: preceding `['I','IV','V']` in C returns 4 suggestions, top is `I` with reason "authentic resolution" |
| 5  | PROGRESSION_CATALOG contains 25 progressions across 7 genres | VERIFIED | `test_catalog_has_25_entries` and `test_catalog_covers_7_genres` both pass; genres: pop, rock, jazz, blues, rnb, classical, edm |
| 6  | get_common_progressions MCP tool accepts key + optional genre + octave, returns JSON with MIDI boundary validation | VERIFIED | `tools/theory.py` line 346: `@mcp.tool()` decorator; MIDI 0-127 check at lines 361-369; `json.dumps` return |
| 7  | generate_progression MCP tool accepts key + numerals + scale_type + octave, validates empty input and MIDI range | VERIFIED | `tools/theory.py` line 385: `@mcp.tool()` decorator; empty-numerals check at lines 398-403; MIDI boundary validation at lines 406-413 |
| 8  | analyze_progression MCP tool accepts chord_names + key, validates empty input | VERIFIED | `tools/theory.py` line 429: `@mcp.tool()` decorator; empty-chord_names check at lines 440-445 |
| 9  | suggest_next_chord MCP tool accepts key + preceding + optional genre, validates empty input | VERIFIED | `tools/theory.py` line 462: `@mcp.tool()` decorator; empty-preceding check at lines 474-479 |
| 10 | All 4 tools are registered with FastMCP and discoverable | VERIFIED | Lines 346, 385, 429, 462 each have `@mcp.tool()` decorator; `test_progression_tools_registered` confirms all 4 in tool list |

**Score:** 10/10 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `MCP_Server/theory/progressions.py` | 4 library functions + PROGRESSION_CATALOG | VERIFIED | 25 catalog entries, 7 genres; 4 public functions + 7 internal helpers; no stubs |
| `MCP_Server/theory/__init__.py` | Barrel exports for 4 progression functions | VERIFIED | Line 6: `from .progressions import get_common_progressions, generate_progression, analyze_progression, suggest_next_chord`; all 4 in `__all__` |
| `MCP_Server/tools/theory.py` | 4 new @mcp.tool() functions | VERIFIED | 4 decorated functions at lines 346, 385, 429, 462 with full implementations |
| `tests/test_theory.py` | TestProgressionLibrary (37 tests) + TestProgressionTools (18 tests) | VERIFIED | Both classes present; all 55 tests pass |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `MCP_Server/theory/progressions.py` | `music21.roman.RomanNumeral` | lazy import | VERIFIED | `_resolve_numeral_to_chord` uses music21 RomanNumeral resolution |
| `MCP_Server/theory/progressions.py` | `MCP_Server/theory/chords.py` | direct import | VERIFIED | Imports `_make_note_obj` for MIDI-to-note conversion |
| `MCP_Server/theory/progressions.py` | `MCP_Server/theory/scales.py` | direct import | VERIFIED | Imports `SCALE_CATALOG` for modal parent-key resolution |
| `MCP_Server/tools/theory.py` | `MCP_Server/theory/progressions.py` | aliased imports | VERIFIED | Lines 21-24: all 4 functions imported as `_get_common_progressions`, `_generate_progression`, `_analyze_progression`, `_suggest_next_chord` |
| `MCP_Server/theory/__init__.py` | `MCP_Server/theory/progressions.py` | barrel re-export | VERIFIED | Line 6: `from .progressions import ...` |
| `MCP_Server/theory/analysis.py` | `MCP_Server/theory/progressions.py` | direct import | VERIFIED | Phase 18 imports `analyze_progression` for harmonic rhythm Roman numeral injection |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `tools/theory.py::get_common_progressions` | `result` | `_get_common_progressions(key, genre, octave)` → `progressions.py` → `_resolve_numeral_to_chord` → music21 RomanNumeral | Yes — MIDI pitches resolved from catalog Roman numerals | FLOWING |
| `tools/theory.py::generate_progression` | `result` | `_generate_progression(key, numerals, ...)` → `_resolve_numeral_to_chord` + `_voice_lead_pair` | Yes — voice-led MIDI chord sequence | FLOWING |
| `tools/theory.py::analyze_progression` | `result` | `_analyze_progression(chord_names, key)` → music21 ChordSymbol + RomanNumeral | Yes — Roman numeral labels from chord names | FLOWING |
| `tools/theory.py::suggest_next_chord` | `result` | `_suggest_next_chord(key, preceding, genre)` → `_THEORY_RULES` + catalog frequency | Yes — ranked suggestions with reasons | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command/Check | Result | Status |
|----------|--------------|--------|--------|
| get_common_progressions returns pop progressions for genre="pop" | Python: `get_common_progressions('C', 'pop')` | 4 pop progressions returned, each with name/genre/numerals/chords | PASS |
| generate_progression applies voice leading to I-IV-V-I | Python: `generate_progression('C', ['I','IV','V','I'])` | 4 chords with minimal voice movement between consecutive chords | PASS |
| analyze_progression identifies C-Am-F-G as I-vi-IV-V | Python: `analyze_progression(['C','Am','F','G'], 'C')` | `[{numeral:"I", function:"tonic"}, {numeral:"vi", function:"submediant"}, ...]` | PASS |
| suggest_next_chord recommends I after V (authentic resolution) | Python: `suggest_next_chord('C', ['I','IV','V'])` | Top suggestion: `I` with reason "authentic resolution" | PASS |
| TestProgressionLibrary — 37 unit tests | `pytest tests/test_theory.py::TestProgressionLibrary` | 37 passed | PASS |
| TestProgressionTools — 18 integration tests | `pytest tests/test_theory.py::TestProgressionTools` | 18 passed | PASS |
| Full theory suite — no regressions | `pytest tests/test_theory.py` | 224 passed in 18.69s | PASS |

---

### Requirements Coverage

All requirement IDs appear in both Plan 01 and Plan 02 frontmatter. Cross-referenced against `.planning/REQUIREMENTS.md`:

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PROG-01 | 17-01, 17-02 | User can retrieve common chord progressions by genre/style with MIDI pitch output | SATISFIED | `get_common_progressions` library function + MCP tool; 25-entry PROGRESSION_CATALOG across 7 genres; MIDI boundary validation; 12 unit tests + 5 integration tests pass |
| PROG-02 | 17-01, 17-02 | User can generate a chord progression with voice leading applied, given a key and Roman numeral sequence | SATISFIED | `generate_progression` library function + MCP tool; permutation-optimized voice leading; modal scale support; 9 unit tests + 4 integration tests pass |
| PROG-03 | 17-01, 17-02 | User can analyze a sequence of chords as Roman numeral progression in a given key | SATISFIED | `analyze_progression` library function + MCP tool; detects diatonic + borrowed chords; chord name normalization (Bb→B-); 7 unit tests + 4 integration tests pass |
| PROG-04 | 17-01, 17-02 | User can get next-chord suggestions given current progression context and style | SATISFIED | `suggest_next_chord` library function + MCP tool; hybrid theory-rules + catalog-frequency ranking; genre filtering; 9 unit tests + 4 integration tests pass |

No orphaned requirements. All 4 IDs claimed in plans and all 4 verified in codebase.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

No TODO/FIXME/placeholder comments, no empty returns, no hardcoded stub values found in either file.

---

### Human Verification Required

None. All behaviors are mechanically verifiable:
- Progression catalog content is deterministic.
- Voice leading uses permutation optimization with deterministic minimum-movement selection.
- Roman numeral analysis uses music21's ChordSymbol → RomanNumeral pipeline.
- All validation paths (empty input, invalid numerals, out-of-range MIDI) are covered by tests.

There is no visual output or real-time Ableton integration in this phase.

---

### Gaps Summary

No gaps. All four observable goals are fully achieved:

1. **Genre-specific progressions** — `get_common_progressions` returns 25 catalog progressions across 7 genres, resolved to MIDI pitches in any key, with MIDI boundary validation at the tool layer.

2. **Voice-led chord sequences** — `generate_progression` resolves Roman numerals via music21 and applies permutation-optimized voice leading (O(n!) for n<=5 notes) to minimize pitch movement between consecutive chords.

3. **Roman numeral analysis** — `analyze_progression` uses music21 ChordSymbol and RomanNumeral to identify diatonic and borrowed chords, with chord name normalization handling "Bb" → "B-" notation.

4. **Next-chord suggestions** — `suggest_next_chord` combines theory rules (function-based harmonic tendencies) with catalog frequency data, returning 3-5 ranked suggestions with explanatory reasons.

All artifacts are substantive, wired, and data-flowing. 224 tests pass with zero regressions.

---

_Verified: 2026-03-25T22:00:00Z_
_Verifier: Claude (manual verification for gap closure)_
