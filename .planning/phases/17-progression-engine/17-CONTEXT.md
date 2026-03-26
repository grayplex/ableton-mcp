# Phase 17: Progression Engine - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver 4 progression-focused MCP tools: retrieve genre-specific chord progression templates with MIDI output, generate voice-led chord sequences from Roman numeral input in any key/scale, analyze a chord sequence as Roman numerals (including non-diatonic chords), and suggest next chords given context using a hybrid theory-rules + catalog-frequency approach. All logic lives in `MCP_Server/theory/progressions.py` with tools registered in the existing `MCP_Server/tools/theory.py`.

</domain>

<decisions>
## Implementation Decisions

### Progression Catalog
- **D-01:** Catalog stores Roman numeral sequences only — resolved to MIDI at call time using key param + existing `build_chord`/`get_diatonic_chords`. Keeps catalog key-agnostic
- **D-02:** Core genre coverage (~20-30 progressions): pop, rock, jazz, blues, R&B/soul, classical, EDM — 3-5 progressions per genre
- **D-03:** Metadata per template: name + genre + numerals only (e.g., `{"name": "Axis", "genre": "pop", "numerals": ["I", "V", "vi", "IV"]}`)
- **D-04:** `get_common_progressions` returns both Roman numerals AND resolved MIDI pitches (using key param). User gets the template AND ready-to-use notes
- **D-05:** Flat list output with genre field per progression (consistent with `list_scales` returning flat catalog with category field). Optional genre filter parameter

### Voice Leading in generate_progression
- **D-06:** Basic nearest-voice voice leading: each chord voiced to minimize total pitch movement from previous chord. No parallel 5ths/octaves checking. Phase 19 adds sophisticated version later
- **D-07:** Accepts key + optional scale type parameter. Defaults to major/minor from key signature, but allows specifying scale type (dorian, mixolydian, etc.) for modal progressions. Reuses Phase 16 scale catalog

### Next-Chord Suggestion
- **D-08:** Hybrid algorithm: theory rules (dominant→tonic, predominant→dominant, common substitutions) weighted by catalog progression frequency. More nuanced than either approach alone
- **D-09:** Input: key + 1-4 preceding chords (as Roman numerals or chord names). Style/genre as optional filter
- **D-10:** Returns top 3-5 ranked suggestions, each with brief reason (e.g., "dominant resolution", "common pop pattern", "deceptive cadence")
- **D-11:** Up to 4 preceding chords considered — use all provided for context. More chords = better suggestion

### Roman Numeral Analysis
- **D-12:** Detects and labels non-diatonic chords: secondary dominants (V/V), borrowed chords (bVII from mixolydian), Neapolitan (bII). Uses music21's roman numeral analysis
- **D-13:** Input: chord names (e.g., "Cmaj7", "Dm", "G7") + key. Parses chord names, then computes Roman numerals
- **D-14:** Rich output per chord: Roman numeral + chord quality + root + MIDI pitches (e.g., `{"numeral": "V7", "quality": "dominant 7th", "root": "G", "notes": [...]}`)

### Output Consistency
- **D-15:** Unified chord object format across all 4 tools: `{"numeral": "V7", "root": "G", "quality": "dominant 7th", "notes": [{"midi": 67, "name": "G4"}, ...]}`. Same shape everywhere, with optional fields depending on context
- **D-16:** No hard limit on progression length for `generate_progression` — accept any Roman numeral sequence length. The AI controls what it sends

### Carried Forward from Phase 14-16
- **D-17:** Library code in `MCP_Server/theory/progressions.py`, tools in `MCP_Server/tools/theory.py` (Phase 14 pattern)
- **D-18:** Barrel exports from `MCP_Server/theory/__init__.py` (Phase 14 D-03)
- **D-19:** No prefix on tool names — `get_common_progressions`, not `theory_get_common_progressions` (Phase 14 D-15)
- **D-20:** MIDI validation (0-127) at tool boundary layer, not in library functions (Phase 14 D-16)
- **D-21:** Rich note objects `{"midi": int, "name": str}` for all pitch output (Phase 14 D-04/D-05)
- **D-22:** `json.dumps()` returns on success, `format_error()` on error (Phase 14 D-06/D-07)
- **D-23:** Lazy music21 imports inside theory/ functions (Phase 14 D-14)
- **D-24:** C4 = MIDI 60 scientific pitch notation (Phase 14 D-17)
- **D-25:** Aliased imports to avoid name collisions between tool and library functions (Phase 15 pattern)

