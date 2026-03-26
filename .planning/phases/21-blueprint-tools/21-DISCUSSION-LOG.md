# Phase 21: Blueprint Tools - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 21-blueprint-tools
**Areas discussed:** Section filtering design, Tool output shape, Error responses

---

## Section Filtering Design

| Option | Description | Selected |
|--------|-------------|----------|
| List of strings | sections=["harmony", "rhythm"]. Clean, typed. | ✓ |
| Comma-separated string | sections="harmony,rhythm". Needs parsing. | |
| Single section parameter | section="harmony". Multiple calls needed. | |

**User's choice:** List of strings

| Option | Description | Selected |
|--------|-------------|----------|
| Return full blueprint | All 6 dimensions when no filter. | ✓ |
| Return curated subset | Default subset to save tokens. | |

**User's choice:** Return full blueprint
**Notes:** None

---

## Tool Output Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Direct dict as JSON | Nested structure preserved. | ✓ |
| Flattened structure | Top-level keys, loses grouping. | |

**User's choice:** Direct dict as JSON

| Option | Description | Selected |
|--------|-------------|----------|
| Summary per genre | id, name, bpm_range, subgenres list. | ✓ |
| Names only | Just id and name. | |
| Full blueprints | All data for all genres. Expensive. | |

**User's choice:** Summary per genre
**Notes:** None

---

## Error Responses

| Option | Description | Selected |
|--------|-------------|----------|
| Use format_error() | Structured errors matching all other tools. | ✓ |
| Plain error strings | Simple but inconsistent. | |

**User's choice:** Use format_error()

| Option | Description | Selected |
|--------|-------------|----------|
| Try alias first | Resolve aliases before erroring. Forgiving. | ✓ |
| Exact match only | Strict matching, no alias resolution. | |

**User's choice:** Try alias first
**Notes:** None

---

## Claude's Discretion

- Tool file placement, parameter naming, docstrings
- Subgenre parameter design
- Invalid section name handling
- Test structure

## Deferred Ideas

None — discussion stayed within phase scope
