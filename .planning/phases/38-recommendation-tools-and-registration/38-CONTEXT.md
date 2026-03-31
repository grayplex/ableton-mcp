# Phase 38: Recommendation Tools and Registration - Context

**Gathered:** 2026-03-31
**Mode:** auto (Claude selected recommended defaults)
**Status:** Ready for planning

<domain>
## Phase Boundary

Add `get_sound_recommendation` and `get_instrument_profile` MCP tools to the existing `MCP_Server/tools/sounds.py`, and add `MCP_Server.sounds` to the packages list in `pyproject.toml`. `tools/__init__.py` already imports `sounds` (done in Phase 37) -- no change needed there. This is the final phase of v1.5.

</domain>

<decisions>
## Implementation Decisions

### Tool File Location (D-01)
- **D-01:** Both new tools go in the existing `MCP_Server/tools/sounds.py` (D-11 from Phase 37). Add imports for `recommend` and `get_profile` at the top of that file alongside the existing `list_descriptors` import.

### get_sound_recommendation Tool (D-02)
- **D-02:** Takes one required string parameter `descriptor`. Calls `catalog.recommend(descriptor)`. If result is None (no match), returns a helpful error via `format_error`. If result is a dict, returns `json.dumps(result)` -- the dict already has id, name, score, browser_path, category_hint, reasoning. Docstring should note that `browser_path` is directly usable with `load_instrument_or_effect`.

### get_instrument_profile Tool (D-03)
- **D-03:** Takes one required string parameter `instrument`. Calls `catalog.get_profile(instrument)`. If None (not found), returns `format_error` with list of available instrument ids (from `catalog.list_profiles()`). If found, returns `json.dumps(profile)` -- the full PROFILE dict including sonic_character, strengths, weaknesses, descriptor_affinities, browser.

### pyproject.toml Update (D-04)
- **D-04:** Add `"MCP_Server.sounds"` to the packages list. Current list: `["MCP_Server", "MCP_Server.tools", "MCP_Server.theory"]`. New list: `["MCP_Server", "MCP_Server.tools", "MCP_Server.theory", "MCP_Server.sounds"]`. Also check if `MCP_Server.genres` and `MCP_Server.mixing` need adding (they work without it, so add only `MCP_Server.sounds` as required by SC4).

### Plan Count (D-05)
- **D-05:** One plan. Simple additions to existing files, no new modules, no new test infrastructure beyond verifying the tools are importable.

### Test Coverage (D-06)
- **D-06:** Extend `tests/test_sounds.py` with a `TestMCPTools` class:
  - `test_get_sound_recommendation_importable`: tool function importable from tools.sounds
  - `test_get_instrument_profile_importable`: tool function importable from tools.sounds
  - `test_list_sound_descriptors_already_registered`: all 3 tools in tools.sounds module
  - No integration tests that call through MCP server -- unit-level import/callable checks sufficient

</decisions>

<canonical_refs>
## Canonical References

- `MCP_Server/tools/sounds.py` — add two new tools here
- `MCP_Server/tools/genres.py` — pattern for tools with parameters (`get_genre_blueprint` takes `genre: str`)
- `MCP_Server/sounds/catalog.py` — `recommend()`, `get_profile()`, `list_profiles()` to import
- `pyproject.toml` — packages list to update

</canonical_refs>

<code_context>
## Existing Code Insights

### Already Done (Phase 37)
- `tools/__init__.py` imports `sounds` — SC3 partially satisfied
- `list_sound_descriptors` registered in sounds.py
- `recommend()` and `get_profile()` available in catalog

### Patterns to Follow
- `get_genre_blueprint(ctx, genre: str, ...)` — parameterized tool pattern
- `format_error("...", detail=str(e), suggestion="...")` — error response
- `json.dumps(result)` — return format for all tools

</code_context>

<deferred>
## Deferred Ideas

- Genre-aware recommendations (SREC-04) — post-v1.5
- Batch recommendation (multiple descriptors at once) — future enhancement

</deferred>

---

*Phase: 38-recommendation-tools-and-registration*
*Context gathered: 2026-03-31 (auto mode)*
