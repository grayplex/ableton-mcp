# Phase 28: Section Execution and Quality Gate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 28-section-execution-and-quality-gate
**Areas discussed:** Checklist data source, Pending definition, Progress check shape

---

## Checklist Data Source

| Option | Description | Selected |
|--------|-------------|----------|
| Caller passes plan + section_name | Stateless: caller passes production plan dict and section_name. Tool filters sections, checks instrument status per role's track. | ✓ |
| Read Ableton state only | Stateful: tool reads locators + track names from Ableton, infers roles from track names. Unreliable because scaffold creates one track per unique role, not per section. | |
| section_name + explicit roles list | Caller builds roles list themselves. More flexible but puts burden on caller. | |

**User's choice:** Caller passes plan + section_name (recommended)
**Notes:** Consistent with scaffold_arrangement pattern which also accepts the plan dict directly.

---

## "Pending" Definition

| Option | Description | Selected |
|--------|-------------|----------|
| Instrument loaded | Done when track has ≥1 device. Fast, one Ableton read per track. | ✓ |
| Notes exist in clips | Done when track has MIDI notes. Heavier — requires reading clip contents. | |
| Both: instrument AND notes | Most strict — instrument AND notes required. Likely overkill for checklist purpose. | |

**User's choice:** Instrument loaded (recommended)
**Notes:** The checklist is about preventing forgotten instruments, not tracking compositional progress.

---

## Progress Check Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Empty tracks list | Returns only tracks with no instrument: {empty_tracks, total_tracks, empty_count}. Focused. | ✓ |
| All tracks with status | Returns every track with has_instrument flag. More verbose but comprehensive. | |

**User's choice:** Empty tracks list (recommended)
**Notes:** Focused format aligns with success criterion 2 ("see which scaffolded MIDI tracks have no instrument loaded").

---

## Claude's Discretion

- Whether to extend `scaffold.py` tool module or create a new `execution.py`
- Whether to extend `get_arrangement_state` Remote Script command or add a new one for device presence
- How to handle track name mismatches (track renamed after scaffold)

## Deferred Ideas

None.
