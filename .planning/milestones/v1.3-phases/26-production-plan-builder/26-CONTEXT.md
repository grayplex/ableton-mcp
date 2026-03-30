# Phase 26: Production Plan Builder - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver two new MCP tools — `generate_production_plan` and `generate_section_plan` — that take genre + key + BPM + vibe (+ optional overrides), pull arrangement data from Phase 25 blueprints, calculate bar positions, and return a token-efficient flat production plan with per-section checklists. Server-side computation only; no Ableton socket calls from these tools; Claude holds the plan in context.

</domain>

<decisions>
## Implementation Decisions

### Output Structure
- **D-01:** Plan output is a flat JSON object with a top-level header (`genre`, `key`, `bpm`, `vibe`, `time_signature`) and a `sections` array.
- **D-02:** Each section entry contains: `name`, `bar_start`, `bars`, `roles` (list of active instrument roles), and `transition_in` (string descriptor — omitted for intro/first section, per Phase 25 D-04).
- **D-03:** `roles` + `transition_in` together serve as the per-section checklist. No additional action-verb authoring required — roles are pulled directly from blueprint section data.
- **D-04:** Output must be under 400 tokens (success criterion 1). Flat structure with no nesting beyond `sections[]` keeps token cost low.

### Beat / Bar Position Calculation
- **D-05:** Positions are expressed as `bar_start` (1-indexed bar number), not raw beat numbers.
- **D-06:** `time_signature` is an optional parameter (default `"4/4"`). The tool does NOT call Ableton to fetch the time signature — it accepts it as a caller-supplied param. Callers who need the live session's time sig should call `get_session_info` first.
- **D-07:** Bar positions are calculated cumulatively from section bar counts: section 1 starts at bar 1, section 2 at bar `1 + section_1.bars`, etc.

### Override Interface
- **D-08:** `generate_production_plan` accepts three optional structured override params:
  - `section_bar_overrides: dict | None` — map of section name → new bar count, e.g. `{"breakdown": 8}`
  - `add_sections: list[dict] | None` — list of new sections to insert, each with `name`, `bars`, `after` (section name to insert after), e.g. `[{"name": "bridge", "bars": 8, "after": "breakdown"}]`
  - `remove_sections: list[str] | None` — list of section names to drop, e.g. `["buildup2", "drop2"]`
- **D-09:** Overrides are applied before bar position calculation so positions in the output always reflect the final modified structure.
- **D-10:** `generate_section_plan` does not accept overrides — it targets a single section by name and returns only that section's plan entry.

### Vibe Parameter
- **D-11:** `vibe` is a free-form string (e.g. `"dark and hypnotic"`, `"euphoric rave energy"`). The server does not interpret or compute with it — it is echoed verbatim as a top-level field in the plan output so Claude (reading the plan during execution) can apply it contextually.
- **D-12:** Vibe is optional with no default. If omitted, the `vibe` field is excluded from the output.

### Claude's Discretion
- Exact param names and type annotations (follow existing tool module conventions in `MCP_Server/tools/`)
- How to handle a `section_bar_overrides` key for a section name that doesn't exist in the blueprint (warn vs. ignore)
- Whether `generate_section_plan` also accepts `time_signature` param or always uses 4/4 (lean toward accepting it for consistency)
- Token count validation approach (assert in tests vs. soft warning in output)

</decisions>

<specifics>
## Specific Requirements

- Under 400 tokens output is a hard success criterion (PLAN-01) — not a guideline
- `generate_section_plan` must work without generating the full track plan (PLAN-02) — it is a standalone tool, not a wrapper that filters full plan output
- Beat positions use the session's real time signature, not hardcoded 4/4 — but the tool gets this via parameter, not socket call (D-06)
- No server-side plan persistence — MCP is stateless; Claude holds the plan in context (from REQUIREMENTS.md out-of-scope section)

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — PLAN-01, PLAN-02, PLAN-03 (full production plan, single-section plan, override support)
- `.planning/ROADMAP.md` — Phase 26 success criteria (4 criteria including token budget and time signature requirement)

### Blueprint Data (Phase 25 output — what this phase consumes)
- `MCP_Server/genres/schema.py` — `ArrangementEntry` TypedDict with `name`, `bars`, `energy`, `roles`, `transition_in`; `GenreBlueprint` top-level shape
- `MCP_Server/genres/catalog.py` — `get_blueprint(genre, subgenre)` and `list_genres()` — the API this phase calls to fetch section data
- `MCP_Server/genres/house.py` — Canonical reference blueprint with all 7 sections fully authored including energy/roles/transition_in

### Existing Tool Pattern (follow this convention)
- `MCP_Server/tools/genres.py` — `get_genre_blueprint` and `get_genre_palette` — shows `@mcp.tool()` decorator, `Context` param, `format_error()` usage, `json.dumps()` return pattern
- `MCP_Server/tools/theory.py` — Additional tool module example for multi-function module structure

### Prior Phase Context
- `.planning/phases/25-blueprint-arrangement-extension/25-CONTEXT.md` — D-04 (transition_in absent for first section), D-05 (roles are active roles only), D-07 (roles list active instruments only)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/genres/catalog.py` — `get_blueprint(genre, subgenre)` returns a full `GenreBlueprint` dict including `arrangement.sections` with energy/roles/transition_in. This is the data source for both new tools.
- `MCP_Server/connection.py` — `format_error()` — standard error return format used by all tool modules
- `MCP_Server/tools/genres.py` — complete tool module example to follow for new `MCP_Server/tools/plans.py`

### Established Patterns
- All tools return `str` (JSON-encoded or error string via `format_error`)
- Tool params use Python type hints; optional params use `X | None = None`
- `@mcp.tool()` decorator registers tools automatically with FastMCP
- Blueprint section data flows through `get_blueprint()` → `blueprint["arrangement"]["sections"]` → list of `ArrangementEntry` dicts

### Integration Points
- New tool module: `MCP_Server/tools/plans.py` — new file following existing tool module pattern
- Registered automatically via `MCP_Server/tools/__init__.py` import (check how existing modules are registered)
- Phase 27 (`scaffold_arrangement`) will consume the output of `generate_production_plan` — the `sections` array with `bar_start` and `name` is what becomes Ableton locators

</code_context>

<deferred>
## Deferred Ideas

- Vibe-to-energy preset library (e.g. "dark" → shift energy curve down 1-2 points) — user noted vibe is too subjective for server-side mapping; deferred to v1.4+ per REQUIREMENTS.md
- Default instrument loading per role on scaffold tracks — deferred to v1.3.1 per REQUIREMENTS.md

</deferred>

---

*Phase: 26-production-plan-builder*
*Context gathered: 2026-03-27*
