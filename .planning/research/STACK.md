# Technology Stack: v1.3 Arrangement Intelligence

**Project:** Ableton MCP v1.3
**Researched:** 2026-03-27

## Recommended Stack

### No New External Dependencies

v1.3 requires **zero new pip packages**. All arrangement intelligence features are pure Python logic (template data, plan builders, checklist generators) served through existing FastMCP tools, backed by existing Ableton LOM commands. This continues the v1.2 pattern: new internal modules, no new external deps.

**Rationale:** Arrangement templates are data (Python dicts extending genre blueprints). Production plans are computed from that data. Session scaffolding uses existing Ableton LOM APIs. No new computational domain (unlike v1.1 which needed music21 for theory).

### Existing Stack (unchanged)

| Technology | Version | Purpose | Status for v1.3 |
|------------|---------|---------|-----------------|
| Python | 3.10+ (host), 3.11 (Ableton) | Runtime | Unchanged |
| mcp[cli] | >=1.3.0 | MCP server framework (FastMCP) | Unchanged |
| music21 | >=9.0 | Theory engine backend | Unchanged (not directly used by v1.3) |
| pytest | >=8.3 | Testing | Unchanged |
| ruff | >=0.15.6 | Linting | Unchanged |

### New Internal Modules (no external deps)

| Module | Purpose | Dependencies |
|--------|---------|--------------|
| `MCP_Server/arrangement/` | Arrangement intelligence package | Python stdlib only |
| `MCP_Server/arrangement/__init__.py` | Package init | None |
| `MCP_Server/arrangement/templates.py` | Arrangement template builder (genre data + energy curves + per-section elements) | `MCP_Server/genres/` |
| `MCP_Server/arrangement/planner.py` | Production plan builder (genre + vibe -> section plan) | `arrangement/templates.py` |
| `MCP_Server/arrangement/checklist.py` | Section execution checklist generator | `arrangement/planner.py` |
| `MCP_Server/tools/arrangement_intelligence.py` | New MCP tool wrappers for v1.3 features | `arrangement/`, `mcp` |

**Note:** The existing `MCP_Server/tools/arrangement.py` (4 Ableton arrangement clip tools) and `AbletonMCP_Remote_Script/handlers/arrangement.py` (4 handlers) remain unchanged. v1.3 adds intelligence on top, not replacement.

## Ableton LOM APIs Needed

### Already Available (existing v1.0 handlers)

These APIs are already implemented and sufficient for v1.3 scaffolding:

| API | Handler | MCP Tool | v1.3 Use |
|-----|---------|----------|----------|
| `Song.cue_points` (get) | `get_cue_points` | `get_cue_points` | Read back locators after creation |
| `Song.set_or_delete_cue()` | `set_or_delete_cue` | `set_or_delete_cue` | Create locators (toggle at position) |
| `Song.current_song_time` (get/set) | `get_playback_position` | `get_playback_position` | Position cursor before creating cue |
| `Song.jump_by()` | `jump_by` | `jump_by` | Navigate to specific beat positions |
| `Track.name` (get/set) | `rename_track` | `rename_track` | Name tracks per arrangement role |
| `Track.color_index` (set) | `set_track_color` | `set_track_color` | Color-code tracks by section role |
| `Track.create_midi_clip()` | `create_arrangement_midi_clip` | `create_arrangement_midi_clip` | Place section clips |
| `Song.create_midi_track()` | `create_midi_track` | `create_midi_track` | Create tracks for arrangement |
| `Song.create_audio_track()` | `create_audio_track` | `create_audio_track` | Create audio tracks |

### New Remote Script Handlers Needed

| Handler | LOM API | Purpose | Confidence |
|---------|---------|---------|------------|
| `create_cue_at_position` | `Song.current_song_time` (set) + `Song.set_or_delete_cue()` | Create a named locator at a specific beat position without moving playback | HIGH |
| `set_cue_name` | `CuePoint.name` (set) | Rename a cue point/locator. **Live 12 confirmed writable** (was read-only pre-Live 12) | HIGH |
| `delete_all_cues` | iterate `Song.cue_points` + `Song.set_or_delete_cue()` | Clear all existing locators before scaffolding | MEDIUM |

