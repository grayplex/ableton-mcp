# Phase 34: Full Genre Recipe Expansion - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend the mixing recipe library to all 12 genres by authoring `RECIPE` + `MASTER_RECIPE` for the 8 remaining genres: synthwave, hip_hop_trap, dubstep, trance, lo_fi, future_bass, disco_funk, neo_soul_rnb.

No new MCP tools, no new Remote Script handlers. Pure data authoring — new genre files drop into `MCP_Server/mixing/` and auto-discover via pkgutil. The existing `get_mix_recipe`, `apply_mix_recipe`, `apply_master_recipe`, and `suggest_mix_adjustments` tools adapt automatically.

</domain>

<decisions>
## Implementation Decisions

### Carried Forward from Phase 30 (all apply unchanged)
- **D-01:** Recipe values in natural units (Hz, dB, ms, %, not normalized 0.0–1.0)
- **D-02:** Sound-shaping params only — no `Device On`, `LegacyMode`, or housekeeping params
- **D-03:** All 9 roles authored for every genre (kick, bass, lead, pad, chords, vocal, atmospheric, return, master)
- **D-04:** Omit inapplicable devices entirely — no None markers
- **D-05:** One file per genre in `MCP_Server/mixing/`, pkgutil auto-discovery, zero registration code

### D-07: Plan Split Strategy
Two plans split by genre family:
- **Plan 34-01:** Electronic/synth-heavy genres — synthwave, dubstep, trance, future_bass
- **Plan 34-02:** Groove/organic genres — hip_hop_trap, disco_funk, neo_soul_rnb, lo_fi

Each plan also includes `MASTER_RECIPE` for its 4 genres. Mirrors the Phase 22+23 pattern for genre authoring.

### D-08: Genre Aliases
Minimal alias set — only what's needed to handle slash/ampersand input variants. Add to `_GENRE_ALIASES` in `MCP_Server/mixing/catalog.py`:

| Alias | Resolves to |
|-------|-------------|
| `hip-hop` | `hip_hop_trap` |
| `hip hop` (→ normalized `hip_hop`) | `hip_hop_trap` |
| `r&b` (→ normalized `r_b`) | `neo_soul_rnb` |
| `disco/funk` (→ normalized `disco_funk`) | already canonical |

Canonical snake_case IDs (synthwave, dubstep, trance, lo_fi, future_bass, hip_hop_trap, disco_funk, neo_soul_rnb) are the primary names. No broad shorthand aliases (no `trap`, `funk`, `future` as standalone aliases).

### D-09: Tool Docstring Updates
After Phase 34, all four mixing tools (`get_mix_recipe`, `apply_mix_recipe`, `apply_master_recipe`, and `suggest_mix_adjustments`) must replace their hardcoded genre list with a reference to `list_recipes()`:

```
Genres: use list_recipes() to see all available genres.
```

This keeps docstrings accurate regardless of future genre additions.

### Claude's Discretion
- Exact natural-unit parameter values for each role/genre combination (musical authoring)
- Which devices are present per role in each genre (omit inapplicable per D-04)
- Non-typical role/genre pairings receive safe generic values (per D-03)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Recipe Files (structure to mirror exactly)
- `MCP_Server/mixing/house.py` — reference RECIPE structure (9 roles, device keys, natural units, MASTER_RECIPE at bottom)
- `MCP_Server/mixing/drum_and_bass.py` — DnB reference showing non-typical role handling

### Catalog (parameter names for validation)
- `MCP_Server/devices/catalog.py` — CATALOG dict with 327 live-validated parameters; all recipe param names MUST match entries here
- `MCP_Server/devices/__init__.py` — `ROLES` list (9 canonical roles)

### Alias Registry (where to add new aliases)
- `MCP_Server/mixing/catalog.py` — `_GENRE_ALIASES` dict (add D-08 entries here)

### Tool Docstrings (4 files to update per D-09)
- `MCP_Server/tools/mixing.py` — `get_mix_recipe`, `apply_mix_recipe`, `apply_master_recipe`, `set_sidechain_source`
- `MCP_Server/tools/suggest.py` (or wherever `suggest_mix_adjustments` lives) — update genre list reference

### Requirements
- `RECIP-02` (REQUIREMENTS.md) — 8 new track recipes + master recipes for all 12 genres
- `MSTR-01` (REQUIREMENTS.md) — master bus recipe for all 12 genres

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/mixing/house.py` / `techno.py` / `ambient.py` / `drum_and_bass.py` — 4 complete reference files, ~650 lines each; new files follow identical structure
- `MCP_Server/mixing/catalog.py` — auto-discovery and alias resolution; only `_GENRE_ALIASES` needs updating (D-08)
- `tests/test_mixing.py` — iterates `_registry.items()` dynamically; new genres auto-covered with zero test additions required

### Established Patterns
- Each file: comment header with D-01..D-04 reminders, then `RECIPE = {...}` keyed by role, then `MASTER_RECIPE = {...}` at the bottom
- Filter type comments in-file (e.g., `# 0=48dB/oct, 1=12dB/oct, 2=Low Shelf, 3=Bell...`) — carry this documentation style forward
- Compressor2 Ratio uses 0.0–1.0 range (NOT raw ratio like 4:1) — the catalog stores it as normalized

### Integration Points
- New `.py` files in `MCP_Server/mixing/` → auto-discovered by catalog on first call
- `_GENRE_ALIASES` in `catalog.py` → add D-08 aliases
- `MCP_Server/tools/mixing.py` → update 3 docstrings
- Wherever `suggest_mix_adjustments` lives → update 1 docstring

</code_context>

<specifics>
## Specific Ideas

- Genre file naming mirrors blueprint filenames exactly: `synthwave.py`, `hip_hop_trap.py`, `dubstep.py`, `trance.py`, `lo_fi.py`, `future_bass.py`, `disco_funk.py`, `neo_soul_rnb.py`
- MASTER_RECIPE at bottom of each file (GlueCompressor + MultibandDynamics + Limiter chain)
- The `_normalize()` function in catalog.py handles spaces/hyphens → underscores, so `hip-hop` naturally becomes `hip_hop` which can alias to `hip_hop_trap`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 34-full-genre-recipe-expansion*
*Context gathered: 2026-03-30*
