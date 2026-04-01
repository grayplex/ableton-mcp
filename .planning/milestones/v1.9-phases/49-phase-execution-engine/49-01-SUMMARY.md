---
phase: 49-phase-execution-engine
plan: 01
subsystem: orchestration
tags: [execution-plan, mcp-tool, phase-checklist, genre-patterns, midi-notes]
dependency_graph:
  requires: [48-production-agenda]
  provides: [get_phase_execution_plan, get_execution_plan]
  affects: [MCP_Server/orchestration, MCP_Server/tools/orchestration.py]
tech_stack:
  added: []
  patterns: [TypedDict-step-catalog, sentinel-args, genre-param-lookup]
key_files:
  created:
    - MCP_Server/orchestration/execution.py
    - tests/test_phase_execution.py
  modified:
    - MCP_Server/orchestration/__init__.py
    - MCP_Server/tools/orchestration.py
decisions:
  - "Merged kick+clap into one add_notes_to_clip step to keep serialized PhaseChecklist under 2000 chars"
  - "Omit 'phase' field from each step (redundant with checklist.phase_name) and omit null depends_on_step to minimize token cost"
  - "Seed note patterns (2-6 notes per instrument) represent 1-bar patterns to be looped; user extends in Ableton"
  - "House and trance drum patterns reduced to 3 kick_clap notes + 2 hi-hat notes as seed pattern"
metrics:
  duration: "35 minutes"
  completed: "2026-04-01"
  tasks: 5
  files: 4
---

# Phase 49 Plan 01: Phase Execution Engine Summary

Implemented `get_phase_execution_plan(phase_name, genre, section_name?, context?)` MCP tool returning a compact `PhaseChecklist` with concrete ordered `ExecutionStep` entries — exact tool names, genre-appropriate MIDI notes, and sentinel args for session-state values Claude resolves at runtime.

## What Was Built

**`MCP_Server/orchestration/execution.py`** — new module with:
- `_DRUM_PATTERNS` dict: 5 pattern groups (house, techno, hiphop, dubstep, trance) each with kick_clap and hihat note arrays
- `_GENRE_DRUM_GROUP` mapping: all 12 genres to their pattern group (ambient → None)
- `_GENRE_PARAMS` mapping: bass/harmony/melody instrument names per genre (e.g., hip_hop_trap uses Wavetable for bass, synthwave uses Wavetable for melody)
- Step builder functions per phase type: `_build_setup_steps`, `_build_drums_steps`, `_build_bass_steps`, `_build_harmony_steps`, `_build_melody_steps`, `_build_sound_design_steps`, `_build_arrangement_steps`, `_build_mix_steps`, `_build_master_steps`
- `get_execution_plan(phase_name, genre, section_name=None, context=None)` public API

**`MCP_Server/tools/orchestration.py`** — added `get_phase_execution_plan` MCP tool

**`MCP_Server/orchestration/__init__.py`** — exposed `get_execution_plan` in public API

**`tests/test_phase_execution.py`** — 8 pure unit tests, all passing

## Test Results

8/8 tests passing:
1. `test_drums_house_has_kick_notes` — kick note (pitch 36) present in add_notes_to_clip step
2. `test_drums_ambient_returns_error` — ambient returns `{"error": "No drums phase in ambient agenda"}`
3. `test_mix_phase_has_apply_recipe_step` — apply_mix_recipe present in mix checklist
4. `test_master_phase_has_apply_master_recipe` — apply_master_recipe present in master checklist
5. `test_section_name_uses_arrangement_clip` — section_name="Drop" uses create_arrangement_midi_clip, not create_clip
6. `test_setup_phase_has_set_tempo` — set_tempo step with tempo == 125 (house BPM midpoint)
7. `test_json_output_under_2000_chars` — all 9 phase types × house under 2000 chars
8. `test_step_numbers_sequential` — step_number values are 1,2,...N without gaps

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed `_note()` keyword argument error**
- **Found during:** Task 1 (first test run)
- **Issue:** `_DRUM_PATTERNS` used `vel=` as keyword arg but `_note()` uses `velocity=` parameter name
- **Fix:** Changed all `_note(pitch, time, vel=X)` calls to positional `_note(pitch, time, 0.25, X)`
- **Files modified:** MCP_Server/orchestration/execution.py

**2. [Rule 1 - Bug] Drum pattern dict key mismatch**
- **Found during:** Refactoring drum patterns to reduce token count
- **Issue:** After restructuring `_DRUM_PATTERNS` to use `kick_clap` key, `_build_drums_steps` still referenced old `pattern["kick"]` and `pattern["clap"]` keys
- **Fix:** Updated `_build_drums_steps` to use `pattern["kick_clap"]` and `pattern["hihat"]`
- **Files modified:** MCP_Server/orchestration/execution.py

**3. [Rule 2 - Token Budget] Iterative note count reduction to pass 2000-char test**
- **Found during:** Task 5 (test_json_output_under_2000_chars failing)
- **Issue:** Full 8-step drums checklist with per-note dicts (pitch, start_time, duration, velocity) serialized to 3621 chars, far exceeding the 2000-char budget
- **Fix applied in 4 iterations:**
  1. Removed `mute: False` from note dicts (saves ~12 chars/note)
  2. Shortened description strings (removed verbose "Replace <track_index>..." text)
  3. Removed `phase` field from each step (redundant with checklist `phase_name`)
  4. Omit `depends_on_step` when None
  5. Merged kick + clap into single `add_notes_to_clip` step
  6. Reduced hi-hat to 2 notes (half-beat seed pattern)
  7. Reduced house kick to 2 notes (0.0, 2.0 beats as seed)
  Final result: drums/house = 1970 chars
- **Files modified:** MCP_Server/orchestration/execution.py

## Known Stubs

None. All 9 phase checklists return concrete executable steps with genre-appropriate values.

## Self-Check: PASSED

- execution.py: FOUND
- test_phase_execution.py: FOUND
- 49-01-PLAN.md: FOUND
- Implementation commit: bd7cc9c
