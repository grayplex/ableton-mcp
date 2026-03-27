# Phase 22: Core Genre Library - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 22-core-genre-library
**Areas discussed:** Subgenre selection, Content depth parity, Theory name validation

---

## Subgenre Selection

**Initial approach:** Use REQUIREMENTS.md subgenres as-is.
**User's choice:** Customize subgenres.
**User's approach:** Claude suggests improvements, user reviews.

**Suggested additions accepted:**
- Deep dubstep (original UK sound, 140 BPM, half-time) — accepted
- Alternative R&B (Weeknd, Frank Ocean territory) — accepted

**User-requested additions:**
- Peaktime/driving techno — accepted (festival-oriented, high-energy)
- EDM trap — deferred (distinct genre, not a hip-hop subgenre; Hex Cougar, ISOxo, RL Grime)
- Neuro DnB — accepted (distinct from neurofunk: heavier, more experimental)

**Clarification:** Neuro DnB confirmed as DISTINCT from neurofunk, not a synonym.

**EDM Trap disposition:** User confirmed it should be deferred to future genre (GENR-13+), not placed under hip-hop/trap.

| Genre | Final Subgenres |
|-------|----------------|
| Techno | minimal, industrial, melodic, Detroit, peaktime/driving |
| Hip-hop/Trap | boom bap, trap, lo-fi hip-hop |
| Ambient | dark ambient, drone, cinematic |
| DnB | liquid, neurofunk, jungle, neuro |
| Dubstep | brostep, riddim, melodic, deep dubstep |
| Trance | progressive, uplifting, psytrance |
| Neo-soul/R&B | neo-soul, contemporary R&B, alternative R&B |

---

## Content Depth Parity

| Option | Description | Selected |
|--------|-------------|----------|
| Equal depth, all match house.py | Every genre matches house.py detail level. | ✓ |
| P0 deeper, P1 lighter | Priority genres get more detail. | |
| You decide per genre | Claude determines per genre. | |

**User's choice:** Equal depth, all match house.py
**Notes:** None

---

## Theory Name Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Validate at authoring time | Tests check chord_types and scales against theory engine. | ✓ |
| Defer to Phase 24 | Schema-only validation, Phase 24 handles names. | |

**User's choice:** Validate at authoring time
**Notes:** Catches mistakes immediately rather than waiting for Phase 24.

---

## Claude's Discretion

- Exact instrumentation roles, chord progressions, BPM ranges per genre
- Arrangement structures, rhythm details, mixing conventions, production tips
- File naming conventions

## Deferred Ideas

- EDM Trap as standalone genre (GENR-13+) — Hex Cougar, ISOxo, RL Grime
