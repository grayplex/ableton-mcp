---
phase: quick
plan: 260401-pye
type: execute
wave: 1
depends_on: []
files_modified:
  - AbletonMCP_Remote_Script/handlers/scaffold.py
  - MCP_Server/orchestration/checkpoint.py
  - MCP_Server/orchestration/next_actions.py
  - tests/test_checkpoint.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Checkpoint reads live Ableton state in exactly 2 socket round-trips (get_arrangement_state + get_mix_state), not N+2"
    - "Phase detection still works correctly for all phases (drums, bass, harmony, melody, arrangement, etc.)"
    - "All existing checkpoint tests pass with the new approach"
  artifacts:
    - path: "AbletonMCP_Remote_Script/handlers/scaffold.py"
      provides: "get_arrangement_state with has_clips boolean per track"
      contains: "has_clips"
    - path: "MCP_Server/orchestration/checkpoint.py"
      provides: "Checkpoint without per-track clip queries"
    - path: "MCP_Server/orchestration/next_actions.py"
      provides: "Transition guidance without per-track clip queries"
  key_links:
    - from: "AbletonMCP_Remote_Script/handlers/scaffold.py"
      to: "MCP_Server/orchestration/checkpoint.py"
      via: "has_clips field in get_arrangement_state response tracks"
      pattern: "has_clips"
---

<objective>
Eliminate N sequential `get_arrangement_clips` socket round-trips from checkpoint and
next_actions by adding a `has_clips` boolean to each track in the `get_arrangement_state`
Remote Script response. Both callers only use clip data to check whether a track has
any clips (boolean), never the clip details themselves. This reduces worst-case from
N+2 round-trips to exactly 2.

Purpose: Checkpoint currently takes 2 + N round-trips (where N = number of tracks).
At 10s timeout each, a session with 8 tracks risks up to 100s worst-case latency.
With this fix, checkpoint always takes exactly 2 round-trips regardless of track count.

Output: Modified Remote Script handler, updated checkpoint.py and next_actions.py,
passing tests.
</objective>

<execution_context>
@.planning/quick/260401-pye-checkpoint-makes-n-2-sequential-socket-r/260401-pye-PLAN.md
</execution_context>

<context>
@AbletonMCP_Remote_Script/handlers/scaffold.py (get_arrangement_state handler)
@AbletonMCP_Remote_Script/handlers/arrangement.py (get_arrangement_clips handler — for reference)
@MCP_Server/orchestration/checkpoint.py (get_checkpoint caller)
@MCP_Server/orchestration/next_actions.py (get_transition_guidance caller)
@tests/test_checkpoint.py (existing tests)
@MCP_Server/connection.py (send_command / timeout context)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add has_clips to get_arrangement_state and remove per-track clip queries</name>
  <files>
    AbletonMCP_Remote_Script/handlers/scaffold.py
    MCP_Server/orchestration/checkpoint.py
    MCP_Server/orchestration/next_actions.py
    tests/test_checkpoint.py
  </files>
  <action>
IMPORTANT: First rebase the worktree off misc-fixes: `git fetch origin && git rebase misc-fixes`

**1. Remote Script — scaffold.py `_get_arrangement_state`:**

In the track iteration loop (around line 67-72), add `has_clips` to each track dict:

```python
for i, track in enumerate(self._song.tracks):
    tracks.append({
        "index": i,
        "name": track.name,
        "has_instrument": getattr(track, "has_audio_output", False),
        "has_clips": len(track.arrangement_clips) > 0,
    })
```

Also update the docstring to document the new field.

**2. checkpoint.py — `get_checkpoint`:**

Remove the entire `clips_by_track` loop (lines 148-155) that calls `get_arrangement_clips` per track. Instead, build `clips_by_track` from the `has_clips` field already in `tracks`:

```python
# Build clips_by_track from arrangement_state (no extra round-trips)
clips_by_track = {}
for track in tracks:
    # has_clips from get_arrangement_state; use sentinel list for truthy check
    clips_by_track[track["name"]] = ["_"] if track.get("has_clips") else []
```

This preserves the existing `_track_has_clips()` function contract (checks `len(clips) > 0`) without changing any downstream logic.

