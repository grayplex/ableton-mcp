# Project Research Summary

**Project:** Ableton MCP — Sound Selection Intelligence (v1.5)
**Domain:** AI-driven instrument/preset recommendation layer for Ableton Live MCP server
**Researched:** 2026-03-30
**Confidence:** HIGH

## Executive Summary

v1.5 adds an instrument recommendation system to the Ableton MCP server. The feature takes text descriptors like "warm pad" or "punchy kick" and maps them to one of the 6 native Ableton instruments (Wavetable, Analog, Operator, Drift, Simpler, Drum Rack) with a browser path that lets Claude navigate to appropriate presets. This is pure authored data plus Python stdlib logic — no new dependencies are required. The codebase already has a proven pattern for this kind of feature in `genres/` and `mixing/`, and v1.5 follows that pattern exactly: a new peer package (`sounds/`) with one file per instrument, a catalog with pkgutil auto-discovery, a weighted scoring engine, and a thin tool wrapper exposing 3 MCP tools.

The recommended approach is a two-axis descriptor system (role + character) with weighted affinity scores on each instrument profile. When Claude calls `get_sound_recommendation("warm evolving pad")`, the catalog tokenizes the string, looks up per-tag affinity weights across all 6 instrument profiles, and returns the top-ranked match with a browser path and one-line reasoning. This is transparent, deterministic, and debuggable with zero ML dependencies. The `list_sound_descriptors` tool gives Claude the exact valid vocabulary, eliminating any fuzzy-matching requirement.

The single highest-risk area is browser path correctness. Ableton's browser has two distinct roots (`instruments/` and `sounds/`) that are easy to confuse, and authored paths must be validated against a live Ableton session before all 6 profiles are written. Every other risk — descriptor taxonomy overlap, genre coupling creep, auto-discovery misconfiguration — is caught early by the Phase 1 build order (data layer first, schema locked before profiles are authored).

## Key Findings

### Recommended Stack

v1.5 requires no new runtime dependencies. The implementation uses Python stdlib (`pkgutil`, `importlib`, `json`, `copy`, `logging`) and the existing `mcp[cli] >= 1.3.0` package for tool registration. The only project-level change needed is adding `MCP_Server.sounds` to the `packages` list in `pyproject.toml`, and adding a `sounds` import line to `MCP_Server/tools/__init__.py`.

Fuzzy-matching libraries (`thefuzz`, `rapidfuzz`) and ML embedding libraries (`sentence-transformers`, `scikit-learn`) are explicitly ruled out. They solve a problem that does not exist: Claude picks descriptors from `list_sound_descriptors` output, so there is no free-text approximation scenario. Alias normalization (`lower().strip().replace(" ", "_")`) plus exact-match dict lookup is correct and sufficient.

**Core technologies:**
- Python stdlib (`pkgutil`, `importlib`): auto-discovery of instrument profile modules — same pattern as `genres/` and `mixing/`
- FastMCP (`mcp[cli] >= 1.3.0`): register 3 new `@mcp.tool()` functions — no version change needed
- Plain Python dicts: instrument profile data format — established project convention (D-01/D-02)

### Expected Features

All v1.5 deliverables are P1 (table stakes). There are no differentiators that require effort beyond the core spec — the two-axis descriptor system and reasoning output are part of the baseline feature, not optional enhancements.

**Must have (table stakes):**
- `get_sound_recommendation(descriptor)` returning instrument name, browser path, and one-line reasoning — core promise; without it Claude fumbles randomly through the browser
- `list_sound_descriptors()` returning all valid tags grouped by role — required for Claude discoverability
- `get_instrument_profile(instrument)` returning full character doc — reasoning substrate for recommendations
- Instrument profiles for all 6 native instruments (Wavetable, Analog, Operator, Drift, Simpler, Drum Rack) — incomplete coverage silently fails whole sound categories
- Browser category paths validated against a live Ableton session — unvalidated paths are the highest-risk failure mode

