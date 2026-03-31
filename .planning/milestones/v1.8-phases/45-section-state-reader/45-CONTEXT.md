# Phase 45 Context: Section State Reader

**Phase:** 45 — Section State Reader
**Milestone:** v1.8 Iterative Refinement Protocol
**Requirements:** SNAP-01, SNAP-02
**Date:** 2026-03-31

## Goal

`get_section_state(section_name)` — single MCP tool that returns everything
Claude already built in a named arrangement section: bar range, per-track clips
with note summaries, and mix context (device params + recipe delta). No
refinement logic — pure read.

## Codebase Scouting

### What exists and will be reused

| Asset | Location | Used for |
|-------|----------|----------|
| `_beat_to_bar` / `_bar_to_beat` | `MCP_Server/tools/scaffold.py:57-88` | Beat ↔ bar conversion |
| `get_arrangement_state` RS command | Called by `get_arrangement_overview` | Resolves locators + tracks |
| `get_arrangement_clips` RS command | `AbletonMCP_Remote_Script/handlers/arrangement.py:78` | Gets clips per track |
| `get_mix_state` RS command | Called by analysis + intelligence tools | Device param snapshot |
| `_infer_role` | `MCP_Server/tools/analysis.py:27` | Role inference from track name |
| `_find_track` | `MCP_Server/tools/intelligence.py:17` | Track lookup in mix state |
| `suggest_mix_adjustments` internals | `MCP_Server/tools/intelligence.py:92` | Recipe delta computation |
| `prompt/schema.py` | `MCP_Server/prompt/schema.py` | TypedDict pattern to follow |
| `DIFF_THRESHOLD = 0.03` | `MCP_Server/tools/intelligence.py:14` | Recipe delta threshold |

### Critical finding: `get_notes` does NOT work for arrangement clips

`get_notes` (RS command) uses `_resolve_clip_slot(song, track_index, clip_index)` which
accesses `track.clip_slots[clip_index]` — **session view only**.

Arrangement clips are accessed via `track.arrangement_clips` (a list of Clip objects).
There is no existing RS command to get notes from an arrangement clip.

**Decision: Add new RS command `get_arrangement_clip_notes`** (see RS section below).

### `get_arrangement_clips` return shape (confirmed from RS handler)

```json
{
  "track_name": "Pad",
  "clips": [
    {
      "name": "clip name",
      "start_time": 16.0,   // beats, 0-indexed
      "end_time": 32.0,     // beats
      "length": 16.0,       // beats
      "is_audio_clip": false,
      "color": "orange"
    }
  ]
}
```

### Arrangement clip position vs bar position

Locators from `get_arrangement_state` return `cue_points[].time` in **beats** (0-indexed).
Clip `start_time` / `end_time` from `get_arrangement_clips` are also in **beats**.
Section bar range is computed from locator beat positions using `_beat_to_bar`.
Clip filtering is done beat-space: `clip.start_time >= section_start_beat AND clip.start_time < section_end_beat`.

## Locked Decisions

### D-01: New RS command required for arrangement clip notes

Add `get_arrangement_clip_notes(track_index, clip_start_time)` to the arrangement
handler. It finds the clip in `track.arrangement_clips` whose `start_time` matches
(±0.01 beat tolerance) and returns the same note format as `get_notes`:
```json
{"note_count": N, "notes": [{"pitch", "start_time", "duration", "velocity", "mute"}]}
```
Returns `{"note_count": 0, "notes": []}` if clip not found (no exception).
Register as a read command (no `write=True`).

### D-02: Package layout

```
MCP_Server/refinement/
  __init__.py          (empty, marks package)
  schema.py            (SectionState, TrackStateEntry, ClipSummary TypedDicts only)
MCP_Server/tools/
  refinement.py        (get_section_state MCP tool — Phase 45 only)
```
No sub-packages. Same pattern as `MCP_Server/prompt/` (schema separate from tools).

### D-03: Note summary is MCP-side computation, not RS-side

The RS command returns raw notes. The MCP tool computes:
- `pitch_min`: `min(note["pitch"] for note in notes)` or `None` when empty
- `pitch_max`: `max(note["pitch"] for note in notes)` or `None` when empty
- `note_count`: `len(notes)`
- `dominant_octave`: `(pitch_min + pitch_max) // 2 // 12` (integer division MIDI octave)
- `rhythm_density`: `note_count / clip_length_in_bars` (notes per bar, float)

### D-04: Section bar range from locators

`get_arrangement_state` returns cue_points sorted by position. The section named
`section_name` has `start_bar = _beat_to_bar(locator.time, beats_per_bar)`.
The `end_bar` is the next locator's bar position (or `session_length_bars` if it's
the last section). If no locator matches (case-insensitive), return:
```json
{"section": "Bridge", "tracks": [], "error": "Section 'Bridge' not found in arrangement"}
```