**3. next_actions.py — `get_transition_guidance`:**

Apply the exact same replacement in `get_transition_guidance` (around lines 242-249):
Remove the per-track `get_arrangement_clips` loop and replace with the same `clips_by_track` construction from `has_clips`.

**4. tests/test_checkpoint.py — update fixtures:**

Update `_make_track` helper to accept and include `has_clips` parameter (default False):

```python
def _make_track(name, has_instrument=True, index=0, devices=None, has_clips=False):
    return {"name": name, "has_instrument": has_instrument, "index": index,
            "devices": devices or [], "has_clips": has_clips}
```

Update `_make_conn` to no longer need the `get_arrangement_clips` branch in `send_command` — the mock no longer needs to handle that command for checkpoint tests. BUT keep backward compatibility: if `clips_by_track` is passed, set `has_clips` on tracks automatically.

Update test fixtures that pass `clips_by_track` to instead pass `has_clips=True` on relevant tracks:
- `test_drums_complete`: change `_make_track("Kick Drums", True, 0)` to `_make_track("Kick Drums", True, 0, has_clips=True)`
- `test_master_complete`: change both tracks to `has_clips=True`

Update `_make_conn` to propagate `clips_by_track` into track `has_clips` for backward compat:
```python
def _make_conn(arrangement_state, mix_state, clips_by_track=None):
    clips_by_track = clips_by_track or {}
    # Inject has_clips into tracks based on clips_by_track
    for t in arrangement_state.get("tracks", []):
        if t["name"] in clips_by_track and clips_by_track[t["name"]]:
            t["has_clips"] = True
        elif "has_clips" not in t:
            t["has_clips"] = False
    mock_conn = MagicMock()
    def send_command(cmd, params=None):
        if cmd == "get_arrangement_state":
            return arrangement_state
        elif cmd == "get_mix_state":
            return mix_state
        return {}
    mock_conn.send_command.side_effect = send_command
    return mock_conn
```

Also add a new test `test_no_per_track_clip_queries` that asserts `send_command` is called exactly 2 times (get_arrangement_state + get_mix_state), never with get_arrangement_clips:

```python
def test_no_per_track_clip_queries(self):
    """Checkpoint must not issue per-track get_arrangement_clips calls."""
    arr = {
        "tracks": [
            _make_track("Drums", True, 0, has_clips=True),
            _make_track("Bass", True, 1, has_clips=True),
            _make_track("Chords", True, 2, has_clips=False),
        ],
        "cue_points": [], "song_length": 32.0,
    }
    mix = {"tracks": [], "return_tracks": [], "master_track": {"devices": []}}
    mock = _make_conn(arr, mix)
    with patch("MCP_Server.orchestration.checkpoint.get_ableton_connection",
               return_value=mock):
        get_checkpoint("house")
    commands = [call.args[0] for call in mock.send_command.call_args_list]
    assert "get_arrangement_clips" not in commands
    assert commands == ["get_arrangement_state", "get_mix_state"]
```
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/test_checkpoint.py -x -v</automated>
  </verify>
  <done>
    - get_arrangement_state returns has_clips boolean per track
    - checkpoint.py makes exactly 2 send_command calls (get_arrangement_state + get_mix_state)
    - next_actions.py get_transition_guidance makes exactly 2 send_command calls
    - All existing checkpoint tests pass
    - New test verifies no per-track clip queries
  </done>
</task>

</tasks>

<verification>
- `python -m pytest tests/test_checkpoint.py -x -v` — all tests pass including new round-trip count test
- `python -m pytest tests/ -x --timeout=60` — full test suite still passes (no regressions)
- Grep for `get_arrangement_clips` in checkpoint.py and next_actions.py — should find zero occurrences
</verification>

<success_criteria>
- Checkpoint makes exactly 2 socket round-trips regardless of track count
- All checkpoint and next_actions tests pass
- Phase detection logic unchanged (same boolean semantics)
</success_criteria>

<output>
After completion, create `.planning/quick/260401-pye-checkpoint-makes-n-2-sequential-socket-r/260401-pye-SUMMARY.md`
</output>