**Should have (differentiators):**
- Two-axis descriptor system (role + character), e.g., "warm pad" vs "bright pad" vs "dark pad" — key value-add over manual browsing
- Instrument `weaknesses` in profiles — negative guidance prevents bad recommendations (e.g., "Drift is poor for metallic FM textures — use Operator instead")
- Grouped descriptor output from `list_sound_descriptors` — prevents Claude from guessing when the descriptor list is long

**Defer (v2+):**
- Genre-aware recommendations (descriptor + genre context) — combinatorial explosion; separation of concerns favors descriptor-only now
- Third-party plugin profiles — scope limited to 6 native instruments
- Preset-level descriptions — too many presets, stale across Ableton updates
- Audio-analysis-based matching — requires audio streaming, fundamentally different architecture not compatible with MCP protocol

### Architecture Approach

v1.5 adds one new peer package (`MCP_Server/sounds/`) alongside the existing `genres/`, `mixing/`, and `theory/` packages. The package contains a catalog module (auto-discovery + weighted scoring engine) and one profile file per instrument. A new `MCP_Server/tools/sounds.py` exposes 3 MCP tools. The only modified existing file is `MCP_Server/tools/__init__.py` (one added import). No Remote Script changes. No genre coupling.

**Major components:**
1. `sounds/{instrument}.py` files — static `INSTRUMENT` dict constants with character, descriptor affinities (weighted 0.0–1.0), and browser paths per role
2. `sounds/catalog.py` — pkgutil auto-discovery, reverse descriptor index built at import time, weighted sum scoring engine, `get_profile()` / `list_descriptors()` / `recommend()` public API
3. `tools/sounds.py` — thin MCP tool wrappers: input validation, JSON serialization, `format_error()` for failures; delegates all logic to the `sounds/` package

The data flow is: Claude calls `get_sound_recommendation("warm evolving pad")` → tool tokenizes descriptor → catalog scores all 6 profiles by summing tag affinity weights → returns ranked results with instrument name, direct load path, category hint, and reasoning → Claude uses existing `load_instrument_or_effect` tool with the returned load path.

### Critical Pitfalls

1. **Browser path mismatch (`instruments/` vs `sounds/` root)** — Ableton's browser has two distinct hierarchies: `instruments/Wavetable/Pad` (instrument-specific presets) and `sounds/Pad` (presets from all instruments mixed together). All profile paths must use `instruments/{Name}` for melodic synths and `drums/` for Drum Rack. The `sounds/` root must not appear in any profile. Validate every load path with a live Ableton session before authoring all 6 profiles.

2. **Descriptor taxonomy too broad or overlapping** — Tags like "warm" that match 3–4 instruments equally give no differentiating signal. Design the two-axis (role + character) taxonomy first, ensure each descriptor maps to a clear primary instrument, and test that no two descriptors return identical results unless intentionally documented.

3. **Recommendation output not directly loadable** — If `get_sound_recommendation` returns only a preset category path (e.g., `instruments/Wavetable/Pads/Warm Pad`), Claude needs 2–3 additional tool calls to load anything. The output must include a `load_path` field (`instruments/Wavetable` or `drums/Drum Rack`) that can be passed directly to `load_instrument_or_effect` in one call.

4. **Genre coupling creep** — It is tempting to add "best for: house, techno" fields to profiles. The v1.5 spec explicitly forbids genre dependency. Profiles describe inherent sonic character only. Locking the schema with no genre field prevents this from creeping in.

5. **Auto-discovery misconfiguration** — The new `sounds/` package needs `__init__.py` with `__path__` set correctly for `pkgutil.iter_modules` to find instrument modules. A missing or incorrect `__init__.py` causes zero instruments to be discovered with no error message. Verify `list_sound_descriptors()` returns results for all 6 instruments before authoring any matching logic.

## Implications for Roadmap

Based on research, the dependency chain is clear: data schema must be locked before profiles are authored, profiles must exist before the scoring engine can run, and the scoring engine must work before tools can expose it. This maps cleanly to 4 phases.

### Phase 1: Instrument Profile Data Layer

**Rationale:** All downstream work depends on the profile data and schema being correct. Browser path schema and descriptor taxonomy design must be locked here — changing them after all 6 profiles are authored requires rewriting all profiles. This phase eliminates the 3 highest-risk pitfalls (browser path confusion, taxonomy overlap, genre coupling) before any tool code is written.

