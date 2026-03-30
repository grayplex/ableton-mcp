# Phase 27: Locator and Scaffolding Commands - Research

**Researched:** 2026-03-27
**Domain:** Ableton Live API (cue points, tracks), MCP tool layer, production plan consumption
**Confidence:** HIGH

## Summary

Phase 27 delivers two MCP tools that bridge the pure-computation production plan (Phase 26) with the live Ableton session. `scaffold_arrangement` writes locators and MIDI tracks into Ableton, while `get_arrangement_overview` reads them back. Both require socket calls to Ableton via the existing `send_command` infrastructure.

The critical technical finding is the locator creation approach: Ableton's Live API has no direct "create cue point at position X" method. Instead, the established pattern is to (1) set `song.current_song_time` to the target beat position, then (2) call `song.set_or_delete_cue()` to create the locator at that position, then (3) set `cue_point.name` on the newly created cue point. In Live 12, `CuePoint.name` is now settable (it was read-only in Live 11 and earlier). The project targets Live 12, so this approach is viable.

**Primary recommendation:** Create a new Remote Script handler file `scaffold.py` with commands `create_locator_at` (set playhead + toggle cue + rename) and `get_arrangement_state` (read all cue points, tracks, song length, time signature). Create a new MCP tool file `scaffold.py` that orchestrates multiple socket calls for `scaffold_arrangement` and a single call for `get_arrangement_overview`.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Track names use bare role names from the plan's role list (e.g. "kick", "bass", "lead", "pad").
- **D-02:** When the same role string appears in multiple sections (implying different sounds), tracks are numbered with a plain suffix: "lead", "lead 2", "lead 3". No section prefix. Numbering is automatic and deterministic.
- **D-03:** Deduplication is by role name string. If "lead" appears 3 times across sections, create 3 tracks: "lead", "lead 2", "lead 3".
- **D-04:** Create one shared MIDI track per unique role occurrence (per D-02/D-03), using the deduplicated union of all roles across all sections. All tracks are created in one pass.
- **D-05:** No `section_filter` parameter.
- **D-06:** All scaffold-created tracks are MIDI tracks.
- **D-07:** One locator per section, named by section name, placed at beat position derived from `bar_start`.
- **D-08:** Bar-to-beat conversion: `beat_position = (bar_start - 1) * beats_per_bar`, where `beats_per_bar = numerator * (4.0 / denominator)`.
- **D-09:** `scaffold_arrangement` reads the session time signature internally via `get_session_info` socket call.
- **D-10:** `scaffold_arrangement` accepts raw plan JSON dict (output of `generate_production_plan`). Two-tool workflow.
- **D-11:** Expected input shape: `sections` array from the plan, each entry with `name`, `bar_start`, `bars`, `roles` keys.
- **D-12:** `get_arrangement_overview` returns `{locators: [{name, bar}], tracks: [string], session_length_bars: int}`.
- **D-13:** `locators[].bar` is 1-indexed. Conversion: `bar = floor(beat_position / beats_per_bar) + 1`.
- **D-14:** `tracks` is a flat list of track names (strings).
- **D-15:** `session_length_bars` from `song.song_length` / `beats_per_bar`.

### Claude's Discretion
- Whether to place scaffold/overview tools in a new `MCP_Server/tools/scaffold.py` or extend `plans.py`. **Recommendation:** New file `scaffold.py` -- clean separation between pure-computation (plans.py, no socket) and Ableton-connected (scaffold.py, socket calls).
- Whether to add locator creation commands to `transport.py` or a new handler file. **Recommendation:** New `AbletonMCP_Remote_Script/handlers/scaffold.py` -- keeps transport handlers focused on playback/navigation.
- How to handle partial failure mid-scaffold. **Recommendation:** Report what was created and the error; do not attempt rollback.
- Which Live API method for positional locator creation. **Finding:** Use `song.current_song_time = beat_pos` + `song.set_or_delete_cue()` + `cue_point.name = name` (see Architecture Patterns below).

