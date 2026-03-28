# Project Research Summary

**Project:** Ableton MCP v1.3 Arrangement Intelligence
**Domain:** AI-assisted arrangement planning and session scaffolding for a DAW MCP server
**Researched:** 2026-03-27
**Confidence:** HIGH

## Executive Summary

v1.3 adds an arrangement intelligence layer to an existing, well-understood MCP server codebase. The work falls cleanly into three concerns: (1) enriching the 12 existing genre blueprints with per-section energy levels, instrument role lists, and transition descriptors; (2) a server-side plan builder that combines that enriched data with user-supplied genre/key/vibe parameters to produce a concrete, flat, checklist-driven production plan; and (3) Remote Script commands that write the plan into Ableton as named locators and named tracks. No new external dependencies are required. The stack is pure Python logic sitting on top of the existing FastMCP/TCP/Ableton LOM infrastructure established in v1.0–v1.2.

The recommended approach is a strict three-step workflow: generate plan (server-side, no Ableton), scaffold arrangement (locators + tracks in Ableton via a single atomic batch command), then execute section-by-section using existing tools guided by per-section checklists. The plan is returned as data to Claude rather than persisted server-side, because MCP is stateless and Claude is the natural state holder. The critical design insight is that the "session IS the plan" — locator names and track names in Ableton serve as persistent external memory that survives context pressure at tool call 30+.

The most significant implementation risk is the Ableton LOM's locator creation API: there is no `create_cue_at(time, name)` method. Creating a named locator requires a three-step Remote Script sequence (seek to position, toggle cue, set name) that MUST be atomic in a single handler. Exposing this as multiple MCP tool calls would cause race conditions and partial-failure states. This constraint, along with the need for optional-only schema extensions to avoid breaking 148 existing tests, must be settled in the first phase before any plan builder or scaffold logic is written.

## Key Findings

### Recommended Stack

v1.3 requires zero new pip packages. All arrangement intelligence is pure Python computation (template data in dicts, plan builder functions, checklist generators) served through existing FastMCP tools and backed by existing Ableton LOM commands over the established localhost:9877 TCP socket. The existing `mcp[cli] >=1.3.0`, `music21 >=9.0` (used by theory engine but not directly by v1.3), `pytest >=8.3`, and `ruff >=0.15.6` stack is entirely unchanged.

One new internal package is needed: `MCP_Server/production/` (mirroring the existing `MCP_Server/theory/` pattern) with `planner.py` (pure functions, fully unit-testable) and `scaffold.py` (uses `connection.send_command()`, requires Ableton for integration tests). The `pyproject.toml` packages list gains one entry: `MCP_Server.production`.

**Core technologies:**
- Python stdlib only: arrangement templates — no Jinja2, no Pydantic; existing TypedDict + runtime validation pattern is sufficient
- Existing FastMCP tools: plan and scaffold exposed as 4 new MCP tools (generate_production_plan, generate_section_plan, scaffold_arrangement, get_section_checklist)
- Ableton LOM via existing TCP socket: 4 new Remote Script commands (create_locator, delete_locator, scaffold_arrangement batch, get_arrangement_overview)
- Existing theory engine (MCP_Server/theory/): plan builder references key/scale names only; Claude resolves harmony per-section on demand using existing tools

### Expected Features

**Must have (table stakes):**
- Per-section energy level (int 1–10) in all 12 genre blueprints — quantifies the energy curve that defines arrangement flow
- Per-section instrument roles list in blueprints — this IS the execution checklist; tells Claude exactly which elements belong in each section
- Per-section transition descriptor string in blueprints — tells Claude how to connect sections (riser, filter sweep, impact hit)
- Production plan builder tool — `generate_production_plan(genre, key, bpm, vibe)` returning a flat, terse plan dict with per-section checklists and calculated beat positions
- Named locator creation (atomic Remote Script command) — single `create_locator(time, name)` handler that performs seek/toggle/name internally
- Session scaffolding tool — `scaffold_arrangement(plan)` creating all locators and named tracks in one batch Remote Script call
- Section checklist tool — `get_section_checklist(plan, section_name)` returning pending elements for a section

**Should have (competitive):**
- Transition descriptors between sections — `transition_in` field connecting arrangement to existing automation tools contextually
- Single-section mode — `generate_section_plan` for targeted work on one section without planning the whole track
- Context-aware plan modification — plan builder accepts override parameters (shorter breakdown, add bridge)
- `get_arrangement_overview` Remote Script command — composite read of locators + track names + session length for Claude to re-orient during long workflows

