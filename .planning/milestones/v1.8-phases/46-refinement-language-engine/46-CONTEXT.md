# Phase 46 Context: Refinement Language Engine

**Phase:** 46 — Refinement Language Engine
**Milestone:** v1.8 Iterative Refinement Protocol
**Requirements:** REFN-01, REFN-02, PARS-02
**Date:** 2026-03-31
**Depends on:** Phase 45 (uses get_section_state internals + schema)

## Goal

Three tools:
1. `REFINEMENT_LEXICON` — 20+ aesthetic adjectives mapped to multi-domain `RefinementVector` deltas
2. `interpret_section_refinement(section_name, instruction)` — reads section state, maps instruction
   through lexicon, returns a read-only `SectionRefinementPlan` with per-track note ops + device targets
3. `refine_prompt(brief, refinement_text)` — takes an existing `ProductionBrief` + follow-up text,
   selectively re-derives only affected fields, returns updated brief + diff

## Codebase Scouting

### What exists and will be reused

| Asset | Location | Used for |
|-------|----------|----------|
| `classify_prompt` | `MCP_Server/prompt/parser.py` | Tokenize refinement instruction |
| `_derive_energy_level` | `MCP_Server/prompt/deriver.py:98` | refine_prompt energy re-derivation |
| `_derive_tempo` | `MCP_Server/prompt/deriver.py:112` | refine_prompt tempo re-derivation |
| `_derive_key_feel` | `MCP_Server/prompt/deriver.py:165` | refine_prompt key_feel re-derivation |
| `_derive_groove_feel` | `MCP_Server/prompt/deriver.py:197` | refine_prompt groove re-derivation |
| `_derive_velocity_style` | `MCP_Server/prompt/deriver.py:266` | refine_prompt velocity re-derivation |
| `ProductionBrief` TypedDict | `MCP_Server/prompt/schema.py` | refine_prompt input/output type |
| `get_ableton_connection` | `MCP_Server/connection.py` | RS calls for section state |
| `CATALOG` | `MCP_Server/devices/catalog.py` | Device param lookup for device targets |
| `natural_to_normalized` | `MCP_Server/devices/convert.py` | Timbral delta computation |
| `normalized_to_natural` | `MCP_Server/devices/convert.py` | Reading current param display values |
| Phase 45 `_note_summary`, `_device_summary`, `_recipe_delta` | `MCP_Server/tools/refinement.py` | Can be imported as internal helpers |
| Phase 45 RS commands | `get_arrangement_state`, `get_arrangement_clips`, `get_arrangement_clip_notes`, `get_mix_state` | Called directly from interpreter |

## Locked Decisions

### D-01: RefinementVector uses None-able fields (not zero defaults)

Fields that don't apply to an adjective are `None`, not `0`. This lets the interpreter
skip dimensions that the adjective didn't specify, rather than applying a zero-delta
(which would compute a no-op but add noise to the reasoning).

Example: "higher" → `harmonic.register_shift_semitones=+5`, timbral and dynamic both `None`.
"darker" → all three dimensions specified.

### D-02: REFINEMENT_LEXICON maps normalized terms (underscores, lowercase)

Same normalization as prompt lexicon: input tokens are lowercased + spaces→underscores
before lookup. "More energetic" → "more_energetic". Multi-word phrases listed explicitly
in the lexicon. Single-word adjectives are also listed.

### D-03: interpret_section_refinement does NOT call the get_section_state MCP tool

It calls the RS commands directly (like Phase 45 `get_section_state` does internally)
to avoid double JSON serialization. It re-reads the section state inline.

Alternative considered: parse the section state JSON from `get_section_state()`. Rejected —
introduces extra parsing step and couples Phase 46 to Phase 45's JSON output format.
**Decision: share the RS command dispatch logic, not the MCP tool wrapper.**

### D-04: SectionRefinementPlan schema additions

New TypedDicts added to `MCP_Server/refinement/schema.py`:

```python
class NoteOperation(TypedDict):
    semitone_shift: int          # applied to all notes in section clips
    density_delta: int           # +1 denser, -1 sparser, 0 unchanged
    scale_substitutions: list    # [{from_pitch_class: int, to_pitch_class: int}]
    velocity_shift: int          # +/- MIDI velocity (0 = unchanged)

class DeviceChange(TypedDict):
    device_name: str
    class_name: str
    param_name: str
    current_normalized: float
    target_normalized: float
    reason: str

class TrackRefinementEntry(TypedDict):
    track_name: str
    track_index: int
    note_operation: NoteOperation
    device_changes: list         # list[DeviceChange]

class SectionRefinementPlan(TypedDict):
    section: str
    instruction: str
    vector: dict                 # merged RefinementVector as dict (for transparency)
    tracks: list                 # list[TrackRefinementEntry]
    reasoning: list              # plain-English explanation list
```

### D-05: Scale substitutions for mode_bias

When `harmonic.mode_bias == "minor"`: suggest lowering the major 3rd (pitch class 4 → 3)
and major 6th (pitch class 9 → 8). This is the parallel-minor substitution.
When `mode_bias == "major"`: raise minor 3rd (3 → 4) and minor 6th (8 → 9).
When `mode_bias is None`: `scale_substitutions = []`.

No music theory engine required — these are fixed pitch class remappings.

### D-06: Device parameter targets from RefinementVector timbral delta

