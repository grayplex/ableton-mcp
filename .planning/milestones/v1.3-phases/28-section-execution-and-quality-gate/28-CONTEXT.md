# Phase 28: Section Execution and Quality Gate - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver two new MCP tools for methodical section execution and arrangement completeness checking:

1. `get_section_checklist(plan, section_name)` — returns the list of roles for a named section with instrument status per track, so Claude knows which roles still need an instrument loaded
2. `get_arrangement_progress()` — reads all MIDI tracks from Ableton and returns which have no instrument loaded, flagging the ones that will produce silence

Both tools read Ableton state (track devices) via socket calls. No new Remote Script handlers needed beyond what Phase 27 built — instrument presence is derivable from `track.devices`.

</domain>

<decisions>
## Implementation Decisions

### Checklist Data Source
- **D-01:** `get_section_checklist` is **stateless** — caller passes the production plan dict (output of `generate_production_plan`) plus a `section_name` string. Tool filters sections array to find the matching section, then checks each role's corresponding track in Ableton for instrument presence. No plan persistence in Ableton; the caller already has the plan.
- **D-02:** Return shape: roles for the section with per-role instrument status. Pending roles are those whose track has no instrument loaded.

### "Pending" / "Done" Definition
- **D-03:** A role is considered **done** when its corresponding MIDI track has at least one device loaded (`len(track.devices) > 0`). A role is **pending** when the track exists but has no devices. Instrument-only signal — notes/clips are not checked. This is intentional: the checklist is about "did you load an instrument", not "did you write notes".
- **D-04:** Track name matching follows Phase 27 D-02/D-03 naming convention: bare role names with numbered suffixes for duplicates ("lead", "lead 2", "lead 3"). Checklist tool must reverse the deduplication logic to map roles back to track names.

### Arrangement Progress Check
- **D-05:** Tool name: `get_arrangement_progress`. Returns only the empty (no-instrument) tracks, not all tracks. Shape:
  ```json
  {
    "empty_tracks": ["lead 2", "pad"],
    "total_tracks": 8,
    "empty_count": 2
  }
  ```
- **D-06:** "Empty" means: MIDI track with no devices loaded. Non-MIDI tracks (audio, return, master) are excluded from the check — scaffolded tracks are always MIDI per Phase 27 D-06.

### Claude's Discretion
- Whether to add `get_section_checklist` and `get_arrangement_progress` to the existing `MCP_Server/tools/scaffold.py` module (natural fit since they read scaffold output) or create a new `execution.py` module.
- Whether to add a new Remote Script handler command to enumerate track device counts, or reuse `get_arrangement_state` (already returns track names) and augment it with device info — researcher should check if `get_arrangement_state` can be extended without breaking Phase 27.
- How to handle the case where a role's expected track name doesn't exist in Ableton (e.g., user renamed a track). Options: skip silently, return a warning, or mark as unknown.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — EXEC-01 (section checklist), EXEC-02 (arrangement progress check); also Phase 28 success criteria
- `.planning/ROADMAP.md` — Phase 28 goal and success criteria (3 criteria)

### Prior Phase Output (what Phase 28 builds on)
- `.planning/phases/27-locator-and-scaffolding-commands/27-CONTEXT.md` — D-02/D-03 (track naming with numbered suffixes), D-06 (all scaffold tracks are MIDI), D-14 (instrument status deferred to Phase 28)
- `MCP_Server/tools/scaffold.py` — `get_arrangement_overview` return shape (locators, tracks, session_length_bars); `_deduplicate_roles()` helper that Phase 28 must mirror/reuse to map roles → track names

### Remote Script Patterns
- `AbletonMCP_Remote_Script/handlers/scaffold.py` — `get_arrangement_state` command (returns cue_points, tracks, song_length, time signature) — candidate for extension with device info
- `AbletonMCP_Remote_Script/handlers/tracks.py` — existing device enumeration pattern: `for device in track.devices` with `device.name`, `device.class_name`

### Tool Module Pattern
- `MCP_Server/tools/scaffold.py` — canonical tool module pattern for this phase: `@mcp.tool()`, `Context` param, `format_error()`, `get_ableton_connection()`, `json.dumps()` return
- `MCP_Server/connection.py` — `format_error()` and `ableton.send_command()` patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/tools/scaffold.py` → `_deduplicate_roles(sections)` — already computes the full role→track name mapping. Phase 28 checklist needs the inverse: given a role name, find its track name. Reuse or export this helper.
- `AbletonMCP_Remote_Script/handlers/scaffold.py` → `get_arrangement_state` — already reads all tracks from `song.tracks`. Extending it to include `len(track.devices) > 0` per track would be minimal.
- `AbletonMCP_Remote_Script/handlers/tracks.py` — device enumeration pattern: `for device_index, device in enumerate(track.devices)` — already established; Phase 28 only needs the count/presence check.

### Established Patterns
- All Remote Script write commands use `@command("name", write=True)`; read commands omit `write=True`
- All MCP tools return `str` (JSON or `format_error()` string)
- Track index is 0-based in Ableton API; `song.tracks` enumerates all tracks in order

### Integration Points
- `get_section_checklist` and `get_arrangement_progress` must be registered in `MCP_Server/tools/__init__.py` (import the module)
- If a new Remote Script handler command is added, register it in `AbletonMCP_Remote_Script/handlers/__init__.py`
- Phase 28 success criterion 3 requires end-to-end workflow: plan → scaffold → section checklist — no new tool interactions outside scaffold.py territory

</code_context>

<specifics>
## Specific Requirements

- `get_section_checklist` receives the full plan dict (same shape as `generate_production_plan` output) plus a `section_name` string — caller pattern mirrors `scaffold_arrangement`
- "Pending" = track exists in Ableton with zero devices. "Done" = track has ≥1 device loaded.
- Progress check returns only empty tracks (not all tracks) — focused format per success criterion 2
- Non-MIDI tracks excluded from progress check (scaffold only creates MIDI tracks per Phase 27 D-06)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 28-section-execution-and-quality-gate*
*Context gathered: 2026-03-28*
