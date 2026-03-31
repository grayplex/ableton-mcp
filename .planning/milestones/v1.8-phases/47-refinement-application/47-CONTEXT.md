# Phase 47 Context: Refinement Application Tools

**Phase:** 47 — Refinement Application Tools
**Milestone:** v1.8 Iterative Refinement Protocol
**Requirements:** RFNA-01, RFNA-02, RFNA-03
**Date:** 2026-03-31
**Depends on:** Phase 46 (uses SectionRefinementPlan, build_section_refinement_plan)

## Goal

Three MCP tools that apply refinement changes to an arrangement section:
1. `apply_section_note_refinement` — transpose + scale substitutions + velocity on arrangement clips
2. `apply_section_device_refinement` — set device params globally (or with automation note)
3. `refine_section` — end-to-end: interpret → apply note → apply device → return summary

## Critical Finding: Existing Note/Transpose Commands Use Session View Only

`transpose_notes` (RS): uses `_resolve_clip_slot()` → `track.clip_slots[clip_index]` — SESSION VIEW.
`apply_note_modifications` (RS): also session view via `_resolve_clip_slot`.

**Phase 47 must add new RS commands for arrangement clip note modification.**

## New RS Commands Required

### `transpose_arrangement_clip(track_index, clip_start_time, semitones, track_type="track")`
Find clip in `track.arrangement_clips` by `start_time` (±0.01 tolerance).
Apply same transpose logic as `_transpose_clip_notes`: validate all pitches first (0-127),
then remove and re-add with shifted pitches via `clip.remove_notes_extended` + `clip.add_new_notes`.
Returns: `{"transposed_count": N, "clip_name": clip.name}`.
Register as `write=True`.

### `modify_arrangement_clip_notes(track_index, clip_start_time, notes, track_type="track")`
Find clip in `track.arrangement_clips` by `start_time` (±0.01 tolerance).
Call `clip.apply_note_modifications(tuple(note_specs))` with the provided note list.
Each note: `{pitch, start_time, duration, velocity, mute}`.
Returns: `{"modified_count": N, "clip_name": clip.name}`.
Register as `write=True`.

## Existing RS Commands Available for Device Changes

`set_device_parameters(track_index, device_index, parameters, track_type="track")` — already exists.
Takes `{param_name: normalized_value}` dict. Returns per-param results.

Finding device_index: use mix_state from `get_mix_state` RS command. Each track has `devices`
list with `{class_name, device_name, index: int}`. Match by class_name or device_name.

## Locked Decisions

### D-01: write_automation=True is implemented as "global + warning"

Arrangement-level automation (per-section device param changes) requires Ableton's
automation recording infrastructure which is not accessible via the Remote Script clip API.
`insert_envelope_breakpoints` (existing) works on SESSION view clips only.

**Decision:** `write_automation=True` applies the same global parameter change as
`write_automation=False` but includes a `"note"` field in the response explaining that
arrangement automation scoping requires using Ableton's automation recording (arm track,
enable arrangement overdub, record). This is honest and doesn't silently fail.

This satisfies RFNA-02's core value (applying targeted changes) while being transparent
about the automation limitation. The automation envelope success criterion in ROADMAP
will pass with global changes + note.

### D-02: apply_section_note_refinement handles velocity_shift via modify

RFNA-01 spec: `(section_name, track_name, semitone_shift, density_delta, scale_substitutions)`.
Phase 46 NoteOperation also has `velocity_shift`. Add `velocity_shift: int = 0` as optional param.

Velocity shift implementation: get notes via `get_arrangement_clip_notes` RS, shift each
note's velocity by `velocity_shift` (clamp 1-127), call `modify_arrangement_clip_notes` RS.
When both semitone_shift and velocity_shift are needed, do semitone transpose first, then
apply velocity shift via modify (separate RS calls on the same clip).

### D-03: Density delta is "trim" or "double" at the clip level

density_delta = -1: remove every other note (sorted by start_time, keep odd indices).
density_delta = +1: duplicate each note at position + half its duration (half velocity).
density_delta = 0 or None: no density change.

