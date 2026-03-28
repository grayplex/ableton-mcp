# Project Research Summary

**Project:** Ableton MCP v1.4 — Mix/Master Intelligence
**Domain:** AI-assisted mixing and mastering for electronic music production via Ableton Live MCP
**Researched:** 2026-03-28
**Confidence:** HIGH (stack and architecture confirmed via codebase inspection; feature conventions HIGH from domain sources; specific parameter values LOW — require live Ableton validation)

## Executive Summary

Ableton MCP v1.4 adds a mix/master intelligence layer on top of a working 181-command MCP server. The approach is to build a new `MCP_Server/mixing/` package — a peer to the existing `genres/` and `theory/` packages — containing a static device parameter catalog, role x genre mix recipes, and a recipe engine. This follows proven patterns already in the codebase and requires zero new Python package dependencies. The headline feature is an `apply_mix_recipe` tool that applies genre-appropriate mixing chains (EQ, compression, sends, volume targets) to Ableton tracks in a single MCP call, replacing the current need for Claude to issue 10-30+ sequential tool calls to achieve the same result.

The recommended build order is: device parameter catalog first (the foundation that everything depends on), followed by role taxonomy and core mix recipes for 4 genres, then the apply-recipe tool and gain staging check, then master bus recipes and tools, and finally the "suggest adjustments" intelligence layer and recipe expansion to all 12 genres. This sequence respects hard dependencies — recipes cannot be authored without a validated parameter catalog, and the suggest-adjustments diff engine cannot work without the recipe and state-reader layers beneath it.

The most serious risk in this milestone is parameter name and value mismatch: Ableton's LOM uses internal parameter naming conventions that differ from GUI labels (e.g., `"1 Frequency A"` not `"Frequency"`), and many parameters store normalized floats rather than natural units (e.g., EQ frequency is 0.0-1.0, not 20-20000 Hz). Every part of this milestone depends on getting the catalog right from a live Ableton session query, not hand-authored from documentation. Two features originally scoped — LUFS metering and Spectrum frequency analysis — are architecturally impossible via the LOM and must be dropped from v1.4 scope.

## Key Findings

### Recommended Stack

No new pip dependencies are needed for v1.4. All new functionality is pure Python data structures (dicts, TypedDicts) layered on top of the existing stack: Python 3.11 (Remote Script), Python >=3.10 (MCP Server), FastMCP >=1.3.0, music21 >=9.0, and the localhost:9877 TCP socket IPC. The only new Remote Script addition is a `get_track_meters` handler for reading `track.output_meter_level/left/right`, which enables gain staging checks without any new libraries.

**Core technologies (unchanged):**
- Python dicts + TypedDict: device catalog and mix recipes — same proven pattern as genre blueprints, no external library exists for this domain
- Existing `set_device_parameter` / `get_device_parameters` handlers: sufficient for recipe application (with batch wrapper)
- `mixer_helpers.py` extension: add `_from_db()` inverse and `_meter_to_db()` for target-based gain staging
- LOM `track.output_meter_level/left/right`: gain staging feedback, available without new deps

**Explicitly dropped from scope:**
- pyloudnorm: requires raw audio samples (NumPy arrays) — MCP Server and Remote Script have no audio buffer access; LUFS measurement is architecturally impossible
- Spectrum frequency data: LOM exposes only Spectrum device control parameters, not the frequency bin display data; visual-only device

### Expected Features

**Must have (table stakes):**
- Device parameter catalog (F1) — foundation for all recipes; without validated API names, every recipe fails
- Role taxonomy (F2) — lightweight canonical grouping; organizes recipe lookup
- Role x genre mix recipes for 4 core genres: house, techno, ambient, DnB (F3) — the core value proposition
- Apply recipe tool (F4) — single-call mixing; eliminates 10-30 sequential tool calls per track
- Gain staging check (F6) — reads track volumes, flags outliers vs. targets; foundational for any mix assessment
- Master bus recipes, 12 genres (F8) — mastering is inseparable from mixing in electronic music
- Master bus apply tool (F9) — thin wrapper over F4 targeting master track

**Should have (differentiators):**
- Device state reader / batch get (F5) — collapses 48 individual `get_device_parameters` calls to 1 for a 16-track session
- Suggest adjustments with reasoning (F7) — reads current state, diffs against recipe, explains each suggestion; the "AI mixing engineer" feature
- Mix recipe expansion to all 12 genres (F3 remainder) — completion of the data surface

