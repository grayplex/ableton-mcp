# Phase 40 Context: Arrangement, Sound Selection, and Harmonic Evaluators

**Phase:** 40
**Milestone:** v1.6 Self-evaluation
**Mode:** --auto (Claude-selected defaults)
**Created:** 2026-03-31

## Phase Goal

All three remaining evaluators are implemented and unit-tested. Each returns a populated `DimensionScore` from live session data. Phase 41 will wire all four evaluators into `evaluate_session()`.

## Requirements In Scope

- ARNG-01: Arrangement completeness evaluator
- SND-01: Sound selection coverage evaluator
- HARM-01: Harmonic coherence evaluator

## Schema Available (from Phase 39)

```python
from MCP_Server.evaluation.schema import EvaluationIssue, DimensionScore, grade_from_score
```

All evaluators use these TypedDicts and the `grade_from_score()` helper. No schema changes needed.

## Data Sources for Each Evaluator

### Arrangement Completeness (ARNG-01)

| Data Needed | RS Command | Response Structure |
|-------------|-----------|-------------------|
| Tracks + has_devices | `get_arrangement_state` | `{tracks: [{name, has_devices}], cue_points, song_length}` |
| Clips per track | `get_arrangement_clips` | `{track_name, clips: [{name, start_time, end_time, length}]}` per track_index |

`get_arrangement_clips` requires `track_index` → need N calls (one per track). This is acceptable for evaluation — read-only, bounded by track count.

**Track status logic:**
- No devices → `"critical"` — track is empty scaffold, produces silence
- Has devices + no arrangement clips → `"warning"` — instrument loaded but nothing recorded/placed
- Has devices + has arrangement clips → pass (no issue)

### Sound Selection Coverage (SND-01)

| Data Needed | RS Command | Response Structure |
|-------------|-----------|-------------------|
| Device names per track | `get_mix_state` | `{tracks: [{name, devices: [{class_name, device_name}]}]}` |

Role → expected instrument mapping via `sounds/catalog.py`:
- `_infer_role(track_name)` → role tag (e.g. "kick", "pad", "bass")
- Load all profiles from `catalog.list_profiles()` + `catalog.get_profile(id)`
- Find instrument with highest `descriptor_affinities["role"][inferred_role]` weight
- Check if any `device_name` on the track contains the expected instrument name (case-insensitive)
- Mismatch → `"warning"`; no role match → skip track

**Example:** "KICK_01" → role "kick" → Drum Rack has role["kick"]=0.9 (highest) → check if Drum Rack loaded

### Harmonic Coherence (HARM-01)

| Data Needed | RS Command | Response Structure |
|-------------|-----------|-------------------|
| Session key/scale | `get_scale_info` | `{root_note: int 0-11, scale_name: str, scale_intervals: [int], scale_mode: int}` |
| Track list + clips | `get_session_state` | `{tracks: [{name, index, type, devices, clips?: [{scene_index, name}]}]}` |
| Notes per clip | `get_notes` | `{notes: [{pitch, start_time, duration, velocity}]}` per track_index + clip_index |

## Locked Decisions

### D-01: Arrangement evaluator uses arrangement clips, not Session clips
Use `get_arrangement_state` + `get_arrangement_clips(track_index)` per track. The scaffold creates tracks for Arrangement view; arrangement clips are the correct thing to check. Session view clips (clip_slots) are irrelevant to the scaffold workflow.

### D-02: Arrangement evaluator skips return tracks and master
Only regular tracks (`song.tracks`) are scaffold candidates. Return tracks and master are not iterated. Matches `get_arrangement_state` which also only returns `song.tracks`.

### D-03: Arrangement scoring formula
```
score = (clean_tracks / total_tracks) * 10
```
- `clean_tracks` = tracks with devices + at least one arrangement clip
- `total_tracks` = total regular tracks (all of them — even no-device tracks count against score)
- Each critical issue (no devices) counts as 0; each warning (no clips but has devices) counts as 0.5 toward clean

Simplified: `score = ((has_device_and_clips + 0.5 * has_devices_no_clips) / total_tracks) * 10`

### D-04: Sound selection uses device_name (display name), not class_name
`get_mix_state` returns both `class_name` (e.g. "InstrumentVector") and `device_name` (e.g. "Wavetable"). The instrument profile names ("Wavetable", "Analog", "Operator", "Drift", "Simpler", "Drum Rack") match `device_name`, not `class_name`. Use case-insensitive `in` check: `expected_name.lower() in device["device_name"].lower()`.

