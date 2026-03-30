# Phase 18: Harmonic Analysis - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver 3 harmonic analysis MCP tools: detect key/scale from MIDI notes, segment notes into time-positioned chords, and analyze harmonic rhythm (chord durations, change frequency, progression structure). All tools accept note data as input (from `get_notes` output), not clip references directly. All logic lives in `MCP_Server/theory/analysis.py` with tools registered in the existing `MCP_Server/tools/theory.py`.

</domain>

<decisions>
## Implementation Decisions

### Key Detection (detect_key) — ANLY-01
- **D-01:** Returns top 3 ranked candidates (consistent with `identify_chord` in Phase 15 returning ranked candidates for ambiguous input)
- **D-02:** Major and minor keys appear as distinct, separate candidates — C major and A minor are ranked independently with their own confidence scores (music21's Krumhansl-Schmuckler naturally distinguishes them)
- **D-03:** Each candidate contains: key name, mode (major/minor), confidence score (0-1). No scale pitches or correlation vectors — keep it minimal

### Chord Segmentation (analyze_clip_chords) — ANLY-02
- **D-04:** Fixed time grid segmentation with configurable resolution parameter: `'beat'` (default), `'half_beat'`, `'bar'`. No onset-based detection
- **D-05:** Small quantization window catches slightly off-grid notes (e.g., strummed chords that don't land exactly on beat). Hardcoded tolerance, not user-configurable
- **D-06:** Each segment contains: time position (beat), identified chord name, quality, root, MIDI pitches as rich note objects, confidence. Reuses existing `identify_chord` from Phase 15
- **D-07:** No raw MIDI notes per segment in output — only the chord identification result

### Harmonic Rhythm (analyze_harmonic_rhythm) — ANLY-03
- **D-08:** Time unit is beats (consistent with beat-based segmentation grid)
- **D-09:** Returns stats + chord timeline: chord list with durations, average changes-per-bar, most common chord duration. Raw data that Claude can interpret contextually. No repetition/structure detection
- **D-10:** Chord timeline includes Roman numeral analysis when key is provided
- **D-11:** Key parameter is optional — when provided, Roman numerals are included in the timeline; when omitted, timeline has chord names only

### Carried Forward from Phase 14
- **D-12:** Library code in `MCP_Server/theory/analysis.py`, tools in `MCP_Server/tools/theory.py` (D-01, D-02 from Phase 14)
- **D-13:** Barrel exports from `MCP_Server/theory/__init__.py` (D-03 from Phase 14)
- **D-14:** No prefix on tool names — `detect_key`, not `theory_detect_key` (D-15 from Phase 14)
- **D-15:** MIDI validation (0-127) at tool boundary layer, not in library functions (D-16 from Phase 14)
- **D-16:** Rich note objects `{"midi": int, "name": str}` for pitch output (D-04/D-05 from Phase 14)
- **D-17:** `json.dumps()` string returns; errors use `format_error()` (D-06/D-07 from Phase 14)
- **D-18:** Standalone tests — no `mock_connection` needed since analysis tools are pure computation (D-09 from Phase 14)
- **D-19:** Lazy music21 imports inside functions (D-14 from Phase 14)

### Claude's Discretion
- Quantization window size (exact tolerance in beats for off-grid note capture)
- Internal implementation of Krumhansl-Schmuckler vs other music21 key detection algorithms
- How to handle empty segments (no notes in a time window) — skip or report as rest

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Theory Engine Architecture
- `.planning/phases/14-theory-foundation/14-CONTEXT.md` — Module structure, output format, naming conventions, lazy imports
- `.planning/phases/15-chord-engine/15-CONTEXT.md` — Chord quality vocabulary, identify_chord pattern (ranked candidates)
- `.planning/phases/17-progression-engine/17-CONTEXT.md` — Roman numeral analysis pattern, unified chord object format

### Requirements
- `.planning/REQUIREMENTS.md` §Harmonic Analysis Tools — ANLY-01, ANLY-02, ANLY-03 acceptance criteria

### Existing Code
- `MCP_Server/theory/chords.py` — `identify_chord()` function to reuse for chord segmentation
- `MCP_Server/theory/progressions.py` — `analyze_progression()` for Roman numeral analysis pattern
- `MCP_Server/tools/theory.py` — Existing tool registration pattern (16 theory tools)
- `MCP_Server/theory/__init__.py` — Barrel export pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `identify_chord(midi_pitches)` in `chords.py` — returns ranked chord candidates from MIDI pitches. Directly reusable for chord segmentation (collect notes per time window, pass to identify_chord)
- `analyze_progression(chord_names, key)` in `progressions.py` — returns Roman numeral analysis. Can inform harmonic rhythm Roman numeral output
- `midi_to_note(midi_number)` in `pitch.py` — converts MIDI to note names for rich note objects

### Established Patterns
- Theory library functions are pure Python + music21, no Ableton dependencies
- Tools call library functions, serialize to JSON, return string
- Tests use `mcp_server` fixture for integration tests, direct function calls for unit tests
- One library file per domain: `pitch.py`, `chords.py`, `scales.py`, `progressions.py` → `analysis.py`

### Integration Points
- New `analysis.py` added to `MCP_Server/theory/` package
- New functions exported from `MCP_Server/theory/__init__.py`
- 3 new tool functions added to `MCP_Server/tools/theory.py`
- Tests added to `tests/test_theory.py`

</code_context>

<specifics>
## Specific Ideas

- Strummed chords that land slightly off-beat should be captured by the quantization window rather than missed or split across segments
- Arpeggios handled naturally by the time grid — notes within a beat/bar window are collected and identified together
- No odd meter support needed — standard time signatures are the target use case

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-harmonic-analysis*
*Context gathered: 2026-03-25*