### D-05: Mix context uses direct RS calls, not MCP tool wrappers

`get_section_state` calls `get_mix_state` RS command directly (like `suggest_mix_adjustments`
does) — not `get_mix_state()` the MCP tool — to avoid double JSON parsing.
Same for `get_arrangement_state`.

### D-06: Recipe delta in mix_context is optional

`mix_context.recipe_delta` is populated only when:
1. The caller passes `genre` param to `get_section_state` (optional, default `None`)
2. `_infer_role(track_name)` returns a non-None role
3. `get_recipe(role, genre)` returns a recipe

If any of these fail, `recipe_delta` is an empty list (not an error).

### D-07: Prominent device parameters per device type

For `mix_context.device_params`, use these 3 fixed params per recognized device class:
- `AutoFilter`: `["Frequency", "Resonance", "Filter Type"]`
- `Compressor2`: `["Threshold", "Ratio", "Attack Time"]`
- `Eq8` (EQ Eight): `["Frequency 1", "Gain 1", "Frequency 4"]`
- Unknown devices: first 3 parameters by list order from mix state

### D-08: Clip filtering includes clips that START in the section range

A clip is "in the section" if: `section_start_beat <= clip.start_time < section_end_beat`.
Clips that overlap the boundary (start before, end inside) are excluded to keep the
definition clean. Audio clips are included in clip list but skipped for note summaries
(`is_audio_clip = True` → `note_summary = None`).

### D-09: Only MIDI tracks with clips in range appear in SectionState.tracks

Tracks with zero clips in the section range are omitted entirely (not shown with empty
clip lists). This keeps `SectionState` concise for sections where only 3 of 8 tracks
have content.

### D-10: `get_section_state` MCP tool signature

```python
def get_section_state(ctx: Context, section_name: str, genre: str = None) -> str:
```
`genre` is optional — enables recipe_delta when provided.

## TypedDict Schemas

```python
class ClipSummary(TypedDict):
    name: str
    start_bar: int          # 1-indexed bar within arrangement
    end_bar: int            # 1-indexed exclusive end bar
    length_bars: int
    is_audio: bool
    note_count: int | None           # None for audio clips
    pitch_min: int | None
    pitch_max: int | None
    dominant_octave: int | None      # MIDI octave 0–9
    rhythm_density: float | None     # notes per bar

class DeviceParamSummary(TypedDict):
    device_name: str
    class_name: str
    prominent_params: dict           # {param_name: normalized_float}

class TrackStateEntry(TypedDict):
    track_name: str
    track_index: int
    role: str | None                 # inferred via _infer_role
    clips: list                      # list[ClipSummary]
    mix_context: dict                # {volume, pan, devices, recipe_delta}

class SectionState(TypedDict):
    section: str
    start_bar: int
    end_bar: int
    tracks: list                     # list[TrackStateEntry]
    error: str | None
```

## Implementation Order

1. **RS handler** — add `get_arrangement_clip_notes` to `AbletonMCP_Remote_Script/handlers/arrangement.py`
2. **Schema** — `MCP_Server/refinement/__init__.py` + `schema.py` (TypedDicts)
3. **MCP tool** — `MCP_Server/tools/refinement.py` with `get_section_state`
4. **Register** — add `from MCP_Server.tools.refinement import *` to `tools/__init__.py`
5. **Tests** — `tests/test_section_state.py` (mock-based, all 5 success criteria)
6. **pyproject.toml** — add `MCP_Server.refinement` to packages list

## Test Coverage (all mock-based, no live Ableton)

| Test | What it verifies |
|------|-----------------|
| `test_section_not_found` | Returns `{"section": "X", "tracks": [], "error": "...not found..."}` |
| `test_section_with_clips` | 2 tracks × 3 clips → correct TrackStateEntry count and ClipSummary fields |
| `test_note_summary_computed` | pitch_min/max/dominant_octave/rhythm_density correct for 4-note mock |
| `test_audio_clip_excluded_from_notes` | is_audio=True → note_summary fields are None |
| `test_mix_context_no_genre` | recipe_delta=[] when genre=None |
| `test_mix_context_with_recipe_delta` | recipe_delta populated for Compressor params >20% off recipe |
| `test_empty_section` | Section exists but no clips in range → tracks=[] error=None |
| `test_get_arrangement_clip_notes_rs` | RS handler returns notes for clip at matching start_time |

## Out of Scope for Phase 45

- Refinement interpretation (Phase 46)
- Any write operations
- Cross-section comparison
- Session-view clips (arrangement only)
