---
phase: 26-production-plan-builder
plan: 02
subsystem: api
tags: [mcp-tools, genre-blueprints, production-planning, arrangement, overrides, bar-positions]

# Dependency graph
requires:
  - phase: 26-production-plan-builder
    plan: 01
    provides: generate_production_plan and _build_plan_sections with override params declared but unimplemented
  - phase: 22-core-genre-library
    provides: 12 genre blueprints with arrangement sections (name/bars/energy/roles/transition_in)
provides:
  - section_bar_overrides: resize any blueprint section to a custom bar count; positions recalculate
  - add_sections: insert custom sections after a named anchor; positions recalculate
  - remove_sections: drop named sections from the plan; positions recalculate
  - warnings list in output for nonexistent section references
  - ValueError / format_error for duplicate section name on add
affects: [26-03-plan-scribe, any future plan/arrangement workflows that consume plan output]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Override application order: remove -> add -> resize -> calculate (D-09)"
    - "_build_plan_sections returns tuple (plan_sections, warnings) after override refactor"
    - "Duplicate name raises ValueError; caller catches and returns format_error"
    - "Added sections get roles=[] and no transition_in (no blueprint data for custom sections)"
    - "Warnings list included in output only when non-empty (parallel to vibe conditional pattern)"

key-files:
  created: []
  modified:
    - MCP_Server/tools/plans.py
    - tests/test_plan_tools.py

key-decisions:
  - "_build_plan_sections signature extended to accept all three override params; returns tuple not list"
  - "Override order is remove -> add -> resize -> calculate bar positions (D-09 from CONTEXT.md)"
  - "Duplicate section name raises ValueError (not a warning) -- caller converts to format_error"
  - "Nonexistent anchor/name produces warning string (not error) -- plan is still returned with warnings list"
  - "Added custom sections have roles=[] and no transition_in (no blueprint data, these are user-defined)"

patterns-established:
  - "Warning accumulation pattern: build warnings list during processing, include in result only if non-empty"
  - "Override validation pattern: validate each entry, accumulate warnings/errors before applying changes"

requirements-completed: [PLAN-03]

# Metrics
duration: 20min
completed: 2026-03-28
---

# Phase 26 Plan 02: Production Plan Builder Overrides Summary

**Section override support for generate_production_plan: remove/add/resize sections with correct bar position recalculation and warnings for invalid references**

## Performance

- **Duration:** 20 min
- **Started:** 2026-03-28T03:45:00Z
- **Completed:** 2026-03-28T04:05:24Z
- **Tasks:** 1 (TDD: test commit + implementation commit)
- **Files modified:** 2

## Accomplishments

- Added `remove_sections` support: drops named sections and recalculates all bar positions
- Added `add_sections` support: inserts custom sections after a named anchor with correct positions
- Added `section_bar_overrides` support: resizes named sections and shifts all subsequent bar positions
- Combined overrides work correctly in documented order (remove -> add -> resize -> calculate)
- Nonexistent section references produce a `warnings` list in the plan output (not errors)
- Duplicate section names on `add_sections` return format_error immediately
- 10 new override tests added; all 27 plan tool tests pass; 175 related module tests pass

## Task Commits

Each task was committed atomically with TDD RED/GREEN commits:

1. **Task 1 (RED): Override tests** - `9c2acc8` (test)
2. **Task 1 (GREEN): Override implementation** - `acfb8ff` (feat)

## Files Created/Modified

- `MCP_Server/tools/plans.py` - Extended `_build_plan_sections` with override params; returns `(sections, warnings)` tuple; updated `generate_production_plan` to pass overrides and include warnings in output
- `tests/test_plan_tools.py` - Added `TestOverrides` class with 9 tests covering all override combinations

## Decisions Made

- `_build_plan_sections` returns a tuple `(plan_sections, warnings)` instead of a plain list — cleanest way to propagate warnings back to the caller without side effects
- Override order follows D-09 from CONTEXT.md: remove first (reduces the section set), then add (adds to the reduced set), then resize (changes bar counts), then calculate positions (final pass)
- Duplicate section names on add raise `ValueError` so the caller can return `format_error` before any partial changes are made — this is an error not a warning because the intent is ambiguous
- Nonexistent anchor/name on remove/add/resize is a warning (not an error) — the remaining overrides and the plan are still returned, which is more useful than failing the whole call
- Added sections get `roles=[]` and no `transition_in` key — they are custom user-defined sections with no blueprint data

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- This worktree is based on `main` (phase 24 only), but phase 25 arrangement extensions and phase 26 plan 01 files exist only on `gsd/v1.3-arrangement-intelligence`. Used `git checkout gsd/v1.3-arrangement-intelligence -- <files>` to bring the required files into the working tree before implementing plan 02.

## Next Phase Readiness

- All three override params are fully functional: section_bar_overrides, add_sections, remove_sections
- Override application order (remove -> add -> resize -> calculate) is verified by tests
- Plan 02 output format is stable: sections array + optional warnings list
- Phase 26 Plan 03 (if any) can extend generate_production_plan further or consume its output

---
*Phase: 26-production-plan-builder*
*Completed: 2026-03-28*

## Self-Check: PASSED

- FOUND: MCP_Server/tools/plans.py
- FOUND: tests/test_plan_tools.py
- FOUND: .planning/phases/26-production-plan-builder/26-02-SUMMARY.md
- FOUND commit: 9c2acc8 (test RED phase)
- FOUND commit: acfb8ff (feat GREEN phase)
- All 27 plan tool tests pass