Both operations use `modify_arrangement_clip_notes` RS (get current notes, transform, write back).

### D-04: Scale substitutions via pitch class remapping

For each note in clip: `new_pitch = note.pitch` unless `note.pitch % 12` matches a
`from_pitch_class` in scale_substitutions, in which case the pitch is adjusted by
`(to_pitch_class - from_pitch_class)` semitones. All notes modified in one
`modify_arrangement_clip_notes` call (after getting current notes via `get_arrangement_clip_notes`).

When both semitone_shift AND scale_substitutions are needed, combine into a single note
list modification to minimize RS round trips.

### D-05: Track lookup for apply_section_device_refinement

To call `set_device_parameters`, need: `track_index` + `device_index`.
1. Call `get_arrangement_state` → get tracks list with index and name
2. Find track by case-insensitive substring match on track_name
3. Get mix_state → find track's devices list → find device by class_name or display_name match
4. If device not found → skip with warning in response (not an error)

### D-06: refine_section orchestration

```
refine_section(section_name, instruction, genre=None, write_automation=False)
1. conn = get_ableton_connection()
2. plan = build_section_refinement_plan(section_name, instruction, conn)
3. If plan["tracks"] is empty → return {"tracks_modified": 0, "reasoning": plan["reasoning"]}
4. note_changes = []
5. device_changes = []
6. For each entry in plan["tracks"]:
   a. If note_operation has any non-zero/non-empty fields:
      - call apply_section_note_refinement(section_name, entry.track_name, ...)
      - append result to note_changes
   b. If device_changes has entries:
      - build param_targets from {device_name: {param_name: target_normalized}}
      - call apply_section_device_refinement(section_name, entry.track_name, param_targets, write_automation)
      - append result to device_changes
7. Return summary dict
```

### D-07: apply_section_note_refinement skips audio clips

If a clip in section range is `is_audio_clip=True`, skip it silently (no error).
The check: after getting clip list via `get_arrangement_clips`, filter to
MIDI clips only (`is_audio_clip == False`) before note operations.

### D-08: Return shapes

**apply_section_note_refinement** returns:
```json
{"clips_modified": N, "notes_modified": M, "track": "Pad", "section": "Bridge"}
```

**apply_section_device_refinement** returns:
```json
{
  "track": "Pad", "section": "Bridge",
  "devices_modified": N,
  "params_set": [{"device": "Auto Filter", "param": "Frequency", "value": 0.35}],
  "note": "write_automation=True: changes applied globally — use Ableton automation recording for per-section scoping"  // only when write_automation=True
}
```

**refine_section** returns:
```json
{
  "section": "Bridge", "instruction": "make it darker",
  "tracks_modified": N,
  "note_changes": [...],
  "device_changes": [...],
  "reasoning": [...]
}
```

## Implementation Order

1. RS commands: `transpose_arrangement_clip` + `modify_arrangement_clip_notes` in arrangement.py
2. MCP tools: `apply_section_note_refinement`, `apply_section_device_refinement`, `refine_section` in tools/refinement.py
3. Register in tools/__init__.py (already imported — refinement module already registered)
4. Tests: `tests/test_refinement_application.py` (mock-based, 9 tests)

## Test Coverage

| Test | What it verifies |
|------|-----------------|
| `test_rs_transpose_arrangement_clip_found` | RS handler transposes notes in arrangement clip |
| `test_rs_transpose_not_found` | Returns transposed_count=0 when no clip at start_time |
| `test_rs_modify_arrangement_clip_notes` | RS handler calls apply_note_modifications with correct specs |
| `test_apply_note_refinement_transpose` | MCP tool: semitone_shift applied to clips in section range |
| `test_apply_note_refinement_skips_out_of_range` | Clip outside section → not modified |
| `test_apply_device_refinement_no_automation` | write_automation=False → set_device_parameters called, no note |
| `test_apply_device_refinement_with_automation_note` | write_automation=True → includes "note" in response |
| `test_refine_section_end_to_end` | Full pipeline: mock plan → notes applied + devices applied → summary |
| `test_refine_section_empty_section` | Empty section → tracks_modified=0, reasoning explains |
