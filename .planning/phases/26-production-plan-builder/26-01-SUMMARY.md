---
phase: 26-production-plan-builder
plan: 01
subsystem: api
tags: [mcp-tools, genre-blueprints, production-planning, arrangement, bar-positions]

# Dependency graph
requires:
  - phase: 20-blueprint-infrastructure
    provides: genre catalog with get_blueprint(), ArrangementEntry schema
  - phase: 21-blueprint-tools
    provides: genre tool module patterns (ctx=None passthrough, format_error, mock boilerplate)
  - phase: 22-core-genre-library
    provides: 12 genre blueprints with arrangement sections
provides:
  - generate_production_plan MCP tool: flat JSON plan with cumulative bar positions for all sections
  - generate_section_plan MCP tool: single section plan with correct bar_start offset
  - _build_plan_sections helper: reusable cumulative bar calculation with deep copy safety
affects: [26-02-plan-builder-overrides, any future plan/arrangement workflows]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure computation MCP tools: no socket calls, no Ableton dependency"
    - "Deep copy before mutation: copy.deepcopy(blueprint[arrangement][sections]) before adding bar_start"
    - "Conditional field pattern: include vibe in result only when not None"
    - "Cumulative bar tracking: bar starts at 1, bar += s[bars] after each section"

key-files:
  created:
    - MCP_Server/tools/plans.py
    - tests/test_plan_tools.py
  modified:
    - MCP_Server/tools/__init__.py

key-decisions:
  - "bar_start is 1-based and cumulative: intro=1, buildup=17, drop=25 for house (16+8+32 pattern)"
  - "Vibe field conditional: included in output only when provided by caller (not None)"
  - "time_signature defaults to 4/4 when caller omits it"
  - "Deep copy of arrangement sections prevents blueprint registry mutation across repeated calls"
  - "section_bar_overrides, add_sections, remove_sections declared in signature but not implemented (Plan 02)"

patterns-established:
  - "Plan tool pattern: get_blueprint() -> deepcopy sections -> _build_plan_sections() -> assemble result dict"
  - "section_not_found error includes available section names in suggestion"

requirements-completed: [PLAN-01, PLAN-02]

# Metrics
duration: 2min
completed: 2026-03-28
---

# Phase 26 Plan 01: Production Plan Builder — Core Tools Summary

**Two pure-computation MCP tools (generate_production_plan, generate_section_plan) that transform genre blueprint arrangement data into flat JSON plans with 1-based cumulative bar positions and conditional vibe/time_signature fields.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-28T03:56:36Z
- **Completed:** 2026-03-28T03:58:49Z
- **Tasks:** 1
- **Files modified:** 3

## Accomplishments

- Created `MCP_Server/tools/plans.py` with `generate_production_plan`, `generate_section_plan`, and `_build_plan_sections` helper
- Registered plans module in `MCP_Server/tools/__init__.py` in alphabetical position
- 17 tests in `tests/test_plan_tools.py` covering all 12 base genres, bar position math, token budget, mutation safety, and conditional fields

## Task Commits

Each task was committed atomically:

1. **Task 1: Create test file and plan builder module with both tools** - `8ac2207` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `MCP_Server/tools/plans.py` - Core plan builder tools and _build_plan_sections helper
- `MCP_Server/tools/__init__.py` - Added `plans` to tool module imports
- `tests/test_plan_tools.py` - 17 tests covering both tools

## Decisions Made

- bar_start values are 1-based and cumulative: house intro=1, buildup=17 (1+16), drop=25 (17+8), breakdown=57 (25+32), buildup2=73, drop2=81, outro=113
- Vibe field is conditional: only included in output dict when caller provides a non-None vibe argument
- Plan 02 override params (section_bar_overrides, add_sections, remove_sections) are declared in signature but body ignores them — no forward-breaking change
- Deep copy is mandatory before adding bar_start to avoid mutating the blueprint registry across repeated calls

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- tiktoken import failure in test_genre_quality.py and async mock TypeError in many older test files are pre-existing issues not caused by this plan. All non-async genre/palette/plan tests pass (169 tests green).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02 can immediately add override logic to `_build_plan_sections` — signature already declares the params
- `get_blueprint()` integration pattern is established and tested across all 12 genres
- Bar position math is validated; cumulative bar tracking is correct and mutation-safe

---
*Phase: 26-production-plan-builder*
*Completed: 2026-03-28*

## Self-Check: PASSED

- FOUND: MCP_Server/tools/plans.py
- FOUND: tests/test_plan_tools.py
- FOUND: .planning/phases/26-production-plan-builder/26-01-SUMMARY.md
- FOUND: commit 8ac2207
