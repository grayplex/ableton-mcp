# Phase 50 Context: Production Checkpoint System

**Phase:** 50 — Production Checkpoint System
**Milestone:** v1.9 Orchestration/Agent Loop
**Requirements:** CHKP-01, CHKP-02
**Date:** 2026-03-31
**Mode:** --auto

## Goal

`get_production_checkpoint(genre?)` — reads live Ableton session state and returns
a compact `ProductionCheckpoint` identifying which production phases are complete,
which is active, and a single-sentence `resume_hint`. Enables context-reset recovery:
Claude calls this one tool and knows exactly where to continue.

## Codebase Scouting

### TypedDicts already defined (Phase 48)

`ProductionCheckpoint` and `SessionStats` are already in `MCP_Server/orchestration/schema.py`.
Phase 50 only adds `checkpoint.py` + expands `tools/orchestration.py`.

### RS commands / MCP tools called by checkpoint

| Call | What it returns | Used for |
|------|----------------|---------|
| `get_arrangement_state` RS | `{tracks:[{name,has_devices}], cue_points:[{name,time}], song_length}` | track topology, locators |
| `get_arrangement_clips` RS | `{track_name, clips:[{start_time,end_time,is_audio_clip}]}` | clip presence per track |
| `get_mix_state` RS | `{tracks:[{name,type,devices:[{class_name}]}], master_track:{devices}}` | device presence |

All three are sent directly via `conn.send_command(...)` — not MCP tool wrappers.

### Phase completion heuristics

| Phase | Heuristic | Evidence in session |
|-------|-----------|-------------------|
| setup | ≥2 MIDI tracks AND ≥1 locator (cue point) | `len(tracks) >= 2 and len(cue_points) >= 1` |
| drums | Any track with "drum" or "kick" (case-insensitive) in name AND has_devices=True AND has arrangement clips | track name match + device + clips |
| bass | Any track with "bass" in name AND has_devices AND clips | track name match + device + clips |
| harmony | Any track with "chord", "pad", "harm", "keys", "piano", "strings" in name AND clips | track name + clips |
| melody | Any track with "lead", "melody", "mel" in name AND clips | track name + clips |
| sound_design | Any track has Auto Filter OR Wavetable device loaded (distinct from instrument devices) | device class_name check |
| arrangement | `get_arrangement_progress` returns `empty_tracks == []` AND `total_tracks >= 3` | all tracks have instruments |
| mix | Master track has NO GlueCompressor AND at least 1 non-master track has Compressor2 device | device presence check |
| master | Master track has GlueCompressor AND Limiter device | device class_name check |

### Active phase detection

Walk phases in AGENDA_CATALOG[genre] order. First phase whose heuristic returns False
is the active_phase. Progress estimate: 0.3 if phase was started (tracks/devices exist
for it), 0.0 if not started. "Arrangements" phase is special: progress = 1 - (empty_tracks / total_tracks).

### Session stats from RS data

```python
SessionStats(
    track_count=len(tracks),
    tracks_with_instruments=sum(1 for t in tracks if t["has_devices"]),
    tracks_with_clips=sum(1 for t in tracks if has_clips(t)),   # requires get_arrangement_clips per track
    has_mix_applied=any(d["class_name"]=="Compressor2" for d in all_track_devices),
    has_master_applied=any(d["class_name"] in {"GlueCompressor","Limiter2"} for d in master_devices),
)
```

`has_clips` is determined by calling `get_arrangement_clips` for each track and checking
if any clips exist. This requires N RS round-trips (one per track). Use track count from
`get_arrangement_state` — if track count > 8, only check first 8 tracks to avoid timeout.

### Resume hint construction

Template: "Continue with {active_phase_name}: {next_action_description}"
- setup: "Continue with setup: call set_tempo, then scaffold_arrangement with the production plan"
- drums: "Continue with drum programming: create a Drums track, load a Drum Rack, and add a kick pattern"
- bass: "Continue with bass: create a Bass track, load Analog, and write a bass line"
- harmony: "Continue with harmony: create a Chords track, load Wavetable, and add a chord progression"
- melody: "Continue with melody: create a Lead track, load Operator, and write the main melody"
- sound_design: "Continue with sound design: add effects chains (Auto Filter, Reverb) to synth tracks"
- arrangement: "Continue with arrangement: copy and vary clips across sections for dynamic flow"
- mix: "Continue with mixing: call apply_mix_recipe for each track role, then check_gain_staging"
- master: "Continue with mastering: call apply_master_recipe to apply the master bus chain"
- all_complete: "Production is complete — call evaluate_session for a final quality check"