### Deferred Ideas (OUT OF SCOPE)
- Default instrument loading per role on scaffold tracks
- `section_filter` param on scaffold
- Track type or instrument status in `get_arrangement_overview`
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCAF-01 | User can scaffold a full arrangement into Ableton -- creates all named locators and named tracks in Arrangement view from a production plan in one atomic operation | Locator creation via playhead positioning + set_or_delete_cue + CuePoint.name (Live 12); MIDI track creation via existing `create_midi_track` + `set_track_name` handlers; new `scaffold.py` handler + tool files |
| SCAF-02 | User can retrieve an arrangement overview -- returns locators (with positions), track names, and session length for mid-session re-orientation | New `get_arrangement_state` handler reads `song.cue_points`, `song.tracks`, `song.song_length`, `song.signature_numerator/denominator`; MCP tool converts beat positions to 1-indexed bars |
</phase_requirements>

## Architecture Patterns

### Recommended Project Structure

New files only (no modifications to existing files except registration):
```
AbletonMCP_Remote_Script/
  handlers/
    __init__.py           # ADD: import scaffold
    scaffold.py           # NEW: create_locator_at, scaffold_tracks, get_arrangement_state
MCP_Server/
  tools/
    __init__.py           # ADD: import scaffold
    scaffold.py           # NEW: scaffold_arrangement, get_arrangement_overview
  connection.py           # ADD: new commands to _WRITE_COMMANDS set
tests/
  test_scaffold.py        # NEW: scaffold tool tests
```

### Pattern 1: Locator Creation via Playhead Positioning (Live 12)

**What:** Create a named locator at a specific beat position without user interaction.
**When to use:** Any time a locator needs to be placed at a computed position.
**Confidence:** HIGH -- verified via AbletonOSC documentation (which uses the same Live API) and Cycling '74 forum confirmation that CuePoint.name is settable in Live 12.

```python
# In AbletonMCP_Remote_Script/handlers/scaffold.py
@command("create_locator_at", write=True)
def _create_locator_at(self, params):
    """Create a named locator at a specific beat position."""
    beat_position = params["beat_position"]
    name = params["name"]

    # Save current position to restore after
    original_position = self._song.current_song_time

    # Move playhead to target position
    self._song.current_song_time = beat_position

    # Create cue point at current playhead position
    self._song.set_or_delete_cue()

    # Find the newly created cue point and set its name
    # Cue points are sorted by time; find the one at our position
    for cp in self._song.cue_points:
        if abs(cp.time - beat_position) < 0.001:
            cp.name = name
            break

    # Restore playhead
    self._song.current_song_time = original_position

    return {"name": name, "beat_position": beat_position}
```

**Critical edge case:** `set_or_delete_cue()` is a toggle. If a cue already exists at that exact position, it will be DELETED instead of created. The scaffold should either (a) check existing cue points first and skip positions that already have one, or (b) document this as a known limitation. Recommendation: check first, skip if exists, include in response.

### Pattern 2: Batch Track Creation

**What:** Create multiple MIDI tracks in one handler call to minimize round-trips.
**When to use:** Scaffold needs to create 5-15 tracks efficiently within the 15-second timeout.

```python
# In AbletonMCP_Remote_Script/handlers/scaffold.py
@command("scaffold_tracks", write=True)
def _scaffold_tracks(self, params):
    """Create multiple named MIDI tracks in one operation."""
    track_names = params["track_names"]  # list of strings
    created = []
    for name in track_names:
        index = len(self._song.tracks)  # append at end
        self._song.create_midi_track(-1)
        new_track = self._song.tracks[len(self._song.tracks) - 1]
        new_track.name = name
        created.append({"index": len(self._song.tracks) - 1, "name": name})
    return {"created_tracks": created, "count": len(created)}
```

### Pattern 3: MCP Tool Orchestrating Multiple Socket Calls

**What:** The MCP tool layer makes multiple `send_command` calls in sequence.
**When to use:** `scaffold_arrangement` needs: get session info, create locators, create tracks.

