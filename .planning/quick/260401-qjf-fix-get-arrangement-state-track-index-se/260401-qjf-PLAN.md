---
phase: quick-260401-qjf
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - MCP_Server/tools/scaffold.py
  - MCP_Server/orchestration/execution.py
  - tests/test_execution.py
  - tests/test_phase_execution.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "get_arrangement_overview includes track index alongside track name so Claude can resolve sentinels without a separate get_all_tracks call"
    - "Execution step descriptions for sentinel-bearing steps explicitly instruct Claude to resolve track indices at call time"
  artifacts:
    - path: "MCP_Server/tools/scaffold.py"
      provides: "get_arrangement_overview returning {name, index} dicts instead of bare name strings"
    - path: "MCP_Server/orchestration/execution.py"
      provides: "Sentinel resolution hints in step descriptions"
  key_links:
    - from: "MCP_Server/tools/scaffold.py"
      to: "AbletonMCP_Remote_Script/handlers/scaffold.py"
      via: "get_arrangement_state command returns index field per track"
      pattern: 'track\["index"\]'
---

<objective>
Make sentinel resolution for `<track_index>` more robust by: (1) including track index in `get_arrangement_overview` output so the executor can resolve sentinels from arrangement overview without a separate `get_all_tracks()` call, and (2) adding explicit sentinel resolution instructions in execution step descriptions for steps that use `<track_index>` sentinels.

Purpose: Currently `get_arrangement_overview` strips track indices (returns only names), forcing an extra `get_all_tracks()` round-trip to resolve `<track_index>` sentinels. The scaffold handler already returns index per track — we just need to surface it. Additionally, step descriptions should be explicit about when and how to resolve sentinels.

Output: Updated `get_arrangement_overview` returning track objects with index, updated execution step descriptions with sentinel hints.
</objective>

<execution_context>
@.planning/STATE.md
</execution_context>

<context>
@MCP_Server/tools/scaffold.py
@MCP_Server/orchestration/execution.py
@AbletonMCP_Remote_Script/handlers/scaffold.py
@tests/test_execution.py
@tests/test_phase_execution.py

<interfaces>
<!-- get_arrangement_state (Remote Script) already returns index per track: -->
From AbletonMCP_Remote_Script/handlers/scaffold.py line 67-73:
```python
for i, track in enumerate(self._song.tracks):
    tracks.append({
        "index": i,
        "name": track.name,
        "has_instrument": getattr(track, "has_audio_output", False),
        "has_clips": len(track.arrangement_clips) > 0,
    })
```

<!-- get_arrangement_overview currently strips index (line 186): -->
From MCP_Server/tools/scaffold.py line 184-188:
```python
return json.dumps({
    "locators": locators,
    "tracks": [t["name"] for t in state["tracks"]],
    "session_length_bars": session_length_bars,
})
```

<!-- Execution steps use "<track_index>" sentinel in suggested_args: -->
From MCP_Server/orchestration/execution.py line 238-239:
```python
# Sentinel hints removed — the "<track_index>" / "<clip_index>" values in
# suggested_args already signal that Claude must resolve them at call time.
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Include track index in get_arrangement_overview output and add sentinel resolution hints to execution steps</name>
  <files>MCP_Server/tools/scaffold.py, MCP_Server/orchestration/execution.py, tests/test_execution.py, tests/test_phase_execution.py</files>
  <behavior>
    - Test: get_arrangement_overview returns tracks as list of {"name": str, "index": int} dicts (not bare strings)
    - Test: Existing test assertions for track name access still pass (backward compat — consumers using `t["name"]` still work)
    - Test: Execution steps with `<track_index>` sentinel have descriptions containing "resolve" or "get_arrangement_overview" or "get_all_tracks" hint text
  </behavior>
  <action>
**IMPORTANT: Before making any changes, rebase this worktree off of `misc-fixes`:**
```bash
git fetch origin misc-fixes && git rebase origin/misc-fixes
```

**Part A — get_arrangement_overview track index inclusion:**

In `MCP_Server/tools/scaffold.py`, function `get_arrangement_overview` (line ~184-188), change:
```python
"tracks": [t["name"] for t in state["tracks"]],
```
to:
```python
"tracks": [{"name": t["name"], "index": t["index"]} for t in state["tracks"]],
```

This surfaces the index already returned by the Remote Script's `get_arrangement_state` handler. The `get_arrangement_overview` docstring should be updated to mention that tracks now include index.

**Part B — Sentinel resolution hints in execution step descriptions:**

In `MCP_Server/orchestration/execution.py`, update the comment at line ~238-239 to be a proper docstring/constant. Then for each phase builder that uses `<track_index>` sentinel (`_build_drums_steps`, `_build_bass_steps`, `_build_harmony_steps`, `_build_melody_steps`), update the **first step that uses `<track_index>`** (the `set_track_name` step, step 2 in each) to append a resolution hint to its description. Specifically, change descriptions like:
```python
"Name track 'Drums'"
```
to:
```python
"Name track 'Drums' — resolve <track_index> via get_arrangement_overview or get_all_tracks"
```

Do the same for `_build_sound_design_steps` and `_build_mix_steps` which already have inline hints — standardize them to use the same phrasing: `"resolve <...> via get_arrangement_overview or get_all_tracks"`.

**Part C — Update tests:**

In `tests/test_execution.py`:
- Update `_mock_execution_factory` tracks to always include `"index"` field (already present — verify).
- Add a test `test_arrangement_overview_includes_track_index` that mocks `get_arrangement_state` and asserts the response includes `{"name": ..., "index": ...}` dicts.

In `tests/test_phase_execution.py`:
- Add a test `test_sentinel_steps_have_resolution_hint` that for each phase with `<track_index>` sentinels, verifies the first sentinel-bearing step's description contains a resolution hint (e.g., "resolve" or "get_arrangement_overview").
  </action>
  <verify>
    <automated>cd I:/ableton-mcp && python -m pytest tests/test_execution.py tests/test_phase_execution.py -x -q 2>&1 | tail -20</automated>
  </verify>
  <done>
    - get_arrangement_overview returns track objects with both name and index fields
    - Execution steps with track_index sentinels contain explicit resolution instructions in their descriptions
    - All existing tests pass, new tests for both behaviors pass
  </done>
</task>

</tasks>

<verification>
```bash
cd I:/ableton-mcp && python -m pytest tests/test_execution.py tests/test_phase_execution.py -x -q
```
All tests pass including new sentinel resolution hint test and track index test.
</verification>

<success_criteria>
- get_arrangement_overview output includes track index per track (no more stripping to bare names)
- Sentinel-bearing execution steps have explicit resolution hints in descriptions
- No regressions in existing test suites
</success_criteria>

<output>
After completion, create `.planning/quick/260401-qjf-fix-get-arrangement-state-track-index-se/260401-qjf-SUMMARY.md`
</output>