**Defer to post-v1.3:**
- Arrangement analysis of existing tracks — different domain (stem separation, structural segmentation), different milestone
- Empty arrangement clip pre-creation — locators provide sufficient visual guidance; clips created during execution
- Default instrument loading on scaffold tracks — better UX but higher complexity; v1.3.1 candidate
- Vibe-to-energy preset library — Claude interprets vibes contextually without a lookup table
- Section reordering support — requires delete-and-rebuild locator workflow; document as known limitation for v1.3

### Architecture Approach

v1.3 extends the existing two-tier architecture (MCP Server / Remote Script) without adding tiers, protocols, or external services. The new `MCP_Server/production/` package follows the identical pattern as `MCP_Server/theory/`: a pure library module (`planner.py`) that is fully unit-testable without Ableton, an orchestration module (`scaffold.py`) that uses `connection.send_command()`, and thin tool wrappers in `tools/production.py`. Genre blueprint extensions flow through the existing catalog auto-discovery and subgenre merge without catalog changes. The Remote Script gains new commands in the existing `handlers/arrangement.py`.

**Major components:**
1. `MCP_Server/production/planner.py` — pure computation: blueprint data + user params to flat ProductionPlan dict with beat positions and per-section checklists; no Ableton dependency; reads via `genres.get_blueprint()`
2. `MCP_Server/production/scaffold.py` — orchestration: sends `scaffold_arrangement` batch command to Remote Script; handles locator + track creation; returns creation summary
3. `AbletonMCP_Remote_Script/handlers/arrangement.py` (extended) — new atomic locator creation handler and batch scaffold command; enforces seek/toggle/name atomicity and idempotency; handles time-signature-aware beat positioning

### Critical Pitfalls

1. **Locator creation is not atomic by default** — `Song.set_or_delete_cue()` toggles at the current playback position; creating 7 locators via separate MCP tool calls causes 21+ round-trips and race conditions. Prevent by implementing a single `scaffold_arrangement` Remote Script command that creates all locators atomically with rollback on partial failure.

2. **Schema extension must use optional fields** — adding required fields to `ArrangementEntry` TypedDict breaks all 12 genre files and 148 passing tests simultaneously. Prevent by making all new fields (`energy`, `elements`, `transition_in`) optional in schema and validated only when present; existing genres remain valid throughout migration.

3. **Context collapse at tool call 30+** — Claude loses the production plan during long sessions. Prevent by making the session itself the plan: locator names and track names in Ableton serve as persistent external memory; a `get_arrangement_overview` progress-check tool lets Claude re-orient in one call without reconstructing state from raw listings.

4. **Over-engineered plan representation** — arrangement intelligence is intellectually tempting but the plan must stay flat and terse. Prevent by defining the output format before writing any code; a 7-section plan must stay under 400 tokens; no nested phases, dependency graphs, or energy curve polynomials.

5. **Time signature arithmetic hardcoded to 4/4** — any literal `* 4` in beat position math breaks for 3/4, 6/8, 5/4 genres. Prevent by using `beats_per_bar = numerator * (4.0 / denominator)` from day one, reading `Song.signature_numerator/denominator` from the session. The fix is one line; there is no acceptable shortcut.

## Implications for Roadmap

The architecture research recommends four phases (25–28) with strict dependency ordering. Each phase is independently shippable and testable.

### Phase 25: Blueprint Arrangement Extension

**Rationale:** Data-only foundation phase. No Ableton needed, no new modules. Must come first because the plan builder (Phase 26) requires enriched arrangement data to generate meaningful checklists, and schema correctness must be proven before any consumption code is written. Mirrors Phase 20 (Blueprint Infrastructure) in scope and approach.

**Delivers:** All 12 genre blueprints enriched with `energy` (int 1–10), `roles`/`elements` (list of instrument role strings), and `transition_in` (str) per section; `ArrangementEntry` TypedDict extended with optional fields; `validate_blueprint()` updated to validate new fields when present; all 148 existing tests still pass with zero changes to genre files.

**Addresses:** Per-section element lists, energy levels, transition descriptors (table stakes features).

**Avoids:** Schema breaking cascade (Pitfall 4) — optional fields only; backward compatibility test verifies all existing genres pass unchanged.

**Research flag:** No deeper research needed. Pattern is identical to v1.2 blueprint work. Standard.

### Phase 26: Production Plan Builder