**Critical finding — CuePoint.name is now writable in Live 12:**
- Pre-Live 12: `CuePoint.name` was read-only (get + observe only)
- Live 12+: `CuePoint.name` is writable via `set name` (confirmed by [Cycling74 forum](https://cycling74.com/forums/setting-locator-names))
- This is essential for v1.3 — locators must be named ("Intro", "Drop 1", etc.) to serve as visual section markers
- The LOM reference (Max 9 PDF, page 56) lists `name` as `symbol` type with observe access; the writable change was added in Live 12

**Locator creation pattern (workaround for LOM limitation):**
The LOM has no `create_cue_at_time(time, name)` method. `Song.set_or_delete_cue()` toggles at the current `Song.current_song_time`. The workaround is:
1. Store current `Song.current_song_time`
2. Set `Song.current_song_time` to target beat position
3. Call `Song.set_or_delete_cue()` to create the cue
4. Set `CuePoint.name` on the newly created cue
5. Restore original `Song.current_song_time`

This must be a single atomic Remote Script handler (not multiple MCP tool calls) to avoid race conditions and ensure the name is set on the correct cue point.

### APIs NOT Needed

| API | Why Not |
|-----|---------|
| `Clip.move_notes()` | v1.3 scaffolds structure, not note content |
| Session-to-arrangement recording | Arrangement clips are created directly |
| `Song.tempo_automation` | v1.3 uses single tempo per track |
| Max for Live devices | Remote Script API is sufficient |
| `Song.create_scene()` | Working in arrangement view, not session |

## Genre Blueprint Schema Extensions

The existing `ArrangementEntry` TypedDict (`{name: str, bars: int}`) needs expansion for v1.3. The new fields provide the data that production plans and checklists consume.

### Current Schema (v1.2)

```python
class ArrangementEntry(TypedDict):
    name: str   # "intro", "drop", etc.
    bars: int   # 16, 32, etc.
```

### Extended Schema (v1.3)

```python
class ArrangementEntry(TypedDict):
    name: str           # Section name: "intro", "drop", "breakdown"
    bars: int           # Bar count: 16, 32
    energy: float       # Energy level 0.0-1.0 (for energy curve)
    elements: List[str] # Active instrument roles: ["kick", "hi-hats", "pad"]
    automation_cues: List[str]  # Automation hints: ["filter_sweep_up", "reverb_swell"]
```

**Backward compatibility:** Extend the existing schema with optional fields defaulting sensibly. Validation (`validate_blueprint`) adds checks for new fields when present. Existing v1.2 blueprints remain valid; v1.3 enriches them incrementally.

**Token budget impact:** Each section gains ~3-5 additional tokens (energy float, 3-5 element strings, 1-2 automation cues). For a 7-section arrangement, this adds roughly 25-40 tokens. The v1.2 budget ceiling of 670 tokens per blueprint should expand to ~750 tokens max. Still well within context limits.

## MCP Protocol Patterns for Stateful Workflows

### What v1.3 Does NOT Need

| Pattern | Why Not Needed |
|---------|----------------|
| MCP Tasks (async/polling) | Scaffolding is synchronous — create tracks + cues in sequence, done |
| MCP Sampling (server-initiated LLM calls) | Plan generation is deterministic from template data |
| MCP Elicitation (user input during workflow) | User provides genre + vibe upfront; no mid-workflow decisions |
| Server-side session state | Plans are returned as data; the AI assistant holds workflow state |
| WebSocket streaming | All operations are request/response |

### What v1.3 DOES Need

**Composite tools that return structured plans as data:**

The v1.3 tools are "plan generators" — they take inputs (genre, vibe, mode) and return structured JSON that the AI assistant then executes step-by-step using existing v1.0 tools. This is the correct MCP pattern for multi-step workflows: the server provides intelligence, the client (Claude) provides execution.

```
AI calls: get_production_plan(genre="house", vibe="dark", mode="full")
Server returns: { sections: [...], tracks: [...], locators: [...] }
AI then executes: create_midi_track() x N, create_cue_at_position() x N, etc.
```

**Scaffold-in-one tool (optional optimization):**

A single `scaffold_arrangement` tool that creates all tracks + locators in one Remote Script round-trip. This avoids N separate socket calls and is faster. The trade-off is less granular undo (one undo undoes the entire scaffold vs. one track at a time).

**Recommendation:** Provide both patterns:
1. `get_production_plan` — returns the plan as data (Claude executes piece by piece)
2. `scaffold_arrangement` — executes the plan server-side in one call (fast, atomic)

Claude should prefer `scaffold_arrangement` for full-track mode and `get_production_plan` for targeted single-section mode where it needs finer control.

## Alternatives Considered

| Decision | Chosen | Alternative | Why Not |
|----------|--------|-------------|---------|
| Arrangement data format | Extend existing Python dicts in genre blueprints | Separate JSON/YAML arrangement files | Blueprints already have arrangement sections; extending is simpler and keeps data co-located |
| Plan builder location | Server-side Python module | Client-side (Claude prompt engineering only) | Server-side ensures consistent plans; Claude's knowledge of genre conventions is unreliable under context pressure |
| Checklist format | Structured JSON returned by tool | Markdown text returned by tool | JSON is parseable; Claude can track completion state; Markdown is ambiguous |
| Locator creation | Atomic Remote Script handler | Sequence of MCP tool calls (jump, toggle cue, rename) | Race conditions: playback could move between calls; atomicity is essential |
| State management | Stateless tools (plan = pure data) | Server-side session tracking | Unnecessary complexity; the AI assistant is the natural state holder in MCP |
| New external library for templates | None (pure Python logic) | Jinja2 for template rendering | Templates are data structures, not text; Jinja2 is for text templating |
| New external library for validation | None (extend existing validate_blueprint) | Pydantic for schema validation | Existing TypedDict + validate_blueprint pattern works; adding Pydantic for 3 new fields is overkill |

## What NOT to Add

| Do Not Add | Reason |
|------------|--------|
| Pydantic | Existing TypedDict validation is sufficient for dict schemas |
| Jinja2 | Arrangement templates are data structures, not text templates |
| Any state management library | MCP is stateless by design; AI holds workflow state |
| Any async framework beyond existing anyio | All arrangement operations are synchronous |
| Any database (SQLite, etc.) | Plans are computed on-the-fly, not persisted |
| tiktoken (for v1.3) | Token budget measurement was a v1.2 dev-only concern; v1.3 enrichments are small enough to eyeball |

## Package Configuration Changes

```toml
# pyproject.toml — add to existing [tool.setuptools] packages list
packages = [
    "MCP_Server",
    "MCP_Server.tools",
    "MCP_Server.theory",
    "MCP_Server.genres",
    "MCP_Server.arrangement",  # NEW for v1.3
]
```

No new entries in `[project.dependencies]`.

## Sources

- [Cycling74 LOM Reference (Max 9 PDF)](https://cycling74-docs-production.nyc3.cdn.digitaloceanspaces.com/pdfs/9.0.7-rev.1/Max9-LOM-en.pdf) — CuePoint class: page 56, Song class: pages 126-140 (HIGH confidence)
- [Cycling74 Forum: Setting Locator Names](https://cycling74.com/forums/setting-locator-names) — Confirms CuePoint.name is writable in Live 12 (HIGH confidence)
- [Cycling74 LOM Documentation (Max 8)](https://docs.cycling74.com/legacy/max8/vignettes/live_object_model) — Song.cue_points, set_or_delete_cue (HIGH confidence)
- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — Protocol patterns, stateless tool design (HIGH confidence)
- Existing codebase: `AbletonMCP_Remote_Script/handlers/transport.py` — current cue point implementation (HIGH confidence, direct code review)
- Existing codebase: `MCP_Server/genres/schema.py` — current ArrangementEntry TypedDict (HIGH confidence, direct code review)
- Existing codebase: `MCP_Server/tools/arrangement.py` — current arrangement tools (HIGH confidence, direct code review)

---
*Stack research for: v1.3 Arrangement Intelligence*
*Researched: 2026-03-27*
