# Phase 25: Blueprint Arrangement Extension - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend all 12 genre blueprints' `arrangement.sections` entries with 3 new fields: `energy` (int 1-10), `roles` (list of active instrument roles), and `transition_in` (string descriptor). Extend the schema and validator to expose these fields. Backward-compatible — all 148 existing genre tests pass without modification.

This is pure data authoring + schema extension. No new MCP tools, no new tool modules. The `get_genre_blueprint` tool already returns the full blueprint dict — once sections carry the new fields, the tool exposes them automatically.

</domain>

<decisions>
## Implementation Decisions

### Schema Extension
- **D-01:** New fields are added to `ArrangementEntry` TypedDict as optional (not required) — keeps `validate_blueprint()` backward-compatible so existing test fixtures without the new fields still pass
- **D-02:** In all actual genre blueprints, every section is authored with the new fields (energy, roles, and transition_in where applicable) — optional in schema, populated in practice

### Subgenre Section Coverage (D-03)
- **D-03:** Subgenres inherit energy/roles/transition_in from the parent genre's matching section by name (default). Subgenres MAY optionally override any of the new fields on a per-section basis if their energy curve or roles differ meaningfully from the parent.
  - Example: progressive_house overrides `arrangement.sections` with different bar counts — the merge logic should fall back to parent section data for energy/roles/transition_in unless the subgenre explicitly provides them.

### Intro/First Section Convention (D-04)
- **D-04:** The first section (typically "intro") omits `transition_in` entirely — no key, no empty string, no null. Code downstream must handle absence gracefully. This also applies to any section that is structurally "the start" (no preceding section to transition from).

### Per-Section Roles Convention (D-05)
- **D-05:** Per-section `roles` are a soft-constrained subset of `instrumentation.roles` — convention only, not enforced by the validator. Role strings should match the genre's top-level instrumentation roles. Tests spot-check specific sections but do not fail if a section role isn't in the top-level list (allows section-specific roles like `"riser"` or `"fx_swell"` when appropriate).

### Content Authoring
- **D-06:** Energy levels (1-10) model the section's energy curve: intro ~2-3, buildup ramps up, drop peaks at 8-10, breakdown drops to 3-5, outro fades to 2-3. Each genre's curve should reflect its actual energy arc, not a generic template.
- **D-07:** Per-section roles list the instrument roles ACTIVE in that section (not silent/absent ones). Drop sections should list full production elements; breakdowns/intros may omit leads, drums, etc.
- **D-08:** `transition_in` is a short descriptor phrase (e.g., "filter sweep + riser", "impact hit", "gradual strip-back", "drum fill"). Should be actionable enough for Claude to use as a production instruction.

### Claude's Discretion
- Exact energy values per section per genre (follow D-06 guidance)
- Exact role lists per section (follow D-05 convention, referencing top-level instrumentation.roles)
- Exact transition_in strings per section (follow D-08 guidance)
- How subgenre merge logic resolves inherited vs. overridden section data (catalog.py implementation detail)
- Whether TypedDict uses `total=False` on a subclass or `Optional` fields for the new keys

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Schema & Infrastructure
- `MCP_Server/genres/schema.py` — `ArrangementEntry` TypedDict and `validate_blueprint()` — extend here for new fields
- `MCP_Server/genres/catalog.py` — Subgenre merge logic — update to handle inherited vs. overridden new fields
- `MCP_Server/genres/house.py` — Canonical blueprint template — implement new fields here first as the reference example

### All Genre Files (must be extended)
- `MCP_Server/genres/house.py`
- `MCP_Server/genres/techno.py`
- `MCP_Server/genres/hip_hop_trap.py`
- `MCP_Server/genres/ambient.py`
- `MCP_Server/genres/drum_and_bass.py`
- `MCP_Server/genres/dubstep.py`
- `MCP_Server/genres/trance.py`
- `MCP_Server/genres/neo_soul_rnb.py`
- `MCP_Server/genres/synthwave.py`
- `MCP_Server/genres/lo_fi.py`
- `MCP_Server/genres/future_bass.py`
- `MCP_Server/genres/disco_funk.py`

### Tests
- `tests/test_genres.py` — Existing 148 tests that must pass without modification
- `tests/test_genre_quality.py` — Quality gate tests (check if arrangement section tests exist here)

### Requirements
- `.planning/REQUIREMENTS.md` — ARNG-01, ARNG-02, ARNG-03
- `.planning/ROADMAP.md` — Phase 25 success criteria (4 criteria)

### Prior Context
- `.planning/phases/20-blueprint-infrastructure/20-CONTEXT.md` — D-11 (generic roles), D-12 (arrangement structure) — both apply here

</canonical_refs>

<code_context>
## Existing Code Insights

### Current ArrangementEntry shape (schema.py)
```python
class ArrangementEntry(TypedDict):
    name: str   # e.g., "intro"
    bars: int   # e.g., 16
```
Extension adds optional: `energy: int`, `roles: List[str]`, `transition_in: str`

### Existing sections in house.py (7 sections)
intro(16), buildup(8), drop(32), breakdown(16), buildup2(8), drop2(32), outro(16)

### Subgenre that overrides arrangement
- `progressive_house` in house.py overrides all 7 sections with different bar counts — merge logic in catalog.py handles this

### get_genre_blueprint tool (tools/genres.py)
Returns `json.dumps(blueprint)` — no changes needed to the tool itself. New section fields appear automatically once blueprints carry them.

### 148 existing tests
Located in `tests/test_genres.py` and `tests/test_genre_quality.py`. The `_make_valid_blueprint()` fixture has sections without new fields — validator must remain backward-compatible (D-01).

</code_context>

<specifics>
## Specific Requirements

- Success criterion 4 explicitly requires backward compatibility: all 148 existing tests pass without modification
- `transition_in` is absent (not empty string) for intro/first sections — D-04
- Subgenre section override is optional: subgenres that only differ in bar counts don't need to re-author energy/roles/transition_in — D-03
- Per-section roles are active roles only (not the full genre instrumentation list) — D-07

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 25-blueprint-arrangement-extension*
*Context gathered: 2026-03-27*
