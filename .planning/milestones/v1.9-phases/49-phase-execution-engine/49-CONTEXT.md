# Phase 49 Context: Phase Execution Plan Engine

**Phase:** 49 — Phase Execution Plan Engine
**Milestone:** v1.9 Orchestration/Agent Loop
**Requirements:** EXEC-01, EXEC-02
**Date:** 2026-03-31
**Mode:** --auto

## Goal

`get_phase_execution_plan(phase_name, genre, section_name?, context?)` — returns a
`PhaseChecklist` with concrete, ordered `ExecutionStep` entries, each naming the exact
MCP tool and genre-appropriate suggested args. Claude calls this and then executes the
steps in order — no in-context reasoning needed about "what tool to use next".

## Codebase Scouting

### TypedDicts already defined (Phase 48)

`MCP_Server/orchestration/schema.py` already contains `ExecutionStep` and `PhaseChecklist`.
Phase 49 only adds `execution.py` + expands `tools/orchestration.py`.

### Relevant tool signatures

| Tool | Key params | Used in phases |
|------|-----------|----------------|
| `set_tempo` | `tempo: float` | setup |
| `set_scale` | `root_note: int (0-11)`, `scale_name: str` | setup |
| `scaffold_arrangement` | `plan: dict` | setup |
| `get_arrangement_overview` | — | setup, arrangement |
| `create_midi_track` | `index: int = -1` | drums, bass, harmony, melody |
| `set_track_name` | `track_index: int, name: str` | drums, bass, harmony, melody |
| `load_instrument_or_effect` | `track_index: int, instrument_name: str` | drums, bass, harmony, melody, sound_design |
| `create_clip` | `track_index: int, clip_index: int, length: float` | drums, bass, harmony, melody (session view) |
| `create_arrangement_midi_clip` | `track_index: int, start_time: float, length: float` | when section_name provided |
| `add_notes_to_clip` | `track_index: int, clip_index: int, notes: list` | drums, bass, harmony, melody |
| `quantize_notes` | `track_index: int, clip_index: int` | drums |
| `apply_mix_recipe` | `track_index: int, role: str, genre: str` | mix |
| `check_gain_staging` | — | mix |
| `suggest_mix_adjustments` | `genre: str` | mix |
| `apply_master_recipe` | `genre: str` | master |
| `get_arrangement_progress` | — | arrangement |
| `evaluate_session` | `genre: str` | arrangement (gate check) |

### `add_notes_to_clip` notes format

```python
notes = [{"pitch": 36, "start_time": 0.0, "duration": 0.25, "velocity": 100, "mute": False}]
```
- pitch: MIDI pitch 0-127
- start_time: beat offset within clip (0-indexed, float)
- duration: in beats
- velocity: 0-127

### MIDI drum note conventions

- 36: Bass Drum / Kick
- 38: Snare Drum
- 42: Closed Hi-Hat
- 46: Open Hi-Hat
- 39: Hand Clap
- 49: Crash Cymbal
- 51: Ride Cymbal

### `scaffold_arrangement` plan format

```python
{"genre": "house", "sections": [{"name": "Intro", "bars": 8}, {"name": "Drop", "bars": 16}, ...]}
```
Matches `generate_production_plan` output shape.

### Section scoping

When `section_name` is provided, note-writing steps switch from session-view (`create_clip`)
to arrangement-view (`create_arrangement_midi_clip`). The bar range is passed as a sentinel
`"<section_start_beat>"` since it depends on `get_arrangement_overview` at runtime.

## Locked Decisions

### D-01: New module `MCP_Server/orchestration/execution.py`

Contains `_STEP_CATALOG` (nested dict: genre → phase_type → list[step dicts]) plus helper
functions. `get_execution_plan(phase_name, genre, section_name, context)` is the public API.
Genres that share a step pattern point to the same step list via reference.

### D-02: Step catalog architecture

Three layers:
1. `_DEFAULT_STEPS[phase_type]` — generic steps used when no genre-specific override exists
2. `_GENRE_OVERRIDES[genre_id][phase_type]` — replaces default steps for that genre×phase
3. `_GENRE_PARAMS[genre_id]` — parameter overrides applied on top of defaults (BPM, scale, instrument hints)

Most genres share default steps; only drum pattern notes and instrument hints differ. This
keeps the catalog maintainable — add a genre by adding its `_GENRE_PARAMS` entry.

### D-03: Sentinel values for session-state args

Steps that need track index, clip index, or bar position use string sentinels:
- `"<track_index>"` — Claude resolves from `get_all_tracks` output
- `"<clip_index>"` — typically 0 (first slot)
- `"<section_start_beat>"` — from `get_arrangement_overview` locator
- `"<section_length_beats>"` — from section bar range

The `description` field explains the sentinel: "Replace `<track_index>` with the Drums track index from get_all_tracks()".

### D-04: Drum patterns per genre group

**House / Disco / Lo-fi** (4-on-floor kick):
- Kick (36): beats 0.0, 1.0, 2.0, 3.0 — velocity 100
- Clap (39): beats 1.0, 3.0 — velocity 90
- Hi-hat closed (42): 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5 — velocity 70

**Techno / DnB** (heavy kick, driving pattern):
- Kick (36): beats 0.0, 1.0, 2.0, 3.0 — velocity 110
- Hi-hat closed (42): every 0.5 beats — velocity 75
- Percussion (51): 0.5, 2.5 — velocity 60

