# Phase 28: Section Execution and Quality Gate - Research

**Researched:** 2026-03-28
**Domain:** MCP tool development (stateless checklist + arrangement progress check via Ableton Live API)
**Confidence:** HIGH

## Summary

Phase 28 adds two read-only MCP tools that close the production workflow loop: `get_section_checklist` (returns pending instrument roles for a named section) and `get_arrangement_progress` (flags scaffolded MIDI tracks with no instrument loaded). Both tools combine client-side plan data with live Ableton track state retrieved via socket commands.

The implementation is straightforward because all building blocks already exist. The `_deduplicate_roles` helper in `scaffold.py` already computes role-to-track-name mappings. The Remote Script's `get_arrangement_state` handler already enumerates all tracks. The only gap is that `get_arrangement_state` currently returns track names only (strings) -- it needs to also return device presence per track. The `tracks.py` handler already has a device enumeration pattern (`for device in track.devices`) that can be adapted.

**Primary recommendation:** Extend `get_arrangement_state` to include `has_devices: bool` per track (backward-compatible addition), then build both MCP tools in a new `MCP_Server/tools/execution.py` module that reuses `_deduplicate_roles` from `scaffold.py`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** `get_section_checklist` is stateless -- caller passes the production plan dict plus a `section_name` string. Tool filters sections array to find the matching section, then checks each role's corresponding track in Ableton for instrument presence. No plan persistence in Ableton.
- **D-02:** Return shape: roles for the section with per-role instrument status. Pending roles are those whose track has no instrument loaded.
- **D-03:** A role is "done" when its corresponding MIDI track has at least one device loaded (`len(track.devices) > 0`). A role is "pending" when the track exists but has no devices. Instrument-only signal -- notes/clips are not checked.
- **D-04:** Track name matching follows Phase 27 D-02/D-03 naming convention: bare role names with numbered suffixes for duplicates. Checklist tool must reverse the deduplication logic to map roles back to track names.
- **D-05:** Tool name: `get_arrangement_progress`. Returns only the empty (no-instrument) tracks, not all tracks. Shape: `{"empty_tracks": [...], "total_tracks": N, "empty_count": N}`
- **D-06:** "Empty" means: MIDI track with no devices loaded. Non-MIDI tracks (audio, return, master) are excluded -- scaffolded tracks are always MIDI per Phase 27 D-06.

### Claude's Discretion
- Whether to add tools to existing `scaffold.py` or create a new `execution.py` module.
- Whether to add a new Remote Script handler command or extend `get_arrangement_state` with device info.
- How to handle the case where a role's expected track name doesn't exist in Ableton (renamed/deleted track).

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EXEC-01 | User can get a per-section execution checklist -- returns pending instrument roles for a given section so Claude can execute methodically | Checklist tool combines plan section roles with live Ableton track device state; `_deduplicate_roles` provides role-to-track mapping; `get_arrangement_state` (extended) provides device presence |
| EXEC-02 | User can check arrangement progress -- flags scaffolded MIDI tracks that have no instrument loaded, preventing silent empty tracks | Progress tool reads all tracks from extended `get_arrangement_state`, filters to those with `has_devices: false`, returns focused empty-track list |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mcp (FastMCP) | 1.26.0 | MCP server framework | Project standard; `@mcp.tool()` decorator pattern |
| Python | 3.10+ | Runtime | Project standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json | stdlib | Serialize tool responses | All MCP tool return values |
| unittest.mock | stdlib | Test mocking | Mock Ableton socket connection |
| pytest | 9.0.2 | Test framework | All test files |

No new dependencies required. Phase 28 uses only existing project libraries.

## Architecture Patterns

### Recommended Module Structure

**Recommendation:** Create a new `MCP_Server/tools/execution.py` module rather than extending `scaffold.py`.

Rationale: `scaffold.py` is a write tool (creates locators and tracks). Phase 28 tools are read-only checklist/progress tools. Separation by read/write responsibility matches the project's existing `plans.py` (pure computation) vs `scaffold.py` (Ableton writes) split.

```
MCP_Server/tools/
    execution.py          # NEW: get_section_checklist, get_arrangement_progress
    scaffold.py           # EXISTING: scaffold_arrangement, get_arrangement_overview (+ export _deduplicate_roles)
    __init__.py           # ADD: import execution module

AbletonMCP_Remote_Script/handlers/
    scaffold.py           # MODIFY: extend get_arrangement_state to include device presence per track
```

