# Phase 6: MIDI Editing - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete MIDI note editing capabilities — add, read, remove, quantize, and transpose notes in MIDI clips. This phase covers note data manipulation only. Clip lifecycle (create, delete, loop) is Phase 5 (complete). Device/instrument loading is Phase 7. Audio clip properties are Phase 10.

</domain>

<decisions>
## Implementation Decisions

### Note addition behavior
- Append mode using Live 11+ `add_new_notes` API — existing notes stay, new notes are added on top
- Replace the current `set_notes(tuple)` implementation which overwrites all notes
- Return `{note_count: N, clip_name: "..."}` — lightweight, AI already knows what it sent
- Keep `mute` parameter (already implemented, useful for ghost/draft notes)
- Validate note values in the handler: pitch 0-127, velocity 1-127, duration > 0 — clear error messages with specific out-of-range values

### Get notes response
- Return core 5 properties per note: pitch, start_time, duration, velocity, mute
- Always return ALL notes — no time/pitch range filtering (AI can filter client-side)
- Include note_count alongside notes array: `{note_count: N, notes: [...]}`
- Sort notes by start_time ascending, ties broken by pitch (low to high)

### Remove notes targeting
- Time + pitch range parameters: start_time_min, start_time_max, pitch_min, pitch_max — all optional
- Omitting a param means "no constraint" on that dimension
- Return `{removed_count: N}` — lightweight confirmation
- Claude's Discretion: behavior when all range params omitted (remove all vs require at least one)

### Quantize behavior
- Operates on ALL notes in clip — no range filter
- Grid size as float in beats: 0.25 for 1/16th, 0.5 for 1/8th, 1.0 for 1/4 — consistent with existing beat-based params
- Strength defaults to 100% (full snap to grid), adjustable 0.0-1.0
- Quantizes start times only (standard behavior)

### Transpose behavior
- Operates on ALL notes in clip — no range filter
- Semitones as integer (positive = up, negative = down)
- Error if ANY note would go out of MIDI range (0-127) — strict validation, AI must check range before calling
- Error message includes the offending note's current pitch and the requested transposition

### Claude's Discretion
- Whether remove_notes with no range params removes all notes or requires at least one range constraint
- Internal implementation of quantize algorithm (snap-to-nearest-grid-point)
- Whether quantize/transpose responses include the updated note count

</decisions>

<specifics>
## Specific Ideas

- Error messages designed for AI self-correction — include current values when validation fails (carried from Phase 4/5)
- All responses use `json.dumps(result, indent=2)` for consistency (carried from Phase 5)
- Regular tracks only — no track_type parameter (carried from Phase 5)
- Round-trip friendly: get_notes returns the same 5 properties that add_notes accepts

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_resolve_clip_slot(song, track_index, clip_index)` in handlers/clips.py: validated clip slot resolution — reuse for all note operations
- `_clip_info_dict(clip)` in handlers/clips.py: standard clip info builder
- `NoteHandlers` mixin in handlers/notes.py: already has `_add_notes_to_clip` — needs rewrite to use `add_new_notes` API
- `add_notes_to_clip` MCP tool in tools/clips.py: already exists — needs update to return JSON
- `format_error(title, detail, suggestion)` in connection.py: AI-friendly error formatting
- `@command('name', write=True)` decorator for state-modifying commands

### Established Patterns
- Mixin class pattern: NoteHandlers inherited by AbletonMCP
- `@command` decorator with `write=True` for set/modify operations, no flag for read operations
- `get_ableton_connection().send_command()` pattern in MCP tools
- JSON response format with `json.dumps(result, indent=2)`
- Conditional params dict building (see `set_clip_loop` pattern)
- Validation errors include current values for AI self-correction

### Integration Points
- handlers/notes.py: Rewrite `_add_notes_to_clip`, add `_get_notes`, `_remove_notes`, `_quantize_clip_notes`, `_transpose_clip_notes`
- MCP_Server/tools/clips.py or new tools/notes.py: Add/update MCP tool definitions
- Import `_resolve_clip_slot` from handlers/clips.py into handlers/notes.py
- tests/: Add notes domain smoke tests

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-midi-editing*
*Context gathered: 2026-03-14*