**Hip-Hop / Trap** (swing kick, hard snare):
- Kick (36): 0.0, 2.5 — velocity 110
- Snare (38): 1.0, 3.0 — velocity 100
- Hi-hat closed (42): every 0.25 beats (16th notes) — velocity 65

**Trance / Synthwave / Future Bass** (driving kick + clap):
- Kick (36): 0.0, 1.0, 2.0, 3.0 — velocity 105
- Clap (39): 1.0, 3.0 — velocity 95
- Hi-hat closed (42): 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5 — velocity 72

**Dubstep** (half-time feel):
- Kick (36): 0.0, 3.0 — velocity 115 (half-time)
- Snare (38): 2.0 — velocity 105 (half-time snare on beat 3)
- Hi-hat closed (42): every 0.5 beats — velocity 68

**Ambient** — no drums phase (skipped in catalog)

### D-05: Instrument hints per genre

Default instruments per phase type (overridden per genre via `_GENRE_PARAMS`):
- drums: "Drum Rack"
- bass: "Analog" (most genres); hip_hop_trap/lo_fi → "Wavetable"
- harmony: "Wavetable" (most); ambient → "Drift"
- melody: "Operator" (most); synthwave → "Wavetable"
- sound_design: "Wavetable"

### D-06: `get_phase_execution_plan` MCP tool signature

```python
async def get_phase_execution_plan(
    ctx: Context,
    phase_name: str,
    genre: str,
    section_name: str = None,
    context: str = None,       # JSON string of partial ProductionBrief or override dict
) -> str:
```

- `phase_name`: must match a phase_type in AGENDA_CATALOG (setup/drums/bass/harmony/melody/sound_design/arrangement/mix/master)
- `genre`: resolved via `resolve_alias`
- `section_name`: if provided, note-writing steps use arrangement view with sentinel bar positions
- `context`: optional JSON override dict; keys: `instrument`, `tempo`, `scale`, `root_note` (override defaults)
- Returns: `json.dumps(PhaseChecklist)` or `json.dumps({"error": "..."})`

### D-07: Token budget for checklist

Maximum 500 tokens (~2000 chars) for serialized PhaseChecklist.
Note arrays are the largest component. Limit:
- Kick pattern: max 8 notes
- Snare/clap: max 4 notes
- Hi-hat: max 8 notes
- Bass line: max 8 notes
- Chord notes: max 4 chords × 3 notes = 12 note events

Total notes across all add_notes_to_clip steps in drums phase: ≤20 notes.
Test validates: `len(json.dumps(result)) < 2000` for each phase type.

### D-08: Setup phase uses genre BPM midpoint and first scale

From `_GENRE_PARAMS[genre_id]`:
- `tempo`: `(bpm_range[0] + bpm_range[1]) // 2` — use blueprint bpm_range
- `root_note`: 0 (C) for most genres
- `scale_name`: first entry in blueprint `harmony.scales` list

### D-09: Mix phase includes per-role apply_mix_recipe steps

Mix phase generates one `apply_mix_recipe` step per standard role in the genre:
- Roles pulled from `get_blueprint(genre_id)["instrumentation"]["roles"][:5]`
- Each step: `{"track_index": "<{role}_track_index>", "role": role, "genre": genre_id}`
- Final two steps always: `check_gain_staging` → `suggest_mix_adjustments`

### D-10: arrangement phase steps

1. `get_arrangement_overview` — see current state
2. `get_arrangement_progress` — identify empty tracks
3. `evaluate_session(genre)` — score before finishing arrangement
4. `get_section_checklist` — detailed per-section check
5. Loop advice step (description only, no tool — step with tool_name "—", description "Review evaluate_session output and apply top_fixes")

### D-11: Tests use inline expected data (no live Ableton)

All tests: pure function calls on `get_execution_plan()` — no MCP, no connection.
Checklist is validated by structure (has steps, tool_names are strings, suggested_args are dicts).

## Implementation Order

1. `MCP_Server/orchestration/execution.py` — `_GENRE_PARAMS`, `_DEFAULT_STEPS`, `_DRUM_PATTERNS`, `get_execution_plan`
2. Update `MCP_Server/tools/orchestration.py` — add `get_phase_execution_plan` MCP tool
3. Write `tests/test_phase_execution.py` — 8 tests
4. Run tests, fix failures
5. Commit

## Test Coverage

| Test | What it verifies |
|------|-----------------|
| `test_drums_house_has_kick_notes` | drums/house checklist contains add_notes_to_clip step with pitch 36 in notes |
| `test_drums_ambient_returns_error` | get_execution_plan("drums","ambient") returns {"error": ...} (no drums in ambient) |
| `test_mix_phase_has_apply_recipe_step` | mix/house checklist contains apply_mix_recipe step |
| `test_master_phase_has_apply_master_recipe` | master/techno checklist contains apply_master_recipe step |
| `test_section_name_uses_arrangement_clip` | section_name="Drop" changes note-writing steps to create_arrangement_midi_clip |
| `test_setup_phase_has_set_tempo` | setup/house checklist step 1 is set_tempo with tempo ~125 |
| `test_json_output_under_2000_chars` | serialized PhaseChecklist < 2000 chars for all phase types × house |
| `test_step_numbers_sequential` | step_number values are 1,2,3,... without gaps |

## Out of Scope for Phase 49

- Checkpoint reading from Ableton (Phase 50)
- Next-action recommender (Phase 51)
- Adaptive step generation from session state
- Parallel step execution