```python
# In MCP_Server/tools/scaffold.py
@mcp.tool()
def scaffold_arrangement(ctx: Context, plan: dict) -> str:
    """Scaffold an arrangement into Ableton from a production plan."""
    try:
        ableton = get_ableton_connection()

        # 1. Get session time signature
        session = ableton.send_command("get_session_info")
        numerator = session["signature_numerator"]
        denominator = session["signature_denominator"]
        beats_per_bar = numerator * (4.0 / denominator)

        # 2. Create locators for each section
        sections = plan["sections"]
        locators_created = []
        for section in sections:
            beat_pos = (section["bar_start"] - 1) * beats_per_bar
            result = ableton.send_command("create_locator_at", {
                "beat_position": beat_pos,
                "name": section["name"],
            })
            locators_created.append(result)

        # 3. Deduplicate roles and create tracks
        track_names = _deduplicate_roles(sections)
        tracks_result = ableton.send_command("scaffold_tracks", {
            "track_names": track_names,
        })

        return json.dumps({
            "locators_created": len(locators_created),
            "tracks_created": tracks_result["count"],
            "track_names": track_names,
        })
    except Exception as e:
        return format_error(...)
```

### Pattern 4: Role Deduplication Algorithm (D-02, D-03)

**What:** Deterministic naming: count each role across all sections, generate suffixed names.
**When to use:** Before creating tracks in scaffold.

```python
def _deduplicate_roles(sections: list[dict]) -> list[str]:
    """Build deduplicated track name list from plan sections.

    Each unique role string gets one track. If a role appears N times
    across all sections, N tracks are created: "role", "role 2", "role 3".
    """
    from collections import Counter
    role_counts = Counter()
    for section in sections:
        for role in section.get("roles", []):
            role_counts[role] += 1

    track_names = []
    for role, count in role_counts.items():
        track_names.append(role)
        for i in range(2, count + 1):
            track_names.append(f"{role} {i}")
    return track_names
```

### Anti-Patterns to Avoid
- **Making one socket call per track creation:** Would cause N round-trips for N tracks. Use a batch `scaffold_tracks` handler instead that creates all tracks in one call.
- **Using individual `create_midi_track` + `set_track_name` MCP calls:** Would be 2N round-trips. The scaffold MCP tool should use bulk Remote Script commands.
- **Assuming `set_or_delete_cue()` always creates:** It toggles. Must check if a cue already exists at the target position.
- **Not restoring playhead position:** Moving `current_song_time` for locator creation moves the user's playhead. Must save and restore.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Track creation | Custom track-creation logic | Existing `song.create_midi_track()` API | Already proven in handlers/tracks.py |
| Socket communication | New protocol/connection | Existing `ableton.send_command()` | Handles timeouts, reconnection, framing |
| Error formatting | Custom error strings | `format_error()` from connection.py | Consistent AI-readable format |
| Time signature reading | Manual property access | Existing `get_session_info` handler | Already returns numerator/denominator |

## Common Pitfalls

### Pitfall 1: set_or_delete_cue Toggle Behavior
**What goes wrong:** Calling `set_or_delete_cue()` at a position that already has a cue point DELETES it instead of creating a new one.
**Why it happens:** The API is a toggle, not an idempotent create.
**How to avoid:** Before creating each locator, check if `song.cue_points` already contains one at that beat position (within a small epsilon). Skip creation if one exists; optionally rename the existing one.
**Warning signs:** Running scaffold twice removes all locators instead of being a no-op.

### Pitfall 2: Timeout from Too Many Round-Trips
**What goes wrong:** Creating 7 locators + 12 tracks with individual socket calls takes >15 seconds.
**Why it happens:** Each `send_command` has socket overhead. At ~200ms per call, 19 calls = ~4 seconds. But with connection validation, it could be worse.
**How to avoid:** Batch track creation into a single handler call. Locator creation cannot be easily batched (each needs playhead positioning), but 7 calls is manageable. Total: ~10 calls for a typical arrangement.
**Warning signs:** Timeout errors on larger arrangements (10+ sections, 20+ roles).

### Pitfall 3: Playhead Position Not Restored
**What goes wrong:** After scaffold, the user's playhead is at the position of the last created locator instead of where it was.
**Why it happens:** `create_locator_at` modifies `song.current_song_time`.
**How to avoid:** Save `current_song_time` before the loop, restore after all locators are created.
**Warning signs:** User reports playhead jumping after scaffold.

