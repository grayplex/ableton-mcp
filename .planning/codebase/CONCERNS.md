# Codebase Concerns

**Analysis Date:** 2026-04-01

---

## Known Limitations

**`get_arrangement_clip_notes` is arrangement-only:**
- The RS command `get_arrangement_clip_notes` (`AbletonMCP_Remote_Script/handlers/arrangement.py:116`) retrieves MIDI notes from arrangement clips only, identified by `clip_start_time` float position. There is no equivalent command for reading notes from session-view clip slots. Any tool that needs note content from session clips must use `get_clip_info` and is limited to clip metadata, not note data.

**`get_arrangement_state` omits track index:**
- The RS handler `_get_arrangement_state` (`AbletonMCP_Remote_Script/handlers/scaffold.py:51`) returns tracks as `{name, has_devices}` only — no `index` field. All checkpoint and next-action logic that inspects tracks works by name matching, not index. Any session with duplicate track names (e.g., two tracks both named "Pad") will silently cause incorrect phase inference.

**Checkpoint clips-by-track is capped at 8 tracks:**
- `get_checkpoint` and `get_transition_guidance` both iterate `tracks[:8]` when fetching `get_arrangement_clips` per track (`MCP_Server/orchestration/checkpoint.py:158`, `MCP_Server/orchestration/next_actions.py:223`). Sessions with more than 8 tracks will have clips for tracks 9+ treated as empty, causing incorrect "phase not complete" reporting.

**`has_devices` means any device, not just instruments:**
- The `has_devices` flag in `get_arrangement_state` is `len(track.devices) > 0`, which is `True` even if the track has only FX devices and no instrument. Checkpoint logic uses `has_devices` as a proxy for "track has an instrument loaded", which produces false positives for FX-only tracks.

**Execution step `clip_index: 0` assumption:**
- All session-clip phase steps in `MCP_Server/orchestration/execution.py` hardcode `"clip_index": 0`. This assumes every newly created track will have its first clip in slot 0. A session where slot 0 is already occupied (e.g., after multiple rounds of work) will fail silently at the note-writing step.

**Prompt parser is English-only:**
- The signal lexicon (`MCP_Server/prompt/lexicon.py`) covers English keywords only. Non-English prompts pass tokens through as `raw_descriptors` with no signal extraction. This is documented as out-of-scope for v1.7 but is a hard boundary with no fallback.

---

## Technical Debt

**Duplicate phase-detection constants across two modules:**
- Phase name sets (`_DRUM_NAMES`, `_BASS_NAMES`, `_HARMONY_NAMES`, `_MELODY_NAMES`) and device class name strings (`_COMPRESSOR`, `_GLUE_COMPRESSOR`, `_LIMITER`) are defined identically in both `MCP_Server/orchestration/checkpoint.py` and `MCP_Server/orchestration/next_actions.py`. A comment in `next_actions.py:12` acknowledges this: `"# Phase completion heuristics (same as checkpoint.py, duplicated for clarity)"`. Any update to detection logic must be applied in both files or the two modules will diverge.

**Double `get_ableton_connection()` calls per checkpoint request:**
- Both `get_checkpoint` and `get_transition_guidance` call `get_ableton_connection()` twice per invocation: once for arrangement/mix state, then again as `conn2` for the per-track clip loop. Since `get_ableton_connection` uses a global singleton under a mutex, both calls return the same socket — but the mutex is acquired and released twice, and the second call triggers a fresh liveness ping. Files: `MCP_Server/orchestration/checkpoint.py:146+157`, `MCP_Server/orchestration/next_actions.py:211+222`.

**`_step()` drops the `phase` key from ExecutionStep output:**
- The `_step` factory function in `MCP_Server/orchestration/execution.py:119` explicitly omits the `phase` key from the returned dict to minimize tokens. The `ExecutionStep` TypedDict in `MCP_Server/orchestration/schema.py:36` declares `phase: str` as a required field. Produced dicts are schema-non-conformant. This causes no runtime error (TypedDict is not enforced), but any consumer expecting `step["phase"]` will raise a `KeyError`.

**`_build_arrangement_steps` contains a non-callable placeholder step:**
- Step 5 in `_build_arrangement_steps` (`MCP_Server/orchestration/execution.py:370`) has `tool_name: "—"` and empty `suggested_args`. It is excluded from `estimated_tool_calls` but included in `total_steps` and will appear in `get_next_actions` output. Claude must detect and skip the `"—"` tool name at call time.

