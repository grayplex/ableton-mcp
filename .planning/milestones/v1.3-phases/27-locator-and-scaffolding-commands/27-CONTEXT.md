# Phase 27: Locator and Scaffolding Commands - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver two new MCP tools that write a production plan into Ableton Arrangement view and read it back:

1. `scaffold_arrangement` — accepts the JSON output of `generate_production_plan`, reads the live session's time signature, creates named locators at the correct beat positions and named MIDI tracks (one per unique role) in Ableton — all in one atomic operation.
2. `get_arrangement_overview` — returns a minimal state summary: all locators with bar positions, all track names, and session length in bars for mid-session re-orientation.

Both tools make socket calls to Ableton (unlike the pure-computation tools in Phase 26).

</domain>

<decisions>
## Implementation Decisions

### Track Naming
- **D-01:** Track names use bare role names from the plan's role list (e.g. "kick", "bass", "lead", "pad").
- **D-02:** When the same role string appears in multiple sections (implying different sounds), tracks are numbered with a plain suffix: "lead", "lead 2", "lead 3". No section prefix. Numbering is automatic and deterministic — count occurrences of each role across all sections.
- **D-03:** Deduplication is by role name string. If "lead" appears 3 times across sections, create 3 tracks: "lead", "lead 2", "lead 3".

### Track Creation Scope
- **D-04:** Create one shared MIDI track per unique role occurrence (per D-02/D-03), using the deduplicated union of all roles across all sections. All tracks are created in one pass.
- **D-05:** No `section_filter` parameter — scaffold always creates tracks for all roles in the plan. Caller controls scope by passing a filtered plan (e.g. via `remove_sections` override before calling scaffold).
- **D-06:** All scaffold-created tracks are MIDI tracks (audio and return tracks are out of scope for v1.3 scaffolding, per REQUIREMENTS.md out-of-scope section).

### Locator Creation
- **D-07:** One locator per section, named by section name (e.g. "intro", "drop", "breakdown"), placed at the beat position derived from `bar_start`.
- **D-08:** Bar-to-beat conversion: `beat_position = (bar_start - 1) * beats_per_bar`, where `beats_per_bar = numerator * (4.0 / denominator)` from the session time signature (matches the REQUIREMENTS.md formula).
- **D-09:** `scaffold_arrangement` reads the session time signature internally via a `get_session_info` socket call — no `time_signature` parameter for callers. This differs from Phase 26's `generate_production_plan` (which accepted `time_signature` as a param), but is intentional: scaffold writes to Ableton so it should use the live session's actual state.

### Scaffold Input
- **D-10:** `scaffold_arrangement` accepts the raw plan JSON dict (output of `generate_production_plan`). Does NOT accept genre+params — no internal plan generation. Two-tool workflow: generate plan first, then scaffold.
- **D-11:** Expected input shape: the `sections` array from the plan, each entry with `name`, `bar_start`, `bars`, `roles` keys.

### `get_arrangement_overview` Response
- **D-12:** Returns a minimal flat structure:
  ```json
  {
    "locators": [{"name": "intro", "bar": 1}, ...],
    "tracks": ["kick", "bass", "lead", "pad"],
    "session_length_bars": 64
  }
  ```
- **D-13:** `locators[].bar` is a 1-indexed bar number (not raw beats), matching the `bar_start` convention from Phase 26. Conversion: `bar = floor(beat_position / beats_per_bar) + 1`.
- **D-14:** `tracks` is a flat list of track names (strings), not objects. No instrument status or type info — that's Phase 28's responsibility.
- **D-15:** `session_length_bars` is derived from Ableton's `song.song_length` (in beats) divided by `beats_per_bar`.

### Tool Architecture
- **Claude's Discretion:** Whether to place scaffold/overview tools in a new `MCP_Server/tools/scaffold.py` module or extend `plans.py`. Recommend new file given the architectural split: `plans.py` is pure computation (no socket calls); scaffold tools need socket calls to Ableton. Keep the separation clean.
- **Claude's Discretion:** Whether to add the locator creation commands (`create_locator`, `set_locator_name`) to `AbletonMCP_Remote_Script/handlers/transport.py` (near existing cue point handlers) or a new `arrangement_scaffold.py` handler file.
- **Claude's Discretion:** How to handle partial failure mid-scaffold (e.g. 5 of 12 tracks created before an error). Report what was created and the error; do not attempt rollback (Ableton has no transactional API).
- **Claude's Discretion:** Whether to use `song.set_or_delete_cue()` + playhead repositioning or another Live 12 API method for positional locator creation. Researcher should confirm the correct Live API approach.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — SCAF-01 (atomic scaffold into Ableton), SCAF-02 (arrangement overview readback); also Out of Scope section (audio clips, non-MIDI tracks, non-4/4 UI out of scope)
- `.planning/ROADMAP.md` — Phase 27 success criteria (3 criteria including 15-second write timeout)