**Rationale:** Server-side only, pure Python, fully unit-testable without Ableton. Depends on Phase 25 enriched data for meaningful output. Must precede Phase 27 because the scaffold command consumes the plan structure. Mirrors Phase 21 (Blueprint Tools) in scope.

**Delivers:** `MCP_Server/production/` package; `planner.py` generating flat ProductionPlan dicts with calculated beat positions and per-section checklists; `tools/production.py` exposing `generate_production_plan` and `generate_section_plan` MCP tools; unit tests covering multiple genres, keys, and vibe variants.

**Addresses:** Production plan from genre + vibe (table stake), single-section mode (should-have), context-aware plan modification (should-have).

**Avoids:** Over-engineered plan representation (Pitfall 5) — output format defined and validated against 400-token budget before any code; redundant plan builder (Pitfall 9) — vibe and duration parameters ensure output differs from raw blueprint data.

**Research flag:** No deeper research needed. Pure Python computation with well-understood inputs and outputs. Standard.

### Phase 27: Locator and Scaffolding Commands

**Rationale:** Requires Ableton for integration testing. Depends on Phase 26 plan structure to know what locators and tracks to create. The critical LOM constraint (seek/toggle/name atomicity) makes this the highest-risk phase technically — the implementation detail is fully researched and the exact handler pattern is documented in ARCHITECTURE.md, but it requires live Ableton verification.

**Delivers:** `create_locator`, `delete_locator`, `get_arrangement_overview` Remote Script commands in `handlers/arrangement.py`; `scaffold_arrangement` batch command (creates all locators + named tracks + sets tempo in one TCP call); corresponding MCP tool wrappers; `connection.py` updated with new write commands.

**Addresses:** Named locator creation (table stake), session scaffolding tool (table stake), `get_arrangement_overview` progress-check (should-have).

**Avoids:** Cue point seek-toggle fragility (Pitfall 1) — atomic batch command with rollback; CuePoint.name writability (Pitfall 2) — read-back verification after setting name; time signature arithmetic (Pitfall 6) — `beats_per_bar` formula from day one; scaffold conflicts with existing content (Pitfall 10) — pre-scaffold session state query.

**Research flag:** Integration testing against live Ableton required. LOM constraints are fully researched (HIGH confidence) but the atomic handler behavior must be verified in a live session. Flag for integration validation during phase planning.

### Phase 28: Section Execution and Quality Gate

**Rationale:** Integration phase where all components come together. Depends on all prior phases. Mirrors Phase 24 (Quality Gate) in scope — end-to-end workflow validation rather than new feature development.

**Delivers:** `get_section_checklist` MCP tool; end-to-end workflow test (plan to scaffold to execute section checklists); quality gate: full arrangement from genre blueprint to playable Ableton session; progress-check tool validating that scaffolded MIDI tracks have instruments loaded.

**Addresses:** Section execution checklist (table stake), context collapse prevention (Pitfall 3 — progress-check tool ships here, not as an afterthought).

**Avoids:** Context collapse (Pitfall 3) — progress-check tool explicitly validates that Claude can re-orient from session state alone; missing instruments on scaffolded tracks (Pitfall 7) — progress-check flags instrumentless tracks.

**Research flag:** No deeper research needed. Thin tool wrapper + integration validation. Standard quality gate pattern.

### Phase Ordering Rationale

- Phase 25 before 26: Blueprint enrichment data is the input to the plan builder; generating meaningful checklists requires `energy` and `roles` to be present in blueprints
- Phase 26 before 27: The `scaffold_arrangement` batch command needs to know what a ProductionPlan looks like (structure, field names, beat position format) before the Remote Script handler can parse it
- Phase 27 before 28: Section checklist execution requires locators and named tracks to exist in Ableton; the quality gate validates the full stack
- Each phase is independently testable: Phase 25 and 26 are pure Python (pytest only); Phase 27 requires live Ableton; Phase 28 requires both

### Research Flags

Phases needing deeper research or integration validation during planning:
- **Phase 27:** Live Ableton integration testing for the `create_locator` atomic handler. The LOM constraint is fully documented but the seek/toggle/name sequence and CuePoint.name writability in Live 12 must be verified against a live instance. Also verify `scaffold_arrangement` batch command stays under the existing 15-second TIMEOUT_WRITE.

