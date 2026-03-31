# Phase 36: Instrument Profile Authoring - Context

**Gathered:** 2026-03-31
**Mode:** auto (Claude selected recommended defaults)
**Status:** Ready for planning

<domain>
## Phase Boundary

Author the remaining 5 native Ableton instrument profiles (Analog, Operator, Drift, Simpler, Drum Rack) as individual modules in `MCP_Server/sounds/`, following the Wavetable reference schema from Phase 35. Each profile must be auto-discovered by `catalog.py` and cover sonic character, strengths, weaknesses, descriptor affinities, and browser category paths. A validation checkpoint plan mirrors Phase 35's Plan 02 pattern for live Ableton browser path confirmation.

</domain>

<decisions>
## Implementation Decisions

### Profile Schema
- **D-01 (inherited):** All Phase 35 schema decisions carry forward unchanged -- two-axis descriptor affinities, minimal PROFILE dict, short phrase lists for strengths/weaknesses, single-string sonic_character paragraph, root + categories browser dict
- **D-02:** No new schema fields added in Phase 36 -- profiles are strictly parallel to `wavetable.py`

### Browser Root Paths (assumed -- need live validation per D-06)
- **D-03:** Analog root: `"Instruments/Analog"` (standard Ableton browser path for Analog synth)
- **D-04:** Operator root: `"Instruments/Operator"` (standard Ableton browser path for Operator FM synth)
- **D-05:** Drift root: `"Instruments/Drift"` (introduced in Live 11.3; same pattern as other instruments)
- **D-06:** Simpler root: `"Instruments/Simpler"` (sample-based instrument; same pattern)
- **D-07:** Drum Rack root: `"Instruments/Drum Rack"` (the instrument device itself, not the Drums content folder) -- this is the highest-uncertainty path; live validation is the primary goal of Plan 02
- **D-08:** All 5 root paths are assumed; live validation checkpoint in Plan 02 will confirm or correct them (same D-06 fallback from Phase 35 applies -- keep path on failure, log warning)

### Descriptor Affinity Values
- **D-09:** Analog affinities -- warm analog subtractive: role={bass:0.85, lead:0.8, keys:0.7, pad:0.55}, character={warm:0.9, punchy:0.7, dark:0.65, bright:0.6, aggressive:0.6, evolving:0.3}
- **D-10:** Operator affinities -- FM synthesis, metallic and percussive: role={keys:0.85, bass:0.8, lead:0.75, pad:0.5, texture:0.4}, character={bright:0.85, punchy:0.75, aggressive:0.65, warm:0.5, dark:0.45, evolving:0.45}
- **D-11:** Drift affinities -- vintage organic analog drift: role={bass:0.8, lead:0.75, keys:0.7, pad:0.65, texture:0.5}, character={warm:0.85, dark:0.7, evolving:0.6, bright:0.45, punchy:0.55, aggressive:0.4}
- **D-12:** Simpler affinities -- sample-based, versatile, sample-dependent: role={keys:0.7, bass:0.7, lead:0.65, pad:0.6, texture:0.55}, character={warm:0.6, bright:0.6, organic:0.75, evolving:0.4, punchy:0.5, aggressive:0.35}
- **D-13:** Drum Rack affinities -- dedicated to percussion roles: role={kick:0.95, snare:0.95, hihat:0.9, percussion:0.9, pad:0.2, lead:0.1}, character={punchy:0.95, aggressive:0.75, tight:0.8, warm:0.4, bright:0.5, evolving:0.25}

### Aliases Per Instrument
- **D-14:** Analog aliases: `["analog", "al"]`
- **D-15:** Operator aliases: `["operator", "op"]`
- **D-16:** Drift aliases: `["drift"]`
- **D-17:** Simpler aliases: `["simpler", "smplr"]`
- **D-18:** Drum Rack aliases: `["drum rack", "drum_rack", "dr", "drumsrack"]`

### Simpler Modes Coverage
- **D-19:** Simpler's `sonic_character` paragraph must mention all three modes -- Classic (pitched playback), One-Shot (single-shot triggering), and Slice (sample slicing/chopping) -- to satisfy SC3 in the phase success criteria
- **D-20:** No per-mode sub-profiles -- single PROFILE dict with modes described in text only; Phase 37 scoring treats Simpler as one instrument