Three timbral dimensions map to specific device params:

| Vector field | Device class | Param name | Application |
|---|---|---|---|
| `filter_cutoff_delta_pct` | `AutoFilter` | `Frequency` | current * (1 + delta/100), clamp 0-1 |
| `brightness_db` | `Eq8` | `Gain 4` (band 4 = high shelf) | natural + brightness_db, re-normalize |
| `reverb_wet_delta` | `Reverb` | `Wet/Dry Mix` | current + delta, clamp 0-1 |

If the track has no device of that class, the change is silently skipped.
If `timbral` is None (adjective doesn't specify timbre), skip all device changes.

Dynamic vector:
| Vector field | Device class | Param | Application |
|---|---|---|---|
| `compression_ratio_delta` | `Compressor2` | `Ratio` | current + delta, clamp 0-1 |

`velocity_shift` goes into `NoteOperation.velocity_shift` (applied to notes in Phase 47).

### D-07: Vector merging for multi-word instructions

When instruction has multiple adjectives ("darker and heavier"), look up each adjective
in the lexicon and SUM the deltas for each dimension. Fields that are None in one vector
are ignored (not summed as 0). Final merged vector is clamped to sensible ranges.

Clamp rules:
- `register_shift_semitones`: clamp to [-12, +12]
- `filter_cutoff_delta_pct`: clamp to [-80, +80]
- `brightness_db`: clamp to [-12, +12]
- `velocity_shift`: clamp to [-40, +40]
- `density_delta`: clamp to [-2, +2]
- `reverb_wet_delta` and `compression_ratio_delta`: clamp to [-0.5, +0.5]

### D-08: refine_prompt selective re-derivation logic

Signal types trigger specific field re-derivation:
- `tempo_signals` present → re-derive `tempo_range` using `_derive_tempo(signals, original_genre)`
- `mood_signals` present → re-derive `key_feel`, `energy_level`, `velocity_style`
- `genre_signals` present → re-derive `primary_genre`, `tempo_range`, `key_feel`,
  `groove_feel`, `instrument_hints` (all genre-dependent fields)
- `structural_hints` with groove keywords → re-derive `groove_feel`
- `effect_signals` present → re-derive `effect_hints`
- `instrument_signals` present → prepend new instruments to `instrument_hints`

Fields not covered by any found signal type retain their original values verbatim.

### D-09: refine_prompt returns diff dict

`diff` format: `{field_name: {"before": old_value, "after": new_value}}` — only includes
fields that actually changed. Empty diff is valid (unrecognized instruction → no changes).

### D-10: Low-confidence original brief warning in refine_prompt

If `original_brief["confidence"] < 0.3`, add a reasoning entry:
`"Warning: original brief has low confidence ({:.2f}) — some fields may be unreliable"`.
Derivation still runs normally.

### D-11: Module layout

New files:
- `MCP_Server/refinement/lexicon.py` — `RefinementVector` TypedDict + `REFINEMENT_LEXICON`
- `MCP_Server/refinement/interpreter.py` — `build_section_refinement_plan(section_name, instruction, conn, beats_per_bar)` pure logic

Modified files:
- `MCP_Server/refinement/schema.py` — add `NoteOperation`, `DeviceChange`, `TrackRefinementEntry`, `SectionRefinementPlan`
- `MCP_Server/tools/refinement.py` — add `interpret_section_refinement` + `refine_prompt` MCP tools

### D-12: REFINEMENT_LEXICON adjectives (minimum 20)

Must include: darker, brighter, warmer, colder, harder, softer, heavier, lighter,
sparser, denser, higher, lower, more_energetic, less_energetic, more_melodic,
more_rhythmic, more_spacious, tighter, dirtier, cleaner.

"Darker" vector (canonical example from requirements):
```python
{
    "harmonic": {"register_shift_semitones": -3, "mode_bias": "minor", "density_delta": 0},
    "timbral": {"filter_cutoff_delta_pct": -25.0, "brightness_db": -2.0, "reverb_wet_delta": 0.05},
    "dynamic": {"velocity_shift": -8, "compression_ratio_delta": 0.05},
}
```

## Test Coverage

| Test | What it verifies |
|------|-----------------|
| `test_lexicon_has_20_adjectives` | len(REFINEMENT_LEXICON) >= 20 |
| `test_darker_vector_shape` | "darker" has all three domain keys, register_shift_semitones=-3 |
| `test_vector_merge_accumulates` | "darker" + "heavier" summed register_shift correctly |
| `test_interpret_section_refinement_returns_plan` | mock section → SectionRefinementPlan with tracks |
| `test_interpret_section_refinement_reasoning` | reasoning has >=1 entry per track |
| `test_interpret_unknown_instruction` | unrecognized → tracks=[], reasoning explains |
| `test_refine_prompt_mood_only` | "make it darker" mood signal → key_feel updated, primary_genre unchanged |
| `test_refine_prompt_tempo` | "speed it up to 140" → tempo_range=(135, 145), other fields unchanged |
| `test_refine_prompt_diff` | diff contains only changed fields |
| `test_refine_prompt_low_confidence_warning` | confidence<0.3 → warning in reasoning |
| `test_scale_substitutions_minor` | mode_bias="minor" → substitutions include {from:4, to:3} |
| `test_device_change_filter_cutoff` | timbral filter_cutoff_delta_pct → AutoFilter Frequency target |