**Delivers:** `MCP_Server/sounds/` package skeleton with `__init__.py` and `catalog.py`, all 6 instrument profile files, catalog auto-discovery verified, `get_instrument_profile` tool working end-to-end, browser load paths validated against a live Ableton session.

**Addresses:** `get_instrument_profile` MCP tool (table stakes), instrument profiles for all 6 instruments (table stakes), browser path validation (table stakes).

**Avoids:** Browser path mismatch (validate during this phase), genre coupling (lock schema with no genre field), auto-discovery misconfiguration (test catalog discovers all 6 before continuing).

### Phase 2: Descriptor Taxonomy and Scoring Engine

**Rationale:** The descriptor taxonomy and affinity weights are authored data in the profile files, but the scoring engine that uses them is separate logic. Building the engine after profiles exist allows immediate testing against real data. This phase locks the descriptor vocabulary — changes after this point require retesting all descriptor combinations.

**Delivers:** Complete descriptor tag taxonomy (~30–50 tags across role and character axes), `recommend()` function with weighted sum scoring in `catalog.py`, browser path resolution logic, `list_sound_descriptors()` tool returning grouped output, full test coverage of scoring and ranking.

**Addresses:** `list_sound_descriptors` MCP tool (table stakes), two-axis descriptor system (differentiator), instrument weaknesses guiding away from poor choices (differentiator).

**Avoids:** Descriptor taxonomy overlap (test every descriptor returns a distinct primary recommendation), recommendation not directly loadable (include `load_path` field in scoring output from day one).

### Phase 3: get_sound_recommendation MCP Tool and Integration

**Rationale:** The tool layer is last because it is a thin wrapper over already-tested logic. Integration testing here closes the loop: `get_sound_recommendation("warm pad")` → load path → `load_instrument_or_effect` → instrument loaded in one call. This is the user-facing payoff of the previous two phases.

**Delivers:** `MCP_Server/tools/sounds.py` with 3 tool functions, `tools/__init__.py` import added, end-to-end integration tests (recommendation to loaded instrument), `pyproject.toml` packages list updated.

**Addresses:** `get_sound_recommendation` MCP tool (table stakes), grouped descriptor output (differentiator).

**Avoids:** Recommendation output not directly loadable (integration test verifies round-trip), synthesis jargon in reasoning (plain-language reasoning tested against sample outputs).

### Phase 4: Validation and Coverage Audit

**Rationale:** The "looks done but isn't" checklist from PITFALLS.md identifies specific coverage gaps that are easy to miss: Drum Rack percussive descriptor coverage, Simpler's three modes, grouped `list_sound_descriptors` output, and `load_path` field present in `get_instrument_profile` output. A dedicated audit phase prevents shipping with silent gaps.

**Delivers:** Complete percussive descriptor coverage (kick, snare, hi-hat → Drum Rack), Simpler profile covering Classic/One-Shot/Slice modes, all 6 instruments verified discoverable via auto-discovery, all load paths verified with live Ableton UAT, milestone audit passed.

**Addresses:** Remaining coverage gaps from the "looks done but isn't" checklist in PITFALLS.md.

**Avoids:** Drum Rack missing from percussive recommendations, Simpler treated as sampler-only, paths tested with `get_browser_tree` but never actually round-trip loaded.

### Phase Ordering Rationale

- Schema and data must precede logic: the scoring engine needs profiles to score against.
- Descriptor taxonomy must be authored before the scoring engine is written: affinities live in profile dicts, not in catalog code.
- Tool layer is always last — it is the thinnest layer and depends on everything below it.
- Validation phase at the end catches coverage gaps that unit tests miss (live UAT, edge case descriptors, Drum Rack percussive coverage).

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1:** Browser path schema requires live Ableton validation. The exact folder names under `instruments/Wavetable/`, `instruments/Analog/`, etc. are MEDIUM confidence from documentation only. Must be confirmed with `get_browser_items_at_path` in a live session before profiles are finalized. Drum Rack browser root (`drums/` vs `instruments/Drum Rack`) needs specific confirmation.

