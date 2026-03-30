---
phase: 33-mix-adjustment-intelligence
plan: 01
subsystem: tools
tags: [mcp-tool, mixing, diff-computation, device-parameters, intelligence]

# Dependency graph
requires:
  - phase: 32-device-state-reader-and-gain-staging
    provides: get_mix_state RS command and analysis.py tool module with _infer_role
  - phase: 31-apply-recipe-and-batch-parameter-tools
    provides: natural_to_normalized conversion and convert_recipe_to_payload
  - phase: 30-core-mix-recipes
    provides: genre mix recipes (house, techno, ambient, dnb) with get_recipe catalog
provides:
  - suggest_mix_adjustments MCP tool for parameter-level mix feedback
  - normalized_to_natural reverse conversion function for display values
affects: [phase-34-master-chain, future-whole-session-suggestions]

# Tech tracking
tech-stack:
  added: []
  patterns: [diff-computation-with-threshold, reverse-parameter-conversion, display-value-formatting]

key-files:
  created:
    - MCP_Server/tools/intelligence.py
    - tests/test_intelligence.py
  modified:
    - MCP_Server/devices/convert.py
    - MCP_Server/tools/__init__.py
    - tests/test_convert.py

key-decisions:
  - "normalized_to_natural returns None for unknown device/param (vs unchanged value in forward direction) to signal missing data"
  - "Display formatting uses unit-aware strings (~Hz, dB, ms, %) with is_quantized rounding to int"
  - "Reason generation uses direction (above/below) + target display value + genre/role context"

patterns-established:
  - "Reverse conversion pattern: normalized_to_natural mirrors natural_to_normalized with safe_min guard"
  - "Intelligence tool pattern: read state, lookup recipe, diff computation, threshold filter, display format"

requirements-completed: [INTEL-01]

# Metrics
duration: 4min
completed: 2026-03-28
---

# Phase 33 Plan 01: Mix Adjustment Intelligence Summary

**suggest_mix_adjustments tool diffs track device state against role x genre recipe targets, returning per-parameter suggestions with display values and one-sentence reasons**

## What Was Built

### Task 1: normalized_to_natural() reverse conversion
Added inverse conversion function to `MCP_Server/devices/convert.py` that converts normalized 0.0-1.0 values back to natural units (Hz, dB, ms). Handles log (with safe_min guard for natural_min=0), linear, linear_db, and no-conversion cases. Returns None for unknown device/param (unlike the forward function which returns unchanged value). 9 test methods added to `tests/test_convert.py` including round-trip validation.

### Task 2: suggest_mix_adjustments MCP tool
Created `MCP_Server/tools/intelligence.py` with the `suggest_mix_adjustments` tool that:
1. Gets current device state via `get_mix_state` RS command
2. Finds track by case-insensitive substring match across all track groups
3. Resolves role (explicit or inferred via `_infer_role`)
4. Looks up recipe via `get_recipe(role, genre)`
5. Computes per-parameter diffs (normalized values), filtering below 0.03 threshold
6. Formats display values using `normalized_to_natural` + unit-aware formatting
7. Generates one-sentence reasons with direction and target context
8. Returns JSON grouped by device display name

Registered in `MCP_Server/tools/__init__.py`. 13 test methods in `tests/test_intelligence.py` covering all behaviors including error cases.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | `4b61272` | normalized_to_natural() reverse conversion with 9 tests |
| 2 | `db3c8f6` | suggest_mix_adjustments tool, registration, 13 tests |

## Verification

- `python -m pytest tests/test_intelligence.py tests/test_convert.py -x -q` -- 37 passed
- `python -m pytest tests/test_analysis.py tests/test_mixing.py -x -q` -- 76 passed (no regressions)
- No write commands in intelligence.py (read-only tool confirmed)
- Tool registered and discoverable via __init__.py import

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all functionality is fully wired.

## Self-Check: PASSED

- All 6 key files verified present on disk
- Both commit hashes (4b61272, db3c8f6) verified in git log
- 37 domain tests pass (13 intelligence + 24 convert)
- 290 pre-existing test failures unchanged (not caused by this plan)