### Pitfall 4: CuePoint Name Assignment Race Condition
**What goes wrong:** After calling `set_or_delete_cue()`, the cue_points list may not be immediately updated, or the new cue point may not be findable by position.
**Why it happens:** Ableton's internal state update may be asynchronous relative to the Python API.
**How to avoid:** Access `song.cue_points` immediately after `set_or_delete_cue()` within the same `write=True` handler. Since write handlers run on Ableton's main thread, the state should be consistent. If not, a small defensive retry or sorting-based lookup can help.
**Warning signs:** Locators created but unnamed.

### Pitfall 5: Role Counter Ordering Non-Determinism
**What goes wrong:** `Counter` iteration order in Python 3.7+ follows insertion order, but if roles appear in different orders across sections, the "lead 2" vs "lead 3" assignment could vary.
**Why it happens:** Counter preserves first-seen order, not alphabetical order.
**How to avoid:** This is actually fine per D-02 -- numbering is automatic and deterministic based on the order roles appear in the plan's sections list. Document that ordering follows the plan's section order.
**Warning signs:** None if plan order is stable (which it is, since blueprints have fixed section order).

### Pitfall 6: Forgetting to Register New Commands
**What goes wrong:** New handler commands are not dispatched; socket calls fail with "unknown command".
**Why it happens:** Missing registration in `_WRITE_COMMANDS` (connection.py), `handlers/__init__.py`, or `tools/__init__.py`.
**How to avoid:** Registration checklist: (1) handler file imported in `handlers/__init__.py`, (2) handler class mixed into AbletonMCP, (3) command names added to `_WRITE_COMMANDS` in `connection.py`, (4) tool file imported in `tools/__init__.py`.
**Warning signs:** "Unknown command" or timeout errors.

## Code Examples

### Existing Pattern: MCP Tool with Socket Call
Source: `MCP_Server/tools/transport.py`
```python
@mcp.tool()
def get_cue_points(ctx: Context) -> str:
    """Get all cue points in the song."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_cue_points")
        return json.dumps(result, indent=2)
    except Exception as e:
        return format_error("Failed to get cue points", detail=str(e),
                          suggestion="Verify connection with get_connection_status")
```

### Existing Pattern: Write Handler Registration
Source: `AbletonMCP_Remote_Script/handlers/tracks.py`
```python
@command("create_midi_track", write=True)
def _create_midi_track(self, params):
    """Create a new MIDI track at the specified index."""
    index = params.get("index", -1)
    self._song.create_midi_track(index)
    new_track_index = len(self._song.tracks) - 1 if index == -1 else index
    new_track = self._song.tracks[new_track_index]
    return {"index": new_track_index, "name": new_track.name, "type": "midi"}
```

### Existing Pattern: get_session_info (time signature source)
Source: `AbletonMCP_Remote_Script/handlers/base.py`
```python
@command("get_session_info")
def _get_session_info(self, params=None):
    result = {
        "tempo": self._song.tempo,
        "signature_numerator": self._song.signature_numerator,
        "signature_denominator": self._song.signature_denominator,
        "track_count": len(self._song.tracks),
        ...
    }
    return result
```

### Existing Pattern: Test with mock_connection
Source: `tests/test_transport.py`
```python
async def test_set_tempo_calls_send_command(mcp_server, mock_connection):
    mock_connection.send_command.return_value = {"tempo": 140.0}
    result = await mcp_server.call_tool("set_tempo", {"tempo": 140.0})
    text = result[0][0].text
    assert "140" in text
    mock_connection.send_command.assert_called_once_with("set_tempo", {"tempo": 140.0})
```

