# Architecture Patterns: v1.3 Arrangement Intelligence

**Domain:** Arrangement intelligence layer for Ableton MCP server
**Researched:** 2026-03-27
**Confidence:** HIGH (architecture follows established codebase patterns, LOM constraints verified)

## Recommended Architecture

### Overview

v1.3 adds three capabilities to the existing two-tier architecture:

1. **Extended genre blueprint data** -- arrangement templates with energy curves, per-section element maps, and automation cues (data layer, MCP_Server only)
2. **Production plan builder** -- server-side logic that combines genre blueprints + theory engine into actionable production plans (new module, MCP_Server only)
3. **Session scaffolding** -- Remote Script commands that write locators and arrangement clips into Ableton (new Remote Script commands + new MCP tools)

No new tiers, no new protocols. Everything flows through the existing TCP socket.

```
Claude (MCP Client)
    |
    | MCP protocol
    v
MCP_Server/
    tools/production.py     <-- NEW: plan + scaffold tools
    production/             <-- NEW: plan builder logic
        __init__.py
        planner.py          <-- plan generation from blueprint + vibe
        scaffold.py         <-- Ableton scaffolding orchestration
    genres/
        schema.py           <-- MODIFIED: extended ArrangementEntry
        house.py            <-- MODIFIED: enriched arrangement data
        ... (all 12 genres)
    tools/arrangement.py    <-- MODIFIED: new scaffolding tools
    |
    | TCP socket (localhost:9877)
    v
AbletonMCP_Remote_Script/
    handlers/arrangement.py <-- MODIFIED: locator + batch clip commands
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `MCP_Server/production/planner.py` | Generate production plans from genre + vibe + key | genres catalog, theory engine |
| `MCP_Server/production/scaffold.py` | Orchestrate Ableton scaffolding (locators, tracks, clips) | connection.py (sends commands) |
| `MCP_Server/tools/production.py` | MCP tool definitions for plan + scaffold | planner.py, scaffold.py |
| `handlers/arrangement.py` (extended) | New Remote Script commands for locators and batch ops | Ableton LOM (Song, Track, CuePoint) |

### What Is New vs. Modified

| File | Status | Changes |
|------|--------|---------|
| `MCP_Server/production/__init__.py` | **NEW** | Package init |
| `MCP_Server/production/planner.py` | **NEW** | Plan generation logic |
| `MCP_Server/production/scaffold.py` | **NEW** | Scaffolding orchestration |
| `MCP_Server/tools/production.py` | **NEW** | MCP tool definitions (4-6 tools) |
| `MCP_Server/genres/schema.py` | **MODIFIED** | Extended ArrangementEntry TypedDict |
| `MCP_Server/genres/*.py` (all 12) | **MODIFIED** | Enriched arrangement sections |
| `MCP_Server/genres/catalog.py` | **NO CHANGE** | Auto-discovery works as-is |
| `MCP_Server/tools/__init__.py` | **MODIFIED** | Add `production` to imports |
| `MCP_Server/connection.py` | **MODIFIED** | Add new commands to _WRITE_COMMANDS |
| `AbletonMCP_Remote_Script/handlers/arrangement.py` | **MODIFIED** | New locator + batch commands |
| `AbletonMCP_Remote_Script/handlers/__init__.py` | **NO CHANGE** | arrangement already imported |
| `tests/test_production.py` | **NEW** | Plan builder unit tests |
| `tests/test_arrangement_schema.py` | **NEW** | Extended schema validation tests |

## Data Flow

### 1. Plan Generation (server-side only, no Ableton)

```
Claude calls: generate_production_plan(genre="house", key="Am", vibe="dark minimal")
    |
    v
tools/production.py
    |-- genres.get_blueprint("house") --> full blueprint dict
    |-- planner.build_plan(blueprint, key, vibe)
    |       |-- reads blueprint["arrangement"]["sections"]
    |       |-- reads blueprint["instrumentation"]["roles"]
    |       |-- calls theory engine for key-resolved chords/scales
    |       |-- assembles per-section element checklist
    |       v
    |   returns ProductionPlan dict:
    |       {
    |         "genre": "house",
    |         "key": "Am",
    |         "tempo": 124,
    |         "sections": [
    |           {
    |             "name": "intro",
    |             "bars": 16,
    |             "start_beat": 0.0,
    |             "energy": 0.3,
    |             "elements": ["kick", "hi-hats", "pad"],
    |             "checklist": [
    |               {"element": "kick", "action": "four-on-the-floor, 127 vel"},
    |               {"element": "hi-hats", "action": "offbeat 8th closed"},
    |               {"element": "pad", "action": "Am7 sustained, LP 800Hz"},
    |             ],
    |             "automation_cues": ["filter LP sweep on pad"],
    |             "transition_to_next": "noise riser last 4 bars"
    |           },
    |           ...
    |         ],
    |         "tracks_needed": ["Kick", "Bass", "Hi-Hats", "Pad", ...],
    |       }
    v
Returned to Claude as JSON
```

### 2. Session Scaffolding (requires Ableton)

```
Claude calls: scaffold_arrangement(plan)
    |
    v
tools/production.py --> scaffold.py
    |
    |-- For each section in plan:
    |     send_command("create_locator", {time: start_beat, name: "INTRO"})
    |
    |-- For each track in plan.tracks_needed:
    |     send_command("create_midi_track", {name: "Kick"})
    |
    |-- set_tempo(plan.tempo)
    v
Returns: {locators_created: 7, tracks_created: 8, tempo_set: 124}
```

### 3. Section Execution (Claude drives, using existing tools)

```
Claude reads plan section[0] checklist:
    |-- create_arrangement_midi_clip(track=0, start=0.0, length=64.0)
    |-- add_notes_to_clip(...)    # existing tool
    |-- load_instrument_or_effect(...)  # existing tool
    |-- ...
    v
No new tools needed -- existing tools cover clip/note/device operations
```

## Critical LOM Constraint: Locator Creation

**CuePoint.time is READ-ONLY in the Ableton LOM.** You cannot set a locator's position directly. The only way to create a locator is:

1. Set `Song.current_song_time` to the desired position (read-write property)
2. Call `Song.set_or_delete_cue()` which toggles a cue point at the current position
3. Find the newly created CuePoint in `Song.cue_points` and set its `name`

This means locator creation requires a **sequential multi-step Remote Script command** rather than a simple single-call operation. The Remote Script handler must:

```python
@command("create_locator", write=True)
def _create_locator(self, params):
    time = params["time"]
    name = params["name"]

    # Check if locator already exists at this time
    for cp in self._song.cue_points:
        if abs(cp.time - time) < 0.01:
            cp.name = name  # Just rename existing
            return {"created": False, "renamed": True, "time": time, "name": name}

    # Save current position
    original_time = self._song.current_song_time

    # Move to target, create locator
    self._song.current_song_time = time
    self._song.set_or_delete_cue()

    # Find and name the new cue point
    for cp in self._song.cue_points:
        if abs(cp.time - time) < 0.01:
            cp.name = name
            break

    # Restore position
    self._song.current_song_time = original_time

    return {"created": True, "time": time, "name": name}
```

**Risk:** If a cue point already exists at that position, `set_or_delete_cue()` will DELETE it instead. The handler MUST check `Song.cue_points` first and skip creation if one already exists at that time (rename instead).

**Batch consideration:** Creating 7 locators means 7 position moves. A `scaffold_arrangement` command that does all at once on the Remote Script side avoids 7 round-trips over TCP.

Sources:
- [CuePoint LOM reference](https://docs.cycling74.com/apiref/lom/cuepoint/) -- confirms name is R/W, time is R/O
- [Song LOM reference](https://docs.cycling74.com/apiref/lom/song/) -- confirms set_or_delete_cue() toggles at current position

## Patterns to Follow

### Pattern 1: Blueprint Extension (Backward-Compatible)

The existing `ArrangementEntry` TypedDict has only `name` and `bars`. Extend it with **optional** fields so existing blueprints remain valid during migration:

```python
# schema.py -- BEFORE
class ArrangementEntry(TypedDict):
    name: str
    bars: int

# schema.py -- AFTER (two approaches, pick one)

# Approach A: Subclass with total=False
class ArrangementEntryV2(ArrangementEntry, total=False):
    """Extended arrangement entry with optional v1.3 fields."""
    energy: float           # 0.0-1.0, section energy level
    elements: list[str]     # which instrumentation roles are active
    automation_cues: list[str]  # automation hints for this section
    transition: str         # transition description to next section

# Approach B: Keep one class, validate optionals in validate_blueprint()
# (simpler, matches current validation style)
```

Use approach B (validate optionals in `validate_blueprint()`) because the existing codebase uses runtime validation, not TypedDict enforcement. The validator already hand-checks each field; adding optional field checks fits naturally.

**Why not a separate "arrangement_v2" key:** Breaks the clean one-key-per-dimension pattern. Extending the existing sections list is cleaner and the catalog/merger already handles it.

### Pattern 2: Production Module (Mirrors Theory/Genres Pattern)

Follow the same pattern as `MCP_Server/theory/` and `MCP_Server/genres/`:

- **Library module** (`production/planner.py`): Pure functions, no Ableton dependency, fully unit-testable
- **Orchestration module** (`production/scaffold.py`): Uses `connection.send_command()`, not directly testable without Ableton
- **Tool module** (`tools/production.py`): Thin wrappers that call library functions

This means `planner.py` can be tested with the same pattern as theory tests -- pure Python, no mocks needed.

### Pattern 3: Checklist-Driven Execution

The production plan includes per-section **checklists** -- ordered lists of elements to create. This addresses the stated goal of "nothing skipped under context pressure."

The checklist is **data, not automation**. Claude reads it and executes each item using existing tools. The plan builder generates it; Claude consumes it. This avoids building a complex automation engine while solving the "forgot the hi-hats" problem.

```python
# Example checklist entry
{
    "element": "kick",
    "action": "four-on-the-floor, 127 velocity, full section length",
    "track_name": "Kick",
    "priority": 1  # core elements first, flourishes last
}
```

### Pattern 4: Batch Commands for Scaffolding

Creating an arrangement scaffold involves many small operations (7 locators, 8 tracks). Rather than 15+ TCP round-trips, provide a batch scaffolding command on the Remote Script side:

```python
@command("scaffold_arrangement", write=True)
def _scaffold_arrangement(self, params):
    """Create locators and tracks for arrangement scaffolding.

    Params:
        locators: [{time, name}, ...]
        tracks: [{name, type}, ...]  # type: "midi" or "audio"
        tempo: float (optional)
    """
```

This is consistent with how the existing codebase handles compound operations (e.g., `add_notes_to_clip` accepts a list of notes).

## Anti-Patterns to Avoid

### Anti-Pattern 1: Putting Plan Logic in the Remote Script

**What:** Moving production plan generation into the Remote Script
**Why bad:** Remote Script runs in Ableton's embedded Python with no access to music21, no pip, limited stdlib. Theory engine is server-side only (established decision from v1.1).
**Instead:** All plan logic in `MCP_Server/production/`. Remote Script only handles LOM operations.

### Anti-Pattern 2: Separate Arrangement Data Files

**What:** Creating a separate `arrangements/` package parallel to `genres/`
**Why bad:** Arrangement data is inherently tied to genre conventions. Separating it creates sync issues and doubles the lookup logic.
**Instead:** Extend the existing `arrangement` section within each genre blueprint dict.

### Anti-Pattern 3: Auto-Executing Plans

**What:** A single tool that generates a plan AND scaffolds AND creates all clips
**Why bad:** Claude loses visibility, can't adapt mid-execution, can't handle errors per-element. Long-running single command will timeout (existing TIMEOUT_WRITE is 15s). Violates the "session IS the plan" philosophy.
**Instead:** Three-step workflow: (1) generate plan, (2) scaffold arrangement, (3) Claude executes section-by-section using existing tools.

### Anti-Pattern 4: Storing Plan State Server-Side

**What:** Keeping plan state in MCP server memory between tool calls
**Why bad:** MCP is stateless between tool invocations. Server may restart. Plan state would be lost.
**Instead:** Return the full plan to Claude. Claude holds it in context. Plan is pure data (JSON dict).

## Integration Points with Existing Architecture

### Genre Blueprints (existing, to be extended)

The plan builder reads from `genres.get_blueprint()` -- no new access pattern needed. The extended arrangement data flows through the existing catalog auto-discovery and subgenre merge. Subgenre arrangement overrides (like `progressive_house` already has) continue to work via shallow merge.

### Theory Engine (existing, no changes)

The plan builder calls theory functions to resolve chords/scales in the requested key:
- `generate_progression(key, numerals, scale_type)` -- for section chord sequences
- `get_scale_pitches(key, scale_name)` -- for melodic element hints
- `build_chord(root, quality)` -- for specific chord voicings

These are all existing functions in `MCP_Server/theory/`. No theory modifications needed.

### Existing Arrangement Tools (existing, no changes)

`create_arrangement_midi_clip`, `create_arrangement_audio_clip`, `get_arrangement_clips`, `duplicate_clip_to_arrangement` -- all continue to work unchanged. Claude uses these during section execution.

### Existing Transport/Cue Tools (existing, no changes)

`get_cue_points`, `set_or_delete_cue`, `jump_to_cue` -- already exist. The new `create_locator` command is a higher-level wrapper that handles the position-move-create-name dance. The existing tools remain for ad-hoc use.

## Schema Extension Detail

### Current ArrangementEntry

```python
{"name": "intro", "bars": 16}
```

### Extended ArrangementEntry (v1.3)

```python
{
    "name": "intro",
    "bars": 16,
    "energy": 0.3,
    "elements": ["kick", "hi-hats", "pad"],
    "automation_cues": ["filter LP sweep on pad"],
    "transition": "noise riser last 4 bars"
}
```

### Validation Strategy

The existing `validate_blueprint()` checks that each `arrangement.sections` entry has `name` (str) and `bars` (int). New fields are validated only if present:

```python
# In validate_blueprint(), after existing name/bars check on line 196:
if "energy" in entry:
    if not isinstance(entry["energy"], (int, float)):
        raise ValueError(f"arrangement.sections[{i}].energy must be numeric")
    if not (0.0 <= entry["energy"] <= 1.0):
        raise ValueError(f"arrangement.sections[{i}].energy must be 0.0-1.0")
if "elements" in entry:
    if not isinstance(entry["elements"], list):
        raise ValueError(f"arrangement.sections[{i}].elements must be a list")
if "automation_cues" in entry:
    if not isinstance(entry["automation_cues"], list):
        raise ValueError(f"arrangement.sections[{i}].automation_cues must be a list")
if "transition" in entry:
    if not isinstance(entry["transition"], str):
        raise ValueError(f"arrangement.sections[{i}].transition must be a string")
```

This is backward-compatible: blueprints without `energy`/`elements` pass validation. The plan builder treats missing fields as "use defaults from genre instrumentation roles."

### Token Budget Impact

Each genre blueprint is currently 537-670 tokens (per D-13 quality gate from v1.2). Adding 4 fields per section entry (~7 sections) adds roughly 150-200 tokens per genre. This keeps blueprints under ~850 tokens, well within acceptable limits. The plan builder output (returned to Claude, not stored in blueprints) is separate from blueprint token budget.

## New MCP Tools (tools/production.py)

| Tool | Purpose | Calls Ableton? |
|------|---------|----------------|
| `generate_production_plan` | Genre + key + vibe -> full plan with checklists | No |
| `generate_section_plan` | Single section plan for targeted work | No |
| `scaffold_arrangement` | Write locators + tracks into Ableton | Yes |
| `get_section_checklist` | Extract checklist for one section from a plan | No |

**Tool count:** 4 new tools (204 total). Consistent with project pattern of small, focused tools.

**Why `generate_section_plan` exists:** The PROJECT.md states "Either mode: full track end-to-end OR targeted single section." This tool generates a plan for just one section, useful when Claude is working on a specific part.

## New Remote Script Commands

| Command | Type | Purpose |
|---------|------|---------|
| `create_locator` | write | Create named locator at specific beat position |
| `delete_locator` | write | Delete locator at specific beat position |
| `scaffold_arrangement` | write | Batch create locators + tracks + set tempo |
| `get_arrangement_overview` | read | Return all locators + track names + total length |

**Why `get_arrangement_overview`:** Claude needs to understand the current state before scaffolding (avoid duplicating locators) and during execution (know which sections exist). This is a read command that composites data from `Song.cue_points`, track names, and `Song.song_length`.

## Suggested Build Order

### Phase 25: Blueprint Arrangement Extension

1. Extend `ArrangementEntry` TypedDict with optional fields
2. Update `validate_blueprint()` for new optional fields
3. Enrich all 12 genre blueprints with energy/elements/automation data
4. Tests: schema validation, backward compat, enriched data

**Rationale:** Data-only, no Ableton needed, no new modules. Foundation for everything else. Mirrors Phase 20 (Blueprint Infrastructure) in scope.

### Phase 26: Production Plan Builder

1. Create `MCP_Server/production/` package
2. Implement `planner.py` -- plan generation logic
3. Create `tools/production.py` -- `generate_production_plan` + `generate_section_plan`
4. Tests: plan generation with various genres/keys/vibes

**Rationale:** Server-side only, pure Python, fully testable. Depends on Phase 25 for enriched data. Mirrors Phase 21 (Blueprint Tools) in scope.

### Phase 27: Locator and Scaffolding Commands

1. Add `create_locator`, `delete_locator`, `get_arrangement_overview` to Remote Script `handlers/arrangement.py`
2. Add `scaffold_arrangement` batch command to Remote Script
3. Add MCP tool wrappers in `tools/production.py` or `tools/arrangement.py`
4. Update `connection.py` with new write commands
5. Tests: unit tests for scaffold logic, integration notes for Remote Script

**Rationale:** Requires Ableton for integration testing. Depends on Phase 26 for plan structure that scaffolding consumes.

### Phase 28: Section Execution and Quality Gate

1. Add `get_section_checklist` tool
2. End-to-end workflow validation
3. Verify full workflow: plan -> scaffold -> execute section checklists
4. Quality gate: full arrangement from blueprint to Ableton

**Rationale:** Integration phase. Everything comes together. Mirrors Phase 24 (Quality Gate) in scope.

**Phase ordering rationale:**
- Phase 25 before 26: Plan builder needs enriched arrangement data to generate meaningful checklists
- Phase 26 before 27: Scaffolding needs plan structure to know what locators/tracks to create
- Phase 27 before 28: Section execution needs locators/tracks in Ableton
- Each phase is independently shippable and testable

## Scalability Considerations

| Concern | Current (12 genres) | At 30 genres | At 100 genres |
|---------|---------------------|--------------|---------------|
| Blueprint size | ~600-850 tokens/genre | Same per genre | Same per genre |
| Plan generation time | <50ms | <50ms | <50ms |
| Scaffold time (7 locators) | ~1s (7 TCP round-trips) | Same | Same |
| Scaffold time (batch) | ~200ms (1 TCP call) | Same | Same |

No scalability concerns. Plan generation is pure computation. Scaffolding is bounded by section count (typically 5-9 sections per genre), not genre count.

## Sources

- [CuePoint LOM reference](https://docs.cycling74.com/apiref/lom/cuepoint/) -- CuePoint.name R/W, CuePoint.time R/O
- [Song LOM reference](https://docs.cycling74.com/apiref/lom/song/) -- Song.cue_points, set_or_delete_cue(), current_song_time R/W
- [Live Object Model overview](https://docs.cycling74.com/legacy/max8/vignettes/live_object_model) -- LOM hierarchy and class relationships
- Existing codebase: `MCP_Server/genres/schema.py` (current TypedDict + validation), `MCP_Server/genres/catalog.py` (auto-discovery + merge), `AbletonMCP_Remote_Script/handlers/arrangement.py` (existing arrangement commands), `AbletonMCP_Remote_Script/handlers/transport.py` (existing cue point commands), `MCP_Server/connection.py` (timeout/command classification)

---
*Architecture research for: v1.3 Arrangement Intelligence*
*Researched: 2026-03-27*
