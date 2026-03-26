# Project Research Summary

**Project:** Ableton MCP v1.2 — Genre/Style Blueprints
**Domain:** Static reference system for AI-assisted music production (MCP server extension)
**Researched:** 2026-03-25
**Confidence:** HIGH

## Executive Summary

v1.2 adds a genre blueprint system to an existing, mature MCP server (197 tools, proven architecture). The feature is a static reference layer: curated Python dicts describing production conventions for 12 electronic music genres, served through 3 new MCP tools. This is an additive, low-risk extension — zero new external dependencies, no protocol changes, no modifications to the Remote Script or any of the 17 existing tool modules. The critical architectural decision is delivery via MCP tools (model-controlled) rather than MCP resources (application-controlled), which allows Claude to autonomously fetch genre context when a user mentions a style, without requiring manual client-side setup.

The recommended build order is infrastructure-first, content-second: define the schema and catalog, validate end-to-end with one genre (house), then write the remaining 11 genre files. The `get_genre_palette` bridge tool — which calls the theory engine to resolve genre harmony conventions into key-specific chords and scales — is built last because it depends on both the blueprint library and theory engine being stable. This sequencing matches the existing codebase's own growth pattern (theory engine infrastructure preceded content expansion) and limits rework risk.

The primary risks are content quality (genre inaccuracy erodes user trust faster than code bugs) and context window bloat (verbose blueprints degrade Claude's reasoning on long production sessions). Both have clear mitigations: target 800-1200 tokens per full blueprint using concise structured dicts, and expose section filtering so Claude can request only the relevant portion. Architectural risks — circular imports and schema drift across 12 genre files — are eliminated at the infrastructure phase through strict import boundaries and import-time schema validation.

## Key Findings

### Recommended Stack

v1.2 requires zero new external packages. The entire feature is built on Python stdlib and existing dependencies (music21 for the palette bridge's theory calls, mcp[cli] for tool registration). The only configuration changes are two `pyproject.toml` package entries (`MCP_Server.blueprints`, `MCP_Server.blueprints.genres`) and one import line in `tools/__init__.py`.

**Core technologies:**
- Python dicts: blueprint data format — matches existing PROGRESSION_CATALOG/RHYTHM_CATALOG patterns; no runtime file I/O; malformed Python fails loudly at import, not silently at runtime
- FastMCP `@mcp.tool()`: delivery mechanism — model-controlled (Claude decides when to fetch); consistent with all 197 existing tools; universally supported across MCP clients; no new primitive types introduced
- music21 (existing): palette bridge backend — existing theory functions resolve blueprint harmony names (e.g., `"min7"`, `"dorian"`) to key-specific MIDI data; no new dependency needed

### Expected Features

**Must have (table stakes):**
- `list_genre_blueprints()` — Claude needs genre discovery before fetching; zero external dependencies
- `get_genre_blueprint(genre, subgenre, sections)` — core value proposition; `sections` parameter is required to avoid context bloat (full blueprints are 2000+ tokens without filtering)
- Instrumentation, harmony, rhythm, arrangement, mixing sections — users expect all five; each maps to existing MCP tool categories
- Minimum 8 genres: house, techno, hip-hop/trap, ambient (P0) + DnB, dubstep, trance, neo-soul (P1) — covers maximum electronic music territory
- Subgenre support with shallow merge — deep_house vs. tech_house conventions differ substantially; merge behavior must be predictable

**Should have (differentiators):**
- `get_genre_palette(genre, key, subgenre)` — bridges blueprints to theory engine; returns key-resolved chords, scales, progressions ready for use with existing production tools
- Ableton-specific tips section — maps genre conventions to named Ableton instruments/effects
- Genre aliases (e.g., `"dnb"` maps to `"drum_and_bass"`) — prevents tool call failures from naming mismatches
- BPM range per genre — immediately actionable parameter for `set_tempo`

**Defer (v2+):**
- Auto-genre detection from Ableton session state — fragile, error-prone; asking the user is better UX and easier to implement correctly
- Blueprint editing/creation tools — blueprints are curated reference data, not user-managed content
- Real-time web updates — introduces network dependency and data trust issues; static curated data is more reliable
- Genre-specific operation tools (e.g., `create_house_track`) — combinatorial explosion (12 genres × N operations); generic tools + blueprint context is the correct abstraction

### Architecture Approach

The blueprint system is structurally parallel to the existing theory engine: a library package (`MCP_Server/blueprints/`) holds schema, catalog, and one Python module per genre; a tool module (`MCP_Server/tools/blueprints.py`) wraps the library with `@mcp.tool()` decorators following the identical pattern as `tools/theory.py`. The two systems are intentionally decoupled — blueprint modules store convention names as strings (e.g., `"chord_types": ["min7", "dom9"]`), never importing theory functions. Only the `get_genre_palette` tool bridges the gap at runtime, eliminating circular dependency risk.

**Major components:**
1. `blueprints/genres/*.py` (12 files) — individual genre data as Python dicts; one file per genre; 80-120 lines each; no imports from theory
2. `blueprints/catalog.py` — registry, lookup by genre/subgenre, alias resolution, shallow merge logic for subgenres; central coordinator
3. `blueprints/schema.py` — canonical schema definition + import-time validation function; ensures all 12 genres are structurally consistent; catches drift immediately at startup
4. `blueprints/__init__.py` — clean public API (`get_blueprint`, `list_genres`); only surface imported by tool layer
5. `tools/blueprints.py` — 3 MCP tool wrappers (`list_genre_blueprints`, `get_genre_blueprint`, `get_genre_palette`); the only file that imports from both `blueprints/` and `theory/`
6. `tests/test_blueprints.py` — schema validation across all genres; tool output format; palette bridge correctness; theory-compatibility cross-reference

### Critical Pitfalls

1. **Blueprint-theory circular imports** — blueprint modules must never contain `from MCP_Server.theory import ...`; only `tools/blueprints.py` crosses the boundary at runtime. Enforced by code review; detectable by grep.
2. **Context window bloat from verbose blueprints** — target 800-1200 tokens per full blueprint; use `sections` parameter to let Claude request only what it needs; keep `notes` fields to one sentence maximum; measure token counts in tests and fail any blueprint over 1500 tokens.
3. **Genre data inaccuracy** — wrong BPM ranges or chord conventions cause "this doesn't sound like techno" failures that are harder to diagnose than code bugs; cross-reference multiple production sources per genre; use ranges not single values; include a `sources` field per blueprint for traceability.
4. **Schema drift across genre files** — run `schema.py` validation at import time (not just in tests) so any structural inconsistency fails loudly at startup rather than silently during a production session.
5. **Palette tool failures on unsupported chord/scale names** — validate every blueprint `chord_type` and `scale` name against the theory engine's supported types before shipping; use try/except in the palette tool to skip unsupported qualities gracefully rather than returning an error.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Blueprint Infrastructure + First Genre
**Rationale:** Everything else depends on schema and catalog being defined; validate the full pipeline end-to-end with one genre before committing content effort to all 12; matches the existing codebase's infrastructure-before-content pattern and limits rework.
**Delivers:** `schema.py`, `catalog.py`, `genres/__init__.py`, `genres/house.py` (canonical example with all subgenres), `blueprints/__init__.py`, test scaffold
**Addresses:** Blueprint schema definition, subgenre merge logic, alias resolution infrastructure
**Avoids:** Schema drift (Pitfall 4 — validation enforced from day one), missing pyproject.toml entries (Pitfall 10)

### Phase 2: Core Tool Layer + Integration Wiring
**Rationale:** With infrastructure and one validated genre, build the tool wrappers to achieve end-to-end validation (data → catalog → MCP API → test); locks the API surface before scaling content; proves the delivery mechanism works.
**Delivers:** `tools/blueprints.py` with `list_genre_blueprints` and `get_genre_blueprint` (section filtering included); `tools/__init__.py` registration; full test coverage for tool layer; token count measurement for house blueprint
**Uses:** Existing FastMCP `@mcp.tool()` pattern from `tools/theory.py`
**Implements:** Tool wrapper component; validates MCP tools (not resources) delivery decision

### Phase 3: Genre Content — P0 + P1 Batch
**Rationale:** Schema validated, pipeline proven, API locked, tests in place — now scale content with confidence; P0 genres (techno, hip-hop/trap, ambient) join house from Phase 1 to cover maximum stylistic range; P1 genres (DnB, dubstep, trance, neo-soul) follow immediately since infrastructure is identical and no new design decisions are needed.
**Delivers:** 7 genre files (techno, hip-hop/trap, ambient, DnB, dubstep, trance, neo-soul); 8 genres total after Phase 1's house; each includes aliases and subgenres
**Addresses:** 8-genre minimum table stake; alias resolution (Pitfall 9)
**Avoids:** Schema drift — import-time validation from Phase 1 catches inconsistencies immediately

### Phase 4: P2 Genres + Palette Bridge
**Rationale:** `get_genre_palette` depends on both the blueprint library and theory engine being stable — build last; P2 genres (synthwave, lo-fi, future bass, disco/funk) are lower priority and complete the catalog alongside the bridge tool; all chord/scale names across all 12 genres must be audited against the theory engine before implementing the bridge.
**Delivers:** 4 remaining P2 genre files; `get_genre_palette` tool with theory engine integration; cross-reference validation test (every blueprint harmony name verified against theory engine's supported types)
**Addresses:** Differentiator feature (palette bridge), full 12-genre coverage
**Avoids:** Palette edge cases (Pitfall 5 — graceful try/except for unsupported chord qualities; names audited at import)

### Phase Ordering Rationale

- Schema and catalog come before all content: all 12 genre files, both retrieval tools, and the palette bridge depend on the infrastructure — building content first would require rework when the schema evolves.
- One genre validates before scaling: design flaws in the data structure are cheap to fix after one genre and expensive after twelve.
- Tool layer before remaining content: the API shape should be locked before authors write 11 more genre files against it.
- Palette bridge last: it is the only code-level integration point between blueprints and theory; isolating it to the final phase keeps integration failures contained and eliminates circular dependency risk during development.
- P2 genres slot with the bridge: they are content work with no blocking dependencies, and completing all 12 genres in the same phase as the bridge makes for a clean, shippable milestone.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (genre content):** Content accuracy requires per-genre domain research — BPM ranges, chord conventions, and subgenre distinctions should be verified against producer community sources (forums, tutorials, academic analyses), not written from memory. Plan research tasks per genre.
- **Phase 4 (palette bridge):** Requires auditing the theory engine's 26 supported chord qualities and all scale names to build a validated allow-list for blueprint harmony sections before authoring P2 genre content or implementing the bridge.

Phases with standard patterns (skip research-phase):
- **Phase 1 (infrastructure):** Direct parallel to existing theory engine pattern (`PROGRESSION_CATALOG`, `RHYTHM_CATALOG`); well-understood codebase; no unknowns.
- **Phase 2 (tool layer):** `tools/theory.py` is the exact template; the pattern is fully established.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Verified against existing `pyproject.toml`; zero new dependencies confirmed; no alternatives required |
| Features | HIGH | Table stakes derived from existing codebase patterns and clear domain requirements; anti-features well-reasoned against architectural constraints |
| Architecture | HIGH | Direct structural parallel to existing theory engine; all component boundaries verified against actual codebase; no speculative design |
| Pitfalls | HIGH | Most pitfalls derived from existing codebase analysis (import patterns, tool registration, token economy); domain-specific content risks are well-understood |

**Overall confidence:** HIGH

### Gaps to Address

- **Genre accuracy validation:** Blueprint content (BPM ranges, chord conventions, mixing guidance) cannot be fully validated by code review. Plan per-genre content research during Phase 3. Add a `sources` field to each blueprint dict for traceability and future review.
- **Theory engine chord/scale name compatibility:** The palette bridge assumes blueprint harmony names map to theory engine function parameters. Before Phase 4, audit `theory/chords.py` (26 chord qualities) and `theory/scales.py` to build a definitive allow-list; write a cross-reference validation test.
- **Token budget empirical baseline:** The 800-1200 token target is a design constraint, not a measured baseline. Measure actual token counts for the house blueprint in Phase 1 and adjust schema verbosity guidance before writing the remaining 11 genres.

## Sources

### Primary (HIGH confidence)
- Existing codebase: `MCP_Server/theory/progressions.py` (PROGRESSION_CATALOG pattern), `MCP_Server/theory/rhythm.py` (RHYTHM_CATALOG pattern), `MCP_Server/tools/theory.py` (tool wrapper pattern), `MCP_Server/tools/__init__.py` (import-based registration), `MCP_Server/server.py` (FastMCP setup)
- Existing codebase: `pyproject.toml` (confirmed zero new dependencies required)

### Secondary (MEDIUM confidence)
- MCP protocol documentation — Resources vs. Tools control model; delivery mechanism decision rationale
- FastMCP documentation — decorator syntax, tool vs. resource patterns, prompt distinctions
- Electronic music production domain knowledge — genre conventions, subgenre distinctions, BPM ranges

### Tertiary (LOW confidence)
- Genre-specific content accuracy — needs validation against producer community sources (forums, tutorial channels, academic music analyses) during Phase 3 content authoring; treat all genre content as draft until reviewed

---
*Research completed: 2026-03-25*
*Ready for roadmap: yes*