### Pattern 1: Extending get_arrangement_state (Recommended)

**What:** Add `has_devices: bool` to each track entry in `get_arrangement_state` response. Currently returns `tracks: ["kick", "bass", "lead"]` (string list). Change to `tracks: [{"name": "kick", "has_devices": true}, ...]` (object list).

**Why this over a new handler:** Avoids a second socket round-trip. `get_arrangement_state` already iterates all tracks. Adding `len(track.devices) > 0` per track is one extra attribute read per track -- negligible cost.

**Backward compatibility concern:** `get_arrangement_overview` in `scaffold.py` currently reads `state["tracks"]` as a string list. It must be updated to extract names from the new object format: `[t["name"] for t in state["tracks"]]`.

**Example (Remote Script change):**
```python
# In AbletonMCP_Remote_Script/handlers/scaffold.py, get_arrangement_state
tracks = []
for track in self._song.tracks:
    tracks.append({
        "name": track.name,
        "has_devices": len(track.devices) > 0,
    })
```

### Pattern 2: Role-to-Track Name Mapping for Checklist

**What:** Given a section's roles list and the full plan's sections, determine which Ableton track name corresponds to each role occurrence in the target section.

**How it works:**
1. Call `_deduplicate_roles(plan["sections"])` to get the full track name list (same logic used by `scaffold_arrangement`)
2. For the target section, determine which numbered instance of each role this section uses
3. Map each role in the section to its track name

**Key insight:** The dedup algorithm counts how many sections each role appears in, then assigns "role", "role 2", "role 3" in section-appearance order. To reverse this for a specific section:
- Track the section index (1-based among sections containing that role)
- Map to "role" for index 1, "role N" for index N

**Example (MCP tool helper):**
```python
def _map_section_roles_to_tracks(plan_sections: list[dict], section_name: str) -> list[dict]:
    """Map a section's roles to their Ableton track names using dedup logic.

    Returns list of {"role": str, "track_name": str} dicts.
    """
    # Find target section
    target = None
    for s in plan_sections:
        if s["name"] == section_name:
            target = s
            break
    if target is None:
        return []

    # For each role in the target section, count which occurrence this is
    # (how many earlier sections also contain this role)
    result = []
    for role in target.get("roles", []):
        occurrence = 0
        for s in plan_sections:
            section_roles_unique = set()
            for r in s.get("roles", []):
                if r not in section_roles_unique:
                    section_roles_unique.add(r)
                    if r == role:
                        occurrence += 1
            if s["name"] == section_name:
                break

        track_name = role if occurrence <= 1 else f"{role} {occurrence}"
        result.append({"role": role, "track_name": track_name})

    return result
```

### Pattern 3: MCP Tool Registration

**What:** Standard `@mcp.tool()` with `Context` param, `format_error()` for errors, `json.dumps()` return.

```python
# MCP_Server/tools/execution.py
import json
from mcp.server.fastmcp import Context
from MCP_Server.connection import format_error, get_ableton_connection
from MCP_Server.server import mcp
from MCP_Server.tools.scaffold import _deduplicate_roles

@mcp.tool()
def get_section_checklist(ctx: Context, plan: dict, section_name: str) -> str:
    """..."""
    # implementation
```

**Registration:** Add `execution` to the import line in `MCP_Server/tools/__init__.py`.

### Anti-Patterns to Avoid
- **Storing plan state server-side:** MCP is stateless. The caller (Claude) holds the plan in context and passes it to each tool call. Never cache plans.
- **Returning all tracks in progress check:** D-05 explicitly says return only empty tracks. Do not return done tracks -- it wastes tokens.
- **Checking notes/clips for "done" status:** D-03 is explicit: device presence only. A track with an instrument but no notes is "done" for the checklist.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Role deduplication | Custom dedup logic in execution.py | Import `_deduplicate_roles` from `scaffold.py` | Must produce identical track names to what scaffold_arrangement created |
| Track device presence | New `get_track_devices` handler per track | Extend `get_arrangement_state` to include `has_devices` | One socket call vs N calls (one per track) |
| Error formatting | Custom error dicts | `format_error()` from `connection.py` | Project-wide consistent error shape |

