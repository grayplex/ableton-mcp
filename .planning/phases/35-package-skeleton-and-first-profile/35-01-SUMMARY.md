---
phase: 35-package-skeleton-and-first-profile
plan: 01
subsystem: sounds
tags: [instrument-profiles, auto-discovery, pkgutil, wavetable]
dependency_graph:
  requires: []
  provides: [sounds-package, wavetable-profile, get_profile-api, list_profiles-api]
  affects: [MCP_Server/sounds/]
tech_stack:
  added: []
  patterns: [pkgutil-auto-discovery, alias-normalization, PROFILE-constant]
key_files:
  created:
    - MCP_Server/sounds/__init__.py
    - MCP_Server/sounds/catalog.py
    - MCP_Server/sounds/wavetable.py
    - tests/test_sounds.py
  modified: []
decisions:
  - Cloned genres/catalog.py auto-discovery pattern for sounds/ package
  - No schema validation module (simpler than genres; per D-02)
  - Alias normalization uses same approach as genres (lowercase, spaces/hyphens to underscores)
metrics:
  duration: 1m
  completed: "2026-03-31T12:39:00Z"
  tasks_completed: 1
  tasks_total: 1
  test_count: 17
  test_pass: 17
  lines_added: 299
---

# Phase 35 Plan 01: Package Skeleton and First Profile Summary

sounds/ package with pkgutil auto-discovery catalog and Wavetable instrument profile -- proves data schema, alias resolution, and browser path structure before committing to all 6 instruments in Phase 36.

## What Was Built

### sounds/ Package (3 source files, 159 lines)

- **`MCP_Server/sounds/__init__.py`** -- Public API re-exports (`get_profile`, `list_profiles`)
- **`MCP_Server/sounds/catalog.py`** -- Auto-discovery engine using `pkgutil.iter_modules` to find PROFILE constants in sibling modules; alias normalization (case, spaces, hyphens); lazy initialization on first access
- **`MCP_Server/sounds/wavetable.py`** -- Reference instrument profile with sonic character, strengths/weaknesses, descriptor affinities (role + character axes with 0.0-1.0 weights), and browser path mapping

### Test Suite (140 lines, 17 tests)

- **TestAutoDiscovery** (3 tests): wavetable discovered, catalog module skipped, metadata shape
- **TestGetProfile** (2 tests): canonical id lookup, unknown returns None
- **TestAliasResolution** (4 tests): abbreviation "wt", case "Wavetable", space "wave table", hyphen "wave-table"
- **TestProfileShape** (8 tests): required keys, sonic_character type, strengths/weaknesses lists, affinity axes, weight ranges 0.0-1.0, browser root and categories

## Task Completion

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create test scaffold and sounds/ package skeleton | 412bb3c | tests/test_sounds.py, MCP_Server/sounds/{__init__,catalog,wavetable}.py |

## Verification Results

- `python -m pytest tests/test_sounds.py -x -v` -- 17/17 passed
- `get_profile('wavetable')` -- returns dict with name "Wavetable", browser root "Instruments/Wavetable"
- `get_profile('wt')` -- resolves alias to id "wavetable"
- `get_profile('Wavetable')` -- case-insensitive resolution works
- `get_profile('wave table')` -- space normalization works
- `get_profile('wave-table')` -- hyphen normalization works
- `get_profile('nonexistent')` -- returns None

## Deviations from Plan

None -- plan executed exactly as written. Source files and tests were created in the same commit (TDD RED+GREEN combined) since the plan specified a single task with both phases.

## Known Stubs

None -- all data is real, all APIs are functional.

## Self-Check: PASSED