Phases with standard, well-documented patterns (skip research-phase):
- **Phase 25:** Blueprint extension follows identical pattern to v1.2 Phase 20. No new APIs, no new modules.
- **Phase 26:** Pure Python plan builder follows identical pattern to theory engine. Fully unit-testable, no external dependencies.
- **Phase 28:** Quality gate follows identical pattern to v1.2 Phase 24.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new external dependencies confirmed by direct codebase review. Internal module structure derived from existing `MCP_Server/theory/` pattern which is well-established. |
| Features | HIGH | Table stakes features verified against existing codebase (schema, blueprints, LOM APIs confirmed). Genre arrangement patterns from MEDIUM-confidence external sources but cross-validated against 12 existing blueprints. |
| Architecture | HIGH | Architecture follows established codebase patterns exactly. LOM constraints verified against official Cycling '74 documentation and existing Remote Script code. Critical locator creation pattern documented with exact handler pseudocode. |
| Pitfalls | HIGH | All critical pitfalls derived from direct codebase inspection and verified LOM API behavior. CuePoint.name writability in Live 12 confirmed via Cycling '74 forum. Beat position arithmetic and context collapse risks are design constraints, not speculation. |

**Overall confidence:** HIGH

### Gaps to Address

- **Scaffold batch command timeout:** The `scaffold_arrangement` batch command creating 7 locators + 8 tracks must complete within the existing `TIMEOUT_WRITE` of 15 seconds. This is expected to be well under that limit based on architecture analysis, but should be measured in the first Phase 27 integration test against a live session.

- **CuePoint.name writability syntax:** Research confirms Live 12 makes `CuePoint.name` writable, but the exact Python API syntax (`cp.name = value` vs. a setter method) should be verified in the first integration test. The fallback (locators exist but are unnamed) degrades gracefully but defeats the "session as plan" design.

- **Subgenre arrangement override completeness:** Some subgenres (e.g., `progressive_house`) already override `arrangement.sections`. The Phase 25 blueprint enrichment must audit all subgenres to determine which have arrangement overrides and ensure those are enriched consistently. The catalog merge behavior (shallow merge) means subgenre overrides replace the parent arrangement entirely — this is the existing behavior and should be preserved.

- **Token budget after enrichment:** The v1.2 quality gate (D-13) established a ceiling of 670 tokens per blueprint. Adding per-section enrichment fields may push some genres to ~850 tokens. The Phase 25 quality gate should verify the new ceiling remains acceptable and update the D-13 token budget parameter if needed.

## Sources

### Primary (HIGH confidence)
- [Cycling '74 LOM Reference (Max 9 PDF)](https://cycling74-docs-production.nyc3.cdn.digitaloceanspaces.com/pdfs/9.0.7-rev.1/Max9-LOM-en.pdf) — CuePoint class (page 56), Song class (pages 126–140)
- [Cycling '74 LOM Documentation](https://docs.cycling74.com/apiref/lom/) — CuePoint.name R/W, CuePoint.time R/O, Song.set_or_delete_cue() behavior, Song.cue_points
- [Cycling '74 Forum: Setting Locator Names](https://cycling74.com/forums/setting-locator-names) — CuePoint.name writable in Live 12 confirmed
- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) — stateless tool design, protocol patterns
- Existing codebase: `MCP_Server/genres/schema.py`, `MCP_Server/genres/catalog.py`, all 12 genre files — confirmed ArrangementEntry schema, catalog auto-discovery, existing arrangement data
- Existing codebase: `AbletonMCP_Remote_Script/handlers/transport.py` — current cue point implementation (toggle at current position only)
- Existing codebase: `AbletonMCP_Remote_Script/handlers/arrangement.py` — existing arrangement clip CRUD (4 commands unchanged in v1.3)
- Existing codebase: `MCP_Server/tools/arrangement.py` — existing MCP arrangement tools
- Existing codebase: `MCP_Server/connection.py` — TIMEOUT_WRITE (15s), command classification pattern

### Secondary (MEDIUM confidence)
- [EDM Tips - EDM Song Structure](https://edmtips.com/edm-song-structure/) — section energy and element patterns for drop-based genres
- [AudioServices - Arrangements in Electronic Music](https://audioservices.studio/blog/understanding-arrangements-in-electronic-music-production) — genre-specific arrangement conventions
- [Cycling '74 LOM Documentation (Max 8 legacy)](https://docs.cycling74.com/legacy/max8/vignettes/live_object_model) — LOM hierarchy and class relationships
- [Cymatics - EDM Song Structure](https://cymatics.fm/blogs/production/edm-song-structure) — standard section definitions for house, techno, DnB

### Tertiary (LOW confidence)
- None — all significant findings were cross-validated against at least two sources or direct codebase inspection.

---
*Research completed: 2026-03-27*
*Ready for roadmap: yes*
