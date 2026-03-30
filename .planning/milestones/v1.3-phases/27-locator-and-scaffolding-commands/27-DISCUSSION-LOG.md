# Phase 27: Locator and Scaffolding Commands - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 27-locator-and-scaffolding-commands
**Areas discussed:** Track naming convention, Track creation scope, Overview richness, Scaffold input shape

---

## Track Naming Convention

| Option | Description | Selected |
|--------|-------------|----------|
| Bare role name | "kick", "bass", "lead" — clean and short | |
| Section:role | "drop:kick", "breakdown:lead" — fully scoped, many more tracks | |
| Role (numbered if repeated) | "kick", "lead", "lead 2" — handles same role with different sounds | ✓ |

**User's choice:** Role (numbered if repeated)
**Notes:** First occurrence uses bare role name; subsequent occurrences of the same role string get numeric suffixes (lead, lead 2, lead 3). Automatic and deterministic.

---

## Track Creation Scope

| Option | Description | Selected |
|--------|-------------|----------|
| One track per unique role | Deduplicated union of all roles — 5 tracks for 5 unique roles across 8 sections | ✓ |
| One track per section × role | Every section's role gets its own track — 20+ tracks for the same arrangement | |

**User's choice:** One track per unique role (recommended default)
**Notes:** All unique roles across all sections (no section_filter param needed).

---

## Overview Richness

| Option | Description | Selected |
|--------|-------------|----------|
| Locators + track names + length | Minimal: locators with bar positions, track names list, session_length_bars | ✓ |
| Plus track type + instrument status | Each track also includes MIDI/audio type and has_instrument flag | |

**User's choice:** Minimal (locators + track names + session length)
**Notes:** Track instrument status is Phase 28's responsibility. Keep overview token-efficient.

---

## Scaffold Input Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Raw plan JSON from generate_production_plan | Two-tool workflow; scaffold is a pure writer | ✓ |
| Genre + params (generates internally) | One-tool workflow but duplicates plan builder logic | |

**User's choice:** Raw plan JSON (recommended default)
**Notes:** Time signature is read from live Ableton session internally (not a caller param), unlike generate_production_plan which accepts time_signature as a param.

---

## Claude's Discretion

- Whether scaffold tools go in new `scaffold.py` module or extend `plans.py`
- Whether new Remote Script handler goes in `transport.py` or a new `scaffold.py` handler
- How to handle partial failure mid-scaffold
- Which Live 12 API method to use for positional locator creation (researcher to confirm)

## Deferred Ideas

- section_filter param — not needed; use generate_production_plan overrides instead
- Default instrument loading per role — v1.3.1 candidate per REQUIREMENTS.md
- Track type/instrument status in overview — Phase 28 scope
