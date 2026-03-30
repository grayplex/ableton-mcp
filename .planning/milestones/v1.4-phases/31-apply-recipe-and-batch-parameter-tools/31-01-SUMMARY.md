---
phase: 31-apply-recipe-and-batch-parameter-tools
plan: 01
subsystem: mixing/devices
tags: [conversion, master-recipe, catalog, tdd]
dependency_graph:
  requires: [MCP_Server/devices/catalog.py, MCP_Server/mixing/catalog.py]
  provides: [MCP_Server/devices/convert.py, get_master_recipe API, MASTER_RECIPE data]
  affects: [31-02 apply_mix_recipe and apply_master_recipe MCP tools]
tech_stack:
  added: []
  patterns: [natural-to-normalized conversion, master bus recipe constants, auto-discovery extension]
key_files:
  created:
    - MCP_Server/devices/convert.py
    - tests/test_convert.py
  modified:
    - MCP_Server/mixing/house.py
    - MCP_Server/mixing/techno.py
    - MCP_Server/mixing/ambient.py
    - MCP_Server/mixing/drum_and_bass.py
    - MCP_Server/mixing/catalog.py
    - MCP_Server/mixing/__init__.py
    - tests/test_mixing.py
decisions:
  - "D-01: Limiter param names corrected from plan: 'Gain' -> 'Input Gain', 'Link Channels' -> 'Link', 'Lookahead' is quantized 0-2"
  - "D-02: MultibandDynamics param names use parenthesized format from CATALOG: 'Band Activator (Low)' not 'Band Activator Low'"
  - "D-03: MultibandDynamics Input Gain added per-band (Low/Mid/High) not single 'Input Gain'"
  - "D-04: GlueCompressor Dry/Wet uses 100.0 (natural %) not 1.0 (normalized) -- conversion handles %->0-1"
metrics:
  duration: 4min
  completed: "2026-03-28T19:55:00Z"
  tasks: 1
  files_created: 2
  files_modified: 7
  tests_added: 22
  tests_total_pass: 52
---

# Phase 31 Plan 01: Conversion Module and Master Recipe Data Summary

Natural-to-normalized conversion layer (log/linear/linear_db/passthrough with clamping) plus MASTER_RECIPE constants for 4 genres (house, techno, ambient, DnB) with auto-discovery via pkgutil

## What Was Built

### MCP_Server/devices/convert.py (new)
- `natural_to_normalized(device_class, param_name, natural_value)`: Converts natural-unit values (Hz, dB, ms, %) to normalized 0.0-1.0 floats using CATALOG conversion metadata. Handles log, linear, linear_db, and passthrough (conversion=None). Clamps out-of-range values. Returns unchanged for unknown device/param.
- `convert_recipe_to_payload(recipe)`: Transforms `{device_class: {param: natural_val}}` to `[{"class_name": str, "params": {param: normalized_val}}]` for the RS handler.

### MASTER_RECIPE Constants (4 genres)
Each genre file received a `MASTER_RECIPE` dict with 3 device chains:
- **GlueCompressor**: Threshold, Ratio, Attack, Release, Makeup, Dry/Wet, Peak Clip In, Range
- **MultibandDynamics**: Master Output, Band Activator (Low/Mid/High), Above Threshold (Low/Mid/High), Above Ratio (Low/Mid/High), Input Gain (Low/Mid/High)
- **Limiter**: Input Gain, Ceiling, Link, Lookahead

Genre characteristics:
- **House**: Punchy, glued, loud (-6dB threshold, 4dB limiter gain)
- **Techno**: Hard, aggressive (-8dB threshold, 5dB limiter gain)
- **Ambient**: Gentle, transparent (-4dB threshold, 2dB limiter gain)
- **DnB**: Punchy, very aggressive (-10dB threshold, 6dB limiter gain)

### Catalog Extension
- `_master_registry` parallel to `_registry` for master bus recipes
- `_discover_recipes()` extended to detect MASTER_RECIPE attr on genre modules
- `get_master_recipe(genre)` public API with alias resolution (e.g., "dnb" -> drum_and_bass)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected MASTER_RECIPE parameter names to match CATALOG**
- **Found during:** Task 1 (CATALOG validation)
- **Issue:** Plan specified param names that differed from actual CATALOG entries. Limiter used "Gain" (CATALOG: "Input Gain"), "Link Channels" (CATALOG: "Link"). MultibandDynamics used space-separated "Band Activator Low" (CATALOG: "Band Activator (Low)"). Plan had single "Input Gain" for MultibandDynamics but CATALOG only has per-band variants.
- **Fix:** Used CATALOG param names exactly. Added per-band Input Gain (Low/Mid/High) for MultibandDynamics. Fixed Dry/Wet to use natural % (100.0) not normalized (1.0).
- **Files modified:** house.py, techno.py, ambient.py, drum_and_bass.py
- **Commit:** 2875519

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 9089034 | test | Failing tests for conversion module and master recipes (TDD RED) |
| 2875519 | feat | Conversion module and master recipe data for 4 genres (TDD GREEN) |

## Known Stubs

None -- all functions are fully implemented with real data.

## Self-Check: PASSED