**`neo_soul_rnb` drum pattern falls back to `house`:**
- `_GENRE_DRUM_GROUP` in `MCP_Server/orchestration/execution.py:93` maps `neo_soul_rnb` to the `house` drum pattern with the comment `# default to house pattern`. Neo-soul/R&B uses swing-feel or live-kit patterns, not four-on-the-floor house kicks. This produces genre-inappropriate drum suggestions for `neo_soul_rnb`.

**`_build_bass_steps` uses identical static notes for all genres:**
- The bass line seed pattern in `_build_bass_steps` (`MCP_Server/orchestration/execution.py:219`) is a four-note hardcoded MIDI array used identically for all 12 genres. Unlike drums, there is no per-genre bass pattern variation. A house bass and a dubstep wobble bass are generated identically.

**`conftest.py` `_GAC_PATCH_TARGETS` requires manual updates:**
- Every new tool module that imports `get_ableton_connection` via `from ... import` must be added to `_GAC_PATCH_TARGETS` in `tests/conftest.py`. Orchestration modules (`MCP_Server/orchestration/checkpoint.py`, `MCP_Server/orchestration/next_actions.py`) that call `get_ableton_connection` indirectly are not listed and are therefore not patched in tests that use the `mock_connection` fixture. New tool modules added without updating this list will attempt a real Ableton socket connection during tests.

---

## Performance Concerns

**Checkpoint makes N+2 sequential socket round-trips:**
- `get_production_checkpoint` issues 2 commands (`get_arrangement_state`, `get_mix_state`) plus up to 8 `get_arrangement_clips` calls — up to 10 total sequential socket round-trips. At 10 seconds read timeout each, a worst case with a slow session could take up to 100 seconds. There is no batch mechanism for multi-track clip queries.

**`get_transition_guidance` duplicates all checkpoint queries:**
- `get_transition_guidance` (`MCP_Server/orchestration/next_actions.py:190`) independently re-fetches `get_arrangement_state`, `get_mix_state`, and up to 8 `get_arrangement_clips` calls, even when called immediately after `get_production_checkpoint`. No caching or shared state exists between the two functions.

**`get_next_actions` without `phase_name` compounds checkpoint latency:**
- When called without an explicit `phase_name`, `get_next_actions_result` calls `get_checkpoint` (the 10 round-trip operation above), then calls `get_execution_plan` (pure computation). High-frequency agent loops calling `get_next_actions` repeatedly will repeatedly incur the full checkpoint cost.

**`apply_recipe` has 30-second timeout with no progress feedback:**
- The `apply_recipe` command is in `_BROWSER_COMMANDS` with a 30-second timeout in `MCP_Server/connection.py:35`. A stalled device load (e.g., Ableton scanning a VST library) blocks the entire MCP server for 30 seconds before timing out. There is no progress feedback mechanism.

---

## Deferred Features

**HIST-01 — Execution history log:**
- No per-session log of executed steps. `get_next_actions` always returns the full checklist from step 1, regardless of how many steps have already been run. A comment in `MCP_Server/orchestration/next_actions.py:179` acknowledges: `"# Skip steps if phase already started (progress > 0.3) — return all for now (HIST-01 deferred)"`. Claude must manually track which steps have been executed.
- Source: `REQUIREMENTS.md` Future Requirements → HIST-01

**PARA-01 — Parallel phase execution:**
- All phases are strictly sequential. `ProductionPhase.depends_on` is always `[phase_order[i-1]]`. Phases with no true data dependency (e.g., bass programming does not require drums to be complete) are not flagged as parallelizable.
- Source: `REQUIREMENTS.md` Future Requirements → PARA-01

**ADPT-01 — Adaptive agenda refinement:**
- No `refine_agenda` tool. A user instruction like "skip mastering" or "add a second melody phase" requires re-calling `get_production_agenda` from scratch.
- Source: `REQUIREMENTS.md` Future Requirements → ADPT-01

**REFN-03 — Refinement history log:**
- No session-scoped log of applied `SectionRefinementPlan` operations. `refine_section` cannot detect conflicting or redundant refinements. Calling it twice with opposite instructions applies both silently.
- Source: `v1.8-REQUIREMENTS.md` Future Requirements → REFN-03

**RFNA-04 — Revert section refinement:**
- No revert capability for `apply_section_note_refinement` or `apply_section_device_refinement`. Ableton's native undo stack is the only recourse. Requires REFN-03 first.
- Source: `v1.8-REQUIREMENTS.md` Future Requirements → RFNA-04