### Plan Tool Direct-Call Test Pattern (no socket, no mcp)
Source: `tests/test_plan_tools.py`
```python
# Mock mcp module so @mcp.tool() is passthrough, then call function directly
def test_full_plan_house_basic(self):
    result = generate_production_plan(ctx=None, genre="house", key="Am", bpm=125)
    plan = json.loads(result)
    assert plan["genre"] == "house"
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | Standard (no pytest.ini detected) |
| Quick run command | `python -m pytest tests/test_scaffold.py -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCAF-01 | scaffold_arrangement creates locators and tracks from plan | unit (mock socket) | `python -m pytest tests/test_scaffold.py::TestScaffoldArrangement -x` | Wave 0 |
| SCAF-01 | Role deduplication produces correct track names (D-02/D-03) | unit (pure function) | `python -m pytest tests/test_scaffold.py::TestRoleDeduplication -x` | Wave 0 |
| SCAF-01 | Bar-to-beat conversion matches formula (D-08) | unit (pure function) | `python -m pytest tests/test_scaffold.py::TestBarToBeat -x` | Wave 0 |
| SCAF-01 | scaffold_arrangement tool is registered in MCP server | unit | `python -m pytest tests/test_scaffold.py::test_scaffold_tools_registered -x` | Wave 0 |
| SCAF-02 | get_arrangement_overview returns locators with 1-indexed bars | unit (mock socket) | `python -m pytest tests/test_scaffold.py::TestArrangementOverview -x` | Wave 0 |
| SCAF-02 | get_arrangement_overview returns flat track name list | unit (mock socket) | `python -m pytest tests/test_scaffold.py::TestArrangementOverview -x` | Wave 0 |
| SCAF-02 | session_length_bars conversion is correct (D-15) | unit (pure function) | `python -m pytest tests/test_scaffold.py::TestBarConversions -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_scaffold.py -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_scaffold.py` -- covers SCAF-01, SCAF-02 (all test classes above)
- [ ] Add `"MCP_Server.tools.scaffold.get_ableton_connection"` to `_GAC_PATCH_TARGETS` in `tests/conftest.py`

## Open Questions

1. **CuePoint.name timing after set_or_delete_cue()**
   - What we know: In Live 12, `CuePoint.name` is settable. `set_or_delete_cue()` creates at current playhead.
   - What's unclear: Whether `song.cue_points` list is immediately updated in the same handler call, or if there's a frame delay.
   - Recommendation: Implement optimistically (access immediately). If testing reveals a delay, add a small `schedule_message` callback. The `write=True` handler runs on main thread, so immediate access should work.

2. **Track index stability during batch creation**
   - What we know: `create_midi_track(-1)` appends. `song.tracks` updates immediately.
   - What's unclear: Whether rapid sequential creation within one handler call causes index drift.
   - Recommendation: After each `create_midi_track(-1)`, access `song.tracks[len(song.tracks) - 1]` for the new track. This is the existing pattern in `tracks.py`.

## Sources

### Primary (HIGH confidence)
- `AbletonMCP_Remote_Script/handlers/transport.py` -- existing cue point handlers, `set_or_delete_cue`, `get_cue_points`
- `AbletonMCP_Remote_Script/handlers/tracks.py` -- existing `create_midi_track` handler pattern
- `AbletonMCP_Remote_Script/handlers/base.py` -- `get_session_info` returning `signature_numerator/denominator`
- `MCP_Server/tools/plans.py` -- plan output shape consumed by scaffold
- `MCP_Server/connection.py` -- `send_command`, `format_error`, `_WRITE_COMMANDS`, timeout constants

### Secondary (MEDIUM confidence)
- [AbletonOSC README](https://github.com/ideoforms/AbletonOSC/blob/master/README.md) -- confirms `current_song_time` is settable, `set_or_delete_cue` creates at playhead, cue point name is settable
- [Cycling '74 Forum: Setting Locator Names](https://cycling74.com/forums/setting-locator-names) -- confirms CuePoint.name is writable in Live 12

### Tertiary (LOW confidence)
- None -- all critical findings verified through at least two sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- uses only existing project infrastructure (no new libraries)
- Architecture: HIGH -- follows established handler + tool patterns from 26 prior phases
- Pitfalls: HIGH -- toggle behavior documented in existing code; timeout constraints are measurable
- Locator API: MEDIUM -- playhead-positioning approach confirmed by AbletonOSC and community, but not tested in this codebase yet

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable domain -- Ableton Live API changes only with major releases)