**Key insight:** The role-to-track mapping MUST match exactly what `scaffold_arrangement` used when creating tracks. Reimplementing dedup logic risks divergence. Import and reuse the same function.

## Common Pitfalls

### Pitfall 1: Dedup Order Sensitivity
**What goes wrong:** The checklist maps a role to the wrong track number because the occurrence counting iterates sections differently than `_deduplicate_roles`.
**Why it happens:** `_deduplicate_roles` counts how many sections contain each role (not how many times the role string appears within a section), then assigns numbers. If the checklist counts differently, "lead 2" in the checklist might refer to a different track than the one scaffold created.
**How to avoid:** Use the exact same section iteration order and counting logic as `_deduplicate_roles`. The occurrence number for a section is determined by its position among sections containing that role.
**Warning signs:** Tests where checklist says "lead 2 is pending" but the actual "lead 2" track in Ableton has an instrument.

### Pitfall 2: get_arrangement_state Backward Compatibility
**What goes wrong:** Changing `tracks` from string list to object list breaks `get_arrangement_overview`.
**Why it happens:** `get_arrangement_overview` reads `state["tracks"]` and passes it through directly. After the change, it would return objects instead of strings.
**How to avoid:** Update `get_arrangement_overview` in the same commit that changes `get_arrangement_state`. Extract track names: `[t["name"] for t in state["tracks"]]`.
**Warning signs:** Existing `test_scaffold.py` tests for `get_arrangement_overview` will fail if the overview tool is not updated.

### Pitfall 3: Track Renamed by User
**What goes wrong:** User renames a scaffolded track in Ableton (e.g., "lead" to "synth lead"). The checklist tool cannot find the expected track name.
**Why it happens:** Track names are the only identifier; Ableton does not preserve a "role" metadata field.
**How to avoid:** Per CONTEXT.md Claude's Discretion, return a warning/unknown status for roles whose expected track name is not found. Recommended: `"status": "not_found"` with a message like `"Track 'lead' not found -- may have been renamed"`.
**Warning signs:** Checklist returns all roles as "not_found" after user renames tracks.

### Pitfall 4: conftest.py Patch Target Missing
**What goes wrong:** New `execution.py` module imports `get_ableton_connection`, but the mock patch in `conftest.py` does not include `MCP_Server.tools.execution.get_ableton_connection`.
**Why it happens:** The `_GAC_PATCH_TARGETS` list in conftest.py must be updated for every new module that imports `get_ableton_connection`.
**How to avoid:** Add `"MCP_Server.tools.execution.get_ableton_connection"` to `_GAC_PATCH_TARGETS` in `conftest.py`.
**Warning signs:** Tests pass individually but `mock_connection.send_command` is never called -- the real connection factory runs.

## Code Examples

### get_section_checklist Return Shape
```json
{
  "section": "drop",
  "roles": [
    {"role": "kick", "track_name": "kick", "status": "done"},
    {"role": "lead", "track_name": "lead 2", "status": "pending"},
    {"role": "bass", "track_name": "bass", "status": "done"}
  ],
  "pending_count": 1,
  "total_count": 3
}
```

### get_arrangement_progress Return Shape (per D-05)
```json
{
  "empty_tracks": ["lead 2", "pad"],
  "total_tracks": 8,
  "empty_count": 2
}
```