## Locked Decisions

### D-01: New module `MCP_Server/orchestration/checkpoint.py`

Contains `_infer_completed_phases(genre, arrangement_state, mix_state, clips_by_track)`,
`_build_session_stats(...)`, and `get_checkpoint(genre)` public function. The function
calls RS commands directly via connection (not MCP tool wrappers) to minimize round-trips.

### D-02: RS calls sequence in get_checkpoint

```
conn = get_ableton_connection()
arrangement_state = conn.send_command("get_arrangement_state")
mix_state = conn.send_command("get_mix_state")
# Only fetch clips for first min(track_count, 8) tracks to bound latency
clips_by_track = {}
for track in arrangement_state["tracks"][:8]:
    result = conn.send_command("get_arrangement_clips", {"track_index": track["index"]})
    clips_by_track[track["name"]] = result.get("clips", [])
```

### D-03: Empty session handling

If `arrangement_state["tracks"]` is empty:
```python
return ProductionCheckpoint(
    genre=genre,
    completed_phases=[],
    active_phase="setup",
    active_phase_progress=0.0,
    pending_steps=["set_tempo", "set_scale", "scaffold_arrangement"],
    session_stats=SessionStats(track_count=0, tracks_with_instruments=0,
                               tracks_with_clips=0, has_mix_applied=False, has_master_applied=False),
    next_phase="drums",
    resume_hint="Session is empty — start with setup: set tempo, set key, and scaffold tracks",
)
```

### D-04: genre parameter is optional

When `genre=None`, checkpoint skips phase completion inference (no AGENDA_CATALOG lookup)
and returns:
- `completed_phases=[]` (cannot infer without genre order)
- `active_phase=None`
- `resume_hint="Provide a genre to get phase-specific guidance. Session has {N} tracks."`
- `session_stats` still populated from RS data

### D-05: Device class_name values in mix_state

From `get_mix_state` RS, device `class_name` values:
- Compressor: `"Compressor2"`
- EQ Eight: `"Eq8"`
- Glue Compressor: `"GlueCompressor"`
- Limiter: `"Limiter2"`
- Auto Filter: `"AutoFilter"`
- Wavetable: `"InstrumentVector"`
- Analog: `"InstrumentAnalog"`
- Drum Rack: `"DrumGroupDevice"`

### D-06: `get_production_checkpoint` MCP tool signature

```python
@mcp.tool()
def get_production_checkpoint(ctx: Context, genre: str = None) -> str:
    """Get a compact snapshot of production progress from live Ableton state.
    ...
    """
```

Returns `json.dumps(ProductionCheckpoint)` on success or `json.dumps({"error": "..."})` on connection failure.

### D-07: Tests are mock-based (no live Ableton)

Mock `get_ableton_connection` to return a connection whose `send_command` returns
prepared fixture data. Tests verify the heuristic logic, not the RS protocol.

Test fixture: a "mid-production" session with 4 tracks (Kick/Drums, Bass, Chords, Lead),
first 3 have devices + clips, Lead has no clips → arrangement/melody not complete.

## Implementation Order

1. `MCP_Server/orchestration/checkpoint.py`
2. Update `MCP_Server/tools/orchestration.py` — add `get_production_checkpoint`
3. Update `MCP_Server/orchestration/__init__.py` — expose `get_checkpoint`
4. Write `tests/test_checkpoint.py` — 7 tests
5. Run tests, fix failures
6. Commit

## Test Coverage

| Test | What it verifies |
|------|-----------------|
| `test_empty_session` | `completed_phases=[]`, `active_phase="setup"`, resume_hint mentions "empty" |
| `test_setup_complete_drums_active` | 3 tracks, locators present → setup complete; no drum clips → drums active |
| `test_drums_complete` | Drum Rack track with clips → "drums" in completed_phases |
| `test_no_genre_returns_none_active_phase` | genre=None → active_phase=None, session_stats populated |
| `test_master_complete` | master track has GlueCompressor + Limiter2 → "master" in completed_phases |
| `test_resume_hint_is_single_sentence` | resume_hint has no newlines and ends with sentence terminator |
| `test_session_stats_populated` | track_count, tracks_with_instruments correct from fixture |

## Out of Scope for Phase 50

- Next-action recommender (Phase 51)
- Persistent checkpoint storage across sessions
- Non-arrangement (session view) clip detection