### Prior Phase Output (what scaffold_arrangement consumes)
- `.planning/phases/26-production-plan-builder/26-CONTEXT.md` — D-05 (`bar_start` is 1-indexed), D-06 (time_signature is caller-supplied for plan builder), D-07 (cumulative bar calculation), D-08/D-09/D-10 (override interface)
- `MCP_Server/tools/plans.py` — `generate_production_plan` output shape: `{genre, key, bpm, vibe, time_signature, sections: [{name, bar_start, bars, roles, transition_in?}]}`

### Existing Cue Point API (locator foundation)
- `AbletonMCP_Remote_Script/handlers/transport.py` — `get_cue_points`, `set_or_delete_cue`, `jump_to_cue` — existing cue point read/toggle/jump handlers; scaffold will need positional creation beyond these
- `MCP_Server/tools/transport.py` — `get_cue_points` MCP tool

### Existing Track Creation API (track foundation)
- `AbletonMCP_Remote_Script/handlers/tracks.py` — `create_midi_track`, `create_audio_track`, `create_return_track` — track creation patterns including `song.create_midi_track(index)` call
- `MCP_Server/tools/tracks.py` — track tool module for patterns

### Tool Module Pattern to Follow
- `MCP_Server/tools/plans.py` — canonical tool module: `@mcp.tool()`, `Context` param, `format_error()`, `json.dumps()` return
- `MCP_Server/tools/genres.py` — additional tool module reference
- `MCP_Server/connection.py` — `format_error()` and `ableton.send_command()` patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AbletonMCP_Remote_Script/handlers/tracks.py` — `_resolve_track()` helper + `create_midi_track` at `song.create_midi_track(index)` — directly reusable for track creation in scaffold
- `AbletonMCP_Remote_Script/handlers/transport.py` — `get_cue_points` handler — read path already exists; creation path needs new handler using Live API
- `MCP_Server/connection.py` — `ableton.send_command()` + `format_error()` — the socket call pattern all scaffold tools must use
- `MCP_Server/tools/plans.py` — `_build_plan_sections()` helper already produces the `{name, bar_start, bars, roles}` shape that `scaffold_arrangement` will consume

### Established Patterns
- All Remote Script handlers use `@command("command_name", write=True)` for write operations — scaffold handlers must include `write=True`
- All MCP tools return `str` (JSON via `json.dumps()` or error via `format_error()`)
- Track index is 0-based in Ableton API; track names are set via `track.name = "..."`
- Beat positions in Ableton are 0-indexed floats (beat 0 = start of song); `bar_start=1` maps to `beat_position=0.0`

### Integration Points
- New handler file: `AbletonMCP_Remote_Script/handlers/scaffold.py` (or extend `transport.py`) — add `create_locator_at`, `rename_locator` commands
- New tool module: `MCP_Server/tools/scaffold.py` — `scaffold_arrangement` and `get_arrangement_overview` tools
- Both must be registered: handler via `AbletonMCP_Remote_Script/handlers/__init__.py`, tool module via `MCP_Server/tools/__init__.py`
- Phase 28 (`get_arrangement_progress`) will build on the track list from `get_arrangement_overview` — keep track name format consistent

</code_context>

<specifics>
## Specific Requirements

- Scaffold must complete within the 15-second write timeout (success criterion 3) — this constrains how many separate socket round-trips are acceptable for a typical 7-section arrangement
- `get_arrangement_overview` locators use `bar` (1-indexed), not raw beat position — consistent with Phase 26 `bar_start` convention
- Two-tool workflow is intentional: generate plan → scaffold. No internal plan generation in `scaffold_arrangement`
- Time signature is fetched live from Ableton inside scaffold (not a caller param) — scaffold should reflect the actual session state

</specifics>

<deferred>
## Deferred Ideas

- Default instrument loading per role on scaffold tracks — deferred to v1.3.1 per REQUIREMENTS.md (came up in Phase 26, still deferred)
- `section_filter` param on scaffold — not needed; callers use `remove_sections` override on `generate_production_plan` instead
- Track type or instrument status in `get_arrangement_overview` — deferred to Phase 28 (`get_arrangement_progress`)

</deferred>

---

*Phase: 27-locator-and-scaffolding-commands*
*Context gathered: 2026-03-27*