Phases with standard patterns (skip research-phase):
- **Phase 2:** Weighted sum scoring is fully specified in ARCHITECTURE.md with reference implementation. The algorithm requires no further research.
- **Phase 3:** Tool registration follows the exact `tools/mixing.py` → `mixing/catalog.py` pattern. No unknowns.
- **Phase 4:** Audit checklist is pre-written in PITFALLS.md. No research needed, just execution.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | No new dependencies; all patterns derived from existing codebase analysis with direct code inspection |
| Features | MEDIUM-HIGH | Table stakes features are clear; browser preset category paths are MEDIUM confidence pending live session validation |
| Architecture | HIGH | Derived entirely from existing codebase patterns (genres/, mixing/, devices/); no external dependencies or novel patterns introduced |
| Pitfalls | HIGH | Based on deep codebase analysis of browser integration, existing catalog patterns, Remote Script browser handler behavior |

**Overall confidence:** HIGH

### Gaps to Address

- **Browser category paths within each instrument** — The specific subfolder names under `instruments/Wavetable/`, `instruments/Analog/`, etc. are MEDIUM confidence from third-party documentation. Confirm with `get_browser_items_at_path` against a live Ableton 12 session at the start of Phase 1. The load path at the instrument root (`instruments/Wavetable`) is stable and HIGH confidence; deeper preset category subfolders need validation.

- **Drum Rack browser root** — PITFALLS.md identifies `drums/Drum Rack` vs `instruments/Drum Rack` as a specific known confusion point. Confirm the correct root path in live UAT during Phase 1 before authoring the Drum Rack profile.

- **Descriptor affinity weight calibration** — The affinity weights (0.0–1.0) in ARCHITECTURE.md are illustrative starting points. They will need tuning after Phase 2 tests reveal which instruments are over- or under-recommended for specific descriptor combinations. This is expected: it is handled by editing profile dicts with no tool code changes required.

## Sources

### Primary (HIGH confidence)
- Codebase: `MCP_Server/genres/catalog.py` — pkgutil auto-discovery pattern, alias normalization
- Codebase: `MCP_Server/mixing/catalog.py` — `_normalize()` + alias dict pattern
- Codebase: `MCP_Server/tools/__init__.py` — tool registration via single import line
- Codebase: `MCP_Server/tools/browser.py` — `get_browser_items_at_path`, `get_browser_tree` interfaces
- Codebase: `MCP_Server/tools/devices.py` — `load_instrument_or_effect` path parameter
- Codebase: `AbletonMCP_Remote_Script/handlers/browser.py` — `_resolve_browser_path`, `_CATEGORY_MAP`
- Codebase: `pyproject.toml` — dependency list, setuptools packages
- Project spec: `.planning/PROJECT.md` — v1.5 requirements and architecture constraints

### Secondary (MEDIUM confidence)
- [Ableton Live 12 Browser and Tags FAQ](https://help.ableton.com/hc/en-us/articles/11425042663708-Browser-and-Tags-in-Live-12-FAQ) — Sound filter tags (Bass, Lead, Pad, Keys, etc.)
- [Ableton Live Instrument Reference Manual](https://www.ableton.com/en/manual/live-instrument-reference/) — Instrument architectures and synthesis types
- [Ableton Drift blog post](https://www.ableton.com/en/blog/drift-exploring-the-new-synth-in-live-113/) — Drift sonic character
- [ADSR Sounds: Drift Presets](https://www.adsrsounds.com/synth/ableton-drift/) — Drift preset categories
- [Soundfly: Learning to Describe Synth Sounds](https://flypaper.soundfly.com/discover/learning-to-describe-synth-sounds-to-rebuild-patches/) — Sound descriptor vocabulary

### Tertiary (LOW confidence — needs live validation)
- Instrument preset browser subfolder names within `instruments/{Name}/` — inferred from documentation; requires live Ableton session confirmation during Phase 1
- Drum Rack browser root path — flagged in PITFALLS.md as a known confusion point; confirm in live UAT

---
*Research completed: 2026-03-30*
*Ready for roadmap: yes*