**Defer to v1.5+:**
- Section-aware mixing — requires automation infrastructure not present until v1.5
- Frequency conflict detection — needs audio analysis or sophisticated heuristics beyond LOM access
- Sidechain routing automation — basic sidechain params belong in recipes, but full routing automation is complex and session-dependent
- LUFS / Spectrum analysis — architecturally impossible via LOM

### Architecture Approach

The `mixing/` package integrates as a peer to `genres/` and `theory/`, never modifying genre blueprints (which would break 12-genre validation and bloat token counts). The architecture keeps intelligence server-side: the Remote Script stays dumb (no new business logic in Ableton's Python sandbox), recipe resolution happens in `mixing/engine.py`, and MCP tools in `tools/mixing.py` are thin wrappers that call the engine then dispatch existing Remote Script commands. The only potential Remote Script modification is a fix to `browser.py` to support `track_type: "master"` in `load_browser_item` — this is an integration gap requiring verification.

**Major components:**
1. `mixing/catalog.py` — static dict mapping 10-12 Ableton built-in devices to their exact API parameter names, value ranges, and conversion semantics; MUST be bootstrapped from live Ableton queries, not hand-authored
2. `mixing/recipes/*.py` — per-genre recipe files with auto-discovery (same pkgutil pattern as `genres/`); recipe data references genre IDs but is separate from genre blueprint prose
3. `mixing/engine.py` — pure computation: recipe lookup, resolution against catalog, diff generation; no Ableton dependency, fully unit-testable
4. `mixing/gain.py` — gain staging analysis: compare track volumes and meter readings to role/genre targets, produce flagged output
5. `tools/mixing.py` — MCP tool endpoints: validate inputs, call engine, dispatch existing Remote Script commands, format output

### Critical Pitfalls

1. **Parameter name mismatch** — Ableton's API uses internal names like `"1 Frequency A"` (not `"Frequency"`), `"Output Gain"` (not `"Makeup"`). Build the catalog by querying `get_device_parameters` on live Ableton devices; never hand-author from documentation or GUI labels. A `verify_catalog` test that loads each device and checks all names is mandatory.

2. **Normalized vs. natural unit values** — EQ Eight frequency is stored as 0.0-1.0 (logarithmic mapping to 20Hz-20kHz), not in Hz. Compressor Attack/Release are likely normalized, not in milliseconds. The catalog must record actual `min`/`max`/`unit` from the API, and the apply-recipe tool must convert human-unit recipe values before calling `set_device_parameter`. Formula: `normalized = (log10(hz) - log10(20)) / (log10(20000) - log10(20))` for frequency.

3. **Recipe application ordering and atomicity** — Device loading via `load_browser_item` is async; setting parameters immediately in a separate MCP call is fragile. A single Remote Script command that loads, verifies instantiation, resolves `device_index` by `class_name` scan, and sets all params atomically is safer than orchestrating separate Claude tool calls for load + set. This conflicts with ARCHITECTURE.md's preference for orchestrating existing tools — this tension must be resolved during Phase 3 planning via a spike.

4. **MIDI tracks without instruments** — `track.mixer_device.volume` exists on all tracks but is meaningless for MIDI tracks without instruments. Gain staging tools must check `track.has_audio_output` or `len(track.devices) > 0` and skip/flag empty MIDI tracks. Reuse the instrument-presence check from v1.3 `get_arrangement_progress`.

5. **EQ Eight complete band state** — Setting only `"1 Frequency A"` without also setting `"1 Filter On A"`, `"1 Filter Type A"`, `"1 Gain A"`, and `"1 Resonance A"` produces unpredictable results depending on the device's default state. EQ recipes must specify the complete state for every band they use. Consider a dedicated `apply_eq_recipe` Remote Script command with band-level specification.

## Implications for Roadmap

Based on combined research, the suggested phase structure follows the hard dependency chain: catalog before recipes, recipes before apply-tool, apply-tool before suggest-adjustments. Data authoring is the largest effort (~250 recipe dicts across 12 genres) and should be parallelized across phases rather than deferred to a single large phase.

### Phase 1: Device Parameter Catalog and Schema Foundation

**Rationale:** Every other component in v1.4 depends on knowing the exact API parameter names, value ranges, and conversion semantics for 10-12 Ableton built-in devices. Building this incorrectly (from documentation instead of live queries) breaks every subsequent phase. Must be first.

**Delivers:** `mixing/schema.py` with TypedDicts; `mixing/catalog.py` with live-verified parameter data for EQ Eight, Compressor, Glue Compressor, Limiter, Utility, Reverb, Delay, Auto Filter, Drum Buss, Multiband Dynamics; UAT verification script that loads each device and cross-checks catalog against live Ableton output.

**Addresses:** F1 (Device Parameter Catalog)

**Avoids:** Pitfall 1 (parameter name mismatch), Pitfall 2 (normalized vs. natural units), Pitfall 9 (Compressor non-uniform ranges), Pitfall 10 (class_name surprises)

**Research flag:** NEEDS research-phase — device class names and parameter ranges require live Ableton session verification. Cannot be known ahead of time from documentation alone.

### Phase 2: Role Taxonomy and Core Mix Recipes (4 Genres)

**Rationale:** With a verified catalog, recipes can be authored correctly. Starting with 4 high-impact genres (house, techno, ambient, DnB) validates the recipe schema with a manageable data surface before scaling to 12 genres. The role taxonomy is lightweight and needed by both recipes and the gain staging tool.

**Delivers:** `mixing/recipes/` subpackage with auto-discovery; `mixing/engine.py` for recipe lookup; house, techno, ambient, DnB recipe files covering 8-10 core roles each; master bus recipes for the same 4 genres; role taxonomy constants.

**Addresses:** F2 (Role Taxonomy), F3 (core 4 genres), F8 (master bus recipes for core 4 genres)

**Avoids:** Pitfall 8 (EQ band completeness — schema requires full band spec), Pitfall 11 (keeping recipes separate from blueprint prose), Pitfall 3 (recipe load order encoded in recipe definition)

**Research flag:** Standard patterns — recipe data authoring follows proven genre blueprint pattern. No new architecture research needed.

### Phase 3: Apply Recipe Tool and Batch Parameter Setting

**Rationale:** The apply-recipe tool is the headline feature. Must be built after catalog and recipes so there is real data to test against. The atomicity question (single Remote Script command vs. orchestrated MCP calls) should be resolved here based on a spike.

**Delivers:** `tools/mixing.py` with `apply_mix_recipe` and `apply_master_recipe` tools; Remote Script atomic handler (load + verify + set all params in one command); `set_device_parameters_batch` handler for reducing round-trips; possible `browser.py` fix for master track device loading.

**Addresses:** F4 (Apply Recipe Tool), F9 (Master Bus Tools)

**Avoids:** Pitfall 3 (atomicity), Pitfall 5 (master bus insert order), Pitfall 12 (return track type), Pitfall 13 (Device On parameter), Pitfall 14 (duplicate devices)

**Research flag:** NEEDS research-phase — the atomicity design is a genuine architectural decision with performance and reliability tradeoffs. Run a spike measuring round-trip latency and async device loading behavior before committing.

### Phase 4: Gain Staging Check and Device State Reader

**Rationale:** With recipes applicable, the feedback loop tools come next. Gain staging check provides immediate user value and the batch device state reader enables the suggest-adjustments feature in the next phase.

**Delivers:** `mixing/gain.py` with analysis logic; `get_mix_state` tool (batch device state reader); `check_gain_staging` tool; Remote Script `get_track_meters` handler for `output_meter_level/left/right`; Remote Script batch track info command.

**Addresses:** F5 (Device State Reader), F6 (Gain Staging Check)

**Avoids:** Pitfall 4 (MIDI tracks without instruments), performance trap of sequential per-track reads

**Research flag:** Standard patterns — gain analysis math is straightforward; v1.3 instrument-presence check pattern is available for reuse.

### Phase 5: Suggest Adjustments Intelligence Layer

**Rationale:** The "AI mixing engineer" differentiator. Depends on both the recipe layer (F3) and the state reader (F5) being complete and tested. Building this last ensures it has the full foundation.

**Delivers:** `engine.diff_against_recipe()` function; `suggest_mix_adjustments` MCP tool with reasoning output per parameter diff; documentation of the suggest-then-confirm workflow.

**Addresses:** F7 (Suggest Adjustments)

**Avoids:** Black-box automation (always show what will change + reasoning before applying)

**Research flag:** Standard patterns — diff logic is pure computation, no Ableton dependency, well-understood pattern.

### Phase 6: Recipe Expansion to All 12 Genres

**Rationale:** Data scaling phase. Applies the validated schema and patterns to the remaining 8 genres. The recipe authoring infrastructure is proven; this phase is primarily content work.

**Delivers:** Recipe files for synthwave, hip-hop/trap, dubstep, trance, lo-fi, future bass, disco/funk, neo-soul/R&B; master bus recipes for same 8 genres; F3 and F8 completion.

**Addresses:** F3 (full 12-genre expansion), F8 (all master bus recipes)

**Research flag:** Standard patterns — recipe authoring follows Phase 2 pattern. Genre mixing conventions are well-documented in production education sources.

### Phase Ordering Rationale

- Phases 1-3 form a hard dependency chain (catalog -> recipes -> apply-tool); cannot be reordered
- Phase 4 is prerequisite to Phase 5 (state reader needed for diff engine)
- Phase 6 is pure data expansion; could begin in parallel with Phase 5 if resources allow
- Master bus recipes (F8) should be authored alongside per-track recipes in each data phase, not deferred — they share the same catalog and schema
- Sidechain routing automation is intentionally deferred; sidechain parameters belong in recipes but routing index resolution requires session-dependent logic that is v1.5 scope

### Research Flags

Phases needing deeper research during planning:
- **Phase 1:** Live Ableton session required to capture device class names and parameter names/ranges for all 10-12 target devices. This is UAT-first, not code-first.
- **Phase 3:** Atomicity design decision — single Remote Script apply command vs. orchestrated MCP calls. Run a spike to measure round-trip latency and test whether async device loading causes timing issues before committing to architecture.

Phases with standard patterns (skip research-phase):
- **Phase 2:** Recipe schema follows existing genre blueprint pattern exactly. Auto-discovery via pkgutil is already proven.
- **Phase 4:** Gain analysis math is trivial; instrument-presence check pattern already exists in v1.3.
- **Phase 5:** Diff logic is pure computation with no Ableton dependency.
- **Phase 6:** Content authoring only; architecture is locked by Phase 2.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Zero new dependencies confirmed by codebase inspection; pyloudnorm and Spectrum data correctly eliminated with documented rationale |
| Features | MEDIUM-HIGH | Table stakes features well-established; specific device parameter names are MEDIUM (must be live-verified); genre mixing conventions are HIGH from multiple production education sources |
| Architecture | HIGH | All integration points verified via source code inspection; one gap: master track device loading via `load_browser_item` needs verification |
| Pitfalls | HIGH | Parameter naming and normalization pitfalls confirmed via live API behavior documentation and codebase analysis; sidechain routing fragility confirmed by reading existing handler code |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Exact device class names:** Not confirmed for all 10-12 target devices. Only `"OriginalSimpler"` is known from existing tests. All others (Compressor, EQ Eight, Glue Compressor, etc.) must be queried from a live session before Phase 1 can complete. Handle by making catalog bootstrap the first deliverable of Phase 1.

- **EQ Eight frequency normalization formula:** The log-frequency mapping formula in PITFALLS.md is a community-sourced approximation. The exact mapping must be verified against Ableton's implementation — small errors in the conversion formula produce audibly wrong frequency values. Include a conversion accuracy test in Phase 1 UAT.

- **Compressor Attack/Release ranges:** PITFALLS.md flags these as "likely normalized 0-1 with non-linear mapping" but this is unconfirmed. Must be captured in Phase 1 live query.

- **`load_browser_item` master track support:** ARCHITECTURE.md flags this as a potential integration gap. The existing handler indexes into `song.tracks[]`, which excludes the master track. This may require a Remote Script fix; needs verification before Phase 3 begins.

- **Atomicity vs. orchestration tradeoff:** PITFALLS.md recommends a single atomic Remote Script command for recipe application. ARCHITECTURE.md recommends orchestrating existing tools to avoid Remote Script business logic. This unresolved tension must be settled in Phase 3 via a spike based on measured latency and observed async behavior.

- **Recipe parameter values (numeric):** Specific recipe values (e.g., "house kick compressor threshold = -12 dB") are informed by production education sources but have LOW confidence as exact starting points. Treat v1.4 recipes as starting points; the system should make values easily adjustable.

## Sources

### Primary (HIGH confidence)
- Ableton Live Object Model — Cycling74 docs (Track metering, Device parameter access, confirmed via codebase cross-reference)
- Ableton Live 12 Audio Effect Reference — official device documentation
- Existing codebase: `devices.py`, `mixer_helpers.py`, `genres/schema.py`, `genres/catalog.py`, `conftest.py` — all findings verified by direct code inspection

### Secondary (MEDIUM confidence)
- Remotify Device Parameters reference — community-documented Ableton device parameter names for Live 11 (structure carries to Live 12)
- iZotope mixing and mastering guides — genre mixing conventions and master bus chain order
- Toolroom Academy / Audeobox / Loopmasters mixing guides — EDM genre-specific mixing conventions
- Ableton Forum on Spectrum device — confirms no mappable parameters for frequency data

### Tertiary (LOW confidence)
- Specific numeric recipe values (thresholds, frequencies, ratios) — informed starting points from production education sources; require ear-testing and iterative refinement in practice

---
*Research completed: 2026-03-28*
*Ready for roadmap: yes*
