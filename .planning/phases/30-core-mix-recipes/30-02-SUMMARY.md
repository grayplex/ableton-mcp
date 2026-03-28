---
phase: 30-core-mix-recipes
plan: 02
subsystem: mixing
tags: [mix-recipes, ambient, drum-and-bass, mcp-tool, genre-recipes]

# Dependency graph
requires:
  - phase: 30-01
    provides: "Mix recipe infrastructure (catalog, house/techno recipes, test suite)"
provides:
  - "Ambient genre mix recipe (9 roles, all param-validated)"
  - "Drum and bass genre mix recipe (9 roles, all param-validated)"
  - "get_mix_recipe MCP tool for querying recipes by role/genre"
  - "Tool registration in MCP server"
affects: [31-apply-mix-recipe, 34-master-bus-recipes]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Recipe authoring pattern: genre-specific sonic character via device param values in natural units"]

key-files:
  created:
    - MCP_Server/mixing/ambient.py
    - MCP_Server/mixing/drum_and_bass.py
    - MCP_Server/tools/mixing.py
  modified:
    - MCP_Server/tools/__init__.py
    - tests/test_mixing.py

key-decisions:
  - "Used Delay device class name (not ProxyAudioEffectDevice) matching CATALOG and house.py pattern"
  - "Ambient recipes use very gentle compression (1.3-2:1 ratio) with long reverb tails (3-5s decay)"
  - "DnB recipes use aggressive compression (5-6:1) with DrumBuss on kick and fast attack/release"
  - "DnB vocal includes Gate device for cleanup (matching house vocal pattern)"

patterns-established:
  - "Genre sonic identity via parameter values: ambient = spacious/gentle, DnB = punchy/aggressive"

requirements-completed: [RECIP-01]

# Metrics
duration: 5min
completed: 2026-03-28
---

# Phase 30 Plan 02: Genre Recipes and MCP Tool Summary

**Ambient and DnB genre recipes authored with get_mix_recipe MCP tool exposing all 4 core genres (36 role/genre combinations) via JSON query API.**

## What Was Built

### Ambient Genre Recipe (MCP_Server/mixing/ambient.py)
- All 9 roles authored with ambient-appropriate values
- Sonic character: spacious, ethereal, minimal compression (1.3-2:1 ratios), long reverb tails (3-5s), wide stereo fields (up to 2.0 width)
- Kick/bass kept gentle and warm; pads and atmospheric elements are the primary focus
- Long Delay feedback (0.4-0.5) for wash effects

### Drum and Bass Genre Recipe (MCP_Server/mixing/drum_and_bass.py)
- All 9 roles authored with DnB-appropriate values
- Sonic character: fast and punchy drums, heavy sub-bass, aggressive compression (5-6:1), short reverbs (0.8-1.5s), tight low end
- Kick uses DrumBuss for saturation and transient shaping
- Vocal includes Gate for cleanup
- Bass is mono with 150Hz bass mono crossover

### get_mix_recipe MCP Tool (MCP_Server/tools/mixing.py)
- Single MCP tool: `get_mix_recipe(role, genre) -> JSON`
- Returns full device parameter dict for role/genre combination
- Returns helpful error with role/genre suggestions for invalid input
- Resolves role aliases (vocals -> vocal, kick drum -> kick) and genre aliases (dnb -> drum_and_bass)

### Tool Registration
- Added `mixing` module to `MCP_Server/tools/__init__.py` import chain
- Auto-discovered by pkgutil without any manual registration

### Test Coverage
- 6 new MCP tool tests in `TestMixRecipeTool` class
- 27 total mixing tests passing (auto-discovery, get_recipe, aliases, param validation, completeness, data structure, list_recipes, tool)

## Verification Results

- `pytest tests/test_mixing.py -x -v`: 27 passed
- `list_recipes()` returns: `['ambient', 'drum_and_bass', 'house', 'techno']`
- `get_recipe('kick', 'dnb')` returns device dict (alias resolution works)
- All recipe param names validated against device CATALOG

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan referenced ProxyAudioEffectDevice instead of Delay**
- **Found during:** Task 1
- **Issue:** Plan description mentioned "ProxyAudioEffectDevice" for delay effects, but the actual CATALOG device class name is "Delay" (matching house.py and techno.py)
- **Fix:** Used "Delay" as the device class key throughout both recipes
- **Files modified:** MCP_Server/mixing/ambient.py, MCP_Server/mixing/drum_and_bass.py

## Known Stubs

None -- all recipes contain complete, genre-appropriate parameter values for every role.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | dd4bd76 | Ambient and DnB genre recipe data files |
| 2 | 3ac4b89 | get_mix_recipe MCP tool + registration + tests |

## Self-Check: PASSED
