---
phase: 45-section-state-reader
plan: 01
subsystem: refinement
tags: [section-state, arrangement, notes, mix-context, typed-dict, rs-command]
dependency_graph:
  requires:
    - MCP_Server/tools/scaffold.py (_beat_to_bar, _bar_to_beat)
    - MCP_Server/tools/analysis.py (_infer_role)
    - MCP_Server/tools/intelligence.py (_find_track)
    - MCP_Server/mixing/catalog.py (get_recipe)
    - MCP_Server/devices/catalog.py (CATALOG)
    - MCP_Server/devices/convert.py (natural_to_normalized)
    - AbletonMCP_Remote_Script/handlers/arrangement.py (get_arrangement_clips, get_arrangement_state)
  provides:
    - MCP_Server/refinement/ package with TypedDict schema
    - get_section_state MCP tool
    - get_arrangement_clip_notes RS command
  affects:
    - Phase 46 (Iterative Refinement) will consume get_section_state output
tech_stack:
  added:
    - MCP_Server/refinement/ package
  patterns:
    - TypedDict schema in separate schema.py (same as MCP_Server/prompt/schema.py pattern)
    - RS command using track.arrangement_clips (arrangement-view specific)
    - beat-to-bar conversion via _beat_to_bar for locator range math
key_files:
  created:
    - MCP_Server/refinement/__init__.py
    - MCP_Server/refinement/schema.py
    - MCP_Server/tools/refinement.py
    - tests/test_section_state.py
  modified:
    - AbletonMCP_Remote_Script/handlers/arrangement.py (added get_arrangement_clip_notes)
    - MCP_Server/tools/__init__.py (added refinement import)
    - pyproject.toml (added MCP_Server.refinement to packages)
decisions:
  - "New RS command get_arrangement_clip_notes required because get_notes uses session-view clip_slots not arrangement_clips"
  - "Recipe delta threshold set to 0.20 (20%) for section state vs 0.03 (3%) in suggest_mix_adjustments — coarser for read-only snapshot"
  - "Tracks with zero clips in section range omitted entirely from SectionState.tracks (D-09)"
  - "Clip filtering uses beat-space: section_start_beat <= clip.start_time < section_end_beat"
metrics:
  duration_minutes: 5
  completed_date: "2026-03-31"
  tasks_completed: 9
  files_changed: 7
requirements:
  - SNAP-01
  - SNAP-02
---

# Phase 45 Plan 01: Section State Reader Summary

One-liner: Section State Reader with `get_section_state(section_name, genre=None)` MCP tool and `get_arrangement_clip_notes` RS command returning per-track clip+note snapshots with optional recipe delta.

## What Was Built

### RS Command: `get_arrangement_clip_notes`
Added to `AbletonMCP_Remote_Script/handlers/arrangement.py` after `_get_arrangement_clips`. Finds an arrangement clip by `start_time` (±0.01 beat tolerance), calls `get_notes_extended(0, 128, 0.0, clip.length)`, and returns note list with `{pitch, start_time, duration, velocity, mute}`. Returns `{"note_count": 0, "notes": []}` for not-found or audio clips. Does not use `write=True`.

### Package: `MCP_Server/refinement/`
- `__init__.py`: docstring with Public API listing
- `schema.py`: Three TypedDicts — `ClipSummary`, `TrackStateEntry`, `SectionState` — all JSON-serializable without `.asdict()`

### MCP Tool: `get_section_state`
Full implementation in `MCP_Server/tools/refinement.py`:
1. Calls `get_arrangement_state` RS for locators, time signature, tracks
2. Computes `beats_per_bar = numerator * (4.0 / denominator)`
3. Finds locator by case-insensitive name match
4. If missing: returns `SectionState` with `error="Section '...' not found"`, `tracks=[]`
5. For each track: calls `get_arrangement_clips`, filters clips by beat range
6. For MIDI clips: calls `get_arrangement_clip_notes`, computes note summary (pitch_min/max, dominant_octave, rhythm_density)
7. Builds `mix_context` from `get_mix_state` RS: volume, pan, device summaries with prominent params, optional `recipe_delta` when `genre` is provided and role inferred
8. Tracks with zero clips omitted (D-09)

### Tests: `tests/test_section_state.py`
11 mock-based tests (2 RS handler + 7 MCP tool + 2 schema), all passing.

## Test Results

```
tests/test_section_state.py::TestRSHandler::test_rs_get_arrangement_clip_notes_found PASSED
tests/test_section_state.py::TestRSHandler::test_rs_get_arrangement_clip_notes_not_found PASSED
tests/test_section_state.py::TestGetSectionState::test_section_not_found PASSED
tests/test_section_state.py::TestGetSectionState::test_section_clips_collected PASSED
tests/test_section_state.py::TestGetSectionState::test_note_summary_correct PASSED
tests/test_section_state.py::TestGetSectionState::test_audio_clip_note_fields_none PASSED
tests/test_section_state.py::TestGetSectionState::test_mix_context_no_genre PASSED
tests/test_section_state.py::TestGetSectionState::test_mix_context_with_recipe_delta PASSED
tests/test_section_state.py::TestGetSectionState::test_empty_section_no_clips PASSED
tests/test_section_state.py::TestSchema::test_clip_summary_json_serializable PASSED
tests/test_section_state.py::TestSchema::test_section_state_json_serializable PASSED

11 passed in 0.21s
```

## Commits

- `e3eff34`: feat(45): Section State Reader — get_section_state MCP tool + get_arrangement_clip_notes RS command

## Deviations from Plan

None — plan executed exactly as written. All files were already implemented and committed. Tests confirmed 11/11 pass (plan specified 8 required; 3 additional schema tests were included).

## Known Stubs

None. All data paths are wired: RS commands return real data, note summaries computed from actual note lists, mix context from real get_mix_state response. Recipe delta returns `[]` gracefully when recipe lookup fails — this is correct documented behavior (D-06), not a stub.

## Self-Check: PASSED

Files verified present:
- `/home/user/ableton-mcp/MCP_Server/refinement/__init__.py` — FOUND
- `/home/user/ableton-mcp/MCP_Server/refinement/schema.py` — FOUND
- `/home/user/ableton-mcp/MCP_Server/tools/refinement.py` — FOUND
- `/home/user/ableton-mcp/tests/test_section_state.py` — FOUND

Commit `e3eff34` verified in git log.