### D-05: Sound selection top-instrument lookup
Pre-build a role→instrument mapping at evaluator startup:
```python
# For each role, find which instrument profile has highest role affinity
_role_to_instrument: dict[str, str] = {}  # role -> instrument display name
```
This is computed once from `catalog.list_profiles()` + `catalog.get_profile()` calls. No connection needed. If a role has no affinity mapping in any profile, skip that track.

### D-06: Harmonic evaluator fallback for no key set
If `scale_name` is empty string or `scale_intervals` is empty list → return DimensionScore with:
- `score = 10.0` (can't evaluate without a key — assume pass)
- `grade = "A"`
- `issues = [EvaluationIssue(dimension="harmony", severity="info", message="No session key set — harmonic coherence check skipped", fix_hint="set_scale(root_note=0, scale_name='major') to enable harmonic evaluation")]`

### D-07: Harmonic pitch class computation
```python
pitch_classes: set[int] = set()
cumulative = 0
pitch_classes.add(root_note % 12)
for interval in scale_intervals:
    cumulative += interval
    pitch_classes.add((root_note + cumulative) % 12)
```
No music21 or theory library needed — pure integer arithmetic on the intervals from the RS response.

### D-08: Harmonic evaluator iterates Session view clips
Use `get_session_state` (not `get_arrangement_clips`). The Session state gives all clips with `scene_index` and `name`. Then call `get_notes(track_index, scene_index)` for each clip. This covers MIDI notes in Session view clips, which is where most MIDI editing happens.

Only check tracks with `type == "midi"` (or any track with a MIDI instrument device, inferred by presence of clips). Skip audio tracks.

### D-09: Harmonic scoring formula
```
score = (in_key_notes / total_notes) * 10
```
- `total_notes` = all MIDI notes across all clips
- `in_key_notes` = notes where `pitch % 12` is in pitch_classes
- If `total_notes == 0` → score = 10.0 (no notes to check — assume pass)

### D-10: All three evaluators in separate files
```
MCP_Server/evaluation/arrangement.py   → evaluate_arrangement(conn) -> DimensionScore
MCP_Server/evaluation/sounds_coverage.py → evaluate_sounds_coverage(conn) -> DimensionScore
MCP_Server/evaluation/harmonic.py       → evaluate_harmonic(conn) -> DimensionScore
```
Same signature as `evaluate_mix_balance(genre, conn)` except:
- `evaluate_arrangement(conn)` — no genre needed
- `evaluate_sounds_coverage(conn)` — no genre needed
- `evaluate_harmonic(conn)` — no genre needed

### D-11: No MCP tools in Phase 40
Same as Phase 39 — pure evaluation logic, no MCP wiring. Phase 41 does all wiring.

## Files to Create

```
MCP_Server/evaluation/arrangement.py
MCP_Server/evaluation/sounds_coverage.py
MCP_Server/evaluation/harmonic.py
tests/test_evaluation_phase40.py
```

## Test Strategy

Single test file `tests/test_evaluation_phase40.py` with three classes:

**TestArrangementEvaluator:**
- All tracks have devices + clips → score 10.0
- All tracks empty (no devices) → score 0.0, all critical issues
- Mixed: half with devices, half without → score between 0 and 10
- `result["dimension"] == "arrangement"`

**TestSoundsCoverageEvaluator:**
- Kick track with Drum Rack loaded → no issue (correct match)
- Pad track with Drum Rack loaded → warning (Wavetable expected for pad)
- Track with unknown role → skipped (no issue)
- `result["dimension"] == "sounds"`

**TestHarmonicEvaluator:**
- No scale set (empty scale_name) → score 10.0, info issue
- C major scale, all notes in C major → score 10.0
- C major scale, one out-of-key note → score < 10.0, warning issue with pitch info
- No clips → score 10.0
- `result["dimension"] == "harmony"`

## Dependencies

- `MCP_Server.evaluation.schema` (EvaluationIssue, DimensionScore, grade_from_score)
- `MCP_Server.devices.catalog` (ROLES — for _infer_role)
- `MCP_Server.sounds.catalog` (list_profiles, get_profile — for sounds coverage)
- `conn.send_command(...)` — injected, no direct import of connection module
