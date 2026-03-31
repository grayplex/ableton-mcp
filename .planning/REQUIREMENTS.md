# Requirements: AbletonMCP v1.8 Iterative Refinement Protocol

**Defined:** 2026-03-31
**Core Value:** An AI assistant can refine a section of a production — "make the bridge darker" — by reading back what it already built, interpreting the instruction in context, and surgically modifying just that section without touching anything else.

## v1.8 Requirements

### Section State Reader

- [x] **SNAP-01**: `get_section_state(section_name)` MCP tool returns a `SectionState` TypedDict snapshot of everything in the named arrangement section: (a) section bar range (start_bar, end_bar resolved from locator names via `get_arrangement_overview`), (b) per-track list of `TrackStateEntry` dicts each containing track name, track index, role (inferred from track name), and a list of clips in that bar range with their positions, (c) per-clip note summary (pitch_min, pitch_max, note_count, dominant_octave, rhythm_density notes/bar); missing or empty sections return a descriptive error, not an exception

- [x] **SNAP-02**: Each `TrackStateEntry` in `SectionState` includes a `mix_context` dict: current normalized volume and pan, the loaded device names (top-level chain only), and for each recognized device type (EQ Three, Auto Filter, Compressor) the 3 most prominent current parameter values; if the track's role is resolvable and a genre recipe exists, `recipe_delta` lists params that deviate >20% from recipe targets (reuses `suggest_mix_adjustments` internals) — providing "what's already there" before any refinement

### Refinement Language Engine

- [ ] **REFN-01**: A `RefinementLexicon` in `MCP_Server/refinement/lexicon.py` maps 20+ aesthetic adjectives to multi-domain `RefinementVector` TypedDicts: `{harmonic: {register_shift_semitones, mode_bias, density_delta}, timbral: {filter_cutoff_delta_pct, brightness_db, reverb_wet_delta}, dynamic: {velocity_shift, compression_ratio_delta}}`; adjectives covered include at minimum: darker, brighter, warmer, colder, harder, softer, heavier, lighter, sparser, denser, higher, lower, more energetic, less energetic, more melodic, more rhythmic, more spacious, tighter, dirtier, cleaner; each vector uses signed proportional deltas (not absolute values) so application is always relative to current state

- [ ] **REFN-02**: `interpret_section_refinement(section_name, instruction)` MCP tool: calls `get_section_state` to read the current section, tokenizes the instruction through the prompt parser's tokenizer for signal extraction, maps tokens through `RefinementLexicon` to produce a merged `RefinementVector`, then resolves the vector against actual current values to produce a `SectionRefinementPlan` TypedDict — listing per-track note operations (semitone shifts, density changes), per-track device parameter targets (absolute values derived from current + delta), and a plain-English `reasoning` list explaining each proposed change; tool is read-only (applies nothing)

- [ ] **PARS-02**: `refine_prompt(brief, refinement_text)` MCP tool accepts an existing `ProductionBrief` dict and a follow-up refinement string ("add more swing", "make it darker", "speed it up to 140"), re-derives only the parameters affected by the refinement signals (leaving unaffected fields unchanged), returns an updated `ProductionBrief` plus a `diff` dict showing exactly which fields changed and why; confidence does not drop if primary_genre is unchanged; low-confidence original brief produces a warning in reasoning but derivation still runs

### Refinement Application

- [ ] **RFNA-01**: `apply_section_note_refinement(section_name, track_name, semitone_shift, density_delta, scale_substitutions)` MCP tool: resolves the section bar range, identifies all arrangement clips for `track_name` that fall within the range, applies the specified operations — `semitone_shift` transposes all notes via `transpose_notes` (positive = up, negative = down), `density_delta` trims (removes highest-velocity outliers) or doubles (duplicates pattern at half velocity) notes when nonzero, `scale_substitutions` (list of `{from_pitch_class, to_pitch_class}`) remaps MIDI note pitch classes via `apply_note_modifications`; clips outside the section range are untouched; returns a summary of how many clips and notes were modified

- [ ] **RFNA-02**: `apply_section_device_refinement(section_name, track_name, param_targets, write_automation)` MCP tool: resolves the section bar range from locators; if `write_automation=False` (default), applies `param_targets` dict (device_name → {param_name: normalized_value}) globally to the track via `set_device_parameters` with a warning that the change affects all sections; if `write_automation=True`, writes automation envelopes for each parameter over the section bar range (start_bar to end_bar) using existing automation tools, inserting breakpoints just before and just after the section to restore pre-refinement values — enabling per-section timbral changes without affecting other sections; returns applied parameters and automation point count

- [ ] **RFNA-03**: `refine_section(section_name, instruction, genre, write_automation)` MCP tool: end-to-end single-call refinement — calls `interpret_section_refinement` to get the `SectionRefinementPlan`, then for each track in the plan calls `apply_section_note_refinement` (if note operations present) and `apply_section_device_refinement` (if device changes present), collects all change summaries, and returns a structured result with `section`, `instruction`, `tracks_modified`, `note_changes`, `device_changes`, and `reasoning`; `genre` parameter enables recipe_delta context in state read; `write_automation` passed through to `apply_section_device_refinement`; if no changes are applicable (section empty or instruction unrecognized), returns a clear explanation rather than an error

## Future Requirements

### Refinement History

- **REFN-03**: `list_section_refinements(section_name)` — session-scoped log of refinements applied to a section, each entry recording the original instruction, `SectionRefinementPlan`, and timestamp; enables Claude to say "here's what was already changed" and detect conflicting refinements — deferred to post-v1.8

### Undo/Revert

- **RFNA-04**: `revert_section_refinement(section_name, track_name, revert_to)` — reads a previous `SectionRefinementPlan` from history and applies inverse operations (negate semitone_shift, restore saved device params); requires REFN-03 — deferred

### Cross-Section Comparison

- **SNAP-03**: `compare_sections(section_a, section_b)` — returns a diff of `SectionState` between two named sections: which tracks differ, by how much (note density, pitch register, device parameters); helps Claude explain "the bridge is already darker than the verse" without applying changes — deferred

## Out of Scope

| Feature | Reason |
|---------|--------|
| Audio clip pitch manipulation via refinement | Audio pitch requires warp-based editing; out of scope for note refinement path |
| Real-time parameter modulation | MCP is request/response; no streaming control |
| Undo stack integration (Ableton native) | Ableton's undo tracks individual actions; batch undo not accessible via Remote Script API |
| Cross-session state persistence | Session state is ephemeral; persistence requires external storage not yet scoped |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SNAP-01 | Phase 45 | Complete |
| SNAP-02 | Phase 45 | Complete |
| REFN-01 | Phase 46 | Pending |
| REFN-02 | Phase 46 | Pending |
| PARS-02 | Phase 46 | Pending |
| RFNA-01 | Phase 47 | Pending |
| RFNA-02 | Phase 47 | Pending |
| RFNA-03 | Phase 47 | Pending |

**Coverage:**
- v1.8 requirements: 8 total
- Mapped to phases: 8
- Unmapped: 0

---
*Requirements defined: 2026-03-31*
*Last updated: 2026-03-31 — v1.8 milestone opened*