**SNAP-03 — Cross-section comparison:**
- No `compare_sections` tool. Claude cannot programmatically diff `SectionState` between two named sections.
- Source: `v1.8-REQUIREMENTS.md` Future Requirements → SNAP-03

**PARS-03 — Prompt signal conflict resolution:**
- When contradictory signals appear in a prompt (e.g., "euphoric dark techno"), the parser resolves silently by whichever signal last overwrites the parameter. No `signal_conflicts` list in `ProductionBrief`.
- Source: `v1.7-REQUIREMENTS.md` Future Requirements → PARS-03

**SESS-03 — Prompt history:**
- No `list_production_briefs()` tool. Session-scoped brief history is not persisted.
- Source: `v1.7-REQUIREMENTS.md` Future Requirements → SESS-03

**Section-aware mixing, frequency conflict detection, full sidechain automation:**
- `apply_mix_recipe` applies a genre recipe globally to a track with no per-section variation. Per-section timbral changes require the slower `apply_section_device_refinement` with `write_automation=True`.
- Source: `v1.4-REQUIREMENTS.md` Future Requirements

---

## Architectural Risks

**Phase completion inference is fragile name-matching:**
- `_infer_completed_phases` in `MCP_Server/orchestration/checkpoint.py:49` determines phase completion by substring-matching track names against fixed sets (`_DRUM_NAMES = {"drum", "kick", "snare", "percussion", "beat"}`). A session where the user named the drums track "Pattern 1", "Beat Loop", or any non-matching name will cause the checkpoint to permanently report that phase as incomplete regardless of actual content. This is a core architectural assumption that cannot be worked around without HIST-01.

**Master phase short-circuits the entire phase walk:**
- If `GlueCompressor` and `Limiter2` are both present on the master track, `_infer_completed_phases` immediately returns all phases as complete (`MCP_Server/orchestration/checkpoint.py:58-61`). A session with only a master chain pre-applied but no actual instrument tracks reports 100% production completion. This is an intentional design decision recorded in `.planning/STATE.md`, but it creates a false-positive risk for any workflow that pre-loads a master bus template.

**Connection singleton is not safe under concurrent tool calls:**
- The global `_ableton_connection` in `MCP_Server/connection.py` is protected by `_connection_lock` during creation and liveness validation, but `send_command` does not hold the lock during the socket write+read cycle. If FastMCP dispatches two tool requests concurrently (e.g., via async parallelism), their socket messages can interleave. MCP's request/response protocol makes concurrent dispatch unlikely in practice but this is an implicit assumption rather than an enforced invariant.

**Three key packages are absent from the current runtime environment:**
- `mcp` (FastMCP) is listed as a required dependency in `pyproject.toml` but is not installed. `ModuleNotFoundError: No module named 'mcp'` occurs on import of `MCP_Server.server` and any `MCP_Server.tools.*` module. This causes 411 test failures across all tool test files. Only the 132 tests in pure-Python modules (`test_checkpoint.py`, `test_genres.py`, `test_next_actions.py`, and related orchestration/genre tests) pass.
- `pytest-asyncio` is absent: the `asyncio_mode = "auto"` setting in `pyproject.toml` has no effect; all `async def test_*` functions fail with `"async def functions are not natively supported"`.
- `tiktoken` is absent: `tests/test_genre_quality.py` fails at import with `ModuleNotFoundError: No module named 'tiktoken'`.
- Fix: `pip install mcp[cli] pytest-asyncio tiktoken` (or install via `pip install -e ".[dev]"` if the environment supports the full dependency group).

**No formal session-state persistence:**
- All production progress (completed phases, applied refinements, production brief) exists only in Ableton's live session and the in-memory MCP connection. A Claude context reset loses all orchestration state. The checkpoint tool reconstructs a heuristic partial picture, but HIST-01 (execution log) and REFN-03 (refinement log) are unimplemented, leaving resume-after-reset incomplete for any production beyond the setup phase.

**`get_arrangement_state` does not include track index; sentinel resolution requires a separate call:**
- `ExecutionStep.suggested_args` uses `"<track_index>"` sentinel strings for all phase steps requiring a track index. The `description` field instructs Claude to resolve via `get_all_tracks()`. This is a correct design for a stateless checklist generator, but it means every phase execution requires at least one additional `get_all_tracks` call per new track. If track order changes between plan generation and execution (e.g., user adds tracks in Ableton), index resolution can silently produce stale results.

---

*Concerns audit: 2026-04-01*
