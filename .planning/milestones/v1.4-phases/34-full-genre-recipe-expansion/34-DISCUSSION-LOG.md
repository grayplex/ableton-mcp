# Phase 34: Full Genre Recipe Expansion - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-30
**Phase:** 34-full-genre-recipe-expansion
**Areas discussed:** Plan split strategy, Genre aliases, Tool docstring updates

---

## Plan Split Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Two plans, genre family split | Plan 1: synthwave/dubstep/trance/future_bass; Plan 2: hip_hop_trap/disco_funk/neo_soul_rnb/lo_fi | ✓ |
| Single plan, all 8 | One dense plan, ~6k lines of data in one execution | |
| Four plans, 2 genres each | Most granular, 4x planning overhead | |

**User's choice:** Two plans, genre family split (Recommended)
**Notes:** Mirrors Phase 22+23 pattern for genre authoring.

---

## Genre Aliases

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal — slash/special char variants only | Only r&b, hip-hop, slash forms | ✓ |
| Comprehensive — all common shorthands | trap, rnb, funk, future, lofi, etc. | |
| None — canonical IDs only | No new aliases at all | |

**User's choice:** Minimal (Recommended)
**Notes:** Canonical snake_case IDs are primary; aliases only for slash/ampersand input variants.

---

## Tool Docstring Updates

| Option | Description | Selected |
|--------|-------------|----------|
| Reference list_recipes() | Replace hardcoded list with "use list_recipes()" | ✓ |
| List all 12 inline | Explicit but requires future maintenance | |

**User's choice:** Reference list_recipes() (Recommended)
**Notes:** Applies to get_mix_recipe, apply_mix_recipe, apply_master_recipe, suggest_mix_adjustments.

---

## Claude's Discretion

- Exact natural-unit parameter values per role/genre combination
- Which devices to include per role per genre
- Non-typical role/genre pairings handled with safe generic values