### Claude's Discretion
- Internal `progressions.py` library API design (function signatures, helper utilities)
- Progression catalog exact contents (specific progressions per genre within the ~20-30 target)
- Theory rule weights vs. catalog frequency weights in hybrid suggestion algorithm
- How to parse chord name strings into root + quality for analyze_progression
- music21 roman numeral module usage patterns
- Reuse strategy for existing `chords.py`/`scales.py` functions
- Test organization and edge case selection
- Error handling for invalid Roman numerals, unrecognized chord names, empty input

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Theory Module (Phase 14-16 output)
- `MCP_Server/theory/__init__.py` — Barrel exports pattern (add new progression functions here)
- `MCP_Server/theory/pitch.py` — Reference library module: lazy imports, `_force_sharp()`, `_format_note_name()`, `_parse_note_name()`
- `MCP_Server/theory/chords.py` — Chord library: `build_chord()`, `get_diatonic_chords()`, `identify_chord()` — all reusable for progression resolution
- `MCP_Server/theory/scales.py` — Scale library: `SCALE_CATALOG`, `get_scale_pitches()` — reusable for modal progression support
- `MCP_Server/tools/theory.py` — Tool module: @mcp.tool() pattern, MIDI validation, json.dumps/format_error, existing 12 theory tools

### Codebase Patterns
- `MCP_Server/connection.py` — `format_error()` utility for error responses
- `MCP_Server/server.py` — FastMCP server setup, `mcp` instance creation

### Testing
- `tests/conftest.py` — `mcp_server` fixture for tool integration tests
- `tests/test_theory.py` — Phase 14-16 theory tests (pattern for new progression tests)

### Requirements
- `.planning/REQUIREMENTS.md` — PROG-01 through PROG-04 acceptance criteria
- `.planning/ROADMAP.md` — Phase 17 deliverables

### Prior Context
- `.planning/phases/14-theory-foundation/14-CONTEXT.md` — Foundation patterns
- `.planning/phases/15-chord-engine/15-CONTEXT.md` — Chord patterns (build_chord, identify_chord reuse)
- `.planning/phases/16-scale-mode-explorer/16-CONTEXT.md` — Scale patterns (catalog structure, modal support)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/theory/chords.py:build_chord()` — Build chord from root + quality → MIDI pitches. Essential for resolving Roman numerals to notes
- `MCP_Server/theory/chords.py:get_diatonic_chords()` — Enumerate diatonic chords for a key. Essential for Roman numeral resolution and validation
- `MCP_Server/theory/chords.py:identify_chord()` — Identify chord from MIDI pitches. Useful for analyze_progression's chord name parsing
- `MCP_Server/theory/scales.py:SCALE_CATALOG` — 38-scale catalog with interval patterns. Enables modal progression support (D-07)
- `MCP_Server/theory/scales.py:get_scale_pitches()` — Generate scale pitches for any scale/root. Useful for modal chord building
- `MCP_Server/theory/pitch.py` — `_force_sharp()`, `_format_note_name()`, `_parse_note_name()` — core pitch utilities

### Established Patterns
- Lazy music21 import via module-level `_module = None` + getter function (chords.py has `_get_roman_module()` already)
- Rich note objects: `{"midi": int, "name": str}` (all theory tools)
- Tool boundary validation with `format_error()` for invalid input
- `json.dumps(result, indent=2)` for all tool returns
- Aliased imports (e.g., `_build_chord`) to avoid tool/library name collisions
- Flat catalog with category field for browseable data (scales.py pattern)

### Integration Points
- `MCP_Server/theory/__init__.py` — Add 4 progression function exports
- `MCP_Server/tools/theory.py` — Add 4 new @mcp.tool() functions
- `tests/test_theory.py` — Add progression test cases (both unit and integration)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

- Full voice leading rules (parallel 5ths/octaves avoidance, leading tone resolution) — Phase 19 scope
- Modulation detection in analyze_progression — Phase 18 harmonic analysis scope
- Mood/energy tags on progression templates — future enhancement
- Tempo/feel hints on progression templates — future enhancement

</deferred>

---

*Phase: 17-progression-engine*
*Context gathered: 2026-03-24*