### Mock Factory Pattern for Tests
```python
def _mock_execution_factory(tracks=None):
    """Mock for get_arrangement_state with device presence."""
    if tracks is None:
        tracks = [
            {"name": "kick", "has_devices": True},
            {"name": "bass", "has_devices": False},
        ]

    def side_effect(cmd, params=None):
        if cmd == "get_arrangement_state":
            return {
                "cue_points": [],
                "tracks": tracks,
                "song_length": 256.0,
                "signature_numerator": 4,
                "signature_denominator": 4,
            }
        return {}

    return side_effect
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `get_arrangement_state` returns `tracks: [str]` | Will return `tracks: [{"name": str, "has_devices": bool}]` | Phase 28 | Must update `get_arrangement_overview` consumer |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pytest.ini` or default discovery |
| Quick run command | `python -m pytest tests/test_scaffold.py tests/test_execution.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EXEC-01 | `get_section_checklist` returns pending roles for a named section | unit | `python -m pytest tests/test_execution.py::TestSectionChecklist -x` | No -- Wave 0 |
| EXEC-01 | Checklist maps roles to correct track names via dedup logic | unit | `python -m pytest tests/test_execution.py::TestSectionChecklist::test_role_to_track_mapping -x` | No -- Wave 0 |
| EXEC-01 | Checklist handles missing section name gracefully | unit | `python -m pytest tests/test_execution.py::TestSectionChecklist::test_section_not_found -x` | No -- Wave 0 |
| EXEC-01 | Checklist handles renamed/missing track with warning | unit | `python -m pytest tests/test_execution.py::TestSectionChecklist::test_track_not_found -x` | No -- Wave 0 |
| EXEC-02 | `get_arrangement_progress` returns only empty tracks | unit | `python -m pytest tests/test_execution.py::TestArrangementProgress -x` | No -- Wave 0 |
| EXEC-02 | Progress check excludes non-MIDI tracks (handled by `get_arrangement_state` only returning `song.tracks`) | unit | `python -m pytest tests/test_execution.py::TestArrangementProgress::test_only_midi_tracks -x` | No -- Wave 0 |
| EXEC-02 | All tracks have instruments -> empty_tracks is empty list | unit | `python -m pytest tests/test_execution.py::TestArrangementProgress::test_all_tracks_loaded -x` | No -- Wave 0 |
| -- | Backward compat: `get_arrangement_overview` still returns string track names after state change | unit | `python -m pytest tests/test_scaffold.py::TestArrangementOverview -x` | Yes -- existing |
| -- | Both new tools are registered in MCP server | unit | `python -m pytest tests/test_execution.py::test_execution_tools_registered -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_execution.py tests/test_scaffold.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_execution.py` -- covers EXEC-01, EXEC-02
- [ ] `conftest.py` update -- add `MCP_Server.tools.execution.get_ableton_connection` to `_GAC_PATCH_TARGETS`
- [ ] No framework install needed -- pytest already configured

## Open Questions

1. **Duplicate roles within a single section**
   - What we know: `_deduplicate_roles` uses `section_seen` set to count each role only once per section. A section with `roles: ["lead", "lead"]` counts "lead" only once for that section.
   - What's unclear: Should `get_section_checklist` deduplicate roles within the target section too, or report each occurrence?
   - Recommendation: Deduplicate within section (matching `_deduplicate_roles` behavior). Blueprint roles lists should not contain duplicates, but defensive dedup is cheap.

2. **Track type filtering in get_arrangement_state**
   - What we know: `get_arrangement_state` iterates `self._song.tracks` which in Ableton's API returns only regular tracks (not return or master tracks). So non-MIDI track exclusion (D-06) is partially handled -- audio tracks still appear.
   - What's unclear: Should the handler filter to MIDI tracks only, or should the MCP tool do the filtering?
   - Recommendation: Return all regular tracks with `has_devices` from the handler; let the MCP tool decide what to filter. This keeps the handler general-purpose. The `has_midi_input` attribute on track objects can distinguish MIDI from audio if needed, but since scaffold only creates MIDI tracks, all scaffolded tracks will be MIDI.

## Sources

### Primary (HIGH confidence)
- `MCP_Server/tools/scaffold.py` -- `_deduplicate_roles` implementation, `get_arrangement_overview` consumer of `get_arrangement_state`
- `AbletonMCP_Remote_Script/handlers/scaffold.py` -- `get_arrangement_state` handler, current return shape
- `AbletonMCP_Remote_Script/handlers/tracks.py` -- device enumeration pattern (`for device in track.devices`)
- `MCP_Server/tools/plans.py` -- `generate_production_plan` output shape (plan dict with sections array)
- `.planning/phases/27-locator-and-scaffolding-commands/27-CONTEXT.md` -- D-02/D-03 track naming, D-06 MIDI only, D-14 device status deferred to Phase 28
- `.planning/phases/28-section-execution-and-quality-gate/28-CONTEXT.md` -- all locked decisions D-01 through D-06
- `tests/conftest.py` -- `_GAC_PATCH_TARGETS` list, `mock_connection` fixture, `mcp_server` fixture
- `tests/test_scaffold.py` -- existing test patterns, mock factory pattern

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all patterns established in Phase 27
- Architecture: HIGH -- extending existing handler + new MCP module follows established project patterns
- Pitfalls: HIGH -- backward compatibility concern is concrete and verifiable; dedup ordering is the only subtle logic

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable domain -- project internal patterns)