### Plan Structure
- **D-21:** Two plans, mirroring Phase 35 structure:
  - Plan 01: Author all 5 profiles + unit tests (TDD: write tests first, then profiles)
  - Plan 02: Browser path validation checkpoint against live Ableton (same checkpoint pattern as 35-02)
- **D-22:** Plan 01 tests must assert: (a) all 5 profiles are auto-discovered by catalog, (b) `list_profiles()` returns 6 total instruments, (c) each new profile passes alias normalization checks, (d) each profile has the required schema keys

### Claude's Discretion
- Specific wording in `sonic_character`, `strengths`, and `weaknesses` fields is left to Claude's judgment -- musicological accuracy preferred over verbosity

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Reference Implementation
- `MCP_Server/sounds/wavetable.py` -- The exact schema and structure to replicate for all 5 new profiles
- `MCP_Server/sounds/catalog.py` -- Auto-discovery and alias normalization; new profiles just need to be added as modules

### Pattern References
- `MCP_Server/genres/techno.py` -- Module structure pattern (single dict constant, aliases list)
- `MCP_Server/mixing/techno.py` -- RECIPE dict constant structure

### Phase 35 Artifacts
- `.planning/phases/35-package-skeleton-and-first-profile/35-CONTEXT.md` -- All inherited schema decisions (D-01 through D-10)
- `.planning/phases/35-package-skeleton-and-first-profile/35-02-SUMMARY.md` -- Browser path validation checkpoint pattern to replicate in Plan 02

### Requirements
- `.planning/REQUIREMENTS.md` -- INST-02 (Analog), INST-03 (Operator), INST-04 (Drift), INST-05 (Simpler), INST-06 (Drum Rack)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MCP_Server/sounds/catalog.py` -- No changes needed; new modules auto-discovered by existing `_discover_profiles()`
- `MCP_Server/sounds/__init__.py` -- No changes needed; pkgutil auto-discovery handles new modules
- `MCP_Server/sounds/wavetable.py` -- Direct copy-edit template for all 5 new profiles

### Established Patterns
- Each profile: pure Python module exporting `PROFILE` dict constant with keys: id, name, aliases, sonic_character, strengths, weaknesses, descriptor_affinities, browser
- `descriptor_affinities` shape: `{"role": {tag: float}, "character": {tag: float}}`
- `browser` shape: `{"root": "Instruments/Name", "categories": {"role": "Category Folder"}}`
- Tests: mirror existing `tests/test_sounds_catalog.py` pattern (if it exists) or `tests/test_genres_catalog.py`

### Integration Points
- No changes to catalog.py or __init__.py -- new files only
- Phase 38 will consume `catalog.get_profile()` and `catalog.list_profiles()` -- public API is already stable

</code_context>

<specifics>
## Specific Ideas

- Drum Rack `browser.categories` should map percussion roles: `{"kick": "Drums & Percussion", "snare": "Drums & Percussion", "hihat": "Drums & Percussion"}` -- all map to the same folder since Drum Rack presets are not split by drum type
- Operator `browser.categories` should include FM-specific categories like: `{"keys": "Keys", "bass": "Bass", "lead": "Leads", "bell": "Bell & Mallet"}`
- Simpler `browser.categories` can use: `{"keys": "Keys & Plucks", "bass": "Bass", "one_shot": "One Shots"}` since Simpler is organized around sample type/role

</specifics>

<deferred>
## Deferred Ideas

- Per-mode Simpler profiles (Classic/One-Shot/Slice as separate entries) -- deferred to Phase 37+ if scoring engine needs finer granularity
- Additional instrument profiles beyond the 6 native instruments (e.g., Meld, Analog+, third-party) -- out of v1.5 scope
- Validation of category sub-paths (D-07 from Phase 35 carries forward: root-only validation)

</deferred>

---

*Phase: 36-instrument-profile-authoring*
*Context gathered: 2026-03-31 (auto mode)*
